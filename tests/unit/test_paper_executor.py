from tests.unit.paper_helpers import executor, plan


def test_executor_submits_ready_trade_plan(tmp_path):
    result = executor(tmp_path).execute(plan(), "signal-1")
    assert result.position is not None
    assert result.order.status.value == "FILLED"
