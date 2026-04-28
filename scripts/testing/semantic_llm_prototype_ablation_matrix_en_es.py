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
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXAMPLE_FRAME_BATCH_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    SENTENCE_VETO_CONTEXT_VIEWS,
    SENTENCE_VETO_SCORERS,
)
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_QUEUE_JSON,
)
from semantic_llm_prototype_admission_probe_en_es import (  # noqa: E402
    DEFAULT_PROTOTYPE_CONTEXT_VIEW,
    build_prototype_admission_report,
)
from semantic_llm_prototype_ablation_matrix_rendering import (  # noqa: E402
    render_prototype_ablation_matrix_markdown,
)
from semantic_llm_prototype_ablation_matrix_sources import (  # noqa: E402
    SourceSpec,
    resolve_source_specs,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_REVERSE_AUX_EVIDENCE = (
    EXAMPLE_FRAME_BATCH_ROOT
    / "en-es-reverse-aux-example-frames-v10-20260425a_normalized_evidence.json"
)
DEFAULT_GENERATED_COMPOSITE_EVIDENCE = (
    EXAMPLE_FRAME_BATCH_ROOT
    / "en-es-reverse-aux-plus-llm-missing-rows-plus-balanced-remediation-latest_normalized_evidence.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_prototype_ablation_matrix_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_prototype_ablation_matrix_latest.md"
DEFAULT_SOURCE_MODES = (
    "reviewed_dataset",
    "empty_batch",
    "reverse_aux",
    "generated_composite",
    "generated_active_only",
    "generated_no_phrase",
    "generated_no_shadow",
)
DEFAULT_SCOPES = ("prompt_queue", "all_dataset_families")
SUPPORTED_SCOPES = frozenset(DEFAULT_SCOPES)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a no-spend prototype semantic-veto ablation matrix over source modes, "
            "scorers, context views, thresholds, and internal guard shapes."
        )
    )
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--source-modes",
        default=",".join(DEFAULT_SOURCE_MODES),
        help="Comma-separated source modes.",
    )
    parser.add_argument(
        "--scopes",
        default=",".join(DEFAULT_SCOPES),
        help="Comma-separated scopes: prompt_queue, all_dataset_families.",
    )
    parser.add_argument(
        "--scorers",
        default="token_jaccard,tfidf_cosine",
        help="Comma-separated scorer ids.",
    )
    parser.add_argument(
        "--context-views",
        default=",".join(SENTENCE_VETO_CONTEXT_VIEWS),
        help="Comma-separated context view ids.",
    )
    parser.add_argument(
        "--min-active-grid",
        default="0.00,0.35",
        help="Comma-separated active-score thresholds.",
    )
    parser.add_argument(
        "--min-margin-grid",
        default="0.00,0.05",
        help="Comma-separated active-vs-shadow margin thresholds.",
    )
    parser.add_argument("--reverse-aux-json", type=Path, default=DEFAULT_REVERSE_AUX_EVIDENCE)
    parser.add_argument(
        "--generated-composite-json",
        type=Path,
        default=DEFAULT_GENERATED_COMPOSITE_EVIDENCE,
    )
    parser.add_argument(
        "--evidence-batch-json",
        action="append",
        type=Path,
        default=[],
        help="Optional additional evidence batch JSON; mode ids become custom_1, custom_2, ...",
    )
    parser.add_argument(
        "--window-tokens",
        type=int,
        default=DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    )
    parser.add_argument("--mask-token", default=DEFAULT_SENTENCE_VETO_MASK_TOKEN)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_prototype_ablation_matrix_report(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    source_modes: Sequence[str] = DEFAULT_SOURCE_MODES,
    scopes: Sequence[str] = DEFAULT_SCOPES,
    scorers: Sequence[str] = ("token_jaccard", "tfidf_cosine"),
    context_views: Sequence[str] = SENTENCE_VETO_CONTEXT_VIEWS,
    min_active_scores: Sequence[float] = (0.0, 0.35),
    min_margins: Sequence[float] = (0.0, 0.05),
    reverse_aux_path: Path = DEFAULT_REVERSE_AUX_EVIDENCE,
    generated_composite_path: Path = DEFAULT_GENERATED_COMPOSITE_EVIDENCE,
    extra_evidence_paths: Sequence[Path] = (),
    source_payload_overrides: Mapping[str, Mapping[str, object]] | None = None,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
    normalized_scopes = _normalize_supported_strings(scopes, SUPPORTED_SCOPES, "scope")
    normalized_scorers = _normalize_supported_strings(scorers, SENTENCE_VETO_SCORERS, "scorer")
    normalized_context_views = _normalize_supported_strings(
        context_views,
        SENTENCE_VETO_CONTEXT_VIEWS,
        "context view",
    )
    normalized_min_active_scores = [float(value) for value in min_active_scores]
    normalized_min_margins = [float(value) for value in min_margins]
    if not normalized_min_active_scores or not normalized_min_margins:
        raise ValueError("The ablation matrix requires non-empty threshold grids.")

    source_specs, skipped_sources = resolve_source_specs(
        source_modes=source_modes,
        reverse_aux_path=reverse_aux_path,
        generated_composite_path=generated_composite_path,
        extra_evidence_paths=extra_evidence_paths,
        overrides=source_payload_overrides or {},
    )
    if not source_specs:
        raise ValueError("The ablation matrix requires at least one resolvable source mode.")

    rows: list[dict[str, object]] = []
    run_reports = 0
    for source_spec in source_specs:
        for scope in normalized_scopes:
            all_dataset_families = scope == "all_dataset_families"
            for scorer_id in normalized_scorers:
                for context_view in normalized_context_views:
                    for min_active_score in normalized_min_active_scores:
                        for min_margin in normalized_min_margins:
                            report = build_prototype_admission_report(
                                queue_payload=queue_payload,
                                dataset_payload=dataset_payload,
                                evidence_batch_payload=source_spec.payload,
                                all_dataset_families=all_dataset_families,
                                scorer_id=scorer_id,
                                context_view=context_view,
                                min_active_score=min_active_score,
                                min_margin=min_margin,
                                window_tokens=window_tokens,
                                mask_token=mask_token,
                                generated_at=generated_at,
                            )
                            run_reports += 1
                            coverage = _coverage_summary(report.get("coverage_rows"))
                            for config in report.get("configurations", ()):
                                if isinstance(config, Mapping):
                                    rows.append(
                                        _matrix_row(
                                            source_spec=source_spec,
                                            scope=scope,
                                            report=report,
                                            config=config,
                                            coverage=coverage,
                                        )
                                    )

    rows.sort(key=_rank_key)
    best_row = _public_row(_select_best(rows))
    best_candidate_source_row = _public_row(
        _select_best(row for row in rows if row.get("source_class") == "candidate_source")
    )
    report: dict[str, object] = {
        "schema_version": 1,
        "status": "ok",
        "generated_at": generated_at,
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "decision_contract": "binary_replace_or_abstain",
        "row_count": len(rows),
        "run_report_count": run_reports,
        "grid": {
            "source_modes": [source.mode for source in source_specs],
            "scopes": normalized_scopes,
            "scorers": normalized_scorers,
            "context_views": normalized_context_views,
            "min_active_scores": normalized_min_active_scores,
            "min_margins": normalized_min_margins,
            "window_tokens": int(window_tokens),
            "mask_token": str(mask_token or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
        },
        "skipped_sources": skipped_sources,
        "best_row": best_row,
        "best_candidate_source_row": best_candidate_source_row,
        "best_by_source_mode": _best_by_field(rows, "source_mode"),
        "best_by_scope": _best_by_field(rows, "scope"),
        "best_by_decision_shape": _best_by_field(rows, "decision_shape"),
        "best_by_context_view": _best_by_field(rows, "context_view"),
        "best_by_scorer": _best_by_field(rows, "scorer_id"),
        "best_candidate_by_scope": _best_by_field(_candidate_rows(rows), "scope"),
        "best_candidate_by_decision_shape": _best_by_field(
            _candidate_rows(rows),
            "decision_shape",
        ),
        "best_candidate_by_context_view": _best_by_field(
            _candidate_rows(rows),
            "context_view",
        ),
        "best_candidate_by_scorer": _best_by_field(_candidate_rows(rows), "scorer_id"),
        "assumption_audit": _build_assumption_audit(rows),
        "rows": rows,
    }
    report["recommendation"] = _build_recommendation(report)
    return report


def _matrix_row(
    *,
    source_spec: SourceSpec,
    scope: str,
    report: Mapping[str, object],
    config: Mapping[str, object],
    coverage: Mapping[str, object],
) -> dict[str, object]:
    summary = config.get("summary") if isinstance(config.get("summary"), Mapping) else {}
    row = {
        "matrix_id": (
            f"{source_spec.mode}:{scope}:{report.get('scorer_id', '')}:"
            f"{report.get('context_view', DEFAULT_PROTOTYPE_CONTEXT_VIEW)}:"
            f"a={float(report.get('min_active_score') or 0.0):.2f}:"
            f"m={float(report.get('min_margin') or 0.0):.2f}:"
            f"{config.get('config_id', '')}"
        ),
        "source_mode": source_spec.mode,
        "source_label": source_spec.label,
        "source_class": source_spec.source_class,
        "source_path": source_spec.path,
        "source_description": source_spec.description,
        "evidence_source_id": str(report.get("evidence_source_id") or "").strip(),
        "evidence_batch_id": str(report.get("evidence_batch_id") or "").strip(),
        "scope": scope,
        "evaluation_scope": str(report.get("evaluation_scope") or "").strip(),
        "scorer_id": str(report.get("scorer_id") or "").strip(),
        "context_view": str(report.get("context_view") or "").strip(),
        "min_active_score": float(report.get("min_active_score") or 0.0),
        "min_margin": float(report.get("min_margin") or 0.0),
        "config_id": str(config.get("config_id") or "").strip(),
        "label": str(config.get("label") or "").strip(),
        "decision_shape": _decision_shape(config),
        "phrase_guard_pos_scope": str(config.get("phrase_guard_pos_scope") or "").strip(),
        "use_phrase_prototypes": bool(config.get("use_phrase_prototypes")),
        "use_phrase_containment_gate": bool(config.get("use_phrase_containment_gate")),
        "use_surface_pos_rescue": bool(config.get("use_surface_pos_rescue")),
        "phrase_control_evidence_mode": str(
            config.get("phrase_control_evidence_mode") or ""
        ).strip(),
        "cases_total": int(summary.get("cases_total") or 0),
        "gold_replace_cases": int(summary.get("gold_replace_cases") or 0),
        "gold_abstain_cases": int(summary.get("gold_abstain_cases") or 0),
        "decision_accuracy": _round_float(summary.get("decision_accuracy")),
        "replace_precision": _round_float(summary.get("replace_precision")),
        "replace_recall": _round_float(summary.get("replace_recall")),
        "harmful_replace_rate": _round_float(summary.get("harmful_replace_rate")),
        "false_abstain_rate": _round_float(summary.get("false_abstain_rate")),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
        "phrase_preemption_hit_count": int(summary.get("phrase_preemption_hit_count") or 0),
        "phrase_containment_hit_count": int(summary.get("phrase_containment_hit_count") or 0),
        "active_rescue_applied_count": int(summary.get("active_rescue_applied_count") or 0),
        "source_coverage": dict(coverage),
        "harmful_replace_case_ids": list(config.get("harmful_replace_case_ids") or ()),
        "false_abstain_case_ids": list(config.get("false_abstain_case_ids") or ()),
    }
    row["objective_score"] = _objective_score(row)
    return row


def _coverage_summary(value: object) -> dict[str, object]:
    rows = [row for row in value or () if isinstance(row, Mapping)]
    families_total = len(rows)
    active_covered = 0
    any_shadow_covered = 0
    all_shadow_covered = 0
    phrase_covered = 0
    complete = 0
    for row in rows:
        active_count = int(row.get("active_example_count") or 0)
        shadow_counts = [
            int(count)
            for count in row.get("shadow_example_counts", ())
            if isinstance(count, (int, float))
        ]
        phrase_count = int(row.get("phrase_control_example_count") or 0)
        has_active = active_count > 0
        has_any_shadow = any(count > 0 for count in shadow_counts)
        has_all_shadow = bool(shadow_counts) and all(count > 0 for count in shadow_counts)
        has_phrase = phrase_count > 0
        active_covered += int(has_active)
        any_shadow_covered += int(has_any_shadow)
        all_shadow_covered += int(has_all_shadow)
        phrase_covered += int(has_phrase)
        complete += int(has_active and has_all_shadow and has_phrase)
    return {
        "families_total": families_total,
        "active_covered_families": active_covered,
        "any_shadow_covered_families": any_shadow_covered,
        "all_shadow_covered_families": all_shadow_covered,
        "phrase_covered_families": phrase_covered,
        "contract_complete_families": complete,
    }


def _decision_shape(config: Mapping[str, object]) -> str:
    if bool(config.get("use_surface_pos_rescue")):
        return "active_shadow_containment_surface_pos"
    if bool(config.get("use_phrase_prototypes")):
        return "active_shadow_phrase_semantic_prototypes"
    if bool(config.get("use_phrase_containment_gate")):
        return "active_shadow_phrase_containment"
    if str(config.get("phrase_guard_pos_scope") or "").strip() == "active_only":
        return "active_shadow_active_pos_guard"
    return "active_shadow_family_pos_guard"


def _build_assumption_audit(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    candidate_rows = _candidate_rows(rows)
    generated_rows = [
        row for row in rows if str(row.get("source_mode") or "").startswith("generated")
    ]
    no_surface_rows = [row for row in candidate_rows if not bool(row.get("use_surface_pos_rescue"))]
    viable_no_surface_rows = [
        row for row in no_surface_rows if float(row.get("replace_recall") or 0.0) > 0.0
    ]
    no_phrase_rows = [
        row
        for row in candidate_rows
        if not bool(row.get("use_phrase_containment_gate"))
        and not bool(row.get("use_phrase_prototypes"))
    ]
    best_candidate = _select_best(candidate_rows)
    best_candidate_false = (
        int(best_candidate.get("false_abstain_count") or 0)
        if isinstance(best_candidate, Mapping)
        else 0
    )
    simplification_candidates = [
        _public_row(row)
        for row in sorted(no_surface_rows, key=_rank_key)
        if int(row.get("harmful_replace_count") or 0) == 0
        and int(row.get("false_abstain_count") or 0) <= best_candidate_false
        and float(row.get("replace_recall") or 0.0) > 0.0
    ][:10]
    return {
        "best_oracle_row": _public_row(
            _select_best(row for row in rows if row.get("source_class") == "oracle")
        ),
        "best_candidate_source_row": _public_row(_select_best(candidate_rows)),
        "best_empty_baseline_row": _public_row(
            _select_best(row for row in rows if row.get("source_class") == "baseline")
        ),
        "best_without_surface_pos_row": _public_row(_select_best(no_surface_rows)),
        "best_viable_without_surface_pos_row": _public_row(_select_best(viable_no_surface_rows)),
        "best_without_phrase_control_row": _public_row(_select_best(no_phrase_rows)),
        "best_generated_composite_row": _public_row(
            _select_best(
                row for row in generated_rows if row.get("source_mode") == "generated_composite"
            )
        ),
        "best_generated_active_only_row": _public_row(
            _select_best(
                row for row in generated_rows if row.get("source_mode") == "generated_active_only"
            )
        ),
        "best_generated_no_phrase_row": _public_row(
            _select_best(
                row for row in generated_rows if row.get("source_mode") == "generated_no_phrase"
            )
        ),
        "best_generated_no_shadow_row": _public_row(
            _select_best(
                row for row in generated_rows if row.get("source_mode") == "generated_no_shadow"
            )
        ),
        "simplification_candidates": simplification_candidates,
    }


def _build_recommendation(report: Mapping[str, object]) -> str:
    audit = (
        report.get("assumption_audit")
        if isinstance(report.get("assumption_audit"), Mapping)
        else {}
    )
    oracle = (
        audit.get("best_oracle_row") if isinstance(audit.get("best_oracle_row"), Mapping) else {}
    )
    candidate = (
        audit.get("best_candidate_source_row")
        if isinstance(audit.get("best_candidate_source_row"), Mapping)
        else {}
    )
    simplified = (
        audit.get("best_viable_without_surface_pos_row")
        if isinstance(audit.get("best_viable_without_surface_pos_row"), Mapping)
        else {}
    )
    if not candidate:
        return "No candidate source row was available; resolve source inputs before tuning."
    candidate_harmful = int(candidate.get("harmful_replace_count") or 0)
    candidate_false = int(candidate.get("false_abstain_count") or 0)
    oracle_false = int(oracle.get("false_abstain_count") or 0)
    simplified_harmful = int(simplified.get("harmful_replace_count") or 0)
    simplified_false = int(simplified.get("false_abstain_count") or 0)
    notes: list[str] = []
    if candidate_harmful == 0:
        notes.append("candidate source rows can preserve the zero-harm constraint")
    else:
        notes.append("candidate source rows still leak harmful replacements")
    if oracle and candidate_false > oracle_false:
        notes.append(
            "there is still an oracle-vs-source gap, so source coverage remains a first-order node"
        )
    if simplified and simplified_harmful == 0 and simplified_false <= candidate_false:
        notes.append("a simplified no-surface-POS candidate matches or beats the current best")
    else:
        notes.append("the current best still depends on the richer guard stack")
    return "; ".join(notes) + "."


def _best_by_field(rows: Sequence[Mapping[str, object]], field: str) -> dict[str, object]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        key = str(row.get(field) or "").strip()
        if key:
            grouped.setdefault(key, []).append(row)
    return {
        key: _public_row(_select_best(group_rows)) for key, group_rows in sorted(grouped.items())
    }


def _candidate_rows(rows: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    return [row for row in rows if row.get("source_class") == "candidate_source"]


def _select_best(rows: object) -> Mapping[str, object] | None:
    materialized = [
        row
        for row in rows or ()
        if isinstance(row, Mapping) and int(row.get("cases_total") or 0) > 0
    ]
    if not materialized:
        return None
    return sorted(materialized, key=_rank_key)[0]


def _rank_key(row: Mapping[str, object]) -> tuple[float, int, int, float, float, str]:
    return (
        float(row.get("objective_score") or 0.0),
        int(row.get("harmful_replace_count") or 0),
        int(row.get("false_abstain_count") or 0),
        -float(row.get("replace_recall") or 0.0),
        -float(row.get("decision_accuracy") or 0.0),
        str(row.get("matrix_id") or ""),
    )


def _objective_score(row: Mapping[str, object]) -> float:
    harmful = int(row.get("harmful_replace_count") or 0)
    false_abstain = int(row.get("false_abstain_count") or 0)
    recall_penalty = 1.0 - float(row.get("replace_recall") or 0.0)
    accuracy_penalty = 1.0 - float(row.get("decision_accuracy") or 0.0)
    return round((harmful * 1000.0) + (false_abstain * 10.0) + recall_penalty + accuracy_penalty, 6)


def _public_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(row, Mapping):
        return None
    keys = (
        "matrix_id",
        "source_mode",
        "source_class",
        "scope",
        "scorer_id",
        "context_view",
        "min_active_score",
        "min_margin",
        "decision_shape",
        "cases_total",
        "harmful_replace_count",
        "false_abstain_count",
        "replace_recall",
        "decision_accuracy",
        "objective_score",
        "source_coverage",
        "harmful_replace_case_ids",
        "false_abstain_case_ids",
    )
    return {key: row.get(key) for key in keys}


def _normalize_supported_strings(
    values: Sequence[str],
    supported: Sequence[str] | frozenset[str],
    label: str,
) -> list[str]:
    supported_set = {str(value) for value in supported}
    normalized = [value for value in _normalize_string_list(values) if value in supported_set]
    if not normalized:
        raise ValueError(f"The ablation matrix requires at least one supported {label}.")
    return normalized


def _normalize_string_list(values: Sequence[str] | str) -> list[str]:
    if isinstance(values, str):
        raw_values = values.split(",")
    else:
        raw_values = values
    seen: set[str] = set()
    normalized: list[str] = []
    for value in raw_values:
        text = str(value or "").strip()
        if text and text not in seen:
            normalized.append(text)
            seen.add(text)
    return normalized


def _parse_float_grid(value: str) -> list[float]:
    return [float(item) for item in _normalize_string_list(value)]


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def _round_float(value: object) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    args = _parse_args()
    queue_payload = _load_json(args.queue_json)
    dataset_payload = load_sentence_veto_dataset(args.dataset)
    report = build_prototype_ablation_matrix_report(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        source_modes=_normalize_string_list(args.source_modes),
        scopes=_normalize_string_list(args.scopes),
        scorers=_normalize_string_list(args.scorers),
        context_views=_normalize_string_list(args.context_views),
        min_active_scores=_parse_float_grid(args.min_active_grid),
        min_margins=_parse_float_grid(args.min_margin_grid),
        reverse_aux_path=args.reverse_aux_json,
        generated_composite_path=args.generated_composite_json,
        extra_evidence_paths=args.evidence_batch_json,
        window_tokens=max(0, int(args.window_tokens)),
        mask_token=str(args.mask_token or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_prototype_ablation_matrix_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
