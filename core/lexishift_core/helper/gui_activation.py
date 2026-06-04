from __future__ import annotations

import getpass
from typing import Callable

OPEN_RESOURCE_SETTINGS_MESSAGE = "OPEN_SETTINGS:resources"


def gui_singleton_socket_name() -> str:
    return f"LexiShiftGUI_{getpass.getuser()}"


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
    session_id: str | None = None,
    log: Callable[[str], None] | None = None,
) -> bool:
    return send_local_activation_message(
        gui_singleton_socket_name(),
        resource_settings_activation_message(pair, session_id=session_id),
        log=log,
    )
