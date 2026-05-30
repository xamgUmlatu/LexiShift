from __future__ import annotations

from collections.abc import Iterable as IterableCollection
from dataclasses import dataclass, field
from datetime import datetime
from math import floor
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.srs import SrsSettings, SrsStore, srs_item_is_active
from lexishift_core.srs.browsing_admission import (
    BrowsingAdmissionCandidate,
    BrowsingAdmissionSimulationResult,
    BrowsingSignalIngestPolicy,
    BrowsingSignalStore,
    simulate_browsing_admission_presets,
)
from lexishift_core.srs.growth import SrsGrowthConfig, grow_srs_store, plan_srs_growth
from lexishift_core.srs.scheduler import (
    RATING_AGAIN,
    RATING_EASY,
    RATING_GOOD,
    RATING_HARD,
    select_active_items,
)
from lexishift_core.srs.selector import SelectorCandidate, SelectorConfig, SelectorWeights
from lexishift_core.srs.signal_queue import SIGNAL_FEEDBACK, SrsSignalEvent
from lexishift_core.srs.source import SOURCE_FREQUENCY_LIST
from lexishift_core.srs.time import now_utc, parse_ts


STALE_ACTIVE_AGE_DAYS = 7
SECONDS_PER_DAY = 24 * 60 * 60


@dataclass(frozen=True)
class FeedbackWindowStats:
    pair: str
    window_size_requested: int
    window_size_effective: int
    feedback_count: int
    count_again: int
    count_hard: int
    count_good: int
    count_easy: int
    retention_ratio: Optional[float]
    strain_ratio: Optional[float]


@dataclass(frozen=True)
class AdmissionRefreshThresholds:
    retention_low: float = 0.55
    retention_mid: float = 0.70
    due_pressure_high: float = 0.80


@dataclass(frozen=True)
class AdmissionRefreshPolicy:
    feedback_window_size: int = 100
    min_feedback_events: int = 8
    partial_admission_ratio: float = 0.50
    thresholds: AdmissionRefreshThresholds = field(default_factory=AdmissionRefreshThresholds)
    max_active_items_override: Optional[int] = None
    max_new_items_override: Optional[int] = None
    active_item_ids: Optional[Sequence[str]] = None
    allowed_pos: Optional[set[str]] = None
    selector_config: SelectorConfig = field(
        default_factory=lambda: SelectorConfig(
            weights=SelectorWeights(
                base_freq=0.80,
                topic_bias=0.0,
                user_pref=0.0,
                confidence=0.20,
                difficulty_target=0.0,
            ),
            top_n=200,
        )
    )
    default_source_type: str = SOURCE_FREQUENCY_LIST
    initial_stability: float = 1.0
    initial_difficulty: float = 0.5
    blocked_lemmas: Optional[set[str]] = None


@dataclass(frozen=True)
class AdmissionRefreshDecision:
    pair: str
    max_active_items: int
    max_new_items_per_day: int
    active_count: int
    active_zero_exposure_zero_feedback: int
    active_zero_exposure_zero_feedback_age_unknown: int
    active_stale_zero_exposure_zero_feedback: int
    stale_active_age_days: int
    due_count: int
    due_pressure: float
    capacity_budget: int
    base_admission_budget: int
    admission_budget: int
    reason_code: str
    notes: Sequence[str]
    feedback_window: FeedbackWindowStats


@dataclass(frozen=True)
class AdmissionRefreshDiagnostics:
    filtered_by_pos: int = 0
    blocked_by_lifecycle: int = 0
    blocked_lemmas: Sequence[str] = field(default_factory=tuple)
    admitted_by_pos_bucket: Mapping[str, int] = field(default_factory=dict)
    unknown_pos_seen: int = 0
    allowed_pos: Sequence[str] = field(default_factory=tuple)
    candidate_pool_effective: int = 0


@dataclass(frozen=True)
class AdmissionRefreshResult:
    decision: AdmissionRefreshDecision
    candidate_pool_size: int
    admitted_count: int
    selected_lemmas: Sequence[str]
    applied: bool
    diagnostics: AdmissionRefreshDiagnostics = field(default_factory=AdmissionRefreshDiagnostics)


def preview_browsing_admission_refresh(
    *,
    store: SrsStore,
    settings: SrsSettings,
    pair: str,
    candidates: Sequence[SelectorCandidate],
    events: Iterable[SrsSignalEvent],
    browsing_store: BrowsingSignalStore,
    policy: Optional[AdmissionRefreshPolicy] = None,
    browsing_policy: Optional[BrowsingSignalIngestPolicy] = None,
    row_limit: int = 20,
    now: Optional[datetime] = None,
) -> dict[str, object]:
    policy = policy or AdmissionRefreshPolicy()
    browsing_policy = browsing_policy or BrowsingSignalIngestPolicy()
    allowed_pos = _normalize_allowed_pos(policy.allowed_pos)
    blocked_lemmas = _resolve_lifecycle_blocked_lemmas(
        store=store,
        pair=pair,
        policy=policy,
    )
    decision = plan_admission_refresh(
        store=store,
        settings=settings,
        pair=pair,
        events=events,
        policy=policy,
        now=now,
    )
    if decision.admission_budget <= 0:
        return {
            "status": "skipped",
            "reason": decision.reason_code,
            "applied_to_actual_admission": False,
            "runtime_srs_mutation": False,
            "admission_budget": decision.admission_budget,
            "aggregate_item_count": len(browsing_store.items),
            "simulations": {},
        }

    effective_candidates = _apply_lifecycle_filter(
        _apply_allowed_pos_filter(candidates, allowed_pos=allowed_pos),
        blocked_lemmas=blocked_lemmas,
    )
    growth_config = SrsGrowthConfig(
        selector_config=policy.selector_config,
        coverage_scalar=1.0,
        max_new_items=decision.admission_budget,
        allowed_pos=allowed_pos or None,
        initial_stability=policy.initial_stability,
        initial_difficulty=policy.initial_difficulty,
        default_source_type=policy.default_source_type,
        confidence_min=None,
    )
    growth_plan = plan_srs_growth(
        effective_candidates,
        store=store,
        settings=settings,
        config=growth_config,
        allowed_pairs=[pair],
        allowed_pos=allowed_pos or None,
        blocked_lemmas=blocked_lemmas or None,
    )
    simulation_candidates = tuple(
        _browsing_candidate_from_scored(entry) for entry in growth_plan.scored
    )
    matching_signal_count = sum(
        1 for candidate in simulation_candidates if candidate.lemma in browsing_store.items
    )
    simulations = simulate_browsing_admission_presets(
        simulation_candidates,
        store=browsing_store,
        admission_budget=decision.admission_budget,
        policy=browsing_policy,
    )
    return {
        "status": "ok",
        "scope": "refresh_candidate_preview_only",
        "applied_to_actual_admission": False,
        "runtime_srs_mutation": False,
        "admission_budget": decision.admission_budget,
        "candidate_pool_effective": len(simulation_candidates),
        "aggregate_item_count": len(browsing_store.items),
        "matching_signal_count": matching_signal_count,
        "blocked_by_lifecycle": _count_blocked_by_lifecycle(candidates, blocked_lemmas),
        "blocked_lemmas": tuple(sorted(blocked_lemmas)),
        "neutral_selected_lemmas": tuple(candidate.lemma for candidate in growth_plan.selected),
        "simulations": {
            name: _simulation_preview(result, row_limit=row_limit)
            for name, result in simulations.items()
        },
    }


def compute_feedback_window_stats(
    events: Iterable[SrsSignalEvent],
    *,
    pair: str,
    window_size: int,
) -> FeedbackWindowStats:
    requested_size = max(1, int(window_size))
    feedback_events = [
        event for event in events if event.event_type == SIGNAL_FEEDBACK and event.pair == pair
    ]
    scoped = feedback_events[-requested_size:]

    count_again = 0
    count_hard = 0
    count_good = 0
    count_easy = 0
    for event in scoped:
        rating = str(event.rating or "").strip().lower()
        if rating == RATING_AGAIN:
            count_again += 1
        elif rating == RATING_HARD:
            count_hard += 1
        elif rating == RATING_GOOD:
            count_good += 1
        elif rating == RATING_EASY:
            count_easy += 1

    total = count_again + count_hard + count_good + count_easy
    retention_ratio = None
    strain_ratio = None
    if total > 0:
        retention_ratio = (count_good + count_easy) / total
        strain_ratio = (count_again + count_hard) / total

    return FeedbackWindowStats(
        pair=pair,
        window_size_requested=requested_size,
        window_size_effective=len(scoped),
        feedback_count=total,
        count_again=count_again,
        count_hard=count_hard,
        count_good=count_good,
        count_easy=count_easy,
        retention_ratio=retention_ratio,
        strain_ratio=strain_ratio,
    )


def plan_admission_refresh(
    *,
    store: SrsStore,
    settings: SrsSettings,
    pair: str,
    events: Iterable[SrsSignalEvent],
    policy: Optional[AdmissionRefreshPolicy] = None,
    now: Optional[datetime] = None,
) -> AdmissionRefreshDecision:
    policy = policy or AdmissionRefreshPolicy()
    now = now or now_utc()

    max_active_items = _resolve_positive_int(
        policy.max_active_items_override, fallback=settings.max_active_items, minimum=1
    )
    max_new_items = _resolve_non_negative_int(
        policy.max_new_items_override,
        fallback=settings.max_new_items_per_day,
    )
    active_item_id_set = _normalize_active_item_id_set(policy.active_item_ids)
    capacity_items = _active_capacity_items_for_pair(
        store,
        pair=pair,
        active_item_ids=active_item_id_set,
    )
    due_items = select_active_items(
        capacity_items,
        now=now,
        max_active=max_active_items,
        allowed_pairs=[pair],
    )
    due_count = len(due_items)
    due_pressure = due_count / float(max_active_items) if max_active_items > 0 else 1.0
    active_count = len(capacity_items)
    active_capacity_diagnostics = _active_capacity_diagnostics_for_pair(
        store,
        pair=pair,
        active_item_ids=active_item_id_set,
        now=now,
        stale_age_days=STALE_ACTIVE_AGE_DAYS,
    )

    capacity_budget = max(0, max_active_items - active_count)
    base_budget = min(max_new_items, capacity_budget)

    feedback_stats = compute_feedback_window_stats(
        events,
        pair=pair,
        window_size=policy.feedback_window_size,
    )

    admission_budget = base_budget
    reason_code = "normal"
    notes: list[str] = []
    if base_budget <= 0:
        admission_budget = 0
        reason_code = "capacity_exhausted"
        notes.append("No admission capacity remains under max_active_items.")
        stale_count = active_capacity_diagnostics["active_stale_zero_exposure_zero_feedback"]
        if stale_count > 0:
            notes.append(
                "Some active items are stale, unseen, and unreviewed; use dashboard "
                "diagnostics before adding an automatic release policy."
            )
    elif due_pressure > policy.thresholds.due_pressure_high:
        admission_budget = 0
        reason_code = "due_pressure_high"
        notes.append("Due pressure is above threshold; paused new admissions.")
    elif feedback_stats.feedback_count >= policy.min_feedback_events:
        retention = (
            feedback_stats.retention_ratio if feedback_stats.retention_ratio is not None else 1.0
        )
        if retention < policy.thresholds.retention_low:
            admission_budget = 0
            reason_code = "retention_low"
            notes.append("Retention is below low threshold; paused new admissions.")
        elif retention < policy.thresholds.retention_mid:
            admission_budget = max(1, int(floor(base_budget * policy.partial_admission_ratio)))
            reason_code = "retention_mid"
            notes.append("Retention is mid-range; reduced new admissions.")
    else:
        notes.append("Feedback window is small; using capacity-based admission budget.")

    return AdmissionRefreshDecision(
        pair=pair,
        max_active_items=max_active_items,
        max_new_items_per_day=max_new_items,
        active_count=active_count,
        active_zero_exposure_zero_feedback=active_capacity_diagnostics[
            "active_zero_exposure_zero_feedback"
        ],
        active_zero_exposure_zero_feedback_age_unknown=active_capacity_diagnostics[
            "active_zero_exposure_zero_feedback_age_unknown"
        ],
        active_stale_zero_exposure_zero_feedback=active_capacity_diagnostics[
            "active_stale_zero_exposure_zero_feedback"
        ],
        stale_active_age_days=STALE_ACTIVE_AGE_DAYS,
        due_count=due_count,
        due_pressure=round(due_pressure, 6),
        capacity_budget=capacity_budget,
        base_admission_budget=base_budget,
        admission_budget=admission_budget,
        reason_code=reason_code,
        notes=tuple(notes),
        feedback_window=feedback_stats,
    )


def apply_admission_refresh(
    *,
    store: SrsStore,
    settings: SrsSettings,
    pair: str,
    candidates: Sequence[SelectorCandidate],
    events: Iterable[SrsSignalEvent],
    policy: Optional[AdmissionRefreshPolicy] = None,
    now: Optional[datetime] = None,
) -> tuple[SrsStore, AdmissionRefreshResult]:
    policy = policy or AdmissionRefreshPolicy()
    allowed_pos = _normalize_allowed_pos(policy.allowed_pos)
    blocked_lemmas = _resolve_lifecycle_blocked_lemmas(
        store=store,
        pair=pair,
        policy=policy,
    )
    filtered_by_pos = _count_filtered_by_allowed_pos(candidates, allowed_pos=allowed_pos)
    blocked_by_lifecycle = _count_blocked_by_lifecycle(candidates, blocked_lemmas)
    unknown_pos_seen = _count_unknown_pos(candidates)
    decision = plan_admission_refresh(
        store=store,
        settings=settings,
        pair=pair,
        events=events,
        policy=policy,
        now=now,
    )
    effective_candidates = _apply_lifecycle_filter(
        _apply_allowed_pos_filter(candidates, allowed_pos=allowed_pos),
        blocked_lemmas=blocked_lemmas,
    )
    if decision.admission_budget <= 0:
        diagnostics = AdmissionRefreshDiagnostics(
            filtered_by_pos=filtered_by_pos,
            blocked_by_lifecycle=blocked_by_lifecycle,
            blocked_lemmas=tuple(sorted(blocked_lemmas)),
            admitted_by_pos_bucket={},
            unknown_pos_seen=unknown_pos_seen,
            allowed_pos=tuple(sorted(allowed_pos)),
            candidate_pool_effective=len(effective_candidates),
        )
        return store, AdmissionRefreshResult(
            decision=decision,
            candidate_pool_size=len(candidates),
            admitted_count=0,
            selected_lemmas=tuple(),
            applied=False,
            diagnostics=diagnostics,
        )

    growth_config = SrsGrowthConfig(
        selector_config=policy.selector_config,
        coverage_scalar=1.0,
        max_new_items=decision.admission_budget,
        allowed_pos=allowed_pos or None,
        initial_stability=policy.initial_stability,
        initial_difficulty=policy.initial_difficulty,
        default_source_type=policy.default_source_type,
        confidence_min=None,
    )
    updated_store, growth_plan = grow_srs_store(
        effective_candidates,
        store=store,
        settings=settings,
        config=growth_config,
        allowed_pairs=[pair],
        allowed_pos=allowed_pos or None,
        blocked_lemmas=blocked_lemmas or None,
        now=now,
    )
    selected_lemmas = tuple(candidate.lemma for candidate in growth_plan.selected)
    diagnostics = AdmissionRefreshDiagnostics(
        filtered_by_pos=filtered_by_pos,
        blocked_by_lifecycle=blocked_by_lifecycle,
        blocked_lemmas=tuple(sorted(blocked_lemmas)),
        admitted_by_pos_bucket=_count_admitted_by_pos_bucket(growth_plan.selected),
        unknown_pos_seen=unknown_pos_seen,
        allowed_pos=tuple(sorted(allowed_pos)),
        candidate_pool_effective=len(effective_candidates),
    )
    return updated_store, AdmissionRefreshResult(
        decision=decision,
        candidate_pool_size=len(candidates),
        admitted_count=len(selected_lemmas),
        selected_lemmas=selected_lemmas,
        applied=len(selected_lemmas) > 0,
        diagnostics=diagnostics,
    )


def feedback_window_stats_to_dict(stats: FeedbackWindowStats) -> dict[str, object]:
    return {
        "pair": stats.pair,
        "window_size_requested": stats.window_size_requested,
        "window_size_effective": stats.window_size_effective,
        "feedback_count": stats.feedback_count,
        "count_again": stats.count_again,
        "count_hard": stats.count_hard,
        "count_good": stats.count_good,
        "count_easy": stats.count_easy,
        "retention_ratio": stats.retention_ratio,
        "strain_ratio": stats.strain_ratio,
    }


def admission_refresh_result_to_dict(result: AdmissionRefreshResult) -> dict[str, object]:
    decision = result.decision
    return {
        "pair": decision.pair,
        "max_active_items": decision.max_active_items,
        "max_new_items_per_day": decision.max_new_items_per_day,
        "active_count": decision.active_count,
        "active_zero_exposure_zero_feedback": decision.active_zero_exposure_zero_feedback,
        "active_zero_exposure_zero_feedback_age_unknown": (
            decision.active_zero_exposure_zero_feedback_age_unknown
        ),
        "active_stale_zero_exposure_zero_feedback": (
            decision.active_stale_zero_exposure_zero_feedback
        ),
        "stale_active_age_days": decision.stale_active_age_days,
        "due_count": decision.due_count,
        "due_pressure": decision.due_pressure,
        "capacity_budget": decision.capacity_budget,
        "base_admission_budget": decision.base_admission_budget,
        "admission_budget": decision.admission_budget,
        "reason_code": decision.reason_code,
        "notes": list(decision.notes),
        "feedback_window": feedback_window_stats_to_dict(decision.feedback_window),
        "candidate_pool_size": result.candidate_pool_size,
        "admitted_count": result.admitted_count,
        "selected_lemmas": list(result.selected_lemmas),
        "diagnostics": {
            "filtered_by_pos": int(result.diagnostics.filtered_by_pos),
            "blocked_by_lifecycle": int(result.diagnostics.blocked_by_lifecycle),
            "blocked_lemmas": list(result.diagnostics.blocked_lemmas),
            "admitted_by_pos_bucket": {
                str(key): int(value)
                for key, value in dict(result.diagnostics.admitted_by_pos_bucket).items()
            },
            "unknown_pos_seen": int(result.diagnostics.unknown_pos_seen),
            "allowed_pos": list(result.diagnostics.allowed_pos),
            "candidate_pool_effective": int(result.diagnostics.candidate_pool_effective),
        },
        "applied": result.applied,
    }


def _resolve_positive_int(value: Optional[int], *, fallback: int, minimum: int) -> int:
    if value is None:
        parsed = int(fallback)
    else:
        parsed = int(value)
    return max(minimum, parsed)


def _resolve_non_negative_int(value: Optional[int], *, fallback: int) -> int:
    if value is None:
        parsed = int(fallback)
    else:
        parsed = int(value)
    return max(0, parsed)


def _normalize_active_item_id_set(value: Optional[Sequence[str]]) -> Optional[set[str]]:
    if value is None:
        return None
    if isinstance(value, (str, bytes, bytearray)):
        return set()
    return {str(item_id or "").strip() for item_id in value if str(item_id or "").strip()}


def _active_capacity_items_for_pair(
    store: SrsStore,
    *,
    pair: str,
    active_item_ids: Optional[set[str]],
) -> tuple:
    return tuple(
        item
        for item in store.items
        if item.language_pair == pair
        and srs_item_is_active(item)
        and (active_item_ids is None or item.item_id in active_item_ids)
    )


def _active_capacity_diagnostics_for_pair(
    store: SrsStore,
    *,
    pair: str,
    active_item_ids: Optional[set[str]],
    now: datetime,
    stale_age_days: int,
) -> dict[str, int]:
    zero_unseen = 0
    age_unknown = 0
    stale_unseen = 0
    stale_seconds = max(0, int(stale_age_days)) * SECONDS_PER_DAY
    for item in store.items:
        if item.language_pair != pair or not srs_item_is_active(item):
            continue
        if active_item_ids is not None and item.item_id not in active_item_ids:
            continue
        if int(item.exposures or 0) > 0 or len(item.history or ()) > 0:
            continue
        zero_unseen += 1
        admitted_at = parse_ts(item.admitted_at)
        if admitted_at is None:
            age_unknown += 1
            continue
        if (now - admitted_at).total_seconds() >= stale_seconds:
            stale_unseen += 1
    return {
        "active_zero_exposure_zero_feedback": zero_unseen,
        "active_zero_exposure_zero_feedback_age_unknown": age_unknown,
        "active_stale_zero_exposure_zero_feedback": stale_unseen,
    }


def _normalize_allowed_pos(value: Optional[IterableCollection[str]]) -> set[str]:
    if not value:
        return set()
    return {str(item).strip().lower() for item in value if str(item).strip()}


def _normalize_blocked_lemmas(value: Optional[IterableCollection[str]]) -> set[str]:
    if not value:
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def _resolve_lifecycle_blocked_lemmas(
    *,
    store: SrsStore,
    pair: str,
    policy: AdmissionRefreshPolicy,
) -> set[str]:
    blocked = _normalize_blocked_lemmas(policy.blocked_lemmas)
    for item in store.items:
        if item.language_pair != pair or srs_item_is_active(item):
            continue
        lemma = str(item.lemma or "").strip()
        if lemma:
            blocked.add(lemma)
    return blocked


def _apply_allowed_pos_filter(
    candidates: Sequence[SelectorCandidate],
    *,
    allowed_pos: set[str],
) -> list[SelectorCandidate]:
    if not allowed_pos:
        return list(candidates)
    filtered: list[SelectorCandidate] = []
    for candidate in candidates:
        bucket = _resolve_candidate_pos_bucket(candidate)
        if bucket and bucket not in allowed_pos:
            continue
        filtered.append(candidate)
    return filtered


def _apply_lifecycle_filter(
    candidates: Sequence[SelectorCandidate],
    *,
    blocked_lemmas: set[str],
) -> list[SelectorCandidate]:
    if not blocked_lemmas:
        return list(candidates)
    return [candidate for candidate in candidates if candidate.lemma not in blocked_lemmas]


def _count_filtered_by_allowed_pos(
    candidates: Sequence[SelectorCandidate],
    *,
    allowed_pos: set[str],
) -> int:
    if not allowed_pos:
        return 0
    filtered_count = 0
    for candidate in candidates:
        bucket = _resolve_candidate_pos_bucket(candidate)
        if bucket and bucket not in allowed_pos:
            filtered_count += 1
    return filtered_count


def _count_blocked_by_lifecycle(
    candidates: Sequence[SelectorCandidate],
    blocked_lemmas: set[str],
) -> int:
    if not blocked_lemmas:
        return 0
    return sum(1 for candidate in candidates if candidate.lemma in blocked_lemmas)


def _browsing_candidate_from_scored(entry) -> BrowsingAdmissionCandidate:
    metadata = entry.candidate.metadata if isinstance(entry.candidate.metadata, Mapping) else {}
    return BrowsingAdmissionCandidate(
        lemma=entry.candidate.lemma,
        neutral_score=max(0.0, float(entry.breakdown.final_score)),
        readiness_multiplier=_safe_signal_float(metadata.get("readiness_multiplier"), default=1.0),
        explicit_preference_fit=max(0.0, float(entry.candidate.topic_bias)),
        source_confidence=max(0.0, float(entry.candidate.confidence or 0.0)) or 1.0,
    )


def _simulation_preview(
    result: BrowsingAdmissionSimulationResult,
    *,
    row_limit: int,
) -> dict[str, object]:
    payload = result.to_dict()
    rows = payload.get("rows")
    if isinstance(rows, list):
        selected_rows = [row for row in rows if isinstance(row, Mapping) and row.get("selected")]
        boosted_rows = [
            row
            for row in rows
            if isinstance(row, Mapping) and float(row.get("browsing_signal", 0.0) or 0.0) > 0.0
        ]
        preview_rows: list[Mapping[str, object]] = []
        seen: set[str] = set()
        for row in selected_rows + boosted_rows + rows:
            if not isinstance(row, Mapping):
                continue
            lemma = str(row.get("lemma") or "")
            if lemma in seen:
                continue
            seen.add(lemma)
            preview_rows.append(row)
            if len(preview_rows) >= max(0, int(row_limit)):
                break
        payload["rows"] = preview_rows
        payload["row_count"] = len(rows)
        payload["row_preview_count"] = len(preview_rows)
    return payload


def _safe_signal_float(value: object, *, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed:
        return default
    return parsed


def _count_unknown_pos(candidates: Sequence[SelectorCandidate]) -> int:
    count = 0
    for candidate in candidates:
        if _is_unknown_candidate_pos(candidate):
            count += 1
    return count


def _is_unknown_candidate_pos(candidate: SelectorCandidate) -> bool:
    metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    mapped = metadata.get("pos_mapped")
    if mapped is False:
        return True
    canonical = str(metadata.get("pos_canonical") or "").strip().lower()
    if canonical:
        return canonical == "other"
    bucket = _resolve_candidate_pos_bucket(candidate)
    return not bucket or bucket == "other"


def _count_admitted_by_pos_bucket(
    candidates: Sequence[SelectorCandidate],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        bucket = _resolve_candidate_pos_bucket(candidate) or "other"
        counts[bucket] = counts.get(bucket, 0) + 1
    return _sort_pos_bucket_counts(counts)


def _sort_pos_bucket_counts(counts: Mapping[str, int]) -> dict[str, int]:
    preferred = ("noun", "adjective", "verb", "adverb", "other")
    ordered_keys: list[str] = []
    for key in preferred:
        if key in counts:
            ordered_keys.append(key)
    for key in sorted(counts.keys()):
        if key not in ordered_keys:
            ordered_keys.append(key)
    return {key: int(counts[key]) for key in ordered_keys}


def _resolve_candidate_pos_bucket(candidate: SelectorCandidate) -> str:
    pos = str(candidate.pos or "").strip().lower()
    if pos:
        return pos
    metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    fallback = str(metadata.get("pos_bucket") or "").strip().lower()
    return fallback
