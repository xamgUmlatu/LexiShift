from __future__ import annotations

import getpass
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QTimer
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


OPEN_RESOURCE_SETTINGS_FLAG = "--open-resource-settings"
RESOURCE_PAIR_FLAG = "--resource-pair"
ACTIVATION_MESSAGE = "ACTIVATE"
OPEN_RESOURCE_SETTINGS_MESSAGE = "OPEN_SETTINGS:resources"


def _cli_value(argv: list[str], flag: str) -> str:
    try:
        index = argv.index(flag)
    except ValueError:
        return ""
    if index + 1 >= len(argv):
        return ""
    return str(argv[index + 1] or "").strip()


def resource_settings_activation_message(pair: str | None = None) -> str:
    pair_text = str(pair or "").strip().lower()
    if pair_text:
        return f"{OPEN_RESOURCE_SETTINGS_MESSAGE}|pair={pair_text}"
    return OPEN_RESOURCE_SETTINGS_MESSAGE


def is_resource_settings_activation_message(message: str) -> bool:
    return str(message or "").startswith(OPEN_RESOURCE_SETTINGS_MESSAGE)


def resource_pair_from_activation_message(message: str) -> str | None:
    text = str(message or "")
    if not is_resource_settings_activation_message(text):
        return None
    _prefix, _separator, tail = text.partition("|")
    for part in tail.split("|"):
        key, separator, value = part.partition("=")
        if separator and key == "pair":
            pair = value.strip().lower()
            return pair or None
    return None


def startup_activation_message(argv: list[str]) -> str:
    if OPEN_RESOURCE_SETTINGS_FLAG in argv:
        return resource_settings_activation_message(_cli_value(argv, RESOURCE_PAIR_FLAG))
    return ACTIVATION_MESSAGE


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


def acquire_singleton_server(
    socket_name: str,
    activation_message: str = ACTIVATION_MESSAGE,
) -> QLocalServer | None:
    socket = QLocalSocket()
    socket.connectToServer(socket_name)
    if socket.waitForConnected(500):
        socket.write(str(activation_message or ACTIVATION_MESSAGE).encode("utf-8"))
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
            message = bytes(client.readAll()).decode("utf-8", errors="ignore")
            window.show()
            window.raise_()
            window.activateWindow()
            should_open_resources = is_resource_settings_activation_message(message) and hasattr(
                window,
                "_open_settings_resources",
            )
            resource_pair = resource_pair_from_activation_message(message)
            client.disconnectFromServer()
            if should_open_resources:
                QTimer.singleShot(0, lambda: window._open_settings_resources(pair=resource_pair))

    server.newConnection.connect(handle_activation)


def prime_theme_assets(logger: StartupLogger) -> None:
    theme_dir()
    logger.log("theme_dir()")
    ensure_sample_images()
    logger.log("ensure_sample_images()")
    ensure_sample_themes()
    logger.log("ensure_sample_themes()")
