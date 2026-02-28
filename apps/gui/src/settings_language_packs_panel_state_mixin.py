from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

from i18n import t
from lexishift_core import SynonymSourceSettings
from utils_paths import reveal_path


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
        return dict(self._language_pack_paths)

    def frequency_paths(self) -> dict[str, str]:
        return dict(self._frequency_pack_paths)

    def embedding_paths(self) -> dict[str, str]:
        return dict(self._embedding_pack_paths)

    def embedding_pair_paths(self) -> dict[str, list[str]]:
        return {key: list(value) for key, value in self._embedding_pair_paths.items()}

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
        self._language_pack_paths = dict(getattr(synonym_settings, "language_packs", {}) or {})
        if synonym_settings.wordnet_dir:
            self._language_pack_paths.setdefault("wordnet-en", synonym_settings.wordnet_dir)
        if synonym_settings.moby_path:
            self._language_pack_paths.setdefault("moby-en", synonym_settings.moby_path)

    def _seed_frequency_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._frequency_pack_paths = dict(getattr(synonym_settings, "frequency_packs", {}) or {})

    def _seed_embedding_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._embedding_pack_paths = dict(getattr(synonym_settings, "embedding_packs", {}) or {})
        self._embedding_pair_paths = {
            key: list(value)
            for key, value in dict(getattr(synonym_settings, "embedding_pair_paths", {}) or {}).items()
            if isinstance(value, (list, tuple))
        }
        self._embedding_pair_enabled = dict(
            getattr(synonym_settings, "embedding_pair_enabled", {}) or {}
        )
