from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from i18n import t
from settings_language_packs_support import is_pack_download_disabled
from settings_pair_resource_plan import (
    PairResourceItem,
    PairResourcePlan,
    available_pair_resource_plans,
    pair_resource_plan,
)
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
        panel_top = self._theme_hex("panel_top", fallback="#FFFFFF")
        panel_border = self._theme_hex("panel_border", fallback="#D8D0C0")
        background = self._theme_hex("background", fallback="#F7F3EA")
        text_color = self._theme_hex("text", fallback="#1F2933")
        self.setStyleSheet(
            "QFrame#learningLanguagePairCard, QFrame#learningLanguageResourceSlot {"
            f"background: {panel_top};"
            f"border: 1px solid {panel_border};"
            "border-radius: 8px;"
            "}"
            "QFrame#learningLanguageResourceSlot {"
            f"background: {background};"
            "}"
            f"QFrame#learningLanguagePairCard QLabel {{ color: {text_color}; }}"
            f"QFrame#learningLanguageResourceSlot QLabel {{ color: {text_color}; }}"
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

    def _pair_resource_download_active(self, item: PairResourceItem) -> bool:
        if item.kind == "frequency":
            row = self._frequency_pack_rows.get(item.pack_id)
            return bool(row is not None and not row.download_button.isEnabled())
        if item.kind == "language":
            row = self._language_pack_rows.get(item.pack_id)
            return bool(row is not None and not row.download_button.isEnabled())
        return False

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
        status = QLabel(
            t("language_packs.pair_setup.installed")
            if installed
            else t("language_packs.pair_setup.missing"),
            slot,
        )
        status.setStyleSheet(
            f"color: {self._status_color_hex('success' if installed else 'warning')};"
        )
        top_row.addWidget(status)
        layout.addLayout(top_row)

        source = QLabel(self._resource_slot_source_text(item), slot)
        source.setWordWrap(True)
        source.setOpenExternalLinks(True)
        layout.addWidget(source)

        actions = QHBoxLayout()
        download_button = QPushButton(
            t("buttons.redownload") if installed else t("buttons.download"),
            slot,
        )
        download_button.setEnabled(
            not self._pair_resource_download_active(item)
            and not is_pack_download_disabled(self._pack_source_overrides, item.pack_id)
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
