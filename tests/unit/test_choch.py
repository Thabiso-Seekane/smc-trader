"""Unit tests for the CHoCH detector."""

import pandas as pd
import pytest

from smart_money.choch import ChoCHDetector
from smart_money.enums import Direction, StructureEventType
from structure.enums import SwingType
from structure.models import MarketStructure, StructurePoint


def candle_frame():
    """Build a candle frame with a clear bullish reversal break."""
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


def make_structure(points):
    """Build a MarketStructure from a list of (index, price, swing_type, label)."""
    parsed = [
        StructurePoint(
            index=i,
            timestamp=pd.Timestamp("2024-01-01 00:00") + pd.Timedelta(minutes=5 * i),
            price=price,
            swing_type=swing_type,
            label=label,
        )
        for i, price, swing_type, label in points
    ]
    return MarketStructure(points=parsed, swings=[])


def swept_level(price, swing_index, is_buy_side):
    """Build a minimal swept liquidity level stub."""

    class _Level:
        def __init__(self):
            self.price = price
            self.swept = True
            self.swing_index = swing_index
            self.is_buy_side = is_buy_side
            self.is_sell_side = not is_buy_side

    return _Level()


def test_bullish_choch_detected_after_sweep_and_break():
    # Bearish structure: LL(1.0) -> LH(1.2) -> LL(0.9), then HL(1.0) reversal.
    structure = make_structure(
        [
            (2, 1.0, SwingType.LOW, "LL"),
            (4, 1.2, SwingType.HIGH, "LH"),
            (6, 0.9, SwingType.LOW, "LL"),
            (8, 1.0, SwingType.LOW, "HL"),
        ]
    )
    frame = candle_frame()
    # Break the prior LH (1.2) with a strong close above.
    frame.loc[10, "close"] = 1.3
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.05
    frame.loc[10, "open"] = 1.05

    swept = [swept_level(0.9, 6, is_buy_side=False)]

    events = ChoCHDetector().detect(
        structure=structure,
        candles=frame,
        swept_sell_side=swept,
        swept_buy_side=[],
    )

    assert len(events) == 1
    event = events[0]
    assert event.event_type == StructureEventType.CHOCH
    assert event.direction == Direction.BULLISH
    assert event.confirmation_index == 10
    assert event.broken_price == 1.2


def test_choch_requires_liquidity_sweep():
    # Same structure but NO swept liquidity -> no CHoCH.
    structure = make_structure(
        [
            (2, 1.0, SwingType.LOW, "LL"),
            (4, 1.2, SwingType.HIGH, "LH"),
            (6, 0.9, SwingType.LOW, "LL"),
            (8, 1.0, SwingType.LOW, "HL"),
        ]
    )
    frame = candle_frame()
    frame.loc[10, "close"] = 1.3
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.05
    frame.loc[10, "open"] = 1.05

    # No swept levels.
    events = ChoCHDetector().detect(
        structure=structure,
        candles=frame,
        swept_sell_side=[],
        swept_buy_side=[],
    )

    assert events == []


def test_choch_requires_bearish_structure():
    # Not enough bearish structure (only 2 bearish points before HL).
    structure = make_structure(
        [
            (2, 1.0, SwingType.LOW, "LL"),
            (4, 1.2, SwingType.HIGH, "LH"),
            (8, 1.0, SwingType.LOW, "HL"),
        ]
    )
    frame = candle_frame()
    frame.loc[10, "close"] = 1.3
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.05
    frame.loc[10, "open"] = 1.05

    swept = [swept_level(0.9, 2, is_buy_side=False)]

    events = ChoCHDetector().detect(
        structure=structure,
        candles=frame,
        swept_sell_side=swept,
        swept_buy_side=[],
    )

    assert events == []


def test_empty_structure_returns_no_events():
    structure = MarketStructure(points=[], swings=[])
    events = ChoCHDetector().detect(
        structure=structure,
        candles=candle_frame(),
        swept_sell_side=[],
        swept_buy_side=[],
    )
    assert events == []
