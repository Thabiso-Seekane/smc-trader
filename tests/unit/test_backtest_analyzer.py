"""Unit tests for the Week 9 BacktestAnalyzer (confluence attribution)."""

from datetime import datetime

import pytest

from backtesting.analyzer import BacktestAnalyzer, ConfluenceBand
from backtesting.enums import Direction, TradeResultType
from backtesting.models import Trade


def make_trade(confluence, pnl, r):
    result = TradeResultType.WIN if pnl > 0 else TradeResultType.LOSS
    return Trade(
        symbol="XAUUSD",
        direction=Direction.BUY,
        entry_price=100.0,
        exit_price=100.0 + pnl,
        volume=1.0,
        profit_loss=float(pnl),
        result=result,
        r_multiple=float(r),
        confluence_score=float(confluence),
        exit_time=datetime(2024, 1, 15),
    )


def test_confluence_band_defaults_empty():
    band = ConfluenceBand()
    assert band.label == ""
    assert band.trades == 0
    assert band.win_rate == 0.0
    assert band.average_r == 0.0
    assert band.total_pnl == 0.0


def test_attribution_groups_by_band():
    analyzer = BacktestAnalyzer()
    trades = [
        make_trade(75.0, 10.0, 1.0),   # 70-79
        make_trade(85.0, 20.0, 2.0),   # 80-89
        make_trade(95.0, 30.0, 3.0),   # 90-100
        make_trade(50.0, -5.0, -1.0),  # below all bands
    ]
    bands = analyzer.confluence_attribution(trades)
    by_label = {b.label: b for b in bands}
    assert by_label["70-79"].trades == 1
    assert by_label["80-89"].trades == 1
    assert by_label["90-100"].trades == 1
    # The 50-score trade falls outside every band.


def test_band_win_rate():
    analyzer = BacktestAnalyzer()
    trades = [
        make_trade(75.0, 10.0, 1.0),
        make_trade(75.0, -5.0, -1.0),
        make_trade(75.0, 20.0, 2.0),
    ]
    bands = analyzer.confluence_attribution(trades)
    band = [b for b in bands if b.label == "70-79"][0]
    assert band.trades == 3
    assert band.win_rate == pytest.approx(2 / 3)
    assert band.total_pnl == pytest.approx(25.0)


def test_band_with_no_trades_returns_zero():
    analyzer = BacktestAnalyzer()
    bands = analyzer.confluence_attribution([])
    assert all(b.trades == 0 for b in bands)


def test_custom_bands():
    analyzer = BacktestAnalyzer(
        bands=[(0.0, 50.0, "0-50"), (50.0, 100.0, "50-100")]
    )
    trades = [
        make_trade(30.0, 5.0, 0.5),
        make_trade(80.0, 10.0, 1.0),
    ]
    bands = analyzer.confluence_attribution(trades)
    by_label = {b.label: b for b in bands}
    assert by_label["0-50"].trades == 1
    assert by_label["50-100"].trades == 1
