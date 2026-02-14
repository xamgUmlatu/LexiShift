from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from dialogs_profiles import ProfilesDialog
from lexishift_core import Profile


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_profiles_dialog_initial_selection_does_not_mutate_profile() -> None:
    _app()
    profile = Profile(
        profile_id="p1",
        name="My Profile",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json", "/tmp/b.json"),
        active_ruleset="/tmp/b.json",
        description="desc",
        tags=("x", "y"),
    )
    dialog = ProfilesDialog((profile,), "p1", Path("/tmp"))
    assert dialog.result_profiles()[0] == profile


def test_set_active_ruleset_persists_selected_ruleset() -> None:
    _app()
    profile = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json", "/tmp/b.json"),
        active_ruleset="/tmp/a.json",
    )
    dialog = ProfilesDialog((profile,), "p1", Path("/tmp"))
    dialog.ruleset_list.setCurrentRow(1)
    dialog._set_active_ruleset()
    assert dialog.result_profiles()[0].active_ruleset == "/tmp/b.json"


def test_remove_profile_keeps_remaining_profile_data() -> None:
    _app()
    profile_a = Profile(
        profile_id="a",
        name="A",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json",),
        active_ruleset="/tmp/a.json",
        description="descA",
        tags=("ta",),
    )
    profile_b = Profile(
        profile_id="b",
        name="B",
        dataset_path="/tmp/b.json",
        rulesets=("/tmp/b.json",),
        active_ruleset="/tmp/b.json",
        description="descB",
        tags=("tb",),
    )
    dialog = ProfilesDialog((profile_a, profile_b), "a", Path("/tmp"))
    dialog.list_widget.setCurrentRow(0)
    dialog._remove_profile()

    remaining = dialog.result_profiles()
    assert len(remaining) == 1
    assert remaining[0] == profile_b
