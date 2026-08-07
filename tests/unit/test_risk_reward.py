"""Unit tests for the Week 8 RiskRewardAnalyzer."""

import pytest

from risk.risk_reward import RiskRewardAnalyzer


def test_analyze_buy():
    analyzer = RiskRewardAnalyzer()
    ratio = analyzer.analyze(entry=1.20, stop=1.10, target=1.40)
    assert ratio == pytest.approx(2.0)


def test_analyze_sell():
    analyzer = RiskRewardAnalyzer()
    ratio = analyzer.analyze(entry=1.20, stop=1.30, target=1.00)
    assert ratio == pytest.approx(2.0)


def test_analyze_zero_risk_returns_zero():
    analyzer = RiskRewardAnalyzer()
    assert analyzer.analyze(entry=1.20, stop=1.20, target=1.40) == 0.0


def test_meets_minimum():
    analyzer = RiskRewardAnalyzer(min_rr=2.0)
    assert analyzer.meets_minimum(entry=1.20, stop=1.10, target=1.40)
    assert not analyzer.meets_minimum(entry=1.20, stop=1.10, target=1.30)


def test_meets_minimum_override():
    analyzer = RiskRewardAnalyzer(min_rr=2.0)
    assert analyzer.meets_minimum(entry=1.20, stop=1.10, target=1.30, min_rr=1.0)


def test_quality_tiers():
    analyzer = RiskRewardAnalyzer()
    assert analyzer.quality(0.0) == "NONE"
    assert analyzer.quality(0.5) == "POOR"
    assert analyzer.quality(1.5) == "FAIR"
    assert analyzer.quality(2.0) == "GOOD"
    assert analyzer.quality(3.0) == "EXCELLENT"
