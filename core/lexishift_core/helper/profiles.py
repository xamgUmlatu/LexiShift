from __future__ import annotations

from pathlib import Path
from typing import Any

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.persistence.settings import AppSettings, Profile, load_app_settings
from lexishift_core.persistence.storage import dataset_to_dict, load_vocab_dataset


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


def _profile_rulesets(profile: Profile) -> list[str]:
    rulesets: list[str] = []
    for raw_path in tuple(profile.rulesets) + (profile.dataset_path, profile.active_ruleset):
        path = str(raw_path or "").strip()
        if path and path not in rulesets:
            rulesets.append(path)
    return rulesets


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


def _resolve_profile(settings: AppSettings, requested_profile_id: str | None) -> tuple[Profile | None, str]:
    requested = str(requested_profile_id or "").strip()
    if requested:
        for profile in settings.profiles:
            if profile.profile_id == requested:
                return profile, requested
    resolved_profile_id = _resolve_active_profile_id(settings)
    for profile in settings.profiles:
        if profile.profile_id == resolved_profile_id:
            return profile, resolved_profile_id
    return None, resolved_profile_id


def _resolve_ruleset_path(raw_path: str, *, settings_path: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = settings_path.parent / candidate
    return candidate.resolve()


def _ruleset_payload(raw_path: str, *, settings_path: Path) -> dict[str, Any]:
    resolved_path = _resolve_ruleset_path(raw_path, settings_path=settings_path)
    payload: dict[str, Any] = {
        "path": raw_path,
        "resolved_path": str(resolved_path),
        "exists": resolved_path.exists(),
        "rules": [],
        "rules_count": 0,
        "error": None,
    }
    if not resolved_path.exists():
        payload["error"] = "Ruleset file not found."
        return payload
    try:
        dataset = load_vocab_dataset(resolved_path)
        serialized = dataset_to_dict(dataset)
        rules = serialized.get("rules", [])
        if not isinstance(rules, list):
            payload["error"] = "Ruleset payload did not contain a rules array."
            return payload
        payload["rules"] = rules
        payload["rules_count"] = len(rules)
    except Exception as exc:  # noqa: BLE001
        payload["error"] = str(exc)
    return payload


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


def get_profile_rulesets_snapshot(paths: HelperPaths, *, profile_id: str | None = None) -> dict[str, Any]:
    settings, load_error = _load_settings(paths)
    requested_profile_id = str(profile_id or "").strip() or None
    profile, resolved_profile_id = _resolve_profile(settings, requested_profile_id)
    rulesets = (
        [_ruleset_payload(path, settings_path=paths.app_settings_path) for path in _profile_rulesets(profile)]
        if profile is not None
        else []
    )
    return {
        "settings_path": str(paths.app_settings_path),
        "settings_exists": paths.app_settings_path.exists(),
        "requested_profile_id": requested_profile_id,
        "active_profile_id": settings.active_profile_id,
        "resolved_profile_id": resolved_profile_id,
        "profile_found": profile is not None,
        "profile": (_profile_to_dict(profile) if profile is not None else None),
        "rulesets": rulesets,
        "rulesets_count": len(rulesets),
        "load_error": load_error,
    }
