from __future__ import annotations

import os
from dataclasses import dataclass

from PySide6.QtCore import QStandardPaths, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from language_packs import LanguagePackDownloadThread, LanguagePackInfo, LANGUAGE_PACKS
from lexishift_core import SynonymSourceSettings
from utils_paths import reveal_path


@dataclass
class LanguagePackRow:
    row: int
    status_item: QTableWidgetItem
    download_button: QPushButton


class LanguagePackPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._language_pack_dir = _language_pack_dir()
        self._language_pack_info = {pack.pack_id: pack for pack in LANGUAGE_PACKS}
        self._language_pack_rows: dict[str, LanguagePackRow] = {}
        self._language_pack_threads: list[LanguagePackDownloadThread] = []
        self._language_pack_paths: dict[str, str] = {}
        self._closing = False

        self.open_language_pack_button = QPushButton("Open local directory")
        self.open_language_pack_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.open_language_pack_button.setMinimumHeight(34)
        self.open_language_pack_button.setStyleSheet(
            "QPushButton {"
            "background: #2F2F2F;"
            "color: #FFFFFF;"
            "padding: 6px 14px;"
            "border-radius: 6px;"
            "}"
            "QPushButton:hover { background: #232323; }"
        )
        self.open_language_pack_button.clicked.connect(self._open_language_pack_dir)

        self.language_pack_table = QTableWidget()
        self.language_pack_table.setColumnCount(7)
        self.language_pack_table.setHorizontalHeaderLabels(
            ["Pack", "Language", "Source", "Status", "Download", "Local", "Size"]
        )
        self.language_pack_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.language_pack_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.language_pack_table.setAlternatingRowColors(True)
        self.language_pack_table.verticalHeader().setVisible(False)
        header = self.language_pack_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.language_pack_table.setMinimumHeight(320)

        self.language_pack_status = QLabel("")
        self.language_pack_status.setWordWrap(True)
        self.language_pack_status.setOpenExternalLinks(True)

        self._populate_language_packs()

        header_row = QHBoxLayout()
        title = QLabel("Language packs")
        title.setStyleSheet("font-weight: 600; font-size: 14px;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        header_row.addWidget(self.open_language_pack_button)

        layout = QVBoxLayout(self)
        layout.addLayout(header_row)
        layout.addWidget(self.language_pack_table)
        layout.addWidget(self.language_pack_status)

    def apply_synonym_settings(self, synonym_settings: SynonymSourceSettings) -> None:
        self._seed_language_pack_paths(synonym_settings)
        self._refresh_language_pack_table()

    def paths(self) -> dict[str, str]:
        return dict(self._language_pack_paths)

    def cancel_downloads(self) -> None:
        self._closing = True
        for thread in list(self._language_pack_threads):
            if thread.isRunning():
                thread.requestInterruption()

    def _open_language_pack_dir(self) -> None:
        reveal_path(self._language_pack_dir)

    def _seed_language_pack_paths(self, synonym_settings: SynonymSourceSettings) -> None:
        self._language_pack_paths = dict(getattr(synonym_settings, "language_packs", {}) or {})
        if synonym_settings.wordnet_dir:
            self._language_pack_paths.setdefault("wordnet-en", synonym_settings.wordnet_dir)
        if synonym_settings.moby_path:
            self._language_pack_paths.setdefault("moby-en", synonym_settings.moby_path)

    def _refresh_language_pack_table(self) -> None:
        for pack_id, row in self._language_pack_rows.items():
            pack = self._language_pack_info.get(pack_id)
            if not pack:
                continue
            row.status_item.setToolTip("")
            row.status_item.setForeground(QColor("#2C2C2C"))
            dest_path = os.path.join(self._language_pack_dir, pack.filename)
            local_path = self._language_pack_paths.get(pack_id)
            if local_path:
                valid, message = self._validate_language_pack_path(pack, local_path)
                if valid:
                    row.status_item.setText("Local OK")
                    row.status_item.setForeground(QColor("#2F6B2F"))
                    row.status_item.setToolTip(local_path)
                else:
                    row.status_item.setText("Invalid")
                    row.status_item.setForeground(QColor("#A03030"))
                    row.status_item.setToolTip(message)
            elif os.path.exists(dest_path):
                row.status_item.setText("Downloaded")
                row.status_item.setForeground(QColor("#8A6D1D"))
                row.status_item.setToolTip(dest_path)
            else:
                row.status_item.setText("Available")
                row.status_item.setForeground(QColor("#5C5C5C"))
            if os.path.exists(dest_path):
                row.download_button.setText("Redownload")
            else:
                row.download_button.setText("Download")

    def _populate_language_packs(self) -> None:
        self._language_pack_rows.clear()
        self.language_pack_table.setRowCount(len(LANGUAGE_PACKS))
        for row, pack in enumerate(LANGUAGE_PACKS):
            name_item = QTableWidgetItem(pack.name)
            language_item = QTableWidgetItem(pack.language)
            source_item = QTableWidgetItem(pack.source)
            status_item = QTableWidgetItem("Available")
            download_button = QPushButton("Download")
            download_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._download_language_pack(pack_id)
            )
            local_button = QPushButton("Select...")
            local_button.clicked.connect(
                lambda checked=False, pack_id=pack.pack_id: self._select_language_pack_path(pack_id)
            )
            size_item = QTableWidgetItem(pack.size)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.language_pack_table.setItem(row, 0, name_item)
            self.language_pack_table.setItem(row, 1, language_item)
            self.language_pack_table.setItem(row, 2, source_item)
            self.language_pack_table.setItem(row, 3, status_item)
            self.language_pack_table.setCellWidget(row, 4, download_button)
            self.language_pack_table.setCellWidget(row, 5, local_button)
            self.language_pack_table.setItem(row, 6, size_item)

            self._language_pack_rows[pack.pack_id] = LanguagePackRow(
                row=row,
                status_item=status_item,
                download_button=download_button,
            )
        self._refresh_language_pack_table()

    def _download_language_pack(self, pack_id: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        dest_path = os.path.join(self._language_pack_dir, pack.filename)
        row.status_item.setText("Downloading...")
        row.download_button.setEnabled(False)
        self.language_pack_status.setStyleSheet("")
        self.language_pack_status.setText(f"Downloading {pack.name}...")
        thread = LanguagePackDownloadThread(pack.pack_id, pack.url, dest_path, self)
        thread.progress.connect(self._on_language_pack_progress)
        thread.completed.connect(self._on_language_pack_completed)
        thread.failed.connect(self._on_language_pack_failed)
        thread.finished.connect(lambda: self._cleanup_language_pack_thread(thread))
        self._language_pack_threads.append(thread)
        thread.start()

    def _select_language_pack_path(self, pack_id: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        if not pack:
            return
        if pack.local_kind == "dir":
            path = QFileDialog.getExistingDirectory(self, f"Select {pack.name} Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                f"Select {pack.name} File",
                "",
                "All Files (*)",
            )
        if not path:
            return
        if pack.pack_id == "wordnet-en":
            path = self._normalize_wordnet_path(path)
        valid, message = self._validate_language_pack_path(pack, path)
        if not valid:
            QMessageBox.warning(self, "Invalid Resource", message)
            self.language_pack_status.setStyleSheet("color: #A03030;")
            self.language_pack_status.setText(message)
            self._language_pack_paths.pop(pack_id, None)
            self._refresh_language_pack_table()
            return
        self._language_pack_paths[pack_id] = path
        self.language_pack_status.setStyleSheet("color: #2F6B2F;")
        self.language_pack_status.setText(f"{pack.name} linked to {path}")
        self._refresh_language_pack_table()

    def _validate_language_pack_path(self, pack: LanguagePackInfo, path: str) -> tuple[bool, str]:
        if pack.local_kind == "dir":
            if not os.path.isdir(path):
                return False, f"{pack.name} expects a directory."
            if pack.pack_id == "wordnet-en":
                if self._has_wordnet_classic(path) or self._has_wordnet_json(path):
                    return True, ""
                return False, (
                    "WordNet directory must contain data.noun/data.verb/data.adj/data.adv "
                    "or JSON files like entries-a.json and noun.act.json."
                )
            missing = [
                name for name in pack.required_files if not os.path.exists(os.path.join(path, name))
            ]
            if missing:
                missing_str = ", ".join(missing)
                return False, f"{pack.name} is missing required files: {missing_str}."
            return True, ""
        if not os.path.isfile(path):
            return False, f"{pack.name} expects a file."
        return True, ""

    def _has_wordnet_classic(self, path: str) -> bool:
        required = ("data.noun", "data.verb", "data.adj", "data.adv")
        return all(os.path.exists(os.path.join(path, name)) for name in required)

    def _has_wordnet_json(self, path: str) -> bool:
        markers = ("entries-a.json", "adj.all.json", "adv.all.json", "noun.act.json", "verb.body.json")
        return any(os.path.exists(os.path.join(path, name)) for name in markers)

    def _normalize_wordnet_path(self, path: str) -> str:
        if not os.path.isdir(path):
            return path
        if self._has_wordnet_classic(path) or self._has_wordnet_json(path):
            return path
        entries = [entry for entry in os.listdir(path) if os.path.isdir(os.path.join(path, entry))]
        if len(entries) == 1:
            candidate = os.path.join(path, entries[0])
            if self._has_wordnet_classic(candidate) or self._has_wordnet_json(candidate):
                return candidate
        return path

    def _on_language_pack_progress(self, pack_id: str, downloaded: int, total: int) -> None:
        row = self._language_pack_rows.get(pack_id)
        if not row:
            return
        row.status_item.setForeground(QColor("#1B4F9C"))
        if total > 0:
            pct = int((downloaded / total) * 100)
            row.status_item.setText(f"Downloading {pct}%")
        else:
            row.status_item.setText("Downloading...")

    def _on_language_pack_completed(self, pack_id: str, dest_path: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        if pack.pack_id == "wordnet-en":
            dest_path = self._normalize_wordnet_path(dest_path)
        valid, message = self._validate_language_pack_path(pack, dest_path)
        if valid:
            self._language_pack_paths[pack_id] = dest_path
            row.status_item.setText("Local OK")
            row.status_item.setToolTip(dest_path)
            self.language_pack_status.setStyleSheet("color: #2F6B2F;")
            self.language_pack_status.setText(f"Downloaded and linked {pack.name} to {dest_path}")
        else:
            self._language_pack_paths.pop(pack_id, None)
            row.status_item.setText("Downloaded")
            row.status_item.setToolTip(dest_path)
            self.language_pack_status.setStyleSheet("color: #A03030;")
            self.language_pack_status.setText(
                f"Downloaded {pack.name}, but validation failed: {message}"
            )
        row.download_button.setEnabled(True)
        row.download_button.setText("Redownload")
        self._refresh_language_pack_table()

    def _on_language_pack_failed(self, pack_id: str, message: str) -> None:
        pack = self._language_pack_info.get(pack_id)
        row = self._language_pack_rows.get(pack_id)
        if not pack or not row:
            return
        if message == "Cancelled" and self._closing:
            row.status_item.setText("Cancelled")
            row.status_item.setForeground(QColor("#6B6B6B"))
            row.download_button.setEnabled(True)
            row.download_button.setText("Download")
            return
        row.status_item.setText("Failed")
        row.download_button.setEnabled(True)
        row.download_button.setText("Retry")
        link = pack.wayback_url
        self.language_pack_status.setStyleSheet("color: #A03030;")
        self.language_pack_status.setText(
            "There was a problem downloading "
            f"{pack.name}. Error: {message}. "
            f'Try the Wayback mirror: <a href="{link}">{link}</a>'
        )

    def _cleanup_language_pack_thread(self, thread: LanguagePackDownloadThread) -> None:
        if thread in self._language_pack_threads:
            self._language_pack_threads.remove(thread)
        thread.deleteLater()


def _language_pack_dir() -> str:
    base_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    base_dir = base_dir or os.path.expanduser("~")
    target = os.path.join(base_dir, "language_packs")
    os.makedirs(target, exist_ok=True)
    return target
