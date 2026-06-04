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
)
from semantic_veto_veto_only_probe_en_es import _mapping_rows


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROBE_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_veto_only_probe_en_es_latest.json"
)
DEFAULT_VALIDATION_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_veto_only_validation_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_veto_only_candidate_selection_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_veto_only_candidate_selection_en_es_latest.md"
)
DEFAULT_PROBE_CONFIG_ID = "control_st_masked_all_margin_phrase_override"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Select shared allow-by-default semantic-veto blocker candidates that "
            "pass both frozen v10 probe and stress-validation reports."
        )
    )
    parser.add_argument("--probe-json", type=Path, default=DEFAULT_PROBE_JSON)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--probe-config-id", default=DEFAULT_PROBE_CONFIG_ID)
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_veto_only_candidate_selection_report(
        probe_report=_load_json(args.probe_json),
        validation_report=_load_json(args.validation_json),
        probe_path=args.probe_json,
        validation_path=args.validation_json,
        probe_config_id=str(args.probe_config_id or "").strip(),
        top_n=max(1, int(args.top_n)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_veto_only_candidate_selection_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_veto_only_candidate_selection_report(
    *,
    probe_report: Mapping[str, object],
    validation_report: Mapping[str, object],
    probe_path: Path | None = None,
    validation_path: Path | None = None,
    probe_config_id: str = DEFAULT_PROBE_CONFIG_ID,
    top_n: int = 12,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    probe_rows = [
        row
        for row in _mapping_rows(probe_report.get("rows"))
        if str(row.get("config_id") or "") == probe_config_id
    ]
    validation_rows = _mapping_rows(validation_report.get("rows"))
    validation_by_key = {_candidate_key(row): row for row in validation_rows}
    candidate_rows = []
    for probe_row in probe_rows:
        validation_row = validation_by_key.get(_candidate_key(probe_row))
        if validation_row is None:
            continue
        candidate_rows.append(
            _candidate_row(
                probe_row=probe_row,
                validation_row=validation_row,
            )
        )
    ranked_rows = sorted(candidate_rows, key=_candidate_rank_key)
    passing_rows = [row for row in ranked_rows if bool(row.get("passes_all_measured_lanes"))]
    return {
        "schema_version": 1,
        "status": "ok" if passing_rows else "review",
        "decision": (
            "veto_only_shared_candidate_found"
            if passing_rows
            else "veto_only_shared_candidate_not_found"
        ),
        "generated_at": generated_at,
        "probe": {
            "path": _repo_path(probe_path),
            "decision": str(probe_report.get("decision") or ""),
            "row_count": int(_as_mapping(probe_report.get("summary")).get("row_count") or 0),
            "target_pass_count": int(
                _as_mapping(probe_report.get("summary")).get("target_pass_count") or 0
            ),
            "selected_config_id": probe_config_id,
        },
        "validation": {
            "path": _repo_path(validation_path),
            "decision": str(validation_report.get("decision") or ""),
            "row_count": int(_as_mapping(validation_report.get("summary")).get("row_count") or 0),
            "target_pass_count": int(
                _as_mapping(validation_report.get("summary")).get("target_pass_count") or 0
            ),
        },
        "e2e_checks": {
            "probe_rows_considered": len(probe_rows),
            "validation_rows_considered": len(validation_rows),
            "matched_parameter_rows": len(candidate_rows),
            "passing_shared_rows": len(passing_rows),
        },
        "summary": {
            "row_count": len(candidate_rows),
            "passing_shared_count": len(passing_rows),
            "top_n": max(1, int(top_n)),
            "best_candidate": _public_candidate_row(ranked_rows[0] if ranked_rows else None),
            "recommendation": _recommendation(passing_rows=passing_rows),
        },
        "top_rows": [_public_candidate_row(row) for row in ranked_rows[: max(1, int(top_n))]],
        "passing_rows": [_public_candidate_row(row) for row in passing_rows[: max(1, int(top_n))]],
        "rows": [_public_candidate_row(row) for row in ranked_rows],
    }


def render_veto_only_candidate_selection_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Veto-Only Candidate Selection",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Probe: `{_as_mapping(report.get('probe')).get('path', '')}`",
        f"- Validation: `{_as_mapping(report.get('validation')).get('path', '')}`",
        f"- Matched candidate rows: `{summary.get('row_count', 0)}`",
        f"- Passing shared rows: `{summary.get('passing_shared_count', 0)}`",
        "",
        "## E2E Checks",
        "",
        _checks_table(report.get("e2e_checks")),
        "",
        "## Top Shared Candidates",
        "",
        _candidate_table(report.get("top_rows")),
        "",
        "## Passing Shared Candidates",
        "",
        _candidate_table(report.get("passing_rows")),
        "",
        "## Recommendation",
        "",
    ]
    for item in _sequence(summary.get("recommendation")):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _candidate_row(
    *,
    probe_row: Mapping[str, object],
    validation_row: Mapping[str, object],
) -> dict[str, object]:
    probe_pass = str(probe_row.get("target_status") or "") == "pass"
    validation_status = str(
        validation_row.get("strict_target_status") or validation_row.get("target_status") or ""
    )
    validation_pass = validation_status == "pass"
    return {
        "candidate_id": (
            f"{probe_row.get('config_id')}|{probe_row.get('phrase_mode')}|"
            f"lead={probe_row.get('shadow_lead_min')}|score={probe_row.get('shadow_score_min')}"
        ),
        "config_id": str(probe_row.get("config_id") or ""),
        "phrase_mode": str(probe_row.get("phrase_mode") or ""),
        "shadow_lead_min": probe_row.get("shadow_lead_min"),
        "shadow_score_min": probe_row.get("shadow_score_min"),
        "probe": _lane_metrics(probe_row),
        "validation": _lane_metrics(validation_row),
        "validation_source_breakdowns": list(
            _mapping_rows(validation_row.get("source_breakdowns"))
        ),
        "passes_all_measured_lanes": probe_pass and validation_pass,
        "combined_utility": round(
            _number(probe_row.get("utility_score")) + _number(validation_row.get("utility_score")),
            4,
        ),
        "minimum_positive_allow_rate": _minimum_optional(
            probe_row.get("positive_allow_rate"),
            validation_row.get("positive_allow_rate"),
        ),
        "minimum_negative_abstain_rate": _minimum_optional(
            probe_row.get("negative_abstain_rate"),
            validation_row.get("negative_abstain_rate"),
        ),
    }


def _lane_metrics(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "positive_allow_rate": row.get("positive_allow_rate"),
        "negative_abstain_rate": row.get("negative_abstain_rate"),
        "utility_score": row.get("utility_score"),
        "target_status": str(row.get("target_status") or ""),
    }


def _candidate_key(row: Mapping[str, object]) -> tuple[str, float, float]:
    return (
        str(row.get("phrase_mode") or ""),
        round(_number(row.get("shadow_lead_min")), 4),
        round(_number(row.get("shadow_score_min")), 4),
    )


def _candidate_rank_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        not bool(row.get("passes_all_measured_lanes")),
        -_number(row.get("combined_utility")),
        -_number(row.get("minimum_positive_allow_rate")),
        -_number(row.get("minimum_negative_abstain_rate")),
        str(row.get("candidate_id") or ""),
    )


def _public_candidate_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(row, Mapping):
        return None
    return {
        "candidate_id": str(row.get("candidate_id") or ""),
        "config_id": str(row.get("config_id") or ""),
        "phrase_mode": str(row.get("phrase_mode") or ""),
        "shadow_lead_min": row.get("shadow_lead_min"),
        "shadow_score_min": row.get("shadow_score_min"),
        "passes_all_measured_lanes": bool(row.get("passes_all_measured_lanes")),
        "combined_utility": row.get("combined_utility"),
        "minimum_positive_allow_rate": row.get("minimum_positive_allow_rate"),
        "minimum_negative_abstain_rate": row.get("minimum_negative_abstain_rate"),
        "probe": dict(_as_mapping(row.get("probe"))),
        "validation": dict(_as_mapping(row.get("validation"))),
        "validation_source_breakdowns": list(
            _mapping_rows(row.get("validation_source_breakdowns"))
        ),
    }


def _candidate_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No candidate rows._"
    lines = [
        "| Candidate | Shared pass | Combined utility | Min pos allow | Min neg abstain | v10 pos/neg | validation pos/neg |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        probe = _as_mapping(row.get("probe"))
        validation = _as_mapping(row.get("validation"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("candidate_id") or "")),
                    str(bool(row.get("passes_all_measured_lanes"))).lower(),
                    str(row.get("combined_utility", "")),
                    _format_percent(row.get("minimum_positive_allow_rate")),
                    _format_percent(row.get("minimum_negative_abstain_rate")),
                    (
                        f"{_format_percent(probe.get('positive_allow_rate'))} / "
                        f"{_format_percent(probe.get('negative_abstain_rate'))}"
                    ),
                    (
                        f"{_format_percent(validation.get('positive_allow_rate'))} / "
                        f"{_format_percent(validation.get('negative_abstain_rate'))}"
                    ),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _checks_table(value: object) -> str:
    mapping = _as_mapping(value)
    if not mapping:
        return "_No E2E checks._"
    lines = ["| Check | Value |", "| --- | --- |"]
    for key, raw_value in mapping.items():
        lines.append(f"| `{_escape_md(str(key))}` | `{_escape_md(str(raw_value))}` |")
    return "\n".join(lines)


def _recommendation(*, passing_rows: Sequence[Mapping[str, object]]) -> list[str]:
    if passing_rows:
        return [
            "A shared veto-only candidate passes both frozen v10 matrix traces and the configured validation report.",
            "Treat this as the leading runtime-candidate family, but keep it research-only until broader representative data is measured.",
            "Next validation should use an expanded representative or LLM-generated locked lane with the same candidate parameters.",
        ]
    return [
        "No shared veto-only candidate currently passes both measured inputs.",
        "Do not promote the v10 pass until a common parameter shape survives the configured validation report.",
    ]


def _minimum_optional(*values: object) -> float | None:
    materialized = [float(value) for value in values if value is not None]
    if not materialized:
        return None
    return round(min(materialized), 4)


def _number(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
