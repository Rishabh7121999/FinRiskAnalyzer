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