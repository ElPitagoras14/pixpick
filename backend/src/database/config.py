from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # The single connection string the app needs (D7): host, port,
    # credentials and database name all travel together in one value.
    database_url: str

    # Three ceilings a connection carries into every session it opens
    # (database-access spec, harden-local-profile): without them, one
    # query with no cap of its own -- the instance quota's own full-table
    # scan under a global lock is the concrete case that makes this
    # reachable -- can hold its connection, and the lock behind it,
    # forever. Milliseconds, because that is the unit Postgres's own GUCs
    # take. Held comfortably above the slowest legitimate case observed
    # so far (the full-table scan), not derived from it: the periodic
    # cleanup this same change adds (task 5.2) is what keeps that case
    # from growing without bound in the first place.
    statement_timeout_ms: int = 30_000
    lock_timeout_ms: int = 5_000
    idle_in_transaction_timeout_ms: int = 60_000


database_settings = DatabaseSettings()  # type: ignore[call-arg]
