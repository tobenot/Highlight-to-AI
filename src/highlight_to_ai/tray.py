from __future__ import annotations

import logging
import os
from collections.abc import Callable
from pathlib import Path


class TrayController:
    def __init__(
        self,
        app_name: str,
        hotkey: str,
        config_path: Path,
        on_quit: Callable[[], None],
        logger: logging.Logger,
    ) -> None:
        self._app_name = app_name
        self._hotkey = hotkey
        self._config_path = config_path
        self._on_quit = on_quit
        self._logger = logger
        self._icon = None

    @property
    def available(self) -> bool:
        try:
            import pystray  # noqa: F401
            from PIL import Image, ImageDraw  # noqa: F401

            return True
        except Exception:
            return False

    def run(self) -> bool:
        """Run tray loop. Returns False if tray dependency is unavailable."""
        try:
            import pystray
        except Exception as exc:
            self._logger.warning("pystray unavailable: %s", exc)
            return False

        icon_image = self._build_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem(f"Hotkey: {self._hotkey}", lambda: None, enabled=False),
            pystray.MenuItem("Open config", self._open_config),
            pystray.MenuItem("Quit", self._quit),
        )

        self._icon = pystray.Icon(self._app_name, icon_image, self._app_name, menu)
        self._logger.info("tray started")
        self._icon.run()
        self._logger.info("tray stopped")
        return True

    def stop(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                self._logger.exception("failed to stop tray icon")

    def _open_config(self, icon, item) -> None:  # noqa: ANN001
        del icon, item
        try:
            if self._config_path.exists() and hasattr(os, "startfile"):
                os.startfile(str(self._config_path))  # type: ignore[attr-defined]
            elif hasattr(os, "startfile"):
                os.startfile(str(self._config_path.parent))  # type: ignore[attr-defined]
        except Exception:
            self._logger.exception("failed to open config path")

    def _quit(self, icon, item) -> None:  # noqa: ANN001
        del item
        self._logger.info("tray quit clicked")
        self._on_quit()
        icon.stop()

    def _build_icon_image(self):  # noqa: ANN201
        from PIL import Image, ImageDraw

        size = 64
        image = Image.new("RGBA", (size, size), (30, 30, 30, 255))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((6, 6, 58, 58), radius=12, fill=(25, 118, 210, 255))
        draw.rectangle((18, 18, 25, 46), fill=(255, 255, 255, 255))
        draw.rectangle((39, 18, 46, 46), fill=(255, 255, 255, 255))
        draw.rectangle((18, 28, 46, 35), fill=(255, 255, 255, 255))
        return image
