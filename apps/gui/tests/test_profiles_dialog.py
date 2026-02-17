from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMessageBox

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
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
        dialog._remove_profile()

    remaining = dialog.result_profiles()
    assert len(remaining) == 1
    assert remaining[0] == profile_b


def test_profile_list_does_not_show_active_marker() -> None:
    _app()
    profile_a = Profile(
        profile_id="a",
        name="A",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json",),
        active_ruleset="/tmp/a.json",
    )
    profile_b = Profile(
        profile_id="b",
        name="B",
        dataset_path="/tmp/b.json",
        rulesets=("/tmp/b.json",),
        active_ruleset="/tmp/b.json",
    )
    dialog = ProfilesDialog((profile_a, profile_b), "a", Path("/tmp"))
    assert dialog.list_widget.item(0).text() == "A"
    assert dialog.list_widget.item(1).text() == "B"


def test_profile_id_is_not_modified_from_manage_dialog() -> None:
    _app()
    profile = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json",),
        active_ruleset="/tmp/a.json",
    )
    dialog = ProfilesDialog((profile,), "p1", Path("/tmp"))
    dialog.name_edit.setText("Renamed")
    dialog._commit_current()
    assert dialog.result_profiles()[0].profile_id == "p1"


def test_ruleset_display_name_hides_path_and_extension() -> None:
    _app()
    profile = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="/tmp/my.profile.rules.json",
        rulesets=("/tmp/my.profile.rules.json",),
        active_ruleset="/tmp/my.profile.rules.json",
    )
    dialog = ProfilesDialog((profile,), "p1", Path("/tmp"))
    display_name = dialog._ruleset_display_name("/tmp/my.profile.rules.json")
    assert display_name == "my.profile.rules"
