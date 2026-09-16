from typing import TypedDict, Any
from typing_extensions import Annotated

from app.models.execution_plan import ExecutionPlan


# ============================================================
# REDUCERS
# ============================================================

def merge_dict(existing: dict, new: dict) -> dict:
    return {
        **existing,
        **new,
    }


def merge_list(existing: list, new: list) -> list:
    return existing + new


# ============================================================
# STATE
# ============================================================

class AgentState(TypedDict):

    # --------------------------------------------------------
    # USER INPUT
    # --------------------------------------------------------

    user_query: str


    # --------------------------------------------------------
    # PLANNING
    # --------------------------------------------------------

    execution_plan: ExecutionPlan | None


    # --------------------------------------------------------
    # ENTITY RESOLUTION
    # --------------------------------------------------------

    companies: list[str]

    tickers: list[str]


    # --------------------------------------------------------
    # RAW DATA
    # --------------------------------------------------------

    financial_data: dict[str, Any]

    news_data: list[dict]

    retrieved_documents: list[dict]


    # --------------------------------------------------------
    # SPECIALIST AGENT OUTPUTS
    # --------------------------------------------------------

    financial_analysis: Annotated[
        dict[str, Any],
        merge_dict
    ]

    news_analysis: Annotated[
        dict[str, Any],
        merge_dict
    ]

    research_analysis: Annotated[
        dict[str, Any],
        merge_dict
    ]


    # --------------------------------------------------------
    # PARALLEL TASK TRACKING
    # --------------------------------------------------------

    completed_tasks: Annotated[
        list[str],
        merge_list
    ]


    # --------------------------------------------------------
    # SYNTHESIS
    # --------------------------------------------------------

    investment_analysis: dict[str, Any]


    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    risk_assessment: dict[str, Any]


    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

    verification_result: dict[str, Any]


    # --------------------------------------------------------
    # GOVERNANCE
    # --------------------------------------------------------

    governance_result: dict[str, Any]

    requires_human_review: bool


    # --------------------------------------------------------
    # CONTROL FLOW
    # --------------------------------------------------------

    next_action: str

    retry_count: int

    max_retries: int


    # --------------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------------

    final_report: str


    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    audit_log: list[dict]

    current_agent: str