def verification_agent(state):

    state["current_agent"] = "verification_agent"

    flags = []

    confidence = state["confidence_score"]

    score = state["risk_score"]

    # Low confidence
    if confidence < 0.6:
        flags.append("LOW_CONFIDENCE")

    # Missing analysis
    if not state["financial_analysis"]:
        flags.append(
            "MISSING_FINANCIAL_ANALYSIS"
        )

    # Missing sentiment
    if not state["sentiment_analysis"]:
        flags.append(
            "MISSING_SENTIMENT_ANALYSIS"
        )

    # Extreme risk warning
    if score > 70:
        flags.append("HIGH_RISK_STOCK")

    # Decide next step
    if flags and state["retry_count"] < state["max_retries"]:

        state["needs_more_data"] = True

        state["governance_flags"] = flags

        state["next_action"] = "retry"

    else:

        state["needs_more_data"] = False

        state["next_action"] = "generate_report"

    state["verification_result"] = (
        f"Verification flags: {flags}"
    )

    state["audit_log"].append({
        "agent": "verification_agent",
        "action": f"Verification completed: {flags}"
    })

    return state