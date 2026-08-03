from types import SimpleNamespace

import pandas as pd

from data import downloader


class FakeRatesResponse:
    def __init__(self):
        self.rows = [
            (1710000000, 1.10, 1.11, 1.09, 1.10, 100, 2, 3),
            (1710003600, 1.11, 1.12, 1.10, 1.11, 120, 1, 4),
        ]


def test_download_candles_builds_dataframe(monkeypatch):
    fake_client = SimpleNamespace(get_rates=lambda symbol, timeframe, count: FakeRatesResponse().rows)
    monkeypatch.setattr(downloader, "get_mt5_rates", lambda symbol, timeframe, count: fake_client.get_rates(symbol, timeframe, count))

    df = downloader.download_candles("XAUUSD", timeframe="M15", count=2)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume", "spread", "real_volume"]
    assert df.iloc[0]["date"] == pd.Timestamp(1710000000, unit="s")
    assert df.iloc[-1]["date"] == pd.Timestamp(1710003600, unit="s")
    assert df["volume"].tolist() == [100, 120]
