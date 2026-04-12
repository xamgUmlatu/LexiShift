#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
import sys
from typing import Callable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from semantic_routing_generalization_bound_reporting import (  # noqa: E402
    render_generalization_bound_markdown,
)
from semantic_routing_generalization_bound_splits import (  # noqa: E402
    build_metric_views,
    build_split_lookup,
    find_row,
    load_generalization_split_manifest,
    partition_rows_by_split,
    resolve_overlap_family_split_id,
    resolve_sentence_veto_split_id,
    select_best_source_only_row,
)
from semantic_routing_sentence_veto_support import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_DATASET,
    build_sentence_veto_report,
)
from semantic_shadow_seed_compare_en_es import (  # noqa: E402
    DEFAULT_BENCHMARK_JSON,
    DEFAULT_DATASET_PATH,
)
from semantic_shadow_veto_proxy_compare_en_es import (  # noqa: E402
    build_veto_proxy_compare_report,
)

DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_routing_generalization_bound_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_generalization_bound_en_es_latest.md"
)
DEFAULT_SPLIT_MANIFEST = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_routing_generalization_splits_en_es.json"
)
DEFAULT_BOOTSTRAP_ITERATIONS = 2000
DEFAULT_RANDOM_SEED = 1729
DEFAULT_CONFIDENCE_LEVEL = 0.95

FIXED_SHADOW_CONTROL_CONFIG = {
    "label": "Fixed-shadow scorer control",
    "scorer_id": "tfidf_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.05,
    "min_margin": 0.0,
    "phrase_control_mode": "off",
    "active_rescue_mode": "off",
}

FIXED_SHADOW_REFERENCE_CONFIG = {
    "label": "Sentence-transformer reference",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.15,
    "phrase_control_mode": "off",
    "active_rescue_mode": "off",
}

FIXED_SHADOW_METRIC_DIRECTIONS = {
    "decision_accuracy": "higher",
    "replace_precision": "higher",
    "replace_recall": "higher",
    "harmful_replace_rate": "lower",
    "false_abstain_rate": "lower",
    "winner_accuracy": "higher",
    "shadow_winner_accuracy": "higher",
}

VETO_PROXY_METRIC_DIRECTIONS = {
    "overall_accuracy": "higher",
    "abstain_recall": "higher",
    "harmful_allow_rate": "lower",
    "allow_precision": "higher",
    "overblocking_rate": "lower",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate cluster-aware confidence bounds for the current en-es semantic-veto "
            "controls. The report combines a fixed-shadow runtime scorer control with the "
            "current lower-bound blocker-generation lanes."
        )
    )
    parser.add_argument(
        "--sentence-dataset",
        type=Path,
        default=DEFAULT_SENTENCE_VETO_DATASET,
        help="Sentence-level fixed-shadow veto dataset JSON.",
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
        "--family-splits-manifest",
        type=Path,
        default=DEFAULT_SPLIT_MANIFEST,
        help="Explicit tune vs held-out family split manifest.",
    )
    parser.add_argument(
        "--bootstrap-iterations",
        type=int,
        default=DEFAULT_BOOTSTRAP_ITERATIONS,
        help="Cluster-bootstrap resample count.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Random seed for cluster-bootstrap sampling.",
    )
    parser.add_argument(
        "--confidence-level",
        type=float,
        default=DEFAULT_CONFIDENCE_LEVEL,
        help="Bootstrap confidence level between 0 and 1.",
    )
    parser.add_argument(
        "--include-sentence-transformer-reference",
        action="store_true",
        help="Also compute the current sentence-transformer reference row.",
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


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    bounded_quantile = min(max(float(quantile), 0.0), 1.0)
    sorted_values = sorted(float(value) for value in values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = bounded_quantile * (len(sorted_values) - 1)
    lower_index = int(math.floor(rank))
    upper_index = int(math.ceil(rank))
    if lower_index == upper_index:
        return sorted_values[lower_index]
    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    fraction = rank - lower_index
    return lower_value + ((upper_value - lower_value) * fraction)


def _summarize_sentence_veto_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    cases_total = len(rows)
    gold_replace_cases = 0
    gold_abstain_cases = 0
    predicted_replace_cases = 0
    true_replace_count = 0
    true_abstain_count = 0
    harmful_replace_count = 0
    false_abstain_count = 0
    winner_labeled_cases = 0
    winner_correct_count = 0
    shadow_winner_labeled_cases = 0
    shadow_winner_correct_count = 0

    for row in rows:
        gold_decision = str(row.get("gold_decision") or "").strip().lower()
        predicted_decision = str(row.get("predicted_decision") or "").strip().lower()
        gold_winner = str(row.get("gold_winner") or "").strip()
        predicted_winner = str(row.get("predicted_winner") or "").strip()
        gold_winner_type = str(row.get("gold_winner_type") or "").strip().lower()

        if gold_decision == "replace":
            gold_replace_cases += 1
        else:
            gold_abstain_cases += 1
        if predicted_decision == "replace":
            predicted_replace_cases += 1
        if predicted_decision == "replace" and gold_decision == "replace":
            true_replace_count += 1
        elif predicted_decision == "replace":
            harmful_replace_count += 1
        elif gold_decision == "replace":
            false_abstain_count += 1
        else:
            true_abstain_count += 1

        if gold_winner_type in {"active", "shadow"}:
            winner_labeled_cases += 1
            if predicted_winner and predicted_winner == gold_winner:
                winner_correct_count += 1
        if gold_winner_type == "shadow":
            shadow_winner_labeled_cases += 1
            if predicted_winner and predicted_winner == gold_winner:
                shadow_winner_correct_count += 1

    return {
        "cases_total": cases_total,
        "gold_replace_cases": gold_replace_cases,
        "gold_abstain_cases": gold_abstain_cases,
        "predicted_replace_cases": predicted_replace_cases,
        "true_replace_count": true_replace_count,
        "true_abstain_count": true_abstain_count,
        "harmful_replace_count": harmful_replace_count,
        "false_abstain_count": false_abstain_count,
        "winner_labeled_cases": winner_labeled_cases,
        "shadow_winner_labeled_cases": shadow_winner_labeled_cases,
        "decision_accuracy": _safe_rate(true_replace_count + true_abstain_count, cases_total),
        "replace_precision": _safe_rate(true_replace_count, predicted_replace_cases),
        "replace_recall": _safe_rate(true_replace_count, gold_replace_cases),
        "harmful_replace_rate": _safe_rate(harmful_replace_count, gold_abstain_cases),
        "false_abstain_rate": _safe_rate(false_abstain_count, gold_replace_cases),
        "winner_accuracy": _safe_rate(winner_correct_count, winner_labeled_cases),
        "shadow_winner_accuracy": _safe_rate(
            shadow_winner_correct_count,
            shadow_winner_labeled_cases,
        ),
    }


def _summarize_veto_proxy_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    trigger_rows_total = len(rows)
    ambiguous_trigger_rows = 0
    clear_trigger_rows = 0
    allow_rows = 0
    abstain_rows = 0
    true_abstain_count = 0
    harmful_allow_count = 0
    true_allow_count = 0
    false_abstain_count = 0

    for row in rows:
        should_abstain = bool(row.get("should_abstain"))
        did_abstain = bool(row.get("did_abstain"))
        if should_abstain:
            ambiguous_trigger_rows += 1
        else:
            clear_trigger_rows += 1
        if did_abstain:
            abstain_rows += 1
        else:
            allow_rows += 1
        outcome = str(row.get("outcome") or "").strip()
        if outcome == "true_abstain":
            true_abstain_count += 1
        elif outcome == "harmful_allow":
            harmful_allow_count += 1
        elif outcome == "true_allow":
            true_allow_count += 1
        elif outcome == "false_abstain":
            false_abstain_count += 1

    return {
        "trigger_rows_total": trigger_rows_total,
        "ambiguous_trigger_rows": ambiguous_trigger_rows,
        "clear_trigger_rows": clear_trigger_rows,
        "allow_rows": allow_rows,
        "abstain_rows": abstain_rows,
        "true_abstain_count": true_abstain_count,
        "harmful_allow_count": harmful_allow_count,
        "true_allow_count": true_allow_count,
        "false_abstain_count": false_abstain_count,
        "overall_accuracy": _safe_rate(true_abstain_count + true_allow_count, trigger_rows_total),
        "abstain_recall": _safe_rate(true_abstain_count, ambiguous_trigger_rows),
        "harmful_allow_rate": _safe_rate(harmful_allow_count, ambiguous_trigger_rows),
        "allow_precision": _safe_rate(true_allow_count, allow_rows),
        "allow_rate": _safe_rate(allow_rows, trigger_rows_total),
        "abstain_rate": _safe_rate(abstain_rows, trigger_rows_total),
        "overblocking_rate": _safe_rate(false_abstain_count, clear_trigger_rows),
    }


def _group_rows_by_cluster(
    rows: Sequence[Mapping[str, object]],
    *,
    cluster_key_name: str,
) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        cluster_value = str(row.get(cluster_key_name) or "").strip() or "<missing>"
        grouped.setdefault(cluster_value, []).append(row)
    return grouped


def _build_cluster_summaries(
    grouped_rows: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    summarize_rows: Callable[[Sequence[Mapping[str, object]]], dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cluster_id, cluster_rows in grouped_rows.items():
        summary = summarize_rows(cluster_rows)
        rows.append(
            {
                "cluster_id": str(cluster_id),
                "row_count": len(cluster_rows),
                "summary": summary,
            }
        )
    return sorted(rows, key=lambda item: (-int(item.get("row_count") or 0), item["cluster_id"]))


def _bootstrap_cluster_metrics(
    grouped_rows: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    summarize_rows: Callable[[Sequence[Mapping[str, object]]], dict[str, object]],
    metric_names: Sequence[str],
    bootstrap_iterations: int,
    random_seed: int,
    confidence_level: float,
) -> dict[str, dict[str, object]]:
    cluster_samples = [list(rows) for rows in grouped_rows.values() if rows]
    if not cluster_samples:
        return {}
    lower_quantile = (1.0 - confidence_level) / 2.0
    upper_quantile = 1.0 - lower_quantile
    rng = random.Random(int(random_seed))
    sampled_values: dict[str, list[float]] = {metric: [] for metric in metric_names}
    for _ in range(max(1, int(bootstrap_iterations))):
        sampled_rows: list[Mapping[str, object]] = []
        for _cluster_index in range(len(cluster_samples)):
            sampled_rows.extend(rng.choice(cluster_samples))
        summary = summarize_rows(sampled_rows)
        for metric_name in metric_names:
            value = summary.get(metric_name)
            if isinstance(value, (int, float)):
                sampled_values[metric_name].append(float(value))
    intervals: dict[str, dict[str, object]] = {}
    for metric_name in metric_names:
        values = sampled_values.get(metric_name, [])
        intervals[metric_name] = {
            "lower": _percentile(values, lower_quantile),
            "upper": _percentile(values, upper_quantile),
            "sample_count": len(values),
        }
    return intervals


def _leave_one_cluster_out_metrics(
    grouped_rows: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    summarize_rows: Callable[[Sequence[Mapping[str, object]]], dict[str, object]],
    metric_names: Sequence[str],
    metric_directions: Mapping[str, str],
) -> dict[str, object]:
    cluster_ids = [str(cluster_id) for cluster_id in grouped_rows.keys()]
    if len(cluster_ids) <= 1:
        return {"rows": [], "metrics": {}}

    rows: list[dict[str, object]] = []
    metric_values: dict[str, list[tuple[str, float]]] = {metric: [] for metric in metric_names}
    for omitted_cluster_id in cluster_ids:
        sampled_rows: list[Mapping[str, object]] = []
        for cluster_id, cluster_rows in grouped_rows.items():
            if str(cluster_id) == omitted_cluster_id:
                continue
            sampled_rows.extend(cluster_rows)
        summary = summarize_rows(sampled_rows)
        rows.append(
            {
                "omitted_cluster_id": omitted_cluster_id,
                "row_count": len(sampled_rows),
                "summary": summary,
            }
        )
        for metric_name in metric_names:
            value = summary.get(metric_name)
            if isinstance(value, (int, float)):
                metric_values[metric_name].append((omitted_cluster_id, float(value)))

    metric_report: dict[str, object] = {}
    for metric_name in metric_names:
        values = metric_values.get(metric_name, [])
        if not values:
            metric_report[metric_name] = {
                "min": None,
                "max": None,
                "worst_case": None,
                "worst_case_omitted_cluster_id": "",
            }
            continue
        minimum = min(value for _, value in values)
        maximum = max(value for _, value in values)
        direction = str(metric_directions.get(metric_name) or "higher")
        if direction == "lower":
            worst_cluster_id, worst_case = max(values, key=lambda item: item[1])
        else:
            worst_cluster_id, worst_case = min(values, key=lambda item: item[1])
        metric_report[metric_name] = {
            "min": minimum,
            "max": maximum,
            "worst_case": worst_case,
            "worst_case_omitted_cluster_id": worst_cluster_id,
        }
    return {
        "rows": rows,
        "metrics": metric_report,
    }


def _build_surface_bound(
    *,
    label: str,
    rows: Sequence[Mapping[str, object]],
    cluster_key_name: str,
    summarize_rows: Callable[[Sequence[Mapping[str, object]]], dict[str, object]],
    metric_directions: Mapping[str, str],
    bootstrap_iterations: int,
    random_seed: int,
    confidence_level: float,
    config: Mapping[str, object] | None = None,
) -> dict[str, object]:
    point_summary = summarize_rows(rows)
    grouped_rows = _group_rows_by_cluster(rows, cluster_key_name=cluster_key_name)
    cluster_summaries = _build_cluster_summaries(grouped_rows, summarize_rows=summarize_rows)
    bootstrap_intervals = _bootstrap_cluster_metrics(
        grouped_rows,
        summarize_rows=summarize_rows,
        metric_names=tuple(metric_directions.keys()),
        bootstrap_iterations=bootstrap_iterations,
        random_seed=random_seed,
        confidence_level=confidence_level,
    )
    leave_one_cluster_out = _leave_one_cluster_out_metrics(
        grouped_rows,
        summarize_rows=summarize_rows,
        metric_names=tuple(metric_directions.keys()),
        metric_directions=metric_directions,
    )
    metric_views = build_metric_views(
        point_summary=point_summary,
        bootstrap_intervals=bootstrap_intervals,
        leave_one_cluster_out=leave_one_cluster_out,
        metric_directions=metric_directions,
        confidence_level=confidence_level,
    )
    return {
        "label": label,
        "config": dict(config or {}),
        "cluster_key_name": cluster_key_name,
        "cluster_count": len(grouped_rows),
        "summary": point_summary,
        "metric_views": metric_views,
        "cluster_summaries": cluster_summaries,
        "leave_one_cluster_out_rows": leave_one_cluster_out.get("rows", []),
    }


def _extend_with_split_surfaces(
    surfaces: list[dict[str, object]],
    *,
    label: str,
    rows: Sequence[Mapping[str, object]],
    cluster_key_name: str,
    summarize_rows: Callable[[Sequence[Mapping[str, object]]], dict[str, object]],
    metric_directions: Mapping[str, str],
    bootstrap_iterations: int,
    random_seed: int,
    confidence_level: float,
    config: Mapping[str, object],
    split_ids: Sequence[str],
    split_lookup: Mapping[str, str],
    resolve_split_id: Callable[[Mapping[str, object], Mapping[str, str]], str],
) -> None:
    split_rows, _unassigned_rows = partition_rows_by_split(
        rows,
        split_ids=split_ids,
        split_lookup=split_lookup,
        resolve_split_id=resolve_split_id,
    )
    for index, split_id in enumerate(split_ids):
        subset_rows = tuple(split_rows.get(str(split_id), ()))
        if not subset_rows:
            continue
        surfaces.append(
            _build_surface_bound(
                label=f"{label} [{split_id}]",
                rows=subset_rows,
                cluster_key_name=cluster_key_name,
                summarize_rows=summarize_rows,
                metric_directions=metric_directions,
                bootstrap_iterations=bootstrap_iterations,
                random_seed=random_seed + index + 100,
                confidence_level=confidence_level,
                config={**dict(config), "subset_id": str(split_id)},
            )
        )


def build_generalization_bound_report(
    *,
    sentence_dataset: Path,
    benchmark_dataset: Path,
    benchmark_json: Path,
    family_splits_manifest: Path,
    data_root: Path,
    translation_dict: Path | None,
    reverse_translation_dict: Path | None,
    forward_seed_max_words: int,
    bootstrap_iterations: int,
    random_seed: int,
    confidence_level: float,
    include_sentence_transformer_reference: bool,
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    split_manifest = load_generalization_split_manifest(family_splits_manifest)
    fixed_shadow_split_ids, fixed_shadow_split_lookup = build_split_lookup(
        dict(split_manifest.get("fixed_shadow_sentence_veto") or {})
    )
    reviewed_family_split_ids, reviewed_family_split_lookup = build_split_lookup(
        dict(split_manifest.get("reviewed_overlap_semantic_families") or {})
    )

    fixed_shadow_surfaces: list[dict[str, object]] = []
    fixed_shadow_control_report = build_sentence_veto_report(
        dataset_path=sentence_dataset,
        scorer_id=str(FIXED_SHADOW_CONTROL_CONFIG["scorer_id"]),
        context_view=str(FIXED_SHADOW_CONTROL_CONFIG["context_view"]),
        evidence_view=str(FIXED_SHADOW_CONTROL_CONFIG["evidence_view"]),
        min_active_score=float(FIXED_SHADOW_CONTROL_CONFIG["min_active_score"]),
        min_margin=float(FIXED_SHADOW_CONTROL_CONFIG["min_margin"]),
        phrase_control_mode=str(FIXED_SHADOW_CONTROL_CONFIG["phrase_control_mode"]),
        active_rescue_mode=str(FIXED_SHADOW_CONTROL_CONFIG["active_rescue_mode"]),
    )
    fixed_shadow_control_rows = tuple(
        row
        for row in fixed_shadow_control_report.get("row_results", ())
        if isinstance(row, Mapping)
    )
    fixed_shadow_surfaces.append(
        _build_surface_bound(
            label=str(FIXED_SHADOW_CONTROL_CONFIG["label"]),
            rows=fixed_shadow_control_rows,
            cluster_key_name="family_id",
            summarize_rows=_summarize_sentence_veto_rows,
            metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed,
            confidence_level=confidence_level,
            config=FIXED_SHADOW_CONTROL_CONFIG,
        )
    )
    _extend_with_split_surfaces(
        fixed_shadow_surfaces,
        label=str(FIXED_SHADOW_CONTROL_CONFIG["label"]),
        rows=fixed_shadow_control_rows,
        cluster_key_name="family_id",
        summarize_rows=_summarize_sentence_veto_rows,
        metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
        bootstrap_iterations=bootstrap_iterations,
        random_seed=random_seed,
        confidence_level=confidence_level,
        config=FIXED_SHADOW_CONTROL_CONFIG,
        split_ids=fixed_shadow_split_ids,
        split_lookup=fixed_shadow_split_lookup,
        resolve_split_id=resolve_sentence_veto_split_id,
    )
    if include_sentence_transformer_reference:
        reference_report = build_sentence_veto_report(
            dataset_path=sentence_dataset,
            scorer_id=str(FIXED_SHADOW_REFERENCE_CONFIG["scorer_id"]),
            context_view=str(FIXED_SHADOW_REFERENCE_CONFIG["context_view"]),
            evidence_view=str(FIXED_SHADOW_REFERENCE_CONFIG["evidence_view"]),
            min_active_score=float(FIXED_SHADOW_REFERENCE_CONFIG["min_active_score"]),
            min_margin=float(FIXED_SHADOW_REFERENCE_CONFIG["min_margin"]),
            phrase_control_mode=str(FIXED_SHADOW_REFERENCE_CONFIG["phrase_control_mode"]),
            active_rescue_mode=str(FIXED_SHADOW_REFERENCE_CONFIG["active_rescue_mode"]),
        )
        reference_rows = tuple(
            row for row in reference_report.get("row_results", ()) if isinstance(row, Mapping)
        )
        fixed_shadow_surfaces.append(
            _build_surface_bound(
                label=str(FIXED_SHADOW_REFERENCE_CONFIG["label"]),
                rows=reference_rows,
                cluster_key_name="family_id",
                summarize_rows=_summarize_sentence_veto_rows,
                metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
                bootstrap_iterations=bootstrap_iterations,
                random_seed=random_seed + 1,
                confidence_level=confidence_level,
                config=FIXED_SHADOW_REFERENCE_CONFIG,
            )
        )
        _extend_with_split_surfaces(
            fixed_shadow_surfaces,
            label=str(FIXED_SHADOW_REFERENCE_CONFIG["label"]),
            rows=reference_rows,
            cluster_key_name="family_id",
            summarize_rows=_summarize_sentence_veto_rows,
            metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed + 1,
            confidence_level=confidence_level,
            config=FIXED_SHADOW_REFERENCE_CONFIG,
            split_ids=fixed_shadow_split_ids,
            split_lookup=fixed_shadow_split_lookup,
            resolve_split_id=resolve_sentence_veto_split_id,
        )

    veto_proxy_report = build_veto_proxy_compare_report(
        benchmark_dataset=benchmark_dataset,
        benchmark_json=benchmark_json,
        data_root=data_root,
        translation_dict=translation_dict,
        reverse_translation_dict=reverse_translation_dict,
        forward_seed_max_words=forward_seed_max_words,
        include_row_results=True,
    )
    veto_proxy_rows = [row for row in veto_proxy_report.get("rows", ()) if isinstance(row, Mapping)]
    veto_proxy_surfaces: list[dict[str, object]] = []
    for row in veto_proxy_rows:
        source_id = str(row.get("source_id") or "").strip()
        label = str(row.get("label") or source_id)
        row_results = tuple(
            result for result in row.get("row_results", ()) if isinstance(result, Mapping)
        )
        if not row_results:
            continue
        veto_proxy_surfaces.append(
            _build_surface_bound(
                label=label,
                rows=row_results,
                cluster_key_name="trigger",
                summarize_rows=_summarize_veto_proxy_rows,
                metric_directions=VETO_PROXY_METRIC_DIRECTIONS,
                bootstrap_iterations=bootstrap_iterations,
                random_seed=random_seed + len(veto_proxy_surfaces) + 10,
                confidence_level=confidence_level,
                config={
                    "source_id": source_id,
                    "seed_mode": row.get("seed_mode"),
                    "policy": row.get("policy"),
                    "support_score_min": row.get("support_score_min"),
                    "support_score_max_promoted": row.get("support_score_max_promoted"),
                },
            )
        )
        _extend_with_split_surfaces(
            veto_proxy_surfaces,
            label=label,
            rows=row_results,
            cluster_key_name="trigger",
            summarize_rows=_summarize_veto_proxy_rows,
            metric_directions=VETO_PROXY_METRIC_DIRECTIONS,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed + len(veto_proxy_surfaces) + 10,
            confidence_level=confidence_level,
            config={
                "source_id": source_id,
                "seed_mode": row.get("seed_mode"),
                "policy": row.get("policy"),
                "support_score_min": row.get("support_score_min"),
                "support_score_max_promoted": row.get("support_score_max_promoted"),
            },
            split_ids=reviewed_family_split_ids,
            split_lookup=reviewed_family_split_lookup,
            resolve_split_id=resolve_overlap_family_split_id,
        )

    source_only_row = select_best_source_only_row(veto_proxy_rows)
    reviewed_auto_row = find_row(veto_proxy_rows, "reviewed_auto_shadows")
    curated_row = find_row(veto_proxy_rows, "curated_shadows")
    fixed_shadow_control_surface = fixed_shadow_surfaces[0] if fixed_shadow_surfaces else {}

    def _metric_view(surface: Mapping[str, object], metric_name: str) -> Mapping[str, object]:
        metric_views = surface.get("metric_views")
        if isinstance(metric_views, Mapping):
            metric_view = metric_views.get(metric_name)
            if isinstance(metric_view, Mapping):
                return metric_view
        return {}

    source_only_surface = None
    source_only_source_id = ""
    if isinstance(source_only_row, Mapping):
        source_only_source_id = str(source_only_row.get("source_id") or "").strip()
        source_only_surface = next(
            (
                surface
                for surface in veto_proxy_surfaces
                if isinstance(surface.get("config"), Mapping)
                and str(surface["config"].get("source_id") or "").strip() == source_only_source_id
            ),
            None,
        )

    confidence_corridor = {
        "source_only_source_id": source_only_source_id,
        "source_only_abstain_recall_conservative_floor": (
            _metric_view(source_only_surface or {}, "abstain_recall").get("conservative_floor")
            if isinstance(source_only_surface, Mapping)
            else None
        ),
        "source_only_harmful_allow_conservative_ceiling": (
            _metric_view(source_only_surface or {}, "harmful_allow_rate").get(
                "conservative_ceiling"
            )
            if isinstance(source_only_surface, Mapping)
            else None
        ),
        "fixed_shadow_replace_recall_conservative_floor": _metric_view(
            fixed_shadow_control_surface, "replace_recall"
        ).get("conservative_floor"),
        "fixed_shadow_harmful_replace_conservative_ceiling": _metric_view(
            fixed_shadow_control_surface, "harmful_replace_rate"
        ).get("conservative_ceiling"),
        "reviewed_auto_abstain_recall_conservative_floor": None,
        "reviewed_auto_harmful_allow_conservative_ceiling": None,
        "curated_abstain_recall_conservative_floor": None,
        "curated_harmful_allow_conservative_ceiling": None,
    }
    if isinstance(reviewed_auto_row, Mapping):
        reviewed_auto_surface = next(
            (
                surface
                for surface in veto_proxy_surfaces
                if isinstance(surface.get("config"), Mapping)
                and str(surface["config"].get("source_id") or "").strip()
                == str(reviewed_auto_row.get("source_id") or "").strip()
            ),
            None,
        )
        if isinstance(reviewed_auto_surface, Mapping):
            confidence_corridor["reviewed_auto_abstain_recall_conservative_floor"] = _metric_view(
                reviewed_auto_surface, "abstain_recall"
            ).get("conservative_floor")
            confidence_corridor["reviewed_auto_harmful_allow_conservative_ceiling"] = _metric_view(
                reviewed_auto_surface, "harmful_allow_rate"
            ).get("conservative_ceiling")
    if isinstance(curated_row, Mapping):
        curated_surface = next(
            (
                surface
                for surface in veto_proxy_surfaces
                if isinstance(surface.get("config"), Mapping)
                and str(surface["config"].get("source_id") or "").strip()
                == str(curated_row.get("source_id") or "").strip()
            ),
            None,
        )
        if isinstance(curated_surface, Mapping):
            confidence_corridor["curated_abstain_recall_conservative_floor"] = _metric_view(
                curated_surface, "abstain_recall"
            ).get("conservative_floor")
            confidence_corridor["curated_harmful_allow_conservative_ceiling"] = _metric_view(
                curated_surface, "harmful_allow_rate"
            ).get("conservative_ceiling")

    return {
        "schema_version": 1,
        "status": "ok",
        "pair": "en-es",
        "generated_at": generated_at,
        "methodology": {
            "bootstrap_kind": "cluster_bootstrap_plus_leave_one_cluster_out",
            "bootstrap_iterations": int(bootstrap_iterations),
            "random_seed": int(random_seed),
            "confidence_level": float(confidence_level),
            "fixed_shadow_cluster_key": "family_id",
            "veto_proxy_cluster_key": "trigger",
            "caveats": [
                "Fixed-shadow runtime scorer bounds and veto-proxy blocker bounds are different evaluation surfaces.",
                "The conservative floors and ceilings are intended as current en-es corridor reads, not as fully calibrated production guarantees.",
                "Leave-one-cluster-out stress is included because family sensitivity matters more than optimistic per-row confidence.",
            ],
        },
        "inputs": {
            "sentence_dataset": str(sentence_dataset),
            "benchmark_dataset": str(benchmark_dataset),
            "benchmark_json": str(benchmark_json),
            "family_splits_manifest": str(family_splits_manifest),
            "data_root": str(data_root),
            "forward_seed_max_words": int(forward_seed_max_words),
            "translation_dict": str(translation_dict) if translation_dict else "",
            "reverse_translation_dict": (
                str(reverse_translation_dict) if reverse_translation_dict else ""
            ),
        },
        "fixed_shadow_bounds": fixed_shadow_surfaces,
        "veto_proxy_bounds": veto_proxy_surfaces,
        "confidence_corridor": confidence_corridor,
    }


def main() -> int:
    args = _parse_args()
    report = build_generalization_bound_report(
        sentence_dataset=args.sentence_dataset,
        benchmark_dataset=args.benchmark_dataset,
        benchmark_json=args.benchmark_json,
        family_splits_manifest=args.family_splits_manifest,
        data_root=args.data_root,
        translation_dict=args.translation_dict,
        reverse_translation_dict=args.reverse_translation_dict,
        forward_seed_max_words=max(1, int(args.forward_seed_max_words)),
        bootstrap_iterations=max(1, int(args.bootstrap_iterations)),
        random_seed=int(args.random_seed),
        confidence_level=min(max(float(args.confidence_level), 0.50), 0.999),
        include_sentence_transformer_reference=bool(args.include_sentence_transformer_reference),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_generalization_bound_markdown(
            report,
            fixed_shadow_metric_order=tuple(FIXED_SHADOW_METRIC_DIRECTIONS.keys()),
            veto_proxy_metric_order=tuple(VETO_PROXY_METRIC_DIRECTIONS.keys()),
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
