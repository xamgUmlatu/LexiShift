from __future__ import annotations

from dataclasses import replace
from typing import Optional, Sequence

from lexishift_core.replacement.core import RuleMetadata, VocabRule
from lexishift_core.srs import SrsItem, SrsStore, srs_item_is_active
from lexishift_core.srs.time import now_utc, parse_ts


def normalize_item_id_filter(
    active_item_ids: Optional[Sequence[str]],
) -> Optional[set[str]]:
    normalized = normalize_item_id_sequence(active_item_ids)
    if normalized is None:
        return None
    return set(normalized)


def normalize_item_id_sequence(
    active_item_ids: Optional[Sequence[str]],
) -> Optional[tuple[str, ...]]:
    if active_item_ids is None:
        return None
    normalized: list[str] = []
    seen: set[str] = set()
    for item_id in active_item_ids:
        candidate = str(item_id).strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return tuple(normalized)


def item_is_active_for_pair(item: SrsItem, pair: str) -> bool:
    return item.language_pair == pair and bool(item.lemma) and srs_item_is_active(item)


def annotate_rules_with_srs_serving_metadata(
    rules: Sequence[VocabRule],
    *,
    store: SrsStore,
    pair: str,
    active_item_ids: Optional[Sequence[str]] = None,
) -> tuple[VocabRule, ...]:
    active_item_id_set = normalize_item_id_filter(active_item_ids)
    now = now_utc()
    items_by_lemma: dict[str, SrsItem] = {}
    for item in store.items:
        if not item_is_active_for_pair(item, pair):
            continue
        if active_item_id_set is not None and item.item_id not in active_item_id_set:
            continue
        items_by_lemma.setdefault(item.lemma, item)

    annotated: list[VocabRule] = []
    for rule in rules:
        matching_item = items_by_lemma.get(str(rule.replacement or "").strip())
        if matching_item is None:
            annotated.append(rule)
            continue
        annotated.append(
            _annotate_rule_with_srs_serving_metadata(rule, item=matching_item, now=now)
        )
    return tuple(annotated)


def _build_srs_serving_metadata(item: SrsItem, *, now) -> dict[str, object]:
    next_due = parse_ts(item.next_due)
    in_due = next_due is None or next_due <= now
    payload: dict[str, object] = {
        "schema_version": 1,
        "serving_policy": "due_at_or_before_now",
        "item_id": item.item_id,
        "next_due": item.next_due,
        "in_due": bool(in_due),
        "scheduler_state": item.scheduler_state,
        "scheduler_step": item.scheduler_step,
        "stability": item.stability,
        "difficulty": item.difficulty,
        "last_review": item.last_review,
        "last_seen": item.last_seen,
        "exposures": item.exposures,
        "review_count": len(item.history),
    }
    return {key: value for key, value in payload.items() if value is not None}


def _annotate_rule_with_srs_serving_metadata(
    rule: VocabRule,
    *,
    item: SrsItem,
    now,
) -> VocabRule:
    metadata = rule.metadata or RuleMetadata()
    rulegen_metadata = dict(metadata.rulegen or {})
    rulegen_metadata["srs"] = _build_srs_serving_metadata(item, now=now)
    return replace(rule, metadata=replace(metadata, rulegen=rulegen_metadata))
