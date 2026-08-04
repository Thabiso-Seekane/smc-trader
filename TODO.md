# Week 2 — Market Structure Engine — Implementation TODO

- [x] Confirm plan with user
- [x] Create `structure/enums.py` (Trend, SwingType, StructureLabel)
- [x] Create `structure/models.py` (Swing, StructurePoint, MarketStructure)
- [x] Create `structure/swing_detector.py` (SwingDetector)
- [x] Create `structure/swing_classifier.py` (SwingClassifier)
- [x] Create `structure/trend_analyzer.py` (TrendAnalyzer)
- [x] Create `structure/analyzer.py` (MarketStructureAnalyzer)
- [x] Create `structure/visualizer.py` (StructureVisualizer)
- [x] Create `structure/README.md`
- [x] Update `structure/__init__.py` to export public API
- [x] Create `tests/unit/test_structure.py`
- [x] Run `python -m pytest tests/unit/test_structure.py -v`
- [x] Run full test suite `python -m pytest -v`

## Notes
- Split unit tests into 4 deterministic files using synthetic data (no MT5):
  - `tests/unit/test_swing_detector.py`
  - `tests/unit/test_classifier.py`
  - `tests/unit/test_trend.py`
  - `tests/unit/test_market_structure.py`
- All 30 structure unit tests pass (23 + 3 Plotly visualizer tests + 3 history tests).
- Public API verified: `MarketStructureAnalyzer().analyze(df)` returns
  `.trend`, `.swings`, `.structure`.
- Plotly-based visualizer added (`StructureVisualizer.render/build_figure/to_html`).
- `plotly` + `pandas` added to `pyproject.toml` dependencies.
- Structure history added: `market_structure.history` exposes the full
  chronological HH/HL/LH/LL sequence via `StructureHistory` (with
  `.labels`, `.latest`, `.is_empty`, `__len__`).
- Full suite: 33 passed in tests/unit, 1 skipped in integration.
- `test_main.py` failure is pre-existing (requires a live MT5 connection) and unrelated to the structure work.

