#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.browsing_admission import BrowsingSignalIngestPolicy  # noqa: E402
from lexishift_core.srs.store import SrsSettings  # noqa: E402


REPORT_SCHEMA_VERSION = 1
DEFAULT_PAIR = "en-es"
DEFAULT_PROFILE_ID = "default"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_resource_budget_audit_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_resource_budget_audit_latest.md"

EXTENSION_SRS_STORE = PROJECT_ROOT / "apps" / "chrome-extension" / "shared" / "srs" / "srs_store.js"
EXTENSION_SRS_METRICS = (
    PROJECT_ROOT / "apps" / "chrome-extension" / "shared" / "srs" / "srs_metrics.js"
)
EXTENSION_BROWSING_SIGNALS = (
    PROJECT_ROOT
    / "apps"
    / "chrome-extension"
    / "shared"
    / "srs"
    / "srs_browsing_admission_signals.js"
)
EXTENSION_SETTINGS_DEFAULTS = (
    PROJECT_ROOT / "apps" / "chrome-extension" / "shared" / "settings" / "settings_defaults.js"
)
EXTENSION_HELPER_CACHE = (
    PROJECT_ROOT / "apps" / "chrome-extension" / "shared" / "helper" / "helper_cache.js"
)
HELPER_SIGNAL_QUEUE = PROJECT_ROOT / "core" / "lexishift_core" / "srs" / "signal_queue.py"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit LexiShift SRS cognitive-load and storage/cache budget posture. "
            "The report is read-only and does not mutate helper or extension state."
        )
    )
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--profile-id", default=DEFAULT_PROFILE_ID)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help=(
            "Optional LexiShift helper data root. Defaults to LEXISHIFT_DATA_DIR "
            "or the platform default, read-only."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        pair=str(args.pair),
        profile_id=str(args.profile_id),
        data_root=args.data_root,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_report(
    *,
    pair: str = DEFAULT_PAIR,
    profile_id: str = DEFAULT_PROFILE_ID,
    data_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    normalized_pair = str(pair or DEFAULT_PAIR).strip() or DEFAULT_PAIR
    normalized_profile = _safe_profile_id(profile_id)
    resolved_data_root = (data_root or _default_data_root()).expanduser()
    code_budgets = _code_budget_rows()
    helper_artifacts = _helper_artifact_summary(
        data_root=resolved_data_root,
        profile_id=normalized_profile,
        pair=normalized_pair,
    )
    findings = _findings(code_budgets, helper_artifacts)
    status = "review" if any(row["level"] == "REVIEW" for row in findings) else "ok"
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": status,
        "decision": (
            "srs_resource_budget_ready_with_known_gaps"
            if status == "ok"
            else "srs_resource_budget_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "scope": {
            "pair": normalized_pair,
            "profile_id": normalized_profile,
            "data_root": str(resolved_data_root),
            "data_root_exists": resolved_data_root.exists(),
            "read_only": True,
        },
        "code_budget_rows": code_budgets,
        "helper_artifacts": helper_artifacts,
        "summary": _summary(code_budgets, helper_artifacts, findings),
        "findings": findings,
        "limitations": [
            "The audit reads helper artifacts from disk but does not inspect live chrome.storage.local values.",
            "Chrome storage usage is represented by source constants until a browser-profile export path is added.",
            "File-size thresholds are advisory MVP review thresholds, not Chrome or OS hard limits.",
            "Encounter-starvation diagnostics are based on stored exposure/review counters; they cannot prove future page encounter frequency.",
        ],
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    scope = _as_mapping(report.get("scope"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# SRS Resource Budget Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Pair: `{scope.get('pair', '')}`",
        f"- Profile: `{scope.get('profile_id', '')}`",
        f"- Data root exists: `{scope.get('data_root_exists', False)}`",
        "",
        "## Summary",
        "",
        f"- Code budget rows: `{summary.get('code_budget_row_count', 0)}`",
        f"- Bounded code rows: `{summary.get('bounded_code_row_count', 0)}`",
        f"- Helper artifact rows: `{summary.get('helper_artifact_row_count', 0)}`",
        f"- Helper artifact bytes: `{summary.get('helper_artifact_total_bytes', 0)}`",
        f"- Active SRS items: `{summary.get('active_item_count', 0)}`",
        f"- Zero-exposure active items: `{summary.get('zero_exposure_active_count', 0)}`",
        f"- Zero-feedback active items: `{summary.get('zero_feedback_active_count', 0)}`",
        "",
        "## Code Budgets",
        "",
        "| Surface | Budget | Cap | Current | Status | Notes |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in _mapping_rows(report.get("code_budget_rows")):
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{row.get('surface', '')}`",
                    f"`{row.get('budget', '')}`",
                    str(row.get("cap", "")),
                    str(row.get("current", "")),
                    f"`{row.get('status', '')}`",
                    str(row.get("notes", "")),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Helper Artifacts",
            "",
            "| Artifact | Exists | Bytes | Key Counts | Status |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for row in _mapping_rows(_as_mapping(report.get("helper_artifacts")).get("artifacts")):
        counts = ", ".join(
            f"{key}={value}" for key, value in _as_mapping(row.get("counts")).items()
        )
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{row.get('id', '')}`",
                    f"`{row.get('exists', False)}`",
                    str(row.get("bytes", 0)),
                    counts,
                    f"`{row.get('status', '')}`",
                )
            )
            + " |"
        )
    stale_rows = _mapping_rows(
        _as_mapping(report.get("helper_artifacts")).get("stale_active_preview")
    )
    lines.extend(["", "## Encounter-Starvation Preview", ""])
    if stale_rows:
        lines.extend(
            [
                "| Lemma | Exposures | Reviews | Rule Count | Source Phrases |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in stale_rows:
            lines.append(
                "| "
                + " | ".join(
                    (
                        f"`{row.get('lemma', '')}`",
                        str(row.get("exposures", 0)),
                        str(row.get("review_count", 0)),
                        str(row.get("rule_count", 0)),
                        str(row.get("source_phrase_count", 0)),
                    )
                )
                + " |"
            )
    else:
        lines.append(
            "- No zero-exposure/zero-feedback active items were visible in the audited helper store."
        )
    lines.extend(["", "## Findings", ""])
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}"
        )
    lines.extend(["", "## Limitations", ""])
    for limitation in _string_list(report.get("limitations")):
        lines.append(f"- {limitation}")
    return "\n".join(lines).rstrip() + "\n"


def _code_budget_rows() -> list[dict[str, Any]]:
    settings = SrsSettings()
    browsing_policy = BrowsingSignalIngestPolicy()
    rows = [
        _bounded_row(
            surface="helper_srs_settings",
            budget="max_active_items",
            cap=settings.max_active_items,
            current=settings.max_active_items,
            owner="helper",
            notes="Default active S capacity for a pair/profile.",
        ),
        _bounded_row(
            surface="helper_srs_settings",
            budget="max_new_items_per_day",
            cap=settings.max_new_items_per_day,
            current=settings.max_new_items_per_day,
            owner="helper",
            notes="Current code treats this as a per-refresh admission cap.",
        ),
        _bounded_row(
            surface="extension_srs_store",
            budget="max_items",
            cap=_js_const_int(EXTENSION_SRS_STORE, "MAX_ITEMS"),
            current="source_constant",
            owner="extension",
            notes="Extension-local projection store prune cap.",
        ),
        _bounded_row(
            surface="extension_srs_store",
            budget="max_history_per_item",
            cap=_js_const_int(EXTENSION_SRS_STORE, "MAX_HISTORY"),
            current="source_constant",
            owner="extension",
            notes="Extension-local history clamp per item.",
        ),
        _bounded_row(
            surface="extension_exposure_log",
            budget="max_entries",
            cap=_js_const_int(EXTENSION_SRS_METRICS, "MAX_ENTRIES"),
            current="source_constant",
            owner="extension",
            notes="Extension exposure telemetry ring buffer.",
        ),
        _bounded_row(
            surface="extension_browsing_admission_sender",
            budget="max_pending_scopes",
            cap=_js_const_int(EXTENSION_BROWSING_SIGNALS, "DEFAULT_MAX_SCOPES"),
            current="source_constant",
            owner="extension",
            notes="In-memory pending browsing-signal scopes before flush.",
        ),
        _bounded_row(
            surface="extension_browsing_admission_sender",
            budget="max_signals_per_packet",
            cap=_js_const_int(EXTENSION_BROWSING_SIGNALS, "DEFAULT_MAX_SIGNALS_PER_PACKET"),
            current="source_constant",
            owner="extension",
            notes="Extension packet construction cap.",
        ),
        _bounded_row(
            surface="extension_browsing_admission_sender",
            budget="max_count_per_signal",
            cap=_js_const_int(EXTENSION_BROWSING_SIGNALS, "DEFAULT_MAX_COUNT_PER_SIGNAL"),
            current="source_constant",
            owner="extension",
            notes="Extension-side per-packet signal count cap.",
        ),
        _bounded_row(
            surface="helper_browsing_signal_ingest",
            budget="max_signals_per_packet",
            cap=browsing_policy.max_signals_per_packet,
            current=browsing_policy.max_signals_per_packet,
            owner="helper",
            notes="Helper ingest packet cap.",
        ),
        _bounded_row(
            surface="helper_browsing_signal_ingest",
            budget="max_items_per_store",
            cap=browsing_policy.max_items_per_store,
            current=browsing_policy.max_items_per_store,
            owner="helper",
            notes="Decayed browsing aggregate store cap per pair/profile.",
        ),
        _bounded_row(
            surface="helper_signal_queue",
            budget="max_events",
            cap=_python_default_int(HELPER_SIGNAL_QUEUE, "max_events"),
            current="source_default",
            owner="helper",
            notes="Signal queue save/append event cap.",
        ),
        _bounded_row(
            surface="runtime_page_budget",
            budget="max_replacements_per_page",
            cap=_settings_default_int("maxReplacementsPerPage"),
            current="source_default",
            owner="extension",
            notes="Standard replacement density cap.",
        ),
        _bounded_row(
            surface="runtime_page_budget",
            budget="max_replacements_per_lemma_per_page",
            cap=_settings_default_int("maxReplacementsPerLemmaPerPage"),
            current="source_default",
            owner="extension",
            notes="Standard repeated-lemma density cap.",
        ),
    ]
    rows.extend(_helper_cache_rows())
    return rows


def _helper_artifact_summary(
    *,
    data_root: Path,
    profile_id: str,
    pair: str,
) -> dict[str, Any]:
    profile_dir = data_root / "srs" / "profiles" / profile_id
    safe_pair = pair.replace("/", "-").replace(":", "-")
    paths = {
        "srs_store": profile_dir / "srs_store.json",
        "srs_inventory": profile_dir / "srs_inventory.json",
        "srs_ruleset": profile_dir / f"srs_ruleset_{safe_pair}.json",
        "srs_rulegen_snapshot": profile_dir / f"srs_rulegen_snapshot_{safe_pair}.json",
        "srs_semantic_inventory": profile_dir / f"srs_semantic_inventory_{safe_pair}.json",
        "srs_signal_queue": profile_dir / "srs_signal_queue.json",
        "srs_browsing_signal_store": profile_dir / f"srs_browsing_signals_{safe_pair}.json",
        "srs_admission_suppression": profile_dir / "srs_admission_suppression.json",
    }
    store_payload = _load_json_if_exists(paths["srs_store"])
    inventory_payload = _load_json_if_exists(paths["srs_inventory"])
    ruleset_payload = _load_json_if_exists(paths["srs_ruleset"])
    signal_payload = _load_json_if_exists(paths["srs_signal_queue"])
    browsing_payload = _load_json_if_exists(paths["srs_browsing_signal_store"])
    suppression_payload = _load_json_if_exists(paths["srs_admission_suppression"])

    item_rows = _store_item_rows(store_payload, pair=pair)
    active_ids = _active_inventory_ids(inventory_payload, pair=pair, fallback_items=item_rows)
    rule_counts = _rule_counts_by_lemma(ruleset_payload)
    stale_active = _stale_active_rows(item_rows, active_ids=active_ids, rule_counts=rule_counts)

    artifacts = [
        _artifact_row(
            "srs_store",
            paths["srs_store"],
            counts=_store_counts(item_rows, active_ids=active_ids),
            review_threshold_bytes=2_000_000,
        ),
        _artifact_row(
            "srs_inventory",
            paths["srs_inventory"],
            counts={
                "resolved_active_item_ids": len(active_ids),
                "inventory_file_active_item_ids": _inventory_file_active_count(
                    inventory_payload,
                    pair=pair,
                ),
            },
            review_threshold_bytes=500_000,
        ),
        _artifact_row(
            "srs_ruleset",
            paths["srs_ruleset"],
            counts=_ruleset_counts(ruleset_payload),
            review_threshold_bytes=5_000_000,
        ),
        _artifact_row(
            "srs_rulegen_snapshot",
            paths["srs_rulegen_snapshot"],
            counts=_generic_json_counts(_load_json_if_exists(paths["srs_rulegen_snapshot"])),
            review_threshold_bytes=5_000_000,
        ),
        _artifact_row(
            "srs_semantic_inventory",
            paths["srs_semantic_inventory"],
            counts=_generic_json_counts(_load_json_if_exists(paths["srs_semantic_inventory"])),
            review_threshold_bytes=10_000_000,
        ),
        _artifact_row(
            "srs_signal_queue",
            paths["srs_signal_queue"],
            counts=_signal_counts(signal_payload, pair=pair),
            review_threshold_bytes=2_000_000,
        ),
        _artifact_row(
            "srs_browsing_signal_store",
            paths["srs_browsing_signal_store"],
            counts=_browsing_counts(browsing_payload),
            review_threshold_bytes=3_000_000,
        ),
        _artifact_row(
            "srs_admission_suppression",
            paths["srs_admission_suppression"],
            counts=_suppression_counts(suppression_payload, pair=pair),
            review_threshold_bytes=500_000,
        ),
    ]
    return {
        "profile_dir": str(profile_dir),
        "profile_dir_exists": profile_dir.exists(),
        "artifacts": artifacts,
        "active_item_count": len(active_ids),
        "stale_active_count": len(stale_active),
        "zero_exposure_active_count": sum(1 for row in stale_active if row["exposures"] == 0),
        "zero_feedback_active_count": sum(1 for row in stale_active if row["review_count"] == 0),
        "stale_active_preview": stale_active[:25],
    }


def _store_item_rows(payload: Mapping[str, Any] | None, *, pair: str) -> list[dict[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    rows = []
    for item in payload.get("items", ()):
        if not isinstance(item, Mapping):
            continue
        if str(item.get("language_pair") or "").strip() != pair:
            continue
        rows.append(
            {
                "item_id": str(item.get("item_id") or ""),
                "lemma": str(item.get("lemma") or ""),
                "lifecycle_state": str(item.get("lifecycle_state") or "active"),
                "exposures": _safe_int(item.get("exposures")),
                "review_count": len(
                    item.get("srs_history") if isinstance(item.get("srs_history"), list) else []
                ),
                "last_seen": str(item.get("last_seen") or ""),
                "last_review": str(item.get("last_review") or ""),
                "scheduler_state": str(item.get("scheduler_state") or ""),
            }
        )
    return rows


def _active_inventory_ids(
    payload: Mapping[str, Any] | None,
    *,
    pair: str,
    fallback_items: Sequence[Mapping[str, Any]],
) -> set[str]:
    if isinstance(payload, Mapping):
        pairs = payload.get("pairs")
        if isinstance(pairs, Mapping):
            pair_payload = pairs.get(pair)
            if isinstance(pair_payload, Mapping):
                ids = pair_payload.get("active_item_ids")
                if isinstance(ids, list):
                    return {str(item_id) for item_id in ids if str(item_id or "").strip()}
    return {
        str(item.get("item_id") or "")
        for item in fallback_items
        if str(item.get("lifecycle_state") or "active") == "active"
    }


def _rule_counts_by_lemma(payload: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, Mapping):
        return {}
    counts: dict[str, dict[str, Any]] = {}
    for rule in payload.get("rules", ()):
        if not isinstance(rule, Mapping):
            continue
        lemma = str(rule.get("replacement") or "").strip()
        if not lemma:
            continue
        row = counts.setdefault(
            lemma,
            {
                "rule_count": 0,
                "enabled_rule_count": 0,
                "source_phrases": set(),
            },
        )
        row["rule_count"] += 1
        if rule.get("enabled") is not False:
            row["enabled_rule_count"] += 1
            source_phrase = str(rule.get("source_phrase") or "").strip()
            if source_phrase:
                row["source_phrases"].add(source_phrase)
    return counts


def _stale_active_rows(
    item_rows: Sequence[Mapping[str, Any]],
    *,
    active_ids: set[str],
    rule_counts: Mapping[str, Mapping[str, int]],
) -> list[dict[str, Any]]:
    rows = []
    for item in item_rows:
        if str(item.get("item_id") or "") not in active_ids:
            continue
        if str(item.get("lifecycle_state") or "active") != "active":
            continue
        exposures = _safe_int(item.get("exposures"))
        review_count = _safe_int(item.get("review_count"))
        if exposures > 0 or review_count > 0:
            continue
        lemma = str(item.get("lemma") or "")
        rules = _as_mapping(rule_counts.get(lemma))
        rows.append(
            {
                "item_id": str(item.get("item_id") or ""),
                "lemma": lemma,
                "exposures": exposures,
                "review_count": review_count,
                "last_seen": str(item.get("last_seen") or ""),
                "last_review": str(item.get("last_review") or ""),
                "scheduler_state": str(item.get("scheduler_state") or ""),
                "rule_count": _safe_int(rules.get("rule_count")),
                "source_phrase_count": len(rules.get("source_phrases") or set()),
            }
        )
    rows.sort(key=lambda row: (row["rule_count"], row["lemma"]))
    return rows


def _store_counts(
    item_rows: Sequence[Mapping[str, Any]], *, active_ids: set[str]
) -> dict[str, int]:
    lifecycle_counts = Counter(str(row.get("lifecycle_state") or "active") for row in item_rows)
    return {
        "pair_items": len(item_rows),
        "active_inventory_items": len(active_ids),
        "active_lifecycle_items": lifecycle_counts.get("active", 0),
        "discarded_items": lifecycle_counts.get("discarded", 0),
        "cleared_items": lifecycle_counts.get("cleared", 0),
        "zero_exposure_items": sum(1 for row in item_rows if _safe_int(row.get("exposures")) == 0),
        "zero_feedback_items": sum(
            1 for row in item_rows if _safe_int(row.get("review_count")) == 0
        ),
    }


def _inventory_file_active_count(payload: Mapping[str, Any] | None, *, pair: str) -> int:
    if not isinstance(payload, Mapping):
        return 0
    pairs = payload.get("pairs")
    if not isinstance(pairs, Mapping):
        return 0
    pair_payload = pairs.get(pair)
    if not isinstance(pair_payload, Mapping):
        return 0
    active_ids = pair_payload.get("active_item_ids")
    return len(active_ids) if isinstance(active_ids, list) else 0


def _ruleset_counts(payload: Mapping[str, Any] | None) -> dict[str, int]:
    if not isinstance(payload, Mapping):
        return {}
    rules = [row for row in payload.get("rules", ()) if isinstance(row, Mapping)]
    lemmas = {str(row.get("replacement") or "").strip() for row in rules if row.get("replacement")}
    return {
        "rule_count": len(rules),
        "enabled_rule_count": sum(1 for row in rules if row.get("enabled") is not False),
        "lemmas_with_rules": len(lemmas),
    }


def _signal_counts(payload: Mapping[str, Any] | None, *, pair: str) -> dict[str, int]:
    if not isinstance(payload, Mapping):
        return {}
    events = [row for row in payload.get("events", ()) if isinstance(row, Mapping)]
    scoped = [row for row in events if str(row.get("pair") or "").strip() == pair]
    return {
        "events": len(events),
        "pair_events": len(scoped),
        "feedback_events": sum(1 for row in scoped if row.get("event_type") == "feedback"),
        "exposure_events": sum(1 for row in scoped if row.get("event_type") == "exposure"),
    }


def _browsing_counts(payload: Mapping[str, Any] | None) -> dict[str, int]:
    if not isinstance(payload, Mapping):
        return {}
    items = payload.get("items")
    return {"aggregate_items": len(items) if isinstance(items, Mapping) else 0}


def _suppression_counts(payload: Mapping[str, Any] | None, *, pair: str) -> dict[str, int]:
    if not isinstance(payload, Mapping):
        return {}
    entries = [row for row in payload.get("entries", ()) if isinstance(row, Mapping)]
    scoped = [row for row in entries if str(row.get("pair") or "").strip() == pair]
    return {"entries": len(entries), "pair_entries": len(scoped)}


def _generic_json_counts(payload: Mapping[str, Any] | None) -> dict[str, int]:
    if not isinstance(payload, Mapping):
        return {}
    counts = {}
    for key, value in payload.items():
        if isinstance(value, list):
            counts[f"{key}_count"] = len(value)
        elif isinstance(value, Mapping):
            counts[f"{key}_count"] = len(value)
    return counts


def _artifact_row(
    artifact_id: str,
    path: Path,
    *,
    counts: Mapping[str, int],
    review_threshold_bytes: int,
) -> dict[str, Any]:
    exists = path.exists()
    byte_count = path.stat().st_size if exists else 0
    status = "missing"
    if exists:
        status = "review_size" if byte_count > review_threshold_bytes else "ok"
    return {
        "id": artifact_id,
        "path": str(path),
        "exists": exists,
        "bytes": byte_count,
        "review_threshold_bytes": int(review_threshold_bytes),
        "status": status,
        "counts": dict(counts),
    }


def _helper_cache_rows() -> list[dict[str, Any]]:
    text = _read_text(EXTENSION_HELPER_CACHE)
    has_prune_or_ttl = bool(re.search(r"\b(MAX_|TTL|expires|prune)", text, flags=re.IGNORECASE))
    status = "bounded" if has_prune_or_ttl else "needs_policy"
    notes = (
        "Helper runtime caches have explicit source-level prune/TTL markers."
        if has_prune_or_ttl
        else "Profile/pair helper cache exists but no explicit prune/TTL source constant was found."
    )
    return [
        {
            "surface": "extension_helper_cache",
            "budget": cache_key,
            "owner": "extension",
            "cap": "",
            "current": "chrome.storage.local",
            "status": status,
            "bounded": has_prune_or_ttl,
            "notes": notes,
        }
        for cache_key in (
            "helperRulesetCache",
            "helperSnapshotCache",
            "helperSemanticInventoryCache",
        )
    ]


def _bounded_row(
    *,
    surface: str,
    budget: str,
    cap: object,
    current: object,
    owner: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "surface": surface,
        "budget": budget,
        "owner": owner,
        "cap": cap if cap is not None else "",
        "current": current if current is not None else "",
        "status": "bounded" if cap not in (None, "") else "needs_policy",
        "bounded": cap not in (None, ""),
        "notes": notes,
    }


def _findings(
    code_budgets: Sequence[Mapping[str, Any]],
    helper_artifacts: Mapping[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    unbounded = [row for row in code_budgets if row.get("bounded") is not True]
    if unbounded:
        findings.append(
            {
                "level": "REVIEW",
                "code": "cache_budget_policy_missing",
                "message": (
                    "One or more cache/storage surfaces do not expose an explicit source-level cap or TTL."
                ),
            }
        )
    if helper_artifacts.get("profile_dir_exists") is not True:
        findings.append(
            {
                "level": "INFO",
                "code": "helper_profile_missing",
                "message": "No helper profile directory was present for this audit scope.",
            }
        )
    stale_count = _safe_int(helper_artifacts.get("stale_active_count"))
    if stale_count > 0:
        findings.append(
            {
                "level": "REVIEW",
                "code": "encounter_starvation_candidates",
                "message": (
                    f"{stale_count} active item(s) have zero exposure and zero feedback in the audited store."
                ),
            }
        )
    large_artifacts = [
        str(row.get("id"))
        for row in _mapping_rows(helper_artifacts.get("artifacts"))
        if row.get("status") == "review_size"
    ]
    if large_artifacts:
        findings.append(
            {
                "level": "REVIEW",
                "code": "helper_artifact_size_review",
                "message": "Large helper artifacts need review: " + ", ".join(large_artifacts),
            }
        )
    if not findings:
        findings.append(
            {
                "level": "PASS",
                "code": "resource_budget_audit_clean",
                "message": "No resource-budget review findings were detected for the audited scope.",
            }
        )
    return findings


def _summary(
    code_budgets: Sequence[Mapping[str, Any]],
    helper_artifacts: Mapping[str, Any],
    findings: Sequence[Mapping[str, str]],
) -> dict[str, int | list[str]]:
    artifacts = _mapping_rows(helper_artifacts.get("artifacts"))
    return {
        "code_budget_row_count": len(code_budgets),
        "bounded_code_row_count": sum(1 for row in code_budgets if row.get("bounded") is True),
        "helper_artifact_row_count": len(artifacts),
        "helper_artifact_total_bytes": sum(_safe_int(row.get("bytes")) for row in artifacts),
        "active_item_count": _safe_int(helper_artifacts.get("active_item_count")),
        "zero_exposure_active_count": _safe_int(helper_artifacts.get("zero_exposure_active_count")),
        "zero_feedback_active_count": _safe_int(helper_artifacts.get("zero_feedback_active_count")),
        "finding_codes": [str(row.get("code")) for row in findings],
    }


def _js_const_int(path: Path, const_name: str) -> int | None:
    match = re.search(rf"\bconst\s+{re.escape(const_name)}\s*=\s*(\d+)", _read_text(path))
    return int(match.group(1)) if match else None


def _settings_default_int(key: str) -> int | None:
    match = re.search(rf"\b{re.escape(key)}:\s*(\d+)", _read_text(EXTENSION_SETTINGS_DEFAULTS))
    return int(match.group(1)) if match else None


def _python_default_int(path: Path, name: str) -> int | None:
    match = re.search(rf"\b{name}\s*:\s*int\s*=\s*(\d+)", _read_text(path))
    return int(match.group(1)) if match else None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _load_json_if_exists(path: Path) -> Mapping[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    return payload if isinstance(payload, Mapping) else None


def _default_data_root() -> Path:
    override = os.environ.get("LEXISHIFT_DATA_DIR")
    if override:
        return Path(override)
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(home / "AppData" / "Roaming")
        return Path(base) / "LexiShift" / "LexiShift"
    return home / ".local" / "share" / "LexiShift" / "LexiShift"


def _safe_profile_id(value: object) -> str:
    raw = str(value or DEFAULT_PROFILE_ID).strip() or DEFAULT_PROFILE_ID
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", raw)
    return normalized or DEFAULT_PROFILE_ID


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item) for item in value]


if __name__ == "__main__":
    raise SystemExit(main())
