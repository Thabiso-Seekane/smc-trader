"""Liquidity page — Week 10.

Renders the Week 3 liquidity map: buy-side vs sell-side levels, swept
levels, equal highs/lows, the strongest level, and the next target.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts import liquidity_chart
from dashboard.services import AnalysisBundle


def render(bundle: AnalysisBundle) -> None:
    """Render the liquidity page for the loaded bundle."""
    st.title("Liquidity")
    st.caption(f"{bundle.symbol} · {bundle.timeframe}")

    liquidity = bundle.liquidity
    if liquidity is None:
        st.info("No liquidity data loaded.")
        return

    levels = getattr(liquidity, "levels", []) or []
    buy_side = getattr(liquidity, "buy_side_levels", []) or []
    sell_side = getattr(liquidity, "sell_side_levels", []) or []
    swept = getattr(liquidity, "swept_levels", []) or []

    cols = st.columns(4)
    cols[0].metric("Total Levels", len(levels))
    cols[1].metric("Buy-Side", len(buy_side))
    cols[2].metric("Sell-Side", len(sell_side))
    cols[3].metric("Swept", len(swept))

    strongest = getattr(liquidity, "strongest", None)
    next_target = getattr(liquidity, "next_target", None)
    if strongest is not None:
        st.metric(
            "Strongest Level",
            f"{getattr(strongest, 'price', 0.0):.2f}",
            delta=f"{getattr(strongest, 'liquidity_type', '')}",
        )
    if next_target is not None:
        st.metric(
            "Next Target",
            f"{getattr(next_target, 'price', 0.0):.2f}",
            delta=f"{getattr(next_target, 'liquidity_type', '')}",
        )

    st.subheader("Liquidity Visualization")
    st.plotly_chart(liquidity_chart(bundle), use_container_width=True)

    # --- levels table -----------------------------------------
    st.subheader("Liquidity Levels")
    if levels:
        df = pd.DataFrame(
            [
                {
                    "Price": l.price,
                    "Type": str(getattr(l.liquidity_type, "value", l.liquidity_type)),
                    "Scope": str(getattr(l.scope, "value", l.scope)),
                    "Strength": l.strength,
                    "Swept": l.swept,
                    "Label": l.label,
                }
                for l in levels
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No liquidity levels detected.")

    # --- equal highs / lows -----------------------------------
    st.subheader("Equal Highs & Lows")
    clusters = getattr(liquidity, "clusters", []) or []
    if clusters:
        df = pd.DataFrame(
            [
                {
                    "Price": c.price,
                    "Type": str(getattr(c.liquidity_type, "value", c.liquidity_type)),
                    "Levels": c.size,
                    "Strength": c.strength,
                }
                for c in clusters
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No equal high/low clusters detected.")


__all__ = ["render"]
