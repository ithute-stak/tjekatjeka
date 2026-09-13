from decimal import Decimal


def money(value: float | int | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def production_total(
    material_cost: float,
    electricity_cost: float = 0,
    water_cost: float = 0,
    labour_cost: float = 0,
    machine_cost: float = 0,
    fuel_cost: float = 0,
    other_cost: float = 0,
) -> Decimal:
    return sum(
        (
            money(material_cost),
            money(electricity_cost),
            money(water_cost),
            money(labour_cost),
            money(machine_cost),
            money(fuel_cost),
            money(other_cost),
        ),
        Decimal("0.00"),
    )


def unit_cost(total_cost: float | Decimal, produced: float, rejected: float = 0) -> Decimal:
    good = Decimal(str(produced)) - Decimal(str(rejected))
    if good <= 0:
        raise ValueError("good production quantity must be greater than zero")
    return (Decimal(str(total_cost)) / good).quantize(Decimal("0.0001"))


def job_profit(
    quote_amount: float,
    material_cost: float,
    labour_cost: float,
    transport_cost: float = 0,
    other_cost: float = 0,
) -> Decimal:
    costs = production_total(material_cost, labour_cost=labour_cost, machine_cost=transport_cost, other_cost=other_cost)
    return money(quote_amount) - costs
