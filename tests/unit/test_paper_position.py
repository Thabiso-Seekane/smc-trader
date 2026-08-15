import pytest

from execution.models import Tick
from tests.unit.paper_helpers import broker
from execution.enums import OrderSide
from execution.models import PaperOrder


def test_take_profit_closes_position_and_updates_balance(tmp_path):
    paper = broker(tmp_path)
    position = paper.submit_order(PaperOrder("SMC-1", "signal-1", "smc_v1", 1, "XAUUSD", "M15", OrderSide.BUY, 1, 100, 90, 110))
    paper.set_tick(Tick("XAUUSD", bid=111, ask=111.1))
    closed = paper.get_closed_positions()[0]
    assert closed.trade_id == position.trade_id
    assert closed.realized_pnl == pytest.approx(99.0)
    assert paper.get_account().balance == pytest.approx(10099.0)
