"""Structural displacement detection.

Measures how "valid" a structural break is by scoring the displacement of
the confirmation candle. A genuine displacement shows a decisive body that
occupies most of the candle range and closes beyond the broken level — not
a wick that barely tags the level nor a tiny move that fizzles.

A BOS/CHoCH without displacement is weak. Displacement is scored from a
combination of factors:

    * Candle body size (body-to-range ratio)
    * ATR multiple (close beyond the level relative to average true range)
    * Volume (if available) relative to the nearby average
    * Close beyond the broken structure
    * Consecutive momentum candles in the break direction

The result is a :class:`DisplacementScore` exposing a 0–100 ``strength``,
the ``atr_multiple`` achieved, and a boolean ``confirmed`` flag.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from smart_money.enums import DisplacementQuality


@dataclass(slots=True)
class DisplacementScore:
    """Quantified displacement of a structural breakout.

    Attributes:
        strength: 0–100 composite displacement strength.
        atr_multiple: How far the close pierced the broken level measured
            in multiples of the average true range.
        confirmed: True when the break is strong enough to be trusted
            (strength above the confirmation threshold and at least one
            ATR of extension).
    """

    strength: float = 0.0
    atr_multiple: float = 0.0
    confirmed: bool = False


@dataclass(slots=True)
class DisplacementDetector:
    """Validate structural displacement of a breakout candle.

    Attributes:
        min_body_ratio: Minimum body-to-range ratio for a candle to be
            considered displaced (0.0–1.0). Defaults to 0.5.
        min_move_pips: Minimum required move (in normalized price units)
            beyond the broken level.
        atr_period: Lookback window used to compute average true range.
        min_atr_multiple: Minimum ATR multiple for a break to be
            considered confirmed.
        min_volume_ratio: Minimum volume multiple relative to the recent
            average for a break to be considered confirmed.
        confirm_threshold: Displacement strength at or above which a break
            is considered confirmed.
        min_consecutive: Minimum number of consecutive momentum candles
            required for a strong confirmation.
    """

    min_body_ratio: float = 0.5
    min_move_pips: float = 0.0
    atr_period: int = 14
    min_atr_multiple: float = 1.0
    min_volume_ratio: float = 1.0
    confirm_threshold: float = 70.0
    min_consecutive: int = 1

    def assess(
        self,
        candles: pd.DataFrame,
        index: int,
        broken_price: float,
        direction_is_bullish: bool,
    ) -> DisplacementScore:
        """Assess the displacement of a breakout candle.

        Args:
            candles: OHLCV candle DataFrame.
            index: Candle index that confirms the break.
            broken_price: Price of the structural level being broken.
            direction_is_bullish: True for a bullish break, False for a
                bearish break.

        Returns:
            A :class:`DisplacementScore` for the breakout.
        """
        empty = DisplacementScore()
        if candles is None or candles.empty:
            return empty
        if index < 0 or index >= len(candles):
            return empty

        row = candles.iloc[index]
        high = float(row["high"])
        low = float(row["low"])
        open_ = float(row["open"])
        close = float(row["close"])

        rng = high - low
        if rng <= 0:
            return empty

        body = abs(close - open_)
        body_ratio = body / rng

        # A candle with no body (doji) has no displacement, regardless of
        # volume or momentum.
        if body_ratio <= 0:
            return empty

        # Distance the candle closed beyond the broken level.
        if direction_is_bullish:
            beyond = close - broken_price
        else:
            beyond = broken_price - close
        beyond = max(0.0, beyond)

        atr = self._average_true_range(candles, index)
        atr_multiple = (beyond / atr) if atr > 0 else 0.0

        # Volume ratio (if volume is available).
        volume_ratio = self._volume_ratio(candles, index)

        # Consecutive momentum candles in the break direction.
        momentum = self._consecutive_momentum(candles, index, direction_is_bullish)

        # --- Composite 0-100 score --------------------------------
        # Body size contributes up to 30.
        body_component = min(1.0, body_ratio / self.min_body_ratio) * 30.0
        # ATR multiple contributes up to 30.
        atr_component = min(1.0, atr_multiple / self.min_atr_multiple) * 30.0
        # Closing beyond the level (normalized move) contributes up to 20.
        move_component = min(1.0, beyond / (self.min_move_pips or 1e-9)) * 20.0
        # Volume contributes up to 10.
        volume_component = min(1.0, volume_ratio / self.min_volume_ratio) * 10.0
        # Momentum contributes up to 10.
        momentum_component = min(1.0, momentum / self.min_consecutive) * 10.0

        strength = (
            body_component
            + atr_component
            + move_component
            + volume_component
            + momentum_component
        )
        strength = round(max(0.0, min(100.0, strength)), 2)

        confirmed = (
            strength >= self.confirm_threshold and atr_multiple >= self.min_atr_multiple
        )

        return DisplacementScore(
            strength=strength,
            atr_multiple=round(atr_multiple, 3),
            confirmed=confirmed,
        )

    def score(
        self,
        candles: pd.DataFrame,
        index: int,
        broken_price: float,
        direction_is_bullish: bool,
    ) -> float:
        """Return only the 0–100 displacement strength.

        Convenience helper that delegates to :meth:`assess` and returns the
        ``strength`` field. Useful when callers only need the numeric value.

        Args:
            candles: OHLCV candle DataFrame.
            index: Candle index that confirms the break.
            broken_price: Price of the structural level being broken.
            direction_is_bullish: True for a bullish break.

        Returns:
            The 0–100 displacement strength.
        """
        return self.assess(
            candles, index, broken_price, direction_is_bullish
        ).strength

    def quality(self, score: float) -> DisplacementQuality:
        """Classify a displacement score into a quality label.

        Args:
            score: A 0–100 displacement strength value.

        Returns:
            A :class:`DisplacementQuality` label.
        """
        if score <= 0:
            return DisplacementQuality.NONE
        if score < 40:
            return DisplacementQuality.WEAK
        if score < 70:
            return DisplacementQuality.MODERATE
        return DisplacementQuality.STRONG

    def _average_true_range(self, candles: pd.DataFrame, index: int) -> float:
        """Compute the ATR at ``index`` over ``atr_period`` candles."""
        start = max(0, index - self.atr_period + 1)
        window = candles.iloc[start : index + 1]

        high = window["high"].to_numpy(dtype="float64")
        low = window["low"].to_numpy(dtype="float64")
        close = window["close"].to_numpy(dtype="float64")

        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]

        tr = np.maximum(high - low, np.maximum(
            np.abs(high - prev_close), np.abs(low - prev_close)
        ))
        return float(np.mean(tr)) if len(tr) else 0.0

    def _volume_ratio(self, candles: pd.DataFrame, index: int) -> float:
        """Return the candle volume relative to the recent average volume."""
        if "volume" not in candles.columns:
            return 1.0
        start = max(0, index - self.atr_period + 1)
        window = candles.iloc[start : index + 1]
        volumes = window["volume"].to_numpy(dtype="float64")
        if len(volumes) == 0 or volumes[-1] == 0:
            return 0.0
        avg = float(np.mean(volumes[:-1])) if len(volumes) > 1 else float(volumes[-1])
        if avg <= 0:
            return 1.0
        return float(volumes[-1]) / avg

    def _consecutive_momentum(
        self, candles: pd.DataFrame, index: int, direction_is_bullish: bool
    ) -> int:
        """Count consecutive momentum candles in the break direction.

        A bullish momentum candle closes above its open; a bearish one
        closes below its open.
        """
        closes = candles["close"].to_numpy(dtype="float64")
        opens = candles["open"].to_numpy(dtype="float64")
        count = 0
        for k in range(index, -1, -1):
            bullish = closes[k] > opens[k]
            bearish = closes[k] < opens[k]
            if direction_is_bullish and bullish:
                count += 1
            elif not direction_is_bullish and bearish:
                count += 1
            else:
                break
        return count


__all__ = ["DisplacementDetector", "DisplacementScore"]
