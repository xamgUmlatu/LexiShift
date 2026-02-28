from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from theme_loader import THEME_ALL_COLOR_KEYS


class _ThemedTabContainer(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._bg_pixmap: QPixmap | None = None
        self._bg_opacity = 1.0
        self._bg_position = "center"
        self._bg_size = "cover"
        self._bg_repeat = "no-repeat"

    def set_background(
        self,
        *,
        image_path: str | None,
        opacity: float,
        position: str,
        size: str,
        repeat: str,
    ) -> None:
        if image_path:
            pixmap = QPixmap(image_path)
            self._bg_pixmap = pixmap if not pixmap.isNull() else None
        else:
            self._bg_pixmap = None
        self._bg_opacity = max(0.0, min(1.0, opacity))
        self._bg_position = position
        self._bg_size = size
        self._bg_repeat = repeat
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self._bg_pixmap:
            return
        painter = QPainter(self)
        painter.setOpacity(self._bg_opacity)
        rect = self.rect()
        if self._bg_repeat == "repeat":
            painter.drawTiledPixmap(rect, self._bg_pixmap)
            return
        target = _scale_pixmap(self._bg_pixmap, rect.size(), self._bg_size)
        pos = _position_pixmap(rect, target.size(), self._bg_position)
        painter.drawPixmap(pos, target)


def _merge_theme(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key in THEME_ALL_COLOR_KEYS:
        if key in override:
            merged[key] = override[key]
    for key in ("_background", "_background_path", "_name", "_source", "_base_dir", "_screen_overrides"):
        if key in override:
            merged[key] = override[key]
    return merged


def _scale_pixmap(pixmap: QPixmap, target_size, mode: str) -> QPixmap:
    if mode == "contain":
        return pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if mode == "cover":
        return pixmap.scaled(target_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    if mode.endswith("%"):
        try:
            pct = max(1, min(100, int(mode[:-1])))
        except ValueError:
            return pixmap
        w = int(target_size.width() * pct / 100)
        h = int(target_size.height() * pct / 100)
        return pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return pixmap


def _position_pixmap(rect, size, position: str) -> QPoint:
    pos = position.lower().split()
    if not pos:
        pos = ["center"]
    if "left" in pos:
        x = rect.left()
    elif "right" in pos:
        x = rect.right() - size.width()
    else:
        x = rect.center().x() - size.width() // 2
    if "top" in pos:
        y = rect.top()
    elif "bottom" in pos:
        y = rect.bottom() - size.height()
    else:
        y = rect.center().y() - size.height() // 2
    return QPoint(int(x), int(y))


def _coerce_float(value, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_int(value: str, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
