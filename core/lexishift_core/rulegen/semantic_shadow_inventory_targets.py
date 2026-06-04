from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.pairs.en_es_support import (
    collect_sanitized_gloss_records as collect_en_es_sanitized_gloss_records,
    normalize_reverse_token_with_pos,
)
from lexishift_core.rulegen.semantic_shadow_trigger_support import (
    DEFAULT_TRIGGER_SUPPORT_SCORE_MIN,
    build_trigger_support_details_from_records,
)

RULEGEN_SHADOW_SOURCE_FIELDS = ("top3_sources", "all_sources")
DEFAULT_FORWARD_SEED_MAX_WORDS = 4


def normalize_shadow_text(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


@dataclass(frozen=True)
class BenchmarkShadowTarget:
    target: str
    case_ids: tuple[str, ...]
    tiers: tuple[str, ...]
    reviewed_triggers: tuple[str, ...]


def build_benchmark_shadow_targets(
    cases: Sequence[Mapping[str, object]],
    *,
    targets: Sequence[str] | None = None,
) -> list[BenchmarkShadowTarget]:
    requested = {str(target).strip() for target in targets or () if str(target).strip()}
    grouped: dict[str, dict[str, list[str]]] = {}
    for case in cases:
        target = str(case.get("target") or "").strip()
        if not target:
            continue
        if requested and target not in requested:
            continue
        bucket = grouped.setdefault(
            target,
            {
                "case_ids": [],
                "tiers": [],
                "reviewed_triggers": [],
            },
        )
        case_id = str(case.get("case_id") or "").strip()
        if case_id and case_id not in bucket["case_ids"]:
            bucket["case_ids"].append(case_id)
        tier = str(case.get("tier") or "").strip()
        if tier and tier not in bucket["tiers"]:
            bucket["tiers"].append(tier)
        reviewed_values: list[str] = []
        for key in ("expected_top1_any", "expected_any"):
            value = case.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                reviewed_values.extend(str(item).strip() for item in value if str(item).strip())
        for trigger in reviewed_values:
            normalized = normalize_shadow_text(trigger)
            if normalized and normalized not in bucket["reviewed_triggers"]:
                bucket["reviewed_triggers"].append(normalized)
    return [
        BenchmarkShadowTarget(
            target=target,
            case_ids=tuple(bucket["case_ids"]),
            tiers=tuple(bucket["tiers"]),
            reviewed_triggers=tuple(bucket["reviewed_triggers"]),
        )
        for target, bucket in sorted(grouped.items())
    ]


def build_rulegen_shadow_targets(
    case_results: Sequence[Mapping[str, object]],
    *,
    targets: Sequence[str] | None = None,
    source_field: str = "top3_sources",
) -> list[BenchmarkShadowTarget]:
    normalized_source_field = str(source_field or "").strip() or "top3_sources"
    if normalized_source_field not in RULEGEN_SHADOW_SOURCE_FIELDS:
        raise ValueError(
            f"Unsupported rulegen shadow source field: {normalized_source_field!r}; "
            f"expected one of {RULEGEN_SHADOW_SOURCE_FIELDS!r}"
        )
    requested = {str(target).strip() for target in targets or () if str(target).strip()}
    grouped: dict[str, dict[str, list[str]]] = {}
    for case in case_results:
        target = str(case.get("target") or "").strip()
        if not target:
            continue
        if requested and target not in requested:
            continue
        bucket = grouped.setdefault(
            target,
            {
                "case_ids": [],
                "tiers": [f"rulegen_{normalized_source_field}"],
                "reviewed_triggers": [],
            },
        )
        case_id = str(case.get("case_id") or "").strip()
        if case_id and case_id not in bucket["case_ids"]:
            bucket["case_ids"].append(case_id)
        source_values = case.get(normalized_source_field)
        if not isinstance(source_values, Sequence) or isinstance(source_values, (str, bytes)):
            source_values = ()
        for trigger in source_values:
            normalized = normalize_shadow_text(trigger)
            if normalized and normalized not in bucket["reviewed_triggers"]:
                bucket["reviewed_triggers"].append(normalized)
    return [
        BenchmarkShadowTarget(
            target=target,
            case_ids=tuple(bucket["case_ids"]),
            tiers=tuple(bucket["tiers"]),
            reviewed_triggers=tuple(bucket["reviewed_triggers"]),
        )
        for target, bucket in sorted(grouped.items())
    ]


def augment_shadow_targets_with_forward_gloss_triggers(
    benchmark_targets: Sequence[BenchmarkShadowTarget],
    *,
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    max_words: int = DEFAULT_FORWARD_SEED_MAX_WORDS,
) -> list[BenchmarkShadowTarget]:
    normalized_max_words = max(1, int(max_words))
    augmented_targets: list[BenchmarkShadowTarget] = []
    for benchmark_target in benchmark_targets:
        trigger_values: list[str] = list(benchmark_target.reviewed_triggers)
        seen = {trigger for trigger in trigger_values if trigger}
        forward_records = collect_en_es_sanitized_gloss_records(
            forward_records_by_target.get(benchmark_target.target, ())
        )
        for record in forward_records:
            normalized_trigger = normalize_reverse_token_with_pos(
                record.translation,
                pos_raw=record.pos_raw,
            )
            if not normalized_trigger:
                continue
            if (
                len([token for token in normalized_trigger.split(" ") if token])
                > normalized_max_words
            ):
                continue
            if normalized_trigger in seen:
                continue
            seen.add(normalized_trigger)
            trigger_values.append(normalized_trigger)
        tiers = tuple(
            value
            for value in (*benchmark_target.tiers, "forward_gloss_fragments")
            if str(value).strip()
        )
        augmented_targets.append(
            BenchmarkShadowTarget(
                target=benchmark_target.target,
                case_ids=benchmark_target.case_ids,
                tiers=tiers,
                reviewed_triggers=tuple(trigger_values),
            )
        )
    return augmented_targets


def subtract_shadow_target_triggers(
    minuend_targets: Sequence[BenchmarkShadowTarget],
    subtrahend_targets: Sequence[BenchmarkShadowTarget],
    *,
    tier_label: str,
) -> list[BenchmarkShadowTarget]:
    subtrahend_index = {
        target.target: {
            trigger for trigger in target.reviewed_triggers if str(trigger or "").strip()
        }
        for target in subtrahend_targets
        if str(target.target or "").strip()
    }
    difference_targets: list[BenchmarkShadowTarget] = []
    for target in minuend_targets:
        normalized_target = str(target.target or "").strip()
        if not normalized_target:
            continue
        excluded = subtrahend_index.get(normalized_target, set())
        remaining_triggers = tuple(
            trigger
            for trigger in target.reviewed_triggers
            if str(trigger or "").strip() and trigger not in excluded
        )
        difference_targets.append(
            BenchmarkShadowTarget(
                target=target.target,
                case_ids=target.case_ids,
                tiers=tuple(value for value in (*target.tiers, tier_label) if str(value).strip()),
                reviewed_triggers=remaining_triggers,
            )
        )
    return difference_targets


def build_shadow_trigger_source_index(
    *,
    source_targets_by_label: Mapping[str, Sequence[BenchmarkShadowTarget]],
) -> dict[tuple[str, str], tuple[str, ...]]:
    source_index: dict[tuple[str, str], list[str]] = {}
    for label, targets in source_targets_by_label.items():
        normalized_label = str(label or "").strip()
        if not normalized_label:
            continue
        for target in targets:
            normalized_target = str(target.target or "").strip()
            if not normalized_target:
                continue
            for trigger in target.reviewed_triggers:
                normalized_trigger = normalize_shadow_text(trigger)
                if not normalized_trigger:
                    continue
                bucket = source_index.setdefault((normalized_target, normalized_trigger), [])
                if normalized_label not in bucket:
                    bucket.append(normalized_label)
    return {
        key: tuple(values) for key, values in sorted(source_index.items(), key=lambda item: item[0])
    }


def build_shadow_trigger_support_details(
    *,
    target: str,
    trigger: str,
    source_labels: Sequence[str],
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    reverse_records_by_source: Mapping[str, Sequence[TranslationGlossRecord]],
    forward_provider: str,
    reverse_provider: str,
    benchmark_target_map: Mapping[str, BenchmarkShadowTarget],
    trigger_support_weights: Mapping[str, object] | None = None,
) -> dict[str, object]:
    normalized_target = str(target or "").strip()
    normalized_trigger = normalize_shadow_text(trigger)
    _ = forward_provider, reverse_provider
    return build_trigger_support_details_from_records(
        target=normalized_target,
        trigger=normalized_trigger,
        source_labels=source_labels,
        forward_records=forward_records_by_target.get(normalized_target, ()),
        reverse_records=reverse_records_by_source.get(normalized_trigger, ()),
        benchmark_target_keys=tuple(benchmark_target_map.keys()),
        score_weights=trigger_support_weights,
    )


def filter_shadow_targets_by_trigger_support(
    *,
    seed_targets: Sequence[BenchmarkShadowTarget],
    source_targets_by_label: Mapping[str, Sequence[BenchmarkShadowTarget]],
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    reverse_records_by_source: Mapping[str, Sequence[TranslationGlossRecord]],
    forward_provider: str,
    reverse_provider: str,
    benchmark_target_map: Mapping[str, BenchmarkShadowTarget],
    min_score: float = DEFAULT_TRIGGER_SUPPORT_SCORE_MIN,
    tier_label: str = "trigger_support_filtered",
    trigger_support_weights: Mapping[str, object] | None = None,
) -> tuple[list[BenchmarkShadowTarget], list[dict[str, object]]]:
    source_index = build_shadow_trigger_source_index(
        source_targets_by_label=source_targets_by_label
    )
    filtered_targets: list[BenchmarkShadowTarget] = []
    support_rows: list[dict[str, object]] = []
    for seed_target in seed_targets:
        kept_triggers: list[str] = []
        for trigger in seed_target.reviewed_triggers:
            normalized_trigger = normalize_shadow_text(trigger)
            details = build_shadow_trigger_support_details(
                target=seed_target.target,
                trigger=normalized_trigger,
                source_labels=source_index.get((seed_target.target, normalized_trigger), ()),
                forward_records_by_target=forward_records_by_target,
                reverse_records_by_source=reverse_records_by_source,
                forward_provider=forward_provider,
                reverse_provider=reverse_provider,
                benchmark_target_map=benchmark_target_map,
                trigger_support_weights=trigger_support_weights,
            )
            support_rows.append(
                {
                    "target": seed_target.target,
                    "trigger": normalized_trigger,
                    **details,
                }
            )
            if (_safe_float(details.get("trigger_support_score")) or 0.0) >= float(min_score):
                kept_triggers.append(normalized_trigger)
        filtered_targets.append(
            BenchmarkShadowTarget(
                target=seed_target.target,
                case_ids=seed_target.case_ids,
                tiers=tuple(
                    value for value in (*seed_target.tiers, tier_label) if str(value).strip()
                ),
                reviewed_triggers=tuple(kept_triggers),
            )
        )
    return filtered_targets, support_rows


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (float, int)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


__all__ = (
    "BenchmarkShadowTarget",
    "DEFAULT_FORWARD_SEED_MAX_WORDS",
    "RULEGEN_SHADOW_SOURCE_FIELDS",
    "augment_shadow_targets_with_forward_gloss_triggers",
    "build_benchmark_shadow_targets",
    "build_rulegen_shadow_targets",
    "build_shadow_trigger_source_index",
    "build_shadow_trigger_support_details",
    "filter_shadow_targets_by_trigger_support",
    "normalize_shadow_text",
    "subtract_shadow_target_triggers",
)
