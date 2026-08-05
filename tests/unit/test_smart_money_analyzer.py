"""Unit tests for the SmartMoneyAnalyzer public façade."""

import pandas as pd
import pytest

from core.exceptions import DataValidationError
from liquidity.enums import LiquidityScope, LiquidityType
from liquidity.models import LiquidityLevel, LiquidityMap
from smart_money.analyzer import SmartMoneyAnalyzer
from smart_money.enums import Direction, StructureEventType
from structure.enums import SwingType
from structure.models import MarketStructure, StructurePoint


def candle_frame():
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


def make_liquidity(levels):
    return LiquidityMap(levels=levels)


def test_analyzer_returns_analysis_with_events():
    # A bearish structure with a sweep, then a bullish reversal break.
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

    level = LiquidityLevel(
        price=0.9,
        liquidity_type=LiquidityType.SWING_LOW,
        scope=LiquidityScope.INTERNAL,
        swept=True,
        swing_index=6,
    )
    liquidity = make_liquidity([level])

    result = SmartMoneyAnalyzer().analyze(
        candles=frame,
        structure=structure,
        liquidity=liquidity,
    )

    assert isinstance(result.events, list)
    assert len(result.events) >= 1
    assert result.events[0].event_type == StructureEventType.CHOCH
    assert result.events[0].direction == Direction.BULLISH


def test_analyzer_validates_inputs():
    with pytest.raises(DataValidationError):
        SmartMoneyAnalyzer().analyze(
            candles=pd.DataFrame(),
            structure=MarketStructure(),
            liquidity=LiquidityMap(),
        )


def test_analyzer_handles_bullish_bos():
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

    result = SmartMoneyAnalyzer().analyze(
        candles=frame,
        structure=structure,
        liquidity=LiquidityMap(),
    )

    assert any(e.event_type == StructureEventType.BOS for e in result.events)
