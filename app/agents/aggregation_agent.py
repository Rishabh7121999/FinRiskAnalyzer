def aggregation_agent(state):

    print(
        "\n[Aggregator] "
        "Checking specialist results..."
    )

    required = set(
        state["execution_plan"].parallel_tasks
    )

    completed = set(
        state.get("completed_tasks", [])
    )

    print(
        f"[Aggregator] Required: {required}"
    )

    print(
        f"[Aggregator] Completed: {completed}"
    )

    if required.issubset(completed):

        print(
            "[Aggregator] "
            "All planned tasks completed."
        )

        return {
            "next_action": "investment_analysis"
        }

    print(
        "[Aggregator] "
        "Specialist tasks are incomplete."
    )

    return {
        "next_action": "wait"
    }