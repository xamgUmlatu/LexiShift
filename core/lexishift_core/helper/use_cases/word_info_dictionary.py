from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from lexishift_core.helper.translation_packs import TranslationPackRef
from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.resources.installed_packs import load_installed_pack_manifest_for_artifact


def records_for_candidates(
    records_by_headword: Mapping[str, Sequence[TranslationGlossRecord]],
    lookup_candidates: Sequence[str],
) -> list[TranslationGlossRecord]:
    lookup_set = {_normalize(candidate) for candidate in lookup_candidates}
    records: list[TranslationGlossRecord] = []
    for headword, entries in records_by_headword.items():
        if _normalize(headword) not in lookup_set:
            continue
        records.extend(entries)
    return records


def matched_headword(
    records_by_headword: Mapping[str, Sequence[TranslationGlossRecord]],
    lookup_candidates: Sequence[str],
) -> str:
    lookup_set = {_normalize(candidate) for candidate in lookup_candidates}
    for headword, records in records_by_headword.items():
        if records and _normalize(headword) in lookup_set:
            return str(headword or "").strip()
    return ""


def translation_dictionary_metadata(resolved_pack: TranslationPackRef) -> dict[str, object]:
    return dictionary_metadata_for_path(
        resolved_pack.path,
        fallback_pack_id=resolved_pack.pack_id,
        fallback_provider=resolved_pack.provider,
        source_kind="installed_translation_pack",
    )


def translation_dictionary_match(
    matched_headword_value: str,
    *,
    lookup_surface: str,
) -> dict[str, object]:
    matched = str(matched_headword_value or "").strip()
    if not matched:
        return {"surface": "", "reading": "", "quality": "none"}
    quality = (
        "exact_surface"
        if _normalize(matched) == _normalize(lookup_surface)
        else "candidate_fallback"
    )
    return {"surface": matched, "reading": "", "quality": quality}


def jmdict_gloss_records_for_candidates(
    glosses_by_headword: Mapping[str, Sequence[str]],
    lookup_candidates: Sequence[str],
) -> list[TranslationGlossRecord]:
    lookup_set = {_normalize(candidate) for candidate in lookup_candidates}
    records: list[TranslationGlossRecord] = []
    for headword, glosses in glosses_by_headword.items():
        if _normalize(headword) not in lookup_set:
            continue
        records.extend(TranslationGlossRecord(translation=gloss, pos_raw="") for gloss in glosses)
    return records


def dictionary_metadata_for_path(
    path: Path,
    *,
    fallback_pack_id: str,
    fallback_provider: str,
    source_kind: str,
) -> dict[str, object]:
    manifest = load_installed_pack_manifest_for_artifact(path)
    return {
        "pack_id": _first_text(
            getattr(manifest, "pack_id", "") if manifest is not None else "",
            fallback_pack_id,
        ),
        "provider": _first_text(
            getattr(manifest, "provider", "") if manifest is not None else "",
            fallback_provider,
        ),
        "source_kind": str(source_kind or "").strip(),
    }


def _first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _normalize(value: object) -> str:
    return str(value or "").strip().casefold()
