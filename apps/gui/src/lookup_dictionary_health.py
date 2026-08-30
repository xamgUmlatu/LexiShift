from __future__ import annotations

from pathlib import Path
import threading
from typing import Protocol
import weakref

from PySide6.QtCore import QObject, Signal, Slot

from lexishift_core.helper.yomitan_dictionary_health import (
    inspect_installed_lookup_dictionary_health,
)


class LookupDictionaryHealthTarget(Protocol):
    def _accept_lookup_dictionary_health(
        self,
        dictionaries_dir: str,
        request_token: int,
        records: tuple[object, ...],
        error: str,
    ) -> None: ...


class LookupDictionaryHealthLoader(QObject):
    """Run bounded dictionary probes after the Settings UI has rendered."""

    _loaded = Signal(str, int, object, str)

    def __init__(self) -> None:
        super().__init__()
        self._targets: dict[
            tuple[str, int], weakref.ReferenceType[LookupDictionaryHealthTarget]
        ] = {}
        self._loaded.connect(self._on_loaded)

    def request(
        self,
        target: LookupDictionaryHealthTarget,
        dictionaries_dir: str | Path,
        request_token: int,
    ) -> None:
        path = str(Path(dictionaries_dir))
        self._targets[(path, request_token)] = weakref.ref(target)
        threading.Thread(
            target=self._load,
            args=(path, request_token),
            name="LexiShiftLookupDictionaryHealth",
            daemon=True,
        ).start()

    def _load(self, dictionaries_dir: str, request_token: int) -> None:
        try:
            records = inspect_installed_lookup_dictionary_health(Path(dictionaries_dir))
            error = ""
        except Exception as exc:  # noqa: BLE001
            records = ()
            error = str(exc)
        self._loaded.emit(dictionaries_dir, request_token, records, error)

    @Slot(str, int, object, str)
    def _on_loaded(
        self,
        dictionaries_dir: str,
        request_token: int,
        records: tuple[object, ...],
        error: str,
    ) -> None:
        target_ref = self._targets.pop((dictionaries_dir, request_token), None)
        target = target_ref() if target_ref is not None else None
        if target is None:
            return
        try:
            target._accept_lookup_dictionary_health(
                dictionaries_dir,
                request_token,
                records,
                error,
            )
        except RuntimeError:
            # PySide wrappers can outlive their deleted C++ widget briefly.
            return


_LOOKUP_DICTIONARY_HEALTH_LOADER: LookupDictionaryHealthLoader | None = None


def request_lookup_dictionary_health(
    target: LookupDictionaryHealthTarget,
    dictionaries_dir: str | Path,
    request_token: int,
) -> None:
    global _LOOKUP_DICTIONARY_HEALTH_LOADER
    if _LOOKUP_DICTIONARY_HEALTH_LOADER is None:
        _LOOKUP_DICTIONARY_HEALTH_LOADER = LookupDictionaryHealthLoader()
    _LOOKUP_DICTIONARY_HEALTH_LOADER.request(
        target,
        dictionaries_dir,
        request_token,
    )
