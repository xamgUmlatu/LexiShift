from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.pairs.en_es_support import (
    collect_sanitized_gloss_records as collect_en_es_sanitized_gloss_records,
    normalize_reverse_token_with_pos,
)
from lexishift_core.rulegen.semantic_shadow_frequency import (
    ShadowFrequencyLookup,
    enrich_candidate_frequency_details,
    select_frequency_representative_targets,
)
from lexishift_core.rulegen.semantic_shadow_lexical_bridge import (
    build_bridge_marker_frequency,
    build_semantic_bridge_candidates,
    build_target_bridge_profiles,
)
from lexishift_core.rulegen.semantic_shadow_representative_pruning import (
    apply_representative_pruning,
)
from lexishift_core.rulegen.semantic_shadow_inventory_helpers import (
    build_active_profile_fallback,
    build_forward_shadow_index,
    build_inventory_summary,
)
from lexishift_core.rulegen.semantic_shadow_inventory_targets import (
    DEFAULT_FORWARD_SEED_MAX_WORDS,
    RULEGEN_SHADOW_SOURCE_FIELDS,
    BenchmarkShadowTarget,
    augment_shadow_targets_with_forward_gloss_triggers,
    build_benchmark_shadow_targets,
    build_rulegen_shadow_targets,
    build_shadow_trigger_source_index,
    build_shadow_trigger_support_details,
    filter_shadow_targets_by_trigger_support,
    normalize_shadow_text,
    subtract_shadow_target_triggers,
)
from lexishift_core.rulegen.semantic_shadow_neighborhood import (
    attach_target_forward_neighborhood_terms,
    attach_target_trigger_family_terms,
    build_target_forward_neighborhood_terms,
    build_target_trigger_family_terms,
)
from lexishift_core.rulegen.semantic_shadow_record_clusters import (
    build_shadow_canonical_pos,
    cluster_shadow_records,
)
from lexishift_core.rulegen.semantic_shadow_support import (
    DEFAULT_FREQUENCY_REPRESENTATIVE_BONUS,
    DEFAULT_FREQUENCY_SIMILARITY_TAU,
    DEFAULT_FREQUENCY_SIMILARITY_WEIGHT,
    build_shadow_candidate_support_details,
    merge_shadow_candidate_evidence,
    normalize_shadow_string_list,
)

DEFAULT_SHADOW_PROMOTION_POLICY = "same_pos_lenient_v1"
SUPPORT_SCORE_POLICY = "support_score_v1"
DEFAULT_REPRESENTATIVE_PRUNING_MODE = "off"
REPRESENTATIVE_PRUNING_MODES = (
    DEFAULT_REPRESENTATIVE_PRUNING_MODE,
    "sense_label_pos_v1",
)
SHADOW_PROMOTION_POLICIES = (
    DEFAULT_SHADOW_PROMOTION_POLICY,
    SUPPORT_SCORE_POLICY,
    "benchmark_backed_v1",
    "cross_checked_v1",
    "cross_checked_backoff_missing_active_v1",
)
DEFAULT_SUPPORT_SCORE_MIN = 3.0
DEFAULT_SUPPORT_SCORE_MAX_PROMOTED = 3
DEFAULT_FREQUENCY_REPRESENTATIVE_TOP_K = 0

__all__ = (
    "BenchmarkShadowTarget",
    "DEFAULT_FORWARD_SEED_MAX_WORDS",
    "DEFAULT_REPRESENTATIVE_PRUNING_MODE",
    "RULEGEN_SHADOW_SOURCE_FIELDS",
    "augment_shadow_targets_with_forward_gloss_triggers",
    "build_benchmark_shadow_targets",
    "build_en_es_shadow_inventory",
    "build_rulegen_shadow_targets",
    "build_shadow_trigger_source_index",
    "build_shadow_trigger_support_details",
    "filter_shadow_targets_by_trigger_support",
    "normalize_shadow_text",
    "promote_shadow_candidates_for_policy",
    "promote_shadow_candidates_with_support_score",
    "subtract_shadow_target_triggers",
)


def build_en_es_shadow_inventory(
    *,
    benchmark_targets: Sequence[BenchmarkShadowTarget],
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    reverse_records_by_source: Mapping[str, Sequence[TranslationGlossRecord]],
    target_reverse_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]] | None = None,
    forward_provider: str,
    reverse_provider: str,
    promotion_policy: str = DEFAULT_SHADOW_PROMOTION_POLICY,
    frequency_lookup: ShadowFrequencyLookup | None = None,
    support_score_weights: Mapping[str, object] | None = None,
    semantic_bridge_include_aux_text: bool = False,
    semantic_bridge_include_examples: bool = False,
) -> dict[str, object]:
    benchmark_target_map = {target.target: target for target in benchmark_targets}
    target_trigger_family_terms = build_target_trigger_family_terms(benchmark_targets)
    target_forward_neighborhood_terms = build_target_forward_neighborhood_terms(
        forward_records_by_target=forward_records_by_target,
        collect_records=collect_en_es_sanitized_gloss_records,
    )
    forward_shadow_index = build_forward_shadow_index(
        benchmark_targets=benchmark_targets,
        forward_records_by_target=forward_records_by_target,
        provider=forward_provider,
        collect_records=collect_en_es_sanitized_gloss_records,
        active_candidate_builder=_build_active_candidates_for_trigger,
        canonical_pos_builder=build_shadow_canonical_pos,
    )
    target_bridge_profiles = build_target_bridge_profiles(
        benchmark_targets=benchmark_targets,
        forward_records_by_target=forward_records_by_target,
        reverse_records_by_source=reverse_records_by_source,
        target_reverse_records_by_target=target_reverse_records_by_target,
        include_aux_text_markers=semantic_bridge_include_aux_text,
        include_example_markers=semantic_bridge_include_examples,
    )
    bridge_marker_frequency = build_bridge_marker_frequency(target_bridge_profiles)
    inventory_targets: list[dict[str, object]] = []
    for benchmark_target in benchmark_targets:
        forward_records = collect_en_es_sanitized_gloss_records(
            forward_records_by_target.get(benchmark_target.target, ())
        )
        active_profile_fallback = build_active_profile_fallback(
            target=benchmark_target.target,
            records=forward_records,
            provider=forward_provider,
            canonical_pos_builder=build_shadow_canonical_pos,
        )
        if active_profile_fallback is not None:
            attach_target_trigger_family_terms(
                active_profile_fallback,
                trigger_families_by_target=target_trigger_family_terms,
            )
            attach_target_forward_neighborhood_terms(
                active_profile_fallback,
                neighborhoods_by_target=target_forward_neighborhood_terms,
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
            for candidate in active_candidates:
                enrich_candidate_frequency_details(
                    candidate=candidate,
                    frequency_lookup=frequency_lookup,
                )
                attach_target_trigger_family_terms(
                    candidate,
                    trigger_families_by_target=target_trigger_family_terms,
                )
                attach_target_forward_neighborhood_terms(
                    candidate,
                    neighborhoods_by_target=target_forward_neighborhood_terms,
                )
            for candidate in reverse_active_candidates:
                enrich_candidate_frequency_details(
                    candidate=candidate,
                    frequency_lookup=frequency_lookup,
                )
                attach_target_trigger_family_terms(
                    candidate,
                    trigger_families_by_target=target_trigger_family_terms,
                )
                attach_target_forward_neighborhood_terms(
                    candidate,
                    neighborhoods_by_target=target_forward_neighborhood_terms,
                )
            for candidate in shadow_candidates:
                enrich_candidate_frequency_details(
                    candidate=candidate,
                    frequency_lookup=frequency_lookup,
                )
                attach_target_trigger_family_terms(
                    candidate,
                    trigger_families_by_target=target_trigger_family_terms,
                )
                attach_target_forward_neighborhood_terms(
                    candidate,
                    neighborhoods_by_target=target_forward_neighborhood_terms,
                )
            existing_shadow_targets = {
                str(candidate.get("target") or "").strip()
                for candidate in shadow_candidates
                if str(candidate.get("target") or "").strip()
            }
            shadow_candidate_by_target = {
                str(candidate.get("target") or "").strip(): candidate
                for candidate in shadow_candidates
                if str(candidate.get("target") or "").strip()
            }
            for forward_candidate in forward_shadow_index.get(trigger, ()):
                if not isinstance(forward_candidate, Mapping):
                    continue
                candidate_target = str(forward_candidate.get("target") or "").strip()
                if not candidate_target or candidate_target == benchmark_target.target:
                    continue
                forward_candidate_copy = dict(forward_candidate)
                enrich_candidate_frequency_details(
                    candidate=forward_candidate_copy,
                    frequency_lookup=frequency_lookup,
                )
                attach_target_trigger_family_terms(
                    forward_candidate_copy,
                    trigger_families_by_target=target_trigger_family_terms,
                )
                attach_target_forward_neighborhood_terms(
                    forward_candidate_copy,
                    neighborhoods_by_target=target_forward_neighborhood_terms,
                )
                existing_candidate = shadow_candidate_by_target.get(candidate_target)
                if existing_candidate is not None:
                    merge_shadow_candidate_evidence(existing_candidate, forward_candidate_copy)
                    continue
                shadow_candidates.append(forward_candidate_copy)
                existing_shadow_targets.add(candidate_target)
                shadow_candidate_by_target[candidate_target] = forward_candidate_copy
            for bridge_candidate in build_semantic_bridge_candidates(
                active_target=benchmark_target.target,
                trigger=trigger,
                active_candidates=active_candidates,
                existing_shadow_targets=set(),
                benchmark_target_map=benchmark_target_map,
                target_bridge_profiles=target_bridge_profiles,
                bridge_marker_frequency=bridge_marker_frequency,
            ):
                candidate_target = str(bridge_candidate.get("target") or "").strip()
                if not candidate_target:
                    continue
                bridge_candidate_copy = dict(bridge_candidate)
                enrich_candidate_frequency_details(
                    candidate=bridge_candidate_copy,
                    frequency_lookup=frequency_lookup,
                )
                attach_target_trigger_family_terms(
                    bridge_candidate_copy,
                    trigger_families_by_target=target_trigger_family_terms,
                )
                attach_target_forward_neighborhood_terms(
                    bridge_candidate_copy,
                    neighborhoods_by_target=target_forward_neighborhood_terms,
                )
                existing_candidate = shadow_candidate_by_target.get(candidate_target)
                if existing_candidate is not None:
                    merge_shadow_candidate_evidence(existing_candidate, bridge_candidate_copy)
                    continue
                shadow_candidates.append(bridge_candidate_copy)
                existing_shadow_targets.add(candidate_target)
                shadow_candidate_by_target[candidate_target] = bridge_candidate_copy
            promoted_shadow_candidates = promote_shadow_candidates_for_policy(
                shadow_candidates=shadow_candidates,
                active_candidates=active_candidates,
                active_profile_fallback=active_profile_fallback,
                active_trigger=trigger,
                policy=promotion_policy,
                support_score_weights=support_score_weights,
            )
            trigger_entries.append(
                {
                    "trigger": trigger,
                    "active_candidates": active_candidates,
                    "active_profile_fallback": active_profile_fallback,
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
        "semantic_bridge_options": {
            "include_aux_text": bool(semantic_bridge_include_aux_text),
            "include_examples": bool(semantic_bridge_include_examples),
        },
        "targets": inventory_targets,
        "summary": build_inventory_summary(inventory_targets),
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
    clustered = cluster_shadow_records(
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
    clustered = cluster_shadow_records(
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
    active_profile_fallback: Mapping[str, object] | None = None,
    active_trigger: str = "",
    policy: str = DEFAULT_SHADOW_PROMOTION_POLICY,
    support_score_weights: Mapping[str, object] | None = None,
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
            active_profile_fallback=active_profile_fallback,
            active_trigger=active_trigger,
            min_score=DEFAULT_SUPPORT_SCORE_MIN,
            max_promoted_shadows=DEFAULT_SUPPORT_SCORE_MAX_PROMOTED,
            policy=normalized_policy,
            support_score_weights=support_score_weights,
        )
    active_pos_values = {
        str(candidate.get("canonical_pos") or "").strip().lower()
        for candidate in active_candidates
        if str(candidate.get("canonical_pos") or "").strip()
    }
    has_active_candidates = bool(active_candidates)
    has_active_pos = bool(active_pos_values)
    active_profile_pos = str((active_profile_fallback or {}).get("canonical_pos") or "").strip()
    active_profile_trigger_family_terms = normalize_shadow_string_list(
        (active_profile_fallback or {}).get("target_trigger_family_terms")
    )
    active_profile_forward_neighborhood_terms = normalize_shadow_string_list(
        (active_profile_fallback or {}).get("forward_neighborhood_terms")
    )
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
            active_trigger=active_trigger,
            active_profile_pos=active_profile_pos,
            active_profile_support=bool(active_profile_pos),
            active_profile_trigger_family_terms=active_profile_trigger_family_terms,
            active_profile_forward_neighborhood_terms=active_profile_forward_neighborhood_terms,
            score_weights=support_score_weights,
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
    active_profile_fallback: Mapping[str, object] | None = None,
    active_trigger: str = "",
    min_score: float = DEFAULT_SUPPORT_SCORE_MIN,
    max_promoted_shadows: int = DEFAULT_SUPPORT_SCORE_MAX_PROMOTED,
    policy: str = SUPPORT_SCORE_POLICY,
    frequency_representative_bonus: float = DEFAULT_FREQUENCY_REPRESENTATIVE_BONUS,
    frequency_representative_top_k: int = DEFAULT_FREQUENCY_REPRESENTATIVE_TOP_K,
    frequency_similarity_weight: float = DEFAULT_FREQUENCY_SIMILARITY_WEIGHT,
    frequency_similarity_tau: float = DEFAULT_FREQUENCY_SIMILARITY_TAU,
    representative_pruning_mode: str = DEFAULT_REPRESENTATIVE_PRUNING_MODE,
    support_score_weights: Mapping[str, object] | None = None,
) -> list[dict[str, object]]:
    normalized_policy = str(policy or "").strip() or SUPPORT_SCORE_POLICY
    normalized_max_promoted = max(1, int(max_promoted_shadows))
    normalized_representative_pruning_mode = (
        str(representative_pruning_mode or "").strip() or DEFAULT_REPRESENTATIVE_PRUNING_MODE
    )
    if normalized_representative_pruning_mode not in REPRESENTATIVE_PRUNING_MODES:
        raise ValueError(
            "Unsupported representative pruning mode: "
            f"{normalized_representative_pruning_mode!r}; expected one of "
            f"{REPRESENTATIVE_PRUNING_MODES!r}"
        )
    frequency_representative_targets = select_frequency_representative_targets(
        shadow_candidates=shadow_candidates,
        top_k=int(frequency_representative_top_k),
    )
    active_profile_pos = str((active_profile_fallback or {}).get("canonical_pos") or "").strip()
    active_profile_trigger_family_terms = normalize_shadow_string_list(
        (active_profile_fallback or {}).get("target_trigger_family_terms")
    )
    active_profile_forward_neighborhood_terms = normalize_shadow_string_list(
        (active_profile_fallback or {}).get("forward_neighborhood_terms")
    )
    ranked: list[tuple[tuple[float, int, int, int, str], dict[str, object]]] = []
    for candidate in shadow_candidates:
        candidate_copy = dict(candidate)
        support_details = build_shadow_candidate_support_details(
            candidate=candidate_copy,
            active_candidates=active_candidates,
            active_trigger=active_trigger,
            active_profile_pos=active_profile_pos,
            active_profile_support=bool(active_profile_pos),
            active_profile_trigger_family_terms=active_profile_trigger_family_terms,
            active_profile_forward_neighborhood_terms=active_profile_forward_neighborhood_terms,
            frequency_representative_targets=frequency_representative_targets,
            frequency_representative_bonus=float(frequency_representative_bonus),
            frequency_similarity_weight=float(frequency_similarity_weight),
            frequency_similarity_tau=float(frequency_similarity_tau),
            score_weights=support_score_weights,
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
                    float(candidate_copy.get("semantic_bridge_score") or 0.0),
                    1 if candidate_copy.get("reviewed_trigger_support") else 0,
                    1 if candidate_copy.get("same_pos_as_active") else 0,
                    1 if candidate_copy.get("benchmark_target_present") else 0,
                    str(candidate_copy.get("target") or "").strip(),
                ),
                candidate_copy,
            )
        )
    ranked = apply_representative_pruning(
        ranked,
        mode=normalized_representative_pruning_mode,
        mode_off=DEFAULT_REPRESENTATIVE_PRUNING_MODE,
        supported_modes=REPRESENTATIVE_PRUNING_MODES,
        normalize_text=normalize_shadow_text,
    )
    ranked.sort(reverse=True)
    return [candidate for _score, candidate in ranked[:normalized_max_promoted]]


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
