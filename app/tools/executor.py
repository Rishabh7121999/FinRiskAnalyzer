from datetime import datetime

from app.tools.market_data import fetch_stock_data


class ToolExecutor:

    @staticmethod
    def execute_tool(
        state,
        tool_name,
        **kwargs
    ):

        state["audit_log"].append({
            "timestamp": str(datetime.utcnow()),
            "agent": state["current_agent"],
            "tool": tool_name,
            "args": kwargs
        })

        # Tool registry
        if tool_name == "market_data":

            return fetch_stock_data(
                kwargs["ticker"]
            )

        raise ValueError(
            f"Unknown tool: {tool_name}"
        )