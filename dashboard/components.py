"""Reusable, presentation-only Streamlit components for the dashboard."""

from __future__ import annotations

import streamlit as st


def render_metric(label: str, value, delta: str | None = None) -> None:
    """Render a single dashboard metric card."""
    st.metric(label=label, value=value, delta=delta)


def render_metrics_row(metrics: dict) -> None:
    """Render a row of metric cards from a label-to-value mapping."""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        with col:
            st.metric(label=label, value=value)


def render_section(title: str) -> None:
    """Render a section heading."""
    st.subheader(title)


def render_info_box(text: str) -> None:
    """Render a compact informational note."""
    st.caption(text)


__all__ = ["render_metric", "render_metrics_row", "render_section", "render_info_box"]
