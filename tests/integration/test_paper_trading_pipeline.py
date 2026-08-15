"""End-to-end paper path: closed candle -> plan -> virtual TP -> persisted journal."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pandas as pd

from execution.models import Tick
from execution.realtime import RealTimePaperEngine
from tests.unit.paper_helpers import broker, plan
from execution.paper_executor import PaperExecutor


def test_closed_candle_pipeline_opens_and_closes_paper_trade(tmp_path):
    paper = broker(tmp_path)
    engine = RealTimePaperEngine(
        broker=paper,
        executor=PaperExecutor(paper),
        analyze=lambda frame: SimpleNamespace(best=SimpleNamespace(id="setup-1"), decision=SimpleNamespace(reason="SMC setup")),
        plan=lambda analysis: plan(),
    )
    now = datetime.now(timezone.utc)
    candles = pd.DataFrame({"date": [now - timedelta(minutes=30), now - timedelta(minutes=15), now], "open": [1, 1, 1], "high": [1, 1, 1], "low": [1, 1, 1], "close": [1, 1, 1]})
    result = engine.on_market("XAUUSD", "M15", candles, Tick("XAUUSD", 100, 100.1, now))
    assert result.position is not None
    paper.set_tick(Tick("XAUUSD", 131, 131.1, now + timedelta(minutes=1)))
    assert len(paper.get_closed_positions()) == 1
    assert len(paper.get_fills()) == 1
    assert len(paper.get_trades()) == 1
    assert paper.get_trades()[0].trade_id == paper.get_fills()[0].trade_id
    assert paper.get_account().balance > 10_000
