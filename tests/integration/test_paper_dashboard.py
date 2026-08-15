"""Dashboard navigation includes the read-only Paper Trading monitor."""

from pathlib import Path


def test_dashboard_exposes_paper_trading_page():
    source = (Path(__file__).resolve().parents[2] / "dashboard" / "app.py").read_text(encoding="utf-8")
    assert '"Paper Trading": paper_trading' in source
