"""Unit tests for the StrategyFilters."""

import pytest

from strategy.enums import PremiumDiscountPosition, SignalDirection
from strategy.filters import StrategyFilters
from strategy.models import TradeZone


def make_zone(
    confluence_score: float = 80.0,
    direction: SignalDirection = SignalDirection.BUY,
    premium_discount: PremiumDiscountPosition = PremiumDiscountPosition.DISCOUNT,
    risk_reward: float = 2.0,
    order_block=None,
    structure_event=None,
) -> TradeZone:
    # risk determines the stop distance; target is set to achieve the ratio.
    stop_loss = 99.0
    risk = 1.0
    entry = 100.0
    target = entry + risk * risk_reward
    return TradeZone(
        direction=direction,
        entry_price=entry,
        stop_loss=stop_loss,
        target=target,
        confluence_score=confluence_score,
        premium_discount=premium_discount,
        order_block=order_block,
        structure_event=structure_event,
    )


def test_passes_all_filters_by_default():
    filters = StrategyFilters()
    assert filters.passes(make_zone())


def test_min_confluence_filters_low_scores():
    filters = StrategyFilters(min_confluence=70.0)
    assert filters.passes(make_zone(confluence_score=80.0))
    assert not filters.passes(make_zone(confluence_score=60.0))


def test_min_displacement_filters_weak_events():
    class WeakEvent:
        displacement_strength = 20.0

    class StrongEvent:
        displacement_strength = 60.0

    filters = StrategyFilters(min_displacement=50.0)
    assert filters.passes(make_zone(structure_event=StrongEvent()))
    assert not filters.passes(make_zone(structure_event=WeakEvent()))


def test_higher_tf_alignment():
    filters = StrategyFilters(higher_tf_alignment=True)
    # Buy aligns with bullish HTF.
    assert filters.passes(make_zone(), htf_bias="BULLISH")
    # Buy does not align with bearish HTF.
    assert not filters.passes(make_zone(), htf_bias="BEARISH")


def test_premium_discount_match():
    filters = StrategyFilters(premium_discount_match=True)
    assert filters.passes(make_zone(premium_discount=PremiumDiscountPosition.DISCOUNT))
    assert not filters.passes(
        make_zone(premium_discount=PremiumDiscountPosition.PREMIUM)
    )


def test_min_risk_reward():
    filters = StrategyFilters(min_risk_reward=1.5)
    assert filters.passes(make_zone(risk_reward=2.0))
    # risk_reward field is on the zone's geometry; a poor 0.5R setup fails.
    poor = make_zone()
    poor.target = 100.5
    poor.stop_loss = 99.5
    assert not filters.passes(poor)


def test_max_ob_touches():
    class TouchedBlock:
        touch_count = 3

    class FreshBlock:
        touch_count = 0

    filters = StrategyFilters(max_ob_touches=2)
    assert filters.passes(make_zone(order_block=FreshBlock()))
    assert not filters.passes(make_zone(order_block=TouchedBlock()))


def test_require_liquidity_sweep():
    filters = StrategyFilters(require_liquidity_sweep=True)
    assert filters.passes(make_zone(), liquidity_swept=True)
    assert not filters.passes(make_zone(), liquidity_swept=False)
