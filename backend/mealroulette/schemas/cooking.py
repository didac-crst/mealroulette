from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CookingTimerAlertCreateRequest(BaseModel):
    recipe_id: int = Field(ge=1)
    recipe_step_id: int = Field(ge=1)
    step_number: int = Field(ge=1)
    remaining_seconds: int = Field(ge=1, le=24 * 60 * 60)


class CookingTimerAlertPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_id: int
    recipe_step_id: int
    step_number: int
    dish_name: str
    recipe_name: str
    fire_at: datetime
    status: str
    telegram_scheduled: bool


class CookingTimerAlertCancelResult(BaseModel):
    cancelled: bool
