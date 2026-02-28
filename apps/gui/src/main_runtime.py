from __future__ import annotations

import getpass
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable

from PySide6.QtNetwork import QLocalServer, QLocalSocket

from main_paths import _app_data_dir
from theme_assets import ensure_sample_images, ensure_sample_themes
from theme_loader import theme_dir


class StartupLogger:
    def __init__(self, paths: list[Path]) -> None:
        self._paths = list(paths)
        self._start_time = time.perf_counter()
        self._last_time = self._start_time

    def log(self, label: str) -> None:
        now = time.perf_counter()
        delta_ms = (now - self._last_time) * 1000.0
        total_ms = (now - self._start_time) * 1000.0
        self._last_time = now
        message = f"[startup] {label} (+{delta_ms:.1f} ms, total {total_ms:.1f} ms)"
        for path in self._paths:
            try:
                with open(path, "a", encoding="utf-8") as handle:
                    handle.write(message + "\n")
            except OSError:
                continue
        print(message)


def handle_startup_cli_flags(argv: list[str], startup_logs: list[Path]) -> bool:
    if "--print-data-dir" in argv:
        print(f"[LexiShift] AppDataLocation={_app_data_dir()}")
        print(f"[LexiShift] Startup log paths={startup_logs}")
        return True
    if "--diagnose-startup" in argv:
        print(f"[LexiShift] AppDataLocation={_app_data_dir()}")
        print(f"[LexiShift] Startup log paths={startup_logs}")
    return False


def run_helper_daemon_if_requested(argv: list[str]) -> bool:
    if "--helper-daemon" not in argv:
        return False
    from helper_daemon import run_daemon_from_cli

    filtered_args = [arg for arg in argv[1:] if arg != "--helper-daemon"]
    run_daemon_from_cli(filtered_args)
    return True


def install_exception_hook(app_data_dir: Callable[[], Path]) -> None:
    def exception_hook(exctype, value, tb):
        error_msg = "".join(traceback.format_exception(exctype, value, tb))
        crash_log = app_data_dir() / "crash.log"
        with open(crash_log, "a", encoding="utf-8") as handle:
            handle.write(f"[{datetime.now()}] Crash:\n{error_msg}\n\n")
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = exception_hook


def singleton_socket_name() -> str:
    return f"LexiShiftGUI_{getpass.getuser()}"


def acquire_singleton_server(socket_name: str) -> QLocalServer | None:
    socket = QLocalSocket()
    socket.connectToServer(socket_name)
    if socket.waitForConnected(500):
        socket.write(b"ACTIVATE")
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return None

    server = QLocalServer()
    server.removeServer(socket_name)
    server.listen(socket_name)
    return server


def bind_activation_handler(server: QLocalServer, window) -> None:
    def handle_activation() -> None:
        client = server.nextPendingConnection()
        if client:
            client.waitForReadyRead(100)
            window.show()
            window.raise_()
            window.activateWindow()
            client.disconnectFromServer()

    server.newConnection.connect(handle_activation)


def prime_theme_assets(logger: StartupLogger) -> None:
    theme_dir()
    logger.log("theme_dir()")
    ensure_sample_images()
    logger.log("ensure_sample_images()")
    ensure_sample_themes()
    logger.log("ensure_sample_themes()")
