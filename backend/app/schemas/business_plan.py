"""Validated response format for AI explanations of calculated plans."""

from pydantic import BaseModel, Field


class BusinessPlanNarrative(BaseModel):
    business_plan: str = Field(min_length=1)
    risks: list[str]
    limitations: list[str]


class ReadinessScoreComponent(BaseModel):
    key: str
    label: str
    earned: int
    possible: int
    complete: bool


class BusinessPlanExplanation(BusinessPlanNarrative):
    bank_readiness_score: int = Field(ge=0, le=100)
    bank_readiness_score_status: str = "completeness_only"
    bank_readiness_score_note: str
    bank_readiness_components: list[ReadinessScoreComponent]
