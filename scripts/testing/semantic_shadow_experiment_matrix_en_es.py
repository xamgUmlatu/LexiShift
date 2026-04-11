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

from lexishift_core.rulegen.semantic_shadow_evaluation import (  # noqa: E402
    evaluate_shadow_inventory_against_benchmark_overlap_gold,
    evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    filter_shadow_targets_by_trigger_support,
)
from semantic_shadow_experiment_support import (  # noqa: E402
    DEFAULT_BENCHMARK_JSON,
    DEFAULT_DATASET_PATH,
    build_en_es_seed_mode_payloads,
    build_inventory_for_seed_targets,
    build_shadow_signal_availability_summary,
    build_trigger_row_metadata_from_cases,
    load_en_es_shadow_experiment_resources,
    load_reverse_records_by_source_for_seed_modes,
)

DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_shadow_experiment_matrix_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_experiment_matrix_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_experiment_matrix_en_es_latest.md"
)
_TRIGGER_FILTER_LABELS = {
    "rulegen_top3_sources",
    "rulegen_all_sources",
    "forward_gloss_fragments",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a manifest-driven en-es semantic-shadow experiment matrix across "
            "seed-admission, promotion, and veto-evaluation settings."
        )
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Experiment manifest JSON.",
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


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _parse_float(value: object, *, default: float) -> float:
    if value in (None, ""):
        return float(default)
    return float(value)


def _parse_int(value: object, *, default: int, minimum: int = 0) -> int:
    if value in (None, ""):
        return max(minimum, int(default))
    return max(minimum, int(value))


def _load_manifest(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Experiment manifest must be a JSON object.")
    if str(payload.get("pair") or "").strip() not in ("", "en-es"):
        raise ValueError(
            "The semantic-shadow experiment matrix currently supports only pair='en-es'."
        )
    experiments = payload.get("experiments")
    if not isinstance(experiments, Sequence) or isinstance(experiments, (str, bytes)):
        raise ValueError("Experiment manifest must include an `experiments` list.")
    return payload


def _materialize_experiment_rows(manifest: Mapping[str, object]) -> list[dict[str, object]]:
    defaults = manifest.get("defaults")
    normalized_defaults = dict(defaults) if isinstance(defaults, Mapping) else {}
    rows: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for raw_experiment in manifest.get("experiments", ()):
        if not isinstance(raw_experiment, Mapping):
            continue
        experiment = {**normalized_defaults, **dict(raw_experiment)}
        experiment_id = str(experiment.get("experiment_id") or "").strip()
        if not experiment_id:
            raise ValueError("Each experiment row must include a non-empty `experiment_id`.")
        if experiment_id in seen_ids:
            raise ValueError(f"Duplicate experiment_id in manifest: {experiment_id!r}")
        seen_ids.add(experiment_id)
        seed_mode = str(experiment.get("seed_mode") or "").strip()
        if not seed_mode:
            raise ValueError(f"Experiment {experiment_id!r} is missing `seed_mode`.")
        experiment["experiment_id"] = experiment_id
        experiment["seed_mode"] = seed_mode
        experiment["label"] = str(experiment.get("label") or experiment_id)
        experiment["policy"] = str(experiment.get("policy") or "support_score_v1").strip()
        experiment["trigger_support_score_min"] = _parse_float(
            experiment.get("trigger_support_score_min"),
            default=0.0,
        )
        experiment["support_score_min"] = _parse_float(
            experiment.get("support_score_min"),
            default=5.0,
        )
        experiment["support_score_max_promoted"] = _parse_int(
            experiment.get("support_score_max_promoted"),
            default=2,
            minimum=1,
        )
        experiment["support_frequency_representative_bonus"] = _parse_float(
            experiment.get("support_frequency_representative_bonus"),
            default=0.0,
        )
        experiment["support_frequency_representative_top_k"] = _parse_int(
            experiment.get("support_frequency_representative_top_k"),
            default=0,
            minimum=0,
        )
        experiment["support_frequency_similarity_weight"] = _parse_float(
            experiment.get("support_frequency_similarity_weight"),
            default=0.0,
        )
        experiment["support_frequency_similarity_tau"] = _parse_float(
            experiment.get("support_frequency_similarity_tau"),
            default=0.15,
        )
        experiment["support_representative_pruning_mode"] = str(
            experiment.get("support_representative_pruning_mode") or "off"
        ).strip()
        experiment["semantic_bridge_include_aux_text"] = bool(
            experiment.get("semantic_bridge_include_aux_text")
        )
        experiment["semantic_bridge_include_examples"] = bool(
            experiment.get("semantic_bridge_include_examples")
        )
        experiment["trigger_support_weights"] = dict(
            experiment.get("trigger_support_weights")
            if isinstance(experiment.get("trigger_support_weights"), Mapping)
            else {}
        )
        experiment["shadow_support_weights"] = dict(
            experiment.get("shadow_support_weights")
            if isinstance(experiment.get("shadow_support_weights"), Mapping)
            else {}
        )
        rows.append(experiment)
    if not rows:
        raise ValueError("Experiment manifest did not yield any runnable rows.")
    return rows


def _build_miss_counts(sample_rows: object) -> dict[str, int]:
    counts = {
        "seed_missing": 0,
        "candidate_missing": 0,
        "promotion_miss": 0,
    }
    if not isinstance(sample_rows, Sequence) or isinstance(sample_rows, (str, bytes)):
        return counts
    for sample in sample_rows:
        if not isinstance(sample, Mapping):
            continue
        miss_classification = str(sample.get("miss_classification") or "").strip()
        if miss_classification in counts:
            counts[miss_classification] += 1
    return counts


def build_experiment_matrix_report(
    *,
    manifest_path: Path,
    benchmark_dataset: Path,
    benchmark_json: Path,
) -> dict[str, object]:
    manifest = _load_manifest(manifest_path)
    experiment_rows = _materialize_experiment_rows(manifest)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    resources = load_en_es_shadow_experiment_resources(
        benchmark_dataset=benchmark_dataset,
        benchmark_json=benchmark_json,
    )
    forward_seed_max_words = _parse_int(
        manifest.get("forward_seed_max_words"),
        default=1,
        minimum=1,
    )
    include_neighbor_borrow_seed_modes = bool(manifest.get("include_neighbor_borrow_seed_modes"))
    seed_mode_payloads = build_en_es_seed_mode_payloads(
        resources,
        forward_seed_max_words=forward_seed_max_words,
        include_neighbor_borrow_seed_modes=include_neighbor_borrow_seed_modes,
    )
    reverse_records_by_source = load_reverse_records_by_source_for_seed_modes(
        resources,
        tuple(seed_mode_payloads.values()),
    )
    trigger_row_metadata = build_trigger_row_metadata_from_cases(resources.cases)
    signal_availability = build_shadow_signal_availability_summary(
        resources,
        reverse_records_by_source=reverse_records_by_source,
    )

    rows: list[dict[str, object]] = []
    for experiment in experiment_rows:
        experiment_id = str(experiment.get("experiment_id") or "")
        seed_mode = str(experiment.get("seed_mode") or "")
        payload = seed_mode_payloads.get(seed_mode)
        if payload is None:
            raise ValueError(
                f"Experiment {experiment_id!r} references unknown seed mode {seed_mode!r}."
            )

        supports_trigger_filter = bool(
            _TRIGGER_FILTER_LABELS.intersection(payload.source_targets_by_label.keys())
        )
        trigger_support_score_min = float(experiment.get("trigger_support_score_min") or 0.0)
        filtered_seed_targets = list(payload.seed_targets)
        trigger_support_rows: list[dict[str, object]] = []
        if trigger_support_score_min > 0.0:
            if not supports_trigger_filter:
                raise ValueError(
                    f"Experiment {experiment_id!r} requests trigger filtering for seed mode "
                    f"{seed_mode!r}, which does not expose filterable source labels."
                )
            filtered_seed_targets, trigger_support_rows = filter_shadow_targets_by_trigger_support(
                seed_targets=payload.seed_targets,
                source_targets_by_label=payload.source_targets_by_label,
                forward_records_by_target=resources.forward_records_by_target,
                reverse_records_by_source=reverse_records_by_source,
                forward_provider=resources.forward_provider,
                reverse_provider=resources.reverse_provider,
                benchmark_target_map={
                    target.target: target for target in resources.benchmark_targets
                },
                min_score=trigger_support_score_min,
                trigger_support_weights=experiment.get("trigger_support_weights"),
            )

        inventory = build_inventory_for_seed_targets(
            resources,
            seed_targets=filtered_seed_targets,
            reverse_records_by_source=reverse_records_by_source,
            promotion_policy=str(experiment.get("policy") or "support_score_v1"),
            support_score_weights=experiment.get("shadow_support_weights"),
            semantic_bridge_include_aux_text=bool(
                experiment.get("semantic_bridge_include_aux_text")
            ),
            semantic_bridge_include_examples=bool(
                experiment.get("semantic_bridge_include_examples")
            ),
        )
        gold_proxy = evaluate_shadow_inventory_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=resources.benchmark_targets,
            policies=(str(experiment.get("policy") or "support_score_v1"),),
            support_score_min=float(experiment.get("support_score_min") or 0.0),
            support_score_max_promoted=int(experiment.get("support_score_max_promoted") or 1),
            support_frequency_representative_bonus=float(
                experiment.get("support_frequency_representative_bonus") or 0.0
            ),
            support_frequency_representative_top_k=int(
                experiment.get("support_frequency_representative_top_k") or 0
            ),
            support_frequency_similarity_weight=float(
                experiment.get("support_frequency_similarity_weight") or 0.0
            ),
            support_frequency_similarity_tau=float(
                experiment.get("support_frequency_similarity_tau") or 0.15
            ),
            support_representative_pruning_mode=str(
                experiment.get("support_representative_pruning_mode") or "off"
            ),
            support_score_weights=experiment.get("shadow_support_weights"),
        )
        veto_proxy = evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=resources.benchmark_targets,
            row_metadata_by_key=trigger_row_metadata,
            policies=(str(experiment.get("policy") or "support_score_v1"),),
            support_score_min=float(experiment.get("support_score_min") or 0.0),
            support_score_max_promoted=int(experiment.get("support_score_max_promoted") or 1),
            support_frequency_representative_bonus=float(
                experiment.get("support_frequency_representative_bonus") or 0.0
            ),
            support_frequency_representative_top_k=int(
                experiment.get("support_frequency_representative_top_k") or 0
            ),
            support_frequency_similarity_weight=float(
                experiment.get("support_frequency_similarity_weight") or 0.0
            ),
            support_frequency_similarity_tau=float(
                experiment.get("support_frequency_similarity_tau") or 0.15
            ),
            support_representative_pruning_mode=str(
                experiment.get("support_representative_pruning_mode") or "off"
            ),
            support_score_weights=experiment.get("shadow_support_weights"),
        )
        policy_id = str(experiment.get("policy") or "support_score_v1")
        gold_policy = (
            gold_proxy.get("policies", {}).get(policy_id, {})
            if isinstance(gold_proxy.get("policies"), Mapping)
            else {}
        )
        gold_summary = gold_policy.get("summary") if isinstance(gold_policy, Mapping) else {}
        gold_candidate_pool = (
            gold_proxy.get("candidate_pool_summary")
            if isinstance(gold_proxy.get("candidate_pool_summary"), Mapping)
            else {}
        )
        veto_policy = (
            veto_proxy.get("policies", {}).get(policy_id, {})
            if isinstance(veto_proxy.get("policies"), Mapping)
            else {}
        )
        veto_summary = veto_policy.get("summary") if isinstance(veto_policy, Mapping) else {}
        veto_slice_summaries = (
            veto_policy.get("slice_summaries", []) if isinstance(veto_policy, Mapping) else {}
        )
        harmful_allow_rows = (
            veto_policy.get("sample_harmful_allow_rows", [])
            if isinstance(veto_policy, Mapping)
            else []
        )
        false_abstain_rows = (
            veto_policy.get("sample_false_abstain_rows", [])
            if isinstance(veto_policy, Mapping)
            else []
        )
        filtered_trigger_count = sum(
            len(target.reviewed_triggers)
            for target in filtered_seed_targets
            if target.reviewed_triggers
        )
        original_trigger_count = sum(
            len(target.reviewed_triggers)
            for target in payload.seed_targets
            if target.reviewed_triggers
        )
        miss_counts = _build_miss_counts(harmful_allow_rows)
        rows.append(
            {
                "experiment_id": experiment_id,
                "label": experiment.get("label"),
                "seed_mode": seed_mode,
                "policy": policy_id,
                "forward_seed_max_words": int(forward_seed_max_words),
                "trigger_support_score_min": trigger_support_score_min,
                "trigger_support_weights": experiment.get("trigger_support_weights"),
                "shadow_support_weights": experiment.get("shadow_support_weights"),
                "support_score_min": float(experiment.get("support_score_min") or 0.0),
                "support_score_max_promoted": int(
                    experiment.get("support_score_max_promoted") or 1
                ),
                "support_frequency_representative_bonus": float(
                    experiment.get("support_frequency_representative_bonus") or 0.0
                ),
                "support_frequency_representative_top_k": int(
                    experiment.get("support_frequency_representative_top_k") or 0
                ),
                "support_frequency_similarity_weight": float(
                    experiment.get("support_frequency_similarity_weight") or 0.0
                ),
                "support_frequency_similarity_tau": float(
                    experiment.get("support_frequency_similarity_tau") or 0.15
                ),
                "support_representative_pruning_mode": str(
                    experiment.get("support_representative_pruning_mode") or "off"
                ),
                "semantic_bridge_include_aux_text": bool(
                    experiment.get("semantic_bridge_include_aux_text")
                ),
                "semantic_bridge_include_examples": bool(
                    experiment.get("semantic_bridge_include_examples")
                ),
                "seed_target_count": len(payload.seed_targets),
                "seed_trigger_count_before_filter": original_trigger_count,
                "seed_trigger_count_after_filter": filtered_trigger_count,
                "seed_trigger_keep_rate": (
                    float(filtered_trigger_count) / float(original_trigger_count)
                    if original_trigger_count
                    else None
                ),
                "gold_trigger_inventory_coverage_rate": gold_candidate_pool.get(
                    "gold_trigger_inventory_coverage_rate"
                ),
                "candidate_pool_trigger_recall": gold_candidate_pool.get(
                    "candidate_pool_trigger_recall"
                ),
                "candidate_pool_exact_match_rate": gold_candidate_pool.get(
                    "candidate_pool_exact_match_rate"
                ),
                "gold_candidate_precision": gold_summary.get("candidate_precision"),
                "gold_candidate_recall": gold_summary.get("candidate_recall"),
                "gold_candidate_f1": gold_summary.get("candidate_f1"),
                "gold_trigger_hit_rate": gold_summary.get("gold_trigger_hit_rate"),
                "gold_top1_hit_rate": gold_summary.get("top1_gold_trigger_hit_rate"),
                "gold_overblocking_rate": gold_summary.get("overblocking_rate"),
                "veto_overall_accuracy": veto_summary.get("overall_accuracy"),
                "veto_abstain_recall": veto_summary.get("abstain_recall"),
                "veto_harmful_allow_rate": veto_summary.get("harmful_allow_rate"),
                "veto_allow_precision": veto_summary.get("allow_precision"),
                "veto_overblocking_rate": veto_summary.get("overblocking_rate"),
                "veto_false_abstain_count": veto_summary.get("false_abstain_count"),
                "veto_harmful_allow_count": veto_summary.get("harmful_allow_count"),
                "veto_slice_summaries": veto_slice_summaries,
                "automatic_feature_slice_count": sum(
                    1
                    for key in veto_slice_summaries.keys()
                    if str(key or "").startswith("feature:")
                )
                if isinstance(veto_slice_summaries, Mapping)
                else 0,
                "harmful_allow_miss_counts": miss_counts,
                "sample_harmful_allow_rows": harmful_allow_rows[:5]
                if isinstance(harmful_allow_rows, Sequence)
                else [],
                "sample_false_abstain_rows": false_abstain_rows[:5]
                if isinstance(false_abstain_rows, Sequence)
                else [],
                "trigger_filter_examples_dropped": [
                    {
                        "target": row.get("target"),
                        "trigger": row.get("trigger"),
                        "trigger_support_score": row.get("trigger_support_score"),
                        "trigger_support_features": row.get("trigger_support_features", []),
                    }
                    for row in trigger_support_rows
                    if float(row.get("trigger_support_score") or 0.0) < trigger_support_score_min
                ][:5],
            }
        )

    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "manifest_path": str(manifest_path),
        "benchmark_dataset": str(benchmark_dataset),
        "benchmark_json": str(benchmark_json),
        "forward_seed_max_words": int(forward_seed_max_words),
        "include_neighbor_borrow_seed_modes": include_neighbor_borrow_seed_modes,
        "source_signal_availability": signal_availability,
        "experiment_count": len(rows),
        "rows": rows,
    }


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Semantic Shadow Experiment Matrix",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Manifest: `{report.get('manifest_path', '')}`",
        f"- Forward seed max words: `{report.get('forward_seed_max_words', '')}`",
        f"- Neighbor-borrow modes loaded: `{bool(report.get('include_neighbor_borrow_seed_modes'))}`",
        "- Matrix meaning: each row is a full experiment configuration spanning seed admission, promotion scoring, and veto evaluation.",
    ]
    signal_availability = report.get("source_signal_availability")
    if isinstance(signal_availability, Mapping):
        lines.extend(
            [
                f"- Forward records with examples: `{signal_availability.get('forward_records_with_examples', 0)} / {signal_availability.get('forward_records_total', 0)}` across `{signal_availability.get('forward_targets_with_examples', 0)}` targets",
                f"- Reverse records with aux text: `{signal_availability.get('trigger_reverse_records_with_aux_text', 0)} / {signal_availability.get('trigger_reverse_records_total', 0)}` across `{signal_availability.get('trigger_reverse_triggers_with_aux_text', 0)}` triggers",
            ]
        )
    rows = report.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            "",
            "## Summary",
            "| Experiment | Seed Mode | Trigger Filter | Shadow Min | Max Promoted | Gold Prec | Gold Rec | Veto Acc | Abstain Rec | Harmful Allow |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("experiment_id", "")),
                    str(row.get("seed_mode", "")),
                    str(row.get("trigger_support_score_min", "")),
                    str(row.get("support_score_min", "")),
                    str(row.get("support_score_max_promoted", "")),
                    _render_rate(row.get("gold_candidate_precision")),
                    _render_rate(row.get("gold_candidate_recall")),
                    _render_rate(row.get("veto_overall_accuracy")),
                    _render_rate(row.get("veto_abstain_recall")),
                    _render_rate(row.get("veto_harmful_allow_rate")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Details"])
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        miss_counts = row.get("harmful_allow_miss_counts", {})
        lines.extend(
            [
                "",
                f"### {row.get('experiment_id', '')}",
                f"- Label: `{row.get('label', '')}`",
                f"- Seed mode: `{row.get('seed_mode', '')}`",
                f"- Policy: `{row.get('policy', '')}`",
                f"- Trigger filter min: `{row.get('trigger_support_score_min', '')}`",
                f"- Shadow support min / max promoted: `{row.get('support_score_min', '')}` / `{row.get('support_score_max_promoted', '')}`",
                f"- Semantic-bridge aux text / examples: `{bool(row.get('semantic_bridge_include_aux_text'))}` / `{bool(row.get('semantic_bridge_include_examples'))}`",
                f"- Seed trigger keep rate: `{_render_rate(row.get('seed_trigger_keep_rate'))}` (`{row.get('seed_trigger_count_after_filter', 0)} / {row.get('seed_trigger_count_before_filter', 0)}`)",
                f"- Gold candidate precision / recall / F1: `{_render_rate(row.get('gold_candidate_precision'))}` / `{_render_rate(row.get('gold_candidate_recall'))}` / `{_render_rate(row.get('gold_candidate_f1'))}`",
                f"- Gold trigger hit / top1 hit / exact-pool match: `{_render_rate(row.get('gold_trigger_hit_rate'))}` / `{_render_rate(row.get('gold_top1_hit_rate'))}` / `{_render_rate(row.get('candidate_pool_exact_match_rate'))}`",
                f"- Veto accuracy / abstain recall / harmful allow / overblocking: `{_render_rate(row.get('veto_overall_accuracy'))}` / `{_render_rate(row.get('veto_abstain_recall'))}` / `{_render_rate(row.get('veto_harmful_allow_rate'))}` / `{_render_rate(row.get('veto_overblocking_rate'))}`",
                f"- Veto counts: `false_abstain={row.get('veto_false_abstain_count', 0)}`, `harmful_allow={row.get('veto_harmful_allow_count', 0)}`",
                f"- Automatic feature slices tracked: `{row.get('automatic_feature_slice_count', 0)}`",
                f"- Harmful-allow miss counts: `seed_missing={miss_counts.get('seed_missing', 0)}`, `candidate_missing={miss_counts.get('candidate_missing', 0)}`, `promotion_miss={miss_counts.get('promotion_miss', 0)}`",
            ]
        )
        trigger_support_weights = row.get("trigger_support_weights")
        if isinstance(trigger_support_weights, Mapping) and trigger_support_weights:
            lines.append(
                "- Trigger support weights: "
                f"`{json.dumps(trigger_support_weights, sort_keys=True, ensure_ascii=False)}`"
            )
        shadow_support_weights = row.get("shadow_support_weights")
        if isinstance(shadow_support_weights, Mapping) and shadow_support_weights:
            lines.append(
                "- Shadow support weights: "
                f"`{json.dumps(shadow_support_weights, sort_keys=True, ensure_ascii=False)}`"
            )
        trigger_filter_examples = row.get("trigger_filter_examples_dropped")
        if (
            isinstance(trigger_filter_examples, Sequence)
            and not isinstance(trigger_filter_examples, (str, bytes))
            and trigger_filter_examples
        ):
            lines.append("- Trigger-filter examples dropped:")
            for sample in trigger_filter_examples[:5]:
                if not isinstance(sample, Mapping):
                    continue
                lines.append(
                    f"  - `{sample.get('target', '')}` / `{sample.get('trigger', '')}` score=`{sample.get('trigger_support_score', '')}` features={sample.get('trigger_support_features', [])}"
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
                    f"  - `{sample.get('target', '')}` / `{sample.get('trigger', '')}` gold={sample.get('gold_shadow_targets', [])} promoted={sample.get('promoted_targets', [])} miss={sample.get('miss_classification', '')}"
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
                    f"  - `{sample.get('target', '')}` / `{sample.get('trigger', '')}` promoted={sample.get('promoted_targets', [])} cases={sample.get('case_ids', [])} slices={sample.get('slice_tags', [])}"
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    report = build_experiment_matrix_report(
        manifest_path=args.manifest,
        benchmark_dataset=args.benchmark_dataset,
        benchmark_json=args.benchmark_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
