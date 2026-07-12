from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_user
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.cooking import (
    CookingTimerAlertCancelResult,
    CookingTimerAlertCreateRequest,
    CookingTimerAlertPublic,
)
from mealroulette.services.cooking_timer_alerts import CookingTimerAlertService

router = APIRouter(tags=["cooking"])


@router.post("/cooking-timer-alerts", response_model=CookingTimerAlertPublic)
def schedule_cooking_timer_alert(
    payload: CookingTimerAlertCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CookingTimerAlertPublic:
    return CookingTimerAlertService(db).schedule(current_user, payload)


@router.delete("/cooking-timer-alerts/{alert_id}", response_model=CookingTimerAlertCancelResult)
def cancel_cooking_timer_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CookingTimerAlertCancelResult:
    cancelled = CookingTimerAlertService(db).cancel(current_user, alert_id)
    return CookingTimerAlertCancelResult(cancelled=cancelled)


@router.delete(
    "/cooking-timer-alerts/by-step/{recipe_step_id}",
    response_model=CookingTimerAlertCancelResult,
)
def cancel_cooking_timer_alert_for_step(
    recipe_step_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CookingTimerAlertCancelResult:
    cancelled_count = CookingTimerAlertService(db).cancel_for_step(current_user, recipe_step_id)
    return CookingTimerAlertCancelResult(cancelled=cancelled_count > 0)
