from decimal import Decimal

import pytest

from app.costing import job_profit, production_total, unit_cost


def test_production_cost_includes_all_direct_costs():
    total = production_total(
        material_cost=5000,
        electricity_cost=500,
        water_cost=100,
        labour_cost=800,
        machine_cost=300,
        fuel_cost=200,
        other_cost=100,
    )
    assert total == Decimal("7000.00")


def test_unit_cost_uses_good_units_only():
    assert unit_cost(7000, produced=3600, rejected=100) == Decimal("2.0000")


def test_unit_cost_rejects_zero_good_output():
    with pytest.raises(ValueError):
        unit_cost(100, produced=10, rejected=10)


def test_aluminium_job_profit():
    assert job_profit(24500, 12900, 2000, 600, 1300) == Decimal("7700.00")
