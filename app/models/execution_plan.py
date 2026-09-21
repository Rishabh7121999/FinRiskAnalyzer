from typing import Literal

from pydantic import BaseModel, Field


TaskType = Literal[
    "financial_analysis",
    "news_analysis",
    "research_analysis",
]


class ExecutionPlan(BaseModel):

    intent: Literal[
        "investment_analysis",
        "risk_analysis",
        "news_analysis",
        "company_research",
        "comparison",
        "unknown",
    ]

    companies: list[str] = Field(
        default_factory=list
    )

    tasks: list[TaskType] = Field(
        default_factory=list
    )

    parallel_tasks: list[TaskType] = Field(
        default_factory=list
    )

    requires_financial_analysis: bool = False

    requires_news_analysis: bool = False

    requires_research_analysis: bool = False

    requires_human_review: bool = False

    # market_ranking only: routes planner -> market_ranking_agent
    # instead of -> entity_resolution, since a sector/screening
    # query has no named companies for entity resolution to work
    # with - market_ranking_agent produces the company list.
    requires_market_ranking: bool = False

    sector: str | None = None

    top_n: int | None = None

    ranking_criterion: str | None = None

    horizon: str | None = None

    user_goal: str | None = None