from datetime import timedelta

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class PhotosSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # A product constraint, not a resource quota.
    album_max_photos: int = 50

    # Fits 51 times in the instance limit below, so no one account can get
    # close to the shared ceiling on its own.
    account_max_bytes: int = 120 * 1024 * 1024  # 120 MiB

    # Under R2's 10 GB free tier, with room for objects the database has
    # stopped counting until the maintenance command discards them.
    instance_max_bytes: int = 6 * 1024 * 1024 * 1024  # 6 GiB


photos_settings = PhotosSettings()  # type: ignore[call-arg]

# The product's own contract, not an environment's.
MAX_BATCH_SIZE = 50
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MiB
ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
UPLOAD_GRANT_TTL = timedelta(minutes=15)

# A declared dimension is a presentation hint, never used for authorization
# or storage -- but a hostile value should still not pass for a real one.
MAX_DIMENSION = 20_000
