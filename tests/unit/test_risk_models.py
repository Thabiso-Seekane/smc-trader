"""Unit tests for the Week 8 risk models."""

from datetime import datetime, timedelta

import pytest

from risk.enums import PlanStatus, PositionSizingMethod, RiskStatus
from risk.models import PositionSize, RiskMetrics, TradePlan


def make_plan(
    *,
    direction: str = "BUY",
    entry: float = 1.20,
    stop: float = 1.10,
    target: float = 1.40,
    lots: float = 0.10,
    risk_amount: float = 100.0,
    **kwargs,
) -> TradePlan:
    return TradePlan(
        direction=direction,
        entry_price=entry,
        stop_loss=stop,
        take_profit=target,
        position_size=PositionSize(
            lots=lots, risk_amount=risk_amount, account_at_risk_pct=1.0
        ),
        risk_metrics=RiskMetrics(
            account_balance=10000.0,
            risk_percent=1.0,
            risk_amount=risk_amount,
            position_size=PositionSize(lots=lots, risk_amount=risk_amount),
            status=RiskStatus.WITHIN_LIMIT,
        ),
        **kwargs,
    )


def test_plan_buy_direction():
    plan = make_plan(direction="BUY")
    assert plan.is_buy
    assert not plan.is_sell


def test_plan_sell_direction():
    plan = make_plan(direction="SELL")
    assert plan.is_sell
    assert not plan.is_buy


def test_plan_distances():
    plan = make_plan(entry=1.20, stop=1.10, target=1.40)
    assert plan.risk_distance == pytest.approx(0.10)
    assert plan.reward_distance == pytest.approx(0.20)
    assert plan.risk_reward_ratio == pytest.approx(2.0)


def test_plan_is_ready_with_valid_geometry():
    assert make_plan().is_ready


def test_plan_not_ready_when_position_zero():
    plan = make_plan()
    plan.position_size.lots = 0.0
    assert not plan.is_ready


def test_plan_not_ready_when_rejected():
    plan = make_plan(status=PlanStatus.REJECTED)
    assert not plan.is_ready


def test_plan_expired():
    plan = make_plan(expiration=datetime.now() - timedelta(hours=1))
    assert plan.is_expired


def test_plan_not_expired_when_no_expiration():
    plan = make_plan()
    assert not plan.is_expired


def test_plan_is_risk_valid():
    plan = make_plan()
    assert plan.is_risk_valid


def test_plan_not_risk_valid_when_blocked():
    plan = make_plan()
    plan.risk_metrics.status = RiskStatus.BLOCKED
    assert not plan.is_risk_valid


def test_stop_loss_amount_negative():
    plan = make_plan(risk_amount=100.0)
    assert plan.stop_loss_amount == pytest.approx(-100.0)


def test_take_profit_amount_positive():
    plan = make_plan(risk_amount=100.0)  # R:R = 2
    assert plan.take_profit_amount == pytest.approx(100.0 * 2.0)


def test_pnl_at_r():
    plan = make_plan(risk_amount=100.0)
    assert plan.pnl_at_r(-1) == pytest.approx(-100.0)
    assert plan.pnl_at_r(1) == pytest.approx(100.0)
    assert plan.pnl_at_r(2) == pytest.approx(200.0)


def test_position_size_defaults_invalid():
    assert not PositionSize().is_valid


def test_plan_hash_by_id():
    plan = make_plan()
    assert hash(plan) == hash(plan.id)


def test_slots_prevent_new_attributes():
    plan = make_plan()
    with pytest.raises(AttributeError):
        plan.nonexistent_attr = 1

