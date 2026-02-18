from __future__ import annotations

from dataclasses import replace
from typing import Optional, Sequence

from lexishift_core import Profile
from profile_ruleset_utils import select_active_ruleset, unique_ruleset_paths


def commit_profile_edits(
    profile: Profile,
    *,
    name: str,
    rulesets: Sequence[str],
    override_active: Optional[str],
) -> tuple[Profile, Optional[str]]:
    cleaned_rulesets = unique_ruleset_paths(rulesets)
    active_ruleset = select_active_ruleset(
        cleaned_rulesets,
        profile_active=profile.active_ruleset,
        override_active=override_active,
    )
    updated = replace(
        profile,
        name=name.strip() or profile.profile_id,
        dataset_path=active_ruleset or profile.dataset_path,
        rulesets=tuple(cleaned_rulesets),
        active_ruleset=active_ruleset,
    )
    return updated, active_ruleset


def add_ruleset_to_editor_state(
    profile: Profile,
    *,
    current_rulesets: Sequence[str],
    added_path: str,
    override_active: Optional[str],
) -> tuple[list[str], Optional[str]]:
    rulesets = unique_ruleset_paths(tuple(current_rulesets) + (added_path,))
    active = select_active_ruleset(
        rulesets,
        profile_active=profile.active_ruleset,
        override_active=override_active,
    )
    if active is None:
        active = added_path
    return rulesets, active


def remove_ruleset_from_editor_state(
    profile: Profile,
    *,
    current_rulesets: Sequence[str],
    removed_path: str,
    override_active: Optional[str],
) -> tuple[list[str], Optional[str]]:
    rulesets = [path for path in unique_ruleset_paths(current_rulesets) if path != removed_path]
    active = select_active_ruleset(
        rulesets,
        profile_active=profile.active_ruleset,
        override_active=override_active,
    )
    return rulesets, active


def set_active_ruleset_in_editor_state(
    current_rulesets: Sequence[str],
    *,
    active_path: str,
) -> tuple[list[str], str]:
    rulesets = unique_ruleset_paths(tuple(current_rulesets) + (active_path,))
    return rulesets, active_path
