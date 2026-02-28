from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from lexishift_core.resources.synonyms import EmbeddingIndex


class EmbeddingLoaderThread(QThread):
    loaded = Signal(str, object, str)

    def __init__(self, pair_key: str, paths: list[Path], *, lower_case: bool, parent=None) -> None:
        super().__init__(parent)
        self._pair_key = pair_key
        self._paths = paths
        self._lower_case = lower_case

    def run(self) -> None:
        try:
            index = EmbeddingIndex(self._paths, lower_case=self._lower_case)
        except Exception as exc:
            self.loaded.emit(self._pair_key, None, str(exc))
            return
        self.loaded.emit(self._pair_key, index, "")
