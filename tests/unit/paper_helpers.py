"""Shared fixtures for paper-execution tests."""

from execution.models import SymbolInfo, Tick
from execution.paper_broker import PaperBroker
from execution.persistence import PaperStore
from execution.paper_executor import PaperExecutor
from risk.models import PositionSize, RiskMetrics, TradePlan


def broker(tmp_path, bid=100.0, ask=100.1):
    result = PaperBroker(PaperStore(tmp_path / "paper.db"), initial_balance=10_000)
    result.set_symbol(SymbolInfo("XAUUSD", point=0.1, contract_size=10))
    result.set_tick(Tick("XAUUSD", bid=bid, ask=ask))
    return result


def plan() -> TradePlan:
    return TradePlan(
        symbol="XAUUSD", timeframe="M15", direction="BUY", entry_price=100.1,
        stop_loss=90.0, take_profit=130.0, risk_reward=3.0, confidence=92,
        position_size=PositionSize(lots=1.0, risk_amount=100.0),
        risk_metrics=RiskMetrics(risk_amount=100.0), note="Bullish SMC confluence",
    )


def executor(tmp_path):
    return PaperExecutor(broker(tmp_path))
