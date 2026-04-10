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
from lexishift_core.rulegen.utils import sanitize_dictionary_gloss

DEFAULT_SHADOW_PROMOTION_POLICY = "same_pos_lenient_v1"
SUPPORT_SCORE_POLICY = "support_score_v1"
SHADOW_PROMOTION_POLICIES = (
    DEFAULT_SHADOW_PROMOTION_POLICY,
    SUPPORT_SCORE_POLICY,
    "benchmark_backed_v1",
    "cross_checked_v1",
    "cross_checked_backoff_missing_active_v1",
)
RULEGEN_SHADOW_SOURCE_FIELDS = ("top3_sources", "all_sources")
DEFAULT_FORWARD_SEED_MAX_WORDS = 4
DEFAULT_SUPPORT_SCORE_MIN = 3.0
DEFAULT_SUPPORT_SCORE_MAX_PROMOTED = 3
SHADOW_SUPPORT_SCORE_WEIGHTS = {
    "reviewed_trigger_support": 2.0,
    "benchmark_target_present": 1.0,
    "same_pos_as_active": 1.0,
    "active_side_support": 1.0,
    "cross_pos_mismatch_penalty": -1.0,
}


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
    grouped: dict[str, dict[str, object]] = {}
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
        reviewed_values = []
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
    grouped: dict[str, dict[str, object]] = {}
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
            )
            support_rows.append(
                {
                    "target": seed_target.target,
                    "trigger": normalized_trigger,
                    **details,
                }
            )
            if float(details.get("trigger_support_score") or 0.0) >= float(min_score):
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


def build_en_es_shadow_inventory(
    *,
    benchmark_targets: Sequence[BenchmarkShadowTarget],
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    reverse_records_by_source: Mapping[str, Sequence[TranslationGlossRecord]],
    forward_provider: str,
    reverse_provider: str,
    promotion_policy: str = DEFAULT_SHADOW_PROMOTION_POLICY,
) -> dict[str, object]:
    benchmark_target_map = {target.target: target for target in benchmark_targets}
    forward_shadow_index = _build_forward_shadow_index(
        benchmark_targets=benchmark_targets,
        forward_records_by_target=forward_records_by_target,
        provider=forward_provider,
    )
    inventory_targets: list[dict[str, object]] = []
    for benchmark_target in benchmark_targets:
        forward_records = collect_en_es_sanitized_gloss_records(
            forward_records_by_target.get(benchmark_target.target, ())
        )
        trigger_entries: list[dict[str, object]] = []
        for trigger in benchmark_target.reviewed_triggers:
            active_candidates = _build_active_candidates_for_trigger(
                target=benchmark_target.target,
                trigger=trigger,
                records=forward_records,
                provider=forward_provider,
            )
            reverse_records = reverse_records_by_source.get(trigger, ())
            reverse_candidates = _build_reverse_candidates(
                trigger=trigger,
                records=reverse_records,
                provider=reverse_provider,
                benchmark_target_map=benchmark_target_map,
            )
            reverse_active_candidates = [
                candidate
                for candidate in reverse_candidates
                if str(candidate.get("target") or "").strip() == benchmark_target.target
            ]
            shadow_candidates = [
                candidate
                for candidate in reverse_candidates
                if str(candidate.get("target") or "").strip() != benchmark_target.target
            ]
            existing_shadow_targets = {
                str(candidate.get("target") or "").strip()
                for candidate in shadow_candidates
                if str(candidate.get("target") or "").strip()
            }
            for forward_candidate in forward_shadow_index.get(trigger, ()):
                if not isinstance(forward_candidate, Mapping):
                    continue
                candidate_target = str(forward_candidate.get("target") or "").strip()
                if (
                    not candidate_target
                    or candidate_target == benchmark_target.target
                    or candidate_target in existing_shadow_targets
                ):
                    continue
                shadow_candidates.append(dict(forward_candidate))
                existing_shadow_targets.add(candidate_target)
            promoted_shadow_candidates = promote_shadow_candidates_for_policy(
                shadow_candidates=shadow_candidates,
                active_candidates=active_candidates,
                policy=promotion_policy,
            )
            trigger_entries.append(
                {
                    "trigger": trigger,
                    "active_candidates": active_candidates,
                    "reverse_active_candidates": reverse_active_candidates,
                    "shadow_candidates": shadow_candidates,
                    "promoted_shadow_candidates": promoted_shadow_candidates,
                }
            )
        inventory_targets.append(
            {
                "target": benchmark_target.target,
                "case_ids": list(benchmark_target.case_ids),
                "tiers": list(benchmark_target.tiers),
                "reviewed_triggers": list(benchmark_target.reviewed_triggers),
                "trigger_entries": trigger_entries,
            }
        )
    return {
        "schema_version": 1,
        "pair": "en-es",
        "target_count": len(inventory_targets),
        "reviewed_trigger_count": sum(
            len(target.reviewed_triggers) for target in benchmark_targets
        ),
        "promotion_policy": promotion_policy,
        "providers": {
            "forward": str(forward_provider or "").strip() or "unknown",
            "reverse": str(reverse_provider or "").strip() or "unknown",
        },
        "targets": inventory_targets,
        "summary": _build_inventory_summary(inventory_targets),
    }


def _build_forward_shadow_index(
    *,
    benchmark_targets: Sequence[BenchmarkShadowTarget],
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    provider: str,
) -> dict[str, list[dict[str, object]]]:
    trigger_index: dict[str, list[dict[str, object]]] = {}
    for benchmark_target in benchmark_targets:
        forward_records = collect_en_es_sanitized_gloss_records(
            forward_records_by_target.get(benchmark_target.target, ())
        )
        for trigger in benchmark_target.reviewed_triggers:
            active_candidates = _build_active_candidates_for_trigger(
                target=benchmark_target.target,
                trigger=trigger,
                records=forward_records,
                provider=provider,
            )
            if not active_candidates:
                continue
            bucket = trigger_index.setdefault(trigger, [])
            for candidate in active_candidates:
                candidate_copy = dict(candidate)
                candidate_copy["benchmark_target_present"] = True
                candidate_copy["reviewed_trigger_support"] = True
                candidate_copy["candidate_sources"] = ["forward_index"]
                bucket.append(candidate_copy)
    return trigger_index


def _build_inventory_summary(targets: Sequence[Mapping[str, object]]) -> dict[str, object]:
    trigger_count = 0
    with_active_candidates = 0
    with_shadow_candidates = 0
    with_promoted_shadow_candidates = 0
    for target in targets:
        trigger_entries = target.get("trigger_entries")
        if not isinstance(trigger_entries, Sequence) or isinstance(trigger_entries, (str, bytes)):
            continue
        for trigger_entry in trigger_entries:
            if not isinstance(trigger_entry, Mapping):
                continue
            trigger_count += 1
            if trigger_entry.get("active_candidates"):
                with_active_candidates += 1
            if trigger_entry.get("shadow_candidates"):
                with_shadow_candidates += 1
            if trigger_entry.get("promoted_shadow_candidates"):
                with_promoted_shadow_candidates += 1
    return {
        "trigger_count": trigger_count,
        "triggers_with_active_candidates": with_active_candidates,
        "triggers_with_shadow_candidates": with_shadow_candidates,
        "triggers_with_promoted_shadow_candidates": with_promoted_shadow_candidates,
    }


def _build_active_candidates_for_trigger(
    *,
    target: str,
    trigger: str,
    records: Sequence[TranslationGlossRecord],
    provider: str,
) -> list[dict[str, object]]:
    normalized_trigger = normalize_shadow_text(trigger)
    matching_records = [
        record
        for record in records
        if normalize_reverse_token_with_pos(record.translation, pos_raw=record.pos_raw)
        == normalized_trigger
    ]
    clustered = _cluster_records(
        target_override=target,
        records=matching_records,
        provider=provider,
    )
    for candidate in clustered:
        candidate["matched_trigger"] = trigger
    return clustered


def _build_reverse_candidates(
    *,
    trigger: str,
    records: Sequence[TranslationGlossRecord],
    provider: str,
    benchmark_target_map: Mapping[str, BenchmarkShadowTarget],
) -> list[dict[str, object]]:
    clustered = _cluster_records(
        target_override=None,
        records=records,
        provider=provider,
    )
    for candidate in clustered:
        target = str(candidate.get("target") or "").strip()
        benchmark_target = benchmark_target_map.get(target)
        candidate["candidate_sources"] = ["reverse_lookup"]
        candidate["benchmark_target_present"] = benchmark_target is not None
        if benchmark_target is not None:
            candidate["benchmark_case_ids"] = list(benchmark_target.case_ids)
            candidate["reviewed_trigger_support"] = (
                normalize_shadow_text(trigger) in benchmark_target.reviewed_triggers
            )
        else:
            candidate["reviewed_trigger_support"] = False
    return clustered


def promote_shadow_candidates_for_policy(
    *,
    shadow_candidates: Sequence[Mapping[str, object]],
    active_candidates: Sequence[Mapping[str, object]],
    policy: str = DEFAULT_SHADOW_PROMOTION_POLICY,
) -> list[dict[str, object]]:
    normalized_policy = str(policy or "").strip() or DEFAULT_SHADOW_PROMOTION_POLICY
    if normalized_policy not in SHADOW_PROMOTION_POLICIES:
        raise ValueError(
            f"Unsupported shadow promotion policy: {normalized_policy!r}; "
            f"expected one of {SHADOW_PROMOTION_POLICIES!r}"
        )
    if normalized_policy == SUPPORT_SCORE_POLICY:
        return promote_shadow_candidates_with_support_score(
            shadow_candidates=shadow_candidates,
            active_candidates=active_candidates,
            min_score=DEFAULT_SUPPORT_SCORE_MIN,
            max_promoted_shadows=DEFAULT_SUPPORT_SCORE_MAX_PROMOTED,
            policy=normalized_policy,
        )
    active_pos_values = {
        str(candidate.get("canonical_pos") or "").strip().lower()
        for candidate in active_candidates
        if str(candidate.get("canonical_pos") or "").strip()
    }
    has_active_candidates = bool(active_candidates)
    has_active_pos = bool(active_pos_values)
    ranked: list[tuple[tuple[int, int, int, str], dict[str, object]]] = []
    for candidate in shadow_candidates:
        target = str(candidate.get("target") or "").strip()
        canonical_pos = str(candidate.get("canonical_pos") or "").strip().lower()
        reviewed_trigger_support = bool(candidate.get("reviewed_trigger_support"))
        benchmark_target_present = bool(candidate.get("benchmark_target_present"))
        same_pos = bool(canonical_pos and canonical_pos in active_pos_values)
        promotion_reasons = [
            reason
            for enabled, reason in (
                (reviewed_trigger_support, "reviewed_trigger_support"),
                (benchmark_target_present, "benchmark_target_present"),
                (same_pos, "same_pos_as_active"),
            )
            if enabled
        ]
        if not _shadow_candidate_qualifies_for_policy(
            reviewed_trigger_support=reviewed_trigger_support,
            benchmark_target_present=benchmark_target_present,
            same_pos=same_pos,
            has_active_candidates=has_active_candidates,
            has_active_pos=has_active_pos,
            policy=normalized_policy,
        ):
            continue
        score_vector = (
            1 if reviewed_trigger_support else 0,
            1 if benchmark_target_present else 0,
            1 if same_pos else 0,
            target,
        )
        candidate_copy = dict(candidate)
        candidate_copy["same_pos_as_active"] = same_pos
        candidate_copy["promotion_reasons"] = promotion_reasons
        candidate_copy["promotion_policy"] = normalized_policy
        support_details = build_shadow_candidate_support_details(
            candidate=candidate_copy,
            active_candidates=active_candidates,
        )
        candidate_copy.update(support_details)
        candidate_copy["promotion_reasons"] = promotion_reasons
        ranked.append((score_vector, candidate_copy))
    ranked.sort(reverse=True)
    return [candidate for _score, candidate in ranked[:3]]


def promote_shadow_candidates_with_support_score(
    *,
    shadow_candidates: Sequence[Mapping[str, object]],
    active_candidates: Sequence[Mapping[str, object]],
    min_score: float = DEFAULT_SUPPORT_SCORE_MIN,
    max_promoted_shadows: int = DEFAULT_SUPPORT_SCORE_MAX_PROMOTED,
    policy: str = SUPPORT_SCORE_POLICY,
) -> list[dict[str, object]]:
    normalized_policy = str(policy or "").strip() or SUPPORT_SCORE_POLICY
    normalized_max_promoted = max(1, int(max_promoted_shadows))
    ranked: list[tuple[tuple[float, int, int, int, str], dict[str, object]]] = []
    for candidate in shadow_candidates:
        candidate_copy = dict(candidate)
        support_details = build_shadow_candidate_support_details(
            candidate=candidate_copy,
            active_candidates=active_candidates,
        )
        candidate_copy.update(support_details)
        candidate_copy["promotion_policy"] = normalized_policy
        support_score = float(candidate_copy.get("support_score") or 0.0)
        if support_score < float(min_score):
            continue
        ranked.append(
            (
                (
                    support_score,
                    1 if candidate_copy.get("reviewed_trigger_support") else 0,
                    1 if candidate_copy.get("same_pos_as_active") else 0,
                    1 if candidate_copy.get("benchmark_target_present") else 0,
                    str(candidate_copy.get("target") or "").strip(),
                ),
                candidate_copy,
            )
        )
    ranked.sort(reverse=True)
    return [candidate for _score, candidate in ranked[:normalized_max_promoted]]


def build_shadow_candidate_support_details(
    *,
    candidate: Mapping[str, object],
    active_candidates: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    active_pos_values = {
        str(active_candidate.get("canonical_pos") or "").strip().lower()
        for active_candidate in active_candidates
        if str(active_candidate.get("canonical_pos") or "").strip()
    }
    has_active_candidates = bool(active_candidates)
    has_active_pos = bool(active_pos_values)
    canonical_pos = str(candidate.get("canonical_pos") or "").strip().lower()
    reviewed_trigger_support = bool(candidate.get("reviewed_trigger_support"))
    benchmark_target_present = bool(candidate.get("benchmark_target_present"))
    same_pos = bool(canonical_pos and canonical_pos in active_pos_values)
    cross_pos_mismatch = bool(has_active_pos and canonical_pos and not same_pos)

    support_breakdown = {
        "reviewed_trigger_support": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["reviewed_trigger_support"]
            if reviewed_trigger_support
            else 0.0
        ),
        "benchmark_target_present": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["benchmark_target_present"]
            if benchmark_target_present
            else 0.0
        ),
        "same_pos_as_active": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["same_pos_as_active"] if same_pos else 0.0
        ),
        "active_side_support": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["active_side_support"] if has_active_candidates else 0.0
        ),
        "cross_pos_mismatch_penalty": (
            SHADOW_SUPPORT_SCORE_WEIGHTS["cross_pos_mismatch_penalty"]
            if cross_pos_mismatch
            else 0.0
        ),
    }
    positive_features = [
        feature
        for feature, value in (
            ("reviewed_trigger_support", reviewed_trigger_support),
            ("benchmark_target_present", benchmark_target_present),
            ("same_pos_as_active", same_pos),
            ("active_side_support", has_active_candidates),
        )
        if value
    ]
    penalties = ["cross_pos_mismatch_penalty"] if cross_pos_mismatch else []
    return {
        "same_pos_as_active": same_pos,
        "support_features": positive_features,
        "support_penalties": penalties,
        "support_score_breakdown": support_breakdown,
        "support_score": sum(float(value) for value in support_breakdown.values()),
        "promotion_reasons": positive_features,
    }


def _shadow_candidate_qualifies_for_policy(
    *,
    reviewed_trigger_support: bool,
    benchmark_target_present: bool,
    same_pos: bool,
    has_active_candidates: bool,
    has_active_pos: bool,
    policy: str,
) -> bool:
    if policy == DEFAULT_SHADOW_PROMOTION_POLICY:
        return reviewed_trigger_support or benchmark_target_present or same_pos
    if policy == "benchmark_backed_v1":
        return reviewed_trigger_support or benchmark_target_present
    if policy == "cross_checked_v1":
        return reviewed_trigger_support or (benchmark_target_present and same_pos)
    if policy == "cross_checked_backoff_missing_active_v1":
        if reviewed_trigger_support:
            return True
        if benchmark_target_present and same_pos:
            return True
        return benchmark_target_present and has_active_candidates and not has_active_pos
    return False


def _cluster_records(
    *,
    target_override: str | None,
    records: Sequence[TranslationGlossRecord],
    provider: str,
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, object, object, object], dict[str, object]] = {}
    for index, record in enumerate(records):
        metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
        target = str(target_override or record.translation or "").strip()
        if not target:
            continue
        entry_ord = _as_int(metadata.get("entry_ord"))
        sense_ord = _as_int(metadata.get("sense_ord"))
        gloss_ord = _as_int(metadata.get("gloss_ord"))
        key = (target, entry_ord, sense_ord, gloss_ord)
        if entry_ord is None and sense_ord is None and gloss_ord is None:
            key = (target, None, None, index)
        bucket = grouped.get(key)
        if bucket is None:
            locator = _build_locator(
                provider=provider,
                target=target,
                entry_ord=entry_ord,
                sense_ord=sense_ord,
                gloss_ord=gloss_ord,
                fallback_index=index,
            )
            bucket = {
                "target": target,
                "sense_label": _build_sense_label(record),
                "canonical_pos": _build_canonical_pos(record),
                "provider": provider,
                "locator": locator,
                "glosses": [],
                "qualifiers": _build_qualifiers(metadata),
            }
            grouped[key] = bucket
        emitted_gloss = sanitize_dictionary_gloss(record.translation)
        if emitted_gloss and emitted_gloss not in bucket["glosses"]:
            bucket["glosses"].append(emitted_gloss)
    return list(grouped.values())


def _build_locator(
    *,
    provider: str,
    target: str,
    entry_ord: int | None,
    sense_ord: int | None,
    gloss_ord: int | None,
    fallback_index: int,
) -> dict[str, object]:
    provider_text = str(provider or "").strip() or "unknown"
    if "wiktionary" in provider_text and entry_ord is not None and sense_ord is not None:
        locator: dict[str, object] = {
            "provider": provider_text,
            "locator_kind": "wiktionary_ordinal",
            "entry_ord": entry_ord,
            "sense_ord": sense_ord,
        }
        if gloss_ord is not None:
            locator["gloss_ord"] = gloss_ord
        return locator
    if "freedict" in provider_text and gloss_ord is not None:
        return {
            "provider": provider_text,
            "locator_kind": "freedict_gloss",
            "target_key": target,
            "gloss_ord": gloss_ord,
        }
    return {
        "provider": provider_text,
        "locator_kind": "opaque",
        "opaque_id": f"{normalize_shadow_text(target)}:{fallback_index}",
    }


def _build_sense_label(record: TranslationGlossRecord) -> str:
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    raw_glosses = metadata.get("sense_raw_glosses")
    if isinstance(raw_glosses, Sequence) and not isinstance(raw_glosses, (str, bytes)):
        first = next((str(item).strip() for item in raw_glosses if str(item).strip()), "")
        if first:
            return first
    for key in ("gloss_raw_text", "gloss_fragment_source_text", "gloss_input_text"):
        value = str(metadata.get(key) or "").strip()
        if value:
            return value
    sanitized = sanitize_dictionary_gloss(record.translation)
    return sanitized or str(record.translation or "").strip()


def _build_canonical_pos(record: TranslationGlossRecord) -> str:
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    candidate = str(metadata.get("dictionary_pos_canonical") or "").strip().lower()
    if candidate:
        return candidate
    return str(record.pos_raw or "").strip().lower()


def _build_qualifiers(metadata: Mapping[str, object]) -> dict[str, object] | None:
    qualifiers: dict[str, list[str]] = {}
    tags = _normalize_string_list(
        metadata.get("sense_tags"),
        metadata.get("translation_tags"),
        metadata.get("entry_tags"),
    )
    if tags:
        qualifiers["tags"] = tags
    topics = _normalize_string_list(metadata.get("sense_topics"))
    if topics:
        qualifiers["topics"] = topics
    categories = _normalize_string_list(
        metadata.get("sense_categories"),
        metadata.get("entry_categories"),
    )
    if categories:
        qualifiers["categories"] = categories
    return qualifiers or None


def _normalize_string_list(*values: object) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                text = str(item).strip()
                if text and text not in normalized:
                    normalized.append(text)
        else:
            text = str(value or "").strip()
            if text and text not in normalized:
                normalized.append(text)
    return normalized


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None
