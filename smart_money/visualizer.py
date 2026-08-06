"""Smart Money (CHoCH / BOS / Order Block / Trade Zone / Imbalance) visualizer.

A debugging tool that renders detected structural events, Order Block
zones, Trade Zones, and Imbalance (Fair Value Gap) zones as interactive
Plotly charts. This module is intentionally **not** used by the strategy;
it exists for developers to verify the detection algorithms.

The chart shows:

    * Optional OHLC candlesticks (background).
    * Optional market-structure labels (HH / HL / LL / LH).
    * Optional liquidity sweeps (buy-side and sell-side).
    * CHoCH events (green up-triangles for bullish, red down-triangles for
      bearish).
    * BOS events (green up-arrows for bullish, red down-arrows for bearish).
    * Order Block zones (color-coded by state).
    * Trade Zone confluence zones (color-coded by confluence level).
    * Imbalance / Fair Value Gap zones (color-coded by fill status).

Each event type uses a distinct marker and label so the engineer can
quickly distinguish a change of character from a break of structure.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from liquidity.models import LiquidityMap
from smart_money.imbalance import ImbalanceMap
from smart_money.models import SmartMoneyAnalysis
from smart_money.enums import ConfluenceLevel, FillStatus
from smart_money.order_block_models import OrderBlockMap
from smart_money.trade_zone_models import TradeZoneMap
from structure.models import MarketStructure


@dataclass(slots=True)
class SmartMoneyVisualizer:
    """Renders Plotly charts of CHoCH / BOS events, Order Blocks, Trade Zones, and Imbalances."""

    def build_figure(
        self,
        analysis: SmartMoneyAnalysis,
        candles: pd.DataFrame | None = None,
        structure: MarketStructure | None = None,
        liquidity: LiquidityMap | None = None,
    ) -> go.Figure:
        """Build an interactive Plotly figure for the given events.

        Args:
            analysis: The CHoCH / BOS analysis to render.
            candles: Optional OHLC frame used as the background candlestick
                chart. When omitted, only the event markers are plotted.
            structure: Optional market structure whose labelled swing points
                (HH/HL/LH/LL) are drawn.
            liquidity: Optional liquidity map whose swept levels are drawn.

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

        if structure is not None:
            self._add_structure_labels(fig, structure)

        if liquidity is not None:
            self._add_liquidity_sweeps(fig, liquidity)

        for event in analysis.events:
            self._add_event_marker(fig, event)

        fig.update_layout(
            title="CHoCH / BOS Structural Events",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def build_order_block_figure(
        self,
        blocks: OrderBlockMap,
        candles: pd.DataFrame | None = None,
        structure: MarketStructure | None = None,
        liquidity: LiquidityMap | None = None,
    ) -> go.Figure:
        """Build a Plotly figure rendering Order Block zones.

        Each zone is drawn as a colored rectangle astride the origin
        candle's timestamp. Colors:

            * Bullish active  — green
            * Bearish active  — red
            * Mitigated       — orange
            * Invalidated     — gray

        The rectangle label shows the strength score.

        Args:
            blocks: The :class:`OrderBlockMap` to render.
            candles: Optional OHLC frame for the background chart.
            structure: Optional market structure to overlay.
            liquidity: Optional liquidity map to overlay.

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

        if structure is not None:
            self._add_structure_labels(fig, structure)

        if liquidity is not None:
            self._add_liquidity_sweeps(fig, liquidity)

        for block in blocks.all:
            self._add_order_block_zone(fig, block, candles)

        fig.update_layout(
            title="Order Block Zones",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def build_trade_zone_figure(
        self,
        zones: TradeZoneMap,
        candles: pd.DataFrame | None = None,
        structure: MarketStructure | None = None,
        liquidity: LiquidityMap | None = None,
    ) -> go.Figure:
        """Build a Plotly figure rendering Trade Zone confluence zones.

        Each zone is drawn as a colored rectangle astride its origin
        candle's timestamp. The rectangle color reflects the confluence
        level (``ConfluenceLevel``):

            * STRONG   — green
            * MODERATE — blue
            * WEAK     — orange
            * Mitigated  — purple
            * Invalidated — gray

        The rectangle label shows the confluence score (0-100).

        Args:
            zones: The :class:`TradeZoneMap` to render.
            candles: Optional OHLC frame for the background chart.
            structure: Optional market structure to overlay.
            liquidity: Optional liquidity map to overlay.

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

        if structure is not None:
            self._add_structure_labels(fig, structure)

        if liquidity is not None:
            self._add_liquidity_sweeps(fig, liquidity)

        for zone in zones.all:
            self._add_trade_zone_rectangle(fig, zone, candles)

        fig.update_layout(
            title="Trade Zones — Confluence",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def build_imbalance_figure(
        self,
        imbalances: ImbalanceMap,
        candles: pd.DataFrame | None = None,
        structure: MarketStructure | None = None,
        liquidity: LiquidityMap | None = None,
    ) -> go.Figure:
        """Build a Plotly figure rendering imbalance (Fair Value Gap) zones.

        Each gap is drawn as a colored rectangle astride its origin candle.
        The rectangle color reflects the fill status and quality:

            * Open bullish   — green (unfilled)
            * Open bearish   — red (unfilled)
            * Partial fill   — blue
            * Filled         — gray

        The rectangle label shows the fill percentage and strength score.

        Args:
            imbalances: The :class:`ImbalanceMap` to render.
            candles: Optional OHLC frame for the background chart.
            structure: Optional market structure to overlay.
            liquidity: Optional liquidity map to overlay.

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

        if structure is not None:
            self._add_structure_labels(fig, structure)

        if liquidity is not None:
            self._add_liquidity_sweeps(fig, liquidity)

        for gap in imbalances.all:
            self._add_imbalance_rectangle(fig, gap, candles)

        fig.update_layout(
            title="Imbalance Zones — Fair Value Gaps",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            hovermode="x unified",
        )
        return fig

    def _add_imbalance_rectangle(
        self,
        fig: go.Figure,
        gap,
        candles: pd.DataFrame | None,
    ) -> None:
        """Add a single imbalance gap rectangle colored by fill status."""
        if gap.fill_status == FillStatus.FILLED:
            color = "#7f7f7f"
            label = f"FILLED FVG {gap.fill_percentage:.0f}%"
        elif gap.fill_status == FillStatus.PARTIAL:
            color = "#1f77b4"
            label = f"PARTIAL FVG {gap.fill_percentage:.0f}%"
        elif gap.is_bullish:
            color = "#2ca02c"
            label = f"Bull FVG {gap.strength:.0f}"
        else:
            color = "#d62728"
            label = f"Bear FVG {gap.strength:.0f}"

        # Determine the x-window for the rectangle.
        x0 = x1 = None
        if (
            candles is not None
            and not candles.empty
            and gap.index < len(candles)
        ):
            x0 = candles["date"].iloc[gap.index]
            x1 = x0
        fig.add_trace(
            go.Scatter(
                x=[x0, x1, x1, x0, x0] if x0 is not None else None,
                y=[gap.low, gap.low, gap.high, gap.high, gap.low],
                mode="lines",
                fill="toself",
                fillcolor=color,
                opacity=0.35,
                line={"color": color, "width": 1},
                name=label,
                showlegend=False,
                text=[label],
                hovertemplate=(
                    f"{label}<br>Fill: %{{y:.5f}}<extra></extra>"
                ),
            )
        )

    def _add_trade_zone_rectangle(
        self,
        fig: go.Figure,
        zone,
        candles: pd.DataFrame | None,
    ) -> None:
        """Add a single Trade Zone rectangle colored by confluence level."""
        if zone.invalidated:
            color = "#7f7f7f"
            label = f"Invalidated TZ {zone.confluence_score:.0f}"
        elif zone.mitigated:
            color = "#9467bd"
            label = f"Mitigated TZ {zone.confluence_score:.0f}"
        elif zone.confluence_level == ConfluenceLevel.STRONG:
            color = "#2ca02c"
            label = f"STRONG TZ {zone.confluence_score:.0f}"
        elif zone.confluence_level == ConfluenceLevel.MODERATE:
            color = "#1f77b4"
            label = f"MODERATE TZ {zone.confluence_score:.0f}"
        else:
            color = "#ff7f0e"
            label = f"WEAK TZ {zone.confluence_score:.0f}"

        # Determine the x-window for the rectangle.
        x0 = x1 = None
        origin = getattr(zone, "origin_time", None)
        if candles is not None and not candles.empty and origin is not None:
            x0 = origin
            x1 = x0
        if x0 is None and (
            candles is not None
            and not candles.empty
            and zone.order_block is not None
            and getattr(zone.order_block, "origin_index", None) is not None
            and zone.order_block.origin_index < len(candles)
        ):
            x0 = candles["date"].iloc[zone.order_block.origin_index]
            x1 = x0

        fig.add_trace(
            go.Scatter(
                x=[x0, x1, x1, x0, x0] if x0 is not None else None,
                y=[zone.low, zone.low, zone.high, zone.high, zone.low],
                mode="lines",
                fill="toself",
                fillcolor=color,
                opacity=0.35,
                line={"color": color, "width": 1},
                name=label,
                showlegend=False,
                text=[label],
                hovertemplate=(
                    f"{label}<br>High: %{{y:.5f}}<extra></extra>"
                ),
            )
        )

    def _add_structure_labels(
        self, fig: go.Figure, structure: MarketStructure
    ) -> None:
        """Plot HH/HL/LH/LL labels above/below each classified swing point."""
        for point in structure.points:
            is_high = point.swing_type.value.lower() == "high"
            label_value = _label_value(point.label)
            color = "#2ca02c" if label_value in ("HH", "HL") else "#d62728"
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp],
                    y=[point.price],
                    mode="markers+text",
                    text=[label_value],
                    textposition="top center" if is_high else "bottom center",
                    marker={"symbol": "circle", "size": 8, "color": color},
                    name=f"Structure {label_value}",
                    showlegend=False,
                    hovertemplate=(
                        f"{label_value}<br>Price: %{{y:.5f}}<extra></extra>"
                    ),
                )
            )

    def _add_liquidity_sweeps(
        self, fig: go.Figure, liquidity: LiquidityMap
    ) -> None:
        """Plot swept buy-side and sell-side liquidity with distinct markers."""
        for level in liquidity.swept_levels:
            if level.timestamp is None:
                continue
            if level.is_buy_side:
                marker = "diamond"
                color = "#9467bd"
                label = "BS Sweep"
            else:
                marker = "hexagon"
                color = "#ff7f0e"
                label = "SS Sweep"
            fig.add_trace(
                go.Scatter(
                    x=[level.timestamp],
                    y=[level.price],
                    mode="markers+text",
                    text=[label],
                    textposition="top right",
                    marker={"symbol": marker, "size": 12, "color": color},
                    name=label,
                    showlegend=False,
                    hovertemplate=(
                        f"{label}<br>Price: %{{y:.5f}}<extra></extra>"
                    ),
                )
            )

    def _add_event_marker(self, fig: go.Figure, event) -> None:
        """Add a single CHoCH / BOS marker to the figure."""
        is_bullish = event.is_bullish
        is_choch = event.is_choch

        if is_choch:
            color = "#2ca02c" if is_bullish else "#d62728"
            symbol = "triangle-up" if is_bullish else "triangle-down"
            label = "Bull CHoCH" if is_bullish else "Bear CHoCH"
        else:
            color = "#17becf" if is_bullish else "#d62728"
            symbol = "arrow-up" if is_bullish else "arrow-down"
            label = "Bull BOS" if is_bullish else "Bear BOS"

        fig.add_trace(
            go.Scatter(
                x=[event.timestamp],
                y=[event.broken_price],
                mode="markers+text",
                text=[label],
                textposition="top center" if is_bullish else "bottom center",
                marker={"symbol": symbol, "size": 14, "color": color},
                name=f"{label} ({event.displacement_strength:.0f})",
                customdata=[event.displacement_strength],
                hovertemplate=(
                    f"%{{text}}<br>Broken: %{{y:.5f}}"
                    f"<br>Displacement: %{{customdata[0]:.1f}}<extra></extra>"
                ),
            )
        )

    def _add_order_block_zone(
        self,
        fig: go.Figure,
        block,
        candles: pd.DataFrame | None,
    ) -> None:
        """Add a single Order Block rectangle to the figure."""
        if block.invalidated:
            color = "#7f7f7f"
            label = f"Invalidated OB {block.strength:.0f}"
        elif block.mitigated:
            color = "#ff7f0e"
            label = f"Mitigated OB {block.strength:.0f}"
        elif block.is_bullish:
            color = "#2ca02c"
            label = f"Bull OB {block.strength:.0f}"
        else:
            color = "#d62728"
            label = f"Bear OB {block.strength:.0f}"

        # Determine the x-window for the rectangle.
        x0 = x1 = None
        if (
            candles is not None
            and not candles.empty
            and block.origin_index < len(candles)
        ):
            x0 = candles["date"].iloc[block.origin_index]
            x1 = x0
        fig.add_trace(
            go.Scatter(
                x=[x0, x1, x1, x0, x0] if x0 is not None else None,
                y=[block.low, block.low, block.high, block.high, block.low],
                mode="lines",
                fill="toself",
                fillcolor=color,
                opacity=0.35,
                line={"color": color, "width": 1},
                name=label,
                showlegend=False,
                text=[label],
                hovertemplate=(
                    f"{label}<br>High: %{{y:.5f}}<extra></extra>"
                ),
            )
        )

    def render(
        self,
        analysis: SmartMoneyAnalysis,
        candles: pd.DataFrame | None = None,
        structure: MarketStructure | None = None,
        liquidity: LiquidityMap | None = None,
    ) -> go.Figure:
        """Render the structural events as a Plotly figure.

        Convenience wrapper around :meth:`build_figure`.

        Args:
            analysis: The CHoCH / BOS analysis to render.
            candles: Optional OHLC frame for the background chart.
            structure: Optional market structure to overlay.
            liquidity: Optional liquidity map to overlay.

        Returns:
            A Plotly ``go.Figure``.
        """
        return self.build_figure(analysis, candles, structure, liquidity)

    def to_html(
        self,
        analysis: SmartMoneyAnalysis,
        candles: pd.DataFrame | None = None,
        structure: MarketStructure | None = None,
        liquidity: LiquidityMap | None = None,
    ) -> str:
        """Return a standalone HTML string of the rendered figure.

        Args:
            analysis: The CHoCH / BOS analysis to render.
            candles: Optional OHLC frame for the background chart.
            structure: Optional market structure to overlay.
            liquidity: Optional liquidity map to overlay.

        Returns:
            A full HTML document as a string.
        """
        fig = self.build_figure(analysis, candles, structure, liquidity)
        return fig.to_html(include_plotlyjs="cdn")


def _label_value(label) -> str:
    """Normalize a structure label (enum member or raw string) to its value."""
    return label.value if hasattr(label, "value") else str(label)


__all__ = ["SmartMoneyVisualizer"]
