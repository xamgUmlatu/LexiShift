#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _load_json,
    _mapping_rows,
    _repo_path,
    _safe_float,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_BAND_GRADING_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_band_grading_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_product_scope_band_grading_acceptance_audit_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_band_grading_acceptance_audit_en_es_latest.md"
)

BAND_IDS = ("high_need", "middle_need", "low_need")
FIXED_CONTROL_FORMULAS = (
    "shadow_coverage_only",
    "source_zipf_only",
    "target_zipf_only",
    "polysemy_only",
    "pos_shape_only",
    "linear_equal",
    "linear_source_polysemy",
    "linear_polysemy_shadow",
    "max_signal",
    "source_polysemy_interaction",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a bounded falsification audit before carrying the product-scope "
            "band-grading heuristic to the next LLM-allocation research stage."
        )
    )
    parser.add_argument("--band-grading-json", type=Path, default=DEFAULT_BAND_GRADING_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--candidate-scorer-id", default="")
    parser.add_argument("--candidate-formula-id", default="")
    parser.add_argument("--near-neighbor-fraction", type=float, default=0.90)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_band_grading_acceptance_audit_report(
        band_grading_payload=_load_json(args.band_grading_json),
        band_grading_path=args.band_grading_json,
        candidate_scorer_id=args.candidate_scorer_id,
        candidate_formula_id=args.candidate_formula_id,
        near_neighbor_fraction=args.near_neighbor_fraction,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_band_grading_acceptance_audit_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_band_grading_acceptance_audit_report(
    *,
    band_grading_payload: Mapping[str, object],
    band_grading_path: Path | None = None,
    candidate_scorer_id: str = "",
    candidate_formula_id: str = "",
    near_neighbor_fraction: float = 0.90,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    grade_rows = _mapping_rows(band_grading_payload.get("formula_grade_rows"))
    candidate = _candidate_row(
        band_grading_payload=band_grading_payload,
        grade_rows=grade_rows,
        candidate_scorer_id=candidate_scorer_id,
        candidate_formula_id=candidate_formula_id,
    )
    details = _candidate_detail(band_grading_payload, candidate)
    normalization_rows = _normalization_sensitivity_rows(details)
    scorer_rows = _scorer_sensitivity_rows(grade_rows, candidate)
    neighbor = _near_neighbor_summary(
        grade_rows=grade_rows,
        candidate=candidate,
        near_neighbor_fraction=near_neighbor_fraction,
    )
    controls = _control_summary(grade_rows=grade_rows, candidate=candidate)
    checks = _checks(
        candidate=candidate,
        details=details,
        normalization_rows=normalization_rows,
        scorer_rows=scorer_rows,
        neighbor=neighbor,
        controls=controls,
    )
    issues = [check["check_id"] for check in checks if not check["passed"]]
    status = "review" if issues else "ok"
    decision = "accept_band_grading_v1_for_next_research_stage" if status == "ok" else "review"
    return {
        "schema_version": 1,
        "pair": str(band_grading_payload.get("pair") or "en-es"),
        "status": status,
        "decision": decision,
        "generated_at": generated_at,
        "inputs": {
            "band_grading_path": _repo_path(band_grading_path),
            "band_grading_decision": str(band_grading_payload.get("decision") or ""),
            "near_neighbor_fraction": near_neighbor_fraction,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "purpose": (
                "Falsify obvious weaknesses before freezing the current best "
                "band-creation heuristic as the v1 LLM-allocation candidate."
            ),
            "candidate_selection": (
                "Default candidate is the first best_by_primary_band_grade row from "
                "the band-grading report unless overridden by CLI flags."
            ),
            "acceptance_boundary": (
                "Acceptance means carry-forward for the next research stage, not proof "
                "of final product accuracy and not backend-agnostic promotion."
            ),
        },
        "summary": {
            "issues": issues,
            "candidate": _public_candidate(candidate),
            "normalization_all_positive": all(
                _safe_float(row.get("high_low_failure_delta")) > 0 for row in normalization_rows
            ),
            "sentence_transformer_all_positive": all(
                _safe_float(row.get("primary_normalized_high_low_failure_delta")) > 0
                for row in scorer_rows
                if row.get("backend_family") == "sentence_transformer"
            ),
            "backend_agnostic": all(
                _safe_float(row.get("primary_normalized_high_low_failure_delta")) > 0
                for row in scorer_rows
            ),
            "near_neighbor_count": neighbor.get("near_neighbor_count"),
            "best_fixed_control_formula": _as_mapping(controls.get("best_fixed_control")).get(
                "formula_id"
            ),
            "best_fixed_control_grade": _as_mapping(controls.get("best_fixed_control")).get(
                "primary_grade_score"
            ),
            "candidate_beats_best_fixed_control": controls.get(
                "candidate_beats_best_fixed_control"
            ),
        },
        "checks": checks,
        "normalization_sensitivity_rows": normalization_rows,
        "scorer_sensitivity_rows": scorer_rows,
        "near_neighbor_summary": neighbor,
        "control_summary": controls,
        "limitations": [
            "acceptance_is_for_next_research_stage_not_runtime_policy",
            "tfidf_backend_does_not_consistently_support_the_same_candidate_formula",
            "phrase_no_winner_mass_remains_visible_but_unmeasured_in_the_product_scope_surface",
            "the_49_family_denominator_is_still_small",
        ],
        "next_steps": [
            "Freeze this as product_scope_band_grading_v1 for the next LLM follow-through batch.",
            "Select high/middle/low batches from the v1 heuristic and include low-band controls.",
            "After generation and admission, rerun band grading and this acceptance audit to falsify the heuristic.",
        ],
    }


def render_band_grading_acceptance_audit_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    candidate = _as_mapping(summary.get("candidate"))
    lines = [
        "# en-es Semantic Veto Product-Scope Band Grading Acceptance Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate scorer/config: `{candidate.get('scorer_id', '')}`",
        f"- Candidate formula: `{candidate.get('formula_id', '')}`",
        "",
        "## Checks",
        "",
        _checks_table(report.get("checks")),
        "",
        "## Normalization Sensitivity",
        "",
        _normalization_table(report.get("normalization_sensitivity_rows")),
        "",
        "## Scorer Sensitivity",
        "",
        _scorer_table(report.get("scorer_sensitivity_rows")),
        "",
        "## Near-Neighbor Stability",
        "",
        _neighbor_table(_as_mapping(report.get("near_neighbor_summary"))),
        "",
        "## Fixed Controls",
        "",
        _control_table(_as_mapping(report.get("control_summary"))),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _candidate_row(
    *,
    band_grading_payload: Mapping[str, object],
    grade_rows: Sequence[Mapping[str, object]],
    candidate_scorer_id: str,
    candidate_formula_id: str,
) -> dict[str, object]:
    if candidate_scorer_id and candidate_formula_id:
        for row in grade_rows:
            if (
                str(row.get("scorer_id") or "") == candidate_scorer_id
                and str(row.get("formula_id") or "") == candidate_formula_id
            ):
                return dict(row)
    best_rows = _mapping_rows(
        _as_mapping(band_grading_payload.get("summary")).get("best_by_primary_band_grade")
    )
    if best_rows:
        scorer = str(best_rows[0].get("scorer_id") or "")
        formula = str(best_rows[0].get("formula_id") or "")
        for row in grade_rows:
            if (
                str(row.get("scorer_id") or "") == scorer
                and str(row.get("formula_id") or "") == formula
            ):
                return dict(row)
        return dict(best_rows[0])
    return dict(grade_rows[0]) if grade_rows else {}


def _candidate_detail(
    band_grading_payload: Mapping[str, object],
    candidate: Mapping[str, object],
) -> dict[str, object]:
    scorer = str(candidate.get("scorer_id") or "")
    formula = str(candidate.get("formula_id") or "")
    for row in _mapping_rows(band_grading_payload.get("top_formula_band_details")):
        if (
            str(row.get("scorer_id") or "") == scorer
            and str(row.get("formula_id") or "") == formula
        ):
            return dict(row)
    return {}


def _normalization_sensitivity_rows(details: Mapping[str, object]) -> list[dict[str, object]]:
    by_target: dict[str, dict[str, dict[str, object]]] = {}
    for band in _mapping_rows(details.get("band_metrics")):
        band_id = str(band.get("band_id") or "")
        for row in _mapping_rows(band.get("target_normalized_metrics")):
            by_target.setdefault(str(row.get("target_id") or ""), {})[band_id] = dict(row)
    output = []
    for target_id, rows_by_band in sorted(by_target.items()):
        rates = {
            band_id: _safe_float(
                _as_mapping(rows_by_band.get(band_id)).get("measured_only_failure_rate")
            )
            if _as_mapping(rows_by_band.get(band_id)).get("measured_only_failure_rate") is not None
            else None
            for band_id in BAND_IDS
        }
        measured_weights = [
            _safe_float(_as_mapping(rows_by_band.get(band_id)).get("measured_target_weight"))
            for band_id in BAND_IDS
        ]
        unmeasured_weights = [
            _safe_float(_as_mapping(rows_by_band.get(band_id)).get("unmeasured_target_weight"))
            for band_id in BAND_IDS
        ]
        output.append(
            {
                "target_id": target_id,
                "high_failure_rate": _round4(rates["high_need"]),
                "middle_failure_rate": _round4(rates["middle_need"]),
                "low_failure_rate": _round4(rates["low_need"]),
                "high_low_failure_delta": _round4(
                    rates["high_need"] - rates["low_need"]
                    if rates["high_need"] is not None and rates["low_need"] is not None
                    else None
                ),
                "order_score": _order_score(rates),
                "min_measured_target_weight": _round4(min(measured_weights, default=0.0)),
                "max_unmeasured_target_weight": _round4(max(unmeasured_weights, default=0.0)),
            }
        )
    return output


def _scorer_sensitivity_rows(
    grade_rows: Sequence[Mapping[str, object]],
    candidate: Mapping[str, object],
) -> list[dict[str, object]]:
    formula = str(candidate.get("formula_id") or "")
    rows = []
    for row in grade_rows:
        if str(row.get("formula_id") or "") != formula:
            continue
        rows.append(
            {
                "scorer_id": row.get("scorer_id"),
                "backend_family": _backend_family(str(row.get("scorer_id") or "")),
                "primary_grade_score": row.get("primary_grade_score"),
                "primary_normalized_high_low_failure_delta": row.get(
                    "primary_normalized_high_low_failure_delta"
                ),
                "primary_normalized_order_score": row.get("primary_normalized_order_score"),
                "raw_high_low_failure_delta": row.get("raw_high_low_failure_delta"),
            }
        )
    rows.sort(
        key=lambda row: (str(row.get("backend_family") or ""), str(row.get("scorer_id") or ""))
    )
    return rows


def _near_neighbor_summary(
    *,
    grade_rows: Sequence[Mapping[str, object]],
    candidate: Mapping[str, object],
    near_neighbor_fraction: float,
) -> dict[str, object]:
    scorer = str(candidate.get("scorer_id") or "")
    candidate_grade = _safe_float(candidate.get("primary_grade_score"))
    threshold = candidate_grade * near_neighbor_fraction
    neighbors = [
        row
        for row in grade_rows
        if str(row.get("scorer_id") or "") == scorer
        and _safe_float(row.get("primary_grade_score")) >= threshold
    ]
    feature_stats = _feature_stats([_as_mapping(row.get("weights")) for row in neighbors])
    family_counts = Counter(str(row.get("formula_family") or "") for row in neighbors)
    top_rows = sorted(
        neighbors,
        key=lambda row: (
            -_safe_float(row.get("primary_grade_score")),
            str(row.get("formula_id") or ""),
        ),
    )[:10]
    return {
        "scorer_id": scorer,
        "candidate_grade_score": candidate.get("primary_grade_score"),
        "near_neighbor_fraction": near_neighbor_fraction,
        "near_neighbor_threshold": _round4(threshold),
        "near_neighbor_count": len(neighbors),
        "formula_family_counts": dict(sorted(family_counts.items())),
        "feature_weight_stats": feature_stats,
        "top_neighbor_rows": [
            {
                "formula_id": row.get("formula_id"),
                "formula_family": row.get("formula_family"),
                "primary_grade_score": row.get("primary_grade_score"),
                "primary_normalized_high_low_failure_delta": row.get(
                    "primary_normalized_high_low_failure_delta"
                ),
                "weights": row.get("weights"),
            }
            for row in top_rows
        ],
    }


def _control_summary(
    *,
    grade_rows: Sequence[Mapping[str, object]],
    candidate: Mapping[str, object],
) -> dict[str, object]:
    scorer = str(candidate.get("scorer_id") or "")
    controls = [
        row
        for row in grade_rows
        if str(row.get("scorer_id") or "") == scorer
        and str(row.get("formula_id") or "") in FIXED_CONTROL_FORMULAS
    ]
    controls.sort(
        key=lambda row: (
            -_safe_float(row.get("primary_grade_score")),
            str(row.get("formula_id") or ""),
        )
    )
    best = dict(controls[0]) if controls else {}
    return {
        "scorer_id": scorer,
        "candidate_grade_score": candidate.get("primary_grade_score"),
        "best_fixed_control": _public_control(best),
        "candidate_beats_best_fixed_control": _safe_float(candidate.get("primary_grade_score"))
        > _safe_float(best.get("primary_grade_score")),
        "control_rows": [_public_control(row) for row in controls],
    }


def _checks(
    *,
    candidate: Mapping[str, object],
    details: Mapping[str, object],
    normalization_rows: Sequence[Mapping[str, object]],
    scorer_rows: Sequence[Mapping[str, object]],
    neighbor: Mapping[str, object],
    controls: Mapping[str, object],
) -> list[dict[str, object]]:
    st_rows = [row for row in scorer_rows if row.get("backend_family") == "sentence_transformer"]
    return [
        _check(
            "candidate_detail_available",
            bool(candidate and details),
            "Candidate row has top-band detail rows with per-target normalized metrics.",
        ),
        _check(
            "normalization_targets_all_positive",
            bool(normalization_rows)
            and all(
                _safe_float(row.get("high_low_failure_delta")) > 0 for row in normalization_rows
            ),
            "High-need failure is higher than low-need failure under every normalization target.",
        ),
        _check(
            "normalization_order_all_monotonic",
            bool(normalization_rows)
            and all(_safe_float(row.get("order_score")) >= 1.0 for row in normalization_rows),
            "High, middle, and low bands are monotonic under every normalization target.",
        ),
        _check(
            "sentence_transformer_configs_positive",
            bool(st_rows)
            and all(
                _safe_float(row.get("primary_normalized_high_low_failure_delta")) > 0
                for row in st_rows
            ),
            "The candidate formula remains positive across sentence-transformer candidate configs.",
        ),
        _check(
            "near_neighbor_family_available",
            int(neighbor.get("near_neighbor_count") or 0) >= 5,
            "At least five near-neighbor formulas are within the configured grade threshold.",
        ),
        _check(
            "candidate_beats_fixed_controls",
            bool(controls.get("candidate_beats_best_fixed_control")),
            "The candidate beats the best fixed single/hand-authored control on the same scorer config.",
        ),
    ]


def _check(check_id: str, passed: bool, rationale: str) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "rationale": rationale}


def _public_candidate(candidate: Mapping[str, object]) -> dict[str, object]:
    return {
        "scorer_id": candidate.get("scorer_id"),
        "formula_id": candidate.get("formula_id"),
        "formula_family": candidate.get("formula_family"),
        "primary_grade_score": candidate.get("primary_grade_score"),
        "primary_normalized_high_low_failure_delta": candidate.get(
            "primary_normalized_high_low_failure_delta"
        ),
        "primary_normalized_order_score": candidate.get("primary_normalized_order_score"),
        "raw_high_low_failure_delta": candidate.get("raw_high_low_failure_delta"),
        "band_family_counts": candidate.get("band_family_counts"),
        "weights": candidate.get("weights"),
    }


def _public_control(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "formula_id": row.get("formula_id"),
        "formula_family": row.get("formula_family"),
        "primary_grade_score": row.get("primary_grade_score"),
        "primary_normalized_high_low_failure_delta": row.get(
            "primary_normalized_high_low_failure_delta"
        ),
        "primary_normalized_order_score": row.get("primary_normalized_order_score"),
        "raw_high_low_failure_delta": row.get("raw_high_low_failure_delta"),
        "band_family_counts": row.get("band_family_counts"),
        "weights": row.get("weights"),
    }


def _feature_stats(weights_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    feature_ids = sorted({str(key) for row in weights_rows for key in row})
    output = []
    for feature_id in feature_ids:
        values = [_safe_float(row.get(feature_id)) for row in weights_rows]
        if not values:
            continue
        output.append(
            {
                "feature_id": feature_id,
                "mean_weight": _round4(sum(values) / len(values)),
                "min_weight": _round4(min(values)),
                "max_weight": _round4(max(values)),
                "nonzero_share": _round4(sum(1 for value in values if value > 0) / len(values)),
            }
        )
    return output


def _backend_family(scorer_id: str) -> str:
    lowered = scorer_id.lower()
    if "tfidf" in lowered:
        return "tfidf"
    if "sentence_transformer" in lowered:
        return "sentence_transformer"
    return "other"


def _order_score(rates: Mapping[str, float | None]) -> float | None:
    pairs = (
        ("high_need", "middle_need"),
        ("middle_need", "low_need"),
        ("high_need", "low_need"),
    )
    available = [
        (left, right)
        for left, right in pairs
        if rates.get(left) is not None and rates.get(right) is not None
    ]
    if not available:
        return None
    correct = sum(1 for left, right in available if rates[left] >= rates[right])
    return _round4(correct / len(available))


def _checks_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No checks._"
    lines = ["| Check | Pass | Rationale |", "| --- | --- | --- |"]
    for row in rows:
        lines.append(
            f"| `{_escape_md(str(row.get('check_id') or ''))}` | "
            f"`{str(bool(row.get('passed'))).lower()}` | "
            f"{_escape_md(str(row.get('rationale') or ''))} |"
        )
    return "\n".join(lines)


def _normalization_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No normalization rows._"
    headers = ["target", "high", "middle", "low", "high-low", "order", "measured", "unmeasured"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape_md(value)
                for value in [
                    str(row.get("target_id") or ""),
                    _format_percent(row.get("high_failure_rate")),
                    _format_percent(row.get("middle_failure_rate")),
                    _format_percent(row.get("low_failure_rate")),
                    _format_signed_percent(row.get("high_low_failure_delta")),
                    _number(row.get("order_score")),
                    _format_percent(row.get("min_measured_target_weight")),
                    _format_percent(row.get("max_unmeasured_target_weight")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _scorer_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No scorer rows._"
    headers = ["scorer", "backend", "grade", "SRS high-low", "order", "raw high-low"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape_md(value)
                for value in [
                    str(row.get("scorer_id") or ""),
                    str(row.get("backend_family") or ""),
                    _number(row.get("primary_grade_score")),
                    _format_signed_percent(row.get("primary_normalized_high_low_failure_delta")),
                    _number(row.get("primary_normalized_order_score")),
                    _format_signed_percent(row.get("raw_high_low_failure_delta")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _neighbor_table(summary: Mapping[str, object]) -> str:
    stats = _mapping_rows(summary.get("feature_weight_stats"))
    rows = [
        f"- Near-neighbor threshold: `{summary.get('near_neighbor_threshold')}`",
        f"- Near-neighbor count: `{summary.get('near_neighbor_count')}`",
        f"- Formula family counts: `{json.dumps(summary.get('formula_family_counts') or {}, sort_keys=True)}`",
        "",
    ]
    if not stats:
        rows.append("_No feature stats._")
        return "\n".join(rows)
    rows.extend(
        [
            "| feature | mean | min | max | nonzero |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in stats:
        rows.append(
            f"| `{_escape_md(str(row.get('feature_id') or ''))}` | "
            f"{_number(row.get('mean_weight'))} | "
            f"{_number(row.get('min_weight'))} | "
            f"{_number(row.get('max_weight'))} | "
            f"{_format_percent(row.get('nonzero_share'))} |"
        )
    return "\n".join(rows)


def _control_table(summary: Mapping[str, object]) -> str:
    rows = _mapping_rows(summary.get("control_rows"))
    if not rows:
        return "_No control rows._"
    lines = [
        f"- Candidate beats best fixed control: `{str(bool(summary.get('candidate_beats_best_fixed_control'))).lower()}`",
        "",
        "| formula | grade | SRS high-low | order | raw high-low |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{_escape_md(str(row.get('formula_id') or ''))}` | "
            f"{_number(row.get('primary_grade_score'))} | "
            f"{_format_signed_percent(row.get('primary_normalized_high_low_failure_delta'))} | "
            f"{_number(row.get('primary_normalized_order_score'))} | "
            f"{_format_signed_percent(row.get('raw_high_low_failure_delta'))} |"
        )
    return "\n".join(lines)


def _format_signed_percent(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{100 * _safe_float(value):+.1f}%"


def _number(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{_safe_float(value):.4f}"


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
