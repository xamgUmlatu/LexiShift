from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from lexishift_core import Profile
from ruleset_library_service import (
    analyze_ruleset_delete_impact,
    delete_ruleset_file,
    unlink_ruleset_from_library,
)


def test_analyze_ruleset_delete_impact_reports_linked_and_blocked_profiles() -> None:
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
    impact = analyze_ruleset_delete_impact((profile_blocked, profile_ok), "/tmp/shared.json")
    assert impact.linked_profile_names() == ["A", "B"]
    assert impact.blocked_profile_names() == ["A"]


def test_delete_ruleset_file_removes_existing_file() -> None:
    with TemporaryDirectory() as temp_dir:
        candidate = Path(temp_dir) / "rules.json"
        candidate.write_text("{}", encoding="utf-8")
        delete_ruleset_file(str(candidate))
        assert not candidate.exists()


def test_delete_ruleset_file_is_noop_for_missing_path() -> None:
    with TemporaryDirectory() as temp_dir:
        candidate = Path(temp_dir) / "missing.json"
        delete_ruleset_file(str(candidate))
        assert not candidate.exists()


def test_unlink_ruleset_from_library_updates_active_fallback() -> None:
    profile = Profile(
        profile_id="a",
        name="A",
        dataset_path="/tmp/a.json",
        rulesets=("/tmp/shared.json", "/tmp/a.json"),
        active_ruleset="/tmp/shared.json",
    )
    updated = unlink_ruleset_from_library((profile,), "/tmp/shared.json")
    assert updated[0].rulesets == ("/tmp/a.json",)
    assert updated[0].active_ruleset == "/tmp/a.json"
    assert updated[0].dataset_path == "/tmp/a.json"
