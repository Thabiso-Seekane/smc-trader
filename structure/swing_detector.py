"""Swing detection algorithm.

Detects fractal swing highs and swing lows using a configurable left/right
confirmation window (the ``lookback``). A candle is a swing high when its
``high`` is strictly greater than the surrounding highs within the window;
a swing low when its ``low`` is strictly lower than the surrounding lows.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from structure.models import Swing


@dataclass(slots=True)
class SwingDetector:
    """Configurable fractal swing detector.

    Attributes:
        lookback: Number of candles on each side required to confirm a
            swing. Defaults to 2 (requires a 5-candle fractal).
    """

    lookback: int = 2

    def detect(self, candles: pd.DataFrame) -> list[Swing]:
        """Detect swing highs and lows in the supplied OHLC frame.

        Args:
            candles: DataFrame with ``date``, ``open``, ``high``, ``low``,
                ``close`` columns (``volume`` optional).

        Returns:
            A list of detected :class:`Swing` points, sorted by index.
        """
        if candles is None or candles.empty:
            return []

        highs = candles["high"].to_numpy()
        lows = candles["low"].to_numpy()
        timestamps = candles["date"].tolist()
        lookback = self.lookback

        swings: list[Swing] = []
        n = len(candles)

        for i in range(lookback, n - lookback):
            window_high = highs[i - lookback : i + lookback + 1]
            window_low = lows[i - lookback : i + lookback + 1]

            if highs[i] == window_high.max() and (window_high == highs[i]).sum() == 1:
                swings.append(
                    Swing(
                        index=i,
                        timestamp=timestamps[i],
                        price=float(highs[i]),
                        is_high=True,
                    )
                )

            if lows[i] == window_low.min() and (window_low == lows[i]).sum() == 1:
                swings.append(
                    Swing(
                        index=i,
                        timestamp=timestamps[i],
                        price=float(lows[i]),
                        is_high=False,
                    )
                )

        return swings

    def score_swing(self, swing: Swing, candles: pd.DataFrame) -> float:
        """Score the strength of a swing.

        Placeholder heuristic based on the swing's distance from the
        neighbouring candle close. Used to rank swings by relevance.

        Args:
            swing: The swing to score.
            candles: The OHLC frame the swing was detected from.

        Returns:
            A non-negative strength score.
        """
        if candles is None or candles.empty or swing.index < 0 or swing.index >= len(candles):
            return 0.0

        close = float(candles["close"].iloc[swing.index])
        return round(abs(swing.price - close), 6)


__all__ = ["SwingDetector"]
