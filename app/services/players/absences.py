from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from app.services.base import TransfermarktBase
from app.utils.utils import extract_from_url, trim
from app.utils.xpath import Players


@dataclass
class TransfermarktPlayerAbsences(TransfermarktBase):
    """
    Represents a service for retrieving and parsing the suspensions and absences of a football
    player on Transfermarkt (the "/ausfaelle/" page: red-card bans, yellow-card bans, other
    suspensions and non-disciplinary absences such as national-team call-ups).

    Args:
        player_id (str): The unique identifier of the player.
        page_number (int): The page number of the player's absences history.

    Attributes:
        URL (str): The URL to fetch the player's absences data.
    """

    player_id: str = None
    URL: str = "https://www.transfermarkt.com/player/ausfaelle/spieler/{player_id}/plus/1/page/{page_number}"
    page_number: int = 1

    def __post_init__(self):
        """Initialize the TransfermarktPlayerAbsences class."""
        self.URL = self.URL.format(player_id=self.player_id, page_number=self.page_number)
        self.page = self.request_url_page()
        self.raise_exception_if_not_found(xpath=Players.Profile.URL)

    @staticmethod
    def __competition_id_from_logo(logo_url: Optional[str]) -> Optional[str]:
        """
        Derive the Transfermarkt competition id from the competition logo URL. The absences
        table exposes no competition link, but the logo filename is the competition code,
        e.g. "https://.../images/logo/tiny/es1.png?lm=..." -> "ES1".
        """
        if not logo_url:
            return None
        filename = logo_url.split("/")[-1].split("?")[0]
        code = filename.rsplit(".", 1)[0]
        return code.upper() or None

    def __parse_player_absences(self) -> Optional[List[dict]]:
        """
        Parse the suspensions and absences of a football player from the retrieved data.

        Returns:
            list: A list of dictionaries, where each dictionary represents a suspension/absence.
                Each dictionary contains keys 'season', 'reason', 'competition', 'competitionId',
                'fromDate', 'untilDate', 'days', 'gamesMissed' and 'gamesMissedClubs'. Dates are
                kept as the raw "DD/MM/YYYY" strings returned by Transfermarkt.
        """
        absences: ElementTree = self.page.xpath(Players.Absences.RESULTS)
        player_absences = []

        for absence in absences:
            season = trim(absence.xpath(Players.Absences.SEASONS))
            reason = trim(absence.xpath(Players.Absences.REASON))
            competition = trim(absence.xpath(Players.Absences.COMPETITION))
            competition_logo = trim(absence.xpath(Players.Absences.COMPETITION_LOGO))
            competition_id = self.__competition_id_from_logo(competition_logo)
            date_from = trim(absence.xpath(Players.Absences.FROM))
            date_until = trim(absence.xpath(Players.Absences.UNTIL))
            days = trim(absence.xpath(Players.Absences.DAYS))
            games_missed = trim(absence.xpath(Players.Absences.GAMES_MISSED))
            games_missed_clubs_urls = absence.xpath(Players.Absences.GAMES_MISSED_CLUBS_URLS)
            games_missed_clubs_ids = [extract_from_url(club_url) for club_url in games_missed_clubs_urls]

            player_absences.append(
                {
                    "season": season,
                    "reason": reason,
                    "competition": competition,
                    "competitionId": competition_id,
                    "fromDate": date_from,
                    "untilDate": date_until,
                    "days": days,
                    "gamesMissed": games_missed,
                    "gamesMissedClubs": games_missed_clubs_ids,
                },
            )

        return player_absences

    def get_player_absences(self) -> dict:
        """
        Retrieve and parse the suspensions and absences of a football player.

        Returns:
            dict: A dictionary containing the player's unique identifier, current page number,
                last page number, and absences history.
        """
        self.response["id"] = self.player_id
        self.response["pageNumber"] = self.page_number
        self.response["lastPageNumber"] = self.get_last_page_number()
        self.response["absences"] = self.__parse_player_absences()

        return self.response
