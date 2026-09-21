from unittest.mock import patch

from app.agents.comparison_analysis_agent import comparison_analysis_agent

from tests.conftest import make_execution_plan


def _verdict(company, ticker, composite_score):
    return {
        "company": company,
        "ticker": ticker,
        "recommendation": "Hold",
        "confidence": "medium",
        "thesis": f"{company} thesis",
        "supporting_points": [f"{company} strength"],
        "conflicting_signals": [],
        "key_risks": [],
        "horizon_note": None,
        "composite_score": composite_score,
        "synthesis_status": "ok",
        "quant": {"beta": 1.0, "valuation": {}},
    }


def test_ranks_companies_by_composite_score_descending():
    state = {
        "companies": ["Weaker Co", "Stronger Co"],
        "tickers": ["WEAK.NS", "STRONG.NS"],
        "financial_analysis": {},
        "news_analysis": {},
        "research_analysis": {},
        "execution_plan": make_execution_plan(intent="comparison"),
    }

    verdicts = {
        "WEAK.NS": _verdict("Weaker Co", "WEAK.NS", 0.3),
        "STRONG.NS": _verdict("Stronger Co", "STRONG.NS", 0.8),
    }

    fake_insight = {
        "overall_verdict": "Stronger Co leads.",
        "leader_rationale": "Better fundamentals.",
        "key_differentiators": ["growth"],
        "company_notes": [],
    }

    with patch(
        "app.agents.comparison_analysis_agent.build_verdict",
        side_effect=lambda company, ticker, *a, **kw: verdicts[ticker],
    ), patch(
        "app.agents.comparison_analysis_agent.synthesize_comparison",
        return_value=fake_insight,
    ):
        result = comparison_analysis_agent(state)

    comparison = result["comparison_analysis"]

    assert comparison["leader"] == "Stronger Co"
    assert [entry["ticker"] for entry in comparison["ranking"]] == ["STRONG.NS", "WEAK.NS"]
    assert [entry["rank"] for entry in comparison["ranking"]] == [1, 2]
    assert comparison["overall_verdict"] == "Stronger Co leads."


def test_falls_back_to_leader_only_narrative_when_llm_fails():
    state = {
        "companies": ["Only Co"],
        "tickers": ["ONLY.NS"],
        "financial_analysis": {},
        "news_analysis": {},
        "research_analysis": {},
        "execution_plan": make_execution_plan(intent="comparison"),
    }

    verdict = _verdict("Only Co", "ONLY.NS", 0.6)

    with patch(
        "app.agents.comparison_analysis_agent.build_verdict",
        return_value=verdict,
    ), patch(
        "app.agents.comparison_analysis_agent.synthesize_comparison",
        side_effect=RuntimeError("LLM unavailable"),
    ):
        result = comparison_analysis_agent(state)

    comparison = result["comparison_analysis"]

    assert "Only Co ranks highest" in comparison["overall_verdict"]
    assert comparison["key_differentiators"] == []
    assert result["audit_log"][0]["synthesis"].startswith("failed:")


def test_empty_companies_produces_no_companies_to_compare_message():
    state = {
        "companies": [],
        "tickers": [],
        "financial_analysis": {},
        "news_analysis": {},
        "research_analysis": {},
        "execution_plan": make_execution_plan(intent="comparison"),
    }

    with patch(
        "app.agents.comparison_analysis_agent.synthesize_comparison",
        side_effect=RuntimeError("LLM unavailable"),
    ):
        result = comparison_analysis_agent(state)

    comparison = result["comparison_analysis"]

    assert comparison["leader"] is None
    assert comparison["overall_verdict"] == "No companies to compare."
