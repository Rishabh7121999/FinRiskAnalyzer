"""
Opt-in live smoke test - hits real Gemini + yfinance/news APIs.

Skipped by default (see `addopts` in pyproject.toml). Run explicitly with:

    uv run pytest -m integration

Requires GOOGLE_API_KEY to be set (e.g. via .env, loaded by python-dotenv
the same way the agents load it).
"""

import os

import pytest

from dotenv import load_dotenv

load_dotenv()


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set - skipping live LLM smoke test",
)
def test_full_workflow_produces_a_report_for_a_real_query():
    from app.graph.workflow import graph

    initial_state = {
        "user_query": "Should I invest in Tata Motors?",
        "query_understanding": None,
        "execution_plan": None,
        "companies": [],
        "tickers": [],
        "financial_data": {},
        "news_data": [],
        "retrieved_documents": [],
        "financial_analysis": {},
        "news_analysis": {},
        "research_analysis": {},
        "completed_tasks": [],
        "investment_analysis": {},
        "comparison_analysis": {},
        "risk_assessment": {},
        "verification_result": {},
        "governance_result": {},
        "requires_human_review": False,
        "next_action": "",
        "retry_count": 0,
        "max_retries": 2,
        "final_report": "",
        "audit_log": [],
        "current_agent": "",
    }

    result = graph.invoke(initial_state)

    assert result["tickers"], "entity resolution should have found at least one ticker"
    assert result["final_report"].strip() != ""
    assert "AI FINANCIAL INTELLIGENCE REPORT" in result["final_report"]
    assert "INVESTMENT ANALYSIS" in result["final_report"]
    assert "RISK ASSESSMENT" in result["final_report"]
