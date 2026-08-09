"""Focused tests for Week 10 dashboard visualizations."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pandas as pd

from backtesting.enums import Direction, ExitReason, TradeResultType
from backtesting.models import BacktestConfig, BacktestResult, EquityPoint, Trade
from dashboard.charts import (
    drawdown_chart,
    liquidity_chart,
    market_structure_chart,
    smart_money_chart,
    trade_replay_chart,
)
from dashboard.services import AnalysisBundle


def make_bundle() -> AnalysisBundle:
    dates = [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(3)]
    frame = pd.DataFrame({
        "date": dates, "open": [100, 101, 102], "high": [102, 103, 104],
        "low": [99, 100, 101], "close": [101, 102, 103], "volume": [1, 1, 1],
    })
    return AnalysisBundle(
        df=frame,
        structure=SimpleNamespace(points=[SimpleNamespace(timestamp=dates[1], price=103, label="HH")]),
        liquidity=SimpleNamespace(levels=[SimpleNamespace(price=104, swept=False, is_buy_side=True, label="BSL")]),
        events=SimpleNamespace(events=[SimpleNamespace(confirmation_index=1, timestamp=dates[1], broken_price=103,
                                                        event_type="BOS", is_bullish=True)]),
        order_blocks=SimpleNamespace(all=[SimpleNamespace(low=100, high=101, is_bullish=True)]),
        imbalances=SimpleNamespace(all=[SimpleNamespace(low=101, high=102)]),
        symbol="XAUUSD", timeframe="H1",
    )


def make_result() -> BacktestResult:
    return BacktestResult(
        config=BacktestConfig(),
        equity_curve=[
            EquityPoint(datetime(2024, 1, 1), 1000, 1000, 0),
            EquityPoint(datetime(2024, 1, 2), 900, 900, 0.1),
        ],
    )


def test_week_10_visual_charts_are_plotly_figures():
    bundle = make_bundle()
    assert len(market_structure_chart(bundle).data) == 2
    assert len(liquidity_chart(bundle).layout.shapes) == 1
    assert len(smart_money_chart(bundle).data) == 2
    assert len(smart_money_chart(bundle).layout.shapes) == 2
    assert len(drawdown_chart(make_result()).data) == 1


def test_trade_replay_limits_candles_to_selected_bar():
    bundle = make_bundle()
    trade = Trade(
        symbol="XAUUSD", direction=Direction.BUY, entry_price=101, exit_price=103,
        entry_time=bundle.df["date"].iloc[0], exit_time=bundle.df["date"].iloc[2],
        result=TradeResultType.WIN, exit_reason=ExitReason.TAKE_PROFIT,
    )
    figure = trade_replay_chart(bundle, trade, end_index=1)
    assert len(figure.data[0].x) == 2
    assert len(figure.data) == 2
