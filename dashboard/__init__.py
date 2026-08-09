"""Week 10 Streamlit Dashboard package.

The dashboard wires the full SMC pipeline together — data → structure →
liquidity → CHoCH/BOS → order blocks → FVG → strategy → risk → backtest —
and renders the results with Plotly inside Streamlit.

Run with::

    streamlit run dashboard/app.py
"""

from dashboard.services import AnalysisBundle
from dashboard.settings import DashboardConfig

__all__ = [
    "AnalysisBundle",
    "DashboardConfig",
]
