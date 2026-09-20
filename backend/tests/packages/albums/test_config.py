"""The retention period comes from the environment, not from the code:
changing it SHALL NOT require editing anything here.
"""

from src.packages.albums.config import AlbumsSettings


def test_the_album_retention_defaults_to_30_days():
    """`_env_file=None` on purpose: the repository's own `.env` declares
    this variable, and the point here is what the code falls back to when
    an environment doesn't.
    """
    assert AlbumsSettings(_env_file=None).album_retention_days == 30


def test_the_album_retention_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("ALBUM_RETENTION_DAYS", "7")

    assert AlbumsSettings(_env_file=None).album_retention_days == 7
