from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.pairs.en_es_support import (
    collect_sanitized_gloss_records as collect_en_es_sanitized_gloss_records,
    normalize_reverse_token_with_pos,
)

DEFAULT_TRIGGER_SUPPORT_SCORE_MIN = 4.0
TRIGGER_SUPPORT_SCORE_WEIGHTS = {
    "rulegen_top3_source": 2.0,
    "rulegen_all_source": 1.0,
    "forward_gloss_fragment": 1.0,
    "multi_source_support": 1.0,
    "active_side_support": 1.0,
    "reverse_shadow_support": 1.0,
    "multi_word_penalty": -1.0,
}


def resolve_trigger_support_score_weights(
    overrides: Mapping[str, object] | None = None,
) -> dict[str, float]:
    resolved = {key: float(value) for key, value in TRIGGER_SUPPORT_SCORE_WEIGHTS.items()}
    if overrides is None:
        return resolved
    unknown_keys = sorted(
        str(key or "").strip()
        for key in overrides.keys()
        if str(key or "").strip() and str(key or "").strip() not in resolved
    )
    if unknown_keys:
        raise ValueError(
            "Unsupported trigger support score weight override(s): "
            f"{unknown_keys!r}; expected keys drawn from "
            f"{sorted(resolved.keys())!r}"
        )
    for key, value in overrides.items():
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        resolved[normalized_key] = float(value)
    return resolved


def _normalize_shadow_text(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def build_trigger_support_details_from_records(
    *,
    target: str,
    trigger: str,
    source_labels: Sequence[str],
    forward_records: Sequence[TranslationGlossRecord],
    reverse_records: Sequence[TranslationGlossRecord],
    benchmark_target_keys: Sequence[str],
    score_weights: Mapping[str, object] | None = None,
) -> dict[str, object]:
    resolved_weights = resolve_trigger_support_score_weights(score_weights)
    normalized_target = str(target or "").strip()
    normalized_trigger = _normalize_shadow_text(trigger)
    label_set = {str(label or "").strip() for label in source_labels if str(label or "").strip()}
    benchmark_key_set = {
        _normalize_shadow_text(value) for value in benchmark_target_keys if str(value or "").strip()
    }
    active_candidate_count = _count_active_side_matches(
        trigger=normalized_trigger,
        records=forward_records,
    )
    reverse_shadow_targets = _collect_reverse_shadow_targets(
        target=normalized_target,
        records=reverse_records,
        benchmark_target_keys=benchmark_key_set,
    )
    word_count = len([token for token in normalized_trigger.split(" ") if token])
    source_family_count = sum(
        1
        for label in (
            "rulegen_top3_sources",
            "rulegen_all_sources",
            "forward_gloss_fragments",
        )
        if label in label_set
    )
    score_breakdown = {
        "rulegen_top3_source": (
            resolved_weights["rulegen_top3_source"] if "rulegen_top3_sources" in label_set else 0.0
        ),
        "rulegen_all_source": (
            resolved_weights["rulegen_all_source"]
            if ("rulegen_all_sources" in label_set and "rulegen_top3_sources" not in label_set)
            else 0.0
        ),
        "forward_gloss_fragment": (
            resolved_weights["forward_gloss_fragment"]
            if "forward_gloss_fragments" in label_set
            else 0.0
        ),
        "multi_source_support": (
            resolved_weights["multi_source_support"] if source_family_count >= 2 else 0.0
        ),
        "active_side_support": (
            resolved_weights["active_side_support"] if active_candidate_count > 0 else 0.0
        ),
        "reverse_shadow_support": (
            resolved_weights["reverse_shadow_support"] if reverse_shadow_targets else 0.0
        ),
        "multi_word_penalty": (resolved_weights["multi_word_penalty"] if word_count > 1 else 0.0),
    }
    support_features = [
        feature
        for feature, enabled in (
            ("rulegen_top3_source", "rulegen_top3_sources" in label_set),
            (
                "rulegen_all_source",
                "rulegen_all_sources" in label_set and "rulegen_top3_sources" not in label_set,
            ),
            ("forward_gloss_fragment", "forward_gloss_fragments" in label_set),
            ("multi_source_support", source_family_count >= 2),
            ("active_side_support", active_candidate_count > 0),
            ("reverse_shadow_support", bool(reverse_shadow_targets)),
        )
        if enabled
    ]
    penalties = ["multi_word_penalty"] if word_count > 1 else []
    return {
        "source_labels": sorted(label_set),
        "active_candidate_count": active_candidate_count,
        "reverse_shadow_target_count": len(reverse_shadow_targets),
        "reverse_shadow_targets": sorted(reverse_shadow_targets),
        "trigger_support_features": support_features,
        "trigger_support_penalties": penalties,
        "trigger_support_score_breakdown": score_breakdown,
        "trigger_support_score": sum(float(value) for value in score_breakdown.values()),
    }


def _count_active_side_matches(
    *,
    trigger: str,
    records: Sequence[TranslationGlossRecord],
) -> int:
    return sum(
        1
        for record in collect_en_es_sanitized_gloss_records(records)
        if normalize_reverse_token_with_pos(record.translation, pos_raw=record.pos_raw) == trigger
    )


def _collect_reverse_shadow_targets(
    *,
    target: str,
    records: Sequence[TranslationGlossRecord],
    benchmark_target_keys: set[str],
) -> set[str]:
    normalized_target = _normalize_shadow_text(target)
    reverse_shadow_targets: set[str] = set()
    for record in records:
        candidate_target = _normalize_shadow_text(record.translation)
        if (
            candidate_target
            and candidate_target != normalized_target
            and candidate_target in benchmark_target_keys
        ):
            reverse_shadow_targets.add(candidate_target)
    return reverse_shadow_targets
