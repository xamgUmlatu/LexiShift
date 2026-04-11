#!/usr/bin/env python3
from __future__ import annotations

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

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_CONTEXT_VIEW,
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    DEFAULT_SENTENCE_VETO_MIN_ACTIVE_SCORE,
    DEFAULT_SENTENCE_VETO_MIN_MARGIN,
    RuntimeSimilarityBackend,
    SENTENCE_VETO_CONTEXT_VIEWS,
    SENTENCE_VETO_EVIDENCE_VIEWS,
    SENTENCE_VETO_SCORERS,
    build_runtime_context_views,
    evaluate_runtime_veto_case,
    resolve_runtime_evidence_text,
)

DEFAULT_SENTENCE_VETO_DATASET = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_routing_cases" / "en_es_sentence_veto_v2.json"
)
DEFAULT_SENTENCE_VETO_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_latest.json"
)
DEFAULT_SENTENCE_VETO_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_latest.md"
)
DEFAULT_SENTENCE_VETO_SWEEP_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_sweep_latest.json"
)
DEFAULT_SENTENCE_VETO_SWEEP_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_sweep_latest.md"
)


def load_sentence_veto_dataset(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Sentence-veto dataset must be a JSON object.")
    if int(payload.get("schema_version") or 0) != 1:
        raise ValueError("Sentence-veto dataset must declare schema_version=1.")
    if not str(payload.get("pair") or "").strip():
        raise ValueError("Sentence-veto dataset is missing `pair`.")
    families = payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)) or not families:
        raise ValueError("Sentence-veto dataset must include a non-empty `families` list.")
    normalized_families: list[dict[str, object]] = []
    for raw_family in families:
        if not isinstance(raw_family, Mapping):
            continue
        family_id = str(raw_family.get("family_id") or "").strip()
        trigger = str(raw_family.get("trigger") or "").strip()
        active = (
            dict(raw_family.get("active") or {})
            if isinstance(raw_family.get("active"), Mapping)
            else {}
        )
        shadows = [
            dict(shadow) for shadow in raw_family.get("shadows", ()) if isinstance(shadow, Mapping)
        ]
        cases = [dict(case) for case in raw_family.get("cases", ()) if isinstance(case, Mapping)]
        if not family_id or not trigger or not active or not cases:
            raise ValueError(
                "Each sentence-veto family must include `family_id`, `trigger`, `active`, and `cases`."
            )
        active_sense_id = str(active.get("sense_id") or "").strip()
        if not active_sense_id:
            raise ValueError(f"Family {family_id!r} is missing `active.sense_id`.")
        shadow_ids = {
            str(shadow.get("sense_id") or "").strip()
            for shadow in shadows
            if str(shadow.get("sense_id") or "").strip()
        }
        for case in cases:
            case_id = str(case.get("case_id") or "").strip()
            sentence = str(case.get("sentence") or "").strip()
            source_phrase = str(case.get("source_phrase") or "").strip()
            gold_winner = str(case.get("gold_winner") or "").strip()
            gold_decision = str(case.get("gold_decision") or "").strip().lower()
            if not case_id or not sentence or not source_phrase or not gold_winner:
                raise ValueError(
                    f"Family {family_id!r} contains a case missing one of "
                    f"`case_id`, `sentence`, `source_phrase`, or `gold_winner`."
                )
            if gold_decision and gold_decision not in {"replace", "abstain"}:
                raise ValueError(
                    f"Family {family_id!r} case {case_id!r} has unsupported gold_decision "
                    f"{gold_decision!r}."
                )
            if gold_winner not in {"none", active_sense_id} and gold_winner not in shadow_ids:
                raise ValueError(
                    f"Family {family_id!r} case {case_id!r} gold_winner {gold_winner!r} "
                    "does not match active or shadow sense ids."
                )
        normalized_families.append(
            {
                "family_id": family_id,
                "trigger": trigger,
                "active": active,
                "shadows": shadows,
                "cases": cases,
            }
        )
    payload["families"] = normalized_families
    return payload


def build_sentence_veto_report(
    *,
    dataset_path: Path,
    scorer_id: str,
    context_view: str = DEFAULT_SENTENCE_VETO_CONTEXT_VIEW,
    evidence_view: str = DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW,
    min_active_score: float = DEFAULT_SENTENCE_VETO_MIN_ACTIVE_SCORE,
    min_margin: float = DEFAULT_SENTENCE_VETO_MIN_MARGIN,
    model_name: str | None = None,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> dict[str, object]:
    dataset = load_sentence_veto_dataset(dataset_path)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    backend = RuntimeSimilarityBackend(
        scorer_id=scorer_id,
        model_name=str(model_name or "").strip(),
    )
    backend.fit(
        _collect_config_texts(
            dataset,
            context_view=context_view,
            evidence_view=evidence_view,
            window_tokens=window_tokens,
            mask_token=mask_token,
        )
    )

    summary = _new_sentence_veto_summary()
    family_breakdown: dict[str, dict[str, object]] = {}
    slice_tag_breakdown: dict[str, dict[str, object]] = {}
    gold_winner_type_breakdown: dict[str, dict[str, object]] = {}
    row_results: list[dict[str, object]] = []
    harmful_replace_rows: list[dict[str, object]] = []
    false_abstain_rows: list[dict[str, object]] = []
    winner_error_rows: list[dict[str, object]] = []

    for family in dataset["families"]:
        family_id = str(family.get("family_id") or "").strip()
        trigger = str(family.get("trigger") or "").strip()
        active = dict(family.get("active") or {})
        shadows = [dict(shadow) for shadow in family.get("shadows", ())]
        family_entry = family_breakdown.setdefault(
            family_id,
            {
                "family_id": family_id,
                "trigger": trigger,
                "active_target": str(active.get("target_lemma") or "").strip(),
                "shadow_targets": [
                    str(shadow.get("target_lemma") or "").strip()
                    for shadow in shadows
                    if str(shadow.get("target_lemma") or "").strip()
                ],
                "summary": _new_sentence_veto_summary(),
            },
        )
        for case in family.get("cases", ()):
            result = evaluate_runtime_veto_case(
                family_id=family_id,
                case=case,
                active_sense=active,
                shadow_senses=shadows,
                scorer=backend,
                context_view=context_view,
                evidence_view=evidence_view,
                min_active_score=min_active_score,
                min_margin=min_margin,
                window_tokens=window_tokens,
                mask_token=mask_token,
            )
            row_payload = {
                "case_id": result.case_id,
                "family_id": result.family_id,
                "trigger": trigger,
                "sentence": str(case.get("sentence") or "").strip(),
                "source_phrase": str(case.get("source_phrase") or "").strip(),
                "gold_decision": result.gold_decision,
                "gold_winner": result.gold_winner,
                "gold_winner_type": result.gold_winner_type,
                "predicted_decision": result.predicted_decision,
                "predicted_winner": result.predicted_winner,
                "predicted_winner_type": result.predicted_winner_type,
                "active_score": result.active_score,
                "strongest_shadow_score": result.strongest_shadow_score,
                "margin": result.margin,
                "strongest_shadow_id": result.strongest_shadow_id,
                "context_text": result.context_text,
                "active_evidence_text": result.active_evidence_text,
                "strongest_shadow_evidence_text": result.strongest_shadow_evidence_text,
                "slice_tags": _normalize_string_list(case.get("slice_tags")),
                "slice_dimensions": _normalize_slice_dimensions(case.get("slice_dimensions")),
                "notes": str(case.get("notes") or "").strip(),
            }
            row_results.append(row_payload)
            _accumulate_sentence_veto_summary(summary, result=result)
            _accumulate_sentence_veto_summary(family_entry["summary"], result=result)
            winner_type_entry = gold_winner_type_breakdown.setdefault(
                result.gold_winner_type,
                {
                    "gold_winner_type": result.gold_winner_type,
                    "summary": _new_sentence_veto_summary(),
                },
            )
            _accumulate_sentence_veto_summary(winner_type_entry["summary"], result=result)
            for slice_tag in row_payload["slice_tags"]:
                slice_tag_entry = slice_tag_breakdown.setdefault(
                    slice_tag,
                    {
                        "slice_tag": slice_tag,
                        "summary": _new_sentence_veto_summary(),
                    },
                )
                _accumulate_sentence_veto_summary(slice_tag_entry["summary"], result=result)
            if result.predicted_decision == "replace" and result.gold_decision != "replace":
                _append_sample(harmful_replace_rows, row_payload)
            if result.predicted_decision != "replace" and result.gold_decision == "replace":
                _append_sample(false_abstain_rows, row_payload)
            if (
                result.gold_winner_type in {"active", "shadow"}
                and result.predicted_winner != result.gold_winner
            ):
                _append_sample(winner_error_rows, row_payload)

    _finalize_sentence_veto_summary(summary)
    family_breakdown_rows = _finalize_sentence_veto_breakdown_rows(
        tuple(family_breakdown.values()),
        primary_sort_key="family_id",
    )
    slice_tag_breakdown_rows = _finalize_sentence_veto_breakdown_rows(
        tuple(slice_tag_breakdown.values()),
        primary_sort_key="slice_tag",
        sort_by_cases_desc=True,
    )
    winner_type_breakdown_rows = _finalize_sentence_veto_breakdown_rows(
        tuple(gold_winner_type_breakdown.values()),
        primary_sort_key="gold_winner_type",
        preferred_order=("active", "shadow", "none"),
    )
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": str(dataset.get("pair") or "").strip(),
        "dataset_id": str(dataset.get("dataset_id") or "").strip(),
        "generated_at": generated_at,
        "dataset_path": str(dataset_path),
        "config": {
            "scorer_id": scorer_id,
            "model_name": model_name,
            "context_view": context_view,
            "evidence_view": evidence_view,
            "min_active_score": float(min_active_score),
            "min_margin": float(min_margin),
            "window_tokens": int(window_tokens),
            "mask_token": str(mask_token or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
        },
        "summary": summary,
        "family_breakdown": family_breakdown_rows,
        "slice_tag_breakdown": slice_tag_breakdown_rows,
        "gold_winner_type_breakdown": winner_type_breakdown_rows,
        "row_results": row_results,
        "sample_harmful_replace_rows": harmful_replace_rows,
        "sample_false_abstain_rows": false_abstain_rows,
        "sample_winner_error_rows": winner_error_rows,
    }


def build_sentence_veto_sweep_report(
    *,
    dataset_path: Path,
    scorers: Sequence[str],
    context_views: Sequence[str],
    evidence_views: Sequence[str],
    min_active_scores: Sequence[float],
    min_margins: Sequence[float],
    model_name: str | None = None,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> dict[str, object]:
    dataset = load_sentence_veto_dataset(dataset_path)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    rows: list[dict[str, object]] = []

    normalized_scorers = [
        value for value in _normalize_string_list(scorers) if value in SENTENCE_VETO_SCORERS
    ]
    normalized_context_views = [
        value
        for value in _normalize_string_list(context_views)
        if value in SENTENCE_VETO_CONTEXT_VIEWS
    ]
    normalized_evidence_views = [
        value
        for value in _normalize_string_list(evidence_views)
        if value in SENTENCE_VETO_EVIDENCE_VIEWS
    ]
    normalized_min_active_scores = [float(value) for value in min_active_scores]
    normalized_min_margins = [float(value) for value in min_margins]
    if not normalized_scorers or not normalized_context_views or not normalized_evidence_views:
        raise ValueError(
            "Sentence-veto sweep requires non-empty scorer, context-view, and evidence-view sets."
        )
    if not normalized_min_active_scores or not normalized_min_margins:
        raise ValueError("Sentence-veto sweep requires non-empty min-active and min-margin grids.")

    for scorer_id in normalized_scorers:
        for context_view in normalized_context_views:
            for evidence_view in normalized_evidence_views:
                for min_active_score in normalized_min_active_scores:
                    for min_margin in normalized_min_margins:
                        report = build_sentence_veto_report(
                            dataset_path=dataset_path,
                            scorer_id=scorer_id,
                            context_view=context_view,
                            evidence_view=evidence_view,
                            min_active_score=min_active_score,
                            min_margin=min_margin,
                            model_name=model_name,
                            window_tokens=window_tokens,
                            mask_token=mask_token,
                        )
                        summary = dict(report.get("summary") or {})
                        row = {
                            "config_id": (
                                f"{scorer_id}:{context_view}:{evidence_view}:"
                                f"a={min_active_score:.2f}:m={min_margin:.2f}"
                            ),
                            "scorer_id": scorer_id,
                            "model_name": model_name,
                            "context_view": context_view,
                            "evidence_view": evidence_view,
                            "min_active_score": float(min_active_score),
                            "min_margin": float(min_margin),
                            "decision_accuracy": summary.get("decision_accuracy"),
                            "replace_precision": summary.get("replace_precision"),
                            "replace_recall": summary.get("replace_recall"),
                            "harmful_replace_rate": summary.get("harmful_replace_rate"),
                            "false_abstain_rate": summary.get("false_abstain_rate"),
                            "winner_accuracy": summary.get("winner_accuracy"),
                            "shadow_winner_accuracy": summary.get("shadow_winner_accuracy"),
                            "predicted_replace_rate": summary.get("predicted_replace_rate"),
                            "summary": summary,
                        }
                        row["objective_score"] = _compute_sentence_veto_objective(row)
                        rows.append(row)

    rows.sort(key=_sentence_veto_sweep_rank_key)
    best_row = dict(rows[0]) if rows else None
    best_by_scorer: list[dict[str, object]] = []
    for scorer_id in normalized_scorers:
        scorer_rows = [row for row in rows if str(row.get("scorer_id") or "").strip() == scorer_id]
        if scorer_rows:
            best_by_scorer.append(dict(scorer_rows[0]))
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": str(dataset.get("pair") or "").strip(),
        "dataset_id": str(dataset.get("dataset_id") or "").strip(),
        "generated_at": generated_at,
        "dataset_path": str(dataset_path),
        "grid": {
            "scorers": normalized_scorers,
            "context_views": normalized_context_views,
            "evidence_views": normalized_evidence_views,
            "min_active_scores": normalized_min_active_scores,
            "min_margins": normalized_min_margins,
            "model_name": model_name,
            "window_tokens": int(window_tokens),
            "mask_token": str(mask_token or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
        },
        "row_count": len(rows),
        "best_row": best_row,
        "best_by_scorer": best_by_scorer,
        "rows": rows,
    }


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
        f"- Thresholds: `min_active={config.get('min_active_score', '')}`, `min_margin={config.get('min_margin', '')}`",
        "",
        "## Summary",
        "",
        f"- Decision accuracy: `{_render_rate(summary.get('decision_accuracy'))}`",
        f"- Replace precision / recall: `{_render_rate(summary.get('replace_precision'))}` / `{_render_rate(summary.get('replace_recall'))}`",
        f"- Harmful replace / false abstain: `{_render_rate(summary.get('harmful_replace_rate'))}` / `{_render_rate(summary.get('false_abstain_rate'))}`",
        f"- Winner accuracy / shadow-winner accuracy: `{_render_rate(summary.get('winner_accuracy'))}` / `{_render_rate(summary.get('shadow_winner_accuracy'))}`",
        f"- Predicted replace rate: `{_render_rate(summary.get('predicted_replace_rate'))}`",
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
    lines.extend(
        [
            "",
            "## Gold Winner Type Breakdown",
            "",
        ]
    )
    lines.extend(
        _render_sentence_veto_breakdown_table(
            report.get("gold_winner_type_breakdown"),
            label_key="gold_winner_type",
        )
    )
    lines.extend(
        [
            "",
            "## Slice Tag Breakdown",
            "",
        ]
    )
    lines.extend(
        _render_sentence_veto_breakdown_table(
            report.get("slice_tag_breakdown"),
            label_key="slice_tag",
            limit=12,
        )
    )
    lines.extend(
        [
            "",
            "## Failure Samples",
            "",
        ]
    )
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
        "",
        "## Best Overall",
        "",
    ]
    if best_row:
        lines.extend(_render_sentence_veto_sweep_row(best_row))
    lines.extend(["", "## Best By Scorer", ""])
    for row in best_by_scorer[:10]:
        lines.extend(_render_sentence_veto_sweep_row(row))
        lines.append("")
    lines.extend(["## Top Configs", ""])
    lines.append(
        "| Rank | Scorer | Context | Evidence | min_active | min_margin | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |"
    )
    lines.append("| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for index, row in enumerate(rows[:12], start=1):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(index),
                    str(row.get("scorer_id") or ""),
                    str(row.get("context_view") or ""),
                    str(row.get("evidence_view") or ""),
                    f"{float(row.get('min_active_score') or 0.0):.2f}",
                    f"{float(row.get('min_margin') or 0.0):.2f}",
                    _render_rate(row.get("decision_accuracy")),
                    _render_rate(row.get("harmful_replace_rate")),
                    _render_rate(row.get("false_abstain_rate")),
                    _render_rate(row.get("winner_accuracy")),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


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
        lines.append(f"  sentence: {row.get('sentence', '')}")
    lines.append("")
    return lines


def _render_sentence_veto_sweep_row(row: Mapping[str, object]) -> list[str]:
    return [
        f"- Config: `{row.get('config_id', '')}`",
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


def _collect_config_texts(
    dataset: Mapping[str, object],
    *,
    context_view: str,
    evidence_view: str,
    window_tokens: int,
    mask_token: str,
) -> list[str]:
    texts: list[str] = []
    for family in dataset.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        active = family.get("active")
        if isinstance(active, Mapping):
            texts.append(resolve_runtime_evidence_text(active, evidence_view=evidence_view))
        shadows = family.get("shadows")
        if isinstance(shadows, Sequence) and not isinstance(shadows, (str, bytes)):
            for shadow in shadows:
                if isinstance(shadow, Mapping):
                    texts.append(resolve_runtime_evidence_text(shadow, evidence_view=evidence_view))
        cases = family.get("cases")
        if isinstance(cases, Sequence) and not isinstance(cases, (str, bytes)):
            for case in cases:
                if not isinstance(case, Mapping):
                    continue
                context_views = build_runtime_context_views(
                    str(case.get("sentence") or "").strip(),
                    source_phrase=str(
                        case.get("source_phrase") or case.get("trigger") or ""
                    ).strip(),
                    mask_token=mask_token,
                    window_tokens=window_tokens,
                )
                texts.append(str(context_views.get(context_view) or "").strip())
    return [text for text in texts if str(text or "").strip()]


def _accumulate_sentence_veto_summary(
    summary: dict[str, object],
    *,
    result: object,
) -> None:
    gold_decision = str(getattr(result, "gold_decision", "") or "").strip()
    predicted_decision = str(getattr(result, "predicted_decision", "") or "").strip()
    gold_winner_type = str(getattr(result, "gold_winner_type", "") or "").strip()
    predicted_winner = str(getattr(result, "predicted_winner", "") or "").strip()
    gold_winner = str(getattr(result, "gold_winner", "") or "").strip()
    summary["cases_total"] += 1
    if gold_decision == "replace":
        summary["gold_replace_cases"] += 1
    else:
        summary["gold_abstain_cases"] += 1
    if gold_winner_type == "active":
        summary["gold_active_winner_cases"] += 1
    elif gold_winner_type == "shadow":
        summary["gold_shadow_winner_cases"] += 1
    else:
        summary["gold_none_cases"] += 1
    if predicted_decision == "replace":
        summary["predicted_replace_cases"] += 1
    else:
        summary["predicted_abstain_cases"] += 1
    if predicted_decision == "replace" and gold_decision == "replace":
        summary["true_replace_count"] += 1
    elif predicted_decision == "replace":
        summary["harmful_replace_count"] += 1
    elif gold_decision == "replace":
        summary["false_abstain_count"] += 1
    else:
        summary["true_abstain_count"] += 1
    if gold_winner_type in {"active", "shadow"}:
        summary["winner_labeled_cases"] += 1
        if predicted_winner == gold_winner:
            summary["winner_correct_count"] += 1
    if gold_winner_type == "shadow":
        summary["shadow_winner_labeled_cases"] += 1
        if predicted_winner == gold_winner:
            summary["shadow_winner_correct_count"] += 1


def _new_sentence_veto_summary() -> dict[str, object]:
    return {
        "cases_total": 0,
        "gold_replace_cases": 0,
        "gold_abstain_cases": 0,
        "gold_active_winner_cases": 0,
        "gold_shadow_winner_cases": 0,
        "gold_none_cases": 0,
        "predicted_replace_cases": 0,
        "predicted_abstain_cases": 0,
        "true_replace_count": 0,
        "true_abstain_count": 0,
        "harmful_replace_count": 0,
        "false_abstain_count": 0,
        "winner_labeled_cases": 0,
        "winner_correct_count": 0,
        "shadow_winner_labeled_cases": 0,
        "shadow_winner_correct_count": 0,
    }


def _finalize_sentence_veto_summary(summary: Mapping[str, object]) -> None:
    cases_total = int(summary.get("cases_total") or 0)
    gold_replace_cases = int(summary.get("gold_replace_cases") or 0)
    gold_abstain_cases = int(summary.get("gold_abstain_cases") or 0)
    predicted_replace_cases = int(summary.get("predicted_replace_cases") or 0)
    winner_labeled_cases = int(summary.get("winner_labeled_cases") or 0)
    shadow_winner_labeled_cases = int(summary.get("shadow_winner_labeled_cases") or 0)
    true_replace_count = int(summary.get("true_replace_count") or 0)
    true_abstain_count = int(summary.get("true_abstain_count") or 0)
    harmful_replace_count = int(summary.get("harmful_replace_count") or 0)
    false_abstain_count = int(summary.get("false_abstain_count") or 0)
    winner_correct_count = int(summary.get("winner_correct_count") or 0)
    shadow_winner_correct_count = int(summary.get("shadow_winner_correct_count") or 0)

    summary["decision_accuracy"] = _safe_rate(true_replace_count + true_abstain_count, cases_total)
    summary["replace_precision"] = _safe_rate(true_replace_count, predicted_replace_cases)
    summary["replace_recall"] = _safe_rate(true_replace_count, gold_replace_cases)
    summary["harmful_replace_rate"] = _safe_rate(harmful_replace_count, gold_abstain_cases)
    summary["false_abstain_rate"] = _safe_rate(false_abstain_count, gold_replace_cases)
    summary["winner_accuracy"] = _safe_rate(winner_correct_count, winner_labeled_cases)
    summary["shadow_winner_accuracy"] = _safe_rate(
        shadow_winner_correct_count,
        shadow_winner_labeled_cases,
    )
    summary["predicted_replace_rate"] = _safe_rate(predicted_replace_cases, cases_total)


def _compute_sentence_veto_objective(row: Mapping[str, object]) -> float:
    return (
        _coerce_metric(row.get("decision_accuracy"), default=0.0)
        + _coerce_metric(row.get("replace_precision"), default=0.0)
        + _coerce_metric(row.get("replace_recall"), default=0.0)
        + _coerce_metric(row.get("winner_accuracy"), default=0.0)
        - (2.0 * _coerce_metric(row.get("harmful_replace_rate"), default=0.0))
        - _coerce_metric(row.get("false_abstain_rate"), default=0.0)
    )


def _sentence_veto_sweep_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _coerce_metric(row.get("harmful_replace_rate"), default=1.0),
        _coerce_metric(row.get("false_abstain_rate"), default=1.0),
        -_coerce_metric(row.get("decision_accuracy"), default=0.0),
        -_coerce_metric(row.get("winner_accuracy"), default=0.0),
        -_coerce_metric(row.get("shadow_winner_accuracy"), default=0.0),
        -_coerce_metric(row.get("replace_precision"), default=0.0),
        -_coerce_metric(row.get("replace_recall"), default=0.0),
        str(row.get("scorer_id") or ""),
        str(row.get("context_view") or ""),
        str(row.get("evidence_view") or ""),
        _coerce_metric(row.get("min_active_score"), default=0.0),
        _coerce_metric(row.get("min_margin"), default=0.0),
    )


def _coerce_metric(value: object, *, default: float) -> float:
    if isinstance(value, (float, int)):
        return float(value)
    return float(default)


def _finalize_sentence_veto_breakdown_rows(
    rows: object,
    *,
    primary_sort_key: str,
    sort_by_cases_desc: bool = False,
    preferred_order: Sequence[str] = (),
) -> list[dict[str, object]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return []
    preferred_order_lookup = {
        value: index for index, value in enumerate(_normalize_string_list(preferred_order))
    }
    finalized_rows: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        summary = row.get("summary")
        if not isinstance(summary, Mapping):
            continue
        summary_payload = dict(summary)
        _finalize_sentence_veto_summary(summary_payload)
        payload = dict(row)
        payload["summary"] = summary_payload
        finalized_rows.append(payload)
    if sort_by_cases_desc:
        finalized_rows.sort(
            key=lambda row: (
                -int(
                    (row.get("summary", {}) if isinstance(row.get("summary"), Mapping) else {}).get(
                        "cases_total"
                    )
                    or 0
                ),
                str(row.get(primary_sort_key) or ""),
            )
        )
        return finalized_rows
    if preferred_order_lookup:
        finalized_rows.sort(
            key=lambda row: (
                preferred_order_lookup.get(
                    str(row.get(primary_sort_key) or "").strip(),
                    len(preferred_order_lookup),
                ),
                str(row.get(primary_sort_key) or ""),
            )
        )
        return finalized_rows
    finalized_rows.sort(key=lambda row: str(row.get(primary_sort_key) or ""))
    return finalized_rows


def _normalize_string_list(values: object) -> list[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    normalized: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _normalize_slice_dimensions(value: object) -> dict[str, list[str]]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, list[str]] = {}
    for key, raw_values in value.items():
        dimension_name = str(key or "").strip()
        values = _normalize_string_list(raw_values)
        if dimension_name and values:
            normalized[dimension_name] = values
    return normalized


def _append_sample(
    container: list[dict[str, object]], row: Mapping[str, object], *, limit: int = 8
) -> None:
    if len(container) < limit:
        container.append(dict(row))


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator
