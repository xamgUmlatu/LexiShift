from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import gzip
import html
import json
import math
from pathlib import Path
import re
import unicodedata
from typing import Iterable, Mapping, Sequence
from xml.etree import ElementTree

from lexishift_core.resources.japanese_script import contains_kanji
from lexishift_core.resources.path_cache import load_or_compute_path_json_value


JAPANESE_LEARNER_SIGNALS_VERSION = "japanese_learner_signals_v18"
JMDICT_PRIORITY_INDEX_VERSION = "jmdict_priority_index_v4"
JMDICT_LEXICAL_INDEX_VERSION = "jmdict_lexical_index_v6"
KANJIDIC2_INDEX_VERSION = "kanjidic2_character_index_v3"
JMNEDICT_NAME_INDEX_VERSION = "jmnedict_name_index_v1"
KANJIVG_CHARACTER_INDEX_VERSION = "kanjivg_character_index_v2"
JLPT_VOCABULARY_INDEX_VERSION = "jlpt_vocabulary_index_v7"
JAPANESE_LESSON_VOCABULARY_INDEX_VERSION = "japanese_lesson_vocabulary_index_v2"
JA_ACRONYM_SIGNAL_VERSION = "ja_acronym_signal_v1"

_JMDICT_PRIMARY_PRIORITY_TAGS = frozenset({"news1", "ichi1", "spec1", "gai1"})
_JMDICT_SECONDARY_PRIORITY_TAGS = frozenset({"news2", "ichi2", "gai2"})
_NF_RE = re.compile(r"^nf(\d{1,2})$")
_HTML_ROW_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_HTML_CELL_RE = re.compile(r"<(?:td|th)\b[^>]*>(.*?)</(?:td|th)>", re.IGNORECASE | re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_JAPANESE_TEXT_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
_ACRONYM_GLOSS_WORD_RE = re.compile(r"[A-Za-z]+")
_ACRONYM_ALLOWED_SEPARATORS = frozenset("-_./+&")
_ACRONYM_GLOSS_INITIAL_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "at",
        "by",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "or",
        "per",
        "the",
        "to",
        "with",
        "without",
    }
)
_ACRONYM_JAPANESE_USAGE_GLOSS_CUES = (
    "commercial message",
    "commercial (on radio",
    "commercial (on tv",
    "office lady",
    "no good",
    "not allowed",
    "not acceptable",
    "outtake",
    "blooper",
    "social networking service",
    "social networking site",
    "social media",
)
_ACRONYM_DOMAIN_FIELDS = frozenset(
    {
        "anatomy",
        "architecture",
        "baseball",
        "biochemistry",
        "biology",
        "botany",
        "business",
        "chemistry",
        "computing",
        "economics",
        "engineering",
        "finance",
        "food",
        "geology",
        "internet",
        "law",
        "medicine",
        "music",
        "physics",
        "politics",
        "sports",
        "telecommunications",
        "zoology",
    }
)
_ACRONYM_LETTER_READINGS = {
    "A": ("えー", "えい"),
    "B": ("びー",),
    "C": ("しー",),
    "D": ("でぃー", "でー"),
    "E": ("いー",),
    "F": ("えふ",),
    "G": ("じー",),
    "H": ("えいち", "えっち"),
    "I": ("あい",),
    "J": ("じぇー", "じぇい"),
    "K": ("けー", "けい"),
    "L": ("える",),
    "M": ("えむ",),
    "N": ("えぬ",),
    "O": ("おー", "おう"),
    "P": ("ぴー",),
    "Q": ("きゅー", "きゅう"),
    "R": ("あーる",),
    "S": ("えす",),
    "T": ("てぃー", "てぃ"),
    "U": ("ゆー",),
    "V": ("ぶい",),
    "W": ("だぶりゅー", "だぶる"),
    "X": ("えっくす",),
    "Y": ("わい",),
    "Z": ("ぜっと", "ずぃー"),
}


@dataclass(frozen=True)
class JmdictPriorityPairRecord:
    surface: str = ""
    reading: str = ""
    surface_tags: tuple[str, ...] = ()
    reading_tags: tuple[str, ...] = ()
    entry_tags: tuple[str, ...] = ()
    surface_info_values: tuple[str, ...] = ()
    reading_info_values: tuple[str, ...] = ()
    surface_reading_count: int = 0
    direct_priority_score: float = 0.0
    direct_priority_band: str = "none"
    entry_priority_score: float = 0.0
    entry_priority_band: str = "none"
    safe_priority_score: float = 0.0
    safe_priority_band: str = "none"
    safe_priority_kind: str = "none"

    def to_dict(self) -> dict[str, object]:
        return {
            "surface": self.surface,
            "reading": self.reading,
            "surface_tags": list(self.surface_tags),
            "reading_tags": list(self.reading_tags),
            "entry_tags": list(self.entry_tags),
            "surface_info_values": list(self.surface_info_values),
            "reading_info_values": list(self.reading_info_values),
            "surface_reading_count": int(self.surface_reading_count),
            "direct_priority_score": round(float(self.direct_priority_score), 6),
            "direct_priority_band": self.direct_priority_band,
            "entry_priority_score": round(float(self.entry_priority_score), 6),
            "entry_priority_band": self.entry_priority_band,
            "safe_priority_score": round(float(self.safe_priority_score), 6),
            "safe_priority_band": self.safe_priority_band,
            "safe_priority_kind": self.safe_priority_kind,
            "entry_priority_inherited_only": bool(
                self.entry_priority_score > self.safe_priority_score
            ),
            "priority_leak_risk": bool(
                self.entry_priority_score > self.safe_priority_score
                and (
                    self.safe_priority_kind
                    in {
                        "entry_inherited_only",
                        "surface_only_multi_reading",
                        "marked_form_not_safe",
                    }
                    or bool(self.surface_info_values)
                    or bool(self.reading_info_values)
                )
            ),
        }


@dataclass(frozen=True)
class JmdictPriorityRecord:
    direct_tags: tuple[str, ...] = ()
    entry_tags: tuple[str, ...] = ()
    priority_score: float = 0.0
    priority_band: str = "none"
    nf_min: int | None = None
    direct_priority_score: float = 0.0
    direct_priority_band: str = "none"
    direct_nf_min: int | None = None
    entry_priority_score: float = 0.0
    entry_priority_band: str = "none"
    entry_nf_min: int | None = None
    pair_records: tuple[JmdictPriorityPairRecord, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "direct_tags": list(self.direct_tags),
            "entry_tags": list(self.entry_tags),
            "priority_score": round(float(self.priority_score), 6),
            "priority_band": self.priority_band,
            "nf_min": self.nf_min,
            "direct_priority_score": round(float(self.direct_priority_score), 6),
            "direct_priority_band": self.direct_priority_band,
            "direct_nf_min": self.direct_nf_min,
            "entry_priority_score": round(float(self.entry_priority_score), 6),
            "entry_priority_band": self.entry_priority_band,
            "entry_nf_min": self.entry_nf_min,
            "entry_priority_inherited": bool(
                self.entry_priority_score > self.direct_priority_score
            ),
            "pair_records": [record.to_dict() for record in self.pair_records],
        }


@dataclass(frozen=True)
class JmdictLexicalRecord:
    pos_values: tuple[str, ...] = ()
    misc_values: tuple[str, ...] = ()
    field_values: tuple[str, ...] = ()
    dial_values: tuple[str, ...] = ()
    source_language_values: tuple[str, ...] = ()
    kanji_info_values: tuple[str, ...] = ()
    reading_info_values: tuple[str, ...] = ()
    gloss_values: tuple[str, ...] = ()
    gloss_language_values: tuple[str, ...] = ()
    lexical_class_groups: tuple[str, ...] = ()
    kanji_forms: tuple[str, ...] = ()
    reading_forms: tuple[str, ...] = ()
    form_values: tuple[str, ...] = ()
    entry_count: int = 0
    kanji_form_count: int = 0
    reading_form_count: int = 0
    form_count: int = 0
    sense_count: int = 0
    sense_info_count: int = 0
    gloss_count: int = 0
    xref_count: int = 0
    antonym_count: int = 0
    sense_restriction_count: int = 0
    reading_restriction_count: int = 0
    no_kanji_reading_count: int = 0
    non_vocab_signal_score: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "pos_values": list(self.pos_values),
            "misc_values": list(self.misc_values),
            "field_values": list(self.field_values),
            "dial_values": list(self.dial_values),
            "source_language_values": list(self.source_language_values),
            "kanji_info_values": list(self.kanji_info_values),
            "reading_info_values": list(self.reading_info_values),
            "gloss_values": list(self.gloss_values[:24]),
            "gloss_language_values": list(self.gloss_language_values),
            "lexical_class_groups": list(self.lexical_class_groups),
            "entry_count": int(self.entry_count),
            "kanji_form_count": int(self.kanji_form_count),
            "reading_form_count": int(self.reading_form_count),
            "form_count": int(self.form_count),
            "sense_count": int(self.sense_count),
            "sense_info_count": int(self.sense_info_count),
            "gloss_count": int(self.gloss_count),
            "xref_count": int(self.xref_count),
            "antonym_count": int(self.antonym_count),
            "sense_restriction_count": int(self.sense_restriction_count),
            "reading_restriction_count": int(self.reading_restriction_count),
            "no_kanji_reading_count": int(self.no_kanji_reading_count),
            "non_vocab_signal_score": round(float(self.non_vocab_signal_score), 6),
        }


@dataclass(frozen=True)
class Kanjidic2CharacterRecord:
    literal: str
    grade: int | None = None
    stroke_count: int | None = None
    freq: int | None = None
    old_jlpt: int | None = None
    on_readings: tuple[str, ...] = ()
    kun_readings: tuple[str, ...] = ()
    nanori_readings: tuple[str, ...] = ()
    meanings: tuple[str, ...] = ()
    rad_names: tuple[str, ...] = ()
    radical_values: tuple[str, ...] = ()
    variant_types: tuple[str, ...] = ()
    query_code_types: tuple[str, ...] = ()
    dictionary_reference_types: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class JmnedictNameRecord:
    surfaces: tuple[str, ...] = ()
    readings: tuple[str, ...] = ()
    name_types: tuple[str, ...] = ()
    name_type_groups: tuple[str, ...] = ()
    translation_count: int = 0
    name_signal_score: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "surfaces": list(self.surfaces),
            "readings": list(self.readings),
            "name_types": list(self.name_types),
            "name_type_groups": list(self.name_type_groups),
            "translation_count": int(self.translation_count),
            "name_signal_score": round(float(self.name_signal_score), 6),
        }


@dataclass(frozen=True)
class KanjivgCharacterRecord:
    literal: str
    path_count: int = 0
    group_count: int = 0
    max_group_depth: int = 0
    component_count: int = 0
    component_elements: tuple[str, ...] = ()
    radical_values: tuple[str, ...] = ()
    position_values: tuple[str, ...] = ()
    part_values: tuple[str, ...] = ()
    phonetic_elements: tuple[str, ...] = ()
    variant_count: int = 0
    visual_complexity_score: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "literal": self.literal,
            "path_count": int(self.path_count),
            "group_count": int(self.group_count),
            "max_group_depth": int(self.max_group_depth),
            "component_count": int(self.component_count),
            "component_elements": list(self.component_elements),
            "radical_values": list(self.radical_values),
            "position_values": list(self.position_values),
            "part_values": list(self.part_values),
            "phonetic_elements": list(self.phonetic_elements),
            "variant_count": int(self.variant_count),
            "visual_complexity_score": round(float(self.visual_complexity_score), 6),
        }


@dataclass(frozen=True)
class JlptVocabularyRecord:
    surfaces: tuple[str, ...] = ()
    readings: tuple[str, ...] = ()
    levels: tuple[int, ...] = ()
    source_count: int = 0
    entries: tuple[str, ...] = ()
    normalized_entries: tuple[str, ...] = ()
    guarded_normalized_entries: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        easiest_level = max(self.levels) if self.levels else None
        hardest_level = min(self.levels) if self.levels else None
        return {
            "surfaces": list(self.surfaces),
            "readings": list(self.readings),
            "levels": list(self.levels),
            "entries": list(self.entries),
            "normalized_entries": list(self.normalized_entries),
            "guarded_normalized_entries": list(self.guarded_normalized_entries),
            "easiest_level": easiest_level,
            "hardest_level": hardest_level,
            "source_count": int(self.source_count),
            "difficulty_score": (
                _jlpt_vocab_difficulty_score(easiest_level) if easiest_level is not None else None
            ),
            "beginner_core_score": (
                _jlpt_vocab_beginner_core_score(easiest_level)
                if easiest_level is not None
                else None
            ),
        }


@dataclass(frozen=True)
class JapaneseLessonVocabularyRecord:
    surfaces: tuple[str, ...] = ()
    readings: tuple[str, ...] = ()
    romanizations: tuple[str, ...] = ()
    glosses: tuple[str, ...] = ()
    lesson_indices: tuple[int, ...] = ()
    lesson_keys: tuple[str, ...] = ()
    lesson_titles: tuple[str, ...] = ()
    source_count: int = 0

    def to_dict(self) -> dict[str, object]:
        earliest_lesson = min(self.lesson_indices) if self.lesson_indices else None
        return {
            "surfaces": list(self.surfaces),
            "readings": list(self.readings),
            "romanizations": list(self.romanizations),
            "glosses": list(self.glosses),
            "lesson_indices": list(self.lesson_indices),
            "lesson_keys": list(self.lesson_keys),
            "lesson_titles": list(self.lesson_titles),
            "earliest_lesson": earliest_lesson,
            "source_count": int(self.source_count),
            "difficulty_score": _lesson_vocab_difficulty_score(earliest_lesson),
            "beginner_core_score": _lesson_vocab_beginner_core_score(earliest_lesson),
        }


def load_jmdict_priority_index(path: Path) -> dict[str, JmdictPriorityRecord]:
    return load_or_compute_path_json_value(
        path,
        namespace="japanese_learner_signals",
        key={"kind": "jmdict_priority", "version": JMDICT_PRIORITY_INDEX_VERSION},
        compute=lambda: _load_jmdict_priority_index_uncached(path),
        serialize=lambda value: {key: record.to_dict() for key, record in value.items()},
        deserialize=_deserialize_jmdict_priority_index,
    )


def _load_jmdict_priority_index_uncached(path: Path) -> dict[str, JmdictPriorityRecord]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return {}
    merged: dict[str, JmdictPriorityRecord] = {}
    for _event, elem in context:
        if elem.tag != "entry":
            continue
        kanji_entries = _jmdict_priority_kanji_entries(elem)
        reading_entries = _jmdict_priority_reading_entries(elem)
        entry_tags = _unique_sorted(
            tag for entry in (*kanji_entries, *reading_entries) for tag in entry["tags"]
        )
        pair_records = _jmdict_priority_pair_records(
            kanji_entries,
            reading_entries,
            entry_tags=entry_tags,
        )
        for entry in (*kanji_entries, *reading_entries):
            term = str(entry.get("term") or "").strip()
            if not term:
                continue
            record = _build_jmdict_priority_record(
                direct_tags=entry.get("tags", ()),
                entry_tags=entry_tags,
                pair_records=(
                    record
                    for record in pair_records
                    if record.surface == term or record.reading == term
                ),
            )
            existing = merged.get(term)
            merged[term] = _merge_jmdict_priority_records(existing, record)
        elem.clear()
    return merged


def load_jmnedict_name_index(path: Path) -> dict[str, JmnedictNameRecord]:
    return load_or_compute_path_json_value(
        path,
        namespace="japanese_learner_signals",
        key={"kind": "jmnedict_names", "version": JMNEDICT_NAME_INDEX_VERSION},
        compute=lambda: _load_jmnedict_name_index_uncached(path),
        serialize=lambda value: {key: record.to_dict() for key, record in value.items()},
        deserialize=_deserialize_jmnedict_name_index,
    )


def _load_jmnedict_name_index_uncached(path: Path) -> dict[str, JmnedictNameRecord]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        with _xml_text_stream(path) as source:
            context = ElementTree.iterparse(source, events=("end",))
            merged: dict[str, JmnedictNameRecord] = {}
            for _event, elem in context:
                if elem.tag != "entry":
                    continue
                surfaces = _unique_sorted(_node_text(keb) for keb in elem.findall("k_ele/keb"))
                readings = _unique_sorted(_node_text(reb) for reb in elem.findall("r_ele/reb"))
                terms = surfaces or readings
                name_types = _unique_sorted(
                    _node_text(node) for node in elem.findall("trans/name_type")
                )
                translations = _unique_sorted(
                    _node_text(node) for node in elem.findall("trans/trans_det")
                )
                record = _build_jmnedict_name_record(
                    surfaces=surfaces,
                    readings=readings,
                    name_types=name_types,
                    translation_count=len(translations),
                )
                for term in terms:
                    existing = merged.get(term)
                    merged[term] = _merge_jmnedict_name_records(existing, record)
                elem.clear()
            return merged
    except (ElementTree.ParseError, OSError):
        return {}


def load_jmdict_lexical_index(path: Path) -> dict[str, JmdictLexicalRecord]:
    return load_or_compute_path_json_value(
        path,
        namespace="japanese_learner_signals",
        key={"kind": "jmdict_lexical", "version": JMDICT_LEXICAL_INDEX_VERSION},
        compute=lambda: _load_jmdict_lexical_index_uncached(path),
        serialize=lambda value: {key: record.to_dict() for key, record in value.items()},
        deserialize=_deserialize_jmdict_lexical_index,
    )


def _load_jmdict_lexical_index_uncached(path: Path) -> dict[str, JmdictLexicalRecord]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        context = ElementTree.iterparse(path, events=("end",))
    except (ElementTree.ParseError, OSError):
        return {}
    merged: dict[str, JmdictLexicalRecord] = {}
    for _event, elem in context:
        if elem.tag != "entry":
            continue
        terms = _unique_sorted(
            (
                *(_node_text(keb) for keb in elem.findall("k_ele/keb")),
                *(_node_text(reb) for reb in elem.findall("r_ele/reb")),
            )
        )
        kanji_forms = _unique_sorted(_node_text(keb) for keb in elem.findall("k_ele/keb"))
        reading_forms = _unique_sorted(_node_text(reb) for reb in elem.findall("r_ele/reb"))
        senses = elem.findall("sense")
        record = _build_jmdict_lexical_record(
            pos_values=_collect_texts(elem.findall("sense/pos")),
            misc_values=_collect_texts(elem.findall("sense/misc")),
            field_values=_collect_texts(elem.findall("sense/field")),
            dial_values=_collect_texts(elem.findall("sense/dial")),
            source_language_values=_collect_jmdict_source_languages(elem.findall("sense/lsource")),
            kanji_info_values=_collect_texts(elem.findall("k_ele/ke_inf")),
            reading_info_values=_collect_texts(elem.findall("r_ele/re_inf")),
            gloss_values=_collect_jmdict_gloss_values(elem.findall("sense/gloss")),
            gloss_language_values=_collect_jmdict_gloss_languages(elem.findall("sense/gloss")),
            entry_count=1,
            kanji_forms=kanji_forms,
            reading_forms=reading_forms,
            form_values=terms,
            sense_count=len(senses),
            sense_info_count=_count_nonempty_nodes(elem.findall("sense/s_inf")),
            gloss_count=_count_nonempty_nodes(elem.findall("sense/gloss")),
            xref_count=_count_nonempty_nodes(elem.findall("sense/xref")),
            antonym_count=_count_nonempty_nodes(elem.findall("sense/ant")),
            sense_restriction_count=(
                _count_nonempty_nodes(elem.findall("sense/stagk"))
                + _count_nonempty_nodes(elem.findall("sense/stagr"))
            ),
            reading_restriction_count=_count_nonempty_nodes(elem.findall("r_ele/re_restr")),
            no_kanji_reading_count=len(elem.findall("r_ele/re_nokanji")),
        )
        for term in terms:
            existing = merged.get(term)
            merged[term] = _merge_jmdict_lexical_records(existing, record)
        elem.clear()
    return merged


def load_kanjidic2_character_index(path: Path) -> dict[str, Kanjidic2CharacterRecord]:
    return load_or_compute_path_json_value(
        path,
        namespace="japanese_learner_signals",
        key={"kind": "kanjidic2_characters", "version": KANJIDIC2_INDEX_VERSION},
        compute=lambda: _load_kanjidic2_character_index_uncached(path),
        serialize=lambda value: {key: record.to_dict() for key, record in value.items()},
        deserialize=_deserialize_kanjidic2_character_index,
    )


def _load_kanjidic2_character_index_uncached(
    path: Path,
) -> dict[str, Kanjidic2CharacterRecord]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        with _xml_text_stream(path) as source:
            context = ElementTree.iterparse(source, events=("end",))
            records: dict[str, Kanjidic2CharacterRecord] = {}
            for _event, elem in context:
                if elem.tag != "character":
                    continue
                literal = _node_text(elem.find("literal"))
                if literal:
                    misc = elem.find("misc")
                    on_readings, kun_readings, nanori_readings = _kanjidic2_japanese_readings(elem)
                    records[literal] = Kanjidic2CharacterRecord(
                        literal=literal,
                        grade=_safe_int(
                            _node_text(misc.find("grade") if misc is not None else None)
                        ),
                        stroke_count=_safe_int(
                            _node_text(misc.find("stroke_count") if misc is not None else None)
                        ),
                        freq=_safe_int(_node_text(misc.find("freq") if misc is not None else None)),
                        old_jlpt=_safe_int(
                            _node_text(misc.find("jlpt") if misc is not None else None)
                        ),
                        on_readings=on_readings,
                        kun_readings=kun_readings,
                        nanori_readings=nanori_readings,
                        meanings=_kanjidic2_meanings(elem),
                        rad_names=_collect_texts(elem.findall("misc/rad_name")),
                        radical_values=_kanjidic2_typed_values(
                            elem.findall("radical/rad_value"),
                            attr_name="rad_type",
                        ),
                        variant_types=_collect_attr_values(
                            elem.findall("misc/variant"),
                            attr_name="var_type",
                        ),
                        query_code_types=_collect_attr_values(
                            elem.findall("query_code/q_code"),
                            attr_name="qc_type",
                        ),
                        dictionary_reference_types=_collect_attr_values(
                            elem.findall("dic_number/dic_ref"),
                            attr_name="dr_type",
                        ),
                    )
                elem.clear()
            return records
    except (ElementTree.ParseError, OSError):
        return {}


def load_kanjivg_character_index(path: Path) -> dict[str, KanjivgCharacterRecord]:
    return load_or_compute_path_json_value(
        path,
        namespace="japanese_learner_signals",
        key={"kind": "kanjivg_characters", "version": KANJIVG_CHARACTER_INDEX_VERSION},
        compute=lambda: _load_kanjivg_character_index_uncached(path),
        serialize=lambda value: {key: record.to_dict() for key, record in value.items()},
        deserialize=_deserialize_kanjivg_character_index,
    )


def _load_kanjivg_character_index_uncached(path: Path) -> dict[str, KanjivgCharacterRecord]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        with _xml_text_stream(path) as source:
            context = ElementTree.iterparse(source, events=("end",))
            records: dict[str, KanjivgCharacterRecord] = {}
            for _event, elem in context:
                if _xml_local_name(elem.tag) != "kanji":
                    continue
                record = _build_kanjivg_character_record(elem)
                if record.literal:
                    records[record.literal] = record
                elem.clear()
            return records
    except (ElementTree.ParseError, OSError):
        return {}


def load_jlpt_vocabulary_index(
    path: Path,
    *,
    jmdict_path: Path | None = None,
) -> dict[str, JlptVocabularyRecord]:
    resolved_jmdict_path = _resolve_existing_path(jmdict_path) if jmdict_path else None
    return load_or_compute_path_json_value(
        path,
        namespace="japanese_learner_signals",
        key={
            "kind": "jlpt_vocabulary",
            "version": JLPT_VOCABULARY_INDEX_VERSION,
            "jmdict_path": resolved_jmdict_path,
            "jmdict_signature": _path_signature_for_cache_key(resolved_jmdict_path),
        },
        compute=lambda: _load_jlpt_vocabulary_index_uncached(
            path,
            jmdict_path=resolved_jmdict_path,
        ),
        serialize=lambda value: {key: record.to_dict() for key, record in value.items()},
        deserialize=_deserialize_jlpt_vocabulary_index,
    )


def _load_jlpt_vocabulary_index_uncached(
    path: Path,
    *,
    jmdict_path: Path | None = None,
) -> dict[str, JlptVocabularyRecord]:
    source_path = _resolve_existing_path(path)
    if source_path is None:
        return {}
    merged: dict[str, JlptVocabularyRecord] = {}
    candidate_files = _jlpt_vocabulary_candidate_files(source_path)
    source_rows: list[tuple[str, str, int]] = []
    for candidate in candidate_files:
        rows = (
            _iter_jlpt_vocabulary_json_rows(candidate)
            if candidate.suffix.lower() == ".json"
            else _iter_jlpt_vocabulary_csv_rows(candidate)
        )
        for surface, reading, level in rows:
            if level is None:
                continue
            normalized_surface = _normalize_jlpt_surface(surface)
            normalized_reading = _normalize_jlpt_reading(reading)
            if normalized_surface and normalized_reading:
                source_rows.append((normalized_surface, normalized_reading, int(level)))
            record = _build_jlpt_vocabulary_record(
                surfaces=(surface,),
                readings=(reading,),
                levels=(level,),
                source_count=1,
                entries=(_jlpt_vocabulary_entry_key(surface, reading, level),),
            )
            for term in _unique_sorted((normalized_surface, normalized_reading)):
                existing = merged.get(term)
                merged[term] = _merge_jlpt_vocabulary_records(existing, record)
    if source_rows and jmdict_path is not None and jmdict_path.is_file():
        _merge_jlpt_jmdict_normalized_entries(
            merged,
            source_rows=source_rows,
            jmdict_path=jmdict_path,
        )
    return merged


def _merge_jlpt_jmdict_normalized_entries(
    merged: dict[str, JlptVocabularyRecord],
    *,
    source_rows: Sequence[tuple[str, str, int]],
    jmdict_path: Path,
) -> None:
    pair_lookup, reading_lookup = _jmdict_same_reading_jlpt_normalization_lookup(jmdict_path)
    for source_surface, source_reading, level in source_rows:
        groups: list[tuple[tuple[str, str, bool], ...]] = []
        direct_group = pair_lookup.get((source_surface, source_reading))
        if direct_group:
            groups.append(direct_group)
        if source_surface == source_reading:
            reading_group = reading_lookup.get(source_reading)
            if reading_group and reading_group not in groups:
                groups.append(reading_group)
        for group in groups:
            for surface, reading, guarded in group:
                if reading != source_reading or surface == source_surface:
                    continue
                entry = _jlpt_vocabulary_entry_key(surface, reading, level)
                normalized_entries = () if guarded else (entry,)
                guarded_entries = (entry,) if guarded else ()
                record = _build_jlpt_vocabulary_record(
                    surfaces=(surface,),
                    readings=(reading,),
                    levels=(() if guarded else (level,)),
                    source_count=0,
                    normalized_entries=normalized_entries,
                    guarded_normalized_entries=guarded_entries,
                )
                for term in _unique_sorted((surface, reading)):
                    existing = merged.get(term)
                    merged[term] = _merge_jlpt_vocabulary_records(existing, record)


def _jmdict_same_reading_jlpt_normalization_lookup(
    path: Path,
) -> tuple[
    dict[tuple[str, str], tuple[tuple[str, str, bool], ...]],
    dict[str, tuple[tuple[str, str, bool], ...]],
]:
    pair_groups: dict[tuple[str, str], set[tuple[tuple[str, str, bool], ...]]] = {}
    reading_groups: dict[str, set[tuple[tuple[str, str, bool], ...]]] = {}
    try:
        with _xml_text_stream(path) as source:
            context = ElementTree.iterparse(source, events=("end",))
            for _event, elem in context:
                if elem.tag != "entry":
                    continue
                for group in _jmdict_same_reading_groups(elem):
                    if len(group) < 2:
                        continue
                    normalized_group = tuple(sorted(group))
                    readings = {reading for _surface, reading, _guarded in normalized_group}
                    for reading in readings:
                        reading_groups.setdefault(reading, set()).add(normalized_group)
                    for surface, reading, _guarded in normalized_group:
                        pair_groups.setdefault((surface, reading), set()).add(normalized_group)
                elem.clear()
    except (ElementTree.ParseError, OSError):
        return {}, {}
    unambiguous_pairs = {
        pair: next(iter(groups)) for pair, groups in pair_groups.items() if len(groups) == 1
    }
    unambiguous_readings = {
        reading: next(iter(groups))
        for reading, groups in reading_groups.items()
        if len(groups) == 1
    }
    return unambiguous_pairs, unambiguous_readings


def _jmdict_same_reading_groups(
    elem: ElementTree.Element,
) -> tuple[tuple[tuple[str, str, bool], ...], ...]:
    kanji_forms = [
        (
            _normalize_jlpt_surface(_node_text(k_ele.find("keb"))),
            bool(_collect_texts(k_ele.findall("ke_inf"))),
        )
        for k_ele in elem.findall("k_ele")
    ]
    kanji_forms = [(surface, guarded) for surface, guarded in kanji_forms if surface]
    groups: list[tuple[tuple[str, str, bool], ...]] = []
    for r_ele in elem.findall("r_ele"):
        reading = _normalize_jlpt_reading(_node_text(r_ele.find("reb")))
        if not reading:
            continue
        reading_guarded = bool(_collect_texts(r_ele.findall("re_inf")))
        restrictions = _unique_sorted(
            _normalize_jlpt_surface(_node_text(node)) for node in r_ele.findall("re_restr")
        )
        no_kanji = bool(r_ele.findall("re_nokanji"))
        if restrictions:
            surfaces = [
                (surface, guarded) for surface, guarded in kanji_forms if surface in restrictions
            ]
        elif kanji_forms and not no_kanji:
            surfaces = kanji_forms
        else:
            surfaces = [(reading, False)]
        group = tuple(
            (surface, reading, bool(surface_guarded or reading_guarded))
            for surface, surface_guarded in surfaces
            if surface
        )
        if group:
            groups.append(group)
    return tuple(groups)


def load_japanese_lesson_vocabulary_index(
    path: Path,
) -> dict[str, JapaneseLessonVocabularyRecord]:
    return load_or_compute_path_json_value(
        path,
        namespace="japanese_learner_signals",
        key={
            "kind": "japanese_lesson_vocabulary",
            "version": JAPANESE_LESSON_VOCABULARY_INDEX_VERSION,
        },
        compute=lambda: _load_japanese_lesson_vocabulary_index_uncached(path),
        serialize=lambda value: {key: record.to_dict() for key, record in value.items()},
        deserialize=_deserialize_japanese_lesson_vocabulary_index,
    )


def _load_japanese_lesson_vocabulary_index_uncached(
    path: Path,
) -> dict[str, JapaneseLessonVocabularyRecord]:
    source_path = _resolve_existing_path(path)
    if source_path is None:
        return {}
    merged: dict[str, JapaneseLessonVocabularyRecord] = {}
    for fallback_index, candidate in enumerate(
        _lesson_vocabulary_candidate_files(source_path), start=1
    ):
        lesson_index = _lesson_index_from_path(candidate, fallback=fallback_index)
        lesson_key = _lesson_key_from_path(candidate)
        try:
            text = candidate.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lesson_title = _lesson_title_from_html(text)
        for surface, reading, romanization, gloss in _iter_lesson_vocabulary_rows(text):
            record = _build_japanese_lesson_vocabulary_record(
                surfaces=(surface,),
                readings=(reading,),
                romanizations=(romanization,),
                glosses=(gloss,),
                lesson_indices=(lesson_index,),
                lesson_keys=(lesson_key,),
                lesson_titles=(lesson_title,),
                source_count=1,
            )
            for term in _unique_sorted((surface, reading)):
                existing = merged.get(term)
                merged[term] = _merge_japanese_lesson_vocabulary_records(existing, record)
    return merged


def build_japanese_learner_signal_bundle(
    *,
    lemma: object,
    reading: object | None = None,
    raw_pos: object | None = None,
    wtype: object | None = None,
    source_frequency_profile: Mapping[str, object] | None = None,
    jmdict_priority_index: Mapping[str, JmdictPriorityRecord] | None = None,
    jmdict_lexical_index: Mapping[str, JmdictLexicalRecord] | None = None,
    jmnedict_name_index: Mapping[str, JmnedictNameRecord] | None = None,
    kanjidic2_character_index: Mapping[str, Kanjidic2CharacterRecord] | None = None,
    kanjivg_character_index: Mapping[str, KanjivgCharacterRecord] | None = None,
    jlpt_vocabulary_index: Mapping[str, JlptVocabularyRecord] | None = None,
    lesson_vocabulary_index: Mapping[str, JapaneseLessonVocabularyRecord] | None = None,
) -> dict[str, object]:
    text = str(lemma or "").strip()
    if not text:
        return {}
    payload: dict[str, object] = {
        "version": JAPANESE_LEARNER_SIGNALS_VERSION,
        "surface": text,
    }
    sources: list[str] = []
    script_signal = _build_japanese_script_signal(text)
    if script_signal:
        payload["japanese_script"] = script_signal
        sources.append("japanese_script")
    jmdict_priority_record: JmdictPriorityRecord | None = None
    if jmdict_priority_index:
        jmdict_priority_record = jmdict_priority_index.get(text)
        if jmdict_priority_record is not None:
            priority_payload = jmdict_priority_record.to_dict()
            matched_pair = _jmdict_priority_matched_pair_payload(
                jmdict_priority_record,
                surface=text,
                reading=reading,
            )
            if matched_pair is not None:
                priority_payload["matched_pair"] = matched_pair
            payload["jmdict_priority"] = priority_payload
            sources.append("jmdict_priority")
    jmdict_lexical_record: JmdictLexicalRecord | None = None
    if jmdict_lexical_index:
        jmdict_lexical_record = jmdict_lexical_index.get(text)
        if jmdict_lexical_record is not None:
            payload["jmdict_lexical"] = jmdict_lexical_record.to_dict()
            sources.append("jmdict_lexical")
    if jlpt_vocabulary_index:
        jlpt_payload = _jlpt_vocabulary_match_payload(
            jlpt_vocabulary_index,
            surface=text,
            reading=reading,
        )
        if jlpt_payload is not None:
            payload["jlpt_vocabulary"] = jlpt_payload
            sources.append("jlpt_vocabulary")
    if lesson_vocabulary_index:
        record = lesson_vocabulary_index.get(text)
        if record is not None:
            payload["lesson_vocabulary"] = record.to_dict()
            sources.append("lesson_vocabulary")
    if jmnedict_name_index:
        record = jmnedict_name_index.get(text)
        if record is not None:
            payload["jmnedict_name"] = record.to_dict()
            sources.append("jmnedict_name")
    if kanjidic2_character_index and contains_kanji(text):
        kanji_payload = _build_kanjidic2_aggregate(
            text,
            kanjidic2_character_index=kanjidic2_character_index,
        )
        if kanji_payload:
            payload["kanjidic2"] = kanji_payload
            sources.append("kanjidic2")
    if kanjivg_character_index and contains_kanji(text):
        kanjivg_payload = _build_kanjivg_aggregate(
            text,
            kanjivg_character_index=kanjivg_character_index,
        )
        if kanjivg_payload:
            payload["kanjivg"] = kanjivg_payload
            sources.append("kanjivg")
    acronym_signal = build_japanese_acronym_signal(
        surface=text,
        reading=reading,
        raw_pos=raw_pos,
        wtype=wtype,
        jmdict_priority_record=jmdict_priority_record,
        jmdict_lexical_record=jmdict_lexical_record,
        jmnedict_name_record=(jmnedict_name_index.get(text) if jmnedict_name_index else None),
        source_frequency_profile=source_frequency_profile,
    )
    if acronym_signal:
        payload["ja_acronym"] = acronym_signal
        sources.append("ja_acronym")
    if not sources:
        return {}
    payload["sources"] = sources
    return payload


def _jmdict_priority_matched_pair_payload(
    record: JmdictPriorityRecord,
    *,
    surface: object,
    reading: object | None,
) -> dict[str, object] | None:
    surface_text = str(surface or "").strip()
    reading_text = str(reading or "").strip()
    if not surface_text or not reading_text:
        return None
    surface_key = _jmdict_pair_match_key(surface_text)
    reading_key = _jmdict_pair_match_key(reading_text)
    for pair_record in record.pair_records:
        if (
            _jmdict_pair_match_key(pair_record.surface) == surface_key
            and _jmdict_pair_match_key(pair_record.reading) == reading_key
        ):
            payload = pair_record.to_dict()
            payload["match_type"] = (
                "exact"
                if pair_record.surface == surface_text and pair_record.reading == reading_text
                else "kana_normalized_exact"
            )
            if pair_record.reading != reading_text:
                payload["requested_reading"] = reading_text
            return payload
    return {
        "surface": surface_text,
        "reading": reading_text,
        "match_type": "missing_reading",
        "surface_tags": [],
        "reading_tags": [],
        "entry_tags": list(record.entry_tags),
        "surface_info_values": [],
        "reading_info_values": [],
        "surface_reading_count": 0,
        "direct_priority_score": 0.0,
        "direct_priority_band": "none",
        "entry_priority_score": round(float(record.entry_priority_score), 6),
        "entry_priority_band": record.entry_priority_band,
        "safe_priority_score": 0.0,
        "safe_priority_band": "none",
        "safe_priority_kind": "missing_reading",
        "entry_priority_inherited_only": bool(record.entry_priority_score > 0.0),
        "priority_leak_risk": bool(record.entry_priority_score > 0.0),
    }


def _jmdict_pair_match_key(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).strip()
    return "".join(_katakana_char_to_hiragana(char) for char in normalized)


def _katakana_char_to_hiragana(char: str) -> str:
    codepoint = ord(char)
    if 0x30A1 <= codepoint <= 0x30F6:
        return chr(codepoint - 0x60)
    return char


def build_japanese_acronym_signal(
    *,
    surface: object,
    reading: object | None = None,
    raw_pos: object | None = None,
    wtype: object | None = None,
    jmdict_priority_record: JmdictPriorityRecord | None = None,
    jmdict_lexical_record: JmdictLexicalRecord | None = None,
    jmnedict_name_record: JmnedictNameRecord | None = None,
    source_frequency_profile: Mapping[str, object] | None = None,
) -> dict[str, object]:
    text = str(surface or "").strip()
    if not text:
        return {}
    normalized = unicodedata.normalize("NFKC", text).strip()
    ascii_identifier = _normalize_ascii_identifier(normalized)
    latin_count = sum(1 for char in normalized if _is_latin_letter(char))
    digit_count = sum(1 for char in normalized if char.isdigit())
    token_chars = [char for char in normalized if not char.isspace()]
    token_count = len(token_chars)
    japanese_count = sum(1 for char in token_chars if _is_japanese_char(char))
    fullwidth_source_surface = any(0xFF01 <= ord(char) <= 0xFF5E for char in text)
    latin_upper_count = sum(1 for char in normalized if "A" <= char <= "Z")
    latin_upper_ratio = latin_upper_count / latin_count if latin_count else 0.0
    latin_or_digit_ratio = (latin_count + digit_count) / token_count if token_count else 0.0
    allowed_acronym_chars = all(
        _is_latin_letter(char) or char.isdigit() or char in _ACRONYM_ALLOWED_SEPARATORS
        for char in token_chars
    )
    letters_only = "".join(char.upper() for char in normalized if _is_latin_letter(char))
    all_latin_surface = bool(
        latin_count >= 2
        and latin_or_digit_ratio >= 0.85
        and allowed_acronym_chars
        and not japanese_count
    )
    acronym_surface_confidence = 0.0
    if all_latin_surface and 2 <= latin_count <= 8 and latin_upper_ratio >= 0.8:
        acronym_surface_confidence = 1.0
    elif all_latin_surface and latin_count >= 2 and latin_upper_ratio >= 0.6:
        acronym_surface_confidence = 0.75
    elif all_latin_surface and latin_count >= 2:
        acronym_surface_confidence = 0.55
    mixed_code_confidence = (
        1.0
        if latin_count > 0 and japanese_count > 0
        else 0.65
        if digit_count > 0 and japanese_count > 0
        else 0.0
    )
    if acronym_surface_confidence < 0.5 and mixed_code_confidence < 0.5:
        return {}

    reading_text = str(reading or "").strip()
    spellout_confidence = _acronym_spellout_reading_confidence(
        letters_only,
        reading_text,
    )
    lexicalized_reading = bool(all_latin_surface and reading_text and spellout_confidence < 0.85)
    gloss_values = tuple(jmdict_lexical_record.gloss_values) if jmdict_lexical_record else ()
    exact_gloss_confidence = _exact_acronym_gloss_confidence(
        ascii_identifier,
        gloss_values,
    )
    expanded_gloss_confidence = _expanded_english_gloss_confidence(
        ascii_identifier,
        gloss_values,
    )
    japanese_specific_usage_confidence = _japanese_specific_acronym_usage_confidence(
        gloss_values=gloss_values,
        lexicalized_reading=lexicalized_reading,
        priority_score=(jmdict_priority_record.priority_score if jmdict_priority_record else None),
    )
    source_frequency_profile = source_frequency_profile or {}
    domain_concentration = _acronym_domain_concentration(source_frequency_profile)
    jmdict_field_values = tuple(jmdict_lexical_record.field_values) if jmdict_lexical_record else ()
    field_domain_confidence = (
        1.0
        if any(
            str(field or "").strip().lower() in _ACRONYM_DOMAIN_FIELDS
            for field in jmdict_field_values
        )
        else 0.0
    )
    proper_name_risk = _acronym_proper_name_risk(
        raw_pos=raw_pos,
        wtype=wtype,
        jmnedict_name_record=jmnedict_name_record,
    )
    real_usage_confidence = _acronym_real_usage_confidence(
        jmdict_priority_record=jmdict_priority_record,
        source_frequency_profile=source_frequency_profile,
    )
    recommended_class = _recommended_acronym_class(
        surface_confidence=acronym_surface_confidence,
        mixed_code_confidence=mixed_code_confidence,
        exact_gloss_confidence=exact_gloss_confidence,
        japanese_specific_usage_confidence=japanese_specific_usage_confidence,
        field_domain_confidence=field_domain_confidence,
        proper_name_risk=proper_name_risk,
    )
    state, suitability = _recommended_acronym_state(recommended_class)
    reasons = _acronym_reasons(
        fullwidth_source_surface=fullwidth_source_surface,
        all_latin_surface=all_latin_surface,
        mixed_code_confidence=mixed_code_confidence,
        spellout_confidence=spellout_confidence,
        lexicalized_reading=lexicalized_reading,
        exact_gloss_confidence=exact_gloss_confidence,
        expanded_gloss_confidence=expanded_gloss_confidence,
        japanese_specific_usage_confidence=japanese_specific_usage_confidence,
        field_domain_confidence=field_domain_confidence,
        domain_concentration=domain_concentration,
        proper_name_risk=proper_name_risk,
        real_usage_confidence=real_usage_confidence,
    )
    return {
        "acronym_signal_version": JA_ACRONYM_SIGNAL_VERSION,
        "normalized_ascii_surface": ascii_identifier,
        "surface_confidence": round(acronym_surface_confidence, 6),
        "mixed_code_confidence": round(mixed_code_confidence, 6),
        "all_latin_surface": all_latin_surface,
        "fullwidth_source_surface": fullwidth_source_surface,
        "latin_upper_ratio": round(latin_upper_ratio, 6),
        "latin_or_digit_ratio": round(latin_or_digit_ratio, 6),
        "reading_spellout_confidence": round(spellout_confidence, 6),
        "lexicalized_reading": lexicalized_reading,
        "identity_gloss_confidence": round(exact_gloss_confidence, 6),
        "english_initialism_expansion_confidence": round(expanded_gloss_confidence, 6),
        "expanded_gloss_confidence": round(expanded_gloss_confidence, 6),
        "japanese_specific_usage_confidence": round(
            japanese_specific_usage_confidence,
            6,
        ),
        "jmdict_field_values": list(jmdict_field_values),
        "field_domain_confidence": round(field_domain_confidence, 6),
        "domain_concentration": round(domain_concentration, 6),
        "proper_name_risk": round(proper_name_risk, 6),
        "real_usage_confidence": round(real_usage_confidence, 6),
        "recommended_acronym_class": recommended_class,
        "recommended_candidate_state": state,
        "recommended_admission_suitability": round(suitability, 6),
        "reasons": list(reasons),
    }


def _normalize_ascii_identifier(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).strip()
    return "".join(char.upper() for char in normalized if _is_latin_letter(char) or char.isdigit())


def _acronym_spellout_reading_confidence(letters: str, reading: str) -> float:
    normalized_letters = "".join(
        char.upper() for char in str(letters or "") if _is_latin_letter(char)
    )
    normalized_reading = _normalize_japanese_acronym_reading(reading)
    if not normalized_letters or not normalized_reading:
        return 0.0
    if len(normalized_letters) > 12:
        return 0.0
    positions = {0}
    for letter in normalized_letters:
        options = _ACRONYM_LETTER_READINGS.get(letter, ())
        if not options:
            return 0.0
        next_positions: set[int] = set()
        for position in positions:
            for option in options:
                if normalized_reading.startswith(option, position):
                    next_positions.add(position + len(option))
        if not next_positions:
            return 0.0
        positions = next_positions
    if len(normalized_reading) in positions:
        return 1.0
    return 0.65 if any(position >= len(normalized_reading) - 1 for position in positions) else 0.0


def _normalize_japanese_acronym_reading(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    chars: list[str] = []
    for char in unicodedata.normalize("NFKC", text):
        codepoint = ord(char)
        if 0x30A1 <= codepoint <= 0x30F6:
            chars.append(chr(codepoint - 0x60))
        elif char in {"・", ".", "．", "-", "‐", "‑", "‒", "–", "—", " ", "　"}:
            continue
        else:
            chars.append(char)
    return "".join(chars)


def _exact_acronym_gloss_confidence(
    ascii_identifier: str,
    gloss_values: Sequence[str],
) -> float:
    if not ascii_identifier:
        return 0.0
    for gloss in gloss_values:
        if _normalize_ascii_identifier(gloss) == ascii_identifier:
            return 1.0
    return 0.0


def _expanded_english_gloss_confidence(
    ascii_identifier: str,
    gloss_values: Sequence[str],
) -> float:
    if not ascii_identifier:
        return 0.0
    identifier = "".join(char for char in str(ascii_identifier or "").upper() if "A" <= char <= "Z")
    if len(identifier) < 2 or identifier != str(ascii_identifier or "").upper():
        return 0.0
    for gloss in gloss_values:
        text = " ".join(str(gloss or "").strip().lower().split())
        if not text or _normalize_ascii_identifier(text) == ascii_identifier:
            continue
        if _gloss_has_matching_initialism_expansion(identifier, text):
            return 1.0
    return 0.0


def _gloss_has_matching_initialism_expansion(identifier: str, gloss: str) -> bool:
    for clause in re.split(r"[;:(),/]", str(gloss or "")):
        tokens = [
            token.lower()
            for token in _ACRONYM_GLOSS_WORD_RE.findall(clause)
            if token.lower() not in _ACRONYM_GLOSS_INITIAL_STOPWORDS
        ]
        if len(tokens) < len(identifier):
            continue
        initials = "".join(token[0].upper() for token in tokens)
        if initials == identifier:
            return True
    return False


def _japanese_specific_acronym_usage_confidence(
    *,
    gloss_values: Sequence[str],
    lexicalized_reading: bool,
    priority_score: float | None,
) -> float:
    confidence = 0.45 if lexicalized_reading else 0.0
    lowered_glosses = tuple(
        " ".join(str(gloss or "").strip().lower().split()) for gloss in gloss_values
    )
    if any(cue in gloss for gloss in lowered_glosses for cue in _ACRONYM_JAPANESE_USAGE_GLOSS_CUES):
        confidence = max(confidence, 1.0)
    elif any(" " in gloss for gloss in lowered_glosses):
        confidence = max(confidence, 0.35)
    if priority_score is not None and priority_score >= 0.75 and 0.0 < confidence < 0.7:
        confidence = max(confidence, 0.65)
    return _clamp_score(confidence)


def _acronym_domain_concentration(profile: Mapping[str, object]) -> float:
    domain_count = _safe_float(profile.get("domain_rank_known_count"))
    domain_spread = _safe_float(profile.get("domain_rank_spread"))
    if domain_count is None or domain_spread is None:
        return 0.0
    if domain_count < 2.0 or domain_spread <= 0.0:
        return 0.0
    coverage_score = min(max(domain_count, 0.0) / 12.0, 1.0)
    spread_score = min(1.0, _log_scale(domain_spread, 100000.0))
    return _clamp_score(coverage_score * spread_score)


def _acronym_real_usage_confidence(
    *,
    jmdict_priority_record: JmdictPriorityRecord | None,
    source_frequency_profile: Mapping[str, object],
) -> float:
    values: list[float] = []
    if jmdict_priority_record is not None:
        values.append(float(jmdict_priority_record.priority_score))
    for key in ("core_rank_min", "rank_min"):
        rank = _safe_float(source_frequency_profile.get(key))
        if rank is not None and rank > 0.0:
            values.append(max(0.0, 1.0 - _log_scale(rank, 50000.0)))
    for key in ("core_pmw_max", "pmw_max"):
        pmw = _safe_float(source_frequency_profile.get(key))
        if pmw is not None and pmw > 0.0:
            values.append(min(1.0, _log_scale(pmw, 100.0)))
    return _clamp_score(max(values) if values else 0.0)


def _acronym_proper_name_risk(
    *,
    raw_pos: object | None,
    wtype: object | None,
    jmnedict_name_record: JmnedictNameRecord | None,
) -> float:
    values: list[float] = []
    raw_pos_text = str(raw_pos or "").strip()
    wtype_text = str(wtype or "").strip()
    if "固有名詞" in raw_pos_text:
        values.append(0.9)
    if wtype_text == "固":
        values.append(0.9)
    if jmnedict_name_record is not None:
        values.append(float(jmnedict_name_record.name_signal_score))
    return _clamp_score(max(values) if values else 0.0)


def _recommended_acronym_class(
    *,
    surface_confidence: float,
    mixed_code_confidence: float,
    exact_gloss_confidence: float,
    japanese_specific_usage_confidence: float,
    field_domain_confidence: float,
    proper_name_risk: float,
) -> str:
    if mixed_code_confidence >= 0.5 and surface_confidence < 0.5:
        return "mixed_code_term"
    if proper_name_risk >= 0.7:
        return "proper_name_acronym"
    if japanese_specific_usage_confidence >= 0.7:
        return "japanese_specific_acronym"
    if field_domain_confidence >= 0.8:
        return "domain_acronym"
    if exact_gloss_confidence >= 0.8:
        return "shared_exact_acronym"
    if surface_confidence >= 0.5:
        return "unknown_acronym_like"
    return "not_acronym"


def _recommended_acronym_state(acronym_class: str) -> tuple[str, float]:
    if acronym_class == "shared_exact_acronym":
        return "suppressed_default", 0.0
    if acronym_class == "japanese_specific_acronym":
        return "normal_vocab", 0.70
    if acronym_class == "domain_acronym":
        return "topic_only", 0.25
    if acronym_class == "proper_name_acronym":
        return "deprioritized_vocab", 0.25
    if acronym_class == "mixed_code_term":
        return "deprioritized_vocab", 0.35
    if acronym_class == "unknown_acronym_like":
        return "deprioritized_vocab", 0.35
    return "normal_vocab", 1.0


def _acronym_reasons(
    *,
    fullwidth_source_surface: bool,
    all_latin_surface: bool,
    mixed_code_confidence: float,
    spellout_confidence: float,
    lexicalized_reading: bool,
    exact_gloss_confidence: float,
    expanded_gloss_confidence: float,
    japanese_specific_usage_confidence: float,
    field_domain_confidence: float,
    domain_concentration: float,
    proper_name_risk: float,
    real_usage_confidence: float,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if fullwidth_source_surface:
        reasons.append("fullwidth_latin_surface")
    if all_latin_surface:
        reasons.append("all_latin_surface")
    if mixed_code_confidence >= 0.5:
        reasons.append("mixed_code_surface")
    if spellout_confidence >= 0.85:
        reasons.append("letter_name_reading")
    if lexicalized_reading:
        reasons.append("lexicalized_acronym_reading")
    if exact_gloss_confidence >= 0.8:
        reasons.append("exact_acronym_gloss")
    if expanded_gloss_confidence >= 0.8:
        reasons.append("expanded_english_gloss")
    if japanese_specific_usage_confidence >= 0.7:
        reasons.append("japanese_specific_usage")
    if field_domain_confidence >= 0.8:
        reasons.append("jmdict_domain_field")
    if domain_concentration >= 0.55:
        reasons.append("bccwj_domain_concentration")
    if proper_name_risk >= 0.7:
        reasons.append("proper_name_signal")
    if real_usage_confidence >= 0.7:
        reasons.append("real_usage_signal")
    return tuple(reasons)


def _log_scale(value: float, maximum: float) -> float:
    if maximum <= 0.0:
        return 0.0
    return min(1.0, math.log1p(max(0.0, float(value))) / math.log1p(maximum))


def _safe_float(value: object) -> float | None:
    try:
        text = str(value or "").strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _is_japanese_char(char: str) -> bool:
    return (
        _is_hiragana(char)
        or _is_katakana(char)
        or contains_kanji(char)
        or "\u3400" <= char <= "\u4dbf"
    )


def _build_jmnedict_name_record(
    *,
    surfaces: Iterable[str],
    readings: Iterable[str],
    name_types: Iterable[str],
    translation_count: int,
) -> JmnedictNameRecord:
    normalized_name_types = _unique_sorted(name_types)
    groups = _unique_sorted(_jmnedict_name_type_group(value) for value in normalized_name_types)
    return JmnedictNameRecord(
        surfaces=_unique_sorted(surfaces),
        readings=_unique_sorted(readings),
        name_types=normalized_name_types,
        name_type_groups=groups,
        translation_count=max(0, int(translation_count)),
        name_signal_score=_jmnedict_name_signal_score(groups),
    )


def _merge_jmnedict_name_records(
    existing: JmnedictNameRecord | None,
    new_record: JmnedictNameRecord,
) -> JmnedictNameRecord:
    if existing is None:
        return new_record
    return _build_jmnedict_name_record(
        surfaces=(*existing.surfaces, *new_record.surfaces),
        readings=(*existing.readings, *new_record.readings),
        name_types=(*existing.name_types, *new_record.name_types),
        translation_count=max(existing.translation_count, new_record.translation_count),
    )


def _build_jlpt_vocabulary_record(
    *,
    surfaces: Iterable[str],
    readings: Iterable[str],
    levels: Iterable[int],
    source_count: int,
    entries: Iterable[str] = (),
    normalized_entries: Iterable[str] = (),
    guarded_normalized_entries: Iterable[str] = (),
) -> JlptVocabularyRecord:
    return JlptVocabularyRecord(
        surfaces=_unique_sorted(surfaces),
        readings=_unique_sorted(readings),
        levels=tuple(sorted({int(level) for level in levels if 1 <= int(level) <= 5})),
        source_count=max(0, int(source_count)),
        entries=tuple(sorted({str(entry) for entry in entries if str(entry)})),
        normalized_entries=tuple(
            sorted({str(entry) for entry in normalized_entries if str(entry)})
        ),
        guarded_normalized_entries=tuple(
            sorted({str(entry) for entry in guarded_normalized_entries if str(entry)})
        ),
    )


def _merge_jlpt_vocabulary_records(
    existing: JlptVocabularyRecord | None,
    new_record: JlptVocabularyRecord,
) -> JlptVocabularyRecord:
    if existing is None:
        return new_record
    return _build_jlpt_vocabulary_record(
        surfaces=(*existing.surfaces, *new_record.surfaces),
        readings=(*existing.readings, *new_record.readings),
        levels=(*existing.levels, *new_record.levels),
        source_count=existing.source_count + new_record.source_count,
        entries=(*existing.entries, *new_record.entries),
        normalized_entries=(*existing.normalized_entries, *new_record.normalized_entries),
        guarded_normalized_entries=(
            *existing.guarded_normalized_entries,
            *new_record.guarded_normalized_entries,
        ),
    )


def _jlpt_vocabulary_match_payload(
    index: Mapping[str, JlptVocabularyRecord],
    *,
    surface: object,
    reading: object | None,
) -> dict[str, object] | None:
    surface_key = _normalize_jlpt_surface(surface)
    reading_key = _normalize_jlpt_reading(reading)
    surface_record = index.get(surface_key) if surface_key else None
    reading_record = index.get(reading_key) if reading_key else None
    if surface_record is None:
        return None
    record = surface_record
    exact_levels = _jlpt_exact_levels(
        (surface_record, reading_record),
        surface=surface_key,
        reading=reading_key,
    )
    normalized_exact_levels = _jlpt_normalized_exact_levels(
        (surface_record, reading_record),
        surface=surface_key,
        reading=reading_key,
    )
    guarded_normalized_exact_levels = _jlpt_guarded_normalized_exact_levels(
        (surface_record, reading_record),
        surface=surface_key,
        reading=reading_key,
    )
    effective_exact_levels = tuple(sorted({*exact_levels, *normalized_exact_levels}))
    exact_easiest = max(exact_levels) if exact_levels else None
    exact_hardest = min(exact_levels) if exact_levels else None
    normalized_exact_easiest = max(normalized_exact_levels) if normalized_exact_levels else None
    normalized_exact_hardest = min(normalized_exact_levels) if normalized_exact_levels else None
    guarded_normalized_exact_easiest = (
        max(guarded_normalized_exact_levels) if guarded_normalized_exact_levels else None
    )
    guarded_normalized_exact_hardest = (
        min(guarded_normalized_exact_levels) if guarded_normalized_exact_levels else None
    )
    effective_exact_easiest = max(effective_exact_levels) if effective_exact_levels else None
    effective_exact_hardest = min(effective_exact_levels) if effective_exact_levels else None
    surface_match = surface_record is not None
    reading_match = (
        reading_record is not None
        or bool(exact_levels)
        or bool(normalized_exact_levels)
        or bool(guarded_normalized_exact_levels)
    )
    exact_match = bool(exact_levels)
    normalized_exact_match = bool(normalized_exact_levels)
    guarded_normalized_exact_match = bool(guarded_normalized_exact_levels)
    effective_exact_match = bool(effective_exact_levels)
    payload = record.to_dict()
    payload.update(
        {
            "match_type": (
                "exact"
                if exact_match
                else "normalized_exact"
                if normalized_exact_match
                else "guarded_normalized_exact"
                if guarded_normalized_exact_match
                else "surface"
                if surface_match
                else "reading"
            ),
            "exact_match": exact_match,
            "normalized_exact_match": normalized_exact_match,
            "guarded_normalized_exact_match": guarded_normalized_exact_match,
            "effective_exact_match": effective_exact_match,
            "surface_match": surface_match,
            "reading_match": reading_match,
            "exact_levels": list(exact_levels),
            "normalized_exact_levels": list(normalized_exact_levels),
            "guarded_normalized_exact_levels": list(guarded_normalized_exact_levels),
            "effective_exact_levels": list(effective_exact_levels),
            "exact_easiest_level": exact_easiest,
            "exact_hardest_level": exact_hardest,
            "normalized_exact_easiest_level": normalized_exact_easiest,
            "normalized_exact_hardest_level": normalized_exact_hardest,
            "guarded_normalized_exact_easiest_level": guarded_normalized_exact_easiest,
            "guarded_normalized_exact_hardest_level": guarded_normalized_exact_hardest,
            "effective_exact_easiest_level": effective_exact_easiest,
            "effective_exact_hardest_level": effective_exact_hardest,
            "exact_difficulty_score": (
                _jlpt_vocab_difficulty_score(exact_easiest) if exact_easiest is not None else None
            ),
            "exact_beginner_core_score": (
                _jlpt_vocab_beginner_core_score(exact_easiest)
                if exact_easiest is not None
                else None
            ),
            "normalized_exact_difficulty_score": (
                _jlpt_vocab_difficulty_score(normalized_exact_easiest)
                if normalized_exact_easiest is not None
                else None
            ),
            "normalized_exact_beginner_core_score": (
                _jlpt_vocab_beginner_core_score(normalized_exact_easiest)
                if normalized_exact_easiest is not None
                else None
            ),
            "guarded_normalized_exact_difficulty_score": (
                _jlpt_vocab_difficulty_score(guarded_normalized_exact_easiest)
                if guarded_normalized_exact_easiest is not None
                else None
            ),
            "guarded_normalized_exact_beginner_core_score": (
                _jlpt_vocab_beginner_core_score(guarded_normalized_exact_easiest)
                if guarded_normalized_exact_easiest is not None
                else None
            ),
            "effective_exact_difficulty_score": (
                _jlpt_vocab_difficulty_score(effective_exact_easiest)
                if effective_exact_easiest is not None
                else None
            ),
            "effective_exact_beginner_core_score": (
                _jlpt_vocab_beginner_core_score(effective_exact_easiest)
                if effective_exact_easiest is not None
                else None
            ),
        }
    )
    return payload


def _jlpt_exact_levels(
    records: Iterable[JlptVocabularyRecord | None],
    *,
    surface: str,
    reading: str,
) -> tuple[int, ...]:
    return _jlpt_entry_levels(
        records,
        surface=surface,
        reading=reading,
        entry_attr="entries",
    )


def _jlpt_normalized_exact_levels(
    records: Iterable[JlptVocabularyRecord | None],
    *,
    surface: str,
    reading: str,
) -> tuple[int, ...]:
    return _jlpt_entry_levels(
        records,
        surface=surface,
        reading=reading,
        entry_attr="normalized_entries",
    )


def _jlpt_guarded_normalized_exact_levels(
    records: Iterable[JlptVocabularyRecord | None],
    *,
    surface: str,
    reading: str,
) -> tuple[int, ...]:
    return _jlpt_entry_levels(
        records,
        surface=surface,
        reading=reading,
        entry_attr="guarded_normalized_entries",
    )


def _jlpt_entry_levels(
    records: Iterable[JlptVocabularyRecord | None],
    *,
    surface: str,
    reading: str,
    entry_attr: str,
) -> tuple[int, ...]:
    if not surface or not reading:
        return ()
    levels: set[int] = set()
    for record in records:
        if record is None:
            continue
        for entry in getattr(record, entry_attr, ()):
            entry_surface, entry_reading, level = _parse_jlpt_vocabulary_entry_key(entry)
            if entry_surface == surface and entry_reading == reading and level is not None:
                levels.add(level)
    return tuple(sorted(levels))


def _jlpt_vocabulary_entry_key(surface: object, reading: object, level: object) -> str:
    parsed_level = _safe_int(level)
    if parsed_level is None:
        parsed_level = 0
    return "\t".join(
        (
            _normalize_jlpt_surface(surface),
            _normalize_jlpt_reading(reading),
            str(parsed_level),
        )
    )


def _parse_jlpt_vocabulary_entry_key(entry: object) -> tuple[str, str, int | None]:
    parts = str(entry or "").split("\t")
    if len(parts) != 3:
        return "", "", None
    return parts[0], parts[1], _safe_int(parts[2])


def _normalize_jlpt_surface(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def _normalize_jlpt_reading(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).strip()
    chars: list[str] = []
    for char in normalized:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            chars.append(chr(code - 0x60))
        else:
            chars.append(char)
    return "".join(chars)


def _build_japanese_lesson_vocabulary_record(
    *,
    surfaces: Iterable[str],
    readings: Iterable[str],
    romanizations: Iterable[str],
    glosses: Iterable[str],
    lesson_indices: Iterable[int],
    lesson_keys: Iterable[str],
    lesson_titles: Iterable[str],
    source_count: int,
) -> JapaneseLessonVocabularyRecord:
    return JapaneseLessonVocabularyRecord(
        surfaces=_unique_sorted(surfaces),
        readings=_unique_sorted(readings),
        romanizations=_unique_sorted(romanizations),
        glosses=_unique_sorted(glosses),
        lesson_indices=tuple(sorted({int(index) for index in lesson_indices if int(index) > 0})),
        lesson_keys=_unique_sorted(lesson_keys),
        lesson_titles=_unique_sorted(lesson_titles),
        source_count=max(0, int(source_count)),
    )


def _merge_japanese_lesson_vocabulary_records(
    existing: JapaneseLessonVocabularyRecord | None,
    new_record: JapaneseLessonVocabularyRecord,
) -> JapaneseLessonVocabularyRecord:
    if existing is None:
        return new_record
    return _build_japanese_lesson_vocabulary_record(
        surfaces=(*existing.surfaces, *new_record.surfaces),
        readings=(*existing.readings, *new_record.readings),
        romanizations=(*existing.romanizations, *new_record.romanizations),
        glosses=(*existing.glosses, *new_record.glosses),
        lesson_indices=(*existing.lesson_indices, *new_record.lesson_indices),
        lesson_keys=(*existing.lesson_keys, *new_record.lesson_keys),
        lesson_titles=(*existing.lesson_titles, *new_record.lesson_titles),
        source_count=existing.source_count + new_record.source_count,
    )


def _jlpt_vocab_difficulty_score(level: int | None) -> float:
    if level is None:
        return 0.0
    return {
        5: 0.08,
        4: 0.22,
        3: 0.42,
        2: 0.65,
        1: 0.85,
    }.get(int(level), 0.0)


def _jlpt_vocab_beginner_core_score(level: int | None) -> float:
    if level is None:
        return 0.0
    return {
        5: 1.0,
        4: 0.75,
        3: 0.35,
        2: 0.10,
        1: 0.0,
    }.get(int(level), 0.0)


def _lesson_vocab_difficulty_score(lesson_index: int | None) -> float:
    if lesson_index is None:
        return 0.0
    normalized = min(max(int(lesson_index) - 1, 0) / 40.0, 1.0)
    return round(0.02 + (normalized * 0.38), 6)


def _lesson_vocab_beginner_core_score(lesson_index: int | None) -> float:
    if lesson_index is None:
        return 0.0
    normalized = min(max(int(lesson_index) - 1, 0) / 40.0, 1.0)
    return round(1.0 - normalized, 6)


def _build_japanese_script_signal(text: str) -> dict[str, object]:
    chars = [char for char in str(text or "").strip() if not char.isspace()]
    if not chars:
        return {}
    hiragana_count = sum(1 for char in chars if _is_hiragana(char))
    katakana_count = sum(1 for char in chars if _is_katakana(char))
    kana_count = hiragana_count + katakana_count
    kanji_count = sum(1 for char in chars if contains_kanji(char))
    digit_count = sum(1 for char in chars if char.isdigit())
    latin_count = sum(1 for char in chars if _is_latin_letter(char))
    other_count = max(0, len(chars) - kana_count - kanji_count - digit_count - latin_count)
    script_classes = _unique_sorted(
        (
            "kanji" if kanji_count else "",
            "hiragana" if hiragana_count else "",
            "katakana" if katakana_count else "",
            "digit" if digit_count else "",
            "latin" if latin_count else "",
            "other" if other_count else "",
        )
    )
    return {
        "char_count": len(chars),
        "kanji_count": kanji_count,
        "kana_count": kana_count,
        "hiragana_count": hiragana_count,
        "katakana_count": katakana_count,
        "digit_count": digit_count,
        "latin_count": latin_count,
        "other_count": other_count,
        "script_classes": list(script_classes),
        "script_shape": _japanese_script_shape(script_classes),
        "kanji_ratio": round(kanji_count / len(chars), 6),
        "script_complexity_score": _japanese_script_complexity_score(
            char_count=len(chars),
            kanji_count=kanji_count,
            katakana_count=katakana_count,
            class_count=len(script_classes),
            non_japanese_count=digit_count + latin_count + other_count,
        ),
    }


def _japanese_script_shape(script_classes: Iterable[str]) -> str:
    class_set = frozenset(str(value or "").strip() for value in script_classes if value)
    if not class_set:
        return "empty"
    if class_set == {"kanji"}:
        return "kanji_only"
    if class_set <= {"hiragana", "katakana"}:
        return "kana_only"
    if class_set <= {"kanji", "hiragana", "katakana"}:
        return "mixed_japanese"
    if class_set & {"kanji", "hiragana", "katakana"}:
        return "mixed_japanese_other"
    return "non_japanese"


def _japanese_script_complexity_score(
    *,
    char_count: int,
    kanji_count: int,
    katakana_count: int,
    class_count: int,
    non_japanese_count: int,
) -> float:
    char_score = min(max(0, int(char_count)) / 8.0, 1.0) * 0.25
    kanji_score = min(max(0, int(kanji_count)) / 4.0, 1.0) * 0.35
    mixed_score = 0.20 if int(class_count) > 1 else 0.0
    katakana_score = 0.10 if int(katakana_count) > 0 else 0.0
    non_japanese_score = 0.10 if int(non_japanese_count) > 0 else 0.0
    return round(char_score + kanji_score + mixed_score + katakana_score + non_japanese_score, 6)


def _is_hiragana(char: str) -> bool:
    return "\u3040" <= char <= "\u309f"


def _is_katakana(char: str) -> bool:
    return "\u30a0" <= char <= "\u30ff" or "\uff66" <= char <= "\uff9f"


def _is_latin_letter(char: str) -> bool:
    return ("a" <= char <= "z") or ("A" <= char <= "Z")


def _build_jmdict_lexical_record(
    *,
    pos_values: Iterable[str],
    misc_values: Iterable[str],
    field_values: Iterable[str],
    dial_values: Iterable[str],
    source_language_values: Iterable[str],
    kanji_info_values: Iterable[str],
    reading_info_values: Iterable[str],
    gloss_values: Iterable[str],
    gloss_language_values: Iterable[str],
    entry_count: int,
    sense_count: int,
    sense_info_count: int,
    gloss_count: int,
    xref_count: int,
    antonym_count: int,
    sense_restriction_count: int,
    reading_restriction_count: int,
    no_kanji_reading_count: int,
    kanji_forms: Iterable[str] = (),
    reading_forms: Iterable[str] = (),
    form_values: Iterable[str] = (),
) -> JmdictLexicalRecord:
    normalized_pos = _unique_sorted(pos_values)
    normalized_misc = _unique_sorted(misc_values)
    normalized_field = _unique_sorted(field_values)
    normalized_dial = _unique_sorted(dial_values)
    normalized_source_languages = _unique_sorted(source_language_values)
    normalized_kanji_info = _unique_sorted(kanji_info_values)
    normalized_reading_info = _unique_sorted(reading_info_values)
    normalized_gloss_values = _unique_sorted(gloss_values)
    normalized_gloss_languages = _unique_sorted(gloss_language_values)
    normalized_kanji_forms = _unique_sorted(kanji_forms)
    normalized_reading_forms = _unique_sorted(reading_forms)
    normalized_form_values = _unique_sorted(form_values)
    groups = _unique_sorted(
        (
            *(_jmdict_pos_class_group(value) for value in normalized_pos),
            *(_jmdict_misc_class_group(value) for value in normalized_misc),
            *(_jmdict_dialect_class_group(value) for value in normalized_dial),
            *(_jmdict_source_language_class_group(value) for value in normalized_source_languages),
            *(_jmdict_kanji_info_class_group(value) for value in normalized_kanji_info),
            *(_jmdict_reading_info_class_group(value) for value in normalized_reading_info),
            "sense_info_marked" if int(sense_info_count) > 0 else "",
            "sense_restricted" if int(sense_restriction_count) > 0 else "",
            "reading_restricted" if int(reading_restriction_count) > 0 else "",
            "no_kanji_reading" if int(no_kanji_reading_count) > 0 else "",
            "cross_reference" if int(xref_count) + int(antonym_count) > 0 else "",
            "polysemous_entry" if int(sense_count) >= 4 else "",
        )
    )
    return JmdictLexicalRecord(
        pos_values=normalized_pos,
        misc_values=normalized_misc,
        field_values=normalized_field,
        dial_values=normalized_dial,
        source_language_values=normalized_source_languages,
        kanji_info_values=normalized_kanji_info,
        reading_info_values=normalized_reading_info,
        gloss_values=normalized_gloss_values,
        gloss_language_values=normalized_gloss_languages,
        lexical_class_groups=groups,
        kanji_forms=normalized_kanji_forms,
        reading_forms=normalized_reading_forms,
        form_values=normalized_form_values,
        entry_count=max(0, int(entry_count)),
        kanji_form_count=len(normalized_kanji_forms),
        reading_form_count=len(normalized_reading_forms),
        form_count=len(normalized_form_values),
        sense_count=max(0, int(sense_count)),
        sense_info_count=max(0, int(sense_info_count)),
        gloss_count=max(0, int(gloss_count)),
        xref_count=max(0, int(xref_count)),
        antonym_count=max(0, int(antonym_count)),
        sense_restriction_count=max(0, int(sense_restriction_count)),
        reading_restriction_count=max(0, int(reading_restriction_count)),
        no_kanji_reading_count=max(0, int(no_kanji_reading_count)),
        non_vocab_signal_score=_jmdict_non_vocab_signal_score(groups),
    )


def _merge_jmdict_lexical_records(
    existing: JmdictLexicalRecord | None,
    new_record: JmdictLexicalRecord,
) -> JmdictLexicalRecord:
    if existing is None:
        return new_record
    return _build_jmdict_lexical_record(
        pos_values=(*existing.pos_values, *new_record.pos_values),
        misc_values=(*existing.misc_values, *new_record.misc_values),
        field_values=(*existing.field_values, *new_record.field_values),
        dial_values=(*existing.dial_values, *new_record.dial_values),
        source_language_values=(
            *existing.source_language_values,
            *new_record.source_language_values,
        ),
        kanji_info_values=(*existing.kanji_info_values, *new_record.kanji_info_values),
        reading_info_values=(
            *existing.reading_info_values,
            *new_record.reading_info_values,
        ),
        gloss_values=(*existing.gloss_values, *new_record.gloss_values),
        gloss_language_values=(
            *existing.gloss_language_values,
            *new_record.gloss_language_values,
        ),
        entry_count=existing.entry_count + new_record.entry_count,
        kanji_forms=(*existing.kanji_forms, *new_record.kanji_forms),
        reading_forms=(*existing.reading_forms, *new_record.reading_forms),
        form_values=(*existing.form_values, *new_record.form_values),
        sense_count=existing.sense_count + new_record.sense_count,
        sense_info_count=existing.sense_info_count + new_record.sense_info_count,
        gloss_count=existing.gloss_count + new_record.gloss_count,
        xref_count=existing.xref_count + new_record.xref_count,
        antonym_count=existing.antonym_count + new_record.antonym_count,
        sense_restriction_count=(
            existing.sense_restriction_count + new_record.sense_restriction_count
        ),
        reading_restriction_count=(
            existing.reading_restriction_count + new_record.reading_restriction_count
        ),
        no_kanji_reading_count=(
            existing.no_kanji_reading_count + new_record.no_kanji_reading_count
        ),
    )


def _jmdict_pos_class_group(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if text == "numeric":
        return "numeric"
    if "particle" in text or "auxiliary verb" in text:
        return "particle_or_auxiliary"
    if "suffix" in text or "prefix" in text or text == "counter":
        return "affix_or_counter"
    if "proper" in text:
        return "proper_noun"
    if "pronoun" in text or "interjection" in text:
        return "function_or_discourse_word"
    return "ordinary_lexeme"


def _jmdict_misc_class_group(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if any(marker in text for marker in ("archaic", "obsolete", "rare", "dated")):
        return "marked_usage"
    if "usually written using kana alone" in text:
        return "kana_preferred"
    if any(marker in text for marker in ("honorific", "polite", "familiar")):
        return "register_marked"
    return "misc_marked"


def _jmdict_dialect_class_group(value: object) -> str:
    text = str(value or "").strip()
    return "dialect_marked" if text else ""


def _jmdict_source_language_class_group(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if text.startswith("text:"):
        return "source_text_present"
    if text.startswith("type:"):
        return "source_type_marked"
    if text == "wasei":
        return "wasei_source"
    if text in {"jpn", "japanese"}:
        return "native_source"
    if text in {"chi", "chn", "chinese"}:
        return "sinitic_source"
    return "loanword_source"


def _jmdict_kanji_info_class_group(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if "search-only" in text:
        return "search_only_form"
    if any(
        marker in text
        for marker in (
            "ateji",
            "irregular kanji",
            "irregular kana",
            "out-dated kanji",
            "rarely used kanji",
        )
    ):
        return "kanji_form_marked"
    return "kanji_form_info"


def _jmdict_reading_info_class_group(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if "search-only" in text:
        return "search_only_form"
    if any(
        marker in text
        for marker in (
            "gikun",
            "irregular",
            "out-dated",
            "obsolete",
            "rarely used kana",
        )
    ):
        return "reading_form_marked"
    return "reading_form_info"


def _jmdict_non_vocab_signal_score(groups: Iterable[str]) -> float:
    group_set = frozenset(str(value or "").strip() for value in groups if str(value or "").strip())
    if "particle_or_auxiliary" in group_set:
        return 1.0
    if "numeric" in group_set:
        return 0.9
    if "affix_or_counter" in group_set:
        return 0.85
    if "function_or_discourse_word" in group_set:
        return 0.65
    if "proper_noun" in group_set:
        return 0.45
    if "marked_usage" in group_set:
        return 0.35
    return 0.0


def _jmnedict_name_type_group(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {
        "female given name or forename",
        "given name or forename, gender not specified",
        "male given name or forename",
        "family or surname",
        "full name of a particular person",
    }:
        return "person_name"
    if text in {"place name", "railway station"}:
        return "place_name"
    if text in {"company name", "group", "organization name", "product name", "service"}:
        return "organization_or_product_name"
    if text in {"character", "fiction", "work of art, literature, music, etc. name"}:
        return "creative_work_or_character_name"
    if text in {"creature", "deity", "legend", "mythology", "religion", "ship name"}:
        return "mythic_or_special_name"
    if text:
        return "other_name"
    return "unknown_name"


def _jmnedict_name_signal_score(groups: Iterable[str]) -> float:
    group_set = frozenset(str(value or "").strip() for value in groups if str(value or "").strip())
    if "person_name" in group_set:
        return 1.0
    if "organization_or_product_name" in group_set:
        return 0.85
    if "place_name" in group_set:
        return 0.75
    if "creative_work_or_character_name" in group_set:
        return 0.70
    if "mythic_or_special_name" in group_set:
        return 0.65
    if group_set:
        return 0.60
    return 0.0


def _build_kanjidic2_aggregate(
    text: str,
    *,
    kanjidic2_character_index: Mapping[str, Kanjidic2CharacterRecord],
) -> dict[str, object]:
    kanji_chars = [char for char in text if contains_kanji(char)]
    if not kanji_chars:
        return {}
    records = [kanjidic2_character_index.get(char) for char in kanji_chars]
    known_records = [record for record in records if record is not None]
    grades = [record.grade for record in known_records if record.grade is not None]
    strokes = [record.stroke_count for record in known_records if record.stroke_count is not None]
    freqs = [record.freq for record in known_records if record.freq is not None]
    old_jlpt_levels = [record.old_jlpt for record in known_records if record.old_jlpt is not None]
    on_readings = _unique_sorted(
        reading for record in known_records for reading in record.on_readings
    )
    kun_readings = _unique_sorted(
        reading for record in known_records for reading in record.kun_readings
    )
    nanori_readings = _unique_sorted(
        reading for record in known_records for reading in record.nanori_readings
    )
    meanings = _unique_sorted(meaning for record in known_records for meaning in record.meanings)
    rad_names = _unique_sorted(
        rad_name for record in known_records for rad_name in record.rad_names
    )
    radical_values = _unique_sorted(
        value for record in known_records for value in record.radical_values
    )
    variant_types = _unique_sorted(
        value for record in known_records for value in record.variant_types
    )
    query_code_types = _unique_sorted(
        value for record in known_records for value in record.query_code_types
    )
    dictionary_reference_types = _unique_sorted(
        value for record in known_records for value in record.dictionary_reference_types
    )
    character_readings = [
        {
            "kanji": record.literal,
            "on_readings": list(record.on_readings),
            "kun_readings": list(record.kun_readings),
            "nanori_readings": list(record.nanori_readings),
        }
        for record in known_records
        if record.on_readings or record.kun_readings or record.nanori_readings
    ]
    curriculum_known_count = sum(
        1
        for record in known_records
        if record.grade is not None or record.freq is not None or record.old_jlpt is not None
    )
    payload: dict[str, object] = {
        "kanji": kanji_chars,
        "kanji_count": len(kanji_chars),
        "known_kanji_count": len(known_records),
        "unknown_kanji_count": len(kanji_chars) - len(known_records),
        "grade_known_count": len(grades),
        "freq_known_count": len(freqs),
        "old_jlpt_known_count": len(old_jlpt_levels),
        "nanori_reading_count": len(nanori_readings),
        "meaning_count": len(meanings),
        "rad_name_count": len(rad_names),
        "radical_value_count": len(radical_values),
        "variant_type_count": len(variant_types),
        "query_code_type_count": len(query_code_types),
        "dictionary_reference_type_count": len(dictionary_reference_types),
        "curriculum_signal_known_count": curriculum_known_count,
    }
    if grades:
        payload.update(
            {
                "grade_min": min(grades),
                "grade_max": max(grades),
                "grade_mean": _mean(grades),
                "non_jouyou_or_name_grade_count": sum(1 for value in grades if value >= 9),
                "kanji_grade_difficulty_proxy": _kanji_grade_difficulty(max(grades)),
            }
        )
    if strokes:
        payload.update(
            {
                "stroke_count_max": max(strokes),
                "stroke_count_mean": _mean(strokes),
            }
        )
    if freqs:
        payload.update(
            {
                "freq_rank_min": min(freqs),
                "freq_rank_mean": _mean(freqs),
            }
        )
    if old_jlpt_levels:
        payload.update(
            {
                "old_jlpt_hardest_level": min(old_jlpt_levels),
                "old_jlpt_easiest_level": max(old_jlpt_levels),
            }
        )
    if on_readings:
        payload["on_readings"] = list(on_readings)
    if kun_readings:
        payload["kun_readings"] = list(kun_readings)
    if nanori_readings:
        payload["nanori_readings"] = list(nanori_readings[:24])
    if meanings:
        payload["meanings_sample"] = list(meanings[:24])
    if rad_names:
        payload["rad_names"] = list(rad_names[:24])
    if radical_values:
        payload["radical_values"] = list(radical_values[:24])
    if variant_types:
        payload["variant_type_values"] = list(variant_types)
    if query_code_types:
        payload["query_code_type_values"] = list(query_code_types)
    if dictionary_reference_types:
        payload["dictionary_reference_type_values"] = list(dictionary_reference_types[:24])
    if character_readings:
        payload["character_readings"] = character_readings
    return payload


def _build_kanjivg_character_record(elem: ElementTree.Element) -> KanjivgCharacterRecord:
    literal = _kanjivg_literal_from_id(str(elem.get("id") or ""))
    path_counter = [0]
    group_counter = [0]
    group_depths: list[int] = []
    components: list[str] = []
    radical_values: list[str] = []
    position_values: list[str] = []
    part_values: list[str] = []
    phonetic_elements: list[str] = []
    variant_counter = [0]
    for child in list(elem):
        _collect_kanjivg_node_stats(
            child,
            depth=0,
            literal=literal,
            path_counter=path_counter,
            group_counter=group_counter,
            group_depths=group_depths,
            components=components,
            radical_values=radical_values,
            position_values=position_values,
            part_values=part_values,
            phonetic_elements=phonetic_elements,
            variant_counter=variant_counter,
        )
    path_count = path_counter[0]
    group_count = group_counter[0]
    component_elements = _unique_sorted(components)
    return KanjivgCharacterRecord(
        literal=literal,
        path_count=path_count,
        group_count=group_count,
        max_group_depth=max(group_depths) if group_depths else 0,
        component_count=len(component_elements),
        component_elements=component_elements,
        radical_values=_unique_sorted(radical_values),
        position_values=_unique_sorted(position_values),
        part_values=_unique_sorted(part_values),
        phonetic_elements=_unique_sorted(phonetic_elements),
        variant_count=variant_counter[0],
        visual_complexity_score=_kanjivg_visual_complexity_score(
            path_count=path_count,
            component_count=len(component_elements),
            max_group_depth=max(group_depths) if group_depths else 0,
        ),
    )


def _collect_kanjivg_node_stats(
    elem: ElementTree.Element,
    *,
    depth: int,
    literal: str,
    path_counter: list[int],
    group_counter: list[int],
    group_depths: list[int],
    components: list[str],
    radical_values: list[str],
    position_values: list[str],
    part_values: list[str],
    phonetic_elements: list[str],
    variant_counter: list[int],
) -> None:
    local_name = _xml_local_name(elem.tag)
    if local_name == "path":
        path_counter[0] += 1
    elif local_name == "g":
        next_depth = depth + 1
        group_counter[0] += 1
        group_depths.append(next_depth)
        component = _kanjivg_component_element(elem)
        if component and component != literal:
            components.append(component)
        radical_values.extend(_kanjivg_attr_values(elem, "radical"))
        position_values.extend(_kanjivg_attr_values(elem, "position"))
        part_values.extend(_kanjivg_attr_values(elem, "part"))
        phonetic_elements.extend(_kanjivg_attr_values(elem, "phon"))
        if _kanjivg_attr_values(elem, "variant"):
            variant_counter[0] += 1
        for child in list(elem):
            _collect_kanjivg_node_stats(
                child,
                depth=next_depth,
                literal=literal,
                path_counter=path_counter,
                group_counter=group_counter,
                group_depths=group_depths,
                components=components,
                radical_values=radical_values,
                position_values=position_values,
                part_values=part_values,
                phonetic_elements=phonetic_elements,
                variant_counter=variant_counter,
            )
    else:
        for child in list(elem):
            _collect_kanjivg_node_stats(
                child,
                depth=depth,
                literal=literal,
                path_counter=path_counter,
                group_counter=group_counter,
                group_depths=group_depths,
                components=components,
                radical_values=radical_values,
                position_values=position_values,
                part_values=part_values,
                phonetic_elements=phonetic_elements,
                variant_counter=variant_counter,
            )


def _build_kanjivg_aggregate(
    text: str,
    *,
    kanjivg_character_index: Mapping[str, KanjivgCharacterRecord],
) -> dict[str, object]:
    kanji_chars = [char for char in text if contains_kanji(char)]
    if not kanji_chars:
        return {}
    records = [kanjivg_character_index.get(char) for char in kanji_chars]
    known_records = [record for record in records if record is not None]
    if not known_records:
        return {}
    path_counts = [record.path_count for record in known_records if record.path_count > 0]
    group_counts = [record.group_count for record in known_records if record.group_count > 0]
    group_depths = [
        record.max_group_depth for record in known_records if record.max_group_depth > 0
    ]
    component_counts = [
        record.component_count for record in known_records if record.component_count > 0
    ]
    visual_scores = [
        record.visual_complexity_score
        for record in known_records
        if record.visual_complexity_score > 0.0
    ]
    component_elements = _unique_sorted(
        component for record in known_records for component in record.component_elements
    )
    radical_values = _unique_sorted(
        value for record in known_records for value in record.radical_values
    )
    position_values = _unique_sorted(
        value for record in known_records for value in record.position_values
    )
    part_values = _unique_sorted(value for record in known_records for value in record.part_values)
    phonetic_elements = _unique_sorted(
        value for record in known_records for value in record.phonetic_elements
    )
    variant_counts = [record.variant_count for record in known_records if record.variant_count > 0]
    payload: dict[str, object] = {
        "kanji": kanji_chars,
        "known_kanji_count": len(known_records),
        "unknown_kanji_count": len(kanji_chars) - len(known_records),
        "radical_value_count": len(radical_values),
        "position_value_count": len(position_values),
        "part_value_count": len(part_values),
        "phonetic_component_count": len(phonetic_elements),
        "variant_count": sum(variant_counts),
    }
    if path_counts:
        payload.update(
            {
                "path_count_max": max(path_counts),
                "path_count_mean": _mean(path_counts),
            }
        )
    if group_counts:
        payload.update(
            {
                "group_count_max": max(group_counts),
                "group_count_mean": _mean(group_counts),
            }
        )
    if group_depths:
        payload.update(
            {
                "max_group_depth": max(group_depths),
                "group_depth_mean": _mean(group_depths),
            }
        )
    if component_counts:
        payload.update(
            {
                "component_count_max": max(component_counts),
                "component_count_mean": _mean(component_counts),
            }
        )
    if visual_scores:
        payload.update(
            {
                "visual_complexity_proxy_max": round(max(visual_scores), 6),
                "visual_complexity_proxy_mean": round(sum(visual_scores) / len(visual_scores), 6),
            }
        )
    if component_elements:
        payload["component_elements_sample"] = list(component_elements[:24])
    if radical_values:
        payload["radical_values"] = list(radical_values[:24])
    if position_values:
        payload["position_values"] = list(position_values[:24])
    if part_values:
        payload["part_values"] = list(part_values[:24])
    if phonetic_elements:
        payload["phonetic_elements_sample"] = list(phonetic_elements[:24])
    if variant_counts:
        payload["variant_count_max"] = max(variant_counts)
        payload["variant_count_mean"] = _mean(variant_counts)
    return payload


def _kanjivg_visual_complexity_score(
    *,
    path_count: int,
    component_count: int,
    max_group_depth: int,
) -> float:
    path_score = min(max(0, int(path_count)) / 24.0, 1.0)
    component_score = min(max(0, int(component_count)) / 8.0, 1.0)
    depth_score = min(max(0, int(max_group_depth) - 1) / 4.0, 1.0)
    return round((path_score * 0.55) + (component_score * 0.30) + (depth_score * 0.15), 6)


def _kanjivg_component_element(elem: ElementTree.Element) -> str:
    for key, value in elem.attrib.items():
        if _xml_local_name(key) == "element":
            return str(value or "").strip()
    return ""


def _kanjivg_attr_values(elem: ElementTree.Element, attr_name: str) -> tuple[str, ...]:
    wanted = str(attr_name or "").strip()
    if not wanted:
        return ()
    return _unique_sorted(
        value for key, value in elem.attrib.items() if _xml_local_name(key) == wanted
    )


def _kanjivg_literal_from_id(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    _, _separator, suffix = text.rpartition("_")
    if not suffix:
        return ""
    try:
        return chr(int(suffix, 16))
    except (TypeError, ValueError):
        return ""


def _kanjidic2_japanese_readings(
    elem: ElementTree.Element,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    on_readings: list[str] = []
    kun_readings: list[str] = []
    for reading in elem.findall("reading_meaning/rmgroup/reading"):
        text = _node_text(reading)
        if not text:
            continue
        reading_type = str(reading.get("r_type") or "").strip()
        if reading_type == "ja_on":
            on_readings.append(text)
        elif reading_type == "ja_kun":
            kun_readings.append(text)
    nanori_readings = _collect_texts(elem.findall("reading_meaning/nanori"))
    return _unique_sorted(on_readings), _unique_sorted(kun_readings), nanori_readings


def _kanjidic2_meanings(elem: ElementTree.Element) -> tuple[str, ...]:
    meanings: list[str] = []
    for meaning in elem.findall("reading_meaning/rmgroup/meaning"):
        language = _xml_attr(meaning, "lang")
        if language and language != "en":
            continue
        text = _node_text(meaning)
        if text:
            meanings.append(text)
    return _unique_sorted(meanings)


def _kanjidic2_typed_values(
    nodes: Iterable[ElementTree.Element],
    *,
    attr_name: str,
) -> tuple[str, ...]:
    values: list[str] = []
    for node in nodes:
        text = _node_text(node)
        attr_value = _xml_attr(node, attr_name)
        if text and attr_value:
            values.append(f"{attr_value}:{text}")
        elif text:
            values.append(text)
        elif attr_value:
            values.append(attr_value)
    return _unique_sorted(values)


def _jmdict_priority_kanji_entries(
    elem: ElementTree.Element,
) -> tuple[dict[str, object], ...]:
    entries: list[dict[str, object]] = []
    for k_ele in elem.findall("k_ele"):
        tags = _collect_texts(k_ele.findall("ke_pri"))
        info_values = _collect_texts(k_ele.findall("ke_inf"))
        for keb in k_ele.findall("keb"):
            term = _node_text(keb)
            if term:
                entries.append(
                    {
                        "term": term,
                        "tags": tags,
                        "info_values": info_values,
                    }
                )
    return tuple(entries)


def _jmdict_priority_reading_entries(
    elem: ElementTree.Element,
) -> tuple[dict[str, object], ...]:
    entries: list[dict[str, object]] = []
    for r_ele in elem.findall("r_ele"):
        tags = _collect_texts(r_ele.findall("re_pri"))
        info_values = _collect_texts(r_ele.findall("re_inf"))
        restrictions = _unique_sorted(_node_text(node) for node in r_ele.findall("re_restr"))
        no_kanji = bool(r_ele.findall("re_nokanji"))
        for reb in r_ele.findall("reb"):
            term = _node_text(reb)
            if term:
                entries.append(
                    {
                        "term": term,
                        "tags": tags,
                        "info_values": info_values,
                        "restrictions": restrictions,
                        "no_kanji": no_kanji,
                    }
                )
    return tuple(entries)


def _jmdict_priority_pair_records(
    kanji_entries: Sequence[Mapping[str, object]],
    reading_entries: Sequence[Mapping[str, object]],
    *,
    entry_tags: Iterable[str],
) -> tuple[JmdictPriorityPairRecord, ...]:
    raw_pairs: list[dict[str, object]] = []
    for reading_entry in reading_entries:
        reading = str(reading_entry.get("term") or "").strip()
        if not reading:
            continue
        compatible_surfaces = _jmdict_priority_compatible_surfaces(
            kanji_entries,
            reading_entry,
            reading=reading,
        )
        for surface_entry in compatible_surfaces:
            surface = str(surface_entry.get("term") or "").strip()
            if not surface:
                continue
            raw_pairs.append(
                {
                    "surface": surface,
                    "reading": reading,
                    "surface_tags": tuple(surface_entry.get("tags", ()) or ()),
                    "reading_tags": tuple(reading_entry.get("tags", ()) or ()),
                    "surface_info_values": tuple(surface_entry.get("info_values", ()) or ()),
                    "reading_info_values": tuple(reading_entry.get("info_values", ()) or ()),
                }
            )
        raw_pairs.append(
            {
                "surface": reading,
                "reading": reading,
                "surface_tags": (),
                "reading_tags": tuple(reading_entry.get("tags", ()) or ()),
                "surface_info_values": (),
                "reading_info_values": tuple(reading_entry.get("info_values", ()) or ()),
            }
        )
    surface_readings: dict[str, set[str]] = {}
    for raw_pair in raw_pairs:
        surface_readings.setdefault(str(raw_pair["surface"]), set()).add(str(raw_pair["reading"]))
    records = [
        _build_jmdict_priority_pair_record(
            surface=str(raw_pair["surface"]),
            reading=str(raw_pair["reading"]),
            surface_tags=raw_pair.get("surface_tags", ()),
            reading_tags=raw_pair.get("reading_tags", ()),
            entry_tags=entry_tags,
            surface_info_values=raw_pair.get("surface_info_values", ()),
            reading_info_values=raw_pair.get("reading_info_values", ()),
            surface_reading_count=len(surface_readings.get(str(raw_pair["surface"]), ())),
        )
        for raw_pair in raw_pairs
    ]
    return _merge_jmdict_priority_pair_records(records)


def _jmdict_priority_compatible_surfaces(
    kanji_entries: Sequence[Mapping[str, object]],
    reading_entry: Mapping[str, object],
    *,
    reading: str,
) -> tuple[Mapping[str, object], ...]:
    restrictions = {
        str(value or "").strip()
        for value in reading_entry.get("restrictions", ()) or ()
        if str(value or "").strip()
    }
    if restrictions:
        return tuple(
            entry for entry in kanji_entries if str(entry.get("term") or "").strip() in restrictions
        )
    if kanji_entries and not bool(reading_entry.get("no_kanji")):
        return tuple(kanji_entries)
    return (
        {
            "term": reading,
            "tags": (),
            "info_values": (),
        },
    )


def _build_jmdict_priority_pair_record(
    *,
    surface: str,
    reading: str,
    surface_tags: Iterable[str],
    reading_tags: Iterable[str],
    entry_tags: Iterable[str],
    surface_info_values: Iterable[str],
    reading_info_values: Iterable[str],
    surface_reading_count: int,
) -> JmdictPriorityPairRecord:
    surface_direct_tags = _unique_sorted(surface_tags)
    reading_direct_tags = _unique_sorted(reading_tags)
    entry = _unique_sorted(entry_tags)
    surface_info = _unique_sorted(surface_info_values)
    reading_info = _unique_sorted(reading_info_values)
    surface_score, _surface_band = _jmdict_priority_score(
        surface_direct_tags,
        nf_min=_min_nf_value(surface_direct_tags),
    )
    reading_score, _reading_band = _jmdict_priority_score(
        reading_direct_tags,
        nf_min=_min_nf_value(reading_direct_tags),
    )
    direct_tags = _unique_sorted((*surface_direct_tags, *reading_direct_tags))
    direct_score, direct_band = _jmdict_priority_score(
        direct_tags,
        nf_min=_min_nf_value(direct_tags),
    )
    entry_score, entry_band = _jmdict_priority_score(entry, nf_min=_min_nf_value(entry))
    safe_score, safe_band, safe_kind = _safe_jmdict_pair_priority(
        surface_score=surface_score,
        reading_score=reading_score,
        direct_score=direct_score,
        direct_band=direct_band,
        surface_info_values=surface_info,
        reading_info_values=reading_info,
        surface_reading_count=surface_reading_count,
    )
    return JmdictPriorityPairRecord(
        surface=surface,
        reading=reading,
        surface_tags=surface_direct_tags,
        reading_tags=reading_direct_tags,
        entry_tags=entry,
        surface_info_values=surface_info,
        reading_info_values=reading_info,
        surface_reading_count=max(0, int(surface_reading_count)),
        direct_priority_score=direct_score,
        direct_priority_band=direct_band,
        entry_priority_score=entry_score,
        entry_priority_band=entry_band,
        safe_priority_score=safe_score,
        safe_priority_band=safe_band,
        safe_priority_kind=safe_kind,
    )


def _safe_jmdict_pair_priority(
    *,
    surface_score: float,
    reading_score: float,
    direct_score: float,
    direct_band: str,
    surface_info_values: Sequence[str],
    reading_info_values: Sequence[str],
    surface_reading_count: int,
) -> tuple[float, str, str]:
    if surface_info_values or reading_info_values:
        return 0.0, "none", "marked_form_not_safe"
    if reading_score > 0.0:
        return direct_score, direct_band, "reading_direct"
    if surface_score > 0.0 and int(surface_reading_count) <= 1:
        return surface_score, direct_band, "surface_single_reading"
    if surface_score > 0.0:
        return 0.0, "none", "surface_only_multi_reading"
    return 0.0, "none", "entry_inherited_only"


def _merge_jmdict_priority_pair_records(
    records: Iterable[JmdictPriorityPairRecord],
) -> tuple[JmdictPriorityPairRecord, ...]:
    merged: dict[tuple[str, str], JmdictPriorityPairRecord] = {}
    for record in records:
        key = (record.surface, record.reading)
        existing = merged.get(key)
        if existing is None:
            merged[key] = record
            continue
        merged[key] = _merge_jmdict_priority_pair_record(existing, record)
    return tuple(merged[key] for key in sorted(merged))


def _merge_jmdict_priority_pair_record(
    existing: JmdictPriorityPairRecord,
    record: JmdictPriorityPairRecord,
) -> JmdictPriorityPairRecord:
    combined = _build_jmdict_priority_pair_record(
        surface=record.surface,
        reading=record.reading,
        surface_tags=(*existing.surface_tags, *record.surface_tags),
        reading_tags=(*existing.reading_tags, *record.reading_tags),
        entry_tags=(*existing.entry_tags, *record.entry_tags),
        surface_info_values=(
            *existing.surface_info_values,
            *record.surface_info_values,
        ),
        reading_info_values=(
            *existing.reading_info_values,
            *record.reading_info_values,
        ),
        surface_reading_count=max(
            existing.surface_reading_count,
            record.surface_reading_count,
        ),
    )
    safest = max(
        (existing, record, combined),
        key=lambda item: (
            item.safe_priority_score,
            item.direct_priority_score,
            item.entry_priority_score,
        ),
    )
    if safest is combined:
        return combined
    return _build_jmdict_priority_pair_record(
        surface=record.surface,
        reading=record.reading,
        surface_tags=(*existing.surface_tags, *record.surface_tags),
        reading_tags=(*existing.reading_tags, *record.reading_tags),
        entry_tags=(*existing.entry_tags, *record.entry_tags),
        surface_info_values=safest.surface_info_values,
        reading_info_values=safest.reading_info_values,
        surface_reading_count=safest.surface_reading_count,
    )


def _build_jmdict_priority_record(
    *,
    direct_tags: Iterable[str],
    entry_tags: Iterable[str],
    pair_records: Iterable[JmdictPriorityPairRecord] = (),
) -> JmdictPriorityRecord:
    direct = _unique_sorted(direct_tags)
    entry = _unique_sorted(entry_tags)
    all_tags = _unique_sorted((*direct, *entry))
    nf_min = _min_nf_value(all_tags)
    score, band = _jmdict_priority_score(all_tags, nf_min=nf_min)
    direct_nf_min = _min_nf_value(direct)
    direct_score, direct_band = _jmdict_priority_score(direct, nf_min=direct_nf_min)
    entry_nf_min = _min_nf_value(entry)
    entry_score, entry_band = _jmdict_priority_score(entry, nf_min=entry_nf_min)
    return JmdictPriorityRecord(
        direct_tags=direct,
        entry_tags=entry,
        priority_score=score,
        priority_band=band,
        nf_min=nf_min,
        direct_priority_score=direct_score,
        direct_priority_band=direct_band,
        direct_nf_min=direct_nf_min,
        entry_priority_score=entry_score,
        entry_priority_band=entry_band,
        entry_nf_min=entry_nf_min,
        pair_records=_merge_jmdict_priority_pair_records(pair_records),
    )


def _merge_jmdict_priority_records(
    existing: JmdictPriorityRecord | None,
    new_record: JmdictPriorityRecord,
) -> JmdictPriorityRecord:
    if existing is None:
        return new_record
    return _build_jmdict_priority_record(
        direct_tags=(*existing.direct_tags, *new_record.direct_tags),
        entry_tags=(*existing.entry_tags, *new_record.entry_tags),
        pair_records=(*existing.pair_records, *new_record.pair_records),
    )


def _jmdict_priority_score(tags: Iterable[str], *, nf_min: int | None) -> tuple[float, str]:
    tag_set = frozenset(tags)
    if tag_set & _JMDICT_PRIMARY_PRIORITY_TAGS or (nf_min is not None and nf_min <= 12):
        return 1.0, "primary"
    if tag_set & _JMDICT_SECONDARY_PRIORITY_TAGS or (nf_min is not None and nf_min <= 24):
        return 0.75, "secondary"
    if nf_min is not None and nf_min <= 36:
        return 0.5, "tertiary"
    if tag_set:
        return 0.35, "listed"
    return 0.0, "none"


def _min_nf_value(tags: Iterable[str]) -> int | None:
    values: list[int] = []
    for tag in tags:
        match = _NF_RE.match(str(tag or "").strip().lower())
        if match:
            values.append(int(match.group(1)))
    return min(values) if values else None


def _kanji_grade_difficulty(grade: int) -> float:
    if grade <= 0:
        return 0.0
    if grade <= 6:
        return round(0.10 + ((grade - 1) * 0.08), 6)
    if grade == 8:
        return 0.70
    if grade in {9, 10}:
        return 0.88
    return 0.80


def _collect_texts(nodes: Iterable[ElementTree.Element]) -> tuple[str, ...]:
    return _unique_sorted(_node_text(node).lower() for node in nodes)


def _collect_attr_values(
    nodes: Iterable[ElementTree.Element],
    *,
    attr_name: str,
) -> tuple[str, ...]:
    return _unique_sorted(_xml_attr(node, attr_name) for node in nodes)


def _collect_jmdict_source_languages(
    nodes: Iterable[ElementTree.Element],
) -> tuple[str, ...]:
    values: list[str] = []
    for node in nodes:
        language = _xml_attr(node, "lang")
        source_type = _xml_attr(node, "ls_type")
        wasei = _xml_attr(node, "ls_wasei")
        text = _node_text(node).lower()
        if language:
            values.append(language.lower())
        if source_type:
            values.append(f"type:{source_type.lower()}")
        if wasei:
            values.append("wasei")
        if text:
            values.append(f"text:{text}")
    return _unique_sorted(values)


def _collect_jmdict_gloss_languages(
    nodes: Iterable[ElementTree.Element],
) -> tuple[str, ...]:
    values: list[str] = []
    for node in nodes:
        values.append((_xml_attr(node, "lang") or "eng").lower())
    return _unique_sorted(values)


def _collect_jmdict_gloss_values(
    nodes: Iterable[ElementTree.Element],
) -> tuple[str, ...]:
    values: list[str] = []
    for node in nodes:
        language = (_xml_attr(node, "lang") or "eng").lower()
        if language != "eng":
            continue
        text = _node_text(node)
        if text:
            values.append(text)
    return _unique_sorted(values)


def _count_nonempty_nodes(nodes: Iterable[ElementTree.Element]) -> int:
    return sum(1 for node in nodes if _node_text(node))


def _resolve_existing_path(path: Path) -> Path | None:
    candidate = Path(path)
    if candidate.exists():
        return candidate
    return None


def _jlpt_vocabulary_candidate_files(path: Path) -> tuple[Path, ...]:
    if path.is_file() and path.suffix.lower() in {".csv", ".json"}:
        return (path,)
    if not path.is_dir():
        return ()
    names = ("JLPT_vocab_ALL.csv", "JLPT_vocab_ALL.json")
    matches: list[Path] = []
    for name in names:
        matches.extend(sorted(path.rglob(name)))
    if matches:
        return tuple(dict.fromkeys(matches))
    return tuple(sorted((*path.rglob("*.csv"), *path.rglob("*.json"))))


def _iter_jlpt_vocabulary_csv_rows(path: Path) -> Iterable[tuple[str, str, int | None]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if not isinstance(row, Mapping):
                    continue
                surface = _first_mapping_value(row, ("Kanji", "kanji", "word", "surface"))
                reading = _first_mapping_value(row, ("Reading", "reading", "kana"))
                level = _safe_int(_first_mapping_value(row, ("Level", "level", "jlpt")))
                if surface or reading:
                    yield surface, reading, level
    except (OSError, csv.Error, UnicodeError):
        return


def _iter_jlpt_vocabulary_json_rows(path: Path) -> Iterable[tuple[str, str, int | None]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return
    if isinstance(payload, Mapping):
        for surface, raw_entries in payload.items():
            if isinstance(raw_entries, Mapping):
                raw_entries = (raw_entries,)
            if isinstance(raw_entries, (str, bytes)) or not hasattr(raw_entries, "__iter__"):
                continue
            for raw_entry in raw_entries:
                if not isinstance(raw_entry, Mapping):
                    continue
                reading = _first_mapping_value(raw_entry, ("reading", "Reading", "kana"))
                level = _safe_int(_first_mapping_value(raw_entry, ("level", "Level", "jlpt")))
                yield str(surface or "").strip(), reading, level
        return
    if isinstance(payload, list):
        for raw_entry in payload:
            if not isinstance(raw_entry, Mapping):
                continue
            surface = _first_mapping_value(raw_entry, ("Kanji", "kanji", "word", "surface"))
            reading = _first_mapping_value(raw_entry, ("Reading", "reading", "kana"))
            level = _safe_int(_first_mapping_value(raw_entry, ("Level", "level", "jlpt")))
            if surface or reading:
                yield surface, reading, level


def _lesson_vocabulary_candidate_files(path: Path) -> tuple[Path, ...]:
    if path.is_file() and path.suffix.lower() in {".html", ".xhtml"}:
        return (path,)
    if not path.is_dir():
        return ()
    candidates = sorted((*path.rglob("*.xhtml"), *path.rglob("*.html")))
    return tuple(candidate for candidate in candidates if candidate.is_file())


def _iter_lesson_vocabulary_rows(text: str) -> Iterable[tuple[str, str, str, str]]:
    header_indexes: dict[str, int] = {}
    for row_html in _HTML_ROW_RE.findall(text):
        cells = [_clean_html_cell(cell) for cell in _HTML_CELL_RE.findall(row_html)]
        if len(cells) < 2:
            continue
        normalized_headers = [cell.lower() for cell in cells]
        if "hiragana" in normalized_headers or "kanji" in normalized_headers:
            header_indexes = _lesson_header_indexes(normalized_headers)
            continue
        if header_indexes:
            reading = _lesson_cell_at(cells, header_indexes.get("reading", 1))
            surface = _lesson_cell_at(cells, header_indexes.get("surface", 3)) or reading
            romanization = _lesson_cell_at(cells, header_indexes.get("romanization", -1))
            gloss = _lesson_cell_at(cells, header_indexes.get("gloss", -1))
        else:
            reading = _lesson_cell_at(cells, 1)
            surface = _lesson_cell_at(cells, 3) or reading
            romanization = _lesson_cell_at(cells, 2)
            gloss = _lesson_cell_at(cells, 4)
        if not _contains_japanese(surface) and not _contains_japanese(reading):
            continue
        if not surface and not reading:
            continue
        yield surface, reading, romanization, gloss


def _lesson_header_indexes(headers: Sequence[str]) -> dict[str, int]:
    indexes: dict[str, int] = {}
    for index, header in enumerate(headers):
        compact = " ".join(str(header or "").strip().lower().split())
        if compact in {"hiragana", "kana"}:
            indexes.setdefault("reading", index)
        elif compact == "kanji":
            indexes.setdefault("surface", index)
        elif compact in {"romanization", "romaji", "rōmaji"}:
            indexes.setdefault("romanization", index)
        elif compact in {"english translation", "english", "translation", "meaning"}:
            indexes.setdefault("gloss", index)
    return indexes


def _lesson_cell_at(cells: list[str], index: int) -> str:
    if index < 0 or index >= len(cells):
        return ""
    return str(cells[index] or "").strip()


def _clean_html_cell(value: str) -> str:
    text = _HTML_TAG_RE.sub("", value)
    return html.unescape(text).replace("\xa0", " ").strip()


def _lesson_title_from_html(text: str) -> str:
    for pattern in (
        r"<h1\b[^>]*>(.*?)</h1>",
        r"<h2\b[^>]*>(.*?)</h2>",
        r"<title\b[^>]*>(.*?)</title>",
    ):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        title = _clean_html_cell(match.group(1))
        if title:
            return title
    return ""


def _lesson_index_from_path(path: Path, *, fallback: int) -> int:
    text = str(path)
    for pattern in (
        r"module[-_](\d+)",
        r"chapter[-_](\d+)",
        r"lesson[-_](\d+)",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = _safe_int(match.group(1))
            if value is not None:
                return value
    return int(fallback)


def _lesson_key_from_path(path: Path) -> str:
    return str(path.name or path)


def _first_mapping_value(row: Mapping[object, object], keys: Iterable[str]) -> str:
    for key in keys:
        if key in row:
            return str(row.get(key) or "").strip()
    return ""


def _contains_japanese(text: str) -> bool:
    return bool(_JAPANESE_TEXT_RE.search(str(text or "")))


def _unique_sorted(values: Iterable[object]) -> tuple[str, ...]:
    return tuple(sorted({str(value or "").strip() for value in values if str(value or "").strip()}))


def _node_text(node: ElementTree.Element | None) -> str:
    if node is None:
        return ""
    return str(node.text or "").strip()


def _path_signature_for_cache_key(path: Path | None) -> tuple[int, int] | None:
    if path is None:
        return None
    try:
        stat = path.stat()
    except OSError:
        return None
    return int(stat.st_size), int(stat.st_mtime_ns)


def _safe_int(value: object) -> int | None:
    try:
        text = str(value or "").strip()
        return int(text) if text else None
    except (TypeError, ValueError):
        return None


def _mean(values: Iterable[int]) -> float:
    numbers = [int(value) for value in values]
    if not numbers:
        return 0.0
    return round(sum(numbers) / len(numbers), 6)


def _xml_text_stream(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rb")
    return path.open("rb")


def _xml_local_name(value: object) -> str:
    text = str(value or "")
    if "}" in text:
        return text.rsplit("}", 1)[1]
    return text


def _xml_attr(node: ElementTree.Element, attr_name: str) -> str:
    wanted = str(attr_name or "").strip()
    if not wanted:
        return ""
    for key, value in node.attrib.items():
        if _xml_local_name(key) == wanted:
            return str(value or "").strip()
    return ""


def _deserialize_jmdict_priority_index(payload: object) -> dict[str, JmdictPriorityRecord]:
    if not isinstance(payload, Mapping):
        return {}
    records: dict[str, JmdictPriorityRecord] = {}
    for key, raw_record in payload.items():
        if not isinstance(raw_record, Mapping):
            continue
        term = str(key or "").strip()
        if not term:
            continue
        records[term] = JmdictPriorityRecord(
            direct_tags=tuple(str(item) for item in raw_record.get("direct_tags", ()) or ()),
            entry_tags=tuple(str(item) for item in raw_record.get("entry_tags", ()) or ()),
            priority_score=float(raw_record.get("priority_score") or 0.0),
            priority_band=str(raw_record.get("priority_band") or "none"),
            nf_min=_safe_int(raw_record.get("nf_min")),
            direct_priority_score=float(raw_record.get("direct_priority_score") or 0.0),
            direct_priority_band=str(raw_record.get("direct_priority_band") or "none"),
            direct_nf_min=_safe_int(raw_record.get("direct_nf_min")),
            entry_priority_score=float(raw_record.get("entry_priority_score") or 0.0),
            entry_priority_band=str(raw_record.get("entry_priority_band") or "none"),
            entry_nf_min=_safe_int(raw_record.get("entry_nf_min")),
            pair_records=_deserialize_jmdict_priority_pair_records(
                raw_record.get("pair_records", ()) or ()
            ),
        )
    return records


def _deserialize_jmdict_priority_pair_records(
    payload: object,
) -> tuple[JmdictPriorityPairRecord, ...]:
    if isinstance(payload, Mapping):
        payload = payload.values()
    if isinstance(payload, (str, bytes)) or not hasattr(payload, "__iter__"):
        return ()
    records: list[JmdictPriorityPairRecord] = []
    for raw_record in payload:
        if not isinstance(raw_record, Mapping):
            continue
        records.append(
            JmdictPriorityPairRecord(
                surface=str(raw_record.get("surface") or ""),
                reading=str(raw_record.get("reading") or ""),
                surface_tags=tuple(str(item) for item in raw_record.get("surface_tags", ()) or ()),
                reading_tags=tuple(str(item) for item in raw_record.get("reading_tags", ()) or ()),
                entry_tags=tuple(str(item) for item in raw_record.get("entry_tags", ()) or ()),
                surface_info_values=tuple(
                    str(item) for item in raw_record.get("surface_info_values", ()) or ()
                ),
                reading_info_values=tuple(
                    str(item) for item in raw_record.get("reading_info_values", ()) or ()
                ),
                surface_reading_count=int(raw_record.get("surface_reading_count") or 0),
                direct_priority_score=float(raw_record.get("direct_priority_score") or 0.0),
                direct_priority_band=str(raw_record.get("direct_priority_band") or "none"),
                entry_priority_score=float(raw_record.get("entry_priority_score") or 0.0),
                entry_priority_band=str(raw_record.get("entry_priority_band") or "none"),
                safe_priority_score=float(raw_record.get("safe_priority_score") or 0.0),
                safe_priority_band=str(raw_record.get("safe_priority_band") or "none"),
                safe_priority_kind=str(raw_record.get("safe_priority_kind") or "none"),
            )
        )
    return _merge_jmdict_priority_pair_records(records)


def _deserialize_jmdict_lexical_index(payload: object) -> dict[str, JmdictLexicalRecord]:
    if not isinstance(payload, Mapping):
        return {}
    records: dict[str, JmdictLexicalRecord] = {}
    for key, raw_record in payload.items():
        if not isinstance(raw_record, Mapping):
            continue
        term = str(key or "").strip()
        if not term:
            continue
        records[term] = JmdictLexicalRecord(
            pos_values=tuple(str(item) for item in raw_record.get("pos_values", ()) or ()),
            misc_values=tuple(str(item) for item in raw_record.get("misc_values", ()) or ()),
            field_values=tuple(str(item) for item in raw_record.get("field_values", ()) or ()),
            dial_values=tuple(str(item) for item in raw_record.get("dial_values", ()) or ()),
            source_language_values=tuple(
                str(item) for item in raw_record.get("source_language_values", ()) or ()
            ),
            kanji_info_values=tuple(
                str(item) for item in raw_record.get("kanji_info_values", ()) or ()
            ),
            reading_info_values=tuple(
                str(item) for item in raw_record.get("reading_info_values", ()) or ()
            ),
            gloss_values=tuple(str(item) for item in raw_record.get("gloss_values", ()) or ()),
            gloss_language_values=tuple(
                str(item) for item in raw_record.get("gloss_language_values", ()) or ()
            ),
            lexical_class_groups=tuple(
                str(item) for item in raw_record.get("lexical_class_groups", ()) or ()
            ),
            entry_count=int(raw_record.get("entry_count") or 0),
            kanji_form_count=int(raw_record.get("kanji_form_count") or 0),
            reading_form_count=int(raw_record.get("reading_form_count") or 0),
            form_count=int(raw_record.get("form_count") or 0),
            sense_count=int(raw_record.get("sense_count") or 0),
            sense_info_count=int(raw_record.get("sense_info_count") or 0),
            gloss_count=int(raw_record.get("gloss_count") or 0),
            xref_count=int(raw_record.get("xref_count") or 0),
            antonym_count=int(raw_record.get("antonym_count") or 0),
            sense_restriction_count=int(raw_record.get("sense_restriction_count") or 0),
            reading_restriction_count=int(raw_record.get("reading_restriction_count") or 0),
            no_kanji_reading_count=int(raw_record.get("no_kanji_reading_count") or 0),
            non_vocab_signal_score=float(raw_record.get("non_vocab_signal_score") or 0.0),
        )
    return records


def _deserialize_jmnedict_name_index(payload: object) -> dict[str, JmnedictNameRecord]:
    if not isinstance(payload, Mapping):
        return {}
    records: dict[str, JmnedictNameRecord] = {}
    for key, raw_record in payload.items():
        if not isinstance(raw_record, Mapping):
            continue
        term = str(key or "").strip()
        if not term:
            continue
        records[term] = JmnedictNameRecord(
            surfaces=tuple(str(item) for item in raw_record.get("surfaces", ()) or ()),
            readings=tuple(str(item) for item in raw_record.get("readings", ()) or ()),
            name_types=tuple(str(item) for item in raw_record.get("name_types", ()) or ()),
            name_type_groups=tuple(
                str(item) for item in raw_record.get("name_type_groups", ()) or ()
            ),
            translation_count=int(raw_record.get("translation_count") or 0),
            name_signal_score=float(raw_record.get("name_signal_score") or 0.0),
        )
    return records


def _deserialize_kanjidic2_character_index(
    payload: object,
) -> dict[str, Kanjidic2CharacterRecord]:
    if not isinstance(payload, Mapping):
        return {}
    records: dict[str, Kanjidic2CharacterRecord] = {}
    for key, raw_record in payload.items():
        if not isinstance(raw_record, Mapping):
            continue
        literal = str(raw_record.get("literal") or key or "").strip()
        if not literal:
            continue
        records[literal] = Kanjidic2CharacterRecord(
            literal=literal,
            grade=_safe_int(raw_record.get("grade")),
            stroke_count=_safe_int(raw_record.get("stroke_count")),
            freq=_safe_int(raw_record.get("freq")),
            old_jlpt=_safe_int(raw_record.get("old_jlpt")),
            on_readings=tuple(str(item) for item in raw_record.get("on_readings", ()) or ()),
            kun_readings=tuple(str(item) for item in raw_record.get("kun_readings", ()) or ()),
            nanori_readings=tuple(
                str(item) for item in raw_record.get("nanori_readings", ()) or ()
            ),
            meanings=tuple(str(item) for item in raw_record.get("meanings", ()) or ()),
            rad_names=tuple(str(item) for item in raw_record.get("rad_names", ()) or ()),
            radical_values=tuple(str(item) for item in raw_record.get("radical_values", ()) or ()),
            variant_types=tuple(str(item) for item in raw_record.get("variant_types", ()) or ()),
            query_code_types=tuple(
                str(item) for item in raw_record.get("query_code_types", ()) or ()
            ),
            dictionary_reference_types=tuple(
                str(item) for item in raw_record.get("dictionary_reference_types", ()) or ()
            ),
        )
    return records


def _deserialize_kanjivg_character_index(
    payload: object,
) -> dict[str, KanjivgCharacterRecord]:
    if not isinstance(payload, Mapping):
        return {}
    records: dict[str, KanjivgCharacterRecord] = {}
    for key, raw_record in payload.items():
        if not isinstance(raw_record, Mapping):
            continue
        literal = str(raw_record.get("literal") or key or "").strip()
        if not literal:
            continue
        records[literal] = KanjivgCharacterRecord(
            literal=literal,
            path_count=int(raw_record.get("path_count") or 0),
            group_count=int(raw_record.get("group_count") or 0),
            max_group_depth=int(raw_record.get("max_group_depth") or 0),
            component_count=int(raw_record.get("component_count") or 0),
            component_elements=tuple(
                str(item) for item in raw_record.get("component_elements", ()) or ()
            ),
            radical_values=tuple(str(item) for item in raw_record.get("radical_values", ()) or ()),
            position_values=tuple(
                str(item) for item in raw_record.get("position_values", ()) or ()
            ),
            part_values=tuple(str(item) for item in raw_record.get("part_values", ()) or ()),
            phonetic_elements=tuple(
                str(item) for item in raw_record.get("phonetic_elements", ()) or ()
            ),
            variant_count=int(raw_record.get("variant_count") or 0),
            visual_complexity_score=float(raw_record.get("visual_complexity_score") or 0.0),
        )
    return records


def _deserialize_jlpt_vocabulary_index(payload: object) -> dict[str, JlptVocabularyRecord]:
    if not isinstance(payload, Mapping):
        return {}
    records: dict[str, JlptVocabularyRecord] = {}
    for key, raw_record in payload.items():
        if not isinstance(raw_record, Mapping):
            continue
        term = str(key or "").strip()
        if not term:
            continue
        levels = tuple(
            level
            for level in (_safe_int(item) for item in raw_record.get("levels", ()) or ())
            if level
        )
        records[term] = JlptVocabularyRecord(
            surfaces=tuple(str(item) for item in raw_record.get("surfaces", ()) or ()),
            readings=tuple(str(item) for item in raw_record.get("readings", ()) or ()),
            levels=levels,
            source_count=int(raw_record.get("source_count") or 0),
            entries=tuple(str(item) for item in raw_record.get("entries", ()) or ()),
            normalized_entries=tuple(
                str(item) for item in raw_record.get("normalized_entries", ()) or ()
            ),
            guarded_normalized_entries=tuple(
                str(item) for item in raw_record.get("guarded_normalized_entries", ()) or ()
            ),
        )
    return records


def _deserialize_japanese_lesson_vocabulary_index(
    payload: object,
) -> dict[str, JapaneseLessonVocabularyRecord]:
    if not isinstance(payload, Mapping):
        return {}
    records: dict[str, JapaneseLessonVocabularyRecord] = {}
    for key, raw_record in payload.items():
        if not isinstance(raw_record, Mapping):
            continue
        term = str(key or "").strip()
        if not term:
            continue
        lesson_indices = tuple(
            value
            for value in (_safe_int(item) for item in raw_record.get("lesson_indices", ()) or ())
            if value
        )
        records[term] = JapaneseLessonVocabularyRecord(
            surfaces=tuple(str(item) for item in raw_record.get("surfaces", ()) or ()),
            readings=tuple(str(item) for item in raw_record.get("readings", ()) or ()),
            romanizations=tuple(str(item) for item in raw_record.get("romanizations", ()) or ()),
            glosses=tuple(str(item) for item in raw_record.get("glosses", ()) or ()),
            lesson_indices=lesson_indices,
            lesson_keys=tuple(str(item) for item in raw_record.get("lesson_keys", ()) or ()),
            lesson_titles=tuple(str(item) for item in raw_record.get("lesson_titles", ()) or ()),
            source_count=int(raw_record.get("source_count") or 0),
        )
    return records
