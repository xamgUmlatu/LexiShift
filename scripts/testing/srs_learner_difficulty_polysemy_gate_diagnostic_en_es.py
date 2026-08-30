#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Callable, Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_probe_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_PROBE_JSON,
)
from srs_learner_difficulty_formula_sweep_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_SWEEP_JSON,
    _candidate_by_id,
    _score_formula,
    generate_candidates,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    PAIRWISE_MIN_EXPECTED_GAP,
    PAIRWISE_TIE_TOLERANCE,
    SCORE_KEYS,
)
from srs_learner_difficulty_polysemy_sweep_en_es import (  # noqa: E402
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_JSON_OUT as DEFAULT_POLYSEMY_SWEEP_JSON,
    FOCUS_MIN_ERROR,
    PAIR,
    PRIMARY_STATE,
    PROTECTED_ERROR_MAX,
    PROTECTED_REGRESSION_DELTA,
    PolysemyProfile,
    _as_mapping,
    _as_sequence,
    _compact_record,
    _focus_sort_key,
    _generate_profiles,
    _joined_labeled_rows,
    _load_json,
    _profile_record,
    _profile_scorer,
    _record_for_scorer,
    _round_float,
    _safe_float,
    _safe_sort_key,
    _selected_candidate_id,
    _stable_sort_key,
    load_or_build_formula_report,
)


DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_polysemy_gate_diagnostic_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_polysemy_gate_diagnostic_en_es_latest.md"
)
ROW_SAMPLE_LIMIT = 12
PAIR_SAMPLE_LIMIT = 12
GROUP_SAMPLE_LIMIT = 10


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnose en-es polysemy-gate tradeoffs by comparing baseline, ungated, "
            "stable, safe, and zero-protected profiles row by row."
        )
    )
    parser.add_argument("--formula-probe-json", type=Path, default=DEFAULT_FORMULA_PROBE_JSON)
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_FORMULA_SWEEP_JSON)
    parser.add_argument("--polysemy-sweep-json", type=Path, default=DEFAULT_POLYSEMY_SWEEP_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--candidate-id")
    parser.add_argument("--top-n", type=int, default=45000)
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
        formula_sweep_payload=_load_optional_json(Path(args.formula_sweep_json).expanduser()),
        polysemy_sweep_payload=_load_optional_json(Path(args.polysemy_sweep_json).expanduser()),
        calibration_payload=_load_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_json(Path(args.holdout_json).expanduser()),
        candidate_id=args.candidate_id,
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


def build_report(
    *,
    formula_report: Mapping[str, object],
    formula_sweep_payload: Mapping[str, object] | None,
    polysemy_sweep_payload: Mapping[str, object] | None,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    candidate_id: str | None = None,
    profiles: Sequence[PolysemyProfile] | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    formula_rows = [_as_mapping(row) for row in _as_sequence(formula_report.get("rows"))]
    if not formula_rows:
        raise ValueError("formula report must contain rows; rebuild with include_rows=True")
    rows_by_lemma = {str(row.get("lemma") or "").lower(): row for row in formula_rows}
    selected_candidate_id = (
        candidate_id
        or str(
            _as_mapping(_as_mapping(polysemy_sweep_payload).get("method")).get("base_candidate_id")
            or ""
        )
        or _selected_candidate_id(formula_sweep_payload)
    )
    candidate = _candidate_by_id(generate_candidates(), selected_candidate_id)
    if candidate is None:
        raise ValueError(f"unknown formula candidate: {selected_candidate_id}")
    base_scores_by_lemma = {
        str(row.get("lemma") or "").lower(): _score_formula(candidate, row) for row in formula_rows
    }
    calibration_labels = [
        _as_mapping(row) for row in _as_sequence(calibration_payload.get("labels"))
    ]
    holdout_labels = [_as_mapping(row) for row in _as_sequence(holdout_payload.get("labels"))]
    labeled_rows = _joined_labeled_rows(
        rows_by_lemma=rows_by_lemma,
        base_scores_by_lemma=base_scores_by_lemma,
        calibration_labels=calibration_labels,
        holdout_labels=holdout_labels,
    )
    baseline = _record_for_scorer(
        record_id="baseline",
        scorer=lambda row: base_scores_by_lemma.get(str(row.get("lemma") or "").lower(), 0.0),
        rows_by_lemma=rows_by_lemma,
        calibration_labels=calibration_labels,
        holdout_labels=holdout_labels,
        labeled_rows=labeled_rows,
    )
    records = [
        _profile_record(
            profile=profile,
            rows_by_lemma=rows_by_lemma,
            base_scores_by_lemma=base_scores_by_lemma,
            calibration_labels=calibration_labels,
            holdout_labels=holdout_labels,
            labeled_rows=labeled_rows,
        )
        for profile in (list(profiles) if profiles is not None else list(_generate_profiles()))
    ]
    selected_records = _selected_records(records)
    diagnostics = [
        _profile_diagnostic(
            label=label,
            record=record,
            baseline=baseline,
            base_scores_by_lemma=base_scores_by_lemma,
            labeled_rows=labeled_rows,
        )
        for label, record in selected_records
    ]
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_es_learner_difficulty_polysemy_gate_diagnostic_ready",
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "manual_labels_added": False,
        "method": {
            "purpose": (
                "Diagnose why gated polysemy profiles improve targeted content rows "
                "while sometimes losing holdout score against less guarded profiles."
            ),
            "base_candidate_id": selected_candidate_id,
            "profile_count": len(records),
            "compared_profile_count": len(diagnostics),
            "protected_error_max": PROTECTED_ERROR_MAX,
            "protected_regression_delta": PROTECTED_REGRESSION_DELTA,
            "focus_min_error": FOCUS_MIN_ERROR,
            "pairwise_min_expected_gap": PAIRWISE_MIN_EXPECTED_GAP,
            "pairwise_tie_tolerance": PAIRWISE_TIE_TOLERANCE,
        },
        "inputs": {
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_sweep_decision": _as_mapping(formula_sweep_payload).get("decision"),
            "formula_sweep_generated_at": _as_mapping(formula_sweep_payload).get("generated_at"),
            "polysemy_sweep_decision": _as_mapping(polysemy_sweep_payload).get("decision"),
            "polysemy_sweep_generated_at": _as_mapping(polysemy_sweep_payload).get("generated_at"),
            "calibration_id": calibration_payload.get("calibration_id"),
            "holdout_id": holdout_payload.get("holdout_id"),
            "calibration_count": len(calibration_labels),
            "holdout_count": len(holdout_labels),
            "joined_labeled_rows": len(labeled_rows),
        },
        "summary": {
            "baseline": baseline,
            "compared_profiles": [
                {"comparison_label": label, **_compact_record(record)}
                for label, record in selected_records
            ],
        },
        "diagnostics": diagnostics,
        "interpretation": _interpret(diagnostics),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    lines = [
        "# en-es Polysemy Gate Diagnostic",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        f"- Base candidate: `{method.get('base_candidate_id')}`",
        f"- Profiles evaluated: `{method.get('profile_count')}`",
        "",
        "## Summary",
        "",
        "| Comparison | Profile | Pos gate | Cal balanced | Holdout balanced | Focus improvement | Protected regressions |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    baseline = _as_mapping(_as_mapping(report.get("summary")).get("baseline"))
    lines.append(
        "| Baseline | `baseline` | - | "
        f"{_fmt(_score_at(baseline, 'calibration_primary', 'balanced_score'))} | "
        f"{_fmt(_score_at(baseline, 'holdout_primary', 'balanced_score'))} | "
        f"{_fmt(baseline.get('focus_improvement'))} | "
        f"{baseline.get('protected_regression_count')} |"
    )
    for raw in _as_sequence(_as_mapping(report.get("summary")).get("compared_profiles")):
        row = _as_mapping(raw)
        profile = _as_mapping(row.get("profile"))
        lines.append(
            f"| {_escape(row.get('comparison_label'))} | `{row.get('profile_id')}` | "
            f"`{profile.get('pos_gate')}` | "
            f"{_fmt(row.get('calibration_balanced'))} | "
            f"{_fmt(row.get('holdout_balanced'))} | "
            f"{_fmt(row.get('focus_improvement'))} | "
            f"{row.get('protected_regression_count')} |"
        )
    lines.extend(["", "## Interpretation", ""])
    for item in _as_sequence(report.get("interpretation")):
        lines.append(f"- {item}")
    for raw in _as_sequence(report.get("diagnostics")):
        diagnostic = _as_mapping(raw)
        profile = _as_mapping(diagnostic.get("profile"))
        lines.extend(
            [
                "",
                f"## {diagnostic.get('comparison_label')}",
                "",
                f"- Profile: `{diagnostic.get('profile_id')}`",
                f"- Pos gate: `{profile.get('pos_gate')}`",
                f"- Params: `{_params(profile)}`",
            ]
        )
        for split in ("calibration", "holdout"):
            split_row = _as_mapping(diagnostic.get(split))
            lines.extend(
                [
                    "",
                    f"### {split.title()} Metric Deltas",
                    "",
                    "| Metric | Baseline | Profile | Delta |",
                    "| --- | ---: | ---: | ---: |",
                ]
            )
            for metric in (
                "balanced_score",
                "numeric_mae_score",
                "bucket_accuracy_score",
                "pairwise_order_score",
                "rank_correlation_score",
                "mae",
                "pairwise_wrong_count",
                "bucket_mismatch_count",
            ):
                delta = _as_mapping(split_row.get("metric_deltas")).get(metric)
                if not delta:
                    continue
                delta_row = _as_mapping(delta)
                lines.append(
                    f"| `{metric}` | {_fmt(delta_row.get('baseline'))} | "
                    f"{_fmt(delta_row.get('profile'))} | {_fmt(delta_row.get('delta'))} |"
                )
            lines.extend(["", "Largest improvements:", ""])
            lines.extend(_row_delta_table(_as_sequence(split_row.get("largest_improvements"))))
            lines.extend(["", "Largest regressions:", ""])
            lines.extend(_row_delta_table(_as_sequence(split_row.get("largest_regressions"))))
            pairwise = _as_mapping(split_row.get("pairwise_changes"))
            lines.extend(
                [
                    "",
                    "Pairwise changes:",
                    "",
                    f"- Fixed wrong/tied pairs: `{pairwise.get('fixed_count')}`",
                    f"- Newly wrong pairs: `{pairwise.get('new_wrong_count')}`",
                    f"- Newly tied pairs: `{pairwise.get('new_tie_count')}`",
                ]
            )
            new_wrong = _as_sequence(pairwise.get("new_wrong_pairs"))
            if new_wrong:
                lines.extend(["", "New wrong pair examples:", ""])
                lines.extend(_pair_table(new_wrong))
            group_rows = _as_sequence(split_row.get("group_summaries"))
            if group_rows:
                lines.extend(["", "Most affected groups:", ""])
                lines.extend(_group_table(group_rows))
    lines.append("")
    return "\n".join(lines)


def _selected_records(
    records: Sequence[Mapping[str, object]],
) -> list[tuple[str, Mapping[str, object]]]:
    nonempty = [row for row in records if row.get("profile_id")]
    selections: list[tuple[str, Mapping[str, object]]] = []
    selections.append(
        ("best_stable_overall", sorted(nonempty, key=_stable_sort_key, reverse=True)[0])
    )
    ungated = [
        row
        for row in nonempty
        if str(_as_mapping(row.get("profile")).get("pos_gate") or "none") == "none"
    ]
    if ungated:
        selections.append(
            ("best_stable_ungated", sorted(ungated, key=_stable_sort_key, reverse=True)[0])
        )
    zero_protected = [
        row for row in nonempty if int(row.get("protected_regression_count") or 0) == 0
    ]
    if zero_protected:
        selections.append(
            ("best_zero_protected", sorted(zero_protected, key=_focus_sort_key, reverse=True)[0])
        )
    selections.append(("best_safe", sorted(nonempty, key=_safe_sort_key, reverse=True)[0]))
    return _unique_labeled_records(selections)


def _profile_diagnostic(
    *,
    label: str,
    record: Mapping[str, object],
    baseline: Mapping[str, object],
    base_scores_by_lemma: Mapping[str, float],
    labeled_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    scorer = _profile_scorer(
        profile=_profile_from_record_payload(record),
        base_scores_by_lemma=base_scores_by_lemma,
    )
    return {
        "comparison_label": label,
        "profile_id": record.get("profile_id"),
        "profile": record.get("profile"),
        "calibration": _split_diagnostic(
            split="calibration",
            record=record,
            baseline=baseline,
            labeled_rows=labeled_rows,
            scorer=scorer,
        ),
        "holdout": _split_diagnostic(
            split="holdout",
            record=record,
            baseline=baseline,
            labeled_rows=labeled_rows,
            scorer=scorer,
        ),
    }


def _split_diagnostic(
    *,
    split: str,
    record: Mapping[str, object],
    baseline: Mapping[str, object],
    labeled_rows: Sequence[Mapping[str, object]],
    scorer: Callable[[Mapping[str, object]], float],
) -> dict[str, object]:
    rows = _row_deltas(split=split, labeled_rows=labeled_rows, scorer=scorer)
    changed = [row for row in rows if abs(_safe_float(row.get("delta")) or 0.0) > 0.000001]
    improvements = [
        row for row in changed if (_safe_float(row.get("error_delta")) or 0.0) < -0.000001
    ]
    regressions = [
        row for row in changed if (_safe_float(row.get("error_delta")) or 0.0) > 0.000001
    ]
    return {
        "metric_deltas": _metric_deltas(
            baseline=_as_mapping(baseline.get(f"{split}_primary")),
            profile=_as_mapping(record.get(f"{split}_primary")),
        ),
        "changed_count": len(changed),
        "changed_error_delta_sum": _round_float(
            sum(_safe_float(row.get("error_delta")) or 0.0 for row in changed)
        ),
        "largest_improvements": sorted(
            improvements,
            key=lambda row: _safe_float(row.get("error_delta")) or 0.0,
        )[:ROW_SAMPLE_LIMIT],
        "largest_regressions": sorted(
            regressions,
            key=lambda row: _safe_float(row.get("error_delta")) or 0.0,
            reverse=True,
        )[:ROW_SAMPLE_LIMIT],
        "largest_score_moves": sorted(
            changed,
            key=lambda row: abs(_safe_float(row.get("delta")) or 0.0),
            reverse=True,
        )[:ROW_SAMPLE_LIMIT],
        "pairwise_changes": _pairwise_changes(rows),
        "group_summaries": _group_summaries(changed),
    }


def _row_deltas(
    *,
    split: str,
    labeled_rows: Sequence[Mapping[str, object]],
    scorer: Callable[[Mapping[str, object]], float],
) -> list[dict[str, object]]:
    result = []
    for labeled in labeled_rows:
        if labeled.get("split") != split:
            continue
        label = _as_mapping(labeled.get("label"))
        if str(label.get("expected_candidate_state") or "") != PRIMARY_STATE:
            continue
        source = _as_mapping(labeled.get("row"))
        expected = _safe_float(labeled.get("expected"))
        before = _safe_float(labeled.get("base_score"))
        if expected is None or before is None:
            continue
        after = scorer(source)
        components = _as_mapping(source.get("components"))
        dictionary = _as_mapping(source.get("dictionary"))
        result.append(
            {
                "lemma": source.get("lemma"),
                "expected": _round_float(expected),
                "before": _round_float(before),
                "after": _round_float(after),
                "delta": _round_float(after - before),
                "base_error": _round_float(abs(before - expected)),
                "after_error": _round_float(abs(after - expected)),
                "error_delta": _round_float(abs(after - expected) - abs(before - expected)),
                "pos_bucket": source.get("pos_bucket"),
                "sense_count": dictionary.get("sense_count"),
                "entry_count": dictionary.get("entry_count"),
                "wordfreq_zipf": components.get("wordfreq_zipf"),
                "learner_source_count": components.get("learner_source_count"),
                "is_focus_row": bool(labeled.get("is_focus_row")),
                "is_protected_row": bool(labeled.get("is_protected_row")),
            }
        )
    return result


def _metric_deltas(
    *,
    baseline: Mapping[str, object],
    profile: Mapping[str, object],
) -> dict[str, object]:
    base_scores = _as_mapping(baseline.get("scores"))
    profile_scores = _as_mapping(profile.get("scores"))
    base_metrics = _as_mapping(baseline.get("metrics"))
    profile_metrics = _as_mapping(profile.get("metrics"))
    result = {}
    for key in SCORE_KEYS:
        result[key] = _delta_record(base_scores.get(key), profile_scores.get(key))
    for key in (
        "mae",
        "pairwise_accuracy",
        "pairwise_wrong_count",
        "bucket_accuracy",
        "bucket_mismatch_count",
        "spearman",
    ):
        result[key] = _delta_record(base_metrics.get(key), profile_metrics.get(key))
    return result


def _pairwise_changes(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    fixed = []
    new_wrong = []
    new_tie = []
    for left_index, left in enumerate(rows):
        for right in rows[left_index + 1 :]:
            left_expected = _safe_float(left.get("expected"))
            right_expected = _safe_float(right.get("expected"))
            if left_expected is None or right_expected is None:
                continue
            if abs(right_expected - left_expected) < PAIRWISE_MIN_EXPECTED_GAP:
                continue
            easier, harder = (left, right) if left_expected < right_expected else (right, left)
            base_gap = (_safe_float(harder.get("before")) or 0.0) - (
                _safe_float(easier.get("before")) or 0.0
            )
            after_gap = (_safe_float(harder.get("after")) or 0.0) - (
                _safe_float(easier.get("after")) or 0.0
            )
            base_status = _pair_status(base_gap)
            after_status = _pair_status(after_gap)
            if base_status == after_status:
                continue
            pair = {
                "expected_easier": easier.get("lemma"),
                "expected_harder": harder.get("lemma"),
                "expected_gap": _round_float(
                    (_safe_float(harder.get("expected")) or 0.0)
                    - (_safe_float(easier.get("expected")) or 0.0)
                ),
                "baseline_gap": _round_float(base_gap),
                "profile_gap": _round_float(after_gap),
                "baseline_status": base_status,
                "profile_status": after_status,
            }
            if base_status != "correct" and after_status == "correct":
                fixed.append(pair)
            elif base_status == "correct" and after_status == "wrong":
                new_wrong.append(pair)
            elif base_status == "correct" and after_status == "tie":
                new_tie.append(pair)
    return {
        "fixed_count": len(fixed),
        "new_wrong_count": len(new_wrong),
        "new_tie_count": len(new_tie),
        "fixed_pairs": sorted(
            fixed, key=lambda row: _safe_float(row.get("profile_gap")) or 0.0, reverse=True
        )[:PAIR_SAMPLE_LIMIT],
        "new_wrong_pairs": sorted(
            new_wrong, key=lambda row: _safe_float(row.get("profile_gap")) or 0.0
        )[:PAIR_SAMPLE_LIMIT],
        "new_tie_pairs": sorted(
            new_tie, key=lambda row: _safe_float(row.get("expected_gap")) or 0.0, reverse=True
        )[:PAIR_SAMPLE_LIMIT],
    }


def _group_summaries(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str, str], list[Mapping[str, object]]] = {}
    for row in rows:
        key = (
            str(row.get("pos_bucket") or "unknown"),
            _base_band(_safe_float(row.get("before")) or 0.0),
            _sense_band(_safe_float(row.get("sense_count")) or 0.0),
            _source_band(_safe_float(row.get("learner_source_count"))),
        )
        groups.setdefault(key, []).append(row)
    summaries = []
    for (pos_bucket, base_band, sense_band, source_band), grouped in groups.items():
        error_deltas = [_safe_float(row.get("error_delta")) or 0.0 for row in grouped]
        deltas = [_safe_float(row.get("delta")) or 0.0 for row in grouped]
        summaries.append(
            {
                "pos_bucket": pos_bucket,
                "base_band": base_band,
                "sense_band": sense_band,
                "source_band": source_band,
                "count": len(grouped),
                "mean_delta": _round_float(float(np.mean(deltas))),
                "mean_error_delta": _round_float(float(np.mean(error_deltas))),
                "improvement_count": sum(1 for value in error_deltas if value < -0.000001),
                "regression_count": sum(1 for value in error_deltas if value > 0.000001),
            }
        )
    return sorted(
        summaries,
        key=lambda row: (
            abs(_safe_float(row.get("mean_error_delta")) or 0.0)
            * max(1, int(row.get("count") or 0))
        ),
        reverse=True,
    )[:GROUP_SAMPLE_LIMIT]


def _interpret(diagnostics: Sequence[Mapping[str, object]]) -> list[str]:
    items = []
    for diagnostic in diagnostics:
        label = str(diagnostic.get("comparison_label") or "")
        holdout = _as_mapping(diagnostic.get("holdout"))
        metric_deltas = _as_mapping(holdout.get("metric_deltas"))
        balanced = _as_mapping(metric_deltas.get("balanced_score"))
        pairwise = _as_mapping(metric_deltas.get("pairwise_order_score"))
        bucket = _as_mapping(metric_deltas.get("bucket_accuracy_score"))
        changed = int(holdout.get("changed_count") or 0)
        items.append(
            f"{label}: holdout balanced delta {_fmt(balanced.get('delta'))}, "
            f"pairwise delta {_fmt(pairwise.get('delta'))}, "
            f"bucket delta {_fmt(bucket.get('delta'))}, changed primary rows {changed}."
        )
    return items


def _profile_from_record_payload(record: Mapping[str, object]) -> PolysemyProfile:
    profile = _as_mapping(record.get("profile"))
    return PolysemyProfile(
        profile_id=str(record.get("profile_id") or ""),
        sense_ceiling=float(profile.get("sense_ceiling") or 10.0),
        entry_weight=float(profile.get("entry_weight") or 0.0),
        weight=float(profile.get("weight") or 0.0),
        cap=float(profile.get("cap") or 0.0),
        early_cutoff=float(profile.get("early_cutoff") or 0.4),
        early_power=float(profile.get("early_power") or 1.0),
        common_min_zipf=float(profile.get("common_min_zipf") or 5.0),
        learner_source_gate=str(profile.get("learner_source_gate") or "none"),
        pos_gate=str(profile.get("pos_gate") or "none"),
        min_senses=int(profile.get("min_senses") or 2),
    )


def _delta_record(baseline: object, profile: object) -> dict[str, object]:
    base = _safe_float(baseline)
    observed = _safe_float(profile)
    return {
        "baseline": _round_float(base) if base is not None else None,
        "profile": _round_float(observed) if observed is not None else None,
        "delta": _round_float(observed - base)
        if base is not None and observed is not None
        else None,
    }


def _pair_status(gap: float) -> str:
    if abs(gap) <= PAIRWISE_TIE_TOLERANCE:
        return "tie"
    return "correct" if gap > 0.0 else "wrong"


def _base_band(value: float) -> str:
    lower = max(0, min(9, int(value * 10)))
    return f"{lower / 10:.1f}-{(lower + 1) / 10:.1f}"


def _sense_band(value: float) -> str:
    if value < 2:
        return "0-1"
    if value < 4:
        return "2-3"
    if value < 8:
        return "4-7"
    return "8+"


def _source_band(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value >= 0.999:
        return "all"
    if value <= 0.001:
        return "none"
    return "partial"


def _row_delta_table(rows: Sequence[object]) -> list[str]:
    lines = [
        "| Lemma | Expected | Before | After | Delta | Error delta | POS | Senses |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for raw in rows:
        row = _as_mapping(raw)
        lines.append(
            f"| `{_escape(row.get('lemma'))}` | {_fmt(row.get('expected'))} | "
            f"{_fmt(row.get('before'))} | {_fmt(row.get('after'))} | "
            f"{_fmt(row.get('delta'))} | {_fmt(row.get('error_delta'))} | "
            f"`{_escape(row.get('pos_bucket'))}` | {row.get('sense_count')} |"
        )
    return lines


def _pair_table(rows: Sequence[object]) -> list[str]:
    lines = [
        "| Expected easier | Expected harder | Expected gap | Baseline gap | Profile gap | Before | After |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for raw in rows:
        row = _as_mapping(raw)
        lines.append(
            f"| `{_escape(row.get('expected_easier'))}` | `{_escape(row.get('expected_harder'))}` | "
            f"{_fmt(row.get('expected_gap'))} | {_fmt(row.get('baseline_gap'))} | "
            f"{_fmt(row.get('profile_gap'))} | `{row.get('baseline_status')}` | "
            f"`{row.get('profile_status')}` |"
        )
    return lines


def _group_table(rows: Sequence[object]) -> list[str]:
    lines = [
        "| POS | Base band | Senses | Source | Count | Mean delta | Mean error delta | Improve | Regress |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for raw in rows:
        row = _as_mapping(raw)
        lines.append(
            f"| `{_escape(row.get('pos_bucket'))}` | `{row.get('base_band')}` | "
            f"`{row.get('sense_band')}` | `{row.get('source_band')}` | "
            f"{row.get('count')} | {_fmt(row.get('mean_delta'))} | "
            f"{_fmt(row.get('mean_error_delta'))} | {row.get('improvement_count')} | "
            f"{row.get('regression_count')} |"
        )
    return lines


def _params(profile: Mapping[str, object]) -> str:
    return ", ".join(f"{key}={profile.get(key)}" for key in sorted(profile))


def _score_at(row: Mapping[str, object], split: str, score: str) -> float | None:
    return _safe_float(_as_mapping(_as_mapping(row.get(split)).get("scores")).get(score))


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "-"
    return f"{numeric:.3f}"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _unique_labeled_records(
    records: Sequence[tuple[str, Mapping[str, object]]],
) -> list[tuple[str, Mapping[str, object]]]:
    result = []
    seen = set()
    for label, record in records:
        profile_id = str(record.get("profile_id") or "")
        if not profile_id or profile_id in seen:
            continue
        seen.add(profile_id)
        result.append((label, record))
    return result


def _load_optional_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    return _load_json(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
