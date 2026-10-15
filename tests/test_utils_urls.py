import pytest

from app.utils.utils import extract_from_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("/club-brugge-kv/startseite/verein/2282", "2282"),
        ("/ivan-leko/profil/trainer/34157", "34157"),
        # An unemployed coach's "Without Club" link is not an entity.
        ("/trainer/verfuegbaretrainer/statistik", None),
        ("", None),
        (None, None),
    ],
)
def test_extract_from_url(url, expected):
    assert extract_from_url(url) == expected
