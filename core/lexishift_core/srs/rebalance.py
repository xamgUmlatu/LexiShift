from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.inventory import SrsInventory, resolve_active_item_ids
from lexishift_core.srs.profile_bootstrap import rerank_seed_words_for_profile
from lexishift_core.srs.source import SOURCE_FREQUENCY_LIST, normalize_source_type
from lexishift_core.srs.store import SrsItem, SrsStore
from lexishift_core.srs.store_ops import build_item_id
from lexishift_core.srs.time import now_utc, parse_ts

PROTECTION_RULE_HISTORY_COUNT = "history_count>=4"
PROTECTION_RULE_STABILITY = "stability>=14"
PROTECTION_RULE_REVIEW_NEXT_DUE = "review_next_due>=7d"
SWAPPABLE_RULE_NO_PROTECTION = "no_protection_rule_matched"

SOURCE_KIND_ACTIVE_SWAPPABLE = "active_swappable"
SOURCE_KIND_RETAINED_PARKED = "retained_parked"
SOURCE_KIND_NEW_SEED = "new_seed"

CURRENT_STATE_ACTIVE_PROTECTED = "active_protected"
CURRENT_STATE_ACTIVE_SWAPPABLE = "active_swappable"
CURRENT_STATE_RETAINED_PARKED = "retained_parked"
CURRENT_STATE_NEW_SEED = "new_seed"


@dataclass(frozen=True)
class RebalanceItemDecision:
    item_id: str
    lemma: str
    current_state: str
    source_kind: str
    source_type: str
    protection_rule: Optional[str] = None
    profile_score: Optional[float] = None
    explanation: Optional[str] = None
    pos_bucket: Optional[str] = None
    confidence: Optional[float] = None
    history_count: int = 0
    stability: Optional[float] = None
    scheduler_state: Optional[str] = None
    next_due: Optional[str] = None
    retained_record: bool = False
    candidate_traits: Mapping[str, object] = field(default_factory=dict)
    signals: Mapping[str, object] = field(default_factory=dict)
    weighted_components: Mapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        payload = {
            "item_id": self.item_id,
            "lemma": self.lemma,
            "current_state": self.current_state,
            "source_kind": self.source_kind,
            "source_type": self.source_type,
            "protection_rule": self.protection_rule,
            "profile_score": self.profile_score,
            "explanation": self.explanation,
            "pos_bucket": self.pos_bucket,
            "confidence": self.confidence,
            "history_count": self.history_count,
            "stability": self.stability,
            "scheduler_state": self.scheduler_state,
            "next_due": self.next_due,
            "retained_record": self.retained_record,
            "candidate_traits": dict(self.candidate_traits),
            "signals": dict(self.signals),
            "weighted_components": dict(self.weighted_components),
        }
        return {key: value for key, value in payload.items() if value not in (None, {}, [])}


@dataclass(frozen=True)
class SrsRebalancePlan:
    pair: str
    inventory_source: str
    target_active_count: int
    active_item_ids_before: tuple[str, ...]
    proposed_active_item_ids: tuple[str, ...]
    protected_items: tuple[RebalanceItemDecision, ...] = field(default_factory=tuple)
    swappable_items: tuple[RebalanceItemDecision, ...] = field(default_factory=tuple)
    proposed_parks: tuple[RebalanceItemDecision, ...] = field(default_factory=tuple)
    proposed_activations: tuple[RebalanceItemDecision, ...] = field(default_factory=tuple)
    diagnostics: Mapping[str, object] = field(default_factory=dict)
    activation_payloads: Mapping[str, Mapping[str, object]] = field(
        default_factory=dict,
        repr=False,
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "pair": self.pair,
            "inventory_source": self.inventory_source,
            "target_active_count": self.target_active_count,
            "active_item_ids_before": list(self.active_item_ids_before),
            "proposed_active_item_ids": list(self.proposed_active_item_ids),
            "summary": build_rebalance_summary(self),
            "protected_items": [entry.to_dict() for entry in self.protected_items],
            "swappable_items": [entry.to_dict() for entry in self.swappable_items],
            "proposed_parks": [entry.to_dict() for entry in self.proposed_parks],
            "proposed_activations": [entry.to_dict() for entry in self.proposed_activations],
            "diagnostics": dict(self.diagnostics),
        }


def classify_rebalance_protection(
    item: SrsItem,
    *,
    now: Optional[datetime] = None,
) -> tuple[bool, str]:
    now = now or now_utc()
    history_count = len(tuple(item.history or ()))
    if history_count >= 4:
        return True, PROTECTION_RULE_HISTORY_COUNT
    stability = _safe_optional_float(item.stability)
    if stability is not None and stability >= 14.0:
        return True, PROTECTION_RULE_STABILITY
    next_due = parse_ts(item.next_due)
    if (
        str(item.scheduler_state or "").strip().lower() == "review"
        and next_due is not None
        and next_due >= now + timedelta(days=7)
    ):
        return True, PROTECTION_RULE_REVIEW_NEXT_DUE
    return False, SWAPPABLE_RULE_NO_PROTECTION


def build_rebalance_summary(plan: SrsRebalancePlan) -> dict[str, int]:
    active_before = set(plan.active_item_ids_before)
    active_after = set(plan.proposed_active_item_ids)
    return {
        "active_count_before": len(plan.active_item_ids_before),
        "protected_count": len(plan.protected_items),
        "swappable_count": len(plan.swappable_items),
        "candidate_slots_available": max(
            0,
            int(plan.target_active_count) - len(plan.protected_items),
        ),
        "proposed_keep_count": len(active_before & active_after),
        "proposed_park_count": len(plan.proposed_parks),
        "proposed_activate_count": len(plan.proposed_activations),
        "active_count_after": len(plan.proposed_active_item_ids),
    }


def build_rebalance_plan(
    *,
    store: SrsStore,
    pair: str,
    inventory: Optional[SrsInventory],
    candidates: Sequence[object],
    profile_context: Optional[Mapping[str, object]],
    target_active_count: Optional[int] = None,
    now: Optional[datetime] = None,
) -> SrsRebalancePlan:
    normalized_pair = str(pair or "").strip()
    if not normalized_pair:
        raise ValueError("Missing pair.")
    now = now or now_utc()

    active_item_ids_before, inventory_source = resolve_active_item_ids(
        store=store,
        pair=normalized_pair,
        inventory=inventory,
    )
    pair_items_by_id = {
        item.item_id: item
        for item in store.items
        if item.language_pair == normalized_pair and str(item.item_id or "").strip()
    }
    effective_target_active_count = _resolve_target_active_count(
        active_item_ids_before=active_item_ids_before,
        target_active_count=target_active_count,
    )

    protected_items: list[RebalanceItemDecision] = []
    swappable_items: list[RebalanceItemDecision] = []
    protected_item_ids: list[str] = []
    swappable_item_ids: list[str] = []
    for item_id in active_item_ids_before:
        item = pair_items_by_id.get(item_id)
        if item is None:
            continue
        is_protected, protection_rule = classify_rebalance_protection(item, now=now)
        decision = _build_active_item_decision(
            item=item,
            is_protected=is_protected,
            protection_rule=protection_rule,
        )
        if is_protected:
            protected_items.append(decision)
            protected_item_ids.append(item.item_id)
        else:
            swappable_items.append(decision)
            swappable_item_ids.append(item.item_id)

    candidate_pool, candidate_pool_breakdown = _build_candidate_pool(
        pair=normalized_pair,
        store=store,
        pair_items_by_id=pair_items_by_id,
        candidates=candidates,
        active_item_ids_before=active_item_ids_before,
        swappable_item_ids=tuple(swappable_item_ids),
    )
    ranked_entries, profile_diagnostics = _rank_candidates(
        candidate_pool,
        profile_context=profile_context,
    )
    ranked_by_item_id = {entry.item_id: entry for entry in ranked_entries}
    swappable_items = [
        _merge_ranked_decision(entry=ranked_by_item_id.get(decision.item_id), fallback=decision)
        for decision in swappable_items
    ]

    candidate_slots_available = max(
        0,
        effective_target_active_count - len(protected_item_ids),
    )
    selected_ranked_entries = ranked_entries[:candidate_slots_available]
    proposed_active_item_ids = tuple(
        list(protected_item_ids) + [entry.item_id for entry in selected_ranked_entries]
    )
    proposed_parks = tuple(
        entry for entry in swappable_items if entry.item_id not in proposed_active_item_ids
    )
    activation_entries = [
        entry for entry in selected_ranked_entries if entry.item_id not in active_item_ids_before
    ]
    proposed_activations = tuple(_decision_from_ranked_entry(entry) for entry in activation_entries)
    activation_payloads = {
        entry.item_id: {
            "item_id": entry.item_id,
            "lemma": entry.lemma,
            "language_pair": normalized_pair,
            "source_type": entry.source_type,
            "confidence": entry.confidence,
            "word_package": dict(entry._candidate_word_package or {}),
            "source_kind": entry.source_kind,
        }
        for entry in activation_entries
    }
    diagnostics = {
        "inventory_source": inventory_source,
        "candidate_pool_count": len(candidate_pool),
        "candidate_pool_breakdown": candidate_pool_breakdown,
        "profile_selector_version": profile_diagnostics.get("selector_version"),
        "profile_selector_policy_version": profile_diagnostics.get("selector_policy_version"),
        "profile_context": profile_diagnostics.get("profile_context") or {},
        "top_candidate_preview": [
            {
                "item_id": entry.item_id,
                "lemma": entry.lemma,
                "current_state": entry.current_state,
                "source_kind": entry.source_kind,
                "profile_score": entry.profile_score,
                "explanation": entry.explanation,
            }
            for entry in ranked_entries[:10]
        ],
        "budget": {
            "target_active_count": effective_target_active_count,
            "active_count_before": len(active_item_ids_before),
            "protected_count": len(protected_items),
            "candidate_slots_available": candidate_slots_available,
        },
    }
    return SrsRebalancePlan(
        pair=normalized_pair,
        inventory_source=inventory_source,
        target_active_count=effective_target_active_count,
        active_item_ids_before=tuple(active_item_ids_before),
        proposed_active_item_ids=proposed_active_item_ids,
        protected_items=tuple(protected_items),
        swappable_items=tuple(swappable_items),
        proposed_parks=tuple(proposed_parks),
        proposed_activations=tuple(proposed_activations),
        diagnostics=diagnostics,
        activation_payloads=activation_payloads,
    )


def _resolve_target_active_count(
    *,
    active_item_ids_before: Sequence[str],
    target_active_count: Optional[int],
) -> int:
    if active_item_ids_before:
        return len(tuple(active_item_ids_before))
    if target_active_count is None:
        return 0
    return max(0, int(target_active_count))


def _build_active_item_decision(
    *,
    item: SrsItem,
    is_protected: bool,
    protection_rule: str,
) -> RebalanceItemDecision:
    return RebalanceItemDecision(
        item_id=item.item_id,
        lemma=item.lemma,
        current_state=(
            CURRENT_STATE_ACTIVE_PROTECTED if is_protected else CURRENT_STATE_ACTIVE_SWAPPABLE
        ),
        source_kind=(
            CURRENT_STATE_ACTIVE_PROTECTED if is_protected else SOURCE_KIND_ACTIVE_SWAPPABLE
        ),
        source_type=normalize_source_type(item.source_type),
        protection_rule=protection_rule,
        confidence=_safe_optional_float(item.confidence),
        history_count=len(tuple(item.history or ())),
        stability=_safe_optional_float(item.stability),
        scheduler_state=_normalize_optional_string(item.scheduler_state),
        next_due=_normalize_optional_string(item.next_due),
        retained_record=True,
    )


def _build_candidate_pool(
    *,
    pair: str,
    store: SrsStore,
    pair_items_by_id: Mapping[str, SrsItem],
    candidates: Sequence[object],
    active_item_ids_before: Sequence[str],
    swappable_item_ids: Sequence[str],
) -> tuple[list[object], dict[str, int]]:
    seed_candidates_by_item_id = {
        build_item_id(pair, str(getattr(seed, "lemma", "") or "").strip()): seed
        for seed in candidates
        if str(getattr(seed, "language_pair", "") or "").strip() == pair
        and str(getattr(seed, "lemma", "") or "").strip()
    }
    represented_item_ids: set[str] = set()
    candidate_pool: list[object] = []
    active_item_id_set = set(active_item_ids_before)
    retained_parked_count = 0

    for item_id in swappable_item_ids:
        item = pair_items_by_id.get(item_id)
        if item is None:
            continue
        candidate_pool.append(
            _candidate_from_store_item(
                item=item,
                seed=seed_candidates_by_item_id.get(item_id),
                current_state=CURRENT_STATE_ACTIVE_SWAPPABLE,
                source_kind=SOURCE_KIND_ACTIVE_SWAPPABLE,
            )
        )
        represented_item_ids.add(item_id)

    for item in store.items:
        if item.language_pair != pair or item.item_id in active_item_id_set:
            continue
        if item.item_id in represented_item_ids:
            continue
        candidate_pool.append(
            _candidate_from_store_item(
                item=item,
                seed=seed_candidates_by_item_id.get(item.item_id),
                current_state=CURRENT_STATE_RETAINED_PARKED,
                source_kind=SOURCE_KIND_RETAINED_PARKED,
            )
        )
        represented_item_ids.add(item.item_id)
        retained_parked_count += 1

    for seed in candidates:
        if str(getattr(seed, "language_pair", "") or "").strip() != pair:
            continue
        lemma = str(getattr(seed, "lemma", "") or "").strip()
        if not lemma:
            continue
        item_id = build_item_id(pair, lemma)
        if item_id in represented_item_ids:
            continue
        candidate_pool.append(
            _candidate_from_seed(
                seed=seed,
                item_id=item_id,
                current_state=CURRENT_STATE_NEW_SEED,
            )
        )
        represented_item_ids.add(item_id)

    return candidate_pool, {
        "active_swappable": len(swappable_item_ids),
        "retained_parked": retained_parked_count,
        "new_seed": max(
            0,
            len(candidate_pool) - len(tuple(swappable_item_ids)) - retained_parked_count,
        ),
    }


def _candidate_from_store_item(
    *,
    item: SrsItem,
    seed: Optional[object],
    current_state: str,
    source_kind: str,
) -> object:
    metadata = _coerce_mapping(getattr(seed, "metadata", None))
    word_package = _coerce_mapping(item.word_package) or _coerce_mapping(
        getattr(seed, "word_package", None)
    )
    return SimpleNamespace(
        item_id=item.item_id,
        lemma=item.lemma,
        language_pair=item.language_pair,
        source_type=normalize_source_type(item.source_type),
        current_state=current_state,
        source_kind=source_kind,
        retained_record=True,
        active_before=current_state == CURRENT_STATE_ACTIVE_SWAPPABLE,
        word_package=word_package or None,
        metadata=metadata,
        pos_bucket=_normalize_optional_string(getattr(seed, "pos_bucket", None)),
        pos=_normalize_optional_string(getattr(seed, "pos", None)),
        base_weight=_coalesce_optional_float(
            _safe_optional_float(getattr(seed, "base_weight", None)),
            _safe_optional_float(item.confidence),
        ),
        admission_weight=_coalesce_optional_float(
            _safe_optional_float(getattr(seed, "admission_weight", None)),
            _safe_optional_float(item.confidence),
        ),
        confidence=_safe_optional_float(item.confidence),
    )


def _candidate_from_seed(
    *,
    seed: object,
    item_id: str,
    current_state: str,
) -> object:
    return SimpleNamespace(
        item_id=item_id,
        lemma=str(getattr(seed, "lemma", "") or "").strip(),
        language_pair=str(getattr(seed, "language_pair", "") or "").strip(),
        source_type=SOURCE_FREQUENCY_LIST,
        current_state=current_state,
        source_kind=SOURCE_KIND_NEW_SEED,
        retained_record=False,
        active_before=False,
        word_package=_coerce_mapping(getattr(seed, "word_package", None)) or None,
        metadata=_coerce_mapping(getattr(seed, "metadata", None)),
        pos_bucket=_normalize_optional_string(getattr(seed, "pos_bucket", None)),
        pos=_normalize_optional_string(getattr(seed, "pos", None)),
        base_weight=_safe_optional_float(getattr(seed, "base_weight", None)),
        admission_weight=_safe_optional_float(getattr(seed, "admission_weight", None)),
        confidence=_safe_optional_float(getattr(seed, "admission_weight", None)),
    )


def _rank_candidates(
    candidate_pool: Sequence[object],
    *,
    profile_context: Optional[Mapping[str, object]],
) -> tuple[list[SimpleNamespace], Mapping[str, object]]:
    if not candidate_pool:
        return [], {}
    reranked, profile_diagnostics = rerank_seed_words_for_profile(
        candidate_pool,
        profile_context=profile_context,
        preview_limit=None,
    )
    ranking_preview = profile_diagnostics.get("ranking_preview")
    ranking_entries = list(ranking_preview) if isinstance(ranking_preview, list) else []
    ranked_entries: list[SimpleNamespace] = []
    for index, candidate in enumerate(reranked):
        detail = ranking_entries[index] if index < len(ranking_entries) else {}
        detail_mapping = detail if isinstance(detail, Mapping) else {}
        ranked_entries.append(
            SimpleNamespace(
                item_id=str(getattr(candidate, "item_id", "") or "").strip(),
                lemma=str(getattr(candidate, "lemma", "") or "").strip(),
                current_state=str(getattr(candidate, "current_state", "") or "").strip(),
                source_kind=str(getattr(candidate, "source_kind", "") or "").strip(),
                source_type=normalize_source_type(getattr(candidate, "source_type", None)),
                retained_record=bool(getattr(candidate, "retained_record", False)),
                profile_score=_safe_optional_float(detail_mapping.get("profile_score")),
                explanation=_normalize_optional_string(detail_mapping.get("explanation")),
                pos_bucket=_normalize_optional_string(detail_mapping.get("pos_bucket")),
                confidence=_safe_optional_float(getattr(candidate, "confidence", None)),
                candidate_traits=_coerce_mapping(detail_mapping.get("candidate_traits")),
                signals=_coerce_mapping(detail_mapping.get("signals")),
                weighted_components=_coerce_mapping(detail_mapping.get("weighted_components")),
                _candidate_word_package=_coerce_mapping(getattr(candidate, "word_package", None)),
            )
        )
    return ranked_entries, profile_diagnostics


def _merge_ranked_decision(
    *,
    entry: Optional[SimpleNamespace],
    fallback: RebalanceItemDecision,
) -> RebalanceItemDecision:
    if entry is None:
        return fallback
    return RebalanceItemDecision(
        item_id=fallback.item_id,
        lemma=fallback.lemma,
        current_state=fallback.current_state,
        source_kind=fallback.source_kind,
        source_type=fallback.source_type,
        protection_rule=fallback.protection_rule,
        profile_score=entry.profile_score,
        explanation=entry.explanation,
        pos_bucket=entry.pos_bucket,
        confidence=entry.confidence if entry.confidence is not None else fallback.confidence,
        history_count=fallback.history_count,
        stability=fallback.stability,
        scheduler_state=fallback.scheduler_state,
        next_due=fallback.next_due,
        retained_record=fallback.retained_record,
        candidate_traits=entry.candidate_traits,
        signals=entry.signals,
        weighted_components=entry.weighted_components,
    )


def _decision_from_ranked_entry(entry: SimpleNamespace) -> RebalanceItemDecision:
    return RebalanceItemDecision(
        item_id=entry.item_id,
        lemma=entry.lemma,
        current_state=entry.current_state,
        source_kind=entry.source_kind,
        source_type=entry.source_type,
        profile_score=entry.profile_score,
        explanation=entry.explanation,
        pos_bucket=entry.pos_bucket,
        confidence=entry.confidence,
        retained_record=entry.retained_record,
        candidate_traits=entry.candidate_traits,
        signals=entry.signals,
        weighted_components=entry.weighted_components,
    )


def _safe_optional_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _coalesce_optional_float(*values: Optional[float]) -> Optional[float]:
    for value in values:
        if value is not None:
            return value
    return None


def _normalize_optional_string(value: object) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _coerce_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}
