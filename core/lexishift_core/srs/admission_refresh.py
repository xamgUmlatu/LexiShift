from __future__ import annotations

from collections.abc import Iterable as IterableCollection
from dataclasses import dataclass, field
from datetime import datetime
from math import floor
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.srs import SrsSettings, SrsStore
from lexishift_core.srs.growth import SrsGrowthConfig, grow_srs_store
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
from lexishift_core.srs.time import now_utc


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
    allowed_pos: Optional[set[str]] = None
    selection_seed: Optional[int] = None
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


@dataclass(frozen=True)
class AdmissionRefreshDecision:
    pair: str
    max_active_items: int
    max_new_items_per_day: int
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
    admitted_by_pos_bucket: Mapping[str, int] = field(default_factory=dict)
    unknown_pos_seen: int = 0
    allowed_pos: Sequence[str] = field(default_factory=tuple)
    candidate_pool_effective: int = 0
    selection_policy: str = "weighted_without_replacement"
    selection_seed: Optional[int] = None


@dataclass(frozen=True)
class AdmissionRefreshResult:
    decision: AdmissionRefreshDecision
    candidate_pool_size: int
    admitted_count: int
    selected_lemmas: Sequence[str]
    applied: bool
    diagnostics: AdmissionRefreshDiagnostics = field(default_factory=AdmissionRefreshDiagnostics)


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
    due_items = select_active_items(
        store.items,
        now=now,
        max_active=max_active_items,
        allowed_pairs=[pair],
    )
    due_count = len(due_items)
    due_pressure = due_count / float(max_active_items) if max_active_items > 0 else 1.0

    capacity_budget = max(0, max_active_items - due_count)
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
    filtered_by_pos = _count_filtered_by_allowed_pos(candidates, allowed_pos=allowed_pos)
    unknown_pos_seen = _count_unknown_pos(candidates)
    decision = plan_admission_refresh(
        store=store,
        settings=settings,
        pair=pair,
        events=events,
        policy=policy,
        now=now,
    )
    effective_candidates = _apply_allowed_pos_filter(candidates, allowed_pos=allowed_pos)
    if decision.admission_budget <= 0:
        diagnostics = AdmissionRefreshDiagnostics(
            filtered_by_pos=filtered_by_pos,
            admitted_by_pos_bucket={},
            unknown_pos_seen=unknown_pos_seen,
            allowed_pos=tuple(sorted(allowed_pos)),
            candidate_pool_effective=len(effective_candidates),
            selection_policy=str(
                policy.selector_config.selection_policy or "weighted_without_replacement"
            ),
            selection_seed=policy.selection_seed,
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
        selection_seed=policy.selection_seed,
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
    )
    selected_lemmas = tuple(candidate.lemma for candidate in growth_plan.selected)
    diagnostics = AdmissionRefreshDiagnostics(
        filtered_by_pos=filtered_by_pos,
        admitted_by_pos_bucket=_count_admitted_by_pos_bucket(growth_plan.selected),
        unknown_pos_seen=unknown_pos_seen,
        allowed_pos=tuple(sorted(allowed_pos)),
        candidate_pool_effective=len(effective_candidates),
        selection_policy=str(
            policy.selector_config.selection_policy or "weighted_without_replacement"
        ),
        selection_seed=policy.selection_seed,
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
            "admitted_by_pos_bucket": {
                str(key): int(value)
                for key, value in dict(result.diagnostics.admitted_by_pos_bucket).items()
            },
            "unknown_pos_seen": int(result.diagnostics.unknown_pos_seen),
            "allowed_pos": list(result.diagnostics.allowed_pos),
            "candidate_pool_effective": int(result.diagnostics.candidate_pool_effective),
            "selection_policy": str(
                result.diagnostics.selection_policy or "weighted_without_replacement"
            ),
            "selection_seed": result.diagnostics.selection_seed,
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


def _normalize_allowed_pos(value: Optional[IterableCollection[str]]) -> set[str]:
    if not value:
        return set()
    return {str(item).strip().lower() for item in value if str(item).strip()}


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
