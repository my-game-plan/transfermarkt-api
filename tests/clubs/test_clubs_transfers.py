from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from schema import And, Or, Schema

from app.services.clubs.transfers import TransfermarktClubTransfers


def test_get_club_transfers_not_found():
    with pytest.raises(HTTPException):
        TransfermarktClubTransfers(club_id="0")


@pytest.mark.parametrize("club_id,season_id", [("418", None), ("131", "2014"), ("210", "2017")])
@patch("app.utils.utils.clean_response", side_effect=lambda x: x)
def test_get_club_transfers(
    mock_clean_response,
    club_id,
    season_id,
    regex_date_mmm_dd_yyyy,
    regex_integer,
    regex_height,
    regex_market_value,
    len_greater_than_0,
):
    tfmkt = TransfermarktClubTransfers(club_id=club_id, season_id=season_id)
    result = tfmkt.get_club_transfers()

    expected_schema = Schema(
        {
            "id": And(str, len_greater_than_0),
            "transfers": [
                {
                    "id": And(str, len_greater_than_0),
                    "name": And(str, len_greater_than_0),
                    "fee": Or(None, And(str, regex_market_value)),
                },
            ],
            "updatedAt": datetime,
        },
    )

    assert expected_schema.validate(result)
