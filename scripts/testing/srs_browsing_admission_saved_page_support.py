from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from html.parser import HTMLParser
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
from typing import Any, Mapping, Sequence
import xml.etree.ElementTree as ET

from lexishift_core.helper.pair_resources import resolve_pair_resources
from lexishift_core.helper.paths import build_helper_paths
from lexishift_core.srs.browsing_identity import build_browsing_target_key


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EN_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]{1,40}")
JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
KANJI_RE = re.compile(r"[\u3400-\u9fff]")
KATAKANA_RE = re.compile(r"[\u30a0-\u30ff]")
STOPWORDS = frozenset(
    {
        "about",
        "above",
        "after",
        "also",
        "among",
        "and",
        "are",
        "as",
        "before",
        "between",
        "but",
        "can",
        "for",
        "from",
        "have",
        "into",
        "its",
        "may",
        "not",
        "of",
        "on",
        "or",
        "other",
        "than",
        "that",
        "the",
        "their",
        "them",
        "they",
        "this",
        "to",
        "which",
        "with",
    }
)


@dataclass(frozen=True)
class SavedDocument:
    document_id: str
    side: str
    path: Path
    source_url: str
    license_note: str
    text: str
    sha256: str
    ruby_pairs: Counter[tuple[str, str]]


@dataclass(frozen=True)
class JmdictCandidate:
    target_lemma: str
    target_reading: str
    source_term: str = ""
    surface: str = ""
    glosses: tuple[str, ...] = ()
    priority_rank: int = 999
    frequency_rank: float = 999999999.0

    @property
    def target_key(self) -> str:
        return build_browsing_target_key(
            target_lemma=self.target_lemma,
            target_reading=self.target_reading,
        )


@dataclass(frozen=True)
class SavedPagePolicy:
    version: str = "saved_page_browsing_en_ja_v1"
    max_count_per_signal: float = 5.0
    max_source_candidates_per_term: int = 2
    max_source_ambiguity_candidates: int = 6
    max_target_surface_candidates: int = 80
    max_signal_rows: int = 240
    min_target_surface_length: int = 2

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "max_count_per_signal": self.max_count_per_signal,
            "max_source_candidates_per_term": self.max_source_candidates_per_term,
            "max_source_ambiguity_candidates": self.max_source_ambiguity_candidates,
            "max_target_surface_candidates": self.max_target_surface_candidates,
            "max_signal_rows": self.max_signal_rows,
            "min_target_surface_length": self.min_target_surface_length,
            "source_mapping": "English page tokens are matched only to exact JMDict glosses.",
            "target_mapping": (
                "Japanese ruby pairs are treated as exact readings; non-ruby surface matches "
                "fall back to JMDict with confidence damped by ambiguity."
            ),
        }


class VisibleTextAndRubyExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.ruby_pairs: Counter[tuple[str, str]] = Counter()
        self._skip_depth = 0
        self._in_ruby = False
        self._ruby_surface: list[str] = []
        self._ruby_reading: list[str] = []
        self._ruby_part = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "ruby":
            self._in_ruby = True
            self._ruby_surface = []
            self._ruby_reading = []
            self._ruby_part = ""
        elif self._in_ruby and tag == "rb":
            self._ruby_part = "rb"
        elif self._in_ruby and tag == "rt":
            self._ruby_part = "rt"
        elif self._in_ruby and tag == "rp":
            self._ruby_part = "rp"
        elif tag in {"br", "p", "div", "section", "li", "tr", "h1", "h2", "h3"}:
            self.text_parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "ruby":
            surface = "".join(self._ruby_surface).strip()
            reading = "".join(self._ruby_reading).strip()
            if surface and reading:
                self.ruby_pairs[(surface, reading)] += 1
            self._in_ruby = False
            self._ruby_part = ""
        elif tag in {"rb", "rt", "rp"}:
            self._ruby_part = ""

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_ruby and self._ruby_part == "rt":
            self._ruby_reading.append(data)
            return
        if self._in_ruby and self._ruby_part == "rp":
            return
        if self._in_ruby and self._ruby_part == "rb":
            self._ruby_surface.append(data)
        self.text_parts.append(data)

    def text(self) -> str:
        return collapse_ws(" ".join(self.text_parts))


def load_saved_documents(manifest: Mapping[str, object]) -> list[SavedDocument]:
    documents = []
    for entry in manifest.get("documents") or []:
        if not isinstance(entry, Mapping):
            continue
        path = PROJECT_ROOT / str(entry.get("path") or "")
        encoding = str(entry.get("encoding") or "utf-8")
        raw = path.read_bytes()
        text = decode_document_text(raw, entry=entry, encoding=encoding)
        documents.append(
            SavedDocument(
                document_id=str(entry.get("document_id") or path.stem),
                side=normalize_side(entry.get("side")),
                path=path,
                source_url=str(entry.get("source_url") or ""),
                license_note=str(entry.get("license_note") or ""),
                text=text,
                sha256=hashlib.sha256(raw).hexdigest(),
                ruby_pairs=extract_ruby_pairs(raw, entry=entry, encoding=encoding),
            )
        )
    return documents


def decode_document_text(raw: bytes, *, entry: Mapping[str, object], encoding: str) -> str:
    text = raw.decode(encoding, errors="replace")
    document_format = str(entry.get("format") or "").lower()
    if document_format == "json":
        payload = json.loads(text)
        fields = entry.get("text_fields") or ()
        values = []
        if isinstance(fields, Sequence) and not isinstance(fields, (str, bytes, bytearray)):
            for field in fields:
                value = payload.get(str(field)) if isinstance(payload, Mapping) else None
                if isinstance(value, str):
                    values.append(value)
        return collapse_ws(" ".join(values))
    if document_format == "html":
        parser = VisibleTextAndRubyExtractor()
        parser.feed(text)
        return parser.text()
    return collapse_ws(text)


def extract_ruby_pairs(
    raw: bytes,
    *,
    entry: Mapping[str, object],
    encoding: str,
) -> Counter[tuple[str, str]]:
    if str(entry.get("format") or "").lower() != "html":
        return Counter()
    parser = VisibleTextAndRubyExtractor()
    parser.feed(raw.decode(encoding, errors="replace"))
    return parser.ruby_pairs


def build_jmdict_indexes(
    jmdict_path: Path,
    *,
    source_terms: set[str],
    target_text: str,
    frequency_db: Path | None,
    policy: SavedPagePolicy,
) -> tuple[
    dict[str, list[JmdictCandidate]],
    dict[str, list[JmdictCandidate]],
    set[tuple[str, str]],
    dict[str, object],
]:
    source_index: dict[str, list[JmdictCandidate]] = defaultdict(list)
    target_index: dict[str, list[JmdictCandidate]] = defaultdict(list)
    exact_pairs: set[tuple[str, str]] = set()
    entry_count = 0
    for event, elem in ET.iterparse(jmdict_path, events=("end",)):
        if elem.tag != "entry":
            continue
        entry_count += 1
        kebs = tuple(text_of(child) for child in elem.findall("./k_ele/keb") if text_of(child))
        rebs = tuple(text_of(child) for child in elem.findall("./r_ele/reb") if text_of(child))
        glosses = tuple(text_of(child) for child in elem.findall("./sense/gloss") if text_of(child))
        priorities = tuple(
            text_of(child)
            for child in elem.findall("./k_ele/ke_pri") + elem.findall("./r_ele/re_pri")
            if text_of(child)
        )
        if rebs:
            for surface in set(kebs + rebs):
                for reading in rebs:
                    exact_pairs.add((surface, reading))
        lemma = kebs[0] if kebs else rebs[0] if rebs else ""
        reading = rebs[0] if rebs else ""
        if not lemma or not reading:
            elem.clear()
            continue
        candidate = JmdictCandidate(
            target_lemma=lemma,
            target_reading=reading,
            glosses=glosses,
            priority_rank=priority_rank(priorities),
        )
        for term in exact_source_terms(glosses).intersection(source_terms):
            source_index[term].append(
                JmdictCandidate(
                    target_lemma=lemma,
                    target_reading=reading,
                    source_term=term,
                    glosses=glosses,
                    priority_rank=priority_rank(priorities),
                )
            )
        for surface in set(kebs + rebs):
            if usable_target_surface(surface, policy=policy) and surface in target_text:
                target_index[surface].append(
                    JmdictCandidate(
                        target_lemma=surface,
                        target_reading=reading,
                        surface=surface,
                        glosses=glosses,
                        priority_rank=candidate.priority_rank,
                    )
                )
        elem.clear()
    candidate_lemmas = {
        candidate.target_lemma
        for rows in tuple(source_index.values()) + tuple(target_index.values())
        for candidate in rows
    }
    frequency_ranks = load_frequency_ranks(frequency_db, candidate_lemmas)
    source_index = apply_frequency_ranks(source_index, frequency_ranks)
    target_index = apply_frequency_ranks(target_index, frequency_ranks)
    for rows in source_index.values():
        rows.sort(key=candidate_sort_key)
    for rows in target_index.values():
        rows.sort(key=candidate_sort_key)
    return (
        dict(source_index),
        dict(target_index),
        exact_pairs,
        {
            "path": str(jmdict_path),
            "entry_count": entry_count,
            "source_lookup_term_count": len(source_index),
            "target_surface_lookup_count": len(target_index),
            "exact_surface_reading_pair_count": len(exact_pairs),
            "frequency_db_used": frequency_db is not None and bool(frequency_ranks),
        },
    )


def collect_source_counts(documents: Sequence[SavedDocument]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for document in documents:
        if document.side == "source":
            counts.update(normalized_source_tokens(document.text))
    return counts


def collect_target_surface_counts(
    documents: Sequence[SavedDocument],
    *,
    target_index: Mapping[str, Sequence[JmdictCandidate]],
    policy: SavedPagePolicy,
) -> Counter[str]:
    counts: Counter[str] = Counter()
    surfaces = sorted(target_index, key=len, reverse=True)
    for document in documents:
        if document.side != "target":
            continue
        occupied_spans: list[tuple[int, int]] = []
        for surface in surfaces:
            if usable_target_surface(surface, policy=policy):
                count, spans = count_free_occurrences(
                    document.text,
                    surface,
                    occupied_spans=occupied_spans,
                )
                if count:
                    counts[surface] += count
                    occupied_spans.extend(spans)
    return counts


def collect_exact_ruby_counts(
    documents: Sequence[SavedDocument],
    *,
    exact_pairs: set[tuple[str, str]],
) -> Counter[tuple[str, str]]:
    counts: Counter[tuple[str, str]] = Counter()
    for document in documents:
        if document.side != "target":
            continue
        for pair, count in document.ruby_pairs.items():
            if pair in exact_pairs:
                counts[pair] += count
    return counts


def normalized_source_tokens(text: str) -> list[str]:
    tokens = []
    for raw in EN_TOKEN_RE.findall(text):
        token = normalize_english_token(raw)
        if token and token not in STOPWORDS and len(token) >= 3:
            tokens.append(token)
    return tokens


def normalize_english_token(value: str) -> str:
    token = value.strip().lower().strip("'")
    if token in {"species"}:
        return token
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def count_free_occurrences(
    text: str,
    surface: str,
    *,
    occupied_spans: Sequence[tuple[int, int]],
) -> tuple[int, list[tuple[int, int]]]:
    spans = []
    start = 0
    while True:
        index = text.find(surface, start)
        if index < 0:
            break
        end = index + len(surface)
        if not any(
            index < occupied_end and end > occupied_start
            for occupied_start, occupied_end in occupied_spans
        ):
            spans.append((index, end))
        start = index + max(1, len(surface))
    return len(spans), spans


def exact_source_terms(glosses: Sequence[str]) -> set[str]:
    terms = set()
    for gloss in glosses:
        normalized = normalize_gloss(gloss)
        if normalized:
            terms.add(normalized)
    return terms


def normalize_gloss(gloss: str) -> str:
    words = [normalize_english_token(token) for token in EN_TOKEN_RE.findall(gloss)]
    words = [word for word in words if word and word not in STOPWORDS]
    if len(words) == 1:
        return words[0]
    return ""


def usable_target_surface(surface: str, *, policy: SavedPagePolicy) -> bool:
    if not surface or len(surface) < policy.min_target_surface_length:
        return False
    if not JAPANESE_RE.search(surface):
        return False
    if KANJI_RE.search(surface):
        return len(surface) >= 2
    if KATAKANA_RE.search(surface):
        return len(surface) >= 3
    return len(surface) >= 4


def priority_rank(priorities: Sequence[str]) -> int:
    if not priorities:
        return 999
    rank = 999
    for priority in priorities:
        match = re.search(r"(\d+)$", priority)
        number = int(match.group(1)) if match else 9
        if priority.startswith(("news", "ichi")):
            rank = min(rank, number)
        elif priority.startswith(("spec", "gai")):
            rank = min(rank, 20 + number)
        else:
            rank = min(rank, 50 + number)
    return rank


def candidate_sort_key(candidate: JmdictCandidate) -> tuple[int, int, int, int, str]:
    frequency_missing = 1 if candidate.frequency_rank >= 999999999.0 else 0
    return (
        frequency_missing,
        int(candidate.frequency_rank),
        candidate.priority_rank,
        len(candidate.target_lemma),
        candidate.target_key,
    )


def apply_frequency_ranks(
    index: Mapping[str, Sequence[JmdictCandidate]],
    ranks: Mapping[str, float],
) -> dict[str, list[JmdictCandidate]]:
    return {
        key: [
            JmdictCandidate(
                target_lemma=candidate.target_lemma,
                target_reading=candidate.target_reading,
                source_term=candidate.source_term,
                surface=candidate.surface,
                glosses=candidate.glosses,
                priority_rank=candidate.priority_rank,
                frequency_rank=float(ranks.get(candidate.target_lemma, candidate.frequency_rank)),
            )
            for candidate in rows
        ]
        for key, rows in index.items()
    }


def load_frequency_ranks(frequency_db: Path | None, lemmas: set[str]) -> dict[str, float]:
    if frequency_db is None or not frequency_db.exists() or not lemmas:
        return {}
    ranks: dict[str, float] = {}
    with sqlite3.connect(str(frequency_db)) as conn:
        for chunk in chunked(sorted(lemmas), 400):
            placeholders = ",".join("?" for _ in chunk)
            query = (
                "select lemma, min(coalesce(core_rank, rank, 999999999.0)) "
                f"from frequency where lemma in ({placeholders}) group by lemma"
            )
            for lemma, rank in conn.execute(query, tuple(chunk)):
                if lemma and rank is not None:
                    ranks[str(lemma)] = float(rank)
    return ranks


def chunked(values: Sequence[str], size: int) -> list[Sequence[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def ambiguity_confidence(candidate_count: int) -> float:
    if candidate_count <= 1:
        return 1.0
    return round(1.0 / math.sqrt(candidate_count), 6)


def document_summary(document: SavedDocument) -> dict[str, object]:
    return {
        "document_id": document.document_id,
        "side": document.side,
        "path": repo_path(document.path),
        "source_url": document.source_url,
        "license_note": document.license_note,
        "sha256": document.sha256,
        "text_char_count": len(document.text),
        "ruby_pair_count": sum(document.ruby_pairs.values()),
        "raw_text_stored": False,
    }


def counter_preview(counter: Counter[str], *, limit: int = 20) -> list[dict[str, object]]:
    return [
        {"value": value, "count": count} for value, count in counter.most_common(limit) if value
    ]


def ruby_preview(documents: Sequence[SavedDocument], *, limit: int = 20) -> list[dict[str, object]]:
    counter: Counter[tuple[str, str]] = Counter()
    for document in documents:
        counter.update(document.ruby_pairs)
    return [
        {"surface": surface, "reading": reading, "count": count}
        for (surface, reading), count in counter.most_common(limit)
    ]


def collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def text_of(element: ET.Element) -> str:
    return str(element.text or "").strip()


def normalize_side(value: object) -> str:
    side = str(value or "").strip().lower()
    return side if side in {"source", "target"} else "source"


def resolve_pair_data_paths(
    *,
    pair: str,
    jmdict_path: Path | None,
    frequency_db: Path | None,
) -> tuple[Path, Path | None]:
    if jmdict_path is not None and frequency_db is not None:
        resolved_jmdict = jmdict_path.expanduser()
        resolved_frequency = frequency_db.expanduser()
        if not resolved_jmdict.exists():
            raise FileNotFoundError(resolved_jmdict)
        if not resolved_frequency.exists():
            raise FileNotFoundError(resolved_frequency)
        return resolved_jmdict, resolved_frequency
    paths = build_helper_paths()
    resolved_jmdict, _translation, resolved_frequency = resolve_pair_resources(
        paths,
        pair=pair,
        jmdict_path=jmdict_path,
        translation_dict_path=None,
        set_source_db=frequency_db,
    )
    if resolved_jmdict is None or not resolved_jmdict.exists():
        raise FileNotFoundError(f"Could not resolve JMDict for {pair}.")
    if resolved_frequency is not None and not resolved_frequency.exists():
        raise FileNotFoundError(resolved_frequency)
    return resolved_jmdict, resolved_frequency


def load_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def repo_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)
