def score_company(
    company,
    ticker,
    financial_entry,
    news_entry,
    research_entry,
):

    # -----------------------------------
    # FINANCIAL SIGNAL
    # -----------------------------------

    financial_score = None

    assessment = "unknown"

    observations = []

    beta = None

    valuation = {}

    if (
        financial_entry
        and financial_entry.get("status") != "failed"
    ):

        financial_score = financial_entry.get("normalized_score")

        assessment = financial_entry.get(
            "assessment",
            "unknown",
        )

        observations = financial_entry.get(
            "observations",
            [],
        )

        metrics = financial_entry.get(
            "metrics",
            {},
        ) or {}

        beta = metrics.get("beta")

        valuation = {

            "pe_ratio":
                metrics.get("pe_ratio"),

            "forward_pe":
                metrics.get("forward_pe"),

            "peg_ratio":
                metrics.get("peg_ratio"),

            "ev_to_ebitda":
                metrics.get("ev_to_ebitda"),

        }

    # -----------------------------------
    # NEWS SIGNAL
    # -----------------------------------

    sentiment_score = None

    overall_sentiment = "unknown"

    article_count = 0

    if news_entry:

        sentiment_score = news_entry.get("sentiment_score")

        overall_sentiment = news_entry.get(
            "overall_sentiment",
            "unknown",
        )

        article_count = len(
            news_entry.get("articles", [])
        )

    # -----------------------------------
    # RESEARCH CONTEXT
    # -----------------------------------

    sector = None

    industry = None

    revenue_trend = None

    analyst_upside_pct = None

    key_risks = []

    key_catalysts = []

    if research_entry:

        sector = research_entry.get("sector")

        industry = research_entry.get("industry")

        revenue_trend = research_entry.get(
            "revenue_trend",
            {},
        ).get("trend")

        analyst_consensus = research_entry.get(
            "analyst_consensus",
            {},
        )

        target_mean_price = analyst_consensus.get(
            "target_mean_price"
        )

        current_price = analyst_consensus.get(
            "current_price"
        )

        if target_mean_price and current_price:

            analyst_upside_pct = round(
                (
                    (target_mean_price - current_price)
                    / current_price
                )
                * 100,
                1,
            )

        qualitative_research = research_entry.get(
            "qualitative_research"
        )

        if qualitative_research:

            key_risks = qualitative_research.get(
                "key_risks",
                [],
            )

            key_catalysts = qualitative_research.get(
                "key_catalysts",
                [],
            )

    # -----------------------------------
    # COMPOSITE SCORE
    # -----------------------------------
    # financial_score is already normalised to 0..1 by
    # financial_analysis_agent; sentiment_score range is
    # -1..1 and is normalised to 0..1 here before blending

    confidence = 1.0

    if financial_score is not None:

        financial_norm = min(
            max(financial_score, 0),
            1,
        )

    else:

        financial_norm = 0.5

        confidence -= 0.3

    if sentiment_score is not None and article_count > 0:

        news_norm = min(
            max((sentiment_score + 1) / 2, 0),
            1,
        )

    else:

        news_norm = 0.5

        confidence -= 0.2

    if sector is None:

        confidence -= 0.1

    confidence = round(max(confidence, 0.2), 2)

    composite_score = (
        (0.6 * financial_norm) + (0.4 * news_norm)
    )

    # Secondary research tilt: revenue trajectory and
    # analyst-implied upside/downside nudge the score
    # without overriding the financial/news blend above.

    if revenue_trend == "growing":

        composite_score += 0.03

    elif revenue_trend == "declining":

        composite_score -= 0.05

    if analyst_upside_pct is not None:

        if analyst_upside_pct >= 15:

            composite_score += 0.05

        elif analyst_upside_pct <= -15:

            composite_score -= 0.05

    composite_score = round(
        min(max(composite_score, 0), 1),
        3,
    )

    # -----------------------------------
    # RECOMMENDATION
    # -----------------------------------

    if composite_score >= 0.65:

        recommendation = "Buy"

    elif composite_score >= 0.45:

        recommendation = "Hold"

    else:

        recommendation = "Avoid"

    # -----------------------------------
    # RATIONALE
    # -----------------------------------

    rationale = []

    if financial_score is not None:

        detail = (
            f": {', '.join(observations)}"
            if observations
            else ""
        )

        rationale.append(
            f"Fundamentals assessed as {assessment}{detail}"
        )

    else:

        rationale.append(
            "Financial data unavailable for this company"
        )

    if sentiment_score is not None and article_count > 0:

        rationale.append(
            f"News sentiment is {overall_sentiment} "
            f"(score {sentiment_score}) across "
            f"{article_count} articles"
        )

    else:

        rationale.append(
            "No recent news coverage found"
        )

    if sector:

        rationale.append(
            f"Operates in the {industry or 'unspecified'} "
            f"industry within the {sector} sector"
        )

    if revenue_trend and revenue_trend != "insufficient_data":

        rationale.append(
            f"Multi-year revenue trend is {revenue_trend}"
        )

    if analyst_upside_pct is not None:

        direction = (
            "upside"
            if analyst_upside_pct >= 0
            else "downside"
        )

        rationale.append(
            f"Analyst target price implies "
            f"{abs(analyst_upside_pct)}% {direction} "
            f"from the current price"
        )

    if beta is not None:

        if beta >= 1.3:
            volatility = "high"
        elif beta <= 0.7:
            volatility = "low"
        else:
            volatility = "moderate"

        rationale.append(
            f"Stock volatility is {volatility} (beta {beta})"
        )

    return {

        "company":
            company,

        "ticker":
            ticker,

        "recommendation":
            recommendation,

        "composite_score":
            composite_score,

        "confidence":
            confidence,

        "rationale":
            rationale,

        "financial_assessment":
            assessment,

        "news_sentiment":
            overall_sentiment,

        "sector":
            sector,

        "industry":
            industry,

        "revenue_trend":
            revenue_trend,

        "analyst_upside_pct":
            analyst_upside_pct,

        "key_risks":
            key_risks,

        "key_catalysts":
            key_catalysts,

        "beta":
            beta,

        "valuation":
            valuation,

    }
