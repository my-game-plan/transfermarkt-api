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
        self.raise_exception_if_not_found(xpath=Clubs.Transfers.CLUB_NAME)
        self.__update_season_id()

    def __update_season_id(self):
        """Update the season ID if it's not provided by extracting it from the website."""
        if self.season_id is None:
            self.season_id = extract_from_url(self.get_text_by_xpath(Clubs.Players.CLUB_URL), "season_id")

    def __parse_club_transfers(self) -> list[dict]:
        """
        Parse transfer information from the webpage and return a list of dictionaries, each representing a transfer.

        Returns:
            list[dict]: A list of transfer information dictionaries.
        """
        # page_nationalities = self.page.xpath(Clubs.Players.PAGE_NATIONALITIES)
        # page_players_infos = self.page.xpath(Clubs.Players.PAGE_INFOS)
        # page_players_signed_from = self.page.xpath(
        #     Clubs.Players.Past.PAGE_SIGNED_FROM if self.past else Clubs.Players.Present.PAGE_SIGNED_FROM,
        # )
        players_ids = [extract_from_url(url) for url in self.get_list_by_xpath(Clubs.Players.URLS)]
        players_names = self.get_list_by_xpath(Clubs.Players.NAMES)
        # players_positions = self.get_list_by_xpath(Clubs.Players.POSITIONS)
        # players_dobs = [
        #     safe_regex(dob_age, REGEX_DOB, "dob") for dob_age in self.get_list_by_xpath(Clubs.Players.DOB_AGE)
        # ]
        # players_ages = [
        #     safe_regex(dob_age, REGEX_DOB, "age") for dob_age in self.get_list_by_xpath(Clubs.Players.DOB_AGE)
        # ]
        # players_nationalities = [nationality.xpath(Clubs.Players.NATIONALITIES) for nationality in page_nationalities]
        # players_signed_from = ["; ".join(e.xpath(Clubs.Players.SIGNED_FROM)) for e in page_players_signed_from]

        return [
            {
                "id": idx,
                "name": name,
                # "position": position,
                # "dateOfBirth": dob,
                # "age": age,
            }
            for idx, name, in zip(  # noqa: E501
                players_ids,
                players_names,
                # players_positions,
                # players_dobs,
                # players_ages,
                # players_nationalities,
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
        self.response["transfers"] = self.__parse_club_transfers()
        self.response["updatedAt"] = datetime.now()

        return clean_response(self.response)
