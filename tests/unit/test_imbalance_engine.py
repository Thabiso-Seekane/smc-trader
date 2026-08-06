"""Unit tests for the ImbalanceEngine and ImbalanceMap."""

from datetime import datetime

import pandas as pd
import pytest

from liquidity.enums import LiquidityScope, LiquidityType
from liquidity.models import LiquidityLevel, LiquidityMap
from smart_money.displacement import DisplacementScore
from smart_money.enums import Direction, OrderBlockType, StructureEventType
from smart_money.fair_value_gap import FairValueGap
from smart_money.imbalance import ImbalanceEngine, ImbalanceMap
from smart_money.models import StructureEvent
from smart_money.order_block_models import OrderBlock, OrderBlockMap
from structure.models import MarketStructure


def make_candles(rows) -> pd.DataFrame:
    return pd.DataFrame(
        [
            [datetime(2024, 1, 1 + i), *values]
            for i, values in enumerate(rows)
        ],
        columns=["date", "open", "high", "low", "close", "volume"],
    )


def bull_frame() -> pd.DataFrame:
    """A frame with one clean bullish FVG (10..15)."""
    return make_candles(
        [
            [10, 10, 15, 10, 10],   # 0
            [15, 15, 20, 15, 15],   # 1 (middle, displaced)
            [15, 15, 20, 20, 20],   # 2
            [20, 20, 25, 20, 20],   # 3
            [25, 25, 30, 25, 25],   # 4
        ]
    )


def bear_frame() -> pd.DataFrame:
    """A frame with one clean bearish FVG (20..25)."""
    return make_candles(
        [
            [30, 30, 25, 30, 30],   # 0
            [25, 25, 20, 25, 25],   # 1 (middle, displaced down)
            [20, 20, 15, 20, 20],   # 2
            [15, 15, 10, 15, 15],   # 3
            [10, 10, 5, 10, 10],    # 4
        ]
    )


def make_structure() -> MarketStructure:
    return MarketStructure()


def make_liquidity() -> LiquidityMap:
    return LiquidityMap()


def make_block(direction=OrderBlockType.BULLISH, high=15.0, low=10.0):
    return OrderBlock(
        direction=direction,
        high=high,
        low=low,
        origin_index=0,
        origin_time=datetime(2024, 1, 1),
        created_from_event=Direction.BULLISH,
    )


def make_event(direction=Direction.BULLISH):
    return StructureEvent(
        event_type=StructureEventType.BOS,
        direction=direction,
        timestamp=datetime(2024, 1, 1),
        broken_price=1.10,
        broken_index=0,
        confirmation_index=1,
        displacement=DisplacementScore(strength=90.0, confirmed=True),
    )


def test_imbalance_map_aggregates():
    gap = FairValueGap(
        direction=OrderBlockType.BULLISH,
        high=1.20,
        low=1.10,
        index=1,
        timestamp=datetime(2024, 1, 1),
        strength=80.0,
    )
    zone_map = ImbalanceMap(
        bullish=[gap],
        bearish=[],
        active=[gap],
        partial=[],
        filled=[],
    )
    assert zone_map.count == 1
    assert zone_map.buy_side == [gap]
    assert zone_map.strongest is gap


def test_imbalance_map_strongest_none_when_empty():
    assert ImbalanceMap().strongest is None


def test_engine_analyze_finds_bullish_gap():
    engine = ImbalanceEngine(
        timeframe="H1", min_displacement=0.0, min_size_atr=0.0
    )
    result = engine.analyze(
        df=bull_frame(),
        structure=make_structure(),
        liquidity=make_liquidity(),
        events=[],
        order_blocks=None,
    )
    assert len(result.bullish) >= 1
    assert result.bullish[0].direction == OrderBlockType.BULLISH
    assert result.timeframe == "H1"


def test_engine_analyze_finds_bearish_gap():
    engine = ImbalanceEngine(
        timeframe="H1", min_displacement=0.0, min_size_atr=0.0
    )
    result = engine.analyze(
        df=bear_frame(),
        structure=make_structure(),
        liquidity=make_liquidity(),
        events=[],
        order_blocks=None,
    )
    assert len(result.bearish) >= 1
    assert result.bearish[0].direction == OrderBlockType.BEARISH


def test_engine_links_order_block():
    engine = ImbalanceEngine(
        timeframe="H1", min_displacement=0.0, min_size_atr=0.0
    )
    block_map = OrderBlockMap(bullish=[make_block()], bearish=[])
    result = engine.analyze(
        df=bull_frame(),
        structure=make_structure(),
        liquidity=make_liquidity(),
        events=[],
        order_blocks=block_map,
    )
    zone = result.bullish[0]
    assert zone.linked_order_block is not None


def test_engine_links_liquidity_level():
    level = LiquidityLevel(
        price=12.0,
        liquidity_type=LiquidityType.SWING_HIGH,
        scope=LiquidityScope.EXTERNAL,
    )
    engine = ImbalanceEngine(
        timeframe="H1", min_displacement=0.0, min_size_atr=0.0
    )
    result = engine.analyze(
        df=bull_frame(),
        structure=make_structure(),
        liquidity=LiquidityMap(levels=[level]),
        events=[],
        order_blocks=None,
    )
    zone = result.bullish[0]
    assert zone.linked_liquidity is level


def test_engine_ranks_gaps():
    engine = ImbalanceEngine(
        timeframe="H1", min_displacement=0.0, min_size_atr=0.0
    )
    result = engine.analyze(
        df=bull_frame(),
        structure=make_structure(),
        liquidity=make_liquidity(),
        events=[],
        order_blocks=None,
    )
    for gap in result.all:
        assert gap.strength > 0.0


def test_analyze_multi_merges_timeframes():
    engine = ImbalanceEngine(
        timeframe="", min_displacement=0.0, min_size_atr=0.0
    )
    result = engine.analyze_multi(
        frames={"H1": bull_frame(), "M15": bear_frame()},
        structures={"H1": make_structure(), "M15": make_structure()},
        liquidities={"H1": make_liquidity(), "M15": make_liquidity()},
        events_by_tf={"H1": [], "M15": []},
        order_blocks_by_tf=None,
    )
    assert result.count >= 2


def test_engine_raises_on_invalid_liquidity():
    engine = ImbalanceEngine()
    with pytest.raises(Exception):
        engine.analyze(
            df=bull_frame(),
            structure=make_structure(),
            liquidity="not-a-liquidity-map",  # invalid
            events=[],
            order_blocks=None,
        )
