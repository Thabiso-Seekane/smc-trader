from execution.paper_executor import PaperExecutionConfig, PaperExecutor
from tests.unit.paper_helpers import broker, plan


def test_spread_limit_rejects_new_trade(tmp_path):
    paper = broker(tmp_path, bid=100, ask=105)
    result = PaperExecutor(paper, PaperExecutionConfig(max_spread_points=30)).execute(plan(), "wide-spread")
    assert result.position is None
    assert result.order.rejection_reason == "Spread too high or unavailable"
