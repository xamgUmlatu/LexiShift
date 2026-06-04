from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QStackedWidget, QWidget

from lexishift_core import AppSettings, Profile
from main import MainWindow


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_refresh_ruleset_ui_includes_and_selects_active_ruleset() -> None:
    _app()
    profile = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json",),
        active_ruleset="/tmp/b.json",
    )
    dummy = SimpleNamespace(
        _ruleset_combo_updating=False,
        ruleset_combo=QComboBox(),
        state=SimpleNamespace(
            settings=AppSettings(
                profiles=(profile,),
                active_profile_id="p1",
            )
        ),
    )
    dummy._current_profile = lambda: MainWindow._current_profile(dummy)
    dummy._active_ruleset_path = lambda selected: MainWindow._active_ruleset_path(dummy, selected)

    MainWindow._refresh_ruleset_ui(dummy)

    assert dummy.ruleset_combo.currentData() == "/tmp/b.json"
    values = [dummy.ruleset_combo.itemData(idx) for idx in range(dummy.ruleset_combo.count())]
    assert "/tmp/b.json" in values


def test_update_workspace_mode_shows_empty_page_without_profiles() -> None:
    _app()
    stack = QStackedWidget()
    editor = QWidget()
    empty = QWidget()
    stack.addWidget(editor)
    stack.addWidget(empty)
    stack.setCurrentWidget(editor)

    dummy = SimpleNamespace(
        _workspace_stack=stack,
        _workspace_editor_page=editor,
        _workspace_empty_page=empty,
        state=SimpleNamespace(settings=AppSettings(profiles=tuple(), active_profile_id=None)),
    )
    MainWindow._update_workspace_mode(dummy)
    assert stack.currentWidget() is empty


def test_update_workspace_mode_shows_editor_page_with_profiles() -> None:
    _app()
    profile = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json",),
        active_ruleset="/tmp/a.json",
    )
    stack = QStackedWidget()
    editor = QWidget()
    empty = QWidget()
    stack.addWidget(editor)
    stack.addWidget(empty)
    stack.setCurrentWidget(empty)

    dummy = SimpleNamespace(
        _workspace_stack=stack,
        _workspace_editor_page=editor,
        _workspace_empty_page=empty,
        state=SimpleNamespace(
            settings=AppSettings(
                profiles=(profile,),
                active_profile_id="p1",
            )
        ),
    )
    MainWindow._update_workspace_mode(dummy)
    assert stack.currentWidget() is editor
