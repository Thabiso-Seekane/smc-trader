# Market Structure Engine

Builds a pure price-structure engine that answers:

- Where are the swing highs?
- Where are the swing lows?
- Is each swing a HH, HL, LH, or LL?
- What is the current trend?
- What was the previous trend?
- Is the market transitioning or ranging?

This engine does **not** understand order blocks, liquidity, CHoCH, BOS,
or FVG. It only understands price structure.

## Modules

| Module | Responsibility |
|--------|----------------|
| `enums.py` | Enum definitions only (`Trend`, `SwingType`, `StructureLabel`). |
| `models.py` | Data models only (`Swing`, `StructurePoint`, `MarketStructure`). |
| `swing_detector.py` | Detects fractal swing highs/lows with a configurable `lookback`. |
| `swing_classifier.py` | Labels swings as HH, HL, LH, or LL. |
| `trend_analyzer.py` | Derives current and previous trend from labels. |
| `analyzer.py` | Public façade (`MarketStructureAnalyzer`). |
| `visualizer.py` | Plotly-based debugging renderer (not used by strategy). |

## Quick Start

```python
import pandas as pd
from structure import MarketStructureAnalyzer

df = pd.DataFrame({
    "date": pd.to_datetime([...]),
    "open": [...],
    "high": [...],
    "low": [...],
    "close": [...],
    "volume": [...],
})

result = MarketStructureAnalyzer().analyze(df)
print(result.trend)
print(result.previous_trend)
for point in result.points:
    print(point.index, point.price, point.label)

# Full structure history (chronological HH/HL/LH/LL sequence)
print(result.history.labels)      # e.g. [HH, HL, HH, HL, LH, LL]
print(result.history.latest)      # most recent structure point
```

## Swing Detection

A candle is a **swing high** when its `high` is strictly greater than the
surrounding highs within the lookback window, and a **swing low** when its
`low` is strictly lower than the surrounding lows.

```python
from structure.swing_detector import SwingDetector

detector = SwingDetector(lookback=2)
swings = detector.detect(df)
```

The lookback is configurable so you can change the fractal window without
altering the rest of the pipeline.

## Swing Classification

Each swing is compared to the previous swing of the same type:

| Label | Meaning |
|-------|---------|
| `HH`  | Higher High |
| `HL`  | Higher Low |
| `LH`  | Lower High |
| `LL`  | Lower Low |

## Trend Analysis

- `HH`/`HL` sequences → **Bullish**
- `LL`/`LH` sequences → **Bearish**
- Mixed sequences → **Transition** (a range is reserved for future refinement)

## Structure History

Rather than keeping only the latest structure, the engine retains the full
chronological sequence of labelled swings via `market_structure.history`:

```
HH
↓
HL
↓
HH
↓
HL
↓
LH
↓
LL
```

This history is extremely valuable in later weeks:

- **Liquidity mapping** — significant historical swing points identify
  where liquidity pools sit.
- **CHoCH** — detect the first structural break after a sequence.
- **BOS** — confirm continuation based on previous structure.
- **Internal vs external structure** — the history model supports this
  without a data-model redesign.

## Visualizer

The visualizer renders the structure as an interactive Plotly chart for
debugging:

```python
import plotly.io as pio
from structure.visualizer import StructureVisualizer

fig = StructureVisualizer().render(result, candles=df)
pio.show(fig)          # view in a browser
html = StructureVisualizer().to_html(result, candles=df)  # standalone HTML
```
</content>
