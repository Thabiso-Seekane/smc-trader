"""Unit tests for the Week 8 StopLossPlacer."""

from risk.enums import StopLossMode
from risk.stop_loss import StopLossPlacer


def test_structural_buy_below_entry():
    placer = StopLossPlacer(mode=StopLossMode.STRUCTURAL, atr_multiplier=2.0)
    stop = placer.place(direction="BUY", entry=1.20, structural_stop=1.10)
    assert stop == 1.10


def test_structural_sell_above_entry():
    placer = StopLossPlacer(mode=StopLossMode.STRUCTURAL, atr_multiplier=2.0)
    stop = placer.place(direction="SELL", entry=1.20, structural_stop=1.30)
    assert stop == 1.30


def test_atr_buy_below_entry():
    # entry 1.20, atr 0.02, multiplier 2 => distance 0.04 => stop 1.16
    placer = StopLossPlacer(mode=StopLossMode.ATR, atr_multiplier=2.0)
    stop = placer.place(direction="BUY", entry=1.20, structural_stop=None, atr=0.02)
    assert round(stop, 4) == 1.16


def test_atr_sell_above_entry():
    placer = StopLossPlacer(mode=StopLossMode.ATR, atr_multiplier=2.0)
    stop = placer.place(direction="SELL", entry=1.20, structural_stop=None, atr=0.02)
    assert round(stop, 4) == 1.24


def test_fixed_pips_buy():
    placer = StopLossPlacer(
        mode=StopLossMode.FIXED_PIPS, fixed_distance=0.0050
    )
    stop = placer.place(direction="BUY", entry=1.2000, structural_stop=None, atr=0.0)
    assert round(stop, 4) == 1.1950


def test_default_mode_is_structural():
    placer = StopLossPlacer()
    stop = placer.place(direction="BUY", entry=1.20, structural_stop=1.05)
    assert stop == 1.05
