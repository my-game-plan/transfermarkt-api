import pytest
from schema import And, Or, Regex, Schema

from app.services.clubs.coach_history import TransfermarktClubCoachHistory

ISO_DATE = Regex(r"^\d{4}-\d{2}-\d{2}$")


@pytest.mark.parametrize("club_id", ["2282", "3225", "418"])
def test_get_club_coach_history(club_id, len_greater_than_0):
    tfmkt = TransfermarktClubCoachHistory(club_id=club_id)
    result = tfmkt.get_club_coach_history()

    expected_schema = Schema(
        {
            "id": And(str, len_greater_than_0),
            "coaches": [
                {
                    "id": And(str, str.isdigit),
                    "name": And(str, len_greater_than_0),
                    "dateOfBirth": Or(None, ISO_DATE),
                    "citizenship": [str],
                    "appointed": Or(None, ISO_DATE),
                    "until": Or(None, ISO_DATE),
                    "matches": Or(None, And(str, str.isdigit)),
                    "ppm": Or(None, str),
                },
            ],
        },
    )

    assert expected_schema.validate(result)
    # The page goes back to the club's first recorded coach, so a club with a history has many.
    assert len(result["coaches"]) > 10
    # Newest first, and the current coach has no end date.
    assert result["coaches"][0]["until"] is None
