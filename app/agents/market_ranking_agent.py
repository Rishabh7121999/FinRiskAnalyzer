from app.services.screener_service import (
    fetch_sector_constituents,
    rank_by_criterion,
)


DEFAULT_TOP_N = 5


def market_ranking_agent(state):

    plan = state["execution_plan"]

    print(
        "\n[Market Ranking Agent] "
        f"Screening sector={plan.sector!r} "
        f"criterion={plan.ranking_criterion!r}"
    )

    constituents = fetch_sector_constituents(
        plan.sector
    )

    if not constituents:

        return {

            "companies":
                [],

            "tickers":
                [],

            "current_agent":
                "market_ranking_agent",

            "next_action":
                "execute_plan",

            "audit_log": [
                {
                    "agent": "market_ranking_agent",
                    "action": "sector_unresolved",
                    "sector": plan.sector,
                }
            ],

        }

    top_n = plan.top_n or DEFAULT_TOP_N

    ranked = rank_by_criterion(
        constituents,
        plan.ranking_criterion,
        top_n,
    )

    companies = [
        entry["company_name"]
        for entry in ranked
    ]

    tickers = [
        entry["ticker"]
        for entry in ranked
    ]

    return {

        "companies":
            companies,

        "tickers":
            tickers,

        "current_agent":
            "market_ranking_agent",

        "next_action":
            "execute_plan",

        "audit_log": [
            {
                "agent": "market_ranking_agent",
                "action": "market_ranking_resolved",
                "sector": plan.sector,
                "criterion": plan.ranking_criterion,
                "top_n": top_n,
                "tickers": tickers,
            }
        ],

    }
