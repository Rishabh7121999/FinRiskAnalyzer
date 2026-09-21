def _format_investment_section(investment):

    verdicts = (investment or {}).get("verdicts", {})

    if not verdicts:
        return "No investment analysis was generated for this query."

    lines = []

    for ticker, verdict in verdicts.items():

        lines.append(
            f"{verdict.get('company')} ({ticker}): "
            f"{verdict.get('recommendation')} "
            f"(score={verdict.get('composite_score')}, "
            f"confidence={verdict.get('confidence')})"
        )

        thesis = verdict.get("thesis")

        if thesis:
            lines.append(f"  Thesis: {thesis}")

        for point in verdict.get("supporting_points", []):
            lines.append(f"  + {point}")

        for point in verdict.get("conflicting_signals", []):
            lines.append(f"  ~ {point}")

        for point in verdict.get("key_risks", []):
            lines.append(f"  ! {point}")

        horizon_note = verdict.get("horizon_note")

        if horizon_note:
            lines.append(f"  Horizon note: {horizon_note}")

    return "\n".join(lines)


def _format_comparison_section(comparison):

    ranking = (comparison or {}).get("ranking", [])

    if not ranking:
        return "No comparison was generated for this query."

    lines = [
        f"Leader: {comparison.get('leader')}"
    ]

    overall_verdict = comparison.get("overall_verdict")

    if overall_verdict:
        lines.append(f"Verdict: {overall_verdict}")

    leader_rationale = comparison.get("leader_rationale")

    if leader_rationale:
        lines.append(f"Why the leader wins: {leader_rationale}")

    for differentiator in comparison.get("key_differentiators", []):
        lines.append(f"  * {differentiator}")

    lines.append("")

    for verdict in ranking:

        lines.append(
            f"{verdict.get('rank')}. {verdict.get('company')} "
            f"({verdict.get('ticker')}): "
            f"{verdict.get('recommendation')} "
            f"(score={verdict.get('composite_score')})"
        )

    company_notes = comparison.get("company_notes", [])

    if company_notes:

        lines.append("")

        for note in company_notes:
            lines.append(
                f"{note.get('company')}: {note.get('note')}"
            )

    return "\n".join(lines)


def _format_risk_section(risk):

    assessments = (risk or {}).get("assessments", {})

    if not assessments:
        return "No risk assessment was generated for this query."

    lines = []

    for ticker, assessment in assessments.items():

        lines.append(
            f"{assessment.get('company')} ({ticker}): "
            f"{assessment.get('risk_level')} risk "
            f"(score={assessment.get('risk_score')}, "
            f"confidence={assessment.get('confidence')})"
        )

        for dimension_name, dimension in assessment.get("dimensions", {}).items():
            lines.append(
                f"  {dimension_name}: {dimension.get('level')}"
            )

        for factor in assessment.get("top_risk_factors", []):
            lines.append(f"  ! {factor}")

        for factor in assessment.get("mitigating_factors", []):
            lines.append(f"  + {factor}")

        horizon_note = assessment.get("horizon_note")

        if horizon_note:
            lines.append(f"  Horizon note: {horizon_note}")

    return "\n".join(lines)


def report_generator_agent(state):

    print(
        "\n[Report Generator] "
        "Generating final report..."
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

    investment = state.get(
        "investment_analysis",
        {}
    )

    comparison = state.get(
        "comparison_analysis",
        {}
    )

    risk = state.get(
        "risk_assessment",
        {}
    )

    verification = state.get(
        "verification_result",
        {}
    )

    governance = state.get(
        "governance_result",
        {}
    )

    report = f"""
========================================
AI FINANCIAL INTELLIGENCE REPORT
========================================

Companies:
{companies}

Tickers:
{tickers}

----------------------------------------
FINANCIAL ANALYSIS
----------------------------------------

{financial}

----------------------------------------
NEWS ANALYSIS
----------------------------------------

{news}

----------------------------------------
RESEARCH ANALYSIS
----------------------------------------

{research}

----------------------------------------
INVESTMENT ANALYSIS
----------------------------------------

{_format_investment_section(investment)}

----------------------------------------
COMPARISON
----------------------------------------

{_format_comparison_section(comparison)}

----------------------------------------
RISK ASSESSMENT
----------------------------------------

{_format_risk_section(risk)}

----------------------------------------
VERIFICATION
----------------------------------------

{verification}

----------------------------------------
GOVERNANCE
----------------------------------------

{governance}

========================================
"""

    return {

        "final_report":
            report,

        "current_agent":
            "report_generator_agent",

        "next_action":
            "complete",

        "audit_log": [
            {
                "agent":
                    "report_generator_agent",

                "action":
                    "final_report_generated",
            }
        ],

    }