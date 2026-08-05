"""Data models for the Smart Money (CHoCH / BOS) engine.

This module contains only data models (dataclasses) and holds no business
logic. Structural-event detection is performed by the choch, bos, and
displacement modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from smart_money.enums import (
    BreakSystem,
    Direction,
    DisplacementQuality,
    StructureEventType,
)


@dataclass(slots=True)
class StructureEvent:
    """A single structural change (CHoCH or BOS).

    Events store the full context of a structural break rather than a
    boolean flag. This lets callers reconstruct the history of structural
    changes and reason about each event's displacement strength, the exact
    prices involved, and whether the break was internal or external.

    Attributes:
        event_type: Whether this is a CHoCH or a BOS.
        direction: Bullish or bearish break.
        timestamp: Time of the confirmation candle.
        broken_price: Price of the structural level that was broken.
        broken_index: Candle index of the structural level that was broken.
        confirmation_index: Candle index confirming the break.
        displacement_strength: 0–100 measure of breakout validity.
        system: Internal or external break (for BOS events).
        prev_swing_index: Index of the preceding swing of the same type
            that defined the broken level.
        prev_swing_price: Price of the preceding swing of the same type.
        note: Optional human-readable description for debugging/visuals.
    """

    event_type: StructureEventType
    direction: Direction
    timestamp: datetime
    broken_price: float
    broken_index: int
    confirmation_index: int
    displacement_strength: float = 0.0
    system: BreakSystem | None = None
    prev_swing_index: int | None = None
    prev_swing_price: float | None = None
    note: str = ""

    @property
    def is_choch(self) -> bool:
        """Return True when this event is a Change of Character."""
        return self.event_type == StructureEventType.CHOCH

    @property
    def is_bos(self) -> bool:
        """Return True when this event is a Break of Structure."""
        return self.event_type == StructureEventType.BOS

    @property
    def is_bullish(self) -> bool:
        """Return True when this event is bullish."""
        return self.direction == Direction.BULLISH

    @property
    def is_bearish(self) -> bool:
        """Return True when this event is bearish."""
        return self.direction == Direction.BEARISH


@dataclass(slots=True)
class SmartMoneyAnalysis:
    """Aggregated CHoCH / BOS analysis result.

    This is the output of :class:`smart_money.analyzer.SmartMoneyAnalyzer`.
    It retains the full ordered history of structural events so callers can
    inspect bullish/bearish CHoCHs, BOSs, and their displacement quality.
    """

    events: list[StructureEvent] = field(default_factory=list)
    timeframe: str = ""

    @property
    def choch_events(self) -> list[StructureEvent]:
        """Return only CHoCH events."""
        return [e for e in self.events if e.is_choch]

    @property
    def bos_events(self) -> list[StructureEvent]:
        """Return only BOS events."""
        return [e for e in self.events if e.is_bos]

    @property
    def bullish_events(self) -> list[StructureEvent]:
        """Return all bullish structural events."""
        return [e for e in self.events if e.is_bullish]

    @property
    def bearish_events(self) -> list[StructureEvent]:
        """Return all bearish structural events."""
        return [e for e in self.events if e.is_bearish]

    @property
    def latest(self) -> StructureEvent | None:
        """Return the most recent structural event, if any."""
        return self.events[-1] if self.events else None


__all__ = ["StructureEvent", "SmartMoneyAnalysis", "DisplacementQuality"]
