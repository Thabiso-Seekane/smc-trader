"""Validation for Order Block zones.

Rejects weak zones that should never reach the strategy layer:

    * Tiny candles (range well below the local ATR).
    * Doji candles (no meaningful body).
    * Zones with no displacement (displacement strength below threshold).
    * Zones whose mitigating / invalidating state is already terminal
      (already mitigated or invalidated).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from smart_money.order_block_models import OrderBlock


@dataclass(slots=True)
class OrderBlockValidator:
    """Validate Order Block zones before they are stored.

    Attributes:
        min_displacement: Minimum displacement strength (0-100) for a zone
            to be considered valid.
        min_body_ratio: Minimum body-to-range ratio for the origin candle.
        tiny_atr_fraction: A candle whose range is below this fraction of
            the local ATR is considered "tiny" and rejected.
        reject_consumed: When True, reject zones already mitigated or
            invalidated (they are terminal and should not be re-used).
    """

    min_displacement: float = 30.0
    min_body_ratio: float = 0.3
    tiny_atr_fraction: float = 0.3
    reject_consumed: bool = True

    def is_valid(
        self,
        block: OrderBlock,
        candles: pd.DataFrame,
    ) -> bool:
        """Return True when the zone passes all validation checks.

        Args:
            block: The Order Block zone to validate.
            candles: OHLCV candle DataFrame used for ATR / body checks.

        Returns:
            True when the zone is valid and should be kept.
        """
        if block is None:
            return False

        # Displacement gate — an Order Block cannot exist without displacement.
        if block.displacement_score < self.min_displacement:
            return False

        # Terminal-state gate.
        if self.reject_consumed and (block.mitigated or block.invalidated):
            return False

        # Geometry gates.
        if block.range <= 0:
            return False

        if candles is None or candles.empty:
            return True  # nothing more to check without a frame

        if block.origin_index >= len(candles):
            return False

        row = candles.iloc[block.origin_index]
        high = float(row["high"])
        low = float(row["low"])
        open_ = float(row["open"])
        close = float(row["close"])
        rng = high - low
        if rng <= 0:
            return False
        body = abs(close - open_)
        if body / rng < self.min_body_ratio:
            return False

        atr = self._atr(candles, block.origin_index)
        if atr > 0 and rng < self.tiny_atr_fraction * atr:
            return False

        return True

    def _atr(self, candles: pd.DataFrame, index: int, period: int = 14) -> float:
        """Compute the average true range at ``index``."""
        start = max(0, index - period + 1)
        window = candles.iloc[start : index + 1]
        high = window["high"].to_numpy(dtype="float64")
        low = window["low"].to_numpy(dtype="float64")
        close = window["close"].to_numpy(dtype="float64")
        prev = np.roll(close, 1)
        prev[0] = close[0]
        tr = np.maximum(high - low, np.maximum(np.abs(high - prev), np.abs(low - prev)))
        return float(np.mean(tr)) if len(tr) else 0.0


__all__ = ["OrderBlockValidator"]
