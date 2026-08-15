from datetime import datetime

from backtesting.enums import Direction, TradeResultType
from backtesting.models import BacktestResult, Trade
from backtesting.readiness import ReadinessCriteria, assess_readiness, walk_forward_slices


def result(pnl_values, drawdown=0.05):
    trades = [
        Trade(direction=Direction.BUY, profit_loss=pnl, result=TradeResultType.WIN if pnl > 0 else TradeResultType.LOSS,
              entry_time=datetime.now(), exit_time=datetime.now())
        for pnl in pnl_values
    ]
    pnl = sum(pnl_values)
    return BacktestResult(initial_balance=10_000, final_balance=10_000 + pnl, total_return=pnl / 10_000,
                          max_drawdown=drawdown, trades=trades, total_trades=len(trades))


def test_readiness_passes_only_stable_out_of_sample_evidence():
    folds = [result([20] * 15 + [-10] * 5) for _ in range(5)]
    report = assess_readiness(folds)
    assert report.passed
    assert report.trades == 100


def test_readiness_fails_sparse_or_losing_results():
    report = assess_readiness([result([-100, 20])])
    assert not report.passed
    assert report.failures


def test_walk_forward_slices_separate_train_and_test():
    splits = list(walk_forward_slices(100, train_size=50, test_size=10))
    assert len(splits) == 5
    assert splits[0] == (slice(0, 50), slice(50, 60))
