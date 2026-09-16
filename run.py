from app.graph.workflow import graph


initial_state = {

    "user_query":
        "Should I invest in Reliance Industries for the next five years?",

    "execution_plan": None,

    "companies": [],

    "tickers": [],

    "financial_data": {},

    "news_data": [],

    "retrieved_documents": [],


    # Specialist outputs

    "financial_analysis": {},

    "news_analysis": {},

    "research_analysis": {},


    # Parallel tracking

    "completed_tasks": [],


    # Downstream

    "investment_analysis": {},

    "risk_assessment": {},

    "verification_result": {},

    "governance_result": {},

    "requires_human_review": False,


    # Control

    "next_action": "",

    "retry_count": 0,

    "max_retries": 2,


    # Output

    "final_report": "",


    # Audit

    "audit_log": [],

    "current_agent": "",
}


result = graph.invoke(initial_state)

print("\n========== RESULT ==========")

print(result)