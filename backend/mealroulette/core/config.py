from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://mealroulette:mealroulette@localhost:5432/mealroulette"
    test_database_url: str = (
        "postgresql+psycopg://mealroulette:mealroulette@localhost:5432/mealroulette_test"
    )
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"
    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
