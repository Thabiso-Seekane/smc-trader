"""Unit tests for the ImbalanceRanker."""

from datetime import datetime

import pytest

from smart_money.displacement import DisplacementScore
from smart_money.enums import GapQuality, OrderBlockType
from smart_money.fair_value_gap import FairValueGap
from smart_money.imbalance_ranking import ImbalanceRanker


def make_gap(
    direction=OrderBlockType.BULLISH,
    high=1.20,
    low=1.10,
    displacement_strength=80.0,
    freshness=100.0,
    timeframe="",
    linked_event=None,
    linked_liquidity=None,
):
    return FairValueGap(
        direction=direction,
        high=high,
        low=low,
        index=1,
        timestamp=datetime(2024, 1, 1),
        displacement=DisplacementScore(strength=displacement_strength),
        freshness=freshness,
        timeframe=timeframe,
        linked_structure_event=linked_event,
        linked_liquidity=linked_liquidity,
    )


class _Event:
    def __init__(self, is_choch=False, is_bos=False, displacement_strength=90.0):
        self.is_choch = is_choch
        self.is_bos = is_bos
        self.displacement_strength = displacement_strength


class _Level:
    def __init__(self, price=1.15, strength=50.0, is_external=False):
        self.price = price
        self.strength = strength
        self.is_external = is_external


def test_rank_scores_and_sorts_descending():
    ranker = ImbalanceRanker()
    weak = make_gap(displacement_strength=30.0, freshness=40.0)
    strong = make_gap(displacement_strength=95.0, freshness=100.0)
    ranked = ranker.rank([weak, strong])
    assert ranked[0].strength >= ranked[1].strength
    assert ranked[0] is strong
    assert strong.strength > 0.0


def test_rank_sets_quality():
    ranker = ImbalanceRanker()
    gap = make_gap(displacement_strength=95.0, freshness=100.0)
    ranked = ranker.rank([gap])
    assert ranked[0].quality in (
        GapQuality.STRONG,
        GapQuality.MODERATE,
        GapQuality.WEAK,
    )


def test_level_mapping():
    ranker = ImbalanceRanker()
    assert ranker._quality(0) == GapQuality.NONE
    assert ranker._quality(30) == GapQuality.WEAK
    assert ranker._quality(55) == GapQuality.MODERATE
    assert ranker._quality(85) == GapQuality.STRONG


def test_displacement_factor_uses_linked_event():
    ranker = ImbalanceRanker()
    gap = make_gap(linked_event=_Event(displacement_strength=90.0))
    assert ranker._displacement_factor(gap) == pytest.approx(90.0)


def test_structure_factor_choch_strongest():
    ranker = ImbalanceRanker()
    choch = make_gap(linked_event=_Event(is_choch=True))
    bos = make_gap(linked_event=_Event(is_bos=True))
    assert ranker._structure_factor(choch, []) == 100.0
    assert ranker._structure_factor(bos, []) == 70.0


def test_structure_factor_default():
    ranker = ImbalanceRanker()
    gap = make_gap()
    assert ranker._structure_factor(gap, []) == 50.0


def test_liquidity_factor_linked_level_boost():
    ranker = ImbalanceRanker()
    gap = make_gap(linked_liquidity=_Level(strength=60.0, is_external=True))
    assert ranker._liquidity_factor(gap, None) > 50.0


def test_liquidity_factor_default_neutral():
    ranker = ImbalanceRanker()
    gap = make_gap()
    assert ranker._liquidity_factor(gap, None) == pytest.approx(50.0)


def test_timeframe_factor_ranks_higher_tf_higher():
    ranker = ImbalanceRanker()
    assert ranker._timeframe_factor(make_gap(timeframe="H4")) == 85.0
    assert ranker._timeframe_factor(make_gap(timeframe="M15")) == 50.0
    assert ranker._timeframe_factor(make_gap(timeframe="")) == 50.0


def test_full_score_with_all_factors_high():
    ranker = ImbalanceRanker()
    gap = make_gap(
        displacement_strength=100.0,
        freshness=100.0,
        timeframe="H4",
        linked_event=_Event(is_choch=True, displacement_strength=100.0),
        linked_liquidity=_Level(strength=100.0, is_external=True),
    )
    gap.high = 1.20
    gap.low = 1.00
    gap.range  # ensure geometry
    ranked = ranker.rank([gap])
    assert ranked[0].strength > 70.0
    assert ranked[0].quality == GapQuality.STRONG
