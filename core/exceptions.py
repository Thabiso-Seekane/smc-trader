"""Shared domain exceptions.

Central exception hierarchy for the SMC-Trader platform so that callers
can catch domain-level failures without reaching into implementation
details.
"""

from __future__ import annotations


class SMCError(Exception):
    """Base exception for all application-specific errors."""


class DataValidationError(SMCError):
    """Raised when candle data fails one or more validation checks."""


__all__ = ["SMCError", "DataValidationError"]

