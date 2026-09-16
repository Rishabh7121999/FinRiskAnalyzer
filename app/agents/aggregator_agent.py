def aggregation_agent(state):

    print(
        "\n[Aggregator] "
        "Checking specialist results..."
    )

    plan = state["execution_plan"]

    completed = []

    if state.get("financial_analysis"):
        completed.append("financial_analysis")

    if state.get("news_analysis"):
        completed.append("news_analysis")

    if state.get("research_analysis"):
        completed.append("research_analysis")

    required = set(plan.parallel_tasks)

    completed_set = set(completed)

    if required.issubset(completed_set):

        print(
            "[Aggregator] "
            "All planned tasks completed."
        )

        return {
            "next_action": "investment_analysis"
        }

    print(
        "[Aggregator] "
        "Waiting for remaining tasks."
    )

    return {
        "next_action": "wait"
    }