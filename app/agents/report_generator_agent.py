def report_generator_agent(state):

    state["current_agent"] = "report_generator_agent"

    company = state["company_name"]

    governance_flags = "\n".join(
        state["governance_flags"]
    )

    report = f"""
========================================
AI RISK INTELLIGENCE REPORT
========================================

Company:
{company}

Ticker:
{state['ticker']}

----------------------------------------
FINANCIAL ANALYSIS
----------------------------------------

{state['financial_analysis']}

----------------------------------------
SENTIMENT ANALYSIS
----------------------------------------

{state['sentiment_analysis']}

----------------------------------------
RISK ASSESSMENT
----------------------------------------

Risk Score:
{state['risk_score']}

Confidence Score:
{state['confidence_score']}

----------------------------------------
VERIFICATION
----------------------------------------

{state['verification_result']}

----------------------------------------
GOVERNANCE FLAGS
----------------------------------------

{governance_flags}
"""

    state["final_report"] = report

    state["audit_log"].append({
        "agent": "report_generator_agent",
        "action": "Generated final report"
    })

    return state