# STEP 9 — Validator — Implementation TODO

- [x] Confirm plan with user
- [x] Create `core/exceptions.py` with `SMCError` base and `DataValidationError`
- [x] Create `data/validator.py` with `validate_candles(frame)` and all required checks
- [x] Update `core/__init__.py` to export `DataValidationError` / `SMCError`
- [x] Create `tests/test_validator.py` covering every validation rule
- [x] Run `python -m pytest tests/test_validator.py -v`
- [x] Run full test suite `python -m pytest -v` — **106 passed, 1 skipped**

# Week 3 — Liquidity Engine — Deliverables Audit

- [x] Swing liquidity detection (`liquidity/detector.py`)
- [x] Equal highs detection (`liquidity/equal_highs.py`)
- [x] Equal lows detection (`liquidity/equal_lows.py`)
- [x] Range liquidity detection (`liquidity/range_detector.py`)
- [x] Liquidity sweep detection (`liquidity/sweeps.py`)
- [x] Liquidity strength scoring (`liquidity/ranking.py`)
- [x] Liquidity ranking (`liquidity/ranking.py`)
- [x] LiquidityMap domain model (`liquidity/models.py`)
- [x] Plotly visualization (`liquidity/visualizer.py`)
- [x] Comprehensive unit tests (`tests/unit/test_*.py`)
- [x] Documentation of detection rules and configurable tolerances (`liquidity/README.md`)
- [x] Final full test run — **106 passed, 1 skipped**

# Week 3 — External / Internal Liquidity Refinement

- [x] Add `LiquidityScope` enum (`EXTERNAL`, `INTERNAL`) in `liquidity/enums.py`
- [x] Add `scope` field + `is_external` / `is_internal` to `LiquidityLevel` in `liquidity/models.py`
- [x] Add `external_levels`, `internal_levels`, `external`, `internal`, `external_sweeps`, `internal_sweeps` to `LiquidityMap`
- [x] Wire scope: swings → INTERNAL, equal highs/lows → INTERNAL, range high/low → EXTERNAL
- [x] Add external-liquidity strength bonus in `liquidity/ranking.py`
- [x] Export `LiquidityScope` from `liquidity/__init__.py`
- [x] Add External/Internal tests in `tests/unit/test_liquidity.py`
- [x] Document External vs Internal concept in `liquidity/README.md`
- [x] Full test suite — **110 passed, 1 skipped**
