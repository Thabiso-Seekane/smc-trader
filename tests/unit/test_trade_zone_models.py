"""Unit tests for the Trade Zone data models."""

from datetime import datetime

import pytest

from smart_money.enums import ConfluenceLevel, OrderBlockType, TradeZoneStatus
from smart_money.fair_value_gap import FairValueGap
from smart_money.order_block_models import OrderBlock
from smart_money.trade_zone_models import TradeZone, TradeZoneMap


def make_order_block(
    direction: OrderBlockType = OrderBlockType.BULLISH,
    high: float = 1.20,
    low: float = 1.10,
    **kwargs,
) -> OrderBlock:
    return OrderBlock(
        direction=direction,
        high=high,
        low=low,
        origin_index=0,
        origin_time=datetime(2024, 1, 1),
        created_from_event="BOS",
        **kwargs,
    )


def make_zone(
    direction: OrderBlockType = OrderBlockType.BULLISH,
    high: float = 1.20,
    low: float = 1.10,
    **kwargs,
) -> TradeZone:
    return TradeZone(
        direction=direction,
        high=high,
        low=low,
        origin_time=datetime(2024, 1, 1),
        **kwargs,
    )


def test_zone_directional_helpers():
    bullish = make_zone(OrderBlockType.BULLISH)
    bearish = make_zone(OrderBlockType.BEARISH)
    assert bullish.is_bullish
    assert not bullish.is_bearish
    assert bearish.is_bearish
    assert not bearish.is_bullish


def test_zone_geometry():
    zone = make_zone(high=1.20, low=1.00)
    assert zone.midpoint == pytest.approx(1.10)
    assert zone.range == pytest.approx(0.20)


def test_zone_lifecycle_defaults_active():
    zone = make_zone()
    assert zone.is_active
    assert zone.status == TradeZoneStatus.ACTIVE


def test_zone_mitigated_status():
    zone = make_zone(mitigated=True)
    assert not zone.is_active
    assert zone.status == TradeZoneStatus.MITIGATED


def test_zone_invalidated_status():
    zone = make_zone(invalidated=True)
    assert not zone.is_active
    assert zone.status == TradeZoneStatus.INVALIDATED


def test_zone_has_components():
    zone = make_zone(
        order_block=make_order_block(),
        fair_value_gaps=[FairValueGap(
            direction=OrderBlockType.BULLISH,
            high=1.20,
            low=1.10,
            index=1,
            timestamp=datetime(2024, 1, 1),
        )],
        liquidity_levels=[object()],
        events=[object()],
    )
    assert zone.has_order_block
    assert zone.has_fair_value_gap
    assert zone.has_liquidity
    assert zone.event_count == 1


def test_zone_has_no_components_when_empty():
    zone = make_zone()
    assert not zone.has_order_block
    assert not zone.has_fair_value_gap
    assert not zone.has_liquidity
    assert zone.event_count == 0


def test_zone_hash_is_stable():
    zone = make_zone()
    assert hash(zone) == hash(zone.id)


def test_zone_slots_prevent_new_attributes():
    zone = make_zone()
    with pytest.raises(AttributeError):
        zone.nonexistent_attr = 1


def test_map_aggregates_directional_lists():
    bullish = make_zone(OrderBlockType.BULLISH)
    bearish = make_zone(OrderBlockType.BEARISH)
    zone_map = TradeZoneMap(
        bullish=[bullish],
        bearish=[bearish],
        active=[bullish],
        timeframe="H1",
    )
    assert zone_map.count == 2
    assert zone_map.buy_side == [bullish]
    assert zone_map.sell_side == [bearish]
    assert len(zone_map) == 2


def test_map_strongest_returns_highest_confluence_active():
    weak = make_zone(confluence_score=30.0, confluence_level=ConfluenceLevel.WEAK)
    strong = make_zone(confluence_score=85.0, confluence_level=ConfluenceLevel.STRONG)
    zone_map = TradeZoneMap(
        bullish=[weak, strong],
        bearish=[],
        active=[weak, strong],
    )
    assert zone_map.strongest is strong


def test_map_strongest_ignores_inactive():
    strong_invalidated = make_zone(
        confluence_score=90.0, invalidated=True
    )
    weak_active = make_zone(confluence_score=45.0)
    zone_map = TradeZoneMap(
        bullish=[strong_invalidated, weak_active],
        bearish=[],
        active=[strong_invalidated, weak_active],
    )
    assert zone_map.strongest is weak_active


def test_map_strongest_none_when_empty():
    zone_map = TradeZoneMap()
    assert zone_map.strongest is None
