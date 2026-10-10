"""Logging configuration for Orquestra."""

import logging
import logging.config
import os
import sys

import structlog


def configure_logging() -> None:
    """Configure structlog for JSON logging with correlation ID."""
    debug = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")

    if debug:
        # Development: colored console output
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Production: JSON output
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Configure stdlib logging
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "structlog.stdlib.ProcessorFormatter",
                    "processor": structlog.dev.ConsoleRenderer(colors=False)
                    if debug
                    else structlog.processors.JSONRenderer(),
                },
            },
            "handlers": {
                "default": {
                    "level": "INFO",
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": sys.stdout,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": True,
                },
                "django": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False,
                },
                "django.request": {
                    "handlers": ["default"],
                    "level": "ERROR",
                    "propagate": False,
                },
                "celery": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger with the given name.

    Args:
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    return structlog.get_logger(name)
