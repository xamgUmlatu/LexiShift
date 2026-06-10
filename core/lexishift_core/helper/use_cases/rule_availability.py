from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

from lexishift_core.replacement.core import VocabRule
from lexishift_core.srs import SRS_LIFECYCLE_DISCARDED, SrsInventory, SrsStore, set_active_item_ids
from lexishift_core.srs.store_ops import mark_item_lifecycle

NO_ENABLED_RULES_LIFECYCLE_REASON = "no_enabled_rules"


@dataclass(frozen=True)
class RuleAvailabilityReconciliation:
    reason: str
    active_item_ids_before: tuple[str, ...]
    active_item_ids_after: tuple[str, ...]
    discarded_item_ids: tuple[str, ...]
    discarded_lemmas: tuple[str, ...]
    enabled_rule_lemmas: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return bool(self.discarded_item_ids)

    def to_dict(self) -> dict[str, object]:
        return {
            "reason": self.reason,
            "changed": self.changed,
            "active_count_before": len(self.active_item_ids_before),
            "active_count_after": len(self.active_item_ids_after),
            "discarded_count": len(self.discarded_item_ids),
            "discarded_item_ids": list(self.discarded_item_ids),
            "discarded_lemmas": list(self.discarded_lemmas),
            "enabled_rule_lemma_count": len(self.enabled_rule_lemmas),
        }


def reconcile_active_items_without_enabled_rules(
    *,
    store: SrsStore,
    inventory: SrsInventory,
    pair: str,
    active_item_ids: Sequence[str],
    rules: Sequence[VocabRule],
    reason: str = NO_ENABLED_RULES_LIFECYCLE_REASON,
    now: Optional[datetime] = None,
    last_initialized_at: Optional[str] = None,
    last_refreshed_at: Optional[str] = None,
    last_rebalanced_at: Optional[str] = None,
) -> tuple[SrsStore, SrsInventory, RuleAvailabilityReconciliation]:
    normalized_pair = str(pair or "").strip()
    normalized_reason = str(reason or "").strip() or NO_ENABLED_RULES_LIFECYCLE_REASON
    normalized_active_ids = _normalize_active_item_ids(active_item_ids)
    enabled_rule_lemmas = _enabled_rule_replacement_lemmas(rules)
    items_by_id = {
        str(item.item_id or "").strip(): item
        for item in store.items
        if item.language_pair == normalized_pair and str(item.item_id or "").strip()
    }

    updated_store = store
    active_after: list[str] = []
    discarded_item_ids: list[str] = []
    discarded_lemmas: list[str] = []
    for item_id in normalized_active_ids:
        item = items_by_id.get(item_id)
        if item is None:
            active_after.append(item_id)
            continue
        lemma = str(item.lemma or "").strip()
        if not lemma or lemma in enabled_rule_lemmas:
            active_after.append(item_id)
            continue
        updated_store, updated_item = mark_item_lifecycle(
            updated_store,
            language_pair=normalized_pair,
            lemma=lemma,
            lifecycle_state=SRS_LIFECYCLE_DISCARDED,
            reason=normalized_reason,
            now=now,
        )
        if updated_item is None:
            active_after.append(item_id)
            continue
        discarded_item_ids.append(item_id)
        discarded_lemmas.append(lemma)

    reconciliation = RuleAvailabilityReconciliation(
        reason=normalized_reason,
        active_item_ids_before=normalized_active_ids,
        active_item_ids_after=tuple(active_after),
        discarded_item_ids=tuple(discarded_item_ids),
        discarded_lemmas=tuple(discarded_lemmas),
        enabled_rule_lemmas=tuple(sorted(enabled_rule_lemmas)),
    )
    if not reconciliation.changed:
        return updated_store, inventory, reconciliation

    updated_inventory = set_active_item_ids(
        inventory,
        pair=normalized_pair,
        active_item_ids=reconciliation.active_item_ids_after,
        last_initialized_at=last_initialized_at,
        last_refreshed_at=last_refreshed_at,
        last_rebalanced_at=last_rebalanced_at,
    )
    return updated_store, updated_inventory, reconciliation


def _enabled_rule_replacement_lemmas(rules: Sequence[VocabRule]) -> set[str]:
    return {
        str(rule.replacement or "").strip()
        for rule in rules
        if rule.enabled is not False and str(rule.replacement or "").strip()
    }


def _normalize_active_item_ids(values: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item_id = str(value or "").strip()
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        normalized.append(item_id)
    return tuple(normalized)
