from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence
from xml.etree import ElementTree

from lexishift_core.resources.db_handlers import load_synonyms_from_db
from lexishift_core.resources.dict_loaders import load_jmdict_glosses
from lexishift_core.resources.synonyms_embeddings import EmbeddingIndex


@dataclass(frozen=True)
class SynonymSources:
    wordnet_dir: Optional[Path] = None
    moby_path: Optional[Path] = None
    openthesaurus_path: Optional[Path] = None
    odenet_path: Optional[Path] = None
    jp_wordnet_path: Optional[Path] = None
    jp_wordnet_sqlite_path: Optional[Path] = None
    jmdict_path: Optional[Path] = None
    cc_cedict_path: Optional[Path] = None
    freedict_de_en_path: Optional[Path] = None
    freedict_en_de_path: Optional[Path] = None


@dataclass(frozen=True)
class SynonymOptions:
    max_synonyms: int = 30
    include_phrases: bool = False
    lower_case: bool = True
    require_consensus: bool = False
    use_embeddings: bool = False
    embedding_paths: Sequence[Path] = field(default_factory=tuple)
    embedding_pair: Optional[str] = None
    embedding_threshold: float = 0.0
    embedding_fallback: bool = True


class SynonymGenerator:
    def __init__(self, sources: SynonymSources, options: Optional[SynonymOptions] = None) -> None:
        self._sources = sources
        self._options = options or SynonymOptions()
        self._synonyms: dict[str, set[str]] = {}
        self._stats: dict[str, int] = {
            "moby": 0,
            "wordnet": 0,
            "openthesaurus": 0,
            "odenet": 0,
            "jp_wordnet": 0,
            "jmdict": 0,
            "cc_cedict": 0,
            "freedict_de_en": 0,
            "freedict_en_de": 0,
        }
        self._embeddings: Optional[EmbeddingIndex] = None
        self._load_sources()
        self._load_embeddings()

    def synonyms_for(self, word: str) -> list[str]:
        return self._synonyms_for_detail(word)[0]

    def synonyms_for_detail(self, word: str) -> tuple[list[str], bool]:
        return self._synonyms_for_detail(word)

    def has_embeddings(self) -> bool:
        return self._embeddings is not None

    def embeddings_support_neighbors(self) -> bool:
        if not self._embeddings:
            return False
        return self._embeddings.supports_neighbors()

    def embeddings_has_vector(self, word: str) -> bool:
        if not self._embeddings:
            return False
        return self._embeddings.has_vector(word)

    def _synonyms_for_detail(self, word: str) -> tuple[list[str], bool]:
        key = word.lower() if self._options.lower_case else word
        synonyms = self._synonyms.get(key, set()).copy()
        if not self._options.include_phrases:
            synonyms = {item for item in synonyms if " " not in item}
        if self._options.lower_case:
            synonyms.discard(key)
        else:
            synonyms.discard(word)
        results = sorted(synonyms)
        used_fallback = False
        if (
            not results
            and self._embeddings
            and self._options.embedding_fallback
            and self._embeddings.supports_neighbors()
        ):
            neighbors = self._embeddings.nearest_neighbors(
                key,
                limit=self._options.max_synonyms,
                min_score=0.0,
            )
            fallback = [word for word, _score in neighbors]
            if not self._options.include_phrases:
                fallback = [item for item in fallback if " " not in item]
            results = fallback
            used_fallback = True
        if not used_fallback and self._embeddings and self._embeddings.has_vector(key):
            scored = []
            unknown: list[str] = []
            for synonym in synonyms:
                score = self._embeddings.similarity(key, synonym)
                if score is None:
                    unknown.append(synonym)
                    continue
                if score < self._options.embedding_threshold:
                    continue
                scored.append((score, synonym))
            scored.sort(key=lambda item: (-item[0], item[1]))
            results = [synonym for _, synonym in scored]
            if self._options.embedding_threshold <= 0 and unknown:
                results.extend(sorted(unknown))
        if self._options.max_synonyms > 0:
            results = results[: self._options.max_synonyms]
        return results, used_fallback

    def generate_rules(
        self, targets: Iterable[str], *, avoid_duplicates: bool = True
    ) -> list[tuple[str, str]]:
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
        mappings: list[Mapping[str, set[str]]] = []
        if self._sources.moby_path:
            source_mapping = _load_moby_thesaurus(self._sources.moby_path)
            self._stats["moby"] = len(source_mapping)
            mappings.append(source_mapping)
        if self._sources.wordnet_dir:
            source_mapping = _load_wordnet(self._sources.wordnet_dir)
            self._stats["wordnet"] = len(source_mapping)
            mappings.append(source_mapping)
        if self._sources.openthesaurus_path:
            source_mapping = _load_openthesaurus(self._sources.openthesaurus_path)
            self._stats["openthesaurus"] = len(source_mapping)
            mappings.append(source_mapping)
        if self._sources.odenet_path:
            source_mapping = _load_odenet(self._sources.odenet_path)
            self._stats["odenet"] = len(source_mapping)
            mappings.append(source_mapping)
        if self._sources.jp_wordnet_path:
            source_mapping = _load_jp_wordnet(self._sources.jp_wordnet_path)
            self._stats["jp_wordnet"] = len(source_mapping)
            mappings.append(source_mapping)
        if self._sources.jp_wordnet_sqlite_path:
            source_mapping = load_synonyms_from_db(self._sources.jp_wordnet_sqlite_path)
            self._stats["jp_wordnet"] += len(source_mapping)
            mappings.append(source_mapping)
        if self._sources.jmdict_path:
            source_mapping = _load_jmdict(self._sources.jmdict_path)
            self._stats["jmdict"] = len(source_mapping)
            mappings.append(source_mapping)
        if self._sources.cc_cedict_path:
            source_mapping = _load_cc_cedict(self._sources.cc_cedict_path)
            self._stats["cc_cedict"] = len(source_mapping)
            mappings.append(source_mapping)
        if self._sources.freedict_de_en_path:
            source_mapping = _load_freedict_tei(self._sources.freedict_de_en_path, target_lang="en")
            self._stats["freedict_de_en"] = len(source_mapping)
            mappings.append(source_mapping)
        if self._sources.freedict_en_de_path:
            source_mapping = _load_freedict_tei(self._sources.freedict_en_de_path, target_lang="de")
            self._stats["freedict_en_de"] = len(source_mapping)
            mappings.append(source_mapping)
        if not mappings:
            return
        if self._options.require_consensus and len(mappings) > 1:
            consensus = _apply_consensus_filter(mappings, min_sources=len(mappings))
            self._merge(consensus)
            return
        for mapping in mappings:
            self._merge(mapping)

    def _merge(self, mapping: Mapping[str, set[str]]) -> None:
        for key, values in mapping.items():
            if self._options.lower_case:
                key = key.lower()
                values = {value.lower() for value in values}
            bucket = self._synonyms.setdefault(key, set())
            bucket.update(values)

    def _load_embeddings(self) -> None:
        if not self._options.use_embeddings:
            return
        paths = (
            [Path(item) for item in self._options.embedding_paths if item]
            if self._options.embedding_paths
            else []
        )
        if not paths:
            return
        existing = [path for path in paths if path.exists()]
        if not existing:
            return
        self._embeddings = EmbeddingIndex(existing, lower_case=self._options.lower_case)


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


def _load_openthesaurus(path: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    if not path.exists():
        return mapping
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(";") if part.strip()]
        if len(parts) < 2:
            continue
        for word in parts:
            bucket = mapping.setdefault(word, set())
            for synonym in parts:
                if synonym != word:
                    bucket.add(synonym)
    return mapping


def _load_odenet(path: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    if not path.exists():
        return mapping
    synsets: dict[str, set[str]] = {}
    try:
        current_word: Optional[str] = None
        current_synsets: list[str] = []
        for event, elem in ElementTree.iterparse(path, events=("start", "end")):
            tag = elem.tag
            if tag.endswith("LexicalEntry"):
                if event == "start":
                    current_word = None
                    current_synsets = []
                else:
                    if current_word and current_synsets:
                        for current_synset_id in current_synsets:
                            synsets.setdefault(current_synset_id, set()).add(current_word)
                    current_word = None
                    current_synsets = []
                    elem.clear()
                continue
            if event == "start" and tag.endswith("Lemma"):
                current_word = elem.get("writtenForm") or current_word
                continue
            if event == "start" and tag.endswith("Sense"):
                synset_id = elem.get("synset")
                if synset_id:
                    current_synsets.append(synset_id)
    except ElementTree.ParseError:
        # Fallback: OdeNet oneline XML can contain mismatched tags; use a tolerant scan.
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return mapping
        for chunk in raw.split("</LexicalEntry>"):
            if "<LexicalEntry" not in chunk:
                continue
            lemma_match = re.search(r'writtenForm="([^"]+)"', chunk)
            if not lemma_match:
                continue
            word = lemma_match.group(1).strip()
            if not word:
                continue
            synset_ids = re.findall(r'synset="([^"]+)"', chunk)
            if not synset_ids:
                continue
            for synset_id in synset_ids:
                synsets.setdefault(synset_id, set()).add(word)
    for words in synsets.values():
        if len(words) < 2:
            continue
        for word in words:
            bucket = mapping.setdefault(word, set())
            for synonym in words:
                if synonym != word:
                    bucket.add(synonym)
    return mapping


def _load_jp_wordnet(path: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    if not path.exists():
        return mapping
    synsets: dict[str, set[str]] = {}
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        synset_id = parts[0].strip()
        word = parts[1].strip()
        if not synset_id or not word:
            continue
        synsets.setdefault(synset_id, set()).add(word)
    for words in synsets.values():
        if len(words) < 2:
            continue
        for word in words:
            bucket = mapping.setdefault(word, set())
            for synonym in words:
                if synonym != word:
                    bucket.add(synonym)
    return mapping


def _load_freedict_tei(path: Path, *, target_lang: str) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    if not path.exists():
        return mapping
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    xml_lang_key = "{http://www.w3.org/XML/1998/namespace}lang"
    try:
        for _event, elem in ElementTree.iterparse(path, events=("end",)):
            if elem.tag != f"{{{ns['tei']}}}entry":
                continue
            headwords = [
                orth.text.strip()
                for orth in elem.findall("tei:form/tei:orth", ns)
                if orth.text and orth.text.strip()
            ]
            if not headwords:
                elem.clear()
                continue
            translations = set()
            for quote in elem.findall(".//tei:cit[@type='trans']/tei:quote", ns):
                if not quote.text or not quote.text.strip():
                    continue
                lang = quote.get(xml_lang_key)
                if lang and lang != target_lang:
                    continue
                translations.add(quote.text.strip())
            if translations:
                for headword in headwords:
                    bucket = mapping.setdefault(headword, set())
                    bucket.update(translations)
            elem.clear()
    except (ElementTree.ParseError, OSError):
        return {}
    return mapping


def _load_jmdict(path: Path) -> dict[str, set[str]]:
    return load_jmdict_glosses(path)


def _load_cc_cedict(path: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    if not path.exists():
        return mapping
    pattern = re.compile(r"^(\S+)\s+(\S+)\s+\[.+?\]\s+/(.+)/")
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue
        trad, simp, glosses_raw = match.groups()
        glosses = [gloss.strip() for gloss in glosses_raw.split("/") if gloss.strip()]
        if not glosses:
            continue
        for term in (trad, simp):
            bucket = mapping.setdefault(term, set())
            bucket.update(glosses)
    return mapping


def _load_wordnet(directory: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    classic_files = ("data.noun", "data.verb", "data.adj", "data.adv")
    has_classic = any((directory / name).exists() for name in classic_files)
    if has_classic:
        for filename in classic_files:
            path = directory / filename
            if not path.exists():
                continue
            _parse_wordnet_data(path, mapping)
        return mapping

    json_files = list(directory.glob("*.json"))
    if json_files:
        return _load_wordnet_json(json_files)
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


def _load_wordnet_json(paths: Iterable[Path]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for path in paths:
        name = path.name
        if name.startswith("entries-") or name == "frames.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        for entry in data.values():
            if not isinstance(entry, dict):
                continue
            members = entry.get("members")
            if not members:
                continue
            for word in members:
                bucket = mapping.setdefault(word, set())
                for synonym in members:
                    if synonym != word:
                        bucket.add(synonym)
    return mapping


def _apply_consensus_filter(
    mappings: Iterable[Mapping[str, set[str]]],
    *,
    min_sources: int,
) -> dict[str, set[str]]:
    if min_sources <= 1:
        merged: dict[str, set[str]] = {}
        for mapping in mappings:
            for key, values in mapping.items():
                bucket = merged.setdefault(key, set())
                bucket.update(values)
        return merged
    counts: dict[str, dict[str, int]] = {}
    for mapping in mappings:
        for head, synonyms in mapping.items():
            head_counts = counts.setdefault(head, {})
            for synonym in synonyms:
                head_counts[synonym] = head_counts.get(synonym, 0) + 1
    consensus: dict[str, set[str]] = {}
    for head, head_counts in counts.items():
        filtered = {synonym for synonym, count in head_counts.items() if count >= min_sources}
        if filtered:
            consensus[head] = filtered
    return consensus
