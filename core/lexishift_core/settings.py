from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


@dataclass(frozen=True)
class Profile:
    profile_id: str
    name: str
    dataset_path: str
    description: Optional[str] = None
    tags: Sequence[str] = field(default_factory=tuple)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    rulesets: Sequence[str] = field(default_factory=tuple)
    active_ruleset: Optional[str] = None


@dataclass(frozen=True)
class ImportExportSettings:
    allow_code_export: bool = True
    default_export_format: str = "json"  # json, code
    last_import_path: Optional[str] = None
    last_export_path: Optional[str] = None


@dataclass(frozen=True)
class SynonymSourceSettings:
    wordnet_dir: Optional[str] = None
    moby_path: Optional[str] = None
    max_synonyms: int = 30
    include_phrases: bool = False
    lower_case: bool = True
    require_consensus: bool = False
    use_embeddings: bool = False
    embedding_path: Optional[str] = None
    embedding_threshold: float = 0.0
    embedding_fallback: bool = True


@dataclass(frozen=True)
class AppSettings:
    profiles: Sequence[Profile] = field(default_factory=tuple)
    active_profile_id: Optional[str] = None
    import_export: Optional[ImportExportSettings] = None
    synonyms: Optional[SynonymSourceSettings] = None
    version: int = 1


def load_app_settings(path: str | Path) -> AppSettings:
    payload = Path(path).read_text(encoding="utf-8")
    data = json.loads(payload)
    return settings_from_dict(data)


def save_app_settings(settings: AppSettings, path: str | Path) -> None:
    data = settings_to_dict(settings)
    payload = json.dumps(data, indent=2, sort_keys=True)
    Path(path).write_text(payload, encoding="utf-8")


def settings_from_dict(data: Mapping[str, Any]) -> AppSettings:
    profiles = tuple(_profile_from_dict(item) for item in data.get("profiles", []))
    import_export = _import_export_from_dict(data.get("import_export"))
    synonyms = _synonym_sources_from_dict(data.get("synonyms"))
    return AppSettings(
        profiles=profiles,
        active_profile_id=data.get("active_profile_id"),
        import_export=import_export,
        synonyms=synonyms,
        version=int(data.get("version", 1)),
    )


def settings_to_dict(settings: AppSettings) -> dict[str, Any]:
    data: dict[str, Any] = {
        "version": settings.version,
        "profiles": [_profile_to_dict(profile) for profile in settings.profiles],
        "active_profile_id": settings.active_profile_id,
        "import_export": _import_export_to_dict(settings.import_export),
        "synonyms": _synonym_sources_to_dict(settings.synonyms),
    }
    trimmed = {key: value for key, value in data.items() if value not in (None, [], {})}
    return trimmed


def _profile_from_dict(data: Mapping[str, Any]) -> Profile:
    dataset_path = str(data.get("dataset_path", ""))
    rulesets = tuple(data.get("rulesets", []))
    if not rulesets and dataset_path:
        rulesets = (dataset_path,)
    active_ruleset = data.get("active_ruleset") or dataset_path or (rulesets[0] if rulesets else None)
    return Profile(
        profile_id=str(data.get("profile_id", "")),
        name=str(data.get("name", "")),
        dataset_path=str(active_ruleset or dataset_path),
        description=data.get("description"),
        tags=tuple(data.get("tags", [])),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        rulesets=rulesets,
        active_ruleset=active_ruleset,
    )


def _profile_to_dict(profile: Profile) -> dict[str, Any]:
    dataset_path = profile.dataset_path or profile.active_ruleset or (profile.rulesets[0] if profile.rulesets else "")
    data: dict[str, Any] = {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "dataset_path": dataset_path,
        "description": profile.description,
        "tags": list(profile.tags),
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
        "rulesets": list(profile.rulesets),
        "active_ruleset": profile.active_ruleset,
    }
    return {key: value for key, value in data.items() if value not in (None, [], "")}


def _import_export_from_dict(data: Optional[Mapping[str, Any]]) -> Optional[ImportExportSettings]:
    if not data:
        return None
    return ImportExportSettings(
        allow_code_export=bool(data.get("allow_code_export", True)),
        default_export_format=str(data.get("default_export_format", "json")),
        last_import_path=data.get("last_import_path"),
        last_export_path=data.get("last_export_path"),
    )


def _import_export_to_dict(settings: Optional[ImportExportSettings]) -> Optional[dict[str, Any]]:
    if settings is None:
        return None
    data: dict[str, Any] = {
        "allow_code_export": settings.allow_code_export,
        "default_export_format": settings.default_export_format,
        "last_import_path": settings.last_import_path,
        "last_export_path": settings.last_export_path,
    }
    trimmed = {key: value for key, value in data.items() if value not in (None, [])}
    return trimmed or None


def _synonym_sources_from_dict(data: Optional[Mapping[str, Any]]) -> Optional[SynonymSourceSettings]:
    if not data:
        return None
    return SynonymSourceSettings(
        wordnet_dir=data.get("wordnet_dir"),
        moby_path=data.get("moby_path"),
        max_synonyms=int(data.get("max_synonyms", 30)),
        include_phrases=bool(data.get("include_phrases", False)),
        lower_case=bool(data.get("lower_case", True)),
        require_consensus=bool(data.get("require_consensus", False)),
        use_embeddings=bool(data.get("use_embeddings", False)),
        embedding_path=data.get("embedding_path"),
        embedding_threshold=float(data.get("embedding_threshold", 0.0)),
        embedding_fallback=bool(data.get("embedding_fallback", True)),
    )


def _synonym_sources_to_dict(settings: Optional[SynonymSourceSettings]) -> Optional[dict[str, Any]]:
    if settings is None:
        return None
    data: dict[str, Any] = {
        "wordnet_dir": settings.wordnet_dir,
        "moby_path": settings.moby_path,
        "max_synonyms": settings.max_synonyms,
        "include_phrases": settings.include_phrases,
        "lower_case": settings.lower_case,
        "require_consensus": settings.require_consensus,
        "use_embeddings": settings.use_embeddings,
        "embedding_path": settings.embedding_path,
        "embedding_threshold": settings.embedding_threshold,
        "embedding_fallback": settings.embedding_fallback,
    }
    trimmed = {key: value for key, value in data.items() if value not in (None, [], "")}
    return trimmed or None
