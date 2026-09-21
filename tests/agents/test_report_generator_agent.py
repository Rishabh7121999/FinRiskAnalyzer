from app.agents.report_generator_agent import report_generator_agent

from tests.conftest import make_base_state


def test_renders_all_section_headers():
    result = report_generator_agent(make_base_state())

    report = result["final_report"]

    for header in (
        "AI FINANCIAL INTELLIGENCE REPORT",
        "FINANCIAL ANALYSIS",
        "NEWS ANALYSIS",
        "RESEARCH ANALYSIS",
        "INVESTMENT ANALYSIS",
        "COMPARISON",
        "RISK ASSESSMENT",
        "VERIFICATION",
        "GOVERNANCE",
    ):
        assert header in report


def test_missing_downstream_sections_render_defensively():
    # Mirrors a normal investment_analysis run today: risk/verification/
    # governance are absent from state entirely, not just empty.
    state = make_base_state()
    del state["risk_assessment"]
    del state["verification_result"]
    del state["governance_result"]

    result = report_generator_agent(state)

    report = result["final_report"]

    assert "No risk assessment was generated for this query." in report


def test_investment_section_renders_verdict_details():
    state = make_base_state(
        investment_analysis={
            "verdicts": {
                "TEST.NS": {
                    "company": "Test Co",
                    "ticker": "TEST.NS",
                    "recommendation": "Buy",
                    "composite_score": 0.8,
                    "confidence": "high",
                    "thesis": "Strong thesis.",
                    "supporting_points": ["Great growth"],
                    "conflicting_signals": ["Mixed news"],
                    "key_risks": ["Regulatory risk"],
                    "horizon_note": "Absorbs volatility.",
                }
            }
        }
    )

    report = report_generator_agent(state)["final_report"]

    assert "Test Co (TEST.NS): Buy" in report
    assert "Strong thesis." in report
    assert "+ Great growth" in report
    assert "~ Mixed news" in report
    assert "! Regulatory risk" in report
    assert "Absorbs volatility." in report


def test_empty_investment_analysis_renders_placeholder():
    report = report_generator_agent(make_base_state())["final_report"]

    assert "No investment analysis was generated for this query." in report


def test_risk_section_renders_dimensions_and_factors():
    state = make_base_state(
        risk_assessment={
            "assessments": {
                "TEST.NS": {
                    "company": "Test Co",
                    "risk_level": "High",
                    "risk_score": 0.6,
                    "confidence": "medium",
                    "dimensions": {"financial_risk": {"level": "High"}},
                    "top_risk_factors": ["High leverage"],
                    "mitigating_factors": ["Strong cash flow"],
                    "horizon_note": None,
                }
            }
        }
    )

    report = report_generator_agent(state)["final_report"]

    assert "Test Co (TEST.NS): High risk" in report
    assert "financial_risk: High" in report
    assert "! High leverage" in report
    assert "+ Strong cash flow" in report


def test_comparison_section_renders_ranking_and_notes():
    state = make_base_state(
        comparison_analysis={
            "ranking": [
                {"rank": 1, "company": "Leader Co", "ticker": "LEAD.NS", "recommendation": "Buy", "composite_score": 0.8},
            ],
            "leader": "Leader Co",
            "overall_verdict": "Leader Co wins.",
            "leader_rationale": "Better fundamentals.",
            "key_differentiators": ["Growth"],
            "company_notes": [{"company": "Leader Co", "note": "Consistent performer."}],
        }
    )

    report = report_generator_agent(state)["final_report"]

    assert "Leader: Leader Co" in report
    assert "1. Leader Co (LEAD.NS): Buy" in report
    assert "Leader Co: Consistent performer." in report


def test_sets_control_flow_and_audit_fields():
    result = report_generator_agent(make_base_state())

    assert result["current_agent"] == "report_generator_agent"
    assert result["next_action"] == "complete"
    assert result["audit_log"][0]["action"] == "final_report_generated"


def test_verification_section_no_issues_placeholder():
    report = report_generator_agent(make_base_state())["final_report"]

    assert "No verification issues found." in report


def test_verification_section_renders_flags_and_per_ticker():
    state = make_base_state(
        verification_result={
            "status": "flagged",
            "flags": ["MISSING_NEWS_DATA"],
            "per_ticker_flags": {"TEST.NS": ["MISSING_NEWS_DATA"]},
            "checked_tickers": ["TEST.NS"],
        }
    )

    report = report_generator_agent(state)["final_report"]

    assert "Status: flagged" in report
    assert "MISSING_NEWS_DATA" in report
    assert "TEST.NS: ['MISSING_NEWS_DATA']" in report


def test_governance_section_renders_status_flags_and_disclosure():
    state = make_base_state(
        governance_result={
            "status": "review_required",
            "flags": ["HIGH_RISK_RECOMMENDATION"],
            "per_ticker_flags": {"TEST.NS": ["HIGH_RISK_RECOMMENDATION"]},
            "disclosure": "This is not investment advice.",
        }
    )

    report = report_generator_agent(state)["final_report"]

    assert "Status: review_required" in report
    assert "HIGH_RISK_RECOMMENDATION" in report
    assert "This is not investment advice." in report


def test_review_banner_appears_when_flagged_for_human_review():
    state = make_base_state(requires_human_review=True)

    report = report_generator_agent(state)["final_report"]

    assert "FLAGGED FOR HUMAN REVIEW" in report


def test_no_review_banner_when_not_flagged():
    state = make_base_state(requires_human_review=False)

    report = report_generator_agent(state)["final_report"]

    assert "FLAGGED FOR HUMAN REVIEW" not in report
