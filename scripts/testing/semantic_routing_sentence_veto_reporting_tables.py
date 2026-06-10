from __future__ import annotations

from typing import Mapping, Sequence


def _render_sentence_veto_sweep_row(row: Mapping[str, object]) -> list[str]:
    return [
        f"- Config: `{row.get('config_id', '')}`",
        f"- Phrase control mode: `{row.get('phrase_control_mode', 'off')}`",
        f"- Phrase guard POS scope: `{row.get('phrase_guard_pos_scope', 'family_all')}`",
        f"- Active rescue mode: `{row.get('active_rescue_mode', 'off')}`",
        f"- Harmful replace count / false abstain count: "
        f"`{int(row.get('harmful_replace_count') or 0)}` / "
        f"`{int(row.get('false_abstain_count') or 0)}`",
        f"- Phrase preemption hit count / precision: "
        f"`{int(row.get('phrase_preemption_hit_count') or 0)}` / "
        f"`{_render_rate(row.get('phrase_preemption_precision'))}`",
        f"- Active rescue hit count / precision: "
        f"`{int(row.get('active_rescue_applied_count') or 0)}` / "
        f"`{_render_rate(row.get('active_rescue_precision'))}`",
        f"- Decision accuracy / harmful replace / false abstain: "
        f"`{_render_rate(row.get('decision_accuracy'))}` / "
        f"`{_render_rate(row.get('harmful_replace_rate'))}` / "
        f"`{_render_rate(row.get('false_abstain_rate'))}`",
        f"- Replace precision / recall: "
        f"`{_render_rate(row.get('replace_precision'))}` / "
        f"`{_render_rate(row.get('replace_recall'))}`",
        f"- Winner accuracy / shadow-winner accuracy: "
        f"`{_render_rate(row.get('winner_accuracy'))}` / "
        f"`{_render_rate(row.get('shadow_winner_accuracy'))}`",
    ]


def _render_sentence_veto_ladder_row(row: Mapping[str, object]) -> list[str]:
    lines = [
        f"- Config: `{row.get('config_id', '')}`",
        f"- Soft affordance count / true / false: "
        f"`{int(row.get('soft_affordance_count') or 0)}` / "
        f"`{int(row.get('soft_true_positive_count') or 0)}` / "
        f"`{int(row.get('soft_false_positive_count') or 0)}`",
        f"- Hard replace recall / harmful replace: "
        f"`{_render_rate(row.get('hard_replace_recall'))}` / "
        f"`{_render_rate(row.get('hard_harmful_replace_rate'))}`",
        f"- Replace-or-soft recall / lift: "
        f"`{_render_rate(row.get('replace_or_soft_recall'))}` / "
        f"`{_render_rate(row.get('replace_or_soft_recall_lift'))}`",
        f"- Soft precision / noise: "
        f"`{_render_rate(row.get('soft_precision'))}` / "
        f"`{_render_rate(row.get('soft_noise_rate'))}`",
        f"- Surfaced precision / missed replace rate: "
        f"`{_render_rate(row.get('surfaced_precision'))}` / "
        f"`{_render_rate(row.get('remaining_missed_replace_rate'))}`",
    ]
    sample_soft_true_positive_rows = (
        row.get("sample_soft_true_positive_rows")
        if isinstance(row.get("sample_soft_true_positive_rows"), Sequence)
        and not isinstance(row.get("sample_soft_true_positive_rows"), (str, bytes))
        else []
    )
    if sample_soft_true_positive_rows:
        lines.append(
            "- Soft true-positive samples: "
            + ", ".join(
                f"`{str(sample.get('case_id') or '').strip()}`"
                for sample in sample_soft_true_positive_rows[:4]
                if isinstance(sample, Mapping)
            )
        )
    sample_soft_false_positive_rows = (
        row.get("sample_soft_false_positive_rows")
        if isinstance(row.get("sample_soft_false_positive_rows"), Sequence)
        and not isinstance(row.get("sample_soft_false_positive_rows"), (str, bytes))
        else []
    )
    if sample_soft_false_positive_rows:
        lines.append(
            "- Soft false-positive samples: "
            + ", ".join(
                f"`{str(sample.get('case_id') or '').strip()}`"
                for sample in sample_soft_false_positive_rows[:4]
                if isinstance(sample, Mapping)
            )
        )
    return lines


def _render_sentence_veto_breakdown_table(
    rows: object,
    *,
    label_key: str,
    label_builder: object | None = None,
    limit: int | None = None,
) -> list[str]:
    lines = [
        "| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        lines.append("| none | 0 | n/a | n/a | n/a | n/a |")
        return lines
    rendered_count = 0
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        summary = row.get("summary") if isinstance(row.get("summary"), Mapping) else {}
        label = ""
        if callable(label_builder):
            label = str(label_builder(row) or "").strip()
        if not label:
            label = str(row.get(label_key) or "").strip()
        if not label:
            continue
        lines.append(
            "| "
            + " | ".join(
                (
                    label,
                    str(int(summary.get("cases_total") or 0)),
                    _render_rate(summary.get("decision_accuracy")),
                    _render_rate(summary.get("replace_recall")),
                    _render_rate(summary.get("harmful_replace_rate")),
                    _render_rate(summary.get("winner_accuracy")),
                )
            )
            + " |"
        )
        rendered_count += 1
        if limit is not None and rendered_count >= max(0, int(limit)):
            break
    if rendered_count <= 0:
        lines.append("| none | 0 | n/a | n/a | n/a | n/a |")
    return lines


def _build_family_breakdown_label(row: Mapping[str, object]) -> str:
    trigger = str(row.get("trigger") or "").strip()
    active_target = str(row.get("active_target") or "").strip()
    shadow_targets = _normalize_string_list(row.get("shadow_targets"))
    if trigger and active_target and shadow_targets:
        return f"{trigger} -> {active_target} vs {', '.join(shadow_targets)}"
    if trigger and active_target:
        return f"{trigger} -> {active_target}"
    return str(row.get("family_id") or "").strip()


def _normalize_string_list(values: object) -> list[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    normalized: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _render_rate_metric(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value):.3f}"
