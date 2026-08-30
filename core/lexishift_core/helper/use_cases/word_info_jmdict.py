from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Sequence

from lexishift_core.lexicon.word_package import normalize_reading
from lexishift_core.resources.dict_loaders import JmdictEntryRecord, TranslationGlossRecord
from lexishift_core.resources.jmdict_records import JmdictReadingRecord, JmdictSenseRecord


@dataclass(frozen=True)
class JmdictDefinitionSelection:
    entries: tuple[JmdictEntryRecord, ...]
    match_quality: str
    matched_surface: str = ""
    matched_reading: str = ""


def select_jmdict_definition_entries(
    entries: Sequence[JmdictEntryRecord],
    *,
    surface: str,
    reading: str,
) -> JmdictDefinitionSelection:
    normalized_surface = _normalize(surface)
    normalized_reading = _normalize(reading)
    exact_entries = [
        entry
        for entry in entries
        if normalized_surface
        and normalized_reading
        and _entry_supports_surface_reading(
            entry,
            surface=normalized_surface,
            reading=normalized_reading,
        )
    ]
    if exact_entries:
        return JmdictDefinitionSelection(
            entries=tuple(
                _filter_entry_senses(
                    entry,
                    surface=normalized_surface,
                    reading=normalized_reading,
                )
                for entry in exact_entries
            ),
            match_quality="exact_surface_reading",
            matched_surface=str(surface or "").strip(),
            matched_reading=str(reading or "").strip(),
        )

    fallback_entries = tuple(
        _filter_entry_senses(
            entry,
            surface=normalized_surface,
            reading=normalized_reading,
        )
        for entry in entries
    )
    quality = (
        "surface_only" if normalized_surface and not normalized_reading else "candidate_fallback"
    )
    if not fallback_entries:
        quality = "none"
    return JmdictDefinitionSelection(
        entries=fallback_entries,
        match_quality=quality,
        matched_surface=str(surface or "").strip() if fallback_entries else "",
        matched_reading="",
    )


def jmdict_gloss_records(
    entries: Sequence[JmdictEntryRecord],
) -> list[TranslationGlossRecord]:
    records: list[TranslationGlossRecord] = []
    for entry in entries:
        for sense in entry.senses:
            records.extend(
                TranslationGlossRecord(translation=gloss.text, pos_raw="")
                for gloss in sense.glosses
            )
    return records


def jmdict_entries_for_candidates(
    entries_by_headword: Mapping[str, Sequence[JmdictEntryRecord]],
    lookup_candidates: Sequence[str],
) -> list[JmdictEntryRecord]:
    lookup_set = {_normalize(candidate) for candidate in lookup_candidates}
    entries: list[JmdictEntryRecord] = []
    seen: set[int] = set()
    for headword, candidates in entries_by_headword.items():
        if _normalize(headword) not in lookup_set:
            continue
        for entry in candidates:
            identity = id(entry)
            if identity in seen:
                continue
            seen.add(identity)
            entries.append(entry)
    return entries


def _entry_supports_surface_reading(
    entry: JmdictEntryRecord,
    *,
    surface: str,
    reading: str,
) -> bool:
    kanji_forms = {_normalize(value) for value in entry.kanji_forms}
    kana_forms = {_normalize(value) for value in entry.kana_forms}
    matching_readings = [
        record for record in _entry_reading_records(entry) if _normalize(record.text) == reading
    ]
    if not matching_readings:
        return False
    if surface in kana_forms and surface == reading:
        return True
    if surface not in kanji_forms:
        return False
    return any(_reading_allows_surface(record, surface=surface) for record in matching_readings)


def _entry_reading_records(entry: JmdictEntryRecord) -> tuple[JmdictReadingRecord, ...]:
    if entry.reading_records:
        return entry.reading_records
    return tuple(JmdictReadingRecord(text=value) for value in entry.kana_forms)


def _reading_allows_surface(record: JmdictReadingRecord, *, surface: str) -> bool:
    if record.no_kanji:
        return False
    restrictions = {_normalize(value) for value in record.kanji_restrictions}
    return not restrictions or surface in restrictions


def _filter_entry_senses(
    entry: JmdictEntryRecord,
    *,
    surface: str,
    reading: str,
) -> JmdictEntryRecord:
    senses = tuple(
        sense for sense in entry.senses if _sense_applies(sense, surface=surface, reading=reading)
    )
    glosses = tuple(gloss.text for sense in senses for gloss in sense.glosses)
    return replace(entry, senses=senses, glosses=glosses)


def _sense_applies(
    sense: JmdictSenseRecord,
    *,
    surface: str,
    reading: str,
) -> bool:
    written_restrictions = {_normalize(value) for value in sense.kanji_restrictions}
    reading_restrictions = {_normalize(value) for value in sense.reading_restrictions}
    if written_restrictions and surface and surface not in written_restrictions:
        return False
    if reading_restrictions and reading and reading not in reading_restrictions:
        return False
    return True


def _normalize(value: object) -> str:
    return normalize_reading(value, language_tag="ja").casefold()
