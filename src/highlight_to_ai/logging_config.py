from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import get_default_log_dir


def setup_logging(log_dir: Path | None = None) -> logging.Logger:
    target_dir = log_dir or get_default_log_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    log_file = target_dir / "app.log"

    logger = logging.getLogger("highlight_to_ai")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=512 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("logging initialized file=%s", log_file)
    return logger
