import pytest

from mealroulette.data.default_planning_rules import DEFAULT_PLANNING_RULES_JSON
from mealroulette.schemas.scheduler import PlanningRuleUpdateRequest, PlanningRulesConfig
from mealroulette.services.planning_rule_service import PlanningRuleService


@pytest.mark.integration
def test_active_planning_rules_seeded(db_session, scheduler_seed):
    public = PlanningRuleService(db_session).get_active_public()

    assert public.name == "default"
    assert public.active is True
    assert public.rules.default_grams_per_count == 100
    assert public.rules.vector_min_grams == 5
    assert public.rules.weekly_targets["fish"].min == 1
    assert public.rules.plan_attempts == 50


@pytest.mark.integration
def test_update_active_planning_rules(db_session, scheduler_seed):
    service = PlanningRuleService(db_session)
    updated = service.update_active(
        PlanningRuleUpdateRequest(
            rules=PlanningRulesConfig(
                **{
                    **DEFAULT_PLANNING_RULES_JSON,
                    "default_grams_per_count": 120,
                    "vector_min_grams": 8,
                }
            )
        )
    )

    assert updated.rules.default_grams_per_count == 120
    assert updated.rules.vector_min_grams == 8

    reloaded = service.get_active_rules()
    assert reloaded.default_grams_per_count == 120
