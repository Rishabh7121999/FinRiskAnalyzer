from unittest.mock import patch

from app.agents.entity_resolution_agent import entity_resolution_agent


def test_resolves_each_company_to_a_ticker():
    state = {"companies": ["Reliance Industries", "Tata Motors"]}

    def fake_resolve(company):
        return {
            "Reliance Industries": {"ticker": "RELIANCE.NS", "company": "Reliance Industries"},
            "Tata Motors": {"ticker": "TATAMOTORS.NS", "company": "Tata Motors"},
        }[company]

    with patch(
        "app.agents.entity_resolution_agent.resolve_ticker",
        side_effect=fake_resolve,
    ):
        result = entity_resolution_agent(state)

    assert result["tickers"] == ["RELIANCE.NS", "TATAMOTORS.NS"]
    assert result["current_agent"] == "entity_resolution_agent"
    assert result["next_action"] == "execute_plan"


def test_unresolvable_company_is_skipped_not_crashed():
    state = {"companies": ["Reliance Industries", "Unknown Corp"]}

    def fake_resolve(company):
        if company == "Reliance Industries":
            return {"ticker": "RELIANCE.NS", "company": "Reliance Industries"}
        return None

    with patch(
        "app.agents.entity_resolution_agent.resolve_ticker",
        side_effect=fake_resolve,
    ):
        result = entity_resolution_agent(state)

    assert result["tickers"] == ["RELIANCE.NS"]


def test_audit_log_records_companies_and_tickers():
    state = {"companies": ["Test Co"]}

    with patch(
        "app.agents.entity_resolution_agent.resolve_ticker",
        return_value={"ticker": "TEST.NS", "company": "Test Co"},
    ):
        result = entity_resolution_agent(state)

    entry = result["audit_log"][0]
    assert entry["companies"] == ["Test Co"]
    assert entry["tickers"] == ["TEST.NS"]
