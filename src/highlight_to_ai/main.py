from __future__ import annotations

import sys

from .app import AppRuntime
from .errors import ConfigError
from .logging_config import setup_logging


def main() -> int:
    logger = setup_logging()
    app = AppRuntime(logger=logger)

    try:
        app.start()
    except KeyboardInterrupt:
        print("\nHighlight-to-AI 已退出")
        return 0
    except ConfigError as exc:
        logger.error("configuration error: %s", exc)
        print(f"配置错误：{exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        logger.exception("fatal error")
        print(f"启动失败：{exc}", file=sys.stderr)
        return 1
    finally:
        app.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
