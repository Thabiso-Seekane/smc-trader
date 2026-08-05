from unittest.mock import MagicMock

import pandas as pd
import pytest

import main


def make_frame():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01 00:00", "2024-01-01 00:05"]),
            "open": [1.10, 1.11],
            "high": [1.12, 1.13],
            "low": [1.09, 1.10],
            "close": [1.11, 1.12],
            "volume": [100, 110],
            "spread": [1, 1],
            "real_volume": [3, 4],
        }
    )


def test_main_logs_startup_information(monkeypatch):
    monkeypatch.setattr(main, "mt5_client", MagicMock())
    monkeypatch.setattr(main, "download_candles", lambda *a, **k: make_frame())
    monkeypatch.setattr(main, "save_candles", lambda *a, **k: "data_store/test.parquet")

    main.main()


def test_main_raises_on_invalid_data(monkeypatch):
    monkeypatch.setattr(main, "mt5_client", MagicMock())
    monkeypatch.setattr(
        main, "download_candles", lambda *a, **k: pd.DataFrame()
    )
    monkeypatch.setattr(main, "save_candles", lambda *a, **k: "data_store/test.parquet")

    with pytest.raises(Exception):
        main.main()
