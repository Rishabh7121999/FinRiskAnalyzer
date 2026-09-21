from pydantic import BaseModel, Field


class ResearchInsight(BaseModel):

    business_overview: str

    competitive_position: str

    key_risks: list[str] = Field(
        default_factory=list
    )

    key_catalysts: list[str] = Field(
        default_factory=list
    )
