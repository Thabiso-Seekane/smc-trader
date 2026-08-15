from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from execution.market_data import MT5MarketData


def test_mt5_market_data_adapter_is_read_only_and_normalizes_tick():
    client = SimpleNamespace(
        get_tick=lambda symbol: SimpleNamespace(bid=2500.0, ask=2500.2, time=1_700_000_000),
        symbol_info=lambda symbol: SimpleNamespace(point=0.1, trade_contract_size=10, volume_min=0.01, volume_step=0.01),
    )
    market = MT5MarketData(client)
    tick = market.tick("XAUUSD")
    assert tick.symbol == "XAUUSD"
    assert tick.spread == pytest.approx(0.2)
    assert market.symbol("XAUUSD").contract_size == 10


def test_mt5_candle_dates_match_analysis_timezone_convention():
    client = SimpleNamespace(
        get_rates=lambda *args: [
            {"time": 1_700_000_000, "open": 1, "high": 2, "low": 0.5,
             "close": 1.5, "tick_volume": 10}
        ]
    )

    candles = MT5MarketData(client).candles("EURUSD", "M15", 1)

    assert candles.iloc[0]["date"].tzinfo is None
