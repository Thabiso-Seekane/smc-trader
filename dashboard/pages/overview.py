"""Dashboard overview page — Week 10.

Renders the headline market snapshot: the candlestick chart with SMC
overlays, key market-state metrics (trend, liquidity, strongest OB/FVG,
latest structure event), and the current trade plan if one exists.
"""

from __future__ import annotations

import streamlit as st

from dashboard.charts import candlestick_chart
from dashboard.services import AnalysisBundle
from dashboard.state import get_backtest, get_trades


def render(bundle: AnalysisBundle) -> None:
    """Render the overview page for a loaded analysis bundle."""
    st.title("SMC Trader — Overview")
    st.caption(
        f"{bundle.symbol} · {bundle.timeframe} · "
        f"Period: {bundle.df['date'].iloc[0] if bundle.has_data else '—'} → "
        f"{bundle.df['date'].iloc[-1] if bundle.has_data else '—'}"
    )

    if not bundle.has_data:
        st.info("No data loaded. Select a symbol/timeframe and refresh.")
        return

    # --- headline metrics -------------------------------------
    metric_cols = st.columns(4)

    trend = getattr(bundle.structure, "trend", None) if bundle.structure else None
    trend_label = str(getattr(trend, "value", trend)) if trend is not None else "—"
    metric_cols[0].metric("Trend", trend_label)

    liquidity = bundle.liquidity
    n_levels = len(getattr(liquidity, "levels", []) or []) if liquidity else 0
    metric_cols[1].metric("Liquidity Levels", n_levels)

    ob = bundle.order_blocks
    n_obs = (len(getattr(ob, "active", []) or []) if ob else 0)
    metric_cols[2].metric("Active Order Blocks", n_obs)

    fvg = bundle.imbalances
    n_fvgs = len(getattr(fvg, "active", []) or []) if fvg else 0
    metric_cols[3].metric("Active FVGs", n_fvgs)

    # --- candlestick chart ------------------------------------
    st.plotly_chart(candlestick_chart(bundle), use_container_width=True)

    # --- trade plan (if any) ----------------------------------
    _render_plan(bundle)

    # --- strategy decision ------------------------------------
    _render_decision(bundle)

    # --- last backtest summary (if present) -------------------
    _render_backtest_snapshot()


def _render_plan(bundle: AnalysisBundle) -> None:
    """Render the current trade plan block."""
    plan = bundle.plan
    if plan is None:
        st.info("No trade plan available — no tradeable setup met the threshold.")
        return
    st.subheader("Trade Plan")
    cols = st.columns(5)
    cols[0].metric("Direction", plan.direction)
    cols[1].metric("Entry", f"{plan.entry_price:.2f}")
    cols[2].metric("Stop", f"{plan.stop_loss:.2f}")
    cols[3].metric("Target", f"{plan.take_profit:.2f}")
    cols[4].metric("R:R", f"{plan.risk_reward:.2f}")
    if hasattr(plan, "position_size") and plan.position_size is not None:
        st.caption(
            f"Volume: {plan.position_size.lots} · "
            f"Risk: ${plan.risk_metrics.risk_amount if hasattr(plan, 'risk_metrics') and plan.risk_metrics else 0:,.2f}"
        )
    reason = getattr(getattr(bundle.strategy, "decision", None), "reason", "")
    if reason:
        st.write(f"**Reason:** {reason}")


def _render_decision(bundle: AnalysisBundle) -> None:
    """Render the latest strategy decision."""
    strategy = bundle.strategy
    if strategy is None or strategy.decision is None:
        return
    decision = strategy.decision
    st.subheader("Strategy Decision")
    st.write(
        f"**Status:** {decision.status.value} · "
        f"**Confidence:** {decision.confidence:.1f} · "
        f"**Direction:** {decision.direction.value}"
    )
    if decision.reason:
        st.caption(decision.reason)


def _render_backtest_snapshot() -> None:
    """Render a compact snapshot of the last backtest, if present."""
    result = get_backtest()
    if result is None:
        return
    st.divider()
    st.subheader("Latest Backtest")
    cols = st.columns(4)
    cols[0].metric("Return", f"{result.total_return * 100:.2f}%")
    cols[1].metric("Win Rate", f"{result.win_rate * 100:.2f}%")
    cols[2].metric("Profit Factor", f"{result.profit_factor:.2f}")
    cols[3].metric("Max DD", f"{result.max_drawdown * 100:.2f}%")

    trades = get_trades()
    if trades:
        st.caption(f"{len(trades)} closed trades in the last backtest.")


__all__ = ["render"]
