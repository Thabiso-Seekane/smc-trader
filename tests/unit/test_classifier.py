"""Unit tests for the swing classifier using synthetic, deterministic data."""

from datetime import datetime

from structure.enums import StructureLabel, SwingType
from structure.models import StructurePoint, Swing
from structure.swing_classifier import SwingClassifier


def make_swing(index, price, is_high):
    return Swing(
        index=index,
        timestamp=datetime(2024, 1, 1),
        price=float(price),
        is_high=is_high,
    )


def test_first_high_and_first_low_are_baseline():
    swings = [
        make_swing(2, 102.0, True),   # first high -> HH baseline
        make_swing(4, 99.0, False),   # first low  -> LL baseline
    ]
    points = SwingClassifier().classify(swings)

    assert points[0].label == StructureLabel.HH
    assert points[1].label == StructureLabel.LL


def test_higher_highs_and_higher_lows():
    # two highs that rise, two lows that rise -> HH, HL
    swings = [
        make_swing(2, 102.0, True),   # HH
        make_swing(4, 99.0, False),   # LL
        make_swing(6, 104.0, True),   # HH (higher than 102)
        make_swing(8, 101.0, False),  # HL (higher than 99)
    ]
    points = SwingClassifier().classify(swings)

    assert [p.label for p in points] == [
        StructureLabel.HH,
        StructureLabel.LL,
        StructureLabel.HH,
        StructureLabel.HL,
    ]


def test_lower_highs_and_lower_lows():
    # two highs that fall, two lows that fall -> LH, LL
    swings = [
        make_swing(2, 104.0, True),   # HH
        make_swing(4, 101.0, False),  # LL
        make_swing(6, 102.0, True),   # LH (lower than 104)
        make_swing(8, 99.0, False),   # LL (lower than 101)
    ]
    points = SwingClassifier().classify(swings)

    assert [p.label for p in points] == [
        StructureLabel.HH,
        StructureLabel.LL,
        StructureLabel.LH,
        StructureLabel.LL,
    ]


def test_empty_swings_yield_no_points():
    assert SwingClassifier().classify([]) == []


def test_points_preserve_price_and_type():
    swings = [make_swing(2, 102.0, True)]
    points = SwingClassifier().classify(swings)

    point = points[0]
    assert isinstance(point, StructurePoint)
    assert point.index == 2
    assert point.price == 102.0
    assert point.swing_type == SwingType.HIGH
