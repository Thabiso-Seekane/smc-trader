"""Unit tests for the displacement detector."""

import pandas as pd

from smart_money.displacement import DisplacementDetector
from smart_money.enums import DisplacementQuality


def frame_with_single(open_, high, low, close):
    """Build a one-row candle frame with the given OHLC."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01 00:00"]),
            "open": [open_],
            "high": [high],
            "low": [low],
            "close": [close],
            "volume": [100],
        }
    )


def test_strong_bullish_displacement_scores_high():
    # Big bullish body occupying most of the range, closing well above break.
    frame = frame_with_single(open_=1.05, high=1.30, low=1.04, close=1.28)
    detector = DisplacementDetector(min_body_ratio=0.5, min_move_pips=0.1)
    score = detector.score(frame, 0, broken_price=1.0, direction_is_bullish=True)
    assert score >= 70.0
    assert detector.quality(score) == DisplacementQuality.STRONG


def test_weak_bearish_displacement_scores_low():
    # Small body, barely breaks below the level.
    frame = frame_with_single(open_=1.0, high=1.01, low=0.99, close=0.995)
    detector = DisplacementDetector(min_body_ratio=0.5, min_move_pips=0.1)
    score = detector.score(frame, 0, broken_price=1.0, direction_is_bullish=False)
    assert score < 40.0
    assert detector.quality(score) == DisplacementQuality.WEAK


def test_zero_body_scores_none():
    # Doji (no body) -> no displacement.
    frame = frame_with_single(open_=1.0, high=1.05, low=0.95, close=1.0)
    detector = DisplacementDetector(min_body_ratio=0.5, min_move_pips=0.1)
    score = detector.score(frame, 0, broken_price=1.0, direction_is_bullish=True)
    assert detector.quality(score) == DisplacementQuality.NONE


def test_out_of_range_index_scores_zero():
    frame = frame_with_single(1.0, 1.1, 0.9, 1.05)
    detector = DisplacementDetector()
    assert detector.score(frame, 5, broken_price=1.0, direction_is_bullish=True) == 0.0


def test_empty_frame_scores_zero():
    detector = DisplacementDetector()
    empty = pd.DataFrame(columns=["open", "high", "low", "close"])
    assert detector.score(empty, 0, broken_price=1.0, direction_is_bullish=True) == 0.0
