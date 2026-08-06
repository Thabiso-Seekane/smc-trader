"""Unit tests for the Order Block validator."""

import pandas as pd

from smart_money.enums import Direction, OrderBlockType
from smart_money.order_block_models import OrderBlock
from smart_money.order_block_validator import OrderBlockValidator


def make_block(direction, high, low, origin_index, displacement=80.0,
               mitigated=False, invalidated=False):
    return OrderBlock(
        direction=direction,
        high=high,
        low=low,
        origin_index=origin_index,
        origin_time=pd.Timestamp("2024-01-01 00:00"),
        created_from_event=Direction.BULLISH
        if direction == OrderBlockType.BULLISH
        else Direction.BEARISH,
        displacement_score=displacement,
        mitigated=mitigated,
        invalidated=invalidated,
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


def test_valid_block_passes():
    frame = candle_frame()
    frame.loc[2, "open"] = 1.10
    frame.loc[2, "close"] = 1.05
    frame.loc[2, "high"] = 1.12
    frame.loc[2, "low"] = 1.04

    block = make_block(OrderBlockType.BULLISH, 1.12, 1.04, origin_index=2)
    assert OrderBlockValidator().is_valid(block, candles=frame) is True


def test_weak_displacement_rejected():
    block = make_block(OrderBlockType.BULLISH, 1.12, 1.04, origin_index=2,
                       displacement=10.0)
    frame = candle_frame()
    assert OrderBlockValidator().is_valid(block, candles=frame) is False


def test_doji_rejected():
    # Origin candle has no body.
    frame = candle_frame()
    frame.loc[2, "open"] = 1.10
    frame.loc[2, "close"] = 1.10
    frame.loc[2, "high"] = 1.12
    frame.loc[2, "low"] = 1.08

    block = make_block(OrderBlockType.BULLISH, 1.12, 1.08, origin_index=2)
    assert OrderBlockValidator().is_valid(block, candles=frame) is False


def test_consumed_block_rejected():
    block = make_block(OrderBlockType.BULLISH, 1.12, 1.04, origin_index=2,
                       mitigated=True)
    frame = candle_frame()
    assert OrderBlockValidator(reject_consumed=True).is_valid(block, candles=frame) is False


def test_invalidated_block_rejected():
    block = make_block(OrderBlockType.BULLISH, 1.12, 1.04, origin_index=2,
                       invalidated=True)
    frame = candle_frame()
    assert OrderBlockValidator(reject_consumed=True).is_valid(block, candles=frame) is False


def test_none_block_rejected():
    assert OrderBlockValidator().is_valid(None, candles=candle_frame()) is False
