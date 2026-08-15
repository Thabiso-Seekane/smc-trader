from tests.unit.paper_helpers import executor, broker, plan
from datetime import datetime, timezone

from execution.models import Tick


def test_open_position_is_restored_from_sqlite(tmp_path):
    first = executor(tmp_path)
    first.execute(plan(), "recover")
    restored = broker(tmp_path)
    assert len(restored.get_positions()) == 1
    assert restored.get_positions()[0].signal_id == "recover"


def test_fill_and_completed_trade_are_restored_from_sqlite(tmp_path):
    first = executor(tmp_path)
    result = first.execute(plan(), "completed")
    paper = first.broker
    paper.set_tick(Tick("XAUUSD", 131, 131.1, datetime.now(timezone.utc)))

    restored = broker(tmp_path)
    assert result.position is not None
    assert len(restored.get_fills()) == 1
    assert len(restored.get_trades()) == 1
    assert restored.get_trades()[0].trade_id == result.position.trade_id
