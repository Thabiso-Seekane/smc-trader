import pandas as pd

from data.storage import load_candles, save_candles


def test_storage_round_trip(tmp_path):
    frame = pd.DataFrame({"close": [1.23, 4.56], "volume": [10, 20]})

    path = save_candles(
        frame,
        symbol="XAUUSD",
        timeframe="M15",
        date="2026-08-03",
        root_dir=tmp_path,
    )

    assert path == tmp_path / "data_store" / "XAUUSD" / "M15" / "2026-08-03.parquet"
    assert path.exists()

    reloaded = load_candles(
        symbol="XAUUSD",
        timeframe="M15",
        date="2026-08-03",
        root_dir=tmp_path,
    )
    pd.testing.assert_frame_equal(reloaded, frame)


def test_missing_file_returns_empty_frame(tmp_path):
    loaded = load_candles(
        symbol="XAUUSD",
        timeframe="M15",
        date="2026-08-04",
        root_dir=tmp_path,
    )

    assert loaded.empty
