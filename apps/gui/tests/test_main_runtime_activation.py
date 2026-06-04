from __future__ import annotations

from main_runtime import (
    ACTIVATION_MESSAGE,
    OPEN_RESOURCE_SETTINGS_FLAG,
    OPEN_RESOURCE_SETTINGS_MESSAGE,
    RESOURCE_PAIR_FLAG,
    resource_pair_from_activation_message,
    startup_activation_message,
)


def test_startup_activation_message_defaults_to_activate() -> None:
    assert startup_activation_message(["LexiShift"]) == ACTIVATION_MESSAGE


def test_startup_activation_message_can_route_to_resource_settings() -> None:
    assert (
        startup_activation_message(["LexiShift", OPEN_RESOURCE_SETTINGS_FLAG])
        == OPEN_RESOURCE_SETTINGS_MESSAGE
    )


def test_startup_activation_message_can_carry_resource_pair() -> None:
    message = startup_activation_message(
        ["LexiShift", OPEN_RESOURCE_SETTINGS_FLAG, RESOURCE_PAIR_FLAG, "en-es"]
    )

    assert message == f"{OPEN_RESOURCE_SETTINGS_MESSAGE}|pair=en-es"
    assert resource_pair_from_activation_message(message) == "en-es"
