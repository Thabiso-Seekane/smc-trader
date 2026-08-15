from execution.paper_executor import PaperExecutionConfig, PaperExecutor
from tests.unit.paper_helpers import broker, plan
from datetime import datetime, timezone

from execution.models import Tick


def test_daily_loss_limit_rejects_new_trade(tmp_path):
    paper = broker(tmp_path)
    paper.account.daily_realized_pnl = -300
    result = PaperExecutor(paper, PaperExecutionConfig(max_daily_loss_percent=3)).execute(plan(), "loss-limit")
    assert result.position is None
    assert result.order.rejection_reason == "Maximum daily loss reached"


def test_daily_pnl_resets_on_new_utc_day(tmp_path):
    paper = broker(tmp_path)
    paper.account.daily_realized_pnl = -250.0
    paper.account.daily_pnl_date = "2026-01-01"

    paper.set_tick(Tick("XAUUSD", 100, 100.1, datetime(2026, 1, 2, tzinfo=timezone.utc)))

    assert paper.account.daily_realized_pnl == 0.0
    assert paper.account.daily_pnl_date == "2026-01-02"
