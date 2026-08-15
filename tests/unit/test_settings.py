from config.settings import Settings


def test_settings_reads_environment_aliases(monkeypatch):
    monkeypatch.setenv("MT5_LOGIN", "123456")
    monkeypatch.setenv("MT5_PASSWORD", "secret")
    monkeypatch.setenv("MT5_SERVER", "Demo")
    monkeypatch.setenv("DEFAULT_SYMBOL", "EURUSD")
    monkeypatch.setenv("DEFAULT_TIMEFRAME", "H1")
    monkeypatch.setenv("CANDLES_TO_DOWNLOAD", "250")
    monkeypatch.setenv("RISK_PERCENT", "2.5")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_DIRECTORY", "custom_logs")
    monkeypatch.setenv("DATA_DIRECTORY", "custom_data")

    settings = Settings()

    assert settings.mt5_login == 123456
    assert settings.mt5_password == "secret"
    assert settings.mt5_server == "Demo"
    assert settings.default_symbol == "EURUSD"
    assert settings.default_timeframe == "H1"
    assert settings.candles_to_download == 250
    assert settings.risk_percent == 2.5
    assert settings.log_level == "DEBUG"
    assert settings.log_directory == "custom_logs"
    assert settings.data_directory == "custom_data"


def test_settings_uses_defaults_when_values_are_not_provided(monkeypatch):
    for key in [
        "MT5_LOGIN",
        "MT5_PASSWORD",
        "MT5_SERVER",
        "DEFAULT_SYMBOL",
        "DEFAULT_TIMEFRAME",
        "CANDLES_TO_DOWNLOAD",
        "RISK_PERCENT",
        "LOG_LEVEL",
        "LOG_DIRECTORY",
        "DATA_DIRECTORY",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(mt5_login=100100, mt5_password="pwd", mt5_server="Broker")

    assert settings.default_symbol == "XAUUSD"
    assert settings.default_timeframe == "M15"
    assert settings.candles_to_download == 5000
    assert settings.risk_percent == 1.0
    assert settings.log_level == "INFO"
    assert settings.log_directory == "logs"
    assert settings.data_directory == "data_store"


def test_live_trading_requires_mode_and_explicit_gate():
    paper = Settings(mt5_login=100100, mt5_password="pwd", mt5_server="Broker")
    live_without_gate = Settings(
        mt5_login=100100,
        mt5_password="pwd",
        mt5_server="Broker",
        trading_mode="live",
        live_trading_enabled=False,
    )
    live_with_gate = Settings(
        mt5_login=100100,
        mt5_password="pwd",
        mt5_server="Broker",
        trading_mode="live",
        live_trading_enabled=True,
    )

    assert not paper.live_trading_authorized
    assert not live_without_gate.live_trading_authorized
    assert live_with_gate.live_trading_authorized
