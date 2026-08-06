"""Strategy visualizer.

Renders a complete Week 7 trade setup as an interactive Plotly chart so an
engineer can visually verify *why* the engine likes a setup. The chart shows
the candles, the Order Block, the Fair Value Gap, the liquidity level, the
CHoCH/BOS events, and the entry/stop/target levels with the confluence score.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from strategy.models import StrategyResult, TradeZone


@dataclass(slots=True)
class StrategyVisualizer:
    """Render a strategy setup as a Plotly figure."""

    def build_figure(
        self,
        result: StrategyResult,
        candles: pd.DataFrame | None = None,
    ) -> go.Figure:
        """Build a figure for the best setup (or all tradeable zones).

        Args:
            result: The strategy result to render.
            candles: Optional OHLCV frame used as the background chart.

        Returns:
            A Plotly ``go.Figure``.
        """
        fig = go.Figure()

        if candles is not None and not candles.empty:
            fig.add_trace(
                go.Candlestick(
                    x=candles["date"],
                    open=candles["open"],
                    high=candles["high"],
                    low=candles["low"],
                    close=candles["close"],
                    name="Price",
                    showlegend=False,
                )
            )

        zones = result.tradeable or result.zones
        for zone in zones:
            self._add_entry(fig, zone)
            self._add_geometry(fig, zone)

        title = "Trade Setup"
        if result.decision is not None and result.decision.zone is not None:
            title = (
                f"Trade Setup — {result.decision.direction.value} "
                f"{result.decision.confidence:.0f} ({result.decision.status.value})"
            )

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def _add_entry(self, fig: go.Figure, zone: TradeZone) -> None:
        """Draw the entry level line."""
        color = "#2ca02c" if zone.is_buy else "#d62728"
        fig.add_hline(
            y=zone.entry_price,
            line_dash="dot",
            line_color=color,
            opacity=0.6,
            annotation_text=f"Entry {zone.entry_price:.5f}",
        )

    def _add_geometry(self, fig: go.Figure, zone: TradeZone) -> None:
        """Draw stop-loss and target lines with labels."""
        fig.add_hline(
            y=zone.stop_loss,
            line_color="#d62728",
            annotation_text=f"SL {zone.stop_loss:.5f}",
        )
        fig.add_hline(
            y=zone.target,
            line_color="#2ca02c",
            annotation_text=f"TP {zone.target:.5f}",
        )

    def render(
        self,
        result: StrategyResult,
        candles: pd.DataFrame | None = None,
    ) -> str:
        """Render the strategy setup as a standalone HTML string."""
        fig = self.build_figure(result, candles)
        return fig.to_html(include_plotlyjs="cdn")


__all__ = ["StrategyVisualizer"]
