"""Smart Money (CHoCH / BOS / OB / FVG) page — Week 10.

Renders the Week 4-6 outputs: structural events (CHoCH/BOS), order blocks,
and fair-value gaps / imbalances.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts import smart_money_chart
from dashboard.services import AnalysisBundle


def render(bundle: AnalysisBundle) -> None:
    """Render the smart-money page for the loaded bundle."""
    st.title("Smart Money — CHoCH / BOS / OB / FVG")
    st.caption(f"{bundle.symbol} · {bundle.timeframe}")

    st.subheader("Structural Events (CHoCH / BOS)")
    events = bundle.events
    event_list = getattr(events, "events", []) or [] if events is not None else []
    if event_list:
        df = pd.DataFrame(
            [
                {
                    "Time": e.timestamp,
                    "Type": str(getattr(e.event_type, "value", e.event_type)),
                    "Direction": str(getattr(e.direction, "value", e.direction)),
                    "Broken Price": e.broken_price,
                    "Confirmation": e.confirmation_index,
                    "Displacement": e.displacement_strength,
                    "Note": e.note,
                }
                for e in event_list
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No structural events detected.")

    st.subheader("SMC Visualization")
    st.plotly_chart(smart_money_chart(bundle), use_container_width=True)

    # --- order blocks -----------------------------------------
    st.subheader("Order Blocks")
    ob = bundle.order_blocks
    ob_list = getattr(ob, "all", []) or [] if ob is not None else []
    if ob_list:
        df = pd.DataFrame(
            [
                {
                    "Dir": str(getattr(b.direction, "value", b.direction)),
                    "High": b.high,
                    "Low": b.low,
                    "Strength": b.strength,
                    "Fresh": b.fresh,
                    "Touches": b.touch_count,
                    "Status": str(getattr(b.status, "value", b.status)),
                }
                for b in ob_list
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No order blocks detected.")

    # --- FVGs / imbalances -------------------------------------
    st.subheader("Fair Value Gaps")
    fvg = bundle.imbalances
    gap_list = getattr(fvg, "all", []) or [] if fvg is not None else []
    if gap_list:
        df = pd.DataFrame(
            [
                {
                    "Dir": str(getattr(g.direction, "value", g.direction)),
                    "High": g.high,
                    "Low": g.low,
                    "Strength": g.strength,
                    "Fill": f"{g.fill_percentage:.0f}%",
                    "Touches": g.touch_count,
                    "Fresh": g.freshness,
                }
                for g in gap_list
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No fair value gaps detected.")


__all__ = ["render"]
