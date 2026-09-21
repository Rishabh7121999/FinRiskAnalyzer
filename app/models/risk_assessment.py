from typing import Literal

from pydantic import BaseModel, Field


class RiskAssessment(BaseModel):

    risk_level: Literal[
        "Low",
        "Moderate",
        "High",
        "Severe",
    ]

    top_risk_factors: list[str] = Field(
        default_factory=list
    )

    mitigating_factors: list[str] = Field(
        default_factory=list
    )

    horizon_note: str | None = None
