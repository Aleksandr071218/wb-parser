import logging
import sys

def setup_logging():
    """
    Configures the root logger for the application.

    This setup directs logs to standard output with a consistent format.
    It's designed to work well inside a Docker container where logs are
    typically collected from stdout/stderr.
    """
    # Get the root logger
    logger = logging.getLogger()

    # Set the level
    logger.setLevel(logging.INFO)

    # Create a handler for stdout
    handler = logging.StreamHandler(sys.stdout)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    # Avoid adding handlers if they already exist (e.g., in a reload scenario)
    if not logger.handlers:
        logger.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance for a specific module.

    Example:
        logger = get_logger(__name__)
        logger.info("This is an info message.")
    """
    return logging.getLogger(name)
