# Week 8 — Risk & Trading Plan Engine

The Week 8 Risk Engine answers the questions:

> **"Should I prepare a trade?"** (Week 7) → **"How do I risk it?"** (Week 8)

It converts a Week 7 `TradeZone` into a complete, executable `TradePlan`.
The execution layer (a later week) never calculates stops or lot sizes — it
reads the plan and places orders.

## Architecture

```text
              Confluence Engine
                     │
                     ▼
                   Trade Zone
                     │
                     ▼
                Risk Management
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
 Position Sizing              Trade Validation
      │                             │
      └──────────────┬──────────────┘
                     ▼
                 Trade Plan
                     │
                     ▼
                Execution
```

## Folder Structure

```text
risk/
├── __init__.py
├── analyzer.py        # RiskAnalyzer — public façade
├── position_size.py   # PositionSizer — lot sizing
├── stop_loss.py       # StopLossPlacer — stop placement
├── take_profit.py     # TakeProfitPlacer — target placement
├── risk_reward.py     # RiskRewardAnalyzer — R:R validation
├── validator.py       # RiskValidator — reject over-risk trades
├── account.py         # Account — balance / drawdown / limits
├── models.py          # TradePlan, RiskMetrics, PositionSize
├── enums.py           # PositionSizingMethod, PlanStatus, etc.
├── visualizer.py      # RiskVisualizer
└── README.md
```

## TradePlan Model

The risk engine produces a `TradePlan`:

| Field            | Purpose                                  |
|------------------|------------------------------------------|
| `id`             | Unique plan identifier                   |
| `symbol`         | Trading symbol (e.g. XAUUSD)             |
| `direction`      | BUY / SELL                               |
| `entry_price`    | Ideal entry price                        |
| `stop_loss`      | Protective stop                          |
| `take_profit`    | Profit target                            |
| `risk_reward`    | Reward-to-risk ratio                     |
| `position_size`  | Computed lot size + risk amount          |
| `risk_metrics`   | Balance, risk %, status                  |
| `status`         | READY / REJECTED / EXPIRED               |
| `expiration`     | When the plan expires                    |

## What the Engine Answers

| Question                                          | Module           |
|---------------------------------------------------|------------------|
| How much should I risk?                           | `PositionSizer`  |
| What lot size should I trade?                     | `PositionSizer`  |
| Where should my stop-loss go?                     | `StopLossPlacer` |
| Where should my take-profit go?                   | `TakeProfitPlacer` |
| Does this trade meet the minimum R:R?             | `RiskRewardAnalyzer` |
| How much will I lose if stopped out?              | `TradePlan.stop_loss_amount` |
| How much can I make if the target is hit?         | `TradePlan.take_profit_amount` |
| Should this trade be rejected because of risk?    | `RiskValidator`  |

## Public API

```python
from risk import Account, RiskAnalyzer

account = Account(balance=10_000, risk_percent=1.0)
analyzer = RiskAnalyzer()

plan = analyzer.plan(
    trade_zone=best_setup,      # Week 7 TradeZone
    account=account,
    symbol="XAUUSD",
)

if plan.is_ready:
    print(plan.symbol, plan.direction)
    print("Entry", plan.entry_price, "Stop", plan.stop_loss, "Target", plan.take_profit)
    print("Lots", plan.position_size.lots, "Risk", plan.position_size.risk_amount)
    print("R:R", plan.risk_reward)
else:
    print("Rejected:", plan.note)
```

The execution layer never recalculates stops or lot sizes — it reads the
plan and places orders.
