# Week 10 — Streamlit Dashboard

A **read-only** interactive dashboard that wires the full SMC analysis
pipeline together and renders the results with Plotly.

```
data → structure → liquidity → CHoCH/BOS → order blocks → FVG
→ strategy → risk → backtest
```

## Run

```bash
python -m pip install -e ".[dev]"   # ensure deps incl. streamlit
streamlit run dashboard/app.py
```

Open the printed local URL (default `http://localhost:8501`).

## Pages

| Page                     | Renders                                                        |
|--------------------------|----------------------------------------------------------------|
| Overview                 | Candlestick + SMC overlays, headline metrics, trade plan.      |
| Market Structure         | Swings, structure points, trend.                               |
| Liquidity                | Buy/sell-side levels, equal highs/lows, sweeps.                |
| Smart Money (CHoCH/BOS/OB/FVG) | Structure events, order blocks, fair-value gaps.        |
| Confluence & Strategy    | Ranked trade zones, decision, trade plan.                      |
| Backtest                 | Run the Week 9 backtest, equity curve, drawdown, R, monthly.   |
| Trade Log                | Every closed trade with attribution and P/L.                   |
| Settings                 | Active symbol, analysis, risk, and read-only execution posture. |

## Architecture

```
dashboard/
├── app.py          # Streamlit entrypoint + navigation
├── settings.py     # DashboardConfig (presentation-only settings)
├── state.py        # st.session_state helpers
├── services.py     # Orchestrates the pipeline (only place touching engines)
├── charts.py       # Plotly chart builders
├── components.py   # Shared presentation components
├── widgets/        # Reusable input widgets (sidebar controls)
└── pages/          # overview, market_structure, liquidity, strategy,
                    # backtesting, trades, and settings
```

The dashboard is a **pure presentation layer** — it never contains trading
logic. Strategy/risk/execution decisions all live in the engine packages;
the UI only renders their results.

## Analytics and debugging

- Equity, drawdown, monthly-return, R-multiple, and confluence-performance charts.
- Individual trade explanation and inspection, with a candle-by-candle replay slider.
- Strategy diagnostics show evaluated, tradeable, and below-threshold zones with the
  engine-generated confluence explanation.
- Data and unchanged analysis inputs use Streamlit caching; selected trade and backtest
  results remain in session state.

## Design rules

- No `if choch and bos and fvg` in the UI — all decisions come from the
  engines.
- Read-only with respect to execution: backtesting is simulated, no live
  orders are placed (Week 11+ only).
- The backtester is deterministic, event-driven, and independent of MT5.
