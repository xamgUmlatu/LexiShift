#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_holdout_eval_en_ja import (  # noqa: E402
    holdout_context_from_rows,
    parse_holdout_review_markdown,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _calibration_context,
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    family_parts,
    generate_candidates,
    normalized_scores_for_candidate,
)


PAIR = "en-ja"
DEFAULT_COMBO_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_arbitration_jlpt_exact_surface_inheritance_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_same_surface_floor_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_same_surface_floor_audit_en_ja_latest.md"
)
FOCUS_ROWS = (
    ("外国", "とつくに"),
    ("誘う", "いざなう"),
    ("辛い", "つらい"),
    ("明日", "あした"),
    ("明日", "あす"),
    ("開く", "あく"),
    ("僕", "しもべ"),
    ("女", "おみな"),
    ("下手", "げしゅ"),
    ("君", "きんじ"),
    ("外", "がい"),
    ("彼奴", "きゃつ"),
)
SCORE_KEYS = (
    "balanced_score",
    "numeric_mae_score",
    "bucket_accuracy_score",
    "pairwise_order_score",
    "beginner_core_score",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit protected same-surface rare-reading floor variants against the "
            "current en-ja source-arbitration difficulty candidate."
        )
    )
    parser.add_argument("--combo-json", type=Path, default=DEFAULT_COMBO_JSON)
    parser.add_argument("--low-score-cutoff", type=float, default=0.70)
    parser.add_argument("--blocker-cutoff", type=float, default=0.45)
    parser.add_argument("--movement-epsilon", type=float, default=0.0005)
    parser.add_argument("--detail-limit", type=int, default=16)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        combo_json=args.combo_json,
        low_score_cutoff=args.low_score_cutoff,
        blocker_cutoff=args.blocker_cutoff,
        movement_epsilon=args.movement_epsilon,
        detail_limit=args.detail_limit,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_report(
    *,
    combo_json: Path,
    low_score_cutoff: float,
    blocker_cutoff: float,
    movement_epsilon: float,
    detail_limit: int,
) -> dict[str, object]:
    combo_path = _resolve_repo_path(combo_json)
    combo = json.loads(combo_path.read_text(encoding="utf-8"))
    inputs = _mapping(combo.get("inputs"))
    component_matrix = _resolve_repo_path(Path(str(inputs["component_matrix"])))
    calibration_matrix = _resolve_repo_path(Path(str(inputs["calibration_matrix"])))
    review_markdown = _resolve_repo_path(Path(str(inputs["review_markdown"])))
    candidate_family = str(inputs.get("candidate_family") or "jlpt_exact_surface_inheritance_sweep")

    component = np.load(component_matrix)
    calibration = np.load(calibration_matrix)
    view = ComponentView.from_npz(component)
    parts = family_parts(view)
    calibration_context = _calibration_context(calibration, component)
    holdout_context = holdout_context_from_rows(
        parse_holdout_review_markdown(review_markdown),
        component,
    )

    candidate_rows = _rows(combo.get("candidate_results"))
    candidate_rows_by_id = {
        str(row.get("candidate_id") or ""): row
        for row in candidate_rows
        if str(row.get("candidate_id") or "")
    }
    candidates = generate_candidates(candidate_family=candidate_family)
    candidates_by_id = {candidate.candidate_id: candidate for candidate in candidates}

    baseline_id = _selected_baseline_id(combo)
    candidate_ids = _audit_candidate_ids(
        candidate_rows=candidate_rows,
        baseline_id=baseline_id,
        combo=combo,
    )
    score_arrays = {
        candidate_id: normalized_scores_for_candidate(
            candidates_by_id[candidate_id],
            view,
            parts=parts,
        )
        for candidate_id in candidate_ids
        if candidate_id in candidates_by_id
    }
    baseline_scores = np.asarray(score_arrays[baseline_id], dtype=np.float32)
    target_mask = _target_mask(
        parts=parts,
        baseline_scores=baseline_scores,
        low_score_cutoff=low_score_cutoff,
    )
    protected_exact_mask = _protected_exact_mask(parts=parts)
    blocker_mask = target_mask & (baseline_scores < float(blocker_cutoff))

    comparisons = [
        _candidate_comparison(
            candidate_id,
            baseline_id=baseline_id,
            candidate_row=candidate_rows_by_id.get(candidate_id, {}),
            scores=np.asarray(score_arrays[candidate_id], dtype=np.float32),
            baseline_scores=baseline_scores,
            target_mask=target_mask,
            blocker_mask=blocker_mask,
            protected_exact_mask=protected_exact_mask,
            movement_epsilon=movement_epsilon,
            calibration_context=calibration_context,
            holdout_context=holdout_context,
            detail_limit=detail_limit,
        )
        for candidate_id in candidate_ids
        if candidate_id in score_arrays
    ]
    focus_rows = _focus_rows(
        view=view,
        parts=parts,
        score_arrays=score_arrays,
        candidate_ids=candidate_ids,
    )
    target_examples = {
        candidate_id: _movement_examples(
            view=view,
            parts=parts,
            baseline_scores=baseline_scores,
            candidate_scores=np.asarray(score_arrays[candidate_id], dtype=np.float32),
            mask=target_mask,
            detail_limit=detail_limit,
        )
        for candidate_id in candidate_ids
        if candidate_id in score_arrays and candidate_id != baseline_id
    }
    protected_exact_examples = {
        candidate_id: _movement_examples(
            view=view,
            parts=parts,
            baseline_scores=baseline_scores,
            candidate_scores=np.asarray(score_arrays[candidate_id], dtype=np.float32),
            mask=protected_exact_mask,
            detail_limit=min(detail_limit, 10),
        )
        for candidate_id in candidate_ids
        if candidate_id in score_arrays and candidate_id != baseline_id
    }
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "method": {
            "purpose": (
                "Separate the protected family-only same-surface rare-reading "
                "floor from broader same-surface floors that can regress ordinary "
                "exact learner rows."
            ),
            "baseline_selection": "best holdout-balanced candidate from combo artifact",
            "target_population": (
                "Rows with same_surface_pedagogical_family_only_risk > 0 and "
                f"baseline score <= {low_score_cutoff}."
            ),
            "protected_exact_population": (
                "Rows with same_surface_rare_pollution_risk > 0 and "
                "jlpt_vocab_effective_exact_known > 0."
            ),
        },
        "inputs": {
            "combo_json": _repo_or_home_path(combo_path),
            "component_matrix": _repo_or_home_path(component_matrix),
            "calibration_matrix": _repo_or_home_path(calibration_matrix),
            "review_markdown": _repo_or_home_path(review_markdown),
            "candidate_family": candidate_family,
            "candidate_count": len(candidate_rows),
            "low_score_cutoff": _rounded(low_score_cutoff),
            "blocker_cutoff": _rounded(blocker_cutoff),
            "movement_epsilon": _rounded(movement_epsilon),
        },
        "population": {
            "row_count": int(len(baseline_scores)),
            "target_count": int(target_mask.sum()),
            "target_below_blocker_cutoff": int(blocker_mask.sum()),
            "protected_exact_count": int(protected_exact_mask.sum()),
        },
        "baseline_candidate_id": baseline_id,
        "candidate_ids": candidate_ids,
        "comparisons": comparisons,
        "focus_rows": focus_rows,
        "target_examples": target_examples,
        "protected_exact_examples": protected_exact_examples,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "combo_json": combo_path,
                "component_matrix": component_matrix,
                "calibration_matrix": calibration_matrix,
                "review_markdown": review_markdown,
            },
            code_paths={
                "source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_source_arbitration_en_ja.py",
                "signal_sweep": SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py",
                "holdout_eval": SCRIPT_DIR / "srs_learner_difficulty_holdout_eval_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def _resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _selected_baseline_id(combo: Mapping[str, object]) -> str:
    leaderboards = _mapping(combo.get("leaderboards"))
    holdout = _rows(leaderboards.get("holdout_balanced"))
    if holdout:
        return str(holdout[0].get("candidate_id") or "")
    rows = _rows(combo.get("candidate_results"))
    if not rows:
        raise ValueError("No candidate rows available")
    return max(
        rows,
        key=lambda row: float(
            _mapping(_mapping(row.get("holdout")).get("scores")).get("balanced_score") or 0.0
        ),
    )["candidate_id"]


def _audit_candidate_ids(
    *,
    candidate_rows: Sequence[Mapping[str, object]],
    baseline_id: str,
    combo: Mapping[str, object],
) -> list[str]:
    ids = [baseline_id]
    family_only = [
        row
        for row in candidate_rows
        if _is_protected_family_floor_candidate(_mapping(row.get("params")))
    ]
    family_only = sorted(
        family_only,
        key=lambda row: float(
            _mapping(row.get("params")).get("same_surface_secondary_floor") or 0.0
        ),
    )
    ids.extend(str(row.get("candidate_id") or "") for row in family_only)
    calibration = _rows(_mapping(combo.get("leaderboards")).get("calibration_balanced"))
    if calibration:
        ids.append(str(calibration[0].get("candidate_id") or ""))
    return [candidate_id for candidate_id in dict.fromkeys(ids) if candidate_id]


def _is_protected_family_floor_candidate(params: Mapping[str, object]) -> bool:
    return (
        str(params.get("same_surface_floor_mode") or "") == "none"
        and (_optional_float(params.get("same_surface_floor")) or 0.0) == 0.0
        and str(params.get("same_surface_secondary_floor_mode") or "")
        in {
            "pedagogical_family_only_rare_pollution",
            "pedagogical_family_only_rare_pollution_unprotected_exact",
        }
        and str(params.get("same_surface_source_attenuation_mode") or "") == "none"
        and (_optional_float(params.get("jlpt_exact_blend")) or 0.0) == 0.0
        and str(params.get("jlpt_exact_blend_gate_mode") or "") == "none"
        and (_optional_float(params.get("jlpt_inherited_penalty")) or 0.0) == 0.0
        and str(params.get("jlpt_inherited_penalty_mode") or "") == "none"
    )


def _target_mask(
    *,
    parts: Mapping[str, object],
    baseline_scores: object,
    low_score_cutoff: float,
) -> object:
    return (
        np.asarray(parts["same_surface_pedagogical_family_only_risk"], dtype=np.float32) > 0.0
    ) & (np.asarray(baseline_scores, dtype=np.float32) <= float(low_score_cutoff))


def _protected_exact_mask(*, parts: Mapping[str, object]) -> object:
    return (np.asarray(parts["same_surface_rare_pollution_risk"], dtype=np.float32) > 0.0) & (
        np.asarray(parts["jlpt_vocab_effective_exact_known"], dtype=np.float32) > 0.0
    )


def _candidate_comparison(
    candidate_id: str,
    *,
    baseline_id: str,
    candidate_row: Mapping[str, object],
    scores: object,
    baseline_scores: object,
    target_mask: object,
    blocker_mask: object,
    protected_exact_mask: object,
    movement_epsilon: float,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
    detail_limit: int,
) -> dict[str, object]:
    scores_arr = np.asarray(scores, dtype=np.float32)
    baseline_arr = np.asarray(baseline_scores, dtype=np.float32)
    delta = scores_arr - baseline_arr
    return {
        "candidate_id": candidate_id,
        "is_baseline": candidate_id == baseline_id,
        "params": _compact_params(_mapping(candidate_row.get("params"))),
        "calibration_scores": _score_summary(candidate_row, dataset="calibration"),
        "holdout_scores": _score_summary(candidate_row, dataset="holdout"),
        "global_delta_vs_baseline": _global_delta_summary(delta, movement_epsilon),
        "target_delta_vs_baseline": _masked_delta_summary(
            delta,
            scores_arr,
            baseline_arr,
            target_mask,
            movement_epsilon,
        ),
        "target_below_blocker_cutoff_after": int((blocker_mask & (scores_arr < 0.45)).sum()),
        "protected_exact_delta_vs_baseline": _masked_delta_summary(
            delta,
            scores_arr,
            baseline_arr,
            protected_exact_mask,
            movement_epsilon,
        ),
        "calibration_labeled_delta": _labeled_delta_summary(
            scores_arr,
            baseline_arr,
            calibration_context,
            detail_limit=detail_limit,
        ),
        "holdout_labeled_delta": _labeled_delta_summary(
            scores_arr,
            baseline_arr,
            holdout_context,
            detail_limit=detail_limit,
        ),
    }


def _compact_params(params: Mapping[str, object]) -> dict[str, object]:
    return {
        key: params.get(key)
        for key in (
            "same_surface_floor",
            "same_surface_floor_mode",
            "same_surface_secondary_floor",
            "same_surface_secondary_floor_mode",
            "jlpt_exact_blend",
            "jlpt_exact_blend_gate_mode",
            "jlpt_inherited_penalty",
            "jlpt_inherited_penalty_mode",
        )
        if key in params
    }


def _score_summary(row: Mapping[str, object], *, dataset: str) -> dict[str, object]:
    scores = _mapping(_mapping(row.get(dataset)).get("scores"))
    return {key: _rounded(scores.get(key)) for key in SCORE_KEYS if key in scores}


def _global_delta_summary(delta: object, movement_epsilon: float) -> dict[str, object]:
    delta_arr = np.asarray(delta, dtype=np.float32)
    moved = np.abs(delta_arr) > float(movement_epsilon)
    return {
        "moved_count": int(moved.sum()),
        "mean_delta": _rounded(float(delta_arr.mean())),
        "mean_abs_delta": _rounded(float(np.abs(delta_arr).mean())),
        "max_raise": _rounded(float(delta_arr.max())),
        "max_lower": _rounded(float(delta_arr.min())),
    }


def _masked_delta_summary(
    delta: object,
    scores: object,
    baseline_scores: object,
    mask: object,
    movement_epsilon: float,
) -> dict[str, object]:
    mask_arr = np.asarray(mask, dtype=bool)
    if not bool(mask_arr.any()):
        return {
            "count": 0,
            "moved_count": 0,
            "mean_delta": None,
            "mean_abs_delta": None,
            "max_raise": None,
            "max_lower": None,
            "below_0_45_before": 0,
            "below_0_45_after": 0,
            "below_0_50_before": 0,
            "below_0_50_after": 0,
        }
    delta_arr = np.asarray(delta, dtype=np.float32)[mask_arr]
    scores_arr = np.asarray(scores, dtype=np.float32)[mask_arr]
    baseline_arr = np.asarray(baseline_scores, dtype=np.float32)[mask_arr]
    moved = np.abs(delta_arr) > float(movement_epsilon)
    return {
        "count": int(mask_arr.sum()),
        "moved_count": int(moved.sum()),
        "mean_delta": _rounded(float(delta_arr.mean())),
        "mean_abs_delta": _rounded(float(np.abs(delta_arr).mean())),
        "max_raise": _rounded(float(delta_arr.max())),
        "max_lower": _rounded(float(delta_arr.min())),
        "below_0_45_before": int((baseline_arr < 0.45).sum()),
        "below_0_45_after": int((scores_arr < 0.45).sum()),
        "below_0_50_before": int((baseline_arr < 0.50).sum()),
        "below_0_50_after": int((scores_arr < 0.50).sum()),
    }


def _labeled_delta_summary(
    scores: object,
    baseline_scores: object,
    context: Mapping[str, object],
    *,
    detail_limit: int,
) -> dict[str, object]:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    labels = [str(label) for label in context["labels"]]
    valid = (indices >= 0) & np.isfinite(expected)
    if not bool(valid.any()):
        return {"count": 0, "mean_error_delta": None, "regressions": [], "improvements": []}
    scores_arr = np.asarray(scores, dtype=np.float32)
    baseline_arr = np.asarray(baseline_scores, dtype=np.float32)
    rows = []
    for position in np.where(valid)[0]:
        index = int(indices[position])
        baseline = float(baseline_arr[index])
        candidate = float(scores_arr[index])
        expect = float(expected[position])
        baseline_error = abs(baseline - expect)
        candidate_error = abs(candidate - expect)
        rows.append(
            {
                "label": labels[position],
                "expected": _rounded(expect),
                "baseline": _rounded(baseline),
                "candidate": _rounded(candidate),
                "baseline_error": _rounded(baseline_error),
                "candidate_error": _rounded(candidate_error),
                "error_delta": _rounded(candidate_error - baseline_error),
            }
        )
    deltas = np.asarray([float(row["error_delta"]) for row in rows], dtype=np.float32)
    regressions = sorted(rows, key=lambda row: float(row["error_delta"]), reverse=True)
    improvements = sorted(rows, key=lambda row: float(row["error_delta"]))
    return {
        "count": len(rows),
        "mean_error_delta": _rounded(float(deltas.mean())),
        "regression_count": int((deltas > 0.0005).sum()),
        "improvement_count": int((deltas < -0.0005).sum()),
        "regressions": regressions[:detail_limit],
        "improvements": improvements[:detail_limit],
    }


def _movement_examples(
    *,
    view: ComponentView,
    parts: Mapping[str, object],
    baseline_scores: object,
    candidate_scores: object,
    mask: object,
    detail_limit: int,
) -> list[dict[str, object]]:
    mask_arr = np.asarray(mask, dtype=bool)
    if not bool(mask_arr.any()):
        return []
    baseline_arr = np.asarray(baseline_scores, dtype=np.float32)
    candidate_arr = np.asarray(candidate_scores, dtype=np.float32)
    delta = candidate_arr - baseline_arr
    indices = np.where(mask_arr)[0]
    ranked = sorted(indices, key=lambda index: float(delta[index]), reverse=True)
    return [
        _row_snapshot(
            int(index),
            view=view,
            parts=parts,
            baseline_score=float(baseline_arr[index]),
            candidate_score=float(candidate_arr[index]),
        )
        for index in ranked[:detail_limit]
        if abs(float(delta[index])) > 0.0005
    ]


def _focus_rows(
    *,
    view: ComponentView,
    parts: Mapping[str, object],
    score_arrays: Mapping[str, object],
    candidate_ids: Sequence[str],
) -> list[dict[str, object]]:
    by_pair: dict[tuple[str, str], int] = {}
    for index, (lemma, reading) in enumerate(zip(view.lemmas, view.readings, strict=False)):
        by_pair[(str(lemma), str(reading))] = index
    rows = []
    for lemma, reading in FOCUS_ROWS:
        index = by_pair.get((lemma, reading))
        if index is None:
            rows.append({"label": f"{lemma}/{reading}", "available": False})
            continue
        snapshot = _row_snapshot(
            index,
            view=view,
            parts=parts,
            baseline_score=None,
            candidate_score=None,
        )
        snapshot["available"] = True
        snapshot["scores"] = {
            candidate_id: _rounded(float(np.asarray(score_arrays[candidate_id])[index]))
            for candidate_id in candidate_ids
            if candidate_id in score_arrays
        }
        rows.append(snapshot)
    return rows


def _row_snapshot(
    index: int,
    *,
    view: ComponentView,
    parts: Mapping[str, object],
    baseline_score: float | None,
    candidate_score: float | None,
) -> dict[str, object]:
    row = {
        "label": f"{str(view.lemmas[index])}/{str(view.readings[index])}",
        "lemma": str(view.lemmas[index]),
        "reading": str(view.readings[index]),
        "candidate_state": str(view.candidate_states[index]),
        "core_rank": _rounded(float(view.core_ranks[index]))
        if np.isfinite(view.core_ranks[index])
        else None,
        "same_surface_pedagogical_family_only_risk": _part(
            parts, "same_surface_pedagogical_family_only_risk", index
        ),
        "same_surface_pedagogical_family_only_unprotected_exact_risk": _part(
            parts,
            "same_surface_pedagogical_family_only_unprotected_exact_risk",
            index,
        ),
        "same_surface_rare_pollution_risk": _part(parts, "same_surface_rare_pollution_risk", index),
        "same_surface_exact_commonness": _part(parts, "same_surface_exact_commonness", index),
        "same_surface_rank_disadvantage": _part(parts, "same_surface_rank_disadvantage", index),
        "jlpt_vocab_known": _part(parts, "jlpt_vocab_known", index),
        "jlpt_vocab_surface_known": _part(parts, "jlpt_vocab_surface_known", index),
        "jlpt_vocab_effective_exact_known": _part(parts, "jlpt_vocab_effective_exact_known", index),
        "jlpt_vocab_family_only_known": _part(parts, "jlpt_vocab_family_only_known", index),
        "lesson_vocab_known": _part(parts, "lesson_vocab_known", index),
        "reading_form_source_strength": _part(parts, "reading_form_source_strength", index),
        "rare_reading_form_strength": _part(parts, "rare_reading_form_strength", index),
    }
    if baseline_score is not None:
        row["baseline"] = _rounded(baseline_score)
    if candidate_score is not None:
        row["candidate"] = _rounded(candidate_score)
        row["delta"] = _rounded(candidate_score - float(baseline_score or 0.0))
    return row


def _part(parts: Mapping[str, object], key: str, index: int) -> object:
    value = np.asarray(parts[key], dtype=np.float32)[index]
    return _rounded(float(value))


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# SRS Learner Difficulty Same-Surface Floor Audit (en-ja)",
        "",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "## Purpose",
        "",
        str(_mapping(report.get("method")).get("purpose")),
        "",
        "## Inputs",
        "",
    ]
    inputs = _mapping(report.get("inputs"))
    for key in (
        "combo_json",
        "component_matrix",
        "calibration_matrix",
        "review_markdown",
        "candidate_family",
        "candidate_count",
        "low_score_cutoff",
        "blocker_cutoff",
    ):
        lines.append(f"- {key}: `{_escape(inputs.get(key))}`")
    population = _mapping(report.get("population"))
    lines.extend(
        [
            "",
            "## Population",
            "",
            f"- Total matrix rows: `{_escape(population.get('row_count'))}`",
            f"- Protected family-only rare-reading target rows: `{_escape(population.get('target_count'))}`",
            f"- Target rows below blocker cutoff: `{_escape(population.get('target_below_blocker_cutoff'))}`",
            f"- Effective-exact protected same-surface rows: `{_escape(population.get('protected_exact_count'))}`",
            "",
            "## Candidate Metrics",
            "",
            "| Candidate | s2 floor | primary floor | exact blend | inherited penalty | Holdout balanced | Holdout MAE score | Holdout pairwise | Calibration balanced |",
            "| --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _rows(report.get("comparisons")):
        params = _mapping(row.get("params"))
        holdout = _mapping(row.get("holdout_scores"))
        calibration = _mapping(row.get("calibration_scores"))
        label = "baseline" if row.get("is_baseline") else _short_candidate_label(row)
        lines.append(
            "| "
            f"`{_escape(label)}` | "
            f"{_escape(params.get('same_surface_secondary_floor'))} | "
            f"`{_escape(params.get('same_surface_floor_mode'))}` | "
            f"`{_escape(params.get('jlpt_exact_blend_gate_mode'))}:{_escape(params.get('jlpt_exact_blend'))}` | "
            f"`{_escape(params.get('jlpt_inherited_penalty_mode'))}:{_escape(params.get('jlpt_inherited_penalty'))}` | "
            f"{_escape(holdout.get('balanced_score'))} | "
            f"{_escape(holdout.get('numeric_mae_score'))} | "
            f"{_escape(holdout.get('pairwise_order_score'))} | "
            f"{_escape(calibration.get('balanced_score'))} |"
        )
    lines.extend(
        [
            "",
            "## Movement Summary",
            "",
            "| Candidate | Target moved | Target mean delta | Target below 0.45 after | Protected-exact moved | Global mean abs delta |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _rows(report.get("comparisons")):
        label = "baseline" if row.get("is_baseline") else _short_candidate_label(row)
        target = _mapping(row.get("target_delta_vs_baseline"))
        protected = _mapping(row.get("protected_exact_delta_vs_baseline"))
        global_delta = _mapping(row.get("global_delta_vs_baseline"))
        lines.append(
            "| "
            f"`{_escape(label)}` | "
            f"{_escape(target.get('moved_count'))} | "
            f"{_escape(target.get('mean_delta'))} | "
            f"{_escape(target.get('below_0_45_after'))} | "
            f"{_escape(protected.get('moved_count'))} | "
            f"{_escape(global_delta.get('mean_abs_delta'))} |"
        )
    lines.extend(_focus_markdown(report))
    lines.extend(_labeled_delta_markdown(report, context_key="holdout_labeled_delta"))
    lines.extend(_target_examples_markdown(report))
    return "\n".join(lines) + "\n"


def _short_candidate_label(row: Mapping[str, object]) -> str:
    params = _mapping(row.get("params"))
    secondary = params.get("same_surface_secondary_floor")
    primary = params.get("same_surface_floor_mode")
    exact = params.get("jlpt_exact_blend_gate_mode")
    inherited = params.get("jlpt_inherited_penalty_mode")
    if primary == "none" and exact == "none" and inherited == "none":
        mode = str(params.get("same_surface_secondary_floor_mode") or "")
        if mode.endswith("unprotected_exact"):
            return f"exact_protected_floor_{secondary}"
        return f"protected_family_floor_{secondary}"
    return f"mixed_{secondary}_{primary}_{exact}_{inherited}"


def _focus_markdown(report: Mapping[str, object]) -> list[str]:
    candidate_ids = [str(value) for value in report.get("candidate_ids") or []]
    header_scores = " | ".join(
        f"`{_escape(_compact_candidate_heading(value))}`" for value in candidate_ids
    )
    score_rule = " | ".join("---:" for _value in candidate_ids)
    lines = [
        "",
        "## Focus Rows",
        "",
        f"| Row | Family risk | Exact-protected risk | Exact known | Exact common | {header_scores} |",
        f"| --- | ---: | ---: | ---: | ---: | {score_rule} |",
    ]
    for row in _rows(report.get("focus_rows")):
        scores = _mapping(row.get("scores"))
        score_cells = " | ".join(
            _escape(scores.get(candidate_id)) for candidate_id in candidate_ids
        )
        lines.append(
            "| "
            f"`{_escape(row.get('label'))}` | "
            f"{_escape(row.get('same_surface_pedagogical_family_only_risk'))} | "
            f"{_escape(row.get('same_surface_pedagogical_family_only_unprotected_exact_risk'))} | "
            f"{_escape(row.get('jlpt_vocab_effective_exact_known'))} | "
            f"{_escape(row.get('same_surface_exact_commonness'))} | "
            f"{score_cells} |"
        )
    return lines


def _compact_candidate_heading(candidate_id: str) -> str:
    suffix = "xprot" if "unprotected_exact" in candidate_id else ""
    if "s2f0p62_s2fm" in candidate_id and "ssf0_ssfmnone" in candidate_id:
        return f"s2f0.62{suffix}"
    if "s2f0p5_s2fm" in candidate_id and "ssf0_ssfmnone" in candidate_id:
        return f"s2f0.50{suffix}"
    if "s2f0p42_s2fm" in candidate_id and "ssf0_ssfmnone" in candidate_id:
        return f"s2f0.42{suffix}"
    if "s2f0p74_s2fm" in candidate_id and "ssf0_ssfmnone" in candidate_id:
        return f"s2f0.74{suffix}"
    if "s2f0p34_s2fm" in candidate_id and "ssf0_ssfmnone" in candidate_id:
        return "s2f0.34"
    if "s2f0p24_s2fm" in candidate_id and "ssf0_ssfmnone" in candidate_id:
        return "s2f0.24"
    if "s2f0_s2fmnone" in candidate_id:
        return "s2f0"
    return "mixed"


def _labeled_delta_markdown(report: Mapping[str, object], *, context_key: str) -> list[str]:
    lines = [
        "",
        "## Largest Holdout Label Regressions",
        "",
    ]
    for row in _rows(report.get("comparisons")):
        if row.get("is_baseline"):
            continue
        label = _short_candidate_label(row)
        delta = _mapping(row.get(context_key))
        lines.extend(
            [
                f"### `{_escape(label)}`",
                "",
                f"- Mean error delta: `{_escape(delta.get('mean_error_delta'))}`",
                f"- Regression count: `{_escape(delta.get('regression_count'))}`",
                f"- Improvement count: `{_escape(delta.get('improvement_count'))}`",
                "",
                "| Row | Expected | Baseline | Candidate | Error delta |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for item in _rows(delta.get("regressions"))[:8]:
            lines.append(
                "| "
                f"`{_escape(item.get('label'))}` | "
                f"{_escape(item.get('expected'))} | "
                f"{_escape(item.get('baseline'))} | "
                f"{_escape(item.get('candidate'))} | "
                f"{_escape(item.get('error_delta'))} |"
            )
        lines.append("")
    return lines


def _target_examples_markdown(report: Mapping[str, object]) -> list[str]:
    examples = _mapping(report.get("target_examples"))
    lines = [
        "",
        "## Largest Target Raises",
        "",
    ]
    for candidate_id, rows in examples.items():
        lines.extend(
            [
                f"### `{_escape(_compact_candidate_heading(str(candidate_id)))}`",
                "",
                "| Row | Baseline | Candidate | Delta | Family risk | Exact known | Exact common |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in _rows(rows)[:12]:
            lines.append(
                "| "
                f"`{_escape(row.get('label'))}` | "
                f"{_escape(row.get('baseline'))} | "
                f"{_escape(row.get('candidate'))} | "
                f"{_escape(row.get('delta'))} | "
                f"{_escape(row.get('same_surface_pedagogical_family_only_risk'))} | "
                f"{_escape(row.get('jlpt_vocab_effective_exact_known'))} | "
                f"{_escape(row.get('same_surface_exact_commonness'))} |"
            )
        lines.append("")
    return lines


def _rows(value: object) -> list[dict[str, object]]:
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, Mapping)]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
