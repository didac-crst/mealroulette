from mealroulette.core.config import Settings


def test_settings_defaults():
    settings = Settings()

    assert settings.api_port == 8000
    assert settings.debug is False
    assert "postgresql" in settings.database_url
