from __future__ import annotations

from datetime import datetime
import json
import math
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.browsing_context import (
    aggregate_context_count as browsing_context_count,
    aggregate_evidence_value as browsing_evidence_value,
    aggregate_weighted_evidence_value as browsing_weighted_evidence_value,
    context_evidence_from_dicts,
    decay_context_evidence,
    merge_context_evidence,
    normalize_context_key,
)
from lexishift_core.srs.browsing_identity import (
    aggregate_reading_confidence,
    aggregate_target_key,
    build_browsing_target_key,
    candidate_target_key,
    merge_observation_sources,
    normalize_observation_sources,
    observation_source_for_side,
    resolve_reading_confidence,
)
from lexishift_core.srs.browsing_models import (
    BrowsingAdmissionCandidate,
    BrowsingAdmissionSimulationResult,
    BrowsingAdmissionSimulationRow,
    BrowsingAdmissionStrength,
    BrowsingSignalAggregate,
    BrowsingSignalContextEvidence,  # noqa: F401 - compatibility re-export.
    BrowsingSignalIngestPolicy,
    BrowsingSignalIngestResult,
    BrowsingSignalPacket,
    BrowsingSignalPacketEntry,  # noqa: F401 - compatibility re-export.
    BrowsingSignalStore,
)
from lexishift_core.srs.browsing_probability import (
    combined_probability,
    lane_probability_by_key,
)
from lexishift_core.srs.time import format_ts, now_utc, parse_ts

BROWSING_SIGNAL_SOURCE = "source"
BROWSING_SIGNAL_TARGET = "target"
BROWSING_SIGNAL_REPLACEMENT_EXPOSURE = "replacement_exposure"
BROWSING_SIGNAL_SIDES = frozenset(
    {
        BROWSING_SIGNAL_SOURCE,
        BROWSING_SIGNAL_TARGET,
        BROWSING_SIGNAL_REPLACEMENT_EXPOSURE,
    }
)
BROWSING_STRENGTH_OFF = "off"
BROWSING_STRENGTH_BALANCED = "balanced"
BROWSING_STRENGTH_STRONG = "strong"
MIN_BROWSING_EVIDENCE_MASS = 3.0
MIN_BROWSING_EVIDENCE_CONTEXTS = 2
COMMONNESS_SALIENCE_EXTRA_MASS = 18.0


def browsing_strength_presets() -> dict[str, BrowsingAdmissionStrength]:
    return {
        BROWSING_STRENGTH_OFF: BrowsingAdmissionStrength(
            name=BROWSING_STRENGTH_OFF,
            browsing_alpha=0.0,
            max_browsing_boost=1.0,
            browsing_budget_share=0.0,
        ),
        BROWSING_STRENGTH_BALANCED: BrowsingAdmissionStrength(
            name=BROWSING_STRENGTH_BALANCED,
            browsing_alpha=0.22,
            max_browsing_boost=1.35,
            browsing_budget_share=0.30,
            min_browsing_signal=0.25,
            min_fractional_browsing_budget=0.50,
        ),
        BROWSING_STRENGTH_STRONG: BrowsingAdmissionStrength(
            name=BROWSING_STRENGTH_STRONG,
            browsing_alpha=0.45,
            max_browsing_boost=1.65,
            browsing_budget_share=0.55,
            min_browsing_signal=0.25,
            min_fractional_browsing_budget=0.35,
        ),
    }


def browsing_signal_store_from_dict(data: Mapping[str, object]) -> BrowsingSignalStore:
    raw_items = data.get("items")
    items: dict[str, BrowsingSignalAggregate] = {}
    if isinstance(raw_items, Mapping):
        for key, value in raw_items.items():
            if not isinstance(value, Mapping):
                continue
            aggregate = browsing_signal_aggregate_from_dict(
                value,
                fallback_key=str(key),
                fallback_lemma=str(key),
            )
            if aggregate.target_lemma:
                items[aggregate_target_key(aggregate)] = aggregate
    return BrowsingSignalStore(
        pair=str(data.get("pair", "") or ""),
        profile_id=str(data.get("profile_id", "") or "default"),
        items=items,
        version=max(1, int(_safe_float(data.get("version")) or 1)),
        updated_at=_optional_str(data.get("updated_at")),
        policy_version=str(data.get("policy_version", "") or "browsing_signal_aggregate_v1"),
    )


def browsing_signal_aggregate_from_dict(
    data: Mapping[str, object],
    *,
    fallback_key: str = "",
    fallback_lemma: str = "",
) -> BrowsingSignalAggregate:
    target_lemma = str(data.get("target_lemma", "") or fallback_lemma).strip()
    target_reading = str(
        data.get("target_reading") or data.get("targetReading") or data.get("reading") or ""
    ).strip()
    target_key = build_browsing_target_key(
        target_lemma=target_lemma,
        target_reading=target_reading,
        target_key=data.get("target_key") or data.get("targetKey") or fallback_key,
    )
    return BrowsingSignalAggregate(
        target_lemma=target_lemma,
        target_key=target_key,
        target_reading=target_reading,
        source_hit_count=max(0.0, _safe_float(data.get("source_hit_count")) or 0.0),
        target_hit_count=max(0.0, _safe_float(data.get("target_hit_count")) or 0.0),
        replacement_exposure_count=max(
            0.0,
            _safe_float(data.get("replacement_exposure_count")) or 0.0,
        ),
        source_mapping_confidence=_clamp01(data.get("source_mapping_confidence")),
        reading_confidence=resolve_reading_confidence(data.get("reading_confidence")),
        observation_sources=normalize_observation_sources(data.get("observation_sources")),
        context_evidence=context_evidence_from_dicts(
            data.get("context_evidence") or data.get("contextEvidence") or data.get("contexts"),
            safe_float_fn=_safe_float,
            optional_str_fn=_optional_str,
        ),
        last_seen_at=_optional_str(data.get("last_seen_at")),
        decayed_at=_optional_str(data.get("decayed_at")),
    )


def load_browsing_signal_store(path: Path) -> BrowsingSignalStore:
    if not path.exists():
        return BrowsingSignalStore(pair="")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return BrowsingSignalStore(pair="")
    if not isinstance(payload, Mapping):
        return BrowsingSignalStore(pair="")
    return browsing_signal_store_from_dict(payload)


def save_browsing_signal_store(store: BrowsingSignalStore, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(store.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def maintain_browsing_signal_store(
    store: BrowsingSignalStore,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
    now: Optional[datetime] = None,
) -> BrowsingSignalStore:
    policy = policy or BrowsingSignalIngestPolicy()
    now = now or now_utc()
    if not store.pair and not store.items:
        return store
    decayed_items = {
        aggregate_target_key(item): _decay_aggregate(item, policy=policy, now=now)
        for item in store.items.values()
    }
    retained = _prune_aggregates(decayed_items, policy=policy)
    return BrowsingSignalStore(
        pair=store.pair,
        profile_id=store.profile_id,
        items=retained,
        version=store.version,
        updated_at=format_ts(now),
        policy_version=policy.version,
    )


def ingest_browsing_signal_packet(
    store: BrowsingSignalStore,
    packet: BrowsingSignalPacket,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
    now: Optional[datetime] = None,
) -> BrowsingSignalIngestResult:
    policy = policy or BrowsingSignalIngestPolicy()
    now = now or now_utc()
    now_text = format_ts(now)
    pair = str(packet.pair or store.pair or "").strip()
    profile_id = str(packet.profile_id or store.profile_id or "default").strip() or "default"
    decayed_items = {
        aggregate_target_key(item): _decay_aggregate(item, policy=policy, now=now)
        for item in store.items.values()
    }

    capped_signal_count = 0
    accepted_signal_count = 0
    packet_signals = tuple(packet.signals or ())
    accepted_packet_signals = packet_signals[: max(0, int(policy.max_signals_per_packet))]
    dropped_signal_count = max(0, len(packet_signals) - len(accepted_packet_signals))

    for signal in accepted_packet_signals:
        lemma = str(signal.target_lemma or "").strip()
        side = _normalize_signal_side(signal.side)
        if not lemma or not side:
            dropped_signal_count += 1
            continue
        raw_count = max(0.0, _safe_float(signal.count) or 0.0)
        if raw_count <= 0.0:
            dropped_signal_count += 1
            continue
        capped_count = min(raw_count, max(0.0, float(policy.max_count_per_signal)))
        if capped_count < raw_count:
            capped_signal_count += 1
        target_key = build_browsing_target_key(
            target_lemma=lemma,
            target_reading=signal.target_reading,
            target_key=signal.target_key,
        )
        current = decayed_items.get(target_key) or BrowsingSignalAggregate(
            target_lemma=lemma,
            target_key=target_key,
            target_reading=str(signal.target_reading or "").strip(),
            reading_confidence=_clamp01(signal.reading_confidence),
        )
        source_count = current.source_hit_count
        target_count = current.target_hit_count
        replacement_count = current.replacement_exposure_count
        mapping_confidence = current.source_mapping_confidence
        reading_confidence = max(
            aggregate_reading_confidence(current),
            _clamp01(signal.reading_confidence),
        )
        observation_sources = merge_observation_sources(
            current.observation_sources,
            (
                observation_source_for_side(
                    explicit=signal.observation_source,
                    side=signal.side,
                ),
            ),
        )
        if side == BROWSING_SIGNAL_SOURCE:
            confidence = _clamp01(signal.source_mapping_confidence)
            source_count += capped_count * confidence
            mapping_confidence = max(mapping_confidence, confidence)
            context_count = capped_count * confidence
        elif side == BROWSING_SIGNAL_TARGET:
            target_count += capped_count
            context_count = capped_count
        elif side == BROWSING_SIGNAL_REPLACEMENT_EXPOSURE:
            replacement_count += capped_count
            context_count = capped_count
        else:
            context_count = 0.0
        context_evidence = merge_context_evidence(
            current.context_evidence,
            context_key=normalize_context_key(signal.context_key),
            side=side,
            count=context_count,
            policy=policy,
            now_text=now_text,
        )
        decayed_items[target_key] = BrowsingSignalAggregate(
            target_lemma=lemma,
            target_key=target_key,
            target_reading=str(signal.target_reading or current.target_reading or "").strip(),
            source_hit_count=source_count,
            target_hit_count=target_count,
            replacement_exposure_count=replacement_count,
            source_mapping_confidence=mapping_confidence,
            reading_confidence=reading_confidence,
            observation_sources=observation_sources,
            context_evidence=context_evidence,
            last_seen_at=now_text,
            decayed_at=now_text,
        )
        accepted_signal_count += 1

    retained = _prune_aggregates(decayed_items, policy=policy)
    pruned_item_count = max(0, len(decayed_items) - len(retained))
    updated_store = BrowsingSignalStore(
        pair=pair,
        profile_id=profile_id,
        items=retained,
        version=store.version,
        updated_at=now_text,
        policy_version=policy.version,
    )
    return BrowsingSignalIngestResult(
        store=updated_store,
        input_signal_count=len(packet_signals),
        accepted_signal_count=accepted_signal_count,
        dropped_signal_count=dropped_signal_count,
        capped_signal_count=capped_signal_count,
        pruned_item_count=pruned_item_count,
        retained_item_count=len(retained),
    )


def browsing_raw_value(
    aggregate: BrowsingSignalAggregate | None,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> float:
    policy = policy or BrowsingSignalIngestPolicy()
    if aggregate is None:
        return 0.0
    raw = (
        max(0.0, aggregate.source_hit_count)
        + max(0.0, aggregate.target_hit_count)
        + max(0.0, aggregate.replacement_exposure_count)
        * max(0.0, policy.replacement_exposure_weight)
    )
    return raw * aggregate_reading_confidence(aggregate)


def browsing_signal_value(
    aggregate: BrowsingSignalAggregate | None,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> float:
    policy = policy or BrowsingSignalIngestPolicy()
    raw = browsing_weighted_evidence_value(aggregate, policy=policy)
    if raw <= 0.0:
        return 0.0
    return _clamp01(math.log1p(raw) / math.log1p(max(0.01, policy.browsing_signal_cap)))


def browsing_boost_value(
    signal_value: float,
    *,
    candidate: Optional[BrowsingAdmissionCandidate] = None,
    strength: Optional[BrowsingAdmissionStrength] = None,
) -> float:
    strength = strength or browsing_strength_presets()[BROWSING_STRENGTH_BALANCED]
    fit = 1.0
    if candidate is not None:
        fit = (
            _clamp01(candidate.readiness_multiplier)
            * _clamp01(candidate.source_confidence)
            * (
                1.0
                + max(0.0, strength.preference_alignment_weight)
                * _clamp01(candidate.explicit_preference_fit)
            )
        )
    return 1.0 + min(
        max(0.0, strength.max_browsing_boost - 1.0),
        max(0.0, strength.browsing_alpha) * _clamp01(signal_value) * fit,
    )


def simulate_browsing_admission(
    candidates: Sequence[BrowsingAdmissionCandidate],
    *,
    store: BrowsingSignalStore,
    admission_budget: int,
    strength: BrowsingAdmissionStrength,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
    suppressed_lemmas: Optional[Mapping[str, str]] = None,
    now: Optional[datetime] = None,
) -> BrowsingAdmissionSimulationResult:
    policy = policy or BrowsingSignalIngestPolicy()
    store = maintain_browsing_signal_store(store, policy=policy, now=now)
    budget = max(0, int(admission_budget))
    suppressed = {
        str(lemma or "").strip(): str(reason or "").strip() or "suppressed"
        for lemma, reason in dict(suppressed_lemmas or {}).items()
        if str(lemma or "").strip()
    }
    neutral_ranked = sorted(
        candidates,
        key=lambda item: (-float(item.neutral_score), item.lemma),
    )
    neutral_rank_by_key = {
        candidate_target_key(candidate): index + 1 for index, candidate in enumerate(neutral_ranked)
    }
    active_neutral_ranked = [
        candidate
        for candidate in neutral_ranked
        if _suppressed_reason_for_candidate(candidate, suppressed) is None
    ]
    neutral_selected_lemmas = tuple(candidate.lemma for candidate in active_neutral_ranked[:budget])
    neutral_selected_keys = {
        candidate_target_key(candidate) for candidate in active_neutral_ranked[:budget]
    }

    scored_rows: list[dict[str, object]] = []
    for candidate in neutral_ranked:
        target_key = candidate_target_key(candidate)
        aggregate = _aggregate_for_candidate(store, candidate)
        signal = browsing_signal_value(aggregate, policy=policy)
        evidence = browsing_evidence_value(aggregate, policy=policy)
        context_count = browsing_context_count(aggregate, policy=policy)
        quality_multiplier = browsing_quality_multiplier(candidate)
        count_multiplier = browsing_count_multiplier(aggregate, policy=policy)
        salience_multiplier = browsing_salience_multiplier(
            aggregate,
            candidate=candidate,
            policy=policy,
        )
        specificity_multiplier = browsing_specificity_multiplier(candidate)
        effective_signal = browsing_effective_signal_value(
            signal,
            quality_multiplier=quality_multiplier,
            count_multiplier=count_multiplier,
            salience_multiplier=salience_multiplier,
            specificity_multiplier=specificity_multiplier,
        )
        boost = browsing_boost_value(effective_signal, candidate=candidate, strength=strength)
        suppressed_reason = _suppressed_reason_for_candidate(candidate, suppressed)
        final_score = 0.0 if suppressed_reason else float(candidate.neutral_score) * boost
        scored_rows.append(
            {
                "candidate": candidate,
                "lemma": candidate.lemma,
                "target_key": target_key,
                "target_reading": candidate.target_reading,
                "neutral_rank": neutral_rank_by_key[target_key],
                "neutral_score": float(candidate.neutral_score),
                "browsing_signal": signal,
                "browsing_evidence": evidence,
                "browsing_context_count": context_count,
                "effective_browsing_signal": effective_signal,
                "browsing_quality_multiplier": quality_multiplier,
                "browsing_count_multiplier": count_multiplier,
                "browsing_salience_multiplier": salience_multiplier,
                "browsing_specificity_multiplier": specificity_multiplier,
                "browsing_boost": boost,
                "final_score": final_score,
                "suppressed_reason": suppressed_reason,
            }
        )

    active_rows = [row for row in scored_rows if not row.get("suppressed_reason")]
    signal_volume = sum(
        _safe_float(row.get("effective_browsing_signal")) or 0.0 for row in active_rows
    )
    volume_factor = 0.0
    if signal_volume > 0.0 and strength.volume_tau > 0.0:
        volume_factor = 1.0 - math.exp(-signal_volume / strength.volume_tau)
    raw_browsing_budget = (
        budget * _clamp01(strength.browsing_budget_share) * _clamp01(volume_factor)
    )
    browsing_budget = int(math.floor(raw_browsing_budget))
    browsing_pool = [
        row
        for row in active_rows
        if (_safe_float(row.get("effective_browsing_signal")) or 0.0)
        >= max(0.0, strength.min_browsing_signal)
    ]
    if (
        browsing_budget == 0
        and budget > 0
        and browsing_pool
        and _clamp01(strength.browsing_budget_share) > 0.0
        and raw_browsing_budget >= max(0.0, float(strength.min_fractional_browsing_budget))
    ):
        browsing_budget = 1
    browsing_budget = min(browsing_budget, budget, len(browsing_pool))
    selected_browsing = sorted(
        browsing_pool,
        key=lambda row: (
            -(_safe_float(row.get("final_score")) or 0.0),
            _safe_int(row.get("neutral_rank")),
            str(row["lemma"]),
        ),
    )[:browsing_budget]
    selected_keys = {str(row["target_key"]) for row in selected_browsing}
    general_budget = max(0, budget - len(selected_browsing))
    selected_general = [
        row
        for row in sorted(
            scored_rows,
            key=lambda item: (
                -(_safe_float(item.get("neutral_score")) or 0.0),
                _safe_int(item.get("neutral_rank")),
                str(item["lemma"]),
            ),
        )
        if str(row["target_key"]) not in selected_keys
    ][:general_budget]
    selected_keys.update(str(row["target_key"]) for row in selected_general)
    lane_by_key = {str(row["target_key"]): "browsing" for row in selected_browsing}
    lane_by_key.update({str(row["target_key"]): "general" for row in selected_general})
    browsing_probability_by_key = lane_probability_by_key(
        browsing_pool,
        budget=browsing_budget,
        mass_key="final_score",
    )
    general_probability_by_key = lane_probability_by_key(
        active_rows,
        budget=general_budget,
        mass_key="neutral_score",
    )

    final_ranked = sorted(
        scored_rows,
        key=lambda row: (
            -(_safe_float(row.get("final_score")) or 0.0),
            _safe_int(row.get("neutral_rank")),
            str(row["lemma"]),
        ),
    )
    final_rank_by_key = {
        str(row["target_key"]): index + 1 for index, row in enumerate(final_ranked)
    }
    rows = [
        BrowsingAdmissionSimulationRow(
            lemma=str(row["lemma"]),
            target_key=str(row["target_key"]),
            target_reading=str(row.get("target_reading") or ""),
            neutral_rank=_safe_int(row.get("neutral_rank")),
            final_rank=final_rank_by_key[str(row["target_key"])],
            neutral_score=_safe_float(row.get("neutral_score")) or 0.0,
            final_score=_safe_float(row.get("final_score")) or 0.0,
            browsing_signal=_safe_float(row.get("browsing_signal")) or 0.0,
            browsing_evidence=_safe_float(row.get("browsing_evidence")) or 0.0,
            browsing_context_count=_safe_int(row.get("browsing_context_count")),
            effective_browsing_signal=_safe_float(row.get("effective_browsing_signal")) or 0.0,
            browsing_quality_multiplier=_safe_float(row.get("browsing_quality_multiplier")) or 0.0,
            browsing_count_multiplier=_safe_float(row.get("browsing_count_multiplier")) or 0.0,
            browsing_salience_multiplier=(
                _safe_float(row.get("browsing_salience_multiplier")) or 0.0
            ),
            browsing_specificity_multiplier=(
                _safe_float(row.get("browsing_specificity_multiplier")) or 0.0
            ),
            browsing_boost=_safe_float(row.get("browsing_boost")) or 0.0,
            selected=str(row["target_key"]) in selected_keys,
            selected_lane=lane_by_key.get(str(row["target_key"]), "not_selected"),
            neutral_selected=str(row["target_key"]) in neutral_selected_keys,
            suppressed_reason=(
                str(row["suppressed_reason"]) if row.get("suppressed_reason") else None
            ),
            deterministic_selection_probability=(
                1.0 if str(row["target_key"]) in selected_keys else 0.0
            ),
            browsing_lane_probability=browsing_probability_by_key.get(
                str(row["target_key"]),
                0.0,
            ),
            general_lane_probability=general_probability_by_key.get(
                str(row["target_key"]),
                0.0,
            ),
            approximate_selection_probability=combined_probability(
                browsing_probability_by_key.get(str(row["target_key"]), 0.0),
                general_probability_by_key.get(str(row["target_key"]), 0.0),
            ),
        )
        for row in final_ranked
    ]
    selected_order = tuple(
        str(row["lemma"]) for row in list(selected_browsing) + list(selected_general)
    )
    browsing_relevant_selected_count = sum(
        1
        for row in rows
        if row.selected and row.effective_browsing_signal >= max(0.0, strength.min_browsing_signal)
    )
    browsing_driven_count = sum(1 for row in rows if row.selected and not row.neutral_selected)
    return BrowsingAdmissionSimulationResult(
        strength=strength.name,
        admission_budget=budget,
        browsing_budget=browsing_budget,
        general_budget=general_budget,
        signal_volume=signal_volume,
        volume_factor=volume_factor,
        selected_lemmas=selected_order,
        neutral_selected_lemmas=neutral_selected_lemmas,
        browsing_lane_count=len(selected_browsing),
        browsing_relevant_selected_count=browsing_relevant_selected_count,
        browsing_driven_count=browsing_driven_count,
        suppressed_count=len(suppressed),
        rows=tuple(rows),
    )


def browsing_effective_signal_value(
    signal_value: float,
    *,
    quality_multiplier: float = 1.0,
    count_multiplier: float = 1.0,
    salience_multiplier: float = 1.0,
    specificity_multiplier: float = 1.0,
) -> float:
    return _clamp01(
        _clamp01(signal_value)
        * _clamp01(quality_multiplier)
        * _clamp01(count_multiplier)
        * _clamp01(salience_multiplier)
        * max(0.0, min(1.25, float(specificity_multiplier))),
    )


def browsing_count_multiplier(
    aggregate: BrowsingSignalAggregate | None,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> float:
    evidence = browsing_evidence_value(aggregate, policy=policy)
    if evidence < MIN_BROWSING_EVIDENCE_MASS:
        return 0.0
    if aggregate is not None and aggregate.context_evidence:
        if browsing_context_count(aggregate, policy=policy) < MIN_BROWSING_EVIDENCE_CONTEXTS:
            return 0.0
    return 1.0


def browsing_salience_multiplier(
    aggregate: BrowsingSignalAggregate | None,
    *,
    candidate: Optional[BrowsingAdmissionCandidate] = None,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> float:
    if aggregate is None:
        return 1.0
    evidence = browsing_evidence_value(aggregate, policy=policy)
    if evidence <= 0.0 or candidate is None or not bool(candidate.lexical_commonness_known):
        return 1.0
    commonness = _clamp01(candidate.lexical_commonness)
    if commonness <= 0.0:
        return 1.0
    required_mass = MIN_BROWSING_EVIDENCE_MASS + (
        COMMONNESS_SALIENCE_EXTRA_MASS * commonness * commonness
    )
    return _clamp01(evidence / max(MIN_BROWSING_EVIDENCE_MASS, required_mass))


def browsing_quality_multiplier(candidate: Optional[BrowsingAdmissionCandidate]) -> float:
    if candidate is None:
        return 1.0
    return _clamp01(candidate.admission_suitability)


def browsing_specificity_multiplier(candidate: Optional[BrowsingAdmissionCandidate]) -> float:
    if candidate is None:
        return 1.0
    if not bool(candidate.lexical_commonness_known):
        return 0.75
    commonness = _clamp01(candidate.lexical_commonness)
    return max(0.65, min(1.15, 1.15 - (0.50 * commonness)))


def simulate_browsing_admission_presets(
    candidates: Sequence[BrowsingAdmissionCandidate],
    *,
    store: BrowsingSignalStore,
    admission_budget: int,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
    suppressed_lemmas: Optional[Mapping[str, str]] = None,
    now: Optional[datetime] = None,
) -> dict[str, BrowsingAdmissionSimulationResult]:
    return {
        name: simulate_browsing_admission(
            candidates,
            store=store,
            admission_budget=admission_budget,
            strength=strength,
            policy=policy,
            suppressed_lemmas=suppressed_lemmas,
            now=now,
        )
        for name, strength in browsing_strength_presets().items()
    }


def _decay_aggregate(
    aggregate: BrowsingSignalAggregate,
    *,
    policy: BrowsingSignalIngestPolicy,
    now: datetime,
) -> BrowsingSignalAggregate:
    anchor = parse_ts(aggregate.decayed_at) or parse_ts(aggregate.last_seen_at)
    if anchor is None:
        return aggregate
    elapsed_seconds = max(0.0, (now - anchor).total_seconds())
    elapsed_days = elapsed_seconds / 86400.0
    half_life_days = max(0.01, float(policy.half_life_days))
    multiplier = 0.5 ** (elapsed_days / half_life_days)
    return BrowsingSignalAggregate(
        target_lemma=aggregate.target_lemma,
        target_key=aggregate_target_key(aggregate),
        target_reading=aggregate.target_reading,
        source_hit_count=max(0.0, aggregate.source_hit_count) * multiplier,
        target_hit_count=max(0.0, aggregate.target_hit_count) * multiplier,
        replacement_exposure_count=max(0.0, aggregate.replacement_exposure_count) * multiplier,
        source_mapping_confidence=aggregate.source_mapping_confidence,
        reading_confidence=aggregate_reading_confidence(aggregate),
        observation_sources=aggregate.observation_sources,
        context_evidence=decay_context_evidence(
            aggregate.context_evidence,
            multiplier=multiplier,
        ),
        last_seen_at=aggregate.last_seen_at,
        decayed_at=format_ts(now),
    )


def _prune_aggregates(
    items: Mapping[str, BrowsingSignalAggregate],
    *,
    policy: BrowsingSignalIngestPolicy,
) -> dict[str, BrowsingSignalAggregate]:
    threshold = max(0.0, float(policy.prune_signal_below))
    candidates = [
        item
        for item in items.values()
        if item.target_lemma and browsing_signal_value(item, policy=policy) >= threshold
    ]
    candidates.sort(
        key=lambda item: (
            -browsing_raw_value(item, policy=policy),
            str(item.last_seen_at or ""),
            aggregate_target_key(item),
        )
    )
    retained = candidates[: max(0, int(policy.max_items_per_store))]
    return {
        aggregate_target_key(item): item
        for item in sorted(retained, key=lambda item: aggregate_target_key(item))
    }


def _normalize_signal_side(value: object) -> str:
    side = str(value or "").strip().lower()
    return side if side in BROWSING_SIGNAL_SIDES else ""


def _aggregate_for_candidate(
    store: BrowsingSignalStore,
    candidate: BrowsingAdmissionCandidate,
) -> BrowsingSignalAggregate | None:
    target_key = candidate_target_key(candidate)
    if target_key in store.items:
        return store.items[target_key]
    if candidate.lemma in store.items:
        return store.items[candidate.lemma]
    return None


def _suppressed_reason_for_candidate(
    candidate: BrowsingAdmissionCandidate,
    suppressed: Mapping[str, str],
) -> str | None:
    return suppressed.get(candidate_target_key(candidate)) or suppressed.get(candidate.lemma)


def _optional_str(value: object) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _safe_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        parsed = float(value)
    elif isinstance(value, (float, int)):
        parsed = float(value)
    else:
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError):
            return None
    return parsed if parsed == parsed else None


def _safe_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(str(value or "").strip() or "0")
    except (TypeError, ValueError):
        return 0


def _clamp01(value: object) -> float:
    parsed = _safe_float(value)
    if parsed is None:
        return 0.0
    return max(0.0, min(1.0, parsed))
