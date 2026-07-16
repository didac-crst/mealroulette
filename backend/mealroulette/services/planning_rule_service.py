from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mealroulette.data.default_planning_rules import DEFAULT_PLANNING_RULES_JSON, DEFAULT_PLANNING_RULE_NAME
from mealroulette.models.scheduler import PlanningRule
from mealroulette.schemas.scheduler import (
    PlanningRulePublic,
    PlanningRuleUpdateRequest,
    PlanningRulesConfig,
)


class PlanningRuleService:
    def __init__(self, db: Session, *, household_id: UUID) -> None:
        self.db = db
        self.household_id = household_id

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

    def _ensure_default_rule(self) -> PlanningRule:
        row = PlanningRule(
            household_id=self.household_id,
            name=DEFAULT_PLANNING_RULE_NAME,
            active=True,
            rules_json=DEFAULT_PLANNING_RULES_JSON,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get_active_row(self) -> PlanningRule:
        row = self.db.scalar(
            select(PlanningRule)
            .where(
                PlanningRule.household_id == self.household_id,
                PlanningRule.active.is_(True),
            )
            .order_by(PlanningRule.id)
        )
        if row is None:
            try:
                row = self._ensure_default_rule()
                self.db.commit()
                self.db.refresh(row)
            except IntegrityError:
                self.db.rollback()
                row = self.db.scalar(
                    select(PlanningRule)
                    .where(
                        PlanningRule.household_id == self.household_id,
                        PlanningRule.active.is_(True),
                    )
                    .order_by(PlanningRule.id)
                )
                if row is None:
                    raise
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
