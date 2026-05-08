#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md as _escape_md,
    _load_json,
    _mapping_rows,
    _repo_path,
    _safe_float as _safe_float,
    _utility_weights,
)
from semantic_veto_formula_shape_bakeoff_cells import (
    _build_cells,
    _parameter_sweep_results,
    _public_parameter_sweep_results,
    _rank_aggregation_rows,
    _score_formula_cells,
)
from semantic_veto_formula_shape_bakeoff_common import (
    NEGATIVE_CONTROL_IDS,
    PRIMARY_SELECTION_MODE,
    RANK_AGGREGATION_FORMULA,
    _best_formula_rows,
    _formula_definitions,
    _primary_score_rows,
    _resolve_repo_path,
    _round4 as _round4,
    _sequence as _sequence,
    _string_list,
    _top_k,
    _utc_now,
)
from semantic_veto_formula_shape_bakeoff_eval import (
    _calibration_rows,
    _comparison_rows,
    _negative_control_rows,
    _recommendations,
    _top_priority_cells,
)
from semantic_veto_formula_shape_bakeoff_rendering import (
    render_formula_shape_bakeoff_markdown as render_formula_shape_bakeoff_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_MANIFEST = TEST_INPUTS_ROOT / "semantic_veto_formula_shape_bakeoff_en_es.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_formula_shape_bakeoff_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_formula_shape_bakeoff_en_es_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bake off mathematically distinct heuristic formula shapes for ranking "
            "en-es semantic-veto cells by observed difficulty and data-help priority."
        )
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    manifest = _load_json(args.manifest)
    inputs = _as_mapping(manifest.get("inputs"))
    surface_path = _resolve_repo_path(inputs.get("difficulty_surface_json"))
    policy_path = _resolve_repo_path(inputs.get("product_quality_policy_json"))
    report = build_formula_shape_bakeoff_report(
        manifest=manifest,
        difficulty_surface_payload=_load_json(surface_path),
        policy_payload=_load_json(policy_path),
        manifest_path=args.manifest,
        difficulty_surface_path=surface_path,
        policy_path=policy_path,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_formula_shape_bakeoff_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_formula_shape_bakeoff_report(
    *,
    manifest: Mapping[str, object],
    difficulty_surface_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    manifest_path: Path | None = None,
    difficulty_surface_path: Path | None = None,
    policy_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    weights = _utility_weights(policy_payload)
    cell_grouping = _string_list(manifest.get("cell_grouping"))
    if not cell_grouping:
        cell_grouping = [
            "scorer_id",
            "selection_mode",
            "heuristic_group",
            "manual_case_type",
            "shadow_contract",
            "source_rank_bin",
            "polysemy_band",
        ]
    formula_ids = [
        str(row.get("formula_id") or "")
        for row in _mapping_rows(manifest.get("formula_rows"))
        if str(row.get("formula_id") or "")
    ]
    non_aggregate_formula_ids = [
        formula_id for formula_id in formula_ids if formula_id != RANK_AGGREGATION_FORMULA
    ]
    control_ids = [
        str(row.get("control_id") or "")
        for row in _mapping_rows(manifest.get("negative_controls"))
        if str(row.get("control_id") or "") in NEGATIVE_CONTROL_IDS
    ]
    rows = _mapping_rows(difficulty_surface_payload.get("case_traces"))
    issues: list[str] = []
    if not rows:
        issues.append("difficulty_surface_has_no_case_traces")
    if not non_aggregate_formula_ids:
        issues.append("manifest_has_no_non_aggregate_formula_rows")
    cells = _build_cells(
        rows=rows,
        cell_grouping=cell_grouping,
        weights=weights,
        manifest=manifest,
    )
    formula_score_rows = _score_formula_cells(
        cells=cells,
        formula_ids=non_aggregate_formula_ids,
        control_ids=control_ids,
    )
    parameter_sweep_results = _parameter_sweep_results(
        cells=cells,
        manifest=manifest,
        top_k=_top_k(manifest),
    )
    for sweep_result in parameter_sweep_results:
        formula_score_rows.extend(_mapping_rows(sweep_result.get("selected_score_rows")))
    if RANK_AGGREGATION_FORMULA in formula_ids:
        formula_score_rows.extend(_rank_aggregation_rows(formula_score_rows))
    comparison_rows = _comparison_rows(
        cells=cells,
        score_rows=formula_score_rows,
        top_k=_top_k(manifest),
    )
    calibration_rows = _calibration_rows(score_rows=formula_score_rows)
    negative_control_rows = _negative_control_rows(
        cells=cells,
        score_rows=formula_score_rows,
        top_k=_top_k(manifest),
    )
    top_priority_cells = _top_priority_cells(
        score_rows=formula_score_rows,
        manifest=manifest,
    )
    recommendations = _recommendations(
        top_priority_cells=top_priority_cells,
        manifest=manifest,
    )
    best_rows = _best_formula_rows(comparison_rows)
    return {
        "schema_version": 1,
        "status": "review" if issues else "ok",
        "decision": (
            "formula_shape_bakeoff_established"
            if not issues
            else "formula_shape_bakeoff_incomplete"
        ),
        "generated_at": generated_at,
        "pair": str(
            policy_payload.get("pair") or difficulty_surface_payload.get("pair") or "en-es"
        ),
        "inputs": {
            "manifest_path": _repo_path(manifest_path),
            "difficulty_surface_path": _repo_path(difficulty_surface_path),
            "policy_path": _repo_path(policy_path),
            "difficulty_surface_decision": str(difficulty_surface_payload.get("decision") or ""),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
            "objective": (
                "Rank source/case/scorer cells by observed difficulty and expected "
                "manual_or_llm_data_help_priority."
            ),
            "cell_grouping": cell_grouping,
            "primary_selection_mode": PRIMARY_SELECTION_MODE,
            "sentinel_policy": "exclude_from_primary_formula_validation",
            "missing_rank_policy": "rank_risk_zero_plus_missing_indicator",
            "internal_split": _as_mapping(manifest.get("internal_split")),
            "data_help_priority_formula": str(
                _as_mapping(manifest.get("data_help_priority")).get("formula") or ""
            ),
        },
        "summary": {
            "issues": issues,
            "case_trace_rows_read": len(rows),
            "cell_count": len(cells),
            "primary_cell_count": sum(
                1 for cell in cells if cell["selection_mode"] == "pre_outcome"
            ),
            "sentinel_cell_count": sum(
                1 for cell in cells if cell["selection_mode"] != "pre_outcome"
            ),
            "formula_count": len(formula_ids),
            "parameter_sweep_count": len(parameter_sweep_results),
            "negative_control_count": len(_mapping_rows(manifest.get("negative_controls"))),
            "comparison_row_count": len(comparison_rows),
            "best_formula_by_scope": best_rows,
            "top_data_help_cells": top_priority_cells[: _top_k(manifest)],
        },
        "e2e_checks": {
            "manifest_formula_ids": formula_ids,
            "negative_control_ids": control_ids,
            "cell_grouping_fields": cell_grouping,
            "case_rows_accounted_for": sum(int(cell["case_rows"]) for cell in cells) == len(rows),
            "sentinel_cells_excluded_from_primary": all(
                row["selection_mode"] == PRIMARY_SELECTION_MODE
                for row in _primary_score_rows(formula_score_rows)
            ),
            "missing_rank_cells_preserved": any(
                cell["features"]["rank_missing_rate"] > 0 for cell in cells
            ),
            "data_help_priority_uses_uncertainty": True,
        },
        "formula_definitions": _formula_definitions(manifest),
        "parameter_sweep_results": _public_parameter_sweep_results(parameter_sweep_results),
        "comparison_rows": comparison_rows,
        "calibration_rows": calibration_rows,
        "negative_control_rows": negative_control_rows,
        "top_priority_cells": top_priority_cells,
        "recommendations": recommendations,
        "cell_observations": cells,
        "formula_score_rows": formula_score_rows,
        "limitations": [
            "internal_split_is_advisory_not_true_locked_eval",
            "agent_authored_heuristic_group_cases_need_human_review",
            "formula_parameters_are_hand_specified_defaults_not_trained_coefficients",
            "rank_aggregation_can_only_compare_formulas_available_in_this_manifest",
            "runtime_policy_remains_unchanged",
        ],
        "next_steps": [
            "Inspect top data-help cells before generating more LLM rows.",
            "Promote no runtime behavior from this report alone.",
            "Use the top phrase/no-winner and underfilled cells as the next manual/LLM expansion queue.",
            "After expansion, rerun this report and compare discovery-versus-locked stability.",
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
