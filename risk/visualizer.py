"""Visualizer for the Week 8 Risk Engine.

Renders a :class:`risk.models.TradePlan` as a simple text summary and (when
pandas/plotly are available) an entry/stop/target overlay chart. This is a
debugging aid, not used by the execution layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from risk.models import TradePlan


@dataclass(slots=True)
class RiskVisualizer:
    """Render a :class:`TradePlan` summary."""

    def summarize(self, plan: TradePlan) -> str:
        """Return a compact, human-readable summary of a trade plan."""
        position = plan.position_size
        lines = [
            f"Symbol       : {plan.symbol}",
            f"Direction    : {plan.direction}",
            f"Entry        : {plan.entry_price:.5f}",
            f"Stop Loss    : {plan.stop_loss:.5f}",
            f"Take Profit  : {plan.take_profit:.5f}",
            f"Risk / Reward: {plan.risk_reward:.2f}R",
            f"Lots         : {position.lots:.2f}",
            f"Risk Amount  : {position.risk_amount:.2f}",
            f"Risk % Bal   : {position.account_at_risk_pct:.2f}%",
            f"Confidence   : {plan.confidence:.0f}",
            f"Status       : {plan.status.value}",
        ]
        if plan.note:
            lines.append(f"Note         : {plan.note}")
        return "\n".join(lines)

    def to_text(self, plan: TradePlan) -> str:
        """Alias for :meth:`summarize`."""
        return self.summarize(plan)


__all__ = ["RiskVisualizer"]
