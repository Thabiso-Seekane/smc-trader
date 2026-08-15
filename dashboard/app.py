"""Week 10 Streamlit Dashboard - main entrypoint.

Run with::

    streamlit run dashboard/app.py

The app wires the full SMC pipeline together:

    data -> structure -> liquidity -> CHoCH/BOS -> order blocks -> FVG
    -> strategy -> risk -> backtest

and renders the results with Plotly inside Streamlit. It is a **read-only**
analysis/backtesting tool - it never places a live order.
"""

from __future__ import annotations

import sys
from pathlib import Path

# --- bootstrap: ensure the project root is importable ----------
# When launched via `streamlit run dashboard/app.py`, Streamlit adds the
# *app* directory to sys.path, not the project root. The SMC packages
# (config, data, structure, ..., backtesting) live at the project root, so
# we insert it explicitly to make the full pipeline importable.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from dashboard.settings import DashboardConfig
from dashboard.pages import backtesting, liquidity, market_structure, overview, paper_trading, settings, smart_money, strategy, trades
from dashboard.services import load_analysis
from dashboard.widgets.sidebar import render_sidebar
from dashboard.state import get_bundle, set_bundle

st.set_page_config(
    page_title="SMC Trader",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 1) Render the sidebar (persists selections into session state).
config: DashboardConfig = render_sidebar()

# 2) Load (or reuse) the analysis bundle for the chosen symbol/timeframe.
bundle = get_bundle()
if bundle is None or bundle.symbol != config.symbol or bundle.timeframe != config.timeframe:
    with st.spinner("Running the SMC analysis pipeline..."):
        bundle = load_analysis(config)
        set_bundle(bundle)

# 3) Multi-page navigation.
PAGES = {
    "Overview": overview,
    "Market Structure": market_structure,
    "Liquidity": liquidity,
    "Smart Money (CHoCH/BOS/OB/FVG)": smart_money,
    "Confluence & Strategy": strategy,
    "Backtest": backtesting,
    "Trade Log": trades,
    "Paper Trading": paper_trading,
    "Settings": settings,
}

with st.sidebar:
    st.divider()
    page = st.radio("Section", list(PAGES.keys()), index=0, key="nav_page")

page_module = PAGES[page]

if page == "Overview":
    page_module.render(bundle)
elif page == "Trade Log":
    page_module.render()
elif page == "Backtest":
    page_module.render(bundle, config)
elif page == "Settings":
    page_module.render(config)
else:
    page_module.render(bundle)
