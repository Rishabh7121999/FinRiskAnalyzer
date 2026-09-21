from typing import Literal

from pydantic import BaseModel, Field


class InvestmentVerdict(BaseModel):

    recommendation: Literal[
        "Buy",
        "Hold",
        "Avoid",
    ]

    confidence: Literal[
        "low",
        "medium",
        "high",
    ]

    thesis: str

    supporting_points: list[str] = Field(
        default_factory=list
    )

    conflicting_signals: list[str] = Field(
        default_factory=list
    )

    key_risks: list[str] = Field(
        default_factory=list
    )

    horizon_note: str | None = None
