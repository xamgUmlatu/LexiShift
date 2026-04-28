#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: F401

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    RuntimeSimilarityBackend,
    build_runtime_context_views,
    extract_runtime_phrase_control_signals,
)
from semantic_routing_sentence_veto_helpers import (  # noqa: E402
    _accumulate_sentence_veto_summary,
    _append_sample,
    _finalize_sentence_veto_breakdown_rows,
    _finalize_sentence_veto_summary,
    _new_sentence_veto_summary,
    _normalize_slice_dimensions,
    _normalize_string_list,
)
from semantic_routing_sentence_veto_support import (  # noqa: E402
    _resolve_sentence_veto_phrase_guard_pos_tags,
    load_sentence_veto_dataset,
)

DEFAULT_MANIFEST = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_decision_rule_matrix_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_decision_rule_matrix_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_decision_rule_matrix_en_es_latest.md"
)
DEFAULT_DATASET = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing_cases"
    / "en_es_sentence_veto_v10.json"
)

SUPPORTED_AGGREGATION_RULES = {
    "single_concatenated_text",
    "max_row_score",
    "mean_row_score",
    "top_k_mean",
    "source_weighted_top_k",
    "definition_example_agreement",
    "context_selected_max_row_score",
    "context_selected_top_k_mean",
    "context_selected_source_weighted_top_k",
}
SUPPORTED_DECISION_RULES = {
    "active_minus_strongest_shadow",
    "active_ratio_strongest_shadow",
    "softmax_probability",
    "pairwise_active_beats_all_shadows",
    "pairwise_active_beats_most_shadows",
    "shadow_veto_only",
}
SUPPORTED_EVIDENCE_CONTROLS = {
    "normal",
    "active_only_source",
    "shadow_only_source",
    "no_shadow_competition",
    "shuffled_labels",
    "target_lemma_only",
}
SUPPORTED_PHRASE_HANDLING = {
    "semantic_only",
    "phrase_first",
    "phrase_override",
    "phrase_as_shadow",
}

DEFAULT_SOURCE_WEIGHTS = {
    "all_evidence": 1.0,
    "sense_label": 0.8,
    "definition": 1.0,
    "qualifier": 0.6,
    "auxiliary": 0.5,
    "target_lemma": 0.25,
    "installed_translation_pack": 0.8,
    "wordnet_example_frames": 1.0,
    "wiktextract_example_frames": 1.0,
    "source_row": 1.0,
    "empty": 0.0,
}
_EXPERIMENT_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ']+|___")
_DETERMINERS = frozenset(
    {
        "a",
        "an",
        "her",
        "his",
        "its",
        "my",
        "our",
        "that",
        "the",
        "their",
        "these",
        "this",
        "those",
        "your",
    }
)
_PREPOSITIONS = frozenset(
    {
        "about",
        "after",
        "at",
        "before",
        "beside",
        "by",
        "during",
        "for",
        "from",
        "in",
        "into",
        "near",
        "of",
        "off",
        "on",
        "out",
        "over",
        "past",
        "through",
        "to",
        "toward",
        "under",
        "up",
        "with",
        "within",
        "without",
    }
)
_MODALS = frozenset(
    {"can", "cannot", "can't", "could", "may", "might", "must", "shall", "should", "will", "would"}
)
_NEGATIONS = frozenset({"no", "not", "never", "n't", "without"})
_BE_VERBS = frozenset({"am", "are", "be", "been", "being", "is", "was", "were"})
_AUXILIARY_VERBS = frozenset(
    {
        "am",
        "are",
        "be",
        "been",
        "being",
        "did",
        "do",
        "does",
        "had",
        "has",
        "have",
        "is",
        "was",
        "were",
    }
)
_PRONOUNS = frozenset(
    {"he", "her", "him", "i", "it", "me", "she", "them", "they", "us", "we", "you"}
)
_PARTICLES = frozenset({"away", "back", "down", "in", "off", "on", "out", "over", "through", "up"})


@dataclass(frozen=True)
class EvidenceRow:
    row_id: str
    source_family: str
    text: str
    weight: float
    selector_text: str = ""


@dataclass(frozen=True)
class SenseScore:
    sense_id: str
    target_lemma: str
    winner_type: str
    aggregate_score: float
    row_scores: tuple[dict[str, object], ...]


def _round_float(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isinf(number):
        return number
    return round(number, 6)


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def _resolve_project_path(value: object, *, default: Path) -> Path:
    raw = str(value or "").strip()
    if not raw:
        return default
    path = Path(raw)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _case_id_signature(case_ids: Sequence[str]) -> str:
    normalized = "\n".join(
        sorted(str(case_id or "").strip() for case_id in case_ids if str(case_id or "").strip())
    )
    return _text_sha256(normalized)[:16]


def _normalize_ints(value: object, *, default: Sequence[int]) -> list[int]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return list(default)
    normalized: list[int] = []
    for item in value:
        try:
            normalized.append(int(item))
        except (TypeError, ValueError):
            continue
    return normalized or list(default)


__all__ = [name for name in globals() if not name.startswith("__")]
