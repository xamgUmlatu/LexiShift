from __future__ import annotations

import json
from pathlib import Path
import shutil
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
from lexishift_core.helper.paths import build_helper_paths
from lexishift_core.helper.use_cases.semantic_pack_install import (
    SemanticPackInstallConfig,
    install_semantic_pack,
)
from localized_message_box import localized_question, prepare_message_box
from settings_language_packs_support import (
    is_pack_download_disabled,
    pack_download_disabled_tooltip,
)
from settings_language_packs_style_helpers import resource_table_action_button_style
from settings_pair_resource_plan import (
    PairResourceItem,
    PairResourcePlan,
    available_pair_resource_plans,
    pair_resource_plan,
)
from theme_manager import readable_text_color, rgba_color, theme_surface_opacity
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
        canvas_accent = readable_text_color(accent, bg, minimum_ratio=3.8)
        tab_text = readable_text_color(muted_color, panel_bottom, minimum_ratio=3.8)
        selected_tab_text = readable_text_color(text_color, panel_top)
        table_text = readable_text_color(text_color, table_bg)
        slot_text = readable_text_color(text_color, panel_bottom)
        header_text = readable_text_color(text_color, accent_soft)
        hover_text = readable_text_color(text_color, accent_soft)
        primary_text = readable_text_color("#FFFFFF", primary)
        progress_text = readable_text_color(text_color, bg)
        table_opacity = theme_surface_opacity(self._theme, "table", default=0.90)
        table_surface_bg = rgba_color(table_bg, table_opacity)
        table_alt_bg = rgba_color(panel_top, table_opacity)
        table_header_bg = rgba_color(accent_soft, table_opacity)
        pair_card_bg = rgba_color(table_bg, 0.34)
        resource_slot_bg = rgba_color(panel_bottom, 0.22)
        action_button_style = resource_table_action_button_style(
            table_bg,
            table_text,
            table_sel_bg,
            panel_border,
            panel_bottom,
            accent,
            accent_soft,
            hover_text,
            text_color,
            muted_color,
        )
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
  color: {canvas_accent};
  font-weight: 700;
  font-size: 16px;
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
QScrollArea#learningPairScrollArea {{
  background: transparent;
  border: none;
}}
QScrollArea#learningPairScrollArea > QWidget > QWidget {{
  background: transparent;
}}
QFrame#learningLanguagePairCard {{
  background: {pair_card_bg};
  border: 1px solid {panel_border};
  border-radius: 8px;
}}
QFrame#learningLanguageResourceSlot {{
  background: {resource_slot_bg};
  border: 1px solid {panel_border};
  border-radius: 8px;
}}
QFrame#learningLanguagePairCard QLabel {{
  color: {slot_text};
}}
QFrame#learningLanguageResourceSlot QLabel {{
  color: {slot_text};
}}
QTableWidget {{
  background: {table_surface_bg};
  alternate-background-color: {table_alt_bg};
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
  background: {table_header_bg};
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
QComboBox QAbstractItemView {{
  background: {table_bg};
  color: {table_text};
  border: 1px solid {panel_border};
  selection-background-color: {table_sel_bg};
  selection-color: {readable_text_color(text_color, table_sel_bg)};
  outline: 0px;
}}
QComboBox QAbstractItemView::item {{
  min-height: 24px;
  padding: 6px 8px;
}}
QComboBox QAbstractItemView::item:hover {{
  background: {accent_soft};
  color: {hover_text};
}}
QComboBox QAbstractItemView::item:selected {{
  background: {table_sel_bg};
  color: {readable_text_color(text_color, table_sel_bg)};
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
{action_button_style}
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
        for plan in self._available_learning_pair_add_plans():
            combo.addItem(plan.label, plan.pair)
        self._sync_learning_pair_add_controls()

    def _available_learning_pair_add_plans(self) -> tuple[PairResourcePlan, ...]:
        added = set(getattr(self, "_learning_pair_keys", []))
        return tuple(plan for plan in available_pair_resource_plans() if plan.pair not in added)

    def _sync_learning_pair_add_controls(self) -> None:
        combo = getattr(self, "_learning_pair_combo", None)
        button = getattr(self, "_learning_pair_add_button", None)
        add_row = getattr(self, "_learning_pair_add_row_container", None)
        status_label = getattr(self, "_learning_pair_add_status_label", None)
        has_pair_to_add = bool(combo is not None and combo.currentData())
        if combo is not None:
            combo.setEnabled(has_pair_to_add)
            combo.setVisible(has_pair_to_add)
        if button is not None:
            button.setEnabled(has_pair_to_add)
            button.setVisible(has_pair_to_add)
        if add_row is not None:
            add_row.setVisible(has_pair_to_add)
        if status_label is not None:
            status_label.setVisible(not has_pair_to_add)

    def _add_selected_learning_pair(self) -> None:
        combo = getattr(self, "_learning_pair_combo", None)
        if combo is None:
            return
        pair = str(combo.currentData() or combo.currentText() or "").strip().lower()
        if not pair:
            return
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
        return tuple(plan for plan in plans if plan is not None)

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
                widget.setParent(None)
                widget.deleteLater()
        plans = self._ordered_learning_pair_plans()
        if empty_label is not None:
            empty_label.setVisible(not plans)
        self._populate_learning_pair_combo()
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
        if item.kind == "pos_overlay":
            return self._pos_overlay_pack_info.get(item.pack_id)
        if item.kind == "semantic_pack":
            return self._semantic_pack_info.get(item.pack_id)
        return None

    def _resource_data_root(self) -> Path:
        return Path(self._language_pack_dir).expanduser().resolve().parent

    def _semantic_pack_inventory_path(self, item: PairResourceItem) -> Path:
        return (
            self._resource_data_root()
            / "language_packs"
            / item.pair
            / "semantic_packs"
            / item.pack_id
            / "semantic_inventory.json"
        )

    def _pair_resource_resolved_path(self, item: PairResourceItem) -> str | None:
        pack = self._pair_resource_pack(item)
        if pack is None:
            return None
        if item.kind == "frequency":
            return self._resolve_frequency_pack_path(pack)
        if item.kind == "language":
            return self._resolve_downloaded_path(pack)
        if item.kind == "pos_overlay":
            return self._resolve_pos_overlay_pack_path(pack)
        if item.kind == "semantic_pack":
            inventory_path = self._semantic_pack_inventory_path(item)
            return str(inventory_path) if inventory_path.exists() else None
        return None

    def _pair_resource_is_installed(self, item: PairResourceItem) -> bool:
        if not item.available:
            return False
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
        if item.kind == "pos_overlay":
            valid, _message = self._validate_pos_overlay_pack_path(pack, resolved)
            return valid
        if item.kind == "semantic_pack":
            try:
                payload = json.loads(Path(resolved).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return False
            return isinstance(payload, dict) and bool(payload.get("competition_sets"))
        return False

    def _pair_resource_manual_source_candidate(self, item: PairResourceItem) -> str | None:
        if item.kind != "frequency":
            return None
        pack = self._pair_resource_pack(item)
        if pack is None:
            return None
        if not hasattr(self, "_manual_frequency_source_candidate_path"):
            return None
        return self._manual_frequency_source_candidate_path(pack)

    def _pair_resource_supports_manual_file_import(self, item: PairResourceItem) -> bool:
        if not item.available:
            return False
        if item.kind == "frequency":
            pack = self._pair_resource_pack(item)
            return bool(
                pack is not None
                and hasattr(self, "_supports_frequency_source_import")
                and self._supports_frequency_source_import(pack)
            )
        return item.kind in {"language", "pos_overlay"}

    def _pair_resource_missing_items(self) -> tuple[PairResourceItem, ...]:
        return tuple(
            item
            for item in self._pair_resource_items()
            if item.available and not self._pair_resource_is_installed(item)
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
        if item.kind == "pos_overlay":
            return any(
                getattr(thread, "_pack_id", None) == item.pack_id and thread.isRunning()
                for thread in getattr(self, "_pos_overlay_pack_threads", [])
            )
        return False

    def _download_disabled_for_pair_resource(self, item: PairResourceItem) -> bool:
        if not item.available:
            return True
        return is_pack_download_disabled(
            self._pack_source_overrides,
            item.pack_id,
            self._pair_resource_pack(item),
        )

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
                if not item.optional:
                    blocked.append(item.label)
                continue
            if is_pack_download_disabled(self._pack_source_overrides, item.pack_id, pack):
                if not item.optional:
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
                continue
            if item.kind == "pos_overlay":
                if self._pair_resource_download_active(item):
                    continue
                self._download_pos_overlay_pack(item.pack_id)
                started.append(item.label)
                continue
            if item.kind == "semantic_pack":
                if self._install_semantic_pack_copy(item):
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
        missing_required_items = self._missing_required_items_for_plan(plan)
        installed_required_count = len(plan.required_resources) - len(missing_required_items)
        header = QHBoxLayout()
        title = QLabel(plan.label, card)
        title.setProperty("resourceCardTitle", True)
        title.setStyleSheet("font-weight: 700; font-size: 13px;")
        header.addWidget(title, 1)
        status = QLabel(
            self._learning_pair_status_text(
                installed_required_count,
                len(plan.required_resources),
            ),
            card,
        )
        status.setStyleSheet(
            f"color: {self._status_color_hex('warning' if missing_required_items else 'success')};"
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
        manual_source_candidate = (
            self._pair_resource_manual_source_candidate(item)
            if download_disabled and not installed
            else None
        )
        if installed:
            status_key = "language_packs.pair_setup.installed"
            status_tone = "success"
        elif manual_source_candidate:
            status_key = "language_packs.learning_pairs.downloaded_source_found"
            status_tone = "info"
        elif not item.available:
            status_key = "language_packs.pair_setup.not_available_yet"
            status_tone = "muted"
        elif download_disabled:
            status_key = "language_packs.learning_pairs.manual_setup_required"
            status_tone = "error"
        elif item.optional:
            status_key = "language_packs.pair_setup.recommended"
            status_tone = "info"
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
        action_buttons: list[QPushButton] = []
        pack = self._pair_resource_pack(item)
        if pack is not None:
            info_button = QPushButton(t("language_packs.source_license.button"), slot)
            info_button.setToolTip(
                t("language_packs.source_license.button_tooltip", name=item.label)
            )
            info_button.clicked.connect(
                lambda checked=False, resource=item: (
                    self._show_learning_pair_resource_source_license(resource)
                )
            )
            action_buttons.append(info_button)
        if not item.available:
            unavailable_button = QPushButton(
                t("language_packs.learning_pairs.not_available_yet"),
                slot,
            )
            unavailable_button.setEnabled(False)
            unavailable_button.setToolTip(
                t("language_packs.learning_pairs.semantic_pack_pending_tooltip")
            )
            action_buttons.append(unavailable_button)
        elif download_disabled and not installed:
            import_button = QPushButton(
                t(
                    "language_packs.learning_pairs.import_downloaded"
                    if manual_source_candidate
                    else "language_packs.learning_pairs.manual_setup"
                ),
                slot,
            )
            import_button.setToolTip(
                manual_source_candidate or t("language_packs.learning_pairs.manual_setup_tooltip")
            )
            import_button.clicked.connect(
                lambda checked=False, resource=item, candidate=manual_source_candidate: (
                    self._import_learning_pair_manual_source(resource, candidate)
                    if candidate
                    else self._open_learning_pair_resource_detail(resource)
                )
            )
            action_buttons.append(import_button)
            if self._pair_resource_supports_manual_file_import(item):
                choose_button = QPushButton(t("language_packs.learning_pairs.import_file"), slot)
                choose_button.setToolTip(t("language_packs.learning_pairs.import_file_tooltip"))
                choose_button.clicked.connect(
                    lambda checked=False, resource=item: self._select_learning_pair_resource_file(
                        resource
                    )
                )
                action_buttons.append(choose_button)
        elif not download_disabled:
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
            action_buttons.append(download_button)
        location_path = self._pair_resource_resolved_path(item) if installed else None
        if location_path:
            location_button = QPushButton(
                t("language_packs.learning_pairs.show_file_location"),
                slot,
            )
            location_button.setToolTip(
                t("language_packs.learning_pairs.show_file_location_tooltip")
            )
            location_button.clicked.connect(
                lambda checked=False, resource=item: self._reveal_learning_pair_resource_path(
                    resource
                )
            )
            action_buttons.append(location_button)
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
            action_buttons.append(uninstall_button)
        for button in action_buttons:
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return slot

    def _show_learning_pair_resource_source_license(self, item: PairResourceItem) -> None:
        pack = self._pair_resource_pack(item)
        if pack is None:
            self._set_status_message(
                t("language_packs.learning_pairs.unavailable_resource"),
                tone="error",
            )
            return
        self._show_pack_source_license(pack, self._pair_resource_resolved_path(item))

    def _resource_slot_source_text(self, item: PairResourceItem) -> str:
        pack = self._pair_resource_pack(item)
        if pack is None:
            if item.kind == "semantic_pack" and not item.available:
                return t("language_packs.learning_pairs.semantic_pack_pending")
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

    def _missing_required_items_for_plan(
        self,
        plan: PairResourcePlan,
    ) -> tuple[PairResourceItem, ...]:
        return tuple(
            item for item in plan.required_resources if not self._pair_resource_is_installed(item)
        )

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
        elif item.kind == "pos_overlay":
            self._download_pos_overlay_pack(item.pack_id)
        elif item.kind == "semantic_pack":
            self._install_semantic_pack_copy(item)
        self._refresh_learning_pair_cards()

    def _install_semantic_pack_copy(self, item: PairResourceItem) -> bool:
        if item.kind != "semantic_pack" or not item.available:
            return False
        pack = self._pair_resource_pack(item)
        if pack is None:
            self._set_status_message(
                t("language_packs.learning_pairs.unavailable_resource"),
                tone="error",
            )
            return False
        try:
            report = install_semantic_pack(
                build_helper_paths(self._resource_data_root()),
                config=SemanticPackInstallConfig(
                    pair=item.pair,
                    pack_id=item.pack_id,
                    copy_only=True,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            self._set_status_message(
                t(
                    "language_packs.learning_pairs.semantic_pack_install_failed",
                    resource=item.label,
                    error=str(exc),
                ),
                tone="error",
            )
            return False
        source = report.get("source")
        source_pack_path = (
            str(source.get("source_pack_inventory_path") or "") if isinstance(source, dict) else ""
        )
        self._set_status_message(
            t(
                "language_packs.learning_pairs.semantic_pack_installed",
                resource=item.label,
                path=source_pack_path,
            ),
            tone="success",
        )
        return True

    def _reveal_learning_pair_resource_path(self, item: PairResourceItem) -> None:
        path = self._pair_resource_resolved_path(item)
        if not path:
            self._set_status_message(
                t("language_packs.learning_pairs.file_location_unavailable"),
                tone="warning",
            )
            return
        reveal_path(path)
        self._set_status_message(
            t("language_packs.learning_pairs.file_location_opened", resource=item.label),
            tone="info",
            tooltip=path,
        )

    def _select_learning_pair_resource_file(self, item: PairResourceItem) -> None:
        if item.kind == "frequency":
            self._select_frequency_pack_path(item.pack_id)
        elif item.kind == "language":
            self._select_language_pack_path(item.pack_id)
        elif item.kind == "pos_overlay":
            self._select_pos_overlay_pack_path(item.pack_id)
        self._refresh_pair_resource_setup_panel()

    def _uninstall_learning_pair_resource(self, item: PairResourceItem) -> None:
        if item.kind == "frequency":
            self._delete_frequency_pack(item.pack_id)
        elif item.kind == "language":
            self._delete_language_pack(item.pack_id)
        elif item.kind == "pos_overlay":
            self._delete_pos_overlay_pack(item.pack_id)
        elif item.kind == "semantic_pack":
            path = self._semantic_pack_inventory_path(item)
            if path.exists():
                shutil.rmtree(path.parent, ignore_errors=True)
                self._set_status_message(
                    t("language_packs.removed", name=item.label),
                    tone="success",
                )
        self._refresh_learning_pair_cards()

    def _open_learning_pair_resource_detail(self, item: PairResourceItem) -> None:
        if not item.available:
            self._set_status_message(
                t("language_packs.learning_pairs.semantic_pack_pending"),
                tone="info",
            )
            return
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
        elif item.kind == "pos_overlay":
            self._set_status_message(
                t("language_packs.learning_pairs.manual_setup_opened", resource=item.label),
                tone="info",
            )
            return
        elif item.kind == "semantic_pack":
            self._set_status_message(
                t("language_packs.learning_pairs.semantic_pack_detail", resource=item.label),
                tone="info",
            )
            return
        tabs = getattr(self, "_resource_tabs", None)
        if tabs is not None and tab_index < tabs.count():
            tabs.setCurrentIndex(tab_index)
        if table is not None and row is not None:
            table.selectRow(row.row)
            table.scrollToItem(row.status_item)
        self._set_status_message(
            t("language_packs.learning_pairs.manual_setup_opened", resource=item.label),
            tone="info",
        )

    def _show_learning_pair_manual_setup(self, item: PairResourceItem) -> None:
        if not item.available:
            self._set_status_message(
                t("language_packs.learning_pairs.semantic_pack_pending"),
                tone="info",
            )
            return
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
        elif item.kind == "pos_overlay":
            expected_key = "language_packs.learning_pairs.manual_setup_expected_pos_overlay"
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
                license=str(getattr(pack, "license_name", "") or ""),
                license_url=str(getattr(pack, "license_url", "") or ""),
                url=self._manual_pack_source_page_url(pack)
                if hasattr(self, "_manual_pack_source_page_url")
                else str(getattr(pack, "url", "") or ""),
            )
        )
        provider_button = None
        source_page_url = (
            self._manual_pack_source_page_url(pack)
            if hasattr(self, "_manual_pack_source_page_url")
            else str(getattr(pack, "url", "") or "").strip()
        )
        if source_page_url:
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
        prepare_message_box(dialog)
        dialog.exec()
        if provider_button is not None and dialog.clickedButton() == provider_button:
            webbrowser.open(source_page_url)
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
        elif item.kind == "pos_overlay":
            self._select_pos_overlay_pack_path(item.pack_id)

    def _import_learning_pair_manual_source(
        self,
        item: PairResourceItem,
        candidate: str | None,
    ) -> None:
        if not candidate:
            self._open_learning_pair_resource_detail(item)
            return
        if item.kind == "frequency" and hasattr(self, "_import_frequency_pack_candidate"):
            self._import_frequency_pack_candidate(item.pack_id, candidate)
            return
        self._open_learning_pair_resource_detail(item)
