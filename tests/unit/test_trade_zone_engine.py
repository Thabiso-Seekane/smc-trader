"""Unit tests for the TradeZoneEngine."""

from datetime import datetime

from liquidity.enums import LiquidityScope, LiquidityType
from liquidity.models import LiquidityLevel, LiquidityMap
from smart_money.displacement import DisplacementScore
from smart_money.enums import Direction, OrderBlockType, StructureEventType
from smart_money.fair_value_gap import FairValueGap
from smart_money.models import StructureEvent
from smart_money.order_block_models import OrderBlock, OrderBlockMap
from smart_money.trade_zone_engine import TradeZoneEngine


def make_order_block(
    direction: OrderBlockType = OrderBlockType.BULLISH,
    high: float = 1.20,
    low: float = 1.10,
    **kwargs,
) -> OrderBlock:
    defaults = dict(
        origin_index=0,
        origin_time=datetime(2024, 1, 1),
        created_from_event=Direction.BULLISH,
        strength=80.0,
    )
    defaults.update(kwargs)
    return OrderBlock(
        direction=direction,
        high=high,
        low=low,
        **defaults,
    )


def make_level(
    price: float,
    liquidity_type=LiquidityType.SWING_HIGH,
    scope=LiquidityScope.INTERNAL,
    strength: float = 50.0,
) -> LiquidityLevel:
    return LiquidityLevel(
        price=price,
        liquidity_type=liquidity_type,
        scope=scope,
        strength=strength,
    )


def make_event(direction: Direction = Direction.BULLISH) -> StructureEvent:
    return StructureEvent(
        event_type=StructureEventType.BOS,
        direction=direction,
        timestamp=datetime(2024, 1, 1),
        broken_price=1.10,
        broken_index=0,
        confirmation_index=1,
        displacement=DisplacementScore(strength=90.0, confirmed=True),
    )


def make_fvg(direction: OrderBlockType = OrderBlockType.BULLISH) -> FairValueGap:
    return FairValueGap(
        direction=direction,
        high=1.20,
        low=1.10,
        index=1,
        timestamp=datetime(2024, 1, 1),
        strength=80.0,
    )


def test_analyze_creates_zone_from_block():
    engine = TradeZoneEngine(timeframe="H1")
    result = engine.analyze(
        order_blocks=make_order_block(),
        liquidity=LiquidityMap(),
        events=[],
        fair_value_gaps=[],
    )
    assert len(result.all) == 1
    zone = result.all[0]
    assert zone.order_block is not None
    assert zone.direction == OrderBlockType.BULLISH
    assert zone.high == 1.20
    assert zone.low == 1.10
    assert zone.timeframe == "H1"


def test_analyze_attaches_liquidity_levels():
    level = make_level(price=1.15, scope=LiquidityScope.EXTERNAL)
    liquidity = LiquidityMap(levels=[level])
    engine = TradeZoneEngine()
    result = engine.analyze(
        order_blocks=make_order_block(),
        liquidity=liquidity,
        events=[],
        fair_value_gaps=[],
    )
    zone = result.all[0]
    assert len(zone.liquidity_levels) == 1
    assert zone.liquidity_levels[0] is level


def test_analyze_does_not_attach_non_overlapping_liquidity():
    level = make_level(price=2.00)  # outside the zone (1.10-1.20)
    liquidity = LiquidityMap(levels=[level])
    engine = TradeZoneEngine()
    result = engine.analyze(
        order_blocks=make_order_block(),
        liquidity=liquidity,
        events=[],
        fair_value_gaps=[],
    )
    zone = result.all[0]
    assert zone.liquidity_levels == []


def test_analyze_attaches_matching_events():
    bullish = make_event(Direction.BULLISH)
    bearish = make_event(Direction.BEARISH)
    engine = TradeZoneEngine()
    result = engine.analyze(
        order_blocks=make_order_block(OrderBlockType.BULLISH),
        liquidity=LiquidityMap(),
        events=[bullish, bearish],
        fair_value_gaps=[],
    )
    zone = result.all[0]
    # Only the bullish event (matching the bullish zone) is attached.
    assert bearish not in zone.events
    assert bullish in zone.events


def test_analyze_attaches_fvgs():
    engine = TradeZoneEngine()
    result = engine.analyze(
        order_blocks=make_order_block(),
        liquidity=LiquidityMap(),
        events=[],
        fair_value_gaps=[make_fvg()],
    )
    zone = result.all[0]
    assert len(zone.fair_value_gaps) == 1


def test_analyze_scores_zones():
    engine = TradeZoneEngine()
    result = engine.analyze(
        order_blocks=make_order_block(),
        liquidity=LiquidityMap(),
        events=[],
        fair_value_gaps=[make_fvg()],
    )
    zone = result.all[0]
    assert zone.confluence_score > 0.0
    assert zone.confluence_level.value != "NONE"


def test_analyze_accepts_order_block_map():
    block_map = OrderBlockMap(
        bullish=[make_order_block()],
        bearish=[],
    )
    engine = TradeZoneEngine()
    result = engine.analyze(
        order_blocks=block_map,
        liquidity=LiquidityMap(),
        events=[],
        fair_value_gaps=[],
    )
    assert len(result.all) == 1


def test_analyze_accepts_single_order_block():
    engine = TradeZoneEngine()
    result = engine.analyze(
        order_blocks=make_order_block(),
        liquidity=LiquidityMap(),
        events=[],
        fair_value_gaps=[],
    )
    assert len(result.all) == 1


def test_analyze_multi_merges_timeframes():
    engine = TradeZoneEngine()
    result = engine.analyze_multi(
        order_blocks_by_tf={
            "H1": [make_order_block()],
            "M15": [make_order_block(OrderBlockType.BEARISH)],
        },
        liquidities={"H1": LiquidityMap(), "M15": LiquidityMap()},
        events_by_tf={"H1": [], "M15": []},
        fvgs_by_tf={"H1": [], "M15": []},
    )
    assert len(result.all) == 2
    # Ranked across the combined set.
    assert result.count == 2


def test_analyze_multi_ranks_combined():
    weak = make_order_block(strength=30.0)
    strong = make_order_block(strength=95.0)
    engine = TradeZoneEngine()
    result = engine.analyze_multi(
        order_blocks_by_tf={"H1": [weak], "M15": [strong]},
        liquidities=None,
        events_by_tf=None,
        fvgs_by_tf=None,
    )
    assert result.strongest is not None
    assert result.strongest.confluence_score >= result.all[0].confluence_score


def test_build_map_partitions_by_direction():
    bullish = make_order_block(OrderBlockType.BULLISH)
    bearish = make_order_block(OrderBlockType.BEARISH)
    engine = TradeZoneEngine()
    result = engine.analyze(
        order_blocks=[bullish, bearish],
        liquidity=LiquidityMap(),
        events=[],
        fair_value_gaps=[],
    )
    assert len(result.bullish) == 1
    assert len(result.bearish) == 1
