#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
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
    DEFAULT_MANUAL_CORRECTIONS_JSON,
    FormulaCandidate,
    _apply_correction,
    _corrections_by_lemma,
    _score_formula,
    generate_candidates,
)
from srs_learner_difficulty_normalization import (  # noqa: E402
    DEFAULT_TARGET_BAND_WEIGHTS,
    difficulty_bands,
    target_band_counts,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_metrics,
    _summary_metrics,
)


PAIR = "en-es"
DEFAULT_TOP_N = 45000
DEFAULT_CANDIDATE_LIMIT = 180
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
    / "srs_learner_difficulty_score_warp_sweep_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_score_warp_sweep_en_es_latest.md"
)
PRIMARY_STATE = "normal_vocab"
PROFILE_DIMENSIONS = ("base", "learner", "cognate", "side_source", "guard")
STRATIFIED_BASE_IDS = ("zipf_base", "spalex_blend")
STRATIFIED_LEARNER_IDS = (
    "no_ls",
    "lsz_w060_c012",
    "lsz_w080_c018",
    "lsz_w105_c022",
    "lsb_w060_c012",
    "lsb_w075_c016",
    "lsb_w090_c022",
    "lsb_w105_c022",
    "lsbq_w075_c016",
    "lsbq_w090_c022",
    "lsbq_w105_c022",
    "lsbs_w075_c016",
    "lsbs_w090_c022",
    "lsbs_w105_c022",
)
STRATIFIED_COGNATE_IDS = ("no_cog", "cog_l", "cog_m", "cog_tail")
STRATIFIED_SIDE_SOURCE_IDS = (
    "no_wf",
    "wf_l",
    "wf_m",
    "wf_tail_l",
    "wf_tail_m",
    "wf_reg_l",
    "lex_micro",
    "lex_mid_l",
    "lex_mid_m",
    "lex_tail_l",
)
STRATIFIED_GUARD_IDS = (
    "no_guard",
    "pos_l",
    "dict_l",
    "tail_l",
    "broad_abs_l",
    "broad_abs_t50",
    "broad_abs_t80",
    "ue_floor_l",
    "ue_content_m",
    "ue_struct_l",
    "ue_marked_l",
    "ue_marked_m",
    "ue_usage_l",
    "ue_usage_m",
    "ue_struct_m",
    "ue_combo_m",
    "dict_detail_l",
    "lex_caution_l",
    "combo_l",
    "combo_m",
)


@dataclass(frozen=True)
class WarpProfile:
    profile_id: str
    description: str
    transform: Callable[[np.ndarray, Sequence[Mapping[str, object]]], np.ndarray]
    monotonic: bool = True
    uses_rank: bool = False


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep post-score normalization/warp profiles over selected en-es "
            "learner-difficulty formula candidates."
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
        "--apply-manual-corrections",
        action="store_true",
        help="Apply the sidecar manual correction layer after score warping.",
    )
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--candidate-limit", type=int, default=DEFAULT_CANDIDATE_LIMIT)
    parser.add_argument(
        "--candidate-pool",
        choices=("leaderboard", "stratified", "all"),
        default="stratified",
        help=(
            "leaderboard uses the existing formula-sweep leaders; stratified "
            "keeps key formula-shape dimensions open in a bounded pool; all "
            "uses generated formula order up to --candidate-limit."
        ),
    )
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
        calibration_payload=_load_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_json(Path(args.holdout_json).expanduser()),
        corrections_payload=(
            _load_json(Path(args.manual_corrections_json).expanduser())
            if bool(args.apply_manual_corrections)
            else {}
        ),
        candidate_pool=str(args.candidate_pool),
        candidate_limit=max(1, int(args.candidate_limit)),
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
    formula_sweep_payload: Mapping[str, object] | None,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    corrections_payload: Mapping[str, object] | None = None,
    candidate_pool: str = "stratified",
    candidate_limit: int = DEFAULT_CANDIDATE_LIMIT,
    generated_at: str | None = None,
    candidate_ids: Sequence[str] | None = None,
    warp_profiles: Sequence[WarpProfile] | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    formula_rows = [_as_mapping(row) for row in _as_sequence(formula_report.get("rows"))]
    if not formula_rows:
        raise ValueError("formula report must contain rows; rebuild with include_rows=True")
    candidates_by_id = {candidate.candidate_id: candidate for candidate in generate_candidates()}
    selected_ids = (
        _unique_strings(candidate_ids)
        if candidate_ids is not None
        else _candidate_ids_for_pool(
            formula_sweep_payload=formula_sweep_payload,
            candidate_pool=candidate_pool,
            candidate_limit=candidate_limit,
            candidates_by_id=candidates_by_id,
        )
    )
    candidates = [
        candidates_by_id[candidate_id]
        for candidate_id in selected_ids
        if candidate_id in candidates_by_id
    ]
    if not candidates:
        raise ValueError("no valid formula candidates selected for score-warp sweep")
    profiles = tuple(warp_profiles or generate_warp_profiles())
    calibration_labels = [
        _as_mapping(row) for row in _as_sequence(calibration_payload.get("labels"))
    ]
    holdout_labels = [_as_mapping(row) for row in _as_sequence(holdout_payload.get("labels"))]
    corrections_by_lemma = _corrections_by_lemma(_as_mapping(corrections_payload))
    records: list[dict[str, object]] = []
    for candidate in candidates:
        raw_scores = _candidate_scores(candidate, formula_rows)
        for profile in profiles:
            warped_scores = _apply_warp(profile, raw_scores, formula_rows)
            records.append(
                _profile_record(
                    candidate=candidate,
                    profile=profile,
                    raw_scores=raw_scores,
                    warped_scores=warped_scores,
                    rows=formula_rows,
                    calibration_labels=calibration_labels,
                    holdout_labels=holdout_labels,
                    corrections_by_lemma=corrections_by_lemma,
                )
            )
    calibration_top = sorted(records, key=_calibration_sort_key, reverse=True)[:30]
    calibration_mae_top = sorted(records, key=_calibration_mae_sort_key)[:30]
    holdout_mae_top = sorted(records, key=_holdout_mae_sort_key)[:30]
    holdout_guarded_top = sorted(records, key=_holdout_guarded_sort_key, reverse=True)[:30]
    stable_top = sorted(records, key=_stable_sort_key, reverse=True)[:30]
    identity_records = [record for record in records if record["warp_id"] == "identity"]
    best_identity = sorted(identity_records, key=_stable_sort_key, reverse=True)[0]
    best_calibration = calibration_top[0] if calibration_top else {}
    best_calibration_mae = calibration_mae_top[0] if calibration_mae_top else {}
    best_holdout_mae = holdout_mae_top[0] if holdout_mae_top else {}
    best_guarded = holdout_guarded_top[0] if holdout_guarded_top else {}
    best_stable = stable_top[0] if stable_top else {}
    selected = _unique_records(
        [
            best_identity,
            best_calibration,
            best_calibration_mae,
            best_holdout_mae,
            best_guarded,
            best_stable,
        ],
        key="profile_key",
    )
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_es_learner_difficulty_score_warp_sweep_ready",
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "method": {
            "purpose": (
                "Test whether the formula candidate score scale should be post-processed "
                "by a monotonic normalization/warp before manual cleanup."
            ),
            "candidate_pool": candidate_pool,
            "candidate_limit": candidate_limit,
            "candidate_count": len(candidates),
            "warp_count": len(profiles),
            "profile_count": len(records),
            "selected_candidate_profile_summary": _profile_value_counts(candidates),
            "selected_candidate_ids": [candidate.candidate_id for candidate in candidates],
            "manual_corrections_applied": bool(corrections_by_lemma),
            "manual_correction_count": len(corrections_by_lemma),
            "selection_warning": (
                "Calibration remains the selection split. Holdout is reported as an "
                "overfitting check because score warps can improve absolute-error "
                "metrics without changing pairwise order."
            ),
        },
        "inputs": {
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_probe_top_n": _as_mapping(formula_report.get("inputs")).get("top_n"),
            "formula_sweep_decision": _as_mapping(formula_sweep_payload).get("decision"),
            "formula_sweep_generated_at": _as_mapping(formula_sweep_payload).get("generated_at"),
            "manual_correction_status": _as_mapping(corrections_payload).get("status"),
            "calibration_id": calibration_payload.get("calibration_id"),
            "holdout_id": holdout_payload.get("holdout_id"),
            "calibration_count": len(calibration_labels),
            "holdout_count": len(holdout_labels),
        },
        "summary": {
            "best_identity_profile": _compact_record(best_identity),
            "best_calibration_profile": _compact_record(best_calibration),
            "best_calibration_mae_profile": _compact_record(best_calibration_mae),
            "best_holdout_mae_profile": _compact_record(best_holdout_mae),
            "best_holdout_guarded_profile": _compact_record(best_guarded),
            "best_stable_profile": _compact_record(best_stable),
        },
        "leaderboards": {
            "calibration_top": calibration_top,
            "calibration_mae_top": calibration_mae_top,
            "holdout_mae_top": holdout_mae_top,
            "holdout_guarded_top": holdout_guarded_top,
            "stable_top": stable_top,
        },
        "selected_profile_details": [
            _with_change_samples(record, rows=formula_rows, limit=15) for record in selected
        ],
        "limitations": [
            "The default candidate pool is bounded and stratified across key formula dimensions, not all 32k generated formulas.",
            "Monotonic warps do not create new pairwise information; they only recalibrate absolute proficiency-scale placement.",
            "Rank-curve warps can improve MAE while making product band density less intuitive, so qualitative band review remains required.",
            "When manual corrections are enabled, corrections are applied after the score warp so the comparison matches the final cleanup layer.",
        ],
    }


def generate_warp_profiles() -> tuple[WarpProfile, ...]:
    profiles: list[WarpProfile] = [
        WarpProfile("identity", "No post-score normalization.", _identity),
        WarpProfile("minmax", "Corpus min/max stretch to 0..1.", _minmax),
        WarpProfile(
            "rank_uniform",
            "Assign scores by corpus rank uniformly over 0..1.",
            _rank_uniform,
            uses_rank=True,
        ),
        WarpProfile(
            "rank_curriculum_v1",
            "Assign scores by corpus rank using the existing curriculum target band curve.",
            _rank_curriculum_curve,
            uses_rank=True,
        ),
    ]
    for gamma in (0.70, 0.80, 0.90, 1.10, 1.25, 1.50):
        profiles.append(
            WarpProfile(
                f"power_g{_slug(gamma)}",
                f"Power warp on raw clamped scores: x^{gamma:.2f}.",
                _power(gamma),
            )
        )
        profiles.append(
            WarpProfile(
                f"minmax_power_g{_slug(gamma)}",
                f"Min/max stretch followed by power warp: x^{gamma:.2f}.",
                _minmax_power(gamma),
            )
        )
    for slope in (4.0, 8.0):
        for center in (0.40, 0.50, 0.60):
            profiles.append(
                WarpProfile(
                    f"logistic_s{_slug(slope)}_c{_slug(center)}",
                    f"Endpoint-normalized logistic warp, slope={slope:.1f}, center={center:.2f}.",
                    _logistic(slope=slope, center=center),
                )
            )
    for scale in (0.85, 1.00, 1.15):
        for offset in (-0.04, 0.04):
            profiles.append(
                WarpProfile(
                    f"affine_s{_slug(scale)}_o{_signed_slug(offset)}",
                    f"Clipped affine warp: {scale:.2f}x {offset:+.2f}.",
                    _affine(scale=scale, offset=offset),
                )
            )
    return tuple(profiles)


def _candidate_scores(
    candidate: FormulaCandidate, rows: Sequence[Mapping[str, object]]
) -> np.ndarray:
    return np.asarray([_score_formula(candidate, row) for row in rows], dtype=np.float32)


def _apply_warp(
    profile: WarpProfile,
    scores: np.ndarray,
    rows: Sequence[Mapping[str, object]],
) -> np.ndarray:
    warped = np.asarray(profile.transform(scores, rows), dtype=np.float32)
    return np.clip(warped, 0.0, 1.0)


def _profile_record(
    *,
    candidate: FormulaCandidate,
    profile: WarpProfile,
    raw_scores: np.ndarray,
    warped_scores: np.ndarray,
    rows: Sequence[Mapping[str, object]],
    calibration_labels: Sequence[Mapping[str, object]],
    holdout_labels: Sequence[Mapping[str, object]],
    corrections_by_lemma: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    rows_by_lemma = {
        str(row.get("lemma") or "").lower(): (index, row) for index, row in enumerate(rows)
    }
    record = {
        "profile_key": f"{candidate.candidate_id}::{profile.profile_id}",
        "candidate_id": candidate.candidate_id,
        "candidate_profile": dict(candidate.profile),
        "warp_id": profile.profile_id,
        "warp_description": profile.description,
        "warp_monotonic": profile.monotonic,
        "warp_uses_rank": profile.uses_rank,
        "score_summary": _score_summary(raw_scores=raw_scores, warped_scores=warped_scores),
        "calibration_primary": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            scores=warped_scores,
            primary_only=True,
            corrections_by_lemma=corrections_by_lemma,
        ),
        "holdout_primary": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            scores=warped_scores,
            primary_only=True,
            corrections_by_lemma=corrections_by_lemma,
        ),
        "calibration_raw_primary": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            scores=raw_scores,
            primary_only=True,
            corrections_by_lemma=corrections_by_lemma,
        ),
        "holdout_raw_primary": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            scores=raw_scores,
            primary_only=True,
            corrections_by_lemma=corrections_by_lemma,
        ),
    }
    record["deltas_vs_raw_candidate"] = {
        "calibration_balanced": _metric_delta(
            record, "calibration_primary", "calibration_raw_primary", "balanced_score"
        ),
        "holdout_balanced": _metric_delta(
            record, "holdout_primary", "holdout_raw_primary", "balanced_score"
        ),
        "calibration_mae": _summary_delta(
            record, "calibration_primary", "calibration_raw_primary", "mae"
        ),
        "holdout_mae": _summary_delta(record, "holdout_primary", "holdout_raw_primary", "mae"),
    }
    return record


def _evaluate_labels(
    *,
    labels: Sequence[Mapping[str, object]],
    rows_by_lemma: Mapping[str, tuple[int, Mapping[str, object]]],
    scores: np.ndarray,
    primary_only: bool,
    corrections_by_lemma: Mapping[str, Mapping[str, object]],
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
    row_pairs = []
    missing = []
    for label in selected:
        lemma = str(label.get("lemma") or "")
        pair = rows_by_lemma.get(lemma.lower())
        row = _as_mapping(pair[1]) if pair else {}
        if pair is None:
            missing.append(lemma)
            observed = float("nan")
        else:
            observed = float(scores[pair[0]])
            observed = _apply_correction(
                observed,
                corrections_by_lemma.get(lemma.lower(), {}),
            )
        expected = _safe_float(label.get("expected_learner_difficulty"))
        expected_values.append(expected if expected is not None else float("nan"))
        observed_values.append(observed)
        expected_bands.append(str(label.get("expected_difficulty_band") or ""))
        label_names.append(lemma)
        expected_states.append(str(label.get("expected_candidate_state") or ""))
        observed_states.append(str(row.get("candidate_state") or ""))
        row_pairs.append((label, row, observed))
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
        "largest_errors": _largest_errors(row_pairs, limit=20),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Learner Difficulty Score Warp Sweep",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Sweep Scope",
        "",
        f"- Candidate pool: `{method.get('candidate_pool')}`",
        f"- Formula candidates: `{method.get('candidate_count')}`",
        f"- Warp profiles: `{method.get('warp_count')}`",
        f"- Candidate/warp profiles: `{method.get('profile_count')}`",
        f"- Manual corrections applied: `{method.get('manual_corrections_applied')}`",
        f"- Manual correction rows: `{method.get('manual_correction_count')}`",
        "",
        "## Candidate Shape Coverage",
        "",
    ]
    profile_summary = _as_mapping(method.get("selected_candidate_profile_summary"))
    for dimension in PROFILE_DIMENSIONS:
        counts = _as_mapping(profile_summary.get(dimension))
        if not counts:
            continue
        rendered = ", ".join(f"`{_escape(key)}` ({value})" for key, value in counts.items())
        lines.append(f"- `{dimension}`: {rendered}")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            "| Selection | Candidate | Warp | Cal Balanced | Holdout Balanced | Cal MAE | Holdout MAE | Cal Δ | Holdout Δ |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for key, label in (
        ("best_identity_profile", "best identity"),
        ("best_calibration_profile", "best calibration"),
        ("best_calibration_mae_profile", "best calibration MAE"),
        ("best_holdout_mae_profile", "best holdout MAE"),
        ("best_holdout_guarded_profile", "best holdout-guarded"),
        ("best_stable_profile", "best stable"),
    ):
        lines.append(_summary_row(label, _as_mapping(summary.get(key))))
    lines.extend(
        [
            "",
            "Selection note: score warps primarily affect MAE/bucket calibration, not pairwise order.",
            "",
        ]
    )
    leaderboards = _as_mapping(report.get("leaderboards"))
    for key, title in (
        ("calibration_top", "Calibration Top"),
        ("calibration_mae_top", "Calibration MAE Top"),
        ("holdout_mae_top", "Holdout MAE Top"),
        ("holdout_guarded_top", "Holdout-Guarded Top"),
        ("stable_top", "Stable Top"),
    ):
        lines.extend(
            [
                f"## {title}",
                "",
                "| Candidate | Warp | Cal Balanced | Holdout Balanced | Cal MAE | Holdout MAE | Raw Cal Δ | Raw Holdout Δ |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in _as_sequence(leaderboards.get(key))[:12]:
            lines.append(_leaderboard_row(_as_mapping(row)))
        lines.append("")
    for raw in _as_sequence(report.get("selected_profile_details")):
        lines.extend(_profile_detail_lines(_as_mapping(raw)))
    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.append("## Limitations")
        lines.append("")
        for item in limitations:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def _candidate_ids_for_pool(
    *,
    formula_sweep_payload: Mapping[str, object] | None,
    candidate_pool: str,
    candidate_limit: int,
    candidates_by_id: Mapping[str, FormulaCandidate],
) -> tuple[str, ...]:
    if candidate_pool == "all":
        return tuple(list(candidates_by_id.keys())[:candidate_limit])
    if candidate_pool == "stratified":
        return _stratified_candidate_ids(
            formula_sweep_payload=formula_sweep_payload,
            candidate_limit=candidate_limit,
            candidates_by_id=candidates_by_id,
        )
    return _leaderboard_candidate_ids(
        formula_sweep_payload=formula_sweep_payload,
        candidate_limit=candidate_limit,
        candidates_by_id=candidates_by_id,
    )


def _leaderboard_candidate_ids(
    *,
    formula_sweep_payload: Mapping[str, object] | None,
    candidate_limit: int,
    candidates_by_id: Mapping[str, FormulaCandidate],
) -> tuple[str, ...]:
    ids: list[str] = []
    summary = _as_mapping(_as_mapping(formula_sweep_payload).get("summary"))
    for key in (
        "best_stable_candidate",
        "best_holdout_guarded_candidate",
        "best_calibration_candidate",
        "current_best_baseline",
    ):
        _append_candidate_id(ids, _as_mapping(summary.get(key)).get("candidate_id"))
    leaderboards = _as_mapping(_as_mapping(formula_sweep_payload).get("leaderboards"))
    for board_key in ("stable_top", "calibration_top", "holdout_guarded_top"):
        for row in _as_sequence(leaderboards.get(board_key)):
            _append_candidate_id(ids, _as_mapping(row).get("candidate_id"))
            if len(_unique_strings(ids)) >= candidate_limit:
                return _unique_strings(ids)
    if not ids:
        ids = list(candidates_by_id.keys())[:candidate_limit]
    return _unique_strings(ids)[:candidate_limit]


def _stratified_candidate_ids(
    *,
    formula_sweep_payload: Mapping[str, object] | None,
    candidate_limit: int,
    candidates_by_id: Mapping[str, FormulaCandidate],
) -> tuple[str, ...]:
    seed_limit = min(candidate_limit, max(0, min(50, candidate_limit // 4)))
    has_leaderboard_payload = bool(
        _as_mapping(_as_mapping(formula_sweep_payload).get("leaderboards"))
        or _as_mapping(_as_mapping(formula_sweep_payload).get("summary"))
    )
    ids = (
        list(
            _leaderboard_candidate_ids(
                formula_sweep_payload=formula_sweep_payload,
                candidate_limit=seed_limit,
                candidates_by_id=candidates_by_id,
            )
        )
        if has_leaderboard_payload and seed_limit > 0
        else []
    )
    ids = [
        candidate_id for candidate_id in _unique_strings(ids) if candidate_id in candidates_by_id
    ]
    token_counts: Counter[str] = Counter()
    for candidate_id in ids:
        token_counts.update(_profile_tokens(candidates_by_id[candidate_id]))

    selected = set(ids)
    eligible = [
        candidate
        for candidate in candidates_by_id.values()
        if candidate.candidate_id not in selected and _candidate_in_stratified_scope(candidate)
    ]
    order = {candidate.candidate_id: index for index, candidate in enumerate(eligible)}
    while len(ids) < candidate_limit and eligible:
        best = max(
            eligible,
            key=lambda candidate: (
                _coverage_score(candidate, token_counts),
                -order[candidate.candidate_id],
            ),
        )
        ids.append(best.candidate_id)
        selected.add(best.candidate_id)
        token_counts.update(_profile_tokens(best))
        eligible = [candidate for candidate in eligible if candidate.candidate_id not in selected]
    if len(ids) < candidate_limit:
        for candidate_id in candidates_by_id:
            if candidate_id in selected:
                continue
            ids.append(candidate_id)
            selected.add(candidate_id)
            if len(ids) >= candidate_limit:
                break
    return _unique_strings(ids)[:candidate_limit]


def _candidate_in_stratified_scope(candidate: FormulaCandidate) -> bool:
    profile = _as_mapping(candidate.profile)
    return (
        str(profile.get("base")) in STRATIFIED_BASE_IDS
        and str(profile.get("learner")) in STRATIFIED_LEARNER_IDS
        and str(profile.get("cognate")) in STRATIFIED_COGNATE_IDS
        and str(profile.get("side_source")) in STRATIFIED_SIDE_SOURCE_IDS
        and str(profile.get("guard")) in STRATIFIED_GUARD_IDS
    )


def _coverage_score(
    candidate: FormulaCandidate,
    token_counts: Counter[str],
) -> float:
    return sum(1.0 / (1.0 + float(token_counts[token])) for token in _profile_tokens(candidate))


def _profile_tokens(candidate: FormulaCandidate) -> tuple[str, ...]:
    profile = _as_mapping(candidate.profile)
    tokens: list[str] = []
    for key in PROFILE_DIMENSIONS:
        value = str(profile.get(key) or "")
        if value:
            tokens.append(f"{key}:{value}")
    base = str(profile.get("base") or "")
    learner = str(profile.get("learner") or "")
    cognate = str(profile.get("cognate") or "")
    side_source = str(profile.get("side_source") or "")
    guard = str(profile.get("guard") or "")
    for label, first, second in (
        ("base+learner", base, learner),
        ("learner+cognate", learner, cognate),
        ("learner+side_source", learner, side_source),
        ("side_source+guard", side_source, guard),
    ):
        if first and second:
            tokens.append(f"{label}:{first}|{second}")
    return tuple(tokens)


def _profile_value_counts(candidates: Sequence[FormulaCandidate]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for dimension in PROFILE_DIMENSIONS:
        counter: Counter[str] = Counter()
        for candidate in candidates:
            value = str(_as_mapping(candidate.profile).get(dimension) or "")
            if value:
                counter[value] += 1
        summary[dimension] = {key: counter[key] for key in sorted(counter)}
    return summary


def _append_candidate_id(ids: list[str], value: object) -> None:
    text = str(value or "").strip()
    if text:
        ids.append(text)


def _identity(scores: np.ndarray, rows: Sequence[Mapping[str, object]]) -> np.ndarray:
    del rows
    return np.asarray(scores, dtype=np.float32)


def _minmax(scores: np.ndarray, rows: Sequence[Mapping[str, object]]) -> np.ndarray:
    del rows
    low = float(np.nanmin(scores))
    high = float(np.nanmax(scores))
    if not math.isfinite(low) or not math.isfinite(high) or high <= low:
        return np.asarray(scores, dtype=np.float32)
    return (scores - low) / (high - low)


def _power(gamma: float) -> Callable[[np.ndarray, Sequence[Mapping[str, object]]], np.ndarray]:
    def transform(scores: np.ndarray, rows: Sequence[Mapping[str, object]]) -> np.ndarray:
        del rows
        return np.power(np.clip(scores, 0.0, 1.0), gamma)

    return transform


def _minmax_power(
    gamma: float,
) -> Callable[[np.ndarray, Sequence[Mapping[str, object]]], np.ndarray]:
    def transform(scores: np.ndarray, rows: Sequence[Mapping[str, object]]) -> np.ndarray:
        return np.power(np.clip(_minmax(scores, rows), 0.0, 1.0), gamma)

    return transform


def _logistic(
    *,
    slope: float,
    center: float,
) -> Callable[[np.ndarray, Sequence[Mapping[str, object]]], np.ndarray]:
    def transform(scores: np.ndarray, rows: Sequence[Mapping[str, object]]) -> np.ndarray:
        del rows
        raw = _sigmoid(slope * (np.asarray(scores, dtype=np.float32) - center))
        low = _sigmoid(slope * (0.0 - center))
        high = _sigmoid(slope * (1.0 - center))
        if high <= low:
            return raw
        return (raw - low) / (high - low)

    return transform


def _affine(
    *,
    scale: float,
    offset: float,
) -> Callable[[np.ndarray, Sequence[Mapping[str, object]]], np.ndarray]:
    def transform(scores: np.ndarray, rows: Sequence[Mapping[str, object]]) -> np.ndarray:
        del rows
        return scale * np.asarray(scores, dtype=np.float32) + offset

    return transform


def _rank_uniform(scores: np.ndarray, rows: Sequence[Mapping[str, object]]) -> np.ndarray:
    order = _score_order(scores, rows)
    result = np.zeros(len(scores), dtype=np.float32)
    count = len(order)
    if count <= 0:
        return result
    for rank, index in enumerate(order):
        result[index] = (rank + 0.5) / count
    return result


def _rank_curriculum_curve(scores: np.ndarray, rows: Sequence[Mapping[str, object]]) -> np.ndarray:
    order = _score_order(scores, rows)
    result = np.zeros(len(scores), dtype=np.float32)
    bands = difficulty_bands(0.05)
    counts = target_band_counts(len(order), DEFAULT_TARGET_BAND_WEIGHTS)
    cursor = 0
    for band, count in zip(bands, counts):
        if count <= 0:
            continue
        width = band.end - band.start
        for offset, index in enumerate(order[cursor : cursor + count]):
            result[index] = min(1.0, band.start + (((offset + 0.5) / count) * width))
        cursor += count
    return result


def _score_order(scores: np.ndarray, rows: Sequence[Mapping[str, object]]) -> list[int]:
    return sorted(
        range(len(scores)),
        key=lambda index: (
            float(scores[index]),
            _rank(rows[index]),
            str(rows[index].get("lemma") or ""),
            index,
        ),
    )


def _score_summary(
    *,
    raw_scores: np.ndarray,
    warped_scores: np.ndarray,
) -> dict[str, object]:
    delta = warped_scores - raw_scores
    return {
        "raw_min": _round_float(float(np.nanmin(raw_scores))),
        "raw_max": _round_float(float(np.nanmax(raw_scores))),
        "warped_min": _round_float(float(np.nanmin(warped_scores))),
        "warped_max": _round_float(float(np.nanmax(warped_scores))),
        "mean_delta": _round_float(float(np.nanmean(delta))),
        "max_abs_delta": _round_float(float(np.nanmax(np.abs(delta)))),
    }


def _with_change_samples(
    record: Mapping[str, object],
    *,
    rows: Sequence[Mapping[str, object]],
    limit: int,
) -> dict[str, object]:
    detailed = dict(record)
    samples = _as_sequence(record.get("score_samples"))
    if samples:
        detailed["score_samples"] = list(samples)
        return detailed
    detailed["score_samples"] = []
    del rows, limit
    return detailed


def _largest_errors(
    row_pairs: Sequence[tuple[Mapping[str, object], Mapping[str, object], float]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    errors = []
    for label, row, observed in row_pairs:
        expected = _safe_float(label.get("expected_learner_difficulty"))
        if expected is None or not np.isfinite(observed):
            continue
        errors.append(
            {
                "lemma": label.get("lemma"),
                "expected": _round_float(expected),
                "observed": _round_float(observed),
                "abs_error": _round_float(abs(observed - expected)),
                "expected_candidate_state": label.get("expected_candidate_state"),
                "source_spalex_rank": label.get("source_spalex_rank"),
                "pos": row.get("pos"),
                "pos_bucket": row.get("pos_bucket"),
            }
        )
    return sorted(
        errors,
        key=lambda item: _safe_float(item.get("abs_error")) or -1.0,
        reverse=True,
    )[:limit]


def _compact_record(record: Mapping[str, object]) -> dict[str, object]:
    cal = _compact_metric(_as_mapping(record.get("calibration_primary")))
    holdout = _compact_metric(_as_mapping(record.get("holdout_primary")))
    deltas = _as_mapping(record.get("deltas_vs_raw_candidate"))
    return {
        "profile_key": record.get("profile_key"),
        "candidate_id": record.get("candidate_id"),
        "warp_id": record.get("warp_id"),
        "calibration_balanced": cal.get("balanced_score"),
        "holdout_balanced": holdout.get("balanced_score"),
        "calibration_mae": cal.get("mae"),
        "holdout_mae": holdout.get("mae"),
        "calibration_delta_vs_raw": deltas.get("calibration_balanced"),
        "holdout_delta_vs_raw": deltas.get("holdout_balanced"),
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


def _summary_row(label: str, row: Mapping[str, object]) -> str:
    return (
        f"| {label} | `{_escape(row.get('candidate_id'))}` | "
        f"`{_escape(row.get('warp_id'))}` | "
        f"{_fmt(row.get('calibration_balanced'))} | "
        f"{_fmt(row.get('holdout_balanced'))} | "
        f"{_fmt(row.get('calibration_mae'))} | "
        f"{_fmt(row.get('holdout_mae'))} | "
        f"{_fmt(row.get('calibration_delta_vs_raw'))} | "
        f"{_fmt(row.get('holdout_delta_vs_raw'))} |"
    )


def _leaderboard_row(row: Mapping[str, object]) -> str:
    compact = _compact_record(row)
    return _summary_row("", compact).replace("|  | ", "| ", 1)


def _profile_detail_lines(row: Mapping[str, object]) -> list[str]:
    compact = _compact_record(row)
    score_summary = _as_mapping(row.get("score_summary"))
    lines = [
        f"## `{_escape(compact.get('candidate_id'))}` / `{_escape(compact.get('warp_id'))}`",
        "",
        f"- Calibration balanced: `{_fmt(compact.get('calibration_balanced'))}`",
        f"- Holdout balanced: `{_fmt(compact.get('holdout_balanced'))}`",
        f"- Calibration MAE: `{_fmt(compact.get('calibration_mae'))}`",
        f"- Holdout MAE: `{_fmt(compact.get('holdout_mae'))}`",
        f"- Raw score span: `{_fmt(score_summary.get('raw_min'))}` to `{_fmt(score_summary.get('raw_max'))}`",
        f"- Warped score span: `{_fmt(score_summary.get('warped_min'))}` to `{_fmt(score_summary.get('warped_max'))}`",
        "",
        "Largest calibration errors:",
        "",
    ]
    lines.extend(_error_table(_as_mapping(row.get("calibration_primary")).get("largest_errors")))
    lines.extend(["", "Largest holdout errors:", ""])
    lines.extend(_error_table(_as_mapping(row.get("holdout_primary")).get("largest_errors")))
    lines.append("")
    return lines


def _error_table(rows: object) -> list[str]:
    lines = [
        "| Lemma | Expected | Observed | Abs Error | POS |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for raw in _as_sequence(rows)[:10]:
        row = _as_mapping(raw)
        lines.append(
            f"| `{_escape(row.get('lemma'))}` | {_fmt(row.get('expected'))} | "
            f"{_fmt(row.get('observed'))} | {_fmt(row.get('abs_error'))} | "
            f"`{_escape(row.get('pos_bucket') or row.get('pos'))}` |"
        )
    return lines


def _calibration_sort_key(row: Mapping[str, object]) -> tuple[float, float, float]:
    cal = _compact_metric(_as_mapping(row.get("calibration_primary")))
    holdout = _compact_metric(_as_mapping(row.get("holdout_primary")))
    return (
        _safe_float(cal.get("balanced_score")) or 0.0,
        -(_safe_float(cal.get("mae")) or 1.0),
        _safe_float(holdout.get("balanced_score")) or 0.0,
    )


def _holdout_guarded_sort_key(row: Mapping[str, object]) -> tuple[float, float, float]:
    cal = _compact_metric(_as_mapping(row.get("calibration_primary")))
    holdout = _compact_metric(_as_mapping(row.get("holdout_primary")))
    return (
        _safe_float(holdout.get("balanced_score")) or 0.0,
        _safe_float(cal.get("balanced_score")) or 0.0,
        -abs(
            (_safe_float(cal.get("balanced_score")) or 0.0)
            - (_safe_float(holdout.get("balanced_score")) or 0.0)
        ),
    )


def _calibration_mae_sort_key(row: Mapping[str, object]) -> tuple[float, float, float]:
    cal = _compact_metric(_as_mapping(row.get("calibration_primary")))
    holdout = _compact_metric(_as_mapping(row.get("holdout_primary")))
    return (
        _safe_float(cal.get("mae")) or 1.0,
        -(_safe_float(cal.get("balanced_score")) or 0.0),
        _safe_float(holdout.get("mae")) or 1.0,
    )


def _holdout_mae_sort_key(row: Mapping[str, object]) -> tuple[float, float, float]:
    cal = _compact_metric(_as_mapping(row.get("calibration_primary")))
    holdout = _compact_metric(_as_mapping(row.get("holdout_primary")))
    return (
        _safe_float(holdout.get("mae")) or 1.0,
        -(_safe_float(holdout.get("balanced_score")) or 0.0),
        _safe_float(cal.get("mae")) or 1.0,
    )


def _stable_sort_key(row: Mapping[str, object]) -> tuple[float, float, float]:
    cal = _compact_metric(_as_mapping(row.get("calibration_primary")))
    holdout = _compact_metric(_as_mapping(row.get("holdout_primary")))
    cal_score = _safe_float(cal.get("balanced_score")) or 0.0
    holdout_score = _safe_float(holdout.get("balanced_score")) or 0.0
    return (
        min(cal_score, holdout_score),
        (cal_score + holdout_score) / 2.0,
        -abs(cal_score - holdout_score),
    )


def _metric_delta(
    record: Mapping[str, object],
    current_key: str,
    baseline_key: str,
    metric_key: str,
) -> float | None:
    current = _safe_float(
        _as_mapping(_as_mapping(record.get(current_key)).get("scores")).get(metric_key)
    )
    baseline = _safe_float(
        _as_mapping(_as_mapping(record.get(baseline_key)).get("scores")).get(metric_key)
    )
    if current is None or baseline is None:
        return None
    return _round_float(current - baseline)


def _summary_delta(
    record: Mapping[str, object],
    current_key: str,
    baseline_key: str,
    metric_key: str,
) -> float | None:
    current = _safe_float(
        _as_mapping(_as_mapping(record.get(current_key)).get("metrics")).get(metric_key)
    )
    baseline = _safe_float(
        _as_mapping(_as_mapping(record.get(baseline_key)).get("metrics")).get(metric_key)
    )
    if current is None or baseline is None:
        return None
    return _round_float(current - baseline)


def _unique_records(
    rows: Sequence[Mapping[str, object]],
    *,
    key: str,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in rows:
        value = str(row.get(key) or "")
        if not value or value in seen:
            continue
        result.append(dict(row))
        seen.add(value)
    return result


def _unique_strings(values: Sequence[object]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        result.append(text)
        seen.add(text)
    return tuple(result)


def _rank(row: Mapping[str, object]) -> float:
    rank = _safe_float(row.get("spalex_rank"))
    return rank if rank is not None else 999999999.0


def _sigmoid(value: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-value))


def _slug(value: float) -> str:
    return f"{value:.2f}".replace(".", "")


def _signed_slug(value: float) -> str:
    prefix = "p" if value >= 0 else "m"
    return prefix + _slug(abs(value))


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "-"
    return f"{numeric:.3f}"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _round_float(value: object, digits: int = 6) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    return round(numeric, digits)


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
