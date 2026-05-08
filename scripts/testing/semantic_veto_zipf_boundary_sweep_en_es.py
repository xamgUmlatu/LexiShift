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
    _mapping_rows,
    _repo_path,
    _safe_float,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"

DEFAULT_DIFFICULTY_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_difficulty_stratification_en_es_latest.json"
)
DEFAULT_SRS_ZIPF_BRIDGE_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_zipf_boundary_sweep_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_zipf_boundary_sweep_en_es_latest.md"
DEFAULT_LANE_ID = "sampling_stage1_representative_proxy"
CURRENT_SCHEME_ID = "current_5_4_3"
ZIPF_BANDS = (
    "zipf_5_plus_very_common",
    "zipf_4_to_5_common",
    "zipf_3_to_4_mid",
    "zipf_below_3_rare",
    "missing",
)
ERROR_OUTCOMES = frozenset({"positive_abstain", "negative_allow"})


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep Zipf band boundaries against latest observed semantic-veto rows and "
            "the full generated SRS source-family denominator. Diagnostic-only."
        )
    )
    parser.add_argument("--difficulty-json", type=Path, default=DEFAULT_DIFFICULTY_JSON)
    parser.add_argument("--srs-zipf-bridge-json", type=Path, default=DEFAULT_SRS_ZIPF_BRIDGE_JSON)
    parser.add_argument("--lane-id", default=DEFAULT_LANE_ID)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_zipf_boundary_sweep_report(
        difficulty_payload=_load_json(args.difficulty_json),
        bridge_payload=_load_json(args.srs_zipf_bridge_json),
        difficulty_path=args.difficulty_json,
        bridge_path=args.srs_zipf_bridge_json,
        lane_id=str(args.lane_id),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_zipf_boundary_sweep_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_zipf_boundary_sweep_report(
    *,
    difficulty_payload: Mapping[str, object],
    bridge_payload: Mapping[str, object],
    lane_id: str = DEFAULT_LANE_ID,
    difficulty_path: Path | None = None,
    bridge_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    case_rows = [
        row
        for row in _mapping_rows(difficulty_payload.get("case_traces"))
        if not lane_id or str(row.get("lane_id") or "") == lane_id
    ]
    full_pairs = _mapping_rows(bridge_payload.get("full_source_target_pairs"))
    issues: list[str] = []
    if not case_rows:
        issues.append("no_case_rows_for_lane")
    if not full_pairs:
        issues.append("srs_bridge_has_no_full_source_target_pairs")
    scheme_rows = [
        _score_scheme(
            scheme=scheme,
            case_rows=case_rows,
            full_pairs=full_pairs,
        )
        for scheme in _candidate_schemes()
    ]
    scheme_rows.sort(key=_scheme_sort_key)
    for rank, row in enumerate(scheme_rows, start=1):
        row["rank"] = rank
    current_row = next(
        (row for row in scheme_rows if row.get("scheme_id") == CURRENT_SCHEME_ID),
        {},
    )
    best_row = scheme_rows[0] if scheme_rows else {}
    return {
        "schema_version": 1,
        "pair": str(difficulty_payload.get("pair") or bridge_payload.get("pair") or "en-es"),
        "status": "review" if issues else "ok",
        "decision": "zipf_boundary_sweep_established"
        if not issues
        else "zipf_boundary_sweep_incomplete",
        "generated_at": generated_at,
        "inputs": {
            "difficulty_path": _repo_path(difficulty_path),
            "difficulty_decision": str(difficulty_payload.get("decision") or ""),
            "srs_zipf_bridge_path": _repo_path(bridge_path),
            "srs_zipf_bridge_decision": str(bridge_payload.get("decision") or ""),
            "lane_id": lane_id,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_generation": "none",
            "purpose": (
                "Check whether the current fixed Zipf bands are a defensible slicing "
                "choice for observed veto difficulty and full generated source-family "
                "coverage."
            ),
            "scored_signal": (
                "Outcome separation over latest case rows, penalized when a boundary "
                "scheme creates underfilled observed bands or lopsided full source-family "
                "coverage."
            ),
            "promotion_rule": (
                "This can suggest better reporting bands, but cannot by itself promote "
                "a runtime threshold or prove a causal difficulty curve."
            ),
        },
        "summary": {
            "issues": issues,
            "case_count": len(case_rows),
            "full_source_target_pair_count": len(full_pairs),
            "scheme_count": len(scheme_rows),
            "best_scheme_id": str(best_row.get("scheme_id") or ""),
            "best_objective": best_row.get("objective_score"),
            "current_scheme_rank": current_row.get("rank"),
            "current_scheme_objective": current_row.get("objective_score"),
            "current_minus_best_objective": _round4(
                _safe_float(current_row.get("objective_score"))
                - _safe_float(best_row.get("objective_score"))
            )
            if current_row and best_row
            else None,
        },
        "current_scheme": current_row,
        "top_schemes": scheme_rows[:20],
        "scheme_rows": scheme_rows,
        "limitations": [
            "observed_rows_are_still_underpowered_for_boundary_promotion",
            "objective_is_diagnostic_not_a_proof_of_optimal_bands",
            "full_source_family_distribution_uses_current_rulegen_output_only",
            "wordfreq_zipf_is_not_cefr_or_actual_browser_token_frequency",
        ],
        "next_steps": [
            "Use this report to decide whether future expansion should keep current bands or add alternate reporting bands.",
            "Rerun after representative mid and rare rows are filled.",
            "Treat current-band ties or small objective gaps as evidence that more rows matter more than threshold tuning.",
        ],
    }


def render_zipf_boundary_sweep_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Zipf Boundary Sweep",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Case rows: `{summary.get('case_count', 0)}`",
        f"- Full source-target pairs: `{summary.get('full_source_target_pair_count', 0)}`",
        f"- Schemes swept: `{summary.get('scheme_count', 0)}`",
        f"- Best scheme: `{summary.get('best_scheme_id', '')}`",
        f"- Current scheme rank: `{summary.get('current_scheme_rank', '')}`",
        "",
        "## Top Boundary Schemes",
        "",
        _scheme_table(report.get("top_schemes")),
        "",
        "## Current Scheme",
        "",
        _scheme_detail(_as_mapping(report.get("current_scheme"))),
        "",
        "## Interpretation",
        "",
        "- A high rank means the boundary scheme separates current observed outcomes while keeping the full source-family denominator usable.",
        "- A small gap from the best scheme means threshold tuning is probably less important than adding representative rows.",
        "- A large gap would justify adding alternate reporting bands before relying on current 5/4/3 bands for data budgeting.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _candidate_schemes() -> list[dict[str, object]]:
    candidates: dict[tuple[int, int, int], dict[str, object]] = {}
    for high in (48, 50, 52, 54, 56):
        for common in (36, 38, 40, 42, 44, 46):
            if common >= high:
                continue
            for mid in (24, 26, 28, 30, 32, 34, 36, 38, 40):
                if mid >= common:
                    continue
                key = (high, common, mid)
                candidates[key] = {
                    "scheme_id": _scheme_id(high, common, mid),
                    "very_common_min": high / 10,
                    "common_min": common / 10,
                    "mid_min": mid / 10,
                }
    candidates[(50, 40, 30)] = {
        "scheme_id": CURRENT_SCHEME_ID,
        "very_common_min": 5.0,
        "common_min": 4.0,
        "mid_min": 3.0,
    }
    return list(candidates.values())


def _score_scheme(
    *,
    scheme: Mapping[str, object],
    case_rows: Sequence[Mapping[str, object]],
    full_pairs: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    case_band_rows = _case_band_rows(scheme=scheme, case_rows=case_rows)
    full_band_rows = _full_pair_band_rows(scheme=scheme, full_pairs=full_pairs)
    eta = _failure_eta_squared(case_band_rows=case_band_rows)
    positive_range = _rate_range(
        rows=case_band_rows,
        numerator_key="positive_abstain_count",
        denominator_key="positive_case_count",
    )
    negative_range = _rate_range(
        rows=case_band_rows,
        numerator_key="negative_allow_count",
        denominator_key="negative_case_count",
    )
    non_missing = [row for row in case_band_rows if row["zipf_band"] != "missing"]
    underfilled_observed_band_count = sum(
        1 for row in non_missing if int(row.get("case_count") or 0) < 10
    )
    max_family_share = max(
        (_safe_float(row.get("family_share")) for row in full_band_rows),
        default=0.0,
    )
    objective = (
        eta
        + 0.25 * positive_range
        + 0.10 * negative_range
        - 0.04 * underfilled_observed_band_count
        - 0.05 * max(0.0, max_family_share - 0.70)
    )
    return {
        "scheme_id": str(scheme.get("scheme_id") or ""),
        "very_common_min": scheme.get("very_common_min"),
        "common_min": scheme.get("common_min"),
        "mid_min": scheme.get("mid_min"),
        "objective_score": _round4(objective),
        "failure_eta_squared": _round4(eta),
        "positive_abstain_rate_range": _round4(positive_range),
        "negative_allow_rate_range": _round4(negative_range),
        "underfilled_observed_band_count": underfilled_observed_band_count,
        "max_full_source_family_share": _round4(max_family_share),
        "case_band_rows": case_band_rows,
        "full_source_family_band_rows": full_band_rows,
    }


def _case_band_rows(
    *,
    scheme: Mapping[str, object],
    case_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in case_rows:
        band = _band_for_zipf(_safe_float(row.get("source_zipf_frequency_en")), scheme=scheme)
        grouped[band].append(row)
    output = []
    for band in ZIPF_BANDS:
        rows = grouped.get(band, [])
        outcomes = Counter(str(row.get("product_outcome") or "") for row in rows)
        positive_count = outcomes["positive_allow"] + outcomes["positive_abstain"]
        negative_count = outcomes["negative_abstain"] + outcomes["negative_allow"]
        failures = outcomes["positive_abstain"] + outcomes["negative_allow"]
        output.append(
            {
                "zipf_band": band,
                "case_count": len(rows),
                "positive_case_count": positive_count,
                "negative_case_count": negative_count,
                "positive_abstain_count": outcomes["positive_abstain"],
                "negative_allow_count": outcomes["negative_allow"],
                "failure_rate": _ratio(failures, len(rows)),
                "positive_abstain_rate": _ratio(outcomes["positive_abstain"], positive_count),
                "negative_allow_rate": _ratio(outcomes["negative_allow"], negative_count),
            }
        )
    return output


def _full_pair_band_rows(
    *,
    scheme: Mapping[str, object],
    full_pairs: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in full_pairs:
        band = _band_for_zipf(_safe_float(row.get("source_zipf_frequency_en")), scheme=scheme)
        grouped[band].append(row)
    total = len(full_pairs)
    output = []
    for band in ZIPF_BANDS:
        rows = grouped.get(band, [])
        sources = {str(row.get("source") or "") for row in rows if str(row.get("source") or "")}
        output.append(
            {
                "zipf_band": band,
                "family_count": len(rows),
                "family_share": _ratio(len(rows), total),
                "source_count": len(sources),
                "sample_families": [
                    {
                        "source": str(row.get("source") or ""),
                        "target": str(row.get("target") or ""),
                    }
                    for row in rows[:8]
                ],
            }
        )
    return output


def _failure_eta_squared(*, case_band_rows: Sequence[Mapping[str, object]]) -> float:
    total_cases = sum(int(row.get("case_count") or 0) for row in case_band_rows)
    total_failures = sum(
        int(row.get("positive_abstain_count") or 0) + int(row.get("negative_allow_count") or 0)
        for row in case_band_rows
    )
    if not total_cases:
        return 0.0
    overall_rate = total_failures / total_cases
    total_variance = total_cases * overall_rate * (1.0 - overall_rate)
    if total_variance <= 0:
        return 0.0
    between = 0.0
    for row in case_band_rows:
        case_count = int(row.get("case_count") or 0)
        if not case_count:
            continue
        band_failures = int(row.get("positive_abstain_count") or 0) + int(
            row.get("negative_allow_count") or 0
        )
        band_rate = band_failures / case_count
        between += case_count * (band_rate - overall_rate) ** 2
    return between / total_variance


def _rate_range(
    *,
    rows: Sequence[Mapping[str, object]],
    numerator_key: str,
    denominator_key: str,
) -> float:
    rates = [
        int(row.get(numerator_key) or 0) / int(row.get(denominator_key) or 0)
        for row in rows
        if int(row.get(denominator_key) or 0) > 0 and str(row.get("zipf_band") or "") != "missing"
    ]
    if len(rates) < 2:
        return 0.0
    return max(rates) - min(rates)


def _band_for_zipf(value: float, *, scheme: Mapping[str, object]) -> str:
    if value <= 0:
        return "missing"
    if value >= _safe_float(scheme.get("very_common_min")):
        return "zipf_5_plus_very_common"
    if value >= _safe_float(scheme.get("common_min")):
        return "zipf_4_to_5_common"
    if value >= _safe_float(scheme.get("mid_min")):
        return "zipf_3_to_4_mid"
    return "zipf_below_3_rare"


def _scheme_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, str]:
    return (
        -_safe_float(row.get("objective_score")),
        int(row.get("underfilled_observed_band_count") or 0),
        _safe_float(row.get("max_full_source_family_share")),
        str(row.get("scheme_id") or ""),
    )


def _scheme_id(high: int, common: int, mid: int) -> str:
    return f"zipf_{high / 10:.1f}_{common / 10:.1f}_{mid / 10:.1f}".replace(".", "p")


def _scheme_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No schemes scored._"
    lines = [
        "| Rank | Scheme | Thresholds | Objective | Eta2 | Pos Range | Neg Range | Underfilled | Max Family Share |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    str(int(row.get("rank") or 0)),
                    f"`{_escape_md(str(row.get('scheme_id') or ''))}`",
                    (
                        f"{float(row.get('very_common_min') or 0):.1f} / "
                        f"{float(row.get('common_min') or 0):.1f} / "
                        f"{float(row.get('mid_min') or 0):.1f}"
                    ),
                    f"{float(row.get('objective_score') or 0):.4f}",
                    f"{float(row.get('failure_eta_squared') or 0):.4f}",
                    f"{float(row.get('positive_abstain_rate_range') or 0):.4f}",
                    f"{float(row.get('negative_allow_rate_range') or 0):.4f}",
                    str(int(row.get("underfilled_observed_band_count") or 0)),
                    _format_percent(row.get("max_full_source_family_share")),
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _scheme_detail(row: Mapping[str, object]) -> str:
    if not row:
        return "_Current scheme was not scored._"
    lines = [
        f"- Scheme: `{_escape_md(str(row.get('scheme_id') or ''))}`",
        f"- Rank: `{row.get('rank', '')}`",
        f"- Objective: `{float(row.get('objective_score') or 0):.4f}`",
        "",
        "Observed case bands:",
        "",
        "| Band | Cases | Failure | Positive Abstain | Negative Allow |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for band_row in _mapping_rows(row.get("case_band_rows")):
        lines.append(
            f"| `{_escape_md(str(band_row.get('zipf_band') or ''))}` | "
            f"{int(band_row.get('case_count') or 0)} | "
            f"{_format_percent(band_row.get('failure_rate'))} | "
            f"{_format_percent(band_row.get('positive_abstain_rate'))} | "
            f"{_format_percent(band_row.get('negative_allow_rate'))} |"
        )
    lines.extend(
        [
            "",
            "Full generated source-family bands:",
            "",
            "| Band | Families | Share | Sources |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for band_row in _mapping_rows(row.get("full_source_family_band_rows")):
        lines.append(
            f"| `{_escape_md(str(band_row.get('zipf_band') or ''))}` | "
            f"{int(band_row.get('family_count') or 0)} | "
            f"{_format_percent(band_row.get('family_share'))} | "
            f"{int(band_row.get('source_count') or 0)} |"
        )
    return "\n".join(lines)


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return _round4(float(numerator) / float(denominator))


def _round4(value: float) -> float:
    return round(float(value), 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
