def supervisor_agent(state):

    state["current_agent"] = "supervisor_agent"

    query = state["user_query"]

    state["audit_log"].append({
        "agent": "supervisor_agent",
        "action": "Supervisor initialized workflow"
    })

    state["next_action"] = "entity_resolution"

    return state