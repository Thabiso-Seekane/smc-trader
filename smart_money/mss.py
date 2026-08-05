"""Market Structure Shift (MSS) detection — future extension slot.

MSS (Market Structure Shift) is a planned structural event that captures
a shift in the dominant market structure. It is conceptually distinct from
a CHoCH (a *possible* reversal after a liquidity sweep) in that an MSS
represents a *confirmed* shift produced by a displacement break.

The detector is intentionally a **placeholder** for now. It is registered
in the :class:`smart_money.engine.StructureEventEngine` so that the
downstream strategy layer already has a stable, consistent interface to
consume MSS events once the algorithm is implemented in a later week.

Design notes for the future implementation:

* An MSS should reuse the shared :class:`DisplacementDetector` to validate
  the shift, just like CHoCH and BOS.
* It should distinguish *strong* vs *weak* shifts and *internal* vs
  *external* breaks, reusing the existing ``BreakSystem`` enum.
* It should be added to the engine's detector registry under the key
  ``"mss"`` so it participates in the same event pipeline and history.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from smart_money.enums import StructureEventType
from smart_money.models import StructureEvent
from structure.models import MarketStructure


@dataclass(slots=True)
class MSSDetector:
    """Detect Market Structure Shift events (future implementation).

    This detector is a deliberately empty placeholder. It returns no
    events today but is wired into the :class:`StructureEventEngine`
    registry so the public interface is stable and future-proof.

    Attributes:
        enabled: When False (the default), the detector is registered but
            dormant and produces no events. Set to True once the MSS
            algorithm is implemented.
    """

    enabled: bool = False

    def detect(
        self,
        structure: MarketStructure,
        candles: pd.DataFrame,
        **kwargs,
    ) -> list[StructureEvent]:
        """Detect MSS events.

        Currently a placeholder that returns an empty list. When ``enabled``
        is set to True by a future implementation, this method will return
        :class:`StructureEvent` objects with ``event_type ==
        StructureEventType.MSS``.

        Args:
            structure: Market structure from the Week 2 engine.
            candles: OHLCV candle DataFrame.
            **kwargs: Reserved for future inputs (e.g. liquidity sweeps).

        Returns:
            An empty list for now; MSS events in a future release.
        """
        if not self.enabled:
            return []
        return self._detect_impl(structure, candles, **kwargs)

    def _detect_impl(
        self,
        structure: MarketStructure,
        candles: pd.DataFrame,
        **kwargs,
    ) -> list[StructureEvent]:
        """Future MSS detection algorithm.

        Replace this stub with the real MSS logic in a later week. The
        registered event type is :attr:`StructureEventType.MSS`.
        """
        _ = structure, candles, kwargs
        return []


__all__ = ["MSSDetector"]
