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


photos_settings = PhotosSettings()  # type: ignore[call-arg]

# The product's own contract, not something that should vary between
# environments (proposal's Impact) -- fixed constants, not settings.
MAX_BATCH_SIZE = 50
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MiB
ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
UPLOAD_GRANT_TTL = timedelta(minutes=15)
