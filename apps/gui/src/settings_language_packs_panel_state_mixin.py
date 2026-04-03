from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

from i18n import t
from lexishift_core import SynonymSourceSettings
from utils_paths import reveal_path

_TRANSLATION_PACK_BUILD_MODES = frozenset(
    {
        "freedict_tei_to_sqlite",
        "kaikki_glosses_to_sqlite",
        "kaikki_translations_to_sqlite",
    }
)


class LanguagePackPanelStateMixin:
    def apply_synonym_settings(self, synonym_settings: SynonymSourceSettings) -> None:
        self._seed_language_pack_paths(synonym_settings)
        self._seed_frequency_pack_paths(synonym_settings)
        self._seed_embedding_pack_paths(synonym_settings)
        self._auto_link_downloaded_packs()
        self._auto_link_downloaded_frequency_packs()
        self._auto_link_downloaded_embeddings()
        self._refresh_language_pack_table()
        self._refresh_frequency_pack_table()
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def paths(self) -> dict[str, str]:
        paths: dict[str, str] = {}
        for pack_id, path in self._language_pack_paths.items():
            if self._is_managed_translation_pack_entry(pack_id, path):
                continue
            paths[pack_id] = path
        return paths

    def managed_language_pack_ids(self) -> list[str]:
        pack_ids: list[str] = []
        for pack_id, path in self._language_pack_paths.items():
            if self._is_managed_translation_pack_entry(pack_id, path):
                pack_ids.append(pack_id)
        return sorted(pack_ids)

    def frequency_paths(self) -> dict[str, str]:
        paths: dict[str, str] = {}
        for pack_id, path in self._frequency_pack_paths.items():
            if self._is_managed_frequency_pack_entry(pack_id, path):
                continue
            paths[pack_id] = path
        return paths

    def managed_frequency_pack_ids(self) -> list[str]:
        pack_ids: list[str] = []
        for pack_id, path in self._frequency_pack_paths.items():
            if self._is_managed_frequency_pack_entry(pack_id, path):
                pack_ids.append(pack_id)
        return sorted(pack_ids)

    def embedding_paths(self) -> dict[str, str]:
        paths: dict[str, str] = {}
        for pack_id, path in self._embedding_pack_paths.items():
            pack = self._embedding_pack_info.get(pack_id)
            resolved = self._resolve_downloaded_path(pack, embeddings=True) if pack else None
            if (
                path
                and resolved
                and path == resolved
                and self._is_app_data_path(path, embeddings=True)
            ):
                continue
            paths[pack_id] = path
        return paths

    def embedding_pair_paths(self) -> dict[str, list[str]]:
        resolved: dict[str, list[str]] = {}
        for pair_key, values in self._embedding_pair_paths.items():
            managed_paths: set[str] = set()
            for pack_id in self._embedding_pair_pack_ids.get(pair_key, []):
                pack = self._embedding_pack_info.get(pack_id)
                candidate = self._resolve_downloaded_path(pack, embeddings=True) if pack else None
                if candidate:
                    managed_paths.add(candidate)
            filtered = [value for value in values if value and value not in managed_paths]
            if filtered:
                resolved[pair_key] = list(filtered)
        return resolved

    def embedding_pair_pack_ids(self) -> dict[str, list[str]]:
        return {key: list(value) for key, value in self._embedding_pair_pack_ids.items()}

    def embedding_pair_enabled(self) -> dict[str, bool]:
        return dict(self._embedding_pair_enabled)

    def cancel_downloads(self) -> None:
        self._closing = True
        for thread in list(self._language_pack_threads):
            if thread.isRunning():
                thread.requestInterruption()
        for thread in list(self._frequency_pack_threads):
            if thread.isRunning():
                thread.requestInterruption()
        for thread in list(self._embedding_conversion_threads):
            if thread.isRunning():
                thread.requestInterruption()

    def set_theme(self, theme: dict) -> None:
        self._theme = dict(theme or {})
        self._refresh_language_pack_table()
        self._refresh_frequency_pack_table()
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()

    def _theme_hex(self, key: str, *, fallback: str) -> str:
        value = self._theme.get(key)
        if isinstance(value, str) and value.strip():
            return value
        return fallback

    def _status_color_hex(self, tone: str) -> str:
        text_color = self._theme_hex("text", fallback="#2C2C2C")
        muted_color = self._theme_hex("muted", fallback="#6B6B6B")
        mapping = {
            "success": self._theme_hex("status_success", fallback="#2F6B2F"),
            "warning": self._theme_hex("status_warning", fallback="#8A6D1D"),
            "error": self._theme_hex("status_error", fallback="#A03030"),
            "info": self._theme_hex("status_info", fallback="#1B4F9C"),
            "neutral": self._theme_hex("status_neutral", fallback=text_color),
            "muted": self._theme_hex("status_muted", fallback=muted_color),
        }
        return mapping.get(tone, text_color)

    def _status_color(self, tone: str) -> QColor:
        return QColor(self._status_color_hex(tone))

    def _set_status_item_tone(self, item: QTableWidgetItem, tone: str) -> None:
        item.setForeground(self._status_color(tone))

    def _set_status_message(
        self,
        message: str,
        *,
        tone: Optional[str] = None,
        tooltip: Optional[str] = None,
    ) -> None:
        if tone:
            self.language_pack_status.setStyleSheet(f"color: {self._status_color_hex(tone)};")
        else:
            self.language_pack_status.setStyleSheet("")
        if tooltip is not None:
            self.language_pack_status.setToolTip(tooltip)
        self.language_pack_status.setText(message)

    def _open_language_pack_dir(self) -> None:
        reveal_path(self._language_pack_dir)

    def _open_frequency_pack_dir(self) -> None:
        reveal_path(self._frequency_pack_dir)

    def _show_embeddings_help(self) -> None:
        QMessageBox.information(
            self,
            t("language_packs.embeddings_title"),
            t("language_packs.embeddings_help"),
        )

    def _show_cross_embeddings_help(self) -> None:
        QMessageBox.information(
            self,
            t("language_packs.cross_embeddings_title"),
            t("language_packs.cross_embeddings_help"),
        )

    def _seed_language_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._language_pack_paths = dict(getattr(synonym_settings, "language_pack_paths", {}) or {})
        for pack_id in tuple(getattr(synonym_settings, "managed_language_pack_ids", ()) or ()):
            if pack_id in self._language_pack_paths:
                continue
            pack = self._language_pack_info.get(pack_id)
            if not self._is_pack_id_first_translation_pack(pack):
                continue
            candidate = self._resolve_downloaded_path(pack)
            if candidate:
                self._language_pack_paths[pack_id] = candidate
        if synonym_settings.wordnet_dir:
            self._language_pack_paths.setdefault("wordnet-en", synonym_settings.wordnet_dir)
        if synonym_settings.moby_path:
            self._language_pack_paths.setdefault("moby-en", synonym_settings.moby_path)

    def _seed_frequency_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._frequency_pack_paths = dict(
            getattr(synonym_settings, "frequency_pack_paths", {}) or {}
        )
        for pack_id in tuple(getattr(synonym_settings, "managed_frequency_pack_ids", ()) or ()):
            if pack_id in self._frequency_pack_paths:
                continue
            pack = self._frequency_pack_info.get(pack_id)
            candidate = self._resolve_frequency_pack_path(pack) if pack else None
            if candidate:
                self._frequency_pack_paths[pack_id] = candidate

    def _seed_embedding_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._embedding_pack_paths = dict(
            getattr(synonym_settings, "embedding_pack_paths", {}) or {}
        )
        self._embedding_pair_pack_ids = {
            key: list(value)
            for key, value in dict(
                getattr(synonym_settings, "embedding_pair_pack_ids", {}) or {}
            ).items()
            if isinstance(value, (list, tuple))
        }
        self._embedding_pair_paths = {
            key: list(value)
            for key, value in dict(
                getattr(synonym_settings, "embedding_pair_paths", {}) or {}
            ).items()
            if isinstance(value, (list, tuple))
        }
        self._embedding_pair_enabled = dict(
            getattr(synonym_settings, "embedding_pair_enabled", {}) or {}
        )

    def _is_pack_id_first_translation_pack(self, pack: object) -> bool:
        build_mode = str(getattr(pack, "build_mode", "") or "").strip().lower()
        sqlite_filename = str(getattr(pack, "sqlite_filename", "") or "").strip()
        return bool(sqlite_filename and build_mode in _TRANSLATION_PACK_BUILD_MODES)

    def _is_managed_translation_pack_entry(self, pack_id: str, path: str) -> bool:
        path_text = str(path or "").strip()
        if not path_text or not self._is_app_data_path(path_text):
            return False
        pack = self._language_pack_info.get(pack_id)
        if not self._is_pack_id_first_translation_pack(pack):
            return False
        resolved = self._resolve_downloaded_path(pack)
        if not resolved:
            return False
        return path_text == resolved

    def _is_installed_language_pack_entry(self, pack_id: str, path: str) -> bool:
        path_text = str(path or "").strip()
        if not path_text or not self._is_app_data_path(path_text):
            return False
        pack = self._language_pack_info.get(pack_id)
        resolved = self._resolve_downloaded_path(pack)
        if not resolved:
            return False
        return path_text == resolved

    def _is_managed_frequency_pack_entry(self, pack_id: str, path: str) -> bool:
        path_text = str(path or "").strip()
        if not path_text or not self._is_frequency_pack_data_path(path_text):
            return False
        pack = self._frequency_pack_info.get(pack_id)
        resolved = self._resolve_frequency_pack_path(pack) if pack else None
        if not resolved:
            return False
        return path_text == resolved

    def _is_installed_frequency_pack_entry(self, pack_id: str, path: str) -> bool:
        path_text = str(path or "").strip()
        if not path_text or not self._is_frequency_pack_data_path(path_text):
            return False
        pack = self._frequency_pack_info.get(pack_id)
        resolved = self._resolve_frequency_pack_path(pack) if pack else None
        if not resolved:
            return False
        return path_text == resolved

    def _is_installed_embedding_pack_entry(self, pack_id: str, path: str) -> bool:
        path_text = str(path or "").strip()
        if not path_text or not self._is_app_data_path(path_text, embeddings=True):
            return False
        pack = self._embedding_pack_info.get(pack_id)
        resolved = self._resolve_downloaded_path(pack, embeddings=True) if pack else None
        if not resolved:
            return False
        return path_text == resolved
