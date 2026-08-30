from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal

from lexishift_core import (
    AppSettings,
    Profile,
    SrsStore,
    SynonymSourceSettings,
    VocabDataset,
    load_app_settings,
    load_srs_store,
    load_vocab_dataset,
    save_app_settings,
    save_srs_store,
    save_vocab_dataset,
)
from lexishift_core.helper.installed_packs import (
    installed_pack_root,
    load_installed_pack_manifest,
    resolve_installed_pack_artifact,
)
from language_packs import CROSS_EMBEDDING_PACKS, EMBEDDING_PACKS
from main_paths import _app_data_dir


_EMBEDDING_PAIR_KEY_BY_PACK_ID: dict[str, str] = {
    str(pack.pack_id): str(pack.pair_key)
    for pack in (*EMBEDDING_PACKS, *CROSS_EMBEDDING_PACKS)
    if str(getattr(pack, "pack_id", "")).strip() and str(getattr(pack, "pair_key", "")).strip()
}
_RETIRED_MANAGED_FREQUENCY_PACK_IDS = frozenset({"freq-es-cde"})


def _normalize_profile_path(path: Optional[str], *, base_dir: Path) -> Optional[str]:
    raw = str(path or "").strip()
    if not raw:
        return None
    expanded = os.path.expanduser(raw)
    if not os.path.isabs(expanded):
        expanded = os.path.join(str(base_dir), expanded)
    return os.path.normpath(os.path.abspath(expanded))


def _normalize_profile_id(raw_profile_id: Optional[str], used_ids: set[str]) -> str:
    base = str(raw_profile_id or "").strip() or "profile"
    candidate = base
    suffix = 2
    while candidate in used_ids:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used_ids.add(candidate)
    return candidate


def _normalize_profiles(
    profiles: tuple[Profile, ...],
    *,
    active_profile_id: Optional[str],
    base_dir: Path,
) -> tuple[tuple[Profile, ...], Optional[str]]:
    normalized_profiles: list[Profile] = []
    used_ids: set[str] = set()
    id_mapping: dict[str, str] = {}
    for profile in profiles:
        original_profile_id = str(profile.profile_id or "").strip()
        normalized_profile_id = _normalize_profile_id(original_profile_id, used_ids)
        if original_profile_id and original_profile_id not in id_mapping:
            id_mapping[original_profile_id] = normalized_profile_id

        rulesets: list[str] = []
        for raw_path in tuple(profile.rulesets) + (profile.dataset_path, profile.active_ruleset):
            normalized_path = _normalize_profile_path(raw_path, base_dir=base_dir)
            if normalized_path and normalized_path not in rulesets:
                rulesets.append(normalized_path)

        preferred_active = (
            _normalize_profile_path(profile.active_ruleset, base_dir=base_dir)
            or _normalize_profile_path(profile.dataset_path, base_dir=base_dir)
            or (rulesets[0] if rulesets else None)
        )
        if preferred_active and preferred_active not in rulesets:
            rulesets.append(preferred_active)

        if not rulesets:
            fallback_id = normalized_profile_id
            fallback = _normalize_profile_path(
                str(Path("rulesets") / f"{fallback_id}.json"),
                base_dir=base_dir,
            )
            if fallback:
                rulesets = [fallback]
                preferred_active = fallback

        active_ruleset = preferred_active or (rulesets[0] if rulesets else None)
        dataset_path = active_ruleset or ""
        normalized_profiles.append(
            replace(
                profile,
                profile_id=normalized_profile_id,
                name=(profile.name or "").strip() or normalized_profile_id,
                dataset_path=dataset_path,
                rulesets=tuple(rulesets),
                active_ruleset=active_ruleset,
            )
        )

    normalized = tuple(normalized_profiles)
    profile_ids = [profile.profile_id for profile in normalized if profile.profile_id]
    active_raw = str(active_profile_id or "").strip()
    mapped_active = id_mapping.get(active_raw, active_raw)
    resolved_active = (
        mapped_active if mapped_active in profile_ids else (profile_ids[0] if profile_ids else None)
    )
    return normalized, resolved_active


def _normalize_synonym_pack_settings(
    settings: Optional[SynonymSourceSettings],
) -> Optional[SynonymSourceSettings]:
    if settings is None:
        return None
    app_data_dir = _app_data_dir()
    managed_language_pack_ids, language_pack_paths = _split_managed_pack_paths(
        base_dir=app_data_dir / "language_packs",
        configured_paths=settings.language_pack_paths,
        configured_ids=settings.managed_language_pack_ids,
    )
    managed_frequency_pack_ids, frequency_pack_paths = _split_managed_pack_paths(
        base_dir=app_data_dir / "frequency_packs",
        configured_paths=settings.frequency_pack_paths,
        configured_ids=settings.managed_frequency_pack_ids,
        retired_pack_ids=_RETIRED_MANAGED_FREQUENCY_PACK_IDS,
    )
    embedding_pack_paths, embedding_pair_pack_ids, embedding_pair_paths, embedding_pair_enabled = (
        _normalize_embedding_pack_settings(
            app_data_dir=app_data_dir,
            settings=settings,
        )
    )
    normalized = replace(
        settings,
        managed_language_pack_ids=managed_language_pack_ids,
        language_pack_paths=language_pack_paths,
        managed_frequency_pack_ids=managed_frequency_pack_ids,
        frequency_pack_paths=frequency_pack_paths,
        embedding_pack_paths=embedding_pack_paths,
        embedding_pair_pack_ids=embedding_pair_pack_ids,
        embedding_pair_paths=embedding_pair_paths,
        embedding_pair_enabled=embedding_pair_enabled,
    )
    return normalized


def _normalize_embedding_pack_settings(
    *,
    app_data_dir: Path,
    settings: SynonymSourceSettings,
) -> tuple[dict[str, str], dict[str, list[str]], dict[str, list[str]], dict[str, bool]]:
    base_dir = app_data_dir / "embedding_packs"
    managed_pack_ids: set[str] = set()
    manual_embedding_packs: dict[str, str] = {}
    for pack_id, raw_path in dict(settings.embedding_pack_paths or {}).items():
        pack_key = str(pack_id or "").strip()
        path_text = str(raw_path or "").strip()
        if not pack_key or not path_text:
            continue
        if _is_managed_pack_path(base_dir=base_dir, pack_id=pack_key, raw_path=path_text):
            managed_pack_ids.add(pack_key)
            continue
        manual_embedding_packs[pack_key] = path_text

    pair_pack_ids: dict[str, list[str]] = {
        str(pair_key): [str(value) for value in values if str(value).strip()]
        for pair_key, values in dict(settings.embedding_pair_pack_ids or {}).items()
        if str(pair_key).strip() and isinstance(values, (list, tuple))
    }
    pair_paths: dict[str, list[str]] = {}
    pair_enabled = dict(settings.embedding_pair_enabled or {})

    for managed_pack_id in sorted(managed_pack_ids):
        _promote_managed_embedding_pack_id(
            pair_pack_ids=pair_pack_ids,
            pair_enabled=pair_enabled,
            pair_key=_EMBEDDING_PAIR_KEY_BY_PACK_ID.get(managed_pack_id),
            pack_id=managed_pack_id,
        )

    for pair_key, values in dict(settings.embedding_pair_paths or {}).items():
        normalized_pair_key = str(pair_key or "").strip()
        if not normalized_pair_key or not isinstance(values, (list, tuple)):
            continue
        kept_paths: list[str] = []
        for raw_path in values:
            path_text = str(raw_path or "").strip()
            if not path_text:
                continue
            managed_pack_id = _resolve_managed_embedding_pack_id_for_path(
                base_dir=base_dir,
                raw_path=path_text,
            )
            if (
                managed_pack_id
                and _EMBEDDING_PAIR_KEY_BY_PACK_ID.get(managed_pack_id) == normalized_pair_key
            ):
                _promote_managed_embedding_pack_id(
                    pair_pack_ids=pair_pack_ids,
                    pair_enabled=pair_enabled,
                    pair_key=normalized_pair_key,
                    pack_id=managed_pack_id,
                )
                continue
            kept_paths.append(path_text)
        if kept_paths:
            pair_paths[normalized_pair_key] = kept_paths

    return manual_embedding_packs, pair_pack_ids, pair_paths, pair_enabled


def _promote_managed_embedding_pack_id(
    *,
    pair_pack_ids: dict[str, list[str]],
    pair_enabled: dict[str, bool],
    pair_key: str | None,
    pack_id: str,
) -> None:
    normalized_pair_key = str(pair_key or "").strip()
    normalized_pack_id = str(pack_id or "").strip()
    if not normalized_pair_key or not normalized_pack_id:
        return
    pack_ids = pair_pack_ids.setdefault(normalized_pair_key, [])
    if normalized_pack_id not in pack_ids:
        pack_ids.append(normalized_pack_id)
    pair_enabled.setdefault(normalized_pair_key, True)


def _resolve_managed_embedding_pack_id_for_path(*, base_dir: Path, raw_path: str) -> Optional[str]:
    path_text = str(raw_path or "").strip()
    if not path_text:
        return None
    for pack_id in sorted(_EMBEDDING_PAIR_KEY_BY_PACK_ID):
        if _is_managed_pack_path(base_dir=base_dir, pack_id=pack_id, raw_path=path_text):
            return pack_id
    return None


def _split_managed_pack_paths(
    *,
    base_dir: Path,
    configured_paths: object,
    configured_ids: object,
    retired_pack_ids: object = (),
) -> tuple[tuple[str, ...], dict[str, str]]:
    retired_ids = {
        str(pack_id).strip() for pack_id in tuple(retired_pack_ids or ()) if str(pack_id).strip()
    }
    managed_ids: set[str] = {
        str(pack_id).strip()
        for pack_id in tuple(configured_ids or ())
        if str(pack_id).strip() and str(pack_id).strip() not in retired_ids
    }
    manual_paths: dict[str, str] = {}
    for pack_id, raw_path in dict(configured_paths or {}).items():
        pack_key = str(pack_id or "").strip()
        path_text = str(raw_path or "").strip()
        if not pack_key or not path_text:
            continue
        if pack_key in retired_ids:
            continue
        if _is_managed_pack_path(base_dir=base_dir, pack_id=pack_key, raw_path=path_text):
            managed_ids.add(pack_key)
            continue
        manual_paths[pack_key] = path_text
    return tuple(sorted(managed_ids)), manual_paths


def _is_managed_pack_path(*, base_dir: Path, pack_id: str, raw_path: str) -> bool:
    manifest = load_installed_pack_manifest(base_dir, pack_id)
    if manifest is None or str(manifest.artifact_kind or "").strip().lower() != "sqlite":
        return False
    resolved_artifact = resolve_installed_pack_artifact(base_dir, pack_id)
    if resolved_artifact is None:
        return False
    candidate = Path(raw_path).expanduser()
    try:
        candidate = candidate.resolve()
        resolved_artifact = resolved_artifact.resolve()
        pack_root = installed_pack_root(base_dir, pack_id).resolve()
    except OSError:
        return False
    return (
        candidate == resolved_artifact or candidate == pack_root or pack_root in candidate.parents
    )


class AppState(QObject):
    datasetChanged = Signal(object)
    dirtyChanged = Signal(bool)
    profilesChanged = Signal(object)
    activeProfileChanged = Signal(object)

    def __init__(self, settings_path: Path) -> None:
        super().__init__()
        self._settings_path = settings_path
        self._srs_store_path = settings_path.parent / "srs" / "srs_store.json"
        self._settings = AppSettings()
        self._dataset = VocabDataset()
        self._dataset_path: Optional[Path] = None
        self._srs_store = SrsStore()
        self._dirty = False

    @property
    def settings(self) -> AppSettings:
        return self._settings

    @property
    def dataset(self) -> VocabDataset:
        return self._dataset

    @property
    def srs_store(self) -> SrsStore:
        return self._srs_store

    @property
    def dataset_path(self) -> Optional[Path]:
        return self._dataset_path

    @property
    def dirty(self) -> bool:
        return self._dirty

    def load_settings(self) -> None:
        if self._settings_path.exists():
            loaded = load_app_settings(self._settings_path)
            profiles, active_id = _normalize_profiles(
                tuple(loaded.profiles),
                active_profile_id=loaded.active_profile_id,
                base_dir=self._settings_path.parent,
            )
            synonyms = _normalize_synonym_pack_settings(loaded.synonyms)
            self._settings = replace(
                loaded,
                profiles=profiles,
                active_profile_id=active_id,
                synonyms=synonyms,
            )
            if self._settings != loaded:
                self.save_settings()
        else:
            self._settings = AppSettings()
            self.save_settings()
        self._load_srs_store()
        self.profilesChanged.emit(self._settings.profiles)
        self.activeProfileChanged.emit(self._settings.active_profile_id)

    def save_settings(self) -> None:
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        save_app_settings(self._settings, self._settings_path)

    def _load_srs_store(self) -> None:
        if self._srs_store_path.exists():
            self._srs_store = load_srs_store(self._srs_store_path)
        else:
            self._srs_store = SrsStore()
            self.save_srs_store()

    def save_srs_store(self) -> None:
        self._srs_store_path.parent.mkdir(parents=True, exist_ok=True)
        save_srs_store(self._srs_store, self._srs_store_path)

    def update_srs_store(self, store: SrsStore) -> None:
        self._srs_store = store
        self.save_srs_store()

    def set_profiles(
        self, profiles: tuple[Profile, ...], *, active_profile_id: Optional[str]
    ) -> None:
        normalized_profiles, normalized_active = _normalize_profiles(
            tuple(profiles),
            active_profile_id=active_profile_id,
            base_dir=self._settings_path.parent,
        )
        self._settings = replace(
            self._settings,
            profiles=normalized_profiles,
            active_profile_id=normalized_active,
        )
        self.save_settings()
        self.profilesChanged.emit(self._settings.profiles)
        self.activeProfileChanged.emit(self._settings.active_profile_id)

    def update_settings(self, settings: AppSettings) -> None:
        normalized_profiles, normalized_active = _normalize_profiles(
            tuple(settings.profiles),
            active_profile_id=settings.active_profile_id,
            base_dir=self._settings_path.parent,
        )
        normalized_synonyms = _normalize_synonym_pack_settings(settings.synonyms)
        self._settings = replace(
            settings,
            profiles=normalized_profiles,
            active_profile_id=normalized_active,
            synonyms=normalized_synonyms,
        )
        self.save_settings()
        self.profilesChanged.emit(self._settings.profiles)
        self.activeProfileChanged.emit(self._settings.active_profile_id)

    def load_dataset(self, path: Path) -> None:
        self._dataset = load_vocab_dataset(path) if path.exists() else VocabDataset()
        self._dataset_path = path
        self.set_dirty(False)
        self.datasetChanged.emit(self._dataset)

    def save_dataset(self, *, path: Optional[Path] = None) -> None:
        if path is not None:
            self._dataset_path = path
        if self._dataset_path is None:
            raise ValueError("No dataset path set.")
        self._dataset_path.parent.mkdir(parents=True, exist_ok=True)
        save_vocab_dataset(self._dataset, self._dataset_path)
        self.set_dirty(False)

    def update_dataset(self, dataset: VocabDataset) -> None:
        self._dataset = dataset
        self.set_dirty(True)
        self.datasetChanged.emit(self._dataset)

    def set_dirty(self, dirty: bool) -> None:
        if self._dirty == dirty:
            return
        self._dirty = dirty
        self.dirtyChanged.emit(self._dirty)
