#!/usr/bin/env python3
from __future__ import annotations

from typing import Mapping, Sequence

from semantic_routing_sentence_veto_reporting_tables import (
    _build_family_breakdown_label,
    _normalize_string_list,
    _render_rate,
    _render_rate_metric,
    _render_sentence_veto_breakdown_table,
    _render_sentence_veto_ladder_row,
    _render_sentence_veto_sweep_row,
)


def render_sentence_veto_markdown(report: Mapping[str, object]) -> str:
    config = report.get("config") if isinstance(report.get("config"), Mapping) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# Semantic Routing Sentence Veto Harness",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_path', '')}`",
        f"- Pair: `{report.get('pair', '')}`",
        f"- Scorer: `{config.get('scorer_id', '')}`",
        f"- Model: `{config.get('model_name', '') or 'n/a'}`",
        f"- Context view: `{config.get('context_view', '')}`",
        f"- Evidence view: `{config.get('evidence_view', '')}`",
        f"- Phrase control mode: `{config.get('phrase_control_mode', 'off')}`",
        f"- Phrase guard POS scope: `{config.get('phrase_guard_pos_scope', 'family_all')}`",
        f"- Active rescue mode: `{config.get('active_rescue_mode', 'off')}`",
        f"- Thresholds: `min_active={config.get('min_active_score', '')}`, `min_margin={config.get('min_margin', '')}`",
        "",
        "## Summary",
        "",
        f"- Decision accuracy: `{_render_rate(summary.get('decision_accuracy'))}`",
        f"- Replace precision / recall: `{_render_rate(summary.get('replace_precision'))}` / `{_render_rate(summary.get('replace_recall'))}`",
        f"- Harmful replace / false abstain: `{_render_rate(summary.get('harmful_replace_rate'))}` / `{_render_rate(summary.get('false_abstain_rate'))}`",
        f"- Winner accuracy / shadow-winner accuracy: `{_render_rate(summary.get('winner_accuracy'))}` / `{_render_rate(summary.get('shadow_winner_accuracy'))}`",
        f"- Predicted replace rate: `{_render_rate(summary.get('predicted_replace_rate'))}`",
        f"- Phrase preemption hit rate / precision: `{_render_rate(summary.get('phrase_preemption_hit_rate'))}` / `{_render_rate(summary.get('phrase_preemption_precision'))}`",
        f"- Active rescue applied rate / precision: `{_render_rate(summary.get('active_rescue_applied_rate'))}` / `{_render_rate(summary.get('active_rescue_precision'))}`",
        "",
        "## Family Breakdown",
        "",
    ]
    lines.extend(
        _render_sentence_veto_breakdown_table(
            report.get("family_breakdown"),
            label_key="family_id",
            label_builder=_build_family_breakdown_label,
        )
    )
    lines.extend(["", "## Gold Winner Type Breakdown", ""])
    lines.extend(
        _render_sentence_veto_breakdown_table(
            report.get("gold_winner_type_breakdown"),
            label_key="gold_winner_type",
        )
    )
    lines.extend(["", "## Slice Tag Breakdown", ""])
    lines.extend(
        _render_sentence_veto_breakdown_table(
            report.get("slice_tag_breakdown"),
            label_key="slice_tag",
            limit=12,
        )
    )
    lines.extend(["", "## Failure Samples", ""])
    lines.extend(
        _render_sentence_veto_failure_block(
            "Harmful replace", report.get("sample_harmful_replace_rows")
        )
    )
    lines.extend(
        _render_sentence_veto_failure_block(
            "False abstain", report.get("sample_false_abstain_rows")
        )
    )
    lines.extend(
        _render_sentence_veto_failure_block("Winner errors", report.get("sample_winner_error_rows"))
    )
    return "\n".join(lines) + "\n"


def render_sentence_veto_sweep_markdown(report: Mapping[str, object]) -> str:
    grid = report.get("grid") if isinstance(report.get("grid"), Mapping) else {}
    best_row = report.get("best_row") if isinstance(report.get("best_row"), Mapping) else {}
    best_objective_row = (
        report.get("best_objective_row")
        if isinstance(report.get("best_objective_row"), Mapping)
        else {}
    )
    best_rows_by_harmful_replace_budget = (
        report.get("best_rows_by_harmful_replace_budget")
        if isinstance(report.get("best_rows_by_harmful_replace_budget"), Sequence)
        and not isinstance(report.get("best_rows_by_harmful_replace_budget"), (str, bytes))
        else []
    )
    best_by_scorer = (
        report.get("best_by_scorer")
        if isinstance(report.get("best_by_scorer"), Sequence)
        and not isinstance(report.get("best_by_scorer"), (str, bytes))
        else []
    )
    rows = (
        report.get("rows")
        if isinstance(report.get("rows"), Sequence)
        and not isinstance(report.get("rows"), (str, bytes))
        else []
    )
    lines = [
        "# Semantic Routing Sentence Veto Sweep",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_path', '')}`",
        f"- Pair: `{report.get('pair', '')}`",
        f"- Grid size: `{report.get('row_count', 0)}`",
        f"- Scorers: `{', '.join(str(value) for value in grid.get('scorers', ()))}`",
        f"- Context views: `{', '.join(str(value) for value in grid.get('context_views', ()))}`",
        f"- Evidence views: `{', '.join(str(value) for value in grid.get('evidence_views', ()))}`",
        f"- Phrase control modes: `{', '.join(str(value) for value in grid.get('phrase_control_modes', ()))}`",
        f"- Phrase guard POS scopes: `{', '.join(str(value) for value in grid.get('phrase_guard_pos_scopes', ()))}`",
        f"- Active rescue modes: `{', '.join(str(value) for value in grid.get('active_rescue_modes', ()))}`",
        "",
        "## Best Overall",
        "",
    ]
    if best_row:
        lines.extend(_render_sentence_veto_sweep_row(best_row))
    lines.extend(["", "## Best By Harmful-Replace Budget", ""])
    for budget_entry in best_rows_by_harmful_replace_budget[:10]:
        if not isinstance(budget_entry, Mapping):
            continue
        budget_row = budget_entry.get("row")
        if not isinstance(budget_row, Mapping):
            continue
        lines.append(
            f"- Budget: `harmful_replace_count <= {int(budget_entry.get('harmful_replace_budget') or 0)}`"
        )
        lines.extend(_render_sentence_veto_sweep_row(budget_row))
        lines.append("")
    lines.extend(["## Best Objective", ""])
    if best_objective_row:
        lines.extend(_render_sentence_veto_sweep_row(best_objective_row))
        lines.append("")
    lines.extend(["", "## Best By Scorer", ""])
    for row in best_by_scorer[:10]:
        lines.extend(_render_sentence_veto_sweep_row(row))
        lines.append("")
    lines.extend(["## Top Configs", ""])
    lines.append(
        "| Rank | Scorer | Context | Evidence | Phrase Mode | POS Scope | Rescue Mode | min_active | min_margin | Harmful Cnt | Phrase Hits | Rescue Hits | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |"
    )
    lines.append(
        "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    for index, row in enumerate(rows[:12], start=1):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(index),
                    str(row.get("scorer_id") or ""),
                    str(row.get("context_view") or ""),
                    str(row.get("evidence_view") or ""),
                    str(row.get("phrase_control_mode") or "off"),
                    str(row.get("phrase_guard_pos_scope") or "family_all"),
                    str(row.get("active_rescue_mode") or "off"),
                    f"{float(row.get('min_active_score') or 0.0):.2f}",
                    f"{float(row.get('min_margin') or 0.0):.2f}",
                    str(int(row.get("harmful_replace_count") or 0)),
                    str(int(row.get("phrase_preemption_hit_count") or 0)),
                    str(int(row.get("active_rescue_applied_count") or 0)),
                    _render_rate(row.get("decision_accuracy")),
                    _render_rate(row.get("harmful_replace_rate")),
                    _render_rate(row.get("false_abstain_rate")),
                    _render_rate(row.get("winner_accuracy")),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def render_sentence_veto_ladder_markdown(report: Mapping[str, object]) -> str:
    base_config = (
        report.get("base_config") if isinstance(report.get("base_config"), Mapping) else {}
    )
    base_summary = (
        report.get("base_summary") if isinstance(report.get("base_summary"), Mapping) else {}
    )
    best_row = report.get("best_row") if isinstance(report.get("best_row"), Mapping) else {}
    best_rows_by_soft_false_positive_budget = (
        report.get("best_rows_by_soft_false_positive_budget")
        if isinstance(report.get("best_rows_by_soft_false_positive_budget"), Sequence)
        and not isinstance(report.get("best_rows_by_soft_false_positive_budget"), (str, bytes))
        else []
    )
    rows = (
        report.get("rows")
        if isinstance(report.get("rows"), Sequence)
        and not isinstance(report.get("rows"), (str, bytes))
        else []
    )
    lines = [
        "# Semantic Routing Sentence Veto Decision Ladder",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_path', '')}`",
        f"- Pair: `{report.get('pair', '')}`",
        f"- Base scorer: `{base_config.get('scorer_id', '')}`",
        f"- Base context / evidence: `{base_config.get('context_view', '')}` / `{base_config.get('evidence_view', '')}`",
        f"- Base phrase / rescue: `{base_config.get('phrase_control_mode', 'off')}` / `{base_config.get('active_rescue_mode', 'off')}`",
        f"- Base hard thresholds: `min_active={base_config.get('min_active_score', '')}`, `min_margin={base_config.get('min_margin', '')}`",
        "",
        "## Frozen Hard-Replace Baseline",
        "",
        f"- Hard replace precision / recall: `{_render_rate(base_summary.get('replace_precision'))}` / `{_render_rate(base_summary.get('replace_recall'))}`",
        f"- Hard harmful replace / false abstain: `{_render_rate(base_summary.get('harmful_replace_rate'))}` / `{_render_rate(base_summary.get('false_abstain_rate'))}`",
        "",
        "## Best Overall",
        "",
    ]
    if best_row:
        lines.extend(_render_sentence_veto_ladder_row(best_row))
    lines.extend(["", "## Best By Soft-False-Positive Budget", ""])
    for budget_entry in best_rows_by_soft_false_positive_budget[:10]:
        if not isinstance(budget_entry, Mapping):
            continue
        budget_row = budget_entry.get("row")
        if not isinstance(budget_row, Mapping):
            continue
        lines.append(
            f"- Budget: `soft_false_positive_count <= {int(budget_entry.get('soft_false_positive_budget') or 0)}`"
        )
        lines.extend(_render_sentence_veto_ladder_row(budget_row))
        lines.append("")
    lines.extend(["## Top Configs", ""])
    lines.append(
        "| Rank | soft_active | soft_margin | Soft Cnt | Soft True | Soft False | Replace+Soft Recall | Recall Lift | Soft Precision | Soft Noise | Surfaced Precision | Missed Replace |"
    )
    lines.append(
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    for index, row in enumerate(rows[:12], start=1):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(index),
                    f"{float(row.get('soft_min_active_score') or 0.0):.2f}",
                    f"{float(row.get('soft_min_margin') or 0.0):.2f}",
                    str(int(row.get("soft_affordance_count") or 0)),
                    str(int(row.get("soft_true_positive_count") or 0)),
                    str(int(row.get("soft_false_positive_count") or 0)),
                    _render_rate(row.get("replace_or_soft_recall")),
                    _render_rate(row.get("replace_or_soft_recall_lift")),
                    _render_rate(row.get("soft_precision")),
                    _render_rate(row.get("soft_noise_rate")),
                    _render_rate(row.get("surfaced_precision")),
                    str(int(row.get("remaining_missed_replace_count") or 0)),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def render_sentence_veto_weak_active_probe_markdown(report: Mapping[str, object]) -> str:
    base_config = (
        report.get("base_config") if isinstance(report.get("base_config"), Mapping) else {}
    )
    configurations = (
        report.get("configurations")
        if isinstance(report.get("configurations"), Sequence)
        and not isinstance(report.get("configurations"), (str, bytes))
        else []
    )
    overlay_candidates = (
        report.get("overlay_candidates")
        if isinstance(report.get("overlay_candidates"), Sequence)
        and not isinstance(report.get("overlay_candidates"), (str, bytes))
        else []
    )
    focus_case_ids = _normalize_string_list(report.get("focus_case_ids"))
    lines = [
        "# Semantic Routing Sentence Veto Weak-Active Probe",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_path', '')}`",
        f"- Pair: `{report.get('pair', '')}`",
        f"- Focus slice tags: `{', '.join(_normalize_string_list(report.get('focus_slice_tags')) or ['n/a'])}`",
        f"- Focus cases: `{', '.join(focus_case_ids or ['n/a'])}`",
        f"- Base scorer: `{base_config.get('scorer_id', '')}`",
        f"- Base context / evidence: `{base_config.get('context_view', '')}` / `{base_config.get('evidence_view', '')}`",
        f"- Selected overlay: `{report.get('selected_overlay_label', '') or 'n/a'}`",
        f"- Zero-harm overlay available: `{'yes' if bool(report.get('zero_harmful_overlay_available')) else 'no'}`",
        "",
        "## Configuration Summary",
        "",
        "| Config | Kind | Harmful | False Abstain | Replace Recall | Decision Acc. | Winner Acc. | Rescue Cases |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for raw_config in configurations:
        if not isinstance(raw_config, Mapping):
            continue
        summary = (
            raw_config.get("summary") if isinstance(raw_config.get("summary"), Mapping) else {}
        )
        rescue_case_ids = _normalize_string_list(raw_config.get("active_rescue_case_ids"))
        lines.append(
            "| "
            + " | ".join(
                (
                    str(raw_config.get("label") or raw_config.get("config_id") or ""),
                    str(raw_config.get("kind") or ""),
                    str(int(summary.get("harmful_replace_count") or 0)),
                    str(int(summary.get("false_abstain_count") or 0)),
                    _render_rate(summary.get("replace_recall")),
                    _render_rate(summary.get("decision_accuracy")),
                    _render_rate(summary.get("winner_accuracy")),
                    ", ".join(f"`{case_id}`" for case_id in rescue_case_ids) or "none",
                )
            )
            + " |"
        )
    if len(lines) <= 12:
        lines.append("| none | n/a | 0 | 0 | n/a | n/a | n/a | none |")
    lines.extend(["", "## Overlay Sweep", ""])
    lines.append(
        "| Rank | Primary Margin Floor | Backup Margin Floor | Harmful | False Abstain | Replace Recall | Decision Acc. | Rescue Cases |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for index, raw_row in enumerate(overlay_candidates[:8], start=1):
        if not isinstance(raw_row, Mapping):
            continue
        summary = raw_row.get("summary") if isinstance(raw_row.get("summary"), Mapping) else {}
        rescue_case_ids = _normalize_string_list(raw_row.get("active_rescue_case_ids"))
        lines.append(
            "| "
            + " | ".join(
                (
                    str(index),
                    f"{float(raw_row.get('primary_margin_floor') or 0.0):.2f}",
                    f"{float(raw_row.get('backup_margin_floor') or 0.0):.2f}",
                    str(int(summary.get("harmful_replace_count") or 0)),
                    str(int(summary.get("false_abstain_count") or 0)),
                    _render_rate(summary.get("replace_recall")),
                    _render_rate(summary.get("decision_accuracy")),
                    ", ".join(f"`{case_id}`" for case_id in rescue_case_ids) or "none",
                )
            )
            + " |"
        )
    if len(overlay_candidates) <= 0:
        lines.append("| none | n/a | n/a | 0 | 0 | n/a | n/a | none |")
    lines.extend(["", "## Focus Case Outcomes", ""])
    lines.append("| Config | Case | Gold | Predicted | Margin | Backup Margin | Rescue |")
    lines.append("| --- | --- | --- | --- | ---: | ---: | --- |")
    for raw_config in configurations:
        if not isinstance(raw_config, Mapping):
            continue
        focus_cases = (
            raw_config.get("focus_cases")
            if isinstance(raw_config.get("focus_cases"), Sequence)
            and not isinstance(raw_config.get("focus_cases"), (str, bytes))
            else []
        )
        for case in focus_cases:
            if not isinstance(case, Mapping):
                continue
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(raw_config.get("config_id") or ""),
                        str(case.get("case_id") or ""),
                        str(case.get("gold_decision") or ""),
                        str(case.get("predicted_decision") or ""),
                        _render_rate_metric(case.get("margin")),
                        _render_rate_metric(case.get("active_rescue_backup_margin")),
                        "yes" if bool(case.get("active_rescue_applied")) else "no",
                    )
                )
                + " |"
            )
    lines.extend(["", "## Configuration Notes", ""])
    for raw_config in configurations:
        if not isinstance(raw_config, Mapping):
            continue
        lines.append(f"### {raw_config.get('label', raw_config.get('config_id', ''))}")
        lines.append("")
        lines.append(f"- Description: {raw_config.get('description', '')}")
        lines.append(
            "- Harmful replace cases: "
            + (
                ", ".join(
                    f"`{case_id}`"
                    for case_id in _normalize_string_list(
                        raw_config.get("harmful_replace_case_ids")
                    )
                )
                or "none"
            )
        )
        lines.append(
            "- False abstain cases: "
            + (
                ", ".join(
                    f"`{case_id}`"
                    for case_id in _normalize_string_list(raw_config.get("false_abstain_case_ids"))
                )
                or "none"
            )
        )
        lines.append("")
    return "\n".join(lines) + "\n"


def render_sentence_veto_phrase_leak_probe_markdown(report: Mapping[str, object]) -> str:
    base_config = (
        report.get("base_config") if isinstance(report.get("base_config"), Mapping) else {}
    )
    hard_row_entries = (
        report.get("hard_row_entries")
        if isinstance(report.get("hard_row_entries"), Sequence)
        and not isinstance(report.get("hard_row_entries"), (str, bytes))
        else []
    )
    overlay_entries = (
        report.get("overlay_entries")
        if isinstance(report.get("overlay_entries"), Sequence)
        and not isinstance(report.get("overlay_entries"), (str, bytes))
        else []
    )
    focus_case_ids = _normalize_string_list(report.get("focus_case_ids"))
    lines = [
        "# Semantic Routing Sentence Veto Phrase-Leak Probe",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_path', '')}`",
        f"- Pair: `{report.get('pair', '')}`",
        f"- Focus cases: `{', '.join(focus_case_ids or ['n/a'])}`",
        f"- Base scorer: `{base_config.get('scorer_id', '')}`",
        f"- Base context / evidence: `{base_config.get('context_view', '')}` / `{base_config.get('evidence_view', '')}`",
        "",
        "## Hard-Row Comparison",
        "",
        "| Config | POS Scope | Harmful | False Abstain | Replace Recall | Decision Acc. | Phrase Hits | Rescue Cases |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for raw_config in hard_row_entries:
        if not isinstance(raw_config, Mapping):
            continue
        summary = (
            raw_config.get("summary") if isinstance(raw_config.get("summary"), Mapping) else {}
        )
        config = raw_config.get("config") if isinstance(raw_config.get("config"), Mapping) else {}
        rescue_case_ids = _normalize_string_list(raw_config.get("active_rescue_case_ids"))
        lines.append(
            "| "
            + " | ".join(
                (
                    str(raw_config.get("label") or raw_config.get("config_id") or ""),
                    str(config.get("phrase_guard_pos_scope") or "family_all"),
                    str(int(summary.get("harmful_replace_count") or 0)),
                    str(int(summary.get("false_abstain_count") or 0)),
                    _render_rate(summary.get("replace_recall")),
                    _render_rate(summary.get("decision_accuracy")),
                    str(int(summary.get("phrase_preemption_hit_count") or 0)),
                    ", ".join(f"`{case_id}`" for case_id in rescue_case_ids) or "none",
                )
            )
            + " |"
        )
    lines.extend(["", "## Hard-Row Delta", ""])
    lines.extend(_render_sentence_veto_phrase_leak_delta(report.get("hard_row_delta")))
    lines.extend(["", "## Overlay Comparison", ""])
    lines.append(
        "| Config | POS Scope | Harmful | False Abstain | Replace Recall | Decision Acc. | Phrase Hits | Rescue Cases |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for raw_config in overlay_entries:
        if not isinstance(raw_config, Mapping):
            continue
        summary = (
            raw_config.get("summary") if isinstance(raw_config.get("summary"), Mapping) else {}
        )
        config = raw_config.get("config") if isinstance(raw_config.get("config"), Mapping) else {}
        rescue_case_ids = _normalize_string_list(raw_config.get("active_rescue_case_ids"))
        lines.append(
            "| "
            + " | ".join(
                (
                    str(raw_config.get("label") or raw_config.get("config_id") or ""),
                    str(config.get("phrase_guard_pos_scope") or "family_all"),
                    str(int(summary.get("harmful_replace_count") or 0)),
                    str(int(summary.get("false_abstain_count") or 0)),
                    _render_rate(summary.get("replace_recall")),
                    _render_rate(summary.get("decision_accuracy")),
                    str(int(summary.get("phrase_preemption_hit_count") or 0)),
                    ", ".join(f"`{case_id}`" for case_id in rescue_case_ids) or "none",
                )
            )
            + " |"
        )
    lines.extend(["", "## Overlay Delta", ""])
    lines.extend(_render_sentence_veto_phrase_leak_delta(report.get("overlay_delta")))
    lines.extend(["", "## Focus Case Outcomes", ""])
    lines.append("| Config | Case | Gold | Predicted | Phrase | Reason | Rescue |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for raw_config in [*hard_row_entries, *overlay_entries]:
        if not isinstance(raw_config, Mapping):
            continue
        focus_cases = (
            raw_config.get("focus_cases")
            if isinstance(raw_config.get("focus_cases"), Sequence)
            and not isinstance(raw_config.get("focus_cases"), (str, bytes))
            else []
        )
        for case in focus_cases:
            if not isinstance(case, Mapping):
                continue
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(raw_config.get("config_id") or ""),
                        str(case.get("case_id") or ""),
                        str(case.get("gold_decision") or ""),
                        str(case.get("predicted_decision") or ""),
                        "yes" if bool(case.get("phrase_preemption_hit")) else "no",
                        str(case.get("phrase_reason_code") or ""),
                        "yes" if bool(case.get("active_rescue_applied")) else "no",
                    )
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def _render_sentence_veto_phrase_leak_delta(delta: object) -> list[str]:
    if not isinstance(delta, Mapping):
        return ["- no delta available"]
    changed_rows = (
        delta.get("changed_decision_rows")
        if isinstance(delta.get("changed_decision_rows"), Sequence)
        and not isinstance(delta.get("changed_decision_rows"), (str, bytes))
        else []
    )
    new_phrase_rows = (
        delta.get("new_phrase_preemption_rows")
        if isinstance(delta.get("new_phrase_preemption_rows"), Sequence)
        and not isinstance(delta.get("new_phrase_preemption_rows"), (str, bytes))
        else []
    )
    lines = [
        "- Changed decision cases: "
        + (
            ", ".join(
                f"`{str(row.get('case_id') or '')}`"
                for row in changed_rows
                if str(row.get("case_id") or "").strip()
            )
            or "none"
        )
    ]
    for raw_row in changed_rows:
        if not isinstance(raw_row, Mapping):
            continue
        lines.append(
            f"  - `{raw_row.get('case_id', '')}`: "
            f"`{raw_row.get('baseline_predicted_decision', '')}` -> "
            f"`{raw_row.get('candidate_predicted_decision', '')}` | "
            f"phrase `{raw_row.get('baseline_phrase_reason_code', '')}` -> "
            f"`{raw_row.get('candidate_phrase_reason_code', '')}`"
        )
    lines.append(
        "- Newly phrase-preempted without decision change: "
        + (
            ", ".join(
                f"`{str(row.get('case_id') or '')}`"
                for row in new_phrase_rows
                if str(row.get("case_id") or "").strip()
            )
            or "none"
        )
    )
    return lines


def compute_sentence_veto_objective(row: Mapping[str, object]) -> float:
    return (
        coerce_metric(row.get("decision_accuracy"), default=0.0)
        + coerce_metric(row.get("replace_precision"), default=0.0)
        + coerce_metric(row.get("replace_recall"), default=0.0)
        + coerce_metric(row.get("winner_accuracy"), default=0.0)
        - (2.0 * coerce_metric(row.get("harmful_replace_rate"), default=0.0))
        - coerce_metric(row.get("false_abstain_rate"), default=0.0)
    )


def sentence_veto_sweep_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        coerce_metric(row.get("harmful_replace_rate"), default=1.0),
        int(row.get("harmful_replace_count") or 0),
        coerce_metric(row.get("false_abstain_rate"), default=1.0),
        -coerce_metric(row.get("decision_accuracy"), default=0.0),
        -coerce_metric(row.get("winner_accuracy"), default=0.0),
        -coerce_metric(row.get("shadow_winner_accuracy"), default=0.0),
        -coerce_metric(row.get("replace_precision"), default=0.0),
        -coerce_metric(row.get("replace_recall"), default=0.0),
        str(row.get("scorer_id") or ""),
        str(row.get("context_view") or ""),
        str(row.get("evidence_view") or ""),
        str(row.get("phrase_control_mode") or ""),
        str(row.get("phrase_guard_pos_scope") or ""),
        str(row.get("active_rescue_mode") or ""),
        coerce_metric(row.get("min_active_score"), default=0.0),
        coerce_metric(row.get("min_margin"), default=0.0),
    )


def select_best_sentence_veto_objective_row(
    rows: Sequence[Mapping[str, object]],
    *,
    max_harmful_replace_count: int | None = None,
) -> dict[str, object] | None:
    candidate_rows: list[Mapping[str, object]] = []
    for row in rows:
        harmful_replace_count = int(row.get("harmful_replace_count") or 0)
        if max_harmful_replace_count is not None and harmful_replace_count > max(
            0, int(max_harmful_replace_count)
        ):
            continue
        candidate_rows.append(row)
    if not candidate_rows:
        return None
    best_row = max(candidate_rows, key=_sentence_veto_objective_rank_key)
    return dict(best_row)


def coerce_metric(value: object, *, default: float) -> float:
    if isinstance(value, (float, int)):
        return float(value)
    return float(default)


def _sentence_veto_objective_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        compute_sentence_veto_objective(row),
        -int(row.get("harmful_replace_count") or 0),
        -coerce_metric(row.get("decision_accuracy"), default=0.0),
        -coerce_metric(row.get("replace_recall"), default=0.0),
        -coerce_metric(row.get("winner_accuracy"), default=0.0),
        -coerce_metric(row.get("shadow_winner_accuracy"), default=0.0),
        -coerce_metric(row.get("replace_precision"), default=0.0),
        str(row.get("scorer_id") or ""),
        str(row.get("context_view") or ""),
        str(row.get("evidence_view") or ""),
        str(row.get("phrase_control_mode") or ""),
        str(row.get("phrase_guard_pos_scope") or ""),
        str(row.get("active_rescue_mode") or ""),
        -coerce_metric(row.get("min_active_score"), default=0.0),
        -coerce_metric(row.get("min_margin"), default=0.0),
    )


def _render_sentence_veto_failure_block(title: str, rows: object) -> list[str]:
    lines = [f"### {title}", ""]
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        lines.append("- none")
        lines.append("")
        return lines
    for row in rows[:6]:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- `{row.get('case_id', '')}` `{row.get('predicted_decision', '')}` vs "
            f"`{row.get('gold_decision', '')}` | trigger `{row.get('source_phrase', '')}` | "
            f"margin `{float(row.get('margin') or 0.0):.3f}`"
        )
        if bool(row.get("phrase_preemption_hit")):
            lines.append(
                f"  phrase preemption: `{row.get('phrase_reason_code', '')}` | "
                f"`{row.get('matched_phrase_pattern', '')}`"
            )
        if bool(row.get("active_rescue_applied")):
            lines.append(
                f"  active rescue: `{row.get('active_rescue_reason_code', '')}` | "
                f"backup margin `{_render_rate_metric(row.get('active_rescue_backup_margin'))}`"
            )
        lines.append(f"  sentence: {row.get('sentence', '')}")
    lines.append("")
    return lines
