import logging
import sys

from pythonjsonlogger import jsonlogger

from aptguide.core.config import Settings


def setup_logging(settings: Settings) -> None:
    """配置 JSON 日志"""
    logger = logging.getLogger("aptguide")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
