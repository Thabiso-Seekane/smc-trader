"""Dashboard configuration for the Week 10 Streamlit app.

The dashboard is a *presentation layer* only. It reads configuration from
the project settings and exposes the selectable options (symbol, timeframe,
risk, etc.). It never contains trading logic — it renders the results of the
analysis / strategy / risk / backtesting engines.

Note: this module is intentionally named ``settings`` (not ``config``) to
avoid shadowing the top-level ``config`` package that the SMC pipeline
imports — a name collision would make ``from config.settings import settings``
fail when the dashboard directory is on ``sys.path``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from config.settings import settings

# Available instruments / timeframes surfaced in the UI.
SYMBOLS: list[str] = ["XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD"]
TIMEFRAMES: list[str] = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]

# Default accounting / risk posture.
DEFAULT_BALANCE: float = 10_000.0
DEFAULT_RISK_PERCENT: float = 1.0
DEFAULT_MIN_CONFLUENCE: float = 70.0
DEFAULT_MIN_RR: float = 2.0
DEFAULT_INSTRUMENT_JOINT: float = 10.0


@dataclass(slots=True)
class DashboardConfig:
    """Runtime configuration editable from the UI (no source changes)."""

    symbol: str = field(default_factory=lambda: settings.default_symbol)
    timeframe: str = field(default_factory=lambda: settings.default_timeframe)
    balance: float = DEFAULT_BALANCE
    risk_percent: float = field(default_factory=lambda: settings.risk_percent)
    min_confluence: float = DEFAULT_MIN_CONFLUENCE
    min_rr: float = DEFAULT_MIN_RR
    min_displacement: float = 0.0
    require_liquidity_sweep: bool = False
    premium_discount_match: bool = False
    instrument_joint: float = DEFAULT_INSTRUMENT_JOINT
    candle_count: int = field(
        # The dashboard is an interactive presentation surface. Keeping a
        # bounded window makes its first render responsive while callers can
        # still use the data pipeline to prepare deeper history elsewhere.
        default_factory=lambda: min(settings.candles_to_download, 500)
    )

    @property
    def is_read_only(self) -> bool:
        """The dashboard is read-only with respect to execution (Week 11+)."""
        return True


__all__ = [
    "SYMBOLS",
    "TIMEFRAMES",
    "DEFAULT_BALANCE",
    "DEFAULT_RISK_PERCENT",
    "DEFAULT_MIN_CONFLUENCE",
    "DEFAULT_MIN_RR",
    "DEFAULT_INSTRUMENT_JOINT",
    "DashboardConfig",
]
