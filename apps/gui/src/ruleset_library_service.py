from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from lexishift_core import Profile
from profile_ruleset_utils import (
    blocked_profiles_for_ruleset_removal,
    linked_profiles_for_ruleset,
    normalize_ruleset_path,
    unlink_ruleset_from_profiles,
)


@dataclass(frozen=True)
class RulesetDeleteImpact:
    path: str
    linked_profiles: tuple[Profile, ...]
    blocked_profiles: tuple[Profile, ...]

    def linked_profile_names(self) -> list[str]:
        return [profile.name or profile.profile_id for profile in self.linked_profiles]

    def blocked_profile_names(self) -> list[str]:
        return [profile.name or profile.profile_id for profile in self.blocked_profiles]


def analyze_ruleset_delete_impact(profiles: Sequence[Profile], path: str) -> RulesetDeleteImpact:
    linked = tuple(linked_profiles_for_ruleset(profiles, path))
    blocked = tuple(blocked_profiles_for_ruleset_removal(profiles, path))
    return RulesetDeleteImpact(path=str(path or ""), linked_profiles=linked, blocked_profiles=blocked)


def delete_ruleset_file(path: str) -> None:
    resolved = normalize_ruleset_path(path)
    if resolved.exists() and resolved.is_file():
        resolved.unlink()


def unlink_ruleset_from_library(profiles: Sequence[Profile], path: str) -> tuple[Profile, ...]:
    return unlink_ruleset_from_profiles(profiles, path)
