from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_user
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.planning import (
    MealPlanCreateRequest,
    MealPlanItemAteLeftoversRequest,
    MealPlanItemPublic,
    MealPlanItemSkipRequest,
    MealPlanItemSwapRequest,
    MealPlanItemSwapResponse,
    MealPlanItemUpdateRequest,
    MealPlanPublic,
    MealPlanSlotAssignRequest,
    MealRatingCreateRequest,
    MealRatingPublic,
    MealRatingUpsertResponse,
)
from mealroulette.schemas.scheduler import MealPlanRouletteResponse, MealPlanUndoRouletteResponse
from mealroulette.services.planning import PlanningService
from mealroulette.services.scheduler_service import SchedulerService

router = APIRouter(tags=["planning"])


@router.get("/meal-plans/current", response_model=MealPlanPublic)
def get_current_meal_plan(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanPublic:
    return PlanningService(db).get_current_plan()


@router.get("/meal-plans/{week_start}", response_model=MealPlanPublic)
def get_meal_plan_by_week(
    week_start: date,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanPublic:
    return PlanningService(db).get_plan_by_week(week_start)


@router.post("/meal-plans", response_model=MealPlanPublic, status_code=201)
def create_meal_plan(
    payload: MealPlanCreateRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanPublic:
    return PlanningService(db).create_plan(payload)


@router.put("/meal-plan-items/{item_id}", response_model=MealPlanItemPublic)
def update_meal_plan_item(
    item_id: int,
    payload: MealPlanItemUpdateRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanItemPublic:
    return PlanningService(db).update_item(item_id, payload)


@router.post("/meal-plan-items/{item_id}/mark-eaten", response_model=MealPlanItemPublic)
def mark_meal_plan_item_eaten(
    item_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanItemPublic:
    return PlanningService(db).mark_eaten(item_id)


@router.post("/meal-plan-items/{item_id}/skip", response_model=MealPlanItemPublic)
def skip_meal_plan_item(
    item_id: int,
    payload: MealPlanItemSkipRequest | None = None,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanItemPublic:
    body = payload or MealPlanItemSkipRequest()
    return PlanningService(db).skip_item(item_id, body.skip_reason, body.skip_comment)


@router.post("/meal-plan-items/{item_id}/ate-leftovers", response_model=MealPlanItemPublic)
def mark_meal_plan_item_ate_leftovers(
    item_id: int,
    payload: MealPlanItemAteLeftoversRequest | None = None,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanItemPublic:
    source_id = payload.leftover_source_item_id if payload else None
    return PlanningService(db).mark_ate_leftovers(item_id, source_id)


@router.post("/meal-plan-items/{item_id}/lock", response_model=MealPlanItemPublic)
def lock_meal_plan_item(
    item_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanItemPublic:
    return PlanningService(db).lock_item(item_id)


@router.post("/meal-plan-items/{item_id}/unlock", response_model=MealPlanItemPublic)
def unlock_meal_plan_item(
    item_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanItemPublic:
    return PlanningService(db).unlock_item(item_id)


@router.post("/meal-plan-items/{item_id}/reset-status", response_model=MealPlanItemPublic)
def reset_meal_plan_item_status(
    item_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanItemPublic:
    return PlanningService(db).reset_status_to_planned(item_id)


@router.get("/meal-plan-items/{item_id}/rating", response_model=MealRatingPublic | None)
def get_meal_plan_item_rating(
    item_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealRatingPublic | None:
    return PlanningService(db).get_meal_rating(item_id)


@router.post("/meal-plan-items/{item_id}/rating", response_model=MealRatingUpsertResponse)
def upsert_meal_plan_item_rating(
    item_id: int,
    payload: MealRatingCreateRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealRatingUpsertResponse:
    return PlanningService(db).upsert_meal_rating(item_id, payload)


@router.get("/meal-history", response_model=list[MealPlanItemPublic])
def list_meal_history(
    limit: int = Query(default=50, ge=1, le=200),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MealPlanItemPublic]:
    return PlanningService(db).list_history(limit=limit)


@router.post("/meal-plans/{meal_plan_id}/generate", response_model=MealPlanPublic)
def generate_meal_plan_week(
    meal_plan_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanPublic:
    planning = PlanningService(db)
    SchedulerService(db).generate_week(meal_plan_id)
    return planning.to_plan_public(planning._load_plan(meal_plan_id))


@router.post("/meal-plans/{meal_plan_id}/generate/details", response_model=MealPlanRouletteResponse)
def generate_meal_plan_week_details(
    meal_plan_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanRouletteResponse:
    service = SchedulerService(db)
    result, variety = service.generate_week(meal_plan_id)
    return MealPlanRouletteResponse(
        warnings=result.warnings,
        variety=variety,
        assignments_count=len(result.assignments),
        total_score=result.total_score,
        can_undo=True,
    )


@router.post("/meal-plan-items/{item_id}/reroll", response_model=MealPlanItemPublic)
def reroll_meal_plan_item(
    item_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanItemPublic:
    planning = PlanningService(db)
    SchedulerService(db).reroll_item(item_id)
    return planning.to_item_public(planning._load_item(item_id))


@router.post("/meal-plan-items/{item_id}/reroll/details", response_model=MealPlanRouletteResponse)
def reroll_meal_plan_item_details(
    item_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanRouletteResponse:
    service = SchedulerService(db)
    result, variety = service.reroll_item(item_id)
    return MealPlanRouletteResponse(
        warnings=result.warnings,
        variety=variety,
        assignments_count=len(result.assignments),
        total_score=result.total_score,
        can_undo=True,
    )


@router.post("/meal-plans/{meal_plan_id}/undo-roulette", response_model=MealPlanUndoRouletteResponse)
def undo_meal_plan_roulette(
    meal_plan_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanUndoRouletteResponse:
    restored = SchedulerService(db).undo_last_roulette(meal_plan_id)
    return MealPlanUndoRouletteResponse(restored=restored, can_undo=False)


@router.post("/meal-plan-items/assign", response_model=MealPlanItemPublic)
def assign_meal_plan_slot(
    payload: MealPlanSlotAssignRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanItemPublic:
    return PlanningService(db).assign_meal_slot(
        meal_date=payload.date,
        meal_slot=payload.meal_slot,
        dish_id=payload.dish_id,
        recipe_id=payload.recipe_id,
    )


@router.post("/meal-plan-items/{item_id}/swap", response_model=MealPlanItemSwapResponse)
def swap_meal_plan_items(
    item_id: int,
    payload: MealPlanItemSwapRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanItemSwapResponse:
    source, target = PlanningService(db).swap_items(item_id, payload.target_item_id)
    return MealPlanItemSwapResponse(source=source, target=target)
