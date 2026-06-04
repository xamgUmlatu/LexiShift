from __future__ import annotations

import json


def build_auxiliary_gloss_metadata(
    *,
    entry_ord: object,
    sense_ord: object,
    gloss_ord: object,
    raw_glosses_json: object,
    sense_examples_json: object,
    sense_tags_json: object,
    sense_topics_json: object,
    sense_categories_json: object,
    form_of_json: object,
    alt_of_json: object,
    entry_pos_title: object,
    entry_tags_json: object,
    entry_categories_json: object,
    translation_sense_text: object,
    translation_english_text: object,
    translation_note_text: object,
    translation_roman_text: object,
    translation_tags_json: object,
) -> dict[str, object]:
    metadata: dict[str, object] = {}
    _set_int_metadata(metadata, "entry_ord", entry_ord)
    _set_int_metadata(metadata, "sense_ord", sense_ord)
    _set_int_metadata(metadata, "gloss_ord", gloss_ord)
    _set_text_metadata(metadata, "entry_pos_title", entry_pos_title)
    _set_text_metadata(metadata, "translation_sense_text", translation_sense_text)
    _set_text_metadata(metadata, "translation_english_text", translation_english_text)
    _set_text_metadata(metadata, "translation_note_text", translation_note_text)
    _set_text_metadata(metadata, "translation_roman_text", translation_roman_text)
    _set_json_metadata(metadata, "entry_tags", entry_tags_json)
    _set_json_metadata(metadata, "entry_categories", entry_categories_json)
    _set_json_metadata(metadata, "sense_raw_glosses", raw_glosses_json)
    _set_json_metadata(metadata, "sense_examples", sense_examples_json)
    _set_json_metadata(metadata, "sense_tags", sense_tags_json)
    _set_json_metadata(metadata, "sense_topics", sense_topics_json)
    _set_json_metadata(metadata, "sense_categories", sense_categories_json)
    _set_json_metadata(metadata, "sense_form_of", form_of_json)
    _set_json_metadata(metadata, "sense_alt_of", alt_of_json)
    _set_json_metadata(metadata, "translation_tags", translation_tags_json)
    return metadata


def _set_text_metadata(metadata: dict[str, object], key: str, value: object) -> None:
    text = str(value or "").strip()
    if text:
        metadata[key] = text


def _set_int_metadata(metadata: dict[str, object], key: str, value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        metadata[key] = value
        return
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return
        try:
            metadata[key] = int(text)
        except ValueError:
            return


def _set_json_metadata(metadata: dict[str, object], key: str, value: object) -> None:
    parsed = _parse_json_column(value)
    if parsed in (None, "", [], {}):
        return
    metadata[key] = parsed


def _parse_json_column(value: object) -> object:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text
