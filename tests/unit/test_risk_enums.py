"""Unit tests for the Week 8 risk enums."""

from risk.enums import (
    PlanStatus,
    PositionSizingMethod,
    RiskStatus,
    StopLossMode,
    TakeProfitMode,
)


def test_position_sizing_method_values():
    assert PositionSizingMethod.FIXED_FRACTIONAL.value == "FIXED_FRACTIONAL"
    assert PositionSizingMethod.FIXED_LOT.value == "FIXED_LOT"
    assert PositionSizingMethod.RISK_BASED.value == "RISK_BASED"


def test_plan_status_values():
    assert PlanStatus.READY.value == "READY"
    assert PlanStatus.REJECTED.value == "REJECTED"
    assert PlanStatus.EXPIRED.value == "EXPIRED"


def test_risk_status_values():
    assert RiskStatus.WITHIN_LIMIT.value == "WITHIN_LIMIT"
    assert RiskStatus.MAX_DRAWDOWN.value == "MAX_DRAWDOWN"
    assert RiskStatus.DAILY_LIMIT.value == "DAILY_LIMIT"
    assert RiskStatus.POSITION_CAP.value == "POSITION_CAP"
    assert RiskStatus.BLOCKED.value == "BLOCKED"


def test_stop_loss_mode_values():
    assert StopLossMode.STRUCTURAL.value == "STRUCTURAL"
    assert StopLossMode.ATR.value == "ATR"
    assert StopLossMode.FIXED_PIPS.value == "FIXED_PIPS"


def test_take_profit_mode_values():
    assert TakeProfitMode.RR_MULTIPLE.value == "RR_MULTIPLE"
    assert TakeProfitMode.STRUCTURAL.value == "STRUCTURAL"
    assert TakeProfitMode.FIXED_PIPS.value == "FIXED_PIPS"

