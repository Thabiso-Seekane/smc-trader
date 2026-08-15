from config import get_settings, settings, setup_logging


def test_config_package_exports_are_available():
    assert settings is not None
    assert callable(get_settings)
    assert callable(setup_logging)
    assert settings.default_symbol == "XAUUSD"
    assert settings.risk_percent == 1.0
    assert settings.log_level == "INFO"


def test_settings_load_from_env_and_expose_required_values():
    resolved = get_settings()

    assert resolved is settings
    assert isinstance(resolved.mt5_login, int)
    assert resolved.mt5_login > 0
    assert resolved.mt5_password
    assert resolved.mt5_server
    assert resolved.default_symbol == "XAUUSD"
    assert resolved.default_timeframe == "M15"
    assert resolved.candles_to_download == 5000
    assert resolved.log_level == "INFO"
    assert resolved.log_directory == "logs"
    assert resolved.data_directory == "data_store"
    assert resolved.risk_percent == 1.0
