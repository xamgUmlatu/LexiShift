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
    def _build_learning_languages_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setProperty("resourcePanelTab", True)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        section_title = QLabel(t("language_packs.learning_pairs.title"))
        section_title.setProperty("resourceSectionTitle", True)
        header_row.addWidget(section_title)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        description = QLabel(t("language_packs.learning_pairs.description"))
        description.setProperty("resourceDescription", True)
        description.setWordWrap(True)
        layout.addWidget(description)

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
        header_row = QHBoxLayout()
        section_title = QLabel(t("language_packs.title"))
        section_title.setProperty("resourceSectionTitle", True)
        header_row.addWidget(section_title)
        header_row.addStretch(1)
        header_row.addWidget(self.open_language_pack_button)
        layout.addLayout(header_row)
        description = QLabel(t("language_packs.language_description"))
        description.setProperty("resourceDescription", True)
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addWidget(self.language_pack_table, 1)
        return tab

    def _build_frequency_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setProperty("resourcePanelTab", True)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        header_row = QHBoxLayout()
        section_title = QLabel(t("language_packs.frequency_title"))
        section_title.setProperty("resourceSectionTitle", True)
        header_row.addWidget(section_title)
        header_row.addStretch(1)
        header_row.addWidget(self.open_frequency_pack_button)
        layout.addLayout(header_row)
        description = QLabel(t("language_packs.frequency_description"))
        description.setProperty("resourceDescription", True)
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addWidget(self.frequency_pack_table, 1)
        return tab

    def _build_embedding_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setProperty("resourcePanelTab", True)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        header_row = QHBoxLayout()
        section_title = QLabel(t("language_packs.embeddings_title"))
        section_title.setProperty("resourceSectionTitle", True)
        help_button = QToolButton(tab)
        help_button.setText("?")
        help_button.setToolTip(t("language_packs.embeddings_help"))
        help_button.setAutoRaise(True)
        help_button.clicked.connect(self._show_embeddings_help)
        header_row.addWidget(section_title)
        header_row.addWidget(help_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)
        description = QLabel(t("language_packs.embeddings_description"))
        description.setProperty("resourceDescription", True)
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addWidget(self.embedding_pack_table, 1)
        return tab

    def _build_cross_embedding_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setProperty("resourcePanelTab", True)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        header_row = QHBoxLayout()
        section_title = QLabel(t("language_packs.cross_embeddings_title"))
        section_title.setProperty("resourceSectionTitle", True)
        help_button = QToolButton(tab)
        help_button.setText("?")
        help_button.setToolTip(t("language_packs.cross_embeddings_help"))
        help_button.setAutoRaise(True)
        help_button.clicked.connect(self._show_cross_embeddings_help)
        header_row.addWidget(section_title)
        header_row.addWidget(help_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)
        description = QLabel(t("language_packs.cross_embeddings_description"))
        description.setProperty("resourceDescription", True)
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addWidget(self.cross_embedding_pack_table, 1)
        return tab
