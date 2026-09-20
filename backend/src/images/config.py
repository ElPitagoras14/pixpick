from typing import Literal

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class ImagesSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # Extended with each provider this project adds. An unrecognized value
    # fails startup naming the accepted ones instead of surfacing on the
    # first request for a variant.
    image_provider: Literal["local", "imagekit"]

    # Hex-encoded, matching IMGPROXY_KEY/IMGPROXY_SALT on the transformer
    # service (compose.yaml): the same pair signs on this side and verifies
    # on that one. Optional here -- required only when `image_provider` is
    # "local", enforced by the factory, the same shape as identity's own
    # credentials.
    image_signing_key: str | None = None
    image_signing_salt: str | None = None

    # ImageKit's own account address and private key, used to build and sign
    # every variant address (no network call) -- required only when
    # `image_provider` is "imagekit".
    imagekit_url_endpoint: str | None = None
    imagekit_private_key: str | None = None


images_settings = ImagesSettings()  # type: ignore[call-arg]
