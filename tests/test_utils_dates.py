import pytest

from app.utils.utils import parse_day_first_date


@pytest.mark.parametrize(
    "text,expected",
    [
        ("01/07/2026", "2026-07-01"),
        ("30.06.2028", "2028-06-30"),
        ("26/27 (01/07/2026)", "2026-07-01"),
        ("24/08/1986 (40)", "1986-08-24"),
        ("Jul 1, 2026", "2026-07-01"),
        ("-", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_day_first_date(text, expected):
    assert parse_day_first_date(text) == expected
