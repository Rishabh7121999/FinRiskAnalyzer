def risk_scoring_agent(state):

    state["current_agent"] = "risk_scoring_agent"

    metrics = state["financial_metrics"]

    score = 0

    debt = metrics.get("debt_to_equity") or 0
    pe = metrics.get("trailing_pe") or 0
    growth = metrics.get("revenue_growth") or 0
    margins = metrics.get("profit_margins") or 0

    risk_factors = []

    # Debt risk
    if debt > 150:
        score += 40
        risk_factors.append(
            "High debt-to-equity ratio"
        )

    # Valuation risk
    if pe > 40:
        score += 30
        risk_factors.append(
            "High P/E valuation"
        )

    # Growth risk
    if growth < 0:
        score += 20
        risk_factors.append(
            "Negative revenue growth"
        )

    # Profitability risk
    if margins < 0:
        score += 20
        risk_factors.append(
            "Negative profit margins"
        )

    # Confidence calculation
    confidence = 1.0

    if pe == 0:
        confidence -= 0.2

    if growth == 0:
        confidence -= 0.2

    if debt == 0:
        confidence -= 0.1

    confidence = max(confidence, 0.1)

    state["risk_score"] = score

    state["confidence_score"] = confidence

    state["audit_log"].append({
        "agent": "risk_scoring_agent",
        "action": (
            f"Risk score={score}, "
            f"confidence={confidence}"
        )
    })

    state["next_action"] = "verification"

    return state