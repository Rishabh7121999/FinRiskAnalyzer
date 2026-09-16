def execute_plan(state):

    state["current_agent"] = "execution_agent"

    plan = state["execution_plan"]

    print("\n========== EXECUTION PLAN ==========")

    print("Intent:", plan.intent)
    print("Companies:", plan.companies)
    print("Tasks:", plan.tasks)
    print("Parallel Tasks:", plan.parallel_tasks)

    state["audit_log"].append({
        "agent": "execution_agent",
        "action": "execution_plan_received",
        "tasks": plan.tasks,
        "parallel_tasks": plan.parallel_tasks,
    })

    state["next_action"] = "complete"

    return state