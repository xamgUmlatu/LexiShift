#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_veto_product_quality_policy_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_product_objective_bakeoff_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_product_objective_bakeoff_en_es_latest.md"
)
DEFAULT_SOURCE_PATHS = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_sentence_veto_sweep_latest.json",
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_decision_rule_matrix_en_es_latest.json",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Re-rank historical en-es semantic-veto scorer and decision-rule rows "
            "under the product-quality acceptance policy."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument(
        "--source-json",
        type=Path,
        action="append",
        default=[],
        help=(
            "Historical sweep or matrix JSON artifact to rank. Defaults to the latest "
            "sentence-veto sweep and decision-rule matrix artifacts."
        ),
    )
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    policy = _load_json(args.policy_json)
    source_paths = tuple(args.source_json) if args.source_json else DEFAULT_SOURCE_PATHS
    report = build_product_objective_bakeoff_report(
        policy=policy,
        policy_path=args.policy_json,
        sources=[{"path": path} for path in source_paths],
        top_n=max(1, int(args.top_n)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_product_objective_bakeoff_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_product_objective_bakeoff_report(
    *,
    policy: Mapping[str, object],
    sources: Sequence[Mapping[str, object]],
    policy_path: Path | None = None,
    top_n: int = 12,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    weights = _utility_weights(policy)
    acceptance = _as_mapping(policy.get("acceptance"))
    source_reports: list[dict[str, object]] = []
    product_rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    for source_index, source in enumerate(sources):
        source_report = _load_source_report(source, source_index=source_index)
        rows = _source_product_rows(
            source=source_report,
            weights=weights,
            acceptance=acceptance,
        )
        product_rows.extend(rows)
        source_reports.append(_source_summary(source=source_report, rows=rows))
        issues.extend(_source_issues(source=source_report, rows=rows))

    ranked_rows = sorted(product_rows, key=_product_rank_key)
    target_pass_rows = [
        row
        for row in ranked_rows
        if str(_as_mapping(row.get("target_checks")).get("target_status") or "") == "pass"
    ]
    best_by_source = [
        _public_row(_best_by_product_rank([row for row in ranked_rows if row["source_id"] == sid]))
        for sid in sorted({str(row.get("source_id") or "") for row in ranked_rows})
    ]
    status = "ok" if target_pass_rows and not issues else "review"
    decision = (
        "historical_product_target_pass_found"
        if target_pass_rows
        else "historical_product_target_not_met"
    )
    return {
        "schema_version": 1,
        "status": status,
        "decision": decision,
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
            "source_artifacts_read": len(source_reports),
            "input_rows_read": sum(int(row.get("input_row_count") or 0) for row in source_reports),
            "product_rows_emitted": len(product_rows),
            "all_source_rows_read": sum(
                int(row.get("input_row_count") or 0) for row in source_reports
            )
            == len(product_rows),
            "issue_count": len(issues),
        },
        "summary": {
            "source_count": len(source_reports),
            "row_count": len(product_rows),
            "target_pass_count": len(target_pass_rows),
            "top_n": max(1, int(top_n)),
            "best_product_rank_row": _public_row(_best_by_product_rank(ranked_rows)),
            "best_target_pass_row": _public_row(target_pass_rows[0] if target_pass_rows else None),
            "highest_utility_row": _public_row(_best_by_utility(ranked_rows)),
            "closest_target_shape_row": _public_row(_closest_target_shape(ranked_rows)),
            "best_by_source": best_by_source,
            "recommendation": _recommendation(target_pass_rows=target_pass_rows, issues=issues),
        },
        "sources": source_reports,
        "issues": issues,
        "top_rows": [_public_row(row) for row in ranked_rows[: max(1, int(top_n))]],
        "closest_target_shape_rows": [
            _public_row(row)
            for row in sorted(ranked_rows, key=_target_distance_rank_key)[: max(1, int(top_n))]
        ],
        "rows": [_public_row(row) for row in ranked_rows],
    }


def render_product_objective_bakeoff_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    checks = _as_mapping(report.get("e2e_checks"))
    lines = [
        "# en-es Semantic Veto Product Objective Bakeoff",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Policy: `{_as_mapping(report.get('policy')).get('path', '')}`",
        f"- Sources: `{summary.get('source_count', 0)}`",
        f"- Rows ranked: `{summary.get('row_count', 0)}`",
        f"- Product target pass rows: `{summary.get('target_pass_count', 0)}`",
        "",
        "## E2E Checks",
        "",
        "| Check | Value |",
        "| --- | --- |",
    ]
    for key, value in checks.items():
        lines.append(f"| `{_escape_md(str(key))}` | `{_escape_md(str(value))}` |")

    lines.extend(["", "## Sources", "", _source_table(report.get("sources")), ""])
    lines.extend(["## Best Product Rank Rows", "", _row_table(report.get("top_rows")), ""])
    lines.extend(
        [
            "## Closest Target Shape Rows",
            "",
            _row_table(report.get("closest_target_shape_rows")),
            "",
        ]
    )
    lines.extend(["## Best By Source", "", _row_table(summary.get("best_by_source")), ""])
    lines.extend(["## Recommendation", ""])
    for item in _sequence(summary.get("recommendation")):
        lines.append(f"- {item}")
    issues = _sequence(report.get("issues"))
    if issues:
        lines.extend(["", "## Issues", ""])
        for issue in issues:
            row = _as_mapping(issue)
            lines.append(
                f"- `{row.get('severity', '')}` `{row.get('source_id', '')}`: "
                f"{row.get('message', '')}"
            )
    return "\n".join(lines) + "\n"


def _load_source_report(
    source: Mapping[str, object],
    *,
    source_index: int,
) -> dict[str, object]:
    inline = source.get("report")
    if isinstance(inline, Mapping):
        payload = dict(inline)
        path = None
    else:
        path_text = str(source.get("path") or "").strip()
        if not path_text:
            raise ValueError("Product objective bakeoff source needs `path` or inline `report`.")
        path = _resolve_repo_path(path_text)
        payload = _load_json(path)
    source_type = str(source.get("source_type") or _infer_source_type(payload) or "").strip()
    if not source_type:
        raise ValueError("Could not infer source type for product objective bakeoff source.")
    source_id = str(source.get("source_id") or _default_source_id(path, source_type, source_index))
    row_key = _row_key_for_source_type(source_type)
    rows = _mapping_rows(payload.get(row_key))
    return {
        "source_id": source_id,
        "source_type": source_type,
        "path": _repo_path(path),
        "row_key": row_key,
        "payload": payload,
        "rows": rows,
        "dataset_id": str(payload.get("dataset_id") or "").strip(),
        "dataset_path": str(payload.get("dataset_path") or "").strip(),
        "generated_at": str(payload.get("generated_at") or "").strip(),
    }


def _source_product_rows(
    *,
    source: Mapping[str, object],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, raw_row in enumerate(_mapping_rows(source.get("rows"))):
        outcome_counts = _outcome_counts_from_summary_row(
            raw_row,
            source_id=str(source.get("source_id") or ""),
        )
        metrics = score_product_outcome_counts(
            outcome_counts=outcome_counts,
            weights=weights,
            acceptance=acceptance,
        )
        positive_shortfall = _shortfall(
            metrics.get("positive_allow_rate"),
            _safe_float(acceptance.get("positive_allow_rate_min")),
        )
        negative_shortfall = _shortfall(
            metrics.get("negative_abstain_rate"),
            _safe_float(acceptance.get("negative_abstain_rate_min")),
        )
        row = {
            "source_id": str(source.get("source_id") or ""),
            "source_type": str(source.get("source_type") or ""),
            "source_path": str(source.get("path") or ""),
            "source_row_index": index,
            "dataset_id": str(source.get("dataset_id") or ""),
            "dataset_path": str(source.get("dataset_path") or ""),
            "config_id": str(raw_row.get("config_id") or f"row-{index}"),
            "label": str(raw_row.get("label") or ""),
            "category": str(raw_row.get("category") or ""),
            "algorithm_family": str(raw_row.get("algorithm_family") or ""),
            "parameter_set_id": str(raw_row.get("parameter_set_id") or ""),
            "is_control": bool(raw_row.get("is_control")),
            "scorer_id": str(raw_row.get("scorer_id") or ""),
            "model_name": str(raw_row.get("model_name") or ""),
            "context_view": str(raw_row.get("context_view") or ""),
            "evidence_view": str(raw_row.get("evidence_view") or ""),
            "sense_representation": str(raw_row.get("sense_representation") or ""),
            "aggregation_rule": str(raw_row.get("aggregation_rule") or ""),
            "decision_rule": str(raw_row.get("decision_rule") or ""),
            "phrase_handling": str(raw_row.get("phrase_handling") or ""),
            "phrase_control_mode": str(raw_row.get("phrase_control_mode") or ""),
            "active_rescue_mode": str(raw_row.get("active_rescue_mode") or ""),
            "min_active_score": raw_row.get("min_active_score"),
            "min_margin": raw_row.get("min_margin"),
            "ratio_threshold": raw_row.get("ratio_threshold"),
            "softmax_threshold": raw_row.get("softmax_threshold"),
            "pairwise_min_win_rate": raw_row.get("pairwise_min_win_rate"),
            "original_objective_score": raw_row.get("objective_score"),
            "decision_accuracy": raw_row.get("decision_accuracy"),
            "winner_accuracy": raw_row.get("winner_accuracy"),
            "replace_recall": raw_row.get("replace_recall"),
            "outcome_counts": outcome_counts,
            "metrics": metrics,
            "target_checks": dict(_as_mapping(metrics.get("target_checks"))),
            "positive_allow_shortfall": positive_shortfall,
            "negative_abstain_shortfall": negative_shortfall,
            "target_distance": round(positive_shortfall + negative_shortfall, 4),
        }
        rows.append(row)
    return rows


def _source_summary(
    *,
    source: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    pass_count = sum(
        1
        for row in rows
        if str(_as_mapping(row.get("target_checks")).get("target_status") or "") == "pass"
    )
    return {
        "source_id": str(source.get("source_id") or ""),
        "source_type": str(source.get("source_type") or ""),
        "path": str(source.get("path") or ""),
        "row_key": str(source.get("row_key") or ""),
        "dataset_id": str(source.get("dataset_id") or ""),
        "dataset_path": str(source.get("dataset_path") or ""),
        "generated_at": str(source.get("generated_at") or ""),
        "input_row_count": len(_mapping_rows(source.get("rows"))),
        "product_row_count": len(rows),
        "target_pass_count": pass_count,
        "best_product_rank_row": _public_row(_best_by_product_rank(rows)),
        "closest_target_shape_row": _public_row(_closest_target_shape(rows)),
    }


def _source_issues(
    *,
    source: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    input_count = len(_mapping_rows(source.get("rows")))
    if input_count == 0:
        issues.append(
            {
                "severity": "error",
                "source_id": str(source.get("source_id") or ""),
                "message": "Source artifact contains no readable candidate rows.",
            }
        )
    if input_count != len(rows):
        issues.append(
            {
                "severity": "error",
                "source_id": str(source.get("source_id") or ""),
                "message": "Source row count does not match emitted product row count.",
            }
        )
    return issues


def _outcome_counts_from_summary_row(
    row: Mapping[str, object],
    *,
    source_id: str,
) -> dict[str, int]:
    summary = _as_mapping(row.get("summary"))
    gold_replace = _int_value(row, summary, "gold_replace_cases")
    gold_abstain = _int_value(row, summary, "gold_abstain_cases")
    false_abstain = _int_value(row, summary, "false_abstain_count")
    harmful_replace = _int_value(row, summary, "harmful_replace_count")
    config_id = str(row.get("config_id") or "")
    if gold_replace < 0 or gold_abstain < 0:
        raise ValueError(f"{source_id}:{config_id} has negative gold case counts.")
    if false_abstain < 0 or false_abstain > gold_replace:
        raise ValueError(
            f"{source_id}:{config_id} false abstains exceed gold replace cases "
            f"({false_abstain} > {gold_replace})."
        )
    if harmful_replace < 0 or harmful_replace > gold_abstain:
        raise ValueError(
            f"{source_id}:{config_id} harmful replacements exceed gold abstain cases "
            f"({harmful_replace} > {gold_abstain})."
        )
    return {
        "positive_allow": gold_replace - false_abstain,
        "positive_abstain": false_abstain,
        "negative_abstain": gold_abstain - harmful_replace,
        "negative_allow": harmful_replace,
    }


def _int_value(
    row: Mapping[str, object],
    summary: Mapping[str, object],
    key: str,
) -> int:
    if row.get(key) is not None:
        return int(row.get(key) or 0)
    return int(summary.get(key) or 0)


def _infer_source_type(payload: Mapping[str, object]) -> str:
    if isinstance(payload.get("rows"), Sequence) and not isinstance(
        payload.get("rows"),
        (str, bytes),
    ):
        return "sentence_veto_sweep"
    if isinstance(payload.get("config_rows"), Sequence) and not isinstance(
        payload.get("config_rows"),
        (str, bytes),
    ):
        return "decision_rule_matrix"
    return ""


def _row_key_for_source_type(source_type: str) -> str:
    if source_type == "sentence_veto_sweep":
        return "rows"
    if source_type == "decision_rule_matrix":
        return "config_rows"
    raise ValueError(f"Unsupported product objective bakeoff source type: {source_type!r}")


def _default_source_id(path: Path | None, source_type: str, source_index: int) -> str:
    if path is None:
        return f"{source_type}_{source_index}"
    stem = path.stem
    if stem.endswith("_latest"):
        stem = stem[: -len("_latest")]
    return stem


def _best_by_product_rank(rows: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    materialized = _mapping_rows(rows)
    if not materialized:
        return None
    return sorted(materialized, key=_product_rank_key)[0]


def _best_by_utility(rows: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    materialized = _mapping_rows(rows)
    if not materialized:
        return None
    return sorted(materialized, key=_utility_rank_key)[0]


def _closest_target_shape(rows: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    materialized = _mapping_rows(rows)
    if not materialized:
        return None
    return sorted(materialized, key=_target_distance_rank_key)[0]


def _product_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    metrics = _as_mapping(row.get("metrics"))
    checks = _as_mapping(row.get("target_checks"))
    return (
        str(checks.get("target_status") or "") != "pass",
        -_safe_float(metrics.get("utility_score")),
        _safe_float(row.get("target_distance")),
        -_safe_float(metrics.get("positive_allow_rate")),
        -_safe_float(metrics.get("negative_abstain_rate")),
        str(row.get("source_id") or ""),
        str(row.get("config_id") or ""),
    )


def _utility_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    metrics = _as_mapping(row.get("metrics"))
    return (
        -_safe_float(metrics.get("utility_score")),
        _safe_float(row.get("target_distance")),
        str(row.get("source_id") or ""),
        str(row.get("config_id") or ""),
    )


def _target_distance_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    metrics = _as_mapping(row.get("metrics"))
    return (
        _safe_float(row.get("target_distance")),
        -_safe_float(metrics.get("utility_score")),
        -_safe_float(metrics.get("positive_allow_rate")),
        -_safe_float(metrics.get("negative_abstain_rate")),
        str(row.get("source_id") or ""),
        str(row.get("config_id") or ""),
    )


def _shortfall(value: object, threshold: float) -> float:
    if value is None:
        return threshold
    return round(max(0.0, threshold - _safe_float(value)), 4)


def _public_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(row, Mapping):
        return None
    metrics = _as_mapping(row.get("metrics"))
    checks = _as_mapping(row.get("target_checks"))
    return {
        "source_id": str(row.get("source_id") or ""),
        "source_type": str(row.get("source_type") or ""),
        "config_id": str(row.get("config_id") or ""),
        "label": str(row.get("label") or ""),
        "category": str(row.get("category") or ""),
        "algorithm_family": str(row.get("algorithm_family") or ""),
        "is_control": bool(row.get("is_control")),
        "scorer_id": str(row.get("scorer_id") or ""),
        "context_view": str(row.get("context_view") or ""),
        "evidence_view": str(row.get("evidence_view") or ""),
        "sense_representation": str(row.get("sense_representation") or ""),
        "aggregation_rule": str(row.get("aggregation_rule") or ""),
        "decision_rule": str(row.get("decision_rule") or ""),
        "phrase_handling": str(row.get("phrase_handling") or ""),
        "phrase_control_mode": str(row.get("phrase_control_mode") or ""),
        "active_rescue_mode": str(row.get("active_rescue_mode") or ""),
        "min_active_score": row.get("min_active_score"),
        "min_margin": row.get("min_margin"),
        "positive_allow_rate": metrics.get("positive_allow_rate"),
        "negative_abstain_rate": metrics.get("negative_abstain_rate"),
        "positive_allow_count": metrics.get("positive_allow_count"),
        "positive_abstain_count": metrics.get("positive_abstain_count"),
        "negative_abstain_count": metrics.get("negative_abstain_count"),
        "negative_allow_count": metrics.get("negative_allow_count"),
        "utility_score": metrics.get("utility_score"),
        "target_status": str(checks.get("target_status") or ""),
        "target_distance": row.get("target_distance"),
        "positive_allow_shortfall": row.get("positive_allow_shortfall"),
        "negative_abstain_shortfall": row.get("negative_abstain_shortfall"),
        "decision_accuracy": row.get("decision_accuracy"),
        "winner_accuracy": row.get("winner_accuracy"),
        "replace_recall": row.get("replace_recall"),
        "original_objective_score": row.get("original_objective_score"),
    }


def _source_table(rows_value: object) -> str:
    rows = _mapping_rows(rows_value)
    if not rows:
        return "_No sources._"
    lines = [
        "| Source | Type | Input rows | Product rows | Target pass | Best config | Best pos allow | Best neg abstain | Best utility |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        best = _as_mapping(row.get("best_product_rank_row"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("source_id") or "")),
                    _escape_md(str(row.get("source_type") or "")),
                    str(row.get("input_row_count", 0)),
                    str(row.get("product_row_count", 0)),
                    str(row.get("target_pass_count", 0)),
                    _escape_md(str(best.get("config_id") or "")),
                    _format_percent(best.get("positive_allow_rate")),
                    _format_percent(best.get("negative_abstain_rate")),
                    str(best.get("utility_score", "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _row_table(rows_value: object) -> str:
    rows = _mapping_rows(rows_value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Source | Config | Scorer | Evidence | Rule | Pos allow | Neg abstain | Utility | Target | Distance |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        evidence = str(row.get("evidence_view") or row.get("sense_representation") or "")
        rule = str(row.get("decision_rule") or row.get("phrase_control_mode") or "")
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("source_id") or "")),
                    _escape_md(str(row.get("config_id") or "")),
                    _escape_md(str(row.get("scorer_id") or "")),
                    _escape_md(evidence),
                    _escape_md(rule),
                    _format_percent(row.get("positive_allow_rate")),
                    _format_percent(row.get("negative_abstain_rate")),
                    str(row.get("utility_score", "")),
                    _escape_md(str(row.get("target_status") or "")),
                    str(row.get("target_distance", "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _recommendation(
    *,
    target_pass_rows: Sequence[Mapping[str, object]],
    issues: Sequence[Mapping[str, object]],
) -> list[str]:
    if issues:
        return [
            "Fix bakeoff input/read issues before treating the ranking as evidence.",
            "Do not compare product candidates until every configured source row is accounted for.",
        ]
    if target_pass_rows:
        return [
            "At least one historical row meets the configured product target.",
            "Validate the passing row on heldout or expanded representative lanes before promotion.",
        ]
    return [
        "No historical sweep or matrix row meets the configured product target.",
        "Treat the incumbent as a baseline under the old objective, not as proven best for product acceptance.",
        "Use the closest-target rows to decide whether the next expansion should prioritize permissive decision rules, source evidence, or broader representative data.",
    ]


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
