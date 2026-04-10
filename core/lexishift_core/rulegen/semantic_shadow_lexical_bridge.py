from __future__ import annotations

import re
from typing import Mapping, Sequence

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.pairs.en_es_support import collect_sanitized_gloss_records
from lexishift_core.rulegen.utils import sanitize_dictionary_gloss

DEFAULT_SEMANTIC_BRIDGE_MAX_MARKER_FREQ = 3
DEFAULT_SEMANTIC_BRIDGE_SCORE_MIN = 1.5
BRIDGE_MARKER_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "used",
        "what",
        "which",
        "with",
    }
)
BRIDGE_CATEGORY_PREFIX_RE = re.compile(r"^[a-z]{2,3}:(.+)$", re.IGNORECASE)


def build_target_bridge_profiles(
    *,
    benchmark_targets: Sequence[object],
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    reverse_records_by_source: Mapping[str, Sequence[TranslationGlossRecord]],
    target_reverse_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]] | None = None,
) -> dict[str, dict[str, object]]:
    profiles: dict[str, dict[str, object]] = {}
    for benchmark_target in benchmark_targets:
        target = str(getattr(benchmark_target, "target", "") or "").strip()
        if not target:
            continue
        reviewed_triggers = tuple(
            str(trigger).strip()
            for trigger in (getattr(benchmark_target, "reviewed_triggers", ()) or ())
            if str(trigger).strip()
        )
        forward_records = collect_sanitized_gloss_records(forward_records_by_target.get(target, ()))
        markers: set[str] = set()
        canonical_pos_values: list[str] = []
        for record in forward_records:
            canonical_pos = _build_canonical_pos(record)
            if canonical_pos:
                canonical_pos_values.append(canonical_pos)
            markers.update(extract_bridge_markers_from_text(str(record.translation or "")))
            metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
            markers.update(extract_bridge_markers_from_metadata(metadata))
        direct_reverse_records = ()
        if target_reverse_records_by_target is not None:
            direct_reverse_records = collect_sanitized_gloss_records(
                target_reverse_records_by_target.get(target, ())
            )
        if direct_reverse_records:
            for record in direct_reverse_records:
                markers.update(extract_bridge_markers_from_text(str(record.translation or "")))
                metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
                markers.update(extract_bridge_markers_from_metadata(metadata))
        else:
            for trigger in reviewed_triggers:
                markers.update(extract_bridge_markers_from_text(trigger))
                for record in collect_sanitized_gloss_records(
                    reverse_records_by_source.get(trigger, ())
                ):
                    markers.update(extract_bridge_markers_from_text(str(record.translation or "")))
                    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
                    markers.update(extract_bridge_markers_from_metadata(metadata))
        primary_pos = next((value for value in canonical_pos_values if value), "")
        profiles[target] = {
            "target": target,
            "primary_pos": primary_pos,
            "bridge_markers": tuple(sorted(markers)),
        }
    return profiles


def build_bridge_marker_frequency(
    profiles: Mapping[str, Mapping[str, object]],
) -> dict[str, int]:
    frequency: dict[str, int] = {}
    for profile in profiles.values():
        markers = profile.get("bridge_markers")
        if not isinstance(markers, Sequence) or isinstance(markers, (str, bytes)):
            continue
        for marker in {str(item).strip() for item in markers if str(item).strip()}:
            frequency[marker] = frequency.get(marker, 0) + 1
    return frequency


def build_semantic_bridge_candidates(
    *,
    active_target: str,
    active_candidates: Sequence[Mapping[str, object]],
    existing_shadow_targets: set[str],
    benchmark_target_map: Mapping[str, object],
    target_bridge_profiles: Mapping[str, Mapping[str, object]],
    bridge_marker_frequency: Mapping[str, int],
) -> list[dict[str, object]]:
    active_profile = target_bridge_profiles.get(active_target)
    if not isinstance(active_profile, Mapping):
        return []
    active_markers = {
        str(marker).strip()
        for marker in active_profile.get("bridge_markers", ())
        if str(marker).strip()
    }
    if not active_markers:
        return []
    active_pos_values = {
        str(candidate.get("canonical_pos") or "").strip().lower()
        for candidate in active_candidates
        if str(candidate.get("canonical_pos") or "").strip()
    }
    if not active_pos_values:
        active_profile_pos = str(active_profile.get("primary_pos") or "").strip().lower()
        if active_profile_pos:
            active_pos_values.add(active_profile_pos)
    ranked: list[tuple[tuple[float, str], dict[str, object]]] = []
    for candidate_target, profile in target_bridge_profiles.items():
        normalized_target = str(candidate_target or "").strip()
        if (
            not normalized_target
            or normalized_target == active_target
            or normalized_target in existing_shadow_targets
            or normalized_target not in benchmark_target_map
        ):
            continue
        candidate_markers = {
            str(marker).strip()
            for marker in profile.get("bridge_markers", ())
            if str(marker).strip()
        }
        if not candidate_markers:
            continue
        shared_markers = sorted(
            marker
            for marker in active_markers & candidate_markers
            if int(bridge_marker_frequency.get(marker, 0))
            <= DEFAULT_SEMANTIC_BRIDGE_MAX_MARKER_FREQ
        )
        if not shared_markers:
            continue
        candidate_pos = str(profile.get("primary_pos") or "").strip().lower()
        if active_pos_values and candidate_pos and candidate_pos not in active_pos_values:
            continue
        bridge_score = sum(
            1.0 / max(1, int(bridge_marker_frequency.get(marker, 1))) for marker in shared_markers
        )
        if bridge_score < DEFAULT_SEMANTIC_BRIDGE_SCORE_MIN:
            continue
        ranked.append(
            (
                (-bridge_score, normalized_target),
                {
                    "target": normalized_target,
                    "sense_label": f"semantic bridge via {', '.join(shared_markers[:3])}",
                    "canonical_pos": candidate_pos,
                    "provider": "semantic_bridge",
                    "locator": {
                        "provider": "semantic_bridge",
                        "locator_kind": "target_profile",
                        "target_key": normalized_target,
                    },
                    "glosses": list(shared_markers[:3]),
                    "qualifiers": None,
                    "candidate_sources": ["semantic_bridge"],
                    "benchmark_target_present": True,
                    "reviewed_trigger_support": False,
                    "semantic_bridge_markers": list(shared_markers),
                    "semantic_bridge_score": bridge_score,
                },
            )
        )
    ranked.sort()
    return [candidate for _score, candidate in ranked]


def extract_bridge_markers_from_metadata(metadata: Mapping[str, object]) -> set[str]:
    markers: set[str] = set()
    for key in ("sense_raw_glosses", "sense_topics", "topics"):
        value = metadata.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                markers.update(extract_bridge_markers_from_text(item))
        else:
            markers.update(extract_bridge_markers_from_text(value))
    for key in ("sense_categories", "entry_categories", "categories"):
        value = metadata.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                markers.update(extract_bridge_markers_from_category(item))
        else:
            markers.update(extract_bridge_markers_from_category(value))
    return markers


def extract_bridge_markers_from_category(value: object) -> set[str]:
    text = str(value or "").strip()
    if not text:
        return set()
    match = BRIDGE_CATEGORY_PREFIX_RE.match(text)
    if not match:
        return set()
    return extract_bridge_markers_from_text(match.group(1))


def extract_bridge_markers_from_text(value: object) -> set[str]:
    normalized = sanitize_dictionary_gloss(value).lower()
    if not normalized:
        return set()
    markers: set[str] = set()
    for token in re.findall(r"[a-z][a-z0-9-]*", normalized):
        if token in BRIDGE_MARKER_STOPWORDS:
            continue
        if len(token) <= 2:
            continue
        markers.add(token)
    return markers


def _build_canonical_pos(record: TranslationGlossRecord) -> str:
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    candidate = str(metadata.get("dictionary_pos_canonical") or "").strip().lower()
    if candidate:
        return candidate
    return str(record.pos_raw or "").strip().lower()
