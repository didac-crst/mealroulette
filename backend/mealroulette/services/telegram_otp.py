from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.core.config import get_settings
from mealroulette.models.telegram import TelegramLoginOtp
from mealroulette.models.user import User
from mealroulette.services.telegram_client import TelegramApiError, TelegramClient
from mealroulette.services.telegram_link import TelegramLinkService


def _hash_code(code: str) -> str:
    secret = get_settings().secret_key.encode("utf-8")
    return hmac.new(secret, code.encode("utf-8"), hashlib.sha256).hexdigest()


class TelegramOtpService:
    """One-time password login codes delivered to a linked Telegram chat."""

    OTP_TTL_MINUTES = 5
    OTP_DIGITS = 6
    REQUEST_COOLDOWN_SECONDS = 60
    GENERIC_DETAIL = (
        "If that account exists and has Telegram linked, a login code was sent. "
        "It expires in a few minutes."
    )

    def __init__(self, db: Session, client: TelegramClient | None = None) -> None:
        self.db = db
        self.client = client or TelegramClient()
        self.links = TelegramLinkService(db)

    def request_login_code(self, username: str) -> None:
        user = self.db.scalar(select(User).where(User.username == username))
        if user is None or not user.active:
            return
        link = self.links.get_link_for_user(user.id)
        token = (get_settings().telegram_bot_token or "").strip()
        if link is None or not token:
            return

        now = datetime.now(UTC)
        existing = self.db.scalar(
            select(TelegramLoginOtp).where(TelegramLoginOtp.user_id == user.id).with_for_update()
        )
        if (
            existing is not None
            and existing.used_at is None
            and existing.expires_at >= now
            and (now - existing.created_at).total_seconds() < self.REQUEST_COOLDOWN_SECONDS
        ):
            # Keep the existing unused code; do not resend or invalidate.
            self.db.commit()
            return

        code = f"{secrets.randbelow(10**self.OTP_DIGITS):0{self.OTP_DIGITS}d}"
        code_hash = _hash_code(code)
        expires_at = now + timedelta(minutes=self.OTP_TTL_MINUTES)
        if existing is not None:
            existing.code_hash = code_hash
            existing.expires_at = expires_at
            existing.used_at = None
            existing.created_at = now
        else:
            self.db.add(
                TelegramLoginOtp(
                    id=uuid4(),
                    user_id=user.id,
                    code_hash=code_hash,
                    expires_at=expires_at,
                    created_at=now,
                )
            )
        self.db.commit()

        message = (
            "MealRoulette login code\n\n"
            f"<code>{code}</code>\n\n"
            f"User: {user.username}\n"
            f"Expires in {self.OTP_TTL_MINUTES} minutes.\n"
            "If you did not request this, ignore the message."
        )
        try:
            self.client.send_message(token, link.chat_id, message, parse_mode="HTML")
        except TelegramApiError:
            # Keep generic client response; caller does not learn whether send failed.
            return

    def verify_login_code(self, username: str, code: str) -> User:
        user = self.db.scalar(select(User).where(User.username == username))
        if user is None or not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or code",
            )
        now = datetime.now(UTC)
        row = self.db.scalar(
            select(TelegramLoginOtp).where(TelegramLoginOtp.user_id == user.id).with_for_update()
        )
        if (
            row is None
            or row.used_at is not None
            or row.expires_at < now
            or not hmac.compare_digest(row.code_hash, _hash_code(code.strip()))
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or code",
            )
        row.used_at = now
        self.db.commit()
        return user
