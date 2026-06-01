from __future__ import annotations

import webbrowser

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from i18n import t
from localized_message_box import localized_question, localize_standard_buttons
from settings_language_packs_support import (
    is_pack_download_disabled,
    pack_download_disabled_tooltip,
)
from settings_pair_resource_plan import (
    PairResourceItem,
    PairResourcePlan,
    available_pair_resource_plans,
    pair_resource_plan,
)
from theme_manager import readable_text_color
from utils_paths import reveal_path

_LEARNING_PAIR_SETTINGS_KEY = "resources/learning_pairs"


class LanguagePackPanelPairSetupMixin:
    def _set_focused_pair(self, focused_pair: str | None) -> None:
        self._focused_pair = str(focused_pair or "").strip().lower()
        self._focused_pair_plan = pair_resource_plan(self._focused_pair)
        self._learning_pair_keys = self._load_learning_pair_keys()
        if self._focused_pair_plan is not None:
            self._ensure_learning_pair(self._focused_pair_plan.pair, persist=True)

    def _apply_pair_resource_setup_style(self) -> None:
        bg = self._theme_hex("bg", fallback="#F6F2EB")
        panel_top = self._theme_hex("panel_top", fallback="#FFFFFF")
        panel_bottom = self._theme_hex("panel_bottom", fallback="#EFE7DC")
        panel_border = self._theme_hex("panel_border", fallback="#D8D0C0")
        table_bg = self._theme_hex("table_bg", fallback="#FFFFFF")
        table_sel_bg = self._theme_hex("table_sel_bg", fallback="#E7D9C6")
        text_color = self._theme_hex("text", fallback="#1F2933")
        muted_color = self._theme_hex("muted", fallback="#5C5C5C")
        accent = self._theme_hex("accent", fallback="#9A6A2B")
        accent_soft = self._theme_hex("accent_soft", fallback="#E9D6BF")
        primary = self._theme_hex("primary", fallback="#2F2F2F")
        primary_hover = self._theme_hex("primary_hover", fallback="#232323")
        canvas_text = readable_text_color(text_color, bg)
        canvas_muted = readable_text_color(muted_color, bg, minimum_ratio=3.8)
        tab_text = readable_text_color(muted_color, panel_bottom, minimum_ratio=3.8)
        selected_tab_text = readable_text_color(text_color, panel_top)
        header_surface_text = readable_text_color(text_color, panel_top)
        header_surface_muted = readable_text_color(muted_color, panel_top, minimum_ratio=3.8)
        table_text = readable_text_color(text_color, table_bg)
        slot_text = readable_text_color(text_color, panel_bottom)
        header_text = readable_text_color(text_color, accent_soft)
        hover_text = readable_text_color(text_color, accent_soft)
        primary_text = readable_text_color("#FFFFFF", primary)
        progress_text = readable_text_color(text_color, bg)
        self.setStyleSheet(
            f"""
QWidget {{
  color: {text_color};
}}
QWidget[resourcePanelTab="true"], QWidget[resourcePanelCanvas="true"] {{
  background: transparent;
  color: {canvas_text};
}}
QTabWidget#lexishiftResourceTabs::pane {{
  background: transparent;
  border: 1px solid {panel_border};
  border-radius: 8px;
  top: -1px;
}}
QTabWidget#lexishiftResourceTabs QTabBar::tab {{
  background: {panel_bottom};
  color: {tab_text};
  padding: 8px 14px;
  margin-right: 4px;
  border: 1px solid {panel_border};
  border-top-left-radius: 7px;
  border-top-right-radius: 7px;
  font-weight: 600;
}}
QTabWidget#lexishiftResourceTabs QTabBar::tab:selected {{
  background: {panel_top};
  color: {selected_tab_text};
  border-bottom-color: {panel_top};
}}
QLabel[resourcePanelTitle="true"] {{
  background: {panel_top};
  border: 1px solid {panel_border};
  border-radius: 8px;
  color: {readable_text_color(accent, panel_top, minimum_ratio=3.8)};
  font-weight: 700;
  font-size: 16px;
  padding: 8px 12px;
}}
QFrame[resourceHeaderPanel="true"] {{
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 {panel_top}, stop:1 {table_bg});
  border: 1px solid {panel_border};
  border-radius: 8px;
}}
QLabel[resourceSectionTitle="true"] {{
  color: {canvas_text};
  font-weight: 700;
  font-size: 15px;
}}
QLabel[resourceDescription="true"] {{
  color: {canvas_muted};
  font-size: 13px;
  font-weight: 500;
}}
QFrame[resourceHeaderPanel="true"] QLabel[resourceSectionTitle="true"] {{
  color: {header_surface_text};
  background: transparent;
}}
QFrame[resourceHeaderPanel="true"] QLabel[resourceDescription="true"] {{
  color: {header_surface_muted};
  background: transparent;
}}
QScrollArea#learningPairScrollArea {{
  background: transparent;
  border: none;
}}
QScrollArea#learningPairScrollArea > QWidget > QWidget {{
  background: transparent;
}}
QFrame#learningLanguagePairCard, QFrame#learningLanguageResourceSlot {{
  background: {table_bg};
  border: 1px solid {panel_border};
  border-radius: 8px;
}}
QFrame#learningLanguageResourceSlot {{
  background: {panel_bottom};
}}
QFrame#learningLanguagePairCard QLabel {{
  color: {table_text};
}}
QFrame#learningLanguageResourceSlot QLabel {{
  color: {slot_text};
}}
QTableWidget {{
  background: {table_bg};
  alternate-background-color: {panel_top};
  color: {table_text};
  gridline-color: {panel_border};
  border: 1px solid {panel_border};
  border-radius: 8px;
  selection-background-color: {table_sel_bg};
  selection-color: {readable_text_color(text_color, table_sel_bg)};
}}
QTableWidget::item {{
  padding: 6px 8px;
}}
QHeaderView::section {{
  background: {accent_soft};
  color: {header_text};
  padding: 8px;
  border: none;
  font-weight: 700;
}}
QComboBox {{
  background: {table_bg};
  color: {table_text};
  border: 1px solid {panel_border};
  border-radius: 6px;
  padding: 6px 8px;
}}
QPushButton {{
  background: {table_bg};
  color: {table_text};
  border: 1px solid {panel_border};
  border-radius: 6px;
  padding: 6px 12px;
}}
QPushButton:hover {{
  background: {accent_soft};
  color: {hover_text};
}}
QPushButton#settingsPrimaryButton {{
  background: {primary};
  color: {primary_text};
  border-color: {primary};
}}
QPushButton#settingsPrimaryButton:hover {{
  background: {primary_hover};
  color: {readable_text_color(primary_text, primary_hover)};
  border-color: {primary_hover};
}}
QProgressBar {{
  background: {bg};
  color: {progress_text};
  border: 1px solid {panel_border};
  border-radius: 6px;
  text-align: center;
}}
QProgressBar::chunk {{
  background: {accent};
  border-radius: 5px;
}}
"""
        )

    def _load_learning_pair_keys(self) -> list[str]:
        available = {plan.pair for plan in available_pair_resource_plans()}
        raw = QSettings().value(_LEARNING_PAIR_SETTINGS_KEY, [])
        values = raw if isinstance(raw, list) else str(raw or "").split(",")
        normalized: list[str] = []
        for value in values:
            pair = str(value or "").strip().lower()
            if pair in available and pair not in normalized:
                normalized.append(pair)
        return normalized

    def _persist_learning_pair_keys(self) -> None:
        QSettings().setValue(_LEARNING_PAIR_SETTINGS_KEY, list(self._learning_pair_keys))

    def _ensure_learning_pair(self, pair: str, *, persist: bool) -> None:
        plan = pair_resource_plan(pair)
        if plan is None:
            return
        if not hasattr(self, "_learning_pair_keys"):
            self._learning_pair_keys = []
        if plan.pair not in self._learning_pair_keys:
            self._learning_pair_keys.append(plan.pair)
            if persist:
                self._persist_learning_pair_keys()

    def _populate_learning_pair_combo(self) -> None:
        combo = getattr(self, "_learning_pair_combo", None)
        if combo is None:
            return
        combo.clear()
        for plan in available_pair_resource_plans():
            combo.addItem(plan.label, plan.pair)

    def _add_selected_learning_pair(self) -> None:
        combo = getattr(self, "_learning_pair_combo", None)
        if combo is None:
            return
        pair = str(combo.currentData() or combo.currentText() or "").strip().lower()
        self._ensure_learning_pair(pair, persist=True)
        self._focused_pair = pair
        self._focused_pair_plan = pair_resource_plan(pair)
        self._refresh_learning_pair_cards()

    def _remove_learning_pair(self, pair: str) -> None:
        normalized = str(pair or "").strip().lower()
        plan = pair_resource_plan(normalized)
        if plan is not None:
            installed_items = self._installed_items_for_plan(plan)
            if installed_items and not self._confirm_remove_learning_pair_with_installed_data(
                plan,
                installed_items,
            ):
                return
        self._learning_pair_keys = [
            value for value in self._learning_pair_keys if value != normalized
        ]
        self._persist_learning_pair_keys()
        if self._focused_pair == normalized:
            self._focused_pair = ""
            self._focused_pair_plan = None
        self._refresh_learning_pair_cards()

    def _ordered_learning_pair_plans(self) -> tuple[PairResourcePlan, ...]:
        plans = [pair_resource_plan(pair) for pair in getattr(self, "_learning_pair_keys", [])]
        resolved = [plan for plan in plans if plan is not None]
        focused = getattr(self, "_focused_pair", "")
        if focused:
            resolved.sort(key=lambda plan: 0 if plan.pair == focused else 1)
        return tuple(resolved)

    def _refresh_learning_pair_cards(self) -> None:
        layout = getattr(self, "_learning_pair_list_layout", None)
        empty_label = getattr(self, "_learning_pair_empty_label", None)
        if layout is None:
            return
        self._learning_pair_progress_bars: dict[str, list[QProgressBar]] = {}
        if not hasattr(self, "_learning_pair_progress_values"):
            self._learning_pair_progress_values: dict[str, tuple[int, int]] = {}
        while layout.count() > 1:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        plans = self._ordered_learning_pair_plans()
        if empty_label is not None:
            empty_label.setVisible(not plans)
        for plan in plans:
            layout.insertWidget(layout.count() - 1, self._build_learning_pair_card(plan))

    def _pair_resource_items(self) -> tuple[PairResourceItem, ...]:
        plan = getattr(self, "_focused_pair_plan", None)
        return plan.resources if plan is not None else ()

    def _pair_resource_pack(self, item: PairResourceItem):
        if item.kind == "frequency":
            return self._frequency_pack_info.get(item.pack_id)
        if item.kind == "language":
            return self._language_pack_info.get(item.pack_id)
        return None

    def _pair_resource_resolved_path(self, item: PairResourceItem) -> str | None:
        pack = self._pair_resource_pack(item)
        if pack is None:
            return None
        if item.kind == "frequency":
            return self._resolve_frequency_pack_path(pack)
        if item.kind == "language":
            return self._resolve_downloaded_path(pack)
        return None

    def _pair_resource_is_installed(self, item: PairResourceItem) -> bool:
        pack = self._pair_resource_pack(item)
        if pack is None:
            return False
        resolved = self._pair_resource_resolved_path(item)
        if not resolved:
            return False
        if item.kind == "frequency":
            valid, _message = self._validate_frequency_pack_path(pack, resolved)
            return valid
        if item.kind == "language":
            valid, _message = self._validate_language_pack_path(pack, resolved)
            return valid
        return False

    def _pair_resource_missing_items(self) -> tuple[PairResourceItem, ...]:
        return tuple(
            item
            for item in self._pair_resource_items()
            if not self._pair_resource_is_installed(item)
        )

    def _installed_items_for_plan(self, plan: PairResourcePlan) -> tuple[PairResourceItem, ...]:
        return tuple(item for item in plan.resources if self._pair_resource_is_installed(item))

    def _confirm_remove_learning_pair_with_installed_data(
        self,
        plan: PairResourcePlan,
        installed_items: tuple[PairResourceItem, ...],
    ) -> bool:
        resources = ", ".join(item.label for item in installed_items)
        reply = localized_question(
            self,
            t("language_packs.learning_pairs.remove_pair_confirm_title"),
            t(
                "language_packs.learning_pairs.remove_pair_confirm",
                pair=plan.label,
                resources=resources,
            ),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        return reply == QMessageBox.Yes

    def _pair_resource_download_active(self, item: PairResourceItem) -> bool:
        if self._download_disabled_for_pair_resource(item):
            return False
        if item.kind == "frequency":
            row = self._frequency_pack_rows.get(item.pack_id)
            return bool(row is not None and not row.download_button.isEnabled())
        if item.kind == "language":
            row = self._language_pack_rows.get(item.pack_id)
            return bool(row is not None and not row.download_button.isEnabled())
        return False

    def _download_disabled_for_pair_resource(self, item: PairResourceItem) -> bool:
        return is_pack_download_disabled(self._pack_source_overrides, item.pack_id)

    def _register_learning_pair_progress_bar(
        self,
        pack_id: str,
        progress_bar: QProgressBar,
    ) -> None:
        bars = getattr(self, "_learning_pair_progress_bars", None)
        if bars is None:
            self._learning_pair_progress_bars = {}
            bars = self._learning_pair_progress_bars
        bars.setdefault(pack_id, []).append(progress_bar)
        values = getattr(self, "_learning_pair_progress_values", {})
        current = values.get(pack_id)
        if current is not None:
            self._apply_learning_pair_progress(progress_bar, *current)

    def _apply_learning_pair_progress(
        self,
        progress_bar: QProgressBar,
        downloaded: int,
        total: int,
    ) -> None:
        progress_bar.setVisible(True)
        if total > 0:
            percent = max(0, min(100, int((downloaded / total) * 100)))
            progress_bar.setRange(0, 100)
            progress_bar.setValue(percent)
            progress_bar.setFormat(
                t("language_packs.learning_pairs.download_progress_pct", percent=percent)
            )
            return
        progress_bar.setRange(0, 0)
        progress_bar.setFormat(t("language_packs.learning_pairs.download_progress"))

    def _update_learning_pair_resource_progress(
        self,
        pack_id: str,
        downloaded: int,
        total: int,
    ) -> None:
        if not hasattr(self, "_learning_pair_progress_values"):
            self._learning_pair_progress_values = {}
        self._learning_pair_progress_values[pack_id] = (downloaded, total)
        for progress_bar in getattr(self, "_learning_pair_progress_bars", {}).get(pack_id, []):
            self._apply_learning_pair_progress(progress_bar, downloaded, total)

    def _clear_learning_pair_resource_progress(self, pack_id: str) -> None:
        values = getattr(self, "_learning_pair_progress_values", None)
        if values is not None:
            values.pop(pack_id, None)
        for progress_bar in getattr(self, "_learning_pair_progress_bars", {}).get(pack_id, []):
            progress_bar.setVisible(False)

    def _refresh_pair_resource_setup_panel(self) -> None:
        self._refresh_learning_pair_cards()

    def _download_pair_required_resources(self) -> None:
        missing_items = self._pair_resource_missing_items()
        if not missing_items:
            self._refresh_pair_resource_setup_panel()
            self._set_status_message(t("language_packs.pair_setup.status_ready"), tone="success")
            return
        started: list[str] = []
        blocked: list[str] = []
        for item in missing_items:
            pack = self._pair_resource_pack(item)
            if pack is None:
                blocked.append(item.label)
                continue
            if is_pack_download_disabled(self._pack_source_overrides, item.pack_id):
                blocked.append(item.label)
                continue
            if item.kind == "frequency":
                row = self._frequency_pack_rows.get(item.pack_id)
                if row is not None and not row.download_button.isEnabled():
                    continue
                self._download_frequency_pack(item.pack_id)
                started.append(item.label)
                continue
            if item.kind == "language":
                row = self._language_pack_rows.get(item.pack_id)
                if row is not None and not row.download_button.isEnabled():
                    continue
                self._download_language_pack(item.pack_id)
                started.append(item.label)
        self._refresh_pair_resource_setup_panel()
        if blocked:
            self._set_status_message(
                t(
                    "language_packs.pair_setup.status_blocked",
                    resources=", ".join(blocked),
                ),
                tone="error",
            )
        elif started:
            self._set_status_message(
                t(
                    "language_packs.pair_setup.status_started",
                    resources=", ".join(started),
                ),
                tone="info",
            )

    def _build_learning_pair_card(self, plan: PairResourcePlan) -> QWidget:
        card = QFrame(self)
        card.setObjectName("learningLanguagePairCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        missing_items = self._missing_items_for_plan(plan)
        installed_count = len(plan.resources) - len(missing_items)
        header = QHBoxLayout()
        title = QLabel(plan.label, card)
        title.setProperty("resourceCardTitle", True)
        title.setStyleSheet("font-weight: 700; font-size: 13px;")
        header.addWidget(title, 1)
        status = QLabel(self._learning_pair_status_text(installed_count, len(plan.resources)), card)
        status.setStyleSheet(
            f"color: {self._status_color_hex('warning' if missing_items else 'success')};"
            "font-weight: 600;"
        )
        header.addWidget(status)
        layout.addLayout(header)

        for item in plan.resources:
            layout.addWidget(self._build_learning_pair_resource_slot(item))

        footer = QHBoxLayout()
        download_button = QPushButton(t("language_packs.learning_pairs.download_missing"), card)
        download_button.setEnabled(bool(missing_items))
        download_button.clicked.connect(
            lambda checked=False, pair=plan.pair: self._download_learning_pair_missing(pair)
        )
        footer.addWidget(download_button)
        recheck_button = QPushButton(t("language_packs.learning_pairs.recheck"), card)
        recheck_button.clicked.connect(self._refresh_learning_pair_cards)
        footer.addWidget(recheck_button)
        footer.addStretch(1)
        remove_button = QPushButton(t("language_packs.learning_pairs.remove_pair"), card)
        remove_button.clicked.connect(
            lambda checked=False, pair=plan.pair: self._remove_learning_pair(pair)
        )
        footer.addWidget(remove_button)
        layout.addLayout(footer)
        return card

    def _build_learning_pair_resource_slot(self, item: PairResourceItem) -> QWidget:
        slot = QFrame(self)
        slot.setObjectName("learningLanguageResourceSlot")
        layout = QVBoxLayout(slot)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        label = QLabel(item.label, slot)
        label.setStyleSheet("font-weight: 600;")
        top_row.addWidget(label, 1)
        installed = self._pair_resource_is_installed(item)
        download_disabled = self._download_disabled_for_pair_resource(item)
        if installed:
            status_key = "language_packs.pair_setup.installed"
            status_tone = "success"
        elif download_disabled:
            status_key = "language_packs.learning_pairs.manual_setup_required"
            status_tone = "error"
        else:
            status_key = "language_packs.pair_setup.missing"
            status_tone = "warning"
        status = QLabel(
            t(status_key),
            slot,
        )
        status.setStyleSheet(f"color: {self._status_color_hex(status_tone)};")
        top_row.addWidget(status)
        layout.addLayout(top_row)

        source = QLabel(self._resource_slot_source_text(item), slot)
        source.setWordWrap(True)
        source.setOpenExternalLinks(True)
        layout.addWidget(source)

        progress_bar = QProgressBar(slot)
        progress_bar.setTextVisible(True)
        progress_bar.setVisible(False)
        self._register_learning_pair_progress_bar(item.pack_id, progress_bar)
        if self._pair_resource_download_active(item):
            values = getattr(self, "_learning_pair_progress_values", {}).get(item.pack_id)
            if values is None:
                self._apply_learning_pair_progress(progress_bar, 0, 0)
        layout.addWidget(progress_bar)

        actions = QHBoxLayout()
        if download_disabled and not installed:
            download_button = QPushButton(
                t("language_packs.learning_pairs.manual_setup"),
                slot,
            )
            download_button.setToolTip(t("language_packs.learning_pairs.manual_setup_tooltip"))
            download_button.clicked.connect(
                lambda checked=False, resource=item: self._open_learning_pair_resource_detail(
                    resource
                )
            )
        else:
            download_button = QPushButton(
                t("buttons.redownload") if installed else t("buttons.download"),
                slot,
            )
            download_button.setEnabled(
                not self._pair_resource_download_active(item) and not download_disabled
            )
            download_button.clicked.connect(
                lambda checked=False, resource=item: self._download_learning_pair_resource(resource)
            )
        actions.addWidget(download_button)
        location_path = self._pair_resource_resolved_path(item) if installed else None
        location_button = QPushButton(t("language_packs.learning_pairs.show_file_location"), slot)
        location_button.setEnabled(bool(location_path))
        location_button.setToolTip(
            t("language_packs.learning_pairs.show_file_location_tooltip")
            if location_path
            else t("language_packs.learning_pairs.file_location_unavailable")
        )
        location_button.clicked.connect(
            lambda checked=False, resource=item: self._reveal_learning_pair_resource_path(resource)
        )
        actions.addWidget(location_button)
        if installed:
            uninstall_button = QPushButton(
                t("language_packs.learning_pairs.uninstall_resource"),
                slot,
            )
            uninstall_button.setToolTip(
                t("language_packs.learning_pairs.uninstall_resource_tooltip")
            )
            uninstall_button.clicked.connect(
                lambda checked=False, resource=item: self._uninstall_learning_pair_resource(
                    resource
                )
            )
            actions.addWidget(uninstall_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return slot

    def _resource_slot_source_text(self, item: PairResourceItem) -> str:
        pack = self._pair_resource_pack(item)
        if pack is None:
            return t("language_packs.learning_pairs.unavailable_resource")
        source = pack.display_source()
        return t(
            "language_packs.learning_pairs.resource_source",
            source=source,
            pack_id=item.pack_id,
            size=str(getattr(pack, "size", "") or ""),
            url=str(getattr(pack, "url", "") or ""),
        )

    def _learning_pair_status_text(self, installed: int, total: int) -> str:
        if installed >= total:
            return t("language_packs.pair_setup.status_ready")
        return t("language_packs.pair_setup.status_missing", installed=installed, total=total)

    def _missing_items_for_plan(self, plan: PairResourcePlan) -> tuple[PairResourceItem, ...]:
        return tuple(item for item in plan.resources if not self._pair_resource_is_installed(item))

    def _download_learning_pair_missing(self, pair: str) -> None:
        plan = pair_resource_plan(pair)
        if plan is None:
            return
        self._focused_pair = plan.pair
        self._focused_pair_plan = plan
        self._download_pair_required_resources()
        self._refresh_learning_pair_cards()

    def _download_learning_pair_resource(self, item: PairResourceItem) -> None:
        if self._download_disabled_for_pair_resource(item):
            self._open_learning_pair_resource_detail(item)
            return
        if item.kind == "frequency":
            self._download_frequency_pack(item.pack_id)
        elif item.kind == "language":
            self._download_language_pack(item.pack_id)
        self._refresh_learning_pair_cards()

    def _reveal_learning_pair_resource_path(self, item: PairResourceItem) -> None:
        path = self._pair_resource_resolved_path(item)
        if not path:
            self._set_status_message(
                t("language_packs.learning_pairs.file_location_unavailable"),
                tone="warning",
            )
            return
        reveal_path(path)

    def _uninstall_learning_pair_resource(self, item: PairResourceItem) -> None:
        if item.kind == "frequency":
            self._delete_frequency_pack(item.pack_id)
        elif item.kind == "language":
            self._delete_language_pack(item.pack_id)
        self._refresh_learning_pair_cards()

    def _open_learning_pair_resource_detail(self, item: PairResourceItem) -> None:
        if self._download_disabled_for_pair_resource(item) and not self._pair_resource_is_installed(
            item
        ):
            self._show_learning_pair_manual_setup(item)
            return
        table = None
        row = None
        tab_index = 0
        if item.kind == "language":
            table = getattr(self, "language_pack_table", None)
            row = getattr(self, "_language_pack_rows", {}).get(item.pack_id)
            tab_index = 1
        elif item.kind == "frequency":
            table = getattr(self, "frequency_pack_table", None)
            row = getattr(self, "_frequency_pack_rows", {}).get(item.pack_id)
            tab_index = 2
        tabs = getattr(self, "_resource_tabs", None)
        if tabs is not None:
            tabs.setCurrentIndex(tab_index)
        if table is not None and row is not None:
            table.selectRow(row.row)
            table.scrollToItem(row.status_item)
        self._set_status_message(
            t("language_packs.learning_pairs.manual_setup_opened", resource=item.label),
            tone="info",
        )

    def _show_learning_pair_manual_setup(self, item: PairResourceItem) -> None:
        pack = self._pair_resource_pack(item)
        if pack is None:
            self._set_status_message(
                t("language_packs.learning_pairs.unavailable_resource"),
                tone="error",
            )
            return
        reason = pack_download_disabled_tooltip(self._pack_source_overrides, pack)
        supports_frequency_import = (
            item.kind == "frequency"
            and hasattr(self, "_supports_frequency_source_import")
            and self._supports_frequency_source_import(pack)
        )
        if supports_frequency_import:
            expected_key = "language_packs.learning_pairs.manual_setup_expected_frequency_import"
        else:
            expected_key = (
                "language_packs.learning_pairs.manual_setup_expected_frequency"
                if item.kind == "frequency"
                else "language_packs.learning_pairs.manual_setup_expected_language"
            )
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setWindowTitle(
            t("language_packs.learning_pairs.manual_setup_title", resource=item.label)
        )
        dialog.setText(t("language_packs.learning_pairs.manual_setup_summary"))
        dialog.setInformativeText(
            t(
                "language_packs.learning_pairs.manual_setup_instructions",
                expected=t(expected_key),
            )
        )
        dialog.setDetailedText(
            t(
                "language_packs.learning_pairs.manual_setup_details",
                reason=reason,
                source=pack.display_source(),
                pack_id=item.pack_id,
                url=str(getattr(pack, "url", "") or ""),
            )
        )
        provider_button = None
        if str(getattr(pack, "url", "") or "").strip():
            provider_button = dialog.addButton(
                t("language_packs.learning_pairs.open_provider_page"),
                QMessageBox.ButtonRole.ActionRole,
            )
        select_button = dialog.addButton(
            t(
                "language_packs.learning_pairs.import_file"
                if supports_frequency_import
                else "buttons.select"
            ),
            QMessageBox.ButtonRole.AcceptRole,
        )
        dialog.addButton(QMessageBox.StandardButton.Close)
        localize_standard_buttons(dialog)
        dialog.exec()
        if provider_button is not None and dialog.clickedButton() == provider_button:
            webbrowser.open(str(getattr(pack, "url", "") or "").strip())
            self._set_status_message(
                t("language_packs.learning_pairs.provider_page_opened", resource=item.label),
                tone="info",
            )
            return
        if dialog.clickedButton() != select_button:
            return
        if item.kind == "frequency":
            self._select_frequency_pack_path(item.pack_id)
        elif item.kind == "language":
            self._select_language_pack_path(item.pack_id)
