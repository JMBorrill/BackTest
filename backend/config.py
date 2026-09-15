"""Settings, read from environment variables.

API_TOKEN has no default and may not be empty. The app fails to start
without a usable one, rather than starting and rejecting every request.
"""
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class ConfigError(RuntimeError):
    """Configuration is missing - raised at startup, not mid-request."""


class Settings(BaseSettings):
    # env_ignore_empty so that API_TOKEN= (the state `cp .env.example .env`
    # leaves behind) is treated as unset rather than as a token of "".
    model_config = SettingsConfigDict(env_ignore_empty=True)

    api_token: str
    environment: str = "sandbox"
    data_dir: Path = Path("data")


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        missing = [
            ".".join(str(part) for part in error["loc"]).upper()
            for error in exc.errors()
            if error["type"] == "missing"
        ]
        raise ConfigError(
            f"Missing or empty environment variable(s): {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        ) from exc
