from types import SimpleNamespace

import pandas as pd

from backtesting.models import BacktestResult
from dashboard import services
from dashboard.settings import DashboardConfig
from strategy.enums import SignalDirection


def test_backtest_reanalyzes_rolling_history_and_applies_thresholds(monkeypatch):
    candles = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=30, freq="15min"),
            "open": range(100, 130),
            "high": [value + 0.25 for value in range(100, 130)],
            "low": [value - 0.25 for value in range(100, 130)],
            "close": range(100, 130),
            "volume": [100] * 30,
        }
    )
    history_lengths = []

    def setup_for(history, *_args):
        history_lengths.append(len(history))
        price = float(history["close"].iloc[-1])
        return SimpleNamespace(
            direction=SignalDirection.BUY,
            entry_price=price,
            stop_loss=price - 1,
            target=price + 2,
            confluence_score=80.0,
            reason="adaptive setup",
            is_valid=True,
            risk_reward_ratio=2.0,
        )

    monkeypatch.setattr(services, "_best_setup_for_frame", setup_for)
    result = services.run_backtest(
        candles,
        "EURUSD",
        "M15",
        DashboardConfig(risk_percent=1.0, min_confluence=70, min_rr=2.0),
    )

    assert isinstance(result, BacktestResult)
    assert len(history_lengths) > 1
    assert history_lengths == sorted(history_lengths)
    assert max(history_lengths) == len(candles) - 1
    assert result.config.risk_per_trade == 0.01


def test_backtest_rejects_setup_below_market_requirements(monkeypatch):
    candles = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=25, freq="15min"),
            "open": [100.0] * 25,
            "high": [100.2] * 25,
            "low": [99.8] * 25,
            "close": [100.0] * 25,
            "volume": [100] * 25,
        }
    )
    weak = SimpleNamespace(
        direction=SignalDirection.BUY,
        entry_price=100.0,
        stop_loss=99.0,
        target=102.0,
        confluence_score=60.0,
        reason="weak setup",
        is_valid=True,
        risk_reward_ratio=2.0,
    )
    monkeypatch.setattr(services, "_best_setup_for_frame", lambda *_args: weak)

    result = services.run_backtest(candles, "EURUSD", "M15", DashboardConfig())

    assert result.total_trades == 0
