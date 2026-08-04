"""Data models for the market structure engine.

This module contains only data models (dataclasses) and holds no business
logic. Price-structure analysis is performed by the detector, classifier,
and trend analyzer modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from structure.enums import StructureLabel, SwingType, Trend


@dataclass(slots=True)
class Swing:
    """A single swing point (high or low) detected in the price series."""

    index: int
    timestamp: datetime
    price: float
    is_high: bool
    score: float = 0.0

    @property
    def swing_type(self) -> SwingType:
        """Return the swing type derived from the direction flag."""
        return SwingType.HIGH if self.is_high else SwingType.LOW


@dataclass(slots=True)
class StructurePoint:
    """A swing that has been classified into market structure (HH/HL/LH/LL)."""

    index: int
    timestamp: datetime
    price: float
    swing_type: SwingType
    label: StructureLabel


@dataclass(slots=True)
class StructureHistory:
    """Chronological history of market-structure labels.

    Rather than keeping only the latest structure, this model retains the
    full ordered sequence of labelled swing points. This history is
    essential for later features (liquidity mapping, CHoCH/BOS detection)
    and cleanly supports internal vs. external structure without data-model
    changes.
    """

    points: list[StructurePoint] = field(default_factory=list)

    @property
    def labels(self) -> list[StructureLabel]:
        """Return the ordered HH/HL/LH/LL label sequence."""
        return [point.label for point in self.points]

    @property
    def latest(self) -> StructurePoint | None:
        """Return the most recent structure point, if any."""
        return self.points[-1] if self.points else None

    @property
    def is_empty(self) -> bool:
        """Return True when no structure points have been recorded."""
        return not self.points

    def __len__(self) -> int:
        return len(self.points)


@dataclass(slots=True)
class MarketStructure:
    """Aggregated market-structure analysis result."""

    swings: list[Swing] = field(default_factory=list)
    points: list[StructurePoint] = field(default_factory=list)
    trend: Trend = Trend.RANGE
    previous_trend: Trend = Trend.RANGE

    @property
    def structure(self) -> list[StructurePoint]:
        """Return the classified structure points (public API)."""
        return self.points

    @property
    def history(self) -> StructureHistory:
        """Return the chronological structure history.

        The history is derived from the classified points and preserves
        every labelled swing in order, enabling liquidity mapping and
        CHoCH/BOS detection in later weeks.
        """
        return StructureHistory(points=list(self.points))


__all__ = ["Swing", "StructurePoint", "StructureHistory", "MarketStructure"]
