"""Sidebar controls for the Week 10 Streamlit dashboard.

The sidebar is the single place where the user selects the symbol, timeframe,
account posture, and refresh action. It writes the choices into the shared
:class:`DashboardConfig` held in session state.
"""

from __future__ import annotations

import streamlit as st

from dashboard.settings import SYMBOLS, TIMEFRAMES, DashboardConfig
from dashboard.state import get_config, set_config


def render_sidebar() -> DashboardConfig:
    """Render the sidebar inputs and persist them into session state.

    Returns:
        The active :class:`DashboardConfig` after applying user selections.
    """
    config = get_config()

    with st.sidebar:
        st.title("SMC Trader")
        st.caption("Smart Money Concepts — Week 10")

        symbol = st.selectbox(
            "Symbol",
            SYMBOLS,
            index=SYMBOLS.index(config.symbol)
            if config.symbol in SYMBOLS
            else 0,
            key="sel_symbol",
        )
        timeframe = st.selectbox(
            "Timeframe",
            TIMEFRAMES,
            index=TIMEFRAMES.index(config.timeframe)
            if config.timeframe in TIMEFRAMES
            else 2,
            key="sel_timeframe",
        )

        st.divider()
        st.subheader("Account")
        balance = st.number_input(
            "Balance ($)",
            min_value=100.0,
            value=float(config.balance),
            step=500.0,
            key="inp_balance",
        )
        risk_percent = st.slider(
            "Risk per trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=float(config.risk_percent),
            step=0.1,
            key="slider_risk",
        )
        min_conf = st.slider(
            "Min confluence",
            min_value=0,
            max_value=100,
            value=int(config.min_confluence),
            step=5,
            key="slider_conf",
        )
        min_rr = st.slider(
            "Min R:R",
            min_value=0.5,
            max_value=5.0,
            value=float(config.min_rr),
            step=0.5,
            key="slider_rr",
        )

        st.divider()
        st.caption("Changes persist for this session. Backtesting is a "
                   "read-only simulation — no live execution.")

    # Persist the selections back into the shared config.
    config.symbol = symbol
    config.timeframe = timeframe
    config.balance = float(balance)
    config.risk_percent = float(risk_percent)
    config.min_confluence = float(min_conf)
    config.min_rr = float(min_rr)
    set_config(config)

    return config
