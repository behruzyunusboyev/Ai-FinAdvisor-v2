from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.schemas.financial_calculation import FinancialCalculationRequest
from app.services.financial_plan_service import calculate_financial_plan


@pytest.fixture
def settings() -> SimpleNamespace:
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


def test_plan_service_returns_only_engine_calculations(settings: SimpleNamespace) -> None:
    request = FinancialCalculationRequest(
        equipment_list=[{"name": "Oven", "cost": 12_000_000}],
        initial_investment=50_000_000,
        employee_count=2,
        average_salary=3_000_000,
        rent_monthly=5_000_000,
        utilities_monthly=1_000_000,
        annual_revenue_excluding_vat=100_000_000,
        tax_regime="general",
        annual_net_income_after_tax=10_000_000,
    )

    result = calculate_financial_plan(request, settings)

    assert result["capex"]["equipment_total"] == Decimal("12000000")
    assert result["monthly_opex"]["total"] == Decimal("12000000")
    assert result["annual_taxes"]["output_vat"] == Decimal("12000000")
    assert result["roi"]["roi_percent"] == Decimal("20")
    assert result["loan_schedule"] is None
    assert result["break_even"] is None


def test_plan_service_rejects_incomplete_tax_inputs(settings: SimpleNamespace) -> None:
    request = FinancialCalculationRequest(tax_regime="general")

    with pytest.raises(ValueError, match="annual_revenue_excluding_vat"):
        calculate_financial_plan(request, settings)
