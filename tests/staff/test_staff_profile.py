import pytest
from fastapi import HTTPException
from schema import And, Or, Regex, Schema

from app.services.staff.profile import TransfermarktStaffProfile

ISO_DATE = Regex(r"^\d{4}-\d{2}-\d{2}$")


def test_get_staff_profile_not_found():
    with pytest.raises(HTTPException):
        TransfermarktStaffProfile(staff_id="0")


@pytest.mark.parametrize("staff_id", ["3", "47535", "131333"])
def test_get_staff_profile(staff_id, len_greater_than_0):
    tfmkt = TransfermarktStaffProfile(staff_id=staff_id)
    result = tfmkt.get_staff_profile()

    expected_schema = Schema(
        {
            "id": And(str, len_greater_than_0),
            "name": And(str, len_greater_than_0),
            "firstName": Or(None, str),
            "lastName": And(str, len_greater_than_0),
            "dateOfBirth": Or(None, ISO_DATE),
            "placeOfBirth": Or(None, str),
            "citizenship": [str],
            "coachingLicence": Or(None, str),
            "playerId": Or(None, And(str, str.isdigit)),
            "currentClubId": Or(None, str),
            "currentClubName": Or(None, str),
            "currentRole": Or(None, str),
            "history": [
                {
                    "clubId": Or(None, str),
                    "clubName": Or(None, str),
                    "role": Or(None, str),
                    "appointed": Or(None, ISO_DATE),
                    "until": Or(None, ISO_DATE),
                    "matches": Or(None, And(str, str.isdigit)),
                    "ppm": Or(None, str),
                    "assistantOf": [{"id": Or(None, str), "name": Or(None, str), "games": Or(None, str)}],
                },
            ],
        },
    )

    assert expected_schema.validate(result)
    assert len(result["history"]) > 0
