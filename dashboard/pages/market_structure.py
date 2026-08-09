"""Market Structure page — Week 10.

Renders the Week 2 market structure result: the current/previous trend,
classified structure points (HH/HL/LH/LL), and the swing history.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts import market_structure_chart
from dashboard.services import AnalysisBundle


def render(bundle: AnalysisBundle) -> None:
    """Render the market-structure page for the loaded bundle."""
    st.title("Market Structure")
    st.caption(f"{bundle.symbol} · {bundle.timeframe}")

    structure = bundle.structure
    if structure is None:
        st.info("No market-structure data loaded.")
        return

    cols = st.columns(4)
    trend = getattr(structure, "trend", None)
    prev_trend = getattr(structure, "previous_trend", None)
    cols[0].metric("Current Trend", str(getattr(trend, "value", trend)))
    cols[1].metric("Previous Trend", str(getattr(prev_trend, "value", prev_trend)))

    swings = getattr(structure, "swings", []) or []
    points = getattr(structure, "points", []) or []
    cols[2].metric("Swings", len(swings))
    cols[3].metric("Structure Points", len(points))

    st.subheader("Structure Visualization")
    st.plotly_chart(market_structure_chart(bundle), use_container_width=True)

    # --- structure points table ------------------------------
    st.subheader("Structure Points")
    if points:
        df = pd.DataFrame(
            [
                {
                    "Index": p.index,
                    "Time": p.timestamp,
                    "Price": p.price,
                    "Type": str(getattr(p.swing_type, "value", p.swing_type)),
                    "Label": str(getattr(p.label, "value", p.label)),
                }
                for p in points
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No classified structure points.")

    # --- swings table -----------------------------------------
    st.subheader("Swings")
    if swings:
        df = pd.DataFrame(
            [
                {
                    "Index": s.index,
                    "Time": s.timestamp,
                    "Price": s.price,
                    "Type": "High" if s.is_high else "Low",
                    "Score": s.score,
                }
                for s in swings
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No swings detected.")


__all__ = ["render"]
