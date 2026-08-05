"""Structure Event Engine.

A single, consistent interface for all structural events. Rather than
treating CHoCH and BOS (and future MSS) as completely separate modules,
the engine orchestrates a registry of detectors behind one ``detect`` API
and accumulates their output into a shared :class:`EventHistory`.

Conceptual architecture::

    MarketStructure
            │
            ▼
    StructureEventEngine
            │
            ├── ChoCHDetector
            ├── BosDetector
            ├── MSSDetector (future)
            ├── DisplacementValidator (shared DisplacementDetector)
            └── EventHistory

Why a single engine?

* It provides **one consistent interface** for all structural events, so
  the strategy layer never needs to know how CHoCH vs BOS vs MSS are
  detected.
* It makes the engine **extensible** — adding a new detector (MSS, weak vs
  strong BOS, multi-timeframe events) is as simple as registering it in the
  detector registry.
* It centralizes the shared **DisplacementValidator** and the
  **EventHistory**, so every detector reasons about the same displacement
  scoring and every event lands in the same chronological history.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from liquidity.models import LiquidityMap
from smart_money.bos import BosDetector
from smart_money.choch import ChoCHDetector
from smart_money.displacement import DisplacementDetector
from smart_money.event_history import EventHistory
from smart_money.models import SmartMoneyAnalysis, StructureEvent
from smart_money.mss import MSSDetector
from structure.models import MarketStructure


@dataclass(slots=True)
class StructureEventEngine:
    """Orchestrate all structural-event detectors behind one interface.

    Attributes:
        choch: The CHoCH detector (or a configured instance).
        bos: The BOS detector (or a configured instance).
        mss: The future MSS detector slot (disabled by default).
        displacement: The shared DisplacementValidator used to score and
            confirm every structural break.
        history: The accumulated :class:`EventHistory` of all events.
        timeframe: Optional label attached to shared analysis results.
    """

    choch: ChoCHDetector = field(default_factory=ChoCHDetector)
    bos: BosDetector = field(default_factory=BosDetector)
    mss: MSSDetector = field(default_factory=MSSDetector)
    displacement: DisplacementDetector = field(default_factory=DisplacementDetector)
    history: EventHistory = field(default_factory=EventHistory)
    timeframe: str = field(default="", kw_only=True)

    def register(self, detector, key: str | None = None) -> None:
        """Register a detector into the engine.

        This is the extension point described in the design: any future
        detector (MSS, internal/external BOS variants, multi-timeframe
        events) can be attached to the engine and will participate in the
        same pipeline.

        Args:
            detector: A detector exposing a ``detect(structure, candles, ...)``
                method returning ``list[StructureEvent]``.
            key: Optional registry key. When None, the detector's class name
                (lower-cased) is used.
        """
        if key is None:
            key = type(detector).__name__.lower()
        if key == "chochdetector":
            self.choch = detector
        elif key == "bosdetector":
            self.bos = detector
        elif key == "mssdetector":
            self.mss = detector

    def detect(
        self,
        structure: MarketStructure,
        candles: pd.DataFrame,
        swept_sell_side: list | None = None,
        swept_buy_side: list | None = None,
        external_prices: set[float] | None = None,
    ) -> list[StructureEvent]:
        """Run every registered detector and return the merged, sorted events.

        Args:
            structure: Market structure from the Week 2 engine.
            candles: OHLCV candle DataFrame.
            swept_sell_side: Sell-side liquidity levels that were swept.
            swept_buy_side: Buy-side liquidity levels that were swept.
            external_prices: Optional set of external structural prices used
                to classify BOS events as internal vs external.

        Returns:
            The merged, de-duplicated, chronologically sorted list of
            structural events. The same events are also appended to
            :attr:`history`.
        """
        swept_sell_side = swept_sell_side or []
        swept_buy_side = swept_buy_side or []
        external_prices = external_prices or set()

        events: list[StructureEvent] = []

        # CHoCH detector.
        events.extend(
            self.choch.detect(
                structure=structure,
                candles=candles,
                swept_sell_side=swept_sell_side,
                swept_buy_side=swept_buy_side,
            )
        )

        # BOS detector.
        events.extend(
            self.bos.detect(
                structure=structure,
                candles=candles,
                external_prices=external_prices,
            )
        )

        # Future MSS detector (currently a disabled placeholder).
        events.extend(self.mss.detect(structure=structure, candles=candles))

        # De-duplicate and sort by confirmation index.
        unique: list[StructureEvent] = []
        seen: set[tuple] = set()
        for e in sorted(events, key=lambda e: e.confirmation_index):
            key = (e.event_type, e.direction, e.confirmation_index, e.broken_index)
            if key in seen:
                continue
            seen.add(key)
            unique.append(e)

        # Record into the shared event history.
        self.history.extend(unique)
        self.history.sort()

        return unique

    def analyze(
        self,
        candles: pd.DataFrame,
        structure: MarketStructure,
        liquidity: LiquidityMap,
    ) -> SmartMoneyAnalysis:
        """High-level convenience entry point mirroring the analyzer.

        This wires the engine inputs from a :class:`LiquidityMap`, runs the
        detectors, and returns a :class:`SmartMoneyAnalysis` for callers
        that prefer the aggregated result object.

        Args:
            candles: OHLCV candle DataFrame.
            structure: Market structure from the Week 2 engine.
            liquidity: Liquidity map from the Week 3 engine.

        Returns:
            A :class:`SmartMoneyAnalysis` of the detected structural events.
        """
        swept_sell = [l for l in liquidity.swept_levels if l.is_sell_side]
        swept_buy = [l for l in liquidity.swept_levels if l.is_buy_side]
        external = {level.price for level in liquidity.external_levels}

        events = self.detect(
            structure=structure,
            candles=candles,
            swept_sell_side=swept_sell,
            swept_buy_side=swept_buy,
            external_prices=external,
        )
        return SmartMoneyAnalysis(events=events, timeframe=self.timeframe)


__all__ = ["StructureEventEngine"]
