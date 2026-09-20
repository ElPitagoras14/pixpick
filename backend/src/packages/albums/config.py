from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class AlbumsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # Days an album lives without a new photo, counted from its last one or
    # from its creation. Unlike the two caps in `photos.config`, lowering
    # this expires albums that already exist, the instant it takes effect.
    #
    # A `float`, not an `int`, so a test can bring the window down to a
    # couple of minutes and watch a real expiry.
    album_retention_days: float = 30


albums_settings = AlbumsSettings()  # type: ignore[call-arg]

# Without a max, the only ceiling on either field was whatever body the
# entry point accepts -- a number nobody chose for this, and one that
# travels back on every album listing. Holdover values, generous for the
# product and bounded against abuse -- fixed, not configurable: nothing
# about an environment makes a longer title or description legitimate.
ALBUM_TITLE_MAX_LENGTH = 200
ALBUM_DESCRIPTION_MAX_LENGTH = 2000
