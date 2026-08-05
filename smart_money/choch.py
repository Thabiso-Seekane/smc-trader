"""Change of Character (CHoCH) detection.

A CHoCH is the **first** structural break after a liquidity sweep that
signals an intent to reverse the prevailing trend. It is distinct from a
BOS in that it requires a prior trend *and* a liquidity interaction before
the structural break.

Bullish CHoCH sequence::

    Downtrend (LL -> LH -> LL)
        |
        v
    Liquidity Sweep (sell-side taken)
        |
        v
    Higher Low (HL)
        |
        v
    Break of prior Lower High (LH)
        |
        v
    Bullish CHoCH

The detector does **not** simply fire because price breaks a level. It
requires all three pre-conditions:

    1. Existing bearish structure (a run of LL/LH before the reversal).
    2. Liquidity interaction (a sell-side level is swept).
    3. Structural break (HL forms, then price breaks the prior LH).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from smart_money.displacement import DisplacementDetector
from smart_money.enums import Direction, StructureEventType
from smart_money.models import StructureEvent
from structure.enums import StructureLabel, SwingType
from structure.models import MarketStructure, StructurePoint


def _label_value(label) -> str:
    """Normalize a structure label (enum member or raw string) to its value."""
    return label.value if isinstance(label, StructureLabel) else str(label)


@dataclass(slots=True)
class ChoCHDetector:
    """Detect Bullish and Bearish Changes of Character.

    Attributes:
        min_structure_points: Minimum number of prior bearish/bullish
            structure points required before a CHoCH can fire.
        min_displacement: Minimum displacement strength (0–100) required
            for a break to be considered a valid CHoCH.
        pip_size: Absolute price of one pip, used by the displacement
            detector to normalize the required move.
        min_move_pips: Minimum move (in pips) beyond the broken level
            required for valid displacement.
    """

    min_structure_points: int = 3
    min_displacement: float = 30.0
    pip_size: float = 0.0001
    min_move_pips: float = 1.0

    def detect(
        self,
        structure: MarketStructure,
        candles: pd.DataFrame,
        swept_sell_side: list,
        swept_buy_side: list,
    ) -> list[StructureEvent]:
        """Detect CHoCH events from structure, candles, and liquidity sweeps.

        Args:
            structure: Market structure from the Week 2 engine.
            candles: OHLCV candle DataFrame.
            swept_sell_side: Sell-side liquidity levels that were swept.
            swept_buy_side: Buy-side liquidity levels that were swept.

        Returns:
            A list of :class:`StructureEvent` CHoCH events, ordered by
            confirmation index.
        """
        if structure is None or candles is None or candles.empty:
            return []

        points = structure.points
        if len(points) < self.min_structure_points:
            return []

        events: list[StructureEvent] = []
        displacement = DisplacementDetector(
            min_body_ratio=0.5, min_move_pips=self.min_move_pips
        )

        for i in range(1, len(points)):
            current = points[i]
            previous = points[i - 1]

            # Bullish CHoCH: current is a Higher Low after a sweep.
            event = self._detect_bullish(
                points=points,
                i=i,
                current=current,
                previous=previous,
                candles=candles,
                swept_sell_side=swept_sell_side,
                displacement=displacement,
            )
            if event is not None:
                events.append(event)

            # Bearish CHoCH: current is a Lower High after a sweep.
            event = self._detect_bearish(
                points=points,
                i=i,
                current=current,
                previous=previous,
                candles=candles,
                swept_buy_side=swept_buy_side,
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
        swept_sell_side: list,
        displacement: DisplacementDetector,
    ) -> StructureEvent | None:
        """Detect a single Bullish CHoCH at point ``i``."""
        # The reversal start requires a Higher Low after a Lower Low,
        # signalling the first bullish structure after a downtrend.
        if current.swing_type != SwingType.LOW:
            return None
        if _label_value(current.label) != _label_value(StructureLabel.HL):
            return None
        if _label_value(previous.label) != _label_value(StructureLabel.LL):
            return None

        # 1) Existing bearish structure before this point.
        if not self._has_bearish_structure(points[: i + 1]):
            return None

        # 2) Liquidity interaction: a sell-side level must have been swept
        #    at or before the HL confirmation.
        if not self._liquidity_swept_before(
            swept_sell_side, current.index, is_buy_side=False
        ):
            return None

        # 3) Structural break: after the HL, price must break the prior
        #    Lower High (the most recent high before the HL).
        broken = self._find_break_high(points, i)
        if broken is None:
            return None

        confirm_index = self._find_break_confirmation(
            candles, broken_index=broken.index, broken_price=broken.price,
            bullish=True,
        )
        if confirm_index is None:
            return None

        strength = displacement.score(
            candles=candles,
            index=confirm_index,
            broken_price=broken.price,
            direction_is_bullish=True,
        )
        if strength < self.min_displacement:
            return None

        return StructureEvent(
            event_type=StructureEventType.CHOCH,
            direction=Direction.BULLISH,
            timestamp=candles["date"].iloc[confirm_index],
            broken_price=broken.price,
            broken_index=broken.index,
            confirmation_index=confirm_index,
            displacement_strength=strength,
            prev_swing_index=current.index,
            prev_swing_price=current.price,
            note="Bullish CHoCH after sell-side sweep",
        )

    def _detect_bearish(
        self,
        points: list[StructurePoint],
        i: int,
        current: StructurePoint,
        previous: StructurePoint,
        candles: pd.DataFrame,
        swept_buy_side: list,
        displacement: DisplacementDetector,
    ) -> StructureEvent | None:
        """Detect a single Bearish CHoCH at point ``i``."""
        # The reversal start requires a Lower High after a Higher High,
        # signalling the first bearish structure after an uptrend.
        if current.swing_type != SwingType.HIGH:
            return None
        if _label_value(current.label) != _label_value(StructureLabel.LH):
            return None
        if _label_value(previous.label) != _label_value(StructureLabel.HH):
            return None

        # 1) Existing bullish structure before this point.
        if not self._has_bullish_structure(points[: i + 1]):
            return None

        # 2) Liquidity interaction: a buy-side level must have been swept
        #    at or before the LH confirmation.
        if not self._liquidity_swept_before(
            swept_buy_side, current.index, is_buy_side=True
        ):
            return None

        # 3) Structural break: after the LH, price must break the prior
        #    Higher Low (the most recent low before the LH).
        broken = self._find_break_low(points, i)
        if broken is None:
            return None

        confirm_index = self._find_break_confirmation(
            candles, broken_index=broken.index, broken_price=broken.price,
            bullish=False,
        )
        if confirm_index is None:
            return None

        strength = displacement.score(
            candles=candles,
            index=confirm_index,
            broken_price=broken.price,
            direction_is_bullish=False,
        )
        if strength < self.min_displacement:
            return None

        return StructureEvent(
            event_type=StructureEventType.CHOCH,
            direction=Direction.BEARISH,
            timestamp=candles["date"].iloc[confirm_index],
            broken_price=broken.price,
            broken_index=broken.index,
            confirmation_index=confirm_index,
            displacement_strength=strength,
            prev_swing_index=current.index,
            prev_swing_price=current.price,
            note="Bearish CHoCH after buy-side sweep",
        )

    def _has_bearish_structure(self, points: list[StructurePoint]) -> bool:
        """Return True when the points contain a bearish LL/LH run."""
        bearish = {_label_value(StructureLabel.LL), _label_value(StructureLabel.LH)}
        count = sum(1 for p in points if _label_value(p.label) in bearish)
        return count >= self.min_structure_points

    def _has_bullish_structure(self, points: list[StructurePoint]) -> bool:
        """Return True when the points contain a bullish HH/HL run."""
        bullish = {_label_value(StructureLabel.HH), _label_value(StructureLabel.HL)}
        count = sum(1 for p in points if _label_value(p.label) in bullish)
        return count >= self.min_structure_points

    def _liquidity_swept_before(
        self, levels: list, index: int, is_buy_side: bool
    ) -> bool:
        """Return True when a level was swept at or before ``index``."""
        for level in levels:
            if not level.swept:
                continue
            if is_buy_side and not level.is_buy_side:
                continue
            if not is_buy_side and not level.is_sell_side:
                continue
            # The level's swing index must precede the reversal point.
            if level.swing_index is not None and level.swing_index <= index:
                return True
        return False

    def _find_break_high(
        self, points: list[StructurePoint], i: int
    ) -> StructurePoint | None:
        """Find the most recent high before ``i`` to break (bullish)."""
        for j in range(i - 1, -1, -1):
            if points[j].swing_type == SwingType.HIGH:
                return points[j]
        return None

    def _find_break_low(
        self, points: list[StructurePoint], i: int
    ) -> StructurePoint | None:
        """Find the most recent low before ``i`` to break (bearish)."""
        for j in range(i - 1, -1, -1):
            if points[j].swing_type == SwingType.LOW:
                return points[j]
        return None

    def _find_break_confirmation(
        self,
        candles: pd.DataFrame,
        broken_index: int,
        broken_price: float,
        bullish: bool,
    ) -> int | None:
        """Find the candle index confirming the break of ``broken_price``.

        The confirmation candle closes beyond the broken level and occurs
        after the broken swing's index.
        """
        closes = candles["close"].to_numpy()

        for k in range(broken_index, len(candles)):
            if bullish and closes[k] > broken_price:
                return int(k)
            if not bullish and closes[k] < broken_price:
                return int(k)
        return None


__all__ = ["ChoCHDetector"]
