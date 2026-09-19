from datetime import timedelta

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class PhotosSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # A product constraint, not a resource quota (D14): rating an album
    # photo by photo stops being viable long before storage cost would.
    # Configurable, unlike everything below, because it's a product
    # decision that can reasonably change per environment, unlike the
    # shape of a batch request (proposal's Impact: the one new
    # environment variable this change adds).
    album_max_photos: int = 50

    # The other limit granting evaluates (account-quota spec), declared
    # beside it because the two are checked together and nowhere else.
    # In bytes rather than a friendlier unit: it's compared against a
    # file's own declared size, which arrives in bytes too, so any other
    # unit here would only move a conversion into the comparison.
    # 120 MiB (D6 in add-instance-quota): entering 51 times in the
    # instance limit below is the point, so that no single account can
    # get close to the shared ceiling on its own.
    account_max_bytes: int = 120 * 1024 * 1024  # 120 MiB

    # The third limit granting evaluates (instance-quota spec): the
    # instance's own total, the sum of every account's usage and not
    # derived from how many accounts exist (D6 in add-instance-quota).
    # 6 GiB leaves a deliberate margin under R2's 10 GB free tier, sized
    # to absorb objects the database stops counting -- an expired
    # grant's upload, or an orphan left by a failed delete -- before the
    # maintenance command that discards them ever runs.
    instance_max_bytes: int = 6 * 1024 * 1024 * 1024  # 6 GiB


photos_settings = PhotosSettings()  # type: ignore[call-arg]

# The product's own contract, not something that should vary between
# environments (proposal's Impact) -- fixed constants, not settings.
MAX_BATCH_SIZE = 50
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MiB
ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
UPLOAD_GRANT_TTL = timedelta(minutes=15)
