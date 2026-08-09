"""Session-state helpers for the Week 10 Streamlit dashboard.

Streamlit reruns the script frequently, so anything that must persist
between reruns lives in ``st.session_state`` (selected symbol, timeframe,
the last backtest result, the loaded analysis, etc.). This module centralises
that state so pages never read/write ``st.session_state`` keys ad-hoc.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.settings import DashboardConfig

# Keys used in st.session_state.
KEY_CONFIG = "smc_config"
KEY_ANALYSIS = "smc_analysis"
KEY_BACKTEST = "smc_backtest"
KEY_TRADES = "smc_trades"
KEY_SELECTED_TRADE = "smc_selected_trade"
KEY_DATE_RANGE = "smc_date_range"


def get_config() -> DashboardConfig:
    """Return the persisted :class:`DashboardConfig` (creating it if needed)."""
    if KEY_CONFIG not in st.session_state:
        st.session_state[KEY_CONFIG] = DashboardConfig()
    return st.session_state[KEY_CONFIG]


def set_config(config: DashboardConfig) -> None:
    """Persist a :class:`DashboardConfig` into session state."""
    st.session_state[KEY_CONFIG] = config


def get_analysis() -> Any | None:
    """Return the cached analysis bundle (structure/liquidity/strategy)."""
    return st.session_state.get(KEY_ANALYSIS)


def set_analysis(bundle: Any) -> None:
    """Persist the analysis bundle into session state."""
    st.session_state[KEY_ANALYSIS] = bundle


def get_bundle() -> Any | None:
    """Alias for :func:`get_analysis` (the analysis bundle)."""
    return get_analysis()


def set_bundle(bundle: Any) -> None:
    """Alias for :func:`set_analysis` (persist the analysis bundle)."""
    set_analysis(bundle)


def get_backtest() -> Any | None:
    """Return the cached backtest result, if any."""
    return st.session_state.get(KEY_BACKTEST)


def set_backtest(result: Any) -> None:
    """Persist the backtest result into session state."""
    st.session_state[KEY_BACKTEST] = result


def get_trades() -> list[Any]:
    """Return the trade list (from the last backtest)."""
    return st.session_state.get(KEY_TRADES, [])


def set_trades(trades: list[Any]) -> None:
    """Persist the trade list into session state."""
    st.session_state[KEY_TRADES] = trades


def get_selected_trade() -> int | None:
    """Return the currently selected trade index, if any."""
    return st.session_state.get(KEY_SELECTED_TRADE)


def set_selected_trade(index: int | None) -> None:
    """Persist the selected trade index (for replay / inspection)."""
    st.session_state[KEY_SELECTED_TRADE] = index


def get_date_range() -> tuple | None:
    """Return the selected backtest date range, if any."""
    return st.session_state.get(KEY_DATE_RANGE)


def set_date_range(start, end) -> None:
    """Persist the selected backtest date range."""
    st.session_state[KEY_DATE_RANGE] = (start, end)


def init_state() -> None:
    """Ensure all default state keys exist (called once at startup)."""
    get_config()


__all__ = [
    "get_config",
    "set_config",
    "get_analysis",
    "set_analysis",
    "get_bundle",
    "set_bundle",
    "get_backtest",
    "set_backtest",
    "get_trades",
    "set_trades",
    "get_selected_trade",
    "set_selected_trade",
    "get_date_range",
    "set_date_range",
    "init_state",
]
