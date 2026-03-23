"""Structured logging configuration."""

import logging
import sys

import structlog


def setup_logging(debug: bool = False):
    """Configure structured logging for the application."""
    log_level = logging.DEBUG if debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging for third-party libs
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: str):
    """Return a structured logger bound with the given name."""
    return structlog.get_logger(name)
