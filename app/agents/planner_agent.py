from app.models.execution_plan import (
    ExecutionPlan,
    TaskType,
)


# ============================================================
# QueryUnderstanding.intent -> ExecutionPlan.intent
# ============================================================
# The two models use intentionally different vocabularies:
# QueryUnderstanding.intent classifies user intent (8 values,
# includes ones with no task-selection logic yet, e.g.
# market_ranking). ExecutionPlan.intent is a coarser label
# that also drives routing after aggregation. This mapping
# bridges them explicitly instead of merging the two enums.
#
# financial_analysis and news_analysis both bucket to
# "company_research" (not "investment_analysis"): a query
# asking only for financials or only for news wants that data
# reported back, not a Buy/Hold/Avoid verdict, so it should
# route straight to report_generator like company_information.
#
# market_ranking buckets to "comparison", not
# "company_research": once market_ranking_agent has resolved a
# sector/criterion into a concrete shortlist of companies (see
# requires_market_ranking below), what the user actually wants
# is the same ranked-with-narrative treatment comparison_analysis
# already gives named companies - not a flat data dump.

#### Company Research ####
#Any query whose ExecutionPlan.intent ends up as "company_research" 
# skips the verdict-synthesis agent entirely and goes straight 
# to report_generator, which just renders whatever the specialist agents produced. 
# It's the bucket for "show me information" queries, 
# as opposed to "tell me whether to buy" (investment_analysis) or 
# "rank these against each other" (comparison).

INTENT_MAP: dict[str, str] = {
    "investment_analysis": "investment_analysis", 
    "risk_analysis": "risk_analysis",
    "news_analysis": "company_research",
    "company_information": "company_research",
    "comparison": "comparison",
    "market_ranking": "comparison",
    "financial_analysis": "company_research",
    "unknown": "unknown",
}


# ============================================================
# QueryUnderstanding.intent -> default specialist tasks
# ============================================================
# Deterministic: intent is already a closed, LLM-classified
# enum by the time it reaches the planner, so which of the 3
# independent specialist tasks to run is a lookup, not
# something that needs another LLM call.
#
# market_ranking runs through market_ranking_agent (not
# entity_resolution) to turn a sector/criterion into a concrete
# company shortlist - see requires_market_ranking below - so by
# the time these tasks run it has the same shape as a
# comparison query and gets full depth on each shortlisted
# company.

INTENT_DEFAULT_TASKS: dict[str, list[TaskType]] = {
    "investment_analysis": [
        "financial_analysis",
        "news_analysis",
        "research_analysis",
    ],
    "company_information": [
        "financial_analysis",
        "research_analysis",
    ],
    "financial_analysis": [
        "financial_analysis",
    ],
    "news_analysis": [
        "news_analysis",
    ],
    "risk_analysis": [
        "financial_analysis",
        "news_analysis",
        "research_analysis",
    ],
    "comparison": [
        "financial_analysis",
        "news_analysis",
        "research_analysis",
    ],
    "market_ranking": [
        "financial_analysis",
        "news_analysis",
        "research_analysis",
    ],
    "unknown": [
        "financial_analysis",
        "news_analysis",
        "research_analysis",
    ],
}


# ============================================================
# analysis_scope -> task override
# ============================================================
# When the user explicitly names a dimension (e.g. "compare
# the financials of X and Y"), it overrides the intent's
# default task set entirely rather than adding to it.

SCOPE_TO_TASK: dict[str, TaskType] = {
    "financial": "financial_analysis",
    "news": "news_analysis",
    "research": "research_analysis",
}


def planner_agent(state):

    qu = state["query_understanding"]

    if qu.analysis_scope:

        tasks: list[TaskType] = [
            SCOPE_TO_TASK[scope]
            for scope in qu.analysis_scope
        ]

    else:

        tasks = INTENT_DEFAULT_TASKS.get(
            qu.intent,
            [],
        )

    plan = ExecutionPlan(

        intent=INTENT_MAP.get(
            qu.intent,
            "unknown",
        ),

        companies=qu.companies,

        tasks=tasks,

        parallel_tasks=tasks,

        requires_financial_analysis=(
            "financial_analysis" in tasks
        ),

        requires_news_analysis=(
            "news_analysis" in tasks
        ),

        requires_research_analysis=(
            "research_analysis" in tasks
        ),

        requires_market_ranking=(
            qu.intent == "market_ranking"
        ),

        sector=qu.sector,

        top_n=qu.top_n,

        ranking_criterion=qu.ranking_criterion,

        horizon=qu.horizon,

        user_goal=qu.user_goal,

    )

    return {

        "execution_plan":
            plan,

        "companies":
            qu.companies,

        "current_agent":
            "planner_agent",

        "next_action":
            "resolve_entities",

        "audit_log": [
            {
                "agent": "planner_agent",
                "action": "execution_plan_created",
                "intent": plan.intent,
                "companies": plan.companies,
                "tasks": plan.tasks,
                "analysis_scope": qu.analysis_scope,
            }
        ],

    }
