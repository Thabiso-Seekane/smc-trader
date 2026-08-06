"""Validation for imbalance (Fair Value Gap) zones.

Rejects weak gaps that should never reach the strategy layer:

    * Gaps that are too small (range well below the local ATR).
    * Gaps with no displacement (displacement below threshold).
    * Gaps that are already fully filled (terminal).
    * Gaps created inside a choppy / ranging market (weak structural
      context).
    * Gaps with invalid geometry (non-positive range).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from smart_money.fair_value_gap import FairValueGap


@dataclass(slots=True)
class ImbalanceValidator:
    """Validate Fair Value Gap zones before they are stored.

    Attributes:
        min_displacement: Minimum displacement strength (0-100) for a gap
            to be considered valid.
        min_size_atr: A gap whose range is below this fraction of the local
            ATR is considered too small and rejected.
        reject_filled: When True, reject gaps that are already fully filled
            (they are terminal and should not be re-used).
        reject_in_range: When True, reject gaps whose surrounding window is
            choppy (low directional range relative to ATR).
    """

    min_displacement: float = 30.0
    min_size_atr: float = 0.2
    reject_filled: bool = True
    reject_in_range: bool = False

    def is_valid(
        self,
        gap: FairValueGap,
        candles: pd.DataFrame,
    ) -> bool:
        """Return True when the gap passes all validation checks.

        Args:
            gap: The Fair Value Gap to validate.
            candles: OHLCV candle DataFrame used for ATR / range checks.

        Returns:
            True when the gap is valid and should be kept.
        """
        if gap is None:
            return False

        # Displacement gate — a gap cannot exist without displacement.
        if gap.displacement_strength < self.min_displacement:
            return False

        # Terminal-state gate.
        if self.reject_filled and gap.filled:
            return False

        # Geometry gate.
        if gap.range <= 0:
            return False

        if candles is None or candles.empty:
            return True  # nothing more to check without a frame

        if gap.index >= len(candles):
            return False

        atr = self._atr(candles, gap.index)
        if atr > 0 and gap.range < self.min_size_atr * atr:
            return False

        # Choppy-range gate.
        if self.reject_in_range and self._in_range(candles, gap.index, atr):
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

    def _in_range(
        self, candles: pd.DataFrame, index: int, atr: float, window: int = 5
    ) -> bool:
        """Return True when the surrounding market is choppy / ranging.

        A market is considered "in range" when the net displacement across
        the window is small relative to the total range travelled (low
        trending efficiency).
        """
        start = max(0, index - window + 1)
        end = min(len(candles), index + window + 1)
        window_df = candles.iloc[start:end]
        if len(window_df) < 2:
            return False
        closes = window_df["close"].to_numpy(dtype="float64")
        highs = window_df["high"].to_numpy(dtype="float64")
        lows = window_df["low"].to_numpy(dtype="float64")
        net = abs(closes[-1] - closes[0])
        total = float(np.sum(highs - lows))
        if total <= 0:
            return True
        efficiency = net / total
        # Efficiency below 15% suggests chop.
        return efficiency < 0.15 and atr > 0


__all__ = ["ImbalanceValidator"]
