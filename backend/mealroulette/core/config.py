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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
