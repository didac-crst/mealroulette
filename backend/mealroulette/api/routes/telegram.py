from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_admin
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.telegram import (
    TelegramSendResult,
    TelegramSettingsPublic,
    TelegramSettingsUpdateRequest,
    TelegramSubscriberPublic,
)
from mealroulette.services.telegram_reminder import TelegramReminderService
from mealroulette.services.telegram_settings import TelegramSettingsService
from mealroulette.services.telegram_subscribers import TelegramSubscriberService

router = APIRouter(tags=["telegram"])


@router.get("/telegram/settings", response_model=TelegramSettingsPublic)
def get_telegram_settings(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TelegramSettingsPublic:
    return TelegramSettingsService(db).get_public()


@router.get("/telegram/subscribers", response_model=list[TelegramSubscriberPublic])
def list_telegram_subscribers(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[TelegramSubscriberPublic]:
    return TelegramSubscriberService(db).list_public()


@router.put("/telegram/settings", response_model=TelegramSettingsPublic)
def update_telegram_settings(
    payload: TelegramSettingsUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TelegramSettingsPublic:
    return TelegramSettingsService(db).update(payload)


@router.post("/telegram/test", response_model=TelegramSendResult)
def send_telegram_test(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TelegramSendResult:
    return TelegramReminderService(db).send_test_message()


@router.post("/telegram/send-daily-reminder", response_model=TelegramSendResult)
def send_daily_telegram_reminder(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TelegramSendResult:
    return TelegramReminderService(db).send_daily_reminder()
