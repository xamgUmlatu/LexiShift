from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence

from lexishift_core.srs import SrsItem, SrsSettings, SrsStore
from lexishift_core.srs.source import SOURCE_FREQUENCY_LIST, normalize_source_type
from lexishift_core.srs.selector import (
    ScoredCandidate,
    SelectorCandidate,
    SelectorConfig,
    filter_candidates,
    rank_candidates,
)
from lexishift_core.srs.store_ops import build_item_id, upsert_item


@dataclass(frozen=True)
class SrsGrowthConfig:
    selector_config: SelectorConfig = field(default_factory=SelectorConfig)
    coverage_scalar: Optional[float] = None
    max_new_items: Optional[int] = None
    initial_stability: float = 1.0
    initial_difficulty: float = 0.5
    default_source_type: str = SOURCE_FREQUENCY_LIST
    confidence_min: Optional[float] = None


@dataclass(frozen=True)
class SrsGrowthPlan:
    allowed_pairs: Sequence[str]
    coverage_ratio: float
    target_size: int
    existing_count: int
    add_count: int
    pool_size: int
    filtered_size: int
    scored: Sequence[ScoredCandidate]
    selected: Sequence[SelectorCandidate]


def normalize_coverage_scalar(value: float) -> float:
    if value <= 0:
        return 0.0
    if value <= 1:
        return min(1.0, max(0.0, value))
    return min(1.0, max(0.0, value / 100.0))


def resolve_allowed_pairs(
    settings: SrsSettings,
    *,
    allowed_pairs: Optional[Sequence[str]] = None,
) -> Sequence[str]:
    if allowed_pairs:
        return tuple(allowed_pairs)
    if settings.pair_rules:
        enabled = [pair for pair, rule in settings.pair_rules.items() if rule.enabled]
        return tuple(enabled)
    return ()


def plan_srs_growth(
    candidates: Iterable[SelectorCandidate],
    *,
    store: SrsStore,
    settings: SrsSettings,
    config: Optional[SrsGrowthConfig] = None,
    allowed_pairs: Optional[Sequence[str]] = None,
    blocked_lemmas: Optional[set[str]] = None,
) -> SrsGrowthPlan:
    config = config or SrsGrowthConfig()
    pairs = resolve_allowed_pairs(settings, allowed_pairs=allowed_pairs)
    pair_set = set(pairs)

    pool = [item for item in candidates if not pair_set or item.language_pair in pair_set]
    pool_size = len(pool)

    existing = {
        item.lemma
        for item in store.items
        if not pair_set or item.language_pair in pair_set
    }

    coverage_scalar = (
        config.coverage_scalar
        if config.coverage_scalar is not None
        else settings.coverage_scalar
    )
    coverage_ratio = normalize_coverage_scalar(coverage_scalar)
    target_size = int(round(pool_size * coverage_ratio))
    existing_count = len(existing)

    filtered = filter_candidates(
        pool,
        blocked_lemmas=blocked_lemmas,
        in_s=existing,
        allowed_pairs=pairs if pairs else None,
    )
    scored = rank_candidates(filtered, config=config.selector_config)

    add_count = max(0, target_size - existing_count)
    max_new = config.max_new_items if config.max_new_items is not None else settings.max_new_items_per_day
    if max_new is not None:
        add_count = min(add_count, max(0, int(max_new)))
    add_count = min(add_count, len(scored))

    selected = [entry.candidate for entry in scored[:add_count]]
    return SrsGrowthPlan(
        allowed_pairs=pairs,
        coverage_ratio=coverage_ratio,
        target_size=target_size,
        existing_count=existing_count,
        add_count=add_count,
        pool_size=pool_size,
        filtered_size=len(filtered),
        scored=tuple(scored),
        selected=tuple(selected),
    )


def apply_growth_plan(
    store: SrsStore,
    plan: SrsGrowthPlan,
    *,
    config: Optional[SrsGrowthConfig] = None,
) -> SrsStore:
    config = config or SrsGrowthConfig()
    updated = store
    for candidate in plan.selected:
        confidence = _resolve_confidence(candidate, min_value=config.confidence_min)
        source_type = _resolve_source_type(candidate, default=config.default_source_type)
        item = SrsItem(
            item_id=build_item_id(candidate.language_pair, candidate.lemma),
            lemma=candidate.lemma,
            language_pair=candidate.language_pair,
            source_type=source_type,
            confidence=confidence,
            stability=config.initial_stability,
            difficulty=config.initial_difficulty,
        )
        updated = upsert_item(updated, item)
    return updated


def grow_srs_store(
    candidates: Iterable[SelectorCandidate],
    *,
    store: SrsStore,
    settings: SrsSettings,
    config: Optional[SrsGrowthConfig] = None,
    allowed_pairs: Optional[Sequence[str]] = None,
    blocked_lemmas: Optional[set[str]] = None,
) -> tuple[SrsStore, SrsGrowthPlan]:
    config = config or SrsGrowthConfig()
    plan = plan_srs_growth(
        candidates,
        store=store,
        settings=settings,
        config=config,
        allowed_pairs=allowed_pairs,
        blocked_lemmas=blocked_lemmas,
    )
    updated = apply_growth_plan(store, plan, config=config)
    return updated, plan


def _resolve_source_type(candidate: SelectorCandidate, *, default: str) -> str:
    if candidate.source_type:
        return normalize_source_type(candidate.source_type, default=default)
    source = candidate.metadata.get("source") if hasattr(candidate, "metadata") else None
    if source:
        return normalize_source_type(source, default=default)
    return normalize_source_type(default)


def _resolve_confidence(candidate: SelectorCandidate, *, min_value: Optional[float]) -> Optional[float]:
    value = candidate.confidence
    if min_value is None:
        return value if value > 0 else None
    if value >= min_value:
        return value
    return None
