from dataclasses import dataclass
from typing import Optional

from app.services.base import TransfermarktBase
from app.utils.utils import extract_from_url, parse_day_first_date, trim
from app.utils.xpath import Staff


@dataclass
class TransfermarktClubCoachHistory(TransfermarktBase):
    """
    A class for retrieving and parsing every head coach a football club has had on Transfermarkt.

    The page lists Manager and Caretaker Manager appointments in one table, newest first, back to the
    club's first recorded coach, on a single page. It names no role per row: a caretaker spell reads
    like any other. A coach who held the job twice appears twice. A person's Transfermarkt id is their
    trainer id, the id of /profil/trainer/.

    Args:
        club_id (str): The unique identifier of the football club.
        URL (str): The URL template for the club's coach history page on Transfermarkt.
    """

    club_id: str = None
    URL: str = "https://www.transfermarkt.com/-/mitarbeiterhistorie/verein/{club_id}"

    def __post_init__(self) -> None:
        """Initialize the TransfermarktClubCoachHistory class."""
        self.URL = self.URL.format(club_id=self.club_id)
        self.page = self.request_url_page()

    @staticmethod
    def __text(row, xpath: str) -> Optional[str]:
        """
        Return the trimmed text an XPath finds inside a row, or None for an empty cell or "-".

        Args:
            row: The table row element.
            xpath (str): The XPath relative to the row.

        Returns:
            Optional[str]: The joined text.
        """
        text = trim(" ".join(trim(v) for v in row.xpath(xpath) if trim(v)))
        return None if not text or text == "-" else text

    def __parse_row(self, row) -> Optional[dict]:
        """
        Parse one appointment from a row of the coach history table.

        Args:
            row: The table row element.

        Returns:
            Optional[dict]: The appointment, or None for a row without a trainer link.
        """
        url = self.__text(row, Staff.ClubHistory.URL)
        if not url or "/profil/trainer/" not in url:
            return None
        matches = self.__text(row, Staff.ClubHistory.MATCHES)
        return {
            "id": extract_from_url(url),
            "name": self.__text(row, Staff.ClubHistory.NAME),
            "dateOfBirth": parse_day_first_date(self.__text(row, Staff.ClubHistory.DATE_OF_BIRTH)),
            "citizenship": [trim(c) for c in row.xpath(Staff.ClubHistory.CITIZENSHIP) if trim(c)],
            "appointed": parse_day_first_date(self.__text(row, Staff.ClubHistory.APPOINTED)),
            "until": parse_day_first_date(self.__text(row, Staff.ClubHistory.UNTIL)),
            "matches": matches if matches and matches.isdigit() else None,
            "ppm": self.__text(row, Staff.ClubHistory.PPM),
        }

    def get_club_coach_history(self) -> dict:
        """
        Retrieve and parse every head coach appointment of the specified football club.

        Returns:
            dict: A dictionary containing the club's unique identifier, its coaches newest first,
                and the timestamp of when the data was last updated.
        """
        self.response["id"] = self.club_id
        self.response["coaches"] = [
            coach for coach in (self.__parse_row(row) for row in self.page.xpath(Staff.ClubHistory.ROWS)) if coach
        ]

        return self.response
