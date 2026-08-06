# Week 6 — Imbalance Engine — Implementation TODO

## Goal
Build a complete, extensible **Imbalance Engine** that detects price
imbalances — starting with **Fair Value Gaps (FVGs)** — and is designed to
accommodate future imbalance types (Volume Imbalance, Opening Gap,
Liquidity Void, Inefficient Move) without a pipeline redesign.

```
Price
  │
  ▼
Displacement
  │
  ▼
3-Candle Pattern
  │
  ▼
Create Gap
  │
  ▼
Validate
  │
  ▼
Detect Fill
  │
  ▼
Link (OB / Event / Liquidity)
  │
  ▼
Rank
  │
  ▼
ImbalanceMap
```

## Steps

- [x] Add `FillStatus`, `ImbalanceType`, `GapQuality` to `smart_money/enums.py`
- [x] Extend `smart_money/fair_value_gap.py` (rich `FairValueGap` model + real `FVGDetector`)
- [x] Create `smart_money/fills.py` (`FillDetector` — fill %, status, freshness)
- [x] Create `smart_money/imbalance_validator.py` (`ImbalanceValidator`)
- [x] Create `smart_money/imbalance_ranking.py` (`ImbalanceRanker`)
- [x] Create `smart_money/imbalance.py` (`ImbalanceMap` + `ImbalanceEngine`)
- [x] Update `smart_money/__init__.py` (export new API)
- [x] Extend `smart_money/visualizer.py` (`build_imbalance_figure`)
- [x] Update `smart_money/README.md` (Imbalance Engine docs)
- [x] Create `tests/unit/test_fair_value_gap.py`
- [x] Create `tests/unit/test_gap_fill.py`
- [x] Create `tests/unit/test_gap_validator.py`
- [x] Create `tests/unit/test_gap_ranking.py`
- [x] Create `tests/unit/test_imbalance_engine.py`
- [x] Run full test suite (251 passed, 1 skipped)

## Dependent Files to Edit

- `smart_money/enums.py`
- `smart_money/fair_value_gap.py`
- `smart_money/fills.py` (new)
- `smart_money/imbalance_validator.py` (new)
- `smart_money/imbalance_ranking.py` (new)
- `smart_money/imbalance.py` (new)
- `smart_money/__init__.py`
- `smart_money/visualizer.py`
- `smart_money/README.md`
- `tests/unit/test_fair_value_gap.py` (new)
- `tests/unit/test_gap_fill.py` (new)
- `tests/unit/test_gap_validator.py` (new)
- `tests/unit/test_gap_ranking.py` (new)
- `tests/unit/test_imbalance_engine.py` (new)

---

# Week 7 — Strategy Engine — Implementation TODO

## Goal
Build the **Confluence Engine** referenced in Weeks 5-6. It consumes all
upstream detection outputs (TradeZone, ImbalanceMap, OrderBlockMap,
LiquidityMap, StructureEvents / MarketStructure) and produces
high-probability **setups**. It **prepares** — it does NOT execute
(execution = Week 8).

```
TradeZone / ImbalanceMap / OrderBlockMap / LiquidityMap / Events
       │
       ▼
Strategy Engine (ConfluenceEngine)
       │
       ▼
TradeZoneBuilder (geometry + anchors)
       │
       ▼
ConfluenceScoringEngine (config-driven weights)
       │
       ▼
StrategyFilters (independent gates)
       │
       ▼
StrategyAnalyzer (façade) → TradeDecision (EXCELLENT/STRONG/
                                   ACCEPTABLE/IGNORE)
```

## Steps

- [x] Create `strategy/enums.py` (`SignalDirection`, `DecisionStatus`, `SetupType`, `PremiumDiscountPosition`)
- [x] Create `strategy/models.py` (`TradeZone`, `TradeDecision`, `StrategyResult`)
- [x] Create `strategy/premium_discount.py` (`PremiumDiscountAnalyzer`)
- [x] Create `strategy/higher_timeframe.py` (`HigherTimeframeAnalyzer`)
- [x] Create `strategy/scoring.py` (`ConfluenceScorer` — config-driven weights/thresholds)
- [x] Create `strategy/confluence.py` (`ConfluenceEngine` — decision maker)
- [x] Create `strategy/filters.py` (`StrategyFilters`)
- [x] Create `strategy/trade_zone.py` (`TradeZoneBuilder`)
- [x] Create `strategy/analyzer.py` (`StrategyAnalyzer` façade)
- [x] Create `strategy/visualizer.py` (setup visualization)
- [x] Create `strategy/README.md` (scoring methodology + API)
- [x] Update `strategy/__init__.py` (export new API)
- [x] Create `tests/unit/test_premium_discount.py`
- [x] Create `tests/unit/test_trade_zone.py`
- [x] Create `tests/unit/test_filters.py`
- [x] Create `tests/unit/test_confluence.py`
- [x] Create `tests/unit/test_strategy.py`
- [x] Run full test suite (**270 passed, 1 skipped**)

## Dependent Files to Edit

- `strategy/` package (new)
- `strategy/enums.py` (new)
- `strategy/models.py` (new)
- `strategy/premium_discount.py` (new)
- `strategy/higher_timeframe.py` (new)
- `strategy/scoring.py` (new)
- `strategy/confluence.py` (new)
- `strategy/filters.py` (new)
- `strategy/trade_zone.py` (new)
- `strategy/analyzer.py` (new)
- `strategy/visualizer.py` (new)
- `strategy/README.md` (new)
- `strategy/__init__.py` (new)
- `tests/unit/test_premium_discount.py` (new)
- `tests/unit/test_trade_zone.py` (new)
- `tests/unit/test_filters.py` (new)
- `tests/unit/test_confluence.py` (new)
- `tests/unit/test_strategy.py` (new)
