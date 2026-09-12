from typing import Literal

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class IdentitySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # Extended with each provider this project adds. An unrecognized
    # value fails startup naming the accepted ones (identity-provider
    # spec) instead of surfacing on the first login attempt.
    identity_provider: Literal["local"]


identity_settings = IdentitySettings()  # type: ignore[call-arg]
