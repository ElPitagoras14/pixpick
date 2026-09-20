from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # The single connection string the app needs: host, port, credentials
    # and database name all travel together in one value.
    database_url: str


database_settings = DatabaseSettings()  # type: ignore[call-arg]

# Three ceilings every session opens with. Without them one uncapped query
# -- the instance quota's full-table scan under a global lock is the case
# that makes this reachable -- holds its connection, and the lock behind
# it, forever. Held well above the slowest legitimate case rather than
# derived from it.
STATEMENT_TIMEOUT_MS = 30_000
LOCK_TIMEOUT_MS = 5_000
IDLE_IN_TRANSACTION_TIMEOUT_MS = 60_000
