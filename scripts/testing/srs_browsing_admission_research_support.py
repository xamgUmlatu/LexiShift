from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
import re
import unicodedata
from typing import Mapping, Sequence


DOCUMENT_SIDES = {"source", "target", "mixed"}
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ'-]{1,40}")
MIN_TOKEN_LENGTH = 3

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "after",
    "before",
    "again",
    "while",
    "into",
    "over",
    "under",
    "about",
    "they",
    "their",
    "there",
    "will",
    "would",
    "could",
    "should",
    "have",
    "has",
    "had",
    "was",
    "were",
    "are",
    "not",
    "but",
    "you",
    "your",
    "del",
    "las",
    "los",
    "una",
    "uno",
    "para",
    "con",
    "por",
    "que",
    "como",
    "este",
    "esta",
    "estos",
    "estas",
}


@dataclass(frozen=True)
class BrowsingAdmissionPolicy:
    version: str = "browsing_admission_research_v1"
    max_unique_tokens_per_document: int = 160
    max_count_per_token_per_document: int = 3
    browsing_signal_cap: float = 16.0
    browsing_alpha: float = 0.25
    max_browsing_boost: float = 1.35
    replacement_exposure_weight: float = 0.35
    ambiguity_confidence_exponent: float = 0.5
    min_token_length: int = MIN_TOKEN_LENGTH

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "max_unique_tokens_per_document": self.max_unique_tokens_per_document,
            "max_count_per_token_per_document": self.max_count_per_token_per_document,
            "browsing_signal_cap": self.browsing_signal_cap,
            "browsing_alpha": self.browsing_alpha,
            "max_browsing_boost": self.max_browsing_boost,
            "replacement_exposure_weight": self.replacement_exposure_weight,
            "ambiguity_confidence_exponent": self.ambiguity_confidence_exponent,
            "min_token_length": self.min_token_length,
            "normalization": [
                "lowercase",
                "unicode_nfkc",
                "accent_folded_lookup_aliases",
                "simple_english_suffix_variants",
                "simple_spanish_plural_variants",
            ],
            "privacy_posture": [
                "read_only_research_harness",
                "no_raw_text_in_artifact",
                "no_url_input_or_storage",
                "no_runtime_mutation",
            ],
        }


@dataclass(frozen=True)
class TextDocument:
    document_id: str
    text: str
    source_path: str = ""
    side: str = "source"


@dataclass(frozen=True)
class BrowsingSignal:
    lemma: str
    source_weighted_count: float = 0.0
    target_hit_count: float = 0.0
    replacement_exposure_count: float = 0.0
    source_terms: tuple[str, ...] = ()
    target_terms: tuple[str, ...] = ()
    ambiguous_source_terms: tuple[str, ...] = ()
    mapping_confidence_max: float = 0.0


def build_bridge_indexes(
    payload: Mapping[str, object],
    *,
    policy: BrowsingAdmissionPolicy,
) -> tuple[
    dict[str, tuple[dict[str, object], ...]],
    dict[str, tuple[str, ...]],
    dict[str, object],
]:
    by_source: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    target_terms: dict[str, set[str]] = defaultdict(set)
    raw_source_count = 0
    raw_pair_count = 0
    for row in mapping_rows(payload.get("full_source_target_pairs")):
        source = str(row.get("source") or "").strip()
        target = str(row.get("target") or "").strip()
        if not source or not target:
            continue
        raw_pair_count += 1
        source_keys = source_lookup_keys(source)
        target_keys = target_lookup_keys(target)
        if not source_keys or not target_keys:
            continue
        for target_key in target_keys:
            target_terms[target_key].add(target)
        for source_key in source_keys:
            by_source[source_key][target] = {
                "target": target,
                "source": source,
                "target_zipf_frequency_es": safe_float(row.get("target_zipf_frequency_es")),
                "source_zipf_frequency_en": safe_float(row.get("source_zipf_frequency_en")),
            }
    source_index: dict[str, tuple[dict[str, object], ...]] = {}
    ambiguous_source_terms = 0
    max_targets_per_source = 0
    for source_key, rows_by_target in by_source.items():
        raw_source_count += 1
        rows = sorted(
            rows_by_target.values(),
            key=lambda item: (
                -(safe_float(item.get("target_zipf_frequency_es")) or 0.0),
                str(item.get("target") or ""),
            ),
        )
        target_count = len(rows)
        if target_count > 1:
            ambiguous_source_terms += 1
        max_targets_per_source = max(max_targets_per_source, target_count)
        confidence = 1.0 / (target_count**policy.ambiguity_confidence_exponent)
        source_index[source_key] = tuple({**row, "mapping_confidence": confidence} for row in rows)
    target_index = {key: tuple(sorted(values)) for key, values in target_terms.items()}
    summary = {
        "raw_pair_count": raw_pair_count,
        "source_lookup_key_count": raw_source_count,
        "target_lookup_key_count": len(target_index),
        "ambiguous_source_lookup_key_count": ambiguous_source_terms,
        "max_targets_per_source_lookup_key": max_targets_per_source,
        "ambiguity_policy": "1 / target_count ** ambiguity_confidence_exponent",
    }
    return source_index, target_index, summary


def extract_document_signals(
    documents: Sequence[TextDocument],
    *,
    source_index: Mapping[str, Sequence[Mapping[str, object]]],
    target_index: Mapping[str, Sequence[str]],
    policy: BrowsingAdmissionPolicy,
) -> dict[str, object]:
    source_counts: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    unmapped_counts: Counter[str] = Counter()
    document_summaries: list[dict[str, object]] = []
    for document in documents:
        document_side = normalize_document_side(document.side)
        raw_tokens = tokenize(document.text)
        filtered = [token for token in raw_tokens if usable_token(token, policy=policy)]
        capped_counts = cap_document_counts(filtered, policy=policy)
        source_hits = Counter()
        target_hits = Counter()
        unmapped_hits = Counter()
        for token, count in capped_counts.items():
            source_key = (
                first_lookup_hit(source_variants(token), source_index)
                if document_side in {"source", "mixed"}
                else ""
            )
            if source_key:
                source_counts[source_key] += count
                source_hits[source_key] += count
            target_key = (
                first_lookup_hit(target_variants(token), target_index)
                if document_side in {"target", "mixed"}
                else ""
            )
            if target_key:
                target_counts[target_key] += count
                target_hits[target_key] += count
            if not source_key and not target_key:
                unmapped_counts[token] += count
                unmapped_hits[token] += count
        document_summaries.append(
            {
                "document_id": document.document_id,
                "side": document_side,
                "raw_token_count": len(raw_tokens),
                "usable_token_count": len(filtered),
                "capped_unique_token_count": len(capped_counts),
                "source_lookup_hit_count": sum(source_hits.values()),
                "target_lookup_hit_count": sum(target_hits.values()),
                "unmapped_token_count": sum(unmapped_hits.values()),
                "top_source_lookup_hits": counter_preview(source_hits),
                "top_target_lookup_hits": counter_preview(target_hits),
                "top_unmapped_tokens": counter_preview(unmapped_hits),
                "raw_text_stored": False,
            }
        )
    return {
        "source_token_counts": source_counts,
        "target_token_counts": target_counts,
        "summary": {
            "document_count": len(documents),
            "source_lookup_hit_count": sum(source_counts.values()),
            "target_lookup_hit_count": sum(target_counts.values()),
            "source_lookup_unique_count": len(source_counts),
            "target_lookup_unique_count": len(target_counts),
            "unmapped_token_count": sum(unmapped_counts.values()),
            "unmapped_unique_count": len(unmapped_counts),
            "top_source_lookup_hits": counter_preview(source_counts, limit=20),
            "top_target_lookup_hits": counter_preview(target_counts, limit=20),
            "top_unmapped_tokens": counter_preview(unmapped_counts, limit=20),
            "documents": document_summaries,
        },
    }


def compute_browsing_signals(
    source_counts: Mapping[str, int],
    target_counts: Mapping[str, int],
    *,
    source_index: Mapping[str, Sequence[Mapping[str, object]]],
    target_index: Mapping[str, Sequence[str]],
    policy: BrowsingAdmissionPolicy,
) -> dict[str, BrowsingSignal]:
    mutable: dict[str, dict[str, object]] = {}
    for source_key, count in source_counts.items():
        rows = source_index.get(source_key, ())
        ambiguous = len({str(row.get("target") or "") for row in rows if row.get("target")}) > 1
        for row in rows:
            lemma = str(row.get("target") or "").strip()
            if not lemma:
                continue
            confidence = safe_float(row.get("mapping_confidence")) or 0.0
            entry = mutable.setdefault(
                lemma,
                {
                    "source_weighted_count": 0.0,
                    "target_hit_count": 0.0,
                    "replacement_exposure_count": 0.0,
                    "source_terms": set(),
                    "target_terms": set(),
                    "ambiguous_source_terms": set(),
                    "mapping_confidence_max": 0.0,
                },
            )
            entry["source_weighted_count"] = float(entry["source_weighted_count"]) + (
                count * confidence
            )
            cast_set(entry["source_terms"]).add(source_key)
            if ambiguous:
                cast_set(entry["ambiguous_source_terms"]).add(source_key)
            entry["mapping_confidence_max"] = max(
                float(entry["mapping_confidence_max"]), confidence
            )
    for target_key, count in target_counts.items():
        for lemma in target_index.get(target_key, ()):
            entry = mutable.setdefault(
                lemma,
                {
                    "source_weighted_count": 0.0,
                    "target_hit_count": 0.0,
                    "replacement_exposure_count": 0.0,
                    "source_terms": set(),
                    "target_terms": set(),
                    "ambiguous_source_terms": set(),
                    "mapping_confidence_max": 0.0,
                },
            )
            entry["target_hit_count"] = float(entry["target_hit_count"]) + count
            cast_set(entry["target_terms"]).add(target_key)

    return {
        lemma: BrowsingSignal(
            lemma=lemma,
            source_weighted_count=float(entry["source_weighted_count"]),
            target_hit_count=float(entry["target_hit_count"]),
            replacement_exposure_count=float(entry["replacement_exposure_count"]),
            source_terms=tuple(sorted(cast_set(entry["source_terms"]))),
            target_terms=tuple(sorted(cast_set(entry["target_terms"]))),
            ambiguous_source_terms=tuple(sorted(cast_set(entry["ambiguous_source_terms"]))),
            mapping_confidence_max=float(entry["mapping_confidence_max"]),
        )
        for lemma, entry in sorted(mutable.items())
    }


def public_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    public = []
    for row in rows:
        public.append(
            {
                "lemma": row.get("lemma"),
                "neutral_rank": row.get("neutral_rank"),
                "browsing_rank": row.get("browsing_rank"),
                "rank_delta": row.get("rank_delta"),
                "neutral_score": rounded(row.get("neutral_score")),
                "browsing_score": rounded(row.get("browsing_score")),
                "browsing_signal": rounded(row.get("browsing_signal")),
                "browsing_boost": rounded(row.get("browsing_boost")),
                "readiness_multiplier": rounded(row.get("readiness_multiplier")),
                "difficulty_estimate": rounded(row.get("difficulty_estimate")),
                "admission_weight": rounded(row.get("admission_weight")),
                "source_terms": row.get("source_terms") or [],
                "target_terms": row.get("target_terms") or [],
                "ambiguous_source_terms": row.get("ambiguous_source_terms") or [],
            }
        )
    return public


def summarize_browsing_signals(
    browsing_by_lemma: Mapping[str, BrowsingSignal],
    *,
    policy: BrowsingAdmissionPolicy,
) -> dict[str, object]:
    rows = [
        {
            "lemma": signal.lemma,
            "source_weighted_count": rounded(signal.source_weighted_count),
            "target_hit_count": rounded(signal.target_hit_count),
            "raw_browsing": rounded(raw_browsing_value(signal, policy=policy)),
            "browsing_signal": rounded(browsing_signal_value(signal, policy=policy)),
            "browsing_boost": rounded(
                browsing_boost_value(browsing_signal_value(signal, policy=policy), policy=policy)
            ),
            "source_terms": list(signal.source_terms),
            "target_terms": list(signal.target_terms),
            "ambiguous_source_terms": list(signal.ambiguous_source_terms),
            "mapping_confidence_max": rounded(signal.mapping_confidence_max),
        }
        for signal in browsing_by_lemma.values()
    ]
    rows.sort(
        key=lambda row: (
            -float(row["browsing_signal"] or 0.0),
            str(row["lemma"]),
        )
    )
    return {
        "boosted_lemma_count": len(rows),
        "ambiguous_boosted_lemma_count": sum(1 for row in rows if row["ambiguous_source_terms"]),
        "top_boosted_lemmas": rows[:30],
    }


def build_research_findings(
    *,
    extraction_summary: Mapping[str, object],
    signal_summary: Mapping[str, object],
    admission_delta: Mapping[str, object],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    unmapped_count = int(safe_float(extraction_summary.get("unmapped_token_count")) or 0)
    if unmapped_count:
        findings.append(
            {
                "severity": "info",
                "finding": "unmapped_browsing_tokens_present",
                "detail": (
                    "Some usable page tokens had no source/target lookup hit; inspect "
                    "top_unmapped_tokens before treating source coverage as complete."
                ),
                "count": unmapped_count,
            }
        )
    boosted_count = int(safe_float(signal_summary.get("boosted_lemma_count")) or 0)
    ambiguous_count = int(safe_float(signal_summary.get("ambiguous_boosted_lemma_count")) or 0)
    if boosted_count and ambiguous_count / boosted_count >= 0.5:
        findings.append(
            {
                "severity": "review",
                "finding": "source_target_ambiguity_is_material",
                "detail": (
                    "At least half of boosted lemmas came from ambiguous source mappings; "
                    "production scoring should keep confidence damping and review LP-specific "
                    "minimum confidence thresholds."
                ),
                "ambiguous_boosted_share": rounded(ambiguous_count / boosted_count),
            }
        )
    moved_up = mapping_rows(admission_delta.get("moved_up"))
    if moved_up:
        largest_delta = max(int(safe_float(row.get("rank_delta")) or 0) for row in moved_up)
        if largest_delta >= 100:
            findings.append(
                {
                    "severity": "review",
                    "finding": "ranked_preview_is_sensitive_to_small_boosts",
                    "detail": (
                        "The ranked top-N preview can move clustered candidates sharply; "
                        "production admission should validate realized sampling share, not only "
                        "rank movement."
                    ),
                    "largest_rank_delta": largest_delta,
                }
            )
    return findings


def raw_browsing_value(signal: BrowsingSignal | None, *, policy: BrowsingAdmissionPolicy) -> float:
    if signal is None:
        return 0.0
    return (
        max(0.0, signal.source_weighted_count)
        + max(0.0, signal.target_hit_count)
        + max(0.0, signal.replacement_exposure_count) * policy.replacement_exposure_weight
    )


def browsing_signal_value(
    signal: BrowsingSignal | None,
    *,
    policy: BrowsingAdmissionPolicy,
) -> float:
    raw = raw_browsing_value(signal, policy=policy)
    if raw <= 0.0:
        return 0.0
    return clamp01(math.log1p(raw) / math.log1p(max(0.01, policy.browsing_signal_cap)))


def browsing_boost_value(signal_value: float, *, policy: BrowsingAdmissionPolicy) -> float:
    return 1.0 + min(
        max(0.0, policy.max_browsing_boost - 1.0),
        max(0.0, policy.browsing_alpha) * clamp01(signal_value),
    )


def tokenize(text: str) -> list[str]:
    return [normalize_token(match.group(0)) for match in TOKEN_RE.finditer(text or "")]


def usable_token(token: str, *, policy: BrowsingAdmissionPolicy) -> bool:
    normalized = normalize_token(token)
    if len(normalized) < policy.min_token_length:
        return False
    if normalized in STOPWORDS:
        return False
    return any(char.isalpha() for char in normalized)


def cap_document_counts(tokens: Sequence[str], *, policy: BrowsingAdmissionPolicy) -> Counter[str]:
    raw = Counter(tokens)
    capped = Counter()
    for token, count in raw.most_common(max(1, policy.max_unique_tokens_per_document)):
        capped[token] = min(max(1, policy.max_count_per_token_per_document), count)
    return capped


def source_lookup_keys(value: str) -> tuple[str, ...]:
    keys: list[str] = []
    for variant in source_variants(value):
        add_unique(keys, variant)
    return tuple(keys)


def target_lookup_keys(value: str) -> tuple[str, ...]:
    keys: list[str] = []
    for variant in target_variants(value):
        add_unique(keys, variant)
    return tuple(keys)


def source_variants(value: str) -> tuple[str, ...]:
    token = normalize_token(value)
    variants = [token, accent_fold(token)]
    if token.endswith("'s"):
        variants.append(token[:-2])
    if len(token) > 4 and token.endswith("ies"):
        variants.append(token[:-3] + "y")
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us")):
        variants.append(token[:-1])
    if (
        len(token) > 4
        and token.endswith("es")
        and (token.endswith(("ches", "shes", "sses", "xes", "zes")) or token.endswith("oes"))
    ):
        variants.append(token[:-2])
    if len(token) > 4 and token.endswith("ing"):
        stem = token[:-3]
        variants.extend([stem, stem + "e"])
    if len(token) > 4 and token.endswith("ed"):
        stem = token[:-2]
        variants.extend([stem, stem + "e"])
    return tuple(dict.fromkeys(variant for variant in variants if variant))


def target_variants(value: str) -> tuple[str, ...]:
    token = normalize_token(value)
    variants = [token, accent_fold(token)]
    if len(token) > 4 and token.endswith("es"):
        variants.append(token[:-2])
    if len(token) > 3 and token.endswith("s"):
        variants.append(token[:-1])
    return tuple(dict.fromkeys(variant for variant in variants if variant))


def normalize_token(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().lower()
    text = text.strip(" \t\r\n\"'“”‘’.,;:!?()[]{}<>/\\|*_+=~`")
    return text


def accent_fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def first_lookup_hit(
    variants: Sequence[str],
    lookup: Mapping[str, object],
) -> str:
    for variant in variants:
        if variant in lookup:
            return variant
    return ""


def counter_preview(counter: Mapping[str, int], *, limit: int = 12) -> list[dict[str, object]]:
    return [
        {"token": key, "count": value}
        for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None


def clamp01(value: object) -> float:
    parsed = safe_float(value)
    if parsed is None:
        return 0.0
    return max(0.0, min(1.0, parsed))


def rounded(value: object, digits: int = 4) -> float | None:
    parsed = safe_float(value)
    if parsed is None:
        return None
    return round(parsed, digits)


def add_unique(target: list[str], value: str) -> None:
    if value and value not in target:
        target.append(value)


def cast_set(value: object) -> set[str]:
    return value if isinstance(value, set) else set()


def normalize_document_side(value: object) -> str:
    side = str(value or "").strip().lower()
    return side if side in DOCUMENT_SIDES else "source"
