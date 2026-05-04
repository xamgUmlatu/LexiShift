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
    _utility_weights,
    score_product_outcome_counts,
)
from semantic_veto_veto_only_probe_en_es import (
    VETO_ONLY_PHRASE_MODES,
    _evaluate_veto_only_config,
    _failure_samples,
    _mapping_rows,
    _probe_rank_key,
    _public_probe_row,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_veto_product_quality_policy_en_es.json"
)
DEFAULT_REPORTS = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout_validation_latest.json",
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase_validation_latest.json",
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_veto_only_validation_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_veto_only_validation_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate allow-by-default semantic-veto blocker rules on configured "
            "validation reports such as stress lanes."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument(
        "--report-json",
        type=Path,
        action="append",
        default=[],
        help="Validation report JSON containing configured_case_results, row_results, or case_results.",
    )
    parser.add_argument(
        "--shadow-lead-grid",
        type=str,
        default="-0.10,-0.08,-0.05,-0.03,-0.02,-0.01,0.00,0.01,0.02,0.03,0.05,0.08,0.10,0.15,0.20",
    )
    parser.add_argument(
        "--shadow-score-grid",
        type=str,
        default="0.00,0.02,0.05,0.10,0.20,0.35,0.45,0.50,0.55,0.60,0.65,0.70",
    )
    parser.add_argument(
        "--phrase-modes",
        type=str,
        default=",".join(VETO_ONLY_PHRASE_MODES),
    )
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    policy = _load_json(args.policy_json)
    report_paths = tuple(args.report_json) if args.report_json else DEFAULT_REPORTS
    report = build_veto_only_validation_report(
        policy=policy,
        validation_reports=[{"path": path} for path in report_paths],
        policy_path=args.policy_json,
        shadow_lead_grid=_parse_float_grid(args.shadow_lead_grid),
        shadow_score_grid=_parse_float_grid(args.shadow_score_grid),
        phrase_modes=_parse_string_grid(args.phrase_modes),
        top_n=max(1, int(args.top_n)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_veto_only_validation_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_veto_only_validation_report(
    *,
    policy: Mapping[str, object],
    validation_reports: Sequence[Mapping[str, object]],
    policy_path: Path | None = None,
    shadow_lead_grid: Sequence[float] = (),
    shadow_score_grid: Sequence[float] = (),
    phrase_modes: Sequence[str] = (),
    top_n: int = 12,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    weights = _utility_weights(policy)
    acceptance = _as_mapping(policy.get("acceptance"))
    sources = [
        _load_validation_source(source, index=index)
        for index, source in enumerate(validation_reports)
    ]
    case_rows: list[dict[str, object]] = []
    for source in sources:
        case_rows.extend(source["case_rows"])
    if not case_rows:
        raise ValueError("Veto-only validation has no case rows to replay.")
    normalized_phrase_modes = [
        mode
        for mode in _normalize_strings(phrase_modes, default=VETO_ONLY_PHRASE_MODES)
        if mode in VETO_ONLY_PHRASE_MODES
    ]
    if not normalized_phrase_modes:
        raise ValueError("Veto-only validation requires at least one supported phrase mode.")
    normalized_shadow_leads = _normalize_float_grid(
        shadow_lead_grid,
        default=(
            -0.1,
            -0.08,
            -0.05,
            -0.03,
            -0.02,
            -0.01,
            0.0,
            0.01,
            0.02,
            0.03,
            0.05,
            0.08,
            0.1,
            0.15,
            0.2,
        ),
    )
    normalized_shadow_scores = _normalize_float_grid(
        shadow_score_grid,
        default=(0.0, 0.02, 0.05, 0.1, 0.2, 0.35, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7),
    )
    rows: list[dict[str, object]] = []
    config = _config_from_sources(sources)
    for phrase_mode in normalized_phrase_modes:
        for shadow_lead_min in normalized_shadow_leads:
            for shadow_score_min in normalized_shadow_scores:
                row = _evaluate_veto_only_config(
                    config_id="veto_only_validation",
                    config=config,
                    case_rows=case_rows,
                    phrase_mode=phrase_mode,
                    shadow_lead_min=float(shadow_lead_min),
                    shadow_score_min=float(shadow_score_min),
                    weights=weights,
                    acceptance=acceptance,
                )
                row["source_breakdowns"] = _source_breakdowns(
                    cases=row.get("case_results"),
                    weights=weights,
                    acceptance=acceptance,
                )
                rows.append(row)
    ranked_rows = sorted(rows, key=_probe_rank_key)
    target_pass_rows = [
        row
        for row in ranked_rows
        if str(_as_mapping(row.get("target_checks")).get("target_status") or "") == "pass"
    ]
    return {
        "schema_version": 1,
        "status": "ok" if target_pass_rows else "review",
        "decision": (
            "veto_only_validation_product_target_pass_found"
            if target_pass_rows
            else "veto_only_validation_product_target_not_met"
        ),
        "generated_at": generated_at,
        "pair": str(policy.get("pair") or "en-es"),
        "policy": {
            "path": _repo_path(policy_path),
            "policy_id": str(policy.get("policy_id") or ""),
            "acceptance": dict(acceptance),
            "utility_weights": weights,
        },
        "e2e_checks": {
            "calculus_source": (
                "scripts/testing/semantic_veto_product_quality_en_es.py::"
                "score_product_outcome_counts"
            ),
            "source_reports_read": len(sources),
            "input_case_rows_read": len(case_rows),
            "policy_rows_emitted": len(rows),
            "phrase_modes": normalized_phrase_modes,
            "shadow_lead_grid": normalized_shadow_leads,
            "shadow_score_grid": normalized_shadow_scores,
        },
        "sources": [_public_source(source) for source in sources],
        "summary": {
            "row_count": len(rows),
            "target_pass_count": len(target_pass_rows),
            "top_n": max(1, int(top_n)),
            "best_product_rank_row": _public_validation_row(
                ranked_rows[0] if ranked_rows else None
            ),
            "best_target_pass_row": _public_validation_row(
                target_pass_rows[0] if target_pass_rows else None
            ),
            "recommendation": _recommendation(target_pass_rows=target_pass_rows),
        },
        "top_rows": [_public_validation_row(row) for row in ranked_rows[: max(1, int(top_n))]],
        "target_pass_rows": [
            _public_validation_row(row) for row in target_pass_rows[: max(1, int(top_n))]
        ],
        "failure_samples": _failure_samples(ranked_rows[0] if ranked_rows else None),
        "rows": [_public_validation_row(row) for row in ranked_rows],
    }


def render_veto_only_validation_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Veto-Only Validation",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Policy: `{_as_mapping(report.get('policy')).get('path', '')}`",
        f"- Sources: `{len(_mapping_rows(report.get('sources')))}`",
        f"- Rows evaluated: `{summary.get('row_count', 0)}`",
        f"- Product target pass rows: `{summary.get('target_pass_count', 0)}`",
        "",
        "## E2E Checks",
        "",
        _checks_table(report.get("e2e_checks")),
        "",
        "## Sources",
        "",
        _source_table(report.get("sources")),
        "",
        "## Top Validation Rows",
        "",
        _validation_row_table(report.get("top_rows")),
        "",
        "## Passing Rows",
        "",
        _validation_row_table(report.get("target_pass_rows")),
        "",
        "## Failure Samples For Best Row",
        "",
        _failure_table(report.get("failure_samples")),
        "",
        "## Recommendation",
        "",
    ]
    for item in _sequence(summary.get("recommendation")):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


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
    suite_id = str(source.get("suite_id") or payload.get("heldout_case_scope") or report_id)
    case_rows = []
    for row in _case_rows(payload):
        normalized = dict(row)
        normalized["report_id"] = report_id
        normalized["suite_id"] = suite_id
        case_rows.append(normalized)
    return {
        "report_id": report_id,
        "suite_id": suite_id,
        "path": _repo_path(path),
        "status": str(payload.get("status") or ""),
        "decision": str(payload.get("decision") or ""),
        "configured_lane": dict(_as_mapping(payload.get("configured_lane"))),
        "summary": dict(_as_mapping(payload.get("summary"))),
        "case_rows": case_rows,
    }


def _case_rows(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    for key in ("configured_case_results", "row_results", "case_results"):
        rows = _mapping_rows(payload.get(key))
        if rows:
            return rows
    return []


def _config_from_sources(sources: Sequence[Mapping[str, object]]) -> dict[str, object]:
    first_lane = dict(_as_mapping(sources[0].get("configured_lane"))) if sources else {}
    return {
        "label": "Veto-only replay over validation reports",
        "category": "validation",
        "scorer_id": str(first_lane.get("scorer_id") or ""),
        "context_view": str(first_lane.get("context_view") or ""),
        "sense_representation": "configured_validation_evidence",
        "aggregation_rule": "configured_validation_scores",
        "decision_rule": "allow_default_shadow_veto",
        "phrase_handling": str(first_lane.get("decision_shape") or ""),
    }


def _source_breakdowns(
    *,
    cases: object,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> list[dict[str, object]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in _mapping_rows(cases):
        report_id = str(row.get("report_id") or "unknown")
        grouped[report_id][str(row.get("product_outcome") or "")] += 1
    return [
        {
            "report_id": report_id,
            **score_product_outcome_counts(
                outcome_counts=counts,
                weights=weights,
                acceptance=acceptance,
            ),
        }
        for report_id, counts in sorted(grouped.items())
    ]


def _public_validation_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    public = _public_probe_row(row)
    if public is None:
        return None
    public["source_breakdowns"] = [
        {
            "report_id": str(source.get("report_id") or ""),
            "positive_allow_rate": source.get("positive_allow_rate"),
            "negative_abstain_rate": source.get("negative_abstain_rate"),
            "utility_score": source.get("utility_score"),
            "target_status": str(
                _as_mapping(source.get("target_checks")).get("target_status") or ""
            ),
        }
        for source in _mapping_rows(
            row.get("source_breakdowns") if isinstance(row, Mapping) else None
        )
    ]
    return public


def _public_source(source: Mapping[str, object]) -> dict[str, object]:
    summary = _as_mapping(source.get("summary"))
    return {
        "report_id": str(source.get("report_id") or ""),
        "suite_id": str(source.get("suite_id") or ""),
        "path": str(source.get("path") or ""),
        "case_count": len(_mapping_rows(source.get("case_rows"))),
        "gold_replace_cases": int(summary.get("gold_replace_cases") or 0),
        "gold_abstain_cases": int(summary.get("gold_abstain_cases") or 0),
        "original_harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "original_false_abstain_count": int(summary.get("false_abstain_count") or 0),
    }


def _source_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No sources._"
    lines = [
        "| Source | Suite | Cases | Positives | Negatives | Original harmful | Original false abstain |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("report_id") or "")),
                    _escape_md(str(row.get("suite_id") or "")),
                    str(row.get("case_count", 0)),
                    str(row.get("gold_replace_cases", 0)),
                    str(row.get("gold_abstain_cases", 0)),
                    str(row.get("original_harmful_replace_count", 0)),
                    str(row.get("original_false_abstain_count", 0)),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _validation_row_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target | Source breakdowns |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("phrase_mode") or "")),
                    str(row.get("shadow_lead_min", "")),
                    str(row.get("shadow_score_min", "")),
                    _format_percent(row.get("positive_allow_rate")),
                    _format_percent(row.get("negative_abstain_rate")),
                    str(row.get("utility_score", "")),
                    _escape_md(str(row.get("target_status") or "")),
                    _escape_md(_render_source_breakdowns(row.get("source_breakdowns"))),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _render_source_breakdowns(value: object) -> str:
    parts = []
    for row in _mapping_rows(value):
        parts.append(
            f"{row.get('report_id', '')}: pos {_format_percent(row.get('positive_allow_rate'))}, "
            f"neg {_format_percent(row.get('negative_abstain_rate'))}"
        )
    return "; ".join(parts)


def _checks_table(value: object) -> str:
    mapping = _as_mapping(value)
    if not mapping:
        return "_No E2E checks._"
    lines = ["| Check | Value |", "| --- | --- |"]
    for key, raw_value in mapping.items():
        if isinstance(raw_value, Sequence) and not isinstance(raw_value, (str, bytes)):
            rendered = ", ".join(str(item) for item in raw_value)
        else:
            rendered = str(raw_value)
        lines.append(f"| `{_escape_md(str(key))}` | `{_escape_md(rendered)}` |")
    return "\n".join(lines)


def _failure_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No failures for the best row._"
    lines = [
        "| Source | Case | Trigger | Gold | Winner | Outcome | Reason | Active | Shadow | Lead | Sentence |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("report_id") or "")),
                    _escape_md(str(row.get("case_id") or "")),
                    _escape_md(str(row.get("trigger") or "")),
                    _escape_md(str(row.get("gold_decision") or "")),
                    _escape_md(str(row.get("gold_winner_type") or "")),
                    _escape_md(str(row.get("product_outcome") or "")),
                    _escape_md(str(row.get("veto_reason") or "")),
                    str(row.get("active_score", "")),
                    str(row.get("strongest_shadow_score", "")),
                    str(row.get("shadow_lead", "")),
                    _escape_md(str(row.get("sentence") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _recommendation(*, target_pass_rows: Sequence[Mapping[str, object]]) -> list[str]:
    if target_pass_rows:
        return [
            "At least one veto-only blocker policy meets the configured product target on these validation reports.",
            "Compare the winning blocker against the frozen v10 matrix winner before considering runtime policy changes.",
            "Use source breakdowns and failure samples to decide which blocker signals need broader representative evaluation.",
        ]
    return [
        "No veto-only blocker policy meets the configured product target on these validation reports.",
        "Treat the v10 pass as insufficient until stress and representative validation improve.",
    ]


def _default_report_id(path: Path | None, index: int) -> str:
    if path is None:
        return f"inline_report_{index}"
    stem = path.stem
    for suffix in ("_latest", "_validation"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem


def _parse_string_grid(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _parse_float_grid(value: str) -> list[float]:
    return [float(item.strip()) for item in str(value or "").split(",") if item.strip()]


def _normalize_strings(values: Sequence[str], *, default: Sequence[str]) -> list[str]:
    materialized = [str(value or "").strip() for value in values if str(value or "").strip()]
    return materialized or [str(value) for value in default]


def _normalize_float_grid(values: Sequence[float], *, default: Sequence[float]) -> list[float]:
    materialized = [float(value) for value in values]
    if not materialized:
        materialized = [float(value) for value in default]
    return sorted({round(value, 4) for value in materialized})


def _sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
