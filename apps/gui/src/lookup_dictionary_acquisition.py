from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Sequence

from PySide6.QtCore import QSettings, QStandardPaths

from lexishift_core.helper.lp_capabilities import normalize_pair_key
from lexishift_core.helper.yomitan_dictionary_inspection import (
    YomitanDictionaryArchiveInfo,
    inspect_yomitan_dictionary_zip,
)
from lexishift_core.helper.yomitan_lookup_dictionaries import YomitanDictionaryImportError


ACQUISITION_STARTED_KEY = "resources/lookup_dictionary_acquisition_started_epoch"
ACQUISITION_PAIR_KEY = "resources/lookup_dictionary_acquisition_pair"
ACQUISITION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
DOWNLOAD_MTIME_SLOP_SECONDS = 60
SCAN_LIMIT = 24


@dataclass(frozen=True)
class LookupDictionaryAcquisitionContext:
    started_epoch: float
    pair: str


def begin_lookup_dictionary_acquisition(pair: str, *, now: float | None = None) -> None:
    settings = QSettings()
    settings.setValue(ACQUISITION_STARTED_KEY, int(time.time() if now is None else now))
    settings.setValue(ACQUISITION_PAIR_KEY, normalize_pair_key(pair, default=""))


def clear_lookup_dictionary_acquisition() -> None:
    settings = QSettings()
    settings.remove(ACQUISITION_STARTED_KEY)
    settings.remove(ACQUISITION_PAIR_KEY)


def load_lookup_dictionary_acquisition(
    *,
    now: float | None = None,
) -> LookupDictionaryAcquisitionContext | None:
    settings = QSettings()
    try:
        started_epoch = float(str(settings.value(ACQUISITION_STARTED_KEY, 0) or 0))
    except (TypeError, ValueError):
        started_epoch = 0
    pair = normalize_pair_key(
        str(settings.value(ACQUISITION_PAIR_KEY, "") or ""),
        default="",
    )
    age_seconds = (time.time() if now is None else now) - started_epoch
    if (
        started_epoch <= 0
        or not pair
        or age_seconds < -DOWNLOAD_MTIME_SLOP_SECONDS
        or age_seconds > ACQUISITION_MAX_AGE_SECONDS
    ):
        if started_epoch or pair:
            clear_lookup_dictionary_acquisition()
        return None
    return LookupDictionaryAcquisitionContext(started_epoch=started_epoch, pair=pair)


def lookup_dictionary_download_search_dirs() -> tuple[Path, ...]:
    raw_directories = [
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation),
        str(Path.home() / "Downloads"),
    ]
    directories: list[Path] = []
    seen: set[str] = set()
    for raw_directory in raw_directories:
        path = Path(str(raw_directory or "")).expanduser()
        if not path.is_dir():
            continue
        normalized = str(path.resolve())
        if normalized in seen:
            continue
        seen.add(normalized)
        directories.append(path)
    return tuple(directories)


def find_lookup_dictionary_download_candidate(
    context: LookupDictionaryAcquisitionContext,
    *,
    directories: Sequence[Path],
) -> YomitanDictionaryArchiveInfo | None:
    candidates: list[tuple[float, Path]] = []
    for directory in directories:
        try:
            children = tuple(Path(directory).iterdir())
        except OSError:
            continue
        for path in children:
            if path.suffix.casefold() != ".zip" or not path.is_file():
                continue
            try:
                modified_epoch = path.stat().st_mtime
            except OSError:
                continue
            if modified_epoch + DOWNLOAD_MTIME_SLOP_SECONDS < context.started_epoch:
                continue
            candidates.append((modified_epoch, path))
    candidates.sort(key=lambda item: (item[0], item[1].name), reverse=True)
    expected_language = context.pair.partition("-")[2]
    for _modified_epoch, path in candidates[:SCAN_LIMIT]:
        try:
            info = inspect_yomitan_dictionary_zip(path)
        except (OSError, YomitanDictionaryImportError):
            continue
        if info.source_language and info.source_language != expected_language:
            continue
        return info
    return None


__all__ = [
    "LookupDictionaryAcquisitionContext",
    "begin_lookup_dictionary_acquisition",
    "clear_lookup_dictionary_acquisition",
    "find_lookup_dictionary_download_candidate",
    "load_lookup_dictionary_acquisition",
    "lookup_dictionary_download_search_dirs",
]
