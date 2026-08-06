# Week 5b — Trade Zone Abstraction — Implementation TODO

## Goal
Introduce a `TradeZone` abstraction that aggregates Order Blocks, Fair Value
Gaps, liquidity, and structural events into a single object with a
`Confluence Score`. This makes Weeks 6–9 cleaner by letting the future
Confluence Engine (Week 7) evaluate `TradeZone` objects instead of merging
unrelated structures on the fly.

```
                  Trade Zone
                       │
      ┌────────────────┼─────────────────┐
      │                │                 │
      ▼                ▼                 ▼
 Order Block      Fair Value Gap    Liquidity
                       │
                       ▼
                Confluence Score
```

## Steps

- [x] Add `ConfluenceLevel` / `TradeZoneStatus` to `smart_money/enums.py`
- [x] Create `smart_money/fair_value_gap.py` (FVG skeleton for Week 6)
- [x] Create `smart_money/trade_zone_models.py` (TradeZone, TradeZoneMap)
- [x] Create `smart_money/confluence.py` (ConfluenceScorer)
- [x] Create `smart_money/trade_zone_engine.py` (TradeZoneEngine façade + multi-TF)
- [x] Extend `smart_money/visualizer.py` (TradeZone rendering)
- [x] Update `smart_money/__init__.py` (export new API)
- [x] Update `smart_money/README.md` (TradeZone docs)
- [x] Create `tests/unit/test_trade_zone_models.py`
- [x] Create `tests/unit/test_confluence.py`
- [x] Create `tests/unit/test_trade_zone_engine.py`
- [x] Run full test suite

## Dependent Files to Edit

- `smart_money/enums.py`
- `smart_money/fair_value_gap.py` (new)
- `smart_money/trade_zone_models.py` (new)
- `smart_money/confluence.py` (new)
- `smart_money/trade_zone_engine.py` (new)
- `smart_money/visualizer.py`
- `smart_money/__init__.py`
- `smart_money/README.md`
- `tests/unit/test_trade_zone_models.py` (new)
- `tests/unit/test_confluence.py` (new)
- `tests/unit/test_trade_zone_engine.py` (new)
