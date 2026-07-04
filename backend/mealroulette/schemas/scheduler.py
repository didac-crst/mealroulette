from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field


class WeeklyTargetSpec(BaseModel):
    min: int = Field(ge=0)
    max: int = Field(ge=0)


class PlanningRulesConfig(BaseModel):
    weekly_targets: dict[str, WeeklyTargetSpec] = Field(default_factory=dict)
    weekly_target_tolerance: int = Field(default=1, ge=0)
    avoid_same_dish_within_days: int = Field(default=21, ge=1)
    avoid_similar_meals_within_days: int = Field(default=14, ge=1)
    similarity_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    prefer_seasonal: bool = True
    prefer_high_rated: bool = True
    allow_leftovers: bool = True
    default_grams_per_count: int = Field(default=100, ge=1)
    vector_min_grams: int = Field(default=5, ge=0)
    plan_attempts: int = Field(default=50, ge=1, le=200)
    history_window_days: int = Field(default=14, ge=1)


class PlanningRulePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    active: bool
    rules: PlanningRulesConfig
    created_at: datetime
    updated_at: datetime


class PlanningRuleUpdateRequest(BaseModel):
    rules: PlanningRulesConfig


class SchedulerSettingsPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    run_weekday: int = Field(description="0=Monday … 6=Sunday")
    run_time: time
    timezone: str
    target_week_offset: int = Field(description="0=this week, 1=next week, etc.")
    notify_telegram: bool
    notify_planning_days: int
    last_roulette_at: datetime | None = None
    last_error: str | None = None


class SchedulerSettingsUpdateRequest(BaseModel):
    enabled: bool | None = None
    run_weekday: int | None = Field(default=None, ge=0, le=6)
    run_time: time | None = None
    timezone: str | None = None
    target_week_offset: int | None = Field(default=None, ge=0, le=4)
    notify_telegram: bool | None = None
    notify_planning_days: int | None = Field(default=None, ge=1, le=14)


class MealPlanRouletteResponse(BaseModel):
    warnings: list[str]
    variety: dict
    assignments_count: int
    total_score: float
    can_undo: bool = True


class MealPlanUndoRouletteResponse(BaseModel):
    restored: bool
    can_undo: bool = False
