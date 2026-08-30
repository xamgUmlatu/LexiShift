from __future__ import annotations

import base64
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from theme_image_loader import ThemeImageLoader


_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class _Target:
    def __init__(self) -> None:
        self.accepted: list[tuple[str, int, QImage | None]] = []

    def _accept_theme_image(
        self,
        image_path: str,
        request_token: int,
        image: QImage | None,
    ) -> None:
        self.accepted.append((image_path, request_token, image))


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


class TestThemeImageLoader(unittest.TestCase):
    def test_valid_image_is_delivered_on_the_application_thread(self) -> None:
        app = _app()
        loader = ThemeImageLoader()
        target = _Target()
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "background.png"
            image_path.write_bytes(_ONE_PIXEL_PNG)

            loader.request(target, str(image_path), 7)
            deadline = time.monotonic() + 2.0
            while not target.accepted and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)

        self.assertEqual(len(target.accepted), 1)
        delivered_path, token, image = target.accepted[0]
        self.assertEqual(delivered_path, str(image_path))
        self.assertEqual(token, 7)
        self.assertIsNotNone(image)
        self.assertFalse(image.isNull())

    def test_slow_file_read_does_not_block_requesting_thread(self) -> None:
        _app()
        loader = ThemeImageLoader()
        target = _Target()
        release = threading.Event()

        def slow_read(_image_path: str) -> tuple[QImage | None, str]:
            release.wait(timeout=2.0)
            return None, "test read released"

        with patch("theme_image_loader._read_theme_image", side_effect=slow_read):
            started_at = time.monotonic()
            loader.request(target, "/slow/background.png", 1)
            elapsed = time.monotonic() - started_at
            release.set()

        self.assertLess(elapsed, 0.5)

    def test_concurrent_requests_for_same_path_share_one_read(self) -> None:
        app = _app()
        loader = ThemeImageLoader()
        first_target = _Target()
        second_target = _Target()
        started = threading.Event()
        release = threading.Event()

        def controlled_read(_image_path: str) -> tuple[QImage | None, str]:
            started.set()
            release.wait(timeout=2.0)
            return QImage(1, 1, QImage.Format.Format_RGB32), ""

        with patch("theme_image_loader._read_theme_image", side_effect=controlled_read) as read:
            loader.request(first_target, "/shared/background.png", 1)
            self.assertTrue(started.wait(timeout=1.0))
            loader.request(second_target, "/shared/background.png", 2)
            self.assertEqual(read.call_count, 1)
            release.set()
            deadline = time.monotonic() + 2.0
            while (
                not first_target.accepted or not second_target.accepted
            ) and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)

        self.assertEqual(len(first_target.accepted), 1)
        self.assertEqual(len(second_target.accepted), 1)


if __name__ == "__main__":
    unittest.main()
