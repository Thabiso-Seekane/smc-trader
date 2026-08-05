# Smart Money Engine (CHoCH / BOS / MSS)

Detects structural changes in price — **Change of Character (CHoCH)**,
**Break of Structure (BOS)**, and (future) **Market Structure Shift (MSS)**
— as first-class events, not booleans. It reuses the Week 2 market-structure
engine and the Week 3 liquidity engine to require genuine structure,
liquidity interaction, and a valid structural break before firing.

## What it answers

- Where (and when) did a Bullish or Bearish CHoCH occur?
- Where (and when) did a Bullish or Bearish BOS occur?
- Was the break internal or external?
- How strong is the displacement behind each break?

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

## Visualizer

```python
import plotly.io as pio
from smart_money.visualizer import SmartMoneyVisualizer

fig = SmartMoneyVisualizer().render(result, candles=df)
pio.show(fig)          # view in a browser
html = SmartMoneyVisualizer().to_html(result, candles=df)  # standalone HTML
```
</content>
