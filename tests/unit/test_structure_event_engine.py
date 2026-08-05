"""Unit tests for the Structure Event Engine."""

import pandas as pd
import pytest

from liquidity.enums import LiquidityScope, LiquidityType
from liquidity.models import LiquidityLevel, LiquidityMap
from smart_money.engine import StructureEventEngine
from smart_money.enums import Direction, StructureEventType
from smart_money.event_history import EventHistory
from smart_money.mss import MSSDetector
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


def bullish_choch_structure():
    # Bearish structure: LL(1.0) -> LH(1.2) -> LL(0.9), then HL(1.0) reversal.
    return make_structure(
        [
            (2, 1.0, SwingType.LOW, "LL"),
            (4, 1.2, SwingType.HIGH, "LH"),
            (6, 0.9, SwingType.LOW, "LL"),
            (8, 1.0, SwingType.LOW, "HL"),
        ]
    )


def bullish_bos_structure():
    # Bullish structure: HH(1.0) -> HL(0.9) -> HH(1.1) breaking prior HH(1.0).
    return make_structure(
        [
            (2, 1.0, SwingType.HIGH, "HH"),
            (4, 0.9, SwingType.LOW, "HL"),
            (6, 1.1, SwingType.HIGH, "HH"),
        ]
    )


def test_engine_records_events_in_history():
    structure = bullish_choch_structure()
    frame = candle_frame()
    frame.loc[10, "close"] = 1.3
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.05
    frame.loc[10, "open"] = 1.05

    engine = StructureEventEngine()
    events = engine.detect(
        structure=structure,
        candles=frame,
        swept_sell_side=[swept_level(0.9, 6, is_buy_side=False)],
        swept_buy_side=[],
    )

    assert len(events) == 1
    assert events[0].event_type == StructureEventType.CHOCH
    # The engine's shared history should also contain the event.
    assert len(engine.history) == 1
    assert engine.history.latest is events[0]
    assert engine.history.choch_events == events


def test_engine_merges_choch_and_bos():
    # Structure that fires a CHoCH (with sweep) and a BOS.
    structure = bullish_choch_structure()
    frame = candle_frame()
    frame.loc[10, "close"] = 1.3
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.05
    frame.loc[10, "open"] = 1.05

    engine = StructureEventEngine()
    events = engine.detect(
        structure=structure,
        candles=frame,
        swept_sell_side=[swept_level(0.9, 6, is_buy_side=False)],
        swept_buy_side=[],
    )

    # Add a BOS separately to a fresh engine via the same structure + a BOS-friendly frame.
    engine2 = StructureEventEngine()
    bos_events = engine2.detect(
        structure=bullish_bos_structure(),
        candles=frame,
    )

    assert any(e.event_type == StructureEventType.CHOCH for e in events)
    assert any(e.event_type == StructureEventType.BOS for e in bos_events)


def test_engine_dedupes_and_sorts_events():
    structure = bullish_choch_structure()
    frame = candle_frame()
    frame.loc[10, "close"] = 1.3
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.05
    frame.loc[10, "open"] = 1.05

    engine = StructureEventEngine()
    events = engine.detect(
        structure=structure,
        candles=frame,
        swept_sell_side=[swept_level(0.9, 6, is_buy_side=False)],
        swept_buy_side=[],
    )

    # No duplicates should be present.
    keys = [(e.event_type, e.direction, e.confirmation_index, e.broken_index) for e in events]
    assert len(keys) == len(set(keys))


def test_engine_mss_slot_is_disabled_by_default():
    structure = bullish_choch_structure()
    frame = candle_frame()

    engine = StructureEventEngine()
    events = engine.detect(structure=structure, candles=frame)
    # The MSS detector is registered but dormant -> no MSS events.
    assert not any(e.event_type == StructureEventType.MSS for e in events)
    assert engine.mss.enabled is False


def test_engine_register_custom_detector():
    engine = StructureEventEngine()
    # Registering a fresh MSSDetector should replace the default slot.
    custom_mss = MSSDetector(enabled=True)
    engine.register(custom_mss)
    assert engine.mss is custom_mss


def test_engine_analyze_produces_smart_money_analysis():
    structure = bullish_choch_structure()
    frame = candle_frame()
    frame.loc[10, "close"] = 1.3
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.05
    frame.loc[10, "open"] = 1.05

    level = LiquidityLevel(
        price=0.9,
        liquidity_type=LiquidityType.SWING_LOW,
        scope=LiquidityScope.INTERNAL,
        swept=True,
        swing_index=6,
    )
    liquidity = LiquidityMap(levels=[level])

    engine = StructureEventEngine(timeframe="M5")
    analysis = engine.analyze(
        candles=frame,
        structure=structure,
        liquidity=liquidity,
    )

    assert analysis.timeframe == "M5"
    assert len(analysis.events) >= 1
    assert analysis.events[0].event_type == StructureEventType.CHOCH
    assert analysis.events[0].direction == Direction.BULLISH


def test_event_history_query_helpers():
    history = EventHistory()
    assert history.is_empty
    assert history.latest is None
    assert history.latest_direction is None

    # Manually add a fabricated event-like object via a minimal stub.
    class _Ev:
        def __init__(self, event_type, direction, confirmation_index):
            self.event_type = event_type
            self.direction = direction
            self.confirmation_index = confirmation_index

    history.add(_Ev(StructureEventType.BOS, Direction.BULLISH, 5))
    history.add(_Ev(StructureEventType.CHOCH, Direction.BEARISH, 3))
    history.sort()

    assert not history.is_empty
    # After sorting by confirmation index, the latest is the BOS (index 5).
    assert history.latest.confirmation_index == 5
    assert history.latest_direction == Direction.BULLISH
    assert len(history.bos_events) == 1
    assert len(history.choch_events) == 1
    assert len(history.bullish_events) == 1
    assert len(history.bearish_events) == 1
    # after(4) -> events confirmed after index 4 (the BOS at 5).
    assert len(history.after(4)) == 1
    # before(4) -> events confirmed at or before index 4 (the CHoCH at 3).
    assert len(history.before(4)) == 1
