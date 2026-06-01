from __future__ import annotations

from pathlib import Path
import shutil

from language_packs import FrequencyPackDownloadThread
from language_packs_catalog import FrequencyPackInfo


def import_frequency_source_file(
    pack: FrequencyPackInfo,
    source_path: str | Path,
    *,
    frequency_pack_dir: str | Path,
) -> Path:
    source = Path(source_path)
    if not source.is_file():
        raise FileNotFoundError(str(source))
    pack_root = Path(frequency_pack_dir) / pack.pack_id
    pack_root.mkdir(parents=True, exist_ok=True)
    staged_source = _staged_source_path(pack, pack_root)
    if source.resolve(strict=False) == staged_source.resolve(strict=False):
        staged_source = pack_root / f".import-copy-{staged_source.name.removeprefix('.import-')}"
    if staged_source.exists():
        staged_source.unlink()
    shutil.copy2(source, staged_source)
    sqlite_path = pack_root / pack.sqlite_filename
    converter = FrequencyPackDownloadThread(pack, str(staged_source), str(sqlite_path))
    try:
        final_path = converter._convert_to_sqlite(str(staged_source))  # noqa: SLF001
        converter._write_manifest(final_path)  # noqa: SLF001
    except Exception:
        _cleanup_partial_sqlite(sqlite_path)
        raise
    return Path(final_path)


def _staged_source_path(pack: FrequencyPackInfo, pack_root: Path) -> Path:
    filename = str(pack.source_filename or pack.filename or "source.txt").strip() or "source.txt"
    return pack_root / f".import-{filename}"


def _cleanup_partial_sqlite(sqlite_path: Path) -> None:
    for path in (sqlite_path, Path(f"{sqlite_path}-wal"), Path(f"{sqlite_path}-shm")):
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
