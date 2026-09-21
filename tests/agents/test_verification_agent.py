from app.agents.verification_agent import verification_agent


def _verdict(recommendation="Buy", confidence="high", synthesis_status="ok", conflicting_signals=None):
    return {
        "ticker": "TEST.NS",
        "recommendation": recommendation,
        "confidence": confidence,
        "synthesis_status": synthesis_status,
        "conflicting_signals": conflicting_signals or [],
    }


def _assessment(risk_level="Low", confidence="high", synthesis_status="ok"):
    return {
        "ticker": "TEST.NS",
        "risk_level": risk_level,
        "confidence": confidence,
        "synthesis_status": synthesis_status,
    }


def _base_state(**overrides):
    state = {
        "companies": ["Test Co"],
        "tickers": ["TEST.NS"],
        "financial_analysis": {"TEST.NS": {}},
        "news_analysis": {"Test Co": {}},
        "research_analysis": {"TEST.NS": {}},
        "investment_analysis": {"verdicts": {"TEST.NS": _verdict()}},
        "risk_assessment": {"assessments": {"TEST.NS": _assessment()}},
        "comparison_analysis": {},
    }
    state.update(overrides)
    return state


def test_complete_high_confidence_data_produces_ok_status():
    result = verification_agent(_base_state())

    verification = result["verification_result"]

    assert verification["status"] == "ok"
    assert verification["flags"] == []
    assert verification["checked_tickers"] == ["TEST.NS"]


def test_missing_financial_data_is_flagged():
    result = verification_agent(_base_state(financial_analysis={}))

    verification = result["verification_result"]

    assert "MISSING_FINANCIAL_DATA" in verification["flags"]
    assert "MISSING_FINANCIAL_DATA" in verification["per_ticker_flags"]["TEST.NS"]


def test_missing_news_data_is_flagged():
    result = verification_agent(_base_state(news_analysis={}))

    assert "MISSING_NEWS_DATA" in result["verification_result"]["flags"]


def test_missing_research_data_is_flagged():
    result = verification_agent(_base_state(research_analysis={}))

    assert "MISSING_RESEARCH_DATA" in result["verification_result"]["flags"]


def test_llm_synthesis_fallback_flag_from_verdict():
    result = verification_agent(
        _base_state(
            investment_analysis={
                "verdicts": {"TEST.NS": _verdict(synthesis_status="failed: boom")}
            }
        )
    )

    assert "LLM_SYNTHESIS_FALLBACK" in result["verification_result"]["flags"]


def test_llm_synthesis_fallback_flag_from_risk_assessment():
    result = verification_agent(
        _base_state(
            risk_assessment={
                "assessments": {"TEST.NS": _assessment(synthesis_status="failed: boom")}
            }
        )
    )

    assert "LLM_SYNTHESIS_FALLBACK" in result["verification_result"]["flags"]


def test_low_confidence_flag_from_either_verdict_or_assessment():
    result = verification_agent(
        _base_state(
            investment_analysis={"verdicts": {"TEST.NS": _verdict(confidence="low")}}
        )
    )

    assert "LOW_CONFIDENCE" in result["verification_result"]["flags"]


def test_unreconciled_risk_signal_when_buy_meets_severe_risk_with_no_conflict():
    result = verification_agent(
        _base_state(
            investment_analysis={"verdicts": {"TEST.NS": _verdict(recommendation="Buy")}},
            risk_assessment={"assessments": {"TEST.NS": _assessment(risk_level="Severe")}},
        )
    )

    assert "UNRECONCILED_RISK_SIGNAL" in result["verification_result"]["flags"]


def test_no_unreconciled_signal_when_verdict_already_notes_the_conflict():
    result = verification_agent(
        _base_state(
            investment_analysis={
                "verdicts": {
                    "TEST.NS": _verdict(
                        recommendation="Buy",
                        conflicting_signals=["High risk despite strong fundamentals"],
                    )
                }
            },
            risk_assessment={"assessments": {"TEST.NS": _assessment(risk_level="Severe")}},
        )
    )

    assert "UNRECONCILED_RISK_SIGNAL" not in result["verification_result"]["flags"]


def test_comparison_ranking_used_when_no_investment_verdict():
    result = verification_agent(
        _base_state(
            investment_analysis={},
            comparison_analysis={"ranking": [_verdict(recommendation="Buy")]},
            risk_assessment={"assessments": {"TEST.NS": _assessment(risk_level="Severe")}},
        )
    )

    assert "UNRECONCILED_RISK_SIGNAL" in result["verification_result"]["flags"]


def test_sets_control_flow_and_audit_fields():
    result = verification_agent(_base_state())

    assert result["current_agent"] == "verification_agent"
    assert result["next_action"] == "governance"
    assert result["audit_log"][0]["action"] == "verification_completed"
