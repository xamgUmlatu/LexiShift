from __future__ import annotations

import copy
from collections import Counter
from dataclasses import is_dataclass, replace
import json
from pathlib import Path
from typing import Mapping, Sequence

from lexishift_core.srs.admission_features import (
    canonicalize_topic_token,
    mapping_or_empty,
    normalize_admission_profile_features,
    normalize_topic_string_list,
    safe_optional_float,
)

PROFILE_TOPIC_OVERLAY_SCHEMA_VERSION = 1
ANIMALS_PLANTS_OVERLAY_PAIR = "en-es"
ANIMALS_PLANTS_OVERLAY_FILENAME = "srs_animals_plants_topic_overlay_en_es_spalex_10k_latest.json"
ANIMALS_PLANTS_OVERLAY_TOPICS = frozenset({"animals", "plants_nature"})
PROFILE_TOPIC_OVERLAY_MIN_MEMBERSHIP = 1.0


def resolve_preview_profile_topic_overlay(
    paths: object,
    *,
    pair: str,
    profile_context: Mapping[str, object] | None,
) -> tuple[Mapping[str, object] | None, dict[str, object]]:
    resolved_pair = str(pair or "").strip()
    active_topics = _active_supported_topics(profile_context)
    base_diagnostics = _base_diagnostics(pair=resolved_pair, active_topics=active_topics)
    if resolved_pair != ANIMALS_PLANTS_OVERLAY_PAIR:
        return None, {}
    if not active_topics:
        return None, {}

    candidate_paths = _candidate_overlay_paths(paths)
    overlay_path = next((path for path in candidate_paths if path.exists()), None)
    if overlay_path is None:
        return None, {
            **base_diagnostics,
            "status": "unavailable",
            "reason": "overlay_artifact_missing",
            "candidate_paths": [str(path) for path in candidate_paths],
        }

    try:
        payload = json.loads(overlay_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, {
            **base_diagnostics,
            "status": "unavailable",
            "reason": "overlay_artifact_unreadable",
            "source_path": str(overlay_path),
            "error": str(exc),
        }
    if not isinstance(payload, Mapping):
        return None, {
            **base_diagnostics,
            "status": "unavailable",
            "reason": "overlay_artifact_invalid",
            "source_path": str(overlay_path),
        }

    overlay_id = str(payload.get("overlay_id") or "").strip()
    if str(payload.get("status") or "").strip() != "ok":
        return None, {
            **base_diagnostics,
            "status": "unavailable",
            "reason": "overlay_artifact_not_ready",
            "source_path": str(overlay_path),
            "overlay_id": overlay_id,
        }

    applicable_rows = _applicable_overlay_rows(
        payload,
        pair=resolved_pair,
        active_topics=active_topics,
    )
    if not applicable_rows:
        return None, {
            **base_diagnostics,
            "status": "unavailable",
            "reason": "overlay_rows_absent_for_requested_topics",
            "source_path": str(overlay_path),
            "overlay_id": overlay_id,
        }

    return payload, {
        **base_diagnostics,
        "status": "active",
        "reason": "overlay_artifact_ready",
        "source_path": str(overlay_path),
        "overlay_id": overlay_id,
        "available_row_count": len(_mapping_rows(payload.get("rows"))),
        "applicable_row_count": len(applicable_rows),
        "applicable_topics": dict(
            sorted(Counter(str(row.get("topic") or "") for row in applicable_rows).items())
        ),
        "promotion_state": str(
            mapping_or_empty(payload.get("overlay_policy")).get("promotion_state")
            or "poc_candidate_not_product_overlay"
        ),
    }


def apply_profile_topic_overlay_to_seeds(
    seeds: Sequence[object],
    *,
    overlay_payload: Mapping[str, object] | None,
    profile_context: Mapping[str, object] | None,
    pair: str,
    diagnostics: Mapping[str, object] | None = None,
) -> tuple[list[object], dict[str, object]]:
    base_diagnostics = dict(diagnostics or {})
    if not overlay_payload:
        return list(seeds), base_diagnostics

    active_topics = _active_supported_topics(profile_context)
    rows = _applicable_overlay_rows(
        overlay_payload,
        pair=str(pair or "").strip(),
        active_topics=active_topics,
    )
    rows_by_lemma = _overlay_rows_by_lemma(rows)
    overlay_id = str(overlay_payload.get("overlay_id") or "").strip()
    applied_rows_by_topic: Counter[str] = Counter()
    matched_seed_count = 0
    applied_seed_count = 0
    next_seeds: list[object] = []
    for seed in seeds:
        lemma = str(getattr(seed, "lemma", "") or "").strip()
        overlay_rows = rows_by_lemma.get(lemma, ())
        if not overlay_rows:
            next_seeds.append(seed)
            continue
        matched_seed_count += 1
        updated_seed, applied_topics = _seed_with_profile_topic_overlay(
            seed,
            overlay_id=overlay_id,
            overlay_rows=overlay_rows,
        )
        if applied_topics:
            applied_seed_count += 1
            applied_rows_by_topic.update(applied_topics)
        next_seeds.append(updated_seed)

    eligible_row_count = sum(
        1
        for row in rows
        if (safe_optional_float(row.get("membership")) or 0.0)
        >= PROFILE_TOPIC_OVERLAY_MIN_MEMBERSHIP
    )
    application_status = "applied"
    if not applied_seed_count:
        application_status = (
            "no_seed_matches" if not matched_seed_count else "no_eligible_rows_applied"
        )
    return next_seeds, {
        **base_diagnostics,
        "schema_version": PROFILE_TOPIC_OVERLAY_SCHEMA_VERSION,
        "application_status": application_status,
        "matched_seed_count": matched_seed_count,
        "eligible_row_count": eligible_row_count,
        "applied_seed_count": applied_seed_count,
        "applied_row_count": sum(applied_rows_by_topic.values()),
        "applied_topics": dict(sorted(applied_rows_by_topic.items())),
        "min_membership": PROFILE_TOPIC_OVERLAY_MIN_MEMBERSHIP,
    }


def _base_diagnostics(*, pair: str, active_topics: Sequence[str]) -> dict[str, object]:
    return {
        "schema_version": PROFILE_TOPIC_OVERLAY_SCHEMA_VERSION,
        "overlay_family": "animals_plants",
        "pair": pair,
        "supported_pair": ANIMALS_PLANTS_OVERLAY_PAIR,
        "supported_topics": sorted(ANIMALS_PLANTS_OVERLAY_TOPICS),
        "active_topics": list(active_topics),
        "runtime_scope": "admission_preview_only",
        "policy_change": "none",
    }


def _active_supported_topics(profile_context: Mapping[str, object] | None) -> tuple[str, ...]:
    normalized_context = normalize_admission_profile_features(profile_context)
    active = [
        canonicalize_topic_token(topic)
        for topic in normalized_context.topic_weights.keys()
        if canonicalize_topic_token(topic) in ANIMALS_PLANTS_OVERLAY_TOPICS
    ]
    return tuple(dict.fromkeys(topic for topic in active if topic))


def _candidate_overlay_paths(paths: object) -> tuple[Path, ...]:
    srs_dir = getattr(paths, "srs_dir", None)
    data_root = getattr(paths, "data_root", None)
    candidates: list[Path] = []
    if srs_dir:
        candidates.append(Path(srs_dir) / "topic_overlays" / ANIMALS_PLANTS_OVERLAY_FILENAME)
    if data_root:
        candidates.append(Path(data_root) / "topic_overlays" / ANIMALS_PLANTS_OVERLAY_FILENAME)
    candidates.append(_repo_root() / "docs" / "test_outputs" / ANIMALS_PLANTS_OVERLAY_FILENAME)
    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return tuple(unique)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _applicable_overlay_rows(
    overlay_payload: Mapping[str, object],
    *,
    pair: str,
    active_topics: Sequence[str],
) -> tuple[Mapping[str, object], ...]:
    active_topic_set = {canonicalize_topic_token(topic) for topic in active_topics if topic}
    applicable: list[Mapping[str, object]] = []
    for row in _mapping_rows(overlay_payload.get("rows")):
        row_pair = str(row.get("language_pair") or "").strip()
        topic = canonicalize_topic_token(row.get("topic"))
        lemma = str(row.get("lemma") or "").strip()
        if row_pair != pair or topic not in active_topic_set or not lemma:
            continue
        applicable.append(row)
    return tuple(applicable)


def _seed_with_profile_topic_overlay(
    seed: object,
    *,
    overlay_id: str,
    overlay_rows: Sequence[Mapping[str, object]],
) -> tuple[object, tuple[str, ...]]:
    metadata = dict(mapping_or_empty(getattr(seed, "metadata", None)))
    profile_topics = set(normalize_topic_string_list(metadata.get("profile_topics")))
    overlay_payload = []
    applied_topics: list[str] = []
    for row in overlay_rows:
        topic = canonicalize_topic_token(row.get("topic"))
        membership = safe_optional_float(row.get("membership")) or 0.0
        if topic and membership >= PROFILE_TOPIC_OVERLAY_MIN_MEMBERSHIP:
            profile_topics.add(topic)
            applied_topics.append(topic)
        overlay_payload.append(
            {
                "topic": topic,
                "membership": round(float(membership), 6),
                "review_id": str(row.get("review_id") or ""),
                "confidence_label": str(row.get("confidence_label") or ""),
            }
        )
    metadata["profile_topics"] = sorted(profile_topics)
    metadata["profile_topic_overlay"] = {
        "overlay_id": overlay_id,
        "rows": overlay_payload,
        "min_membership": PROFILE_TOPIC_OVERLAY_MIN_MEMBERSHIP,
    }
    if is_dataclass(seed):
        return replace(seed, metadata=metadata), tuple(applied_topics)
    if hasattr(seed, "__dict__"):
        copied = copy.copy(seed)
        setattr(copied, "metadata", metadata)
        return copied, tuple(applied_topics)
    return seed, tuple()


def _overlay_rows_by_lemma(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        lemma = str(row.get("lemma") or "").strip()
        if lemma:
            grouped.setdefault(lemma, []).append(row)
    return {lemma: tuple(values) for lemma, values in grouped.items()}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]
