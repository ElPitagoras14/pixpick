from typing import Literal

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Not ".env": in native mode the process runs from backend/, but the single
# .env this project uses lives at the repo root. find_dotenv() walks up from
# this file's directory until it finds one. Inside the container image it
# finds nothing and returns "" -- harmless, since compose sets these
# variables directly there and a missing env_file is just skipped.
_ENV_FILE = find_dotenv(usecwd=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    environment: Literal["development", "production"]


settings = Settings()  # type: ignore[call-arg]
