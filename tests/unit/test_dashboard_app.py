"""Smoke-test the Week 10 dashboard app using Streamlit's AppTest.

Run::

    python -m pytest tests/unit/test_dashboard_app.py -q

This drives the real Streamlit runtime headlessly and asserts the main page
renders without raising. It does not require MT5 (data loading falls back to
an empty frame when no data store / terminal is available).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

streamlit = pytest.importorskip("streamlit")
AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

APP_PATH = str(Path(__file__).resolve().parents[2] / "dashboard" / "app.py")


def test_dashboard_app_runs_without_error():
    """The app imports and runs the overview page without raising.

    With no data store / MT5 available, the service layer falls back to
    deterministic synthetic candles, so the full pipeline (structure →
    liquidity → CHoCH/BOS → OB → FVG → strategy → risk → backtest) runs and
    the overview page renders without a live data source.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=180)
    at.run()
    assert not at.exception, f"Dashboard raised: {at.exception}"


if __name__ == "__main__":
    test_dashboard_app_runs_without_error()
    print("DASHBOARD APP SMOKE TEST OK")
