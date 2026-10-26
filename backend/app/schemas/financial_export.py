"""Request shape for downloading calculation results and generated narrative."""

from pydantic import BaseModel, Field

from app.schemas.business_plan import ReadinessScoreComponent
from app.schemas.financial_calculation import FinancialCalculationRequest


class FinancialExportRequest(BaseModel):
    financial_inputs: FinancialCalculationRequest
    business_plan: str | None = Field(None, max_length=20_000)
    risks: list[str] = Field(default_factory=list, max_length=100)
    bank_readiness_score: int | None = Field(None, ge=0, le=100)
    bank_readiness_score_note: str | None = Field(None, max_length=1_000)
    bank_readiness_components: list[ReadinessScoreComponent] = Field(default_factory=list)
