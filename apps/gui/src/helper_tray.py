from __future__ import annotations

import sys
import threading
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from lexishift_core.helper_paths import build_helper_paths
from lexishift_core.helper_status import load_status
from helper_daemon import DaemonConfig, run_daemon
from utils_paths import resource_path, reveal_path


def _tray_icon() -> QIcon:
    if sys.platform == "darwin":
        candidate = resource_path("ttbn.icns")
        if os.path.exists(candidate):
            return QIcon(candidate)
        # Fallback: look in bundle resources if running from .app
        try:
            bundle_res = Path(sys.executable).parent.parent / "Resources" / "ttbn.icns"
            if bundle_res.exists():
                return QIcon(str(bundle_res))
        except Exception:
            pass
    else:
        candidate = resource_path("ttbn.ico")
        if os.path.exists(candidate):
            return QIcon(candidate)
    return QApplication.windowIcon()


def _debug_icon() -> QIcon:
    pixmap = QPixmap(22, 22)
    pixmap.fill()
    painter = QPainter(pixmap)
    painter.fillRect(0, 0, 22, 22, "#2E6BD6")
    painter.setPen("#FFFFFF")
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "L")
    painter.end()
    return QIcon(pixmap)


def _tray_icon_for_statusbar() -> QIcon:
    if os.environ.get("LEXISHIFT_TRAY_DEBUG"):
        return _debug_icon()
    base = _tray_icon()
    pixmap = base.pixmap(18, 18)
    if pixmap.isNull():
        return _debug_icon()
    return QIcon(pixmap)


def _log_line(paths, message: str) -> None:
    try:
        log_path = paths.data_root / "helper_tray.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{message}\n")
    except Exception:  # noqa: BLE001
        pass


def _open_main_app() -> None:
    paths = build_helper_paths()
    
    env = dict(os.environ)
    cmd = []

    if getattr(sys, "frozen", False):
        # On macOS, if we are in a bundle, use 'open' to launch cleanly
        if sys.platform == "darwin":
            exe_path = Path(sys.executable)
            # .../LexiShift.app/Contents/MacOS/LexiShift
            if exe_path.parent.name == "MacOS" and exe_path.parent.parent.name == "Contents":
                bundle_path = exe_path.parent.parent.parent
                if bundle_path.suffix == ".app":
                    # Use -n to force a new instance, otherwise macOS just activates the running tray process
                    cmd = ["open", "-n", str(bundle_path)]
                    try:
                        _log_line(paths, f"[{datetime.now()}] Tray launching via open: {cmd}")
                        subprocess.Popen(cmd, close_fds=True)
                        return
                    except Exception as e:
                        _log_line(paths, f"[{datetime.now()}] Tray failed to launch via open: {e}")
                        return

        # Clean up environment to prevent PyInstaller one-file conflicts
        for key in ["_MEIPASS2", "DYLD_LIBRARY_PATH", "LD_LIBRARY_PATH"]:
            env.pop(key, None)
        cmd = [sys.executable]
    else:
        entry = Path(__file__).resolve().parent / "main.py"
        cmd = [sys.executable, str(entry)]

    try:
        _log_line(paths, f"[{datetime.now()}] Tray launching: {cmd}")
        subprocess.Popen(cmd, close_fds=True, env=env)
    except Exception as e:
        _log_line(paths, f"[{datetime.now()}] Tray failed to launch app: {e}")


class HelperTrayController:
    def __init__(self) -> None:
        self.paths = build_helper_paths()
        _log_line(self.paths, "Helper tray starting.")
        _log_line(self.paths, f"Frozen: {getattr(sys, 'frozen', False)}, OneFile: {hasattr(sys, '_MEIPASS')}")
        _log_line(self.paths, f"System tray available: {QSystemTrayIcon.isSystemTrayAvailable()}")
        self.status_action = QAction("Helper starting…")
        self.status_action.setEnabled(False)

        self.open_app_action = QAction("Open LexiShift")
        self.open_app_action.triggered.connect(_open_main_app)

        self.open_data_action = QAction("Open Helper Data Folder")
        self.open_data_action.triggered.connect(lambda: reveal_path(str(self.paths.data_root)))

        self.open_status_action = QAction("Open Helper Status")
        self.open_status_action.triggered.connect(lambda: reveal_path(str(self.paths.srs_status_path)))

        self.notify_action = QAction("Show Test Notification")
        self.notify_action.triggered.connect(self._show_notification)

        self.quit_action = QAction("Quit Helper")
        self.quit_action.triggered.connect(QApplication.quit)

        self.menu = QMenu()
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()
        self.menu.addAction(self.open_app_action)
        self.menu.addAction(self.open_data_action)
        self.menu.addAction(self.open_status_action)
        self.menu.addAction(self.notify_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        icon = _tray_icon_for_statusbar()
        sizes = icon.availableSizes()
        _log_line(self.paths, f"Tray icon null: {icon.isNull()}, sizes: {sizes}")
        self.tray = QSystemTrayIcon(icon)
        self.tray.setToolTip("LexiShift Helper")
        self.tray.setContextMenu(self.menu)
        self.tray.show()
        self.tray.setVisible(True)
        _log_line(self.paths, f"Tray visible: {self.tray.isVisible()}")

        self._start_daemon()
        self._start_status_timer()

    def _start_daemon(self) -> None:
        config = DaemonConfig()
        thread = threading.Thread(target=run_daemon, args=(config,), daemon=True)
        thread.start()

    def _start_status_timer(self) -> None:
        self._timer = QTimer()
        self._timer.setInterval(15_000)
        self._timer.timeout.connect(self._refresh_status)
        self._timer.start()
        self._refresh_status()

    def _refresh_status(self) -> None:
        status = load_status(self.paths.srs_status_path)
        label = "Helper running"
        if status.last_error:
            label = f"Helper error: {status.last_error}"
        elif status.last_run_at:
            label = f"Last run: {status.last_run_at}"
        self.status_action.setText(label)

    def _show_notification(self) -> None:
        self.tray.showMessage("LexiShift Helper", "Tray helper is running.")


def run_helper_tray() -> None:
    paths = build_helper_paths()
    _log_line(paths, f"[{datetime.now()}] Helper tray process started (PID: {os.getpid()})")
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setWindowIcon(_tray_icon_for_statusbar())
        controller = HelperTrayController()
        QTimer.singleShot(1500, controller._show_notification)
        ret = app.exec()
        _log_line(paths, f"[{datetime.now()}] Helper tray process exited cleanly (Code: {ret})")
        sys.exit(ret)
    except Exception:
        import traceback
        _log_line(paths, f"[{datetime.now()}] Helper tray process crashed:\n{traceback.format_exc()}")
        sys.exit(1)
