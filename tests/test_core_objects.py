from core import DATE_FORMAT, DATETIME_FORMAT, Direction, LiquidityType, SUPPORTED_SYMBOLS, SwingType, TIMEFRAMES, Trend


def test_core_objects_are_available():
    assert DATE_FORMAT == "%Y-%m-%d"
    assert DATETIME_FORMAT == "%Y-%m-%d %H:%M:%S"
    assert "M15" in TIMEFRAMES
    assert "XAUUSD" in SUPPORTED_SYMBOLS

    assert Trend.UP.value == "up"
    assert SwingType.HIGH.value == "high"
    assert LiquidityType.SWING.value == "swing"
    assert Direction.LONG.value == "long"
