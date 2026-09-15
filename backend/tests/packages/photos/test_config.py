"""The two limits granting evaluates come from the environment, not from
the code (account-quota spec, photo-upload spec): changing either one
SHALL NOT require editing anything here.
"""

from src.packages.photos.config import PhotosSettings

_150_MIB = 150 * 1024 * 1024


def test_the_account_limit_defaults_to_150_mib():
    """`_env_file=None` on purpose: the repository's own `.env` declares
    this variable, and the point here is what the code falls back to when
    an environment doesn't.
    """
    assert PhotosSettings(_env_file=None).account_max_bytes == _150_MIB


def test_the_account_limit_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("ACCOUNT_MAX_BYTES", str(10 * 1024 * 1024))

    assert PhotosSettings(_env_file=None).account_max_bytes == 10 * 1024 * 1024


def test_the_album_maximum_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("ALBUM_MAX_PHOTOS", "7")

    assert PhotosSettings(_env_file=None).album_max_photos == 7
