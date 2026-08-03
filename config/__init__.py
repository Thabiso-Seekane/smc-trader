"""
Configuration package.

Provides application settings and logging configuration.
"""

from .settings import get_settings, settings
from .logging import setup_logging

__all__ = [
    "settings",
    "get_settings",
    "setup_logging",
]