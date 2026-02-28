from __future__ import annotations

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QMenu, QMessageBox

from i18n import available_locales, normalize_locale, t


class MainWindowLocaleMixin:
    def _show_empty_locale_menu(self) -> None:
        if not hasattr(self, "empty_locale_button"):
            return
        locale_pref = str(self._ui_settings.value("appearance/locale", "system") or "system")
        active_locale = (
            normalize_locale(QLocale.system().name())
            if locale_pref == "system"
            else normalize_locale(locale_pref)
        )
        menu = QMenu(self.empty_locale_button)
        popup_width = self.empty_locale_button.width()
        anchor_widget = self.empty_locale_button
        if hasattr(self, "empty_locale_icon_badge"):
            popup_width += self.empty_locale_icon_badge.width()
            anchor_widget = self.empty_locale_icon_badge
        menu.setFixedWidth(popup_width)
        self._apply_empty_locale_menu_style(menu)
        for locale, label in sorted(available_locales().items(), key=lambda item: item[1].lower()):
            action = menu.addAction(label)
            action.setData(locale)
            action.setCheckable(True)
            action.setChecked(active_locale == locale)
        selected = menu.exec(anchor_widget.mapToGlobal(anchor_widget.rect().bottomLeft()))
        if selected is None:
            return
        selected_locale = str(selected.data() or "")
        self._set_locale_preference(selected_locale)

    def _apply_empty_locale_menu_style(self, menu: QMenu) -> None:
        panel_top = self._theme_color_hex("panel_top", fallback="#F5F2E9")
        panel_border = self._theme_color_hex("panel_border", fallback="#D5CBB8")
        text = self._theme_color_hex("text", fallback="#2C2A24")
        muted = self._theme_color_hex("muted", fallback="#6F6558")
        accent = self._theme_color_hex("accent", fallback="#4A7DB8")
        accent_soft = self._theme_color_hex("accent_soft", fallback="#DCE8F7")
        primary = self._theme_color_hex("primary", fallback="#4A7DB8")
        menu.setStyleSheet(
            f"""
QMenu {{
  background: {panel_top};
  color: {text};
  border: 2px solid {panel_border};
  border-radius: 12px;
  padding: 6px;
}}
QMenu::item {{
  padding: 8px 12px;
  margin: 2px 4px;
  border-radius: 8px;
  background: transparent;
}}
QMenu::item:selected {{
  background: {accent_soft};
  border: 1px solid {accent};
}}
QMenu::item:checked {{
  background: {accent_soft};
  border: 1px solid {primary};
  font-weight: 700;
}}
QMenu::separator {{
  height: 1px;
  margin: 6px 10px;
  background: {muted};
}}
"""
        )

    def _set_locale_preference(self, locale_pref: str) -> None:
        next_pref = str(locale_pref or "system")
        current_pref = str(self._ui_settings.value("appearance/locale", "system") or "system")
        if next_pref == current_pref:
            return
        self._ui_settings.setValue("appearance/locale", next_pref)
        self._refresh_empty_locale_button_label()
        QMessageBox.information(
            self,
            t("dialogs.locale_change.title"),
            t("dialogs.locale_change.message"),
        )

    def _refresh_empty_locale_button_label(self) -> None:
        if not hasattr(self, "empty_locale_button"):
            return
        locale_pref = str(self._ui_settings.value("appearance/locale", "system") or "system")
        locales = available_locales()
        if locale_pref == "system":
            resolved = normalize_locale(QLocale.system().name())
            selected_label = locales.get(resolved, resolved)
        else:
            selected_label = locales.get(locale_pref, locale_pref)
        self.empty_locale_button.setText(f"{selected_label}  ▾")
