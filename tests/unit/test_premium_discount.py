"""Unit tests for the Premium/Discount analyzer."""

import pytest

from strategy.enums import PremiumDiscountPosition, SignalDirection
from strategy.premium_discount import PremiumDiscountAnalyzer


@pytest.fixture
def analyzer() -> PremiumDiscountAnalyzer:
    return PremiumDiscountAnalyzer()


def test_equilibrium_midpoint(analyzer):
    assert analyzer.equilibrium(1.20, 1.00) == pytest.approx(1.10)


def test_above_equilibrium_is_premium(analyzer):
    assert analyzer.analyze(1.15, 1.20, 1.00) == PremiumDiscountPosition.PREMIUM


def test_below_equilibrium_is_discount(analyzer):
    assert analyzer.analyze(1.05, 1.20, 1.00) == PremiumDiscountPosition.DISCOUNT


def test_at_equilibrium_is_equilibrium(analyzer):
    assert analyzer.analyze(1.10, 1.20, 1.00) == PremiumDiscountPosition.EQUILIBRIUM


def test_buy_scores_high_in_discount(analyzer):
    score = analyzer.score(PremiumDiscountPosition.DISCOUNT, SignalDirection.BUY)
    assert score == 100.0


def test_buy_scores_low_in_premium(analyzer):
    score = analyzer.score(PremiumDiscountPosition.PREMIUM, SignalDirection.BUY)
    assert score == 30.0


def test_sell_scores_high_in_premium(analyzer):
    score = analyzer.score(PremiumDiscountPosition.PREMIUM, SignalDirection.SELL)
    assert score == 100.0


def test_sell_scores_low_in_discount(analyzer):
    score = analyzer.score(PremiumDiscountPosition.DISCOUNT, SignalDirection.SELL)
    assert score == 30.0


def test_equilibrium_is_neutral(analyzer):
    assert analyzer.score(PremiumDiscountPosition.EQUILIBRIUM, SignalDirection.BUY) == 50.0


def test_position_for_direction(analyzer):
    assert analyzer.position_for_direction(SignalDirection.BUY) == PremiumDiscountPosition.DISCOUNT
    assert analyzer.position_for_direction(SignalDirection.SELL) == PremiumDiscountPosition.PREMIUM
