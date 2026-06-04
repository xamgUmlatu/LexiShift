#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from semantic_routing_sentence_veto_support import build_sentence_veto_report  # noqa: E402
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _format_percent,
    _load_json,
    _mapping_rows,
    _repo_path,
    _safe_float,
)


TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_BAKEOFF_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_algorithm_bakeoff_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_selected_candidate_surface_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_selected_candidate_surface_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize selected product-scope algorithm candidates into per-case "
            "score-surface rows for downstream band/heuristic sweeps."
        )
    )
    parser.add_argument("--bakeoff-json", type=Path, default=DEFAULT_BAKEOFF_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bakeoff = _load_json(args.bakeoff_json)
    filtered_dataset_path = _resolve_repo_path(
        str(_as_mapping(bakeoff.get("inputs")).get("filtered_dataset_path") or "")
    )
    candidate_specs = select_candidate_specs(bakeoff)
    candidate_reports = [
        {
            "candidate_id": spec["candidate_id"],
            "selection_reason": spec["selection_reason"],
            "candidate": spec["candidate"],
            "report": build_sentence_veto_report(
                dataset_path=filtered_dataset_path,
                scorer_id=str(spec["candidate"].get("scorer_id") or ""),
                context_view=str(spec["candidate"].get("context_view") or ""),
                evidence_view=str(spec["candidate"].get("evidence_view") or ""),
                min_active_score=float(spec["candidate"].get("min_active_score") or 0.0),
                min_margin=float(spec["candidate"].get("min_margin") or 0.0),
                phrase_control_mode=str(spec["candidate"].get("phrase_control_mode") or ""),
                active_rescue_mode=str(spec["candidate"].get("active_rescue_mode") or ""),
            ),
        }
        for spec in candidate_specs
    ]
    report = build_selected_candidate_surface_report(
        bakeoff_payload=bakeoff,
        candidate_reports=candidate_reports,
        bakeoff_path=args.bakeoff_json,
        filtered_dataset_path=filtered_dataset_path,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_selected_candidate_surface_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def select_candidate_specs(bakeoff_payload: Mapping[str, object]) -> list[dict[str, object]]:
    summary = _as_mapping(bakeoff_payload.get("summary"))
    specs: list[dict[str, object]] = []
    for reason, row in (
        ("best_product_rank", summary.get("best_product_rank_row")),
        ("safest_80pct_positive", summary.get("safest_80pct_positive_row")),
        ("high_recall_soft_assist", summary.get("high_recall_soft_assist_row")),
    ):
        spec = _candidate_spec(reason, _as_mapping(row))
        if spec:
            specs.append(spec)
    for row in _mapping_rows(summary.get("current_policy_like_rows")):
        scorer = str(row.get("scorer_id") or "")
        if scorer == "sentence_transformer_cosine":
            spec = _candidate_spec("current_v3_like", row)
            if spec:
                specs.append(spec)
    for row in _mapping_rows(summary.get("best_by_scorer")):
        scorer = str(row.get("scorer_id") or "")
        if scorer == "tfidf_cosine":
            spec = _candidate_spec("tfidf_best_by_scorer", row)
            if spec:
                specs.append(spec)
    deduped: list[dict[str, object]] = []
    seen: set[str] = set()
    for spec in specs:
        config_id = str(_as_mapping(spec.get("candidate")).get("config_id") or "")
        if not config_id or config_id in seen:
            continue
        seen.add(config_id)
        deduped.append(spec)
    return deduped


def build_selected_candidate_surface_report(
    *,
    bakeoff_payload: Mapping[str, object],
    candidate_reports: Sequence[Mapping[str, object]],
    bakeoff_path: Path | None = None,
    filtered_dataset_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    issues: list[str] = []
    row_results: list[dict[str, object]] = []
    candidate_summaries: list[dict[str, object]] = []
    if not candidate_reports:
        issues.append("no_candidate_reports")
    for candidate_report in candidate_reports:
        candidate = _as_mapping(candidate_report.get("candidate"))
        report = _as_mapping(candidate_report.get("report"))
        candidate_id = str(candidate_report.get("candidate_id") or "").strip()
        if not candidate_id:
            candidate_id = _candidate_id(
                str(candidate_report.get("selection_reason") or "candidate"),
                candidate,
            )
        config = _as_mapping(report.get("config"))
        rows = _normalize_candidate_rows(
            candidate_id=candidate_id,
            selection_reason=str(candidate_report.get("selection_reason") or ""),
            candidate=candidate,
            report_rows=_mapping_rows(report.get("row_results")),
        )
        row_results.extend(rows)
        candidate_summaries.append(
            {
                "candidate_id": candidate_id,
                "selection_reason": str(candidate_report.get("selection_reason") or ""),
                "source_config_id": str(candidate.get("config_id") or ""),
                "base_scorer_id": str(config.get("scorer_id") or candidate.get("scorer_id") or ""),
                "context_view": str(
                    config.get("context_view") or candidate.get("context_view") or ""
                ),
                "evidence_view": str(
                    config.get("evidence_view") or candidate.get("evidence_view") or ""
                ),
                "phrase_control_mode": str(
                    config.get("phrase_control_mode") or candidate.get("phrase_control_mode") or ""
                ),
                "active_rescue_mode": str(
                    config.get("active_rescue_mode") or candidate.get("active_rescue_mode") or ""
                ),
                "min_active_score": candidate.get("min_active_score"),
                "min_margin": candidate.get("min_margin"),
                "case_count": len(rows),
                "metrics": _metrics(rows),
            }
        )
        if not rows:
            issues.append(f"no_rows_for_candidate:{candidate_id}")
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "product_scope_selected_candidate_surface_established"
            if status == "ok"
            else "product_scope_selected_candidate_surface_needs_review"
        ),
        "generated_at": generated_at,
        "pair": str(bakeoff_payload.get("pair") or "en-es"),
        "inputs": {
            "bakeoff_path": _repo_path(bakeoff_path),
            "filtered_dataset_path": _repo_path(filtered_dataset_path),
            "bakeoff_decision": str(bakeoff_payload.get("decision") or ""),
        },
        "methodology": {
            "purpose": (
                "Carry selected product-scope algorithm peaks into downstream "
                "band/formula sweeps as per-case traces."
            ),
            "runtime_policy_change": "none",
            "selection_reasons": sorted(
                {str(row.get("selection_reason") or "") for row in candidate_summaries}
            ),
            "candidate_id_note": (
                "row_results.scorer_id is intentionally set to candidate_id so existing "
                "family/formula sweep tooling can compare selected algorithm rows."
            ),
        },
        "summary": {
            "issues": issues,
            "candidate_count": len(candidate_summaries),
            "row_result_count": len(row_results),
            "candidate_summaries": candidate_summaries,
        },
        "row_results": row_results,
        "limitations": [
            "candidate_set_is_selected_from_discovery_bakeoff",
            "filtered_repaired_full_is_not_final_browsing_distribution",
            "candidate_id_is_encoded_as_scorer_id_for_downstream_sweep_compatibility",
        ],
        "next_steps": [
            "Run repaired-full band/formula sweep with this report as score-surface input.",
            "Compare whether heuristic signals still rank hard families under the corrected candidate rows.",
        ],
    }


def render_selected_candidate_surface_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Product-Scope Selected Candidate Surface",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidates: `{summary.get('candidate_count', 0)}`",
        f"- Row results: `{summary.get('row_result_count', 0)}`",
        "",
        "## Candidates",
        "",
        _candidate_table(summary.get("candidate_summaries")),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    if summary.get("issues"):
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- `{item}`" for item in _sequence(summary.get("issues")))
    return "\n".join(lines) + "\n"


def _candidate_spec(reason: str, row: Mapping[str, object]) -> dict[str, object] | None:
    if not row:
        return None
    return {
        "candidate_id": _candidate_id(reason, row),
        "selection_reason": reason,
        "candidate": dict(row),
    }


def _candidate_id(reason: str, row: Mapping[str, object]) -> str:
    scorer = str(row.get("scorer_id") or "scorer").replace("_cosine", "")
    margin = _margin_label(row.get("min_margin"))
    active = _margin_label(row.get("min_active_score"))
    raw = f"{reason}_{scorer}_a{active}_m{margin}"
    return re.sub(r"[^0-9A-Za-z_]+", "_", raw).strip("_").lower()


def _margin_label(value: object) -> str:
    number = _safe_float(value)
    text = f"{number:.3f}".replace("-", "neg").replace(".", "")
    return text


def _normalize_candidate_rows(
    *,
    candidate_id: str,
    selection_reason: str,
    candidate: Mapping[str, object],
    report_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    rows = []
    for row in report_rows:
        gold = str(row.get("gold_decision") or "")
        predicted = str(row.get("predicted_decision") or "")
        copied = dict(row)
        copied["scorer_id"] = candidate_id
        copied["candidate_id"] = candidate_id
        copied["selection_reason"] = selection_reason
        copied["base_scorer_id"] = str(candidate.get("scorer_id") or "")
        copied["candidate_config_id"] = str(candidate.get("config_id") or "")
        copied["error_type"] = _error_type(gold=gold, predicted=predicted)
        rows.append(copied)
    return rows


def _metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    cases = len(rows)
    gold_replace = sum(1 for row in rows if row.get("gold_decision") == "replace")
    gold_abstain = sum(1 for row in rows if row.get("gold_decision") == "abstain")
    false_abstain = sum(1 for row in rows if row.get("error_type") == "false_abstain")
    harmful = sum(1 for row in rows if row.get("error_type") == "harmful_replace")
    true_replace = gold_replace - false_abstain
    true_abstain = gold_abstain - harmful
    return {
        "case_count": cases,
        "positive_allow_rate": _rate(true_replace, gold_replace),
        "negative_abstain_rate": _rate(true_abstain, gold_abstain),
        "harmful_replace_count": harmful,
        "false_abstain_count": false_abstain,
        "decision_accuracy": _rate(true_replace + true_abstain, cases),
    }


def _error_type(*, gold: str, predicted: str) -> str:
    if gold == predicted:
        return ""
    if gold == "replace" and predicted != "replace":
        return "false_abstain"
    if gold != "replace" and predicted == "replace":
        return "harmful_replace"
    return "other_mismatch"


def _candidate_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No candidates._"
    lines = [
        "| Candidate | Reason | Base scorer | Phrase | Rescue | Pos allow | Neg abstain | Harmful | False abstain |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        metrics = _as_mapping(row.get("metrics"))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('candidate_id') or ''))}`",
                    f"`{_escape_md(str(row.get('selection_reason') or ''))}`",
                    f"`{_escape_md(str(row.get('base_scorer_id') or ''))}`",
                    f"`{_escape_md(str(row.get('phrase_control_mode') or ''))}`",
                    f"`{_escape_md(str(row.get('active_rescue_mode') or ''))}`",
                    _format_percent(metrics.get("positive_allow_rate")),
                    _format_percent(metrics.get("negative_abstain_rate")),
                    str(metrics.get("harmful_replace_count", 0)),
                    str(metrics.get("false_abstain_count", 0)),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
