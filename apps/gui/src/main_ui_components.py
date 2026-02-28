from __future__ import annotations

from collections.abc import Callable

from helper_logger import set_helper_log_handler
from theme_logger import set_log_handler
from theme_widgets import ThemedBackgroundWidget, apply_theme_background
from utility_dock import UtilityDock
from utils_paths import reveal_path


def configure_log_handlers(
    *,
    error_handler: Callable[[str], None],
    info_handler: Callable[[str], None],
) -> None:
    set_log_handler(error_handler)
    set_helper_log_handler(info_handler)


__all__ = [
    "ThemedBackgroundWidget",
    "UtilityDock",
    "apply_theme_background",
    "configure_log_handlers",
    "reveal_path",
]
