"""Unit tests for the Week 7 TradeZone model and TradeZoneBuilder."""

from datetime import datetime

import pandas as pd
import pytest

from liquidity.enums import LiquidityScope, LiquidityType
from liquidity.models import LiquidityLevel, LiquidityMap
from smart_money.displacement import DisplacementScore
from smart_money.enums import Direction, OrderBlockType, StructureEventType
from smart_money.fair_value_gap import FairValueGap
from smart_money.imbalance import ImbalanceMap
from smart_money.models import StructureEvent
from smart_money.order_block_models import OrderBlock, OrderBlockMap
from strategy.enums import PremiumDiscountPosition, SignalDirection
from strategy.models import TradeZone
from strategy.trade_zone import TradeZoneBuilder
from structure.models import MarketStructure, Swing


def make_order_block(direction: OrderBlockType = OrderBlockType.BULLISH) -> OrderBlock:
    return OrderBlock(
        direction=direction,
        high=1.20,
        low=1.10,
        origin_index=0,
        origin_time=datetime(2024, 1, 1),
        created_from_event=Direction.BULLISH,
        strength=80.0,
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


def make_level(price: float) -> LiquidityLevel:
    return LiquidityLevel(
        price=price,
        liquidity_type=LiquidityType.SWING_HIGH,
        scope=LiquidityScope.EXTERNAL,
        strength=50.0,
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


def make_structure() -> MarketStructure:
    return MarketStructure(
        swings=[
            Swing(index=0, timestamp=datetime(2024, 1, 1), price=1.20, is_high=True),
            Swing(index=1, timestamp=datetime(2024, 1, 2), price=1.00, is_high=False),
        ]
    )


def test_zone_directional_helpers():
    buy = TradeZone(direction=SignalDirection.BUY, entry_price=1.0, stop_loss=0.9, target=1.1)
    sell = TradeZone(direction=SignalDirection.SELL, entry_price=1.0, stop_loss=1.1, target=0.9)
    assert buy.is_buy
    assert not buy.is_sell
    assert sell.is_sell
    assert not sell.is_buy


def test_zone_geometry():
    zone = TradeZone(direction=SignalDirection.BUY, entry_price=100.0, stop_loss=99.0, target=102.0)
    assert zone.risk == pytest.approx(1.0)
    assert zone.reward == pytest.approx(2.0)
    assert zone.risk_reward_ratio == pytest.approx(2.0)


def test_zone_is_valid_buy():
    zone = TradeZone(direction=SignalDirection.BUY, entry_price=100.0, stop_loss=99.0, target=102.0)
    assert zone.is_valid


def test_zone_is_invalid_when_geometry_reversed():
    zone = TradeZone(direction=SignalDirection.BUY, entry_price=100.0, stop_loss=101.0, target=102.0)
    assert not zone.is_valid


def test_builder_builds_buy_zone():
    builder = TradeZoneBuilder(timeframe="H1")
    zone = builder.build(
        direction=SignalDirection.BUY,
        structure=make_structure(),
        liquidity=LiquidityMap(levels=[make_level(1.15)]),
        events=[make_event()],
        order_blocks=OrderBlockMap(bullish=[make_order_block()], bearish=[]),
        imbalances=ImbalanceMap(bullish=[make_fvg()], bearish=[]),
        entry_price=1.12,
    )
    assert zone.direction == SignalDirection.BUY
    assert zone.order_block is not None
    assert zone.fair_value_gap is not None
    assert zone.liquidity is not None
    assert zone.structure_event is not None
    assert zone.is_valid


def test_builder_premium_discount_for_buy():
    builder = TradeZoneBuilder()
    zone = builder.build(
        direction=SignalDirection.BUY,
        structure=make_structure(),
        liquidity=LiquidityMap(),
        events=[],
        order_blocks=OrderBlockMap(),
        imbalances=ImbalanceMap(),
        entry_price=1.05,  # below equilibrium (1.10)
    )
    assert zone.premium_discount == PremiumDiscountPosition.DISCOUNT
