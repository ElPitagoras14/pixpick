from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env" -- see src/config.py's _ENV_FILE for why.
_ENV_FILE = find_dotenv(usecwd=False)


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # The single connection string the app needs (D7): host, port,
    # credentials and database name all travel together in one value.
    database_url: str


database_settings = DatabaseSettings()  # type: ignore[call-arg]
