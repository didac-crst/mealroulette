from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramApiError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _raise_for_response(response: httpx.Response, *, context: str) -> None:
    if response.status_code < 400:
        return
    detail = response.text
    try:
        body = response.json()
        detail = body.get("description", detail)
    except ValueError:
        pass
    raise TelegramApiError(f"Telegram API error: {detail}", status_code=response.status_code)


class TelegramClient:
    def __init__(self, *, timeout: float = 30.0) -> None:
        self._timeout = timeout

    def send_message(
        self,
        bot_token: str,
        chat_id: str,
        text: str,
        *,
        parse_mode: str | None = None,
    ) -> None:
        url = f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
        payload: dict[str, str] = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        try:
            response = httpx.post(url, json=payload, timeout=self._timeout)
        except httpx.HTTPError as exc:
            raise TelegramApiError(f"Telegram request failed: {exc}") from exc

        _raise_for_response(response, context="sendMessage")
        logger.info("Telegram message sent to chat %s", chat_id)

    def get_me(self, bot_token: str) -> dict:
        url = f"{TELEGRAM_API_BASE}/bot{bot_token}/getMe"
        try:
            response = httpx.get(url, timeout=self._timeout)
        except httpx.HTTPError as exc:
            raise TelegramApiError(f"Telegram getMe failed: {exc}") from exc

        _raise_for_response(response, context="getMe")
        body = response.json()
        if not body.get("ok"):
            raise TelegramApiError(body.get("description", "getMe failed"))
        result = body.get("result")
        if not isinstance(result, dict):
            raise TelegramApiError("getMe returned invalid payload")
        return result

    def get_updates(self, bot_token: str, *, offset: int | None = None, timeout: int = 25) -> list[dict]:
        url = f"{TELEGRAM_API_BASE}/bot{bot_token}/getUpdates"
        params: dict[str, int] = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        try:
            response = httpx.get(url, params=params, timeout=timeout + 5)
        except httpx.HTTPError as exc:
            raise TelegramApiError(f"Telegram getUpdates failed: {exc}") from exc

        _raise_for_response(response, context="getUpdates")
        body = response.json()
        if not body.get("ok"):
            raise TelegramApiError(body.get("description", "getUpdates failed"))
        result = body.get("result")
        return result if isinstance(result, list) else []
