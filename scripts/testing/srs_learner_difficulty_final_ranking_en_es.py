#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_first500_review_en_es import (  # noqa: E402
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_FORMULA_PROBE_JSON,
    DEFAULT_FORMULA_SWEEP_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_MANUAL_CORRECTIONS_JSON,
    DEFAULT_TOP_N,
    _application_table,
    _as_mapping,
    _as_sequence,
    _compact_metric,
    _compact_row,
    _correction_applications,
    _correction_summary,
    _corrections_by_lemma,
    _escape,
    _evaluate_labels,
    _flag_counts,
    _fmt,
    _interesting_signals,
    _is_suspicious,
    _load_json,
    _load_optional_json,
    _round_float,
    _row_table,
    _safe_float,
    _scored_row,
    _selected_candidate_id,
    _utc_now,
    load_or_build_formula_report,
)
from srs_learner_difficulty_formula_sweep_en_es import (  # noqa: E402
    _candidate_by_id,
    generate_candidates,
)


PAIR = "en-es"
DEFAULT_FIRST_REVIEW_COUNT = 500
DEFAULT_CSV_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_en_es_latest.csv"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_review_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_review_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export the deterministic full en-es learner-difficulty ranking for "
            "the selected formula candidate, with the manual correction layer applied."
        )
    )
    parser.add_argument("--formula-probe-json", type=Path, default=DEFAULT_FORMULA_PROBE_JSON)
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_FORMULA_SWEEP_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument(
        "--manual-corrections-json", type=Path, default=DEFAULT_MANUAL_CORRECTIONS_JSON
    )
    parser.add_argument(
        "--disable-manual-corrections",
        action="store_true",
        help="Export raw model scores without applying the manual correction layer.",
    )
    parser.add_argument("--candidate-id")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--first-review-count", type=int, default=DEFAULT_FIRST_REVIEW_COUNT)
    parser.add_argument("--force-rebuild-probe", action="store_true")
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    formula_report = load_or_build_formula_report(
        formula_probe_json=Path(args.formula_probe_json).expanduser(),
        top_n=max(1, int(args.top_n)),
        force_rebuild=bool(args.force_rebuild_probe),
    )
    corrections_payload = (
        {
            "status": "disabled",
            "corrections": [],
        }
        if args.disable_manual_corrections
        else _load_json(Path(args.manual_corrections_json).expanduser())
    )
    report, csv_rows = build_report(
        formula_report=formula_report,
        sweep_payload=_load_optional_json(Path(args.formula_sweep_json).expanduser()),
        calibration_payload=_load_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_json(Path(args.holdout_json).expanduser()),
        corrections_payload=corrections_payload,
        candidate_id=args.candidate_id,
        first_review_count=max(1, int(args.first_review_count)),
        csv_out=Path(args.csv_out).expanduser().resolve(strict=False),
    )
    csv_out = Path(args.csv_out).expanduser().resolve(strict=False)
    json_out = Path(args.json_out).expanduser().resolve(strict=False)
    markdown_out = Path(args.markdown_out).expanduser().resolve(strict=False)
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(csv_out, csv_rows)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote CSV ranking to {csv_out}")
    print(f"Wrote JSON review artifact to {json_out}")
    print(f"Wrote Markdown review artifact to {markdown_out}")
    return 0


def build_report(
    *,
    formula_report: Mapping[str, object],
    sweep_payload: Mapping[str, object] | None,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    corrections_payload: Mapping[str, object],
    csv_out: Path,
    candidate_id: str | None = None,
    first_review_count: int = DEFAULT_FIRST_REVIEW_COUNT,
    generated_at: str | None = None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    generated_at = generated_at or _utc_now()
    formula_rows = [_as_mapping(row) for row in _as_sequence(formula_report.get("rows"))]
    if not formula_rows:
        raise ValueError("formula report must contain rows; rebuild with include_rows=True")
    selected_candidate_id = candidate_id or _selected_candidate_id(sweep_payload)
    candidate = _candidate_by_id(generate_candidates(), selected_candidate_id)
    if candidate is None:
        raise ValueError(f"unknown formula candidate: {selected_candidate_id}")
    labels_by_lemma = _labels_by_lemma(
        calibration_payload=calibration_payload,
        holdout_payload=holdout_payload,
    )
    corrections_by_lemma = _corrections_by_lemma(corrections_payload)
    scored_rows = [
        _scored_row(
            row=row,
            candidate=candidate,
            labels_by_lemma=labels_by_lemma,
            corrections_by_lemma=corrections_by_lemma,
        )
        for row in formula_rows
    ]
    corrected_rows = sorted(
        scored_rows,
        key=lambda row: (
            _safe_float(row.get("effective_score")) or 0.0,
            _rank(row),
            str(row.get("lemma") or ""),
        ),
    )
    raw_rows = sorted(
        scored_rows,
        key=lambda row: (
            _safe_float(row.get("model_score")) or 0.0,
            _rank(row),
            str(row.get("lemma") or ""),
        ),
    )
    first_rows = corrected_rows[:first_review_count]
    csv_rows = [_csv_row(row=row, rank=rank) for rank, row in enumerate(corrected_rows, start=1)]
    applications = _correction_applications(scored_rows, corrections_by_lemma)
    all_labels = [
        *_as_sequence(calibration_payload.get("labels")),
        *_as_sequence(holdout_payload.get("labels")),
    ]
    report = {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_es_learner_difficulty_final_ranking_review_ready",
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "method": {
            "purpose": (
                "Deterministic full-ranking export for en-es learner-difficulty "
                "review. The full ranking is sorted by corrected score, then "
                "SPALEX rank, then lemma."
            ),
            "candidate_id": selected_candidate_id,
            "manual_corrections_applied": bool(corrections_by_lemma),
            "manual_correction_status": corrections_payload.get("status"),
            "first_review_count": first_review_count,
            "sort_policy": "effective_score, then SPALEX rank, then lemma",
        },
        "outputs": {
            "full_ranking_csv": _repo_path(csv_out),
        },
        "inputs": {
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_probe_top_n": _as_mapping(formula_report.get("inputs")).get("top_n"),
            "formula_sweep_decision": _as_mapping(sweep_payload).get("decision"),
            "formula_sweep_generated_at": _as_mapping(sweep_payload).get("generated_at"),
            "calibration_id": calibration_payload.get("calibration_id"),
            "holdout_id": holdout_payload.get("holdout_id"),
            "component_count": len(scored_rows),
            "correction_count": len(corrections_by_lemma),
        },
        "raw_metrics": _evaluate_labels(
            labels=all_labels,
            rows_by_lemma={str(row.get("lemma") or "").lower(): row for row in scored_rows},
            score_key="model_score",
        ),
        "corrected_metrics": _evaluate_labels(
            labels=all_labels,
            rows_by_lemma={str(row.get("lemma") or "").lower(): row for row in scored_rows},
            score_key="effective_score",
        ),
        "correction_summary": _correction_summary(applications),
        "band_counts": _band_counts(corrected_rows),
        "correction_applications": applications,
        "first_rows": [
            _compact_row(row, rank=index) for index, row in enumerate(first_rows, start=1)
        ],
        "first_row_flag_counts": _flag_counts(first_rows),
        "raw_first80_rows": [
            _compact_row(row, rank=index) for index, row in enumerate(raw_rows[:80], start=1)
        ],
        "suspicious_first_rows": [
            _compact_row(row, rank=index)
            for index, row in enumerate(first_rows, start=1)
            if _is_suspicious(row, rank=index)
        ],
        "limitations": [
            "This is still a review/export artifact; the CSV is not packaged into runtime yet.",
            "The manual set is intentionally small and seeded only from reviewed labels so far.",
            "Spanish inflection/lemma policy still needs product review before the correction layer is considered complete.",
        ],
    }
    return report, csv_rows


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    raw_metrics = _compact_metric(_as_mapping(report.get("raw_metrics")))
    corrected_metrics = _compact_metric(_as_mapping(report.get("corrected_metrics")))
    correction_summary = _as_mapping(report.get("correction_summary"))
    first_review_count = method.get("first_review_count") or DEFAULT_FIRST_REVIEW_COUNT
    lines = [
        "# en-es Learner Difficulty Final Ranking Review",
        "",
        "## Summary",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Candidate: `{_escape(method.get('candidate_id'))}`",
        f"- Full ranking CSV: `{_escape(_as_mapping(report.get('outputs')).get('full_ranking_csv'))}`",
        f"- Component count: `{_escape(_as_mapping(report.get('inputs')).get('component_count'))}`",
        f"- Manual corrections applied: `{method.get('manual_corrections_applied')}`",
        f"- Correction rows: `{correction_summary.get('correction_rows')}`",
        f"- Score-moving rows: `{correction_summary.get('moved_count')}`",
        "",
        "| Metrics | Balanced | MAE | Pairwise | Bucket |",
        "| --- | ---: | ---: | ---: | ---: |",
        (
            f"| Raw | {_fmt(raw_metrics.get('balanced_score'))} | "
            f"{_fmt(raw_metrics.get('mae'))} | {_fmt(raw_metrics.get('pairwise_accuracy'))} | "
            f"{_fmt(raw_metrics.get('bucket_accuracy'))} |"
        ),
        (
            f"| Corrected | {_fmt(corrected_metrics.get('balanced_score'))} | "
            f"{_fmt(corrected_metrics.get('mae'))} | {_fmt(corrected_metrics.get('pairwise_accuracy'))} | "
            f"{_fmt(corrected_metrics.get('bucket_accuracy'))} |"
        ),
        "",
        "The full ranking is sorted by corrected score, then SPALEX rank, then lemma.",
        "",
        "## Band Counts",
        "",
    ]
    lines.extend(_band_count_table(_as_sequence(report.get("band_counts"))))
    lines.extend(["", "## Manual Correction Summary", ""])
    lines.extend(_application_table(_as_sequence(report.get("correction_applications"))))
    lines.extend(["", f"## First {first_review_count} Review Rows", ""])
    lines.extend(_row_table(_as_sequence(report.get("first_rows"))))
    lines.extend(["", f"## Suspicious First {first_review_count} Rows", ""])
    lines.extend(_row_table(_as_sequence(report.get("suspicious_first_rows"))))
    lines.extend(["", f"## First {first_review_count} Flag Counts", ""])
    for flag, count in sorted(_as_mapping(report.get("first_row_flag_counts")).items()):
        lines.append(f"- `{flag}`: `{count}`")
    lines.append("")
    return "\n".join(lines)


def _csv_row(*, row: Mapping[str, object], rank: int) -> dict[str, object]:
    correction = _as_mapping(row.get("correction"))
    signals = _interesting_signals(_as_mapping(row.get("signals") or row.get("components")))
    if not signals:
        signals = _as_mapping(row.get("signals"))
    dictionary = _as_mapping(row.get("dictionary"))
    return {
        "rank": rank,
        "lemma": row.get("lemma"),
        "reading": "",
        "score": row.get("effective_score"),
        "model_score": row.get("model_score"),
        "correction_delta": row.get("correction_delta"),
        "band": _score_band(_safe_float(row.get("effective_score")) or 0.0),
        "spalex_rank": _round_float(row.get("spalex_rank")),
        "candidate_state": row.get("candidate_state"),
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "correction_types": ",".join(
            str(item) for item in _as_sequence(correction.get("correction_types"))
        ),
        "display_form": str(correction.get("display_form") or ""),
        "admission_override": str(correction.get("admission_override") or ""),
        "topic_stretch_allowed": _topic_stretch_allowed(correction),
        "correction_status": str(correction.get("status") or ""),
        "correction_rationale": str(correction.get("rationale") or ""),
        "manual_correction_active": "yes" if _is_active_correction(correction) else "",
        "review_flags": ",".join(str(item) for item in _as_sequence(row.get("review_flags"))),
        "translations": "; ".join(str(item) for item in _as_sequence(row.get("translations"))[:3]),
        "wordfreq_zipf": signals.get("wordfreq_zipf"),
        "learner_source_known": signals.get("learner_source_known"),
        "learner_source_count": signals.get("learner_source_count"),
        "cognate_rescue": signals.get("cognate_rescue"),
        "false_friend_caution": signals.get("false_friend_caution"),
        "pos_function_risk": signals.get("pos_function_risk"),
        "pos_other_risk": signals.get("pos_other_risk"),
        "dict_marked_usage_risk": signals.get("dict_marked_usage_risk"),
        "weak_form_risk": signals.get("weak_form_risk"),
        "dictionary_sense_count": dictionary.get("sense_count"),
        "dictionary_entry_count": dictionary.get("entry_count"),
        "dictionary_marked_terms": ",".join(
            str(item) for item in _as_sequence(dictionary.get("marked_terms"))
        ),
    }


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fieldnames = [
        "rank",
        "lemma",
        "reading",
        "score",
        "model_score",
        "correction_delta",
        "band",
        "spalex_rank",
        "candidate_state",
        "pos",
        "pos_bucket",
        "correction_types",
        "display_form",
        "admission_override",
        "topic_stretch_allowed",
        "correction_status",
        "correction_rationale",
        "manual_correction_active",
        "review_flags",
        "translations",
        "wordfreq_zipf",
        "learner_source_known",
        "learner_source_count",
        "cognate_rescue",
        "false_friend_caution",
        "pos_function_risk",
        "pos_other_risk",
        "dict_marked_usage_risk",
        "weak_form_risk",
        "dictionary_sense_count",
        "dictionary_entry_count",
        "dictionary_marked_terms",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _labels_by_lemma(
    *,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for payload in (calibration_payload, holdout_payload):
        for raw in _as_sequence(payload.get("labels")):
            row = _as_mapping(raw)
            lemma = str(row.get("lemma") or "").strip().lower()
            if lemma:
                result[lemma] = row
    return result


def _band_counts(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    counts: list[dict[str, object]] = []
    for index in range(20):
        start = index / 20.0
        end = (index + 1) / 20.0
        label = _band_label(start, end)
        band_count = sum(
            1
            for row in rows
            if str(
                row.get("effective_score_band")
                or _score_band(_safe_float(row.get("effective_score")) or 0.0)
            )
            == label
        )
        cumulative = sum(
            1
            for row in rows
            if (_safe_float(row.get("effective_score")) or 0.0) < end
            or (end >= 1.0 and (_safe_float(row.get("effective_score")) or 0.0) <= end)
        )
        counts.append({"band": label, "count": band_count, "cumulative_count": cumulative})
    return counts


def _band_count_table(rows: Sequence[object]) -> list[str]:
    lines = [
        "| Band | Count | Cumulative |",
        "| --- | ---: | ---: |",
    ]
    for raw in rows:
        row = _as_mapping(raw)
        lines.append(
            f"| `{_escape(row.get('band'))}` | {row.get('count') or 0} | "
            f"{row.get('cumulative_count') or 0} |"
        )
    return lines


def _topic_stretch_allowed(correction: Mapping[str, object]) -> str:
    if not correction:
        return ""
    correction_types = {str(item) for item in _as_sequence(correction.get("correction_types"))}
    admission = str(correction.get("admission_override") or "").strip()
    if "exclude_standalone_srs" in correction_types:
        return "False"
    if "restricted_admission" in correction_types:
        return "False"
    if admission and admission != "normal_vocab":
        return "False"
    return "True"


def _is_active_correction(correction: Mapping[str, object]) -> bool:
    status = str(correction.get("status") or "active").strip().lower()
    return bool(correction) and status in {"active", "accepted"}


def _rank(row: Mapping[str, object]) -> float:
    rank = _safe_float(row.get("spalex_rank"))
    return rank if rank is not None else 999999999.0


def _score_band(score: float) -> str:
    bounded = min(max(score, 0.0), 1.0)
    index = min(19, int(bounded * 20.0))
    return _band_label(index / 20.0, (index + 1) / 20.0)


def _band_label(start: float, end: float) -> str:
    return f"{start:.2f}-{end:.2f}"


def _repo_path(path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
