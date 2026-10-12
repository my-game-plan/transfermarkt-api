from dataclasses import dataclass
from typing import Optional

from app.services.base import TransfermarktBase
from app.utils.utils import extract_from_url, parse_day_first_date, trim
from app.utils.xpath import Staff


@dataclass
class TransfermarktClubStaff(TransfermarktBase):
    """
    A class for retrieving and parsing everyone on the staff page of a football club on Transfermarkt.

    Every section of the page is returned (Coaching Staff, Management, Board of Directors, Scouting,
    Youth, Medical department, Public Relations, Other), each person tagged with the section they
    are listed under. A person's Transfermarkt id is their trainer id, the id of /profil/trainer/.

    Args:
        club_id (str): The unique identifier of the football club.
        URL (str): The URL template for the club's staff page on Transfermarkt.
    """

    club_id: str = None
    URL: str = "https://www.transfermarkt.com/-/mitarbeiter/verein/{club_id}"

    def __post_init__(self) -> None:
        """Initialize the TransfermarktClubStaff class."""
        self.URL = self.URL.format(club_id=self.club_id)
        self.page = self.request_url_page()

    @staticmethod
    def __first(row, xpath: str) -> Optional[str]:
        """
        Return the first non-empty trimmed text an XPath finds inside a row.

        Args:
            row: The table row element.
            xpath (str): The XPath relative to the row.

        Returns:
            Optional[str]: The text, or None when nothing (or only "-") is there.
        """
        values = [trim(v) for v in row.xpath(xpath) if trim(v)]
        if not values or values[0] == "-":
            return None
        return values[0]

    def __parse_row(self, row, section: str) -> Optional[dict]:
        """
        Parse one person from a row of a staff section.

        Args:
            row: The table row element.
            section (str): The section the row is listed under.

        Returns:
            Optional[dict]: The person, or None for a row without a trainer link.
        """
        url = self.__first(row, Staff.Club.URL)
        if not url or "/profil/trainer/" not in url:
            return None
        age = self.__first(row, Staff.Club.AGE)
        return {
            "id": extract_from_url(url),
            "name": self.__first(row, Staff.Club.NAME),
            "section": section,
            "role": self.__first(row, Staff.Club.ROLE),
            "age": age if age and age.isdigit() else None,
            "citizenship": [trim(c) for c in row.xpath(Staff.Club.CITIZENSHIP) if trim(c)],
            "appointed": parse_day_first_date(self.__first(row, Staff.Club.APPOINTED)),
            "contractExpires": parse_day_first_date(self.__first(row, Staff.Club.CONTRACT_EXPIRES)),
            "lastClubId": extract_from_url(self.__first(row, Staff.Club.LAST_CLUB_URL)),
            "lastClubName": self.__first(row, Staff.Club.LAST_CLUB_NAME),
        }

    def __parse_club_staff(self) -> list[dict]:
        """
        Parse every person on the staff page, section by section.

        Returns:
            list[dict]: One dictionary per person and section. A person listed in two sections
                (an assistant who is also the U21 coach) appears twice, once per section.
        """
        staff = []
        for box in self.page.xpath(Staff.Club.BOXES):
            section = trim(box.xpath(Staff.Club.SECTION))
            for row in box.xpath(Staff.Club.ROWS):
                person = self.__parse_row(row, section)
                if person:
                    staff.append(person)
        return staff

    def get_club_staff(self) -> dict:
        """
        Retrieve and parse the staff of the specified football club.

        Returns:
            dict: A dictionary containing the club's unique identifier, its staff, and the timestamp
                of when the data was last updated.
        """
        self.response["id"] = self.club_id
        self.response["staff"] = self.__parse_club_staff()

        return self.response
