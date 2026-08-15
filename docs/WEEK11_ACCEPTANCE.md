# Week 11 Paper Trading Acceptance

Status: complete. The Week 11 runtime is paper-only and reuses the existing
Weeks 2-8 analysis, strategy, risk, and `TradePlan` pipeline.

| Requirement | Implementation | Verification |
|---|---|---|
| Broker abstraction | `execution/broker.py` | Paper broker protocol tests |
| Virtual order lifecycle | `execution/paper_broker.py` | Order lifecycle tests |
| TradePlan bridge | `execution/paper_executor.py` | Executor and pipeline tests |
| Typed order/position/fill/trade domain | `execution/models.py`, `orders.py`, `positions.py`, `fills.py`, `trades.py` | Model/lifecycle tests |
| Closed-candle processing once | `execution/market_data.py`, `realtime.py` | Closed-candle and signal tests |
| Duplicate signal protection | SQLite `signals` table | Duplicate/restart tests |
| Execution risk guards | `execution/paper_executor.py`, `session.py` | Spread, session, daily-loss, position-limit tests |
| SQLite recovery | `execution/persistence.py` | Orders, positions, fills, trades, account and signal restart tests |
| Paper account and P&L | `execution/paper_portfolio.py` | Realized, unrealized, SL/TP and daily rollover tests |
| Streamlit monitor | `dashboard/pages/paper_trading.py` | Dashboard integration/smoke tests |
| Health reporting | CLI and dashboard paper monitor | Application and dashboard tests |
| Paper-only safety | Paper path has no `order_send` call | Source audit and MT5 smoke |

## Run

Use either:

```powershell
paper-trading
```

or, from the repository root:

```powershell
python -m execution.paper_trading
```

The startup banner prints `MODE: PAPER TRADING` and
`MT5 REAL ORDER: NONE`. Stop with `Ctrl+C`; the SQLite state is committed and
reloaded on the next start.

The separate guarded live broker is outside the Week 11 paper path. It is not
referenced by `PaperTradingApp`, `PaperExecutor`, `PaperBroker`, or
`RealTimePaperEngine`.
