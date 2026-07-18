from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_SECRETS = frozenset(
    {
        "",
        "change-me-in-production",
        "change-me-in-production-use-a-long-random-secret",
    }
)

# Prefer process env; also load repo-root and CWD .env for local runs from backend/.
_REPO_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT_ENV, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://mealroulette:mealroulette@localhost:5432/mealroulette"
    test_database_url: str = (
        "postgresql+psycopg://mealroulette:mealroulette@localhost:5432/mealroulette_test"
    )
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    # Required. Do not ship a usable default — reject missing/placeholder values.
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"
    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None

    @field_validator("secret_key")
    @classmethod
    def reject_placeholder_secret_key(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned in _PLACEHOLDER_SECRETS or cleaned.lower().startswith("change-me"):
            raise ValueError(
                "SECRET_KEY must be set to a strong non-placeholder value "
                "(at least 32 bytes). Generate one, e.g. `python -c "
                "\"import secrets; print(secrets.token_urlsafe(48))\"`."
            )
        if len(cleaned.encode("utf-8")) < 32:
            raise ValueError("SECRET_KEY must be at least 32 bytes for HS256")
        return cleaned


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
