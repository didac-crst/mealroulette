from __future__ import annotations

from mealroulette.core.config import get_settings
from mealroulette.services.telegram_client import TelegramApiError, TelegramClient

_username_cache: dict[str, str] = {}


def resolve_bot_username(token: str, client: TelegramClient | None = None) -> str | None:
    token = token.strip()
    if not token:
        return None

    configured = (get_settings().telegram_bot_username or "").strip().lstrip("@")
    if configured:
        return configured

    cached = _username_cache.get(token)
    if cached:
        return cached

    api_client = client or TelegramClient()
    try:
        me = api_client.get_me(token)
    except TelegramApiError:
        return None

    username = me.get("username")
    if isinstance(username, str) and username.strip():
        normalized = username.strip().lstrip("@")
        _username_cache[token] = normalized
        return normalized
    return None
