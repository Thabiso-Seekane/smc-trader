"""Unit tests for the Week 9 Commission model."""

import pytest

from backtesting.commission import CommissionModel


def test_charge_default():
    model = CommissionModel(per_lot=7.0)
    assert model.charge(1.0) == pytest.approx(14.0)


def test_charge_scales_with_volume():
    model = CommissionModel(per_lot=5.0)
    assert model.charge(2.0) == pytest.approx(20.0)


def test_charge_disabled():
    model = CommissionModel(per_lot=7.0, enabled=False)
    assert model.charge(1.0) == pytest.approx(0.0)


def test_open_close_cost():
    model = CommissionModel(per_lot=7.0)
    assert model.open_cost(1.0) == pytest.approx(7.0)
    assert model.close_cost(1.0) == pytest.approx(7.0)


def test_open_close_cost_disabled():
    model = CommissionModel(per_lot=7.0, enabled=False)
    assert model.open_cost(1.0) == pytest.approx(0.0)
    assert model.close_cost(1.0) == pytest.approx(0.0)
