from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional


@dataclass(frozen=True)
class SynonymSources:
    wordnet_dir: Optional[Path] = None
    moby_path: Optional[Path] = None


@dataclass(frozen=True)
class SynonymOptions:
    max_synonyms: int = 30
    include_phrases: bool = False
    lower_case: bool = True


class SynonymGenerator:
    def __init__(self, sources: SynonymSources, options: Optional[SynonymOptions] = None) -> None:
        self._sources = sources
        self._options = options or SynonymOptions()
        self._synonyms = {}
        self._stats = {"moby": 0, "wordnet": 0}
        self._load_sources()

    def synonyms_for(self, word: str) -> list[str]:
        key = word.lower() if self._options.lower_case else word
        synonyms = self._synonyms.get(key, set()).copy()
        if not self._options.include_phrases:
            synonyms = {item for item in synonyms if " " not in item}
        if self._options.lower_case:
            synonyms.discard(key)
        else:
            synonyms.discard(word)
        results = sorted(synonyms)
        if self._options.max_synonyms > 0:
            results = results[: self._options.max_synonyms]
        return results

    def generate_rules(self, targets: Iterable[str], *, avoid_duplicates: bool = True) -> list[tuple[str, str]]:
        seen_sources: set[str] = set()
        rules: list[tuple[str, str]] = []
        for target in targets:
            synonyms = self.synonyms_for(target)
            for synonym in synonyms:
                if avoid_duplicates and synonym in seen_sources:
                    continue
                seen_sources.add(synonym)
                rules.append((synonym, target))
        return rules

    def total_entries(self) -> int:
        return len(self._synonyms)

    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    def _load_sources(self) -> None:
        if self._sources.moby_path:
            mapping = _load_moby_thesaurus(self._sources.moby_path)
            self._stats["moby"] = len(mapping)
            self._merge(mapping)
        if self._sources.wordnet_dir:
            mapping = _load_wordnet(self._sources.wordnet_dir)
            self._stats["wordnet"] = len(mapping)
            self._merge(mapping)

    def _merge(self, mapping: Mapping[str, set[str]]) -> None:
        for key, values in mapping.items():
            if self._options.lower_case:
                key = key.lower()
                values = {value.lower() for value in values}
            bucket = self._synonyms.setdefault(key, set())
            bucket.update(values)


def _load_moby_thesaurus(path: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    if not path.exists():
        return mapping
    content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line in content:
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",") if part.strip()]
        if len(parts) < 2:
            continue
        head, *synonyms = parts
        mapping.setdefault(head, set()).update(synonyms)
    return mapping


def _load_wordnet(directory: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for filename in ("data.noun", "data.verb", "data.adj", "data.adv"):
        path = directory / filename
        if not path.exists():
            continue
        _parse_wordnet_data(path, mapping)
    return mapping


def _parse_wordnet_data(path: Path, mapping: dict[str, set[str]]) -> None:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line or line.startswith("  ") or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            word_count = int(parts[3], 16)
        except ValueError:
            continue
        words = []
        index = 4
        for _ in range(word_count):
            if index >= len(parts):
                break
            word = parts[index].replace("_", " ")
            words.append(word)
            index += 2
        for word in words:
            bucket = mapping.setdefault(word, set())
            for synonym in words:
                if synonym != word:
                    bucket.add(synonym)
