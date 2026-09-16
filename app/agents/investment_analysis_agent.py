def investment_analysis_agent(state):

    state["current_agent"] = "investment_analysis_agent"

    financial = state.get(
        "financial_analysis",
        {}
    )

    news = state.get(
        "news_analysis",
        {}
    )

    research = state.get(
        "research_analysis",
        {}
    )

    print(
        "\n[Investment Agent] "
        "Synthesizing specialist analyses..."
    )

    state["investment_analysis"] = {

        "financial_analysis": financial,

        "news_analysis": news,

        "research_analysis": research,

        "status": "completed",
    }

    state["audit_log"].append({
        "agent": "investment_analysis_agent",
        "action": "specialist_results_synthesized",
    })

    state["next_action"] = "complete"

    return state