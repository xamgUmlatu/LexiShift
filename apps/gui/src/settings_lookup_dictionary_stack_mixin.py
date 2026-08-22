from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QWidget,
)

from i18n import t
from lexishift_core.helper.lp_capabilities import (
    normalize_pair_key,
    resolve_pair_capability,
)
from lexishift_core.helper.lookup_dictionary_settings import (
    lookup_dictionary_pack_ids_for_pair,
    save_lookup_dictionary_settings,
    with_lookup_dictionary_pack_ids,
)
from settings_lookup_dictionary_acquisition_mixin import (
    LanguagePackPanelLookupDictionaryAcquisitionMixin,
)


_LOOKUP_LANGUAGE_LABEL_KEYS = {
    "de": "languages.german",
    "en": "languages.english",
    "es": "languages.spanish",
    "ja": "languages.japanese",
    "zh": "languages.chinese",
}


def _stack_lookup_language_label(language: str) -> str:
    normalized = str(language or "").strip().lower()
    key = _LOOKUP_LANGUAGE_LABEL_KEYS.get(normalized)
    return t(key) if key else normalized.upper()


def _stack_lookup_pair_label(pair: str) -> str:
    source, separator, target = normalize_pair_key(pair, default="").partition("-")
    if not separator:
        return str(pair or "").strip()
    return (
        f"{_stack_lookup_language_label(source)} → "
        f"{_stack_lookup_language_label(target)} ({source}-{target})"
    )


def _stack_lookup_pair_target_language(pair: str) -> str:
    _source, separator, target = normalize_pair_key(pair, default="").partition("-")
    return target if separator else ""


def _lookup_pair_builtin_source(pair: str) -> str:
    capability = resolve_pair_capability(pair)
    if capability.requires_jmdict_for_rulegen or capability.requires_jmdict_for_seed:
        return "jmdict"
    if capability.requires_translation_dictionary_for_rulegen:
        return "translation"
    return ""


class LanguagePackPanelLookupDictionaryStackMixin(
    LanguagePackPanelLookupDictionaryAcquisitionMixin
):
    def _refresh_lookup_dictionary_stack(self) -> None:
        table = getattr(self, "_lookup_dictionary_order_table", None)
        if table is None:
            return
        pair = self._current_lookup_dictionary_pair()
        pack_ids = lookup_dictionary_pack_ids_for_pair(
            self._lookup_dictionary_settings,
            pair,
        )
        dictionaries = {
            dictionary.pack_id: dictionary for dictionary in self._installed_lookup_dictionaries()
        }
        for row in range(table.rowCount()):
            actions = table.cellWidget(row, 3)
            if actions is not None:
                table.removeCellWidget(row, 3)
                actions.hide()
                actions.deleteLater()
        table.clearContents()
        table.setRowCount(len(pack_ids) + 1)
        actions_width = table.horizontalHeaderItem(3).sizeHint().width() + 18
        for index, pack_id in enumerate(pack_ids):
            dictionary = dictionaries.get(pack_id)
            table.setItem(index, 0, QTableWidgetItem(str(index + 1)))
            if dictionary is None:
                name = t(
                    "language_packs.lookup_dictionaries.missing_dictionary",
                    pack_id=pack_id,
                )
                headwords = "—"
            else:
                name = dictionary.title
                if dictionary.revision:
                    name = f"{name}\n{dictionary.revision}"
                headwords = (
                    _stack_lookup_language_label(dictionary.source_language)
                    if dictionary.source_language
                    else t("language_packs.lookup_dictionaries.unknown_language")
                )
            table.setItem(index, 1, QTableWidgetItem(name))
            table.setItem(index, 2, QTableWidgetItem(headwords))
            actions_width = max(
                actions_width,
                self._set_lookup_dictionary_stack_actions(
                    table,
                    row=index,
                    pack_id=pack_id,
                    pack_count=len(pack_ids),
                ),
            )

        self._set_lookup_dictionary_builtin_row(
            table,
            row=len(pack_ids),
            pair=pair,
        )
        table.setColumnWidth(3, actions_width)
        self._refresh_lookup_dictionary_add_choices()

    def _set_lookup_dictionary_stack_actions(
        self,
        table,
        *,
        row: int,
        pack_id: str,
        pack_count: int,
    ) -> int:
        actions = QWidget(table)
        action_layout = QHBoxLayout(actions)
        action_layout.setContentsMargins(2, 2, 2, 2)
        action_layout.setSpacing(4)
        up_button = QPushButton(t("language_packs.lookup_dictionaries.move_up"), actions)
        up_button.setEnabled(row > 0)
        up_button.clicked.connect(
            lambda checked=False, value=pack_id: self._move_lookup_dictionary_in_stack(
                value,
                -1,
            )
        )
        action_layout.addWidget(up_button)
        down_button = QPushButton(
            t("language_packs.lookup_dictionaries.move_down"),
            actions,
        )
        down_button.setEnabled(row < pack_count - 1)
        down_button.clicked.connect(
            lambda checked=False, value=pack_id: self._move_lookup_dictionary_in_stack(
                value,
                1,
            )
        )
        action_layout.addWidget(down_button)
        remove_button = QPushButton(
            t("language_packs.lookup_dictionaries.remove_from_pair"),
            actions,
        )
        remove_button.clicked.connect(
            lambda checked=False, value=pack_id: self._remove_lookup_dictionary_from_stack(value)
        )
        action_layout.addWidget(remove_button)
        table.setCellWidget(row, 3, actions)
        return actions.sizeHint().width() + 8

    def _set_lookup_dictionary_builtin_row(self, table, *, row: int, pair: str) -> None:
        builtin_source = _lookup_pair_builtin_source(pair)
        table.setItem(
            row,
            0,
            QTableWidgetItem(t("language_packs.lookup_dictionaries.order_last")),
        )
        if builtin_source == "jmdict":
            builtin_label = t("language_packs.lookup_dictionaries.builtin_jmdict")
        elif builtin_source == "translation":
            builtin_label = t("language_packs.lookup_dictionaries.builtin_language_data")
        else:
            builtin_label = t(
                "language_packs.lookup_dictionaries.no_builtin_source",
                pair=_stack_lookup_pair_label(pair),
            )
        table.setItem(row, 1, QTableWidgetItem(builtin_label))
        target_language = _stack_lookup_pair_target_language(pair)
        table.setItem(
            row,
            2,
            QTableWidgetItem(
                _stack_lookup_language_label(target_language) if builtin_source else "—"
            ),
        )
        table.setItem(row, 3, QTableWidgetItem("—"))
        fallback_key = (
            "language_packs.lookup_dictionaries.fallback_detail"
            if builtin_source
            else "language_packs.lookup_dictionaries.no_fallback_detail"
        )
        self._lookup_dictionary_fallback.setText(t(fallback_key))

    def _refresh_lookup_dictionary_add_choices(self) -> None:
        combo = getattr(self, "_lookup_dictionary_add_combo", None)
        if combo is None:
            return
        pair = self._current_lookup_dictionary_pair()
        assigned = set(lookup_dictionary_pack_ids_for_pair(self._lookup_dictionary_settings, pair))
        dictionaries = [
            dictionary
            for dictionary in self._installed_lookup_dictionaries()
            if dictionary.pack_id not in assigned
        ]
        self._updating_lookup_dictionary_controls = True
        try:
            combo.clear()
            combo.addItem(
                t("language_packs.lookup_dictionaries.choose_installed_dictionary"),
                "",
            )
            for dictionary in dictionaries:
                label = dictionary.title
                if dictionary.revision:
                    label = f"{label} — {dictionary.revision}"
                combo.addItem(label, dictionary.pack_id)
            combo.setCurrentIndex(0)
        finally:
            self._updating_lookup_dictionary_controls = False
        self._lookup_dictionary_add_button.setEnabled(False)
        self._refresh_lookup_dictionary_add_detail()

    def _refresh_lookup_dictionary_add_detail(self) -> None:
        combo = getattr(self, "_lookup_dictionary_add_combo", None)
        if combo is None:
            return
        pack_id = str(combo.currentData() or "").strip()
        import_active = bool(getattr(self, "_lookup_dictionary_threads", ()))
        self._lookup_dictionary_add_button.setEnabled(bool(pack_id) and not import_active)
        dictionary = next(
            (item for item in self._installed_lookup_dictionaries() if item.pack_id == pack_id),
            None,
        )
        if dictionary is None:
            assigned = set(
                lookup_dictionary_pack_ids_for_pair(
                    self._lookup_dictionary_settings,
                    self._current_lookup_dictionary_pair(),
                )
            )
            installed = self._installed_lookup_dictionaries()
            has_available = any(item.pack_id not in assigned for item in installed)
            detail_key = (
                "language_packs.lookup_dictionaries.all_installed_assigned"
                if installed and not has_available
                else "language_packs.lookup_dictionaries.add_installed_detail"
            )
            self._lookup_dictionary_detail.setText(t(detail_key))
            self._lookup_dictionary_compatibility.clear()
            return
        self._lookup_dictionary_detail.setText(
            t(
                "language_packs.lookup_dictionaries.dictionary_detail",
                title=dictionary.title,
                revision=dictionary.revision or "—",
                terms=dictionary.term_count,
                filename=dictionary.source_filename or "—",
            )
        )
        pair_language = _stack_lookup_pair_target_language(self._current_lookup_dictionary_pair())
        dictionary_language = dictionary.source_language
        if dictionary_language and pair_language and dictionary_language != pair_language:
            self._lookup_dictionary_compatibility.setText(
                t(
                    "language_packs.lookup_dictionaries.compatibility_warning",
                    dictionary_language=_stack_lookup_language_label(dictionary_language),
                    pair_language=_stack_lookup_language_label(pair_language),
                )
            )
        elif not dictionary_language:
            self._lookup_dictionary_compatibility.setText(
                t("language_packs.lookup_dictionaries.compatibility_unknown")
            )
        else:
            self._lookup_dictionary_compatibility.clear()

    def _save_lookup_dictionary_stack(
        self,
        pack_ids: tuple[str, ...],
        *,
        status_key: str = "language_packs.lookup_dictionaries.selection_saved",
        **status_values: object,
    ) -> None:
        pair = self._current_lookup_dictionary_pair()
        self._lookup_dictionary_settings = with_lookup_dictionary_pack_ids(
            self._lookup_dictionary_settings,
            pair=pair,
            pack_ids=pack_ids,
        )
        save_lookup_dictionary_settings(
            self._lookup_dictionary_settings,
            self._lookup_dictionary_settings_path,
        )
        self._refresh_lookup_dictionary_stack()
        self._refresh_installed_lookup_dictionary_library()
        self._lookup_dictionary_status.setText(t(status_key, **status_values))

    def _add_lookup_dictionary_to_stack(self) -> None:
        pack_id = str(self._lookup_dictionary_add_combo.currentData() or "").strip()
        if not pack_id:
            return
        current = lookup_dictionary_pack_ids_for_pair(
            self._lookup_dictionary_settings,
            self._current_lookup_dictionary_pair(),
        )
        ordered = (pack_id, *(value for value in current if value != pack_id))
        self._save_lookup_dictionary_stack(tuple(ordered))

    def _move_lookup_dictionary_in_stack(self, pack_id: str, offset: int) -> None:
        current = list(
            lookup_dictionary_pack_ids_for_pair(
                self._lookup_dictionary_settings,
                self._current_lookup_dictionary_pair(),
            )
        )
        try:
            current_index = current.index(pack_id)
        except ValueError:
            return
        target_index = current_index + offset
        if target_index < 0 or target_index >= len(current):
            return
        current[current_index], current[target_index] = (
            current[target_index],
            current[current_index],
        )
        self._save_lookup_dictionary_stack(tuple(current))

    def _remove_lookup_dictionary_from_stack(self, pack_id: str) -> None:
        current = lookup_dictionary_pack_ids_for_pair(
            self._lookup_dictionary_settings,
            self._current_lookup_dictionary_pair(),
        )
        if pack_id not in current:
            return
        dictionary = next(
            (item for item in self._installed_lookup_dictionaries() if item.pack_id == pack_id),
            None,
        )
        title = dictionary.title if dictionary is not None else pack_id
        self._save_lookup_dictionary_stack(
            tuple(value for value in current if value != pack_id),
            status_key="language_packs.lookup_dictionaries.removed_from_pair",
            title=title,
        )
