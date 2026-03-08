"""
Zentivra logging utilities.

Provides a custom logger class that automatically attaches tracebacks on error/exception
calls, and a centralized setup for the application. Suppresses noisy third-party loggers
(httpx, azure, playwright, etc.) to keep output readable.
"""

import logging
import sys


class _ZentivraLogger(logging.Logger):
    """
    Custom logger that auto-attaches tracebacks on error/exception calls.

    Overrides error() and exception() to ensure exc_info is set when an exception
    is active, so stack traces appear in logs without explicit exc_info=True.
    """

    def error(self, msg, *args, **kwargs):
        # Auto-attach traceback when an exception is currently being handled
        if "exc_info" not in kwargs:
            kwargs["exc_info"] = sys.exc_info()[0] is not None
        super().error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        kwargs.setdefault("exc_info", True)
        super().exception(msg, *args, **kwargs)


logging.setLoggerClass(_ZentivraLogger)


def setup_logger():
    """
    Create and configure the central Zentivra logger.

    Sets up INFO-level logging to stdout with a structured format including
    timestamp, level, filename:line, and message. Suppresses third-party loggers
    to WARNING. Returns the configured logger instance.
    """
    # Create logger
    logger = logging.getLogger("zentivra")
    logger.setLevel(logging.INFO)

    # Create format
    log_format = (
        "[%(asctime)s] - (%(levelname)s) - [%(filename)s:%(lineno)d] - %(message)s\n"
    )
    formatter = logging.Formatter(log_format)

    # Create stream handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)

    # Suppress noisy third-party loggers
    noisy_loggers = [
        "httpx",
        "httpcore",
        "urllib3",
        "azure",
        "azure.core.pipeline",
        "openai",
        "anthropic",
        "playwright",
        "hpack",
        "charset_normalizer",
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    return logger


# Initialize the global logger instance
logger = setup_logger()
