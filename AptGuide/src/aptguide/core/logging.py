import logging
import sys

from pythonjsonlogger import jsonlogger

from aptguide.core.config import Settings


def setup_logging(settings: Settings) -> None:
    """配置 JSON 日志。"""
    logger = logging.getLogger("aptguide")
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """获取命名日志器。"""
    return logging.getLogger(f"aptguide.{name}")
