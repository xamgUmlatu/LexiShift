from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog

from i18n import t
from lexishift_core.helper.yomitan_dictionary_health import (
    InstalledLookupDictionaryHealth,
)
from lexishift_core.helper.yomitan_lookup_dictionaries import (
    list_installed_lookup_dictionaries,
)
from lookup_dictionary_health import request_lookup_dictionary_health


class LanguagePackPanelLookupDictionaryHealthMixin:
    def _lookup_dictionary_library_records(
        self,
    ) -> tuple[InstalledLookupDictionaryHealth, ...]:
        if self._lookup_dictionary_health_records is not None:
            return self._lookup_dictionary_health_records
        return tuple(
            InstalledLookupDictionaryHealth(
                dictionary=dictionary,
                status="checking",
                reason="checking",
                detail="",
                disk_usage_bytes=self._lookup_dictionary_disk_usage(dictionary.pack_id),
            )
            for dictionary in list_installed_lookup_dictionaries(Path(self._lookup_dictionary_dir))
        )

    @staticmethod
    def _lookup_dictionary_health_label(status: str) -> str:
        key = {
            "healthy": "health_healthy",
            "checking": "health_checking",
            "incompatible": "health_incompatible",
        }.get(status, "health_needs_repair")
        return t(f"language_packs.lookup_dictionaries.{key}")

    @staticmethod
    def _lookup_dictionary_health_tooltip(status: str) -> str:
        key = {
            "healthy": "health_healthy_detail",
            "checking": "health_checking_detail",
            "incompatible": "health_incompatible_detail",
        }.get(status, "health_needs_repair_detail")
        return t(f"language_packs.lookup_dictionaries.{key}")

    def _start_lookup_dictionary_health_check(self) -> None:
        if not hasattr(self, "_lookup_dictionary_health_button"):
            return
        self._lookup_dictionary_health_request_token += 1
        request_token = self._lookup_dictionary_health_request_token
        self._lookup_dictionary_health_pending = True
        self._lookup_dictionary_health_button.setEnabled(False)
        request_lookup_dictionary_health(
            self,
            self._lookup_dictionary_dir,
            request_token,
        )

    def _accept_lookup_dictionary_health(
        self,
        dictionaries_dir: str,
        request_token: int,
        records: tuple[object, ...],
        error: str,
    ) -> None:
        if request_token != self._lookup_dictionary_health_request_token or Path(
            dictionaries_dir
        ) != Path(self._lookup_dictionary_dir):
            return
        self._lookup_dictionary_health_pending = False
        self._lookup_dictionary_health_button.setEnabled(True)
        if error:
            self._lookup_dictionary_status.setText(
                t("language_packs.lookup_dictionaries.health_check_failed")
            )
            return
        self._lookup_dictionary_health_records = tuple(
            record for record in records if isinstance(record, InstalledLookupDictionaryHealth)
        )
        self._refresh_lookup_dictionary_stack()
        self._refresh_installed_lookup_dictionary_library()

    def _select_lookup_dictionary_repair_zip(self, pack_id: str, title: str) -> None:
        start_directory = ""
        if hasattr(self, "_manual_source_search_dirs"):
            search_directories = self._manual_source_search_dirs()
            if search_directories:
                start_directory = str(search_directories[0])
        source_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            t("language_packs.lookup_dictionaries.select_repair_zip", title=title),
            start_directory,
            t("language_packs.lookup_dictionaries.zip_filter"),
        )
        if source_path:
            self._confirm_and_start_lookup_dictionary_import(
                Path(source_path),
                expected_pack_id=pack_id,
            )
