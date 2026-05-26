from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import sqlite3
import tempfile
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import annotate_rules_with_srs_serving_metadata
from lexishift_core.replacement.core import VocabRule
from lexishift_core.srs import SrsItem, load_srs_store
from lexishift_core.srs.scheduler import select_active_items
from lexishift_core.srs.time import now_utc, parse_ts
from lexishift_core.srs.browsing_admission import (
    BrowsingSignalAggregate,
    BrowsingSignalStore,
    save_browsing_signal_store,
)
from synthetic_translation_fixture_support import (
    write_jmdict_fixture,
    write_translation_dictionary_sqlite_fixture,
)

_TEMP_ROOT = Path(tempfile.gettempdir())
_TEMP_ROOT_RESOLVED = _TEMP_ROOT.resolve(strict=False)
_TIMESTAMP_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)\b")
_GENERATION_ID_RE = re.compile(r"\b([a-z]{2}-[a-z]{2}:[A-Za-z0-9._-]+):[0-9a-f]{8,}\b")
_TEMP_PATH_RE = re.compile(
    r"(?:" + re.escape(str(_TEMP_ROOT)) + r"|" + re.escape(str(_TEMP_ROOT_RESOLVED)) + r')/[^"\s,]+'
)


def _alpha_suffix(index: int) -> str:
    value = max(0, int(index))
    chars: list[str] = []
    for _ in range(3):
        chars.append(chr(ord("a") + (value % 26)))
        value //= 26
    return "".join(reversed(chars))


def _build_tokens(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{_alpha_suffix(i)}" for i in range(max(0, int(count)))]


def _write_frequency_db(*, path: Path, lemmas: list[str], pos: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("DROP TABLE IF EXISTS frequency;")
        conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, pos TEXT);")
        rows = [
            (lemma, float(index + 1), float(len(lemmas) - index), pos)
            for index, lemma in enumerate(lemmas)
        ]
        conn.executemany(
            "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?);",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def _load_ruleset_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Ruleset payload must be an object: {path}")
    return payload


def _load_snapshot_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Snapshot payload must be an object: {path}")
    return payload


def summarize_findings(
    findings: Sequence[Mapping[str, Any]],
    *,
    fail_on_warn: bool = False,
) -> dict[str, Any]:
    pass_count = 0
    warn_count = 0
    fail_count = 0
    for item in findings:
        level = str(item.get("level") or "").upper()
        if level == "PASS":
            pass_count += 1
        elif level == "WARN":
            warn_count += 1
        elif level == "FAIL":
            fail_count += 1
    status = "FAIL" if fail_count else "WARN" if warn_count else "PASS"
    should_fail = fail_count > 0 or (fail_on_warn and warn_count > 0)
    return {
        "status": status,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "should_fail": should_fail,
    }


def _normalize_temp_path_for_publication(value: str) -> str:
    try:
        path = Path(value)
    except (OSError, RuntimeError, ValueError):
        return value
    relative = None
    for root in (_TEMP_ROOT, _TEMP_ROOT_RESOLVED):
        try:
            relative = path.relative_to(root)
            break
        except ValueError:
            pass
        try:
            relative = path.resolve(strict=False).relative_to(root)
            break
        except (OSError, RuntimeError, ValueError):
            pass
    if relative is None:
        return value
    stable_parts = relative.parts[1:] if len(relative.parts) > 1 else ()
    if not stable_parts:
        return "<temp_root>"
    return "/".join(("<temp_root>", *stable_parts))


def _normalize_string_for_publication(value: str) -> str:
    normalized = _TEMP_PATH_RE.sub(
        lambda match: _normalize_temp_path_for_publication(match.group(0)),
        value,
    )
    normalized = _GENERATION_ID_RE.sub(r"\1:<generated>", normalized)
    normalized = _TIMESTAMP_RE.sub("<timestamp>", normalized)
    return normalized


def _normalize_for_publication(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_for_publication(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_for_publication(item) for item in value]
    if isinstance(value, str):
        return _normalize_string_for_publication(value)
    return value


def prepare_report_for_publication(report: Mapping[str, Any]) -> dict[str, Any]:
    published = _normalize_for_publication(deepcopy(dict(report)))
    published["generated_at"] = "<generated_at>"
    published["artifact_normalization"] = {
        "mode": "stable_latest_v1",
        "generated_at": "<generated_at>",
        "timestamps": "<timestamp>",
        "temp_root": "<temp_root>",
        "generation_ids": "<generated>",
    }
    return published


def _round_optional(value: object, *, digits: int = 6) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return round(parsed, digits)


def _item_snapshot(item: SrsItem) -> dict[str, Any]:
    return {
        "item_id": item.item_id,
        "lemma": item.lemma,
        "lifecycle_state": item.lifecycle_state,
        "scheduler_state": item.scheduler_state,
        "scheduler_step": item.scheduler_step,
        "stability": _round_optional(item.stability),
        "difficulty": _round_optional(item.difficulty),
        "last_review": item.last_review,
        "next_due": item.next_due,
        "exposures": int(item.exposures or 0),
        "history_count": len(tuple(item.history or ())),
    }


def store_snapshot(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    max_active: int,
) -> dict[str, Any]:
    store = load_srs_store(paths.srs_store_path_for(profile_id))
    pair_items = sorted(
        [item for item in store.items if item.language_pair == pair],
        key=lambda item: item.lemma,
    )
    due_items = select_active_items(
        store.items,
        max_active=max_active,
        allowed_pairs=[pair],
    )
    return {
        "total_items_for_pair": len(pair_items),
        "active_count": sum(1 for item in pair_items if item.lifecycle_state == "active"),
        "due_count": len(due_items),
        "lemmas": [item.lemma for item in pair_items],
        "due_lemmas": [item.lemma for item in due_items],
        "items": [_item_snapshot(item) for item in pair_items],
    }


def _items_by_lemma(snapshot: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not isinstance(snapshot, Mapping):
        return {}
    items = snapshot.get("items")
    if not isinstance(items, list):
        return {}
    mapped: dict[str, Mapping[str, Any]] = {}
    for item in items:
        if not isinstance(item, Mapping):
            continue
        lemma = str(item.get("lemma") or "").strip()
        if lemma:
            mapped[lemma] = item
    return mapped


def snapshot_delta(
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
) -> dict[str, Any]:
    before_items = _items_by_lemma(before)
    after_items = _items_by_lemma(after)
    before_lemmas = set(before_items)
    after_lemmas = set(after_items)
    shared_lemmas = sorted(before_lemmas & after_lemmas)
    changed_lemmas = [
        lemma for lemma in shared_lemmas if dict(before_items[lemma]) != dict(after_items[lemma])
    ]
    reviewed_lemmas = [
        lemma
        for lemma in shared_lemmas
        if int(after_items[lemma].get("history_count") or 0)
        > int(before_items[lemma].get("history_count") or 0)
    ]
    scheduler_fields = ("scheduler_state", "scheduler_step", "stability", "difficulty", "next_due")
    scheduler_changed_lemmas = [
        lemma
        for lemma in shared_lemmas
        if any(
            before_items[lemma].get(field) != after_items[lemma].get(field)
            for field in scheduler_fields
        )
    ]
    return {
        "total_items_delta": int((after or {}).get("total_items_for_pair") or 0)
        - int((before or {}).get("total_items_for_pair") or 0),
        "active_count_delta": int((after or {}).get("active_count") or 0)
        - int((before or {}).get("active_count") or 0),
        "due_count_delta": int((after or {}).get("due_count") or 0)
        - int((before or {}).get("due_count") or 0),
        "added_lemmas": sorted(after_lemmas - before_lemmas),
        "removed_lemmas": sorted(before_lemmas - after_lemmas),
        "changed_lemmas": changed_lemmas,
        "reviewed_lemmas": reviewed_lemmas,
        "scheduler_changed_lemmas": scheduler_changed_lemmas,
    }


def ruleset_unique_target_count(path: Path) -> int:
    payload = _load_ruleset_payload(path)
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        return 0
    replacements = {
        str(rule.get("replacement") or "").strip()
        for rule in rules
        if isinstance(rule, Mapping) and str(rule.get("replacement") or "").strip()
    }
    return len(replacements)


def ruleset_srs_due_metadata_count(path: Path) -> int:
    payload = _load_ruleset_payload(path)
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        return 0
    replacements = {
        str(rule.get("replacement") or "").strip()
        for rule in rules
        if isinstance(rule, Mapping)
        and str(rule.get("replacement") or "").strip()
        and _srs_serving_metadata(rule) is not None
    }
    return len(replacements)


def ruleset_due_active_target_count(path: Path) -> int:
    payload = _load_ruleset_payload(path)
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        return 0
    now = now_utc()
    replacements = {
        str(rule.get("replacement") or "").strip()
        for rule in rules
        if isinstance(rule, Mapping)
        and str(rule.get("replacement") or "").strip()
        and _srs_rule_is_due(rule, now=now)
    }
    return len(replacements)


def snapshot_target_count(path: Path) -> int:
    payload = _load_snapshot_payload(path)
    stats = payload.get("stats")
    if isinstance(stats, Mapping) and stats.get("target_count") is not None:
        return int(stats.get("target_count") or 0)
    targets = payload.get("targets", [])
    return len(targets) if isinstance(targets, list) else 0


def build_seed_candidates() -> list[SimpleNamespace]:
    specs = [
        ("alpha", 0.95, "noun", 1.00),
        ("beta", 0.90, "noun", 1.00),
        ("gamma", 0.84, "adjective", 0.85),
        ("delta", 0.78, "verb", 0.70),
        ("epsilon", 0.73, "adverb", 0.55),
        ("zeta", 0.68, "other", 0.40),
    ]
    candidates: list[SimpleNamespace] = []
    for index, (lemma, base_weight, bucket, pos_weight) in enumerate(specs):
        candidates.append(
            SimpleNamespace(
                lemma=lemma,
                language_pair="en-ja",
                core_rank=float(index + 1),
                pos=f"{bucket}-tag",
                pos_bucket=bucket,
                pos_weight=pos_weight,
                pmw=100.0 - (index * 5.0),
                base_weight=base_weight,
                admission_weight=round(base_weight * pos_weight, 6),
                metadata={},
            )
        )
    return candidates


def seed_browsing_preview_store(paths: HelperPaths, *, pair: str, profile_id: str) -> None:
    prefix_by_pair = {
        "en-ja": "ja",
        "en-de": "de",
    }
    prefix = prefix_by_pair.get(pair)
    if not prefix:
        return
    save_browsing_signal_store(
        BrowsingSignalStore(
            pair=pair,
            profile_id=profile_id,
            items={
                f"{prefix}abw": BrowsingSignalAggregate(
                    target_lemma=f"{prefix}abw",
                    target_hit_count=80.0,
                ),
                f"{prefix}abx": BrowsingSignalAggregate(
                    target_lemma=f"{prefix}abx",
                    target_hit_count=30.0,
                ),
            },
        ),
        paths.srs_browsing_signal_store_path_for(profile_id, pair),
    )


def browsing_preview_findings(
    refresh_payload: Mapping[str, Any], *, pair: str
) -> list[dict[str, Any]]:
    browsing_preview = refresh_payload.get("browsing_admission_preview")
    if not isinstance(browsing_preview, Mapping):
        return [
            {
                "level": "FAIL",
                "code": "SRS_BROWSING_PREVIEW_MISSING",
                "pair": pair,
                "message": "Refresh response did not include browsing preview diagnostics.",
                "details": None,
            }
        ]
    simulations = browsing_preview.get("simulations")
    balanced = simulations.get("balanced") if isinstance(simulations, Mapping) else None
    strong = simulations.get("strong") if isinstance(simulations, Mapping) else None
    balanced_lane_count = (
        int(balanced.get("browsing_lane_count") or 0) if isinstance(balanced, Mapping) else 0
    )
    strong_lane_count = (
        int(strong.get("browsing_lane_count") or 0) if isinstance(strong, Mapping) else 0
    )
    matching_signal_count = int(browsing_preview.get("matching_signal_count") or 0)
    aggregate_item_count = int(browsing_preview.get("aggregate_item_count") or 0)
    if aggregate_item_count > 0 and matching_signal_count > 0 and balanced_lane_count > 0:
        return [
            {
                "level": "PASS",
                "code": "SRS_BROWSING_PREVIEW_SIGNAL_VISIBLE",
                "pair": pair,
                "message": (
                    "Refresh preview shows non-empty browsing signal without mutating actual "
                    "SRS admission."
                ),
                "details": (
                    f"aggregate_item_count={aggregate_item_count} "
                    f"matching_signal_count={matching_signal_count} "
                    f"balanced_browsing_lane_count={balanced_lane_count} "
                    f"strong_browsing_lane_count={strong_lane_count}"
                ),
            }
        ]
    return [
        {
            "level": "FAIL",
            "code": "SRS_BROWSING_PREVIEW_SIGNAL_MISSING",
            "pair": pair,
            "message": "Refresh preview did not expose the seeded browsing signal.",
            "details": json.dumps(browsing_preview, ensure_ascii=False),
        }
    ]


def create_frequency_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL)")
        conn.execute(
            "INSERT INTO frequency (lemma, core_rank, pmw) VALUES (?, ?, ?)",
            ("alpha", 1.0, 100.0),
        )
        conn.commit()
    finally:
        conn.close()
    return path


def stub_run_rulegen_for_pair(*, store, pair, **kwargs):
    active_item_ids = kwargs.get("active_item_ids")
    active_item_id_set = (
        {str(item_id).strip() for item_id in active_item_ids if str(item_id).strip()}
        if isinstance(active_item_ids, (frozenset, list, set, tuple))
        else None
    )
    pair_lemmas = sorted(
        {
            item.lemma
            for item in store.items
            if item.language_pair == pair
            and (active_item_id_set is None or item.item_id in active_item_id_set)
        }
    )
    rules = tuple(
        VocabRule(source_phrase=f"src_{lemma}", replacement=lemma) for lemma in pair_lemmas
    )
    rules = annotate_rules_with_srs_serving_metadata(
        rules,
        store=store,
        pair=pair,
        active_item_ids=active_item_ids,
    )
    snapshot_targets = [{"lemma": lemma, "sources": [f"src_{lemma}"]} for lemma in pair_lemmas]
    snapshot = {
        "version": 1,
        "pair": pair,
        "targets": snapshot_targets,
        "stats": {
            "target_count": len(pair_lemmas),
            "rule_count": len(rules),
            "source_count": len(rules),
        },
    }
    return store, SimpleNamespace(rules=rules, snapshot=snapshot, target_count=len(pair_lemmas))


def _srs_serving_metadata(rule: Mapping[str, Any]) -> Mapping[str, Any] | None:
    metadata = rule.get("metadata")
    if not isinstance(metadata, Mapping):
        return None
    rulegen = metadata.get("rulegen")
    if isinstance(rulegen, Mapping):
        srs = rulegen.get("srs")
        if isinstance(srs, Mapping):
            return srs
    if "next_due" in metadata or "in_due" in metadata:
        return metadata
    return None


def _srs_rule_is_due(rule: Mapping[str, Any], *, now) -> bool:
    srs = _srs_serving_metadata(rule)
    if srs is None:
        return True
    next_due = parse_ts(srs.get("next_due"))
    if next_due is not None:
        return next_due <= now
    in_due = srs.get("in_due")
    if isinstance(in_due, bool):
        return in_due
    return True


def build_pair_resources(paths: HelperPaths, *, pair: str) -> None:
    if pair == "en-ja":
        targets = _build_tokens("ja", 70)
        sources = _build_tokens("eng", 70)
        _write_frequency_db(
            path=paths.frequency_packs_dir / "freq-ja-bccwj.sqlite",
            lemmas=targets,
            pos="名詞-普通名詞-一般",
        )
        write_jmdict_fixture(
            paths.language_packs_dir / "JMdict_e",
            entries=list(zip(targets, sources, strict=True)),
        )
        return
    if pair == "en-de":
        targets = _build_tokens("de", 70)
        sources = _build_tokens("eng", 70)
        _write_frequency_db(
            path=paths.frequency_packs_dir / "freq-de-default.sqlite",
            lemmas=targets,
            pos="SUB:NOM:SIN:NEU",
        )
        write_translation_dictionary_sqlite_fixture(
            paths.language_packs_dir / "freedict-de-en.sqlite",
            entries=[
                (target, source, "noun") for target, source in zip(targets, sources, strict=True)
            ],
            metadata_source="synthetic_srs_quality",
        )
        return
    raise ValueError(f"Unsupported synthetic SRS pair: {pair}")
