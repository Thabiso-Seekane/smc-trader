"""Unit tests for the ImbalanceValidator."""

from datetime import datetime

import pandas as pd
import pytest

from smart_money.displacement import DisplacementScore
from smart_money.enums import OrderBlockType
from smart_money.fair_value_gap import FairValueGap
from smart_money.imbalance_validator import ImbalanceValidator


def make_candles(rows) -> pd.DataFrame:
    return pd.DataFrame(
        [
            [datetime(2024, 1, 1 + i), *values]
            for i, values in enumerate(rows)
        ],
        columns=["date", "open", "high", "low", "close", "volume"],
    )


def make_gap(high=15.0, low=10.0, displacement_strength=80.0, filled=False):
    return FairValueGap(
        direction=OrderBlockType.BULLISH,
        high=high,
        low=low,
        index=1,
        timestamp=datetime(2024, 1, 1),
        displacement=DisplacementScore(strength=displacement_strength),
        filled=filled,
    )


def test_valid_gap_passes():
    candles = make_candles(
        [
            [10, 10, 15, 10, 10],
            [15, 15, 20, 15, 15],
            [20, 20, 25, 20, 20],
        ]
    )
    validator = ImbalanceValidator(min_displacement=0.0, min_size_atr=0.0)
    assert validator.is_valid(make_gap(), candles)


def test_rejects_low_displacement():
    candles = make_candles([[10, 10, 15, 10, 10], [15, 15, 20, 15, 15]])
    validator = ImbalanceValidator(min_displacement=70.0)
    gap = make_gap(displacement_strength=30.0)
    assert validator.is_valid(gap, candles) is False


def test_rejects_filled_gap():
    candles = make_candles([[10, 10, 15, 10, 10], [15, 15, 20, 15, 15]])
    validator = ImbalanceValidator()
    assert validator.is_valid(make_gap(filled=True), candles) is False


def test_rejects_non_positive_range():
    candles = make_candles([[10, 10, 15, 10, 10], [15, 15, 20, 15, 15]])
    validator = ImbalanceValidator()
    gap = make_gap(high=10.0, low=10.0)
    assert validator.is_valid(gap, candles) is False


def test_rejects_none():
    validator = ImbalanceValidator()
    assert validator.is_valid(None, pd.DataFrame()) is False


def test_valid_without_frame():
    # With no candles, only displacement / geometry / fill checks apply.
    validator = ImbalanceValidator(min_displacement=0.0)
    assert validator.is_valid(make_gap(), pd.DataFrame()) is True


def test_rejects_too_small_gap_relative_to_atr():
    # Large ATR candles, tiny gap => rejected.
    candles = make_candles(
        [
            [10, 10, 100, 10, 10],   # huge range
            [15, 15, 100, 15, 15],
            [20, 20, 100, 20, 20],
        ]
    )
    validator = ImbalanceValidator(
        min_displacement=0.0, min_size_atr=0.5, reject_in_range=False
    )
    # gap range = 5, ATR ~ huge => 5 < 0.5 * ATR => rejected
    assert validator.is_valid(make_gap(high=15.0, low=10.0), candles) is False
