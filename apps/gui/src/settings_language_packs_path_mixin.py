from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

from lexishift_core.helper.installed_packs import (
    installed_pack_root,
    load_installed_pack_manifest,
    resolve_installed_pack_artifact,
)
from language_packs import FrequencyPackInfo, LanguagePackInfo
from settings_language_packs_support import is_sqlite_db_file


class LanguagePackPanelPathMixin:
    def _download_archive_path(self, pack: LanguagePackInfo, *, embeddings: bool = False) -> str:
        if embeddings:
            return str(self._embedding_pack_storage_dir(pack) / pack.filename)
        return str(self._language_pack_storage_dir(pack) / pack.filename)

    def _language_pack_sqlite_path(self, pack: LanguagePackInfo) -> str | None:
        if not pack.sqlite_filename:
            return None
        return str(self._language_pack_storage_dir(pack) / pack.sqlite_filename)

    def _legacy_language_pack_sqlite_paths(self, pack: LanguagePackInfo) -> tuple[str, ...]:
        if not pack.sqlite_filename:
            return ()
        legacy_name = f"{pack.pack_id}.sqlite"
        storage_dir = self._language_pack_storage_dir(pack)
        candidates = [
            str(storage_dir / legacy_name),
            str(Path(self._language_pack_dir) / legacy_name),
        ]
        unique: list[str] = []
        for candidate in candidates:
            if candidate not in unique:
                unique.append(candidate)
        return tuple(unique)

    def _language_pack_storage_dir(self, pack: LanguagePackInfo) -> Path:
        return installed_pack_root(Path(self._language_pack_dir), pack.pack_id)

    def _frequency_pack_storage_dir(self, pack: FrequencyPackInfo) -> Path:
        return installed_pack_root(Path(self._frequency_pack_dir), pack.pack_id)

    def _frequency_archive_path(self, pack: FrequencyPackInfo) -> str:
        return str(self._frequency_pack_storage_dir(pack) / pack.filename)

    def _frequency_sqlite_path(self, pack: FrequencyPackInfo) -> str:
        return str(self._frequency_pack_storage_dir(pack) / pack.sqlite_filename)

    def _legacy_frequency_sqlite_paths(self, pack: FrequencyPackInfo) -> tuple[str, ...]:
        legacy_name = f"{pack.pack_id}.sqlite"
        storage_dir = self._frequency_pack_storage_dir(pack)
        candidates = [
            str(storage_dir / legacy_name),
            str(Path(self._frequency_pack_dir) / legacy_name),
        ]
        unique: list[str] = []
        for candidate in candidates:
            if candidate not in unique:
                unique.append(candidate)
        return tuple(unique)

    def _embedding_pack_storage_dir(self, pack: LanguagePackInfo) -> Path:
        return installed_pack_root(Path(self._embedding_pack_dir), pack.pack_id)

    def _embedding_pack_sqlite_path(self, pack: LanguagePackInfo) -> str:
        return str(self._embedding_pack_storage_dir(pack) / "main.sqlite")

    def _embedding_sqlite_path(self, source_path: str) -> str:
        lowered = source_path.lower()
        if lowered.endswith((".sqlite", ".sqlite3", ".db")):
            return source_path
        return f"{source_path}.sqlite"

    def _resolve_downloaded_path(
        self, pack: Optional[LanguagePackInfo], *, embeddings: bool = False
    ) -> Optional[str]:
        if not pack:
            return None
        if not embeddings:
            manifest = load_installed_pack_manifest(Path(self._language_pack_dir), pack.pack_id)
            if manifest is not None:
                resolved_artifact = resolve_installed_pack_artifact(
                    Path(self._language_pack_dir),
                    pack.pack_id,
                )
                if resolved_artifact is not None:
                    return str(resolved_artifact)
            sqlite_candidates = [
                candidate
                for candidate in (
                    self._language_pack_sqlite_path(pack),
                    *self._legacy_language_pack_sqlite_paths(pack),
                )
                if candidate
            ]
            for sqlite_path in sqlite_candidates:
                if self._is_sqlite_db(sqlite_path):
                    return sqlite_path
        archive_path = self._download_archive_path(pack, embeddings=embeddings)
        if embeddings:
            manifest = load_installed_pack_manifest(Path(self._embedding_pack_dir), pack.pack_id)
            if manifest is not None:
                resolved_artifact = resolve_installed_pack_artifact(
                    Path(self._embedding_pack_dir),
                    pack.pack_id,
                )
                if resolved_artifact is not None:
                    return str(resolved_artifact)
            managed_sqlite = self._embedding_pack_sqlite_path(pack)
            if self._is_sqlite_db(managed_sqlite):
                return managed_sqlite
            optimized = self._embedding_sqlite_path(archive_path)
            if self._is_sqlite_db(optimized):
                return optimized
        if archive_path.endswith(".zip"):
            extracted = os.path.splitext(archive_path)[0]
            if embeddings:
                optimized = self._embedding_sqlite_path(extracted)
                if self._is_sqlite_db(optimized):
                    return optimized
            if os.path.isdir(extracted):
                return extracted
        if archive_path.endswith((".tar.gz", ".tgz", ".tar.xz", ".txz")):
            extracted = archive_path
            for suffix in (".tar.gz", ".tgz", ".tar.xz", ".txz"):
                if extracted.endswith(suffix):
                    extracted = extracted[: -len(suffix)]
                    break
            if embeddings:
                optimized = self._embedding_sqlite_path(extracted)
                if self._is_sqlite_db(optimized):
                    return optimized
            if os.path.isdir(extracted):
                return extracted
        if archive_path.endswith(".gz"):
            extracted = os.path.splitext(archive_path)[0]
            if embeddings:
                optimized = self._embedding_sqlite_path(extracted)
                if self._is_sqlite_db(optimized):
                    return optimized
            if os.path.exists(extracted):
                return extracted
        if os.path.exists(archive_path):
            return archive_path
        return None

    def _resolve_frequency_pack_path(self, pack: Optional[FrequencyPackInfo]) -> Optional[str]:
        if not pack:
            return None
        manifest = load_installed_pack_manifest(Path(self._frequency_pack_dir), pack.pack_id)
        if manifest is not None:
            resolved_artifact = resolve_installed_pack_artifact(
                Path(self._frequency_pack_dir),
                pack.pack_id,
            )
            if resolved_artifact is not None:
                return str(resolved_artifact)
        sqlite_candidates = [
            self._frequency_sqlite_path(pack),
            *self._legacy_frequency_sqlite_paths(pack),
        ]
        for sqlite_path in sqlite_candidates:
            if os.path.exists(sqlite_path):
                return sqlite_path
        return None

    def _is_app_data_path(self, path: str, *, embeddings: bool = False) -> bool:
        base = os.path.abspath(self._embedding_pack_dir if embeddings else self._language_pack_dir)
        target = os.path.abspath(os.path.expanduser(path))
        try:
            return os.path.commonpath([base, target]) == base
        except ValueError:
            return False

    def _is_frequency_pack_data_path(self, path: str) -> bool:
        base = os.path.abspath(self._frequency_pack_dir)
        target = os.path.abspath(os.path.expanduser(path))
        try:
            return os.path.commonpath([base, target]) == base
        except ValueError:
            return False

    def _remove_path(self, path: str) -> None:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    def _has_wordnet_classic(self, path: str) -> bool:
        required = ("data.noun", "data.verb", "data.adj", "data.adv")
        return all(os.path.exists(os.path.join(path, name)) for name in required)

    def _has_wordnet_json(self, path: str) -> bool:
        markers = (
            "entries-a.json",
            "adj.all.json",
            "adv.all.json",
            "noun.act.json",
            "verb.body.json",
        )
        return any(os.path.exists(os.path.join(path, name)) for name in markers)

    def _normalize_wordnet_path(self, path: str) -> str:
        if not os.path.isdir(path):
            return path
        if self._has_wordnet_classic(path) or self._has_wordnet_json(path):
            return path
        entries = [entry for entry in os.listdir(path) if os.path.isdir(os.path.join(path, entry))]
        if len(entries) == 1:
            candidate = os.path.join(path, entries[0])
            if self._has_wordnet_classic(candidate) or self._has_wordnet_json(candidate):
                return candidate
        return path

    def _is_sqlite_db(self, path: str) -> bool:
        return is_sqlite_db_file(path)
