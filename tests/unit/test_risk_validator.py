"""Unit tests for the Week 8 RiskValidator."""

from risk.account import Account
from risk.enums import PlanStatus, PositionSizingMethod, RiskStatus
from risk.models import PositionSize, RiskMetrics, TradePlan
from risk.validator import RiskValidator


def make_plan(
    *,
    entry: float = 1.20,
    stop: float = 1.10,
    target: float = 1.40,
    lots: float = 0.10,
    risk_percent: float = 1.0,
    status: RiskStatus = RiskStatus.WITHIN_LIMIT,
) -> TradePlan:
    return TradePlan(
        direction="BUY",
        entry_price=entry,
        stop_loss=stop,
        take_profit=target,
        position_size=PositionSize(lots=lots, risk_amount=100.0),
        risk_metrics=RiskMetrics(
            account_balance=10000.0,
            risk_percent=risk_percent,
            risk_amount=100.0,
            position_size=PositionSize(lots=lots, risk_amount=100.0),
            status=status,
        ),
    )


def test_valid_plan_passes():
    validator = RiskValidator()
    valid, reasons = validator.validate(make_plan())
    assert valid
    assert reasons == []


def test_rejects_zero_risk_distance():
    validator = RiskValidator()
    valid, reasons = validator.validate(make_plan(entry=1.20, stop=1.20, target=1.40))
    assert not valid
    assert any("Risk distance" in r for r in reasons)


def test_rejects_zero_reward_distance():
    validator = RiskValidator()
    valid, reasons = validator.validate(make_plan(entry=1.20, stop=1.10, target=1.20))
    assert not valid
    assert any("Reward distance" in r for r in reasons)


def test_rejects_low_rr():
    validator = RiskValidator(min_rr=2.0)
    # R:R = 1.0 (risk 0.10, reward 0.10)
    valid, reasons = validator.validate(make_plan(entry=1.20, stop=1.10, target=1.30))
    assert not valid
    assert any("R:R" in r for r in reasons)


def test_rejects_over_risk_percent():
    validator = RiskValidator(max_risk_percent=5.0)
    valid, reasons = validator.validate(make_plan(risk_percent=10.0))
    assert not valid
    assert any("risk" in r.lower() and "above" in r.lower() for r in reasons)


def test_rejects_zero_position():
    validator = RiskValidator()
    valid, reasons = validator.validate(make_plan(lots=0.0))
    assert not valid
    assert any("Position size" in r for r in reasons)


def test_rejects_blocked_account():
    validator = RiskValidator()
    valid, reasons = validator.validate(
        make_plan(), account=Account(blocked=True)
    )
    assert not valid
    assert any("Account status" in r for r in reasons)


def test_apply_sets_rejected_status():
    validator = RiskValidator(min_rr=2.0)
    plan = make_plan(entry=1.20, stop=1.10, target=1.30)  # R:R = 1
    result = validator.apply(plan)
    assert result.status == PlanStatus.REJECTED
    assert result.note != ""
