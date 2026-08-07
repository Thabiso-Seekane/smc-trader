# Week 8 — Risk & Trading Plan Engine — Implementation TODO

## Goal
Build a Risk & Trade Planning Engine that converts a Week 7 `TradeZone`
into a complete, executable `TradePlan`. The risk engine answers:

* How much should I risk?
* What lot size should I trade?
* Where should my stop-loss go?
* Where should my take-profit go?
* Does this trade meet the minimum R:R?
* How much money will I lose if stopped out?
* How much money can I make if the target is hit?
* Should this trade be rejected because of risk?

```
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

## Steps

- [x] Create `risk/enums.py` (`PositionSizingMethod`, `RiskStatus`, `PlanStatus`)
- [x] Create `risk/models.py` (`TradePlan`, `RiskMetrics`, `PositionSize`)
- [x] Create `risk/account.py` (`Account` — balance, equity, risk tracking)
- [x] Create `risk/position_size.py` (`PositionSizer` — risk-based lot sizing)
- [x] Create `risk/stop_loss.py` (`StopLossPlacer` — stop placement rules)
- [x] Create `risk/take_profit.py` (`TakeProfitPlacer` — target placement rules)
- [x] Create `risk/risk_reward.py` (`RiskRewardAnalyzer` — R:R validation)
- [x] Create `risk/validator.py` (`RiskValidator` — reject over-risk trades)
- [x] Create `risk/analyzer.py` (`RiskAnalyzer` — public façade)
- [x] Create `risk/visualizer.py` (TradePlan rendering)
- [x] Create `risk/__init__.py` (export new API)
- [x] Create `risk/README.md` (Risk Engine docs)
- [x] Create `tests/unit/test_risk_enums.py`
- [x] Create `tests/unit/test_risk_models.py`
- [x] Create `tests/unit/test_risk_account.py`
- [x] Create `tests/unit/test_risk_position_size.py`
- [x] Create `tests/unit/test_risk_stop_loss.py`
- [x] Create `tests/unit/test_risk_take_profit.py`
- [x] Create `tests/unit/test_risk_reward.py`
- [x] Create `tests/unit/test_risk_validator.py`
- [x] Create `tests/unit/test_risk_analyzer.py`
- [x] Create `tests/unit/test_risk_visualizer.py`
- [x] Run full test suite
- [x] Update `TODO.md` checklist
- [ ] Commit & push `feature/week8-risk-trading-plan`

## Dependent Files to Edit

- `risk/` package (activate)
- `risk/enums.py` (new)
- `risk/models.py` (new)
- `risk/account.py` (new)
- `risk/position_size.py` (new)
- `risk/stop_loss.py` (new)
- `risk/take_profit.py` (new)
- `risk/risk_reward.py` (new)
- `risk/validator.py` (new)
- `risk/analyzer.py` (new)
- `risk/visualizer.py` (new)
- `risk/README.md` (new)
- `risk/__init__.py`
- `tests/unit/test_risk_enums.py` (new)
- `tests/unit/test_risk_models.py` (new)
- `tests/unit/test_risk_account.py` (new)
- `tests/unit/test_position_size.py` (new)
- `tests/unit/test_stop_loss.py` (new)
- `tests/unit/test_take_profit.py` (new)
- `tests/unit/test_risk_reward.py` (new)
- `tests/unit/test_risk_validator.py` (new)
- `tests/unit/test_risk_analyzer.py` (new)

