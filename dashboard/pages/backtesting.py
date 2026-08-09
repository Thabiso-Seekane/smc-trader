"""Backtest page — Week 10.

Renders the Week 9 backtest results: headline metrics, equity curve,
drawdown, monthly returns, R-distribution, and confluence attribution.
The user can run a backtest over the loaded data and export the report.
"""

from __future__ import annotations

import streamlit as st

from backtesting.models import BacktestResult
from backtesting.report import BacktestReport
from dashboard.charts import (
    drawdown_chart,
    equity_curve_chart,
    monthly_returns_chart,
    r_distribution_chart,
    confluence_vs_performance_chart,
)
from dashboard.charts import trade_replay_chart
from dashboard.services import AnalysisBundle, run_backtest
from dashboard.state import get_backtest, get_selected_trade, get_trades, set_backtest, set_selected_trade, set_trades


def render(bundle: AnalysisBundle, config) -> None:
    """Render the backtest page for the loaded bundle."""
    st.title("Backtest")
    st.caption(f"{bundle.symbol} · {bundle.timeframe}")

    if not bundle.has_data:
        st.info("No data loaded to backtest.")
        return

    # --- controls ---------------------------------------------
    col_run, col_export = st.columns([1, 2])
    with col_run:
        run_pressed = st.button("▶ Run Backtest", type="primary", use_container_width=True)
    with col_export:
        csv_bytes = _export_csv_bytes(get_trades())
        st.download_button(
            "⬇ Export Trade Log (CSV)",
            data=csv_bytes,
            file_name=f"backtest_{bundle.symbol}_{bundle.timeframe}.csv",
            mime="text/csv",
            disabled=not get_trades(),
            use_container_width=True,
        )

    if run_pressed:
        with st.spinner("Running deterministic backtest..."):
            try:
                result = run_backtest(
                    bundle.df,
                    bundle.symbol,
                    bundle.timeframe,
                    config,
                )
                set_backtest(result)
                set_trades(result.trades)
                st.success(f"Backtest completed — {result.total_trades} trades.")
            except Exception as exc:  # noqa: BLE001 - surface any engine error
                st.error(f"Backtest failed: {exc}")
                return

    result = get_backtest()
    if result is None:
        st.info("Run a backtest to see results.")
        return

    _render_results(result, bundle)


def _render_results(result: BacktestResult, bundle: AnalysisBundle) -> None:
    """Render the backtest results."""
    st.subheader("Headline Metrics")
    cols = st.columns(4)
    cols[0].metric("Final Balance", f"${result.final_balance:,.2f}")
    cols[1].metric("Return", f"{result.total_return * 100:.2f}%")
    cols[2].metric("Win Rate", f"{result.win_rate * 100:.2f}%")
    cols[3].metric("Profit Factor", f"{result.profit_factor:.2f}")

    cols2 = st.columns(4)
    cols2[0].metric("Trades", result.total_trades)
    cols2[1].metric("Max Drawdown", f"{result.max_drawdown * 100:.2f}%")
    cols2[2].metric("Expectancy", f"{result.expectancy:.2f}")
    cols2[3].metric("Sharpe", f"{result.sharpe_ratio:.2f}")

    st.subheader("Equity Curve")
    st.plotly_chart(equity_curve_chart(result), use_container_width=True)

    st.subheader("Drawdown Curve")
    st.plotly_chart(drawdown_chart(result), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(monthly_returns_chart(result), use_container_width=True)
    with col_b:
        st.plotly_chart(r_distribution_chart(result), use_container_width=True)

    st.subheader("Confluence vs Performance")
    st.plotly_chart(confluence_vs_performance_chart(result), use_container_width=True)

    # --- trades table -----------------------------------------
    st.subheader("Trades")
    trades = get_trades()
    if trades:
        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "Symbol": t.symbol,
                    "Dir": str(getattr(t.direction, "value", t.direction)),
                    "Entry": t.entry_price,
                    "Exit": t.exit_price,
                    "P/L": t.profit_loss,
                    "R": t.r_multiple,
                    "Result": str(getattr(t.result, "value", t.result)),
                    "Confluence": t.confluence_score,
                    "Exit Reason": str(getattr(t.exit_reason, "value", t.exit_reason)),
                }
                for t in trades
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
        _render_trade_inspection(bundle, trades)


def _render_trade_inspection(bundle: AnalysisBundle, trades) -> None:
    """Inspect a selected trade and replay the known candles up to an exit bar."""
    st.subheader("Individual Trade Inspection & Replay")
    selected = get_selected_trade()
    selected = selected if selected is not None and selected < len(trades) else 0
    index = st.selectbox(
        "Trade to inspect", range(len(trades)), index=selected,
        format_func=lambda i: f"#{i + 1} — {trades[i].symbol} {trades[i].r_multiple:.2f}R",
        key="backtest_trade_selection",
    )
    set_selected_trade(index)
    trade = trades[index]
    cols = st.columns(4)
    cols[0].metric("P/L", f"${trade.profit_loss:,.2f}")
    cols[1].metric("R-multiple", f"{trade.r_multiple:.2f}R")
    cols[2].metric("Confluence", f"{trade.confluence_score:.0f}")
    cols[3].metric("Exit", str(getattr(trade.exit_reason, "value", trade.exit_reason)))
    st.write(f"**Trade explanation:** {trade.reason or 'No engine explanation was recorded.'}")

    if bundle.has_data:
        exit_matches = bundle.df.index[bundle.df["date"] <= trade.exit_time]
        last_bar = int(exit_matches[-1]) if len(exit_matches) else len(bundle.df) - 1
        replay_bar = st.slider("Replay candle", min_value=0, max_value=max(0, last_bar), value=last_bar,
                               key=f"replay_bar_{index}")
        st.plotly_chart(trade_replay_chart(bundle, trade, replay_bar), use_container_width=True)


def _export_csv_bytes(trades) -> bytes:
    """Render the trade log as a CSV byte string for download."""
    if not trades:
        return b""
    from backtesting.models import BacktestResult, BacktestConfig

    # Build a minimal result to reuse the report writer.
    result = BacktestResult(trades=trades, config=BacktestConfig())
    report = BacktestReport(result=result)
    import tempfile
    from pathlib import Path

    # to_csv writes to a file path — write to a temp file then read it back.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "trades.csv"
        report.to_csv(path)
        return path.read_bytes()


__all__ = ["render"]
