import logging.config
import os


def setup_logging(
    app_name: str,
    log_level: str = "INFO",
    log_dir: str = "logs",
) -> None:
    """
    Setup logging configuration with both file and console handlers

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        app_name: Application name for log file naming
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s - "
                    "method:%(method)s - time:%(execution_time)s"
                ),
                "defaults": {"method": "N/A", "execution_time": "N/A"},
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "simple",
                "filename": os.path.join(log_dir, f"{app_name}.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 1,
            },
        },
        "loggers": {
            "": {"handlers": ["console", "file"], "level": "DEBUG"},
            "booking_providers": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(config)
