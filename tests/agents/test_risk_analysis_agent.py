from unittest.mock import patch

from app.agents.risk_analysis_agent import (
    _confidence_from_flags,
    _fallback_top_risk_factors,
    _risk_label,
    _score_business_risk,
    _score_financial_risk,
    _score_market_risk,
    _score_sentiment_risk,
    build_risk_assessment,
    risk_analysis_agent,
)

from tests.conftest import make_execution_plan, make_financial_entry, make_news_entry, make_research_entry


# ------------------------------------------------------------
# Dimension scorers
# ------------------------------------------------------------


def test_financial_risk_flags_high_leverage_and_no_data_case():
    score, drivers, has_data = _score_financial_risk(
        {"metrics": {"debt_to_equity": 200, "free_cash_flow": -10}}
    )
    assert has_data is True
    assert score > 0.5
    assert "High debt-to-equity ratio" in drivers

    score, drivers, has_data = _score_financial_risk(None)
    assert has_data is False
    assert score == 0.5


def test_market_risk_high_beta_is_flagged():
    score, drivers, has_data = _score_market_risk({"beta": 1.8, "valuation": {}})
    assert has_data is True
    assert score >= 0.6
    assert any("volatility" in driver.lower() for driver in drivers)


def test_market_risk_no_signals_returns_neutral_no_data():
    score, drivers, has_data = _score_market_risk({"beta": None, "valuation": {}})
    assert has_data is False
    assert score == 0.5


def test_sentiment_risk_negative_news_scores_high():
    score, drivers, has_data = _score_sentiment_risk(
        {"sentiment_score": -0.5, "articles": [{"title": "x"}] * 5}
    )
    assert has_data is True
    assert score == 0.8


def test_sentiment_risk_no_articles_is_no_data():
    score, drivers, has_data = _score_sentiment_risk({"sentiment_score": -0.5, "articles": []})
    assert has_data is False
    assert score == 0.5


def test_business_risk_uses_key_risks_and_ownership():
    quant = {"key_risks": ["risk a", "risk b", "risk c"]}
    research_entry = {"ownership": {"institutional_holding_pct": 0.05}}

    score, drivers, has_data = _score_business_risk(quant, research_entry)

    assert has_data is True
    assert "Low institutional ownership conviction" in drivers


def test_risk_label_boundaries():
    assert _risk_label(0.75) == "Severe"
    assert _risk_label(0.5) == "High"
    assert _risk_label(0.3) == "Moderate"
    assert _risk_label(0.1) == "Low"


def test_confidence_from_flags_boundaries():
    assert _confidence_from_flags([True, True, True, True]) == "high"
    assert _confidence_from_flags([True, True, False, False]) == "medium"
    assert _confidence_from_flags([True, False, False, False]) == "low"


def test_fallback_top_risk_factors_orders_most_severe_first():
    dimensions = {
        "financial_risk": {"score": 0.2, "drivers": ["low risk driver"]},
        "market_risk": {"score": 0.9, "drivers": ["high risk driver"]},
    }

    factors = _fallback_top_risk_factors(dimensions)

    assert factors[0] == "high risk driver"
    assert factors[1] == "low risk driver"


# ------------------------------------------------------------
# build_risk_assessment() - LLM success/fallback
# ------------------------------------------------------------


def test_build_risk_assessment_uses_llm_narrative_on_success():
    fake_narrative = {
        "risk_level": "Severe",
        "top_risk_factors": ["llm risk"],
        "mitigating_factors": ["llm mitigant"],
        "horizon_note": "note",
    }

    with patch(
        "app.agents.risk_analysis_agent.synthesize_risk_assessment",
        return_value=fake_narrative,
    ):
        result = build_risk_assessment(
            "Test Co",
            "TEST.NS",
            make_financial_entry(metrics={"debt_to_equity": 200}),
            make_news_entry(sentiment_score=-0.5, articles=[{"title": "x"}] * 3),
            make_research_entry(),
            "5 years",
        )

    assert result["risk_level"] == "Severe"
    assert result["synthesis_status"] == "ok"
    assert "dimensions" in result


def test_build_risk_assessment_falls_back_to_rule_based_level_when_llm_fails():
    with patch(
        "app.agents.risk_analysis_agent.synthesize_risk_assessment",
        side_effect=RuntimeError("LLM unavailable"),
    ):
        result = build_risk_assessment(
            "Test Co",
            "TEST.NS",
            make_financial_entry(metrics={"debt_to_equity": 200}),
            make_news_entry(sentiment_score=-0.5, articles=[{"title": "x"}] * 3),
            make_research_entry(),
            None,
        )

    assert result["synthesis_status"].startswith("failed:")
    assert result["horizon_note"] is None
    assert result["top_risk_factors"] == _fallback_top_risk_factors(result["dimensions"])


def test_risk_analysis_agent_builds_one_assessment_per_company():
    state = {
        "companies": ["Test Co"],
        "tickers": ["TEST.NS"],
        "financial_analysis": {"TEST.NS": make_financial_entry()},
        "news_analysis": {"Test Co": make_news_entry()},
        "research_analysis": {"TEST.NS": make_research_entry()},
        "execution_plan": make_execution_plan(horizon="5 years"),
    }

    fake_assessment = {
        "company": "Test Co",
        "ticker": "TEST.NS",
        "risk_level": "Moderate",
        "risk_score": 0.4,
        "confidence": "medium",
        "dimensions": {},
        "top_risk_factors": [],
        "mitigating_factors": [],
        "horizon_note": None,
        "synthesis_status": "ok",
        "quant": {},
    }

    with patch(
        "app.agents.risk_analysis_agent.build_risk_assessment",
        return_value=fake_assessment,
    ) as build_mock:
        result = risk_analysis_agent(state)

    build_mock.assert_called_once_with(
        "Test Co",
        "TEST.NS",
        state["financial_analysis"]["TEST.NS"],
        state["news_analysis"]["Test Co"],
        state["research_analysis"]["TEST.NS"],
        "5 years",
    )

    assert result["risk_assessment"]["assessments"]["TEST.NS"]["risk_level"] == "Moderate"
    assert result["audit_log"][0]["risk_levels"] == {"TEST.NS": "Moderate"}
