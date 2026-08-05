"""Unit tests for the smart money input validator."""

import pandas as pd
import pytest

from core.exceptions import DataValidationError
from liquidity.models import LiquidityMap
from smart_money.validator import SmartMoneyValidator
from structure.models import MarketStructure


def valid_frame():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01 00:00", "2024-01-01 00:05"]),
            "open": [1.0, 1.01],
            "high": [1.1, 1.11],
            "low": [0.9, 0.91],
            "close": [1.05, 1.06],
            "volume": [100, 110],
        }
    )


def test_valid_inputs_pass():
    SmartMoneyValidator().validate(
        candles=valid_frame(),
        structure=MarketStructure(),
        liquidity=LiquidityMap(),
    )


def test_empty_candles_raise():
    with pytest.raises(DataValidationError):
        SmartMoneyValidator().validate(
            candles=pd.DataFrame(),
            structure=MarketStructure(),
            liquidity=LiquidityMap(),
        )


def test_non_dataframe_candles_raise():
    with pytest.raises(DataValidationError):
        SmartMoneyValidator().validate(
            candles=[1, 2, 3],
            structure=MarketStructure(),
            liquidity=LiquidityMap(),
        )


def test_missing_columns_raise():
    frame = valid_frame().drop(columns=["volume"])
    with pytest.raises(DataValidationError):
        SmartMoneyValidator().validate(
            candles=frame,
            structure=MarketStructure(),
            liquidity=LiquidityMap(),
        )


def test_wrong_structure_type_raises():
    with pytest.raises(DataValidationError):
        SmartMoneyValidator().validate(
            candles=valid_frame(),
            structure="not-a-structure",
            liquidity=LiquidityMap(),
        )


def test_wrong_liquidity_type_raises():
    with pytest.raises(DataValidationError):
        SmartMoneyValidator().validate(
            candles=valid_frame(),
            structure=MarketStructure(),
            liquidity="not-a-map",
        )
