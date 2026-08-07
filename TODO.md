# Week 9 — Backtesting Engine & Performance Analytics — Implementation TODO

## Goal
Build a **deterministic, event-driven backtesting engine** that replays the
full SMC pipeline (Market Structure → Liquidity → CHoCH/BOS → Order Blocks →
FVG → Strategy → Trade Plan → Execution) against historical OHLC data.

The engine processes candles **sequentially** (no future data / no
look-ahead bias) and uses the **same** strategy + risk-management logic that
the future paper/live engine will use. It simulates execution (spread,
slippage, commission, intrabar resolution), tracks a portfolio, and produces
performance analytics (equity curve, drawdown, win rate, profit factor,
expectancy, R-multiple distribution, Sharpe, confluence attribution).

```
              Strategy
                 │
        ┌────────┴────────┐
        ▼                 ▼
   Backtest Engine   Paper Engine
        │                 │
        ▼                 ▼
   Simulator            MT5
```

## Steps

- [ ] Create `backtesting/enums.py` (`OrderType`, `OrderStatus`, `PositionStatus`, `TradeResultType`, `ExitReason`, `IntrabarResolution`)
- [ ] Create `backtesting/models.py` (`BacktestConfig`, `Order`, `Position`, `Trade`, `EquityPoint`, `BacktestResult`, `PerformanceSummary`)
- [ ] Create `backtesting/commission.py` (`CommissionModel` — per-lot commission)
- [ ] Create `backtesting/slippage.py` (`SlippageModel` — entry/exit slippage)
- [ ] Create `backtesting/orders.py` (`OrderManager` — order lifecycle)
- [ ] Create `backtesting/position.py` (`PositionManager` — open/close positions)
- [ ] Create `backtesting/portfolio.py` (`Portfolio` — balance, equity, open/closed positions, exposure)
- [ ] Create `backtesting/simulator.py` (`TradeSimulator` — sequential candle processing, conservative intrabar)
- [ ] Create `backtesting/equity_curve.py` (`EquityCurve` — equity points)
- [ ] Create `backtesting/metrics.py` (`PerformanceMetrics` — return, win rate, PF, expectancy, drawdown, Sharpe, R-analysis)
- [ ] Create `backtesting/analyzer.py` (`BacktestAnalyzer` — confluence-score attribution)
- [ ] Create `backtesting/report.py` (`BacktestReport` — CSV / JSON / HTML export)
- [ ] Create `backtesting/visualizer.py` (equity, drawdown, R-distribution, monthly returns, confluence vs performance)
- [ ] Create `backtesting/engine.py` (`BacktestEngine` — public façade)
- [ ] Create `backtesting/__init__.py` (export new API)
- [ ] Create `backtesting/README.md` (Backtesting docs)
- [ ] Create `tests/unit/test_backtest_enums.py`
- [ ] Create `tests/unit/test_backtest_models.py`
- [ ] Create `tests/unit/test_commission.py`
- [ ] Create `tests/unit/test_slippage.py`
- [ ] Create `tests/unit/test_orders.py`
- [ ] Create `tests/unit/test_position.py`
- [ ] Create `tests/unit/test_portfolio.py`
- [ ] Create `tests/unit/test_simulator.py`
- [ ] Create `tests/unit/test_equity_curve.py`
- [ ] Create `tests/unit/test_metrics.py`
- [ ] Create `tests/unit/test_backtest_engine.py`
- [ ] Create `tests/integration/test_full_backtest.py`
- [ ] Run full test suite
- [ ] Update `TODO.md` checklist
- [ ] Commit & push `feature/week9-backtesting-engine`

## Dependent Files to Edit

- `backtesting/` package (activate)
- `backtesting/enums.py` (new)
- `backtesting/models.py` (new)
- `backtesting/commission.py` (new)
- `backtesting/slippage.py` (new)
- `backtesting/orders.py` (new)
- `backtesting/position.py` (new)
- `backtesting/portfolio.py` (new)
- `backtesting/simulator.py` (new)
- `backtesting/equity_curve.py` (new)
- `backtesting/metrics.py` (new)
- `backtesting/analyzer.py` (new)
- `backtesting/report.py` (new)
- `backtesting/visualizer.py` (new)
- `backtesting/engine.py` (new)
- `backtesting/README.md` (new)
- `backtesting/__init__.py`
- `tests/unit/test_backtest_*.py` (new)
- `tests/integration/test_full_backtest.py` (new)
