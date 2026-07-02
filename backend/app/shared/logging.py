"""Structured JSON logging configuration."""

import logging
import sys

from pythonjsonlogger.json import JsonFormatter


def setup_logging():
    """Configure structured JSON logging using settings.LOG_LEVEL."""
    from app.config import settings

    root = logging.getLogger()

    # Avoid adding duplicate handlers on repeated calls
    if any(
        isinstance(h, logging.StreamHandler) and isinstance(getattr(h, "formatter", None), JsonFormatter)
        for h in root.handlers
    ):
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    root.addHandler(handler)
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
