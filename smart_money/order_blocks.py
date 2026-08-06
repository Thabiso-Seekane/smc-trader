"""Order Block detection.

An Order Block is the last opposing candle before a strong displacement
that breaks structure. It represents an institutional mandate zone where
price is likely to react.

Bullish Order Block::

    ... bearish candles ... -> last bearish candle -> strong bullish
    displacement -> break of structure -> the last bearish candle becomes
    the Bullish Order Block.

Bearish Order Block::

    ... bullish candles ... -> last bullish candle -> strong bearish
    displacement -> break of structure -> the last bullish candle becomes
    the Bearish Order Block.

The pipeline is:

    1. Consume a structural event (CHoCH/BOS) with valid displacement.
    2. Walk backwards from the event's confirmation index to find the last
       opposing candle (bearish for a Bullish OB, bullish for a Bearish OB).
    3. Build the zone from that candle's high/low.
    4. Validate the zone (delegated to the validator).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from smart_money.enums import Direction, OrderBlockType
from smart_money.models import StructureEvent
from smart_money.order_block_models import OrderBlock


def _label_direction(direction) -> Direction:
    """Normalize a direction (enum member/string) to a smart_money Direction."""
    if isinstance(direction, Direction):
        return direction
    val = str(direction).upper()
    if "BULL" in val or "LONG" in val or val == "UP":
        return Direction.BULLISH
    if "BEAR" in val or "SHORT" in val or val == "DOWN":
        return Direction.BEARISH
    return Direction.BULLISH


def _ob_type_from_direction(direction: Direction) -> OrderBlockType:
    """Map a smart_money Direction to an OrderBlockType."""
    return OrderBlockType.BULLISH if direction == Direction.BULLISH else OrderBlockType.BEARISH


@dataclass(slots=True)
class OrderBlockDetector:
    """Detect Bullish and Bearish Order Blocks from structural events.

    Attributes:
        lookback: Maximum number of candles to walk back when locating the
            origin candle.
        min_displacement: Minimum displacement strength (0-100) required for
            an event to seed an Order Block.
        min_body_ratio: Minimum body-to-range ratio for the origin candle so
            tiny / doji candles are rejected.
        reject_tiny: When True, origin candles whose range is below the ATR
            fraction are rejected.
        require_confirmed: When True, only events with confirmed displacement
            seed an Order Block.
    """

    lookback: int = 20
    min_displacement: float = 30.0
    min_body_ratio: float = 0.3
    reject_tiny: bool = True
    require_confirmed: bool = False

    def detect(
        self,
        events: list[StructureEvent],
        candles: pd.DataFrame,
        timeframe: str = "",
    ) -> list[OrderBlock]:
        """Detect Order Blocks from a list of structural events.

        Args:
            events: Structural events (CHoCH/BOS) from the Week 4 engine.
            candles: OHLCV candle DataFrame.
            timeframe: Label attached to detected zones.

        Returns:
            A list of :class:`OrderBlock` zones, ordered by origin index.
        """
        if not events or candles is None or candles.empty:
            return []

        blocks: list[OrderBlock] = []

        for event in events:
            if not self._eligible(event):
                continue
            block = self._build_block(event, candles, timeframe)
            if block is not None:
                blocks.append(block)

        blocks.sort(key=lambda b: b.origin_index)
        return blocks

    def _eligible(self, event: StructureEvent) -> bool:
        """Return True when an event can seed an Order Block."""
        if event.displacement_strength < self.min_displacement:
            return False
        if self.require_confirmed and not event.is_confirmed:
            return False
        return True

    def _build_block(
        self,
        event: StructureEvent,
        candles: pd.DataFrame,
        timeframe: str,
    ) -> OrderBlock | None:
        """Build a single Order Block from a structural event."""
        direction = _label_direction(event.direction)
        # A Bullish displacement seeds a Bullish Order Block whose origin is
        # the last bearish candle before the move.
        want_bearish = direction == Direction.BULLISH
        origin_index = self._find_origin_candle(
            candles, event.confirmation_index, want_bearish, event.broken_index
        )
        if origin_index is None:
            return None

        row = candles.iloc[origin_index]
        high = float(row["high"])
        low = float(row["low"])
        open_ = float(row["open"])
        close = float(row["close"])

        # Reject doji / tiny bodies.
        rng = high - low
        if rng <= 0:
            return None
        body = abs(close - open_)
        if body / rng < self.min_body_ratio:
            return None
        if self.reject_tiny and self._is_tiny(candles, origin_index, rng):
            return None

        return OrderBlock(
            direction=_ob_type_from_direction(direction),
            high=high,
            low=low,
            origin_index=origin_index,
            origin_time=row["date"],
            created_from_event=direction,
            displacement_score=event.displacement_strength,
            timeframe=timeframe,
        )

    def _find_origin_candle(
        self,
        candles: pd.DataFrame,
        confirm_index: int,
        want_bearish: bool,
        after_index: int = -1,
    ) -> int | None:
        """Find the last candle of the desired type before ``confirm_index``.

        Walks backwards from the confirmation candle looking for the last
        candle whose body is in the opposing direction (bearish for a bullish
        displacement). ``after_index`` optionally bounds the search to candles
        strictly after the broken structural level.
        """
        start = confirm_index - 1
        # Only search within the origin window.
        min_index = max(0, after_index + 1 if after_index >= 0 else 0)
        for k in range(start, min_index - 1, -1):
            if k < 0:
                break
            open_ = float(candles["open"].iloc[k])
            close = float(candles["close"].iloc[k])
            if want_bearish and close < open_:
                return int(k)
            if not want_bearish and close > open_:
                return int(k)
        return None

    def _is_tiny(
        self, candles: pd.DataFrame, index: int, rng: float, atr_period: int = 14
    ) -> bool:
        """Return True when the candle range is a small fraction of ATR."""
        start = max(0, index - atr_period + 1)
        window = candles.iloc[start : index + 1]
        high = window["high"].to_numpy(dtype="float64")
        low = window["low"].to_numpy(dtype="float64")
        close = window["close"].to_numpy(dtype="float64")
        prev = np.roll(close, 1)
        prev[0] = close[0]
        tr = np.maximum(high - low, np.maximum(np.abs(high - prev), np.abs(low - prev)))
        atr = float(np.mean(tr)) if len(tr) else 0.0
        if atr <= 0:
            return False
        return rng < 0.3 * atr


__all__ = ["OrderBlockDetector"]
