from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.semantic_shadow_inventory import (
    BenchmarkShadowTarget,
    normalize_shadow_text,
)


DEFAULT_NEIGHBOR_BORROW_MIN_SIMILARITY = 0.60
DEFAULT_NEIGHBOR_BORROW_MIN_REVERSE_TARGET_COUNT = 14
DEFAULT_NEIGHBOR_BORROW_MAX_TRIGGERS = 1
DEFAULT_NEIGHBOR_BORROW_MAX_WORDS = 4


def _build_trigger_document_frequency(
    seed_targets: Sequence[BenchmarkShadowTarget],
) -> dict[str, int]:
    document_frequency: dict[str, int] = {}
    for seed_target in seed_targets:
        seen_in_target: set[str] = set()
        for trigger in seed_target.reviewed_triggers:
            normalized_trigger = normalize_shadow_text(trigger)
            if not normalized_trigger or normalized_trigger in seen_in_target:
                continue
            seen_in_target.add(normalized_trigger)
            document_frequency[normalized_trigger] = (
                int(document_frequency.get(normalized_trigger) or 0) + 1
            )
    return document_frequency


def _count_unique_reverse_targets(records: Sequence[TranslationGlossRecord]) -> int:
    unique_targets = {
        normalize_shadow_text(record.translation)
        for record in records
        if normalize_shadow_text(record.translation)
    }
    return len(unique_targets)


def augment_shadow_targets_with_neighbor_borrowed_triggers(
    seed_targets: Sequence[BenchmarkShadowTarget],
    *,
    neighbor_index: Mapping[str, Sequence[Mapping[str, object]]],
    reverse_records_by_source: Mapping[str, Sequence[TranslationGlossRecord]] | None = None,
    min_reverse_target_count: int = DEFAULT_NEIGHBOR_BORROW_MIN_REVERSE_TARGET_COUNT,
    max_borrowed_triggers_per_target: int = DEFAULT_NEIGHBOR_BORROW_MAX_TRIGGERS,
    max_words: int = DEFAULT_NEIGHBOR_BORROW_MAX_WORDS,
    tier_label: str = "neighbor_trigger_borrow",
) -> list[BenchmarkShadowTarget]:
    normalized_limit = max(1, int(max_borrowed_triggers_per_target))
    normalized_max_words = max(1, int(max_words))
    normalized_min_reverse_target_count = max(0, int(min_reverse_target_count))
    trigger_document_frequency = _build_trigger_document_frequency(seed_targets)
    seed_target_map = {
        str(target.target or "").strip(): target
        for target in seed_targets
        if str(target.target or "").strip()
    }
    augmented_targets: list[BenchmarkShadowTarget] = []
    for seed_target in seed_targets:
        target_key = str(seed_target.target or "").strip()
        trigger_values = list(seed_target.reviewed_triggers)
        seen = {normalize_shadow_text(trigger) for trigger in trigger_values if trigger}
        borrowed_count = 0
        for neighbor in neighbor_index.get(target_key, ()):
            if not isinstance(neighbor, Mapping):
                continue
            neighbor_target = str(neighbor.get("target") or "").strip()
            if not neighbor_target:
                continue
            neighbor_seed_target = seed_target_map.get(neighbor_target)
            if neighbor_seed_target is None:
                continue
            borrow_candidates: list[tuple[tuple[int, int, str], str]] = []
            for borrowed_trigger in neighbor_seed_target.reviewed_triggers:
                normalized_trigger = normalize_shadow_text(borrowed_trigger)
                if not normalized_trigger or normalized_trigger in seen:
                    continue
                if (
                    len([token for token in normalized_trigger.split(" ") if token])
                    > normalized_max_words
                ):
                    continue
                reverse_target_count = _count_unique_reverse_targets(
                    (reverse_records_by_source or {}).get(normalized_trigger, ())
                )
                if reverse_records_by_source is not None and reverse_target_count <= 0:
                    continue
                if reverse_target_count < normalized_min_reverse_target_count:
                    continue
                borrow_candidates.append(
                    (
                        (
                            reverse_target_count if reverse_target_count > 0 else 1_000_000,
                            int(trigger_document_frequency.get(normalized_trigger) or 0),
                            normalized_trigger,
                        ),
                        normalized_trigger,
                    )
                )
            for _rank, normalized_trigger in sorted(borrow_candidates):
                seen.add(normalized_trigger)
                trigger_values.append(normalized_trigger)
                borrowed_count += 1
                if borrowed_count >= normalized_limit:
                    break
            if borrowed_count >= normalized_limit:
                break
        tiers = seed_target.tiers
        if borrowed_count:
            tiers = tuple(value for value in (*seed_target.tiers, tier_label) if str(value).strip())
        augmented_targets.append(
            BenchmarkShadowTarget(
                target=seed_target.target,
                case_ids=seed_target.case_ids,
                tiers=tiers,
                reviewed_triggers=tuple(trigger_values),
            )
        )
    return augmented_targets
