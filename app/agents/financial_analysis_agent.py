from app.services.market_service import (
    get_company_data
)


def financial_agent(state):

    companies = state["companies"]

    tickers = state["tickers"]

    print(
        "\n[Financial Agent]"
    )

    results = []

    for ticker in tickers:

        print(
            f"Fetching financial data for {ticker}"
        )

        data = get_company_data(
            ticker
        )

        analysis = analyze_financials(
            data
        )

        results.append(
            analysis
        )


    return {

        "agent_results": [
            {
                "task": "financial_analysis",
                "data": results,
            }
        ]

    }


def analyze_financials(data):

    if "error" in data:

        return {

            "ticker":
                data.get("ticker"),

            "status":
                "failed",

            "error":
                data["error"],

        }


    score = 0

    observations = []


    # -----------------------------------
    # REVENUE GROWTH
    # -----------------------------------

    revenue_growth = data.get(
        "revenue_growth"
    )

    if revenue_growth is not None:

        if revenue_growth > 0.10:

            score += 2

            observations.append(
                "Strong revenue growth"
            )

        elif revenue_growth > 0:

            score += 1

            observations.append(
                "Positive revenue growth"
            )

        else:

            score -= 1

            observations.append(
                "Negative revenue growth"
            )


    # -----------------------------------
    # PROFITABILITY
    # -----------------------------------

    roe = data.get("roe")

    if roe is not None:

        if roe > 0.15:

            score += 2

            observations.append(
                "Strong return on equity"
            )

        elif roe > 0.08:

            score += 1

            observations.append(
                "Moderate return on equity"
            )

        else:

            observations.append(
                "Low return on equity"
            )


    # -----------------------------------
    # DEBT
    # -----------------------------------

    debt_to_equity = data.get(
        "debt_to_equity"
    )

    if debt_to_equity is not None:

        if debt_to_equity < 100:

            score += 1

            observations.append(
                "Manageable debt level"
            )

        else:

            score -= 1

            observations.append(
                "High debt-to-equity"
            )


    # -----------------------------------
    # OVERALL ASSESSMENT
    # -----------------------------------

    if score >= 4:

        assessment = "strong"

    elif score >= 2:

        assessment = "moderate"

    else:

        assessment = "weak"


    return {

        "ticker":
            data.get("ticker"),

        "company_name":
            data.get("company_name"),

        "score":
            score,

        "assessment":
            assessment,

        "observations":
            observations,

        "metrics": data,

    }