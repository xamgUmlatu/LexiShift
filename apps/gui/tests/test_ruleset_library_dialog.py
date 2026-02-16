from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from dialogs_rulesets import RulesetLibraryDialog
from lexishift_core import Profile


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_unlink_ruleset_updates_profiles_and_active_path() -> None:
    _app()
    profile_a = Profile(
        profile_id="a",
        name="A",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json", "/tmp/shared.json"),
        active_ruleset="/tmp/shared.json",
    )
    profile_b = Profile(
        profile_id="b",
        name="B",
        dataset_path="/tmp/b.json",
        rulesets=("/tmp/shared.json", "/tmp/b.json"),
        active_ruleset="/tmp/shared.json",
    )
    dialog = RulesetLibraryDialog((profile_a, profile_b))
    dialog._unlink_ruleset("/tmp/shared.json")
    updated = dialog.result_profiles()

    assert updated[0].rulesets == ("/tmp/a.json",)
    assert updated[0].active_ruleset == "/tmp/a.json"
    assert updated[0].dataset_path == "/tmp/a.json"

    assert updated[1].rulesets == ("/tmp/b.json",)
    assert updated[1].active_ruleset == "/tmp/b.json"
    assert updated[1].dataset_path == "/tmp/b.json"


def test_ruleset_list_collects_unique_paths() -> None:
    _app()
    profile = Profile(
        profile_id="a",
        name="A",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json", "/tmp/b.json", "/tmp/a.json"),
        active_ruleset="/tmp/b.json",
    )
    dialog = RulesetLibraryDialog((profile,))
    collected = dialog._collect_rulesets()
    assert collected == ["/tmp/a.json", "/tmp/b.json"]


def test_ruleset_list_displays_stem_without_path_or_extension() -> None:
    _app()
    profile = Profile(
        profile_id="a",
        name="A",
        dataset_path="/tmp/my.custom.ruleset.json",
        rulesets=("/tmp/my.custom.ruleset.json",),
        active_ruleset="/tmp/my.custom.ruleset.json",
    )
    dialog = RulesetLibraryDialog((profile,))
    display_name = dialog._ruleset_display_name("/tmp/my.custom.ruleset.json")
    assert display_name == "my.custom.ruleset"
    item = dialog.ruleset_list.item(0)
    assert item is not None
    text = item.text()
    assert "/tmp" not in text
    assert ".json" not in text
