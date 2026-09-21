from unittest.mock import patch

from app.agents.market_ranking_agent import market_ranking_agent

from tests.conftest import make_execution_plan


def test_ranks_and_returns_top_n_companies():
    state = {
        "execution_plan": make_execution_plan(
            sector="banking",
            ranking_criterion="market cap",
            top_n=2,
        )
    }

    constituents = [
        {"company_name": "Bank A", "ticker": "A.NS"},
        {"company_name": "Bank B", "ticker": "B.NS"},
    ]

    ranked = [
        {"company_name": "Bank B", "ticker": "B.NS", "criterion": "market_cap", "value": 200},
        {"company_name": "Bank A", "ticker": "A.NS", "criterion": "market_cap", "value": 100},
    ]

    with patch(
        "app.agents.market_ranking_agent.fetch_sector_constituents",
        return_value=constituents,
    ) as fetch_mock, patch(
        "app.agents.market_ranking_agent.rank_by_criterion",
        return_value=ranked,
    ) as rank_mock:
        result = market_ranking_agent(state)

    fetch_mock.assert_called_once_with("banking")
    rank_mock.assert_called_once_with(constituents, "market cap", 2)

    assert result["companies"] == ["Bank B", "Bank A"]
    assert result["tickers"] == ["B.NS", "A.NS"]
    assert result["current_agent"] == "market_ranking_agent"


def test_unresolved_sector_returns_empty_result_not_a_crash():
    state = {
        "execution_plan": make_execution_plan(
            sector="not a real sector",
            ranking_criterion="market cap",
            top_n=5,
        )
    }

    with patch(
        "app.agents.market_ranking_agent.fetch_sector_constituents",
        return_value=[],
    ):
        result = market_ranking_agent(state)

    assert result["companies"] == []
    assert result["tickers"] == []
    assert result["audit_log"][0]["action"] == "sector_unresolved"


def test_default_top_n_used_when_not_specified():
    state = {
        "execution_plan": make_execution_plan(
            sector="banking",
            ranking_criterion=None,
            top_n=None,
        )
    }

    with patch(
        "app.agents.market_ranking_agent.fetch_sector_constituents",
        return_value=[{"company_name": "Bank A", "ticker": "A.NS"}],
    ), patch(
        "app.agents.market_ranking_agent.rank_by_criterion",
        return_value=[],
    ) as rank_mock:
        market_ranking_agent(state)

    # DEFAULT_TOP_N = 5
    assert rank_mock.call_args.args[2] == 5
