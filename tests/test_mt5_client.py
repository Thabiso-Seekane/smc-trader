from types import SimpleNamespace

from data import mt5_client


class FakeMT5:
    def __init__(self):
        self.initialized = False
        self.last_error_value = 0

    def initialize(self, login, password, server, **kwargs):
        self.initialized = True
        return True

    def shutdown(self):
        self.initialized = False

    def account_info(self):
        return {"login": 123456, "server": "test-server"}

    def terminal_info(self):
        return {"build": 1234}

    def symbols_get(self):
        return ["EURUSD", "XAUUSD"]

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        return [{"symbol": symbol, "timeframe": timeframe, "count": count}]

    def last_error(self):
        return self.last_error_value


def test_mt5_client_public_api(monkeypatch):
    fake_mt5 = FakeMT5()
    monkeypatch.setattr(mt5_client, "mt5", fake_mt5)
    monkeypatch.setattr(
        mt5_client,
        "_get_settings",
        lambda: SimpleNamespace(
            mt5_login=123456,
            mt5_password="secret",
            mt5_server="test-server",
            default_symbol="XAUUSD",
            default_timeframe="M15",
            candles_to_download=10,
        ),
    )
    monkeypatch.setattr(mt5_client, "_connected", False)

    assert mt5_client.connect() is True
    assert mt5_client.account_info() == {"login": 123456, "server": "test-server"}
    assert mt5_client.terminal_info() == {"build": 1234}
    assert mt5_client.symbols() == ["EURUSD", "XAUUSD"]
    assert mt5_client.resolve_symbol("xauusd") == "XAUUSD"
    assert mt5_client.get_rates("XAUUSD", "M15", 3) == [{"symbol": "XAUUSD", "timeframe": 15, "count": 3}]
    mt5_client.disconnect()
    assert fake_mt5.initialized is False


def test_resolve_symbol_supports_broker_aliases_and_suffixes(monkeypatch):
    monkeypatch.setattr(
        mt5_client,
        "symbols",
        lambda: [SimpleNamespace(name="GOLD"), SimpleNamespace(name="EURUSD.a")],
    )

    assert mt5_client.resolve_symbol("XAUUSD") == "GOLD"
    assert mt5_client.resolve_symbol("EURUSD") == "EURUSD.a"
    assert mt5_client.resolve_symbol("UNKNOWN") is None


def test_hourly_timeframe_uses_mt5_constant(monkeypatch):
    fake_mt5 = FakeMT5()
    fake_mt5.TIMEFRAME_H1 = 16385
    monkeypatch.setattr(mt5_client, "mt5", fake_mt5)

    assert mt5_client._normalize_timeframe("H1") == 16385
