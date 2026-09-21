from unittest.mock import patch

from app.agents.financial_analysis_agent import (
    _score_cash_quality,
    _score_earnings_growth,
    _score_growth,
    _score_leverage_liquidity,
    _score_profitability,
    _score_valuation,
    analyze_financials,
    financial_analysis_agent,
)


# ------------------------------------------------------------
# analyze_financials()
# ------------------------------------------------------------


def test_error_in_data_short_circuits_to_failed_status():
    result = analyze_financials({"ticker": "BAD.NS", "error": "no data"})

    assert result == {
        "ticker": "BAD.NS",
        "status": "failed",
        "error": "no data",
    }


def test_strong_fundamentals_assessment():
    data = {
        "ticker": "GOOD.NS",
        "company_name": "Good Co",
        "revenue_cagr": 0.20,
        "net_income_cagr": 0.20,
        "roe": 0.25,
        "operating_margin": 0.25,
        "profit_margin": 0.20,
        "peg_ratio": 0.8,
        "debt_to_equity": 30,
        "current_ratio": 2.0,
        "interest_coverage": 10,
        "free_cash_flow": 1000,
    }

    result = analyze_financials(data)

    assert result["assessment"] == "strong"
    assert result["normalized_score"] >= 0.65


def test_weak_fundamentals_assessment():
    data = {
        "ticker": "BAD.NS",
        "company_name": "Bad Co",
        "revenue_growth": -0.10,
        "earnings_growth": -0.50,
        "roe": -0.05,
        "operating_margin": -0.05,
        "profit_margin": -0.05,
        "pe_ratio": 60,
        "debt_to_equity": 200,
        "current_ratio": 0.5,
        "interest_coverage": 1,
        "free_cash_flow": -100,
    }

    result = analyze_financials(data)

    assert result["assessment"] == "weak"
    assert result["normalized_score"] < 0.45


def test_missing_metrics_default_to_neutral_without_crashing():
    result = analyze_financials({"ticker": "SPARSE.NS", "company_name": "Sparse Co"})

    assert result["assessment"] == "moderate"
    assert result["observations"] == []


# ------------------------------------------------------------
# Growth scoring: multi-year CAGR preferred over single-year growth
# ------------------------------------------------------------


def test_growth_prefers_cagr_over_single_year_growth():
    score, note = _score_growth({"revenue_cagr": 0.20, "revenue_growth": -0.50})

    assert score == 1.0
    assert "multi-year" in note


def test_growth_falls_back_to_single_year_when_no_cagr():
    score, note = _score_growth({"revenue_growth": 0.20})

    assert score == 1.0
    assert "multi-year" not in note


def test_growth_returns_neutral_when_no_data():
    score, note = _score_growth({})

    assert score == 0.5
    assert note is None


def test_earnings_growth_negative_scores_low():
    score, note = _score_earnings_growth({"earnings_growth": -0.1})

    assert score == 0.2
    assert "Negative" in note


# ------------------------------------------------------------
# Valuation: PEG preferred over PE
# ------------------------------------------------------------


def test_valuation_prefers_peg_over_pe():
    score, note = _score_valuation({"peg_ratio": 0.5, "pe_ratio": 100})

    assert score == 1.0
    assert "PEG" in note


def test_valuation_falls_back_to_pe_when_no_peg():
    score, note = _score_valuation({"pe_ratio": 10})

    assert score == 0.8


def test_valuation_ignores_non_positive_peg():
    score, note = _score_valuation({"peg_ratio": -1, "pe_ratio": 10})

    assert score == 0.8


# ------------------------------------------------------------
# Profitability / leverage / cash quality boundaries
# ------------------------------------------------------------


def test_profitability_averages_available_sub_scores():
    score, note = _score_profitability({"roe": 0.25, "operating_margin": 0.25})

    assert 0.9 <= score <= 1.0
    assert note == "Strong profitability"


def test_leverage_flags_high_debt_and_weak_liquidity():
    score, note = _score_leverage_liquidity(
        {"debt_to_equity": 200, "current_ratio": 0.5, "interest_coverage": 1}
    )

    assert score < 0.3
    assert "high debt-to-equity" in note.lower()
    assert "weak short-term liquidity" in note.lower()


def test_cash_quality_negative_free_cash_flow():
    score, note = _score_cash_quality({"free_cash_flow": -50})

    assert score == 0.2
    assert "Negative" in note


def test_cash_quality_missing_data_is_neutral():
    score, note = _score_cash_quality({})

    assert score == 0.5
    assert note is None


# ------------------------------------------------------------
# financial_analysis_agent() - service boundary mocked
# ------------------------------------------------------------


def test_agent_fetches_and_analyzes_each_ticker():
    state = {
        "companies": ["Test Co"],
        "tickers": ["TEST.NS"],
    }

    company_data = {
        "ticker": "TEST.NS",
        "company_name": "Test Co",
        "revenue_growth": 0.10,
        "profit_margin": 0.10,
    }

    growth_data = {
        "revenue_cagr": None,
        "net_income_cagr": None,
        "interest_coverage": None,
    }

    with patch(
        "app.agents.financial_analysis_agent.get_company_data",
        return_value=company_data,
    ), patch(
        "app.agents.financial_analysis_agent.get_growth_and_coverage",
        return_value=growth_data,
    ):
        result = financial_analysis_agent(state)

    assert "TEST.NS" in result["financial_analysis"]
    assert result["financial_analysis"]["TEST.NS"]["assessment"] in (
        "strong",
        "moderate",
        "weak",
    )
    assert result["completed_tasks"] == ["financial_analysis"]
