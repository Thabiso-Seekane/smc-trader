"""Unit tests for the Week 8 TakeProfitPlacer."""

from risk.enums import TakeProfitMode
from risk.take_profit import TakeProfitPlacer


def test_rr_multiple_buy():
    placer = TakeProfitPlacer(mode=TakeProfitMode.RR_MULTIPLE, rr_multiple=2.0)
    target = placer.place(direction="BUY", entry=1.20, stop=1.10)
    assert round(target, 4) == 1.40


def test_rr_multiple_sell():
    placer = TakeProfitPlacer(mode=TakeProfitMode.RR_MULTIPLE, rr_multiple=2.0)
    target = placer.place(direction="SELL", entry=1.20, stop=1.30)
    assert round(target, 4) == 1.00


def test_structural_target_buy():
    placer = TakeProfitPlacer(mode=TakeProfitMode.STRUCTURAL)
    target = placer.place(
        direction="BUY", entry=1.20, stop=1.10, structural_target=1.50
    )
    assert target == 1.50


def test_structural_target_sell():
    placer = TakeProfitPlacer(mode=TakeProfitMode.STRUCTURAL)
    target = placer.place(
        direction="SELL", entry=1.20, stop=1.30, structural_target=0.90
    )
    assert target == 0.90


def test_fixed_pips_buy():
    placer = TakeProfitPlacer(mode=TakeProfitMode.FIXED_PIPS, fixed_distance=0.05)
    target = placer.place(direction="BUY", entry=1.2000, stop=1.1500)
    assert round(target, 4) == 1.2500


def test_default_mode_is_rr_multiple():
    placer = TakeProfitPlacer()
    target = placer.place(direction="BUY", entry=1.20, stop=1.10)
    assert round(target, 4) == 1.40
