import pytest
from fastapi import HTTPException
from schema import And, Optional, Or, Regex, Schema

from app.services.players.absences import TransfermarktPlayerAbsences


def test_get_player_absences_not_found():
    with pytest.raises(HTTPException):
        TransfermarktPlayerAbsences(player_id="0")


@pytest.mark.parametrize(
    "player_id,page_number",
    [("25557", 1), ("25557", 999), ("3373", 1)],
)
def test_get_player_absences(player_id, page_number, len_greater_than_0, regex_integer):
    tfmkt = TransfermarktPlayerAbsences(player_id=player_id, page_number=page_number)
    result = tfmkt.get_player_absences()

    # Dates on the suspensions/absences table are rendered as DD/MM/YYYY.
    regex_date_dd_mm_yyyy = Regex(r"^(\d{2}/\d{2}/\d{4})$")

    expected_schema = Schema(
        {
            "id": And(str, regex_integer),
            "pageNumber": int,
            "lastPageNumber": int,
            "absences": [
                {
                    "season": And(str, len_greater_than_0),
                    "reason": And(str, len_greater_than_0),
                    Optional("competition"): str,
                    Optional("competitionId"): Or(str, None),
                    "fromDate": And(str, regex_date_dd_mm_yyyy),
                    Optional("untilDate"): str,
                    Optional("days"): str,
                    Optional("gamesMissed"): str,
                    "gamesMissedClubs": [str],
                },
            ],
        },
        ignore_extra_keys=True,
    )

    assert expected_schema.validate(result)
