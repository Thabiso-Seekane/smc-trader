"""Shared UI helpers for the Week 10 Streamlit dashboard pages."""

from __future__ import annotations

import streamlit as st


def render_metric(label: str, value, delta: str | None = None) -> None:
    """Render a single metric card using Streamlit's metric widget."""
    st.metric(label=label, value=value, delta=delta)


def render_metrics_row(metrics: dict) -> None:
    """Render a row of metric columns from a {label: value} dict."""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        with col:
            st.metric(label=label, value=value)


def render_section(title: str) -> None:
    """Render a section header."""
    st.subheader(title)


def render_info_box(text: str) -> None:
    """Render a muted info note."""
    st.caption(text)


__all__ = [
    "render_metric",
    "render_metrics_row",
    "render_section",
    "render_info_box",
]
