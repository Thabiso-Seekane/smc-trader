"""Unit tests for the Week 8 RiskAnalyzer."""

import pytest

from risk.account import Account
from risk.analyzer import RiskAnalyzer
from risk.enums import PlanStatus


class FakeZone:
    """Minimal stand-in for a Week 7 strategy TradeZone."""

    def __init__(
        self,
        direction="BUY",
        entry_price=1.20,
        stop_loss=1.10,
        target=1.40,
        confluence_score=80.0,
    ):
        self.direction = _EnumLike(direction)
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.target = target
        self.confluence_score = confluence_score


class _EnumLike:
    def __init__(self, value):
        self.value = value


def test_plan_from_explicit_geometry():
    analyzer = RiskAnalyzer()
    plan = analyzer.plan(
        account=Account(balance=10000.0),
        direction="BUY",
        entry=1.20,
        stop=1.10,
        target=1.40,
    )
    assert plan.direction == "BUY"
    assert plan.entry_price == 1.20
    assert plan.stop_loss == 1.10
    assert plan.take_profit == 1.40
    assert plan.position_size.lots > 0
    assert plan.is_ready


def test_plan_from_zone():
    analyzer = RiskAnalyzer()
    zone = FakeZone()
    plan = analyzer.plan(trade_zone=zone, account=Account(balance=10000.0))
    assert plan.direction == "BUY"
    assert plan.entry_price == 1.20
    assert plan.stop_loss == 1.10
    assert plan.take_profit == 1.40
    assert plan.confidence == 80.0


def test_plan_defaults_to_buy_when_no_zone():
    analyzer = RiskAnalyzer()
    plan = analyzer.plan(
        account=Account(balance=10000.0),
        entry=1.20, stop=1.10, target=1.30,
    )
    assert plan.direction == "BUY"


def test_plan_risk_reward_computed():
    analyzer = RiskAnalyzer()
    plan = analyzer.plan(
        account=Account(balance=10000.0),
        direction="BUY",
        entry=1.20,
        stop=1.10,
        target=1.40,
    )
    assert plan.risk_reward == pytest.approx(2.0)


def test_plan_rejected_when_poor_rr():
    analyzer = RiskAnalyzer()
    plan = analyzer.plan(
        account=Account(balance=10000.0),
        direction="BUY",
        entry=1.20,
        stop=1.10,
        target=1.15,  # R:R < 1
    )
    assert plan.status == PlanStatus.REJECTED
    assert plan.note != ""


def test_plan_symbol_default():
    analyzer = RiskAnalyzer()
    plan = analyzer.plan(
        account=Account(balance=10000.0),
        entry=1.20, stop=1.10, target=1.30,
    )
    assert plan.symbol == "XAUUSD"


def test_plan_symbol_override():
    analyzer = RiskAnalyzer()
    plan = analyzer.plan(
        account=Account(balance=10000.0),
        entry=1.20, stop=1.10, target=1.30,
        symbol="EURUSD",
    )
    assert plan.symbol == "EURUSD"
