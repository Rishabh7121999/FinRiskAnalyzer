from pydantic import BaseModel, Field


class CompanyComparisonNote(BaseModel):

    company: str

    note: str


class ComparisonInsight(BaseModel):

    overall_verdict: str

    leader_rationale: str

    key_differentiators: list[str] = Field(
        default_factory=list
    )

    company_notes: list[CompanyComparisonNote] = Field(
        default_factory=list
    )
