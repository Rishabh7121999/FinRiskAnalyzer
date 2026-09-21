from app.agents.governance_agent import DISCLOSURE_TEXT, governance_agent


def test_no_flags_clears_governance_and_disclosure_always_present():
    result = governance_agent(
        {
            "verification_result": {},
            "investment_analysis": {},
            "risk_assessment": {},
            "comparison_analysis": {},
        }
    )

    governance = result["governance_result"]

    assert governance["status"] == "cleared"
    assert governance["flags"] == []
    assert governance["disclosure"] == DISCLOSURE_TEXT
    assert result["requires_human_review"] is False


def test_severe_risk_with_buy_recommendation_flags_high_risk():
    result = governance_agent(
        {
            "verification_result": {},
            "investment_analysis": {"verdicts": {"TEST.NS": {"recommendation": "Buy"}}},
            "risk_assessment": {"assessments": {"TEST.NS": {"risk_level": "Severe"}}},
            "comparison_analysis": {},
        }
    )

    governance = result["governance_result"]

    assert "HIGH_RISK_RECOMMENDATION" in governance["flags"]
    assert "HIGH_RISK_RECOMMENDATION" in governance["per_ticker_flags"]["TEST.NS"]
    assert governance["status"] == "review_required"
    assert result["requires_human_review"] is True


def test_severe_risk_with_avoid_recommendation_does_not_flag():
    result = governance_agent(
        {
            "verification_result": {},
            "investment_analysis": {"verdicts": {"TEST.NS": {"recommendation": "Avoid"}}},
            "risk_assessment": {"assessments": {"TEST.NS": {"risk_level": "Severe"}}},
            "comparison_analysis": {},
        }
    )

    assert result["governance_result"]["flags"] == []
    assert result["requires_human_review"] is False


def test_comparison_ranking_used_when_no_investment_verdict():
    result = governance_agent(
        {
            "verification_result": {},
            "investment_analysis": {},
            "risk_assessment": {"assessments": {"TEST.NS": {"risk_level": "Severe"}}},
            "comparison_analysis": {
                "ranking": [{"ticker": "TEST.NS", "recommendation": "Hold"}]
            },
        }
    )

    assert "HIGH_RISK_RECOMMENDATION" in result["governance_result"]["flags"]


def test_fallback_plus_low_confidence_flags_unreliable_synthesis():
    result = governance_agent(
        {
            "verification_result": {
                "per_ticker_flags": {
                    "TEST.NS": ["LLM_SYNTHESIS_FALLBACK", "LOW_CONFIDENCE"]
                }
            },
            "investment_analysis": {},
            "risk_assessment": {},
            "comparison_analysis": {},
        }
    )

    governance = result["governance_result"]

    assert "UNRELIABLE_SYNTHESIS" in governance["flags"]
    assert "UNRELIABLE_SYNTHESIS" in governance["per_ticker_flags"]["TEST.NS"]
    # The original verification flags are preserved alongside the new one.
    assert "LLM_SYNTHESIS_FALLBACK" in governance["per_ticker_flags"]["TEST.NS"]
    assert result["requires_human_review"] is True


def test_fallback_without_low_confidence_does_not_flag_unreliable_synthesis():
    result = governance_agent(
        {
            "verification_result": {
                "per_ticker_flags": {"TEST.NS": ["LLM_SYNTHESIS_FALLBACK"]}
            },
            "investment_analysis": {},
            "risk_assessment": {},
            "comparison_analysis": {},
        }
    )

    assert "UNRELIABLE_SYNTHESIS" not in result["governance_result"]["flags"]


def test_unreconciled_risk_signal_flags_requires_analyst_reconciliation():
    result = governance_agent(
        {
            "verification_result": {
                "per_ticker_flags": {"TEST.NS": ["UNRECONCILED_RISK_SIGNAL"]}
            },
            "investment_analysis": {},
            "risk_assessment": {},
            "comparison_analysis": {},
        }
    )

    governance = result["governance_result"]

    assert "REQUIRES_ANALYST_RECONCILIATION" in governance["flags"]
    assert result["requires_human_review"] is True


def test_sets_control_flow_and_audit_fields():
    result = governance_agent(
        {
            "verification_result": {},
            "investment_analysis": {},
            "risk_assessment": {},
            "comparison_analysis": {},
        }
    )

    assert result["current_agent"] == "governance_agent"
    assert result["next_action"] == "generate_report"
    assert result["audit_log"][0]["action"] == "governance_checks_completed"
