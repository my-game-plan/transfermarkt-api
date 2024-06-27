import csv
import pandas as pd

from services.clubs.transfers import TransfermarktClubTransfers
from services.competitions.clubs import TransfermarktCompetitionClubs
from services.players.stats import TransfermarktPlayerStats


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


def parse_minutes(raw_minutes: str):
    return int(raw_minutes.replace("'", "").replace(".", ""))


competition_id = "PL1"
competition_matches_per_season = 34
season_id = "2023"
competition_arrivals = []

if __name__ == "__main__":
    competition_clubs = TransfermarktCompetitionClubs(competition_id=competition_id, season_id=season_id).get_competition_clubs()
    for club in competition_clubs["clubs"]:
        club_transfers = TransfermarktClubTransfers(club_id=club["id"], season_id=season_id).get_club_transfers()
        for arrival in club_transfers["arrivals"]:
            _player_stats = TransfermarktPlayerStats(player_id=arrival["id"]).get_player_stats()
            player_stats = _player_stats.get("stats")
            if player_stats:
                player_competition_stats = next(
                    (stat for stat in player_stats if stat["competitionID"] == competition_id), None)
                if player_competition_stats:
                    if "minutesPlayed" in player_competition_stats:
                        minutes_played = parse_minutes(player_competition_stats["minutesPlayed"])
                    else:
                        print(f"Player {arrival['name']} has no minutes played for competition {competition_id}")
                        minutes_played = 0
                    raw_fee = arrival.get("fee")
                    if raw_fee is None:
                        parsed_fee = 0
                    elif raw_fee == "End of loan":
                        continue
                    elif raw_fee in ["?", "-", "free transfer", "loan transfer", "Loan fee:", "draft"]:
                        parsed_fee = 0
                    elif "Loan fee: " in raw_fee:
                        parsed_fee = parse_currency_value(raw_fee.replace("Loan fee: ", ""), arrival["id"])
                    else:
                        parsed_fee = parse_currency_value(raw_fee, arrival["id"])
                    pct_minutes_played = round(minutes_played / (competition_matches_per_season * 90), 2)
                    age = int(arrival.get("age", 26))
                    arrival_info = {"club_name": club["name"], "player_name": arrival["name"], "player_age": age,
                                    "left": arrival["left"], "fee": parsed_fee,
                                    "minutes_played": minutes_played, "pct_minutes_played": pct_minutes_played, "euro_minutes_played": pct_minutes_played * parsed_fee, "raw_fee": raw_fee}
                    competition_arrivals.append(arrival_info)
                else:
                    print(f"Player {arrival['name']} has no stats for competition {competition_id}")
            else:
                print(f"Player {arrival['name']} has no stats")

    competition_arrivals_df = pd.DataFrame(competition_arrivals)

    result_df = competition_arrivals_df.groupby('club_name').agg({
        'pct_minutes_played': 'mean',  # Average percentage of minutes played
        'player_name': 'count',  # Count of players
        'player_age': 'mean',  # Average age of players
        'euro_minutes_played': 'sum',  # Sum of Eurominutes
        'fee': 'sum'  # Sum of fees
    }).reset_index()
    result_df['weighted_pct_played'] = result_df['euro_minutes_played'] / result_df['fee']

    competition_arrivals_df.to_csv(f'{competition_id}_competition_arrivals.csv', index=False)
    result_df.to_csv(f'{competition_id}_competition_summary.csv', index=False)
