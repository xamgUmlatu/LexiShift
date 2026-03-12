from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Optional, Sequence

from lexishift_core import Profile


def normalize_ruleset_path(path: str) -> Path:
    return Path(os.path.abspath(os.path.expanduser(path)))


def ruleset_display_name(path: str) -> str:
    normalized = normalize_ruleset_path(path)
    name = normalized.stem.strip()
    if name:
        return name
    raw_name = Path(path).name
    return raw_name or path


def unique_ruleset_paths(paths: Iterable[str | None]) -> list[str]:
    unique: list[str] = []
    for path in paths:
        value = str(path or "").strip()
        if value and value not in unique:
            unique.append(value)
    return unique


def profile_ruleset_paths(profile: Profile) -> list[str]:
    # Canonical profile->ruleset expansion order used across dialogs and main UI.
    return unique_ruleset_paths(
        tuple(profile.rulesets) + (profile.dataset_path, profile.active_ruleset)
    )


def preferred_active_ruleset(profile: Profile, *, default_path: str) -> str:
    if profile.active_ruleset:
        return profile.active_ruleset
    if profile.rulesets:
        return profile.rulesets[0]
    if profile.dataset_path:
        return profile.dataset_path
    return str(default_path or "")


def select_active_ruleset(
    rulesets: Sequence[str],
    *,
    profile_active: Optional[str],
    override_active: Optional[str] = None,
) -> Optional[str]:
    unique = unique_ruleset_paths(rulesets)
    if override_active and override_active in unique:
        return override_active
    if profile_active and profile_active in unique:
        return profile_active
    if unique:
        return unique[0]
    return None


def resolve_profile_dataset_path(profile: Profile, *, default_path: Path) -> Path:
    # Prefer the first real file from active/rulesets/dataset; otherwise use first candidate.
    candidates = unique_ruleset_paths(
        (profile.active_ruleset, *profile.rulesets, profile.dataset_path)
    )
    if not candidates:
        return default_path
    normalized = [normalize_ruleset_path(path) for path in candidates]
    for candidate in normalized:
        if candidate.exists() and candidate.is_file():
            return candidate
    return normalized[0]


def assign_active_ruleset_to_profile(
    profiles: Sequence[Profile],
    *,
    active_profile_id: Optional[str],
    dataset_path: Path | str,
) -> tuple[tuple[Profile, ...], bool]:
    # Main-window rule: selecting a ruleset also links it to the active profile.
    if not active_profile_id:
        return tuple(profiles), False
    path_str = str(dataset_path)
    updated_profiles: list[Profile] = []
    updated = False
    for profile in profiles:
        if profile.profile_id != active_profile_id:
            updated_profiles.append(profile)
            continue
        rulesets = unique_ruleset_paths(tuple(profile.rulesets) + (path_str,))
        updated_profiles.append(
            replace(
                profile,
                dataset_path=path_str,
                rulesets=tuple(rulesets),
                active_ruleset=path_str,
            )
        )
        updated = True
    return tuple(updated_profiles), updated


def collect_profile_rulesets(profiles: Sequence[Profile]) -> list[str]:
    paths: list[str] = []
    for profile in profiles:
        for path in profile_ruleset_paths(profile):
            if path not in paths:
                paths.append(path)
    return paths


def linked_profiles_for_ruleset(profiles: Sequence[Profile], path: str) -> list[Profile]:
    linked: list[Profile] = []
    for profile in profiles:
        if path in profile_ruleset_paths(profile):
            linked.append(profile)
    return linked


def blocked_profiles_for_ruleset_removal(profiles: Sequence[Profile], path: str) -> list[Profile]:
    blocked: list[Profile] = []
    for profile in linked_profiles_for_ruleset(profiles, path):
        remaining = [entry for entry in profile_ruleset_paths(profile) if entry != path]
        if not remaining:
            blocked.append(profile)
    return blocked


def unlink_ruleset_from_profiles(profiles: Sequence[Profile], path: str) -> tuple[Profile, ...]:
    # Keep profiles untouched when unlink would leave them with no rulesets.
    updated_profiles: list[Profile] = []
    for profile in profiles:
        rulesets = profile_ruleset_paths(profile)
        if path not in rulesets:
            updated_profiles.append(profile)
            continue
        remaining = [entry for entry in rulesets if entry != path]
        if not remaining:
            updated_profiles.append(profile)
            continue
        active = profile.active_ruleset
        if not active or active == path or active not in remaining:
            active = remaining[0]
        updated_profiles.append(
            replace(
                profile,
                dataset_path=active,
                rulesets=tuple(remaining),
                active_ruleset=active,
            )
        )
    return tuple(updated_profiles)
