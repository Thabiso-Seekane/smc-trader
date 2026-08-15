from execution.enums import OrderSide
from execution.models import PaperOrder
from tests.unit.paper_helpers import broker


def test_paper_broker_fills_and_tracks_virtual_position(tmp_path):
    paper = broker(tmp_path)
    position = paper.submit_order(PaperOrder("SMC-1", "signal-1", "smc_v1", 1, "XAUUSD", "M15", OrderSide.BUY, 1, 100, 90, 130))
    assert position.is_open
    assert position.entry_price == 100.1
    assert len(paper.get_positions()) == 1
