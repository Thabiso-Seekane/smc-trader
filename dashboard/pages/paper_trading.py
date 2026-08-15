"""Read-only paper-trading monitor for Week 11."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.services import AnalysisBundle, get_paper_broker


def render(bundle: AnalysisBundle) -> None:
    """Show paper-account state, current SMC signal context, and journal."""
    st.title("Paper Trading")
    st.success("MODE: PAPER - no live orders can be sent from this dashboard.")
    broker = get_paper_broker()
    account = broker.get_account()
    positions = broker.get_positions()
    closed = broker.get_closed_positions()
    trades = broker.get_trades()
    wins = sum(trade.realized_pnl > 0 for trade in trades)
    win_rate = wins / len(trades) * 100 if trades else 0.0

    cols = st.columns(7)
    cols[0].metric("Balance", f"${account.balance:,.2f}")
    cols[1].metric("Equity", f"${account.equity:,.2f}")
    cols[2].metric("Daily P/L", f"${account.daily_realized_pnl:,.2f}")
    cols[3].metric("Open Trades", len(positions))
    cols[4].metric("Drawdown", f"{account.drawdown_percent:.2f}%")
    cols[5].metric("Trades", len(trades))
    cols[6].metric("Win Rate", f"{win_rate:.1f}%")

    st.subheader("System Health")
    health = st.columns(5)
    health[0].metric("Mode", "PAPER")
    health[1].metric("Market Data", "RECEIVING" if bundle.has_data else "UNAVAILABLE")
    health[2].metric("Strategy", "RUNNING" if bundle.strategy is not None else "WAITING")
    health[3].metric("Paper Broker", "RUNNING")
    health[4].metric("Database", "CONNECTED")
    st.caption(f"Account last updated: {account.updated_at}")

    st.subheader("Current Signal")
    decision = getattr(bundle.strategy, "decision", None)
    plan = bundle.plan
    signal_cols = st.columns(4)
    signal_cols[0].metric("Bias", str(getattr(getattr(decision, "direction", None), "value", "WAITING")))
    signal_cols[1].metric("Confluence", f"{getattr(decision, 'confidence', 0):.0f}/100")
    signal_cols[2].metric("CHoCH/BOS", len(getattr(bundle.events, "events", []) or []))
    signal_cols[3].metric(
        "Active OB / FVG",
        f"{len(getattr(bundle.order_blocks, 'active', []) or [])} / {len(getattr(bundle.imbalances, 'active', []) or [])}",
    )
    if plan is not None:
        st.caption(
            f"Trade plan: {plan.direction} @ {plan.entry_price:.2f} | "
            f"SL {plan.stop_loss:.2f} | TP {plan.take_profit:.2f} | R:R {plan.risk_reward:.2f}"
        )
    else:
        st.caption("Paper status: waiting for a validated trade plan.")

    st.subheader("Open Positions")
    if positions:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": p.trade_id,
                        "Symbol": p.symbol,
                        "Direction": p.side.value,
                        "Entry": p.entry_price,
                        "SL": p.stop_loss,
                        "TP": p.take_profit,
                        "Unrealized P/L": broker.unrealized_pnl(p),
                        "Status": p.status.value,
                        "Reason": p.reason,
                    }
                    for p in positions
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No open paper positions.")

    st.subheader("Paper Trade Journal")
    if trades:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": trade.trade_id,
                        "Time": trade.closed_at,
                        "Symbol": trade.symbol,
                        "Direction": trade.side.value,
                        "P/L": trade.realized_pnl,
                        "Result": "WIN" if trade.realized_pnl > 0 else "LOSS",
                        "Exit": trade.close_reason.value,
                    }
                    for trade in trades
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No closed paper trades have been recorded.")


__all__ = ["render"]
