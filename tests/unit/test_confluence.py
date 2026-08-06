"""Unit tests for the ConfluenceScorer."""

from datetime import datetime

import pytest

from smart_money.confluence import ConfluenceScorer
from smart_money.enums import ConfluenceLevel, FreshnessLevel, OrderBlockType
from smart_money.fair_value_gap import FairValueGap
from smart_money.order_block_models import OrderBlock
from smart_money.trade_zone_models import TradeZone


def make_order_block(
    strength: float = 80.0,
    touch_count: int = 0,
    mitigated: bool = False,
    invalidated: bool = False,
) -> OrderBlock:
    return OrderBlock(
        direction=OrderBlockType.BULLISH,
        high=1.20,
        low=1.10,
        origin_index=0,
        origin_time=datetime(2024, 1, 1),
        created_from_event="BOS",
        strength=strength,
        touch_count=touch_count,
        mitigated=mitigated,
        invalidated=invalidated,
    )


def make_fvg(strength: float = 90.0) -> FairValueGap:
    return FairValueGap(
        direction=OrderBlockType.BULLISH,
        high=1.20,
        low=1.10,
        index=1,
        timestamp=datetime(2024, 1, 1),
        strength=strength,
    )


def make_zone(
    order_block: OrderBlock | None = None,
    fvgs: list[FairValueGap] | None = None,
    liquidity_levels: list = None,
    events: list = None,
    timeframe: str = "",
) -> TradeZone:
    return TradeZone(
        direction=OrderBlockType.BULLISH,
        high=1.20,
        low=1.10,
        origin_time=datetime(2024, 1, 1),
        order_block=order_block,
        fair_value_gaps=fvgs or [],
        liquidity_levels=liquidity_levels or [],
        events=events or [],
        timeframe=timeframe,
    )


class _LiquidityLevel:
    def __init__(self, strength=0.0, is_external=False):
        self.strength = strength
        self.is_external = is_external


class _Event:
    def __init__(self, is_choch=False, is_bos=False, is_bullish=False):
        self.is_choch = is_choch
        self.is_bos = is_bos
        self.is_bullish = is_bullish


def test_score_mutates_zone():
    scorer = ConfluenceScorer()
    zone = make_zone(order_block=make_order_block())
    assert zone.confluence_score == 0.0
    assert zone.confluence_level == ConfluenceLevel.NONE
    scorer.score(zone)
    assert zone.confluence_score > 0.0
    assert zone.confluence_level != ConfluenceLevel.NONE


def test_score_without_order_block_uses_neutral_factors():
    # With no order block and no FVG, the neutral factors (liquidity /
    # structure / timeframe) still contribute a baseline score.
    scorer = ConfluenceScorer()
    zone = make_zone()
    scorer.score(zone)
    assert zone.confluence_score == pytest.approx(25.0)
    assert zone.confluence_level == ConfluenceLevel.WEAK


def test_order_block_factor_blocks_boost():
    scorer = ConfluenceScorer()
    zone = make_zone(order_block=make_order_block(strength=100.0))
    assert scorer._order_block_factor(zone) == 100.0


def test_order_block_factor_none_is_zero():
    scorer = ConfluenceScorer()
    zone = make_zone()
    assert scorer._order_block_factor(zone) == 0.0


def test_freshness_modulates_order_block():
    scorer = ConfluenceScorer()
    fresh = make_zone(order_block=make_order_block(strength=100.0, touch_count=0))
    touched_once = make_zone(
        order_block=make_order_block(strength=100.0, touch_count=1)
    )
    touched_twice = make_zone(
        order_block=make_order_block(strength=100.0, touch_count=2)
    )
    mitigated = make_zone(
        order_block=make_order_block(strength=100.0, mitigated=True)
    )

    assert scorer._order_block_factor(fresh) == 100.0
    assert scorer._order_block_factor(touched_once) == pytest.approx(80.0)
    assert scorer._order_block_factor(touched_twice) == pytest.approx(60.0)
    assert scorer._order_block_factor(mitigated) == pytest.approx(40.0)


def test_fvg_factor_from_strength():
    scorer = ConfluenceScorer()
    zone = make_zone(fvgs=[make_fvg(strength=85.0)])
    assert scorer._fvg_factor(zone) == pytest.approx(85.0)


def test_fvg_factor_without_strength_defaults():
    scorer = ConfluenceScorer()
    zone = make_zone(fvgs=[make_fvg(strength=0.0)])
    assert scorer._fvg_factor(zone) == pytest.approx(70.0)


def test_fvg_factor_none_is_zero():
    scorer = ConfluenceScorer()
    zone = make_zone()
    assert scorer._fvg_factor(zone) == 0.0


def test_liquidity_factor_none_is_neutral():
    scorer = ConfluenceScorer()
    zone = make_zone()
    assert scorer._liquidity_factor(zone) == pytest.approx(50.0)


def test_liquidity_factor_external_boost():
    scorer = ConfluenceScorer()
    zone = make_zone(
        liquidity_levels=[_LiquidityLevel(strength=40.0, is_external=True)]
    )
    score = scorer._liquidity_factor(zone)
    assert score > 50.0


def test_structure_factor_none_is_neutral():
    scorer = ConfluenceScorer()
    zone = make_zone()
    assert scorer._structure_factor(zone) == pytest.approx(50.0)


def test_structure_factor_choch_is_strongest():
    scorer = ConfluenceScorer()
    zone = make_zone(events=[_Event(is_choch=True)])
    assert scorer._structure_factor(zone) == 100.0


def test_structure_factor_bos_stronger_than_plain():
    scorer = ConfluenceScorer()
    bos = make_zone(events=[_Event(is_bos=True)])
    plain = make_zone(events=[_Event(is_bullish=True)])
    assert scorer._structure_factor(bos) == 70.0
    assert scorer._structure_factor(plain) == 60.0


def test_timeframe_factor_ranks_higher_tf_higher():
    scorer = ConfluenceScorer()
    assert scorer._timeframe_factor(make_zone(timeframe="H4")) == 85.0
    assert scorer._timeframe_factor(make_zone(timeframe="M15")) == 50.0
    assert scorer._timeframe_factor(make_zone(timeframe="")) == 50.0


def test_level_mapping():
    scorer = ConfluenceScorer()
    assert scorer._level(0) == ConfluenceLevel.NONE
    assert scorer._level(30) == ConfluenceLevel.WEAK
    assert scorer._level(55) == ConfluenceLevel.MODERATE
    assert scorer._level(85) == ConfluenceLevel.STRONG


def test_rank_sorts_descending():
    scorer = ConfluenceScorer()
    low = make_zone(order_block=make_order_block(strength=30.0))
    high = make_zone(order_block=make_order_block(strength=95.0))
    ranked = scorer.rank([low, high])
    assert ranked[0].confluence_score >= ranked[1].confluence_score
    assert ranked[0] is high


def test_full_score_with_all_factors_high():
    scorer = ConfluenceScorer()
    zone = make_zone(
        order_block=make_order_block(strength=100.0),
        fvgs=[make_fvg(strength=100.0)],
        liquidity_levels=[_LiquidityLevel(strength=100.0, is_external=True)],
        events=[_Event(is_choch=True)],
        timeframe="H4",
    )
    scorer.score(zone)
    assert zone.confluence_score > 70.0
    assert zone.confluence_level == ConfluenceLevel.STRONG
