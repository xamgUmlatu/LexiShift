from __future__ import annotations

import re
from typing import Mapping, Sequence

from lexishift_core.resources.dict_loaders import (
    JmdictEntryRecord,
    TranslationGlossRecord,
)
from lexishift_core.resources.jmdict_records import JmdictSenseRecord


_JMDICT_ORTHOGRAPHY_NOTE_CLAUSE = re.compile(
    r"(?P<written_form>[^\s;]+) signifies (?P<description>[^;]+)"
)


def build_translation_sense_payloads(
    records: Sequence[TranslationGlossRecord],
    *,
    language: str,
    source: str,
    source_kind: str,
    sense_limit: int,
    detail_limit: int,
    example_limit: int,
    label_limit: int,
) -> list[dict[str, object]]:
    grouped: dict[str, list[TranslationGlossRecord]] = {}
    for index, record in enumerate(records):
        group_id = _record_sense_group_id(record)
        key = group_id or f"record:{index}"
        if key not in grouped and len(grouped) >= sense_limit:
            continue
        grouped.setdefault(key, []).append(record)
    payloads: list[dict[str, object]] = []
    for records_in_sense in grouped.values():
        payload = _translation_sense_payload(
            records_in_sense,
            language=language,
            source=source,
            source_kind=source_kind,
            rank=len(payloads) + 1,
            detail_limit=detail_limit,
            example_limit=example_limit,
            label_limit=label_limit,
        )
        if payload:
            payloads.append(payload)
    return payloads


def build_jmdict_sense_payloads(
    entries: Sequence[JmdictEntryRecord],
    *,
    language: str,
    source: str,
    source_kind: str,
    sense_limit: int,
    detail_limit: int,
    label_limit: int,
) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    for entry in entries:
        for sense in entry.senses:
            signature = _jmdict_sense_signature(sense)
            if signature in seen:
                continue
            seen.add(signature)
            payload = _jmdict_sense_payload(
                sense,
                entry_written_forms=entry.kanji_forms,
                language=language,
                source=source,
                source_kind=source_kind,
                rank=len(payloads) + 1,
                detail_limit=detail_limit,
                label_limit=label_limit,
            )
            if payload:
                payloads.append(payload)
            if len(payloads) >= sense_limit:
                return payloads
    return payloads


def _translation_sense_payload(
    records: Sequence[TranslationGlossRecord],
    *,
    language: str,
    source: str,
    source_kind: str,
    rank: int,
    detail_limit: int,
    example_limit: int,
    label_limit: int,
) -> dict[str, object]:
    glosses: list[dict[str, str]] = []
    pos_values: list[str] = []
    details: list[str] = []
    labels: list[str] = []
    examples: list[dict[str, str]] = []
    sense_id = ""
    for record in records:
        raw_text = str(record.translation or "").strip()
        text, inline_detail = _split_inline_gloss_detail(raw_text)
        if text and text.casefold() not in {
            str(item.get("text") or "").casefold() for item in glosses
        }:
            glosses.append({"text": text})
        _append_unique(pos_values, getattr(record, "pos_raw", ""))
        metadata = _record_metadata(record)
        sense_id = sense_id or _record_sense_group_id(record)
        for detail in _sense_details(metadata, fallback_text=text):
            _append_unique(details, detail)
        _append_unique(details, inline_detail)
        for key in (
            "translation_sense_text",
            "translation_english_text",
            "translation_note_text",
        ):
            _append_unique(details, metadata.get(key))
        for key in (
            "sense_tags",
            "sense_topics",
            "sense_categories",
            "translation_tags",
        ):
            for label in _string_items(metadata.get(key)):
                _append_unique(labels, label)
        for example in _sense_examples(metadata, limit=example_limit):
            if example not in examples:
                examples.append(example)
    if not glosses:
        return {}
    payload: dict[str, object] = {
        "glosses": glosses,
        "language": str(language or "").strip(),
        "source": str(source or "").strip(),
        "source_kind": source_kind,
        "rank": rank,
    }
    if sense_id:
        payload["sense_id"] = sense_id
    if pos_values:
        payload["pos"] = pos_values
    if details:
        payload["details"] = details[:detail_limit]
    if labels:
        payload["labels"] = labels[:label_limit]
    if examples:
        payload["examples"] = examples[:example_limit]
    return payload


def _jmdict_sense_signature(sense: JmdictSenseRecord) -> tuple[object, ...]:
    return (
        tuple(gloss.text.casefold() for gloss in sense.glosses),
        sense.kanji_restrictions,
        sense.reading_restrictions,
        sense.pos_values,
        sense.field_values,
        sense.misc_values,
        sense.info_values,
        sense.dialect_values,
    )


def _jmdict_sense_payload(
    sense: JmdictSenseRecord,
    *,
    entry_written_forms: Sequence[str],
    language: str,
    source: str,
    source_kind: str,
    rank: int,
    detail_limit: int,
    label_limit: int,
) -> dict[str, object]:
    glosses: list[dict[str, object]] = []
    for gloss in sense.glosses:
        text = _truncate_text(gloss.text)
        if not text:
            continue
        item: dict[str, object] = {"text": text}
        if gloss.language:
            item["language"] = gloss.language
        if gloss.gloss_type:
            item["type"] = gloss.gloss_type
        if gloss.gender:
            item["gender"] = gloss.gender
        if gloss.priority_values:
            item["priority"] = list(gloss.priority_values)
        glosses.append(item)
    if not glosses:
        return {}
    labels: list[str] = []
    for values in (sense.field_values, sense.misc_values, sense.dialect_values):
        for value in values:
            _append_unique(labels, value)
    payload: dict[str, object] = {
        "glosses": glosses,
        "language": str(language or "").strip(),
        "source": str(source or "").strip(),
        "source_kind": source_kind,
        "rank": rank,
    }
    if sense.pos_values:
        payload["pos"] = list(sense.pos_values)
    if sense.info_values:
        payload["details"] = list(sense.info_values)[:detail_limit]
        structured_notes = _jmdict_structured_notes(
            sense.info_values[:detail_limit],
            entry_written_forms=entry_written_forms,
        )
        if structured_notes:
            payload["structured_notes"] = structured_notes
    if labels:
        payload["labels"] = labels[:label_limit]
    if sense.kanji_restrictions or sense.reading_restrictions:
        payload["restrictions"] = {
            "written_forms": list(sense.kanji_restrictions),
            "readings": list(sense.reading_restrictions),
        }
    if sense.cross_references:
        payload["cross_references"] = list(sense.cross_references)
    if sense.antonyms:
        payload["antonyms"] = list(sense.antonyms)
    return payload


def _jmdict_structured_notes(
    info_values: Sequence[str],
    *,
    entry_written_forms: Sequence[str],
) -> list[dict[str, object]]:
    known_forms = {str(value or "").strip() for value in entry_written_forms}
    known_forms.discard("")
    if not known_forms:
        return []
    structured: list[dict[str, object]] = []
    for value in info_values:
        source_text = str(value or "").strip()
        normalized_text = " ".join(source_text.split())
        clauses = [clause.strip() for clause in normalized_text.split(";")]
        if len(clauses) < 2 or any(not clause for clause in clauses):
            continue
        items: list[dict[str, str]] = []
        for clause in clauses:
            match = _JMDICT_ORTHOGRAPHY_NOTE_CLAUSE.fullmatch(clause)
            if match is None:
                items = []
                break
            written_form = match.group("written_form").strip()
            description = match.group("description").strip()
            if written_form not in known_forms or not description:
                items = []
                break
            items.append(
                {
                    "written_form": written_form,
                    "text": _truncate_text(description),
                }
            )
        if items:
            structured.append(
                {
                    "kind": "orthography_variants",
                    "source_text": source_text,
                    "items": items,
                }
            )
    return structured


def _record_metadata(record: TranslationGlossRecord) -> Mapping[str, object]:
    metadata = getattr(record, "metadata", None)
    return metadata if isinstance(metadata, Mapping) else {}


def _record_sense_group_id(record: TranslationGlossRecord) -> str:
    metadata = _record_metadata(record)
    parts: list[str] = []
    for key in ("entry_ord", "sense_ord"):
        value = metadata.get(key)
        if value is not None and str(value).strip():
            parts.append(f"{key}:{value}")
    return "|".join(parts) if len(parts) == 2 else ""


def _sense_details(metadata: Mapping[str, object], *, fallback_text: str) -> list[str]:
    details: list[str] = []
    fallback_normalized = str(fallback_text or "").strip().casefold()
    for value in _string_items(metadata.get("sense_raw_glosses")):
        if value.casefold() != fallback_normalized:
            _append_unique(details, value)
    return details


def _sense_examples(
    metadata: Mapping[str, object],
    *,
    limit: int,
) -> list[dict[str, str]]:
    examples: list[dict[str, str]] = []
    raw_examples = metadata.get("sense_examples")
    if not isinstance(raw_examples, Sequence) or isinstance(raw_examples, (str, bytes)):
        return examples
    for raw in raw_examples:
        if not isinstance(raw, Mapping):
            continue
        text = _truncate_text(raw.get("text"))
        translation = _truncate_text(raw.get("translation") or raw.get("english"))
        if not text and not translation:
            continue
        example: dict[str, str] = {}
        if text:
            example["text"] = text
        if translation and translation.casefold() != text.casefold():
            example["translation"] = translation
        if example not in examples:
            examples.append(example)
        if len(examples) >= limit:
            break
    return examples


def _split_inline_gloss_detail(value: str) -> tuple[str, str]:
    text = " ".join(str(value or "").strip().split())
    if not text.endswith(")") or " (" not in text:
        return _truncate_text(text), ""
    head, detail = text.split(" (", 1)
    head = head.strip()
    detail = detail[:-1].strip()
    if not head or not detail:
        return _truncate_text(text), ""
    return _truncate_text(head), _truncate_text(detail)


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        raw_values: Sequence[object] = (value,)
    elif isinstance(value, Sequence):
        raw_values = value
    else:
        return []
    return [text for raw in raw_values if (text := _truncate_text(raw))]


def _append_unique(values: list[str], value: object) -> None:
    text = _truncate_text(value)
    if text and text.casefold() not in {item.casefold() for item in values}:
        values.append(text)


def _truncate_text(value: object, *, limit: int = 160) -> str:
    text = " ".join(str(value or "").strip().split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."
