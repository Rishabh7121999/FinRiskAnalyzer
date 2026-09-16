from app.tools.executor import ToolExecutor


def fetch_data_agent(state):

    state["current_agent"] = "fetch_data_agent"

    ticker = state["ticker"]

    stock_data = ToolExecutor.execute_tool(
        state,
        tool_name="market_data",
        ticker=ticker
    )

    state["stock_data"] = stock_data

    state["financial_metrics"] = stock_data

    state["audit_log"].append({
        "agent": "fetch_data_agent",
        "action": f"Fetched data for {ticker}"
    })

    return state