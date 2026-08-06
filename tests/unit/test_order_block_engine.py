"""Unit tests for the Order Block engine public façade."""

import pandas as pd
import pytest

from core.exceptions import DataValidationError
from liquidity.enums import LiquidityScope, LiquidityType
from liquidity.models import LiquidityLevel, LiquidityMap
from smart_money.displacement import DisplacementScore
from smart_money.enums import Direction, OrderBlockType, StructureEventType
from smart_money.models import StructureEvent
from smart_money.order_block_engine import OrderBlockEngine
from structure.models import MarketStructure


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


def bullish_event():
    return StructureEvent(
        event_type=StructureEventType.BOS,
        direction=Direction.BULLISH,
        timestamp=pd.Timestamp("2024-01-01 00:50"),
        broken_price=1.0,
        broken_index=8,
        confirmation_index=10,
        displacement=DisplacementScore(strength=90.0, confirmed=True),
    )


def bullish_frame():
    """A frame forming a bullish block at origin 9 that stays active."""
    frame = candle_frame()
    # Origin candle (bearish) at index 9.
    frame.loc[9, "open"] = 1.10
    frame.loc[9, "close"] = 1.05
    frame.loc[9, "high"] = 1.12
    frame.loc[9, "low"] = 1.04
    # Bullish break at index 10, gapped above the zone (low >= 1.12) so the
    # block is not touched / mitigated.
    frame.loc[10, "open"] = 1.13
    frame.loc[10, "close"] = 1.30
    frame.loc[10, "high"] = 1.35
    frame.loc[10, "low"] = 1.13
    # Keep price above the zone afterwards so it stays active.
    for k in range(11, 30):
        frame.loc[k, "open"] = 1.20
        frame.loc[k, "close"] = 1.22
        frame.loc[k, "high"] = 1.25
        frame.loc[k, "low"] = 1.18
    return frame


def test_engine_returns_map_with_bullish_block():
    result = OrderBlockEngine().analyze(
        df=bullish_frame(),
        structure=MarketStructure(),
        liquidity=LiquidityMap(),
        events=[bullish_event()],
    )

    assert len(result.bullish) == 1
    assert result.bullish[0].direction == OrderBlockType.BULLISH
    assert result.bullish[0].origin_index == 9
    assert result.strongest is not None


def test_engine_validates_inputs():
    with pytest.raises(DataValidationError):
        OrderBlockEngine().analyze(
            df=pd.DataFrame(),
            structure=MarketStructure(),
            liquidity=LiquidityMap(),
            events=[],
        )


def test_engine_handles_empty_events():
    result = OrderBlockEngine().analyze(
        df=bullish_frame(),
        structure=MarketStructure(),
        liquidity=LiquidityMap(),
        events=[],
    )
    assert result.all == []


def test_engine_multi_timeframe():
    frame = bullish_frame()
    result = OrderBlockEngine().analyze_multi(
        frames={"H1": frame, "M15": frame},
        structures={"H1": MarketStructure(), "M15": MarketStructure()},
        liquidities={"H1": LiquidityMap(), "M15": LiquidityMap()},
        events_by_tf={
            "H1": [bullish_event()],
            "M15": [bullish_event()],
        },
    )
    assert len(result.all) == 2


def test_engine_liquidity_interaction():
    level = LiquidityLevel(
        price=1.05,
        liquidity_type=LiquidityType.SWING_HIGH,
        scope=LiquidityScope.EXTERNAL,
        strength=50.0,
    )
    liquidity = LiquidityMap(levels=[level])

    result = OrderBlockEngine().analyze(
        df=bullish_frame(),
        structure=MarketStructure(),
        liquidity=liquidity,
        events=[bullish_event()],
    )
    assert len(result.bearish) == 0
    assert len(result.all) >= 1
