from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

from i18n import t
from lexishift_core import SynonymSourceSettings
from settings_language_packs_support import (
    LANGUAGE_RESOURCE_FAMILY_SECONDARY,
    LANGUAGE_RESOURCE_FAMILY_TRANSLATION,
    LANGUAGE_RESOURCE_ORIGIN_MANAGED,
    LANGUAGE_RESOURCE_ORIGIN_MANUAL,
    LanguageResourceBinding,
    split_language_resource_bindings,
)
from theme_combo_popup import apply_combo_popup_theme_to_children
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
        if hasattr(self, "_refresh_pair_resource_setup_panel"):
            self._refresh_pair_resource_setup_panel()

    def paths(self) -> dict[str, str]:
        _managed_ids, manual_paths, _wordnet_dir, _moby_path = split_language_resource_bindings(
            getattr(self, "_language_resource_bindings", {})
        )
        return manual_paths

    def managed_language_pack_ids(self) -> list[str]:
        managed_ids, _manual_paths, _wordnet_dir, _moby_path = split_language_resource_bindings(
            getattr(self, "_language_resource_bindings", {})
        )
        return list(managed_ids)

    def language_resource_bindings(self) -> dict[str, LanguageResourceBinding]:
        return dict(getattr(self, "_language_resource_bindings", {}) or {})

    def _language_resource_binding(self, pack_id: str) -> LanguageResourceBinding | None:
        binding = getattr(self, "_language_resource_bindings", {}).get(pack_id)
        return binding if isinstance(binding, LanguageResourceBinding) else None

    def _language_resource_effective_path(self, pack_id: str) -> str | None:
        binding = self._language_resource_binding(pack_id)
        if binding:
            path_text = str(binding.effective_path or "").strip()
            if path_text:
                return path_text
        path_text = str(getattr(self, "_language_pack_paths", {}).get(pack_id, "")).strip()
        return path_text or None

    def frequency_paths(self) -> dict[str, str]:
        paths: dict[str, str] = {}
        for pack_id, path in self._frequency_pack_paths.items():
            if pack_id in getattr(self, "_managed_frequency_pack_ids", set()) or (
                self._is_managed_frequency_pack_entry(pack_id, path)
            ):
                continue
            paths[pack_id] = path
        return paths

    def managed_frequency_pack_ids(self) -> list[str]:
        pack_ids = set(getattr(self, "_managed_frequency_pack_ids", set()) or set())
        for pack_id, path in self._frequency_pack_paths.items():
            if self._is_managed_frequency_pack_entry(pack_id, path):
                pack_ids.add(pack_id)
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
        for thread in list(self._pos_overlay_pack_threads):
            if thread.isRunning():
                thread.requestInterruption()
        for thread in list(self._embedding_conversion_threads):
            if thread.isRunning():
                thread.requestInterruption()
        for thread in list(getattr(self, "_seed_cache_prepare_threads", [])):
            if thread.isRunning():
                thread.requestInterruption()

    def set_theme(self, theme: dict) -> None:
        self._theme = dict(theme or {})
        if hasattr(self, "_apply_pair_resource_setup_style"):
            self._apply_pair_resource_setup_style()
        apply_combo_popup_theme_to_children(self, self._theme)
        self._refresh_language_pack_table()
        self._refresh_frequency_pack_table()
        self._refresh_embedding_pack_table()
        self._refresh_cross_embedding_pack_table()
        if hasattr(self, "_refresh_pair_resource_setup_panel"):
            self._refresh_pair_resource_setup_panel()

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
        bindings: dict[str, LanguageResourceBinding] = {}
        for pack_id in tuple(getattr(synonym_settings, "managed_language_pack_ids", ()) or ()):
            pack = self._language_pack_info.get(pack_id)
            if not self._is_pack_id_first_translation_pack(pack):
                continue
            candidate = self._resolve_downloaded_path(pack)
            if candidate:
                valid, _message = self._validate_language_pack_path(pack, candidate)
                if valid:
                    bindings[pack_id] = LanguageResourceBinding(
                        pack_id=pack_id,
                        family=self._language_resource_family(pack_id),
                        origin=LANGUAGE_RESOURCE_ORIGIN_MANAGED,
                        effective_path=candidate,
                    )
        for pack_id, path in dict(
            getattr(synonym_settings, "language_pack_paths", {}) or {}
        ).items():
            path_text = str(path or "").strip()
            if not path_text:
                continue
            if self._is_managed_translation_pack_entry(pack_id, path):
                bindings[pack_id] = LanguageResourceBinding(
                    pack_id=pack_id,
                    family=self._language_resource_family(pack_id),
                    origin=LANGUAGE_RESOURCE_ORIGIN_MANAGED,
                    effective_path=path_text,
                )
            else:
                bindings[pack_id] = LanguageResourceBinding(
                    pack_id=pack_id,
                    family=self._language_resource_family(pack_id),
                    origin=LANGUAGE_RESOURCE_ORIGIN_MANUAL,
                    effective_path=path_text,
                )
        if synonym_settings.wordnet_dir:
            bindings.setdefault(
                "wordnet-en",
                LanguageResourceBinding(
                    pack_id="wordnet-en",
                    family=LANGUAGE_RESOURCE_FAMILY_SECONDARY,
                    origin=LANGUAGE_RESOURCE_ORIGIN_MANUAL,
                    effective_path=synonym_settings.wordnet_dir,
                ),
            )
        if synonym_settings.moby_path:
            bindings.setdefault(
                "moby-en",
                LanguageResourceBinding(
                    pack_id="moby-en",
                    family=LANGUAGE_RESOURCE_FAMILY_SECONDARY,
                    origin=LANGUAGE_RESOURCE_ORIGIN_MANUAL,
                    effective_path=synonym_settings.moby_path,
                ),
            )
        self._language_resource_bindings = bindings
        self._sync_language_pack_compat_state()

    def _seed_frequency_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._frequency_pack_paths = dict(
            getattr(synonym_settings, "frequency_pack_paths", {}) or {}
        )
        self._managed_frequency_pack_ids = set()
        for pack_id in tuple(getattr(synonym_settings, "managed_frequency_pack_ids", ()) or ()):
            pack = self._frequency_pack_info.get(pack_id)
            candidate = self._resolve_frequency_pack_path(pack) if pack else None
            if candidate:
                valid, _message = self._validate_frequency_pack_path(pack, candidate)
                if valid:
                    self._managed_frequency_pack_ids.add(pack_id)
        for pack_id, path in tuple(self._frequency_pack_paths.items()):
            if self._is_managed_frequency_pack_entry(pack_id, path):
                self._managed_frequency_pack_ids.add(pack_id)
                self._frequency_pack_paths.pop(pack_id, None)

    def _seed_embedding_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._embedding_pack_paths = {}
        self._embedding_pair_pack_ids = {
            key: list(value)
            for key, value in dict(
                getattr(synonym_settings, "embedding_pair_pack_ids", {}) or {}
            ).items()
            if isinstance(value, (list, tuple))
        }
        self._embedding_pair_enabled = dict(
            getattr(synonym_settings, "embedding_pair_enabled", {}) or {}
        )
        for pack_id, path in dict(
            getattr(synonym_settings, "embedding_pack_paths", {}) or {}
        ).items():
            pack_key = str(pack_id or "").strip()
            path_text = str(path or "").strip()
            if not pack_key or not path_text:
                continue
            if self._embedding_pack_pair_key(pack_key) and self._is_installed_embedding_pack_entry(
                pack_key, path_text
            ):
                self._ensure_embedding_pair_pack_id(pack_key)
                continue
            self._embedding_pack_paths[pack_key] = path_text
        self._embedding_pair_paths = {}
        for pair_key, values in dict(
            getattr(synonym_settings, "embedding_pair_paths", {}) or {}
        ).items():
            normalized_pair_key = str(pair_key or "").strip()
            if not normalized_pair_key or not isinstance(values, (list, tuple)):
                continue
            kept_paths: list[str] = []
            for raw_path in values:
                path_text = str(raw_path or "").strip()
                if not path_text:
                    continue
                managed_pack_id = self._managed_embedding_pack_id_for_path(path_text)
                if (
                    managed_pack_id
                    and self._embedding_pack_pair_key(managed_pack_id) == normalized_pair_key
                ):
                    self._ensure_embedding_pair_pack_id(
                        managed_pack_id,
                        pair_key=normalized_pair_key,
                    )
                    continue
                kept_paths.append(path_text)
            if kept_paths:
                self._embedding_pair_paths[normalized_pair_key] = kept_paths

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

    def _set_manual_language_pack_entry(self, pack_id: str, path: str) -> None:
        self._language_resource_bindings[pack_id] = LanguageResourceBinding(
            pack_id=pack_id,
            family=self._language_resource_family(pack_id),
            origin=LANGUAGE_RESOURCE_ORIGIN_MANUAL,
            effective_path=path,
        )
        self._sync_language_pack_compat_state()

    def _set_managed_language_pack_entry(
        self, pack_id: str, *, effective_path: str | None = None
    ) -> None:
        pack = self._language_pack_info.get(pack_id)
        resolved_path = str(effective_path or "").strip() or (
            self._resolve_downloaded_path(pack) if pack else None
        )
        self._language_resource_bindings[pack_id] = LanguageResourceBinding(
            pack_id=pack_id,
            family=self._language_resource_family(pack_id),
            origin=LANGUAGE_RESOURCE_ORIGIN_MANAGED,
            effective_path=resolved_path,
        )
        self._sync_language_pack_compat_state()

    def _clear_language_pack_entry(self, pack_id: str) -> None:
        self._language_resource_bindings.pop(pack_id, None)
        self._sync_language_pack_compat_state()

    def _is_managed_frequency_pack_entry(self, pack_id: str, path: str) -> bool:
        path_text = str(path or "").strip()
        if not path_text or not self._is_frequency_pack_data_path(path_text):
            return False
        pack = self._frequency_pack_info.get(pack_id)
        resolved = self._resolve_frequency_pack_path(pack) if pack else None
        if not resolved:
            return False
        return path_text == resolved

    def _set_manual_frequency_pack_entry(self, pack_id: str, path: str) -> None:
        self._managed_frequency_pack_ids.discard(pack_id)
        self._frequency_pack_paths[pack_id] = path

    def _set_managed_frequency_pack_entry(self, pack_id: str) -> None:
        self._frequency_pack_paths.pop(pack_id, None)
        self._managed_frequency_pack_ids.add(pack_id)

    def _clear_frequency_pack_entry(self, pack_id: str) -> None:
        self._frequency_pack_paths.pop(pack_id, None)
        self._managed_frequency_pack_ids.discard(pack_id)

    def _language_resource_family(self, pack_id: str) -> str:
        pack = self._language_pack_info.get(pack_id)
        if self._is_pack_id_first_translation_pack(pack):
            return LANGUAGE_RESOURCE_FAMILY_TRANSLATION
        return LANGUAGE_RESOURCE_FAMILY_SECONDARY

    def _sync_language_pack_compat_state(self) -> None:
        managed_ids, manual_paths, _wordnet_dir, _moby_path = split_language_resource_bindings(
            self._language_resource_bindings
        )
        self._managed_language_pack_ids = set(managed_ids)
        self._language_pack_paths = manual_paths

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

    def _embedding_pack_pair_key(self, pack_id: str) -> str | None:
        pack = self._embedding_pack_info.get(pack_id)
        pair_key = str(getattr(pack, "pair_key", "") or "").strip()
        return pair_key or None

    def _ensure_embedding_pair_pack_id(
        self,
        pack_id: str,
        *,
        pair_key: str | None = None,
    ) -> None:
        normalized_pack_id = str(pack_id or "").strip()
        normalized_pair_key = str(
            pair_key or self._embedding_pack_pair_key(normalized_pack_id) or ""
        ).strip()
        if not normalized_pack_id or not normalized_pair_key:
            return
        pack_ids = [
            value
            for value in self._embedding_pair_pack_ids.get(normalized_pair_key, [])
            if str(value or "").strip()
        ]
        if normalized_pack_id not in pack_ids:
            pack_ids.append(normalized_pack_id)
        self._embedding_pair_pack_ids[normalized_pair_key] = pack_ids
        self._embedding_pair_enabled.setdefault(normalized_pair_key, True)

    def _managed_embedding_pack_id_for_path(self, path: str) -> str | None:
        path_text = str(path or "").strip()
        if not path_text:
            return None
        for pack_id in sorted(self._embedding_pack_info):
            if not self._embedding_pack_pair_key(pack_id):
                continue
            if self._is_installed_embedding_pack_entry(pack_id, path_text):
                return pack_id
        return None
