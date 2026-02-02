from __future__ import annotations

from dataclasses import dataclass, field
import csv
import math
from pathlib import Path
from typing import Iterable, Optional, Sequence


@dataclass(frozen=True)
class FrequencySourceConfig:
    path: Path
    delimiter: Optional[str] = None
    has_header: bool = True
    header_starts_with: Optional[str] = None
    skip_prefixes: Sequence[str] = field(default_factory=tuple)
    word_column: Optional[str] = None
    word_index: int = 0
    frequency_column: Optional[str] = None
    frequency_index: int = 1
    rank_column: Optional[str] = None
    rank_index: int = 1
    encoding: str = "utf-8"
    lower_case: bool = True
    min_frequency: float = 0.0


@dataclass(frozen=True)
class FrequencyLexicon:
    scores: dict[str, float] = field(default_factory=dict)
    default_score: float = 0.0

    def weight(self, token: str) -> float:
        key = token.lower() if token else ""
        return self.scores.get(key, self.default_score)

    def weight_phrase(self, phrase: str, *, reducer: str = "avg") -> float:
        tokens = [item for item in phrase.split() if item]
        if not tokens:
            return self.default_score
        values = [self.weight(token) for token in tokens]
        if reducer == "min":
            return min(values)
        if reducer == "max":
            return max(values)
        return sum(values) / len(values)


def load_frequency_lexicon(config: FrequencySourceConfig) -> FrequencyLexicon:
    path = config.path
    if not path.exists():
        return FrequencyLexicon()
    delimiter = config.delimiter
    if delimiter is None:
        delimiter = "\t" if path.suffix.lower() in {".tsv"} else ","
    rows = _read_rows(
        path,
        delimiter=delimiter,
        encoding=config.encoding,
        skip_prefixes=config.skip_prefixes,
    )
    headers = []
    if config.has_header:
        headers = _read_header(rows, header_starts_with=config.header_starts_with)
        if headers is None:
            return FrequencyLexicon()
    word_index = _resolve_index(headers, config.word_column, config.word_index)
    freq_index = _resolve_index(headers, config.frequency_column, config.frequency_index)
    rank_index = _resolve_index(headers, config.rank_column, config.rank_index)

    entries: list[tuple[str, Optional[float], Optional[float]]] = []
    freqs: list[float] = []
    ranks: list[float] = []
    for row in rows:
        if not row:
            continue
        if word_index >= len(row):
            continue
        word = str(row[word_index]).strip()
        if not word:
            continue
        if config.lower_case:
            word = word.lower()
        freq_value = _safe_float(row, freq_index)
        rank_value = _safe_float(row, rank_index)
        if freq_value is not None:
            freqs.append(freq_value)
        if rank_value is not None:
            ranks.append(rank_value)
        entries.append((word, freq_value, rank_value))

    scores: dict[str, float] = {}
    if freqs:
        max_freq = max(freqs)
        for word, freq_value, _rank_value in entries:
            if freq_value is None or freq_value < config.min_frequency:
                continue
            score = math.log1p(freq_value) / math.log1p(max_freq) if max_freq > 0 else 0.0
            scores[word] = max(scores.get(word, 0.0), score)
        return FrequencyLexicon(scores=scores)
    if ranks:
        max_rank = max(ranks)
        for word, _freq_value, rank_value in entries:
            if rank_value is None:
                continue
            score = 1.0 - ((rank_value - 1.0) / (max_rank - 1.0)) if max_rank > 1 else 1.0
            scores[word] = max(scores.get(word, 0.0), score)
        return FrequencyLexicon(scores=scores)
    return FrequencyLexicon(scores=scores)


def build_frequency_provider(lexicon: FrequencyLexicon, *, reducer: str = "avg"):
    def provider(candidate) -> float:
        phrase = getattr(candidate, "source_phrase", "")
        return lexicon.weight_phrase(str(phrase), reducer=reducer)

    return provider


def _read_rows(
    path: Path,
    *,
    delimiter: str,
    encoding: str,
    skip_prefixes: Sequence[str] = (),
) -> Iterable[list[str]]:
    if delimiter.isspace():
        for raw in path.read_text(encoding=encoding, errors="ignore").splitlines():
            line = raw.strip()
            if not line:
                continue
            if _should_skip_line(line, skip_prefixes):
                continue
            yield line.split()
        return
    with path.open(encoding=encoding, errors="ignore", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        for row in reader:
            if not row:
                continue
            first = str(row[0]).strip() if row else ""
            if not first:
                continue
            if _should_skip_line(first, skip_prefixes):
                continue
            yield row


def _read_header(rows: Iterable[list[str]], *, header_starts_with: Optional[str]) -> Optional[list[str]]:
    if header_starts_with is None:
        try:
            return next(rows)
        except StopIteration:
            return None
    target = header_starts_with.lower()
    for row in rows:
        if not row:
            continue
        head = str(row[0]).strip().lower()
        if head == target:
            return row
    return None


def _should_skip_line(line: str, prefixes: Sequence[str]) -> bool:
    for prefix in prefixes:
        if line.startswith(prefix):
            return True
    return False


def _resolve_index(headers: list[str], name: Optional[str], fallback_index: int) -> int:
    if name:
        lowered = [header.lower() for header in headers]
        if name.lower() in lowered:
            return lowered.index(name.lower())
    return fallback_index


def _safe_float(row, index: Optional[int]) -> Optional[float]:
    if index is None:
        return None
    if index >= len(row):
        return None
    try:
        return float(str(row[index]).strip())
    except (TypeError, ValueError):
        return None
