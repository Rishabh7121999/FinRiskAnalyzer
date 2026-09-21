from app.graph.workflow import (
    fan_out_tasks,
    route_after_aggregation,
    route_after_planner,
)
from app.models.execution_plan import ExecutionPlan

from tests.conftest import make_execution_plan


def test_route_after_planner_goes_to_market_ranking_when_required():
    state = {"execution_plan": make_execution_plan(requires_market_ranking=True)}

    assert route_after_planner(state) == "market_ranking"


def test_route_after_planner_goes_to_entity_resolution_otherwise():
    state = {"execution_plan": make_execution_plan(requires_market_ranking=False)}

    assert route_after_planner(state) == "entity_resolution"


def test_route_after_aggregation_comparison_intent():
    state = {"execution_plan": make_execution_plan(intent="comparison")}

    assert route_after_aggregation(state) == "comparison_analysis"


def test_route_after_aggregation_company_research_and_news_go_to_verification():
    # No synthesis agent runs for these intents, but the report still
    # goes through verification -> governance for consistency.
    for intent in ("company_research", "news_analysis"):
        state = {"execution_plan": make_execution_plan(intent=intent)}

        assert route_after_aggregation(state) == "verification"


def test_route_after_aggregation_default_runs_investment_and_risk_together():
    for intent in ("investment_analysis", "risk_analysis", "unknown"):
        state = {"execution_plan": make_execution_plan(intent=intent)}

        assert route_after_aggregation(state) == ["investment_analysis", "risk_analysis"]


def test_route_after_aggregation_covers_every_execution_plan_intent():
    from typing import get_args

    all_intents = get_args(ExecutionPlan.model_fields["intent"].annotation)

    for intent in all_intents:
        state = {"execution_plan": make_execution_plan(intent=intent)}

        # Should not raise for any valid ExecutionPlan.intent value.
        route_after_aggregation(state)


def test_fan_out_tasks_sends_one_task_per_planned_task():
    state = {
        "execution_plan": make_execution_plan(
            parallel_tasks=["financial_analysis", "news_analysis"]
        ),
        "user_query": "Should I invest in Test Co?",
        "companies": ["Test Co"],
        "tickers": ["TEST.NS"],
    }

    sends = fan_out_tasks(state)

    assert [send.node for send in sends] == ["financial_analysis", "news_analysis"]

    for send in sends:
        assert send.arg["companies"] == ["Test Co"]
        assert send.arg["tickers"] == ["TEST.NS"]


def test_fan_out_tasks_skips_unknown_task_names():
    # ExecutionPlan.parallel_tasks is typed list[TaskType] (a closed
    # Literal), so a real ExecutionPlan can never contain an unknown
    # task name - use a bare stand-in to exercise fan_out_tasks'
    # defensive `task_to_node.get(task) is None -> skip` branch
    # directly, independent of that model-level guarantee.
    from types import SimpleNamespace

    state = {
        "execution_plan": SimpleNamespace(
            parallel_tasks=["financial_analysis", "not_a_real_task"]
        ),
        "user_query": "Should I invest in Test Co?",
        "companies": ["Test Co"],
        "tickers": ["TEST.NS"],
    }

    sends = fan_out_tasks(state)

    assert [send.node for send in sends] == ["financial_analysis"]


def test_fan_out_tasks_empty_plan_sends_nothing():
    state = {
        "execution_plan": make_execution_plan(parallel_tasks=[]),
        "user_query": "Should I invest in Test Co?",
        "companies": ["Test Co"],
        "tickers": ["TEST.NS"],
    }

    assert fan_out_tasks(state) == []


def test_every_route_after_aggregation_target_is_a_real_node():
    # Guards against route_after_aggregation returning a string that
    # doesn't correspond to a node wired into the graph.
    from app.graph.workflow import workflow

    node_names = set(workflow.nodes.keys())

    targets = set()
    for intent in ("comparison", "company_research", "news_analysis", "investment_analysis"):
        outcome = route_after_aggregation({"execution_plan": make_execution_plan(intent=intent)})
        targets.update(outcome if isinstance(outcome, list) else [outcome])

    assert targets.issubset(node_names)
