#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_heuristic_difficulty_surface_analysis import (
    _authored_by_trigger,
    _build_breakdowns,
    _failure_concentration,
    _formula_bakeoff,
    _metrics_for_rows,
    _normalized_score_rows,
    _veto_only_summary,
)
from semantic_veto_heuristic_difficulty_surface_expansion import _expansion_plan
from semantic_veto_heuristic_difficulty_surface_common import (
    PRIMARY_SELECTION_MODE,
    _load_json,
    _load_optional_json,
    _repo_path,
    _utc_now,
)
from semantic_veto_heuristic_difficulty_surface_rendering import (
    render_heuristic_difficulty_surface_markdown as render_heuristic_difficulty_surface_markdown,
)
from semantic_veto_product_quality_en_es import _as_mapping, _utility_weights


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_POLICY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_veto_product_quality_policy_en_es.json"
)
DEFAULT_AUTHORING_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_group_case_authoring_en_es_latest.json"
)
DEFAULT_TFIDF_REPORT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_group_sentence_veto_tfidf_en_es_latest.json"
)
DEFAULT_ST_REPORT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_group_sentence_veto_st_en_es_latest.json"
)
DEFAULT_VETO_ONLY_REPORT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_group_veto_only_validation_st_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_difficulty_surface_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_difficulty_surface_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Map the en-es heuristic-group dataset from source-word features and case "
            "shapes to observed semantic-veto difficulty. This is research-only."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--authoring-json", type=Path, default=DEFAULT_AUTHORING_JSON)
    parser.add_argument("--tfidf-report-json", type=Path, default=DEFAULT_TFIDF_REPORT)
    parser.add_argument("--sentence-transformer-report-json", type=Path, default=DEFAULT_ST_REPORT)
    parser.add_argument("--veto-only-json", type=Path, default=DEFAULT_VETO_ONLY_REPORT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    policy = _load_json(args.policy_json)
    report = build_heuristic_difficulty_surface_report(
        policy=policy,
        authoring_payload=_load_json(args.authoring_json),
        score_sources=[
            {
                "source_id": "tfidf_cosine",
                "path": args.tfidf_report_json,
                "report": _load_json(args.tfidf_report_json),
            },
            {
                "source_id": "sentence_transformer_cosine",
                "path": args.sentence_transformer_report_json,
                "report": _load_json(args.sentence_transformer_report_json),
            },
        ],
        veto_only_payload=_load_optional_json(args.veto_only_json),
        policy_path=args.policy_json,
        authoring_path=args.authoring_json,
        veto_only_path=args.veto_only_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_heuristic_difficulty_surface_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_heuristic_difficulty_surface_report(
    *,
    policy: Mapping[str, object],
    authoring_payload: Mapping[str, object],
    score_sources: Sequence[Mapping[str, object]],
    veto_only_payload: Mapping[str, object] | None = None,
    policy_path: Path | None = None,
    authoring_path: Path | None = None,
    veto_only_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    weights = _utility_weights(policy)
    acceptance = _as_mapping(policy.get("acceptance"))
    authored_by_trigger = _authored_by_trigger(authoring_payload)
    normalized_rows: list[dict[str, object]] = []
    score_source_summaries = []
    for source in score_sources:
        source_id = str(source.get("source_id") or "").strip()
        report = _as_mapping(source.get("report"))
        source_path = source.get("path") if isinstance(source.get("path"), Path) else None
        source_rows = _normalized_score_rows(
            report=report,
            source_id=source_id,
            source_path=source_path,
            authored_by_trigger=authored_by_trigger,
        )
        normalized_rows.extend(source_rows)
        score_source_summaries.append(
            {
                "source_id": source_id,
                "path": _repo_path(source_path),
                "scorer_id": str(_as_mapping(report.get("config")).get("scorer_id") or source_id),
                "case_rows": len(source_rows),
                "report_status": str(report.get("status") or ""),
            }
        )

    issues = []
    if not authored_by_trigger:
        issues.append("authoring_report_has_no_authored_triggers")
    if not normalized_rows:
        issues.append("no_score_rows_available")

    overall = _metrics_for_rows(normalized_rows, weights=weights, acceptance=acceptance)
    primary_rows = [
        row for row in normalized_rows if row.get("selection_mode") == PRIMARY_SELECTION_MODE
    ]
    primary = _metrics_for_rows(primary_rows, weights=weights, acceptance=acceptance)
    breakdowns = _build_breakdowns(
        rows=normalized_rows,
        weights=weights,
        acceptance=acceptance,
    )
    formula_bakeoff = _formula_bakeoff(
        rows=normalized_rows,
        authored_by_trigger=authored_by_trigger,
        weights=weights,
        acceptance=acceptance,
    )
    expansion_plan = _expansion_plan(
        rows=normalized_rows,
        authored_by_trigger=authored_by_trigger,
        weights=weights,
        acceptance=acceptance,
    )
    veto_only_summary = _veto_only_summary(veto_only_payload)
    return {
        "schema_version": 1,
        "status": "review" if issues else "ok",
        "decision": (
            "heuristic_difficulty_surface_established"
            if not issues
            else "heuristic_difficulty_surface_incomplete"
        ),
        "generated_at": generated_at,
        "pair": str(policy.get("pair") or "en-es"),
        "inputs": {
            "policy_path": _repo_path(policy_path),
            "authoring_path": _repo_path(authoring_path),
            "veto_only_path": _repo_path(veto_only_path),
            "score_sources": score_source_summaries,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
            "control_formula": "source_rank_plus_wordnet_sense_and_pos_count",
            "primary_validation_selection_mode": PRIMARY_SELECTION_MODE,
            "sentinel_excluded_from_primary_formula_validation": True,
            "missing_rank_policy": "missing_rank_is_bucketed_and_excluded_from_rank_formula_correlation",
            "difficulty_formula": (
                "weighted_loss_rate = observed_utility_loss / worst_possible_utility_loss "
                "using semantic_veto_product_quality utility weights"
            ),
        },
        "summary": {
            "authored_trigger_count": len(authored_by_trigger),
            "score_row_count": len(normalized_rows),
            "scorer_count": len({row["scorer_id"] for row in normalized_rows}),
            "primary_score_row_count": len(primary_rows),
            "sentinel_score_row_count": len(normalized_rows) - len(primary_rows),
            "issues": issues,
            "overall": overall,
            "primary_only": primary,
            "veto_only_reference": veto_only_summary,
        },
        "breakdowns": breakdowns,
        "failure_concentration": _failure_concentration(normalized_rows),
        "formula_bakeoff": formula_bakeoff,
        "expansion_plan": expansion_plan,
        "case_traces": normalized_rows,
        "limitations": [
            "agent_authored_cases_need_human_review_before_promotion_claims",
            "formula_bakeoff_is_correlation_not_causal_proof",
            "sentence_transformer_phrase_score_lead_is_unavailable_in_current_sentence_veto_rows",
            "sentinel_rows_are_outcome_informed_and_excluded_from_primary_heuristic_validation",
            "runtime_policy_remains_unchanged",
        ],
        "next_steps": [
            "Review formula bakeoff rows to decide which feature family predicts each failure class.",
            "Expand phrase/no-winner cells before spending broad LLM budget.",
            "Keep low-polysemy controls positive-plus-phrase unless a real alternate sense is found.",
            "Human-review draft target/shadow choices before using this lane as locked evaluation.",
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
