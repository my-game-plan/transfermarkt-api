import re
from dataclasses import dataclass
from typing import Optional

from app.services.base import TransfermarktBase
from app.utils.regex import REGEX_DOB
from app.utils.utils import extract_from_url, parse_day_first_date, safe_regex, trim
from app.utils.xpath import Staff

REGEX_ASSISTANT_GAMES = r"\((?P<games>\d+) Games?\)"


@dataclass
class TransfermarktStaffProfile(TransfermarktBase):
    """
    A class for retrieving and parsing a staff member's profile and full career from Transfermarkt.

    One request covers both: the career page (/stationen/) carries the same profile header as the
    profile page, so identity and history come from the same document. A staff member is anyone with
    a trainer page, from head coach to physiotherapist.

    Args:
        staff_id (str): The Transfermarkt trainer id of the staff member.
        URL (str): The URL template for the staff member's career page on Transfermarkt.
    """

    staff_id: str = None
    URL: str = "https://www.transfermarkt.com/-/stationen/trainer/{staff_id}"

    def __post_init__(self) -> None:
        """Initialize the TransfermarktStaffProfile class."""
        self.URL = self.URL.format(staff_id=self.staff_id)
        self.page = self.request_url_page()
        self.raise_exception_if_not_found(xpath=Staff.Profile.ID)

    def __parse_name(self) -> dict:
        """
        Parse the name from the profile header, where the last name is the bold part.

        Returns:
            dict: The keys 'name', 'firstName' and 'lastName'.
        """
        headline = self.page.xpath(Staff.Profile.HEADLINE)
        if not headline:
            return {"name": None, "firstName": None, "lastName": None}
        last_name = trim(" ".join(headline[0].xpath(".//strong//text()"))) or None
        name = re.sub(r"\s+", " ", trim(" ".join(headline[0].xpath(".//text()")))) or None
        first_name = None
        if name and last_name and name.endswith(last_name):
            first_name = trim(name[: -len(last_name)]) or None
        return {"name": name, "firstName": first_name, "lastName": last_name}

    def __parse_profile(self) -> dict:
        """
        Parse the profile header: identity, citizenship, licence and the current club.

        Returns:
            dict: The profile fields.
        """
        dob_age = self.get_text_by_xpath(Staff.Profile.DOB_AGE)
        player_url = self.get_text_by_xpath(Staff.Profile.PLAYER_URL)
        return {
            **self.__parse_name(),
            "dateOfBirth": parse_day_first_date(safe_regex(dob_age, REGEX_DOB, "dob")),
            "placeOfBirth": self.get_text_by_xpath(Staff.Profile.PLACE_OF_BIRTH),
            "citizenship": self.get_list_by_xpath(Staff.Profile.CITIZENSHIP),
            "coachingLicence": self.get_text_by_xpath(Staff.Profile.COACHING_LICENCE),
            "playerId": extract_from_url(player_url) if player_url else None,
            "currentClubId": extract_from_url(self.get_text_by_xpath(Staff.Profile.CURRENT_CLUB_URL)),
            "currentClubName": self.get_text_by_xpath(Staff.Profile.CURRENT_CLUB_NAME),
            "currentRole": self.get_text_by_xpath(Staff.Profile.CURRENT_ROLE),
        }

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

    def __parse_assistant_of(self, row) -> list[dict]:
        """
        Parse the "... of:" row naming the managers an assistant worked under.

        Args:
            row: The extra row following an appointment.

        Returns:
            list[dict]: One dictionary per manager with 'id', 'name' and 'games'.
        """
        managers = []
        for link in row.xpath(Staff.History.ASSISTANT_OF):
            tail = link.tail or ""
            managers.append(
                {
                    "id": extract_from_url(link.get("href")),
                    "name": link.get("title") or trim(link.text or ""),
                    "games": safe_regex(tail, REGEX_ASSISTANT_GAMES, "games"),
                },
            )
        return managers

    def __parse_history(self) -> list[dict]:
        """
        Parse every appointment of the career, newest first as Transfermarkt lists them.

        Returns:
            list[dict]: One dictionary per appointment with the club, role, dates, matches,
                points per match and the managers an assistant worked under.
        """
        history = []
        for row in self.page.xpath(Staff.History.ROWS):
            if row.xpath(Staff.History.IS_EXTRA):
                if history:
                    history[-1]["assistantOf"] = self.__parse_assistant_of(row)
                continue
            matches = self.__text(row, Staff.History.MATCHES)
            history.append(
                {
                    "clubId": extract_from_url(self.__text(row, Staff.History.CLUB_URL)),
                    "clubName": self.__text(row, Staff.History.CLUB_NAME),
                    "role": self.__text(row, Staff.History.ROLE),
                    "appointed": parse_day_first_date(self.__text(row, Staff.History.APPOINTED)),
                    "until": parse_day_first_date(self.__text(row, Staff.History.UNTIL)),
                    "matches": matches if matches and matches.isdigit() else None,
                    "ppm": self.__text(row, Staff.History.PPM),
                    "assistantOf": [],
                },
            )
        return history

    def get_staff_profile(self) -> dict:
        """
        Retrieve and parse the staff member's profile and career.

        Returns:
            dict: The profile fields, the career under 'history', and the timestamp of when the
                data was last updated.
        """
        self.response["id"] = self.staff_id
        self.response.update(self.__parse_profile())
        self.response["history"] = self.__parse_history()

        return self.response
