import re
from dataclasses import dataclass
from datetime import datetime

from app.services.base import TransfermarktBase
from app.utils.regex import REGEX_DOB
from app.utils.utils import clean_response, extract_from_url, safe_regex
from app.utils.xpath import Clubs


@dataclass
class TransfermarktClubTransfers(TransfermarktBase):
    """
    A class for retrieving and parsing the transfers of a football club from Transfermarkt.

    Args:
        club_id (str): The unique identifier of the football club.
        season_id (str): The unique identifier of the season.
        URL (str): The URL template for the club's transfers page on Transfermarkt.
    """

    club_id: str = None
    season_id: str = None
    URL: str = "https://www.transfermarkt.com/-/transfers/verein/{club_id}/saison_id/{season_id}/plus/1"

    def __post_init__(self) -> None:
        """Initialize the TransfermarktClubTransfers class."""
        self.URL = self.URL.format(club_id=self.club_id, season_id=self.season_id)
        self.page = self.request_url_page()
        self.raise_exception_if_not_found(xpath=Clubs.Players.CLUB_NAME)
        self.__update_season_id()

    def __update_season_id(self):
        """Update the season ID if it's not provided by extracting it from the website."""
        if self.season_id is None:
            self.season_id = extract_from_url(self.get_text_by_xpath(Clubs.Players.CLUB_URL), "season_id")

    def __parse_club_transfers(self, xpath_prefix: str) -> list[dict]:
        """
        Parse transfer information from the webpage and return a list of dictionaries, each representing a transfer.

        Returns:
            list[dict]: A list of transfer information dictionaries.
        """
        players_ids = [self._extract_id_from_href(href) for href in self.get_list_by_xpath(xpath_prefix + Clubs.Transfers.IDS)]
        players_names = self.get_list_by_xpath(xpath_prefix + Clubs.Transfers.NAMES)
        ages = self.get_list_by_xpath(xpath_prefix + Clubs.Transfers.AGES)
        # market_values = self.get_list_by_xpath(Clubs.Transfers.MARKET_VALUES)
        lefts_xpath = xpath_prefix + Clubs.Transfers.LEFTS_CLUB + " | " + xpath_prefix + Clubs.Transfers.LEFTS_RETIRED
        lefts = self.get_list_by_xpath(lefts_xpath)
        fees = self.get_list_by_xpath(xpath_prefix + Clubs.Transfers.FEES)

        assert len(players_ids) == len(players_names) == len(ages) == len(lefts) == len(fees)

        return [
            {
                "id": idx,
                "name": name,
                "age": age,
                # "marketValue": market_value,
                "left": left,
                "fee": fee,
            }
            for idx, name, age, left, fee in zip(  # noqa: E501
                players_ids,
                players_names,
                ages,
                # market_values,
                lefts,
                fees,
            )
        ]

    def get_club_transfers(self) -> dict:
        """
        Retrieve and parse player information for the specified football club.

        Returns:
            dict: A dictionary containing the club's unique identifier, player information, and the timestamp of when
                  the data was last updated.
        """
        self.response["id"] = self.club_id
        self.response["arrivals"] = self.__parse_club_transfers("//div[h2[contains(text(), 'Arrivals')]]")
        self.response["departures"] = self.__parse_club_transfers("//div[h2[contains(text(), 'Departures')]]")
        self.response["updatedAt"] = datetime.now()

        return clean_response(self.response)

    @staticmethod
    def _extract_id_from_href(href: str) -> str:
        """
        Extract the player ID from the href attribute of an anchor tag.

        Args:
            href (str): The href attribute of an anchor tag.

        Returns:
            str: The extracted player ID.
        """
        return re.search(r'/profil/spieler/(\d+)', href).group(1)
