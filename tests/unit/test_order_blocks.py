"""Unit tests for the Order Block detector."""

import pandas as pd

from smart_money.displacement import DisplacementScore
from smart_money.enums import Direction, OrderBlockType, StructureEventType
from smart_money.models import StructureEvent
from smart_money.order_blocks import OrderBlockDetector


def candle_frame():
    """Build a candle frame with a clear bullish displacement break."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                pd.date_range("2024-01-01", periods=30, freq="5min")
            ),
            "open": [1.0] * 30,
            "high": [1.0] * 30,
            "low": [1.0] * 30,
            "close": [1.0] * 30,
            "volume": [100] * 30,
        }
    )


def bullish_event():
    """A bullish BOS event with strong displacement."""
    return StructureEvent(
        event_type=StructureEventType.BOS,
        direction=Direction.BULLISH,
        timestamp=pd.Timestamp("2024-01-01 00:50"),
        broken_price=1.0,
        broken_index=8,
        confirmation_index=10,
        displacement=DisplacementScore(strength=90.0, confirmed=True),
    )


def bearish_event():
    """A bearish BOS event with strong displacement."""
    return StructureEvent(
        event_type=StructureEventType.BOS,
        direction=Direction.BEARISH,
        timestamp=pd.Timestamp("2024-01-01 00:50"),
        broken_price=1.0,
        broken_index=8,
        confirmation_index=10,
        displacement=DisplacementScore(strength=90.0, confirmed=True),
    )


def test_bullish_order_block_detected():
    # Last bearish candle before the bullish displacement is index 9.
    frame = candle_frame()
    frame.loc[9, "open"] = 1.10
    frame.loc[9, "close"] = 1.05   # bearish
    frame.loc[9, "high"] = 1.12
    frame.loc[9, "low"] = 1.04
    frame.loc[10, "open"] = 1.05
    frame.loc[10, "close"] = 1.30   # bullish break
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.05

    blocks = OrderBlockDetector().detect(
        events=[bullish_event()], candles=frame, timeframe="M15"
    )

    assert len(blocks) == 1
    block = blocks[0]
    assert block.direction == OrderBlockType.BULLISH
    assert block.origin_index == 9
    assert block.high == 1.12
    assert block.low == 1.04
    assert block.displacement_score == 90.0
    assert block.timeframe == "M15"


def test_bearish_order_block_detected():
    # Last bullish candle before the bearish displacement is index 9.
    frame = candle_frame()
    frame.loc[9, "open"] = 1.05
    frame.loc[9, "close"] = 1.10   # bullish
    frame.loc[9, "high"] = 1.12
    frame.loc[9, "low"] = 1.04
    frame.loc[10, "open"] = 1.10
    frame.loc[10, "close"] = 0.85   # bearish break
    frame.loc[10, "high"] = 1.10
    frame.loc[10, "low"] = 0.80

    blocks = OrderBlockDetector().detect(
        events=[bearish_event()], candles=frame, timeframe="M15"
    )

    assert len(blocks) == 1
    block = blocks[0]
    assert block.direction == OrderBlockType.BEARISH
    assert block.origin_index == 9
    assert block.high == 1.12
    assert block.low == 1.04


def test_weak_displacement_does_not_create_block():
    # Displacement below threshold -> no block.
    event = StructureEvent(
        event_type=StructureEventType.BOS,
        direction=Direction.BULLISH,
        timestamp=pd.Timestamp("2024-01-01 00:50"),
        broken_price=1.0,
        broken_index=8,
        confirmation_index=10,
        displacement=DisplacementScore(strength=10.0, confirmed=False),
    )
    frame = candle_frame()
    frame.loc[9, "open"] = 1.10
    frame.loc[9, "close"] = 1.05
    frame.loc[9, "high"] = 1.12
    frame.loc[9, "low"] = 1.04

    blocks = OrderBlockDetector().detect(events=[event], candles=frame)
    assert blocks == []


def test_doji_origin_candle_rejected():
    # Origin candle has no body (doji) -> rejected.
    frame = candle_frame()
    frame.loc[9, "open"] = 1.10
    frame.loc[9, "close"] = 1.10   # doji
    frame.loc[9, "high"] = 1.12
    frame.loc[9, "low"] = 1.08
    frame.loc[10, "open"] = 1.10
    frame.loc[10, "close"] = 1.30
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.10

    blocks = OrderBlockDetector().detect(
        events=[bullish_event()], candles=frame
    )
    assert blocks == []


def test_empty_events_returns_no_blocks():
    blocks = OrderBlockDetector().detect(events=[], candles=candle_frame())
    assert blocks == []


def test_multiple_blocks_ordered_by_origin():
    # Two events producing two blocks, sorted by origin index.
    frame = candle_frame()
    # First bull block origin at 4.
    frame.loc[4, "open"] = 1.10
    frame.loc[4, "close"] = 1.05
    frame.loc[4, "high"] = 1.12
    frame.loc[4, "low"] = 1.04
    frame.loc[5, "open"] = 1.05
    frame.loc[5, "close"] = 1.30
    frame.loc[5, "high"] = 1.35
    frame.loc[5, "low"] = 1.05
    # Second bull block origin at 9.
    frame.loc[9, "open"] = 1.10
    frame.loc[9, "close"] = 1.05
    frame.loc[9, "high"] = 1.12
    frame.loc[9, "low"] = 1.04
    frame.loc[10, "open"] = 1.05
    frame.loc[10, "close"] = 1.30
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.05

    ev1 = StructureEvent(
        event_type=StructureEventType.BOS,
        direction=Direction.BULLISH,
        timestamp=pd.Timestamp("2024-01-01 00:25"),
        broken_price=1.0,
        broken_index=3,
        confirmation_index=5,
        displacement=DisplacementScore(strength=90.0, confirmed=True),
    )
    ev2 = StructureEvent(
        event_type=StructureEventType.BOS,
        direction=Direction.BULLISH,
        timestamp=pd.Timestamp("2024-01-01 00:50"),
        broken_price=1.0,
        broken_index=8,
        confirmation_index=10,
        displacement=DisplacementScore(strength=90.0, confirmed=True),
    )

    blocks = OrderBlockDetector().detect(events=[ev2, ev1], candles=frame)
    assert [b.origin_index for b in blocks] == [4, 9]
