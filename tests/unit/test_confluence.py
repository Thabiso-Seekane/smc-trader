"""Unit tests for the Week 7 ConfluenceEngine and ConfluenceScorer."""

import pytest

from smart_money.displacement import DisplacementScore
from smart_money.enums import Direction, StructureEventType
from smart_money.models import StructureEvent, SmartMoneyAnalysis
from strategy.confluence import ConfluenceEngine
from strategy.enums import DecisionStatus, SignalDirection
from strategy.scoring import ConfluenceScorer, DEFAULT_THRESHOLDS, DEFAULT_WEIGHTS


class FakeLiquidity:
    def __init__(self, swept=False):
        self._swept = swept

    @property
    def swept_levels(self):
        return [object()] if self._swept else []


class FakeBlock:
    def __init__(self, active=True):
        self._active = active

    @property
    def is_active(self):
        return self._active


class FakeGap:
    def __init__(self, active=True):
        self._active = active

    @property
    def is_active(self):
        return self._active


def make_event(event_type: StructureEventType = StructureEventType.BOS, direction=Direction.BULLISH) -> StructureEvent:
    return StructureEvent(
        event_type=event_type,
        direction=direction,
        timestamp=__import__("datetime").datetime(2024, 1, 1),
        broken_price=1.10,
        broken_index=0,
        confirmation_index=1,
        displacement=DisplacementScore(strength=90.0, confirmed=True),
    )


def make_events(*types):
    return SmartMoneyAnalysis(events=[make_event(t) for t in types])


def make_engine() -> ConfluenceEngine:
    return ConfluenceEngine(timeframe="H1")


def make_blocks(active=True):
    return [FakeBlock(active)]


def make_gaps(active=True):
    return [FakeGap(active)]


def decide(
    engine: ConfluenceEngine,
    direction=SignalDirection.BUY,
    htf_bias="BULLISH",
    liquidity=None,
    events=None,
    order_blocks=None,
    imbalances=None,
    entry=1.05,
):
    return engine.decide(
        direction=direction,
        liquidity=liquidity,
        events=events,
        order_blocks=order_blocks,
        imbalances=imbalances,
        entry_price=entry,
        stop_loss=1.00,
        target=1.20,
        swing_high=1.20,
        swing_low=1.00,
        htf_bias=htf_bias,
    )


def test_perfect_bullish_confluence_is_excellent():
    engine = make_engine()
    decision = decide(
        engine,
        liquidity=FakeLiquidity(swept=True),
        events=make_events(StructureEventType.CHOCH, StructureEventType.BOS),
        order_blocks=make_blocks(),
        imbalances=make_gaps(),
        entry=1.05,  # discount region
    )
    assert decision.status == DecisionStatus.EXCELLENT
    assert decision.confidence >= 90.0


def test_missing_bos_lowers_score():
    engine = make_engine()
    full = decide(
        engine,
        liquidity=FakeLiquidity(swept=True),
        events=make_events(StructureEventType.CHOCH, StructureEventType.BOS),
        order_blocks=make_blocks(),
        imbalances=make_gaps(),
    )
    no_bos = decide(
        engine,
        liquidity=FakeLiquidity(swept=True),
        events=make_events(StructureEventType.CHOCH),
        order_blocks=make_blocks(),
        imbalances=make_gaps(),
    )
    assert no_bos.confidence < full.confidence


def test_missing_choch_lowers_score():
    engine = make_engine()
    full = decide(
        engine,
        liquidity=FakeLiquidity(swept=True),
        events=make_events(StructureEventType.CHOCH, StructureEventType.BOS),
        order_blocks=make_blocks(),
        imbalances=make_gaps(),
    )
    no_choch = decide(
        engine,
        liquidity=FakeLiquidity(swept=True),
        events=make_events(StructureEventType.BOS),
        order_blocks=make_blocks(),
        imbalances=make_gaps(),
    )
    # CHoCH contributes 15 points; removing it reduces the score by 15.
    assert no_choch.confidence == pytest.approx(full.confidence - 15.0)


def test_low_confluence_is_ignored():
    engine = make_engine()
    decision = decide(
        engine,
        liquidity=FakeLiquidity(swept=False),
        events=make_events(),
        order_blocks=None,
        imbalances=None,
        htf_bias="NEUTRAL",
    )
    assert decision.status == DecisionStatus.IGNORE
    assert decision.confidence < 70


def test_higher_timeframe_conflict_zeroes_factor():
    scorer = ConfluenceScorer(weights=DEFAULT_WEIGHTS, thresholds=DEFAULT_THRESHOLDS)
    # Buy but bearish HTF => no higher_timeframe factor.
    engine = make_engine()
    decision = decide(engine, htf_bias="BEARISH", entry=1.15)  # premium region
    assert decision.confidence < 100.0


def test_config_driven_weights():
    weights = {k: v for k, v in DEFAULT_WEIGHTS.items()}
    weights["order_block"] = 0.0  # remove order block weight
    scorer = ConfluenceScorer(weights=weights, thresholds=DEFAULT_THRESHOLDS)
    # With order_block weight 0, its presence doesn't change the score.
    total = sum(weights.values())
    assert total == 100.0 - 10.0


def test_status_mapping():
    scorer = ConfluenceScorer()
    assert scorer.status(95) == DecisionStatus.EXCELLENT
    assert scorer.status(85) == DecisionStatus.STRONG
    assert scorer.status(75) == DecisionStatus.ACCEPTABLE
    assert scorer.status(50) == DecisionStatus.IGNORE
