from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import (
    HouseholdScope,
    get_current_household_admin,
    get_current_household_scope,
)
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.telegram import (
    TelegramSendResult,
    TelegramSettingsPublic,
    TelegramSettingsUpdateRequest,
    TelegramSubscriberPublic,
)
from mealroulette.services.telegram_link import TelegramLinkService
from mealroulette.services.telegram_reminder import TelegramReminderService
from mealroulette.services.telegram_settings import TelegramSettingsService

router = APIRouter(tags=["telegram"])


@router.get("/telegram/settings", response_model=TelegramSettingsPublic)
def get_telegram_settings(
    _admin: User = Depends(get_current_household_admin),
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> TelegramSettingsPublic:
    return TelegramSettingsService(db).get_public(scope.household_id)


@router.get("/telegram/subscribers", response_model=list[TelegramSubscriberPublic])
def list_telegram_subscribers(
    _admin: User = Depends(get_current_household_admin),
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> list[TelegramSubscriberPublic]:
    links = TelegramLinkService(db).list_linked_recipients(scope.household_id)
    return [
        TelegramSubscriberPublic(
            id=link.id,
            chat_id=link.chat_id,
            telegram_user_id=link.telegram_user_id,
            username=link.username,
            display_name=link.display_name,
            subscribed_at=link.linked_at,
        )
        for link in links
    ]


@router.put("/telegram/settings", response_model=TelegramSettingsPublic)
def update_telegram_settings(
    payload: TelegramSettingsUpdateRequest,
    _admin: User = Depends(get_current_household_admin),
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> TelegramSettingsPublic:
    return TelegramSettingsService(db).update(scope.household_id, payload)


@router.post("/telegram/test", response_model=TelegramSendResult)
def send_telegram_test(
    _admin: User = Depends(get_current_household_admin),
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> TelegramSendResult:
    return TelegramReminderService(db).send_test_message(scope.household_id)


@router.post("/telegram/send-daily-reminder", response_model=TelegramSendResult)
def send_daily_telegram_reminder(
    _admin: User = Depends(get_current_household_admin),
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> TelegramSendResult:
    return TelegramReminderService(db).send_daily_reminder(scope.household_id)
