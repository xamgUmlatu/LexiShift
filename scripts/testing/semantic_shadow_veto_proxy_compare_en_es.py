#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from lexishift_core.rulegen.semantic_shadow_evaluation import (  # noqa: E402
    evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    build_benchmark_shadow_targets,
)
from semantic_shadow_seed_compare_en_es import (  # noqa: E402
    DEFAULT_BENCHMARK_JSON,
    DEFAULT_DATASET_PATH,
    build_seed_compare_report,
    load_benchmark_dataset_payload,
)

DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_veto_proxy_compare_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_veto_proxy_compare_en_es_latest.md"
)

DEFAULT_SHADOW_SOURCES = (
    {
        "source_id": "curated_shadows",
        "label": "Curated overlap oracle",
        "seed_mode": "benchmark_reviewed",
        "policy": "gold_overlap_oracle",
    },
    {
        "source_id": "reviewed_auto_shadows",
        "label": "Reviewed-trigger auto shadows",
        "seed_mode": "benchmark_reviewed",
        "policy": "support_score_v1",
        "support_score_min": 5.0,
        "support_score_max_promoted": 1,
    },
    {
        "source_id": "auto_shadows",
        "label": "Source-only auto shadows",
        "seed_mode": "rulegen_top3_plus_forward_gloss",
        "policy": "support_score_v1",
        "support_score_min": 5.0,
        "support_score_max_promoted": 2,
    },
    {
        "source_id": "no_shadows",
        "label": "No shadow veto",
        "seed_mode": "rulegen_top3_plus_forward_gloss",
        "policy": "none",
    },
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare lower-bound veto behavior for curated shadows versus auto-mined "
            "shadow sources on the en-es reviewed overlap gold."
        )
    )
    parser.add_argument(
        "--benchmark-dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Reviewed rulegen benchmark dataset JSON.",
    )
    parser.add_argument(
        "--benchmark-json",
        type=Path,
        default=DEFAULT_BENCHMARK_JSON,
        help="Rulegen benchmark report JSON containing best_run case_results.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(resolve_data_root()),
        help="LexiShift data root (default: helper resolve_data_root()).",
    )
    parser.add_argument(
        "--translation-dict",
        type=Path,
        default=None,
        help="Optional explicit forward translation pack path for en-es.",
    )
    parser.add_argument(
        "--reverse-translation-dict",
        type=Path,
        default=None,
        help="Optional explicit reverse translation pack path for en-es.",
    )
    parser.add_argument(
        "--forward-seed-max-words",
        type=int,
        default=1,
        help="Maximum word count for forward-gloss-derived trigger seeds.",
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


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _delta(value: object, baseline: object) -> float | None:
    if not isinstance(value, (float, int)) or not isinstance(baseline, (float, int)):
        return None
    return float(value) - float(baseline)


def build_veto_proxy_compare_report(
    *,
    benchmark_dataset: Path,
    benchmark_json: Path,
    data_root: Path,
    translation_dict: Path | None,
    reverse_translation_dict: Path | None,
    forward_seed_max_words: int,
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    dataset_payload = load_benchmark_dataset_payload(benchmark_dataset)
    benchmark_targets = build_benchmark_shadow_targets(_collect_cases(dataset_payload))
    benchmark_report = json.loads(benchmark_json.read_text(encoding="utf-8"))
    helper_paths = build_helper_paths(Path(data_root))
    forward_pack, reverse_pack = resolve_pair_translation_packs(
        helper_paths,
        pair="en-es",
        translation_dict_path=translation_dict,
        reverse_translation_dict_path=reverse_translation_dict,
    )
    seed_compare_report = build_seed_compare_report(
        dataset_payload=dataset_payload,
        benchmark_report=benchmark_report,
        data_root=Path(data_root),
        forward_pack=forward_pack,
        reverse_pack=reverse_pack,
        forward_seed_max_words=forward_seed_max_words,
    )
    seed_modes = seed_compare_report.get("seed_modes")
    if not isinstance(seed_modes, Mapping):
        return {
            "schema_version": 1,
            "pair": "en-es",
            "generated_at": generated_at,
            "status": "seed_modes_unavailable",
            "rows": [],
        }

    rows: list[dict[str, object]] = []
    for source in DEFAULT_SHADOW_SOURCES:
        seed_mode = str(source.get("seed_mode") or "")
        seed_payload = seed_modes.get(seed_mode)
        if not isinstance(seed_payload, Mapping):
            continue
        inventory = seed_payload.get("inventory")
        if not isinstance(inventory, Mapping):
            continue
        policy = str(source.get("policy") or "")
        veto_report = evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            policies=(policy,),
            support_score_min=float(source.get("support_score_min") or 0.0),
            support_score_max_promoted=int(source.get("support_score_max_promoted") or 1),
        )
        policy_payload = veto_report.get("policies", {}).get(policy, {})
        summary = policy_payload.get("summary") if isinstance(policy_payload, Mapping) else {}
        candidate_pool = (
            veto_report.get("candidate_pool_summary")
            if isinstance(veto_report.get("candidate_pool_summary"), Mapping)
            else {}
        )
        rows.append(
            {
                "source_id": str(source.get("source_id") or ""),
                "label": str(source.get("label") or ""),
                "seed_mode": seed_mode,
                "policy": policy,
                "support_score_min": source.get("support_score_min"),
                "support_score_max_promoted": source.get("support_score_max_promoted"),
                "inventory_entry_coverage_rate": candidate_pool.get(
                    "inventory_entry_coverage_rate"
                ),
                "gold_trigger_inventory_coverage_rate": candidate_pool.get(
                    "gold_trigger_inventory_coverage_rate"
                ),
                "gold_trigger_active_support_rate": candidate_pool.get(
                    "gold_trigger_active_support_rate"
                ),
                "overall_accuracy": summary.get("overall_accuracy"),
                "abstain_recall": summary.get("abstain_recall"),
                "harmful_allow_rate": summary.get("harmful_allow_rate"),
                "allow_precision": summary.get("allow_precision"),
                "overblocking_rate": summary.get("overblocking_rate"),
                "abstain_rate": summary.get("abstain_rate"),
                "allow_rate": summary.get("allow_rate"),
                "ambiguous_trigger_rows": summary.get("ambiguous_trigger_rows"),
                "clear_trigger_rows": summary.get("clear_trigger_rows"),
                "true_abstain_count": summary.get("true_abstain_count"),
                "harmful_allow_count": summary.get("harmful_allow_count"),
                "true_allow_count": summary.get("true_allow_count"),
                "false_abstain_count": summary.get("false_abstain_count"),
                "sample_harmful_allow_rows": policy_payload.get("sample_harmful_allow_rows", []),
                "sample_false_abstain_rows": policy_payload.get("sample_false_abstain_rows", []),
            }
        )

    curated_row = next((row for row in rows if row.get("source_id") == "curated_shadows"), None)
    if isinstance(curated_row, Mapping):
        for row in rows:
            row["delta_vs_curated_overall_accuracy"] = _delta(
                row.get("overall_accuracy"), curated_row.get("overall_accuracy")
            )
            row["delta_vs_curated_abstain_recall"] = _delta(
                row.get("abstain_recall"), curated_row.get("abstain_recall")
            )
            row["delta_vs_curated_harmful_allow_rate"] = _delta(
                row.get("harmful_allow_rate"), curated_row.get("harmful_allow_rate")
            )
            row["delta_vs_curated_overblocking_rate"] = _delta(
                row.get("overblocking_rate"), curated_row.get("overblocking_rate")
            )

    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": str(seed_compare_report.get("status") or "unknown"),
        "comparison_kind": "lower_bound_veto_proxy",
        "gold_reference": seed_compare_report.get("gold_reference", {}),
        "benchmark_report": {
            "path": str(benchmark_json),
        },
        "forward_seed_max_words": int(forward_seed_max_words),
        "rows": rows,
    }


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Veto Proxy Comparison",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        "- Comparison meaning: use the reviewed trigger-overlap gold as a lower-bound veto proxy.",
        "- Decision rule: if a shadow source emits any blockers for an ambiguous trigger row, count that row as `abstain`; otherwise count it as `allow`.",
        "- Limitation: this is not the sentence-level cosine veto benchmark. It measures whether a shadow source carries enough blocker structure to support abstention on the reviewed ambiguity families.",
    ]
    rows = report.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "",
            "## Summary",
            "| Shadow Source | Seed Mode | Accuracy | Abstain Recall | Harmful Allow | Allow Precision | Overblocking |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("source_id", "")),
                    str(row.get("seed_mode", "")),
                    _render_rate(row.get("overall_accuracy")),
                    _render_rate(row.get("abstain_recall")),
                    _render_rate(row.get("harmful_allow_rate")),
                    _render_rate(row.get("allow_precision")),
                    _render_rate(row.get("overblocking_rate")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Details"])
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        lines.extend(
            [
                "",
                f"### {row.get('source_id', '')}",
                f"- Label: `{row.get('label', '')}`",
                f"- Seed mode: `{row.get('seed_mode', '')}`",
                f"- Policy: `{row.get('policy', '')}`",
                f"- Overall accuracy: `{_render_rate(row.get('overall_accuracy'))}`",
                f"- Abstain recall on ambiguous rows: `{_render_rate(row.get('abstain_recall'))}`",
                f"- Harmful allow rate: `{_render_rate(row.get('harmful_allow_rate'))}`",
                f"- Allow precision: `{_render_rate(row.get('allow_precision'))}`",
                f"- Overblocking rate: `{_render_rate(row.get('overblocking_rate'))}`",
            ]
        )
        if row.get("source_id") != "curated_shadows":
            lines.extend(
                [
                    f"- Delta vs curated accuracy: `{_render_rate(row.get('delta_vs_curated_overall_accuracy'))}`",
                    f"- Delta vs curated abstain recall: `{_render_rate(row.get('delta_vs_curated_abstain_recall'))}`",
                    f"- Delta vs curated harmful allow: `{_render_rate(row.get('delta_vs_curated_harmful_allow_rate'))}`",
                    f"- Delta vs curated overblocking: `{_render_rate(row.get('delta_vs_curated_overblocking_rate'))}`",
                ]
            )
        harmful_rows = row.get("sample_harmful_allow_rows")
        if (
            isinstance(harmful_rows, Sequence)
            and not isinstance(harmful_rows, (str, bytes))
            and harmful_rows
        ):
            lines.append("- Sample harmful-allow rows:")
            for sample in harmful_rows[:5]:
                if not isinstance(sample, Mapping):
                    continue
                lines.append(
                    f"  - `{sample.get('target', '')}` / `{sample.get('trigger', '')}` gold={sample.get('gold_shadow_targets', [])} promoted={sample.get('promoted_targets', [])}"
                )
        false_abstain_rows = row.get("sample_false_abstain_rows")
        if (
            isinstance(false_abstain_rows, Sequence)
            and not isinstance(false_abstain_rows, (str, bytes))
            and false_abstain_rows
        ):
            lines.append("- Sample false-abstain rows:")
            for sample in false_abstain_rows[:5]:
                if not isinstance(sample, Mapping):
                    continue
                lines.append(
                    f"  - `{sample.get('target', '')}` / `{sample.get('trigger', '')}` promoted={sample.get('promoted_targets', [])}"
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    report = build_veto_proxy_compare_report(
        benchmark_dataset=args.benchmark_dataset,
        benchmark_json=args.benchmark_json,
        data_root=Path(args.data_root),
        translation_dict=args.translation_dict,
        reverse_translation_dict=args.reverse_translation_dict,
        forward_seed_max_words=max(1, int(args.forward_seed_max_words)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
