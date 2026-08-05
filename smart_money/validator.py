"""Input validation for the Smart Money (CHoCH / BOS) engine.

Ensures the engine is given well-formed candle, structure, and liquidity
inputs before any detection runs. Reuses the shared domain exception
``DataValidationError`` so callers can catch a single error type across
the data pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.exceptions import DataValidationError
from liquidity.models import LiquidityMap
from structure.models import MarketStructure

# Columns required on a candle frame.
_CANDLE_COLUMNS = ("date", "open", "high", "low", "close", "volume")


@dataclass(slots=True)
class SmartMoneyValidator:
    """Validate inputs passed to the Smart Money analyzer."""

    def validate(
        self,
        candles: pd.DataFrame,
        structure: MarketStructure,
        liquidity: LiquidityMap,
    ) -> None:
        """Validate the candle, structure, and liquidity inputs.

        Args:
            candles: OHLCV candle DataFrame.
            structure: Market structure from the Week 2 engine.
            liquidity: Liquidity map from the Week 3 engine.

        Raises:
            DataValidationError: if any input is malformed.
        """
        self._validate_candles(candles)
        self._validate_structure(structure)
        self._validate_liquidity(liquidity)

    def _validate_candles(self, candles: pd.DataFrame) -> None:
        """Ensure the candle frame is non-empty and well-formed."""
        if not isinstance(candles, pd.DataFrame):
            raise DataValidationError("candles must be a pandas DataFrame")
        if candles.empty:
            raise DataValidationError("candles DataFrame is empty")
        missing = [col for col in _CANDLE_COLUMNS if col not in candles.columns]
        if missing:
            raise DataValidationError(
                "candles is missing required columns: " + ", ".join(missing)
            )

    def _validate_structure(self, structure: MarketStructure) -> None:
        """Ensure the market structure is present."""
        if not isinstance(structure, MarketStructure):
            raise DataValidationError("structure must be a MarketStructure")

    def _validate_liquidity(self, liquidity: LiquidityMap) -> None:
        """Ensure the liquidity map is present."""
        if not isinstance(liquidity, LiquidityMap):
            raise DataValidationError("liquidity must be a LiquidityMap")


__all__ = ["SmartMoneyValidator"]
