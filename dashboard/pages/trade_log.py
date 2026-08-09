"""Trade Log page — Week 10.

Renders the Week 9 trade log with full attribution: every closed trade with
its entry/exit, R-multiple, confluence score, and reason. This is where the
user evaluates *why* each trade happened, not just whether it made money.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.state import get_backtest, get_selected_trade, get_trades, set_selected_trade


def render() -> None:
    """Render the trade log page."""
    st.title("Trade Log")
    st.caption("Every closed trade with attribution — why it happened, not just P/L.")

    trades = get_trades()
    if not trades:
        st.info("No trades yet. Run a backtest first.")
        return

    result = get_backtest()
    if result is not None:
        cols = st.columns(4)
        cols[0].metric("Total Trades", result.total_trades)
        cols[1].metric("Wins", result.winning_trades)
        cols[2].metric("Losses", result.losing_trades)
        cols[3].metric("Avg R", f"{result.average_rr:.2f}")

    # --- full trade table -------------------------------------
    st.subheader("Trades")
    df = pd.DataFrame(
        [
            {
                "Symbol": t.symbol,
                "Dir": str(getattr(t.direction, "value", t.direction)),
                "Entry": t.entry_price,
                "Exit": t.exit_price,
                "Volume": t.volume,
                "Entry Time": t.entry_time,
                "Exit Time": t.exit_time,
                "Risk": t.risk_amount,
                "P/L": t.profit_loss,
                "Commission": t.commission,
                "Slippage": t.slippage_cost,
                "R": t.r_multiple,
                "Result": str(getattr(t.result, "value", t.result)),
                "Confluence": t.confluence_score,
                "Reason": t.reason,
            }
            for t in trades
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    selected = get_selected_trade()
    selected = selected if selected is not None and selected < len(trades) else 0
    selected = st.selectbox(
        "Inspect trade", range(len(trades)), index=selected,
        format_func=lambda i: f"#{i + 1} — {trades[i].symbol} {trades[i].r_multiple:.2f}R",
        key="trade_log_selection",
    )
    set_selected_trade(selected)
    trade = trades[selected]
    st.subheader("Selected Trade Explanation")
    st.write(trade.reason or "No engine explanation was recorded for this trade.")
    st.caption(
        f"Entry: {trade.entry_time} @ {trade.entry_price} · "
        f"Exit: {trade.exit_time} @ {trade.exit_price} · {trade.exit_reason}"
    )

    # --- win/loss stats ---------------------------------------
    wins = [t for t in trades if t.profit_loss > 0]
    losses = [t for t in trades if t.profit_loss <= 0]
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Wins")
        if wins:
            st.write(f"Count: {len(wins)}")
            st.write(f"Gross Profit: ${sum(t.profit_loss for t in wins):,.2f}")
            st.write(f"Avg Win: ${sum(t.profit_loss for t in wins) / len(wins):,.2f}")
    with col_b:
        st.subheader("Losses")
        if losses:
            st.write(f"Count: {len(losses)}")
            st.write(f"Gross Loss: ${sum(t.profit_loss for t in losses):,.2f}")
            st.write(f"Avg Loss: ${sum(t.profit_loss for t in losses) / len(losses):,.2f}")


__all__ = ["render"]
