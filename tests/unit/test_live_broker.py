from types import SimpleNamespace

import pytest

from backtesting.readiness import ReadinessReport
from execution.live_broker import LiveMT5Broker, LiveTradingBlocked


def readiness(passed=True):
    return ReadinessReport(passed, 5, 100, 0.1, 1.5, 0.05, 0.8, 10.0)


def settings(enabled=True):
    return SimpleNamespace(
        live_trading_authorized=enabled,
        live_risk_acknowledgement="I_ACCEPT_LIVE_TRADING_RISK",
        max_spread_points=30,
        risk_percent=1.0,
        live_max_margin_fraction=0.25,
        live_max_deviation_points=20,
        execution_magic_number=501001,
        live_order_comment="test",
    )


class Client:
    mt5 = SimpleNamespace(ORDER_TYPE_BUY=0, ORDER_TYPE_SELL=1, TRADE_ACTION_DEAL=1,
                          ORDER_TIME_GTC=0, ORDER_FILLING_RETURN=2,
                          TRADE_RETCODE_DONE=10009, TRADE_RETCODE_PLACED=10008)

    def _require_mt5(self): return self.mt5
    def account_info(self): return SimpleNamespace(balance=10_000, margin_free=9_000, trade_allowed=True)
    def terminal_info(self): return SimpleNamespace(trade_allowed=True)
    def symbol_info(self, symbol): return SimpleNamespace(point=0.00001, volume_min=0.01, volume_max=10, volume_step=0.01, filling_mode=2)
    def get_tick(self, symbol): return SimpleNamespace(bid=1.10000, ask=1.10010)
    def order_calc_profit(self, *args): return -100
    def order_calc_margin(self, *args): return 500
    def order_check(self, request): return SimpleNamespace(retcode=0, comment="ok")
    def order_send(self, request): return SimpleNamespace(retcode=10009, comment="done")


def plan():
    return SimpleNamespace(symbol="EURUSD", is_buy=True, stop_loss=1.0991, take_profit=1.1021,
                           position_size=SimpleNamespace(lots=0.10))


def test_live_broker_fails_closed_without_authorization_or_readiness():
    with pytest.raises(LiveTradingBlocked):
        LiveMT5Broker(Client(), settings(False), readiness()).submit(plan())
    with pytest.raises(LiveTradingBlocked):
        LiveMT5Broker(Client(), settings(), readiness(False)).submit(plan())


def test_live_broker_preflights_before_send():
    result = LiveMT5Broker(Client(), settings(), readiness()).submit(plan())
    assert result.request["volume"] == 0.1
    assert result.result.retcode == 10009
