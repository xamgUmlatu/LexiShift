#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_formula_shape_bakeoff_en_es import (
    _as_mapping,
    _escape_md,
    _load_json,
    _mapping_rows,
    _round4,
    _safe_float,
    _sequence,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_MANIFEST = TEST_INPUTS_ROOT / "semantic_veto_sampling_expansion_design_en_es.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_sampling_expansion_design_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_sampling_expansion_design_en_es_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render a scientific semantic-veto sampling expansion design that keeps "
            "representative, stratified, targeted, control, discovery, and locked "
            "lanes separate."
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
    curve_path = _resolve_repo_path(inputs.get("curve_guided_expansion_json"))
    policy_path = _resolve_repo_path(inputs.get("product_quality_policy_json"))
    report = build_sampling_expansion_design_report(
        manifest=manifest,
        curve_payload=_load_json(curve_path),
        policy_payload=_load_json(policy_path),
        manifest_path=args.manifest,
        curve_path=curve_path,
        policy_path=policy_path,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_sampling_expansion_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_sampling_expansion_design_report(
    *,
    manifest: Mapping[str, object],
    curve_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    manifest_path: Path | None = None,
    curve_path: Path | None = None,
    policy_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    lanes = _mapping_rows(manifest.get("lanes"))
    queue_rows = _mapping_rows(curve_payload.get("expansion_queue"))
    issues = _issues(manifest=manifest, lanes=lanes, queue_rows=queue_rows)
    lane_reports = [_lane_report(lane=lane, queue_rows=queue_rows) for lane in lanes]
    stage_plan = [_stage_public(row) for row in _mapping_rows(manifest.get("stage_plan"))]
    totals = _row_budget_totals(lane_reports)
    return {
        "schema_version": 1,
        "status": "review" if issues else "ok",
        "decision": (
            "sampling_expansion_design_established"
            if not issues
            else "sampling_expansion_design_incomplete"
        ),
        "generated_at": generated_at,
        "pair": str(policy_payload.get("pair") or curve_payload.get("pair") or "en-es"),
        "inputs": {
            "manifest_path": _repo_path(manifest_path),
            "curve_guided_expansion_path": _repo_path(curve_path),
            "product_quality_policy_path": _repo_path(policy_path),
            "curve_guided_decision": str(curve_payload.get("decision") or ""),
            "product_policy_id": str(policy_payload.get("policy_id") or ""),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
            "random_seed": str(manifest.get("random_seed") or ""),
            "split_policy": _as_mapping(manifest.get("split_policy")),
            "global_rules": [str(item) for item in _sequence(manifest.get("global_rules"))],
            "core_principle": (
                "Representative rows estimate product quality, stratified rows draw "
                "the difficulty surface, targeted rows test mechanisms, controls "
                "detect leakage, and locked rows validate after selection."
            ),
        },
        "summary": {
            "issues": issues,
            "lane_count": len(lane_reports),
            "curve_queue_rows_read": len(queue_rows),
            "curve_queue_priority_counts": dict(
                Counter(str(row.get("priority") or "") for row in queue_rows)
            ),
            "row_budget_totals": totals,
            "locked_eval_share": _round4(
                totals["locked_eval_rows"] / totals["total_rows"] if totals["total_rows"] else 0.0
            ),
            "representative_locked_rows": sum(
                int(row.get("locked_eval_rows") or 0)
                for row in lane_reports
                if row.get("lane_type") == "representative_random"
            ),
            "targeted_priority_scope": _targeted_priority_scope(lanes),
        },
        "lane_reports": lane_reports,
        "stratified_cells": _stratified_cells(lanes),
        "targeted_curve_cells": _targeted_curve_cells(lanes=lanes, queue_rows=queue_rows),
        "bias_controls": _bias_controls(lane_reports),
        "stage_plan": stage_plan,
        "acceptance_link": {
            "positive_allow_rate_min": _as_mapping(policy_payload.get("acceptance")).get(
                "positive_allow_rate_min"
            ),
            "negative_abstain_rate_min": _as_mapping(policy_payload.get("acceptance")).get(
                "negative_abstain_rate_min"
            ),
            "representative_lane_required_for_promotion": _as_mapping(
                policy_payload.get("acceptance")
            ).get("representative_lane_required_for_promotion"),
            "promotion_claim_rule": (
                "Only the representative locked lane can estimate product quality; "
                "stratified and targeted lanes can explain or improve it."
            ),
        },
        "next_steps": [
            "Freeze this sampling design before authoring additional rows.",
            "Materialize the representative sampling frame and P0 manual rows first.",
            "Run leakage/control prompts before any LLM generation spend.",
            "After P0 discovery rows are scored, rerun the difficulty surface and decide whether P1 expansion is still justified.",
        ],
    }


def render_sampling_expansion_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    totals = _as_mapping(summary.get("row_budget_totals"))
    lines = [
        "# en-es Semantic Veto Sampling Expansion Design",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Lanes: `{summary.get('lane_count', 0)}`",
        f"- Curve queue rows read: `{summary.get('curve_queue_rows_read', 0)}`",
        f"- Planned total rows: `{totals.get('total_rows', 0)}`",
        f"- Locked-eval share: `{_metric(summary.get('locked_eval_share'))}`",
        "",
        "## Lane Budgets",
        "",
        _lane_table(report.get("lane_reports")),
        "",
        "## Stratified Grid",
        "",
        _stratified_table(report.get("stratified_cells")),
        "",
        "## Targeted Curve Cells",
        "",
        _targeted_table(report.get("targeted_curve_cells")),
        "",
        "## Bias Controls",
        "",
    ]
    lines.extend(f"- `{item}`" for item in _sequence(report.get("bias_controls")))
    lines.extend(["", "## Methodology", ""])
    methodology = _as_mapping(report.get("methodology"))
    lines.append(f"- Core principle: {methodology.get('core_principle', '')}")
    lines.append(f"- Random seed: `{methodology.get('random_seed', '')}`")
    for item in _sequence(methodology.get("global_rules")):
        lines.append(f"- {item}")
    lines.extend(["", "## Stage Plan", ""])
    lines.extend(_stage_lines(report.get("stage_plan")))
    lines.extend(["", "## Acceptance Link", ""])
    acceptance = _as_mapping(report.get("acceptance_link"))
    for key, value in acceptance.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _issues(
    *,
    manifest: Mapping[str, object],
    lanes: Sequence[Mapping[str, object]],
    queue_rows: Sequence[Mapping[str, object]],
) -> list[str]:
    issues = []
    if not str(manifest.get("random_seed") or ""):
        issues.append("manifest_missing_random_seed")
    lane_types = {str(row.get("lane_type") or "") for row in lanes}
    required = {
        "representative_random",
        "stratified_balanced",
        "targeted_curve_expansion",
        "negative_control",
    }
    for lane_type in sorted(required - lane_types):
        issues.append(f"missing_lane_type:{lane_type}")
    if not queue_rows:
        issues.append("curve_guided_report_has_no_expansion_queue")
    for lane in lanes:
        if not str(lane.get("lane_id") or ""):
            issues.append("lane_missing_lane_id")
        if not str(lane.get("claim_supported") or ""):
            issues.append(f"{lane.get('lane_id', 'unknown')}:missing_claim_supported")
        if not _sequence(lane.get("bias_controls")):
            issues.append(f"{lane.get('lane_id', 'unknown')}:missing_bias_controls")
    if not any(
        row.get("lane_type") == "representative_random"
        and _safe_float(row.get("locked_eval_rows")) > 0
        for row in lanes
    ):
        issues.append("representative_lane_has_no_locked_eval_rows")
    return issues


def _lane_report(
    *,
    lane: Mapping[str, object],
    queue_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    lane_type = str(lane.get("lane_type") or "")
    if lane_type == "stratified_balanced":
        budget = _stratified_budget(lane)
    elif lane_type == "targeted_curve_expansion":
        budget = _targeted_budget(lane=lane, queue_rows=queue_rows)
    else:
        budget = _explicit_budget(lane)
    total = sum(budget.values())
    return {
        "lane_id": str(lane.get("lane_id") or ""),
        "lane_type": lane_type,
        "purpose": str(lane.get("purpose") or ""),
        "claim_supported": str(lane.get("claim_supported") or ""),
        "sampling_frame": str(lane.get("sampling_frame") or ""),
        "selection_method": str(lane.get("selection_method") or ""),
        "context_policy": str(lane.get("context_policy") or ""),
        "manual_discovery_rows": budget["manual_discovery_rows"],
        "llm_discovery_rows": budget["llm_discovery_rows"],
        "locked_eval_rows": budget["locked_eval_rows"],
        "total_rows": total,
        "uses_random_sampling": lane_type in {"representative_random", "stratified_balanced"},
        "is_representative": lane_type == "representative_random",
        "can_support_promotion_metric": lane_type == "representative_random",
        "can_select_hypotheses": lane_type in {"stratified_balanced", "targeted_curve_expansion"},
        "bias_controls": [str(item) for item in _sequence(lane.get("bias_controls"))],
    }


def _explicit_budget(lane: Mapping[str, object]) -> dict[str, int]:
    return {
        "manual_discovery_rows": int(lane.get("manual_discovery_rows") or 0),
        "llm_discovery_rows": int(lane.get("llm_discovery_rows") or 0),
        "locked_eval_rows": int(lane.get("locked_eval_rows") or 0),
    }


def _stratified_budget(lane: Mapping[str, object]) -> dict[str, int]:
    cell_count = _stratified_cell_count(lane)
    rows_per_cell = _as_mapping(lane.get("rows_per_cell"))
    return {
        "manual_discovery_rows": cell_count * int(rows_per_cell.get("manual_discovery_rows") or 0),
        "llm_discovery_rows": cell_count * int(rows_per_cell.get("llm_discovery_rows") or 0),
        "locked_eval_rows": cell_count * int(rows_per_cell.get("locked_eval_rows") or 0),
    }


def _stratified_cell_count(lane: Mapping[str, object]) -> int:
    return (
        len(_sequence(lane.get("case_types")))
        * len(_sequence(lane.get("source_rank_bins")))
        * len(_sequence(lane.get("polysemy_bands")))
    )


def _targeted_budget(
    *,
    lane: Mapping[str, object],
    queue_rows: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    priorities = set(str(item) for item in _sequence(lane.get("priority_scope")) if str(item))
    selected = [
        row for row in queue_rows if not priorities or str(row.get("priority") or "") in priorities
    ]
    return {
        "manual_discovery_rows": sum(
            int(row.get("manual_discovery_rows") or 0) for row in selected
        ),
        "llm_discovery_rows": sum(int(row.get("llm_discovery_rows") or 0) for row in selected),
        "locked_eval_rows": sum(int(row.get("locked_eval_rows") or 0) for row in selected),
    }


def _row_budget_totals(lane_reports: Sequence[Mapping[str, object]]) -> dict[str, int]:
    manual = sum(int(row.get("manual_discovery_rows") or 0) for row in lane_reports)
    llm = sum(int(row.get("llm_discovery_rows") or 0) for row in lane_reports)
    locked = sum(int(row.get("locked_eval_rows") or 0) for row in lane_reports)
    return {
        "manual_discovery_rows": manual,
        "llm_discovery_rows": llm,
        "locked_eval_rows": locked,
        "discovery_rows": manual + llm,
        "total_rows": manual + llm + locked,
    }


def _stratified_cells(lanes: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows = []
    for lane in lanes:
        if str(lane.get("lane_type") or "") != "stratified_balanced":
            continue
        rows_per_cell = _as_mapping(lane.get("rows_per_cell"))
        for case_type in _sequence(lane.get("case_types")):
            for rank_bin in _sequence(lane.get("source_rank_bins")):
                for polysemy_band in _sequence(lane.get("polysemy_bands")):
                    rows.append(
                        {
                            "lane_id": lane.get("lane_id"),
                            "case_type": str(case_type),
                            "source_rank_bin": str(rank_bin),
                            "polysemy_band": str(polysemy_band),
                            "manual_discovery_rows": int(
                                rows_per_cell.get("manual_discovery_rows") or 0
                            ),
                            "llm_discovery_rows": int(rows_per_cell.get("llm_discovery_rows") or 0),
                            "locked_eval_rows": int(rows_per_cell.get("locked_eval_rows") or 0),
                        }
                    )
    return rows


def _targeted_curve_cells(
    *,
    lanes: Sequence[Mapping[str, object]],
    queue_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    priorities = _targeted_priority_scope(lanes)
    selected = [
        row for row in queue_rows if not priorities or str(row.get("priority") or "") in priorities
    ]
    result = []
    for row in selected:
        result.append(
            {
                "priority": row.get("priority"),
                "manual_case_type": row.get("manual_case_type"),
                "heuristic_group": row.get("heuristic_group"),
                "scorer_id": row.get("scorer_id"),
                "source_rank_bin": row.get("source_rank_bin"),
                "polysemy_band": row.get("polysemy_band"),
                "expansion_score": row.get("expansion_score"),
                "manual_discovery_rows": row.get("manual_discovery_rows"),
                "llm_discovery_rows": row.get("llm_discovery_rows"),
                "locked_eval_rows": row.get("locked_eval_rows"),
                "reasons": row.get("reasons"),
                "triggers": row.get("triggers"),
            }
        )
    result.sort(
        key=lambda row: (
            {"P0": 0, "P1": 1, "P2": 2}.get(str(row.get("priority") or ""), 9),
            -_safe_float(row.get("expansion_score")),
            str(row.get("manual_case_type") or ""),
        )
    )
    return result


def _targeted_priority_scope(lanes: Sequence[Mapping[str, object]]) -> list[str]:
    for lane in lanes:
        if str(lane.get("lane_type") or "") == "targeted_curve_expansion":
            return [str(item) for item in _sequence(lane.get("priority_scope")) if str(item)]
    return []


def _bias_controls(lane_reports: Sequence[Mapping[str, object]]) -> list[str]:
    controls: list[str] = []
    for row in lane_reports:
        for item in _sequence(row.get("bias_controls")):
            controls.append(str(item))
    return sorted(set(controls))


def _stage_public(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "stage_id": str(row.get("stage_id") or ""),
        "entry_condition": str(row.get("entry_condition") or ""),
        "exit_condition": str(row.get("exit_condition") or ""),
    }


def _lane_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Lane | Type | Claim | Manual discovery | LLM discovery | Locked eval | Representative? |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('lane_id') or ''))}`",
                    f"`{_escape_md(str(row.get('lane_type') or ''))}`",
                    f"`{_escape_md(str(row.get('claim_supported') or ''))}`",
                    str(row.get("manual_discovery_rows") or 0),
                    str(row.get("llm_discovery_rows") or 0),
                    str(row.get("locked_eval_rows") or 0),
                    "`yes`" if row.get("is_representative") else "`no`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _stratified_table(value: object, *, limit: int = 24) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Case type | Rank bin | Polysemy | Manual | LLM | Locked |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('case_type') or ''))}`",
                    f"`{_escape_md(str(row.get('source_rank_bin') or ''))}`",
                    f"`{_escape_md(str(row.get('polysemy_band') or ''))}`",
                    str(row.get("manual_discovery_rows") or 0),
                    str(row.get("llm_discovery_rows") or 0),
                    str(row.get("locked_eval_rows") or 0),
                ]
            )
            + " |"
        )
    if len(rows) > limit:
        lines.append(f"| _{len(rows) - limit} more cells omitted_ |  |  |  |  |  |")
    return "\n".join(lines)


def _targeted_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Priority | Case type | Group | Scorer | Score | Manual | LLM | Locked |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('priority') or ''))}`",
                    f"`{_escape_md(str(row.get('manual_case_type') or ''))}`",
                    f"`{_escape_md(str(row.get('heuristic_group') or ''))}`",
                    f"`{_escape_md(str(row.get('scorer_id') or ''))}`",
                    _metric(row.get("expansion_score")),
                    str(row.get("manual_discovery_rows") or 0),
                    str(row.get("llm_discovery_rows") or 0),
                    str(row.get("locked_eval_rows") or 0),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _stage_lines(value: object) -> list[str]:
    lines = []
    for row in _mapping_rows(value):
        lines.append(
            f"- `{row.get('stage_id', '')}`: entry `{row.get('entry_condition', '')}`; "
            f"exit `{row.get('exit_condition', '')}`"
        )
    return lines or ["_No stages._"]


def _resolve_repo_path(value: object) -> Path:
    path = Path(str(value or ""))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _metric(value: object) -> str:
    if value is None:
        return ""
    return f"{_safe_float(value):.4f}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
