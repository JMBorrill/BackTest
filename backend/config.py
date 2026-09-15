"""Settings, read from environment variables.

There is no default for API_TOKEN. The app fails to start without it,
which is the point: a token with a fallback value is a token that reaches
production unchanged.
"""
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError
from pydantic_settings import BaseSettings

load_dotenv()


class ConfigError(RuntimeError):
    """Configuration is missing - raised at startup, not mid-request."""


class Settings(BaseSettings):
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
            f"Missing environment variable(s): {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        ) from exc
