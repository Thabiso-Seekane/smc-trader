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

### PKG (backtesting package)
- [x] Create `backtesting/enums.py` (`OrderType`, `OrderStatus`, `PositionStatus`, `TradeResultType`, `ExitReason`, `IntrabarResolution`)
- [x] Create `backtesting/models.py` (`BacktestConfig`, `Order`, `Position`, `Trade`, `EquityPoint`, `BacktestResult`, `PerformanceSummary`)
- [x] Create `backtesting/commission.py` (`CommissionModel` — per-lot commission)
- [x] Create `backtesting/slippage.py` (`SlippageModel` — entry/exit slippage)
- [x] Create `backtesting/orders.py` (`OrderManager` — order lifecycle)
- [x] Create `backtesting/position.py` (`PositionManager` — open/close positions)
- [x] Create `backtesting/portfolio.py` (`Portfolio` — balance, equity, open/closed positions, exposure)
- [x] Create `backtesting/simulator.py` (`TradeSimulator` — sequential candle processing, conservative intrabar)
- [x] Create `backtesting/equity_curve.py` (`EquityCurve` — equity points)
- [x] Create `backtesting/metrics.py` (`PerformanceMetrics` — return, win rate, PF, expectancy, drawdown, Sharpe, R-analysis)
- [x] Create `backtesting/analyzer.py` (`BacktestAnalyzer` — confluence-score attribution)
- [x] Create `backtesting/report.py` (`BacktestReport` — CSV / JSON / HTML export)
- [x] Create `backtesting/visualizer.py` (equity, drawdown, R-distribution, monthly returns, confluence vs performance)
- [x] Create `backtesting/engine.py` (`BacktestEngine` — public façade)
- [x] Create `backtesting/__init__.py` (export new API)
- [x] Create `backtesting/README.md` (Backtesting docs)

### Risk integration
- [x] Wire automatic position sizing from `risk_per_trade` + stop distance into the engine
- [x] Enforce a risk cap so multiple concurrent positions cannot exceed the configured risk budget

### Tests
- [x] Create `tests/unit/test_backtest_enums.py`
- [x] Create `tests/unit/test_backtest_models.py`
- [x] Create `tests/unit/test_backtest_commission.py`
- [x] Create `tests/unit/test_backtest_slippage.py`
- [x] Create `tests/unit/test_backtest_orders.py`
- [x] Create `tests/unit/test_backtest_position.py`
- [x] Create `tests/unit/test_backtest_portfolio.py`
- [x] Create `tests/unit/test_backtest_simulator.py`
- [x] Create `tests/unit/test_backtest_equity_curve.py`
- [x] Create `tests/unit/test_backtest_metrics.py`
- [x] Create `tests/unit/test_backtest_engine.py`
- [x] Create `tests/unit/test_backtest_analyzer.py`
- [x] Create `tests/unit/test_backtest_report.py`
- [x] Create `tests/unit/test_backtest_visualizer.py`
- [x] Create `tests/unit/test_drawdown.py` (drawdown / equity-curve drawdown)
- [x] Create `tests/integration/test_full_backtest.py`
- [x] Create `tests/integration/test_strategy_backtest.py`

### Wrap-up
- [x] Run full test suite
- [x] Update `TODO.md` checklist
- [x] Commit & push `feature/week9-backtesting-engine`

## Dependent Files to Edit

- `backtesting/engine.py` (risk sizing + risk cap)
- `tests/unit/test_drawdown.py` (new)
- `tests/integration/test_full_backtest.py` (new)
- `tests/integration/test_strategy_backtest.py` (new)
