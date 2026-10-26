from types import SimpleNamespace

from app.schemas.financial_calculation import FinancialCalculationRequest
from app.services.financial_plan_service import calculate_financial_plan
from app.services.readiness_score import calculate_readiness_score


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        UZB_VAT_RATE=12,
        UZB_PROFIT_TAX_RATE=15,
        UZB_INCOME_TAX_RATE=12,
        UZB_SOCIAL_TAX_RATE=12,
        UZB_TURNOVER_TAX_RATE=4,
        UZB_SIMPLIFIED_VAT_RATE=6,
        UZB_BASE_CALCULATION_AMOUNT=440_000,
        UZB_TURNOVER_TAX_LIMIT_BHM=12_000,
        READINESS_WEIGHT_CAPEX=10,
        READINESS_WEIGHT_OPEX=20,
        READINESS_WEIGHT_SALES_TAX=20,
        READINESS_WEIGHT_INVESTMENT_ROI=20,
        READINESS_WEIGHT_LOAN=20,
        READINESS_WEIGHT_TAX_OUTPUT=10,
    )


def test_readiness_score_is_deterministic_and_explains_each_weight() -> None:
    settings = _settings()
    payload = FinancialCalculationRequest(
        equipment_list=[{"name": "Oven", "cost": 1_000_000}],
        employee_count=1,
        average_salary=2_000_000,
        rent_monthly=1_000_000,
        utilities_monthly=100_000,
        initial_investment=20_000_000,
        annual_revenue_excluding_vat=100_000_000,
        annual_input_vat=5_000_000,
        annual_taxable_profit=10_000_000,
        annual_net_income_after_tax=5_000_000,
        tax_regime="general",
        loan_amount=10_000_000,
        loan_term_months=12,
        loan_interest_rate=12,
        loan_repayment_method="annuity",
    )
    results = calculate_financial_plan(payload, settings)

    score = calculate_readiness_score(
        payload=payload,
        results=results,
        settings=settings,
    )

    assert score.score == 100
    assert score.status == "completeness_only"
    assert sum(item.possible for item in score.components) == 100
    assert all(item.complete for item in score.components)
    assert "kredit qarori emas" in score.note


def test_readiness_score_does_not_award_missing_financial_sections() -> None:
    settings = _settings()
    payload = FinancialCalculationRequest()
    results = calculate_financial_plan(payload, settings)

    score = calculate_readiness_score(
        payload=payload,
        results=results,
        settings=settings,
    )

    assert score.score == 0
    assert not any(item.complete for item in score.components)
