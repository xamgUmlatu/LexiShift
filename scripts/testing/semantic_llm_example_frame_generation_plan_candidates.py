#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Sequence

DEFAULT_SEMANTIC_CANDIDATES_PER_ROW = 5
DEFAULT_HARD_SEMANTIC_CANDIDATES_PER_ROW = 10
DEFAULT_PHRASE_CANDIDATES_PER_ROW = 1

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def candidate_count_for_slot(
    *,
    generation_target: str,
    active_pos: str,
    candidate_pos: str,
    shadow_positions: Sequence[str],
    semantic_candidates_per_row: int,
    hard_semantic_candidates_per_row: int,
    phrase_candidates_per_row: int,
) -> int:
    if generation_target == "phrase_control_example":
        return phrase_candidates_per_row
    if (
        candidate_strategy(
            generation_target=generation_target,
            active_pos=active_pos,
            candidate_pos=candidate_pos,
            shadow_positions=shadow_positions,
        )
        == "same_pos_hard_semantic"
    ):
        return hard_semantic_candidates_per_row
    return semantic_candidates_per_row


def candidate_strategy(
    *,
    generation_target: str,
    active_pos: str,
    candidate_pos: str,
    shadow_positions: Sequence[str],
) -> str:
    if generation_target == "phrase_control_example":
        return "phrase_containment"
    normalized_active_pos = str(active_pos or "").strip().lower()
    normalized_candidate_pos = str(candidate_pos or "").strip().lower()
    if generation_target == "active_example":
        same_pos = any(
            str(shadow_pos or "").strip().lower() == normalized_active_pos
            for shadow_pos in shadow_positions
        )
    else:
        same_pos = bool(normalized_active_pos and normalized_candidate_pos == normalized_active_pos)
    return "same_pos_hard_semantic" if same_pos else "standard_semantic"


def request_id(
    *,
    family_id: str,
    request_kind: str,
    candidate_id: str,
    candidate_index: int,
    candidate_count: int,
) -> str:
    parts = ["en-es", "example-frame-missing", request_kind, slug(family_id)]
    if request_kind == "shadow" and candidate_id:
        parts.append(slug(candidate_id))
    if candidate_count > 1:
        parts.append(f"candidate-{candidate_index:02d}")
    return ":".join(parts)


def expected_row_id(
    *,
    family_id: str,
    request_kind: str,
    candidate_id: str,
    candidate_index: int,
    candidate_count: int,
) -> str:
    parts = [slug(family_id), "llm"]
    if request_kind == "phrase-control":
        parts.extend(["phrase-control", "missing", "v1"])
    elif request_kind == "shadow":
        parts.extend(["shadow", slug(candidate_id), "missing", "v1"])
    else:
        parts.extend(["active", "missing", "v1"])
    if candidate_count > 1:
        parts.append(f"candidate-{candidate_index:02d}")
    return ":".join(parts)


def slug(value: object) -> str:
    text = str(value or "").strip().lower()
    return _SLUG_RE.sub("-", text).strip("-") or "row"
