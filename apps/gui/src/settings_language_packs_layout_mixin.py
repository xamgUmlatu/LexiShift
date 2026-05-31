from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from i18n import t


class LanguagePackPanelLayoutMixin:
    def _build_pair_resource_setup_panel(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("pairResourceSetupPanel")
        self._pair_resource_setup_panel = frame

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel(frame)
        title.setObjectName("pairResourceSetupTitle")
        title.setStyleSheet("font-weight: 600; font-size: 13px;")
        self._pair_resource_setup_title = title
        layout.addWidget(title)

        message = QLabel(frame)
        message.setWordWrap(True)
        self._pair_resource_setup_message = message
        layout.addWidget(message)

        resource_list = QLabel(frame)
        resource_list.setWordWrap(True)
        self._pair_resource_setup_list = resource_list
        layout.addWidget(resource_list)

        footer = QHBoxLayout()
        status = QLabel(frame)
        status.setWordWrap(True)
        self._pair_resource_setup_status = status
        footer.addWidget(status, 1)

        download_button = QPushButton(frame)
        download_button.clicked.connect(self._download_pair_required_resources)
        self._pair_resource_setup_download_button = download_button
        footer.addWidget(download_button)
        layout.addLayout(footer)

        return frame

    def _build_language_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        header_row = QHBoxLayout()
        section_title = QLabel(t("language_packs.title"))
        section_title.setStyleSheet("font-weight: 600; font-size: 13px;")
        header_row.addWidget(section_title)
        header_row.addStretch(1)
        header_row.addWidget(self.open_language_pack_button)
        layout.addLayout(header_row)
        description = QLabel(t("language_packs.language_description"))
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addWidget(self.language_pack_table)
        return tab

    def _build_frequency_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        header_row = QHBoxLayout()
        section_title = QLabel(t("language_packs.frequency_title"))
        section_title.setStyleSheet("font-weight: 600; font-size: 13px;")
        header_row.addWidget(section_title)
        header_row.addStretch(1)
        header_row.addWidget(self.open_frequency_pack_button)
        layout.addLayout(header_row)
        description = QLabel(t("language_packs.frequency_description"))
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addWidget(self.frequency_pack_table)
        return tab

    def _build_embedding_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        header_row = QHBoxLayout()
        section_title = QLabel(t("language_packs.embeddings_title"))
        section_title.setStyleSheet("font-weight: 600; font-size: 13px;")
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
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addWidget(self.embedding_pack_table)
        return tab

    def _build_cross_embedding_pack_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        header_row = QHBoxLayout()
        section_title = QLabel(t("language_packs.cross_embeddings_title"))
        section_title.setStyleSheet("font-weight: 600; font-size: 13px;")
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
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addWidget(self.cross_embedding_pack_table)
        return tab
