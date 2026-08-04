# Liquidity Engine

Builds a pure liquidity-mapping engine that answers:

- Where is Buy Side Liquidity?
- Where is Sell Side Liquidity?
- Which liquidity is strongest?
- Has liquidity already been swept?
- What is the next liquidity target?

This engine depends on the Week 2 Market Structure Engine for swing
detection. It does **not** decide to buy or sell — it only builds a
Liquidity Map.

## Architecture

```
                Market Structure
                       │
                       ▼
              Swing Highs / Lows
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
 Equal Highs    Equal Lows     Swing Liquidity
        │              │              │
        └──────────────┼──────────────┘
                       ▼
             Liquidity Aggregator
                       │
                       ▼
                Liquidity Map
```

## Modules

| Module | Responsibility |
|--------|----------------|
| `enums.py` | Enum definitions (`LiquidityType`, `LiquidityStatus`). |
| `models.py` | Data models (`LiquidityLevel`, `LiquidityCluster`, `LiquidityMap`). |
| `detector.py` | Converts swings into swing-high/swing-low liquidity levels. |
| `equal_highs.py` | Groups proximate swing highs into stronger equal-high clusters. |
| `equal_lows.py` | Groups proximate swing lows into stronger equal-low clusters. |
| `sweeps.py` | Marks levels as swept when price trades through them. |
| `ranking.py` | Computes strength scores and identifies the next target. |
| `analyzer.py` | Public façade (`LiquidityAnalyzer`). |
| `visualizer.py` | Plotly-based debugging renderer (not used by strategy). |

## Quick Start

```python
import pandas as pd
from liquidity.analyzer import LiquidityAnalyzer

df = pd.DataFrame({
    "date": pd.to_datetime([...]),
    "open": [...],
    "high": [...],
    "low": [...],
    "close": [...],
    "volume": [...],
})

result = LiquidityAnalyzer().analyze(df)

# Query the map
print(result.buy_side_levels)    # active BSL above current price
print(result.sell_side_levels)   # active SSL below current price
print(result.swept_levels)       # levels already taken
print(result.strongest)          # most significant pool
print(result.next_target)        # next likely target
```

## Liquidity Types

| Enum Value | Description |
|------------|-------------|
| `BUY_SIDE` | Generic buy-side pool above price |
| `SELL_SIDE` | Generic sell-side pool below price |
| `EQUAL_HIGHS` | Clustered swing highs forming a strong resistance |
| `EQUAL_LOWS` | Clustered swing lows forming a strong support |
| `RANGE_HIGH` | Top of a defined trading range |
| `RANGE_LOW` | Bottom of a defined trading range |
| `SWING_HIGH` | A single significant swing high |
| `SWING_LOW` | A single significant swing low |

## Liquidity Lifecycle

```
  ┌─────────┐
  │  ACTIVE │  ← resting and not yet swept
  └────┬────┘
       │ price trades through the level
       ▼
  ┌─────────┐
  │  SWEPT  │  ← liquidity has been taken
  └─────────┘
```

## Visualizer

The visualizer renders the liquidity map as an interactive Plotly chart:

```python
from liquidity.visualizer import LiquidityVisualizer

fig = LiquidityVisualizer().render(result, candles=df)
# fig.show() — view in a browser
html = LiquidityVisualizer().to_html(result, candles=df)
```

