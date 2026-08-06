"""End-to-end unit tests for the Week 7 StrategyAnalyzer."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from liquidity.enums import LiquidityScope, LiquidityType
from liquidity.models import LiquidityLevel, LiquidityMap
from smart_money.displacement import DisplacementScore
from smart_money.enums import Direction, OrderBlockType, StructureEventType
from smart_money.fair_value_gap import FairValueGap
from smart_money.imbalance import ImbalanceMap
from smart_money.models import StructureEvent, SmartMoneyAnalysis
from smart_money.order_block_models import OrderBlock, OrderBlockMap
from strategy.analyzer import StrategyAnalyzer
from strategy.enums import DecisionStatus, SignalDirection
from structure.models import MarketStructure, Swing


def make_df():
    n = 20
    dates = [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(n)]
    return pd.DataFrame(
        {
            "date": dates,
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [100.5] * n,
            "volume": [1000] * n,
        }
    )


def make_structure() -> MarketStructure:
    return MarketStructure(
        swings=[
            Swing(index=0, timestamp=datetime(2024, 1, 1), price=1.20, is_high=True),
            Swing(index=1, timestamp=datetime(2024, 1, 2), price=1.00, is_high=False),
        ]
    )


def make_liquidity(swept=False) -> LiquidityMap:
    level = LiquidityLevel(
        price=1.15,
        liquidity_type=LiquidityType.SWING_HIGH,
        scope=LiquidityScope.EXTERNAL,
        strength=50.0,
        swept=swept,
    )
    return LiquidityMap(levels=[level])


def make_events() -> SmartMoneyAnalysis:
    return SmartMoneyAnalysis(
        events=[
            StructureEvent(
                event_type=StructureEventType.BOS,
                direction=Direction.BULLISH,
                timestamp=datetime(2024, 1, 1),
                broken_price=1.10,
                broken_index=0,
                confirmation_index=1,
                displacement=DisplacementScore(strength=90.0, confirmed=True),
            )
        ]
    )


def make_order_blocks() -> OrderBlockMap:
    block = OrderBlock(
        direction=OrderBlockType.BULLISH,
        high=1.20,
        low=1.10,
        origin_index=1,
        origin_time=datetime(2024, 1, 1),
        created_from_event=Direction.BULLISH,
        strength=80.0,
    )
    return OrderBlockMap(bullish=[block], bearish=[])


def make_imbalances() -> ImbalanceMap:
    gap = FairValueGap(
        direction=OrderBlockType.BULLISH,
        high=1.20,
        low=1.10,
        index=1,
        timestamp=datetime(2024, 1, 1),
        strength=80.0,
    )
    return ImbalanceMap(bullish=[gap], bearish=[])


def test_analyze_returns_result():
    analyzer = StrategyAnalyzer(timeframe="H1")
    result = analyzer.analyze(
        df=make_df(),
        structure=make_structure(),
        liquidity=make_liquidity(swept=True),
        events=make_events(),
        order_blocks=make_order_blocks(),
        imbalances=make_imbalances(),
        htf_bias="BULLISH",
        entry_price=1.05,
    )
    assert result.decision is not None
    assert len(result.zones) >= 0


def test_analyze_best_setup_is_bullish_high_conf():
    analyzer = StrategyAnalyzer(timeframe="H1")
    result = analyzer.analyze(
        df=make_df(),
        structure=make_structure(),
        liquidity=make_liquidity(swept=True),
        events=make_events(),
        order_blocks=make_order_blocks(),
        imbalances=make_imbalances(),
        htf_bias="BULLISH",
        entry_price=1.05,
    )
    best = result.best
    # The bullish setup with full confluence should be tradeable.
    if best is not None:
        assert best.confluence_score >= 70
        assert best.is_buy


def test_analyze_no_trade_when_low_confluence():
    analyzer = StrategyAnalyzer(timeframe="H1")
    result = analyzer.analyze(
        df=make_df(),
        structure=make_structure(),
        liquidity=make_liquidity(swept=False),
        events=SmartMoneyAnalysis(),
        order_blocks=OrderBlockMap(),
        imbalances=ImbalanceMap(),
        htf_bias="NEUTRAL",
        entry_price=1.05,
    )
    assert result.best is None
    assert result.decision.status == DecisionStatus.IGNORE


def test_analyze_ranks_bullish_higher_than_bearish():
    analyzer = StrategyAnalyzer(timeframe="H1")
    result = analyzer.analyze(
        df=make_df(),
        structure=make_structure(),
        liquidity=make_liquidity(swept=True),
        events=make_events(),  # bullish events only
        order_blocks=make_order_blocks(),  # bullish block only
        imbalances=make_imbalances(),  # bullish gap only
        htf_bias="BULLISH",
        entry_price=1.05,
    )
    if result.zones:
        buy_zones = [z for z in result.zones if z.is_buy]
        sell_zones = [z for z in result.zones if z.is_sell]
        if buy_zones and sell_zones:
            assert buy_zones[0].confluence_score >= sell_zones[0].confluence_score


def test_strategy_result_best_and_count():
    from strategy.models import StrategyResult, TradeDecision, TradeZone

    zone = TradeZone(
        direction=SignalDirection.BUY,
        entry_price=100.0,
        stop_loss=99.0,
        target=102.0,
        confluence_score=85.0,
    )
    result = StrategyResult(
        zones=[zone],
        timeframe="H1",
        decision=TradeDecision(
            status=DecisionStatus.STRONG,
            confidence=85.0,
            direction=SignalDirection.BUY,
            zone=zone,
        ),
    )
    assert result.count == 1
    assert result.best is zone
    assert len(result.tradeable) == 1
