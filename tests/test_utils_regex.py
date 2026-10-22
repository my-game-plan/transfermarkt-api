import pytest

from app.utils.regex import REGEX_DOB
from app.utils.utils import safe_regex


@pytest.mark.parametrize(
    "text,dob,age",
    [
        # The player profile header, as Transfermarkt serves it since at least Oct 2026.
        ("30/01/2001 (25)", "30/01/2001", "25"),
        ("Jan 30, 2001 (25)", "Jan 30, 2001", "25"),
        ("N/A", None, None),
    ],
)
def test_regex_dob(text, dob, age):
    assert safe_regex(text, REGEX_DOB, "dob") == dob
    assert safe_regex(text, REGEX_DOB, "age") == age
