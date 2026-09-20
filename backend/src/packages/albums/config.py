from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class AlbumsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # How many days an album lives without a new photo, counted from its
    # last one -- or its creation, until it has one (album-retention
    # spec). Declared here, in this capability's own package, rather
    # than beside the other two caps in `photos.config`: the rule is
    # album-retention's alone (proposal's Modified Capabilities), and
    # unlike those two, lowering it does not merely block new albums --
    # it expires ones that already exist the instant the new value
    # takes effect (D1 in album-retention's design). Whoever lowers it
    # SHALL know that before doing so, not after.
    #
    # A `float`, not an `int`: the product's own value is always a
    # whole number of days, but task 6.1 verifies a real expiry, not a
    # simulated one, and that needs the plazo down at a couple of
    # minutes for the verification to finish in a reasonable time --
    # 1/720 of a day, not expressible as a whole one.
    album_retention_days: float = 30


albums_settings = AlbumsSettings()  # type: ignore[call-arg]

# Without a max, the only ceiling on either field was whatever body the
# entry point accepts -- a number nobody chose for this, and one that
# travels back on every album listing (album-management spec, harden-
# local-profile task 1.5). Holdover values, generous for the product and
# bounded against abuse -- fixed, not configurable: nothing about an
# environment makes a longer title or description legitimate.
ALBUM_TITLE_MAX_LENGTH = 200
ALBUM_DESCRIPTION_MAX_LENGTH = 2000
