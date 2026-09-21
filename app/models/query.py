from typing import Literal

from pydantic import BaseModel, Field


class QueryUnderstanding(BaseModel):

    intent: Literal[
        "investment_analysis",
        "company_information",
        "financial_analysis",
        "news_analysis",
        "comparison",
        "market_ranking",
        "risk_analysis",
        "unknown",
    ]

    companies: list[str] = Field(
        default_factory=list
    )

    comparison_companies: list[str] = Field(
        default_factory=list
    )

    horizon: str | None = None

    sector: str | None = None

    market: str | None = None

    top_n: int | None = None

    ranking_criterion: str | None = None

    # Only set when the query explicitly restricts analysis to
    # one or more dimensions (e.g. "compare the financials of
    # X and Y", "what's the latest news on X"). Empty means no
    # restriction - the planner falls back to the intent's
    # default task set.
    analysis_scope: list[
        Literal[
            "financial",
            "news",
            "research",
        ]
    ] = Field(
        default_factory=list
    )

    user_goal: str

    constraints: list[str] = Field(
        default_factory=list
    )
