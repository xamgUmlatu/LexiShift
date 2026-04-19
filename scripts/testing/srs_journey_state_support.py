from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Mapping

from lexishift_core.helper.engine import get_srs_runtime_diagnostics
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.srs import SrsItem, SrsSettings, load_srs_settings, load_srs_store
from lexishift_core.srs.scheduler import get_item_retrievability, select_active_items
from lexishift_core.srs.signal_queue import load_signal_events

from srs_journey_harness_support import DEFAULT_PROFILE_ID
from srs_journey_review_support import word_package_preview


def load_signal_log(
    paths: HelperPaths, *, profile_id: str = DEFAULT_PROFILE_ID
) -> list[dict[str, object]]:
    events = load_signal_events(paths.srs_signal_queue_path_for(profile_id))
    payload: list[dict[str, object]] = []
    for index, event in enumerate(events, start=1):
        payload.append(
            {
                "index": index,
                "event_type": event.event_type,
                "pair": event.pair,
                "lemma": event.lemma,
                "source_type": event.source_type,
                "rating": event.rating,
                "ts": event.ts,
                "metadata": dict(event.metadata or {}),
            }
        )
    return payload


def published_targets_from_ruleset(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = payload.get("rules", [])
    targets = sorted(
        {
            str(rule.get("replacement") or "").strip()
            for rule in rules
            if isinstance(rule, Mapping) and str(rule.get("replacement") or "").strip()
        }
    )
    return targets


def published_sources_from_ruleset(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = payload.get("rules", [])
    sources = sorted(
        {
            str(rule.get("source_phrase") or "").strip()
            for rule in rules
            if isinstance(rule, Mapping) and str(rule.get("source_phrase") or "").strip()
        }
    )
    return sources


def snapshot_targets_from_snapshot(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    targets = payload.get("targets", [])
    if not isinstance(targets, list):
        return []
    resolved: list[str] = []
    for target in targets:
        if isinstance(target, Mapping):
            lemma = str(target.get("lemma") or target.get("replacement") or "").strip()
            if lemma:
                resolved.append(lemma)
    return sorted(set(resolved))


def _item_payload(
    item: SrsItem,
    *,
    settings: SrsSettings,
    now: datetime,
    due_lemmas: set[str],
    due_rank_by_lemma: Mapping[str, int],
    published_lemmas: set[str],
    cohort_by_lemma: Mapping[str, str],
) -> dict[str, object]:
    return {
        "lemma": item.lemma,
        "cohort": cohort_by_lemma.get(item.lemma, "frontier"),
        "status": _infer_status(item),
        "source_type": item.source_type,
        "confidence": item.confidence,
        "next_due": item.next_due,
        "due_rank": due_rank_by_lemma.get(item.lemma),
        "stability": item.stability,
        "difficulty": item.difficulty,
        "retrievability": get_item_retrievability(item, settings=settings, now=now),
        "scheduler_state": item.scheduler_state,
        "scheduler_step": item.scheduler_step,
        "last_seen": item.last_seen,
        "last_review": item.last_review,
        "exposures": int(item.exposures),
        "history_count": len(item.history),
        "recent_history": [
            {"ts": entry.ts, "rating": entry.rating} for entry in list(item.history)[-4:]
        ],
        "in_admitted": True,
        "in_due": item.lemma in due_lemmas,
        "in_published": item.lemma in published_lemmas,
        "word_package": word_package_preview(item.word_package),
    }


def _infer_status(item: SrsItem) -> str:
    history_count = len(item.history)
    if history_count == 0:
        return "new"
    if item.stability is None:
        return "learning"
    if item.stability >= 4.0:
        return "mature"
    if item.stability >= 2.0:
        return "review"
    return "learning"


def phase_snapshot(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    now: datetime,
    cohort_by_lemma: Mapping[str, str],
) -> dict[str, object]:
    diagnostics = get_srs_runtime_diagnostics(paths, pair=pair, profile_id=profile_id)
    store = load_srs_store(paths.srs_store_path_for(profile_id))
    settings = load_srs_settings(paths.srs_settings_path)
    pair_items = sorted(
        [item for item in store.items if item.language_pair == pair],
        key=lambda item: item.lemma,
    )
    due_items = select_active_items(
        pair_items,
        now=now,
        max_active=settings.max_active_items,
        allowed_pairs=[pair],
    )
    due_lemmas = {item.lemma for item in due_items}
    due_rank_by_lemma = {item.lemma: index for index, item in enumerate(due_items, start=1)}
    ruleset_path = Path(str(diagnostics.get("ruleset_path") or ""))
    snapshot_path = Path(str(diagnostics.get("snapshot_path") or ""))
    published_lemmas = (
        set(published_targets_from_ruleset(ruleset_path)) if ruleset_path.exists() else set()
    )
    published_sources = (
        published_sources_from_ruleset(ruleset_path) if ruleset_path.exists() else []
    )
    snapshot_lemmas = (
        set(snapshot_targets_from_snapshot(snapshot_path)) if snapshot_path.exists() else set()
    )
    admitted = [item.lemma for item in pair_items]
    due = sorted(due_lemmas)
    published = sorted(published_lemmas)
    return {
        "runtime": {
            "diagnostics": diagnostics,
            "ruleset_path": str(ruleset_path),
            "snapshot_path": str(snapshot_path),
            "ruleset_sources_preview": published_sources[:5],
            "snapshot_targets": sorted(snapshot_lemmas),
        },
        "sets": {
            "admitted": admitted,
            "due": due,
            "published": published,
        },
        "relationships": {
            "published_not_due": sorted(published_lemmas - due_lemmas),
            "published_not_admitted": sorted(published_lemmas - set(admitted)),
            "due_not_published": sorted(due_lemmas - published_lemmas),
        },
        "counts": {
            "admitted": len(admitted),
            "due": len(due),
            "published": len(published),
        },
        "items": [
            _item_payload(
                item,
                settings=settings,
                now=now,
                due_lemmas=due_lemmas,
                due_rank_by_lemma=due_rank_by_lemma,
                published_lemmas=published_lemmas,
                cohort_by_lemma=cohort_by_lemma,
            )
            for item in pair_items
        ],
    }


def phase_deltas(
    previous: Mapping[str, object] | None, current: Mapping[str, object]
) -> dict[str, list[str]]:
    if previous is None:
        return {
            "admitted_in": list(current.get("sets", {}).get("admitted", [])),
            "admitted_out": [],
            "due_in": list(current.get("sets", {}).get("due", [])),
            "due_out": [],
            "published_in": list(current.get("sets", {}).get("published", [])),
            "published_out": [],
        }

    previous_sets = previous.get("sets", {}) if isinstance(previous, Mapping) else {}
    current_sets = current.get("sets", {}) if isinstance(current, Mapping) else {}

    def _delta(key: str) -> tuple[list[str], list[str]]:
        before = (
            set(previous_sets.get(key, []))
            if isinstance(previous_sets.get(key, []), list)
            else set()
        )
        after = (
            set(current_sets.get(key, [])) if isinstance(current_sets.get(key, []), list) else set()
        )
        return sorted(after - before), sorted(before - after)

    admitted_in, admitted_out = _delta("admitted")
    due_in, due_out = _delta("due")
    published_in, published_out = _delta("published")
    return {
        "admitted_in": admitted_in,
        "admitted_out": admitted_out,
        "due_in": due_in,
        "due_out": due_out,
        "published_in": published_in,
        "published_out": published_out,
    }
