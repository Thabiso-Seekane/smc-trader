"""Risk validation for the Week 8 Risk Engine.

This module answers: *"Should this trade be rejected because of risk?"*

It applies a series of independent gates over the plan and the account and
rejects the trade when any gate fails. The execution layer never re-checks
these — a REJECTED plan is simply not executed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from risk.account import Account
from risk.enums import PlanStatus, RiskStatus
from risk.models import RiskMetrics, TradePlan


@dataclass(slots=True)
class RiskValidator:
    """Validate a trade plan against risk rules.

    Attributes:
        min_rr: Minimum acceptable reward-to-risk ratio.
        max_risk_percent: Maximum per-trade risk as % of balance.
        reject_when_account_blocked: When True, reject if the account
            status is anything other than WITHIN_LIMIT.
    """

    min_rr: float = 2.0
    max_risk_percent: float = 5.0
    reject_when_account_blocked: bool = True

    def validate(
        self,
        plan: TradePlan,
        account: Account | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate a plan; return (valid, reasons).

        Args:
            plan: The :class:`TradePlan` to validate.
            account: Optional :class:`Account`. When provided, account-level
                risk gates are also applied.

        Returns:
            A tuple of (``valid``, ``reasons``) where ``reasons`` lists the
            human-readable violations (empty when valid).
        """
        reasons: list[str] = []

        # Geometry / R:R gate.
        if plan.risk_distance <= 0:
            reasons.append("Risk distance is zero — stop is invalid.")
        if plan.reward_distance <= 0:
            reasons.append("Reward distance is zero — target is invalid.")
        if plan.risk_reward_ratio < self.min_rr:
            reasons.append(
                f"R:R {plan.risk_reward_ratio:.2f} below minimum {self.min_rr:.2f}."
            )

        # Per-trade risk gate.
        if plan.risk_metrics.risk_percent > self.max_risk_percent:
            reasons.append(
                f"Per-trade risk {plan.risk_metrics.risk_percent:.1f}% "
                f"above maximum {self.max_risk_percent:.1f}%."
            )

        # Position-size gate.
        if not plan.position_size.is_valid:
            reasons.append("Position size is zero — lot size could not be computed.")

        # Account-level gates.
        if account is not None:
            status = account.status
            if self.reject_when_account_blocked and status != RiskStatus.WITHIN_LIMIT:
                reasons.append(f"Account status is {status.value}.")

        return (len(reasons) == 0, reasons)

    def apply(self, plan: TradePlan, account: Account | None = None) -> TradePlan:
        """Validate a plan and set its status accordingly (mutates plan)."""
        valid, reasons = self.validate(plan, account)
        if not valid:
            plan.status = PlanStatus.REJECTED
            plan.note = "; ".join(reasons)
        return plan


__all__ = ["RiskValidator"]
