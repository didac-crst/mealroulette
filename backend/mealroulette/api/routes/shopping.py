from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_admin, get_current_user
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.shopping import (
    ShoppingListCreateRequest,
    ShoppingListItemPublic,
    ShoppingListItemUpdateRequest,
    ShoppingListPublic,
)
from mealroulette.schemas.telegram import TelegramSendResult
from mealroulette.services.shopping import ShoppingListService
from mealroulette.services.telegram_reminder import TelegramReminderService

router = APIRouter(tags=["shopping"])


@router.get("/shopping-list", response_model=ShoppingListPublic)
def preview_shopping_list(
    from_date: date = Query(alias="from"),
    days: int = Query(default=3, ge=1, le=14),
    exclude_pantry: bool = Query(default=True),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShoppingListPublic:
    return ShoppingListService(db).generate_preview(from_date, days, exclude_pantry)


@router.post("/shopping-lists", response_model=ShoppingListPublic, status_code=201)
def create_shopping_list(
    payload: ShoppingListCreateRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShoppingListPublic:
    return ShoppingListService(db).create_list(payload)


@router.get("/shopping-lists/{shopping_list_id}", response_model=ShoppingListPublic)
def get_shopping_list(
    shopping_list_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShoppingListPublic:
    return ShoppingListService(db).get_list(shopping_list_id)


@router.put("/shopping-list-items/{item_id}", response_model=ShoppingListItemPublic)
def update_shopping_list_item(
    item_id: int,
    payload: ShoppingListItemUpdateRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShoppingListItemPublic:
    return ShoppingListService(db).update_item(item_id, payload)


@router.post("/shopping-lists/{shopping_list_id}/send-telegram", response_model=TelegramSendResult)
def send_shopping_list_telegram(
    shopping_list_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TelegramSendResult:
    return TelegramReminderService(db).send_shopping_list(shopping_list_id)
