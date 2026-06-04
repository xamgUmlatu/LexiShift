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
    _safe_float,
    _utility_weights,
    score_product_outcome_counts,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_veto_product_quality_policy_en_es.json"
)
DEFAULT_MATRIX_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_decision_rule_matrix_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_veto_only_probe_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_veto_only_probe_en_es_latest.md"
)
VETO_ONLY_PHRASE_MODES = ("shadow_only", "shadow_or_phrase", "shadow_or_phrase_score")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay decision-matrix case traces as an allow-by-default semantic veto: "
            "show replacements unless shadow or phrase evidence is strong enough to block."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--matrix-json", type=Path, default=DEFAULT_MATRIX_JSON)
    parser.add_argument(
        "--config-ids",
        type=str,
        default="",
        help="Optional comma-separated matrix config ids to replay. Defaults to all configs.",
    )
    parser.add_argument(
        "--shadow-lead-grid",
        type=str,
        default="-0.05,-0.02,0.00,0.02,0.05,0.08,0.10,0.15,0.20",
        help="Comma-separated strongest-shadow minus active-score thresholds.",
    )
    parser.add_argument(
        "--shadow-score-grid",
        type=str,
        default="0.00,0.02,0.05,0.10,0.20,0.35,0.45,0.50,0.55,0.60,0.65",
        help="Comma-separated minimum strongest-shadow scores.",
    )
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    policy = _load_json(args.policy_json)
    matrix = _load_json(args.matrix_json)
    report = build_veto_only_probe_report(
        policy=policy,
        matrix=matrix,
        policy_path=args.policy_json,
        matrix_path=args.matrix_json,
        config_ids=_parse_string_grid(args.config_ids),
        shadow_lead_grid=_parse_float_grid(args.shadow_lead_grid),
        shadow_score_grid=_parse_float_grid(args.shadow_score_grid),
        top_n=max(1, int(args.top_n)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_veto_only_probe_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_veto_only_probe_report(
    *,
    policy: Mapping[str, object],
    matrix: Mapping[str, object],
    policy_path: Path | None = None,
    matrix_path: Path | None = None,
    config_ids: Sequence[str] = (),
    shadow_lead_grid: Sequence[float] = (),
    shadow_score_grid: Sequence[float] = (),
    top_n: int = 12,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    weights = _utility_weights(policy)
    acceptance = _as_mapping(policy.get("acceptance"))
    matrix_configs = {
        str(row.get("config_id") or ""): row for row in _mapping_rows(matrix.get("config_rows"))
    }
    cases_by_config = _cases_by_config(matrix.get("case_results"))
    selected_config_ids = _selected_config_ids(
        requested=config_ids,
        available=tuple(cases_by_config),
    )
    if not selected_config_ids:
        raise ValueError("Veto-only probe has no matrix configs to replay.")
    normalized_shadow_leads = _normalize_float_grid(
        shadow_lead_grid,
        default=(-0.05, -0.02, 0.0, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2),
    )
    normalized_shadow_scores = _normalize_float_grid(
        shadow_score_grid,
        default=(0.0, 0.02, 0.05, 0.1, 0.2, 0.35, 0.45, 0.5, 0.55, 0.6, 0.65),
    )
    phrase_modes = VETO_ONLY_PHRASE_MODES
    rows: list[dict[str, object]] = []
    for config_id in selected_config_ids:
        case_rows = cases_by_config[config_id]
        config = matrix_configs.get(config_id, {})
        for phrase_mode in phrase_modes:
            for shadow_lead_min in normalized_shadow_leads:
                for shadow_score_min in normalized_shadow_scores:
                    rows.append(
                        _evaluate_veto_only_config(
                            config_id=config_id,
                            config=config,
                            case_rows=case_rows,
                            phrase_mode=phrase_mode,
                            shadow_lead_min=float(shadow_lead_min),
                            shadow_score_min=float(shadow_score_min),
                            weights=weights,
                            acceptance=acceptance,
                        )
                    )
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
            "veto_only_product_target_pass_found"
            if target_pass_rows
            else "veto_only_product_target_not_met"
        ),
        "generated_at": generated_at,
        "pair": str(policy.get("pair") or matrix.get("pair") or "en-es"),
        "policy": {
            "path": _repo_path(policy_path),
            "policy_id": str(policy.get("policy_id") or ""),
            "acceptance": dict(acceptance),
            "utility_weights": weights,
        },
        "matrix": {
            "path": _repo_path(matrix_path),
            "matrix_id": str(matrix.get("matrix_id") or ""),
            "dataset_id": str(matrix.get("dataset_id") or ""),
            "dataset_path": str(matrix.get("dataset_path") or ""),
            "case_result_count": len(_mapping_rows(matrix.get("case_results"))),
            "config_count": len(cases_by_config),
        },
        "e2e_checks": {
            "calculus_source": (
                "scripts/testing/semantic_veto_product_quality_en_es.py::"
                "score_product_outcome_counts"
            ),
            "input_case_results_read": sum(
                len(cases_by_config[cid]) for cid in selected_config_ids
            ),
            "selected_config_count": len(selected_config_ids),
            "policy_rows_emitted": len(rows),
            "phrase_modes": list(phrase_modes),
            "shadow_lead_grid": normalized_shadow_leads,
            "shadow_score_grid": normalized_shadow_scores,
        },
        "summary": {
            "row_count": len(rows),
            "target_pass_count": len(target_pass_rows),
            "top_n": max(1, int(top_n)),
            "best_product_rank_row": _public_probe_row(ranked_rows[0] if ranked_rows else None),
            "best_target_pass_row": _public_probe_row(
                target_pass_rows[0] if target_pass_rows else None
            ),
            "best_by_source_config": [
                _public_probe_row(
                    _best_by_rank([row for row in ranked_rows if row["config_id"] == cid])
                )
                for cid in selected_config_ids
            ],
            "recommendation": _recommendation(target_pass_rows=target_pass_rows),
        },
        "top_rows": [_public_probe_row(row) for row in ranked_rows[: max(1, int(top_n))]],
        "target_pass_rows": [
            _public_probe_row(row) for row in target_pass_rows[: max(1, int(top_n))]
        ],
        "failure_samples": _failure_samples(ranked_rows[0] if ranked_rows else None),
        "rows": [_public_probe_row(row) for row in ranked_rows],
    }


def render_veto_only_probe_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Veto-Only Probe",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Policy: `{_as_mapping(report.get('policy')).get('path', '')}`",
        f"- Matrix: `{_as_mapping(report.get('matrix')).get('path', '')}`",
        f"- Rows evaluated: `{summary.get('row_count', 0)}`",
        f"- Product target pass rows: `{summary.get('target_pass_count', 0)}`",
        "",
        "## E2E Checks",
        "",
        _checks_table(report.get("e2e_checks")),
        "",
        "## Top Veto-Only Rows",
        "",
        _probe_row_table(report.get("top_rows")),
        "",
        "## Passing Rows",
        "",
        _probe_row_table(report.get("target_pass_rows")),
        "",
        "## Best By Source Config",
        "",
        _probe_row_table(summary.get("best_by_source_config")),
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


def _evaluate_veto_only_config(
    *,
    config_id: str,
    config: Mapping[str, object],
    case_rows: Sequence[Mapping[str, object]],
    phrase_mode: str,
    shadow_lead_min: float,
    shadow_score_min: float,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    outcome_counts: Counter[str] = Counter()
    evaluated_cases: list[dict[str, object]] = []
    for case in case_rows:
        veto_hit, veto_reason = _veto_hit(
            case=case,
            phrase_mode=phrase_mode,
            shadow_lead_min=shadow_lead_min,
            shadow_score_min=shadow_score_min,
        )
        predicted_decision = "abstain" if veto_hit else "replace"
        gold_decision = _normalize_gold_decision(case.get("gold_decision"))
        product_outcome = _product_outcome(gold=gold_decision, predicted=predicted_decision)
        outcome_counts[product_outcome] += 1
        evaluated_cases.append(
            {
                "case_id": str(case.get("case_id") or ""),
                "report_id": str(case.get("report_id") or ""),
                "suite_id": str(case.get("suite_id") or ""),
                "family_id": str(case.get("family_id") or ""),
                "trigger": str(case.get("trigger") or ""),
                "sentence": str(case.get("sentence") or ""),
                "gold_decision": gold_decision,
                "gold_winner_type": str(case.get("gold_winner_type") or ""),
                "predicted_decision": predicted_decision,
                "product_outcome": product_outcome,
                "veto_reason": veto_reason,
                "active_score": _round4(case.get("active_score")),
                "strongest_shadow_score": _round4(case.get("strongest_shadow_score")),
                "shadow_lead": _round4(
                    _safe_float(case.get("strongest_shadow_score"))
                    - _safe_float(case.get("active_score"))
                ),
                "phrase_preemption_hit": bool(case.get("phrase_preemption_hit")),
            }
        )
    metrics = score_product_outcome_counts(
        outcome_counts=outcome_counts,
        weights=weights,
        acceptance=acceptance,
    )
    return {
        "config_id": config_id,
        "label": str(config.get("label") or ""),
        "category": str(config.get("category") or ""),
        "algorithm_family": str(config.get("algorithm_family") or ""),
        "is_control": bool(config.get("is_control")),
        "scorer_id": str(config.get("scorer_id") or ""),
        "model_name": str(config.get("model_name") or ""),
        "context_view": str(config.get("context_view") or ""),
        "sense_representation": str(config.get("sense_representation") or ""),
        "aggregation_rule": str(config.get("aggregation_rule") or ""),
        "decision_rule": "allow_default_shadow_veto",
        "source_decision_rule": str(config.get("decision_rule") or ""),
        "source_phrase_handling": str(config.get("phrase_handling") or ""),
        "phrase_mode": phrase_mode,
        "shadow_lead_min": _round4(shadow_lead_min),
        "shadow_score_min": _round4(shadow_score_min),
        "metrics": metrics,
        "target_checks": dict(_as_mapping(metrics.get("target_checks"))),
        "case_results": evaluated_cases,
    }


def _veto_hit(
    *,
    case: Mapping[str, object],
    phrase_mode: str,
    shadow_lead_min: float,
    shadow_score_min: float,
) -> tuple[bool, str]:
    if phrase_mode == "shadow_or_phrase" and bool(case.get("phrase_preemption_hit")):
        return True, "phrase_preemption"
    active_score = _safe_float(case.get("active_score"))
    shadow_score = _safe_float(case.get("strongest_shadow_score"))
    phrase_score = _safe_float(case.get("phrase_control_score"))
    shadow_lead = shadow_score - active_score
    if phrase_mode == "shadow_or_phrase_score":
        if bool(case.get("phrase_preemption_hit")):
            return True, "phrase_preemption"
        if (
            phrase_score >= shadow_score_min
            and phrase_score - max(active_score, shadow_score) >= shadow_lead_min
        ):
            return True, "phrase_score_lead"
    if shadow_score >= shadow_score_min and shadow_lead >= shadow_lead_min:
        return True, "shadow_lead"
    return False, ""


def _cases_by_config(value: object) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in _mapping_rows(value):
        config_id = str(row.get("config_id") or "").strip()
        if config_id:
            grouped[config_id].append(row)
    return dict(grouped)


def _selected_config_ids(
    *,
    requested: Sequence[str],
    available: Sequence[str],
) -> list[str]:
    available_set = set(available)
    if requested:
        missing = [config_id for config_id in requested if config_id not in available_set]
        if missing:
            raise ValueError(f"Requested matrix config ids not found: {missing!r}")
        return [config_id for config_id in requested if config_id in available_set]
    return sorted(available)


def _product_outcome(*, gold: str, predicted: str) -> str:
    product_class = "positive" if gold == "replace" else "negative"
    user_outcome = "allow" if predicted == "replace" else "abstain"
    return f"{product_class}_{user_outcome}"


def _normalize_gold_decision(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"replace", "allow", "yes"}:
        return "replace"
    if text in {"abstain", "no", "none", "no_replace", "no-replace"}:
        return "abstain"
    raise ValueError(f"Unknown gold decision: {value!r}")


def _probe_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    metrics = _as_mapping(row.get("metrics"))
    checks = _as_mapping(row.get("target_checks"))
    return (
        str(checks.get("target_status") or "") != "pass",
        -_safe_float(metrics.get("utility_score")),
        -_safe_float(metrics.get("positive_allow_rate")),
        -_safe_float(metrics.get("negative_abstain_rate")),
        _safe_float(row.get("shadow_score_min")),
        _safe_float(row.get("shadow_lead_min")),
        str(row.get("config_id") or ""),
        str(row.get("phrase_mode") or ""),
    )


def _best_by_rank(rows: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    materialized = _mapping_rows(rows)
    if not materialized:
        return None
    return sorted(materialized, key=_probe_rank_key)[0]


def _public_probe_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(row, Mapping):
        return None
    metrics = _as_mapping(row.get("metrics"))
    checks = _as_mapping(row.get("target_checks"))
    return {
        "config_id": str(row.get("config_id") or ""),
        "label": str(row.get("label") or ""),
        "category": str(row.get("category") or ""),
        "algorithm_family": str(row.get("algorithm_family") or ""),
        "is_control": bool(row.get("is_control")),
        "scorer_id": str(row.get("scorer_id") or ""),
        "context_view": str(row.get("context_view") or ""),
        "sense_representation": str(row.get("sense_representation") or ""),
        "aggregation_rule": str(row.get("aggregation_rule") or ""),
        "decision_rule": str(row.get("decision_rule") or ""),
        "source_decision_rule": str(row.get("source_decision_rule") or ""),
        "source_phrase_handling": str(row.get("source_phrase_handling") or ""),
        "phrase_mode": str(row.get("phrase_mode") or ""),
        "shadow_lead_min": row.get("shadow_lead_min"),
        "shadow_score_min": row.get("shadow_score_min"),
        "positive_allow_rate": metrics.get("positive_allow_rate"),
        "negative_abstain_rate": metrics.get("negative_abstain_rate"),
        "positive_allow_count": metrics.get("positive_allow_count"),
        "positive_abstain_count": metrics.get("positive_abstain_count"),
        "negative_abstain_count": metrics.get("negative_abstain_count"),
        "negative_allow_count": metrics.get("negative_allow_count"),
        "utility_score": metrics.get("utility_score"),
        "target_status": str(checks.get("target_status") or ""),
    }


def _failure_samples(row: Mapping[str, object] | None) -> list[dict[str, object]]:
    if not isinstance(row, Mapping):
        return []
    failures = [
        case
        for case in _mapping_rows(row.get("case_results"))
        if str(case.get("product_outcome") or "") in {"positive_abstain", "negative_allow"}
    ]
    return [
        {
            "case_id": str(case.get("case_id") or ""),
            "report_id": str(case.get("report_id") or ""),
            "suite_id": str(case.get("suite_id") or ""),
            "trigger": str(case.get("trigger") or ""),
            "gold_decision": str(case.get("gold_decision") or ""),
            "gold_winner_type": str(case.get("gold_winner_type") or ""),
            "product_outcome": str(case.get("product_outcome") or ""),
            "veto_reason": str(case.get("veto_reason") or ""),
            "active_score": case.get("active_score"),
            "strongest_shadow_score": case.get("strongest_shadow_score"),
            "shadow_lead": case.get("shadow_lead"),
            "sentence": str(case.get("sentence") or ""),
        }
        for case in failures[:24]
    ]


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


def _probe_row_table(rows_value: object) -> str:
    rows = _mapping_rows(rows_value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Config | Scorer | Context | Evidence | Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("config_id") or "")),
                    _escape_md(str(row.get("scorer_id") or "")),
                    _escape_md(str(row.get("context_view") or "")),
                    _escape_md(str(row.get("sense_representation") or "")),
                    _escape_md(str(row.get("phrase_mode") or "")),
                    str(row.get("shadow_lead_min", "")),
                    str(row.get("shadow_score_min", "")),
                    _format_percent(row.get("positive_allow_rate")),
                    _format_percent(row.get("negative_abstain_rate")),
                    str(row.get("utility_score", "")),
                    _escape_md(str(row.get("target_status") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _failure_table(rows_value: object) -> str:
    rows = _mapping_rows(rows_value)
    if not rows:
        return "_No failures for the best row._"
    lines = [
        "| Case | Trigger | Gold | Winner | Outcome | Reason | Active | Shadow | Lead | Sentence |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
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
            "The allow-by-default veto-only framing found rows that meet the configured product target on frozen v10 matrix traces.",
            "Before runtime promotion, validate the best row on stress lanes and a broader representative lane.",
            "Inspect negative allows in the best row to decide which blocker evidence should be expanded next.",
        ]
    return [
        "The allow-by-default veto-only framing did not meet the configured product target on frozen v10 matrix traces.",
        "Use the best-row failure samples to decide whether the missing blocker is shadow evidence, phrase/no-winner evidence, or representative data.",
    ]


def _parse_string_grid(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _parse_float_grid(value: str) -> list[float]:
    return [float(item.strip()) for item in str(value or "").split(",") if item.strip()]


def _normalize_float_grid(
    values: Sequence[float],
    *,
    default: Sequence[float],
) -> list[float]:
    materialized = [float(value) for value in values]
    if not materialized:
        materialized = [float(value) for value in default]
    return sorted({_round4(value) for value in materialized})


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _round4(value: object) -> float:
    return round(_safe_float(value), 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
