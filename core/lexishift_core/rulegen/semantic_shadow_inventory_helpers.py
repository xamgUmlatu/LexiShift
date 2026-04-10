from __future__ import annotations

from typing import Callable, Mapping, Sequence

from lexishift_core.resources.dict_loaders import TranslationGlossRecord


def build_forward_shadow_index(
    *,
    benchmark_targets: Sequence[object],
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    provider: str,
    collect_records: Callable[[Sequence[TranslationGlossRecord]], Sequence[TranslationGlossRecord]],
    active_candidate_builder: Callable[..., list[dict[str, object]]],
) -> dict[str, list[dict[str, object]]]:
    trigger_index: dict[str, list[dict[str, object]]] = {}
    for benchmark_target in benchmark_targets:
        target = str(getattr(benchmark_target, "target", "") or "").strip()
        if not target:
            continue
        reviewed_triggers = tuple(
            str(trigger).strip()
            for trigger in (getattr(benchmark_target, "reviewed_triggers", ()) or ())
            if str(trigger).strip()
        )
        forward_records = collect_records(forward_records_by_target.get(target, ()))
        for trigger in reviewed_triggers:
            active_candidates = active_candidate_builder(
                target=target,
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


def build_active_profile_fallback(
    *,
    target: str,
    records: Sequence[TranslationGlossRecord],
    provider: str,
    canonical_pos_builder: Callable[[TranslationGlossRecord], str],
) -> dict[str, object] | None:
    canonical_pos_values = {
        canonical_pos_builder(record) for record in records if canonical_pos_builder(record)
    }
    if len(canonical_pos_values) != 1:
        return None
    return {
        "target": str(target or "").strip(),
        "canonical_pos": next(iter(canonical_pos_values)),
        "provider": str(provider or "").strip() or "unknown",
        "profile_kind": "forward_target_pos_profile",
        "profile_record_count": len(records),
    }


def build_inventory_summary(targets: Sequence[Mapping[str, object]]) -> dict[str, object]:
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
