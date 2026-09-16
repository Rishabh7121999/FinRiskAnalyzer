from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langgraph.types import Send

from app.models.state import AgentState


# ============================================================
# AGENTS
# ============================================================

from app.agents.planner_agent import planner_agent

from app.agents.entity_resolution_agent import (
    entity_resolution_agent
)

from app.agents.financial_analysis_agent import (
    financial_analysis_agent
)

from app.agents.news_analysis_agent import (
    news_analysis_agent
)

from app.agents.research_analysis_agent import (
    research_analysis_agent
)


# ============================================================
# DYNAMIC FAN-OUT
# ============================================================

def fan_out_tasks(state: AgentState):

    plan = state["execution_plan"]

    task_to_node = {

        "financial_analysis":
            "financial_analysis",

        "news_analysis":
            "news_analysis",

        "research_analysis":
            "research_analysis",
    }

    sends = []

    for task in plan.parallel_tasks:

        node = task_to_node.get(task)

        if node is None:
            continue

        sends.append(

            Send(
                node,
                {
                    "user_query": state["user_query"],
                    "companies": state["companies"],
                    "tickers": state["tickers"],
                }
            )

        )

    return sends


# ============================================================
# CREATE GRAPH
# ============================================================

workflow = StateGraph(AgentState)


# ============================================================
# ADD NODES
# ============================================================

workflow.add_node(
    "planner",
    planner_agent
)

workflow.add_node(
    "entity_resolution",
    entity_resolution_agent
)

workflow.add_node(
    "financial_analysis",
    financial_analysis_agent
)

workflow.add_node(
    "news_analysis",
    news_analysis_agent
)

workflow.add_node(
    "research_analysis",
    research_analysis_agent
)


# ============================================================
# START
# ============================================================

workflow.add_edge(
    START,
    "planner"
)


# ============================================================
# PLANNING
# ============================================================

workflow.add_edge(
    "planner",
    "entity_resolution"
)


# ============================================================
# DYNAMIC PARALLEL EXECUTION
# ============================================================

workflow.add_conditional_edges(
    "entity_resolution",
    fan_out_tasks
)


# ============================================================
# TEMPORARY END
#
# We will add proper fan-in next.
# ============================================================

workflow.add_edge(
    "financial_analysis",
    END
)

workflow.add_edge(
    "news_analysis",
    END
)

workflow.add_edge(
    "research_analysis",
    END
)


# ============================================================
# COMPILE
# ============================================================

graph = workflow.compile()