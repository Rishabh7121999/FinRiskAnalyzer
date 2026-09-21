def verification_agent(state):

    print(
        "\n[Verification Agent] "
        "Checking analysis quality..."
    )

    companies = state.get(
        "companies",
        []
    )

    tickers = state.get(
        "tickers",
        []
    )

    financial = state.get(
        "financial_analysis",
        {}
    )

    news = state.get(
        "news_analysis",
        {}
    )

    research = state.get(
        "research_analysis",
        {}
    )

    investment_verdicts = state.get(
        "investment_analysis",
        {}
    ).get(
        "verdicts",
        {}
    )

    risk_assessments = state.get(
        "risk_assessment",
        {}
    ).get(
        "assessments",
        {}
    )

    comparison_by_ticker = {
        entry["ticker"]: entry
        for entry in state.get(
            "comparison_analysis",
            {}
        ).get(
            "ranking",
            []
        )
    }

    per_ticker_flags = {}

    global_flags = []

    for company, ticker in zip(companies, tickers):

        flags = []

        if ticker not in financial:
            flags.append("MISSING_FINANCIAL_DATA")

        if company not in news:
            flags.append("MISSING_NEWS_DATA")

        if ticker not in research:
            flags.append("MISSING_RESEARCH_DATA")

        verdict = (
            investment_verdicts.get(ticker)
            or comparison_by_ticker.get(ticker)
        )

        assessment = risk_assessments.get(ticker)

        if (
            verdict is not None
            and verdict.get("synthesis_status") != "ok"
        ):
            flags.append("LLM_SYNTHESIS_FALLBACK")

        if (
            assessment is not None
            and assessment.get("synthesis_status") != "ok"
        ):
            flags.append("LLM_SYNTHESIS_FALLBACK")

        if (
            verdict is not None
            and verdict.get("confidence") == "low"
        ):
            flags.append("LOW_CONFIDENCE")

        if (
            assessment is not None
            and assessment.get("confidence") == "low"
        ):
            flags.append("LOW_CONFIDENCE")

        if (
            verdict is not None
            and assessment is not None
            and verdict.get("recommendation") == "Buy"
            and assessment.get("risk_level") in ("High", "Severe")
            and not verdict.get("conflicting_signals")
        ):
            flags.append("UNRECONCILED_RISK_SIGNAL")

        if flags:

            per_ticker_flags[ticker] = sorted(
                set(flags)
            )

            global_flags.extend(flags)

    verification_result = {

        "status":
            "flagged" if global_flags else "ok",

        "flags":
            sorted(set(global_flags)),

        "per_ticker_flags":
            per_ticker_flags,

        "checked_tickers":
            tickers,

    }

    return {

        "verification_result":
            verification_result,

        "current_agent":
            "verification_agent",

        "next_action":
            "governance",

        "audit_log": [
            {
                "agent":
                    "verification_agent",

                "action":
                    "verification_completed",

                "status":
                    verification_result["status"],

                "flags":
                    verification_result["flags"],
            }
        ],

    }
