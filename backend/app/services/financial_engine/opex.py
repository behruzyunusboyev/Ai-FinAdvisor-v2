"""Monthly operating cost calculations using explicitly supplied inputs."""

from dataclasses import dataclass
from decimal import Decimal

from app.services.financial_engine.capex import MoneyInput, _non_negative_money


@dataclass(frozen=True)
class MonthlyOpex:
    """Monthly operating cost components, in UZS."""

    payroll: Decimal | None
    rent: Decimal | None
    utilities: Decimal | None
    total: Decimal | None


def calculate_monthly_opex(
    employee_count: int | None,
    average_salary: MoneyInput | None,
    rent_monthly: MoneyInput | None,
    utilities_monthly: MoneyInput | None,
) -> MonthlyOpex:
    """Calculate known monthly OPEX and leave incomplete components unknown."""
    if employee_count is not None and (
        isinstance(employee_count, bool)
        or not isinstance(employee_count, int)
        or employee_count < 0
    ):
        raise ValueError("employee_count must be a non-negative integer")

    salary = (
        None
        if average_salary is None
        else _non_negative_money(average_salary, "average_salary")
    )
    if employee_count == 0:
        payroll = Decimal(0)
    elif employee_count is not None and salary is not None:
        payroll = Decimal(employee_count) * salary
    else:
        payroll = None

    rent = None if rent_monthly is None else _non_negative_money(rent_monthly, "rent_monthly")
    utilities = (
        None
        if utilities_monthly is None
        else _non_negative_money(utilities_monthly, "utilities_monthly")
    )
    components = (payroll, rent, utilities)
    total = (
        sum(components, start=Decimal(0))
        if all(component is not None for component in components)
        else None
    )
    return MonthlyOpex(
        payroll=payroll,
        rent=rent,
        utilities=utilities,
        total=total,
    )
