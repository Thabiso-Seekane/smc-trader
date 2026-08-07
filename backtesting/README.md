# Backtesting Engine & Performance Analytics (Week 9)

A deterministic, event-driven backtesting engine that replays the full SMC
pipeline against historical OHLC data. It processes candles **sequentially**
(no look-ahead bias) and uses the same strategy + risk logic that the future
paper/live engine will use.

## Architecture

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

The backtester is **independent of MT5**. It consumes historical OHLC data
and simulates execution itself. MT5 is only for providing market data.

## Modules

| Module            | Purpose                                                        |
|-------------------|----------------------------------------------------------------|
| `enums.py`        | Order / position / result enums, intrabar resolution policy.   |
| `models.py`       | `BacktestConfig`, `Order`, `Position`, `Trade`, `EquityPoint`, `BacktestResult`, `PerformanceSummary`. |
| `commission.py`   | Per-lot commission charges.                                    |
| `slippage.py`     | Fixed slippage applied to fills.                               |
| `orders.py`       | Order lifecycle (submit / fill / cancel / reject).            |
| `position.py`     | Open/close positions, MFE/MAE, realized P&L.                   |
| `portfolio.py`    | Balance, equity, exposure, open/closed positions.              |
| `simulator.py`    | Sequential candle processing + intrabar resolution.            |
| `equity_curve.py` | Equity snapshots and running drawdown.                         |
| `metrics.py`      | Win rate, profit factor, expectancy, drawdown, Sharpe, R-analysis. |
| `analyzer.py`     | Confluence-score attribution.                                  |
| `report.py`       | CSV / JSON / HTML export.                                      |
| `visualizer.py`   | Plotly equity, drawdown, R-distribution, monthly returns.      |
| `engine.py`       | Public `BacktestEngine` façade.                                |

## Usage

```python
import pandas as pd
from backtesting import BacktestEngine, BacktestConfig

config = BacktestConfig(
    initial_balance=10_000.0,
    commission=7.0,
    slippage=0.05,
    spread=0.0,
    risk_per_trade=0.01,
    symbol="XAUUSD",
    timeframe="M15",
)

def executor(candle):
    # Return a list of orders or tuples:
    # (entry, stop, target, volume[, confluence, reason, direction])
    if candle.close < 2500:
        return [(2500.0, 2480.0, 2560.0, 0.20, 85.0, "Sweep + CHoCH", "BUY")]
    return []

engine = BacktestEngine(config=config)
result = engine.run(data=df, executor=executor)

print(result.total_trades)
print(result.win_rate)
print(result.profit_factor)
print(result.max_drawdown)
print(result.expectancy)

result.trades
result.equity_curve
```

## Reporting

```python
from backtesting import BacktestReport

report = BacktestReport(result)
report.to_csv("reports/trades.csv")
report.to_json("reports/summary.json")
report.to_html("reports/report.html")
print(report.text_summary())
```

## Visualization

```python
from backtesting import BacktestVisualizer

viz = BacktestVisualizer()
viz.equity_curve(result).show()
viz.drawdown_curve(result).show()
viz.r_distribution(result).show()
viz.monthly_returns(result).show()
viz.report_figure(result).show()
```

## Rendering

Event-driven: orders are filled and positions resolved **only** using the
current candle — never future data. This prevents look-ahead bias.

## Intrabar Resolution

When both the stop-loss and take-profit touch within a single candle, the
simulator uses a deterministic policy:

* `CONSERVATIVE` — assume the stop-loss was hit first (worst case).
* `OPTIMISTIC` — assume the take-profit was hit first (best case).
* `BAR_CLOSE` — resolve at the candle close.

A more advanced version can use lower-timeframe data to determine the actual
sequence.

## Strategy Attribution

Trades are grouped by their Week 7 confluence score so you can empirically
test whether "higher confluence = better trades":

```python
from backtesting import BacktestAnalyzer
analyzer = BacktestAnalyzer()
for band in analyzer.confluence_attribution(result.trades):
    print(band.label, band.trades, f"{band.win_rate:.0%}", f"{band.average_r:.2f}R")
