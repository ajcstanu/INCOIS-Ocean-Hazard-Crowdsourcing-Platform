import sys
from loguru import logger
from config.settings import settings


def setup_logger() -> None:
    """Configure Loguru logger for the application."""
    logger.remove()  # Remove default handler

    log_level = "DEBUG" if settings.APP_DEBUG else "INFO"
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
    )

    # File handler (rotating)
    logger.add(
        "logs/incois_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="INFO",
        rotation="00:00",
        retention="30 days",
        compression="zip",
    )

    logger.info(f"Logger initialized | env={settings.APP_ENV} | level={log_level}")
