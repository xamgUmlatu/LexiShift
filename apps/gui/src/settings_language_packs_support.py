from __future__ import annotations

import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Mapping, Optional

from PySide6.QtCore import QStandardPaths, QThread, Signal
from PySide6.QtWidgets import QPushButton, QTableWidgetItem


@dataclass
class LanguagePackRow:
    row: int
    status_item: QTableWidgetItem
    download_button: QPushButton
    delete_button: QPushButton


@dataclass
class FrequencyPackRow:
    row: int
    status_item: QTableWidgetItem
    download_button: QPushButton
    delete_button: QPushButton


@dataclass
class EmbeddingPackRow:
    row: int
    status_item: QTableWidgetItem
    download_button: QPushButton
    delete_button: QPushButton
    use_button: QPushButton


LANGUAGE_RESOURCE_FAMILY_TRANSLATION = "translation"
LANGUAGE_RESOURCE_FAMILY_SECONDARY = "secondary"
LANGUAGE_RESOURCE_ORIGIN_MANAGED = "managed"
LANGUAGE_RESOURCE_ORIGIN_MANUAL = "manual"


@dataclass(frozen=True)
class LanguageResourceBinding:
    pack_id: str
    family: str
    origin: str
    effective_path: Optional[str] = None


def split_language_resource_bindings(
    bindings: Mapping[str, LanguageResourceBinding] | None,
) -> tuple[tuple[str, ...], dict[str, str], Optional[str], Optional[str]]:
    managed_pack_ids: list[str] = []
    manual_paths: dict[str, str] = {}
    for pack_id, binding in dict(bindings or {}).items():
        pack_key = str(pack_id or "").strip()
        if not pack_key:
            continue
        if binding.origin == LANGUAGE_RESOURCE_ORIGIN_MANAGED:
            managed_pack_ids.append(pack_key)
            continue
        path_text = str(binding.effective_path or "").strip()
        if path_text:
            manual_paths[pack_key] = path_text
    wordnet_dir = str(manual_paths.get("wordnet-en", "")).strip() or None
    moby_path = str(manual_paths.get("moby-en", "")).strip() or None
    return tuple(sorted(set(managed_pack_ids))), manual_paths, wordnet_dir, moby_path


def is_sqlite_db_file(path: str | Path) -> bool:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return False
    try:
        with target.open("rb") as handle:
            header = handle.read(16)
    except OSError:
        return False
    return header.startswith(b"SQLite format 3")


def has_frequency_table(path: str | Path) -> bool:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return False
    try:
        with sqlite3.connect(str(target)) as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND lower(name)=lower('frequency') LIMIT 1;"
            ).fetchone()
    except sqlite3.Error:
        return False
    return row is not None


def resolve_embedding_converter_script() -> Path:
    this_file = Path(__file__).resolve()
    candidates = (
        this_file.parents[3] / "scripts" / "data" / "convert_embeddings.py",
        this_file.parents[2] / "scripts" / "data" / "convert_embeddings.py",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Embedding conversion script not found: scripts/data/convert_embeddings.py"
    )


class EmbeddingConversionThread(QThread):
    completed = Signal(str, str)
    failed = Signal(str, str)

    def __init__(
        self,
        *,
        pack_id: str,
        source_path: str,
        output_path: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._pack_id = pack_id
        self._source_path = Path(source_path)
        self._output_path = Path(output_path)

    def run(self) -> None:
        try:
            if not self._source_path.exists():
                raise FileNotFoundError(f"Embedding file not found: {self._source_path}")
            if is_sqlite_db_file(self._output_path):
                self.completed.emit(self._pack_id, str(self._output_path))
                return
            script = resolve_embedding_converter_script()
            command = [
                sys.executable,
                str(script),
                "--input",
                str(self._source_path),
                "--output",
                str(self._output_path),
                "--overwrite",
                "--progress",
                "0",
            ]
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "").strip()
                if not detail:
                    detail = f"embedding conversion failed with exit code {result.returncode}"
                raise RuntimeError(detail)
            if not is_sqlite_db_file(self._output_path):
                raise RuntimeError("embedding conversion did not produce a valid SQLite file")
            self.completed.emit(self._pack_id, str(self._output_path))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(self._pack_id, str(exc))


def language_pack_dir() -> str:
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not base:
        base = str(Path.home() / ".lexishift")
    path = Path(base) / "language_packs"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def embedding_pack_dir() -> str:
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not base:
        base = str(Path.home() / ".lexishift")
    path = Path(base) / "embedding_packs"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def frequency_pack_dir() -> str:
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not base:
        base = str(Path.home() / ".lexishift")
    path = Path(base) / "frequency_packs"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)
