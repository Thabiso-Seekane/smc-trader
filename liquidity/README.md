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
| `range_detector.py` | Detects range-high / range-low liquidity from a consolidation. |
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

## External vs Internal Liquidity

Every liquidity level carries a `scope` classifying it as **External** or
**Internal** liquidity. This distinction matters in Smart Money Concepts:
major reversals often begin after **external** liquidity is taken, while
**internal** liquidity is frequently swept as part of continuation moves.
Building this in now makes the Week 4 CHoCH/BOS logic more accurate.

```
                       Liquidity
              ┌────────────┴────────────┐
              ▼                         ▼
      External Liquidity          Internal Liquidity
      ─────────────────          ──────────────────
      Range High                 Minor Swing High
      Range Low                  Minor Swing Low
      (Weekly / Daily / Major     Internal Equal High
       Swing levels feed in        Internal Equal Low
       during Week 4)
```

| Scope | Enum | Current Types | Typical Behaviour |
|-------|------|---------------|-------------------|
| External | `LiquidityScope.EXTERNAL` | `RANGE_HIGH`, `RANGE_LOW` | Major structural levels; reversals often begin after these are taken |
| Internal | `LiquidityScope.INTERNAL` | `SWING_HIGH`, `SWING_LOW`, `EQUAL_HIGHS`, `EQUAL_LOWS` | Minor pools inside the dealing range; frequently swept in continuation moves |

External pools also receive a strength bonus in `LiquidityRanker` so they
rank above structurally similar internal pools, making them preferred
reversal targets.

### Querying by scope

```python
result = LiquidityAnalyzer().analyze(df)

print(result.external_levels)   # or result.external()
print(result.internal_levels)   # or result.internal()
print(result.external_sweeps)   # external pools already taken
print(result.internal_sweeps)   # internal pools already taken
```

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

## Detection Rules & Configurable Tolerances

All tolerances are expressed in **pips** and normalized to an absolute
price distance using the instrument's pip size (`core.constants.pip_size`),
so a single setting behaves consistently across symbols.

| Detector | Configurable | Default | Detection Rule |
|----------|--------------|---------|----------------|
| `LiquidityDetector` | — | — | Every swing high from Week 2 becomes a `SWING_HIGH` (buy-side) level; every swing low becomes a `SWING_LOW` (sell-side) level. |
| `EqualHighDetector` | `tolerance` (pips), `symbol` | `tolerance=2` | Two or more swing highs within `tolerance` pips of each other are grouped into a single `EQUAL_HIGHS` cluster at their average price. |
| `EqualLowDetector` | `tolerance` (pips), `symbol` | `tolerance=2` | Two or more swing lows within `tolerance` pips are grouped into a single `EQUAL_LOWS` cluster at their average price. |
| `RangeDetector` | `lookback`, `tolerance` (pips), `symbol` | `lookback=3`, `tolerance=20` | Confirmed when at least `lookback * 2` alternating swings exist, swings strictly alternate high/low, and the range height (`max high − min low`) is positive and within `tolerance` pips. Emits one `RANGE_HIGH` and one `RANGE_LOW`. |
| `SweepDetector` | `lookahead` | `lookahead=True` | A buy-side level is swept when the candle `high` ≥ level price; a sell-side level is swept when the candle `low` ≤ level price. |
| `LiquidityRanker` | `recency_window_days`, `max_touches` | `recency_window_days=14`, `max_touches=5` | Strength is a weighted 0–100 score from five factors (swing significance, equal-level cluster, higher timeframe, number of touches, recency), each worth up to 20 points. |

### Example: configuring the analyzer

```python
result = LiquidityAnalyzer(
    lookback=2,          # swing fractal lookback (Week 2)
    tolerance=2,         # equal high/low proximity (pips)
    symbol="XAUUSD",     # normalizes pip tolerance to price
).analyze(df)
```

