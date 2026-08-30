from __future__ import annotations

import threading
from typing import Protocol
import weakref

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

from theme_logger import log_theme


MAX_THEME_IMAGE_BYTES = 64 * 1024 * 1024


class ThemeImageTarget(Protocol):
    def _accept_theme_image(
        self,
        image_path: str,
        request_token: int,
        image: QImage | None,
    ) -> None: ...


class ThemeImageLoader(QObject):
    """Load theme images without allowing file I/O to block the GUI thread."""

    _loaded = Signal(str, object, str)

    def __init__(self) -> None:
        super().__init__()
        self._loading: set[str] = set()
        self._waiters: dict[str, list[tuple[weakref.ReferenceType, int]]] = {}
        self._loaded.connect(self._on_loaded)

    def request(
        self,
        target: ThemeImageTarget,
        image_path: str,
        request_token: int,
    ) -> None:
        path = str(image_path or "")
        if not path:
            return
        self._waiters.setdefault(path, []).append((weakref.ref(target), request_token))
        if path in self._loading:
            return

        self._loading.add(path)
        threading.Thread(
            target=self._load,
            args=(path,),
            name="LexiShiftThemeImageLoader",
            daemon=True,
        ).start()

    def _load(self, image_path: str) -> None:
        image, error = _read_theme_image(image_path)
        self._loaded.emit(image_path, image, error)

    @Slot(str, object, str)
    def _on_loaded(self, image_path: str, image: QImage | None, error: str) -> None:
        self._loading.discard(image_path)
        if error:
            log_theme(f"[Theme] Failed to load image: {image_path} ({error})")
        for target_ref, request_token in self._waiters.pop(image_path, []):
            target = target_ref()
            if target is None:
                continue
            self._deliver(target, image_path, request_token, image)

    @staticmethod
    def _deliver(
        target: ThemeImageTarget,
        image_path: str,
        request_token: int,
        image: QImage | None,
    ) -> None:
        try:
            target._accept_theme_image(image_path, request_token, image)
        except RuntimeError:
            # PySide wrappers can outlive their deleted C++ widget briefly.
            return


def _read_theme_image(image_path: str) -> tuple[QImage | None, str]:
    try:
        with open(image_path, "rb") as handle:
            payload = handle.read(MAX_THEME_IMAGE_BYTES + 1)
    except OSError as exc:
        return None, str(exc)
    if len(payload) > MAX_THEME_IMAGE_BYTES:
        return None, f"image exceeds {MAX_THEME_IMAGE_BYTES // (1024 * 1024)} MiB limit"

    image = QImage.fromData(payload)
    if image.isNull():
        return None, "unsupported or invalid image data"
    return image, ""


_THEME_IMAGE_LOADER: ThemeImageLoader | None = None


def request_theme_image(
    target: ThemeImageTarget,
    image_path: str,
    request_token: int,
) -> None:
    global _THEME_IMAGE_LOADER
    if _THEME_IMAGE_LOADER is None:
        _THEME_IMAGE_LOADER = ThemeImageLoader()
    _THEME_IMAGE_LOADER.request(target, image_path, request_token)
