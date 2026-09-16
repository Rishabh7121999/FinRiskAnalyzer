from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.tools.ticker_resolver import resolve_ticker

from dotenv import load_dotenv
load_dotenv()

llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite")

from app.tools.ticker_resolver import resolve_ticker


def entity_resolution_agent(state):

    state["current_agent"] = "entity_resolution_agent"

    companies = state["companies"]

    resolved_tickers = []

    for company in companies:

        result = resolve_ticker(company)

        if result:

            resolved_tickers.append(
                result["ticker"]
            )

    state["tickers"] = resolved_tickers

    state["audit_log"].append({
        "agent": "entity_resolution_agent",
        "action": "entities_resolved",
        "companies": companies,
        "tickers": resolved_tickers,
    })

    state["next_action"] = "execute_plan"

    return state