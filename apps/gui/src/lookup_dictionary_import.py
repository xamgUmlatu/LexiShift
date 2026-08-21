from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from lexishift_core.helper.yomitan_lookup_dictionaries import (
    YomitanDictionaryImportCancelled,
    import_yomitan_dictionary_zip,
)


class YomitanDictionaryImportThread(QThread):
    progress = Signal(int, int)
    completed = Signal(str, object)
    failed = Signal(str, str)
    cancelled = Signal(str)

    def __init__(
        self,
        *,
        pair: str,
        source_path: str | Path,
        dictionaries_dir: str | Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._pair = str(pair or "").strip().lower()
        self._source_path = Path(source_path)
        self._dictionaries_dir = Path(dictionaries_dir)

    def run(self) -> None:
        try:
            result = import_yomitan_dictionary_zip(
                self._source_path,
                dictionaries_dir=self._dictionaries_dir,
                progress=lambda current, total: self.progress.emit(current, total),
                should_cancel=self.isInterruptionRequested,
            )
            self.completed.emit(self._pair, result)
        except YomitanDictionaryImportCancelled:
            self.cancelled.emit(self._pair)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(self._pair, str(exc))
