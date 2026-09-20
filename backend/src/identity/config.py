from typing import Literal

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class IdentitySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # Extended with each provider this project adds. An unrecognized value
    # fails startup naming the accepted ones instead of surfacing on the
    # first login attempt.
    identity_provider: Literal["local", "google"]

    # The application's credentials in Google's console. Optional here -- a
    # `Literal` field can't say "required only for one provider" -- so the
    # factory is what actually enforces their presence, and only for the
    # provider that's active.
    google_client_id: str | None = None
    google_client_secret: str | None = None


identity_settings = IdentitySettings()  # type: ignore[call-arg]
