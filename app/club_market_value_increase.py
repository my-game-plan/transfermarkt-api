import pandas as pd
from datetime import datetime

from services.clubs.players import TransfermarktClubPlayers
from services.competitions.clubs import TransfermarktCompetitionClubs
from services.players.market_value import TransfermarktPlayerMarketValue


def parse_currency_value(raw_currency_value: str, player_id: str):
    # Ensure the value contains the Euro sign
    if "€" not in raw_currency_value:
        print(f"Player ID: {player_id} - Missing € in raw currency value: {raw_currency_value}")
        return None

    # Remove the Euro sign
    currency_value = raw_currency_value.replace("€", "")

    # Initialize the multiplier based on whether value ends in 'k' or 'm'
    if "k" in currency_value:
        multiplier = 1000
        currency_value = currency_value.replace("k", "")
    elif "m" in currency_value:
        multiplier = 1000000
        currency_value = currency_value.replace("m", "")
    else:
        print(f"Player ID: {player_id} - Missing k/m in currency value: {currency_value}")
        return None

    # Convert the market value to integer after applying the multiplier
    try:
        currency_value_int = int(float(currency_value) * multiplier)
        return currency_value_int
    except ValueError:
        print(f"Player ID: {player_id} - Invalid currency value format: {currency_value}")
        return None


def parse_market_value(raw_player_market_value: dict, player_id: str):
    # Check if the market value is present in the input dictionary
    if "marketValueHistory" not in raw_player_market_value:
        print(f"Player ID: {player_id} - No marketValueHistory object: {raw_player_market_value}")
        return None

    market_values = []
    for market_value in raw_player_market_value["marketValueHistory"]:
        if "value" not in market_value:
            print(f"Player ID: {player_id} - No value object: {market_value}")
        else:
            value = parse_currency_value(market_value["value"], player_id)
            if value:
                if "age" in market_value:
                    age = int(market_value["age"])
                else:
                    age = None
                    print(f"Player ID: {player_id} - No age in market_value object: {market_value}")
                market_values.append({"date": datetime.strptime(market_value["date"], '%b %d, %Y'), "value": value,
                                      "age": age, "clubID": market_value["clubID"]})

    return market_values


competition_id = "PO1"
season_id = "2023"
start_date = datetime.strptime("2023-10-01", "%Y-%m-%d")
end_date = datetime.strptime("2024-05-31", "%Y-%m-%d")
players_value_info = []

if __name__ == "__main__":
    competition_clubs = TransfermarktCompetitionClubs(competition_id=competition_id, season_id=season_id).get_competition_clubs()
    for club in competition_clubs["clubs"]:
        club_players = TransfermarktClubPlayers(club_id=club["id"]).get_club_players()
        for player in club_players["players"]:
            start_club_id, end_club_id, start_value, end_value = None, None, None, None
            raw_market_values = TransfermarktPlayerMarketValue(player_id=player["id"]).get_player_market_value()
            market_values = parse_market_value(raw_market_values, player["id"])
            for market_value in market_values:
                if market_value["date"] < start_date:
                    start_value = market_value["value"]
                    start_club_id = market_value["clubID"]
                if market_value["date"] < end_date:
                    end_value = market_value["value"]
                    end_club_id = market_value["clubID"]
            if start_club_id and (start_club_id == end_club_id):
                market_value_increase = end_value - start_value
                player_value_info = {"club_name": club["name"], "player_name": player["name"], "player_age": int(player["age"]),
                               "market_value_increase": market_value_increase, "start_market_value": start_value, "end_market_value": end_value}
                players_value_info.append(player_value_info)

    players_value_info_df = pd.DataFrame(players_value_info)

    result_df = players_value_info_df.groupby('club_name').agg({
        'market_value_increase': 'sum',
        'start_market_value': 'sum',
        'end_market_value': 'sum',
        'player_name': 'count',  # Count of players
        'player_age': 'mean',  # Average age of players
    }).reset_index()

    players_value_info_df.to_csv(f'{competition_id}_players_value_info.csv', index=False)
    result_df.to_csv(f'{competition_id}_market_value_summary.csv', index=False)
