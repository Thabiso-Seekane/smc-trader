"""Visualization for the Week 9 Backtesting Engine.

A debugging and reporting tool that renders the backtest output as
interactive Plotly charts. These charts become the foundation of the Week 10
dashboard.

Charts:
    * Equity curve (equity vs time)
    * Drawdown curve (drawdown vs time)
    * R-multiple distribution
    * Monthly returns
    * Win/loss distribution
    * Confluence score vs average R
"""

from __future__ import annotations

from dataclasses import dataclass

import plotly.graph_objects as go

from backtesting.analyzer import BacktestAnalyzer
from backtesting.metrics import PerformanceMetrics
from backtesting.models import BacktestResult


@dataclass(slots=True)
class BacktestVisualizer:
    """Renders Plotly charts of backtest performance."""

    def equity_curve(self, result: BacktestResult) -> go.Figure:
        """Render the equity curve.

        Args:
            result: The backtest result.

        Returns:
            A Plotly ``go.Figure``.
        """
        fig = go.Figure()
        if result.equity_curve:
            fig.add_trace(
                go.Scatter(
                    x=[p.timestamp for p in result.equity_curve],
                    y=[p.equity for p in result.equity_curve],
                    mode="lines",
                    name="Equity",
                    line={"color": "#1f77b4", "width": 2},
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[p.timestamp for p in result.equity_curve],
                    y=[p.balance for p in result.equity_curve],
                    mode="lines",
                    name="Balance",
                    line={"color": "#7f7f7f", "width": 1, "dash": "dash"},
                )
            )
        fig.update_layout(
            title="Equity Curve",
            xaxis_title="Time",
            yaxis_title="Equity",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def drawdown_curve(self, result: BacktestResult) -> go.Figure:
        """Render the drawdown curve.

        Args:
            result: The backtest result.

        Returns:
            A Plotly ``go.Figure``.
        """
        fig = go.Figure()
        if result.equity_curve:
            fig.add_trace(
                go.Scatter(
                    x=[p.timestamp for p in result.equity_curve],
                    y=[p.drawdown * 100 for p in result.equity_curve],
                    mode="lines",
                    name="Drawdown (%)",
                    line={"color": "#d62728", "width": 2},
                    fill="tozeroy",
                )
            )
        fig.update_layout(
            title="Drawdown",
            xaxis_title="Time",
            yaxis_title="Drawdown (%)",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def r_distribution(self, result: BacktestResult) -> go.Figure:
        """Render the R-multiple histogram.

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
                    name="R-multiple",
                    marker={"color": "#2ca02c"},
                )
            )
        fig.update_layout(
            title="R-Multiple Distribution",
            xaxis_title="R",
            yaxis_title="Frequency",
            template="plotly_white",
            bargap=0.05,
        )
        return fig

    def monthly_returns(self, result: BacktestResult) -> go.Figure:
        """Render monthly returns as a bar chart.

        Args:
            result: The backtest result.

        Returns:
            A Plotly ``go.Figure``.
        """
        monthly = PerformanceMetrics.monthly_returns(result.trades)
        fig = go.Figure()
        if monthly:
            fig.add_trace(
                go.Bar(
                    x=list(monthly.keys()),
                    y=list(monthly.values()),
                    name="Monthly P/L",
                    marker_color=[
                        "#2ca02c" if v >= 0 else "#d62728"
                        for v in monthly.values()
                    ],
                )
            )
        fig.update_layout(
            title="Monthly Returns",
            xaxis_title="Month",
            yaxis_title="P/L",
            template="plotly_white",
        )
        return fig

    def win_loss_distribution(self, result: BacktestResult) -> go.Figure:
        """Render the win/loss distribution as a bar chart.

        Args:
            result: The backtest result.

        Returns:
            A Plotly ``go.Figure``.
        """
        wins = result.winning_trades
        losses = result.losing_trades
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=["Wins", "Losses"],
                y=[wins, losses],
                name="Outcome",
                marker_color=["#2ca02c", "#d62728"],
                text=[wins, losses],
                textposition="outside",
            )
        )
        fig.update_layout(
            title="Win / Loss Distribution",
            xaxis_title="Outcome",
            yaxis_title="Trades",
            template="plotly_white",
        )
        return fig

    def confluence_vs_performance(self, result: BacktestResult) -> go.Figure:
        """Render average R per confluence band.

        Args:
            result: The backtest result.

        Returns:
            A Plotly ``go.Figure``.
        """
        bands = BacktestAnalyzer().confluence_attribution(result.trades)
        fig = go.Figure()
        if bands:
            fig.add_trace(
                go.Bar(
                    x=[b.label for b in bands],
                    y=[b.average_r for b in bands],
                    name="Avg R",
                    marker_color="#1f77b4",
                    text=[f"{b.average_r:.2f}R" for b in bands],
                    textposition="outside",
                )
            )
        fig.update_layout(
            title="Confluence Score vs Average R",
            xaxis_title="Confluence Band",
            yaxis_title="Average R",
            template="plotly_white",
        )
        return fig

    def report_figure(self, result: BacktestResult) -> go.Figure:
        """Build a combined multi-panel dashboard figure.

        Args:
            result: The backtest result.

        Returns:
            A Plotly subplot figure with equity, drawdown, R-distribution,
            and monthly returns.
        """
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Equity Curve",
                "Drawdown",
                "R Distribution",
                "Monthly Returns",
            ),
        )
        if result.equity_curve:
            fig.add_trace(
                go.Scatter(
                    x=[p.timestamp for p in result.equity_curve],
                    y=[p.equity for p in result.equity_curve],
                    mode="lines",
                    name="Equity",
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=[p.timestamp for p in result.equity_curve],
                    y=[p.drawdown * 100 for p in result.equity_curve],
                    mode="lines",
                    name="Drawdown",
                ),
                row=1,
                col=2,
            )
        r_values = [t.r_multiple for t in result.trades]
        if r_values:
            fig.add_trace(
                go.Histogram(x=r_values, name="R"),
                row=2,
                col=1,
            )
        monthly = PerformanceMetrics.monthly_returns(result.trades)
        if monthly:
            fig.add_trace(
                go.Bar(
                    x=list(monthly.keys()),
                    y=list(monthly.values()),
                    name="Monthly",
                ),
                row=2,
                col=2,
            )
        fig.update_layout(
            title="Backtest Report",
            template="plotly_white",
            height=700,
            showlegend=False,
        )
        return fig


__all__ = ["BacktestVisualizer"]
