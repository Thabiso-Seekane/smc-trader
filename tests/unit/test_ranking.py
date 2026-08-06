"""Unit tests for the Order Block ranker."""

import pandas as pd

from smart_money.displacement import DisplacementScore
from smart_money.enums import Direction, OrderBlockType, StructureEventType
from smart_money.models import StructureEvent
from smart_money.order_block_models import OrderBlock
from smart_money.ranking import OrderBlockRanker


def make_block(direction, displacement, timeframe, touch_count=0, mitigated=False):
    return OrderBlock(
        direction=direction,
        high=1.10,
        low=1.00,
        origin_index=2,
        origin_time=pd.Timestamp("2024-01-01 00:00"),
        created_from_event=Direction.BULLISH,
        displacement_score=displacement,
        timeframe=timeframe,
        touch_count=touch_count,
        mitigated=mitigated,
    )


def make_structure_event(event_type, displacement):
    return StructureEvent(
        event_type=event_type,
        direction=Direction.BULLISH,
        timestamp=pd.Timestamp("2024-01-01 00:00"),
        broken_price=1.0,
        broken_index=2,
        confirmation_index=5,
        displacement=DisplacementScore(strength=displacement),
    )


def test_strong_block_scores_high():
    block = make_block(OrderBlockType.BULLISH, 90.0, "W")
    ranker = OrderBlockRanker()
    ranked = ranker.rank([block])
    assert ranked[0].strength >= 70.0
    assert ranked[0].quality.value == "STRONG"


def test_weak_small_block_scores_low():
    block = make_block(OrderBlockType.BEARISH, 5.0, "M1", touch_count=2,
                       mitigated=True)
    ranker = OrderBlockRanker()
    ranked = ranker.rank([block])
    assert ranked[0].strength < 40.0
    assert ranked[0].quality.value == "WEAK"


def test_sorting_by_strength_descending():
    strong = make_block(OrderBlockType.BULLISH, 90.0, "W")
    weak = make_block(OrderBlockType.BEARISH, 5.0, "M1", touch_count=2,
                      mitigated=True)
    ranked = OrderBlockRanker().rank([weak, strong])
    assert [b.displacement_score for b in ranked] == [90.0, 5.0]


def test_fresh_scores_higher_than_mitigated():
    fresh = make_block(OrderBlockType.BULLISH, 80.0, "H1", touch_count=0)
    mitigated = make_block(OrderBlockType.BULLISH, 80.0, "H1", touch_count=3,
                           mitigated=True)
    ranked = OrderBlockRanker().rank([mitigated, fresh])
    assert ranked[0].id == fresh.id


def test_choch_scores_higher_than_bos():
    choch = make_structure_event(StructureEventType.CHOCH, 80.0)
    bos = make_structure_event(StructureEventType.BOS, 80.0)

    # Separate block instances (ranker mutates block.strength in place).
    block_choch = make_block(OrderBlockType.BULLISH, 80.0, "H1")
    block_bos = make_block(OrderBlockType.BULLISH, 80.0, "H1")

    ranked = OrderBlockRanker().rank([block_choch], structure_events=[choch])
    ranked_bos = OrderBlockRanker().rank([block_bos], structure_events=[bos])
    assert ranked[0].strength > ranked_bos[0].strength
