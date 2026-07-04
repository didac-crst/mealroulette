from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_admin
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.scheduler import (
    PlanningRulePublic,
    PlanningRuleUpdateRequest,
    SchedulerSettingsPublic,
    SchedulerSettingsUpdateRequest,
)
from mealroulette.services.planning_rule_service import PlanningRuleService
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
