from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QLabel, QPushButton

from i18n import t
from lexishift_core.helper.yomitan_dictionary_inspection import (
    YomitanDictionaryArchiveInfo,
    inspect_yomitan_dictionary_zip,
)
from lexishift_core.helper.yomitan_lookup_dictionaries import YomitanDictionaryImportError
from lookup_dictionary_acquisition import (
    LookupDictionaryAcquisitionContext,
    begin_lookup_dictionary_acquisition,
    clear_lookup_dictionary_acquisition,
    find_lookup_dictionary_download_candidate,
    load_lookup_dictionary_acquisition,
    lookup_dictionary_download_search_dirs,
)


class LanguagePackPanelLookupDictionaryAcquisitionMixin:
    _lookup_dictionary_download_candidate: YomitanDictionaryArchiveInfo | None
    _lookup_dictionary_status: QLabel
    _lookup_dictionary_detected_import_button: QPushButton
    _confirm_and_start_lookup_dictionary_import: Callable[..., None]

    def _lookup_dictionary_download_search_dirs(self) -> tuple[Path, ...]:
        return lookup_dictionary_download_search_dirs()

    def _begin_lookup_dictionary_acquisition(self, pair: str) -> None:
        begin_lookup_dictionary_acquisition(pair)
        self._lookup_dictionary_download_candidate = None
        self._refresh_lookup_dictionary_download_candidate()

    def _clear_lookup_dictionary_acquisition(self) -> None:
        clear_lookup_dictionary_acquisition()
        self._lookup_dictionary_download_candidate = None
        button = getattr(self, "_lookup_dictionary_detected_import_button", None)
        if button is not None:
            button.setVisible(False)

    def _lookup_dictionary_acquisition_context(
        self,
    ) -> LookupDictionaryAcquisitionContext | None:
        return load_lookup_dictionary_acquisition()

    def _find_lookup_dictionary_download_candidate(
        self,
    ) -> YomitanDictionaryArchiveInfo | None:
        context = self._lookup_dictionary_acquisition_context()
        if context is None:
            return None
        return find_lookup_dictionary_download_candidate(
            context,
            directories=self._lookup_dictionary_download_search_dirs(),
        )

    def _refresh_lookup_dictionary_download_candidate(self) -> None:
        button = getattr(self, "_lookup_dictionary_detected_import_button", None)
        if button is None:
            return
        candidate = self._find_lookup_dictionary_download_candidate()
        self._lookup_dictionary_download_candidate = candidate
        button.setVisible(candidate is not None)
        if candidate is None:
            return
        button.setText(t("language_packs.lookup_dictionaries.import_detected_zip"))
        self._lookup_dictionary_status.setText(
            t(
                "language_packs.lookup_dictionaries.downloaded_dictionary_found",
                title=candidate.title,
                filename=candidate.path.name,
            )
        )

    def _import_detected_lookup_dictionary_zip(self) -> None:
        candidate = self._lookup_dictionary_download_candidate
        if candidate is None:
            self._refresh_lookup_dictionary_download_candidate()
            candidate = self._lookup_dictionary_download_candidate
        if candidate is None:
            self._lookup_dictionary_status.setText(
                t("language_packs.lookup_dictionaries.downloaded_dictionary_missing")
            )
            return
        try:
            inspected = inspect_yomitan_dictionary_zip(candidate.path)
        except (OSError, YomitanDictionaryImportError):
            self._lookup_dictionary_download_candidate = None
            self._lookup_dictionary_detected_import_button.setVisible(False)
            self._lookup_dictionary_status.setText(
                t("language_packs.lookup_dictionaries.downloaded_dictionary_missing")
            )
            return
        context = self._lookup_dictionary_acquisition_context()
        self._confirm_and_start_lookup_dictionary_import(
            inspected.path,
            pair=context.pair if context is not None else "",
        )
