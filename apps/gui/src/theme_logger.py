from __future__ import annotations

from typing import Callable, Optional

_log_handler: Optional[Callable[[str], None]] = None


def set_log_handler(handler: Callable[[str], None] | None) -> None:
    global _log_handler
    _log_handler = handler


def log_theme(message: str) -> None:
    if not message:
        return
    if _log_handler:
        _log_handler(message)
    else:
        print(message)
