from typing import Literal

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class StorageSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # Extended with each provider this project adds. An unrecognized value
    # fails startup naming the accepted ones (object-storage spec) instead
    # of surfacing on the first upload attempt. Everything below is
    # grouped by provider and optional here -- only the group the active
    # value names is required, enforced by the factory (same shape as
    # `identity`'s own credentials) rather than by these types, since a
    # `Literal` field can't say "required only for one value".
    storage_provider: Literal["local", "r2"]

    # MinIO's own admin/root credentials, used for local development only
    # -- the same relationship POSTGRES_USER/PASSWORD have with Postgres,
    # since there's no separate scoped user in local mode.
    minio_access_key_id: str | None = None
    minio_secret_access_key: str | None = None
    minio_bucket: str | None = None

    # Two addresses for the same storage (D4 in
    # add-media-ports-and-local-adapters): the one the browser can reach,
    # used to sign upload grants, and the one the server reaches, used to
    # query and delete objects -- genuinely two values for MinIO, unlike
    # R2 below (D7 in add-cloud-media-adapters).
    minio_browser_endpoint: str | None = None
    minio_server_endpoint: str | None = None

    # An R2 API token's key pair, scoped to this project's bucket.
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket: str | None = None

    # A single address, not two (D7): R2 is public from every side, so
    # the browser and the server reach it the same way -- one field says
    # so directly, instead of two that would always have to agree.
    r2_endpoint: str | None = None


storage_settings = StorageSettings()  # type: ignore[call-arg]
