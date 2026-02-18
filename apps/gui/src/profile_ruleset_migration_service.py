from __future__ import annotations

import os
from dataclasses import replace
from typing import Optional, Sequence

from lexishift_core import Profile


def migrate_profile_ruleset_paths(
    profiles: Sequence[Profile],
    *,
    base_dir: str | os.PathLike[str],
    rulesets_dir: str | os.PathLike[str],
) -> tuple[tuple[Profile, ...], bool]:
    base_dir_abs = os.path.abspath(str(base_dir))
    rulesets_dir_abs = os.path.abspath(str(rulesets_dir))
    changed = False
    updated_profiles: list[Profile] = []

    def migrate_path(path: Optional[str]) -> tuple[Optional[str], bool]:
        if not path:
            return path, False
        expanded = os.path.abspath(os.path.expanduser(path))
        if expanded.startswith(rulesets_dir_abs + os.sep):
            return path, False
        try:
            if os.path.commonpath([expanded, base_dir_abs]) != base_dir_abs:
                return path, False
        except ValueError:
            return path, False
        if not os.path.exists(expanded):
            return path, False
        new_path = os.path.join(rulesets_dir_abs, os.path.basename(expanded))
        if expanded != new_path:
            os.makedirs(rulesets_dir_abs, exist_ok=True)
            if not os.path.exists(new_path):
                try:
                    os.replace(expanded, new_path)
                except OSError:
                    return path, False
            return new_path, True
        return path, False

    for profile in profiles:
        dataset_path, changed_dataset = migrate_path(profile.dataset_path)
        active_ruleset, changed_active = migrate_path(profile.active_ruleset)
        rulesets: list[str] = []
        changed_rulesets = False
        for ruleset_path in profile.rulesets:
            migrated, changed_rule = migrate_path(ruleset_path)
            rulesets.append(migrated or ruleset_path)
            changed_rulesets = changed_rulesets or changed_rule
        if changed_dataset or changed_active or changed_rulesets:
            changed = True
            updated_profiles.append(
                replace(
                    profile,
                    dataset_path=dataset_path or profile.dataset_path,
                    active_ruleset=active_ruleset or profile.active_ruleset,
                    rulesets=tuple(rulesets),
                )
            )
        else:
            updated_profiles.append(profile)

    return tuple(updated_profiles), changed
