# Structure Event Engine — Implementation TODO

## Steps

- [x] Analyze current architecture (choch.py, bos.py, analyzer.py, displacement.py, models.py, enums.py)
- [x] Confirm plan scope with user (backward-compatible analyzer, MSS placeholder, EventHistory)
- [x] Create `smart_money/event_history.py` (EventHistory wrapper with query helpers)
- [x] Create `smart_money/engine.py` (StructureEventEngine orchestrator + DisplacementValidator + detector registry + MSS slot)
- [x] Add `MSS` to `smart_money/enums.py` (StructureEventType.MSS)
- [x] Create `smart_money/mss.py` (MSSDetector future-slot placeholder)
- [x] Refactor `smart_money/analyzer.py` to delegate to StructureEventEngine
- [x] Update `smart_money/__init__.py` to export new public API
- [x] Add `mss_events` property to `smart_money/models.py` SmartMoneyAnalysis
- [x] Update `smart_money/README.md` with new engine architecture
- [x] Create `tests/unit/test_structure_event_engine.py`
- [x] Run full smart_money test suite to confirm no regressions (`126 passed`)

## Dependent Files to Edit

- `smart_money/enums.py` ✅
- `smart_money/engine.py` ✅ (new)
- `smart_money/event_history.py` ✅ (new)
- `smart_money/mss.py` ✅ (new)
- `smart_money/analyzer.py` ✅
- `smart_money/__init__.py` ✅
- `smart_money/models.py` ✅
- `smart_money/README.md` ✅
- `tests/unit/test_structure_event_engine.py` ✅ (new)

## Follow-up Steps

- Run `pytest tests/unit -k "choch or bos or smart_money or structure_event or displacement"` to verify no regressions.

