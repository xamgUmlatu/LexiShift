from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from lexishift_core import Profile
from main_profile_ruleset_service import (
    build_profile_combo_items,
    build_ruleset_combo_items,
    resolve_active_profile,
)


def test_resolve_active_profile_falls_back_to_first_when_missing() -> None:
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
    resolved = resolve_active_profile((profile_a, profile_b), "missing")
    assert resolved == profile_a


def test_build_profile_combo_items_returns_active_index_and_labels() -> None:
    profile_a = Profile(
        profile_id="a",
        name="Alpha",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json",),
        active_ruleset="/tmp/a.json",
    )
    profile_b = Profile(
        profile_id="b",
        name="",
        dataset_path="/tmp/b.json",
        rulesets=("/tmp/b.json",),
        active_ruleset="/tmp/b.json",
    )
    items, active_index = build_profile_combo_items((profile_a, profile_b), "b")
    assert [item.label for item in items] == ["Alpha", "b"]
    assert active_index == 1


def test_build_ruleset_combo_items_marks_missing_and_keeps_active() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        existing = root / "exists.json"
        existing.write_text("{}", encoding="utf-8")
        missing = root / "missing.json"
        profile = Profile(
            profile_id="p1",
            name="P1",
            dataset_path=str(existing),
            rulesets=(str(existing),),
            active_ruleset=str(missing),
        )
        items, active_index = build_ruleset_combo_items(
            profile,
            default_dataset_path=str(root / "default.json"),
        )
        assert [item.path for item in items] == [str(existing), str(missing)]
        assert [item.missing for item in items] == [False, True]
        assert active_index == 1
