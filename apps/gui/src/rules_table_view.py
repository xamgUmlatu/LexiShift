from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QPushButton, QStyle, QStyledItemDelegate, QTableView

from i18n import t


class DeleteButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._color = QColor("#D64545")
        self._hover_color = QColor("#C73C3C")

    def set_colors(self, color: QColor, hover_color: QColor) -> None:
        self._color = QColor(color)
        self._hover_color = QColor(hover_color)

    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        rect = option.rect.adjusted(6, 4, -6, -4)
        hover = option.state & QStyle.State_MouseOver
        color = self._hover_color if hover else self._color
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 4, 4)
        painter.setPen(Qt.white)
        painter.drawText(rect, Qt.AlignCenter, t("buttons.delete"))
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return size.expandedTo(QSize(64, size.height()))


class RulesTableView(QTableView):
    """Rules table with custom empty-state rendering and contextual help affordance."""

    emptyGuideRequested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._empty_title = t("rules_table.empty_title")
        self._empty_hint = t("rules_table.empty_hint")
        self._show_empty_guide_button = False
        self._empty_palette = {
            "card_bg": QColor("#F5F2E9"),
            "card_border": QColor("#D5CBB8"),
            "title": QColor("#2C2A24"),
            "hint": QColor("#6F6558"),
            "accent": QColor("#4A7DB8"),
        }
        self._empty_guide_button = QPushButton("?", self.viewport())
        self._empty_guide_button.setProperty("emptyGuideFab", True)
        self._empty_guide_button.setFixedSize(28, 28)
        self._empty_guide_button.setToolTip(t("rules_table.open_setup_guide"))
        self._empty_guide_button.setVisible(False)
        self._empty_guide_button.clicked.connect(
            lambda _checked=False: self.emptyGuideRequested.emit()
        )

    def set_empty_palette(
        self,
        *,
        card_bg: str,
        card_border: str,
        title: str,
        hint: str,
        accent: str,
    ) -> None:
        self._empty_palette = {
            "card_bg": QColor(card_bg),
            "card_border": QColor(card_border),
            "title": QColor(title),
            "hint": QColor(hint),
            "accent": QColor(accent),
        }
        self.viewport().update()

    def set_empty_guide_button_visible(self, visible: bool) -> None:
        self._show_empty_guide_button = bool(visible)
        self._sync_empty_guide_button_visibility()

    def _empty_card_geometry(self) -> tuple[int, int, int, int]:
        rect = self.viewport().rect()
        card_width = min(620, max(300, rect.width() - 88))
        card_height = 136
        card_x = rect.center().x() - card_width // 2
        card_y = rect.center().y() - card_height // 2
        return card_x, card_y, card_width, card_height

    def _sync_empty_guide_button_visibility(self) -> None:
        model = self.model()
        is_empty = model is not None and model.rowCount() == 0
        show = self._show_empty_guide_button and is_empty
        self._empty_guide_button.setVisible(show)
        if not show:
            return
        card_x, card_y, card_width, card_height = self._empty_card_geometry()
        # Anchor the guide affordance to the top-right of the empty-state card.
        button_width = self._empty_guide_button.width()
        button_height = self._empty_guide_button.height()
        x = card_x + card_width - button_width - 12
        y = card_y + 10
        self._empty_guide_button.setGeometry(x, y, button_width, button_height)
        self._empty_guide_button.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_empty_guide_button_visibility()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        model = self.model()
        if model is None or model.rowCount() > 0:
            self._empty_guide_button.setVisible(False)
            return
        rect = self.viewport().rect()
        if rect.width() < 260 or rect.height() < 150:
            self._empty_guide_button.setVisible(False)
            return

        card_x, card_y, card_width, card_height = self._empty_card_geometry()

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._empty_palette["card_bg"])
        painter.drawRoundedRect(card_x, card_y, card_width, card_height, 18, 18)

        painter.setPen(QPen(self._empty_palette["card_border"], 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(card_x, card_y, card_width, card_height, 18, 18)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._empty_palette["accent"])
        painter.drawRoundedRect(card_x + 20, card_y + 20, 44, 8, 4, 4)

        title_font = painter.font()
        title_font.setBold(True)
        title_font.setPointSize(max(11, title_font.pointSize() + 1))
        painter.setFont(title_font)
        painter.setPen(self._empty_palette["title"])
        painter.drawText(
            card_x + 20,
            card_y + 34,
            card_width - 40,
            34,
            Qt.AlignLeft | Qt.AlignVCenter,
            self._empty_title,
        )

        hint_font = painter.font()
        hint_font.setBold(False)
        hint_font.setPointSize(max(9, hint_font.pointSize() - 1))
        painter.setFont(hint_font)
        painter.setPen(self._empty_palette["hint"])
        painter.drawText(
            card_x + 20,
            card_y + 68,
            card_width - 40,
            48,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
            self._empty_hint,
        )
        painter.end()
        self._sync_empty_guide_button_visibility()
