# Week 7 — Strategy Engine

The Week 7 Strategy Engine answers the question:

> **"Should I prepare a trade?"**

It does **not** execute a trade — execution happens in Week 8. Week 7 is
responsible for identifying high-probability **setups**.

## Architecture

```text
Market Structure
       │
       ▼
Liquidity Engine
       │
       ▼
CHoCH / BOS Engine
       │
       ▼
Order Block Engine
       │
       ▼
Fair Value Gap Engine
       │
       ▼
Confluence Engine
       │
┌──────┴──────┐
▼             ▼
Trade Zones   Setup Ranking
       │
       ▼
Strategy Decision
```

## Core Idea

Instead of asking *"Is there an Order Block?"* or *"Is there a CHoCH?"*, the
strategy asks **"Is there a high-quality trading zone?"** — a much more
powerful abstraction.

## Folder Structure

```text
strategy/
├── __init__.py
├── analyzer.py        # StrategyAnalyzer — public façade
├── confluence.py      # ConfluenceEngine — decision maker
├── filters.py         # StrategyFilters — independent gates
├── premium_discount.py# PremiumDiscountAnalyzer
├── higher_timeframe.py# HigherTimeframeAnalyzer
├── scoring.py         # ConfluenceScorer — config-driven weights
├── trade_zone.py      # TradeZoneBuilder — geometry + anchors
├── models.py          # TradeZone, TradeDecision, StrategyResult
├── enums.py           # SignalDirection, DecisionStatus, etc.
├── visualizer.py      # StrategyVisualizer
└── README.md
```

## Confluence Scoring

The `ConfluenceEngine` blends eight independent factors into a 0-100 score.
The weights are **configuration-driven** so they can be tuned during
backtesting (Week 9) without changing source code.

| Factor                | Weight |
|-----------------------|--------|
| Higher Timeframe Bias | 20     |
| Liquidity Sweep       | 15     |
| CHoCH                 | 15     |
| BOS                   | 15     |
| Order Block           | 10     |
| Fair Value Gap        | 10     |
| Premium / Discount    | 10     |
| Risk / Reward         | 5      |
| **Total**             | **100**|

### Example

A perfect bullish confluence scores 100. Removing the Order Block drops it
to 90, removing BOS drops it to 75, removing CHoCH drops it to 60 — weak.

## Trading Thresholds

Instead of a boolean, the engine returns a `TradeDecision`:

| Confidence | Status     |
|-----------|------------|
| 90-100    | EXCELLENT  |
| 80-89     | STRONG     |
| 70-79     | ACCEPTABLE |
| Below 70  | IGNORE     |

## Premium / Discount

Using the latest dealing range (swing high → swing low), the analyzer
classifies a price relative to the 50% equilibrium:

* **Above equilibrium** → PREMIUM (expensive).
* **Below equilibrium** → DISCOUNT (cheap).
* Bullish setups are preferred in discount; bearish setups in premium.

## Higher Timeframe Bias

Trading against the higher timeframe is a common retail mistake. The
`HigherTimeframeAnalyzer` aligns buys with a bullish HTF and rejects
counter-HTF setups.

## Filters

`StrategyFilters` are independent, enable/disable checks:

* `min_confluence`
* `min_displacement`
* `higher_tf_alignment`
* `premium_discount_match`
* `min_risk_reward`
* `max_ob_age`
* `max_ob_touches`
* `require_liquidity_sweep`

## Public API

```python
structure = structure_engine.analyze(df)
liquidity = liquidity_engine.analyze(df, structure)
events = smart_money_engine.analyze(df, structure, liquidity)
order_blocks = order_block_engine.analyze(df, structure, liquidity, events)
imbalances = imbalance_engine.analyze(df, structure, liquidity, events, order_blocks)

trade_zones = strategy_engine.analyze(
    df, structure, liquidity, events, order_blocks, imbalances
)

best_setup = trade_zones.best()
print(best_setup.confluence_score)
print(best_setup.direction)
print(best_setup.reason)
```

The execution layer (Week 8) never needs to know how the score was
calculated — it simply receives the best validated setup.
