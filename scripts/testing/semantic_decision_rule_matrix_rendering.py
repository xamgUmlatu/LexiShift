#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: F405

from semantic_decision_rule_matrix_common import *  # noqa: F403
from semantic_decision_rule_matrix_metrics import *  # noqa: F403


def render_decision_rule_matrix_markdown(report: Mapping[str, object]) -> str:
    best = (
        report.get("best_by_constraint")
        if isinstance(report.get("best_by_constraint"), Mapping)
        else {}
    )
    negative = (
        report.get("negative_control_summary")
        if isinstance(report.get("negative_control_summary"), Mapping)
        else {}
    )
    config_rows = _as_mapping_rows(report.get("config_rows"))
    lines = [
        "# en-es Semantic Decision Rule Matrix",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Matrix: `{report.get('matrix_id', '')}`",
        f"- Dataset: `{report.get('dataset_path', '')}`",
        f"- Manifest: `{report.get('manifest_path', '')}`",
        f"- Evaluation suites: `{len(_as_mapping_rows(report.get('evaluation_suites')))}`",
        f"- Config rows: `{report.get('row_count', 0)}`",
        f"- Case score traces: `{report.get('case_result_count', 0)}`",
        f"- Case traces included in JSON: `{not bool(report.get('case_results_omitted'))}`",
        f"- Negative-control sanity: `{negative.get('status', 'unknown')}`",
        "",
        "## Recommendation",
        "",
        str(report.get("recommendation") or ""),
        "",
        "## Best By Constraint",
        "",
    ]
    for key in (
        "incumbent_control",
        "best_overall",
        "best_zero_harm",
        "best_promotable_candidate",
    ):
        row = best.get(key) if isinstance(best.get(key), Mapping) else None
        if row:
            lines.extend(_render_public_config_row(key, row))
            lines.append("")

    source_batches = _as_mapping_rows(report.get("source_evidence_batches"))
    if source_batches:
        lines.extend(["## Source Evidence Batches", ""])
        lines.append("| Path | Rows | Attached Rows | SHA-256 |")
        lines.append("| --- | ---: | ---: | --- |")
        for row in source_batches:
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(row.get("path") or ""),
                        str(int(row.get("row_count") or 0)),
                        str(int(row.get("attached_row_count") or 0)),
                        str(row.get("sha256") or ""),
                    )
                )
                + " |"
            )
        lines.append("")

    source_scopes = _as_mapping_rows(report.get("source_evidence_scopes"))
    if source_scopes:
        lines.extend(["## Source Evidence Scopes", ""])
        lines.append("| Scope | Paths | Attached Rows | Mask | Window |")
        lines.append("| ---: | --- | ---: | --- | ---: |")
        for row in source_scopes:
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(row.get("scope_index") or ""),
                        "<br>".join(str(path) for path in row.get("paths", ()) or ()),
                        str(int(row.get("attached_row_count") or 0)),
                        str(row.get("mask_token") or ""),
                        str(int(row.get("window_tokens") or 0)),
                    )
                )
                + " |"
            )
        lines.append("")

    candidate_rows = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    family_summary = _as_mapping_rows(report.get("family_bakeoff_summary"))
    if family_summary:
        lines.extend(["## Algorithm Family Winners", ""])
        lines.append(
            "| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |"
        )
        lines.append("| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |")
        for row in family_summary:
            best_row = row.get("best_row") if isinstance(row.get("best_row"), Mapping) else {}
            zero_harm = (
                row.get("best_zero_harm_row")
                if isinstance(row.get("best_zero_harm_row"), Mapping)
                else {}
            )
            display_row = zero_harm or best_row
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(row.get("algorithm_family") or ""),
                        str(int(row.get("config_count") or 0)),
                        str(best_row.get("config_id") or ""),
                        str(zero_harm.get("config_id") or ""),
                        str(int(display_row.get("harmful_replace_count") or 0)),
                        str(int(display_row.get("false_abstain_count") or 0)),
                        _render_rate(display_row.get("winner_accuracy")),
                        f"{float(display_row.get('objective_score') or 0.0):.4f}",
                    )
                )
                + " |"
            )
        lines.append("")

    if len(_as_mapping_rows(report.get("evaluation_suites"))) > 1:
        lines.extend(["## Evaluation Suite Breakdown", ""])
        lines.append("| Config | Suite | Cases | Harmful | False Abstain | Accuracy |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: |")
        for config in candidate_rows[:8]:
            for suite_row in _as_mapping_rows(config.get("suite_breakdown")):
                summary = _breakdown_summary(suite_row)
                lines.append(
                    "| "
                    + " | ".join(
                        (
                            str(config.get("config_id") or ""),
                            str(suite_row.get("suite_id") or ""),
                            str(int(summary.get("cases_total") or 0)),
                            str(int(summary.get("harmful_replace_count") or 0)),
                            str(int(summary.get("false_abstain_count") or 0)),
                            _render_rate(summary.get("decision_accuracy")),
                        )
                    )
                    + " |"
                )
        lines.append("")

    signature_summary = (
        report.get("decision_signature_summary")
        if isinstance(report.get("decision_signature_summary"), Mapping)
        else {}
    )
    if signature_summary:
        lines.extend(["## Decision Signature Clusters", ""])
        lines.append(
            f"- Unique replace signatures: `{signature_summary.get('unique_replace_signature_count', 0)}`"
        )
        lines.append(
            f"- Largest replace-signature cluster: `{signature_summary.get('largest_replace_signature_size', 0)}` configs"
        )
        for row in _as_mapping_rows(signature_summary.get("top_replace_signature_clusters"))[:5]:
            lines.append(
                "- "
                f"`{row.get('signature', '')}`: `{int(row.get('config_count') or 0)}` configs, "
                f"sample `{', '.join(str(value) for value in row.get('sample_config_ids', ()))}`"
            )
        lines.append("")

    tie_summary = (
        report.get("metric_tie_summary")
        if isinstance(report.get("metric_tie_summary"), Mapping)
        else {}
    )
    if tie_summary:
        lines.extend(["## Headline Metric Ties", ""])
        lines.append(f"- Tied primary-metric groups: `{tie_summary.get('tied_group_count', 0)}`")
        lines.append(
            f"- Largest tied group: `{tie_summary.get('largest_tied_group_size', 0)}` configs"
        )
        for row in _as_mapping_rows(tie_summary.get("top_tied_groups"))[:8]:
            lines.append(
                "- "
                f"`{row.get('metric_signature', '')}`: `{int(row.get('config_count') or 0)}` "
                f"configs, unique replace signatures "
                f"`{int(row.get('unique_replace_signature_count') or 0)}`, "
                f"ROC AUC `{_render_range(row.get('roc_auc_min'), row.get('roc_auc_max'))}`, "
                f"Avg Prec. `{_render_range(row.get('average_precision_min'), row.get('average_precision_max'))}`"
            )
        lines.append("")

    selection_summary = (
        report.get("selection_validation_summary")
        if isinstance(report.get("selection_validation_summary"), Mapping)
        else {}
    )
    if selection_summary:
        lines.extend(["## Discovery Selection vs Locked Eval", ""])
        lines.append(f"- Policy: {selection_summary.get('selection_policy', '')}")
        lines.append(
            "| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |"
        )
        lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
        for row in _as_mapping_rows(selection_summary.get("rows")):
            selected = (
                row.get("selected_on_discovery")
                if isinstance(row.get("selected_on_discovery"), Mapping)
                else {}
            )
            oracle = (
                row.get("locked_oracle") if isinstance(row.get("locked_oracle"), Mapping) else {}
            )
            discovery = (
                selected.get("discovery") if isinstance(selected.get("discovery"), Mapping) else {}
            )
            locked = (
                selected.get("locked_eval")
                if isinstance(selected.get("locked_eval"), Mapping)
                else {}
            )
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(row.get("algorithm_family") or ""),
                        str(selected.get("config_id") or ""),
                        str(int(discovery.get("harmful_replace_count") or 0)),
                        str(int(discovery.get("false_abstain_count") or 0)),
                        str(int(locked.get("harmful_replace_count") or 0)),
                        str(int(locked.get("false_abstain_count") or 0)),
                        _render_float(locked.get("objective_score")),
                        str(oracle.get("config_id") or ""),
                    )
                )
                + " |"
            )
        lines.append("")

    delta_summary = (
        report.get("incumbent_delta_summary")
        if isinstance(report.get("incumbent_delta_summary"), Mapping)
        else {}
    )
    if delta_summary:
        lines.extend(["## Incumbent Case Deltas", ""])
        lines.append(f"- Incumbent config: `{delta_summary.get('incumbent_config_id', '')}`")
        lines.append(
            f"- Configs identical to incumbent decisions: `{delta_summary.get('identical_decision_count', 0)}`"
        )
        for row in _as_mapping_rows(delta_summary.get("top_delta_rows"))[:8]:
            lines.append(
                "- "
                f"`{row.get('config_id', '')}`: decisions changed "
                f"`{int(row.get('decision_changed_count') or 0)}`, "
                f"false abstains fixed/introduced "
                f"`{int(row.get('false_abstain_fixed_count') or 0)}`/"
                f"`{int(row.get('false_abstain_introduced_count') or 0)}`, "
                f"harmful fixed/introduced "
                f"`{int(row.get('harmful_fixed_count') or 0)}`/"
                f"`{int(row.get('harmful_introduced_count') or 0)}`"
            )
        lines.append("")

    lines.extend(["## Top Candidate Configs", ""])
    lines.append(
        "| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |"
    )
    lines.append(
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    for index, row in enumerate(candidate_rows[:20], start=1):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(index),
                    str(row.get("algorithm_family") or ""),
                    str(row.get("config_id") or ""),
                    str(row.get("scorer_id") or ""),
                    str(row.get("context_view") or ""),
                    str(row.get("sense_representation") or ""),
                    str(row.get("aggregation_rule") or ""),
                    str(row.get("decision_rule") or ""),
                    str(row.get("phrase_handling") or ""),
                    str(row.get("evidence_control") or ""),
                    str(int(row.get("harmful_replace_count") or 0)),
                    str(int(row.get("false_abstain_count") or 0)),
                    _render_rate(row.get("winner_accuracy")),
                    _render_float(row.get("ranking_roc_auc")),
                    _render_float(row.get("ranking_average_precision")),
                    f"{float(row.get('objective_score') or 0.0):.4f}",
                )
            )
            + " |"
        )

    negative_rows = _as_mapping_rows(negative.get("rows"))
    if negative_rows:
        lines.extend(["", "## Negative Controls", ""])
        for row in negative_rows:
            lines.append(
                "- "
                f"`{row.get('config_id', '')}`: `{row.get('status', '')}` "
                f"({row.get('expected_failure_mode', '')}; "
                f"harmful `{int(row.get('harmful_replace_count') or 0)}`, "
                f"false abstain `{int(row.get('false_abstain_count') or 0)}`, "
                f"accuracy `{_render_rate(row.get('decision_accuracy'))}`)"
            )

    overfit = (
        report.get("overfitting_checks")
        if isinstance(report.get("overfitting_checks"), Mapping)
        else {}
    )
    lines.extend(["", "## Overfitting Checks", ""])
    lines.append(
        f"- Split policy: `{overfit.get('split_policy', '')}` "
        f"(locked remainders `{overfit.get('locked_eval_remainders', [])}`)"
    )
    for row in _as_mapping_rows(overfit.get("rows"))[:10]:
        lines.append(
            "- "
            f"`{row.get('config_id', '')}`: discovery objective "
            f"`{_render_float(row.get('discovery_objective_score'))}`, locked objective "
            f"`{_render_float(row.get('locked_eval_objective_score'))}`, "
            f"worst leave-one-family objective "
            f"`{_render_float(row.get('worst_leave_one_family_objective_score'))}`"
        )

    threshold_rows = _as_mapping_rows(report.get("threshold_sensitivity"))
    if threshold_rows:
        lines.extend(["", "## Threshold Sensitivity", ""])
        for row in threshold_rows[:20]:
            lines.append(
                "- "
                f"`{row.get('config_id', '')}` {row.get('threshold_label', '')}: "
                f"harmful `{int(row.get('harmful_replace_count') or 0)}`, "
                f"false abstain `{int(row.get('false_abstain_count') or 0)}`, "
                f"objective `{_render_float(row.get('objective_score'))}`"
            )

    dropout_rows = _as_mapping_rows(report.get("source_dropout"))
    if dropout_rows:
        lines.extend(["", "## Source-Family Dropout", ""])
        for row in dropout_rows[:20]:
            lines.append(
                "- "
                f"`{row.get('config_id', '')}` drop `{row.get('dropped_source_family', '')}`: "
                f"harmful `{int(row.get('harmful_replace_count') or 0)}`, "
                f"false abstain `{int(row.get('false_abstain_count') or 0)}`, "
                f"objective `{_render_float(row.get('objective_score'))}`"
            )
    return "\n".join(lines).rstrip() + "\n"
