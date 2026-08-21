#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_probe_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_PROBE_JSON,
    build_report as build_formula_probe_report,
)
from srs_learner_difficulty_formula_sweep_en_es import (  # noqa: E402
    _candidate_by_id,
    _score_formula,
    generate_candidates,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_metrics,
    _summary_metrics,
)


PAIR = "en-es"
DEFAULT_TOP_N = 45000
DEFAULT_FIRST_REVIEW_COUNT = 500
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_es.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_es.json"
)
DEFAULT_FORMULA_SWEEP_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_formula_sweep_corrected_en_es_latest.json"
)
DEFAULT_MANUAL_CORRECTIONS_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_manual_corrections_en_es.json"
)
DEFAULT_RECOMMENDED_CANDIDATE_ID = "spalex_blend__lsbq_w105_c022__cog_m__lex_micro__no_guard"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_first500_review_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_first500_review_en_es_latest.md"
)
PRIMARY_STATE = "normal_vocab"
SUSPICIOUS_EARLY_LIMIT = 120


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply the sidecar en-es learner-difficulty manual correction seed and "
            "export a first-500 acceptance review pack."
        )
    )
    parser.add_argument("--formula-probe-json", type=Path, default=DEFAULT_FORMULA_PROBE_JSON)
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_FORMULA_SWEEP_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument(
        "--manual-corrections-json", type=Path, default=DEFAULT_MANUAL_CORRECTIONS_JSON
    )
    parser.add_argument("--candidate-id")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--first-review-count", type=int, default=DEFAULT_FIRST_REVIEW_COUNT)
    parser.add_argument("--force-rebuild-probe", action="store_true")
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
    report = build_report(
        formula_report=formula_report,
        sweep_payload=_load_optional_json(Path(args.formula_sweep_json).expanduser()),
        calibration_payload=_load_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_json(Path(args.holdout_json).expanduser()),
        corrections_payload=_load_json(Path(args.manual_corrections_json).expanduser()),
        candidate_id=args.candidate_id,
        first_review_count=max(1, int(args.first_review_count)),
    )
    json_out = Path(args.json_out).expanduser().resolve(strict=False)
    markdown_out = Path(args.markdown_out).expanduser().resolve(strict=False)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def load_or_build_formula_report(
    *,
    formula_probe_json: Path,
    top_n: int,
    force_rebuild: bool = False,
) -> dict[str, object]:
    if not force_rebuild and formula_probe_json.is_file():
        payload = _load_json(formula_probe_json)
        if payload.get("rows"):
            return payload
    return build_formula_probe_report(
        top_n=top_n,
        sample_limit=8,
        include_rows=True,
    )


def build_report(
    *,
    formula_report: Mapping[str, object],
    sweep_payload: Mapping[str, object] | None,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    corrections_payload: Mapping[str, object],
    candidate_id: str | None = None,
    first_review_count: int = DEFAULT_FIRST_REVIEW_COUNT,
    generated_at: str | None = None,
) -> dict[str, object]:
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
    raw_rows = sorted(
        scored_rows,
        key=lambda row: (
            _safe_float(row.get("model_score")) or 0.0,
            _rank(row),
            str(row.get("lemma") or ""),
        ),
    )
    corrected_rows = sorted(
        scored_rows,
        key=lambda row: (
            _safe_float(row.get("effective_score")) or 0.0,
            _rank(row),
            str(row.get("lemma") or ""),
        ),
    )
    first_rows = corrected_rows[:first_review_count]
    applications = _correction_applications(scored_rows, corrections_by_lemma)
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_es_learner_difficulty_first500_review_ready",
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "manual_labels_added": False,
        "method": {
            "purpose": (
                "Apply the sidecar en-es manual correction seed and inspect the "
                "first learner-facing 500 rows before production wiring."
            ),
            "candidate_id": selected_candidate_id,
            "manual_correction_status": corrections_payload.get("status"),
            "first_review_count": first_review_count,
            "sort_policy": "effective_score, then SPALEX rank, then lemma",
        },
        "inputs": {
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_probe_top_n": _as_mapping(formula_report.get("inputs")).get("top_n"),
            "formula_sweep_decision": _as_mapping(sweep_payload).get("decision"),
            "formula_sweep_generated_at": _as_mapping(sweep_payload).get("generated_at"),
            "calibration_id": calibration_payload.get("calibration_id"),
            "holdout_id": holdout_payload.get("holdout_id"),
            "correction_count": len(corrections_by_lemma),
        },
        "summary": {
            "candidate_rows_scanned": len(scored_rows),
            "first_review_count": len(first_rows),
            "correction_summary": _correction_summary(applications),
            "raw_metrics": _evaluate_labels(
                labels=[
                    *_as_sequence(calibration_payload.get("labels")),
                    *_as_sequence(holdout_payload.get("labels")),
                ],
                rows_by_lemma={str(row.get("lemma") or "").lower(): row for row in scored_rows},
                score_key="model_score",
            ),
            "corrected_metrics": _evaluate_labels(
                labels=[
                    *_as_sequence(calibration_payload.get("labels")),
                    *_as_sequence(holdout_payload.get("labels")),
                ],
                rows_by_lemma={str(row.get("lemma") or "").lower(): row for row in scored_rows},
                score_key="effective_score",
            ),
            "first500_flag_counts": _flag_counts(first_rows),
        },
        "correction_applications": applications,
        "first500_rows": [
            _compact_row(row, rank=index) for index, row in enumerate(first_rows, start=1)
        ],
        "raw_first80_rows": [
            _compact_row(row, rank=index) for index, row in enumerate(raw_rows[:80], start=1)
        ],
        "suspicious_first500_rows": [
            _compact_row(row, rank=index)
            for index, row in enumerate(first_rows, start=1)
            if _is_suspicious(row, rank=index)
        ],
        "limitations": [
            "This is still a sidecar review artifact; the correction seed is not wired into runtime ranking yet.",
            "Correction rows are seeded only from reviewed labels, not from subjective inspection of every first-500 row.",
            "Some grammar/function rows may still need product policy decisions about standalone SRS admission.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    summary = _as_mapping(report.get("summary"))
    correction_summary = _as_mapping(summary.get("correction_summary"))
    raw_metrics = _compact_metric(_as_mapping(summary.get("raw_metrics")))
    corrected_metrics = _compact_metric(_as_mapping(summary.get("corrected_metrics")))
    lines = [
        "# en-es First-500 Learner Difficulty Review",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Candidate: `{method.get('candidate_id')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Summary",
        "",
        f"- Rows scanned: `{summary.get('candidate_rows_scanned')}`",
        f"- First-review rows: `{summary.get('first_review_count')}`",
        f"- Correction rows: `{correction_summary.get('correction_rows')}`",
        f"- Active rows applied: `{correction_summary.get('active_count')}`",
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
        "First-500 flag counts:",
        "",
    ]
    for flag, count in sorted(_as_mapping(summary.get("first500_flag_counts")).items()):
        lines.append(f"- `{flag}`: `{count}`")
    lines.extend(["", "## Correction Applications", ""])
    lines.extend(_application_table(_as_sequence(report.get("correction_applications"))))
    lines.extend(["", "## Corrected First 120 Rows", ""])
    lines.extend(_row_table(_as_sequence(report.get("first500_rows"))[:120]))
    suspicious = _as_sequence(report.get("suspicious_first500_rows"))
    lines.extend(["", "## Suspicious First-500 Rows", ""])
    lines.extend(_row_table(suspicious[:120]))
    lines.append("")
    return "\n".join(lines)


def _scored_row(
    *,
    row: Mapping[str, object],
    candidate: object,
    labels_by_lemma: Mapping[str, Mapping[str, object]],
    corrections_by_lemma: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    lemma = str(row.get("lemma") or "").strip()
    key = lemma.lower()
    model_score = _score_formula(candidate, row)
    correction = corrections_by_lemma.get(key, {})
    effective_score = _apply_correction(model_score, correction)
    label = labels_by_lemma.get(key, {})
    flags = _review_flags(row=row, label=label, correction=correction)
    return {
        "lemma": lemma,
        "candidate_state": row.get("candidate_state"),
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "spalex_rank": row.get("spalex_rank"),
        "model_score": _round_float(model_score),
        "effective_score": _round_float(effective_score),
        "correction_delta": _round_float(effective_score - model_score),
        "correction": correction,
        "label": label,
        "translations": list(_as_sequence(row.get("translations")))[:5],
        "signals": _interesting_signals(_as_mapping(row.get("components"))),
        "dictionary": _as_mapping(row.get("dictionary")),
        "review_flags": flags,
    }


def _apply_correction(score: float, correction: Mapping[str, object]) -> float:
    if not _is_active_correction(correction):
        return _clamp01(score)
    override = _safe_float(correction.get("score_override"))
    floor = _safe_float(correction.get("min_score"))
    if override is not None:
        return _clamp01(override)
    if floor is not None:
        return _clamp01(max(score, floor))
    return _clamp01(score)


def _evaluate_labels(
    *,
    labels: Sequence[object],
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    score_key: str,
) -> dict[str, object]:
    selected = [
        _as_mapping(label)
        for label in labels
        if _safe_float(_as_mapping(label).get("expected_learner_difficulty")) is not None
        and str(_as_mapping(label).get("expected_candidate_state") or "") == PRIMARY_STATE
    ]
    expected_values = []
    observed_values = []
    expected_bands = []
    label_names = []
    expected_states = []
    observed_states = []
    missing = []
    for label in selected:
        lemma = str(label.get("lemma") or "")
        row = rows_by_lemma.get(lemma.lower())
        if row is None:
            missing.append(lemma)
        expected = _safe_float(label.get("expected_learner_difficulty"))
        expected_values.append(expected if expected is not None else float("nan"))
        observed_values.append(
            _safe_float(_as_mapping(row).get(score_key)) if row else float("nan")
        )
        expected_bands.append(str(label.get("expected_difficulty_band") or ""))
        label_names.append(lemma)
        expected_states.append(str(label.get("expected_candidate_state") or ""))
        observed_states.append(str(_as_mapping(row).get("candidate_state") or ""))
    metrics = _difficulty_metrics(
        expected_values=np.asarray(expected_values, dtype=np.float32),
        observed_values=np.asarray(observed_values, dtype=np.float32),
        expected_bands=expected_bands,
        labels=label_names,
        expected_candidate_states=np.asarray(expected_states, dtype="<U64"),
        observed_candidate_states=np.asarray(observed_states, dtype="<U64"),
    )
    return {
        "label_count": len(selected),
        "missing_count": len(missing),
        "missing": missing[:20],
        "scores": metrics["scores"],
        "metrics": _summary_metrics(metrics),
    }


def _corrections_by_lemma(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for raw in _as_sequence(payload.get("corrections")):
        row = _as_mapping(raw)
        lemma = str(row.get("lemma") or row.get("surface") or "").strip().lower()
        if not lemma:
            continue
        result[lemma] = row
    return result


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


def _correction_applications(
    rows: Sequence[Mapping[str, object]],
    corrections_by_lemma: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    rows_by_lemma = {str(row.get("lemma") or "").lower(): row for row in rows}
    applications = []
    for lemma, correction in sorted(corrections_by_lemma.items()):
        row = rows_by_lemma.get(lemma)
        model_score = _safe_float(_as_mapping(row).get("model_score"))
        effective_score = _safe_float(_as_mapping(row).get("effective_score"))
        active = _is_active_correction(correction)
        applications.append(
            {
                "lemma": lemma,
                "status": str(correction.get("status") or ""),
                "active": active,
                "found": row is not None,
                "model_score": _round_float(model_score) if model_score is not None else None,
                "effective_score": _round_float(effective_score)
                if effective_score is not None
                else None,
                "delta": _round_float((effective_score or 0.0) - (model_score or 0.0))
                if row is not None
                else None,
                "correction_types": list(_as_sequence(correction.get("correction_types"))),
                "admission_override": str(correction.get("admission_override") or ""),
                "rationale": str(correction.get("rationale") or ""),
            }
        )
    return applications


def _correction_summary(applications: Sequence[Mapping[str, object]]) -> dict[str, object]:
    active_count = sum(
        1 for row in applications if bool(row.get("active")) and bool(row.get("found"))
    )
    moved_count = sum(
        1 for row in applications if abs(_safe_float(row.get("delta")) or 0.0) > 0.000001
    )
    return {
        "correction_rows": len(applications),
        "active_count": active_count,
        "missing_count": sum(1 for row in applications if not bool(row.get("found"))),
        "moved_count": moved_count,
        "max_abs_delta": _round_float(
            max((abs(_safe_float(row.get("delta")) or 0.0) for row in applications), default=0.0)
        ),
    }


def _compact_metric(row: Mapping[str, object]) -> dict[str, object]:
    scores = _as_mapping(row.get("scores"))
    metrics = _as_mapping(row.get("metrics"))
    return {
        "balanced_score": scores.get("balanced_score"),
        "mae": metrics.get("mae"),
        "pairwise_accuracy": metrics.get("pairwise_accuracy"),
        "bucket_accuracy": metrics.get("bucket_accuracy"),
    }


def _compact_row(row: Mapping[str, object], *, rank: int) -> dict[str, object]:
    label = _as_mapping(row.get("label"))
    correction = _as_mapping(row.get("correction"))
    return {
        "rank": rank,
        "lemma": row.get("lemma"),
        "effective_score": row.get("effective_score"),
        "model_score": row.get("model_score"),
        "correction_delta": row.get("correction_delta"),
        "pos_bucket": row.get("pos_bucket"),
        "spalex_rank": row.get("spalex_rank"),
        "label_expected": label.get("expected_learner_difficulty"),
        "label_state": label.get("expected_candidate_state"),
        "correction_types": list(_as_sequence(correction.get("correction_types"))),
        "admission_override": correction.get("admission_override"),
        "translations": list(_as_sequence(row.get("translations")))[:3],
        "review_flags": list(_as_sequence(row.get("review_flags"))),
        "signals": row.get("signals"),
    }


def _review_flags(
    *,
    row: Mapping[str, object],
    label: Mapping[str, object],
    correction: Mapping[str, object],
) -> list[str]:
    flags: list[str] = []
    components = _as_mapping(row.get("components"))
    dictionary = _as_mapping(row.get("dictionary"))
    if str(row.get("pos_bucket") or "") == "other":
        flags.append("pos_other")
    if _safe_float(components.get("pos_function_risk")):
        flags.append("function_or_grammar")
    if not _as_sequence(row.get("translations")):
        flags.append("missing_translation")
    if _as_sequence(dictionary.get("marked_terms")):
        flags.append("marked_usage")
    expected = _safe_float(label.get("expected_learner_difficulty"))
    if expected is not None:
        flags.append("reviewed_label")
    if correction:
        flags.append("manual_correction")
        if "restricted_admission" in set(_as_sequence(correction.get("correction_types"))):
            flags.append("restricted_admission")
    return flags


def _flag_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for flag in _as_sequence(row.get("review_flags")):
            key = str(flag)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _is_suspicious(row: Mapping[str, object], *, rank: int) -> bool:
    flags = set(str(flag) for flag in _as_sequence(row.get("review_flags")))
    if rank <= SUSPICIOUS_EARLY_LIMIT and flags.intersection(
        {"pos_other", "function_or_grammar", "missing_translation", "marked_usage"}
    ):
        return True
    return bool(flags.intersection({"restricted_admission"}))


def _interesting_signals(components: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "wordfreq_zipf",
        "learner_source_known",
        "learner_source_count",
        "cognate_rescue",
        "false_friend_caution",
        "pos_function_risk",
        "pos_other_risk",
        "dict_marked_usage_risk",
        "gated_dict_marked_usage_risk",
        "weak_form_risk",
    )
    return {
        key: _round_float(value)
        for key in keys
        if (value := _safe_float(components.get(key))) is not None
    }


def _application_table(rows: Sequence[object]) -> list[str]:
    lines = [
        "| Lemma | Model | Effective | Delta | Types | Admission |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for raw in rows:
        row = _as_mapping(raw)
        lines.append(
            f"| `{_escape(row.get('lemma'))}` | {_fmt(row.get('model_score'))} | "
            f"{_fmt(row.get('effective_score'))} | {_fmt(row.get('delta'))} | "
            f"`{_escape(','.join(str(x) for x in _as_sequence(row.get('correction_types'))))}` | "
            f"`{_escape(row.get('admission_override'))}` |"
        )
    return lines


def _row_table(rows: Sequence[object]) -> list[str]:
    lines = [
        "| # | Lemma | Effective | Model | POS | Label | Flags | Translations |",
        "| ---: | --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for raw in rows:
        row = _as_mapping(raw)
        label = (
            f"{_fmt(row.get('label_expected'))} {row.get('label_state')}"
            if row.get("label_expected") is not None
            else "-"
        )
        lines.append(
            f"| {row.get('rank')} | `{_escape(row.get('lemma'))}` | "
            f"{_fmt(row.get('effective_score'))} | {_fmt(row.get('model_score'))} | "
            f"`{_escape(row.get('pos_bucket'))}` | {_escape(label)} | "
            f"`{_escape(','.join(str(x) for x in _as_sequence(row.get('review_flags'))))}` | "
            f"{_escape('; '.join(str(x) for x in _as_sequence(row.get('translations'))[:2]))} |"
        )
    return lines


def _is_active_correction(correction: Mapping[str, object]) -> bool:
    status = str(correction.get("status") or "active").strip().lower()
    return status in {"active", "accepted"}


def _selected_candidate_id(sweep_payload: Mapping[str, object] | None) -> str:
    summary = _as_mapping(_as_mapping(sweep_payload).get("summary"))
    for key in (
        "best_calibration_candidate",
        "best_stable_candidate",
        "best_holdout_guarded_candidate",
    ):
        candidate_id = str(_as_mapping(summary.get(key)).get("candidate_id") or "")
        if candidate_id:
            return candidate_id
    return DEFAULT_RECOMMENDED_CANDIDATE_ID


def _rank(row: Mapping[str, object]) -> float:
    rank = _safe_float(row.get("spalex_rank"))
    return rank if rank is not None else 999999999.0


def _load_optional_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    return _load_json(path)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_float(value: object, digits: int = 6) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    return round(numeric, digits)


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "-"
    return f"{numeric:.3f}"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
