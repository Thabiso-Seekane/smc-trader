"""Unit tests for the trend analyzer using synthetic, deterministic data."""

from datetime import datetime

from structure.enums import StructureLabel, SwingType, Trend
from structure.models import StructurePoint
from structure.trend_analyzer import TrendAnalyzer


def make_point(label, index=0):
    """Build a classified structure point with the given label."""
    return StructurePoint(
        index=index,
        timestamp=datetime(2024, 1, 1),
        price=100.0,
        swing_type=SwingType.HIGH if label in (StructureLabel.HH, StructureLabel.LH)
        else SwingType.LOW,
        label=label,
    )


def test_empty_points_is_range():
    assert TrendAnalyzer().analyze([]) == (Trend.RANGE, Trend.RANGE)


def test_bullish_sequence_is_bullish():
    # HH, HL, HH -> bullish
    points = [
        make_point(StructureLabel.HH),
        make_point(StructureLabel.HL),
        make_point(StructureLabel.HH),
    ]
    current, previous = TrendAnalyzer().analyze(points)
    assert current == Trend.BULLISH


def test_bearish_sequence_is_bearish():
    # LL, LH, LL -> bearish
    points = [
        make_point(StructureLabel.LL),
        make_point(StructureLabel.LH),
        make_point(StructureLabel.LL),
    ]
    current, previous = TrendAnalyzer().analyze(points)
    assert current == Trend.BEARISH


def test_mixed_structure_is_transition():
    # HH, LL -> mixed bullish and bearish -> transition
    points = [
        make_point(StructureLabel.HH),
        make_point(StructureLabel.LL),
    ]
    current, _ = TrendAnalyzer().analyze(points)
    assert current == Trend.TRANSITION


def test_single_point_reports_previous_range():
    points = [make_point(StructureLabel.HH)]
    current, previous = TrendAnalyzer().analyze(points)
    assert current == Trend.BULLISH
    assert previous == Trend.RANGE
