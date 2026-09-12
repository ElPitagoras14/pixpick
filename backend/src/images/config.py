from typing import Literal

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class ImagesSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # Extended with each provider this project adds. An unrecognized value
    # fails startup naming the accepted ones (image-delivery spec) instead
    # of surfacing on the first request for a variant.
    image_provider: Literal["local"]

    # Hex-encoded, matching IMGPROXY_KEY/IMGPROXY_SALT on the transformer
    # service (compose.yaml): the same pair signs on this side and
    # verifies on that one.
    image_signing_key: str
    image_signing_salt: str


images_settings = ImagesSettings()  # type: ignore[call-arg]
