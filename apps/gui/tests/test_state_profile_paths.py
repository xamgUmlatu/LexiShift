from __future__ import annotations

import os
from pathlib import Path

from lexishift_core import Profile
from state import _normalize_profiles


def test_normalize_profiles_resolves_relative_ruleset_paths_and_active_profile() -> None:
    base_dir = Path("/tmp/lexishift-profile-normalize")
    profile = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="rulesets/a.json",
        rulesets=("rulesets/a.json", "./rulesets/a.json", ""),
        active_ruleset="",
    )

    normalized_profiles, active_profile_id = _normalize_profiles(
        (profile,),
        active_profile_id="missing",
        base_dir=base_dir,
    )

    normalized = normalized_profiles[0]
    expected_path = os.path.normpath(os.path.abspath(str(base_dir / "rulesets" / "a.json")))
    assert normalized.dataset_path == expected_path
    assert normalized.active_ruleset == expected_path
    assert normalized.rulesets == (expected_path,)
    assert active_profile_id == "p1"


def test_normalize_profiles_keeps_explicit_active_ruleset_and_appends_it_to_rulesets() -> None:
    base_dir = Path("/tmp/lexishift-profile-normalize")
    profile = Profile(
        profile_id="p1",
        name="P1",
        dataset_path="rulesets/a.json",
        rulesets=("rulesets/a.json",),
        active_ruleset="rulesets/b.json",
    )

    normalized_profiles, _active_profile_id = _normalize_profiles(
        (profile,),
        active_profile_id="p1",
        base_dir=base_dir,
    )

    normalized = normalized_profiles[0]
    expected_a = os.path.normpath(os.path.abspath(str(base_dir / "rulesets" / "a.json")))
    expected_b = os.path.normpath(os.path.abspath(str(base_dir / "rulesets" / "b.json")))
    assert normalized.active_ruleset == expected_b
    assert normalized.dataset_path == expected_b
    assert normalized.rulesets == (expected_a, expected_b)


def test_normalize_profiles_rewrites_duplicate_and_empty_profile_ids() -> None:
    base_dir = Path("/tmp/lexishift-profile-normalize")
    p1 = Profile(
        profile_id="dup",
        name="",
        dataset_path="rulesets/a.json",
        rulesets=("rulesets/a.json",),
        active_ruleset="rulesets/a.json",
    )
    p2 = Profile(
        profile_id="dup",
        name="Second",
        dataset_path="rulesets/b.json",
        rulesets=("rulesets/b.json",),
        active_ruleset="rulesets/b.json",
    )
    p3 = Profile(
        profile_id="",
        name="",
        dataset_path="rulesets/c.json",
        rulesets=("rulesets/c.json",),
        active_ruleset="rulesets/c.json",
    )

    normalized_profiles, active_profile_id = _normalize_profiles(
        (p1, p2, p3),
        active_profile_id="dup",
        base_dir=base_dir,
    )

    ids = [profile.profile_id for profile in normalized_profiles]
    assert ids == ["dup", "dup-2", "profile"]
    assert normalized_profiles[0].name == "dup"
    assert normalized_profiles[2].name == "profile"
    assert active_profile_id == "dup"
