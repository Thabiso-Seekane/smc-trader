"""Unit tests for the displacement detector."""

import pandas as pd

from smart_money.displacement import DisplacementDetector, DisplacementScore
from smart_money.enums import DisplacementQuality


def frame_with_candles(rows):
    """Build a candle frame from a list of (open, high, low, close, volume)."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [f"2024-01-01 00:{i:02d}" for i in range(len(rows))]
            ),
            "open": [r[0] for r in rows],
            "high": [r[1] for r in rows],
            "low": [r[2] for r in rows],
            "close": [r[3] for r in rows],
            "volume": [r[4] for r in rows],
        }
    )


def strong_bullish_frame():
    """A single decisive bullish candle breaking well above the level."""
    return frame_with_candles([(1.05, 1.30, 1.04, 1.28, 100)])


def weak_bearish_frame():
    """A barely-convincing bearish break.

    Price has been trending up (bullish momentum against the break), and
    the final candle only pokes marginally below the level with a small
    body. Neither momentum nor volume should inflate the displacement.
    """
    return frame_with_candles(
        [
            (1.00, 1.02, 0.99, 1.01, 100),
            (1.01, 1.03, 1.00, 1.02, 100),
            (1.02, 1.03, 1.01, 1.02, 100),
            (1.02, 1.021, 1.019, 1.0195, 100),
        ]
    )


def test_strong_bullish_displacement_scores_high():
    frame = strong_bullish_frame()
    detector = DisplacementDetector(min_body_ratio=0.5, min_move_pips=0.1)
    score = detector.assess(frame, 0, broken_price=1.0, direction_is_bullish=True)

    assert isinstance(score, DisplacementScore)
    assert score.strength >= 70.0
    assert score.confirmed is True
    assert score.atr_multiple >= 1.0
    assert detector.quality(score.strength) == DisplacementQuality.STRONG


def test_weak_bearish_displacement_scores_low():
    # Small body, barely breaks below the level, and momentum is against it.
    frame = weak_bearish_frame()
    detector = DisplacementDetector(min_body_ratio=0.5, min_move_pips=0.1)
    score = detector.assess(
        frame, len(frame) - 1, broken_price=1.02, direction_is_bullish=False
    )

    assert isinstance(score, DisplacementScore)
    assert score.strength < 40.0
    assert score.confirmed is False
    assert score.atr_multiple < 1.0
    assert detector.quality(score.strength) == DisplacementQuality.WEAK


def test_zero_body_scores_none():
    # Doji (no body) -> no displacement.
    frame = frame_with_candles([(1.0, 1.05, 0.95, 1.0, 100)])
    detector = DisplacementDetector(min_body_ratio=0.5, min_move_pips=0.1)
    score = detector.assess(frame, 0, broken_price=1.0, direction_is_bullish=True)

    assert score.strength == 0.0
    assert score.confirmed is False
    assert detector.quality(score.strength) == DisplacementQuality.NONE


def test_out_of_range_index_scores_zero():
    frame = frame_with_candles([(1.0, 1.1, 0.9, 1.05, 100)])
    detector = DisplacementDetector()
    score = detector.assess(frame, 5, broken_price=1.0, direction_is_bullish=True)
    assert score.strength == 0.0
    assert score.confirmed is False


def test_empty_frame_scores_zero():
    detector = DisplacementDetector()
    empty = pd.DataFrame(columns=["open", "high", "low", "close"])
    score = detector.assess(empty, 0, broken_price=1.0, direction_is_bullish=True)
    assert score.strength == 0.0
    assert score.confirmed is False


def test_consecutive_momentum_increases_score():
    # Two consecutive bullish candles: the second is the confirming break.
    frame = frame_with_candles(
        [
            (1.00, 1.20, 0.99, 1.15, 100),
            (1.15, 1.40, 1.05, 1.35, 100),
        ]
    )
    detector = DisplacementDetector(min_body_ratio=0.5, min_move_pips=0.1)
    score = detector.assess(frame, 1, broken_price=1.0, direction_is_bullish=True)
    assert score.strength >= 70.0
    assert score.confirmed is True


def test_score_convenience_returns_strength():
    frame = strong_bullish_frame()
    detector = DisplacementDetector(min_body_ratio=0.5, min_move_pips=0.1)
    strength = detector.score(frame, 0, broken_price=1.0, direction_is_bullish=True)
    assert isinstance(strength, float)
    assert strength >= 70.0
