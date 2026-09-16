def retry_agent(state):

    state["current_agent"] = "retry_agent"

    retries = state["retry_count"]

    if retries >= state["max_retries"]:

        state["next_action"] = "generate_report"

        state["audit_log"].append({
            "agent": "retry_agent",
            "action": "Max retries reached"
        })

        return state

    state["retry_count"] += 1

    state["audit_log"].append({
        "agent": "retry_agent",
        "action": (
            "Retrying workflow with additional "
            "analysis cycle"
        )
    })

    # Could route differently later
    state["next_action"] = "fetch_data"

    return state