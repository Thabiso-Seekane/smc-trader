"""Service layer for the Week 10 Streamlit dashboard.

The services module is the *only* place that touches the trading engines. It
orchestrates the full pipeline:

    MT5 / data_store -> structure -> liquidity -> CHoCH/BOS -> OB -> FVG
    -> strategy -> risk -> backtest

The Streamlit pages never contain trading logic - they call these services
and render the returned objects. This keeps the dashboard a pure
presentation layer (Week 10 rule: no ``if choch and bos and fvg`` in the UI).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

# --- data ----------------------------------------------------
from data.storage import load_candles
from data.validator import validate_candles

# --- analysis engines ----------------------------------------
from liquidity.analyzer import LiquidityAnalyzer
from smart_money.analyzer import SmartMoneyAnalyzer
from smart_money.imbalance import ImbalanceEngine
from smart_money.order_block_engine import OrderBlockEngine
from strategy.analyzer import StrategyAnalyzer
from strategy.filters import StrategyFilters
from structure.analyzer import MarketStructureAnalyzer

# --- risk -----------------------------------------------------
from risk.account import Account
from risk.analyzer import RiskAnalyzer

# --- backtesting ----------------------------------------------
from backtesting.engine import BacktestEngine
from backtesting.models import BacktestConfig, BacktestResult

from dashboard.settings import DashboardConfig


@st.cache_resource(show_spinner=False)
def get_paper_broker():
    """Return the persisted paper broker used only for dashboard inspection."""
    from config.settings import settings
    from execution.paper_broker import PaperBroker
    from execution.persistence import PaperStore

    return PaperBroker(
        PaperStore(settings.paper_database),
        initial_balance=settings.paper_initial_balance,
    )


@dataclass(slots=True)
class AnalysisBundle:
    """Everything the pages need to render a full SMC analysis."""

    df: pd.DataFrame = field(default_factory=pd.DataFrame)
    structure: Any = None
    liquidity: Any = None
    events: Any = None
    order_blocks: Any = None
    imbalances: Any = None
    strategy: Any = None
    plan: Any = None
    account: Any = None
    symbol: str = ""
    timeframe: str = ""
    current_price: float = 0.0

    @property
    def has_data(self) -> bool:
        """Return True when a candle frame is loaded."""
        return self.df is not None and not self.df.empty


@st.cache_data(ttl=60, show_spinner=False)
def load_historical_data(
    symbol: str,
    timeframe: str,
    candle_count: int = 500,
    root_dir: str | None = None,
) -> pd.DataFrame:
    """Load (and validate) historical candles for a symbol/timeframe.

    Falls back to the parquet data store when MT5 is unavailable. The
    dashboard never downloads data on every rerun - callers should wrap this
    in ``st.cache_data``.
    """
    # Try to load from the data store first (fastest, no MT5 needed).
    frame = load_candles(
        symbol=symbol,
        timeframe=timeframe,
        date="latest",
        root_dir=root_dir,
    )
    if frame is not None and not frame.empty:
        return validate_candles(frame).tail(candle_count)

# Last resort: deterministic synthetic demo candles so the dashboard
    # always has something to render (no MT5 / data store required).
    #
    # NOTE: we deliberately avoid attempting an MT5 download here. The
    # dashboard must be non-blocking and deterministic; a live download
    # would ``mt5.initialize()`` and hang when no terminal is running. Use
    # ``main.py`` to populate the data store with real candles instead.
    return _synthetic_candles(symbol=symbol, timeframe=timeframe, count=candle_count)


def _synthetic_candles(
    symbol: str,
    timeframe: str,
    count: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """Build a deterministic, validator-compliant OHLCV frame for demo use.

    The walk is a seeded random walk with realistic OHLC bounds so the full
    SMC pipeline (structure, liquidity, CHoCH/BOS, OB, FVG, strategy) can
    produce output without a live data source.

    Args:
        symbol: Symbol label (unused for generation, kept for parity).
        timeframe: Timeframe label used to infer the candle interval.
        count: Number of candles to generate.
        seed: Random seed for a reproducible demo series.

    Returns:
        A validated OHLCV DataFrame.
    """
    interval_minutes = _timeframe_minutes(timeframe)
    end = datetime.now().replace(second=0, microsecond=0)
    dates = pd.date_range(end=end, periods=count, freq=f"{interval_minutes}min")

    rng = np.random.default_rng(seed)
    base = 2500.0 if "XAU" in symbol.upper() else 1.10
    noise = rng.normal(0.0, 1.0, size=count)
    drift = np.linspace(0.0, 20.0, count) if "XAU" in symbol.upper() else np.linspace(0.0, 0.02, count)
    closes = base + drift + np.cumsum(noise) * (0.5 if "XAU" in symbol.upper() else 0.001)

    opens = np.empty(count)
    opens[0] = closes[0]
    opens[1:] = closes[:-1]

    spread = 0.4 if "XAU" in symbol.upper() else 0.0002
    highs = np.maximum(opens, closes) + rng.uniform(0.1, spread, size=count)
    lows = np.minimum(opens, closes) - rng.uniform(0.1, spread, size=count)
    volumes = rng.integers(100, 5000, size=count).astype(float)

    frame = pd.DataFrame(
        {
            "date": dates,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }
    )
    return validate_candles(frame)


def _timeframe_minutes(timeframe: str) -> int:
    """Return the number of minutes for a timeframe label (default 15)."""
    mapping = {
        "M1": 1, "M5": 5, "M15": 15, "M30": 30,
        "H1": 60, "H4": 240, "D1": 1440,
    }
    return mapping.get(str(timeframe).upper(), 15)


def load_analysis(config: DashboardConfig) -> AnalysisBundle:
    """Load data and run the full analysis pipeline for a config.

    Convenience wrapper used by the dashboard app: loads historical candles
    for the configured symbol/timeframe, then runs :func:`analyze_symbol`.

    Args:
        config: The dashboard configuration (symbol, timeframe, risk, etc.).

    Returns:
        A fully populated :class:`AnalysisBundle`.
    """
    return _load_analysis_cached(
        config.symbol,
        config.timeframe,
        config.candle_count,
        config.balance,
        config.risk_percent,
        config.instrument_joint,
    )


@st.cache_resource(ttl=60, show_spinner=False)
def _load_analysis_cached(
    symbol: str,
    timeframe: str,
    candle_count: int,
    balance: float,
    risk_percent: float,
    instrument_joint: float,
) -> AnalysisBundle:
    """Cache an unchanged analysis bundle for the current dashboard inputs."""
    config = DashboardConfig(
        symbol=symbol,
        timeframe=timeframe,
        candle_count=candle_count,
        balance=balance,
        risk_percent=risk_percent,
        instrument_joint=instrument_joint,
    )
    df = load_historical_data(symbol, timeframe, candle_count)
    return analyze_symbol(df, symbol, timeframe, config)


def analyze_symbol(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    config: DashboardConfig,
) -> AnalysisBundle:
    """Run the full analysis pipeline and return an :class:`AnalysisBundle`.

    Args:
        df: OHLCV candle DataFrame.
        symbol: Trading symbol.
        timeframe: Timeframe label.
        config: The dashboard configuration (risk %, balance, etc.).

    Returns:
        A fully populated :class:`AnalysisBundle`.
    """
    if df is None or df.empty:
        return AnalysisBundle(symbol=symbol, timeframe=timeframe)

    # 1) Market structure (Week 2).
    structure = MarketStructureAnalyzer(lookback=2).analyze(df)

    # 2) Liquidity (Week 3).
    liquidity = LiquidityAnalyzer(
        symbol=symbol, timeframe=timeframe
    ).analyze(df)

    # 3) CHoCH / BOS (Week 4).
    events = SmartMoneyAnalyzer(timeframe=timeframe).analyze(
        candles=df, structure=structure, liquidity=liquidity
    )

    # 4) Order blocks (Week 5).
    order_blocks = OrderBlockEngine(timeframe=timeframe).analyze(
        df=df, structure=structure, liquidity=liquidity, events=events
    )

    # 5) Fair value gaps / imbalances (Week 6).
    imbalances = ImbalanceEngine(timeframe=timeframe).analyze(
        df=df, structure=structure, liquidity=liquidity, events=events,
        order_blocks=order_blocks,
    )

    # 6) Strategy confluence (Week 7).
    strategy = StrategyAnalyzer(
        timeframe=timeframe,
        filters=StrategyFilters(
            min_confluence=config.min_confluence,
            min_displacement=config.min_displacement,
            premium_discount_match=config.premium_discount_match,
            min_risk_reward=config.min_rr,
            require_liquidity_sweep=config.require_liquidity_sweep,
        ),
    ).analyze(
        df=df,
        structure=structure,
        liquidity=liquidity,
        events=events,
        order_blocks=order_blocks,
        imbalances=imbalances,
    )

    # 7) Risk / trade plan (Week 8).
    account = Account(balance=config.balance)
    try:
        risk = RiskAnalyzer(
            symbol=symbol,
            timeframe=timeframe,
            default_risk_percent=config.risk_percent,
            instrument_joint=config.instrument_joint,
        )
        best = strategy.best if strategy is not None else None
        plan = risk.plan(best, account=account) if best is not None else None
    except Exception:
        plan = None

    current_price = float(df["close"].iloc[-1]) if len(df) else 0.0

    return AnalysisBundle(
        df=df,
        structure=structure,
        liquidity=liquidity,
        events=events,
        order_blocks=order_blocks,
        imbalances=imbalances,
        strategy=strategy,
        plan=plan,
        account=account,
        symbol=symbol,
        timeframe=timeframe,
        current_price=current_price,
    )


def run_backtest(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    config: DashboardConfig,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> BacktestResult:
    """Run a backtest over the loaded candles using the strategy executor.

    The executor replays each candle **sequentially** (no look-ahead) and
    submits the strategy's best setup as an order. Risk-managed volume is
    computed by the engine from ``risk_per_trade`` + stop distance - the
    dashboard only supplies the setup geometry.
    """
    frame = df
    if start_date is not None and end_date is not None:
        frame = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    point = float(frame.attrs.get("point", 0.0) or 0.0)
    contract_size = float(frame.attrs.get("contract_size", 1.0) or 1.0)
    observed_spread = (
        float(frame["spread"].median()) * point
        if point > 0 and "spread" in frame and not frame["spread"].empty
        else 0.0
    )

    engine = BacktestEngine(
        config=BacktestConfig(
            initial_balance=config.balance,
            commission=7.0,
            slippage=point * 0.5 if point > 0 else 0.0,
            spread=observed_spread,
            # Dashboard/user settings express risk as a percentage (1 = 1%),
            # while BacktestConfig deliberately stores a fraction.
            risk_per_trade=config.risk_percent / 100.0,
            symbol=symbol,
            timeframe=timeframe,
            contract_size=contract_size,
        )
    )

    seen_setups: set[tuple] = set()
    warmup = min(100, max(20, len(frame) // 5))
    lookback = min(500, len(frame))

    def executor(row):
        index = int(row.Index)
        if index < warmup:
            return []
        # Orders evaluated before the current bar may only use information
        # through the previous closed candle. This makes the earliest
        # execution the following bar and avoids same-bar high/low leakage.
        history = frame.iloc[max(0, index - lookback):index]
        setup = _best_setup_for_frame(history, symbol, timeframe, config)
        if setup is None or not setup.is_valid:
            return []
        if setup.confluence_score < config.min_confluence:
            return []
        if setup.risk_reward_ratio < config.min_rr:
            return []

        # Zone UUIDs are rebuilt on every analysis pass. Use stable market
        # geometry to prevent the same unchanged setup from firing each bar.
        setup_key = (
            str(setup.direction),
            round(float(setup.entry_price), 8),
            round(float(setup.stop_loss), 8),
            round(float(setup.target), 8),
        )
        if setup_key in seen_setups:
            return []
        seen_setups.add(setup_key)
        return [
            (
                setup.entry_price,
                setup.stop_loss,
                setup.target,
                None,  # engine sizes from configured fractional risk
                setup.confluence_score,
                setup.reason,
                setup.direction.value if hasattr(setup.direction, "value") else str(setup.direction),
            )
        ]

    return engine.run(frame, executor=executor)


def _best_setup_for_frame(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    config: DashboardConfig,
):
    """Return the best tradeable setup for the frame (or None)."""
    if df is None or df.empty:
        return None
    bundle = analyze_symbol(df, symbol, timeframe, config)
    if bundle.strategy is None:
        return None
    return bundle.strategy.best


__all__ = [
    "AnalysisBundle",
    "load_historical_data",
    "load_analysis",
    "analyze_symbol",
    "run_backtest",
    "get_paper_broker",
]
