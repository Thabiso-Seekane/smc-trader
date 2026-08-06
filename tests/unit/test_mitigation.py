"""Unit tests for the Order Block mitigation/invalidation/freshness detector."""

import pandas as pd

from smart_money.enums import Direction, FreshnessLevel, OrderBlockType
from smart_money.mitigation import MitigationDetector
from smart_money.order_block_models import OrderBlock


def make_block(direction, high, low, origin_index):
    return OrderBlock(
        direction=direction,
        high=high,
        low=low,
        origin_index=origin_index,
        origin_time=pd.Timestamp("2024-01-01 00:00"),
        created_from_event=(
            Direction.BULLISH if direction == OrderBlockType.BULLISH
            else Direction.BEARISH
        ),
        displacement_score=80.0,
    )


def candle_frame():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                pd.date_range("2024-01-01", periods=20, freq="5min")
            ),
            "open": [1.0] * 20,
            "high": [1.0] * 20,
            "low": [1.0] * 20,
            "close": [1.0] * 20,
            "volume": [100] * 20,
        }
    )


def test_fresh_block_not_mitigated():
    # Bullish block at index 2; price stays above the zone -> fresh.
    frame = candle_frame()
    for k in range(3, 20):
        frame.loc[k, "high"] = 1.20
        frame.loc[k, "low"] = 1.15
        frame.loc[k, "close"] = 1.18

    block = make_block(OrderBlockType.BULLISH, 1.10, 1.00, origin_index=2)
    MitigationDetector().analyze([block], candles=frame)

    assert block.touch_count == 0
    assert block.fresh is True
    assert block.mitigated is False
    assert block.invalidated is False
    assert block.freshness == FreshnessLevel.FRESH


def test_mitigated_block_when_price_returns():
    # Price returns into the zone after origin -> mitigated.
    frame = candle_frame()
    frame.loc[5, "high"] = 1.05
    frame.loc[5, "low"] = 0.98
    frame.loc[5, "close"] = 1.02

    block = make_block(OrderBlockType.BULLISH, 1.10, 1.00, origin_index=2)
    MitigationDetector().analyze([block], candles=frame)

    assert block.touch_count >= 1
    assert block.mitigated is True
    assert block.invalidated is False
    assert block.fresh is False


def test_invalidated_bullish_block():
    # Price closes below the low of a bullish zone -> invalidated.
    frame = candle_frame()
    frame.loc[5, "high"] = 0.99
    frame.loc[5, "low"] = 0.90
    frame.loc[5, "close"] = 0.92  # close below low (1.00)

    block = make_block(OrderBlockType.BULLISH, 1.10, 1.00, origin_index=2)
    MitigationDetector().analyze([block], candles=frame)

    assert block.invalidated is True


def test_invalidated_bearish_block():
    # Price closes above the high of a bearish zone -> invalidated.
    frame = candle_frame()
    frame.loc[5, "high"] = 1.20
    frame.loc[5, "low"] = 1.15
    frame.loc[5, "close"] = 1.18  # close above high (1.10)

    block = make_block(OrderBlockType.BEARISH, 1.10, 1.00, origin_index=2)
    MitigationDetector().analyze([block], candles=frame)

    assert block.invalidated is True


def test_touched_once_freshness():
    # Price touches the zone once -> single touch, mitigated.
    frame = candle_frame()
    # Candles stay above the zone (1.00-1.10) except a single touch at 5.
    for k in range(3, 20):
        frame.loc[k, "high"] = 1.20
        frame.loc[k, "low"] = 1.15
        frame.loc[k, "close"] = 1.18
    frame.loc[5, "high"] = 1.05
    frame.loc[5, "low"] = 0.99
    frame.loc[5, "close"] = 1.02

    block = make_block(OrderBlockType.BULLISH, 1.10, 1.00, origin_index=2)
    MitigationDetector().analyze([block], candles=frame)

    assert block.touch_count == 1
    assert block.mitigated is True
    assert block.freshness == FreshnessLevel.MITIGATED


def test_empty_blocks_returns_empty():
    result = MitigationDetector().analyze([], candles=candle_frame())
    assert result == []
