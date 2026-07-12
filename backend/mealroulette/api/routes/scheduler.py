from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_admin
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.scheduler import (
    PlanningRulePublic,
    PlanningRuleUpdateRequest,
    SchedulerRouletteRunResult,
    SchedulerSettingsPublic,
    SchedulerSettingsUpdateRequest,
)
from mealroulette.services.planning_rule_service import PlanningRuleService
from mealroulette.services.scheduled_roulette import ScheduledRouletteService
from mealroulette.services.scheduler_settings import SchedulerSettingsService

router = APIRouter(tags=["scheduler"])


@router.get("/planning-rules/active", response_model=PlanningRulePublic)
def get_active_planning_rules(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> PlanningRulePublic:
    return PlanningRuleService(db).get_active_public()


@router.put("/planning-rules/active", response_model=PlanningRulePublic)
def update_active_planning_rules(
    payload: PlanningRuleUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> PlanningRulePublic:
    return PlanningRuleService(db).update_active(payload)


@router.get("/scheduler/settings", response_model=SchedulerSettingsPublic)
def get_scheduler_settings(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> SchedulerSettingsPublic:
    return SchedulerSettingsService(db).get_public()


@router.put("/scheduler/settings", response_model=SchedulerSettingsPublic)
def update_scheduler_settings(
    payload: SchedulerSettingsUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> SchedulerSettingsPublic:
    return SchedulerSettingsService(db).update(payload)


@router.post("/scheduler/run-roulette", response_model=SchedulerRouletteRunResult)
def run_scheduler_roulette_now(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> SchedulerRouletteRunResult:
    result = ScheduledRouletteService(db).run_now()
    telegram = result.telegram
    detail = f"Generated {result.assignments_count} meals for week {result.week_start_date.isoformat()}"
    if telegram is not None:
        detail = f"{detail}. {telegram.detail}"
    return SchedulerRouletteRunResult(
        ran=True,
        detail=detail,
        meal_plan_id=result.meal_plan_id,
        week_start_date=result.week_start_date,
        assignments_count=result.assignments_count,
        warnings=result.warnings,
        telegram_recipient_count=telegram.recipient_count if telegram else 0,
    )
