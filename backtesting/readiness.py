"""Evidence-based profitability and live-readiness gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from backtesting.models import BacktestResult


@dataclass(frozen=True, slots=True)
class ReadinessCriteria:
    min_folds: int = 5
    min_trades: int = 100
    min_profit_factor: float = 1.20
    min_total_return: float = 0.0
    max_drawdown: float = 0.10
    min_profitable_fold_ratio: float = 0.60
    min_expectancy: float = 0.0


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    passed: bool
    folds: int
    trades: int
    total_return: float
    profit_factor: float
    max_drawdown: float
    profitable_fold_ratio: float
    expectancy: float
    failures: tuple[str, ...] = field(default_factory=tuple)


def assess_readiness(
    out_of_sample_results: Iterable[BacktestResult],
    criteria: ReadinessCriteria | None = None,
) -> ReadinessReport:
    """Assess only out-of-sample results; never claim guaranteed profit."""
    criteria = criteria or ReadinessCriteria()
    results = list(out_of_sample_results)
    trades = [trade for result in results for trade in result.trades]
    gross_profit = sum(t.profit_loss for t in trades if t.profit_loss > 0)
    gross_loss = abs(sum(t.profit_loss for t in trades if t.profit_loss < 0))
    profit_factor = gross_profit / gross_loss if gross_loss else (float("inf") if gross_profit else 0.0)
    initial = sum(result.initial_balance for result in results)
    pnl = sum(result.final_balance - result.initial_balance for result in results)
    total_return = pnl / initial if initial else 0.0
    expectancy = sum(t.profit_loss for t in trades) / len(trades) if trades else 0.0
    profitable = sum(result.total_return > 0 for result in results)
    profitable_ratio = profitable / len(results) if results else 0.0
    max_drawdown = max((result.max_drawdown for result in results), default=0.0)

    failures: list[str] = []
    checks = (
        (len(results) >= criteria.min_folds, f"requires at least {criteria.min_folds} out-of-sample folds"),
        (len(trades) >= criteria.min_trades, f"requires at least {criteria.min_trades} closed trades"),
        (profit_factor >= criteria.min_profit_factor, f"profit factor {profit_factor:.2f} below {criteria.min_profit_factor:.2f}"),
        (total_return > criteria.min_total_return, f"aggregate return {total_return:.2%} is not positive"),
        (max_drawdown <= criteria.max_drawdown, f"drawdown {max_drawdown:.2%} exceeds {criteria.max_drawdown:.2%}"),
        (profitable_ratio >= criteria.min_profitable_fold_ratio, f"profitable-fold ratio {profitable_ratio:.0%} below {criteria.min_profitable_fold_ratio:.0%}"),
        (expectancy > criteria.min_expectancy, f"expectancy {expectancy:.2f} is not positive"),
    )
    failures.extend(message for passed, message in checks if not passed)
    return ReadinessReport(
        passed=not failures, folds=len(results), trades=len(trades),
        total_return=total_return, profit_factor=profit_factor,
        max_drawdown=max_drawdown, profitable_fold_ratio=profitable_ratio,
        expectancy=expectancy, failures=tuple(failures),
    )


def walk_forward_slices(length: int, train_size: int, test_size: int, step: int | None = None):
    """Yield non-overlapping test slices preceded by a training window."""
    if min(length, train_size, test_size) <= 0:
        return
    step = step or test_size
    end_train = train_size
    while end_train + test_size <= length:
        yield slice(end_train - train_size, end_train), slice(end_train, end_train + test_size)
        end_train += step


__all__ = ["ReadinessCriteria", "ReadinessReport", "assess_readiness", "walk_forward_slices"]
