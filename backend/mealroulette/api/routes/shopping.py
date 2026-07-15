from datetime import date

from fastapi import APIRouter, Depends, Query

from mealroulette.auth.dependencies import get_current_household_admin, get_current_user, get_current_household_scope, get_shopping_service, HouseholdScope
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
from mealroulette.db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["shopping"])


@router.get("/shopping-list", response_model=ShoppingListPublic)
def preview_shopping_list(
    from_date: date = Query(alias="from"),
    days: int = Query(default=3, ge=1, le=14),
    exclude_pantry: bool = Query(default=True),
    _user: User = Depends(get_current_user),
    shopping: ShoppingListService = Depends(get_shopping_service),
) -> ShoppingListPublic:
    return shopping.generate_preview(from_date, days, exclude_pantry)


@router.post("/shopping-lists", response_model=ShoppingListPublic, status_code=201)
def create_shopping_list(
    payload: ShoppingListCreateRequest,
    _user: User = Depends(get_current_user),
    shopping: ShoppingListService = Depends(get_shopping_service),
) -> ShoppingListPublic:
    return shopping.create_list(payload)


@router.get("/shopping-lists/{shopping_list_id}", response_model=ShoppingListPublic)
def get_shopping_list(
    shopping_list_id: int,
    _user: User = Depends(get_current_user),
    shopping: ShoppingListService = Depends(get_shopping_service),
) -> ShoppingListPublic:
    return shopping.get_list(shopping_list_id)


@router.put("/shopping-list-items/{item_id}", response_model=ShoppingListItemPublic)
def update_shopping_list_item(
    item_id: int,
    payload: ShoppingListItemUpdateRequest,
    _user: User = Depends(get_current_user),
    shopping: ShoppingListService = Depends(get_shopping_service),
) -> ShoppingListItemPublic:
    return shopping.update_item(item_id, payload)


@router.post("/shopping-lists/{shopping_list_id}/send-telegram", response_model=TelegramSendResult)
def send_shopping_list_telegram(
    shopping_list_id: int,
    _admin: User = Depends(get_current_household_admin),
    scope: HouseholdScope = Depends(get_current_household_scope),
    db: Session = Depends(get_db),
) -> TelegramSendResult:
    return TelegramReminderService(db).send_shopping_list(shopping_list_id, scope.household_id)
