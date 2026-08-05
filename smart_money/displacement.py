"""Structural displacement detection.

Measures how "valid" a structural break is by scoring the displacement of
the confirmation candle. A genuine displacement shows a decisive body that
occupies most of the candle range and closes beyond the broken level — not
a wick that barely tags the level.

The displacement score is a 0–100 value used to validate that a CHoCH/BOS
break is structurally meaningful rather than a speculative false break.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from smart_money.enums import DisplacementQuality


@dataclass(slots=True)
class DisplacementDetector:
    """Validate structural displacement of a breakout candle.

    Attributes:
        min_body_ratio: Minimum body-to-range ratio for a candle to be
            considered displaced (0.0–1.0). Defaults to 0.5.
        min_move_pips: Minimum required move (in pips) beyond the broken
            level for the displacement to be considered strong. Supplied
            as a normalized price distance via ``pip_size``.
    """

    min_body_ratio: float = 0.5
    min_move_pips: float = 0.0

    def score(
        self,
        candles: pd.DataFrame,
        index: int,
        broken_price: float,
        direction_is_bullish: bool,
    ) -> float:
        """Score the displacement strength of a breakout candle.

        Args:
            candles: OHLCV candle DataFrame.
            index: Candle index that confirms the break.
            broken_price: Price of the structural level being broken.
            direction_is_bullish: True for a bullish break, False for a
                bearish break.

        Returns:
            A 0–100 displacement strength value.
        """
        if candles is None or candles.empty:
            return 0.0
        if index < 0 or index >= len(candles):
            return 0.0

        row = candles.iloc[index]
        high = float(row["high"])
        low = float(row["low"])
        open_ = float(row["open"])
        close = float(row["close"])

        rng = high - low
        if rng <= 0:
            return 0.0

        body = abs(close - open_)
        body_ratio = body / rng

        # Distance the candle closed beyond the broken level.
        if direction_is_bullish:
            beyond = close - broken_price
            body_beyond = close - max(open_, broken_price)
        else:
            beyond = broken_price - close
            body_beyond = min(open_, broken_price) - close

        beyond = max(0.0, beyond)
        body_beyond = max(0.0, body_beyond)

        # Score components.
        body_component = min(1.0, body_ratio / self.min_body_ratio) * 50.0
        move_component = min(1.0, beyond / (self.min_move_pips or 1e-9)) * 50.0
        body_beyond_component = min(1.0, body_beyond / (self.min_move_pips or 1e-9)) * 1.0

        score = body_component + move_component + body_beyond_component
        return round(max(0.0, min(100.0, score)), 2)

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


__all__ = ["DisplacementDetector"]
