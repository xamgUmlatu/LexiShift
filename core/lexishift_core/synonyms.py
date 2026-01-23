from __future__ import annotations

from dataclasses import dataclass
import heapq
import json
import math
import re
import sqlite3
import struct
from pathlib import Path
from typing import Iterable, Mapping, Optional
from xml.etree import ElementTree


@dataclass(frozen=True)
class SynonymSources:
    wordnet_dir: Optional[Path] = None
    moby_path: Optional[Path] = None
    openthesaurus_path: Optional[Path] = None
    jp_wordnet_path: Optional[Path] = None
    jmdict_path: Optional[Path] = None
    cc_cedict_path: Optional[Path] = None


@dataclass(frozen=True)
class SynonymOptions:
    max_synonyms: int = 30
    include_phrases: bool = False
    lower_case: bool = True
    require_consensus: bool = False
    use_embeddings: bool = False
    embedding_path: Optional[Path] = None
    embedding_threshold: float = 0.0
    embedding_fallback: bool = True


class SynonymGenerator:
    def __init__(self, sources: SynonymSources, options: Optional[SynonymOptions] = None) -> None:
        self._sources = sources
        self._options = options or SynonymOptions()
        self._synonyms = {}
        self._stats = {
            "moby": 0,
            "wordnet": 0,
            "openthesaurus": 0,
            "jp_wordnet": 0,
            "jmdict": 0,
            "cc_cedict": 0,
        }
        self._embeddings = None
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
        mappings: list[Mapping[str, set[str]]] = []
        if self._sources.moby_path:
            mapping = _load_moby_thesaurus(self._sources.moby_path)
            self._stats["moby"] = len(mapping)
            mappings.append(mapping)
        if self._sources.wordnet_dir:
            mapping = _load_wordnet(self._sources.wordnet_dir)
            self._stats["wordnet"] = len(mapping)
            mappings.append(mapping)
        if self._sources.openthesaurus_path:
            mapping = _load_openthesaurus(self._sources.openthesaurus_path)
            self._stats["openthesaurus"] = len(mapping)
            mappings.append(mapping)
        if self._sources.jp_wordnet_path:
            mapping = _load_jp_wordnet(self._sources.jp_wordnet_path)
            self._stats["jp_wordnet"] = len(mapping)
            mappings.append(mapping)
        if self._sources.jmdict_path:
            mapping = _load_jmdict(self._sources.jmdict_path)
            self._stats["jmdict"] = len(mapping)
            mappings.append(mapping)
        if self._sources.cc_cedict_path:
            mapping = _load_cc_cedict(self._sources.cc_cedict_path)
            self._stats["cc_cedict"] = len(mapping)
            mappings.append(mapping)
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
        if not self._options.use_embeddings or not self._options.embedding_path:
            return
        path = Path(self._options.embedding_path)
        if not path.exists():
            return
        self._embeddings = EmbeddingIndex(path, lower_case=self._options.lower_case)


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


def _load_jmdict(path: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    if not path.exists():
        return mapping
    try:
        root = ElementTree.parse(path).getroot()
    except ElementTree.ParseError:
        return mapping
    for entry in root.findall("entry"):
        glosses = [
            gloss.text.strip()
            for gloss in entry.findall("sense/gloss")
            if gloss.text and gloss.text.strip()
        ]
        if not glosses:
            continue
        jp_terms = []
        for elem in entry.findall("k_ele/keb"):
            if elem.text and elem.text.strip():
                jp_terms.append(elem.text.strip())
        for elem in entry.findall("r_ele/reb"):
            if elem.text and elem.text.strip():
                jp_terms.append(elem.text.strip())
        if not jp_terms:
            continue
        for jp_term in jp_terms:
            bucket = mapping.setdefault(jp_term, set())
            bucket.update(glosses)
    return mapping


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


class EmbeddingIndex:
    def __init__(self, path: Path, *, lower_case: bool) -> None:
        self._path = path
        self._lower_case = lower_case
        self._vectors: dict[str, list[float]] = {}
        self._norms: dict[str, float] = {}
        self._phrase_cache: dict[str, Optional[list[float]]] = {}
        self._dim: Optional[int] = None
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._lsh_indices: Optional[list[int]] = None
        self._load()

    def has_vector(self, word: str) -> bool:
        return self._vector_for_term(word) is not None

    def similarity(self, word_a: str, word_b: str) -> Optional[float]:
        vec_a = self._vector_for_term(word_a)
        vec_b = self._vector_for_term(word_b)
        if vec_a is None or vec_b is None:
            return None
        norm_a = math.sqrt(sum(value * value for value in vec_a))
        norm_b = math.sqrt(sum(value * value for value in vec_b))
        if norm_a <= 0.0 or norm_b <= 0.0:
            return None
        dot = 0.0
        for idx in range(len(vec_a)):
            dot += vec_a[idx] * vec_b[idx]
        return dot / (norm_a * norm_b)

    def nearest_neighbors(
        self,
        term: str,
        *,
        limit: int = 30,
        min_score: float = 0.0,
    ) -> list[tuple[str, float]]:
        if limit <= 0:
            return []
        vec = self._vector_for_term(term)
        if vec is None:
            return []
        term_key = term.lower() if self._lower_case else term
        if self._sqlite_conn and self._lsh_indices:
            return self._nearest_neighbors_sqlite(term_key, vec, limit, min_score)
        if self._sqlite_conn:
            return []
        return self._nearest_neighbors_memory(term_key, vec, limit, min_score)

    def supports_neighbors(self) -> bool:
        if self._sqlite_conn:
            return self._lsh_indices is not None
        return True

    def _load(self) -> None:
        if self._path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
            self._load_sqlite()
            return
        if self._path.suffix.lower() == ".bin":
            self._load_word2vec_binary()
            return
        with self._path.open("r", encoding="utf-8", errors="ignore") as handle:
            first_line = handle.readline()
            if not first_line:
                return
            parts = first_line.strip().split()
            if self._is_header(parts):
                self._dim = int(parts[1])
            else:
                self._parse_vector_line(parts)
            for line in handle:
                parts = line.strip().split()
                if not parts:
                    continue
                self._parse_vector_line(parts)

    def _is_header(self, parts: list[str]) -> bool:
        if len(parts) != 2:
            return False
        return parts[0].isdigit() and parts[1].isdigit()

    def _parse_vector_line(self, parts: list[str]) -> None:
        if len(parts) < 2:
            return
        word = parts[0]
        if self._lower_case:
            word = word.lower()
        try:
            values = [float(value) for value in parts[1:]]
        except ValueError:
            return
        if not values:
            return
        if self._dim is None:
            self._dim = len(values)
        if self._dim is not None and len(values) != self._dim:
            return
        self._vectors[word] = values
        norm = math.sqrt(sum(value * value for value in values))
        if norm > 0.0:
            self._norms[word] = norm

    def _vector_for_term(self, term: str) -> Optional[list[float]]:
        if not term:
            return None
        key = term.lower() if self._lower_case else term
        if key in self._phrase_cache:
            return self._phrase_cache[key]
        vec = self._lookup_vector(key)
        if vec is not None:
            self._phrase_cache[key] = vec
            return vec
        if " " not in key and "-" not in key:
            self._phrase_cache[key] = None
            return None
        parts = [part for part in re.split(r"[\s-]+", key) if part]
        if not parts:
            self._phrase_cache[key] = None
            return None
        vectors = [self._lookup_vector(part) for part in parts]
        if any(vector is None for vector in vectors):
            self._phrase_cache[key] = None
            return None
        averaged = [0.0] * len(vectors[0])
        for vector in vectors:
            for idx in range(len(vector)):
                averaged[idx] += vector[idx]
        count = float(len(vectors))
        for idx in range(len(averaged)):
            averaged[idx] /= count
        self._phrase_cache[key] = averaged
        return averaged

    def _lookup_vector(self, key: str) -> Optional[list[float]]:
        if key in self._phrase_cache:
            return self._phrase_cache[key]
        if self._sqlite_conn:
            vec = self._fetch_sqlite_vector(key)
        else:
            vec = self._vectors.get(key)
        if vec is not None:
            self._phrase_cache[key] = vec
        else:
            self._phrase_cache[key] = None
        return vec

    def _fetch_sqlite_vector(self, key: str) -> Optional[list[float]]:
        if not self._sqlite_conn:
            return None
        if self._lower_case:
            row = self._sqlite_conn.execute(
                "SELECT vector FROM vectors WHERE word_lc = ? ORDER BY word = ? DESC LIMIT 1",
                (key, key),
            ).fetchone()
        else:
            row = self._sqlite_conn.execute(
                "SELECT vector FROM vectors WHERE word = ? LIMIT 1",
                (key,),
            ).fetchone()
        if not row:
            return None
        blob = row[0]
        if not blob:
            return None
        dim = self._dim or (len(blob) // 4)
        if dim <= 0:
            return None
        return list(struct.unpack(f"<{dim}f", blob))

    def _load_sqlite(self) -> None:
        self._sqlite_conn = sqlite3.connect(self._path, check_same_thread=False)
        row = None
        try:
            row = self._sqlite_conn.execute(
                "SELECT value FROM meta WHERE key = 'dim' LIMIT 1"
            ).fetchone()
        except sqlite3.Error:
            row = None
        if row and row[0]:
            try:
                self._dim = int(row[0])
            except (TypeError, ValueError):
                self._dim = None
        lsh_row = None
        try:
            lsh_row = self._sqlite_conn.execute(
                "SELECT value FROM meta WHERE key = 'lsh_indices' LIMIT 1"
            ).fetchone()
        except sqlite3.Error:
            lsh_row = None
        if lsh_row and lsh_row[0]:
            try:
                indices = json.loads(lsh_row[0])
                if isinstance(indices, list) and all(isinstance(idx, int) for idx in indices):
                    self._lsh_indices = indices
            except (TypeError, ValueError, json.JSONDecodeError):
                self._lsh_indices = None

    def _nearest_neighbors_memory(
        self,
        term_key: str,
        vec: list[float],
        limit: int,
        min_score: float,
    ) -> list[tuple[str, float]]:
        norm_a = math.sqrt(sum(value * value for value in vec))
        if norm_a <= 0.0:
            return []
        heap: list[tuple[float, str]] = []
        for word, vec_b in self._vectors.items():
            if word == term_key:
                continue
            norm_b = self._norms.get(word)
            if not norm_b:
                continue
            dot = 0.0
            for idx in range(len(vec)):
                dot += vec[idx] * vec_b[idx]
            score = dot / (norm_a * norm_b)
            if score < min_score:
                continue
            if len(heap) < limit:
                heapq.heappush(heap, (score, word))
            else:
                heapq.heappushpop(heap, (score, word))
        heap.sort(reverse=True)
        return [(word, score) for score, word in heap]

    def _nearest_neighbors_sqlite(
        self,
        term_key: str,
        vec: list[float],
        limit: int,
        min_score: float,
    ) -> list[tuple[str, float]]:
        if not self._sqlite_conn or not self._lsh_indices:
            return []
        norm_a = math.sqrt(sum(value * value for value in vec))
        if norm_a <= 0.0:
            return []
        sig = self._lsh_signature(vec)
        sigs = [sig] + [sig ^ (1 << bit) for bit in range(len(self._lsh_indices))]
        placeholders = ", ".join(["?"] * len(sigs))
        query = f"SELECT word, vector, norm FROM vectors WHERE lsh_sig IN ({placeholders})"
        rows = self._sqlite_conn.execute(query, sigs).fetchall()
        heap: list[tuple[float, str]] = []
        for word, blob, norm_b in rows:
            if not word or not blob or not norm_b:
                continue
            if self._lower_case:
                if word.lower() == term_key:
                    continue
            elif word == term_key:
                continue
            dim = self._dim or (len(blob) // 4)
            vec_b = list(struct.unpack(f"<{dim}f", blob))
            dot = 0.0
            length = min(len(vec), len(vec_b))
            for idx in range(length):
                dot += vec[idx] * vec_b[idx]
            score = dot / (norm_a * norm_b)
            if score < min_score:
                continue
            if len(heap) < limit:
                heapq.heappush(heap, (score, word))
            else:
                heapq.heappushpop(heap, (score, word))
        heap.sort(reverse=True)
        return [(word, score) for score, word in heap]

    def _lsh_signature(self, vec: list[float]) -> int:
        if not self._lsh_indices:
            return 0
        sig = 0
        for bit, idx in enumerate(self._lsh_indices):
            if idx < len(vec) and vec[idx] >= 0.0:
                sig |= 1 << bit
        return sig

    def _load_word2vec_binary(self) -> None:
        with self._path.open("rb") as handle:
            header = handle.readline()
            if not header:
                return
            parts = header.split()
            if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
                return
            vocab_size = int(parts[0])
            self._dim = int(parts[1])
            for _ in range(vocab_size):
                word = _read_binary_word(handle)
                if not word:
                    break
                vector = _read_binary_vector(handle, self._dim)
                if vector is None:
                    break
                if self._lower_case:
                    word = word.lower()
                self._vectors[word] = vector
                norm = math.sqrt(sum(value * value for value in vector))
                if norm > 0.0:
                    self._norms[word] = norm


def _read_binary_word(handle) -> Optional[str]:
    chars = bytearray()
    while True:
        char = handle.read(1)
        if not char:
            return None
        if char not in b" \n\r\t":
            chars.append(char[0])
            break
    while True:
        char = handle.read(1)
        if not char or char in b" \n\r\t":
            break
        chars.append(char[0])
    return chars.decode("utf-8", errors="ignore")


def _read_binary_vector(handle, dim: int) -> Optional[list[float]]:
    if dim <= 0:
        return None
    byte_count = dim * 4
    data = handle.read(byte_count)
    if len(data) != byte_count:
        return None
    values = list(struct.unpack(f"<{dim}f", data))
    return values
