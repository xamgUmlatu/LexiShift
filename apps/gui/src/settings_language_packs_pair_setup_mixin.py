from __future__ import annotations

from i18n import t
from settings_language_packs_support import is_pack_download_disabled
from settings_pair_resource_plan import PairResourceItem, pair_resource_plan


class LanguagePackPanelPairSetupMixin:
    def _set_focused_pair(self, focused_pair: str | None) -> None:
        self._focused_pair = str(focused_pair or "").strip().lower()
        self._focused_pair_plan = pair_resource_plan(self._focused_pair)

    def _apply_pair_resource_setup_style(self) -> None:
        panel = getattr(self, "_pair_resource_setup_panel", None)
        if panel is None:
            return
        panel_top = self._theme_hex("panel_top", fallback="#FFFFFF")
        panel_border = self._theme_hex("panel_border", fallback="#D8D0C0")
        text_color = self._theme_hex("text", fallback="#1F2933")
        panel.setStyleSheet(
            "QFrame#pairResourceSetupPanel {"
            f"background: {panel_top};"
            f"border: 1px solid {panel_border};"
            "border-radius: 8px;"
            "}"
            f"QLabel {{ color: {text_color}; }}"
        )

    def _pair_resource_items(self) -> tuple[PairResourceItem, ...]:
        plan = getattr(self, "_focused_pair_plan", None)
        return plan.resources if plan is not None else ()

    def _pair_resource_pack(self, item: PairResourceItem):
        if item.kind == "frequency":
            return self._frequency_pack_info.get(item.pack_id)
        if item.kind == "language":
            return self._language_pack_info.get(item.pack_id)
        return None

    def _pair_resource_is_installed(self, item: PairResourceItem) -> bool:
        pack = self._pair_resource_pack(item)
        if pack is None:
            return False
        if item.kind == "frequency":
            resolved = self._resolve_frequency_pack_path(pack)
            if not resolved:
                return False
            valid, _message = self._validate_frequency_pack_path(pack, resolved)
            return valid
        if item.kind == "language":
            resolved = self._resolve_downloaded_path(pack)
            if not resolved:
                return False
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
        panel = getattr(self, "_pair_resource_setup_panel", None)
        if panel is None:
            return
        plan = getattr(self, "_focused_pair_plan", None)
        if plan is None:
            panel.hide()
            return
        panel.show()
        title = getattr(self, "_pair_resource_setup_title", None)
        message = getattr(self, "_pair_resource_setup_message", None)
        resource_list = getattr(self, "_pair_resource_setup_list", None)
        status = getattr(self, "_pair_resource_setup_status", None)
        download_button = getattr(self, "_pair_resource_setup_download_button", None)
        missing_items = self._pair_resource_missing_items()
        installed_count = len(self._pair_resource_items()) - len(missing_items)
        if title is not None:
            title.setText(t("language_packs.pair_setup.title", pair=plan.label))
        if message is not None:
            message.setText(t("language_packs.pair_setup.description"))
        if resource_list is not None:
            rows = []
            for item in self._pair_resource_items():
                state = (
                    t("language_packs.pair_setup.installed")
                    if self._pair_resource_is_installed(item)
                    else t("language_packs.pair_setup.missing")
                )
                rows.append(f"{item.label}: {state}")
            resource_list.setText("\n".join(rows))
        if status is not None:
            if missing_items:
                status.setText(
                    t(
                        "language_packs.pair_setup.status_missing",
                        installed=installed_count,
                        total=len(self._pair_resource_items()),
                    )
                )
                status.setStyleSheet(f"color: {self._status_color_hex('warning')};")
            else:
                status.setText(t("language_packs.pair_setup.status_ready"))
                status.setStyleSheet(f"color: {self._status_color_hex('success')};")
        if download_button is not None:
            download_button.setText(t("language_packs.pair_setup.download_required"))
            download_button.setEnabled(
                bool(missing_items)
                and not any(self._pair_resource_download_active(item) for item in missing_items)
            )

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
