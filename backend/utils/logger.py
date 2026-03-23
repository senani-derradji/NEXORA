import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """
    Setup a logger with console and optional file handlers.
    Uses singleton pattern to avoid duplicate handlers.

    Args:
        name: Logger name (typically __name__)
        log_file: Optional log file path
        level: Logging level

    Returns:
        Configured logger instance
    """
    # Create logger - check if already exists with handlers to prevent duplicates
    logger = logging.getLogger(name)

    # If logger already has handlers (from previous setup), just return it
    if logger.handlers or logger.level != logging.NOTSET:
        return logger

    logger.setLevel(level)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger


# Default logger for backend
logger = setup_logger('backend', '/var/log/nexora/backend.log')
