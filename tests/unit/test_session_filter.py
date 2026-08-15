from datetime import datetime, time, timezone

from execution.session import SessionFilter, TradingWindow


def test_session_filter_uses_timezone_aware_timestamps():
    session = SessionFilter(enabled=True, timezone="UTC", windows=[TradingWindow(time(8), time(11))])
    assert session.allows(datetime(2026, 8, 10, 9, tzinfo=timezone.utc))
    assert not session.allows(datetime(2026, 8, 10, 12, tzinfo=timezone.utc))
    assert not session.allows(datetime(2026, 8, 10, 9))
