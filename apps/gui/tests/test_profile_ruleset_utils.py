from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from lexishift_core import Profile
from profile_ruleset_utils import (
    assign_active_ruleset_to_profile,
    blocked_profiles_for_ruleset_removal,
    collect_profile_rulesets,
    linked_profiles_for_ruleset,
    preferred_active_ruleset,
    profile_ruleset_paths,
    resolve_profile_dataset_path,
    unlink_ruleset_from_profiles,
)


def test_profile_ruleset_paths_are_unique_and_ordered() -> None:
    profile = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="/tmp/b.json",
        rulesets=("/tmp/a.json", "/tmp/a.json", "/tmp/b.json"),
        active_ruleset="/tmp/c.json",
    )
    assert profile_ruleset_paths(profile) == ["/tmp/a.json", "/tmp/b.json", "/tmp/c.json"]


def test_preferred_active_ruleset_fallback_chain() -> None:
    profile_ruleset = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="/tmp/d.json",
        rulesets=("/tmp/r.json",),
        active_ruleset="",
    )
    assert (
        preferred_active_ruleset(profile_ruleset, default_path="/tmp/default.json") == "/tmp/r.json"
    )

    profile_dataset = Profile(
        profile_id="p2",
        name="P2",
        dataset_path="/tmp/d.json",
        rulesets=tuple(),
        active_ruleset="",
    )
    assert (
        preferred_active_ruleset(profile_dataset, default_path="/tmp/default.json") == "/tmp/d.json"
    )

    profile_default = Profile(
        profile_id="p3",
        name="P3",
        dataset_path="",
        rulesets=tuple(),
        active_ruleset="",
    )
    assert (
        preferred_active_ruleset(profile_default, default_path="/tmp/default.json")
        == "/tmp/default.json"
    )


def test_resolve_profile_dataset_path_prefers_existing_file() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        existing = root / "exists.json"
        existing.write_text("{}", encoding="utf-8")
        missing = root / "missing.json"
        profile = Profile(
            profile_id="p1",
            name="P1",
            dataset_path=str(missing),
            rulesets=(str(missing), str(existing)),
            active_ruleset=str(missing),
        )
        resolved = resolve_profile_dataset_path(profile, default_path=root / "default.json")
        assert resolved == existing


def test_assign_active_ruleset_to_profile_updates_matching_profile() -> None:
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
    updated, changed = assign_active_ruleset_to_profile(
        (profile_a, profile_b),
        active_profile_id="b",
        dataset_path="/tmp/new.json",
    )
    assert changed is True
    assert updated[0] == profile_a
    assert updated[1].dataset_path == "/tmp/new.json"
    assert updated[1].active_ruleset == "/tmp/new.json"
    assert updated[1].rulesets == ("/tmp/b.json", "/tmp/new.json")


def test_blocked_profiles_for_removal_and_unlink_behavior() -> None:
    profile_blocked = Profile(
        profile_id="a",
        name="A",
        dataset_path="/tmp/shared.json",
        rulesets=("/tmp/shared.json",),
        active_ruleset="/tmp/shared.json",
    )
    profile_ok = Profile(
        profile_id="b",
        name="B",
        dataset_path="/tmp/b.json",
        rulesets=("/tmp/shared.json", "/tmp/b.json"),
        active_ruleset="/tmp/shared.json",
    )
    blocked = blocked_profiles_for_ruleset_removal(
        (profile_blocked, profile_ok), "/tmp/shared.json"
    )
    assert [profile.profile_id for profile in blocked] == ["a"]

    unlinked = unlink_ruleset_from_profiles((profile_blocked, profile_ok), "/tmp/shared.json")
    assert unlinked[0] == profile_blocked
    assert unlinked[1].rulesets == ("/tmp/b.json",)
    assert unlinked[1].active_ruleset == "/tmp/b.json"
    assert unlinked[1].dataset_path == "/tmp/b.json"


def test_collect_rulesets_and_linked_profiles() -> None:
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
        rulesets=("/tmp/b.json", "/tmp/shared.json"),
        active_ruleset="/tmp/b.json",
    )
    assert collect_profile_rulesets((profile_a, profile_b)) == [
        "/tmp/a.json",
        "/tmp/shared.json",
        "/tmp/b.json",
    ]
    linked = linked_profiles_for_ruleset((profile_a, profile_b), "/tmp/shared.json")
    assert [profile.profile_id for profile in linked] == ["a", "b"]
