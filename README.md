# SMC Trader

## Project overview

SMC Trader is a Python-based trading platform that follows Smart Money Concepts (SMC) principles. The project currently focuses on a reliable data pipeline for MetaTrader 5 candles, including configuration loading, structured logging, candle validation, parquet persistence, and a small orchestration entry point.

## Folder structure

```text
smc-trader/
├── app/                 # application modules
├── backtesting/         # backtesting logic
├── config/              # settings and logging
├── core/                # shared constants, errors, and types
├── data/                # MT5 integration, downloader, validator, storage
├── docs/                # project documentation
├── tests/               # unit and integration tests
├── main.py              # workflow entry point
└── pyproject.toml       # project metadata and dependencies
```

## Installation

```bash
python -m pip install -e ".[dev]"
```

## Configure .env

Create a local environment file from the example and fill in your MT5 credentials:

```bash
copy .env.example .env
```

Required variables:

```env
MT5_LOGIN=123456
MT5_PASSWORD=your_password
MT5_SERVER=your_mt5_server
DEFAULT_SYMBOL=XAUUSD
DEFAULT_TIMEFRAME=M15
CANDLES_TO_DOWNLOAD=5000
RISK_PERCENT=1.0
LOG_LEVEL=INFO
LOG_DIRECTORY=logs
DATA_DIRECTORY=data_store
```

## How to run the project

```bash
python main.py
```

The workflow will:

1. Load configuration
2. Initialize logging
3. Connect to MetaTrader 5
4. Download candles
5. Validate the DataFrame
6. Save the data to parquet
7. Disconnect from MT5

## Roadmap

- Add strategy execution modules
- Build signal generation and risk rules
- Implement backtesting and reporting
- Add dashboards and live monitoring
- Expand automated test coverage

## Technologies used

- Python
- pandas
- numpy
- pydantic / pydantic-settings
- loguru
- MetaTrader5
- pytest
- parquet via pandas

## License

MIT