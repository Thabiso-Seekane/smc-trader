"""Timezone-aware session filtering for paper execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class TradingWindow:
    start: time
    end: time

    def contains(self, value: time) -> bool:
        return self.start <= value <= self.end if self.start <= self.end else value >= self.start or value <= self.end


@dataclass(slots=True)
class SessionFilter:
    enabled: bool = False
    timezone: str = "UTC"
    windows: list[TradingWindow] = field(default_factory=list)

    def allows(self, timestamp: datetime) -> bool:
        if not self.enabled:
            return True
        if timestamp.tzinfo is None:
            return False
        local = timestamp.astimezone(ZoneInfo(self.timezone)).time()
        return any(window.contains(local) for window in self.windows)


__all__ = ["TradingWindow", "SessionFilter"]
