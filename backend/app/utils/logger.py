import logging
import sys


class _ZentivraLogger(logging.Logger):
    """Custom logger that auto-attaches tracebacks on error/exception calls."""

    def error(self, msg, *args, **kwargs):
        if "exc_info" not in kwargs:
            kwargs["exc_info"] = sys.exc_info()[0] is not None
        super().error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        kwargs.setdefault("exc_info", True)
        super().exception(msg, *args, **kwargs)


logging.setLoggerClass(_ZentivraLogger)


def setup_logger():
    """
    Centralized logger configuration for Zentivra.
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
