from __future__ import annotations

import getpass
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from main_paths import _app_data_dir
from theme_assets import ensure_sample_images, ensure_sample_themes
from theme_loader import theme_dir

STARTUP_SESSION_ID_ENV = "LEXISHIFT_STARTUP_SESSION_ID"
STARTUP_REQUESTED_AT_ENV = "LEXISHIFT_STARTUP_REQUESTED_AT"
STARTUP_SOURCE_ENV = "LEXISHIFT_STARTUP_SOURCE"
STARTUP_LAUNCH_MODE_ENV = "LEXISHIFT_STARTUP_LAUNCH_MODE"
STARTUP_RESOURCE_PAIR_ENV = "LEXISHIFT_STARTUP_RESOURCE_PAIR"


class StartupLogger:
    def __init__(
        self,
        paths: list[Path],
        *,
        start_time: float | None = None,
        argv: list[str] | None = None,
    ) -> None:
        self._paths = list(paths)
        self._start_time = start_time if start_time is not None else time.perf_counter()
        self._last_time = self._start_time
        self._session_id = startup_session_id()
        self._pid = os.getpid()
        self._ppid = os.getppid()
        self._argv_mode = startup_argv_mode(argv or sys.argv)
        self._source = os.environ.get(STARTUP_SOURCE_ENV, "direct")
        self._launch_mode = os.environ.get(STARTUP_LAUNCH_MODE_ENV, "")
        self._resource_pair = os.environ.get(STARTUP_RESOURCE_PAIR_ENV, "")
        self._requested_at = parse_utc_timestamp(os.environ.get(STARTUP_REQUESTED_AT_ENV, ""))

    def log(self, label: str) -> None:
        now = time.perf_counter()
        delta_ms = (now - self._last_time) * 1000.0
        total_ms = (now - self._start_time) * 1000.0
        self._last_time = now
        metadata = self._metadata_parts()
        message = f"[startup] {label} (+{delta_ms:.1f} ms, total {total_ms:.1f} ms) " + " ".join(
            metadata
        )
        for path in self._paths:
            try:
                with open(path, "a", encoding="utf-8") as handle:
                    handle.write(message + "\n")
            except OSError:
                continue
        print(message)

    def _metadata_parts(self) -> list[str]:
        parts = [
            f"session={self._session_id}",
            f"pid={self._pid}",
            f"ppid={self._ppid}",
            f"argv_mode={self._argv_mode}",
            f"source={self._source}",
            f"ts={datetime.now(timezone.utc).isoformat()}",
        ]
        if self._launch_mode:
            parts.append(f"launch_mode={self._launch_mode}")
        if self._resource_pair:
            parts.append(f"resource_pair={self._resource_pair}")
        if self._requested_at is not None:
            since_request_ms = (
                datetime.now(timezone.utc) - self._requested_at
            ).total_seconds() * 1000.0
            parts.append(f"since_request_ms={since_request_ms:.1f}")
        return parts


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


def startup_session_id() -> str:
    value = str(os.environ.get(STARTUP_SESSION_ID_ENV, "") or "").strip()
    if value:
        return value
    generated = f"direct-{os.getpid()}-{time.time_ns()}"
    os.environ[STARTUP_SESSION_ID_ENV] = generated
    return generated


def parse_utc_timestamp(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def startup_argv_mode(argv: list[str]) -> str:
    if OPEN_RESOURCE_SETTINGS_FLAG in argv:
        return "resource_settings"
    if "--helper-daemon" in argv:
        return "helper_daemon"
    if "--diagnose-startup" in argv:
        return "diagnose_startup"
    if "--print-data-dir" in argv:
        return "print_data_dir"
    return "normal"


def resource_settings_activation_message(
    pair: str | None = None,
    *,
    session_id: str | None = None,
) -> str:
    parts = [OPEN_RESOURCE_SETTINGS_MESSAGE]
    pair_text = str(pair or "").strip().lower()
    if pair_text:
        parts.append(f"pair={pair_text}")
    session_text = str(session_id or "").strip()
    if session_text:
        parts.append(f"session={session_text}")
    return "|".join(parts)


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


def startup_session_from_activation_message(message: str) -> str | None:
    text = str(message or "")
    if not is_resource_settings_activation_message(text):
        return None
    _prefix, _separator, tail = text.partition("|")
    for part in tail.split("|"):
        key, separator, value = part.partition("=")
        if separator and key == "session":
            session = value.strip()
            return session or None
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


def bind_activation_handler(
    server: QLocalServer,
    window,
    *,
    logger: StartupLogger | None = None,
) -> None:
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
            activation_session = startup_session_from_activation_message(message)
            if logger is not None:
                logger.log(
                    "activation received "
                    f"activation_session={activation_session or ''} "
                    f"resource_pair={resource_pair or ''}"
                )
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
