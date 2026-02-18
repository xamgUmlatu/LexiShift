from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from lexishift_core import Profile
from profile_ruleset_utils import normalize_ruleset_path, preferred_active_ruleset, ruleset_display_name, unique_ruleset_paths


@dataclass(frozen=True)
class ProfileComboItem:
    label: str
    profile: Profile


@dataclass(frozen=True)
class RulesetComboItem:
    path: str
    display_name: str
    missing: bool


def find_profile_by_id(profiles: Sequence[Profile], profile_id: Optional[str]) -> Optional[Profile]:
    target_id = str(profile_id or "").strip()
    for profile in profiles:
        if profile.profile_id == target_id:
            return profile
    return None


def resolve_active_profile(profiles: Sequence[Profile], active_profile_id: Optional[str]) -> Optional[Profile]:
    active = find_profile_by_id(profiles, active_profile_id)
    if active is not None:
        return active
    if profiles:
        return profiles[0]
    return None


def build_profile_combo_items(
    profiles: Sequence[Profile],
    active_profile_id: Optional[str],
) -> tuple[list[ProfileComboItem], int]:
    items: list[ProfileComboItem] = []
    active_index = -1
    for idx, profile in enumerate(profiles):
        items.append(ProfileComboItem(label=profile.name or profile.profile_id, profile=profile))
        if profile.profile_id == active_profile_id:
            active_index = idx
    return items, active_index


def build_ruleset_combo_items(
    profile: Profile,
    *,
    default_dataset_path: str,
) -> tuple[list[RulesetComboItem], int]:
    active_path = preferred_active_ruleset(profile, default_path=default_dataset_path)
    ruleset_paths = unique_ruleset_paths(tuple(profile.rulesets) + (active_path,))
    items: list[RulesetComboItem] = []
    active_index = -1
    for idx, path in enumerate(ruleset_paths):
        missing = not normalize_ruleset_path(path).exists()
        items.append(
            RulesetComboItem(
                path=path,
                display_name=ruleset_display_name(path),
                missing=missing,
            )
        )
        if path == active_path:
            active_index = idx
    return items, active_index
