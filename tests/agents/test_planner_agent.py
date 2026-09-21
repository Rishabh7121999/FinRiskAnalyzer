import pytest

from app.agents.planner_agent import (
    INTENT_DEFAULT_TASKS,
    INTENT_MAP,
    SCOPE_TO_TASK,
    planner_agent,
)
from app.models.execution_plan import ExecutionPlan, TaskType
from app.models.query import QueryUnderstanding

from typing import get_args


VALID_EXECUTION_PLAN_INTENTS = set(get_args(ExecutionPlan.model_fields["intent"].annotation))
VALID_TASK_TYPES = set(get_args(TaskType))


def make_query_understanding(**overrides):
    defaults = dict(
        intent="investment_analysis",
        companies=["Test Co"],
        comparison_companies=[],
        horizon=None,
        sector=None,
        market=None,
        top_n=None,
        ranking_criterion=None,
        analysis_scope=[],
        user_goal="Evaluate Test Co",
        constraints=[],
    )
    defaults.update(overrides)
    return QueryUnderstanding(**defaults)


# ------------------------------------------------------------
# Consistency guards - encode the invariant CLAUDE.md documents:
# ExecutionPlan.tasks/TaskType and ExecutionPlan.intent must stay
# in sync with the planner's lookup tables.
# ------------------------------------------------------------


def test_every_intent_map_value_is_a_valid_execution_plan_intent():
    for value in INTENT_MAP.values():
        assert value in VALID_EXECUTION_PLAN_INTENTS


def test_every_default_task_is_a_valid_task_type():
    for tasks in INTENT_DEFAULT_TASKS.values():
        for task in tasks:
            assert task in VALID_TASK_TYPES


def test_every_scope_task_is_a_valid_task_type():
    for task in SCOPE_TO_TASK.values():
        assert task in VALID_TASK_TYPES


def test_every_query_understanding_intent_has_a_map_entry():
    query_intents = set(
        get_args(QueryUnderstanding.model_fields["intent"].annotation)
    )
    assert query_intents.issubset(INTENT_MAP.keys())


# ------------------------------------------------------------
# planner_agent behavior
# ------------------------------------------------------------


@pytest.mark.parametrize("intent", list(INTENT_DEFAULT_TASKS.keys()))
def test_planner_maps_each_intent_to_its_documented_tasks(intent):
    state = {"query_understanding": make_query_understanding(intent=intent)}

    result = planner_agent(state)

    plan = result["execution_plan"]

    assert plan.tasks == INTENT_DEFAULT_TASKS[intent]
    assert plan.parallel_tasks == INTENT_DEFAULT_TASKS[intent]
    assert plan.intent == INTENT_MAP[intent]
    assert plan.requires_financial_analysis == ("financial_analysis" in plan.tasks)
    assert plan.requires_news_analysis == ("news_analysis" in plan.tasks)
    assert plan.requires_research_analysis == ("research_analysis" in plan.tasks)


def test_market_ranking_intent_sets_requires_market_ranking():
    state = {"query_understanding": make_query_understanding(intent="market_ranking")}

    plan = planner_agent(state)["execution_plan"]

    assert plan.requires_market_ranking is True


def test_non_market_ranking_intent_does_not_set_requires_market_ranking():
    state = {"query_understanding": make_query_understanding(intent="investment_analysis")}

    plan = planner_agent(state)["execution_plan"]

    assert plan.requires_market_ranking is False


def test_analysis_scope_overrides_default_tasks_entirely():
    state = {
        "query_understanding": make_query_understanding(
            intent="investment_analysis",
            analysis_scope=["financial"],
        )
    }

    plan = planner_agent(state)["execution_plan"]

    assert plan.tasks == ["financial_analysis"]
    assert plan.requires_news_analysis is False
    assert plan.requires_research_analysis is False


def test_analysis_scope_with_multiple_dimensions():
    state = {
        "query_understanding": make_query_understanding(
            intent="comparison",
            analysis_scope=["news", "research"],
        )
    }

    plan = planner_agent(state)["execution_plan"]

    assert plan.tasks == ["news_analysis", "research_analysis"]


def test_planner_carries_horizon_and_user_goal_through():
    state = {
        "query_understanding": make_query_understanding(
            horizon="5 years",
            user_goal="Long term growth",
        )
    }

    plan = planner_agent(state)["execution_plan"]

    assert plan.horizon == "5 years"
    assert plan.user_goal == "Long term growth"


def test_planner_sets_control_flow_fields():
    state = {"query_understanding": make_query_understanding()}

    result = planner_agent(state)

    assert result["current_agent"] == "planner_agent"
    assert result["next_action"] == "resolve_entities"
    assert len(result["audit_log"]) == 1
    assert result["audit_log"][0]["agent"] == "planner_agent"
