from unittest.mock import MagicMock, patch

import pandas as pd

from app.agents.research_analysis_agent import (
    _extract_revenue_trend,
    research_analysis_agent,
)


# ------------------------------------------------------------
# _extract_revenue_trend()
# ------------------------------------------------------------


def test_revenue_trend_growing():
    income_statement = {
        "2024-03-31": {"Total Revenue": 300},
        "2023-03-31": {"Total Revenue": 200},
        "2022-03-31": {"Total Revenue": 100},
    }

    result = _extract_revenue_trend(income_statement)

    assert result["trend"] == "growing"


def test_revenue_trend_declining():
    income_statement = {
        "2024-03-31": {"Total Revenue": 100},
        "2023-03-31": {"Total Revenue": 200},
        "2022-03-31": {"Total Revenue": 300},
    }

    result = _extract_revenue_trend(income_statement)

    assert result["trend"] == "declining"


def test_revenue_trend_volatile():
    income_statement = {
        "2024-03-31": {"Total Revenue": 250},
        "2023-03-31": {"Total Revenue": 100},
        "2022-03-31": {"Total Revenue": 300},
    }

    result = _extract_revenue_trend(income_statement)

    assert result["trend"] == "volatile"


def test_revenue_trend_insufficient_data():
    income_statement = {"2024-03-31": {"Total Revenue": 100}}

    result = _extract_revenue_trend(income_statement)

    assert result["trend"] == "insufficient_data"


def test_revenue_trend_ignores_missing_and_nan_rows():
    income_statement = {
        "2024-03-31": {"Total Revenue": 300},
        "2023-03-31": {"Total Revenue": float("nan")},
        "2022-03-31": {},
    }

    result = _extract_revenue_trend(income_statement)

    assert result["yearly_revenue"] == {"2024": 300}
    assert result["trend"] == "insufficient_data"


# ------------------------------------------------------------
# research_analysis_agent() - yfinance boundary mocked
# ------------------------------------------------------------


def _mock_ticker(info, financials=None):
    ticker = MagicMock()
    ticker.info = info
    ticker.financials = pd.DataFrame(financials or {})
    return ticker


def test_agent_skips_qualitative_research_without_business_summary():
    state = {"tickers": ["TEST.NS"]}

    info = {
        "longName": "Test Co",
        "sector": "Technology",
        "industry": "Software",
        "longBusinessSummary": None,
    }

    with patch(
        "app.agents.research_analysis_agent.yf.Ticker",
        return_value=_mock_ticker(info),
    ):
        result = research_analysis_agent(state)

    entry = result["research_analysis"]["TEST.NS"]

    assert entry["company_name"] == "Test Co"
    assert entry["qualitative_research"] is None
    assert result["completed_tasks"] == ["research_analysis"]


def test_agent_generates_qualitative_research_via_llm_when_summary_present():
    state = {"tickers": ["TEST.NS"]}

    info = {
        "longName": "Test Co",
        "sector": "Technology",
        "longBusinessSummary": "Test Co builds test software.",
    }

    fake_insight = MagicMock()
    fake_insight.model_dump.return_value = {
        "business_overview": "Builds software.",
        "competitive_position": "Strong.",
        "key_risks": [],
        "key_catalysts": [],
    }

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_insight

    with patch(
        "app.agents.research_analysis_agent.yf.Ticker",
        return_value=_mock_ticker(info),
    ), patch(
        "app.agents.research_analysis_agent.research_llm",
        fake_llm,
    ):
        result = research_analysis_agent(state)

    entry = result["research_analysis"]["TEST.NS"]

    assert entry["qualitative_research"]["business_overview"] == "Builds software."


def test_agent_records_error_per_ticker_without_crashing_whole_run():
    state = {"tickers": ["GOOD.NS", "BAD.NS"]}

    def fake_ticker(symbol):
        if symbol == "BAD.NS":
            raise RuntimeError("yfinance unavailable")
        return _mock_ticker({"longName": "Good Co", "longBusinessSummary": None})

    with patch(
        "app.agents.research_analysis_agent.yf.Ticker",
        side_effect=fake_ticker,
    ):
        result = research_analysis_agent(state)

    assert "error" not in result["research_analysis"]["GOOD.NS"]
    assert result["research_analysis"]["BAD.NS"]["error"] == "yfinance unavailable"
