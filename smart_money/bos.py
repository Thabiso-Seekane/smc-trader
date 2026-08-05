"""Break of Structure (BOS) detection.

A BOS is a continuation of the prevailing trend: price breaks a swing
high (bullish) or swing low (bearish) in the direction of the current
structure. Unlike a CHoCH, a BOS does **not** require a prior liquidity
sweep — it simply confirms that the trend is continuing.

CHoCH says: "Maybe the market changed."
BOS says:    "The market has confirmed the new direction."

Bullish BOS::

    HH -> HL -> HH -> HL -> (break prior HH) -> Bullish BOS

Bearish BOS::

    LL -> LH -> LL -> LH -> (break prior LL) -> Bearish BOS

The BOS detector optionally classifies each break as **Internal** or
**External** based on the liquidity scope of the level being broken:

    * Internal BOS — breaks a minor swing within the current range.
    * External BOS — breaks a major structural level (range extreme,
      external swing).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from smart_money.displacement import DisplacementDetector
from smart_money.enums import BreakSystem, Direction, StructureEventType
from smart_money.models import StructureEvent
from structure.enums import StructureLabel, SwingType
from structure.models import MarketStructure, StructurePoint


def _label_value(label) -> str:
    """Normalize a structure label (enum member or raw string) to its value."""
    return label.value if isinstance(label, StructureLabel) else str(label)


@dataclass(slots=True)
class BosDetector:
    """Detect Bullish and Bearish Breaks of Structure.

    Attributes:
        min_structure_points: Minimum number of prior structure points
            required before a BOS can fire.
        min_displacement: Minimum displacement strength (0–100) required
            for a break to be considered a valid BOS.
        pip_size: Absolute price of one pip, used by the displacement
            detector to normalize the required move.
        min_move_pips: Minimum move (in pips) beyond the broken level
            required for valid displacement.
    """

    min_structure_points: int = 2
    min_displacement: float = 30.0
    pip_size: float = 0.0001
    min_move_pips: float = 1.0

    def detect(
        self,
        structure: MarketStructure,
        candles: pd.DataFrame,
        external_prices: set[float] | None = None,
    ) -> list[StructureEvent]:
        """Detect BOS events from structure and candles.

        Args:
            structure: Market structure from the Week 2 engine.
            candles: OHLCV candle DataFrame.
            external_prices: Optional set of prices corresponding to
                external (major structural) liquidity levels. Used to
                classify each BOS as Internal or External.

        Returns:
            A list of :class:`StructureEvent` BOS events, ordered by
            confirmation index.
        """
        if structure is None or candles is None or candles.empty:
            return []

        points = structure.points
        if len(points) < self.min_structure_points:
            return []

        external_prices = external_prices or set()
        events: list[StructureEvent] = []
        displacement = DisplacementDetector(
            min_body_ratio=0.5, min_move_pips=self.min_move_pips
        )

        for i in range(1, len(points)):
            current = points[i]
            previous = points[i - 1]

            # Bullish BOS: current is a HH that breaks the prior HH.
            event = self._detect_bullish(
                points=points,
                i=i,
                current=current,
                previous=previous,
                candles=candles,
                external_prices=external_prices,
                displacement=displacement,
            )
            if event is not None:
                events.append(event)

            # Bearish BOS: current is a LL that breaks the prior LL.
            event = self._detect_bearish(
                points=points,
                i=i,
                current=current,
                previous=previous,
                candles=candles,
                external_prices=external_prices,
                displacement=displacement,
            )
            if event is not None:
                events.append(event)

        events.sort(key=lambda e: e.confirmation_index)
        return events

    def _detect_bullish(
        self,
        points: list[StructurePoint],
        i: int,
        current: StructurePoint,
        previous: StructurePoint,
        candles: pd.DataFrame,
        external_prices: set[float],
        displacement: DisplacementDetector,
    ) -> StructureEvent | None:
        """Detect a single Bullish BOS at point ``i``."""
        if current.swing_type != SwingType.HIGH:
            return None
        if _label_value(current.label) != _label_value(StructureLabel.HH):
            return None
        if _label_value(previous.label) not in (
            _label_value(StructureLabel.HL),
            _label_value(StructureLabel.HH),
        ):
            return None

        # Prior bullish structure must exist.
        if not self._has_bullish_structure(points[: i + 1]):
            return None

        # The broken level is the prior High (the last high before current).
        broken = self._prior_same_type(points, i, SwingType.HIGH)
        if broken is None:
            return None

        confirm_index = self._find_break_confirmation(
            candles,
            broken_index=broken.index,
            broken_price=broken.price,
            bullish=True,
        )
        if confirm_index is None:
            return None

        disp = displacement.assess(
            candles=candles,
            index=confirm_index,
            broken_price=broken.price,
            direction_is_bullish=True,
        )
        if disp.strength < self.min_displacement:
            return None

        system = self._classify_system(broken.price, external_prices)

        return StructureEvent(
            event_type=StructureEventType.BOS,
            direction=Direction.BULLISH,
            timestamp=candles["date"].iloc[confirm_index],
            broken_price=broken.price,
            broken_index=broken.index,
            confirmation_index=confirm_index,
            displacement=disp,
            system=system,
            prev_swing_index=current.index,
            prev_swing_price=current.price,
            note=f"Bullish BOS ({system.value})",
        )

    def _detect_bearish(
        self,
        points: list[StructurePoint],
        i: int,
        current: StructurePoint,
        previous: StructurePoint,
        candles: pd.DataFrame,
        external_prices: set[float],
        displacement: DisplacementDetector,
    ) -> StructureEvent | None:
        """Detect a single Bearish BOS at point ``i``."""
        if current.swing_type != SwingType.LOW:
            return None
        if _label_value(current.label) != _label_value(StructureLabel.LL):
            return None
        if _label_value(previous.label) not in (
            _label_value(StructureLabel.LH),
            _label_value(StructureLabel.LL),
        ):
            return None

        # Prior bearish structure must exist.
        if not self._has_bearish_structure(points[: i + 1]):
            return None

        # The broken level is the prior Low (the last low before current).
        broken = self._prior_same_type(points, i, SwingType.LOW)
        if broken is None:
            return None

        confirm_index = self._find_break_confirmation(
            candles,
            broken_index=broken.index,
            broken_price=broken.price,
            bullish=False,
        )
        if confirm_index is None:
            return None

        disp = displacement.assess(
            candles=candles,
            index=confirm_index,
            broken_price=broken.price,
            direction_is_bullish=False,
        )
        if disp.strength < self.min_displacement:
            return None

        system = self._classify_system(broken.price, external_prices)

        return StructureEvent(
            event_type=StructureEventType.BOS,
            direction=Direction.BEARISH,
            timestamp=candles["date"].iloc[confirm_index],
            broken_price=broken.price,
            broken_index=broken.index,
            confirmation_index=confirm_index,
            displacement=disp,
            system=system,
            prev_swing_index=current.index,
            prev_swing_price=current.price,
            note=f"Bearish BOS ({system.value})",
        )

    def _has_bullish_structure(self, points: list[StructurePoint]) -> bool:
        """Return True when the points contain a bullish HH/HL run."""
        bullish = {_label_value(StructureLabel.HH), _label_value(StructureLabel.HL)}
        count = sum(1 for p in points if _label_value(p.label) in bullish)
        return count >= self.min_structure_points

    def _has_bearish_structure(self, points: list[StructurePoint]) -> bool:
        """Return True when the points contain a bearish LL/LH run."""
        bearish = {_label_value(StructureLabel.LL), _label_value(StructureLabel.LH)}
        count = sum(1 for p in points if _label_value(p.label) in bearish)
        return count >= self.min_structure_points

    def _prior_same_type(
        self, points: list[StructurePoint], i: int, swing_type: SwingType
    ) -> StructurePoint | None:
        """Return the most recent point of ``swing_type`` before ``i``."""
        for j in range(i - 1, -1, -1):
            if points[j].swing_type == swing_type:
                return points[j]
        return None

    def _find_break_confirmation(
        self,
        candles: pd.DataFrame,
        broken_index: int,
        broken_price: float,
        bullish: bool,
    ) -> int | None:
        """Find the candle index confirming the break of ``broken_price``."""
        closes = candles["close"].to_numpy()
        for k in range(broken_index, len(candles)):
            if bullish and closes[k] > broken_price:
                return int(k)
            if not bullish and closes[k] < broken_price:
                return int(k)
        return None

    def _classify_system(
        self, broken_price: float, external_prices: set[float]
    ) -> BreakSystem:
        """Classify a break as External or Internal.

        A price is considered external when it matches (within a small
        tolerance) one of the supplied external structural prices.
        """
        for ext in external_prices:
            if abs(broken_price - ext) < 1e-9:
                return BreakSystem.EXTERNAL
        return BreakSystem.INTERNAL


__all__ = ["BosDetector"]
