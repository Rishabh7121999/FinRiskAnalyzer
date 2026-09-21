from unittest.mock import patch

from app.agents.investment_analysis_agent import (
    _confidence_bucket,
    build_verdict,
    investment_analysis_agent,
)

from tests.conftest import make_execution_plan, make_financial_entry, make_news_entry


def test_confidence_bucket_boundaries():
    assert _confidence_bucket(0.9) == "high"
    assert _confidence_bucket(0.7) == "high"
    assert _confidence_bucket(0.5) == "medium"
    assert _confidence_bucket(0.4) == "medium"
    assert _confidence_bucket(0.1) == "low"


def test_build_verdict_uses_llm_narrative_on_success():
    fake_narrative = {
        "recommendation": "Buy",
        "confidence": "high",
        "thesis": "LLM-generated thesis.",
        "supporting_points": ["point 1"],
        "conflicting_signals": [],
        "key_risks": ["risk 1"],
        "horizon_note": "Long horizon absorbs volatility.",
    }

    with patch(
        "app.agents.investment_analysis_agent.synthesize_investment_verdict",
        return_value=fake_narrative,
    ):
        verdict = build_verdict(
            "Test Co",
            "TEST.NS",
            make_financial_entry(normalized_score=0.9),
            make_news_entry(),
            None,
            "5 years",
            "Grow wealth",
        )

    assert verdict["recommendation"] == "Buy"
    assert verdict["thesis"] == "LLM-generated thesis."
    assert verdict["synthesis_status"] == "ok"
    assert "quant" in verdict


def test_build_verdict_falls_back_to_quant_when_llm_fails():
    with patch(
        "app.agents.investment_analysis_agent.synthesize_investment_verdict",
        side_effect=RuntimeError("LLM unavailable"),
    ):
        verdict = build_verdict(
            "Test Co",
            "TEST.NS",
            make_financial_entry(normalized_score=0.9),
            make_news_entry(),
            None,
            None,
            None,
        )

    quant = verdict["quant"]

    assert verdict["recommendation"] == quant["recommendation"]
    assert verdict["thesis"] == "; ".join(quant["rationale"])
    assert verdict["supporting_points"] == quant["rationale"]
    assert verdict["conflicting_signals"] == []
    assert verdict["horizon_note"] is None
    assert verdict["synthesis_status"].startswith("failed:")


def test_investment_analysis_agent_builds_one_verdict_per_company():
    state = {
        "companies": ["Test Co"],
        "tickers": ["TEST.NS"],
        "financial_analysis": {"TEST.NS": make_financial_entry()},
        "news_analysis": {"Test Co": make_news_entry()},
        "research_analysis": {},
        "execution_plan": make_execution_plan(horizon="5 years", user_goal="Grow wealth"),
    }

    fake_verdict = {
        "company": "Test Co",
        "ticker": "TEST.NS",
        "recommendation": "Hold",
        "confidence": "medium",
        "thesis": "x",
        "supporting_points": [],
        "conflicting_signals": [],
        "key_risks": [],
        "horizon_note": None,
        "composite_score": 0.5,
        "synthesis_status": "ok",
        "quant": {},
    }

    with patch(
        "app.agents.investment_analysis_agent.build_verdict",
        return_value=fake_verdict,
    ) as build_mock:
        result = investment_analysis_agent(state)

    build_mock.assert_called_once_with(
        "Test Co",
        "TEST.NS",
        state["financial_analysis"]["TEST.NS"],
        state["news_analysis"]["Test Co"],
        None,
        "5 years",
        "Grow wealth",
    )

    assert result["investment_analysis"]["verdicts"]["TEST.NS"]["recommendation"] == "Hold"
    assert result["investment_analysis"]["status"] == "completed"
    assert result["audit_log"][0]["recommendations"] == {"TEST.NS": "Hold"}
