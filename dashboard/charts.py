"""Chart-building services for the Week 10 Streamlit dashboard.

This module translates the analysis / strategy / backtest result objects
into Plotly figures. The Streamlit pages only receive these figure objects
and display them — they never build chart traces themselves.

Charts covered:
    * Candlestick chart with structure / liquidity / OB / FVG overlays.
    * Equity curve.
    * Monthly returns.
    * R-multiple distribution.
    * Confluence vs performance attribution.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backtesting.models import BacktestResult
from dashboard.services import AnalysisBundle


def _price_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """Create a consistently styled candlestick figure."""
    fig = go.Figure()
    if df is not None and not df.empty:
        fig.add_trace(go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"],
            low=df["low"], close=df["close"], name="Price",
            increasing_line_color="#2ca02c", decreasing_line_color="#d62728",
        ))
    fig.update_layout(title=title, xaxis_title="Time", yaxis_title="Price",
                      template="plotly_white", xaxis_rangeslider_visible=False,
                      height=600, legend=dict(orientation="h", y=1.02))
    return fig


def candlestick_chart(bundle: AnalysisBundle) -> go.Figure:
    """Render a candlestick chart annotated with the SMC zones.

    Args:
        bundle: The analysis bundle to render.

    Returns:
        A Plotly ``go.Figure`` with candles + overlay zones.
    """
    df = bundle.df
    fig = _price_chart(df, f"{bundle.symbol} {bundle.timeframe} — SMC Analysis")

    # Liquidity levels.
    if bundle.liquidity is not None:
        for level in getattr(bundle.liquidity, "levels", []) or []:
            price = getattr(level, "price", None)
            if price is None:
                continue
            swept = getattr(level, "swept", False)
            color = "#7f7f7f" if swept else "#ff7f0e"
            dash = "dot" if swept else "dash"
            fig.add_hline(
                y=price,
                line=dict(color=color, width=1, dash=dash),
                annotation_text=f"{getattr(level, 'label', '') or getattr(level, 'liquidity_type', '')} {'SWEPT' if swept else ''}",
                annotation_position="top right",
            )

    # Order blocks.
    if bundle.order_blocks is not None:
        for block in getattr(bundle.order_blocks, "all", []) or []:
            high = getattr(block, "high", None)
            low = getattr(block, "low", None)
            if high is None or low is None:
                continue
            color = "#2ca02c" if getattr(block, "is_bullish", False) else "#d62728"
            fig.add_hrect(
                y0=low, y1=high, fillcolor=color, opacity=0.15, line_width=0,
                name="OB",
            )

    # Fair value gaps.
    if bundle.imbalances is not None:
        for gap in getattr(bundle.imbalances, "all", []) or []:
            high = getattr(gap, "high", None)
            low = getattr(gap, "low", None)
            if high is None or low is None:
                continue
            color = "#2ca02c" if getattr(gap, "is_bullish", False) else "#d62728"
            fig.add_hrect(
                y0=low, y1=high, fillcolor=color, opacity=0.10, line_width=0,
                name="FVG",
            )

    # Current price line.
    if bundle.current_price > 0:
        fig.add_hline(
            y=bundle.current_price,
            line=dict(color="#1f77b4", width=1),
            annotation_text=f"@{bundle.current_price:.2f}",
            annotation_position="bottom left",
        )

    return fig


def market_structure_chart(bundle: AnalysisBundle) -> go.Figure:
    """Plot candles with HH/HL/LH/LL structure markers."""
    fig = _price_chart(bundle.df, "Market Structure")
    points = getattr(bundle.structure, "points", []) or []
    if points:
        fig.add_trace(go.Scatter(
            x=[p.timestamp for p in points], y=[p.price for p in points],
            mode="markers+text", text=[str(getattr(p.label, "value", p.label)) for p in points],
            textposition="top center", marker={"size": 9, "color": "#1f77b4"}, name="Structure",
        ))
    return fig


def liquidity_chart(bundle: AnalysisBundle) -> go.Figure:
    """Plot active and swept liquidity levels over price."""
    fig = _price_chart(bundle.df, "Liquidity Map")
    for level in getattr(bundle.liquidity, "levels", []) or []:
        color = "#7f7f7f" if getattr(level, "swept", False) else (
            "#d62728" if getattr(level, "is_buy_side", False) else "#2ca02c"
        )
        fig.add_hline(y=level.price, line={"color": color, "dash": "dot" if level.swept else "dash"},
                      annotation_text=f"{getattr(level, 'label', '') or getattr(level, 'liquidity_type', '')}")
    return fig


def smart_money_chart(bundle: AnalysisBundle) -> go.Figure:
    """Plot CHoCH/BOS confirmations plus order blocks and FVG zones."""
    fig = _price_chart(bundle.df, "CHoCH / BOS / Order Blocks / FVG")
    for event in getattr(bundle.events, "events", []) or []:
        index = getattr(event, "confirmation_index", -1)
        when = bundle.df["date"].iloc[index] if 0 <= index < len(bundle.df) else event.timestamp
        label = str(getattr(event.event_type, "value", event.event_type))
        color = "#2ca02c" if getattr(event, "is_bullish", False) else "#d62728"
        fig.add_trace(go.Scatter(x=[when], y=[event.broken_price], mode="markers+text", text=[label],
                                 textposition="top center", marker={"size": 11, "symbol": "diamond", "color": color},
                                 name=label))
    for block in getattr(bundle.order_blocks, "all", []) or []:
        fig.add_hrect(y0=block.low, y1=block.high, fillcolor="#2ca02c" if getattr(block, "is_bullish", False) else "#d62728",
                      opacity=0.18, line_width=0, annotation_text="OB")
    for gap in getattr(bundle.imbalances, "all", []) or []:
        fig.add_hrect(y0=gap.low, y1=gap.high, fillcolor="#9467bd", opacity=0.16, line_width=0, annotation_text="FVG")
    return fig


def drawdown_chart(result: BacktestResult) -> go.Figure:
    """Render the equity-curve drawdown as a visible standalone chart."""
    fig = go.Figure()
    if result and result.equity_curve:
        fig.add_trace(go.Scatter(x=[p.timestamp for p in result.equity_curve],
                                 y=[p.drawdown * 100 for p in result.equity_curve],
                                 mode="lines", fill="tozeroy", name="Drawdown (%)",
                                 line={"color": "#d62728", "width": 2}))
    fig.update_layout(title="Drawdown Curve", xaxis_title="Time", yaxis_title="Drawdown (%)",
                      template="plotly_white", hovermode="x unified", height=400)
    return fig


def trade_replay_chart(bundle: AnalysisBundle, trade, end_index: int) -> go.Figure:
    """Show price available up to a replay bar, with the selected trade geometry."""
    frame = bundle.df.iloc[: max(1, min(end_index + 1, len(bundle.df)))]
    fig = _price_chart(frame, "Trade Replay")
    if trade is not None:
        fig.add_hline(y=trade.entry_price, line={"color": "#1f77b4"}, annotation_text="Entry")
        fig.add_hline(y=trade.exit_price, line={"color": "#ff7f0e"}, annotation_text="Exit")
        fig.add_trace(go.Scatter(x=[trade.entry_time, trade.exit_time], y=[trade.entry_price, trade.exit_price],
                                 mode="markers+lines", name="Selected trade", marker={"size": 10, "color": "#1f77b4"}))
    return fig


def equity_curve_chart(result: BacktestResult) -> go.Figure:
    """Render the equity curve of a backtest result.

    Args:
        result: The backtest result.

    Returns:
        A Plotly ``go.Figure``.
    """
    fig = go.Figure()
    if result and result.equity_curve:
        fig.add_trace(
            go.Scatter(
                x=[p.timestamp for p in result.equity_curve],
                y=[p.equity for p in result.equity_curve],
                mode="lines",
                name="Equity",
                line=dict(color="#1f77b4", width=2),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[p.timestamp for p in result.equity_curve],
                y=[p.balance for p in result.equity_curve],
                mode="lines",
                name="Balance",
                line=dict(color="#7f7f7f", width=1, dash="dash"),
            )
        )
    fig.update_layout(
        title="Equity Curve",
        xaxis_title="Time",
        yaxis_title="Equity ($)",
        template="plotly_white",
        hovermode="x unified",
        height=450,
    )
    return fig


def monthly_returns_chart(result: BacktestResult) -> go.Figure:
    """Render monthly P&L as a bar chart.

    Args:
        result: The backtest result.

    Returns:
        A Plotly ``go.Figure``.
    """
    from backtesting.metrics import PerformanceMetrics

    monthly = PerformanceMetrics.monthly_returns(result.trades)
    fig = go.Figure()
    if monthly:
        fig.add_trace(
            go.Bar(
                x=list(monthly.keys()),
                y=list(monthly.values()),
                marker_color=[
                    "#2ca02c" if v >= 0 else "#d62728" for v in monthly.values()
                ],
                text=[f"{v:,.0f}" for v in monthly.values()],
                textposition="outside",
            )
        )
    fig.update_layout(
        title="Monthly Returns",
        xaxis_title="Month",
        yaxis_title="P/L ($)",
        template="plotly_white",
        height=400,
    )
    return fig


def r_distribution_chart(result: BacktestResult) -> go.Figure:
    """Render the R-multiple distribution histogram.

    Args:
        result: The backtest result.

    Returns:
        A Plotly ``go.Figure``.
    """
    r_values = [t.r_multiple for t in result.trades]
    fig = go.Figure()
    if r_values:
        fig.add_trace(
            go.Histogram(
                x=r_values,
                nbinsx=20,
                marker_color="#2ca02c",
                name="R-multiple",
            )
        )
    fig.update_layout(
        title="R-Multiple Distribution",
        xaxis_title="R",
        yaxis_title="Frequency",
        template="plotly_white",
        bargap=0.05,
        height=400,
    )
    return fig


def confluence_vs_performance_chart(result: BacktestResult) -> go.Figure:
    """Render average R per confluence band.

    Args:
        result: The backtest result.

    Returns:
        A Plotly ``go.Figure``.
    """
    from backtesting.analyzer import BacktestAnalyzer

    bands = BacktestAnalyzer().confluence_attribution(result.trades)
    fig = go.Figure()
    if bands:
        fig.add_trace(
            go.Bar(
                x=[b.label for b in bands],
                y=[b.average_r for b in bands],
                marker_color="#1f77b4",
                text=[f"{b.average_r:.2f}R" for b in bands],
                textposition="outside",
            )
        )
        # Trades per band as a secondary line.
        fig.add_trace(
            go.Scatter(
                x=[b.label for b in bands],
                y=[b.trades for b in bands],
                mode="lines+markers",
                name="Trades",
                yaxis="y2",
                line=dict(color="#ff7f0e"),
            )
        )
    fig.update_layout(
        title="Confluence Score vs Average R",
        xaxis_title="Confluence Band",
        yaxis_title="Average R",
        yaxis2=dict(title="Trades", overlaying="y", side="right", showgrid=False),
        template="plotly_white",
        height=400,
    )
    return fig


def report_figure(result: BacktestResult) -> go.Figure:
    """Build a combined multi-panel dashboard figure.

    Args:
        result: The backtest result.

    Returns:
        A Plotly subplot figure with equity, drawdown, R-distribution, and
        monthly returns.
    """
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=("Equity Curve", "Drawdown", "R Distribution", "Monthly Returns"),
    )
    if result and result.equity_curve:
        fig.add_trace(
            go.Scatter(
                x=[p.timestamp for p in result.equity_curve],
                y=[p.equity for p in result.equity_curve],
                mode="lines",
                name="Equity",
                line=dict(color="#1f77b4"),
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=[p.timestamp for p in result.equity_curve],
                y=[p.drawdown * 100 for p in result.equity_curve],
                mode="lines",
                name="Drawdown",
                line=dict(color="#d62728"),
                fill="tozeroy",
            ),
            row=1, col=2,
        )
    if result:
        r_values = [t.r_multiple for t in result.trades]
        if r_values:
            fig.add_trace(
                go.Histogram(x=r_values, name="R"),
                row=2, col=1,
            )
        from backtesting.metrics import PerformanceMetrics

        monthly = PerformanceMetrics.monthly_returns(result.trades)
        if monthly:
            fig.add_trace(
                go.Bar(
                    x=list(monthly.keys()),
                    y=list(monthly.values()),
                    name="Monthly",
                ),
                row=2, col=2,
            )
    fig.update_layout(
        title="Backtest Report",
        template="plotly_white",
        height=700,
        showlegend=False,
    )
    return fig


__all__ = [
    "candlestick_chart",
    "market_structure_chart",
    "liquidity_chart",
    "smart_money_chart",
    "drawdown_chart",
    "trade_replay_chart",
    "equity_curve_chart",
    "monthly_returns_chart",
    "r_distribution_chart",
    "confluence_vs_performance_chart",
    "report_figure",
]
