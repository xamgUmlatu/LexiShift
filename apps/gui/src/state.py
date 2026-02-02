from __future__ import annotations

from dataclasses import replace
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


class AppState(QObject):
    datasetChanged = Signal(object)
    dirtyChanged = Signal(bool)
    profilesChanged = Signal(object)
    activeProfileChanged = Signal(object)

    def __init__(self, settings_path: Path) -> None:
        super().__init__()
        self._settings_path = settings_path
        self._srs_store_path = settings_path.parent / "srs_store.json"
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
            self._settings = load_app_settings(self._settings_path)
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
        self._settings = replace(self._settings, profiles=profiles, active_profile_id=active_profile_id)
        self.save_settings()
        self.profilesChanged.emit(self._settings.profiles)
        self.activeProfileChanged.emit(self._settings.active_profile_id)

    def update_settings(self, settings: AppSettings) -> None:
        self._settings = settings
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
