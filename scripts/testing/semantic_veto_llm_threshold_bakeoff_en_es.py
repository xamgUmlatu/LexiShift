#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _load_json,
    _repo_path,
    _resolve_repo_path,
    _safe_float,
    _utility_weights,
    score_product_outcome_counts,
)
from semantic_veto_veto_only_probe_en_es import _mapping_rows


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_POLICY = TEST_INPUTS_ROOT / "semantic_veto_product_quality_policy_en_es.json"
DEFAULT_LLM_SCORING = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_scoring_en_es_latest.json"
DEFAULT_VALIDATION_REPORTS = (
    TEST_OUTPUTS_ROOT
    / "semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout_validation_latest.json",
    TEST_OUTPUTS_ROOT
    / "semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase_validation_latest.json",
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_llm_threshold_bakeoff_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_llm_threshold_bakeoff_en_es_latest.md"
DEFAULT_LEAD_GRID = "-0.10,-0.075,-0.05,-0.025,0.00,0.025,0.05,0.075,0.10,0.125,0.15"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bake off separate shadow and phrase lead thresholds on LLM discovery rows, "
            "then report locked-eval and manual/stress behavior without using those lanes "
            "for candidate selection."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--llm-scoring-json", type=Path, default=DEFAULT_LLM_SCORING)
    parser.add_argument(
        "--validation-report-json",
        type=Path,
        action="append",
        default=[],
        help=(
            "Manual/stress validation report with configured_case_results. Defaults to "
            "the current wave7 active/shadow and phrase validation reports."
        ),
    )
    parser.add_argument("--shadow-lead-grid", default=DEFAULT_LEAD_GRID)
    parser.add_argument("--phrase-lead-grid", default=DEFAULT_LEAD_GRID)
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    validation_paths = (
        tuple(args.validation_report_json)
        if args.validation_report_json
        else DEFAULT_VALIDATION_REPORTS
    )
    report = build_threshold_bakeoff_report(
        policy_payload=_load_json(args.policy_json),
        llm_scoring_payload=_load_json(args.llm_scoring_json),
        validation_sources=[{"path": path} for path in validation_paths],
        policy_path=args.policy_json,
        llm_scoring_path=args.llm_scoring_json,
        shadow_lead_grid=_parse_float_grid(args.shadow_lead_grid),
        phrase_lead_grid=_parse_float_grid(args.phrase_lead_grid),
        top_n=max(1, int(args.top_n)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_threshold_bakeoff_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_threshold_bakeoff_report(
    *,
    policy_payload: Mapping[str, object],
    llm_scoring_payload: Mapping[str, object],
    validation_sources: Sequence[Mapping[str, object]],
    policy_path: Path | None = None,
    llm_scoring_path: Path | None = None,
    shadow_lead_grid: Sequence[float] = (),
    phrase_lead_grid: Sequence[float] = (),
    top_n: int = 12,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    weights = _utility_weights(policy_payload)
    acceptance = _as_mapping(policy_payload.get("acceptance"))
    normalized_shadow_grid = _normalize_float_grid(shadow_lead_grid)
    normalized_phrase_grid = _normalize_float_grid(phrase_lead_grid)
    llm_rows = [
        _normalize_case_row(row, lane_id=f"llm_{row.get('split') or 'unknown'}")
        for row in _mapping_rows(llm_scoring_payload.get("case_results"))
    ]
    validation_reports = [
        _load_validation_source(source, index=index)
        for index, source in enumerate(validation_sources)
    ]
    validation_rows = [
        row for source in validation_reports for row in _mapping_rows(source.get("case_rows"))
    ]
    candidate_rows = []
    for shadow_lead_min in normalized_shadow_grid:
        for phrase_lead_min in normalized_phrase_grid:
            row = _candidate_row(
                shadow_lead_min=shadow_lead_min,
                phrase_lead_min=phrase_lead_min,
                llm_rows=llm_rows,
                validation_rows=validation_rows,
                weights=weights,
                acceptance=acceptance,
            )
            candidate_rows.append(row)

    selected = _select_discovery_candidate(candidate_rows)
    incumbent = _find_candidate(candidate_rows, shadow_lead_min=0.05, phrase_lead_min=0.05)
    all_lane_rows = [
        row
        for row in candidate_rows
        if _target_status(row, "llm_discovery") == "pass"
        and _target_status(row, "llm_locked_eval") == "pass"
        and _target_status(row, "manual_stress_all") == "pass"
    ]
    decision = (
        "separate_threshold_discovery_candidate_found"
        if selected
        else "separate_threshold_discovery_candidate_not_found"
    )
    return {
        "schema_version": 1,
        "status": "ok" if selected else "review",
        "decision": decision,
        "generated_at": generated_at,
        "pair": str(policy_payload.get("pair") or "en-es"),
        "policy": {
            "path": _repo_path(policy_path),
            "policy_id": str(policy_payload.get("policy_id") or ""),
            "acceptance": dict(acceptance),
            "utility_weights": weights,
        },
        "inputs": {
            "llm_scoring_path": _repo_path(llm_scoring_path),
            "validation_report_paths": [
                str(source.get("path") or "") for source in validation_reports
            ],
        },
        "methodology": {
            "selection_lane": "llm_discovery",
            "heldout_lanes": ["llm_locked_eval", "manual_stress_all"],
            "selection_rule": (
                "Select the highest-utility candidate that passes product targets on "
                "llm_discovery only; report locked-eval and stress behavior after selection."
            ),
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
        },
        "e2e_checks": {
            "calculus_source": (
                "scripts/testing/semantic_veto_product_quality_en_es.py::"
                "score_product_outcome_counts"
            ),
            "llm_case_rows_read": len(llm_rows),
            "llm_discovery_rows_read": sum(1 for row in llm_rows if row["split"] == "discovery"),
            "llm_locked_eval_rows_read": sum(
                1 for row in llm_rows if row["split"] == "locked_eval"
            ),
            "validation_reports_read": len(validation_reports),
            "manual_stress_rows_read": len(validation_rows),
            "candidate_rows_emitted": len(candidate_rows),
            "shadow_lead_grid": normalized_shadow_grid,
            "phrase_lead_grid": normalized_phrase_grid,
        },
        "summary": {
            "row_count": len(candidate_rows),
            "top_n": max(1, int(top_n)),
            "selected_discovery_candidate": _public_candidate_row(selected),
            "incumbent_candidate": _public_candidate_row(incumbent),
            "best_all_lane_advisory": _public_candidate_row(
                sorted(all_lane_rows, key=_all_lane_rank_key)[0] if all_lane_rows else None
            ),
            "all_lane_pass_count": len(all_lane_rows),
            "recommendation": _recommendation(
                selected=selected,
                incumbent=incumbent,
                all_lane_rows=all_lane_rows,
            ),
        },
        "validation_sources": [_public_validation_source(source) for source in validation_reports],
        "top_discovery_rows": [
            _public_candidate_row(row)
            for row in sorted(candidate_rows, key=_discovery_rank_key)[: max(1, int(top_n))]
        ],
        "top_all_lane_rows": [
            _public_candidate_row(row)
            for row in sorted(candidate_rows, key=_all_lane_rank_key)[: max(1, int(top_n))]
        ],
        "rows": [
            _public_candidate_row(row) for row in sorted(candidate_rows, key=_all_lane_rank_key)
        ],
    }


def render_threshold_bakeoff_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    selected = _as_mapping(summary.get("selected_discovery_candidate"))
    incumbent = _as_mapping(summary.get("incumbent_candidate"))
    lines = [
        "# en-es Semantic Veto LLM Threshold Bakeoff",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Selection lane: `{_as_mapping(report.get('methodology')).get('selection_lane', '')}`",
        f"- Candidate rows: `{summary.get('row_count', 0)}`",
        f"- All-lane pass rows: `{summary.get('all_lane_pass_count', 0)}`",
        "",
        "## E2E Checks",
        "",
        _checks_table(report.get("e2e_checks")),
        "",
        "## Selected Discovery Candidate",
        "",
        _candidate_detail(selected),
        "",
        "## Incumbent",
        "",
        _candidate_detail(incumbent),
        "",
        "## Top Discovery Rows",
        "",
        _candidate_table(report.get("top_discovery_rows")),
        "",
        "## Top All-Lane Rows",
        "",
        _candidate_table(report.get("top_all_lane_rows")),
        "",
        "## Validation Sources",
        "",
        _source_table(report.get("validation_sources")),
        "",
        "## Recommendation",
        "",
    ]
    for item in _sequence(summary.get("recommendation")):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _candidate_row(
    *,
    shadow_lead_min: float,
    phrase_lead_min: float,
    llm_rows: Sequence[Mapping[str, object]],
    validation_rows: Sequence[Mapping[str, object]],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    evaluated_llm = [
        _evaluate_case(row, shadow_lead_min=shadow_lead_min, phrase_lead_min=phrase_lead_min)
        for row in llm_rows
    ]
    evaluated_validation = [
        _evaluate_case(row, shadow_lead_min=shadow_lead_min, phrase_lead_min=phrase_lead_min)
        for row in validation_rows
    ]
    metrics = {
        "llm_all": _metrics(evaluated_llm, weights=weights, acceptance=acceptance),
        "llm_discovery": _metrics(
            [row for row in evaluated_llm if row["split"] == "discovery"],
            weights=weights,
            acceptance=acceptance,
        ),
        "llm_locked_eval": _metrics(
            [row for row in evaluated_llm if row["split"] == "locked_eval"],
            weights=weights,
            acceptance=acceptance,
        ),
        "manual_stress_all": _metrics(evaluated_validation, weights=weights, acceptance=acceptance),
    }
    source_breakdowns = _source_breakdowns(
        evaluated_validation,
        weights=weights,
        acceptance=acceptance,
    )
    return {
        "candidate_id": (
            f"separate_thresholds|shadow={_round4(shadow_lead_min)}|"
            f"phrase={_round4(phrase_lead_min)}"
        ),
        "decision_shape": "allow_default_separate_shadow_phrase_veto",
        "shadow_lead_min": _round4(shadow_lead_min),
        "phrase_lead_min": _round4(phrase_lead_min),
        "phrase_preemption_enabled": True,
        "metrics": metrics,
        "manual_stress_source_breakdowns": source_breakdowns,
        "selection": {
            "discovery_target_status": _target_status_from_metrics(metrics["llm_discovery"]),
            "locked_eval_target_status": _target_status_from_metrics(metrics["llm_locked_eval"]),
            "manual_stress_target_status": _target_status_from_metrics(
                metrics["manual_stress_all"]
            ),
        },
    }


def _evaluate_case(
    row: Mapping[str, object],
    *,
    shadow_lead_min: float,
    phrase_lead_min: float,
) -> dict[str, object]:
    active = _safe_float(row.get("active_score"))
    shadow = _safe_float(row.get("strongest_shadow_score"))
    phrase = _safe_float(row.get("phrase_control_score"))
    phrase_hit = phrase - max(active, shadow) >= phrase_lead_min
    shadow_hit = shadow - active >= shadow_lead_min
    veto_hit = bool(row.get("phrase_preemption_hit")) or phrase_hit or shadow_hit
    if bool(row.get("phrase_preemption_hit")):
        reason = "phrase_preemption"
    elif phrase_hit:
        reason = "phrase_score_lead"
    elif shadow_hit:
        reason = "shadow_lead"
    else:
        reason = ""
    predicted = "abstain" if veto_hit else "replace"
    gold = str(row.get("gold_decision") or "")
    product_outcome = _product_outcome(gold=gold, predicted=predicted)
    evaluated = dict(row)
    evaluated["predicted_decision"] = predicted
    evaluated["product_outcome"] = product_outcome
    evaluated["veto_reason"] = reason
    evaluated["shadow_lead"] = _round4(shadow - active)
    evaluated["phrase_lead_to_best"] = _round4(phrase - max(active, shadow))
    return evaluated


def _metrics(
    rows: Sequence[Mapping[str, object]],
    *,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    counts = Counter(str(row.get("product_outcome") or "") for row in rows)
    metrics = score_product_outcome_counts(
        outcome_counts=counts,
        weights=weights,
        acceptance=acceptance,
    )
    metrics["case_count"] = len(rows)
    metrics["positive_abstain_count"] = counts.get("positive_abstain", 0)
    metrics["negative_allow_count"] = counts.get("negative_allow", 0)
    return metrics


def _source_breakdowns(
    rows: Sequence[Mapping[str, object]],
    *,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("report_id") or "unknown")].append(row)
    return [
        {
            "report_id": report_id,
            **_metrics(source_rows, weights=weights, acceptance=acceptance),
        }
        for report_id, source_rows in sorted(grouped.items())
    ]


def _normalize_case_row(row: Mapping[str, object], *, lane_id: str) -> dict[str, object]:
    normalized = dict(row)
    normalized.setdefault("lane_id", lane_id)
    normalized.setdefault("report_id", lane_id)
    normalized.setdefault("split", str(row.get("split") or ""))
    return normalized


def _load_validation_source(source: Mapping[str, object], *, index: int) -> dict[str, object]:
    inline = source.get("report")
    if isinstance(inline, Mapping):
        payload = dict(inline)
        path = None
    else:
        path_text = str(source.get("path") or "").strip()
        if not path_text:
            raise ValueError("Validation source needs path or inline report.")
        path = _resolve_repo_path(path_text)
        payload = _load_json(path)
    report_id = str(source.get("report_id") or _default_report_id(path, index))
    case_rows = []
    for row in _case_rows(payload):
        normalized = _normalize_case_row(row, lane_id="manual_stress")
        normalized["report_id"] = report_id
        normalized["split"] = "manual_stress"
        case_rows.append(normalized)
    return {
        "report_id": report_id,
        "path": _repo_path(path),
        "status": str(payload.get("status") or ""),
        "decision": str(payload.get("decision") or ""),
        "case_rows": case_rows,
    }


def _case_rows(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    for key in ("configured_case_results", "row_results", "case_results"):
        rows = _mapping_rows(payload.get(key))
        if rows:
            return rows
    return []


def _select_discovery_candidate(
    rows: Sequence[Mapping[str, object]],
) -> Mapping[str, object] | None:
    passing = [row for row in rows if _target_status(row, "llm_discovery") == "pass"]
    return sorted(passing, key=_discovery_rank_key)[0] if passing else None


def _find_candidate(
    rows: Sequence[Mapping[str, object]],
    *,
    shadow_lead_min: float,
    phrase_lead_min: float,
) -> Mapping[str, object] | None:
    for row in rows:
        if _safe_float(row.get("shadow_lead_min")) == _round4(shadow_lead_min) and _safe_float(
            row.get("phrase_lead_min")
        ) == _round4(phrase_lead_min):
            return row
    return None


def _target_status(row: Mapping[str, object], metric_id: str) -> str:
    metrics = _as_mapping(_as_mapping(row.get("metrics")).get(metric_id))
    return _target_status_from_metrics(metrics)


def _target_status_from_metrics(metrics: Mapping[str, object]) -> str:
    return str(_as_mapping(metrics.get("target_checks")).get("target_status") or "")


def _discovery_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    discovery = _as_mapping(_as_mapping(row.get("metrics")).get("llm_discovery"))
    return (
        0 if _target_status_from_metrics(discovery) == "pass" else 1,
        -_safe_float(discovery.get("utility_score")),
        -_safe_float(discovery.get("positive_allow_rate")),
        -_safe_float(discovery.get("negative_abstain_rate")),
        _safe_float(row.get("shadow_lead_min")),
        _safe_float(row.get("phrase_lead_min")),
    )


def _all_lane_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    metrics = _as_mapping(row.get("metrics"))
    discovery = _as_mapping(metrics.get("llm_discovery"))
    locked = _as_mapping(metrics.get("llm_locked_eval"))
    stress = _as_mapping(metrics.get("manual_stress_all"))
    pass_count = sum(
        1 for metric in (discovery, locked, stress) if _target_status_from_metrics(metric) == "pass"
    )
    combined_utility = sum(
        _safe_float(metric.get("utility_score")) for metric in (discovery, locked, stress)
    )
    min_positive = min(
        _safe_float(metric.get("positive_allow_rate")) for metric in (discovery, locked, stress)
    )
    min_negative = min(
        _safe_float(metric.get("negative_abstain_rate")) for metric in (discovery, locked, stress)
    )
    return (
        -pass_count,
        -combined_utility,
        -min_positive,
        -min_negative,
        _safe_float(row.get("shadow_lead_min")),
        _safe_float(row.get("phrase_lead_min")),
    )


def _public_candidate_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if not row:
        return None
    metrics = _as_mapping(row.get("metrics"))
    public = {
        "candidate_id": str(row.get("candidate_id") or ""),
        "decision_shape": str(row.get("decision_shape") or ""),
        "shadow_lead_min": row.get("shadow_lead_min"),
        "phrase_lead_min": row.get("phrase_lead_min"),
        "selection": dict(_as_mapping(row.get("selection"))),
        "llm_discovery": _public_metrics(metrics.get("llm_discovery")),
        "llm_locked_eval": _public_metrics(metrics.get("llm_locked_eval")),
        "llm_all": _public_metrics(metrics.get("llm_all")),
        "manual_stress_all": _public_metrics(metrics.get("manual_stress_all")),
        "manual_stress_source_breakdowns": [
            {"report_id": str(source.get("report_id") or ""), **_public_metrics(source)}
            for source in _mapping_rows(row.get("manual_stress_source_breakdowns"))
        ],
    }
    return public


def _public_metrics(value: object) -> dict[str, object]:
    metrics = _as_mapping(value)
    return {
        "case_count": metrics.get("case_count"),
        "positive_allow_rate": metrics.get("positive_allow_rate"),
        "negative_abstain_rate": metrics.get("negative_abstain_rate"),
        "positive_abstain_count": metrics.get("positive_abstain_count"),
        "negative_allow_count": metrics.get("negative_allow_count"),
        "utility_score": metrics.get("utility_score"),
        "target_status": _target_status_from_metrics(metrics),
    }


def _public_validation_source(source: Mapping[str, object]) -> dict[str, object]:
    return {
        "report_id": str(source.get("report_id") or ""),
        "path": str(source.get("path") or ""),
        "case_count": len(_mapping_rows(source.get("case_rows"))),
        "status": str(source.get("status") or ""),
        "decision": str(source.get("decision") or ""),
    }


def _candidate_detail(row: Mapping[str, object]) -> str:
    if not row:
        return "_No candidate._"
    return _candidate_table([row])


def _candidate_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Candidate | Shadow | Phrase | Disc pos | Disc neg | Locked pos | Locked neg | Stress pos | Stress neg | Stress utility |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        disc = _as_mapping(row.get("llm_discovery"))
        locked = _as_mapping(row.get("llm_locked_eval"))
        stress = _as_mapping(row.get("manual_stress_all"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("candidate_id") or "")),
                    str(row.get("shadow_lead_min", "")),
                    str(row.get("phrase_lead_min", "")),
                    _format_percent(disc.get("positive_allow_rate")),
                    _format_percent(disc.get("negative_abstain_rate")),
                    _format_percent(locked.get("positive_allow_rate")),
                    _format_percent(locked.get("negative_abstain_rate")),
                    _format_percent(stress.get("positive_allow_rate")),
                    _format_percent(stress.get("negative_abstain_rate")),
                    str(stress.get("utility_score", "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _checks_table(value: object) -> str:
    mapping = _as_mapping(value)
    if not mapping:
        return "_No checks._"
    lines = ["| Check | Value |", "| --- | --- |"]
    for key, raw in mapping.items():
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            rendered = ", ".join(str(item) for item in raw)
        else:
            rendered = str(raw)
        lines.append(f"| `{_escape_md(str(key))}` | `{_escape_md(rendered)}` |")
    return "\n".join(lines)


def _source_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No validation sources._"
    lines = ["| Report | Cases | Status | Decision | Path |", "| --- | ---: | --- | --- | --- |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("report_id") or "")),
                    str(row.get("case_count", 0)),
                    _escape_md(str(row.get("status") or "")),
                    _escape_md(str(row.get("decision") or "")),
                    _escape_md(str(row.get("path") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _recommendation(
    *,
    selected: Mapping[str, object] | None,
    incumbent: Mapping[str, object] | None,
    all_lane_rows: Sequence[Mapping[str, object]],
) -> list[str]:
    if not selected:
        return [
            "No separate-threshold candidate passed product targets on LLM discovery.",
            "Treat threshold adjustment as unsupported until the discovery lane improves.",
        ]
    selected_public = _public_candidate_row(selected) or {}
    incumbent_public = _public_candidate_row(incumbent) or {}
    items = [
        "A discovery-selected separate-threshold candidate exists; evaluate it as research-only.",
        "Do not promote it from this report alone because selection used LLM discovery data.",
    ]
    if selected_public and incumbent_public:
        selected_stress = _as_mapping(selected_public.get("manual_stress_all"))
        incumbent_stress = _as_mapping(incumbent_public.get("manual_stress_all"))
        if _safe_float(selected_stress.get("positive_allow_rate")) < _safe_float(
            incumbent_stress.get("positive_allow_rate")
        ):
            items.append(
                "The discovery-selected candidate overblocks manual/stress positives relative to the incumbent."
            )
        elif _safe_float(selected_stress.get("utility_score")) > _safe_float(
            incumbent_stress.get("utility_score")
        ):
            items.append(
                "The discovery-selected candidate improves combined stress utility versus the incumbent, but still needs a locked representative lane."
            )
    if all_lane_rows:
        items.append(
            "At least one row passes discovery, locked-eval, and combined manual/stress targets; inspect source breakdowns before considering a follow-up candidate-selection harness."
        )
    else:
        items.append(
            "No row passed discovery, locked-eval, and manual/stress targets together under this grid."
        )
    return items


def _product_outcome(*, gold: str, predicted: str) -> str:
    product_class = "positive" if str(gold or "") == "replace" else "negative"
    user_outcome = "allow" if str(predicted or "") == "replace" else "abstain"
    return f"{product_class}_{user_outcome}"


def _parse_float_grid(value: str) -> list[float]:
    return _normalize_float_grid(
        [float(part.strip()) for part in str(value or "").split(",") if part.strip()]
    )


def _normalize_float_grid(values: Sequence[float]) -> list[float]:
    if not values:
        values = (-0.1, -0.075, -0.05, -0.025, 0.0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15)
    return sorted({_round4(float(value)) for value in values})


def _default_report_id(path: Path | None, index: int) -> str:
    if path:
        return path.stem
    return f"inline_validation_{index + 1}"


def _round4(value: object) -> float:
    return round(_safe_float(value), 4)


def _sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
