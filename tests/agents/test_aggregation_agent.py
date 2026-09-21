from app.agents.aggregation_agent import aggregation_agent

from tests.conftest import make_execution_plan


def test_all_required_tasks_completed():
    state = {
        "execution_plan": make_execution_plan(
            parallel_tasks=["financial_analysis", "news_analysis"]
        ),
        "completed_tasks": ["financial_analysis", "news_analysis"],
    }

    result = aggregation_agent(state)

    assert result["next_action"] == "investment_analysis"


def test_extra_completed_tasks_still_count_as_satisfied():
    state = {
        "execution_plan": make_execution_plan(parallel_tasks=["financial_analysis"]),
        "completed_tasks": ["financial_analysis", "news_analysis"],
    }

    result = aggregation_agent(state)

    assert result["next_action"] == "investment_analysis"


def test_missing_required_task_reports_incomplete():
    state = {
        "execution_plan": make_execution_plan(
            parallel_tasks=["financial_analysis", "news_analysis"]
        ),
        "completed_tasks": ["financial_analysis"],
    }

    result = aggregation_agent(state)

    assert result["next_action"] == "wait"


def test_missing_completed_tasks_key_defaults_to_incomplete():
    state = {
        "execution_plan": make_execution_plan(parallel_tasks=["financial_analysis"]),
    }

    result = aggregation_agent(state)

    assert result["next_action"] == "wait"
