"""Unit tests for the Week 8 risk Account."""

import pytest

from risk.account import Account
from risk.enums import RiskStatus


def test_account_defaults():
    account = Account()
    assert account.balance == 10000.0
    assert account.equity == 10000.0
    assert account.can_trade


def test_drawdown_pct():
    account = Account(balance=10000.0, equity=9000.0, initial_balance=10000.0)
    assert account.drawdown_pct == pytest.approx(10.0)


def test_daily_risk_pct():
    account = Account(balance=10000.0, daily_loss=200.0)
    assert account.daily_risk_pct == 2.0


def test_status_within_limit():
    assert Account().status == RiskStatus.WITHIN_LIMIT


def test_status_max_drawdown():
    account = Account(equity=7000.0, initial_balance=10000.0, max_drawdown_pct=20.0)
    assert account.status == RiskStatus.MAX_DRAWDOWN


def test_status_daily_limit():
    account = Account(balance=10000.0, daily_loss=400.0, max_daily_risk_pct=3.0)
    assert account.status == RiskStatus.DAILY_LIMIT


def test_status_position_cap():
    account = Account(open_positions=5, max_open_positions=5)
    assert account.status == RiskStatus.POSITION_CAP


def test_status_blocked():
    account = Account(blocked=True)
    assert account.status == RiskStatus.BLOCKED


def test_can_trade_false_when_limited():
    account = Account(open_positions=5, max_open_positions=5)
    assert not account.can_trade


def test_risk_amount_for():
    account = Account(balance=10000.0)
    assert account.risk_amount_for(1.0) == 100.0
    assert account.risk_amount_for(2.0) == 200.0


def test_available_positions():
    account = Account(open_positions=2, max_open_positions=5)
    assert account.available_positions() == 3
