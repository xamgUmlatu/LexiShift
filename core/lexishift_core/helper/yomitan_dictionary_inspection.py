from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import zipfile

from lexishift_core.helper.yomitan_lookup_dictionaries import (
    MAX_INDEX_BYTES,
    YomitanDictionaryImportError,
    _read_json_member,
    _TERM_BANK_NAME,
    _validated_archive_members,
    _validated_index,
)


@dataclass(frozen=True)
class YomitanDictionaryArchiveInfo:
    path: Path
    title: str
    revision: str
    format: int
    author: str = ""
    source_language: str = ""
    target_language: str = ""


def inspect_yomitan_dictionary_zip(archive_path: Path) -> YomitanDictionaryArchiveInfo:
    """Read only enough of a ZIP to prove it is a supported Yomitan term dictionary."""

    source = Path(archive_path)
    if not source.exists() or not source.is_file():
        raise YomitanDictionaryImportError("Dictionary ZIP does not exist.")
    try:
        archive = zipfile.ZipFile(source)
    except (OSError, zipfile.BadZipFile) as exc:
        raise YomitanDictionaryImportError("The selected file is not a valid ZIP archive.") from exc
    with archive:
        members = _validated_archive_members(archive)
        index_member = members.get("index.json")
        if index_member is None:
            raise YomitanDictionaryImportError("Yomitan dictionary ZIP is missing index.json.")
        metadata = _validated_index(
            _read_json_member(archive, index_member, size_limit=MAX_INDEX_BYTES)
        )
        if not any(_TERM_BANK_NAME.fullmatch(name) for name in members):
            raise YomitanDictionaryImportError(
                "Yomitan dictionary ZIP does not contain any term_bank_*.json files."
            )
    return YomitanDictionaryArchiveInfo(
        path=source,
        title=str(metadata["title"]),
        revision=str(metadata["revision"]),
        format=int(str(metadata["format"])),
        author=str(metadata["author"]),
        source_language=str(metadata["source_language"]),
        target_language=str(metadata["target_language"]),
    )


__all__ = ["YomitanDictionaryArchiveInfo", "inspect_yomitan_dictionary_zip"]
