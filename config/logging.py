"""Logging configuration helpers."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from config.settings import settings


def setup_logging() -> object:
    """Configure Loguru logging for console and file output."""

    log_path = Path(settings.log_directory)
    log_path.mkdir(parents=True, exist_ok=True)

    log_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} - {message}"
    )

    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        colorize=True,
        format=log_format,
    )
    logger.add(
        log_path / "smc_trader.log",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        level=settings.log_level,
        enqueue=True,
        format=log_format,
    )

    return logger


__all__ = ["setup_logging"]