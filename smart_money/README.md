# Smart Money Engine (CHoCH / BOS / MSS / Order Blocks)

Detects structural changes in price — **Change of Character (CHoCH)**,
**Break of Structure (BOS)**, (future) **Market Structure Shift (MSS)**,
and **Order Block zones** — as first-class objects, not booleans. It
reuses the Week 2 market-structure engine, the Week 3 liquidity engine,
and the Week 4 structural events to build a complete picture of where
institutional buying or selling is most likely to occur.

## What it answers

- Where (and when) did a Bullish or Bearish CHoCH occur?
- Where (and when) did a Bullish or Bearish BOS occur?
- Was the break internal or external?
- How strong is the displacement behind each break?
- Where are the high-quality Bullish / Bearish Order Block zones?
- Which zones are active, mitigated, or invalidated?
- How strong is each Order Block (ranked 0-100)?

## Modules

| Module | Responsibility |
|--------|----------------|
| `enums.py` | Enum definitions only (`StructureEventType`, `Direction`, `BreakSystem`, `DisplacementQuality`). |
| `models.py` | Data models only (`StructureEvent`, `SmartMoneyAnalysis`). |
| `displacement.py` | Scores structural displacement (0–100) of a break candle. |
| `validator.py` | Validates candles/structure/liquidity inputs. |
| `choch.py` | Detects Bullish/Bearish CHoCH (requires trend + sweep + break). |
| `bos.py` | Detects Bullish/Bearish BOS with internal/external classification. |
| `mss.py` | Future Market Structure Shift detector (registered but dormant). |
| `event_history.py` | `EventHistory` — queryable chronological store of structural events. |
| `engine.py` | `StructureEventEngine` — single interface orchestrating all detectors. |
| `analyzer.py` | Public façade (`SmartMoneyAnalyzer`) that delegates to the engine. |
| `visualizer.py` | Plotly-based debugging renderer (not used by strategy). |

## Architecture: the Structure Event Engine

Rather than treating CHoCH and BOS as completely separate modules, the
`StructureEventEngine` provides **one consistent interface** for all
structural events:

```
MarketStructure
        │
        ▼
StructureEventEngine
        │
        ├── ChoCHDetector
        ├── BosDetector
        ├── MSSDetector (future)
        ├── DisplacementValidator (shared)
        └── EventHistory
```

The engine holds a registry of detectors, a shared displacement validator,
and an `EventHistory`. Every detector returns `StructureEvent` objects that
are merged, de-duplicated, sorted, and recorded into the history. Adding a
new structural event (MSS, internal vs external BOS, weak vs strong BOS,
multi-timeframe events) is as simple as registering a new detector.

```python
from smart_money import StructureEventEngine

engine = StructureEventEngine()
events = engine.detect(
    structure=structure,
    candles=df,
    swept_sell_side=engine_history_sell,
    swept_buy_side=engine_history_buy,
    external_prices={...},
)
print(engine.history.latest)
```

The `SmartMoneyAnalyzer` facade remains the recommended entry point for most
callers and delegates internally to the engine:

```python
from smart_money import SmartMoneyAnalyzer

result = SmartMoneyAnalyzer().analyze(
    candles=df, structure=structure, liquidity=liquidity,
)
```

## Quick Start

```python
import pandas as pd
from structure import MarketStructureAnalyzer
from liquidity import LiquidityAnalyzer
from smart_money import SmartMoneyAnalyzer

df = pd.DataFrame({
    "date": pd.to_datetime([...]),
    "open": [...], "high": [...], "low": [...], "close": [...], "volume": [...],
})

structure = MarketStructureAnalyzer().analyze(df)
liquidity = LiquidityAnalyzer().analyze(df)

result = SmartMoneyAnalyzer().analyze(
    candles=df,
    structure=structure,
    liquidity=liquidity,
)

for event in result.events:
    print(
        event.event_type.value,   # CHOCH | BOS | MSS
        event.direction.value,    # BULLISH | BEARISH
        "@ index", event.confirmation_index,
        "strength", event.displacement_strength,
    )

print(result.choch_events)
print(result.bos_events)
print(result.mss_events)
```

## CHoCH vs BOS

| | CHoCH | BOS |
|--|-------|-----|
| Meaning | First break suggesting a **reversal** | Break confirming **continuation** |
| Requires trend | Yes (prior trend) | Yes (prior trend) |
| Requires liquidity sweep | Yes | No |
| Sequence (bullish) | LL/LH → sweep → HL → break LH | HH/HL → HH → break HH |

## CHoCH Rules

A CHoCH **never** fires simply by breaking a level. It requires all three:

1. **Existing structure** — a prior bearish run (LL/LH) for a Bullish
   CHoCH, or a prior bullish run (HH/HL) for a Bearish CHoCH.
2. **Liquidity interaction** — a sell-side level must be swept (Bullish)
   or a buy-side level swept (Bearish) before the reversal point.
3. **Structural break** — a Higher Low forms (Bullish) or a Lower High
   forms (Bearish), then price breaks the opposing swing with valid
   displacement.

## BOS Rules

- **Bullish BOS** — HH/HL structure continues; price breaks the prior high.
- **Bearish BOS** — LL/LH structure continues; price breaks the prior low.
- **Internal / External** — a break is External when it coincides with a
  major structural liquidity level (from the liquidity map); otherwise
  Internal.

## Order Block Engine (Week 5)

The **Order Block Engine** consumes the Week 2 structure, Week 3 liquidity
map, and Week 4 structural events to locate high-quality institutional
zones — where is institutional buying or selling most likely to occur?

```
Price
  │
  ▼
CHoCH/BOS
  │
  ▼
Displacement
  │
  ▼
Locate Origin Candle
  │
  ▼
Create Order Block
  │
  ▼
Validate
  │
  ▼
Mitigate / Invalidate
  │
  ▼
Rank
  │
  ▼
OrderBlockMap
```

### The domain model

`OrderBlock` — a single institutional zone with `direction`, `high`, `low`,
`origin_index`, `origin_time`, `created_from_event`, `displacement_score`,
`fresh`, `mitigated`, `invalidated`, `strength`, and `timeframe`.

`OrderBlockMap` — the aggregated result exposing `bullish`, `bearish`,
`active`, `mitigated`, and `invalidated` lists.

```python
from smart_money import OrderBlockEngine

# structure = structure_engine.analyze(df)
# liquidity = liquidity_engine.analyze(df, structure)
# events    = smart_money_engine.analyze(df, structure, liquidity)

results = OrderBlockEngine().analyze(
    df,
    structure=structure,
    liquidity=liquidity,
    events=events,
)

print(results.active)      # fresh, usable zones
print(results.bullish)     # buy-side zones
print(results.bearish)     # sell-side zones
```

### Modules

| Module | Responsibility |
|--------|----------------|
| `order_block_models.py` | `OrderBlock`, `OrderBlockMap` data models. |
| `order_blocks.py` | `OrderBlockDetector` — displacement → origin candle → zone. |
| `order_block_validator.py` | Rejects doji / tiny / weak / consumed zones. |
| `mitigation.py` | `MitigationDetector` — mitigation, invalidation, freshness. |
| `ranking.py` | `OrderBlockRanker` — weighted 0-100 score. |
| `order_block_engine.py` | `OrderBlockEngine` public façade + multi-TF. |

### Multi-timeframe

`OrderBlockEngine.analyze_multi` accepts a dict of `{timeframe: DataFrame}`
(plus matching structures, liquidities, and events) and merges all zones
into a single ranked map.

### Visualizer

```python
import plotly.io as pio
from smart_money.visualizer import SmartMoneyVisualizer

fig = SmartMoneyVisualizer().build_order_block_figure(order_blocks, candles=df)
pio.show(fig)
```

## Visualizer

```python
import plotly.io as pio
from smart_money.visualizer import SmartMoneyVisualizer

fig = SmartMoneyVisualizer().render(result, candles=df)
pio.show(fig)          # view in a browser
html = SmartMoneyVisualizer().to_html(result, candles=df)  # standalone HTML
```

## Trade Zones (Week 5b)

Instead of keeping Order Blocks isolated, the strategy reasons about a
**Trade Zone** — a single high-probability trading zone that aggregates
multiple independent confirmation factors into one object scored by a
**Confluence Score**. This makes Weeks 6–9 cleaner because the future
Confluence Engine (Week 7) simply evaluates `TradeZone` objects instead
of merging unrelated structures on the fly.

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

A `TradeZone` can combine:

- An **Order Block** (Week 5).
- One or more **Fair Value Gaps** (Week 6).
- Nearby **liquidity** (Week 3).
- Recent **CHoCH / BOS** structural events (Week 4).
- Higher-timeframe **alignment**.

### The domain model

`TradeZone` — a single zone with `direction`, `high`, `low`, `origin_time`,
an optional `order_block`, `fair_value_gaps`, `liquidity_levels`, `events`,
plus a `confluence_score` (0-100) and `confluence_level`.

`TradeZoneMap` — the aggregated result exposing `bullish`, `bearish`,
`active`, `strongest`, and `all`.

### The Confluence Scorer

The `ConfluenceScorer` blends the confirmation factors into a single 0-100
score so the strategy can answer "where is the highest-probability trading
zone?":

| Factor | Weight |
|--------|--------|
| Order Block Strength | 30 |
| Fair Value Gap Presence | 20 |
| Liquidity Interaction | 20 |
| Structural Event Context | 15 |
| Higher-Timeframe Alignment | 15 |

A score of 0-39 is `WEAK`, 40-69 is `MODERATE`, and 70+ is `STRONG`.

```python
from smart_money import TradeZoneEngine, ConfluenceScorer

# order_blocks = OrderBlockEngine().analyze(df, structure, liquidity, events)
# liquidity    = liquidity_engine.analyze(df, structure)
# events       = smart_money_engine.analyze(df, structure, liquidity)
# fvgs         = FVGDetector().detect(df, timeframe="H1")

zones = TradeZoneEngine(timeframe="H1").analyze(
    order_blocks=order_blocks,
    liquidity=liquidity,
    events=events,
    fair_value_gaps=fvgs,
)

print(zones.strongest)   # highest-confluence active zone
print(zones.all)         # full ranked list
```

### Multi-timeframe

`TradeZoneEngine.analyze_multi` accepts per-timeframe mappings of order
blocks, liquidities, events, and FVGs, then merges and ranks the combined
set into a single map.

### Trade Zone visualizer

```python
import plotly.io as pio
from smart_money.visualizer import SmartMoneyVisualizer

fig = SmartMoneyVisualizer().build_trade_zone_figure(zones, candles=df)
pio.show(fig)
```

### Trade Zone modules

| Module | Responsibility |
|--------|----------------|
| `fair_value_gap.py` | `FairValueGap` model + `FVGDetector` (Week 6 skeleton). |
| `trade_zone_models.py` | `TradeZone`, `TradeZoneMap` data models. |
| `confluence.py` | `ConfluenceScorer` — weighted 0-100 scoring + ranking. |
| `trade_zone_engine.py` | `TradeZoneEngine` public façade + multi-TF. |
</content>
