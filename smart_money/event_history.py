"""Event history for the Structure Event Engine.

Rather than exposing a raw ``list[StructureEvent]`` to callers, the
:class:`StructureEventEngine` wraps its accumulated events in an
:class:`EventHistory`. This gives the strategy layer a single, consistent
query interface for reasoning about the sequence of structural events
(CHoCH, BOS, and future MSS) without reaching into the detectors.

The history is intentionally a thin, immutable-style view over the
underlying event list. It holds no detection logic and simply provides
convenient filtering/aggregation helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from smart_money.enums import Direction, StructureEventType
from smart_money.models import StructureEvent


@dataclass(slots=True)
class EventHistory:
    """A chronological, queryable history of structural events.

    Attributes:
        events: The ordered list of structural events (oldest first).
    """

    events: list[StructureEvent] = field(default_factory=list)

    def add(self, event: StructureEvent) -> None:
        """Append a single structural event to the history."""
        if event is not None:
            self.events.append(event)

    def extend(self, events: list[StructureEvent]) -> None:
        """Append multiple structural events to the history."""
        self.events.extend(events or [])

    def sort(self) -> None:
        """Sort events chronologically by their confirmation index."""
        self.events.sort(key=lambda e: e.confirmation_index)

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self):
        return iter(self.events)

    def __getitem__(self, index):
        return self.events[index]

    @property
    def latest(self) -> StructureEvent | None:
        """Return the most recent structural event, if any."""
        return self.events[-1] if self.events else None

    @property
    def latest_direction(self) -> Direction | None:
        """Return the direction of the most recent event, if any."""
        latest = self.latest
        return latest.direction if latest is not None else None

    @property
    def is_empty(self) -> bool:
        """Return True when no structural events have been recorded."""
        return not self.events

    def by_type(self, event_type: StructureEventType) -> list[StructureEvent]:
        """Return all events of a given type (e.g. CHoCH or BOS)."""
        return [e for e in self.events if e.event_type == event_type]

    @property
    def choch_events(self) -> list[StructureEvent]:
        """Return only CHoCH events."""
        return self.by_type(StructureEventType.CHOCH)

    @property
    def bos_events(self) -> list[StructureEvent]:
        """Return only BOS events."""
        return self.by_type(StructureEventType.BOS)

    @property
    def mss_events(self) -> list[StructureEvent]:
        """Return only MSS (Market Structure Shift) events."""
        return self.by_type(StructureEventType.MSS)

    def by_direction(self, direction: Direction) -> list[StructureEvent]:
        """Return all events with a given directional bias."""
        return [e for e in self.events if e.direction == direction]

    @property
    def bullish_events(self) -> list[StructureEvent]:
        """Return all bullish structural events."""
        return self.by_direction(Direction.BULLISH)

    @property
    def bearish_events(self) -> list[StructureEvent]:
        """Return all bearish structural events."""
        return self.by_direction(Direction.BEARISH)

    def after(self, confirmation_index: int) -> list[StructureEvent]:
        """Return events confirmed after the given candle index."""
        return [e for e in self.events if e.confirmation_index > confirmation_index]

    def before(self, confirmation_index: int) -> list[StructureEvent]:
        """Return events confirmed at or before the given candle index."""
        return [e for e in self.events if e.confirmation_index <= confirmation_index]


__all__ = ["EventHistory"]
