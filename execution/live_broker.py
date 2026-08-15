"""Fail-closed MT5 live broker. Disabled unless every independent gate passes."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor

from backtesting.readiness import ReadinessReport


class LiveTradingBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LiveOrderResult:
    request: dict
    check: object
    result: object


class LiveMT5Broker:
    """Submit checked market orders only after explicit live authorization."""

    ACKNOWLEDGEMENT = "I_ACCEPT_LIVE_TRADING_RISK"

    def __init__(self, client, settings, readiness: ReadinessReport) -> None:
        self.client = client
        self.settings = settings
        self.readiness = readiness

    def submit(self, plan) -> LiveOrderResult:
        self._authorize()
        mt5 = self.client._require_mt5()
        account = self.client.account_info()
        terminal = self.client.terminal_info()
        if not getattr(account, "trade_allowed", False) or not getattr(terminal, "trade_allowed", False):
            raise LiveTradingBlocked("MT5 account or terminal does not allow trading")

        info = self.client.symbol_info(plan.symbol)
        tick = self.client.get_tick(plan.symbol)
        if info is None or tick is None:
            raise LiveTradingBlocked("symbol metadata or tick is unavailable")
        spread_points = (tick.ask - tick.bid) / info.point if info.point > 0 else float("inf")
        if spread_points > self.settings.max_spread_points:
            raise LiveTradingBlocked("spread exceeds configured maximum")

        volume = self._normalize_volume(plan.position_size.lots, info)
        side = mt5.ORDER_TYPE_BUY if plan.is_buy else mt5.ORDER_TYPE_SELL
        price = tick.ask if plan.is_buy else tick.bid
        estimated_loss = self.client.order_calc_profit(side, plan.symbol, volume, price, plan.stop_loss)
        max_loss = float(account.balance) * self.settings.risk_percent / 100.0
        if estimated_loss is None or abs(min(float(estimated_loss), 0.0)) > max_loss * 1.01:
            raise LiveTradingBlocked("broker-calculated stop loss exceeds risk budget")
        margin = self.client.order_calc_margin(side, plan.symbol, volume, price)
        if margin is None or float(margin) > float(account.margin_free) * self.settings.live_max_margin_fraction:
            raise LiveTradingBlocked("required margin exceeds configured free-margin limit")

        request = {
            "action": mt5.TRADE_ACTION_DEAL, "symbol": plan.symbol, "volume": volume,
            "type": side, "price": price, "sl": plan.stop_loss, "tp": plan.take_profit,
            "deviation": self.settings.live_max_deviation_points,
            "magic": self.settings.execution_magic_number,
            "comment": self.settings.live_order_comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": getattr(info, "filling_mode", mt5.ORDER_FILLING_RETURN),
        }
        check = self.client.order_check(request)
        if check is None or getattr(check, "retcode", -1) != 0:
            raise LiveTradingBlocked(f"MT5 order_check rejected request: {getattr(check, 'comment', 'unknown')}")
        result = self.client.order_send(request)
        accepted = {mt5.TRADE_RETCODE_DONE, getattr(mt5, "TRADE_RETCODE_PLACED", mt5.TRADE_RETCODE_DONE)}
        if result is None or getattr(result, "retcode", -1) not in accepted:
            raise LiveTradingBlocked(f"MT5 order_send failed: {getattr(result, 'comment', 'unknown')}")
        return LiveOrderResult(request=request, check=check, result=result)

    def _authorize(self) -> None:
        if not self.settings.live_trading_authorized:
            raise LiveTradingBlocked("live mode and enable flag are both required")
        if self.settings.live_risk_acknowledgement != self.ACKNOWLEDGEMENT:
            raise LiveTradingBlocked("explicit live-risk acknowledgement is missing")
        if not self.readiness.passed:
            raise LiveTradingBlocked("out-of-sample profitability readiness has not passed")

    @staticmethod
    def _normalize_volume(volume: float, info) -> float:
        step = max(float(getattr(info, "volume_step", 0.01)), 1e-8)
        minimum = float(getattr(info, "volume_min", step))
        maximum = float(getattr(info, "volume_max", volume))
        normalized = floor(float(volume) / step) * step
        if normalized < minimum or normalized > maximum:
            raise LiveTradingBlocked("volume is outside broker limits")
        return round(normalized, 8)


__all__ = ["LiveMT5Broker", "LiveOrderResult", "LiveTradingBlocked"]
