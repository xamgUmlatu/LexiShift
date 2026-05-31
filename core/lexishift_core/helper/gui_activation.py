from __future__ import annotations

import getpass
from typing import Callable

OPEN_RESOURCE_SETTINGS_MESSAGE = "OPEN_SETTINGS:resources"


def gui_singleton_socket_name() -> str:
    return f"LexiShiftGUI_{getpass.getuser()}"


def resource_settings_activation_message(pair: str | None = None) -> str:
    pair_text = str(pair or "").strip().lower()
    return (
        f"{OPEN_RESOURCE_SETTINGS_MESSAGE}|pair={pair_text}"
        if pair_text
        else OPEN_RESOURCE_SETTINGS_MESSAGE
    )


def send_local_activation_message(
    socket_name: str,
    message: str,
    *,
    log: Callable[[str], None] | None = None,
) -> bool:
    try:
        from PySide6.QtCore import QCoreApplication
        from PySide6.QtNetwork import QLocalSocket
    except Exception as exc:  # noqa: BLE001
        if log is not None:
            log(f"resource_settings_activation_unavailable error={exc!s}")
        return False

    try:
        if QCoreApplication.instance() is None:
            QCoreApplication([])
        socket = QLocalSocket()
        socket.connectToServer(socket_name)
        if not socket.waitForConnected(300):
            return False
        socket.write(message.encode("utf-8"))
        sent = socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return bool(sent)
    except Exception as exc:  # noqa: BLE001
        if log is not None:
            log(f"resource_settings_activation_failed error={exc!s}")
        return False


def activate_resource_settings(
    pair: str | None = None,
    *,
    log: Callable[[str], None] | None = None,
) -> bool:
    return send_local_activation_message(
        gui_singleton_socket_name(),
        resource_settings_activation_message(pair),
        log=log,
    )
