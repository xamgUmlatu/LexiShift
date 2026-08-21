#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
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
    build_report as build_formula_probe_report,
)
from srs_learner_difficulty_formula_sweep_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_SWEEP_JSON,
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
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_es.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_polysemy_sweep_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_polysemy_sweep_en_es_latest.md"
)
PRIMARY_STATE = "normal_vocab"
PROTECTED_ERROR_MAX = 0.05
PROTECTED_REGRESSION_DELTA = 0.03
FOCUS_MIN_ERROR = 0.08


@dataclass(frozen=True)
class PolysemyProfile:
    profile_id: str
    sense_ceiling: float
    entry_weight: float
    weight: float
    cap: float
    early_cutoff: float
    early_power: float
    common_min_zipf: float
    learner_source_gate: str
    pos_gate: str
    min_senses: int


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep a bounded early/common polysemy tax for en-es learner difficulty. "
            "This is a sidecar diagnostic; it does not change production ranking."
        )
    )
    parser.add_argument("--formula-probe-json", type=Path, default=DEFAULT_FORMULA_PROBE_JSON)
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_FORMULA_SWEEP_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--candidate-id")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
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
    candidate_id: str | None = None,
    profiles: Sequence[PolysemyProfile] | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    formula_rows = [_as_mapping(row) for row in _as_sequence(formula_report.get("rows"))]
    if not formula_rows:
        raise ValueError("formula report must contain rows; rebuild with include_rows=True")
    rows_by_lemma = {str(row.get("lemma") or "").lower(): row for row in formula_rows}
    selected_candidate_id = candidate_id or _selected_candidate_id(sweep_payload)
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
    profiles = list(profiles) if profiles is not None else list(_generate_profiles())
    records = [
        _profile_record(
            profile=profile,
            rows_by_lemma=rows_by_lemma,
            base_scores_by_lemma=base_scores_by_lemma,
            calibration_labels=calibration_labels,
            holdout_labels=holdout_labels,
            labeled_rows=labeled_rows,
        )
        for profile in profiles
    ]
    calibration_top = sorted(records, key=_calibration_sort_key, reverse=True)[:30]
    stable_top = sorted(records, key=_stable_sort_key, reverse=True)[:30]
    focus_top = sorted(records, key=_focus_sort_key, reverse=True)[:30]
    safest_top = sorted(records, key=_safe_sort_key, reverse=True)[:30]
    zero_protected_records = [
        row for row in records if int(row.get("protected_regression_count") or 0) == 0
    ]
    zero_protected_top = sorted(
        zero_protected_records,
        key=_focus_sort_key,
        reverse=True,
    )[:30]
    selected_records = _unique_records(
        calibration_top[:5]
        + stable_top[:5]
        + focus_top[:5]
        + safest_top[:5]
        + zero_protected_top[:5],
        key="profile_id",
    )
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_es_learner_difficulty_polysemy_sweep_ready",
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "manual_labels_added": False,
        "method": {
            "purpose": (
                "Test whether a bounded early/common polysemy tax can correct "
                "hypercommon words whose many senses make them harder than raw "
                "frequency suggests."
            ),
            "base_candidate_id": selected_candidate_id,
            "profile_count": len(profiles),
            "protected_error_max": PROTECTED_ERROR_MAX,
            "protected_regression_delta": PROTECTED_REGRESSION_DELTA,
            "focus_min_error": FOCUS_MIN_ERROR,
            "formula": (
                "score' = score + min(cap, weight * polysemy * early_gate "
                "* common_gate * learner_source_gate * pos_gate), with all terms in [0,1]."
            ),
        },
        "inputs": {
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_probe_top_n": _as_mapping(formula_report.get("inputs")).get("top_n"),
            "formula_sweep_decision": _as_mapping(sweep_payload).get("decision"),
            "formula_sweep_generated_at": _as_mapping(sweep_payload).get("generated_at"),
            "calibration_id": calibration_payload.get("calibration_id"),
            "holdout_id": holdout_payload.get("holdout_id"),
            "calibration_count": len(calibration_labels),
            "holdout_count": len(holdout_labels),
            "joined_labeled_rows": len(labeled_rows),
            "focus_row_count": sum(1 for row in labeled_rows if bool(row.get("is_focus_row"))),
            "protected_row_count": sum(
                1 for row in labeled_rows if bool(row.get("is_protected_row"))
            ),
        },
        "summary": {
            "baseline": baseline,
            "best_calibration": _compact_record(calibration_top[0] if calibration_top else {}),
            "best_stable": _compact_record(stable_top[0] if stable_top else {}),
            "best_focus": _compact_record(focus_top[0] if focus_top else {}),
            "best_safe": _compact_record(safest_top[0] if safest_top else {}),
            "best_zero_protected": _compact_record(
                zero_protected_top[0] if zero_protected_top else {}
            ),
            "zero_protected_profile_count": len(zero_protected_records),
        },
        "leaderboards": {
            "calibration_top": calibration_top,
            "stable_top": stable_top,
            "focus_top": focus_top,
            "safe_top": safest_top,
            "zero_protected_top": zero_protected_top,
        },
        "selected_profile_details": [
            _with_change_samples(
                record,
                base_scores_by_lemma=base_scores_by_lemma,
                labeled_rows=labeled_rows,
            )
            for record in selected_records
        ],
        "limitations": [
            "Dictionary sense counts are noisy because common words often have many valid extended senses.",
            "This sweep only raises early scores; it cannot address too-hard marked/regional rows.",
            "A metric win here should still be checked in qualitative samples before promotion.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    inputs = _as_mapping(report.get("inputs"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Polysemy Tax Sweep",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Base candidate: `{method.get('base_candidate_id')}`",
        f"- Profiles swept: `{method.get('profile_count')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Inputs",
        "",
        f"- Calibration labels: `{inputs.get('calibration_count')}`",
        f"- Holdout labels: `{inputs.get('holdout_count')}`",
        f"- Joined labeled rows: `{inputs.get('joined_labeled_rows')}`",
        f"- Focus rows: `{inputs.get('focus_row_count')}`",
        f"- Protected rows: `{inputs.get('protected_row_count')}`",
        "",
        "## Summary",
        "",
        f"- Zero-protected profiles found: `{summary.get('zero_protected_profile_count')}`",
        "",
        "| Slot | Profile | Cal Balanced | Holdout Balanced | Focus Improvement | Protected Regressions |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for label, key in (
        ("baseline", "baseline"),
        ("best calibration", "best_calibration"),
        ("best stable", "best_stable"),
        ("best focus", "best_focus"),
        ("best safe", "best_safe"),
        ("best zero protected", "best_zero_protected"),
    ):
        lines.append(_summary_row(label, _as_mapping(summary.get(key))))
    for title, key in (
        ("Calibration Top", "calibration_top"),
        ("Stable Top", "stable_top"),
        ("Focus Top", "focus_top"),
        ("Safe Top", "safe_top"),
        ("Zero-Protected Top", "zero_protected_top"),
    ):
        lines.extend(["", f"## {title}", ""])
        lines.extend(
            _leaderboard_table(_as_sequence(_as_mapping(report.get("leaderboards")).get(key)))
        )
    lines.extend(["", "## Selected Profile Details", ""])
    for raw in _as_sequence(report.get("selected_profile_details")):
        record = _as_mapping(raw)
        lines.extend(
            [
                f"### `{record.get('profile_id')}`",
                "",
                f"- Calibration balanced: `{_metric(record, 'calibration_primary', 'balanced_score')}`",
                f"- Holdout balanced: `{_metric(record, 'holdout_primary', 'balanced_score')}`",
                f"- Focus mean error delta: `{_fmt(record.get('focus_mean_error_delta'))}`",
                f"- Protected regressions: `{record.get('protected_regression_count')}`",
                "",
                "Focus rows:",
                "",
                "| Lemma | Expected | Before | After | Delta | Error Delta | Senses | Entries |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in _as_sequence(record.get("focus_rows")):
            lines.append(_change_row(_as_mapping(row)))
        lines.extend(
            [
                "",
                "Largest raises:",
                "",
                "| Lemma | Expected | Before | After | Delta | Error Delta | Senses | Entries |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in _as_sequence(record.get("largest_raises")):
            lines.append(_change_row(_as_mapping(row)))
        lines.append("")
    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.extend(["## Limitations", ""])
        for item in limitations:
            lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _generate_profiles() -> Sequence[PolysemyProfile]:
    profiles = []
    for sense_ceiling in (4.0, 8.0, 14.0):
        for entry_weight in (0.0, 0.25):
            for weight in (0.10, 0.22):
                for cap in (0.06, 0.12, 0.22):
                    for early_cutoff in (0.30, 0.50):
                        for early_power in (0.5, 1.0):
                            for common_min_zipf in (4.5, 5.0):
                                for learner_source_gate in (
                                    "none",
                                    "not_all_sources",
                                ):
                                    for pos_gate in (
                                        "none",
                                        "content_only",
                                        "noun_adj_only",
                                        "content_soft",
                                    ):
                                        for min_senses in (2, 4, 6):
                                            profiles.append(
                                                PolysemyProfile(
                                                    profile_id=(
                                                        f"poly_s{_slug(sense_ceiling)}"
                                                        f"_ew{_slug(entry_weight)}"
                                                        f"_w{_slug(weight)}"
                                                        f"_c{_slug(cap)}"
                                                        f"_e{_slug(early_cutoff)}"
                                                        f"_p{_slug(early_power)}"
                                                        f"_z{_slug(common_min_zipf)}"
                                                        f"_{learner_source_gate}"
                                                        f"_{pos_gate}"
                                                        f"_ms{min_senses}"
                                                    ),
                                                    sense_ceiling=sense_ceiling,
                                                    entry_weight=entry_weight,
                                                    weight=weight,
                                                    cap=cap,
                                                    early_cutoff=early_cutoff,
                                                    early_power=early_power,
                                                    common_min_zipf=common_min_zipf,
                                                    learner_source_gate=learner_source_gate,
                                                    pos_gate=pos_gate,
                                                    min_senses=min_senses,
                                                ),
                                            )
    return profiles


def _profile_record(
    *,
    profile: PolysemyProfile,
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    base_scores_by_lemma: Mapping[str, float],
    calibration_labels: Sequence[Mapping[str, object]],
    holdout_labels: Sequence[Mapping[str, object]],
    labeled_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    scorer = _profile_scorer(profile=profile, base_scores_by_lemma=base_scores_by_lemma)
    record = _record_for_scorer(
        record_id=profile.profile_id,
        scorer=scorer,
        rows_by_lemma=rows_by_lemma,
        calibration_labels=calibration_labels,
        holdout_labels=holdout_labels,
        labeled_rows=labeled_rows,
    )
    record["profile"] = {
        "sense_ceiling": profile.sense_ceiling,
        "entry_weight": profile.entry_weight,
        "weight": profile.weight,
        "cap": profile.cap,
        "early_cutoff": profile.early_cutoff,
        "early_power": profile.early_power,
        "common_min_zipf": profile.common_min_zipf,
        "learner_source_gate": profile.learner_source_gate,
        "pos_gate": profile.pos_gate,
        "min_senses": profile.min_senses,
    }
    return record


def _record_for_scorer(
    *,
    record_id: str,
    scorer: Callable[[Mapping[str, object]], float],
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    calibration_labels: Sequence[Mapping[str, object]],
    holdout_labels: Sequence[Mapping[str, object]],
    labeled_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    focus = []
    protected_regressions = []
    for row in labeled_rows:
        source = _as_mapping(row.get("row"))
        expected = _safe_float(row.get("expected"))
        base_score = _safe_float(row.get("base_score"))
        if expected is None or base_score is None:
            continue
        observed = scorer(source)
        base_error = abs(base_score - expected)
        observed_error = abs(observed - expected)
        if row.get("is_focus_row"):
            focus.append(observed_error - base_error)
        if (
            row.get("is_protected_row")
            and observed_error - base_error >= PROTECTED_REGRESSION_DELTA
        ):
            protected_regressions.append(row)
    return {
        "profile_id": record_id,
        "calibration_primary": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            scorer=scorer,
            primary_only=True,
        ),
        "holdout_primary": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            scorer=scorer,
            primary_only=True,
        ),
        "focus_mean_error_delta": _round_float(float(np.mean(focus)) if focus else 0.0),
        "focus_improvement": _round_float(-float(np.mean(focus)) if focus else 0.0),
        "protected_regression_count": len(protected_regressions),
    }


def _profile_scorer(
    *,
    profile: PolysemyProfile,
    base_scores_by_lemma: Mapping[str, float],
) -> Callable[[Mapping[str, object]], float]:
    def score(row: Mapping[str, object]) -> float:
        lemma = str(row.get("lemma") or "").lower()
        base = base_scores_by_lemma.get(lemma, 0.0)
        tax = _polysemy_tax(row=row, base=base, profile=profile)
        return _round_float(_clamp01(base + tax))

    return score


def _polysemy_tax(
    *,
    row: Mapping[str, object],
    base: float,
    profile: PolysemyProfile,
) -> float:
    dictionary = _as_mapping(row.get("dictionary"))
    components = _as_mapping(row.get("components"))
    sense_count = _safe_int(dictionary.get("sense_count"))
    if sense_count < profile.min_senses:
        return 0.0
    sense_score = _log_score(sense_count, ceiling=profile.sense_ceiling)
    entry_score = _log_score(dictionary.get("entry_count"), ceiling=4.0)
    polysemy = _clamp01(
        sense_score * (1.0 - profile.entry_weight) + entry_score * profile.entry_weight
    )
    early_gate = _early_gate(base, cutoff=profile.early_cutoff, power=profile.early_power)
    common_gate = _common_gate(components, min_zipf=profile.common_min_zipf)
    learner_gate = _learner_gate(components, mode=profile.learner_source_gate)
    pos_gate = _pos_gate(row=row, mode=profile.pos_gate)
    raw_tax = profile.weight * polysemy * early_gate * common_gate * learner_gate * pos_gate
    return min(profile.cap, raw_tax)


def _joined_labeled_rows(
    *,
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    base_scores_by_lemma: Mapping[str, float],
    calibration_labels: Sequence[Mapping[str, object]],
    holdout_labels: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    result = []
    for split, labels in (("calibration", calibration_labels), ("holdout", holdout_labels)):
        for label in labels:
            expected = _safe_float(label.get("expected_learner_difficulty"))
            if expected is None:
                continue
            lemma = str(label.get("lemma") or "").lower()
            row = rows_by_lemma.get(lemma)
            base_score = base_scores_by_lemma.get(lemma)
            if row is None or base_score is None:
                continue
            dictionary = _as_mapping(row.get("dictionary"))
            base_error = abs(base_score - expected)
            too_easy = base_score + FOCUS_MIN_ERROR <= expected
            is_focus = (
                str(label.get("expected_candidate_state") or "") == PRIMARY_STATE
                and too_easy
                and base_score <= 0.45
                and _safe_int(dictionary.get("sense_count")) >= 4
            )
            result.append(
                {
                    "split": split,
                    "label": label,
                    "row": row,
                    "lemma": lemma,
                    "expected": _round_float(expected),
                    "base_score": _round_float(base_score),
                    "base_error": _round_float(base_error),
                    "is_focus_row": is_focus,
                    "is_protected_row": (
                        str(label.get("expected_candidate_state") or "") == PRIMARY_STATE
                        and base_error <= PROTECTED_ERROR_MAX
                    ),
                }
            )
    return result


def _evaluate_labels(
    *,
    labels: Sequence[Mapping[str, object]],
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    scorer: Callable[[Mapping[str, object]], float],
    primary_only: bool,
) -> dict[str, object]:
    selected = [
        label
        for label in labels
        if _safe_float(label.get("expected_learner_difficulty")) is not None
        and (not primary_only or str(label.get("expected_candidate_state") or "") == PRIMARY_STATE)
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
        observed = scorer(row) if row is not None else float("nan")
        if row is None:
            missing.append(lemma)
        expected = _safe_float(label.get("expected_learner_difficulty"))
        expected_values.append(expected if expected is not None else float("nan"))
        observed_values.append(observed)
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


def _with_change_samples(
    record: Mapping[str, object],
    *,
    base_scores_by_lemma: Mapping[str, float],
    labeled_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    profile = _profile_from_record(record)
    scorer = _profile_scorer(profile=profile, base_scores_by_lemma=base_scores_by_lemma)
    changes = []
    for labeled in labeled_rows:
        row = _as_mapping(labeled.get("row"))
        expected = _safe_float(labeled.get("expected"))
        base_score = _safe_float(labeled.get("base_score"))
        if expected is None or base_score is None:
            continue
        after = scorer(row)
        dictionary = _as_mapping(row.get("dictionary"))
        changes.append(
            {
                "lemma": row.get("lemma"),
                "split": labeled.get("split"),
                "expected": _round_float(expected),
                "before": _round_float(base_score),
                "after": _round_float(after),
                "delta": _round_float(after - base_score),
                "error_delta": _round_float(abs(after - expected) - abs(base_score - expected)),
                "sense_count": dictionary.get("sense_count"),
                "entry_count": dictionary.get("entry_count"),
                "translations": list(_as_sequence(row.get("translations")))[:4],
                "is_focus_row": bool(labeled.get("is_focus_row")),
                "is_protected_row": bool(labeled.get("is_protected_row")),
            }
        )
    detailed = dict(record)
    detailed["focus_rows"] = sorted(
        [row for row in changes if row.get("is_focus_row")],
        key=lambda row: _safe_float(row.get("error_delta")) or 0.0,
    )[:20]
    detailed["largest_raises"] = sorted(
        [row for row in changes if (_safe_float(row.get("delta")) or 0.0) > 0.0],
        key=lambda row: _safe_float(row.get("delta")) or 0.0,
        reverse=True,
    )[:20]
    detailed["protected_regression_rows"] = [
        row
        for row in changes
        if row.get("is_protected_row")
        and (_safe_float(row.get("error_delta")) or 0.0) >= PROTECTED_REGRESSION_DELTA
    ][:20]
    return detailed


def _profile_from_record(record: Mapping[str, object]) -> PolysemyProfile:
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


def _calibration_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    return (
        _score_at(row, "calibration_primary", "balanced_score") or -1.0,
        _safe_float(row.get("focus_improvement")) or 0.0,
        -float(row.get("protected_regression_count") or 0),
        _score_at(row, "holdout_primary", "balanced_score") or -1.0,
    )


def _stable_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    cal = _score_at(row, "calibration_primary", "balanced_score") or -1.0
    holdout = _score_at(row, "holdout_primary", "balanced_score") or -1.0
    gap = abs(cal - holdout)
    return (
        ((cal + holdout) / 2.0) - gap * 0.35,
        min(cal, holdout),
        _safe_float(row.get("focus_improvement")) or 0.0,
        -float(row.get("protected_regression_count") or 0),
    )


def _focus_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    return (
        _safe_float(row.get("focus_improvement")) or 0.0,
        -float(row.get("protected_regression_count") or 0),
        _score_at(row, "calibration_primary", "balanced_score") or -1.0,
        _score_at(row, "holdout_primary", "balanced_score") or -1.0,
    )


def _safe_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    return (
        -float(row.get("protected_regression_count") or 0),
        _score_at(row, "calibration_primary", "balanced_score") or -1.0,
        _safe_float(row.get("focus_improvement")) or 0.0,
        _score_at(row, "holdout_primary", "balanced_score") or -1.0,
    )


def _summary_row(label: str, row: Mapping[str, object]) -> str:
    cal = _score_at(row, "calibration_primary", "balanced_score")
    holdout = _score_at(row, "holdout_primary", "balanced_score")
    if cal is None:
        cal = _safe_float(row.get("calibration_balanced"))
    if holdout is None:
        holdout = _safe_float(row.get("holdout_balanced"))
    return (
        f"| {label} | `{row.get('profile_id') or '-'}` | "
        f"{_fmt(cal)} | "
        f"{_fmt(holdout)} | "
        f"{_fmt(row.get('focus_improvement'))} | {row.get('protected_regression_count', 0)} |"
    )


def _leaderboard_table(rows: Sequence[object]) -> list[str]:
    lines = [
        "| # | Profile | Cal Balanced | Holdout Balanced | Focus Improvement | Protected Regressions | Params |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for index, raw in enumerate(rows[:12], start=1):
        row = _as_mapping(raw)
        profile = _as_mapping(row.get("profile"))
        params = ", ".join(
            f"{key}={profile.get(key)}"
            for key in (
                "sense_ceiling",
                "entry_weight",
                "weight",
                "cap",
                "early_cutoff",
                "early_power",
                "common_min_zipf",
                "learner_source_gate",
                "pos_gate",
                "min_senses",
            )
        )
        lines.append(
            f"| {index} | `{row.get('profile_id')}` | "
            f"{_fmt(_score_at(row, 'calibration_primary', 'balanced_score'))} | "
            f"{_fmt(_score_at(row, 'holdout_primary', 'balanced_score'))} | "
            f"{_fmt(row.get('focus_improvement'))} | {row.get('protected_regression_count')} | "
            f"{_escape(params)} |"
        )
    return lines


def _change_row(row: Mapping[str, object]) -> str:
    return (
        f"| `{_escape(row.get('lemma'))}` | {_fmt(row.get('expected'))} | "
        f"{_fmt(row.get('before'))} | {_fmt(row.get('after'))} | "
        f"{_fmt(row.get('delta'))} | {_fmt(row.get('error_delta'))} | "
        f"{row.get('sense_count')} | {row.get('entry_count')} |"
    )


def _compact_record(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "profile_id": row.get("profile_id"),
        "profile": row.get("profile"),
        "calibration_balanced": _score_at(row, "calibration_primary", "balanced_score"),
        "holdout_balanced": _score_at(row, "holdout_primary", "balanced_score"),
        "calibration_mae": _metric_at(row, "calibration_primary", "mae"),
        "holdout_mae": _metric_at(row, "holdout_primary", "mae"),
        "focus_improvement": row.get("focus_improvement"),
        "focus_mean_error_delta": row.get("focus_mean_error_delta"),
        "protected_regression_count": row.get("protected_regression_count"),
    }


def _score_at(row: Mapping[str, object], split: str, score: str) -> float | None:
    return _safe_float(_as_mapping(_as_mapping(row.get(split)).get("scores")).get(score))


def _metric_at(row: Mapping[str, object], split: str, metric: str) -> float | None:
    return _safe_float(_as_mapping(_as_mapping(row.get(split)).get("metrics")).get(metric))


def _metric(row: Mapping[str, object], split: str, score: str) -> str:
    return _fmt(_score_at(row, split, score))


def _early_gate(base: float, *, cutoff: float, power: float) -> float:
    if cutoff <= 0.0 or base >= cutoff:
        return 0.0
    value = _clamp01((cutoff - base) / cutoff)
    return _clamp01(value**power)


def _common_gate(components: Mapping[str, object], *, min_zipf: float) -> float:
    zipf = _safe_float(components.get("wordfreq_zipf")) or 0.0
    if zipf <= 0.0:
        return 0.0
    return _clamp01((zipf - min_zipf) / max(0.01, 6.0 - min_zipf))


def _learner_gate(components: Mapping[str, object], *, mode: str) -> float:
    if mode == "none":
        return 1.0
    count = _safe_float(components.get("learner_source_count")) or 0.0
    if mode == "not_all_sources":
        return 0.0 if count >= 0.999 else 1.0
    if mode == "partial_source_strength":
        return _clamp01(1.0 - count)
    return 1.0


def _pos_gate(*, row: Mapping[str, object], mode: str) -> float:
    if mode == "none":
        return 1.0
    bucket = str(row.get("pos_bucket") or "").lower()
    if mode == "content_only":
        return 1.0 if bucket in {"noun", "verb", "adjective"} else 0.0
    if mode == "noun_adj_only":
        return 1.0 if bucket in {"noun", "adjective"} else 0.0
    components = _as_mapping(row.get("components"))
    if mode == "content_soft":
        content = _safe_float(components.get("pos_content_gate")) or 0.0
        function = _safe_float(components.get("pos_function_risk")) or 0.0
        other = _safe_float(components.get("pos_other_risk")) or 0.0
        return _clamp01(content * (1.0 - 0.75 * function) * (1.0 - 0.75 * other))
    return 1.0


def _log_score(value: object, *, ceiling: float) -> float:
    numeric = _safe_float(value) or 0.0
    if numeric <= 1.0:
        return 0.0
    return _clamp01(math.log1p(numeric - 1.0) / math.log1p(max(1.0, ceiling - 1.0)))


def _selected_candidate_id(sweep_payload: Mapping[str, object] | None) -> str:
    summary = _as_mapping(_as_mapping(sweep_payload).get("summary"))
    for key in (
        "best_stable_candidate",
        "best_holdout_guarded_candidate",
        "best_calibration_candidate",
    ):
        candidate_id = str(_as_mapping(summary.get(key)).get("candidate_id") or "")
        if candidate_id:
            return candidate_id
    return "spalex_blend__lsb_w090_c022__cog_l__no_wf__no_guard"


def _unique_records(
    records: Sequence[Mapping[str, object]],
    *,
    key: str,
) -> list[Mapping[str, object]]:
    result = []
    seen = set()
    for record in records:
        value = str(record.get(key) or "")
        if value in seen:
            continue
        seen.add(value)
        result.append(record)
    return result


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


def _safe_int(value: object) -> int:
    numeric = _safe_float(value)
    return int(numeric) if numeric is not None else 0


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


def _slug(value: float) -> str:
    return f"{value:.2f}".replace(".", "")


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
