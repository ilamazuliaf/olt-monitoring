import logging
import os
import sys
from typing import Optional


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Configure and return application logger."""
    logger = logging.getLogger("olt_monitor")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_file:
        try:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Tidak dapat membuat handler log file pada '{log_file}': {e}")

    return logger


def get_logger() -> logging.Logger:
    """Retrieve application logger instance."""
    return logging.getLogger("olt_monitor")
