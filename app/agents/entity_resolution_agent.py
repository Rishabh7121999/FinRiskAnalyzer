from app.tools.ticker_resolver import resolve_ticker


def entity_resolution_agent(state):

    companies = state["companies"]

    resolved_tickers = []

    for company in companies:

        result = resolve_ticker(company)

        if result:
            resolved_tickers.append(
                result["ticker"]
            )

    return {
        "tickers": resolved_tickers,

        "current_agent":
            "entity_resolution_agent",

        "next_action":
            "execute_plan",

        "audit_log": [
            {
                "agent": "entity_resolution_agent",
                "action": "entities_resolved",
                "companies": companies,
                "tickers": resolved_tickers,
            }
        ],
    }