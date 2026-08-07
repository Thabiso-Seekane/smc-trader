"""Unit tests for the Week 8 PositionSizer."""

import pytest

from risk.account import Account
from risk.enums import PositionSizingMethod
from risk.position_size import PositionSizer


def test_fixed_lot_uses_min_lots():
    sizer = PositionSizer(
        default_method=PositionSizingMethod.FIXED_LOT, min_lots=0.25
    )
    result = sizer.size(account=Account(), risk_percent=1.0, stop_distance=0.10)
    assert result.lots == pytest.approx(0.25)
    assert result.method == PositionSizingMethod.FIXED_LOT


def test_risk_based():
    sizer = PositionSizer(default_method=PositionSizingMethod.RISK_BASED)
    account = Account(balance=10000.0)
    # risk_amount = 1% of 10000 = 100; lots = 100 / (10 * 0.10) = 100
    result = sizer.size(account=account, risk_percent=1.0, stop_distance=0.10)
    assert result.lots == pytest.approx(100.0)
    assert result.risk_amount == pytest.approx(100.0)


def test_fixed_fractional_default():
    sizer = PositionSizer()
    account = Account(balance=10000.0)
    # risk_amount = 100; lots = 100 / (10 * 0.10) = 100
    result = sizer.size(account=account, risk_percent=1.0, stop_distance=0.10)
    assert result.lots == pytest.approx(100.0)
    assert result.account_at_risk_pct == pytest.approx(1.0)


def test_zero_stop_distance_invalid():
    sizer = PositionSizer()
    result = sizer.size(account=Account(), risk_percent=1.0, stop_distance=0.0)
    assert not result.is_valid


def test_no_account_invalid():
    result = PositionSizer().size(account=None, risk_percent=1.0, stop_distance=0.10)
    assert not result.is_valid
