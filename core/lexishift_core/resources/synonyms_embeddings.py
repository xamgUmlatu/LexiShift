from __future__ import annotations

import heapq
import json
import math
import re
import sqlite3
import struct
from pathlib import Path
from typing import Optional, Sequence


class EmbeddingIndex:
    def __init__(self, path: Path | Sequence[Path], *, lower_case: bool) -> None:
        if isinstance(path, Sequence):
            self._paths = [Path(item) for item in path]
        else:
            self._paths = [Path(path)]
        self._path = self._paths[0] if self._paths else Path()
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
        if not self._paths:
            return
        if len(self._paths) == 1:
            self._load_single(self._paths[0])
            return
        for path in self._paths:
            if path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".bin"}:
                self._load_single(path)
                return
        for path in self._paths:
            self._load_text_vectors(path)

    def _load_single(self, path: Path) -> None:
        if path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
            self._path = path
            self._load_sqlite()
            return
        if path.suffix.lower() == ".bin":
            self._path = path
            self._load_word2vec_binary()
            return
        self._load_text_vectors(path)

    def _load_text_vectors(self, path: Path) -> None:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            first_line = handle.readline()
            if not first_line:
                return
            parts = first_line.strip().split()
            if self._is_header(parts):
                dim = int(parts[1])
                if self._dim is None:
                    self._dim = dim
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
        resolved_vectors: list[list[float]] = [vector for vector in vectors if vector is not None]
        averaged = [0.0] * len(resolved_vectors[0])
        for vector in resolved_vectors:
            for idx in range(len(vector)):
                averaged[idx] += vector[idx]
        count = float(len(resolved_vectors))
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
