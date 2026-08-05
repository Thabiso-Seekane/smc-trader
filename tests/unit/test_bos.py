"""Unit tests for the BOS detector."""

import pandas as pd

from smart_money.bos import BosDetector
from smart_money.enums import BreakSystem, Direction, StructureEventType
from structure.enums import SwingType
from structure.models import MarketStructure, StructurePoint


def candle_frame():
    """Build a base candle frame."""
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


def test_bullish_bos_detected():
    # Bullish structure: HH(1.0) -> HL(0.9) -> HH(1.1) breaking prior HH(1.0).
    structure = make_structure(
        [
            (2, 1.0, SwingType.HIGH, "HH"),
            (4, 0.9, SwingType.LOW, "HL"),
            (6, 1.1, SwingType.HIGH, "HH"),
        ]
    )
    frame = candle_frame()
    # Break prior HH (1.0) with a strong close above.
    frame.loc[8, "open"] = 1.05
    frame.loc[8, "close"] = 1.2
    frame.loc[8, "high"] = 1.25
    frame.loc[8, "low"] = 1.05

    events = BosDetector(min_structure_points=2).detect(
        structure=structure, candles=frame, external_prices=set()
    )

    assert len(events) == 1
    event = events[0]
    assert event.event_type == StructureEventType.BOS
    assert event.direction == Direction.BULLISH
    assert event.broken_price == 1.0
    assert event.system == BreakSystem.INTERNAL


def test_bearish_bos_detected():
    # Bearish structure: LL(1.0) -> LH(1.1) -> LL(0.9) breaking prior LL(1.0).
    structure = make_structure(
        [
            (2, 1.0, SwingType.LOW, "LL"),
            (4, 1.1, SwingType.HIGH, "LH"),
            (6, 0.9, SwingType.LOW, "LL"),
        ]
    )
    frame = candle_frame()
    # Break prior LL (1.0) with a strong close below.
    frame.loc[8, "open"] = 0.95
    frame.loc[8, "close"] = 0.8
    frame.loc[8, "high"] = 0.95
    frame.loc[8, "low"] = 0.75

    events = BosDetector(min_structure_points=2).detect(
        structure=structure, candles=frame, external_prices=set()
    )

    assert len(events) == 1
    event = events[0]
    assert event.event_type == StructureEventType.BOS
    assert event.direction == Direction.BEARISH
    assert event.broken_price == 1.0


def test_bullish_bos_external_when_price_is_external():
    structure = make_structure(
        [
            (2, 1.0, SwingType.HIGH, "HH"),
            (4, 0.9, SwingType.LOW, "HL"),
            (6, 1.1, SwingType.HIGH, "HH"),
        ]
    )
    frame = candle_frame()
    frame.loc[8, "open"] = 1.05
    frame.loc[8, "close"] = 1.2
    frame.loc[8, "high"] = 1.25
    frame.loc[8, "low"] = 1.05

    events = BosDetector(min_structure_points=2).detect(
        structure=structure,
        candles=frame,
        external_prices={1.0},
    )

    assert len(events) == 1
    assert events[0].system == BreakSystem.EXTERNAL


def test_bos_requires_prior_structure():
    # Only 1 point -> insufficient structure.
    structure = make_structure([(2, 1.0, SwingType.HIGH, "HH")])
    frame = candle_frame()
    frame.loc[8, "close"] = 1.2

    events = BosDetector(min_structure_points=2).detect(
        structure=structure, candles=frame, external_prices=set()
    )

    assert events == []


def test_empty_structure_returns_no_events():
    structure = MarketStructure(points=[], swings=[])
    events = BosDetector().detect(
        structure=structure, candles=candle_frame(), external_prices=set()
    )
    assert events == []
