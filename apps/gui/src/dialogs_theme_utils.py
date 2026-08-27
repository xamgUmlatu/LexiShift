from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from theme_image_loader import request_theme_image
from theme_loader import THEME_ALL_COLOR_KEYS


class _ThemedTabContainer(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._bg_pixmap: QPixmap | None = None
        self._bg_opacity = 1.0
        self._bg_position = "center"
        self._bg_size = "cover"
        self._bg_repeat = "no-repeat"
        self._base_top = "#FFFFFF"
        self._base_bottom = "#FFFFFF"
        self._base_border = "#D8D0C0"
        self._base_radius = 10
        self._bg_image_path = ""
        self._bg_request_token = 0

    def set_base_style(
        self,
        *,
        top: str,
        bottom: str,
        border: str,
        radius: int = 10,
    ) -> None:
        self._base_top = str(top or "#FFFFFF")
        self._base_bottom = str(bottom or self._base_top)
        self._base_border = str(border or self._base_bottom)
        self._base_radius = max(0, int(radius))
        self.update()

    def set_background(
        self,
        *,
        image_path: str | None,
        opacity: float,
        position: str,
        size: str,
        repeat: str,
    ) -> None:
        self._bg_request_token += 1
        request_token = self._bg_request_token
        self._bg_image_path = str(image_path or "")
        self._bg_pixmap = None
        if image_path:
            request_theme_image(self, image_path, request_token)
        self._bg_opacity = max(0.0, min(1.0, opacity))
        self._bg_position = position
        self._bg_size = size
        self._bg_repeat = repeat
        self.update()

    def _accept_theme_image(
        self,
        image_path: str,
        request_token: int,
        image: QImage | None,
    ) -> None:
        if request_token != self._bg_request_token or image_path != self._bg_image_path:
            return
        self._bg_pixmap = QPixmap.fromImage(image) if image is not None else None
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(0, 0, -1, -1)
        radius = float(self._base_radius)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0.0, QColor(self._base_top))
        gradient.setColorAt(1.0, QColor(self._base_bottom))
        painter.fillPath(path, gradient)

        if self._bg_pixmap:
            painter.save()
            painter.setClipPath(path)
            painter.setOpacity(self._bg_opacity)
            if self._bg_repeat == "repeat":
                painter.drawTiledPixmap(rect, self._bg_pixmap)
            else:
                target = _scale_pixmap(self._bg_pixmap, rect.size(), self._bg_size)
                pos = _position_pixmap(rect, target.size(), self._bg_position)
                painter.drawPixmap(pos, target)
            painter.restore()

        painter.setPen(QPen(QColor(self._base_border), 1))
        painter.drawPath(path)


def _merge_theme(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key in THEME_ALL_COLOR_KEYS:
        if key in override:
            merged[key] = override[key]
    for key in (
        "_background",
        "_background_path",
        "_surface_opacities",
        "_name",
        "_source",
        "_base_dir",
        "_screen_overrides",
    ):
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
