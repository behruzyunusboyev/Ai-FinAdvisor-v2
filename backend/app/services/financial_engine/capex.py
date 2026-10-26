"""Capital expenditure input parsing and traceable breakdowns."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping, Sequence


MoneyInput = Decimal | int | float | str


@dataclass(frozen=True)
class EquipmentCost:
    """A single equipment cost supplied by the user, in UZS."""

    name: str | None
    cost: Decimal


@dataclass(frozen=True)
class CapexBreakdown:
    """CAPEX values reported without combining potentially overlapping inputs."""

    equipment_items: tuple[EquipmentCost, ...]
    equipment_total: Decimal
    initial_investment: Decimal | None


def _non_negative_money(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, float, str)):
        raise ValueError(f"{field_name} must be a non-negative number")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a non-negative number") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{field_name} must be a non-negative number")
    return amount


def calculate_capex(
    equipment_list: Sequence[Mapping[str, object]] | None,
    initial_investment: MoneyInput | None,
) -> CapexBreakdown:
    """Return itemized equipment cost and declared startup investment separately.

    The input model describes ``initial_investment`` as the total initial
    investment, which may already include equipment. The two values are kept
    separate to avoid double counting until their relationship is specified.
    """
    equipment_items: list[EquipmentCost] = []
    for index, item in enumerate(equipment_list or []):
        if not isinstance(item, Mapping):
            raise ValueError(f"equipment_list[{index}] must be an object")
        cost = _non_negative_money(item.get("cost"), f"equipment_list[{index}].cost")
        name_value = item.get("name")
        if name_value is not None and not isinstance(name_value, str):
            raise ValueError(f"equipment_list[{index}].name must be a string")
        equipment_items.append(EquipmentCost(name=name_value, cost=cost))

    initial_amount = (
        None
        if initial_investment is None
        else _non_negative_money(initial_investment, "initial_investment")
    )
    equipment_total = sum((item.cost for item in equipment_items), start=Decimal(0))
    return CapexBreakdown(
        equipment_items=tuple(equipment_items),
        equipment_total=equipment_total,
        initial_investment=initial_amount,
    )
