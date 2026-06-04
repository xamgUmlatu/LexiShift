#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.rulegen.semantic_shadow_evaluation import (  # noqa: E402
    REFERENCE_SHADOW_POLICY_MODES,
    evaluate_shadow_inventory_against_benchmark_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    SHADOW_PROMOTION_POLICIES,
    build_benchmark_shadow_targets,
)
from rulegen_benchmark_dataset import load_benchmark_dataset_payload  # noqa: E402


DEFAULT_BENCHMARK_DATASET = (
    PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases" / "en_es.json"
)
DEFAULT_INVENTORY_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_gold_proxy_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_gold_proxy_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Grade en-es auto-mined shadow policies against a reviewed-trigger overlap gold proxy "
            "derived from the rulegen benchmark cases."
        )
    )
    parser.add_argument(
        "--benchmark-dataset",
        type=Path,
        default=DEFAULT_BENCHMARK_DATASET,
        help="Input rulegen benchmark dataset.",
    )
    parser.add_argument(
        "--inventory-json",
        type=Path,
        default=DEFAULT_INVENTORY_JSON,
        help="Input semantic shadow inventory JSON artifact.",
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


def _collect_cases(dataset_payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_cases = dataset_payload.get("cases")
    if not isinstance(raw_cases, Sequence) or isinstance(raw_cases, (str, bytes)):
        raise ValueError("Benchmark dataset is missing a `cases` list.")
    return [dict(case) for case in raw_cases if isinstance(case, Mapping)]


def build_shadow_gold_proxy_report(
    *,
    dataset_payload: Mapping[str, object],
    inventory_report: Mapping[str, object],
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    benchmark_targets = build_benchmark_shadow_targets(_collect_cases(dataset_payload))
    inventory = inventory_report.get("inventory")
    if not isinstance(inventory, Mapping):
        return {
            "schema_version": 1,
            "pair": "en-es",
            "generated_at": generated_at,
            "status": "inventory_unavailable",
            "benchmark_dataset": {
                "path": str(dataset_payload.get("source_files", [DEFAULT_BENCHMARK_DATASET])[0]),
                "target_count": len(benchmark_targets),
            },
            "inventory_status": str(inventory_report.get("status") or "unknown"),
            "proxy_evaluation": None,
        }

    proxy_evaluation = evaluate_shadow_inventory_against_benchmark_overlap_gold(
        inventory=inventory,
        benchmark_targets=benchmark_targets,
        policies=SHADOW_PROMOTION_POLICIES + REFERENCE_SHADOW_POLICY_MODES,
    )
    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "benchmark_dataset": {
            "path": str(dataset_payload.get("source_files", [DEFAULT_BENCHMARK_DATASET])[0]),
            "target_count": len(benchmark_targets),
            "reviewed_trigger_count": sum(
                len(target.reviewed_triggers) for target in benchmark_targets
            ),
        },
        "inventory_status": str(inventory_report.get("status") or "unknown"),
        "inventory_promotion_policy": str(inventory.get("promotion_policy") or ""),
        "proxy_evaluation": proxy_evaluation,
    }


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Gold-Proxy Evaluation",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Inventory status: `{report.get('inventory_status', 'unknown')}`",
        (
            "- Proxy meaning: reviewed trigger overlaps in the rulegen benchmark act as the "
            "current lower-bound gold for which targets should compete for the same English trigger."
        ),
        (
            "- Blind spot: this proxy will under-credit real semantic blockers when the competing "
            "benchmark target does not explicitly list the same English trigger, so rows like "
            "`marco / frame -> cuadro` can appear as overblocking here even though they are useful "
            "runtime shadows."
        ),
    ]
    benchmark_dataset = report.get("benchmark_dataset")
    if isinstance(benchmark_dataset, Mapping):
        lines.extend(
            [
                f"- Benchmark targets: `{benchmark_dataset.get('target_count', 0)}`",
                f"- Reviewed triggers: `{benchmark_dataset.get('reviewed_trigger_count', 0)}`",
            ]
        )
    proxy_evaluation = report.get("proxy_evaluation")
    if not isinstance(proxy_evaluation, Mapping):
        return "\n".join(lines) + "\n"

    candidate_pool = proxy_evaluation.get("candidate_pool_summary")
    if isinstance(candidate_pool, Mapping):
        lines.extend(
            [
                "",
                "## Candidate Pool",
                f"- Gold trigger rows: `{candidate_pool.get('gold_trigger_rows', 0)}`",
                f"- Gold rows with active support: `{candidate_pool.get('gold_trigger_rows_with_active_candidates', 0)}` (`{_render_rate(candidate_pool.get('gold_trigger_active_support_rate'))}`)",
                f"- Gold rows with mined overlap: `{candidate_pool.get('gold_trigger_rows_with_mined_overlap', 0)}` (`{_render_rate(candidate_pool.get('candidate_pool_trigger_recall'))}`)",
                f"- Gold rows with exact mined set: `{candidate_pool.get('gold_trigger_rows_with_exact_mined_set', 0)}` (`{_render_rate(candidate_pool.get('candidate_pool_exact_match_rate'))}`)",
            ]
        )

    policies = proxy_evaluation.get("policies")
    if not isinstance(policies, Mapping):
        return "\n".join(lines) + "\n"

    for policy in SHADOW_PROMOTION_POLICIES + REFERENCE_SHADOW_POLICY_MODES:
        payload = policies.get(policy)
        if not isinstance(payload, Mapping):
            continue
        summary = payload.get("summary")
        if not isinstance(summary, Mapping):
            continue
        lines.extend(
            [
                "",
                f"## {policy}",
                f"- Candidate precision: `{_render_rate(summary.get('candidate_precision'))}`",
                f"- Candidate recall: `{_render_rate(summary.get('candidate_recall'))}`",
                f"- Candidate F1: `{_render_rate(summary.get('candidate_f1'))}`",
                f"- Gold trigger hit rate: `{_render_rate(summary.get('gold_trigger_hit_rate'))}`",
                f"- Top-1 gold trigger hit rate: `{_render_rate(summary.get('top1_gold_trigger_hit_rate'))}`",
                f"- Gold trigger exact-match rate: `{_render_rate(summary.get('gold_trigger_exact_match_rate'))}`",
                f"- Underblocking rows: `{summary.get('gold_trigger_rows_underblocked', 0)}`",
                f"- Overblocking rows: `{summary.get('no_gold_trigger_rows_overblocked', 0)}`",
            ]
        )
        underblocked = payload.get("sample_underblocked_rows")
        if (
            isinstance(underblocked, Sequence)
            and not isinstance(underblocked, (str, bytes))
            and underblocked
        ):
            lines.append("- Sample underblocked rows:")
            for row in underblocked[:5]:
                if not isinstance(row, Mapping):
                    continue
                lines.append(
                    f"  - `{row.get('target', '')}` / `{row.get('trigger', '')}` gold={row.get('gold_shadow_targets', [])} promoted={row.get('promoted_targets', [])}"
                )
        overblocked = payload.get("sample_overblocked_rows")
        if (
            isinstance(overblocked, Sequence)
            and not isinstance(overblocked, (str, bytes))
            and overblocked
        ):
            lines.append("- Sample overblocked rows:")
            for row in overblocked[:5]:
                if not isinstance(row, Mapping):
                    continue
                lines.append(
                    f"  - `{row.get('target', '')}` / `{row.get('trigger', '')}` promoted={row.get('promoted_targets', [])}"
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    dataset_payload = load_benchmark_dataset_payload(args.benchmark_dataset)
    inventory_report = json.loads(args.inventory_json.read_text(encoding="utf-8"))
    report = build_shadow_gold_proxy_report(
        dataset_payload=dataset_payload,
        inventory_report=inventory_report,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
