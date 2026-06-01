from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from i18n import t


class LanguagePackPanelLayoutMixin:
    def _add_resource_header(
        self,
        layout: QVBoxLayout,
        parent: QWidget,
        *,
        title: str,
        description: str,
        action_widget: QWidget | None = None,
        help_widget: QWidget | None = None,
    ) -> None:
        header_panel = QFrame(parent)
        header_panel.setProperty("resourceHeaderPanel", True)
        panel_layout = QVBoxLayout(header_panel)
        panel_layout.setContentsMargins(12, 10, 12, 10)
        panel_layout.setSpacing(6)

        header_row = QHBoxLayout()
        section_title = QLabel(title, header_panel)
        section_title.setProperty("resourceSectionTitle", True)
        header_row.addWidget(section_title)
        if help_widget is not None:
            header_row.addWidget(help_widget)
        header_row.addStretch(1)
        if action_widget is not None:
            header_row.addWidget(action_widget)
        panel_layout.addLayout(header_row)

        description_label = QLabel(description, header_panel)
        description_label.setProperty("resourceDescription", True)
        description_label.setWordWrap(True)
        panel_layout.addWidget(description_label)
        layout.addWidget(header_panel)

    def _build_learning_languages_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setProperty("resourcePanelTab", True)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self._add_resource_header(
            layout,
            tab,
            title=t("language_packs.learning_pairs.title"),
            description=t("language_packs.learning_pairs.description"),
        )

        add_row = QHBoxLayout()
        self._learning_pair_combo = QComboBox(tab)
        self._populate_learning_pair_combo()
        add_row.addWidget(self._learning_pair_combo, 1)
        add_button = QPushButton(t("language_packs.learning_pairs.add_pair"), tab)
        add_button.clicked.connect(self._add_selected_learning_pair)
        self._learning_pair_add_button = add_button
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

        self._learning_pair_empty_label = QLabel(
            t("language_packs.learning_pairs.empty"),
            tab,
        )
        self._learning_pair_empty_label.setProperty("resourceDescription", True)
        self._learning_pair_empty_label.setWordWrap(True)
        layout.addWidget(self._learning_pair_empty_label)

        scroll = QScrollArea(tab)
        scroll.setObjectName("learningPairScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._learning_pair_list_container = QWidget(scroll)
        self._learning_pair_list_container.setProperty("resourcePanelCanvas", True)
        self._learning_pair_list_layout = QVBoxLayout(self._learning_pair_list_container)
        self._learning_pair_list_layout.setContentsMargins(0, 0, 0, 0)
        self._learning_pair_list_layout.setSpacing(10)
        self._learning_pair_list_layout.addStretch(1)
        scroll.setWidget(self._learning_pair_list_container)
        layout.addWidget(scroll, 1)

        return tab

    def _build_language_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setProperty("resourcePanelTab", True)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        self._add_resource_header(
            layout,
            tab,
            title=t("language_packs.title"),
            description=t("language_packs.language_description"),
            action_widget=self.open_language_pack_button,
        )
        layout.addWidget(self.language_pack_table, 1)
        return tab

    def _build_frequency_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setProperty("resourcePanelTab", True)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        self._add_resource_header(
            layout,
            tab,
            title=t("language_packs.frequency_title"),
            description=t("language_packs.frequency_description"),
            action_widget=self.open_frequency_pack_button,
        )
        layout.addWidget(self.frequency_pack_table, 1)
        return tab

    def _build_embedding_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setProperty("resourcePanelTab", True)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        help_button = QToolButton(tab)
        help_button.setText("?")
        help_button.setToolTip(t("language_packs.embeddings_help"))
        help_button.setAutoRaise(True)
        help_button.clicked.connect(self._show_embeddings_help)
        self._add_resource_header(
            layout,
            tab,
            title=t("language_packs.embeddings_title"),
            description=t("language_packs.embeddings_description"),
            help_widget=help_button,
        )
        layout.addWidget(self.embedding_pack_table, 1)
        return tab

    def _build_cross_embedding_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setProperty("resourcePanelTab", True)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        help_button = QToolButton(tab)
        help_button.setText("?")
        help_button.setToolTip(t("language_packs.cross_embeddings_help"))
        help_button.setAutoRaise(True)
        help_button.clicked.connect(self._show_cross_embeddings_help)
        self._add_resource_header(
            layout,
            tab,
            title=t("language_packs.cross_embeddings_title"),
            description=t("language_packs.cross_embeddings_description"),
            help_widget=help_button,
        )
        layout.addWidget(self.cross_embedding_pack_table, 1)
        return tab
