import pytest
from schema import And, Or, Regex, Schema

from app.services.clubs.staff import TransfermarktClubStaff

ISO_DATE = Regex(r"^\d{4}-\d{2}-\d{2}$")


@pytest.mark.parametrize("club_id", ["2282", "3225", "418"])
def test_get_club_staff(club_id, len_greater_than_0):
    tfmkt = TransfermarktClubStaff(club_id=club_id)
    result = tfmkt.get_club_staff()

    expected_schema = Schema(
        {
            "id": And(str, len_greater_than_0),
            "staff": [
                {
                    "id": And(str, str.isdigit),
                    "name": And(str, len_greater_than_0),
                    "section": And(str, len_greater_than_0),
                    "role": Or(None, And(str, len_greater_than_0)),
                    "age": Or(None, And(str, str.isdigit)),
                    "citizenship": [str],
                    "appointed": Or(None, ISO_DATE),
                    "contractExpires": Or(None, ISO_DATE),
                    "lastClubId": Or(None, str),
                    "lastClubName": Or(None, str),
                },
            ],
        },
    )

    assert expected_schema.validate(result)
    assert "Coaching Staff" in {person["section"] for person in result["staff"]}
