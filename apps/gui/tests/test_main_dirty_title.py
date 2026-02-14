from __future__ import annotations

from types import SimpleNamespace

from main import MainWindow


class _Toggle:
    def __init__(self) -> None:
        self.enabled = False

    def setEnabled(self, value: bool) -> None:
        self.enabled = bool(value)


def test_dirty_state_updates_save_actions_and_window_title() -> None:
    dummy = SimpleNamespace(
        _save_action=_Toggle(),
        save_ruleset_button=_Toggle(),
        _window_title_base="LexiShift",
        state=SimpleNamespace(dirty=False),
        window_title="",
    )

    def _set_window_title(title: str) -> None:
        dummy.window_title = title

    dummy.setWindowTitle = _set_window_title
    dummy._refresh_window_title = lambda dirty=None: MainWindow._refresh_window_title(dummy, dirty)

    MainWindow._on_dirty_changed(dummy, True)
    assert dummy._save_action.enabled is True
    assert dummy.save_ruleset_button.enabled is True
    assert dummy.window_title == "LexiShift *"

    MainWindow._on_dirty_changed(dummy, False)
    assert dummy._save_action.enabled is False
    assert dummy.save_ruleset_button.enabled is False
    assert dummy.window_title == "LexiShift"
