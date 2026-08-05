"""Unit tests for the smart money enums and data models."""

import pandas as pd

from smart_money.enums import (
    BreakSystem,
    Direction,
    DisplacementQuality,
    StructureEventType,
)
from smart_money.models import SmartMoneyAnalysis, StructureEvent


def test_enums_values():
    assert StructureEventType.CHOCH.value == "CHOCH"
    assert StructureEventType.BOS.value == "BOS"
    assert Direction.BULLISH.value == "BULLISH"
    assert Direction.BEARISH.value == "BEARISH"
    assert BreakSystem.INTERNAL.value == "INTERNAL"
    assert BreakSystem.EXTERNAL.value == "EXTERNAL"
    assert DisplacementQuality.STRONG.value == "STRONG"


def test_structure_event_properties():
    event = StructureEvent(
        event_type=StructureEventType.BOS,
        direction=Direction.BULLISH,
        timestamp=pd.Timestamp("2024-01-01 00:00"),
        broken_price=1.0,
        broken_index=2,
        confirmation_index=5,
        displacement_strength=80.0,
        system=BreakSystem.EXTERNAL,
    )
    assert event.is_choch is False
    assert event.is_bos is True
    assert event.is_bullish is True
    assert event.is_bearish is False


def test_analysis_properties():
    choch = StructureEvent(
        event_type=StructureEventType.CHOCH,
        direction=Direction.BEARISH,
        timestamp=pd.Timestamp("2024-01-01 00:00"),
        broken_price=1.0,
        broken_index=2,
        confirmation_index=5,
    )
    bos = StructureEvent(
        event_type=StructureEventType.BOS,
        direction=Direction.BULLISH,
        timestamp=pd.Timestamp("2024-01-01 00:05"),
        broken_price=1.1,
        broken_index=4,
        confirmation_index=6,
    )
    analysis = SmartMoneyAnalysis(events=[choch, bos])

    assert analysis.choch_events == [choch]
    assert analysis.bos_events == [bos]
    assert analysis.bullish_events == [bos]
    assert analysis.bearish_events == [choch]
    assert analysis.latest == bos
