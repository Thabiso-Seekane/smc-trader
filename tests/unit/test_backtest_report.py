"""Unit tests for the Week 9 BacktestReport."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from backtesting.enums import Direction, ExitReason, TradeResultType
from backtesting.models import (
    BacktestConfig,
    BacktestResult,
    EquityPoint,
    Trade,
)
from backtesting.report import BacktestReport


def make_result():
    trade = Trade(
        symbol="XAUUSD",
        direction=Direction.BUY,
        entry_price=100.0,
        exit_price=120.0,
        volume=1.0,
        entry_time=datetime(2024, 1, 1),
        exit_time=datetime(2024, 1, 2),
        risk_amount=10.0,
        profit_loss=20.0,
        commission=0.0,
        slippage_cost=0.0,
        exit_reason=ExitReason.TAKE_PROFIT,
        result=TradeResultType.WIN,
        r_multiple=2.0,
        confluence_score=85.0,
        reason="setup",
    )
    return BacktestResult(
        config=BacktestConfig(symbol="XAUUSD", timeframe="M15"),
        initial_balance=10000.0,
        final_balance=10020.0,
        total_return=0.002,
        total_trades=1,
        winning_trades=1,
        losing_trades=0,
        win_rate=1.0,
        profit_factor=20.0,
        max_drawdown=0.05,
        sharpe_ratio=1.0,
        average_rr=2.0,
        average_trade=20.0,
        largest_win=20.0,
        largest_loss=0.0,
        expectancy=20.0,
        equity_curve=[
            EquityPoint(datetime(2024, 1, 1), 10000.0, 10000.0, 0.0)
        ],
        trades=[trade],
    )


def test_to_csv(tmp_path):
    path = tmp_path / "trades.csv"
    report = BacktestReport(make_result())
    written = report.to_csv(path)
    assert written.exists()
    content = path.read_text(encoding="utf-8")
    assert "symbol" in content
    assert "XAUUSD" in content


def test_to_json_returns_payload(tmp_path):
    report = BacktestReport(make_result())
    payload = report.to_json(tmp_path / "summary.json")
    assert payload["total_trades"] == 1
    assert payload["win_rate"] == pytest.approx(1.0)
    assert payload["profit_factor"] == pytest.approx(20.0)
    assert len(payload["trades"]) == 1
    assert payload["trades"][0]["confluence_score"] == pytest.approx(85.0)


def test_to_json_writes_file(tmp_path):
    path = tmp_path / "summary.json"
    report = BacktestReport(make_result())
    report.to_json(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["final_balance"] == pytest.approx(10020.0)


def test_text_summary():
    report = BacktestReport(make_result())
    text = report.text_summary()
    assert "BACKTEST REPORT" in text
    assert "XAUUSD" in text
    assert "100.00%" in text  # win rate


def test_to_html(tmp_path):
    report = BacktestReport(make_result())
    html = report.to_html(tmp_path / "report.html")
    assert "<html>" in html
    assert "Backtest Report" in html
    assert "XAUUSD" in html
