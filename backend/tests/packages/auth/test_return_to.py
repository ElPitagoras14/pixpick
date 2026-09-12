import pytest

from src.packages.auth.return_to import sanitize_return_to


@pytest.mark.parametrize(
    "value",
    [
        "//evil.example.com/phish",  # leading double slash
        "https://evil.example.com/phish",  # explicit scheme
        "javascript:alert(1)",  # script scheme
    ],
)
def test_a_site_evading_destination_is_discarded(value):
    assert sanitize_return_to(value) == "/home"


def test_none_uses_the_default():
    assert sanitize_return_to(None) == "/home"


def test_empty_uses_the_default():
    assert sanitize_return_to("") == "/home"


def test_a_same_site_path_is_kept():
    assert sanitize_return_to("/albums/42") == "/albums/42"
