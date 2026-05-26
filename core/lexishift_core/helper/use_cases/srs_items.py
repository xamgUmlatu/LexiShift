from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Mapping, Optional

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.persistence.storage import load_vocab_dataset
from lexishift_core.srs import (
    SRS_LIFECYCLE_ACTIVE,
    SRS_LIFECYCLE_CLEARED,
    SRS_LIFECYCLE_DISCARDED,
    SrsInventory,
    SrsItem,
    load_srs_inventory,
    load_srs_store,
    normalize_srs_lifecycle_state,
    resolve_active_item_ids,
)
from lexishift_core.srs.time import now_utc, parse_ts


SECONDS_PER_DAY = 24 * 60 * 60
RULE_SOURCE_PREVIEW_LIMIT = 4
RULE_DETAILS_DEFAULT_LIMIT = 25
RULE_DETAILS_MAX_LIMIT = 100
ENCOUNTER_STALE_AGE_DAYS = 7


def list_srs_items(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str = "default",
    now: datetime | None = None,
    resolve_profile_id_fn: Callable[..., str],
) -> dict[str, object]:
    normalized_pair = str(pair or "").strip()
    if not normalized_pair:
        raise ValueError("Missing pair.")
    normalized_profile_id = resolve_profile_id_fn(paths, profile_id=profile_id)
    store_path = paths.srs_store_path_for(normalized_profile_id)
    inventory_path = paths.srs_inventory_path_for(normalized_profile_id)
    ruleset_path = paths.ruleset_path(normalized_pair, profile_id=normalized_profile_id)
    anchor = now or now_utc()

    if not store_path.exists():
        return {
            "status": "ok",
            "pair": normalized_pair,
            "profile_id": normalized_profile_id,
            "store_path": str(store_path),
            "store_exists": False,
            "inventory_path": str(inventory_path),
            "inventory_exists": inventory_path.exists(),
            "ruleset_path": str(ruleset_path),
            "ruleset_exists": ruleset_path.exists(),
            "rule_summary": _empty_rule_summary(ruleset_path),
            "inventory_source": "missing_store",
            "summary": _empty_summary(),
            "items": [],
        }

    store = load_srs_store(store_path)
    inventory = _load_inventory_if_present(inventory_path)
    active_item_ids, inventory_source = resolve_active_item_ids(
        store=store,
        pair=normalized_pair,
        inventory=inventory,
    )
    rules_by_lemma, rule_summary = _load_rule_summaries(ruleset_path)
    active_item_id_set = set(active_item_ids)
    scoped_items = [item for item in store.items if item.language_pair == normalized_pair]
    payload_items = [
        _item_payload(
            item,
            active_item_ids=active_item_id_set,
            rules_by_lemma=rules_by_lemma,
            now=anchor,
        )
        for item in scoped_items
    ]
    payload_items.sort(key=_item_sort_key)

    return {
        "status": "ok",
        "pair": normalized_pair,
        "profile_id": normalized_profile_id,
        "store_path": str(store_path),
        "store_exists": True,
        "inventory_path": str(inventory_path),
        "inventory_exists": inventory_path.exists(),
        "ruleset_path": str(ruleset_path),
        "ruleset_exists": ruleset_path.exists(),
        "rule_summary": rule_summary,
        "inventory_source": inventory_source,
        "summary": _summary(payload_items, inventory_active_count=len(active_item_ids)),
        "items": payload_items,
    }


def get_srs_item_rule_details(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    profile_id: str = "default",
    limit: int | None = None,
    resolve_profile_id_fn: Callable[..., str],
) -> dict[str, object]:
    normalized_pair = str(pair or "").strip()
    if not normalized_pair:
        raise ValueError("Missing pair.")
    normalized_lemma = str(lemma or "").strip()
    if not normalized_lemma:
        raise ValueError("Missing lemma.")
    normalized_profile_id = resolve_profile_id_fn(paths, profile_id=profile_id)
    resolved_limit = _normalize_rule_details_limit(limit)
    ruleset_path = paths.ruleset_path(normalized_pair, profile_id=normalized_profile_id)
    payload = _empty_rule_details_payload(
        pair=normalized_pair,
        profile_id=normalized_profile_id,
        lemma=normalized_lemma,
        ruleset_path=ruleset_path,
        limit=resolved_limit,
    )
    if not ruleset_path.exists():
        return payload

    try:
        dataset = load_vocab_dataset(ruleset_path)
    except Exception as exc:  # pragma: no cover - defensive read-only dashboard path
        payload["load_error"] = str(exc)
        return payload

    matches = [
        rule for rule in dataset.rules if str(rule.replacement or "").strip() == normalized_lemma
    ]
    matches.sort(key=_rule_detail_sort_key)
    returned = matches[:resolved_limit]
    enabled_rule_count = sum(1 for rule in matches if rule.enabled is not False)
    payload.update(
        {
            "ruleset_exists": True,
            "rule_count": len(matches),
            "enabled_rule_count": enabled_rule_count,
            "returned_rule_count": len(returned),
            "truncated": len(matches) > len(returned),
            "rules": [_rule_detail_payload(rule) for rule in returned],
        }
    )
    return payload


def _load_inventory_if_present(path: Path) -> Optional[SrsInventory]:
    if not path.exists():
        return None
    return load_srs_inventory(path)


def _item_payload(
    item: SrsItem,
    *,
    active_item_ids: set[str],
    rules_by_lemma: Mapping[str, Mapping[str, object]],
    now: datetime,
) -> dict[str, object]:
    lifecycle_state = normalize_srs_lifecycle_state(item.lifecycle_state)
    active = lifecycle_state == SRS_LIFECYCLE_ACTIVE and item.item_id in active_item_ids
    status, status_label = _dashboard_status(
        item,
        lifecycle_state=lifecycle_state,
        active=active,
        now=now,
    )
    word_package = _word_package_payload(item.word_package)
    display = str(word_package.get("surface") or item.lemma or item.item_id)
    source = word_package.get("source") if isinstance(word_package.get("source"), Mapping) else {}
    source_label = str(source.get("provider") or item.source_type or "srs")
    next_due_dt = parse_ts(item.next_due)
    due_in_seconds = int((next_due_dt - now).total_seconds()) if next_due_dt is not None else None
    last_history = item.history[-1] if item.history else None

    exposures = max(0, int(item.exposures or 0))
    review_count = len(item.history)
    rule_summary = _rule_summary_for_item(rules_by_lemma, item.lemma)
    admitted_age_days = _age_days(item.admitted_at, now=now)

    return {
        "item_id": item.item_id,
        "lemma": item.lemma,
        "display": display,
        "reading": word_package.get("reading") or "",
        "pair": item.language_pair,
        "active": active,
        "status": status,
        "status_label": status_label,
        "next_due": item.next_due,
        "due_in_seconds": due_in_seconds,
        "last_review": item.last_review,
        "last_seen": item.last_seen,
        "admitted_at": item.admitted_at,
        "admitted_age_days": admitted_age_days,
        "exposures": exposures,
        "review_count": review_count,
        "last_rating": last_history.rating if last_history else None,
        "source_type": item.source_type,
        "source_label": source_label,
        "pos": word_package.get("pos_canonical") or word_package.get("pos") or "",
        "rule_summary": rule_summary,
        "encounter_state": _encounter_state(
            active=active,
            exposures=exposures,
            review_count=review_count,
            rule_summary=rule_summary,
            admitted_age_days=admitted_age_days,
        ),
        "advanced": {
            "lifecycle_state": lifecycle_state,
            "lifecycle_reason": item.lifecycle_reason,
            "lifecycle_updated_at": item.lifecycle_updated_at,
            "scheduler_state": item.scheduler_state,
            "scheduler_step": item.scheduler_step,
            "stability": item.stability,
            "difficulty": item.difficulty,
            "confidence": item.confidence,
            "word_package": word_package,
            "history": [{"ts": entry.ts, "rating": entry.rating} for entry in item.history[-5:]],
        },
    }


def _dashboard_status(
    item: SrsItem,
    *,
    lifecycle_state: str,
    active: bool,
    now: datetime,
) -> tuple[str, str]:
    if lifecycle_state == SRS_LIFECYCLE_DISCARDED:
        return "discarded", "Discarded"
    if lifecycle_state == SRS_LIFECYCLE_CLEARED:
        return "cleared", "Cleared"
    if lifecycle_state != SRS_LIFECYCLE_ACTIVE:
        return "removed", "Removed"
    if not active:
        return "queued", "Queued"

    next_due = parse_ts(item.next_due)
    if next_due is None:
        return "learning", "Learning"
    if next_due <= now:
        return "due_now", "Due now"
    if next_due <= now + timedelta(seconds=SECONDS_PER_DAY):
        return "due_soon", "Due soon"
    if str(item.scheduler_state or "").strip().lower() == "review":
        return "reviewing", "Reviewing"
    return "learning", "Learning"


def _word_package_payload(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return dict(value)


def _load_rule_summaries(path: Path) -> tuple[dict[str, Mapping[str, object]], dict[str, object]]:
    summary = _empty_rule_summary(path)
    if not path.exists():
        return {}, summary

    try:
        dataset = load_vocab_dataset(path)
    except Exception as exc:  # pragma: no cover - defensive read-only dashboard path
        summary["load_error"] = str(exc)
        return {}, summary

    source_sets_by_lemma: dict[str, set[str]] = {}
    enabled_counts_by_lemma: dict[str, int] = {}
    total_counts_by_lemma: dict[str, int] = {}
    total_rule_count = 0
    enabled_rule_count = 0
    for rule in dataset.rules:
        lemma = str(rule.replacement or "").strip()
        if not lemma:
            continue
        total_rule_count += 1
        total_counts_by_lemma[lemma] = total_counts_by_lemma.get(lemma, 0) + 1
        if rule.enabled is False:
            continue
        source_phrase = str(rule.source_phrase or "").strip()
        enabled_rule_count += 1
        enabled_counts_by_lemma[lemma] = enabled_counts_by_lemma.get(lemma, 0) + 1
        source_sets_by_lemma.setdefault(lemma, set())
        if source_phrase:
            source_sets_by_lemma[lemma].add(source_phrase)

    rules_by_lemma: dict[str, Mapping[str, object]] = {}
    for lemma in sorted(total_counts_by_lemma.keys()):
        sources = sorted(source_sets_by_lemma.get(lemma, set()))
        preview = sources[:RULE_SOURCE_PREVIEW_LIMIT]
        rules_by_lemma[lemma] = {
            "rule_count": total_counts_by_lemma.get(lemma, 0),
            "enabled_rule_count": enabled_counts_by_lemma.get(lemma, 0),
            "source_phrases": preview,
            "source_phrase_count": len(sources),
            "source_preview_truncated": len(sources) > len(preview),
        }

    summary.update(
        {
            "ruleset_exists": True,
            "rule_count": total_rule_count,
            "enabled_rule_count": enabled_rule_count,
            "lemmas_with_rules": len(rules_by_lemma),
        }
    )
    return rules_by_lemma, summary


def _rule_summary_for_item(
    rules_by_lemma: Mapping[str, Mapping[str, object]], lemma: str
) -> Mapping[str, object]:
    return rules_by_lemma.get(
        lemma,
        {
            "rule_count": 0,
            "enabled_rule_count": 0,
            "source_phrases": [],
            "source_phrase_count": 0,
            "source_preview_truncated": False,
        },
    )


def _empty_rule_summary(path: Path) -> dict[str, object]:
    return {
        "ruleset_path": str(path),
        "ruleset_exists": path.exists(),
        "rule_count": 0,
        "enabled_rule_count": 0,
        "lemmas_with_rules": 0,
        "load_error": None,
    }


def _normalize_rule_details_limit(value: int | None) -> int:
    if value is None:
        return RULE_DETAILS_DEFAULT_LIMIT
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        resolved = RULE_DETAILS_DEFAULT_LIMIT
    return min(RULE_DETAILS_MAX_LIMIT, max(1, resolved))


def _rule_detail_sort_key(rule: object) -> tuple[int, int, str]:
    enabled_order = 0 if getattr(rule, "enabled", True) is not False else 1
    priority = int(getattr(rule, "priority", 0) or 0)
    source_phrase = str(getattr(rule, "source_phrase", "") or "").casefold()
    return (enabled_order, -priority, source_phrase)


def _rule_detail_payload(rule: object) -> dict[str, object]:
    return {
        "source_phrase": str(getattr(rule, "source_phrase", "") or ""),
        "replacement": str(getattr(rule, "replacement", "") or ""),
        "enabled": getattr(rule, "enabled", True) is not False,
        "priority": int(getattr(rule, "priority", 0) or 0),
        "case_policy": str(getattr(rule, "case_policy", "") or "match"),
        "tags": [str(tag) for tag in getattr(rule, "tags", ())],
        "created_at": getattr(rule, "created_at", None),
        "metadata": _rule_metadata_payload(getattr(rule, "metadata", None)),
    }


def _rule_metadata_payload(metadata: object) -> dict[str, object]:
    if metadata is None:
        return {}
    payload: dict[str, object] = {}
    for key in (
        "label",
        "description",
        "notes",
        "source",
        "source_type",
        "language_pair",
        "confidence",
    ):
        value = getattr(metadata, key, None)
        if value not in (None, ""):
            payload[key] = value
    examples = getattr(metadata, "examples", None)
    if examples:
        payload["examples"] = [str(item) for item in examples]
    script_forms = getattr(metadata, "script_forms", None)
    if isinstance(script_forms, Mapping):
        payload["script_forms"] = {
            str(key): str(value)
            for key, value in script_forms.items()
            if str(key).strip() and str(value).strip()
        }
    for key in ("pos", "rulegen", "semantic_admission"):
        value = getattr(metadata, key, None)
        if isinstance(value, Mapping):
            compact = {str(inner_key): inner_value for inner_key, inner_value in value.items()}
            if compact:
                payload[key] = compact
    word_package = getattr(metadata, "word_package", None)
    if isinstance(word_package, Mapping):
        compact_word_package = {
            key: word_package.get(key)
            for key in (
                "surface",
                "reading",
                "pos",
                "pos_canonical",
                "core_rank",
                "row_rank",
            )
            if word_package.get(key) not in (None, "")
        }
        source = word_package.get("source")
        if isinstance(source, Mapping) and source.get("provider"):
            compact_word_package["source_provider"] = source.get("provider")
        if compact_word_package:
            payload["word_package"] = compact_word_package
    return payload


def _empty_rule_details_payload(
    *,
    pair: str,
    profile_id: str,
    lemma: str,
    ruleset_path: Path,
    limit: int,
) -> dict[str, object]:
    return {
        "status": "ok",
        "pair": pair,
        "profile_id": profile_id,
        "lemma": lemma,
        "ruleset_path": str(ruleset_path),
        "ruleset_exists": ruleset_path.exists(),
        "rule_count": 0,
        "enabled_rule_count": 0,
        "returned_rule_count": 0,
        "limit": limit,
        "truncated": False,
        "load_error": None,
        "rules": [],
    }


def _summary(items: list[dict[str, object]], *, inventory_active_count: int) -> dict[str, int]:
    summary = _empty_summary()
    summary["total"] = len(items)
    summary["inventory_active_count"] = max(0, int(inventory_active_count))
    for item in items:
        status = str(item.get("status") or "")
        if item.get("active") is True:
            summary["active"] += 1
        if status in summary:
            summary[status] += 1
        if status in {"discarded", "cleared", "removed"}:
            summary["removed"] += 1
        encounter_state = item.get("encounter_state")
        if isinstance(encounter_state, Mapping):
            if encounter_state.get("zero_exposure") is True:
                summary["active_zero_exposure"] += 1
            if encounter_state.get("zero_feedback") is True:
                summary["active_zero_feedback"] += 1
            if encounter_state.get("zero_exposure_zero_feedback") is True:
                summary["active_zero_exposure_zero_feedback"] += 1
            if encounter_state.get("zero_exposure_zero_feedback_age_unknown") is True:
                summary["active_zero_exposure_zero_feedback_age_unknown"] += 1
            if encounter_state.get("stale_zero_exposure_zero_feedback") is True:
                summary["active_stale_zero_exposure_zero_feedback"] += 1
            if encounter_state.get("without_enabled_rules") is True:
                summary["active_without_enabled_rules"] += 1
            if encounter_state.get("needs_attention") is True:
                summary["encounter_watch"] += 1
        advanced = item.get("advanced")
        if isinstance(advanced, Mapping) and advanced.get("word_package"):
            summary["with_word_package"] += 1
    return summary


def _encounter_state(
    *,
    active: bool,
    exposures: int,
    review_count: int,
    rule_summary: Mapping[str, object],
    admitted_age_days: int | None,
) -> dict[str, object]:
    if not active:
        return {
            "zero_exposure": False,
            "zero_feedback": False,
            "zero_exposure_zero_feedback": False,
            "zero_exposure_zero_feedback_age_unknown": False,
            "stale_zero_exposure_zero_feedback": False,
            "stale_age_days": ENCOUNTER_STALE_AGE_DAYS,
            "without_enabled_rules": False,
            "needs_attention": False,
        }
    zero_exposure = exposures <= 0
    zero_feedback = review_count <= 0
    without_enabled_rules = int(rule_summary.get("enabled_rule_count") or 0) <= 0
    zero_exposure_zero_feedback = zero_exposure and zero_feedback
    age_unknown = zero_exposure_zero_feedback and admitted_age_days is None
    stale_unseen = (
        zero_exposure_zero_feedback
        and admitted_age_days is not None
        and admitted_age_days >= ENCOUNTER_STALE_AGE_DAYS
    )
    return {
        "zero_exposure": zero_exposure,
        "zero_feedback": zero_feedback,
        "zero_exposure_zero_feedback": zero_exposure_zero_feedback,
        "zero_exposure_zero_feedback_age_unknown": age_unknown,
        "stale_zero_exposure_zero_feedback": stale_unseen,
        "stale_age_days": ENCOUNTER_STALE_AGE_DAYS,
        "without_enabled_rules": without_enabled_rules,
        "needs_attention": zero_exposure_zero_feedback or without_enabled_rules,
    }


def _age_days(value: str | None, *, now: datetime) -> int | None:
    parsed = parse_ts(value)
    if parsed is None:
        return None
    return max(0, int((now - parsed).total_seconds() // SECONDS_PER_DAY))


def _empty_summary() -> dict[str, int]:
    return {
        "total": 0,
        "active": 0,
        "queued": 0,
        "due_now": 0,
        "due_soon": 0,
        "learning": 0,
        "reviewing": 0,
        "discarded": 0,
        "cleared": 0,
        "removed": 0,
        "with_word_package": 0,
        "inventory_active_count": 0,
        "active_zero_exposure": 0,
        "active_zero_feedback": 0,
        "active_zero_exposure_zero_feedback": 0,
        "active_zero_exposure_zero_feedback_age_unknown": 0,
        "active_stale_zero_exposure_zero_feedback": 0,
        "active_without_enabled_rules": 0,
        "encounter_watch": 0,
        "encounter_stale_age_days": ENCOUNTER_STALE_AGE_DAYS,
    }


def _item_sort_key(item: dict[str, object]) -> tuple[int, int, str, str]:
    status_order = {
        "due_now": 0,
        "due_soon": 1,
        "learning": 2,
        "reviewing": 3,
        "queued": 4,
        "discarded": 8,
        "cleared": 8,
        "removed": 9,
    }
    due = item.get("due_in_seconds")
    due_order = int(due) if isinstance(due, int) else 10**12
    return (
        status_order.get(str(item.get("status") or ""), 7),
        due_order,
        str(item.get("display") or ""),
        str(item.get("item_id") or ""),
    )
