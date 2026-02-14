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
    VocabDataset,
    load_app_settings,
    load_srs_store,
    load_vocab_dataset,
    save_app_settings,
    save_srs_store,
    save_vocab_dataset,
)


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
    resolved_active = mapped_active if mapped_active in profile_ids else (profile_ids[0] if profile_ids else None)
    return normalized, resolved_active


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
            self._settings = replace(loaded, profiles=profiles, active_profile_id=active_id)
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

    def set_profiles(self, profiles: tuple[Profile, ...], *, active_profile_id: Optional[str]) -> None:
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
        self._settings = replace(
            settings,
            profiles=normalized_profiles,
            active_profile_id=normalized_active,
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
