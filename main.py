from datetime import date

from config import settings, setup_logging
from data import mt5_client
from data.downloader import download_candles
from data.storage import save_candles
from data.validator import validate_candles

logger = setup_logging()


def main() -> None:
    try:
        logger.info("Starting SMC Trader")
        logger.info("Using symbol: {}", settings.default_symbol)
        logger.info("Using timeframe: {}", settings.default_timeframe)
        logger.info("Using risk percent: {}", settings.risk_percent)
        logger.info("Using data directory: {}", settings.data_directory)

        if settings.risk_percent <= 0:
            logger.warning(
                "Risk percent is set to a non-positive value; risk controls may be disabled."
            )

        logger.info("Connecting to MT5")
        mt5_client.connect()

        try:
            logger.info("Downloading candles")
            frame = download_candles(
                symbol=settings.default_symbol,
                timeframe=settings.default_timeframe,
                count=settings.candles_to_download,
            )

            logger.info("Validating candle data")
            validated = validate_candles(frame)

            logger.info("Saving candles to parquet")
            save_path = save_candles(
                validated,
                symbol=settings.default_symbol,
                timeframe=settings.default_timeframe,
                date=date.today().strftime("%Y-%m-%d"),
            )
            logger.info("Saved candles to {}", save_path)
        finally:
            mt5_client.disconnect()
            logger.info("Disconnected from MT5")

        logger.info("Workflow completed successfully")
    except Exception as exc:
        logger.error("Startup failed: {}", exc)
        raise


if __name__ == "__main__":
    main()