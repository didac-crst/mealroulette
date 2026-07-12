from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.models.scheduler import DEFAULT_PLANNING_RULE_ID, PlanningRule
from mealroulette.schemas.scheduler import (
    PlanningRulePublic,
    PlanningRuleUpdateRequest,
    PlanningRulesConfig,
)


class PlanningRuleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def parse_rules(rules_json: dict) -> PlanningRulesConfig:
        return PlanningRulesConfig.model_validate(rules_json)

    @classmethod
    def to_public(cls, row: PlanningRule) -> PlanningRulePublic:
        return PlanningRulePublic(
            id=row.id,
            name=row.name,
            active=row.active,
            rules=cls.parse_rules(row.rules_json),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def get_active_row(self) -> PlanningRule:
        row = self.db.scalar(select(PlanningRule).where(PlanningRule.active.is_(True)).order_by(PlanningRule.id))
        if row is None:
            row = self.db.get(PlanningRule, DEFAULT_PLANNING_RULE_ID)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No planning rules configured")
        return row

    def get_active_public(self) -> PlanningRulePublic:
        return self.to_public(self.get_active_row())

    def get_active_rules(self) -> PlanningRulesConfig:
        return self.parse_rules(self.get_active_row().rules_json)

    def update_active(self, payload: PlanningRuleUpdateRequest) -> PlanningRulePublic:
        row = self.get_active_row()
        row.rules_json = payload.rules.model_dump()
        self.db.commit()
        self.db.refresh(row)
        return self.to_public(row)
