"""Operating break-even and return-on-investment calculations."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping, Sequence

from app.services.financial_engine.capex import MoneyInput, _non_negative_money


@dataclass(frozen=True)
class MenuSalesMixItem:
    """One menu item and its forecast monthly sales volume."""

    name: str
    price: MoneyInput
    unit_cost: MoneyInput
    expected_monthly_units: int


@dataclass(frozen=True)
class BreakEvenResult:
    """Operating break-even for a constant menu sales mix."""

    monthly_fixed_costs: Decimal
    expected_monthly_units: int
    expected_monthly_revenue: Decimal
    contribution_margin_ratio: Decimal
    average_contribution_per_unit: Decimal
    break_even_revenue: Decimal
    break_even_total_units: Decimal
    item_break_even_units: dict[str, Decimal]


@dataclass(frozen=True)
class RoiResult:
    """Return on the full initial investment for one annual period."""

    annual_net_income_after_tax: Decimal
    initial_investment: Decimal
    roi_percent: Decimal


def calculate_break_even(
    *,
    monthly_fixed_costs: MoneyInput,
    menu_items: Sequence[MenuSalesMixItem | Mapping[str, object]],
) -> BreakEvenResult:
    """Calculate operating break-even, holding forecast sales mix constant.

    Fixed costs should include the costs the caller wants this operating
    break-even to cover. The calculation excludes financing and income taxes.
    """
    fixed_costs = _non_negative_money(monthly_fixed_costs, "monthly_fixed_costs")
    normalized_items: list[MenuSalesMixItem] = []
    for index, item in enumerate(menu_items):
        if isinstance(item, MenuSalesMixItem):
            normalized_items.append(item)
            continue
        if not isinstance(item, Mapping):
            raise ValueError(f"menu_items[{index}] must be an object")
        name = item.get("name")
        units = item.get("expected_monthly_units")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"menu_items[{index}].name must be a non-empty string")
        if isinstance(units, bool) or not isinstance(units, int) or units < 0:
            raise ValueError(
                f"menu_items[{index}].expected_monthly_units must be a "
                "non-negative integer"
            )
        normalized_items.append(
            MenuSalesMixItem(
                name=name,
                price=item.get("price"),
                unit_cost=item.get("cost"),
                expected_monthly_units=units,
            )
        )

    if not normalized_items:
        raise ValueError("menu_items must contain at least one item")
    for index, item in enumerate(normalized_items):
        if not isinstance(item.name, str) or not item.name.strip():
            raise ValueError(f"menu_items[{index}].name must be a non-empty string")
        units = item.expected_monthly_units
        if isinstance(units, bool) or not isinstance(units, int) or units < 0:
            raise ValueError(
                f"menu_items[{index}].expected_monthly_units must be a "
                "non-negative integer"
            )
    if len({item.name for item in normalized_items}) != len(normalized_items):
        raise ValueError("menu item names must be unique")

    expected_units = sum(item.expected_monthly_units for item in normalized_items)
    if expected_units == 0:
        raise ValueError("expected monthly sales must include at least one unit")

    total_revenue = Decimal(0)
    total_contribution = Decimal(0)
    unit_values: list[tuple[str, Decimal, int]] = []
    for item in normalized_items:
        price = _non_negative_money(item.price, f"{item.name}.price")
        unit_cost = _non_negative_money(item.unit_cost, f"{item.name}.cost")
        contribution = price - unit_cost
        total_revenue += price * item.expected_monthly_units
        total_contribution += contribution * item.expected_monthly_units
        unit_values.append((item.name, contribution, item.expected_monthly_units))

    if total_revenue <= 0 or total_contribution <= 0:
        raise ValueError("forecast menu mix must have a positive contribution margin")

    margin_ratio = total_contribution / total_revenue
    average_contribution = total_contribution / Decimal(expected_units)
    break_even_revenue = fixed_costs / margin_ratio
    break_even_units = fixed_costs / average_contribution
    item_break_even_units = {
        name: break_even_units * Decimal(units) / Decimal(expected_units)
        for name, _, units in unit_values
    }
    return BreakEvenResult(
        monthly_fixed_costs=fixed_costs,
        expected_monthly_units=expected_units,
        expected_monthly_revenue=total_revenue,
        contribution_margin_ratio=margin_ratio,
        average_contribution_per_unit=average_contribution,
        break_even_revenue=break_even_revenue,
        break_even_total_units=break_even_units,
        item_break_even_units=item_break_even_units,
    )


def calculate_roi(
    *,
    annual_net_income_after_tax: MoneyInput,
    initial_investment: MoneyInput,
) -> RoiResult:
    """Calculate annual after-tax net income as a percentage of investment."""
    try:
        net_income = Decimal(str(annual_net_income_after_tax))
    except InvalidOperation as exc:
        raise ValueError("annual_net_income_after_tax must be a number") from exc
    if not net_income.is_finite():
        raise ValueError("annual_net_income_after_tax must be a finite number")
    investment = _non_negative_money(initial_investment, "initial_investment")
    if investment == 0:
        raise ValueError("initial_investment must be greater than zero")
    return RoiResult(
        annual_net_income_after_tax=net_income,
        initial_investment=investment,
        roi_percent=net_income / investment * Decimal(100),
    )
