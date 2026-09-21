from app.services.market_service import (
    get_company_data,
    get_growth_and_coverage,
)


def financial_analysis_agent(state):

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

        data = {
            **get_company_data(ticker),
            **get_growth_and_coverage(ticker),
        }

        analysis = analyze_financials(
            data
        )

        results.append(
            analysis
        )

    return {
        "financial_analysis": {
            ticker_result["ticker"]: ticker_result
            for ticker_result in results
        },
        "completed_tasks": ["financial_analysis"],
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

    observations = []

    # -----------------------------------
    # GROWTH (multi-year CAGR, falls back
    # to yfinance's single-year figure)
    # -----------------------------------

    growth_score, growth_note = _score_growth(
        data
    )

    if growth_note:
        observations.append(growth_note)

    # -----------------------------------
    # EARNINGS GROWTH
    # -----------------------------------

    earnings_score, earnings_note = _score_earnings_growth(
        data
    )

    if earnings_note:
        observations.append(earnings_note)

    # -----------------------------------
    # PROFITABILITY
    # -----------------------------------

    profitability_score, profitability_note = _score_profitability(
        data
    )

    if profitability_note:
        observations.append(profitability_note)

    # -----------------------------------
    # VALUATION
    # -----------------------------------

    valuation_score, valuation_note = _score_valuation(
        data
    )

    if valuation_note:
        observations.append(valuation_note)

    # -----------------------------------
    # LEVERAGE & LIQUIDITY
    # -----------------------------------

    leverage_score, leverage_note = _score_leverage_liquidity(
        data
    )

    if leverage_note:
        observations.append(leverage_note)

    # -----------------------------------
    # CASH QUALITY
    # -----------------------------------

    cash_score, cash_note = _score_cash_quality(
        data
    )

    if cash_note:
        observations.append(cash_note)

    # -----------------------------------
    # COMPOSITE (weighted average of the
    # categories above, each already
    # normalised to 0..1 - this is the
    # single number downstream scoring
    # should read, so it never has to
    # guess this agent's internal range)
    # -----------------------------------

    weighted_components = [
        (growth_score, 0.20),
        (earnings_score, 0.10),
        (profitability_score, 0.25),
        (valuation_score, 0.15),
        (leverage_score, 0.20),
        (cash_score, 0.10),
    ]

    normalized_score = round(
        sum(
            score * weight
            for score, weight in weighted_components
        ),
        3,
    )

    if normalized_score >= 0.65:

        assessment = "strong"

    elif normalized_score >= 0.45:

        assessment = "moderate"

    else:

        assessment = "weak"

    return {

        "ticker":
            data.get("ticker"),

        "company_name":
            data.get("company_name"),

        "normalized_score":
            normalized_score,

        "assessment":
            assessment,

        "observations":
            observations,

        "metrics": data,

    }


def _score_growth(data):

    growth_rate = data.get("revenue_cagr")

    used_cagr = growth_rate is not None

    if growth_rate is None:
        growth_rate = data.get("revenue_growth")

    if growth_rate is None:
        return 0.5, None

    label = "multi-year revenue growth" if used_cagr else "revenue growth"

    if growth_rate > 0.15:
        return 1.0, f"Strong {label}"

    if growth_rate > 0.05:
        return 0.75, f"Healthy {label}"

    if growth_rate > 0:
        return 0.55, f"Modest {label}"

    return 0.15, f"Revenue is stagnant or declining ({label})"


def _score_earnings_growth(data):

    growth_rate = data.get("net_income_cagr")

    used_cagr = growth_rate is not None

    if growth_rate is None:
        growth_rate = data.get("earnings_growth")

    if growth_rate is None:
        return 0.5, None

    label = "multi-year earnings growth" if used_cagr else "earnings growth"

    if growth_rate > 0.15:
        return 1.0, f"Strong {label}"

    if growth_rate > 0:
        return 0.6, f"Positive {label}"

    return 0.2, f"Negative {label}"


def _score_profitability(data):

    sub_scores = []

    roe = data.get("roe")

    if roe is not None:

        if roe > 0.20:
            sub_scores.append(1.0)
        elif roe > 0.12:
            sub_scores.append(0.7)
        elif roe > 0:
            sub_scores.append(0.4)
        else:
            sub_scores.append(0.1)

    operating_margin = data.get("operating_margin")

    if operating_margin is not None:

        if operating_margin > 0.20:
            sub_scores.append(1.0)
        elif operating_margin > 0.10:
            sub_scores.append(0.7)
        elif operating_margin > 0:
            sub_scores.append(0.4)
        else:
            sub_scores.append(0.1)

    net_margin = data.get("profit_margin")

    if net_margin is not None:

        if net_margin > 0.15:
            sub_scores.append(1.0)
        elif net_margin > 0.08:
            sub_scores.append(0.7)
        elif net_margin > 0:
            sub_scores.append(0.4)
        else:
            sub_scores.append(0.1)

    if not sub_scores:
        return 0.5, None

    average = sum(sub_scores) / len(sub_scores)

    if average >= 0.7:
        note = "Strong profitability"
    elif average >= 0.4:
        note = "Moderate profitability"
    else:
        note = "Weak profitability"

    return average, note


def _score_valuation(data):

    peg_ratio = data.get("peg_ratio")

    if peg_ratio is not None and peg_ratio > 0:

        if peg_ratio < 1:
            return 1.0, "Attractively valued relative to growth (PEG < 1)"

        if peg_ratio < 2:
            return 0.6, "Fairly valued relative to growth"

        return 0.3, "Expensive relative to growth (high PEG)"

    pe_ratio = data.get("pe_ratio")

    if pe_ratio is not None and pe_ratio > 0:

        if pe_ratio < 15:
            return 0.8, "Reasonably valued on trailing earnings"

        if pe_ratio < 25:
            return 0.6, "Moderately valued on trailing earnings"

        if pe_ratio < 40:
            return 0.4, "Richly valued on trailing earnings"

        return 0.2, "Expensive on trailing earnings (high P/E)"

    return 0.5, None


def _score_leverage_liquidity(data):

    sub_scores = []

    notes = []

    debt_to_equity = data.get("debt_to_equity")

    if debt_to_equity is not None:

        if debt_to_equity < 50:
            sub_scores.append(1.0)
            notes.append("low leverage")
        elif debt_to_equity < 100:
            sub_scores.append(0.7)
            notes.append("manageable debt")
        elif debt_to_equity < 150:
            sub_scores.append(0.4)
        else:
            sub_scores.append(0.1)
            notes.append("high debt-to-equity")

    current_ratio = data.get("current_ratio")

    if current_ratio is not None:

        if current_ratio >= 1.5:
            sub_scores.append(1.0)
        elif current_ratio >= 1.0:
            sub_scores.append(0.6)
        else:
            sub_scores.append(0.2)
            notes.append("weak short-term liquidity")

    interest_coverage = data.get("interest_coverage")

    if interest_coverage is not None:

        if interest_coverage >= 8:
            sub_scores.append(1.0)
        elif interest_coverage >= 3:
            sub_scores.append(0.6)
        else:
            sub_scores.append(0.2)
            notes.append("thin interest coverage")

    if not sub_scores:
        return 0.5, None

    average = sum(sub_scores) / len(sub_scores)

    note = "; ".join(notes) if notes else None

    if note:
        note = note[0].upper() + note[1:]

    return average, note


def _score_cash_quality(data):

    free_cash_flow = data.get("free_cash_flow")

    if free_cash_flow is None:
        return 0.5, None

    if free_cash_flow > 0:
        return 1.0, "Generating positive free cash flow"

    return 0.2, "Negative free cash flow"
