from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Protocol


class SynonymDbHandler(Protocol):
    name: str

    def supports(self, path: Path) -> bool: ...

    def load_synonyms(self, path: Path) -> dict[str, set[str]]: ...


def _merge_synset(mapping: dict[str, set[str]], words: set[str]) -> None:
    if len(words) < 2:
        return
    for word in words:
        bucket = mapping.setdefault(word, set())
        for synonym in words:
            if synonym != word:
                bucket.add(synonym)


class JpWordnetSqliteHandler:
    name = "jp-wordnet-sqlite"

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}

    def load_synonyms(self, path: Path) -> dict[str, set[str]]:
        mapping: dict[str, set[str]] = {}
        if not path.exists():
            return mapping
        conn = sqlite3.connect(str(path))
        try:
            cursor = conn.execute(
                """
                SELECT sense.synset, word.lemma
                FROM sense
                JOIN word ON sense.wordid = word.wordid
                WHERE sense.lang = 'jpn'
                ORDER BY sense.synset
                """
            )
            current_synset: str | None = None
            words: set[str] = set()
            for synset_id, lemma in cursor:
                if synset_id != current_synset:
                    _merge_synset(mapping, words)
                    words = set()
                    current_synset = synset_id
                if lemma:
                    cleaned = str(lemma).strip()
                    if cleaned:
                        words.add(cleaned)
            _merge_synset(mapping, words)
        except sqlite3.Error:
            return {}
        finally:
            conn.close()
        return mapping


_HANDLERS: tuple[SynonymDbHandler, ...] = (JpWordnetSqliteHandler(),)


def load_synonyms_from_db(path: Path) -> dict[str, set[str]]:
    for handler in _HANDLERS:
        if handler.supports(path):
            return handler.load_synonyms(path)
    return {}
