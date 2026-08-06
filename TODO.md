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
