# Smart Money Engine (CHoCH / BOS)

Detects structural changes in price — **Change of Character (CHoCH)** and
**Break of Structure (BOS)** — as first-class events, not booleans. It
reuses the Week 2 market-structure engine and the Week 3 liquidity engine
to require genuine structure, liquidity interaction, and a valid structural
break before firing.

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
| `analyzer.py` | Public façade (`SmartMoneyAnalyzer`). |
| `visualizer.py` | Plotly-based debugging renderer (not used by strategy). |

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
        event.event_type.value,   # CHOCH | BOS
        event.direction.value,    # BULLISH | BEARISH
        "@ index", event.confirmation_index,
        "strength", event.displacement_strength,
    )

print(result.choch_events)
print(result.bos_events)
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
