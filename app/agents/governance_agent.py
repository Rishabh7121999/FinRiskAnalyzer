def governance_agent(state):

    state["current_agent"] = "governance_agent"

    flags = state["governance_flags"]

    risk_score = state["risk_score"]

    confidence = state["confidence_score"]

    # High risk governance checks
    if risk_score > 70:

        flags.append(
            "HIGH_RISK_RECOMMENDATION"
        )

    # Low confidence
    if confidence < 0.5:

        flags.append(
            "LOW_CONFIDENCE_ANALYSIS"
        )

    # Missing data
    if not state["financial_analysis"]:

        flags.append(
            "INCOMPLETE_FINANCIAL_ANALYSIS"
        )

    state["governance_flags"] = list(set(flags))

    state["audit_log"].append({
        "agent": "governance_agent",
        "action": (
            f"Governance checks completed: "
            f"{state['governance_flags']}"
        )
    })

    # Decide next action
    if (
        "LOW_CONFIDENCE_ANALYSIS"
        in state["governance_flags"]
        and state["retry_count"] < state["max_retries"]
    ):

        state["next_action"] = "retry"

    else:

        state["next_action"] = "generate_report"

    return state