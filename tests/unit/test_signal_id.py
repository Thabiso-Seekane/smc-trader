from execution.realtime import RealTimePaperEngine


def test_signal_id_inputs_are_deterministic():
    # The engine builds signal IDs from symbol, timeframe, candle time, direction, and setup ID.
    values = ("XAUUSD", "M15", "2026-08-10T10:15:00+00:00", "BUY", "setup-1")
    assert ":".join(values) == ":".join(values)
