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

from app.agents.query_agent import (
    query_agent
)

from app.agents.planner_agent import (
    planner_agent
)

from app.agents.entity_resolution_agent import (
    entity_resolution_agent
)

from app.agents.market_ranking_agent import (
    market_ranking_agent
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

from app.agents.aggregation_agent import (
    aggregation_agent
)

from app.agents.investment_analysis_agent import (
    investment_analysis_agent
)

from app.agents.risk_analysis_agent import (
    risk_analysis_agent
)

from app.agents.comparison_analysis_agent import (
    comparison_analysis_agent
)

from app.agents.verification_agent import (
    verification_agent
)

from app.agents.governance_agent import (
    governance_agent
)

from app.agents.report_generator_agent import (
    report_generator_agent
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

        node = task_to_node.get(
            task
        )

        if node is None:
            continue

        sends.append(

            Send(
                node,
                {
                    "user_query":
                        state["user_query"],

                    "companies":
                        state["companies"],

                    "tickers":
                        state["tickers"],
                }
            )
        )

    return sends


# ============================================================
# ROUTING AFTER PLANNER
# ============================================================
# market_ranking has no named companies for entity_resolution
# to resolve - it has a sector/criterion instead. It routes to
# market_ranking_agent, which resolves that into a concrete
# company/ticker shortlist and rejoins the normal fan-out.

def route_after_planner(
    state: AgentState
):

    if state["execution_plan"].requires_market_ranking:
        return "market_ranking"

    return "entity_resolution"


# ============================================================
# ROUTING AFTER AGGREGATION
# ============================================================

def route_after_aggregation(
    state: AgentState
):

    intent = state["execution_plan"].intent

    if intent == "comparison":
        return "comparison_analysis"

    if intent in ("company_research", "news_analysis"):
        # No synthesis agent runs for these intents, but the
        # report still goes through verification/governance
        # for consistency - verification degrades gracefully
        # to a specialist-data-completeness check when no
        # verdict/risk read exists.
        return "verification"

    # investment_analysis and risk_analysis (and the
    # "unknown" fallback) both want a per-company verdict
    # and a per-company risk read - these are independent
    # lenses over the same aggregated data, not alternatives,
    # so both run rather than picking one.
    return ["investment_analysis", "risk_analysis"]


# ============================================================
# CREATE GRAPH
# ============================================================

workflow = StateGraph(
    AgentState
)


# ============================================================
# ADD NODES
# ============================================================

workflow.add_node(
    "query_understanding",
    query_agent
)

workflow.add_node(
    "planner",
    planner_agent
)

workflow.add_node(
    "entity_resolution",
    entity_resolution_agent
)

workflow.add_node(
    "market_ranking",
    market_ranking_agent
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

workflow.add_node(
    "aggregation",
    aggregation_agent
)

workflow.add_node(
    "investment_analysis",
    investment_analysis_agent
)

workflow.add_node(
    "risk_analysis",
    risk_analysis_agent
)

workflow.add_node(
    "comparison_analysis",
    comparison_analysis_agent
)

workflow.add_node(
    "verification",
    verification_agent
)

workflow.add_node(
    "governance",
    governance_agent
)

workflow.add_node(
    "report_generator",
    report_generator_agent
)


# ============================================================
# START → QUERY UNDERSTANDING
# ============================================================

workflow.add_edge(
    START,
    "query_understanding"
)


# ============================================================
# QUERY UNDERSTANDING → PLANNER
# ============================================================

workflow.add_edge(
    "query_understanding",
    "planner"
)


# ============================================================
# PLANNER → ENTITY RESOLUTION | MARKET RANKING
# ============================================================

workflow.add_conditional_edges(

    "planner",

    route_after_planner,

    {
        "entity_resolution":
            "entity_resolution",

        "market_ranking":
            "market_ranking",
    }
)


# ============================================================
# ENTITY RESOLUTION | MARKET RANKING → PARALLEL TASKS
# ============================================================

workflow.add_conditional_edges(
    "entity_resolution",
    fan_out_tasks
)

workflow.add_conditional_edges(
    "market_ranking",
    fan_out_tasks
)


# ============================================================
# PARALLEL TASKS → AGGREGATOR
# ============================================================

workflow.add_edge(
    "financial_analysis",
    "aggregation"
)

workflow.add_edge(
    "news_analysis",
    "aggregation"
)

workflow.add_edge(
    "research_analysis",
    "aggregation"
)


# ============================================================
# AGGREGATOR → INTENT-BASED ROUTING
# ============================================================

workflow.add_conditional_edges(

    "aggregation",

    route_after_aggregation,

    {
        "investment_analysis":
            "investment_analysis",

        "risk_analysis":
            "risk_analysis",

        "comparison_analysis":
            "comparison_analysis",

        "verification":
            "verification",
    }
)


# ============================================================
# INVESTMENT / RISK / COMPARISON → VERIFICATION
# ============================================================
# Every intent funnels through verification -> governance
# before the report is generated, not just the investment/
# risk path - comparison and specialist-only reports get the
# same QA/compliance gate.

workflow.add_edge(
    "investment_analysis",
    "verification"
)

workflow.add_edge(
    "risk_analysis",
    "verification"
)

workflow.add_edge(
    "comparison_analysis",
    "verification"
)


# ============================================================
# VERIFICATION → GOVERNANCE → REPORT
# ============================================================

workflow.add_edge(
    "verification",
    "governance"
)

workflow.add_edge(
    "governance",
    "report_generator"
)


# ============================================================
# REPORT → END
# ============================================================

workflow.add_edge(
    "report_generator",
    END
)


# ============================================================
# COMPILE
# ============================================================

graph = workflow.compile()