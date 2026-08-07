"""Unit tests for the Week 9 Slippage model."""

import pytest

from backtesting.enums import Direction
from backtesting.slippage import SlippageModel


def test_no_slippage_when_zero():
    model = SlippageModel(slippage=0.0)
    assert model.apply(100.0, Direction.BUY) == pytest.approx(100.0)
    assert model.apply(100.0, Direction.SELL) == pytest.approx(100.0)


def test_disabled_returns_price():
    model = SlippageModel(slippage=0.5, enabled=False)
    assert model.apply(100.0, Direction.BUY) == pytest.approx(100.0)


def test_buy_slippage_raises_price():
    model = SlippageModel(slippage=0.2)
    assert model.apply(100.0, Direction.BUY) == pytest.approx(100.2)


def test_sell_slippage_lowers_price():
    model = SlippageModel(slippage=0.2)
    assert model.apply(100.0, Direction.SELL) == pytest.approx(99.8)
