"""Dashboard settings page for Week 10."""

from __future__ import annotations

import streamlit as st

from dashboard.settings import DashboardConfig


def render(config: DashboardConfig) -> None:
    """Explain the active dashboard configuration and execution boundary."""
    st.title("Settings")
    st.caption("Use the sidebar controls to update settings for this session.")

    st.subheader("Active Analysis Settings")
    st.dataframe(
        {
            "Setting": ["Symbol", "Timeframe", "Candles", "Minimum confluence", "Minimum R:R"],
            "Value": [config.symbol, config.timeframe, config.candle_count, config.min_confluence, config.min_rr],
        },
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Risk Settings")
    st.dataframe(
        {
            "Setting": ["Account balance", "Risk per trade", "Instrument point value"],
            "Value": [f"${config.balance:,.2f}", f"{config.risk_percent:.1f}%", config.instrument_joint],
        },
        use_container_width=True,
        hide_index=True,
    )
    st.info("This dashboard is read-only. Backtests are simulated and no live orders can be placed.")


__all__ = ["render"]
