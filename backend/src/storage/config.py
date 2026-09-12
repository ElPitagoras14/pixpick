from typing import Literal

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class StorageSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # Extended with each provider this project adds. An unrecognized value
    # fails startup naming the accepted ones (object-storage spec) instead
    # of surfacing on the first upload attempt.
    storage_provider: Literal["local"]

    storage_bucket: str

    # Two addresses for the same storage (D4): the one the browser can
    # reach, used to sign upload grants, and the one the server reaches,
    # used to query and delete objects. They coincide once a cloud
    # provider is public from both sides, but not in this local setup.
    storage_browser_endpoint: str
    storage_server_endpoint: str

    # The storage's own admin/root credentials, reused directly as the
    # access/secret key pair (there's no separate scoped user in local
    # mode) -- the same relationship POSTGRES_USER/PASSWORD have with
    # Postgres.
    storage_root_user: str
    storage_root_password: str


storage_settings = StorageSettings()  # type: ignore[call-arg]
