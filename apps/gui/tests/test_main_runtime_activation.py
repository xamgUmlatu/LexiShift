from __future__ import annotations

from main_runtime import (
    ACTIVATION_MESSAGE,
    OPEN_RESOURCE_SETTINGS_FLAG,
    OPEN_RESOURCE_SETTINGS_MESSAGE,
    startup_activation_message,
)


def test_startup_activation_message_defaults_to_activate() -> None:
    assert startup_activation_message(["LexiShift"]) == ACTIVATION_MESSAGE


def test_startup_activation_message_can_route_to_resource_settings() -> None:
    assert (
        startup_activation_message(["LexiShift", OPEN_RESOURCE_SETTINGS_FLAG])
        == OPEN_RESOURCE_SETTINGS_MESSAGE
    )
