"""Unit tests for the Week 8 RiskVisualizer."""

from risk.enums import PositionSizingMethod, RiskStatus
from risk.models import PositionSize, RiskMetrics, TradePlan
from risk.visualizer import RiskVisualizer


def make_plan() -> TradePlan:
    return TradePlan(
        symbol="XAUUSD",
        direction="BUY",
        entry_price=1.20,
        stop_loss=1.10,
        take_profit=1.40,
        position_size=PositionSize(
            lots=0.10, risk_amount=100.0, account_at_risk_pct=1.0
        ),
        risk_metrics=RiskMetrics(
            account_balance=10000.0,
            risk_percent=1.0,
            risk_amount=100.0,
            position_size=PositionSize(lots=0.10, risk_amount=100.0),
            status=RiskStatus.WITHIN_LIMIT,
        ),
    )


def test_summarize_contains_key_fields():
    viz = RiskVisualizer()
    text = viz.summarize(make_plan())
    assert "XAUUSD" in text
    assert "BUY" in text
    assert "1.20000" in text
    assert "0.10" in text
    assert "READY" in text


def test_summarize_includes_note_when_present():
    viz = RiskVisualizer()
    plan = make_plan()
    plan.note = "custom note"
    text = viz.summarize(plan)
    assert "custom note" in text


def test_to_text_alias():
    viz = RiskVisualizer()
    assert viz.to_text(make_plan()) == viz.summarize(make_plan())
