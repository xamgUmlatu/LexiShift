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

from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.resources.dict_loaders import load_translation_gloss_records_ordered  # noqa: E402
from lexishift_core.rulegen.semantic_shadow_evaluation import (  # noqa: E402
    evaluate_shadow_inventory_against_benchmark_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    build_benchmark_shadow_targets,
    build_en_es_shadow_inventory,
    build_rulegen_shadow_targets,
    filter_shadow_targets_by_trigger_support,
    subtract_shadow_target_triggers,
    augment_shadow_targets_with_forward_gloss_triggers,
)
from rulegen_benchmark_dataset import load_benchmark_dataset_payload  # noqa: E402


DEFAULT_DATASET_PATH = (
    PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases" / "en_es.json"
)
DEFAULT_BENCHMARK_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_shadow_trigger_support_sweep_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_trigger_support_sweep_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep the en-es trigger-support score threshold before shadow mining, "
            "then score the filtered seeds under the fixed support-score blocker policy."
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
        "--mode-ids",
        default="rulegen_top3_plus_forward_gloss,rulegen_all_plus_forward_gloss",
        help="Comma-separated seed modes to evaluate.",
    )
    parser.add_argument(
        "--trigger-support-score-values",
        default="2,3,4,5,6",
        help="Comma-separated threshold values for trigger support filtering.",
    )
    parser.add_argument(
        "--shadow-support-score-min",
        type=float,
        default=4.0,
        help="Fixed shadow support-score threshold to use after trigger filtering.",
    )
    parser.add_argument(
        "--shadow-max-promoted",
        type=int,
        default=2,
        help="Fixed maximum number of promoted shadows after trigger filtering.",
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


def _parse_int_csv(value: str) -> list[int]:
    parsed: list[int] = []
    for raw_item in str(value or "").split(","):
        text = raw_item.strip()
        if not text:
            continue
        parsed.append(max(1, int(text)))
    if not parsed:
        raise ValueError("At least one integer value is required.")
    return parsed


def _parse_mode_ids(value: str) -> list[str]:
    parsed = [item.strip() for item in str(value or "").split(",") if item.strip()]
    if not parsed:
        raise ValueError("At least one mode id is required.")
    return parsed


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _safe_f1(precision: object, recall: object) -> float | None:
    if not isinstance(precision, (float, int)) or not isinstance(recall, (float, int)):
        return None
    precision_value = float(precision)
    recall_value = float(recall)
    if (precision_value + recall_value) <= 0:
        return None
    return 2 * precision_value * recall_value / (precision_value + recall_value)


def _collect_cases(dataset_payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_cases = dataset_payload.get("cases")
    if not isinstance(raw_cases, Sequence) or isinstance(raw_cases, (str, bytes)):
        raise ValueError("Benchmark dataset is missing a `cases` list.")
    return [dict(case) for case in raw_cases if isinstance(case, Mapping)]


def _load_best_run_case_results(
    benchmark_report: Mapping[str, object],
) -> list[Mapping[str, object]]:
    pairs = benchmark_report.get("pairs")
    if not isinstance(pairs, Mapping):
        raise ValueError("Benchmark report is missing `pairs`.")
    en_es = pairs.get("en-es")
    if not isinstance(en_es, Mapping):
        raise ValueError("Benchmark report is missing `pairs.en-es`.")
    best_run = en_es.get("best_run")
    if not isinstance(best_run, Mapping):
        raise ValueError("Benchmark report is missing `pairs.en-es.best_run`.")
    case_results = best_run.get("case_results")
    if not isinstance(case_results, Sequence) or isinstance(case_results, (str, bytes)):
        raise ValueError("Benchmark report best_run is missing `case_results`.")
    return [dict(case) for case in case_results if isinstance(case, Mapping)]


def _build_source_mode_payloads(
    *,
    gold_targets,
    best_run_case_results: Sequence[Mapping[str, object]],
    forward_records_by_target,
    reverse_records_by_source,
    forward_provider: str,
    reverse_provider: str,
    forward_seed_max_words: int,
):
    target_filter = [target.target for target in gold_targets]
    rulegen_top3_targets = build_rulegen_shadow_targets(
        best_run_case_results,
        targets=target_filter,
        source_field="top3_sources",
    )
    rulegen_all_targets = build_rulegen_shadow_targets(
        best_run_case_results,
        targets=target_filter,
        source_field="all_sources",
    )
    top3_augmented = augment_shadow_targets_with_forward_gloss_triggers(
        rulegen_top3_targets,
        forward_records_by_target=forward_records_by_target,
        max_words=forward_seed_max_words,
    )
    all_augmented = augment_shadow_targets_with_forward_gloss_triggers(
        rulegen_all_targets,
        forward_records_by_target=forward_records_by_target,
        max_words=forward_seed_max_words,
    )
    top3_forward_only = subtract_shadow_target_triggers(
        top3_augmented,
        rulegen_top3_targets,
        tier_label="forward_gloss_fragments",
    )
    all_forward_only = subtract_shadow_target_triggers(
        all_augmented,
        rulegen_all_targets,
        tier_label="forward_gloss_fragments",
    )
    return {
        "rulegen_top3_plus_forward_gloss": {
            "seed_targets": top3_augmented,
            "source_targets_by_label": {
                "rulegen_top3_sources": rulegen_top3_targets,
                "forward_gloss_fragments": top3_forward_only,
            },
        },
        "rulegen_all_plus_forward_gloss": {
            "seed_targets": all_augmented,
            "source_targets_by_label": {
                "rulegen_all_sources": rulegen_all_targets,
                "forward_gloss_fragments": all_forward_only,
            },
        },
    }


def _evaluate_seed_targets(
    *,
    seed_targets,
    gold_targets,
    forward_records_by_target,
    reverse_records_by_source,
    forward_provider: str,
    reverse_provider: str,
    shadow_support_score_min: float,
    shadow_max_promoted: int,
) -> dict[str, object]:
    inventory = build_en_es_shadow_inventory(
        benchmark_targets=seed_targets,
        forward_records_by_target=forward_records_by_target,
        reverse_records_by_source=reverse_records_by_source,
        forward_provider=forward_provider,
        reverse_provider=reverse_provider,
    )
    evaluation = evaluate_shadow_inventory_against_benchmark_overlap_gold(
        inventory=inventory,
        benchmark_targets=gold_targets,
        policies=("support_score_v1",),
        support_score_min=shadow_support_score_min,
        support_score_max_promoted=shadow_max_promoted,
    )
    summary = {}
    policies = evaluation.get("policies")
    if isinstance(policies, Mapping):
        support_score = policies.get("support_score_v1")
        if isinstance(support_score, Mapping):
            candidate_summary = support_score.get("summary")
            if isinstance(candidate_summary, Mapping):
                summary = dict(candidate_summary)
    candidate_pool = evaluation.get("candidate_pool_summary")
    return {
        "inventory": inventory,
        "evaluation": evaluation,
        "summary": summary,
        "candidate_pool_summary": candidate_pool if isinstance(candidate_pool, Mapping) else {},
    }


def build_trigger_support_sweep_report(
    *,
    benchmark_dataset: Path,
    benchmark_json: Path,
    data_root: Path,
    translation_dict: Path | None,
    reverse_translation_dict: Path | None,
    forward_seed_max_words: int,
    mode_ids: Sequence[str],
    trigger_support_score_values: Sequence[int],
    shadow_support_score_min: float,
    shadow_max_promoted: int,
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    dataset_payload = load_benchmark_dataset_payload(benchmark_dataset)
    benchmark_report = json.loads(benchmark_json.read_text(encoding="utf-8"))
    gold_targets = build_benchmark_shadow_targets(_collect_cases(dataset_payload))
    benchmark_target_map = {target.target: target for target in gold_targets}
    best_run_case_results = _load_best_run_case_results(benchmark_report)
    helper_paths = build_helper_paths(Path(data_root))
    forward_pack, reverse_pack = resolve_pair_translation_packs(
        helper_paths,
        pair="en-es",
        translation_dict_path=translation_dict,
        reverse_translation_dict_path=reverse_translation_dict,
    )
    all_targets = sorted(
        {target.target for target in gold_targets if str(target.target or "").strip()}
    )
    forward_records_by_target = load_translation_gloss_records_ordered(
        forward_pack.path,
        target_lang="en",
        headwords=all_targets,
    )
    source_mode_payloads = _build_source_mode_payloads(
        gold_targets=gold_targets,
        best_run_case_results=best_run_case_results,
        forward_records_by_target=forward_records_by_target,
        reverse_records_by_source={},
        forward_provider=forward_pack.provider,
        reverse_provider=reverse_pack.provider,
        forward_seed_max_words=forward_seed_max_words,
    )
    all_triggers = sorted(
        {
            trigger
            for mode_payload in source_mode_payloads.values()
            for target in mode_payload["seed_targets"]
            for trigger in target.reviewed_triggers
            if str(trigger or "").strip()
        }
    )
    reverse_records_by_source = load_translation_gloss_records_ordered(
        reverse_pack.path,
        target_lang="es",
        headwords=all_triggers,
    )
    rows: list[dict[str, object]] = []
    best_rows_by_mode: dict[str, dict[str, object]] = {}
    for mode_id in mode_ids:
        mode_payload = source_mode_payloads.get(mode_id)
        if not isinstance(mode_payload, Mapping):
            continue
        seed_targets = mode_payload["seed_targets"]
        source_targets_by_label = mode_payload["source_targets_by_label"]
        baseline = _evaluate_seed_targets(
            seed_targets=seed_targets,
            gold_targets=gold_targets,
            forward_records_by_target=forward_records_by_target,
            reverse_records_by_source=reverse_records_by_source,
            forward_provider=forward_pack.provider,
            reverse_provider=reverse_pack.provider,
            shadow_support_score_min=shadow_support_score_min,
            shadow_max_promoted=shadow_max_promoted,
        )
        baseline_summary = baseline["summary"]
        baseline_candidate_pool = baseline["candidate_pool_summary"]
        for min_score in trigger_support_score_values:
            filtered_targets, support_rows = filter_shadow_targets_by_trigger_support(
                seed_targets=seed_targets,
                source_targets_by_label=source_targets_by_label,
                forward_records_by_target=forward_records_by_target,
                reverse_records_by_source=reverse_records_by_source,
                forward_provider=forward_pack.provider,
                reverse_provider=reverse_pack.provider,
                benchmark_target_map=benchmark_target_map,
                min_score=float(min_score),
            )
            filtered_seed_trigger_count = sum(
                len(target.reviewed_triggers) for target in filtered_targets
            )
            support_row_count = len(support_rows)
            kept_row_count = sum(
                1
                for row in support_rows
                if float(row.get("trigger_support_score") or 0.0) >= float(min_score)
            )
            filtered_eval = _evaluate_seed_targets(
                seed_targets=filtered_targets,
                gold_targets=gold_targets,
                forward_records_by_target=forward_records_by_target,
                reverse_records_by_source=reverse_records_by_source,
                forward_provider=forward_pack.provider,
                reverse_provider=reverse_pack.provider,
                shadow_support_score_min=shadow_support_score_min,
                shadow_max_promoted=shadow_max_promoted,
            )
            summary = filtered_eval["summary"]
            candidate_pool = filtered_eval["candidate_pool_summary"]
            rows.append(
                {
                    "mode_id": mode_id,
                    "trigger_support_score_min": float(min_score),
                    "seed_trigger_count_before": sum(
                        len(target.reviewed_triggers) for target in seed_targets
                    ),
                    "seed_trigger_count_after": filtered_seed_trigger_count,
                    "trigger_keep_rate": (
                        kept_row_count / support_row_count if support_row_count > 0 else None
                    ),
                    "candidate_precision": summary.get("candidate_precision"),
                    "candidate_recall": summary.get("candidate_recall"),
                    "candidate_f1": _safe_f1(
                        summary.get("candidate_precision"),
                        summary.get("candidate_recall"),
                    ),
                    "gold_trigger_hit_rate": summary.get("gold_trigger_hit_rate"),
                    "overblocking_rate": summary.get("overblocking_rate"),
                    "gold_trigger_inventory_coverage_rate": candidate_pool.get(
                        "gold_trigger_inventory_coverage_rate"
                    ),
                    "candidate_pool_trigger_recall": candidate_pool.get(
                        "candidate_pool_trigger_recall"
                    ),
                    "baseline_precision": baseline_summary.get("candidate_precision"),
                    "baseline_recall": baseline_summary.get("candidate_recall"),
                    "baseline_f1": _safe_f1(
                        baseline_summary.get("candidate_precision"),
                        baseline_summary.get("candidate_recall"),
                    ),
                    "baseline_overblocking": baseline_summary.get("overblocking_rate"),
                    "baseline_trigger_keep_rate": 1.0,
                    "baseline_gold_trigger_inventory_coverage_rate": baseline_candidate_pool.get(
                        "gold_trigger_inventory_coverage_rate"
                    ),
                    "support_row_examples": [
                        row
                        for row in support_rows
                        if float(row.get("trigger_support_score") or 0.0) < float(min_score)
                    ][:5],
                }
            )
        mode_rows = [row for row in rows if row["mode_id"] == mode_id]
        if mode_rows:
            best_rows_by_mode[mode_id] = sorted(
                mode_rows,
                key=lambda row: (
                    -float(row.get("candidate_f1") or 0.0),
                    -float(row.get("candidate_recall") or 0.0),
                    -float(row.get("candidate_precision") or 0.0),
                    float(row.get("overblocking_rate") or 1.0),
                    -float(row.get("trigger_keep_rate") or 0.0),
                    float(row.get("trigger_support_score_min") or 0.0),
                ),
            )[0]
    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "forward_seed_max_words": int(forward_seed_max_words),
        "shadow_support_score_min": float(shadow_support_score_min),
        "shadow_max_promoted": int(shadow_max_promoted),
        "mode_ids": list(mode_ids),
        "trigger_support_score_values": [int(value) for value in trigger_support_score_values],
        "rows": rows,
        "best_rows_by_mode": best_rows_by_mode,
    }


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Trigger Support Sweep",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Forward seed max words: `{report.get('forward_seed_max_words', '')}`",
        f"- Fixed shadow support score: `min={report.get('shadow_support_score_min', '')}`, `max_promoted={report.get('shadow_max_promoted', '')}`",
        (
            "- Sweep meaning: filter automatic trigger seeds by a compact trigger-support score, "
            "then keep the downstream shadow-promotion policy fixed."
        ),
    ]
    rows = report.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            "",
            "## Rows",
            "| Mode | Min Trigger Score | Seed Triggers After | Trigger Keep Rate | Precision | Recall | F1 | Gold Hit | Overblocking | Baseline Precision | Baseline Recall | Baseline F1 | Baseline Overblocking |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("mode_id", "")),
                    str(row.get("trigger_support_score_min", "")),
                    str(row.get("seed_trigger_count_after", "")),
                    _render_rate(row.get("trigger_keep_rate")),
                    _render_rate(row.get("candidate_precision")),
                    _render_rate(row.get("candidate_recall")),
                    _render_rate(row.get("candidate_f1")),
                    _render_rate(row.get("gold_trigger_hit_rate")),
                    _render_rate(row.get("overblocking_rate")),
                    _render_rate(row.get("baseline_precision")),
                    _render_rate(row.get("baseline_recall")),
                    _render_rate(row.get("baseline_f1")),
                    _render_rate(row.get("baseline_overblocking")),
                ]
            )
            + " |"
        )

    best_rows = report.get("best_rows_by_mode")
    if isinstance(best_rows, Mapping) and best_rows:
        lines.extend(["", "## Best Rows By Mode"])
        for mode_id, row in best_rows.items():
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                f"`{mode_id}` with `min_trigger_score={row.get('trigger_support_score_min')}`: "
                f"precision `{_render_rate(row.get('candidate_precision'))}`, "
                f"recall `{_render_rate(row.get('candidate_recall'))}`, "
                f"F1 `{_render_rate(row.get('candidate_f1'))}`, "
                f"overblocking `{_render_rate(row.get('overblocking_rate'))}`, "
                f"trigger keep `{_render_rate(row.get('trigger_keep_rate'))}`"
            )
            examples = row.get("support_row_examples")
            if (
                isinstance(examples, Sequence)
                and not isinstance(examples, (str, bytes))
                and examples
            ):
                lines.append("  Trigger examples dropped at this threshold:")
                for example in examples[:3]:
                    if not isinstance(example, Mapping):
                        continue
                    lines.append(
                        "  - "
                        f"`{example.get('target', '')}` / `{example.get('trigger', '')}` "
                        f"score=`{example.get('trigger_support_score', '')}` "
                        f"features={example.get('trigger_support_features', [])}"
                    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    report = build_trigger_support_sweep_report(
        benchmark_dataset=args.benchmark_dataset,
        benchmark_json=args.benchmark_json,
        data_root=args.data_root,
        translation_dict=args.translation_dict,
        reverse_translation_dict=args.reverse_translation_dict,
        forward_seed_max_words=max(1, int(args.forward_seed_max_words)),
        mode_ids=_parse_mode_ids(args.mode_ids),
        trigger_support_score_values=_parse_int_csv(args.trigger_support_score_values),
        shadow_support_score_min=float(args.shadow_support_score_min),
        shadow_max_promoted=max(1, int(args.shadow_max_promoted)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
