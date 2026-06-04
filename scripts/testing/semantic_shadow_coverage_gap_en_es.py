#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLD_PROXY_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_gold_proxy_en_es_latest.json"
)
DEFAULT_INVENTORY_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_en_es_latest.json"
)
DEFAULT_BENCHMARK_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_coverage_gap_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_coverage_gap_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Explain the remaining en-es shadow-coverage gaps by comparing the strict "
            "gold-proxy underblocked rows against current inventory and rulegen benchmark sources."
        )
    )
    parser.add_argument(
        "--gold-proxy-json",
        type=Path,
        default=DEFAULT_GOLD_PROXY_JSON,
        help="Input gold-proxy JSON artifact.",
    )
    parser.add_argument(
        "--inventory-json",
        type=Path,
        default=DEFAULT_INVENTORY_JSON,
        help="Input shadow inventory JSON artifact.",
    )
    parser.add_argument(
        "--benchmark-json",
        type=Path,
        default=DEFAULT_BENCHMARK_JSON,
        help="Input rulegen benchmark JSON artifact.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_MARKDOWN_OUT,
        help="Output Markdown artifact path.",
    )
    return parser.parse_args()


def _normalize_items(values: object) -> list[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    normalized: list[str] = []
    for item in values:
        text = str(item or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _build_inventory_lookup(
    inventory_report: Mapping[str, object],
) -> dict[tuple[str, str], Mapping[str, object]]:
    inventory = inventory_report.get("inventory")
    lookup: dict[tuple[str, str], Mapping[str, object]] = {}
    if not isinstance(inventory, Mapping):
        return lookup
    for target_row in inventory.get("targets", ()):
        if not isinstance(target_row, Mapping):
            continue
        target = str(target_row.get("target") or "").strip()
        if not target:
            continue
        trigger_entries = target_row.get("trigger_entries")
        if not isinstance(trigger_entries, Sequence) or isinstance(trigger_entries, (str, bytes)):
            continue
        for trigger_entry in trigger_entries:
            if not isinstance(trigger_entry, Mapping):
                continue
            trigger = str(trigger_entry.get("trigger") or "").strip()
            if trigger:
                lookup[(target, trigger)] = trigger_entry
    return lookup


def _build_benchmark_case_lookup(
    benchmark_report: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    pair_payload = benchmark_report.get("pairs")
    if not isinstance(pair_payload, Mapping):
        return {}
    en_es = pair_payload.get("en-es")
    if not isinstance(en_es, Mapping):
        return {}
    best_run = en_es.get("best_run")
    if not isinstance(best_run, Mapping):
        return {}
    cases = best_run.get("summary", {}).get("cases")
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)):
        return {}
    lookup: dict[str, Mapping[str, object]] = {}
    for case in cases:
        if not isinstance(case, Mapping):
            continue
        target = str(case.get("target") or "").strip()
        if target:
            lookup[target] = case
    return lookup


def build_coverage_gap_report(
    *,
    gold_proxy_report: Mapping[str, object],
    inventory_report: Mapping[str, object],
    benchmark_report: Mapping[str, object],
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    proxy = gold_proxy_report.get("proxy_evaluation")
    if not isinstance(proxy, Mapping):
        return {
            "schema_version": 1,
            "pair": "en-es",
            "generated_at": generated_at,
            "status": "gold_proxy_unavailable",
            "rows": [],
        }
    policies = proxy.get("policies")
    if not isinstance(policies, Mapping):
        return {
            "schema_version": 1,
            "pair": "en-es",
            "generated_at": generated_at,
            "status": "gold_proxy_unavailable",
            "rows": [],
        }
    strict = policies.get("cross_checked_v1")
    if not isinstance(strict, Mapping):
        return {
            "schema_version": 1,
            "pair": "en-es",
            "generated_at": generated_at,
            "status": "gold_proxy_unavailable",
            "rows": [],
        }
    underblocked = strict.get("sample_underblocked_rows")
    if not isinstance(underblocked, Sequence) or isinstance(underblocked, (str, bytes)):
        underblocked = ()

    inventory_lookup = _build_inventory_lookup(inventory_report)
    benchmark_lookup = _build_benchmark_case_lookup(benchmark_report)
    rows: list[dict[str, object]] = []

    for row in underblocked:
        if not isinstance(row, Mapping):
            continue
        target = str(row.get("target") or "").strip()
        trigger = str(row.get("trigger") or "").strip()
        gold_shadow_targets = _normalize_items(row.get("gold_shadow_targets"))
        trigger_entry = inventory_lookup.get((target, trigger), {})
        active_candidates = (
            trigger_entry.get("active_candidates") if isinstance(trigger_entry, Mapping) else ()
        )
        active_support = bool(active_candidates)
        active_summary = "none"
        if (
            isinstance(active_candidates, Sequence)
            and not isinstance(active_candidates, (str, bytes))
            and active_candidates
        ):
            first = active_candidates[0]
            if isinstance(first, Mapping):
                label = str(first.get("sense_label") or "").strip()
                pos = str(first.get("canonical_pos") or "").strip() or "unknown"
                active_summary = f"{pos}: {label}" if label else pos
        for shadow_target in gold_shadow_targets:
            benchmark_case = benchmark_lookup.get(shadow_target, {})
            shadow_sources = _normalize_items(benchmark_case.get("all_sources"))
            shadow_expected = _normalize_items(benchmark_case.get("expected_any"))
            classification = "semantic_bridge_needed"
            if trigger in shadow_sources:
                classification = "rulegen_source_gap"
            elif trigger in shadow_expected:
                classification = "reviewed_trigger_only"
            rows.append(
                {
                    "target": target,
                    "trigger": trigger,
                    "shadow_target": shadow_target,
                    "active_support": active_support,
                    "active_summary": active_summary,
                    "shadow_rulegen_sources": shadow_sources,
                    "shadow_reviewed_expected": shadow_expected,
                    "classification": classification,
                }
            )

    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "rows": rows,
        "summary": {
            "remaining_gap_count": len(rows),
            "semantic_bridge_needed_count": sum(
                1 for row in rows if row["classification"] == "semantic_bridge_needed"
            ),
            "rulegen_source_gap_count": sum(
                1 for row in rows if row["classification"] == "rulegen_source_gap"
            ),
            "reviewed_trigger_only_count": sum(
                1 for row in rows if row["classification"] == "reviewed_trigger_only"
            ),
        },
    }


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Coverage Gap Audit",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
    ]
    summary = report.get("summary")
    if isinstance(summary, Mapping):
        lines.extend(
            [
                f"- Remaining gaps: `{summary.get('remaining_gap_count', 0)}`",
                f"- `semantic_bridge_needed`: `{summary.get('semantic_bridge_needed_count', 0)}`",
                f"- `rulegen_source_gap`: `{summary.get('rulegen_source_gap_count', 0)}`",
                f"- `reviewed_trigger_only`: `{summary.get('reviewed_trigger_only_count', 0)}`",
            ]
        )
    rows = report.get("rows")
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) and rows:
        lines.extend(
            [
                "",
                "## Rows",
                "| Target | Trigger | Shadow | Active Support | Classification | Rulegen Sources | Reviewed Expected |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                f"| `{row.get('target', '')}` | `{row.get('trigger', '')}` | `{row.get('shadow_target', '')}` | `{row.get('active_summary', '')}` | `{row.get('classification', '')}` | `{', '.join(_normalize_items(row.get('shadow_rulegen_sources'))[:8])}` | `{', '.join(_normalize_items(row.get('shadow_reviewed_expected'))[:8])}` |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    gold_proxy_report = json.loads(args.gold_proxy_json.read_text(encoding="utf-8"))
    inventory_report = json.loads(args.inventory_json.read_text(encoding="utf-8"))
    benchmark_report = json.loads(args.benchmark_json.read_text(encoding="utf-8"))
    report = build_coverage_gap_report(
        gold_proxy_report=gold_proxy_report,
        inventory_report=inventory_report,
        benchmark_report=benchmark_report,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
