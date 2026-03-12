from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class UtilityDockPanel(QWidget):
    toggled = Signal(bool)

    def __init__(
        self, panel_id: str, title: str, content: QWidget, *, expanded: bool = False, parent=None
    ) -> None:
        super().__init__(parent)
        self._panel_id = str(panel_id or "")
        self._title = str(title or "")
        self._expanded = bool(expanded)
        self._unread_count = 0
        self.setProperty("utilityDockPanel", True)

        self.header_button = QPushButton()
        self.header_button.setCheckable(True)
        self.header_button.setProperty("variant", "secondary")
        self.header_button.setProperty("dockHeader", True)
        self.header_button.clicked.connect(self._on_toggle_clicked)

        self.badge_label = QLabel("")
        self.badge_label.setProperty("utilityDockBadge", True)
        self.badge_label.setVisible(False)

        self._content = content
        self._content_container = QWidget()
        content_layout = QVBoxLayout(self._content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._content)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self.header_button, 1)
        row.addWidget(self.badge_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addLayout(row)
        layout.addWidget(self._content_container, 1)

        self.set_expanded(self._expanded)

    def panel_id(self) -> str:
        return self._panel_id

    def is_expanded(self) -> bool:
        return self._expanded

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = bool(expanded)
        self._content_container.setVisible(self._expanded)
        self.header_button.blockSignals(True)
        self.header_button.setChecked(self._expanded)
        self.header_button.blockSignals(False)
        if self._expanded:
            self.clear_unread()
        self._sync_header_text()
        if self._expanded:
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            return
        collapsed_height = self.header_button.sizeHint().height() + 10
        self.setMinimumHeight(collapsed_height)
        self.setMaximumHeight(collapsed_height)

    def set_unread_count(self, count: int) -> None:
        self._unread_count = max(0, int(count))
        if self._expanded:
            self._unread_count = 0
        self.badge_label.setVisible(self._unread_count > 0)
        if self._unread_count > 0:
            self.badge_label.setText(str(self._unread_count))

    def clear_unread(self) -> None:
        self.set_unread_count(0)

    def increment_unread(self) -> None:
        self.set_unread_count(self._unread_count + 1)

    def refresh_geometry_hint(self) -> None:
        self.set_expanded(self._expanded)

    def _on_toggle_clicked(self, checked: bool) -> None:
        self.set_expanded(bool(checked))
        self.toggled.emit(self._expanded)

    def _sync_header_text(self) -> None:
        arrow = "▾" if self._expanded else "▸"
        self.header_button.setText(f"{arrow} {self._title}")


class UtilityDock(QWidget):
    panelToggled = Signal(str, bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._panels: dict[str, UtilityDockPanel] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._layout.addStretch(1)

    def add_panel(
        self, panel_id: str, title: str, content: QWidget, *, expanded: bool = False
    ) -> UtilityDockPanel:
        panel_key = str(panel_id or "").strip()
        if not panel_key:
            raise ValueError("panel_id is required")
        if panel_key in self._panels:
            raise ValueError(f"panel already exists: {panel_key}")
        panel = UtilityDockPanel(panel_key, title, content, expanded=expanded, parent=self)
        panel.toggled.connect(lambda state, key=panel_key: self.panelToggled.emit(key, bool(state)))
        self._panels[panel_key] = panel
        self._layout.insertWidget(max(0, self._layout.count() - 1), panel)
        return panel

    def panel(self, panel_id: str) -> Optional[UtilityDockPanel]:
        return self._panels.get(str(panel_id or "").strip())

    def is_panel_expanded(self, panel_id: str) -> bool:
        panel = self.panel(panel_id)
        if panel is None:
            return False
        return panel.is_expanded()

    def set_panel_expanded(self, panel_id: str, expanded: bool) -> None:
        panel = self.panel(panel_id)
        if panel is None:
            return
        panel.set_expanded(bool(expanded))

    def increment_unread(self, panel_id: str) -> None:
        panel = self.panel(panel_id)
        if panel is None:
            return
        panel.increment_unread()

    def clear_unread(self, panel_id: str) -> None:
        panel = self.panel(panel_id)
        if panel is None:
            return
        panel.clear_unread()

    def refresh_geometry_hint(self) -> None:
        for panel in self._panels.values():
            panel.refresh_geometry_hint()
