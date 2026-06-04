from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_shadow_evaluation import (
    evaluate_shadow_inventory_against_benchmark_overlap_gold,
    evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (
    filter_shadow_targets_by_trigger_support,
)
from semantic_shadow_experiment_compare_support import (
    build_candidate_feature_bucket_risk_report,
)
from semantic_shadow_experiment_support import (
    build_overlap_family_generalization_split_summary,
    build_en_es_seed_mode_payloads,
    build_inventory_for_seed_targets,
    build_trigger_row_metadata_from_cases,
    load_en_es_shadow_experiment_resources,
    load_reverse_records_by_source_for_seed_modes,
)

_TRIGGER_FILTER_LABELS = {
    "rulegen_top3_sources",
    "rulegen_all_sources",
    "forward_gloss_fragments",
}
_CORRECT_OUTCOMES = frozenset({"true_abstain", "true_allow"})


def _delta(value: object, baseline: object) -> float | None:
    if not isinstance(value, (float, int)) or not isinstance(baseline, (float, int)):
        return None
    return float(value) - float(baseline)


def _parse_float(value: object, *, default: float) -> float:
    if value in (None, ""):
        return float(default)
    return float(value)


def _parse_int(value: object, *, default: int, minimum: int = 0) -> int:
    if value in (None, ""):
        return max(minimum, int(default))
    return max(minimum, int(value))


def _load_manifest_rows(path: Path) -> dict[str, dict[str, object]]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Experiment manifest must be a JSON object.")
    if str(payload.get("pair") or "").strip() not in ("", "en-es"):
        raise ValueError(
            "The semantic-shadow experiment compare runner currently supports en-es only."
        )
    defaults = payload.get("defaults")
    normalized_defaults = dict(defaults) if isinstance(defaults, Mapping) else {}
    experiments = payload.get("experiments")
    if not isinstance(experiments, Sequence) or isinstance(experiments, (str, bytes)):
        raise ValueError("Experiment manifest must include an `experiments` list.")
    rows: dict[str, dict[str, object]] = {}
    for raw_experiment in experiments:
        if not isinstance(raw_experiment, Mapping):
            continue
        experiment = {**normalized_defaults, **dict(raw_experiment)}
        experiment_id = str(experiment.get("experiment_id") or "").strip()
        seed_mode = str(experiment.get("seed_mode") or "").strip()
        if not experiment_id or not seed_mode:
            raise ValueError("Each experiment row must include `experiment_id` and `seed_mode`.")
        rows[experiment_id] = {
            "experiment_id": experiment_id,
            "label": str(experiment.get("label") or experiment_id),
            "seed_mode": seed_mode,
            "policy": str(experiment.get("policy") or "support_score_v1").strip(),
            "trigger_support_score_min": _parse_float(
                experiment.get("trigger_support_score_min"),
                default=0.0,
            ),
            "support_score_min": _parse_float(
                experiment.get("support_score_min"),
                default=5.0,
            ),
            "support_score_max_promoted": _parse_int(
                experiment.get("support_score_max_promoted"),
                default=2,
                minimum=1,
            ),
            "support_frequency_representative_bonus": _parse_float(
                experiment.get("support_frequency_representative_bonus"),
                default=0.0,
            ),
            "support_frequency_representative_top_k": _parse_int(
                experiment.get("support_frequency_representative_top_k"),
                default=0,
                minimum=0,
            ),
            "support_frequency_similarity_weight": _parse_float(
                experiment.get("support_frequency_similarity_weight"),
                default=0.0,
            ),
            "support_frequency_similarity_tau": _parse_float(
                experiment.get("support_frequency_similarity_tau"),
                default=0.15,
            ),
            "support_representative_pruning_mode": str(
                experiment.get("support_representative_pruning_mode") or "off"
            ).strip(),
            "semantic_bridge_include_aux_text": bool(
                experiment.get("semantic_bridge_include_aux_text")
            ),
            "semantic_bridge_include_examples": bool(
                experiment.get("semantic_bridge_include_examples")
            ),
            "trigger_support_weights": dict(
                experiment.get("trigger_support_weights")
                if isinstance(experiment.get("trigger_support_weights"), Mapping)
                else {}
            ),
            "shadow_support_weights": dict(
                experiment.get("shadow_support_weights")
                if isinstance(experiment.get("shadow_support_weights"), Mapping)
                else {}
            ),
        }
    return rows


def _build_experiment_result(
    *,
    experiment: Mapping[str, object],
    resources: object,
    seed_mode_payloads: Mapping[str, object],
    reverse_records_by_source: Mapping[str, object],
    trigger_row_metadata: Mapping[tuple[str, str], Mapping[str, object]],
    generalization_splits_manifest: Path,
) -> dict[str, object]:
    seed_mode = str(experiment.get("seed_mode") or "")
    payload = seed_mode_payloads.get(seed_mode)
    if not isinstance(payload, object) or payload is None:
        raise ValueError(f"Unknown seed mode for experiment: {seed_mode!r}")

    supports_trigger_filter = bool(
        _TRIGGER_FILTER_LABELS.intersection(payload.source_targets_by_label.keys())
    )
    trigger_support_score_min = float(experiment.get("trigger_support_score_min") or 0.0)
    filtered_seed_targets = list(payload.seed_targets)
    trigger_support_rows: list[dict[str, object]] = []
    if trigger_support_score_min > 0.0:
        if not supports_trigger_filter:
            raise ValueError(
                f"Experiment {experiment.get('experiment_id')!r} requests trigger filtering for "
                f"seed mode {seed_mode!r}, which does not expose filterable source labels."
            )
        filtered_seed_targets, trigger_support_rows = filter_shadow_targets_by_trigger_support(
            seed_targets=payload.seed_targets,
            source_targets_by_label=payload.source_targets_by_label,
            forward_records_by_target=resources.forward_records_by_target,
            reverse_records_by_source=reverse_records_by_source,
            forward_provider=resources.forward_provider,
            reverse_provider=resources.reverse_provider,
            benchmark_target_map={target.target: target for target in resources.benchmark_targets},
            min_score=trigger_support_score_min,
            trigger_support_weights=experiment.get("trigger_support_weights"),
        )

    inventory = build_inventory_for_seed_targets(
        resources,
        seed_targets=filtered_seed_targets,
        reverse_records_by_source=reverse_records_by_source,
        promotion_policy=str(experiment.get("policy") or "support_score_v1"),
        support_score_weights=experiment.get("shadow_support_weights"),
        semantic_bridge_include_aux_text=bool(experiment.get("semantic_bridge_include_aux_text")),
        semantic_bridge_include_examples=bool(experiment.get("semantic_bridge_include_examples")),
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
        include_row_results=True,
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
    veto_row_results = (
        veto_policy.get("row_results", []) if isinstance(veto_policy, Mapping) else []
    )
    split_summary = build_overlap_family_generalization_split_summary(
        veto_row_results,
        manifest_path=generalization_splits_manifest,
    )

    filtered_trigger_count = sum(
        len(target.reviewed_triggers)
        for target in filtered_seed_targets
        if target.reviewed_triggers
    )
    original_trigger_count = sum(
        len(target.reviewed_triggers) for target in payload.seed_targets if target.reviewed_triggers
    )
    return {
        "experiment_id": str(experiment.get("experiment_id") or ""),
        "label": str(experiment.get("label") or ""),
        "seed_mode": seed_mode,
        "policy": policy_id,
        "trigger_support_score_min": trigger_support_score_min,
        "trigger_support_weights": experiment.get("trigger_support_weights"),
        "shadow_support_weights": experiment.get("shadow_support_weights"),
        "support_score_min": float(experiment.get("support_score_min") or 0.0),
        "support_score_max_promoted": int(experiment.get("support_score_max_promoted") or 1),
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
        "gold_candidate_pool_summary": gold_candidate_pool,
        "gold_summary": gold_summary,
        "veto_summary": veto_summary,
        "veto_generalization_split_summary": split_summary,
        "veto_slice_summaries": (
            veto_policy.get("slice_summaries", {}) if isinstance(veto_policy, Mapping) else {}
        ),
        "veto_row_results": veto_row_results,
        "sample_harmful_allow_rows": (
            veto_policy.get("sample_harmful_allow_rows", [])
            if isinstance(veto_policy, Mapping)
            else []
        ),
        "sample_false_abstain_rows": (
            veto_policy.get("sample_false_abstain_rows", [])
            if isinstance(veto_policy, Mapping)
            else []
        ),
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


def _index_row_results(rows: object) -> dict[tuple[str, str], Mapping[str, object]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return {}
    indexed: dict[tuple[str, str], Mapping[str, object]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        key = (str(row.get("target") or "").strip(), str(row.get("trigger") or "").strip())
        if key[0] and key[1]:
            indexed[key] = row
    return indexed


def _is_correct_outcome(outcome: object) -> bool:
    return str(outcome or "").strip() in _CORRECT_OUTCOMES


def _merge_comparison_row(
    *,
    key: tuple[str, str],
    control_row: Mapping[str, object] | None,
    candidate_row: Mapping[str, object] | None,
) -> dict[str, object]:
    anchor = candidate_row if isinstance(candidate_row, Mapping) else control_row or {}
    return {
        "target": key[0],
        "trigger": key[1],
        "gold_shadow_targets": list(anchor.get("gold_shadow_targets", []))
        if isinstance(anchor.get("gold_shadow_targets"), Sequence)
        and not isinstance(anchor.get("gold_shadow_targets"), (str, bytes))
        else [],
        "control_outcome": str(control_row.get("outcome") or "")
        if isinstance(control_row, Mapping)
        else "",
        "candidate_outcome": str(candidate_row.get("outcome") or "")
        if isinstance(candidate_row, Mapping)
        else "",
        "control_promoted_targets": list(control_row.get("promoted_targets", []))
        if isinstance(control_row, Mapping)
        and isinstance(control_row.get("promoted_targets"), Sequence)
        and not isinstance(control_row.get("promoted_targets"), (str, bytes))
        else [],
        "candidate_promoted_targets": list(candidate_row.get("promoted_targets", []))
        if isinstance(candidate_row, Mapping)
        and isinstance(candidate_row.get("promoted_targets"), Sequence)
        and not isinstance(candidate_row.get("promoted_targets"), (str, bytes))
        else [],
        "miss_classification": str(
            candidate_row.get("miss_classification") or control_row.get("miss_classification") or ""
        )
        if isinstance(anchor, Mapping)
        else "",
        "case_ids": list(anchor.get("case_ids", []))
        if isinstance(anchor.get("case_ids"), Sequence)
        and not isinstance(anchor.get("case_ids"), (str, bytes))
        else [],
        "tiers": list(anchor.get("tiers", []))
        if isinstance(anchor.get("tiers"), Sequence)
        and not isinstance(anchor.get("tiers"), (str, bytes))
        else [],
        "slice_tags": list(anchor.get("slice_tags", []))
        if isinstance(anchor.get("slice_tags"), Sequence)
        and not isinstance(anchor.get("slice_tags"), (str, bytes))
        else [],
        "feature_vector": dict(anchor.get("feature_vector", {}))
        if isinstance(anchor.get("feature_vector"), Mapping)
        else {},
        "feature_dimensions": dict(anchor.get("feature_dimensions", {}))
        if isinstance(anchor.get("feature_dimensions"), Mapping)
        else {},
    }


def _compare_row_outcomes(
    *,
    control_rows: Mapping[tuple[str, str], Mapping[str, object]],
    candidate_rows: Mapping[tuple[str, str], Mapping[str, object]],
) -> dict[str, object]:
    improved_rows: list[dict[str, object]] = []
    regressed_rows: list[dict[str, object]] = []
    fixed_harmful_allow_rows: list[dict[str, object]] = []
    introduced_false_abstain_rows: list[dict[str, object]] = []
    persistent_harmful_allow_rows: list[dict[str, object]] = []
    persistent_false_abstain_rows: list[dict[str, object]] = []
    stable_correct = 0
    stable_incorrect = 0

    for key in sorted(set(control_rows.keys()) | set(candidate_rows.keys())):
        control_row = control_rows.get(key)
        candidate_row = candidate_rows.get(key)
        control_outcome = (
            str(control_row.get("outcome") or "") if isinstance(control_row, Mapping) else ""
        )
        candidate_outcome = (
            str(candidate_row.get("outcome") or "") if isinstance(candidate_row, Mapping) else ""
        )
        merged_row = _merge_comparison_row(
            key=key,
            control_row=control_row,
            candidate_row=candidate_row,
        )
        control_correct = _is_correct_outcome(control_outcome)
        candidate_correct = _is_correct_outcome(candidate_outcome)
        if not control_correct and candidate_correct:
            improved_rows.append(merged_row)
        elif control_correct and not candidate_correct:
            regressed_rows.append(merged_row)
        elif control_correct and candidate_correct:
            stable_correct += 1
        else:
            stable_incorrect += 1

        if control_outcome == "harmful_allow" and candidate_outcome == "true_abstain":
            fixed_harmful_allow_rows.append(merged_row)
        if control_outcome == "true_allow" and candidate_outcome == "false_abstain":
            introduced_false_abstain_rows.append(merged_row)
        if control_outcome == "harmful_allow" and candidate_outcome == "harmful_allow":
            persistent_harmful_allow_rows.append(merged_row)
        if control_outcome == "false_abstain" and candidate_outcome == "false_abstain":
            persistent_false_abstain_rows.append(merged_row)

    return {
        "summary": {
            "rows_total": len(set(control_rows.keys()) | set(candidate_rows.keys())),
            "improved_rows": len(improved_rows),
            "regressed_rows": len(regressed_rows),
            "stable_correct_rows": stable_correct,
            "stable_incorrect_rows": stable_incorrect,
            "fixed_harmful_allow_rows": len(fixed_harmful_allow_rows),
            "introduced_false_abstain_rows": len(introduced_false_abstain_rows),
            "persistent_harmful_allow_rows": len(persistent_harmful_allow_rows),
            "persistent_false_abstain_rows": len(persistent_false_abstain_rows),
        },
        "improved_rows": improved_rows,
        "regressed_rows": regressed_rows,
        "fixed_harmful_allow_rows": fixed_harmful_allow_rows,
        "introduced_false_abstain_rows": introduced_false_abstain_rows,
        "persistent_harmful_allow_rows": persistent_harmful_allow_rows,
        "persistent_false_abstain_rows": persistent_false_abstain_rows,
    }


def _build_slice_delta_rows(
    *,
    control_slices: Mapping[str, object],
    candidate_slices: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for slice_key in sorted(set(control_slices.keys()) | set(candidate_slices.keys())):
        control_summary = (
            control_slices.get(slice_key)
            if isinstance(control_slices.get(slice_key), Mapping)
            else {}
        )
        candidate_summary = (
            candidate_slices.get(slice_key)
            if isinstance(candidate_slices.get(slice_key), Mapping)
            else {}
        )
        rows.append(
            {
                "slice_key": slice_key,
                "trigger_rows_total": max(
                    int(control_summary.get("trigger_rows_total") or 0),
                    int(candidate_summary.get("trigger_rows_total") or 0),
                ),
                "ambiguous_trigger_rows": max(
                    int(control_summary.get("ambiguous_trigger_rows") or 0),
                    int(candidate_summary.get("ambiguous_trigger_rows") or 0),
                ),
                "clear_trigger_rows": max(
                    int(control_summary.get("clear_trigger_rows") or 0),
                    int(candidate_summary.get("clear_trigger_rows") or 0),
                ),
                "control_abstain_recall": control_summary.get("abstain_recall"),
                "candidate_abstain_recall": candidate_summary.get("abstain_recall"),
                "delta_abstain_recall": _delta(
                    candidate_summary.get("abstain_recall"),
                    control_summary.get("abstain_recall"),
                ),
                "control_harmful_allow_rate": control_summary.get("harmful_allow_rate"),
                "candidate_harmful_allow_rate": candidate_summary.get("harmful_allow_rate"),
                "delta_harmful_allow_rate": _delta(
                    candidate_summary.get("harmful_allow_rate"),
                    control_summary.get("harmful_allow_rate"),
                ),
                "control_overblocking_rate": control_summary.get("overblocking_rate"),
                "candidate_overblocking_rate": candidate_summary.get("overblocking_rate"),
                "delta_overblocking_rate": _delta(
                    candidate_summary.get("overblocking_rate"),
                    control_summary.get("overblocking_rate"),
                ),
                "control_overall_accuracy": control_summary.get("overall_accuracy"),
                "candidate_overall_accuracy": candidate_summary.get("overall_accuracy"),
                "delta_overall_accuracy": _delta(
                    candidate_summary.get("overall_accuracy"),
                    control_summary.get("overall_accuracy"),
                ),
                "control_harmful_allow_count": int(control_summary.get("harmful_allow_count") or 0),
                "candidate_harmful_allow_count": int(
                    candidate_summary.get("harmful_allow_count") or 0
                ),
                "control_false_abstain_count": int(control_summary.get("false_abstain_count") or 0),
                "candidate_false_abstain_count": int(
                    candidate_summary.get("false_abstain_count") or 0
                ),
            }
        )
    return rows


def _classify_frontier_read(
    *,
    control_result: Mapping[str, object],
    candidate_result: Mapping[str, object],
    row_comparison: Mapping[str, object],
) -> str:
    control_veto = (
        control_result.get("veto_summary")
        if isinstance(control_result.get("veto_summary"), Mapping)
        else {}
    )
    candidate_veto = (
        candidate_result.get("veto_summary")
        if isinstance(candidate_result.get("veto_summary"), Mapping)
        else {}
    )
    summary = (
        row_comparison.get("summary") if isinstance(row_comparison.get("summary"), Mapping) else {}
    )
    accuracy_delta = _delta(
        candidate_veto.get("overall_accuracy"),
        control_veto.get("overall_accuracy"),
    )
    abstain_delta = _delta(
        candidate_veto.get("abstain_recall"),
        control_veto.get("abstain_recall"),
    )
    harmful_delta = _delta(
        candidate_veto.get("harmful_allow_rate"),
        control_veto.get("harmful_allow_rate"),
    )
    overblocking_delta = _delta(
        candidate_veto.get("overblocking_rate"),
        control_veto.get("overblocking_rate"),
    )
    improved_rows = int(summary.get("improved_rows") or 0)
    regressed_rows = int(summary.get("regressed_rows") or 0)
    fixed_harmful = int(summary.get("fixed_harmful_allow_rows") or 0)
    introduced_false = int(summary.get("introduced_false_abstain_rows") or 0)
    if (
        isinstance(accuracy_delta, float)
        and isinstance(abstain_delta, float)
        and isinstance(harmful_delta, float)
        and accuracy_delta > 0.0
        and abstain_delta > 0.0
        and harmful_delta < 0.0
        and improved_rows > regressed_rows
        and fixed_harmful >= introduced_false
        and (overblocking_delta is None or overblocking_delta <= 0.02)
    ):
        return "still_open_meaningful_positive_delta"
    if improved_rows == 0 and regressed_rows == 0:
        return "flat_no_row_level_change"
    if improved_rows > 0 and regressed_rows > 0:
        return "tradeoff_frontier"
    if regressed_rows > improved_rows:
        return "regressive_candidate_row"
    return "mixed_but_positive"


def build_experiment_compare_report(
    *,
    manifest_path: Path,
    benchmark_dataset: Path,
    benchmark_json: Path,
    data_root: Path,
    translation_dict: Path | None,
    reverse_translation_dict: Path | None,
    control_experiment_id: str,
    candidate_experiment_id: str,
    generalization_splits_manifest: Path,
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    manifest_rows = _load_manifest_rows(manifest_path)
    control_row = manifest_rows.get(str(control_experiment_id or "").strip())
    candidate_row = manifest_rows.get(str(candidate_experiment_id or "").strip())
    if not isinstance(control_row, Mapping):
        raise ValueError(f"Unknown control experiment_id: {control_experiment_id!r}")
    if not isinstance(candidate_row, Mapping):
        raise ValueError(f"Unknown candidate experiment_id: {candidate_experiment_id!r}")

    resources = load_en_es_shadow_experiment_resources(
        benchmark_dataset=benchmark_dataset,
        benchmark_json=benchmark_json,
        data_root=data_root,
        translation_dict=translation_dict,
        reverse_translation_dict=reverse_translation_dict,
    )
    seed_mode_payloads = build_en_es_seed_mode_payloads(
        resources,
        forward_seed_max_words=1,
        include_neighbor_borrow_seed_modes=True,
    )
    reverse_records_by_source = load_reverse_records_by_source_for_seed_modes(
        resources,
        tuple(seed_mode_payloads.values()),
    )
    trigger_row_metadata = build_trigger_row_metadata_from_cases(resources.cases)

    control_result = _build_experiment_result(
        experiment=control_row,
        resources=resources,
        seed_mode_payloads=seed_mode_payloads,
        reverse_records_by_source=reverse_records_by_source,
        trigger_row_metadata=trigger_row_metadata,
        generalization_splits_manifest=generalization_splits_manifest,
    )
    candidate_result = _build_experiment_result(
        experiment=candidate_row,
        resources=resources,
        seed_mode_payloads=seed_mode_payloads,
        reverse_records_by_source=reverse_records_by_source,
        trigger_row_metadata=trigger_row_metadata,
        generalization_splits_manifest=generalization_splits_manifest,
    )
    row_comparison = _compare_row_outcomes(
        control_rows=_index_row_results(control_result.get("veto_row_results")),
        candidate_rows=_index_row_results(candidate_result.get("veto_row_results")),
    )
    slice_delta_rows = _build_slice_delta_rows(
        control_slices=(
            control_result.get("veto_slice_summaries")
            if isinstance(control_result.get("veto_slice_summaries"), Mapping)
            else {}
        ),
        candidate_slices=(
            candidate_result.get("veto_slice_summaries")
            if isinstance(candidate_result.get("veto_slice_summaries"), Mapping)
            else {}
        ),
    )
    frontier_read = _classify_frontier_read(
        control_result=control_result,
        candidate_result=candidate_result,
        row_comparison=row_comparison,
    )
    candidate_feature_bucket_risk = build_candidate_feature_bucket_risk_report(
        candidate_result=candidate_result,
        row_comparison=row_comparison,
    )
    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "manifest_path": str(manifest_path),
        "benchmark_dataset": str(benchmark_dataset),
        "benchmark_json": str(benchmark_json),
        "data_root": str(data_root),
        "translation_dict_path": str(translation_dict) if translation_dict is not None else None,
        "reverse_translation_dict_path": (
            str(reverse_translation_dict) if reverse_translation_dict is not None else None
        ),
        "generalization_splits_manifest_path": str(generalization_splits_manifest),
        "forward_pack_path": str(resources.forward_pack.path),
        "reverse_pack_path": str(resources.reverse_pack.path),
        "forward_pack_provider": resources.forward_provider,
        "reverse_pack_provider": resources.reverse_provider,
        "control": control_result,
        "candidate": candidate_result,
        "row_comparison": row_comparison,
        "slice_delta_rows": slice_delta_rows,
        "candidate_feature_bucket_risk": candidate_feature_bucket_risk,
        "frontier_read": frontier_read,
        "gold_precision_delta": _delta(
            candidate_result.get("gold_summary", {}).get("candidate_precision"),
            control_result.get("gold_summary", {}).get("candidate_precision"),
        ),
        "gold_recall_delta": _delta(
            candidate_result.get("gold_summary", {}).get("candidate_recall"),
            control_result.get("gold_summary", {}).get("candidate_recall"),
        ),
        "veto_accuracy_delta": _delta(
            candidate_result.get("veto_summary", {}).get("overall_accuracy"),
            control_result.get("veto_summary", {}).get("overall_accuracy"),
        ),
        "abstain_recall_delta": _delta(
            candidate_result.get("veto_summary", {}).get("abstain_recall"),
            control_result.get("veto_summary", {}).get("abstain_recall"),
        ),
        "harmful_allow_delta": _delta(
            candidate_result.get("veto_summary", {}).get("harmful_allow_rate"),
            control_result.get("veto_summary", {}).get("harmful_allow_rate"),
        ),
        "overblocking_delta": _delta(
            candidate_result.get("veto_summary", {}).get("overblocking_rate"),
            control_result.get("veto_summary", {}).get("overblocking_rate"),
        ),
    }


__all__ = ("build_experiment_compare_report",)
