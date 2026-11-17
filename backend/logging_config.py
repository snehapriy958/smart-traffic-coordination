"""
backend/logging_config.py

Structured Logging Configuration for Smart Traffic Coordination System.
Provides unified console formatting, ISO 8601 UTC timestamps, and level management.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone


class UTCFormatter(logging.Formatter):
    """Logging formatter that renders UTC ISO 8601 timestamps."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def configure_logging(level_name: str = "INFO", structured: bool = True) -> None:
    """Configures application-wide logging with standardized UTC timestamps."""
    level = getattr(logging, level_name.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if any(getattr(h, "_traffic_custom_handler", False) for h in root_logger.handlers):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler._traffic_custom_handler = True  # type: ignore[attr-defined]

    if structured:
        fmt = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
    else:
        fmt = "%(levelname)s: %(message)s"

    formatter = UTCFormatter(fmt=fmt)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
