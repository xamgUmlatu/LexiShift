from __future__ import annotations

from lexishift_core import Profile
from profile_ruleset_service import (
    add_ruleset_to_editor_state,
    commit_profile_edits,
    remove_ruleset_from_editor_state,
    set_active_ruleset_in_editor_state,
)


def test_commit_profile_edits_preserves_profile_id_and_updates_active_dataset() -> None:
    profile = Profile(
        profile_id="p1",
        name="Old",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json", "/tmp/b.json"),
        active_ruleset="/tmp/a.json",
    )
    updated, active = commit_profile_edits(
        profile,
        name="Renamed",
        rulesets=["/tmp/a.json", "/tmp/b.json"],
        override_active="/tmp/b.json",
    )
    assert active == "/tmp/b.json"
    assert updated.profile_id == "p1"
    assert updated.name == "Renamed"
    assert updated.active_ruleset == "/tmp/b.json"
    assert updated.dataset_path == "/tmp/b.json"


def test_add_ruleset_to_editor_state_uses_profile_active_when_present() -> None:
    profile = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json",),
        active_ruleset="/tmp/a.json",
    )
    rulesets, active = add_ruleset_to_editor_state(
        profile,
        current_rulesets=["/tmp/a.json"],
        added_path="/tmp/new.json",
        override_active=None,
    )
    assert rulesets == ["/tmp/a.json", "/tmp/new.json"]
    assert active == "/tmp/a.json"


def test_remove_ruleset_from_editor_state_falls_back_to_remaining_ruleset() -> None:
    profile = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/a.json", "/tmp/b.json"),
        active_ruleset="/tmp/a.json",
    )
    rulesets, active = remove_ruleset_from_editor_state(
        profile,
        current_rulesets=["/tmp/a.json", "/tmp/b.json"],
        removed_path="/tmp/a.json",
        override_active="/tmp/a.json",
    )
    assert rulesets == ["/tmp/b.json"]
    assert active == "/tmp/b.json"


def test_set_active_ruleset_in_editor_state_adds_missing_active_path() -> None:
    rulesets, active = set_active_ruleset_in_editor_state(
        ["/tmp/a.json"],
        active_path="/tmp/missing.json",
    )
    assert rulesets == ["/tmp/a.json", "/tmp/missing.json"]
    assert active == "/tmp/missing.json"
