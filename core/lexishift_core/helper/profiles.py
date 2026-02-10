from __future__ import annotations

from pathlib import Path
from typing import Any

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.persistence.settings import AppSettings, Profile, load_app_settings


def _default_ruleset_path(paths: HelperPaths) -> Path:
    return paths.data_root / "rulesets" / "vocab.json"


def _profile_to_dict(profile: Profile) -> dict[str, Any]:
    return {
        "profile_id": profile.profile_id,
        "name": profile.name or profile.profile_id,
        "dataset_path": profile.dataset_path,
        "active_ruleset": profile.active_ruleset or profile.dataset_path,
        "rulesets": list(profile.rulesets or ()),
        "tags": list(profile.tags or ()),
        "description": profile.description,
    }


def _load_settings(paths: HelperPaths) -> tuple[AppSettings, str | None]:
    settings_path = paths.app_settings_path
    if not settings_path.exists():
        return AppSettings(), None
    try:
        return load_app_settings(settings_path), None
    except Exception as exc:  # noqa: BLE001
        return AppSettings(), str(exc)


def _resolve_active_profile_id(settings: AppSettings) -> str:
    configured = str(settings.active_profile_id or "").strip()
    profile_ids = [profile.profile_id for profile in settings.profiles if profile.profile_id]
    if configured and configured in profile_ids:
        return configured
    if profile_ids:
        return profile_ids[0]
    return "default"


def get_profiles_snapshot(paths: HelperPaths) -> dict[str, Any]:
    settings, load_error = _load_settings(paths)
    profiles = [_profile_to_dict(profile) for profile in settings.profiles]
    return {
        "settings_path": str(paths.app_settings_path),
        "settings_exists": paths.app_settings_path.exists(),
        "default_ruleset_path": str(_default_ruleset_path(paths)),
        "profiles": profiles,
        "profiles_count": len(profiles),
        "active_profile_id": settings.active_profile_id,
        "resolved_profile_id": _resolve_active_profile_id(settings),
        "load_error": load_error,
    }
