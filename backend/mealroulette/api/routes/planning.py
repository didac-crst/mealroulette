from datetime import date

from fastapi import APIRouter, Depends, Query

from mealroulette.auth.dependencies import get_planning_service, get_scheduler_service
from mealroulette.models.user import User
from mealroulette.auth.dependencies import get_current_user
from mealroulette.schemas.planning import (
    MealPlanCreateRequest,
    MealPlanDishLineCreateRequest,
    MealPlanDishLineUpdateRequest,
    MealPlanDoNotPlanRequest,
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
from mealroulette.schemas.scheduler import MealPlanRerollResponse, MealPlanRouletteResponse, MealPlanUndoRouletteResponse
from mealroulette.services.planning import PlanningService
from mealroulette.services.scheduler_service import SchedulerService

router = APIRouter(tags=["planning"])


@router.get("/meal-plans/current", response_model=MealPlanPublic)
def get_current_meal_plan(
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanPublic:
    return planning.get_current_plan()


@router.get("/meal-plans/{week_start}", response_model=MealPlanPublic)
def get_meal_plan_by_week(
    week_start: date,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanPublic:
    return planning.get_plan_by_week(week_start)


@router.post("/meal-plans", response_model=MealPlanPublic, status_code=201)
def create_meal_plan(
    payload: MealPlanCreateRequest,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanPublic:
    return planning.create_plan(payload)


@router.put("/meal-plan-items/{item_id}", response_model=MealPlanItemPublic)
def update_meal_plan_item(
    item_id: int,
    payload: MealPlanItemUpdateRequest,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    return planning.update_item(item_id, payload)


@router.post("/meal-plan-items/{item_id}/mark-eaten", response_model=MealPlanItemPublic)
def mark_meal_plan_item_eaten(
    item_id: int,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    return planning.mark_eaten(item_id)


@router.post("/meal-plan-items/{item_id}/skip", response_model=MealPlanItemPublic)
def skip_meal_plan_item(
    item_id: int,
    payload: MealPlanItemSkipRequest | None = None,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    body = payload or MealPlanItemSkipRequest()
    return planning.skip_item(item_id, body.skip_reason, body.skip_comment)


@router.post("/meal-plan-items/{item_id}/ate-leftovers", response_model=MealPlanItemPublic)
def mark_meal_plan_item_ate_leftovers(
    item_id: int,
    payload: MealPlanItemAteLeftoversRequest | None = None,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    source_id = payload.leftover_source_item_id if payload else None
    return planning.mark_ate_leftovers(item_id, source_id)


@router.post("/meal-plan-items/{item_id}/lock", response_model=MealPlanItemPublic)
def lock_meal_plan_item(
    item_id: int,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    return planning.lock_item(item_id)


@router.post("/meal-plan-items/{item_id}/unlock", response_model=MealPlanItemPublic)
def unlock_meal_plan_item(
    item_id: int,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    return planning.unlock_item(item_id)


@router.post("/meal-plan-items/{item_id}/reset-status", response_model=MealPlanItemPublic)
def reset_meal_plan_item_status(
    item_id: int,
    current_user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    return planning.reset_status_to_planned(item_id, user_id=current_user.id)


@router.get("/meal-plan-items/{item_id}/rating", response_model=MealRatingPublic | None)
def get_meal_plan_item_rating(
    item_id: int,
    current_user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealRatingPublic | None:
    return planning.get_meal_rating(item_id, user_id=current_user.id)


@router.post("/meal-plan-items/{item_id}/rating", response_model=MealRatingUpsertResponse)
def upsert_meal_plan_item_rating(
    item_id: int,
    payload: MealRatingCreateRequest,
    current_user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealRatingUpsertResponse:
    return planning.upsert_meal_rating(item_id, payload, user_id=current_user.id)


@router.get("/meal-history", response_model=list[MealPlanItemPublic])
def list_meal_history(
    limit: int = Query(default=50, ge=1, le=200),
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> list[MealPlanItemPublic]:
    return planning.list_history(limit=limit)


@router.post("/meal-plans/{meal_plan_id}/generate", response_model=MealPlanPublic)
def generate_meal_plan_week(
    meal_plan_id: int,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> MealPlanPublic:
    scheduler.generate_week(meal_plan_id)
    return planning.to_plan_public(planning._load_plan(meal_plan_id))


@router.post("/meal-plans/{meal_plan_id}/generate/details", response_model=MealPlanRouletteResponse)
def generate_meal_plan_week_details(
    meal_plan_id: int,
    _user: User = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> MealPlanRouletteResponse:
    result, variety = scheduler.generate_week(meal_plan_id)
    return MealPlanRouletteResponse(
        warnings=result.warnings,
        variety=variety,
        assignments_count=len(result.assignments),
        total_score=result.total_score,
        can_undo=True,
    )


@router.post("/meal-plan-items/{item_id}/reroll", response_model=MealPlanRerollResponse)
def reroll_meal_plan_item(
    item_id: int,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> MealPlanRerollResponse:
    reroll = scheduler.reroll_item(item_id)
    item = planning.to_item_public(planning._load_item(item_id))
    if reroll.status == "exhausted":
        return MealPlanRerollResponse(status="exhausted", item=item, message=reroll.message)
    assert reroll.result is not None
    return MealPlanRerollResponse(
        status="success",
        item=item,
        warnings=reroll.result.warnings,
        variety=reroll.variety,
        total_score=reroll.result.total_score,
        can_undo=True,
    )


@router.post("/meal-plan-items/{item_id}/reroll/start-over", response_model=MealPlanItemPublic)
def start_over_meal_plan_reroll(
    item_id: int,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> MealPlanItemPublic:
    scheduler.start_over_reroll(item_id)
    return planning.to_item_public(planning._load_item(item_id))


@router.post("/meal-plan-items/{item_id}/reroll/details", response_model=MealPlanRerollResponse)
def reroll_meal_plan_item_details(
    item_id: int,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> MealPlanRerollResponse:
    reroll = scheduler.reroll_item(item_id)
    item = planning.to_item_public(planning._load_item(item_id))
    if reroll.status == "exhausted":
        return MealPlanRerollResponse(status="exhausted", item=item, message=reroll.message)
    assert reroll.result is not None
    return MealPlanRerollResponse(
        status="success",
        item=item,
        warnings=reroll.result.warnings,
        variety=reroll.variety,
        total_score=reroll.result.total_score,
        can_undo=True,
    )


@router.post("/meal-plans/{meal_plan_id}/undo-roulette", response_model=MealPlanUndoRouletteResponse)
def undo_meal_plan_roulette(
    meal_plan_id: int,
    _user: User = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> MealPlanUndoRouletteResponse:
    restored = scheduler.undo_last_roulette(meal_plan_id)
    return MealPlanUndoRouletteResponse(restored=restored, can_undo=False)


@router.post("/meal-plan-items/assign", response_model=MealPlanItemPublic)
def assign_meal_plan_slot(
    payload: MealPlanSlotAssignRequest,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    return planning.assign_meal_slot(
        meal_date=payload.date,
        meal_slot=payload.meal_slot,
        dish_id=payload.dish_id,
        recipe_id=payload.recipe_id,
        mode=payload.mode,
    )


@router.post("/meal-plan-items/{item_id}/lines", response_model=MealPlanItemPublic)
def add_meal_plan_line(
    item_id: int,
    payload: MealPlanDishLineCreateRequest,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    return planning.add_line(item_id, payload)


@router.put("/meal-plan-item-lines/{line_id}", response_model=MealPlanItemPublic)
def update_meal_plan_line(
    line_id: int,
    payload: MealPlanDishLineUpdateRequest,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    return planning.update_line(line_id, payload)


@router.delete("/meal-plan-item-lines/{line_id}", response_model=MealPlanItemPublic)
def delete_meal_plan_line(
    line_id: int,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    return planning.delete_line(line_id)


@router.post("/meal-plan-items/{item_id}/do-not-plan", response_model=MealPlanItemPublic)
def mark_meal_plan_do_not_plan(
    item_id: int,
    payload: MealPlanDoNotPlanRequest | None = None,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    body = payload or MealPlanDoNotPlanRequest()
    return planning.mark_do_not_plan(item_id, body)


@router.post("/meal-plan-items/{item_id}/reopen", response_model=MealPlanItemPublic)
def reopen_meal_plan_slot(
    item_id: int,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemPublic:
    return planning.reopen_slot(item_id)


@router.post("/meal-plan-items/{item_id}/swap", response_model=MealPlanItemSwapResponse)
def swap_meal_plan_items(
    item_id: int,
    payload: MealPlanItemSwapRequest,
    _user: User = Depends(get_current_user),
    planning: PlanningService = Depends(get_planning_service),
) -> MealPlanItemSwapResponse:
    source, target = planning.swap_items(item_id, payload.target_item_id)
    return MealPlanItemSwapResponse(source=source, target=target)
