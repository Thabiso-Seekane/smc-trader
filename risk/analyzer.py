"""Risk Analyzer — the public façade for the Week 8 Risk Engine.

``RiskAnalyzer.plan(trade_zone, account, ...)`` consumes a Week 7
:class:`strategy.models.TradeZone` (or a bare geometry) and produces a
complete :class:`risk.models.TradePlan` with position sizing, stop/target
placement, R:R validation, risk metrics, and projected P&L.

The execution layer never recalculates stops or lot sizes — it reads the
plan and places orders.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from risk.account import Account
from risk.enums import PlanStatus, PositionSizingMethod, RiskStatus
from risk.models import PositionSize, RiskMetrics, TradePlan
from risk.position_size import PositionSizer
from risk.risk_reward import RiskRewardAnalyzer
from risk.stop_loss import StopLossPlacer
from risk.take_profit import TakeProfitPlacer
from risk.validator import RiskValidator


@dataclass(slots=True)
class RiskAnalyzer:
    """High-level orchestrator for trade-plan generation.

    Attributes:
        sizer: The :class:`PositionSizer`.
        stop_placer: The :class:`StopLossPlacer`.
        target_placer: The :class:`TakeProfitPlacer`.
        rr: The :class:`RiskRewardAnalyzer`.
        validator: The :class:`RiskValidator`.
        symbol: Trading symbol attached to plans.
        timeframe: Timeframe label attached to plans.
        default_risk_percent: Default per-trade risk % of balance.
        instrument_joint: Price of one unit (for lot conversion).
    """

    sizer: PositionSizer = field(default_factory=PositionSizer)
    stop_placer: StopLossPlacer = field(default_factory=StopLossPlacer)
    target_placer: TakeProfitPlacer = field(default_factory=TakeProfitPlacer)
    rr: RiskRewardAnalyzer = field(default_factory=RiskRewardAnalyzer)
    validator: RiskValidator = field(default_factory=RiskValidator)
    symbol: str = "XAUUSD"
    timeframe: str = ""
    default_risk_percent: float = 1.0
    instrument_joint: float = 10.0

    def plan(
        self,
        trade_zone=None,
        *,
        account: Account | None = None,
        direction: str | None = None,
        entry: float | None = None,
        stop: float | None = None,
        target: float | None = None,
        structural_stop: float | None = None,
        structural_target: float | None = None,
        symbol: str | None = None,
        risk_percent: float | None = None,
        atr: float = 0.0,
        expiration=None,
        confidence: float = 0.0,
    ) -> TradePlan:
        """Build a :class:`TradePlan` from a trade zone or explicit geometry.

        Args:
            trade_zone: A Week 7 ``strategy.models.TradeZone`` (optional).
                When provided, direction/entry/stop/target/confidence are
                read from it.
            account: Optional :class:`Account` used for sizing and validation.
            direction: Override direction ("BUY"/"SELL").
            entry: Override entry price.
            stop: Override stop-loss price.
            target: Override take-profit price.
            structural_stop: Structural stop for the stop placer.
            structural_target: Structural target for the target placer.
            symbol: Trading symbol override.
            risk_percent: Per-trade risk % override.
            atr: Current ATR value (for ATR-based stops).
            expiration: Optional plan expiration timestamp.
            confidence: Confluence confidence override.

        Returns:
            A validated :class:`TradePlan`.
        """
        # --- resolve geometry from trade_zone -----------------
        zone_dir, zone_entry, zone_stop, zone_target, zone_conf = self._from_zone(
            trade_zone
        )
        direction = (direction or zone_dir or "BUY").upper()
        entry = entry if entry is not None else zone_entry
        stop = stop if stop is not None else zone_stop
        target = target if target is not None else zone_target
        confidence = confidence or zone_conf

# --- place stop / target (only when not explicitly given) -----
        if stop is None:
            stop = self.stop_placer.place(
                direction=direction,
                entry=entry,
                structural_stop=structural_stop,
                atr=atr,
            )
        if target is None:
            target = self.target_placer.place(
                direction=direction,
                entry=entry,
                stop=stop,
                structural_target=structural_target,
            )

        # Guard: without a usable entry we cannot build a plan.
        if entry is None:
            entry = 0.0

        risk_pct = risk_percent if risk_percent is not None else self.default_risk_percent
        bal = account.balance if account is not None else 0.0
        risk_amount = bal * (risk_pct / 100.0) if bal > 0 else 0.0

        stop_distance = abs(entry - stop)
        position = self.sizer.size(
            account=account,
            risk_percent=risk_pct,
            stop_distance=stop_distance,
        ) if account is not None else PositionSize(
            lots=0.0,
            method=PositionSizingMethod.FIXED_FRACTIONAL,
            risk_amount=risk_amount,
            account_at_risk_pct=risk_pct,
        )

        ratio = self.rr.analyze(entry=entry, stop=stop, target=target)

        risk_metrics = RiskMetrics(
            account_balance=bal,
            risk_percent=risk_pct,
            risk_amount=position.risk_amount,
            position_size=position,
            status=account.status if account is not None else RiskStatus.WITHIN_LIMIT,
        )

        plan = TradePlan(
            symbol=symbol or self.symbol,
            direction=direction,
            entry_price=entry,
            instrument_joint=self.instrument_joint,
            stop_loss=stop,
            take_profit=target,
            risk_reward=ratio,
            expiration=expiration,
            timeframe=self.timeframe,
            position_size=position,
            risk=stop_distance,
            reward=abs(target - entry),
            confidence=confidence,
            risk_metrics=risk_metrics,
        )

        return self.validator.apply(plan, account)

    def _from_zone(self, zone):
        """Extract geometry from a Week 7 TradeZone (or None defaults)."""
        if zone is None:
            return None, None, None, None, 0.0
        direction = getattr(zone, "direction", None)
        dir_str = getattr(direction, "value", direction) if direction is not None else None
        entry = getattr(zone, "entry_price", None)
        stop = getattr(zone, "stop_loss", None)
        target = getattr(zone, "target", None)
        conf = getattr(zone, "confluence_score", 0.0) or 0.0
        return dir_str, entry, stop, target, conf


__all__ = ["RiskAnalyzer"]
