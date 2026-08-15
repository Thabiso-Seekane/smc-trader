from execution.enums import ExecutionStatus
from tests.unit.paper_helpers import executor, plan


def test_duplicate_signal_is_rejected(tmp_path):
    service = executor(tmp_path)
    assert service.execute(plan(), "same").position is not None
    duplicate = service.execute(plan(), "same")
    assert duplicate.position is None
    assert duplicate.order.status == ExecutionStatus.REJECTED
    assert duplicate.order.rejection_reason == "Duplicate signal"
