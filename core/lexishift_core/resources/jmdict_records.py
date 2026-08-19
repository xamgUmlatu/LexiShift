from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JmdictGlossRecord:
    text: str
    language: str = "eng"
    gloss_type: str = ""
    gender: str = ""
    priority_values: tuple[str, ...] = ()


@dataclass(frozen=True)
class JmdictReadingRecord:
    text: str
    kanji_restrictions: tuple[str, ...] = ()
    no_kanji: bool = False


@dataclass(frozen=True)
class JmdictSenseRecord:
    glosses: tuple[JmdictGlossRecord, ...]
    kanji_restrictions: tuple[str, ...] = ()
    reading_restrictions: tuple[str, ...] = ()
    pos_values: tuple[str, ...] = ()
    field_values: tuple[str, ...] = ()
    misc_values: tuple[str, ...] = ()
    info_values: tuple[str, ...] = ()
    dialect_values: tuple[str, ...] = ()
    cross_references: tuple[str, ...] = ()
    antonyms: tuple[str, ...] = ()
