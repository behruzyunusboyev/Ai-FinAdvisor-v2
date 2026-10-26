"""Deterministic, configurable completeness score for a draft financing plan."""

from dataclasses import dataclass
from typing import Any

from app.domain.financial import TaxRegime
from app.schemas.financial_calculation import FinancialCalculationRequest


@dataclass(frozen=True)
class ReadinessComponent:
    key: str
    label: str
    earned: int
    possible: int
    complete: bool


@dataclass(frozen=True)
class ReadinessScore:
    score: int
    status: str
    note: str
    components: list[ReadinessComponent]


def calculate_readiness_score(
    *,
    payload: FinancialCalculationRequest,
    results: dict[str, Any],
    settings: object,
) -> ReadinessScore:
    """Score input/result completeness only; this is not a credit decision."""
    has_capex = bool(payload.equipment_list)
    opex_complete = (
        results["monthly_opex"]["total"] is not None
        and payload.employee_count is not None
        and (payload.employee_count == 0 or payload.average_salary is not None)
        and payload.rent_monthly is not None
        and payload.utilities_monthly is not None
    )
    tax_data_complete = (
        payload.annual_revenue_excluding_vat is not None
        and payload.tax_regime is not None
    )
    if payload.tax_regime in (TaxRegime.GENERAL, TaxRegime.VAT_PAYER):
        tax_data_complete = tax_data_complete and (
            payload.annual_input_vat is not None
            and payload.annual_taxable_profit is not None
        )
    sales_tax_complete = tax_data_complete and results["annual_taxes"] is not None
    investment_roi_complete = (
        payload.initial_investment is not None
        and payload.initial_investment > 0
        and results["roi"] is not None
    )
    loan_complete = results["loan_schedule"] is not None
    payroll_tax_inputs_complete = (
        payload.employee_count is not None
        and (payload.employee_count == 0 or payload.average_salary is not None)
    )
    tax_output_complete = sales_tax_complete and payroll_tax_inputs_complete

    checks = (
        ("capex", "Uskunalar va boshlang‘ich xarajatlar", has_capex,
         settings.READINESS_WEIGHT_CAPEX),
        ("opex", "Oylik operatsion xarajatlar", opex_complete,
         settings.READINESS_WEIGHT_OPEX),
        ("sales_tax", "Yillik tushum va soliq rejimi", sales_tax_complete,
         settings.READINESS_WEIGHT_SALES_TAX),
        ("investment_roi", "Investitsiya va ROI prognozi", investment_roi_complete,
         settings.READINESS_WEIGHT_INVESTMENT_ROI),
        ("loan", "Kredit shartlari va to‘lov grafigi", loan_complete,
         settings.READINESS_WEIGHT_LOAN),
        ("tax_output", "Soliq hisob-kitobi", tax_output_complete,
         settings.READINESS_WEIGHT_TAX_OUTPUT),
    )
    possible_total = sum(possible for _, _, _, possible in checks)
    if possible_total != 100 or any(possible < 0 for _, _, _, possible in checks):
        raise ValueError("readiness rubric weights must be non-negative and total 100")

    components = [
        ReadinessComponent(
            key=key,
            label=label,
            earned=possible if complete else 0,
            possible=possible,
            complete=complete,
        )
        for key, label, complete, possible in checks
    ]
    return ReadinessScore(
        score=sum(component.earned for component in components),
        status="completeness_only",
        note=(
            "Bu ball faqat loyiha moliyaviy ma’lumotlarining to‘liqligini "
            "ko‘rsatadi; bankning kredit qarori yoki tasdiqlash ehtimoli emas."
        ),
        components=components,
    )
