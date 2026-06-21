#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
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
    DEFAULT_REVIEW_MARKDOWN,
    holdout_context_from_rows,
    parse_holdout_review_markdown,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _band_samples,
    _calibration_context,
    _difficulty_metrics,
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _summary_metrics,
    _target_curve_normalize,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_COMPONENT_MATRIX,
    GUARDRAIL_BEGINNER_CORE_MIN,
    GUARDRAIL_HIGH_TAIL_MIN,
    GUARDRAIL_PAIRWISE_MIN,
    family_parts,
    generate_candidates,
    raw_scores_for_candidate,
)


PAIR = "en-ja"
DEFAULT_V1_REPORT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_arbitration_en_ja_latest.json"
)
DEFAULT_CAP_REPORT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_arbitration_ordinary_refine_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_stitched_source_arbitration_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_stitched_source_arbitration_en_ja_latest.md"
)
SCORE_KEYS = (
    "balanced_score",
    "numeric_mae_score",
    "bucket_accuracy_score",
    "pairwise_order_score",
    "rank_correlation_score",
    "beginner_core_score",
    "beginner_broad_score",
    "upper_tail_score",
    "high_tail_score",
    "tail_separation_score",
    "default_decision_score",
)


@dataclass(frozen=True)
class StitchCandidate:
    candidate_id: str
    gate_signal: str
    gate_threshold: float
    gate_mode: str
    blend_strength: float
    blend_space: str
    normalize_after_blend: bool


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate v1/ordinary-cap stitched source-arbitration candidates "
            "for en-ja learner difficulty."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--review-markdown", type=Path, default=DEFAULT_REVIEW_MARKDOWN)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--v1-candidate-id", default=None)
    parser.add_argument("--cap-candidate-id", default=None)
    parser.add_argument("--leaderboard-limit", type=int, default=20)
    parser.add_argument("--detail-limit", type=int, default=20)
    parser.add_argument("--band-sample-size", type=int, default=6)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        review_markdown=_resolve_path(args.review_markdown),
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        v1_candidate_id=args.v1_candidate_id,
        cap_candidate_id=args.cap_candidate_id,
        leaderboard_limit=max(1, int(args.leaderboard_limit)),
        detail_limit=max(1, int(args.detail_limit)),
        band_sample_size=max(1, int(args.band_sample_size)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
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
    component_matrix_path: Path,
    calibration_matrix_path: Path,
    review_markdown: Path,
    v1_report_path: Path,
    cap_report_path: Path,
    v1_candidate_id: str | None,
    cap_candidate_id: str | None,
    leaderboard_limit: int,
    detail_limit: int,
    band_sample_size: int,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    calibration = np.load(calibration_matrix_path)
    view = ComponentView.from_npz(component)
    parts = family_parts(view)
    calibration_context = _calibration_context(calibration, component)
    holdout_rows = parse_holdout_review_markdown(review_markdown)
    holdout_context = holdout_context_from_rows(holdout_rows, component)
    v1_payload = _load_json(v1_report_path)
    cap_payload = _load_json(cap_report_path)
    resolved_v1_id = v1_candidate_id or _best_holdout_candidate_id(v1_payload)
    resolved_cap_id = cap_candidate_id or _best_holdout_candidate_id(cap_payload)
    v1_model = _candidate_by_id(resolved_v1_id)
    cap_model = _candidate_by_id(resolved_cap_id)
    target_positions = np.asarray(view.target_positions, dtype=np.float32)
    v1_raw = raw_scores_for_candidate(v1_model, view, parts=parts)
    cap_raw = raw_scores_for_candidate(cap_model, view, parts=parts)
    v1_normalized = _target_curve_normalize(v1_raw, target_positions=target_positions)
    cap_normalized = _target_curve_normalize(cap_raw, target_positions=target_positions)
    candidates = generate_stitch_candidates()
    rows = []
    for candidate in candidates:
        scores = stitched_scores(
            candidate,
            parts=parts,
            target_positions=target_positions,
            v1_raw=v1_raw,
            cap_raw=cap_raw,
            v1_normalized=v1_normalized,
            cap_normalized=cap_normalized,
        )
        rows.append(
            result_for_candidate(
                candidate,
                scores=scores,
                component=component,
                view=view,
                calibration_context=calibration_context,
                holdout_context=holdout_context,
                include_details=False,
                detail_limit=detail_limit,
                band_sample_size=band_sample_size,
            )
        )
    leaderboards = build_leaderboards(rows, limit=leaderboard_limit)
    detailed_results = []
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    for candidate_id in detailed_candidate_ids(leaderboards):
        candidate = candidate_by_id[candidate_id]
        scores = stitched_scores(
            candidate,
            parts=parts,
            target_positions=target_positions,
            v1_raw=v1_raw,
            cap_raw=cap_raw,
            v1_normalized=v1_normalized,
            cap_normalized=cap_normalized,
        )
        detailed_results.append(
            result_for_candidate(
                candidate,
                scores=scores,
                component=component,
                view=view,
                calibration_context=calibration_context,
                holdout_context=holdout_context,
                include_details=True,
                detail_limit=detail_limit,
                band_sample_size=band_sample_size,
            )
        )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Test conditional v1/ordinary-cap expert stitching after the "
                "cap impact audit showed beginner-core degradation."
            ),
            "shape": (
                "score = gate * v1 + (1 - gate) * ordinary_cap, where gate is "
                "computed only from source signals such as pedagogical coverage "
                "or commonness evidence."
            ),
            "guardrails": {
                "pairwise_order_score_min": GUARDRAIL_PAIRWISE_MIN,
                "beginner_core_score_min": GUARDRAIL_BEGINNER_CORE_MIN,
                "high_tail_score_min": GUARDRAIL_HIGH_TAIL_MIN,
            },
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "review_markdown": _repo_or_home_path(review_markdown),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "v1_candidate_id": resolved_v1_id,
            "cap_candidate_id": resolved_cap_id,
            "candidate_count": len(rows),
            "holdout_numeric_count": int(np.isfinite(holdout_context["expected_values"]).sum()),
        },
        "summary": {
            "best_holdout_balanced": leaderboards["holdout_balanced"][0]
            if leaderboards["holdout_balanced"]
            else {},
            "best_holdout_guardrail": leaderboards["holdout_guardrail"][0]
            if leaderboards["holdout_guardrail"]
            else {},
            "best_calibration_balanced": leaderboards["calibration_balanced"][0]
            if leaderboards["calibration_balanced"]
            else {},
            "v1_reference": reference_row("v1", v1_normalized, holdout_context),
            "cap_reference": reference_row("cap", cap_normalized, holdout_context),
        },
        "leaderboards": leaderboards,
        "candidate_results": rows,
        "detailed_results": detailed_results,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "review_markdown": review_markdown,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
            },
            code_paths={
                "source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_source_arbitration_en_ja.py",
                "holdout_eval": SCRIPT_DIR / "srs_learner_difficulty_holdout_eval_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "signal_sweep": SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def generate_stitch_candidates() -> tuple[StitchCandidate, ...]:
    candidates = []
    thresholds = {
        "pedagogical": (0.35, 0.50, 0.65, 0.80),
        "ped_min_ease": (0.55, 0.65, 0.75, 0.85),
        "ped_known": (0.50,),
        "ordinary_mean": (0.65, 0.75, 0.85),
        "freq_priority": (0.60, 0.70, 0.80),
        "priority": (0.50, 0.80),
    }
    for signal, signal_thresholds in thresholds.items():
        for threshold in signal_thresholds:
            for gate_mode in ("hard", "ramp"):
                for strength in (0.50, 0.75, 1.0):
                    for blend_space in ("raw", "normalized"):
                        normalize_options = (True,) if blend_space == "raw" else (False, True)
                        for normalize_after in normalize_options:
                            candidate_id = _stitch_id(
                                signal=signal,
                                threshold=threshold,
                                gate_mode=gate_mode,
                                strength=strength,
                                blend_space=blend_space,
                                normalize_after=normalize_after,
                            )
                            candidates.append(
                                StitchCandidate(
                                    candidate_id=candidate_id,
                                    gate_signal=signal,
                                    gate_threshold=threshold,
                                    gate_mode=gate_mode,
                                    blend_strength=strength,
                                    blend_space=blend_space,
                                    normalize_after_blend=normalize_after,
                                )
                            )
    return tuple(candidates)


def stitched_scores(
    candidate: StitchCandidate,
    *,
    parts: Mapping[str, object],
    target_positions: object,
    v1_raw: object,
    cap_raw: object,
    v1_normalized: object,
    cap_normalized: object,
) -> object:
    gate = stitch_gate(candidate, parts=parts)
    if candidate.blend_space == "raw":
        left = np.asarray(v1_raw, dtype=np.float32)
        right = np.asarray(cap_raw, dtype=np.float32)
    elif candidate.blend_space == "normalized":
        left = np.asarray(v1_normalized, dtype=np.float32)
        right = np.asarray(cap_normalized, dtype=np.float32)
    else:
        raise ValueError(f"Unsupported blend space: {candidate.blend_space}")
    blended = (gate * left) + ((1.0 - gate) * right)
    clipped = np.clip(blended, 0.0, 1.0).astype(np.float32)
    if candidate.normalize_after_blend:
        return _target_curve_normalize(clipped, target_positions=target_positions)
    return clipped


def stitch_gate(candidate: StitchCandidate, *, parts: Mapping[str, object]) -> object:
    signal = gate_signal(candidate.gate_signal, parts=parts)
    if candidate.gate_mode == "hard":
        gate = np.where(signal >= float(candidate.gate_threshold), 1.0, 0.0)
    elif candidate.gate_mode == "ramp":
        lower = float(candidate.gate_threshold)
        gate = np.clip((signal - lower) / max(1.0 - lower, 1e-6), 0.0, 1.0)
    else:
        raise ValueError(f"Unsupported gate mode: {candidate.gate_mode}")
    return (gate * float(candidate.blend_strength)).astype(np.float32)


def gate_signal(name: str, *, parts: Mapping[str, object]) -> object:
    if name == "pedagogical":
        return np.asarray(parts["ordinary_gate_pedagogical"], dtype=np.float32)
    if name == "ped_min_ease":
        ped = np.asarray(parts["ped_min"], dtype=np.float32)
        return np.nan_to_num(1.0 - ped, nan=0.0).astype(np.float32)
    if name == "ped_known":
        return np.asarray(parts["ped_conf"], dtype=np.float32)
    if name == "ordinary_mean":
        return np.asarray(parts["ordinary_gate_mean"], dtype=np.float32)
    if name == "freq_priority":
        return np.asarray(parts["ordinary_gate_freq_priority"], dtype=np.float32)
    if name == "priority":
        return np.asarray(parts["ordinary_gate_priority"], dtype=np.float32)
    raise ValueError(f"Unsupported stitch gate signal: {name}")


def result_for_candidate(
    candidate: StitchCandidate,
    *,
    scores: object,
    component: object,
    view: ComponentView,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
    include_details: bool,
    detail_limit: int,
    band_sample_size: int,
) -> dict[str, object]:
    calibration_metrics = metrics_for_context(scores, calibration_context)
    holdout_metrics = metrics_for_context(scores, holdout_context)
    row = {
        "candidate_id": candidate.candidate_id,
        "params": candidate_params(candidate),
        "calibration": {
            "scores": calibration_metrics["scores"],
            "metrics": _summary_metrics(calibration_metrics),
        },
        "holdout": {
            "scores": holdout_metrics["scores"],
            "metrics": _summary_metrics(holdout_metrics),
        },
        "generalization_delta": _rounded(
            _optional_float(holdout_metrics["scores"].get("balanced_score"))
            - _optional_float(calibration_metrics["scores"].get("balanced_score"))
            if _optional_float(holdout_metrics["scores"].get("balanced_score")) is not None
            and _optional_float(calibration_metrics["scores"].get("balanced_score")) is not None
            else None
        ),
    }
    if include_details:
        row["details"] = {
            "band_samples": _band_samples(
                scores,
                component=component,
                segment_ids=np.zeros(len(view.frequency), dtype=np.int64),
                expert_ids=(candidate.candidate_id,),
                per_band=band_sample_size,
            ),
            "holdout_errors": detail_rows(scores, holdout_context, limit=detail_limit),
            "calibration_errors": detail_rows(scores, calibration_context, limit=detail_limit),
            "holdout_wrong_pairwise_examples": holdout_metrics["pairwise_order"]["wrong_examples"][
                :detail_limit
            ],
        }
    return row


def metrics_for_context(normalized: object, context: Mapping[str, object]) -> dict[str, object]:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    observed = np.full(len(indices), np.nan, dtype=np.float32)
    valid = indices >= 0
    observed[valid] = np.asarray(normalized, dtype=np.float32)[indices[valid]]
    return _difficulty_metrics(
        expected_values=context["expected_values"],
        observed_values=observed,
        expected_bands=context["expected_bands"],
        expected_candidate_states=context.get("expected_candidate_states"),
        observed_candidate_states=context.get("observed_candidate_states"),
        labels=context["labels"],
    )


def build_leaderboards(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> dict[str, list[dict[str, object]]]:
    return {
        "holdout_balanced": leaderboard(
            rows,
            dataset="holdout",
            score_key="balanced_score",
            limit=limit,
        ),
        "holdout_guardrail": leaderboard(
            guardrail_rows(rows),
            dataset="holdout",
            score_key="balanced_score",
            limit=limit,
        ),
        "holdout_pairwise": leaderboard(
            rows,
            dataset="holdout",
            score_key="pairwise_order_score",
            limit=limit,
        ),
        "holdout_mae": leaderboard(
            rows,
            dataset="holdout",
            score_key="numeric_mae_score",
            limit=limit,
        ),
        "calibration_balanced": leaderboard(
            rows,
            dataset="calibration",
            score_key="balanced_score",
            limit=limit,
        ),
    }


def guardrail_rows(rows: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    filtered = []
    for row in rows:
        holdout = _mapping(_mapping(row.get("holdout")).get("scores"))
        if (_optional_float(holdout.get("pairwise_order_score")) or 0.0) < GUARDRAIL_PAIRWISE_MIN:
            continue
        if (
            _optional_float(holdout.get("beginner_core_score")) or 0.0
        ) < GUARDRAIL_BEGINNER_CORE_MIN:
            continue
        if (_optional_float(holdout.get("high_tail_score")) or 0.0) < GUARDRAIL_HIGH_TAIL_MIN:
            continue
        filtered.append(row)
    return filtered


def leaderboard(
    rows: Sequence[Mapping[str, object]],
    *,
    dataset: str,
    score_key: str,
    limit: int,
) -> list[dict[str, object]]:
    sortable = [row for row in rows if _score(row, dataset, score_key) is not None]
    return [
        compact_result(row)
        for row in sorted(
            sortable,
            key=lambda row: float(_score(row, dataset, score_key) or -1.0),
            reverse=True,
        )[:limit]
    ]


def reference_row(label: str, scores: object, context: Mapping[str, object]) -> dict[str, object]:
    metrics = metrics_for_context(scores, context)
    return {
        "candidate_id": label,
        "holdout_scores": metrics["scores"],
        "holdout_metrics": _summary_metrics(metrics),
    }


def compact_result(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "candidate_id": row.get("candidate_id"),
        "params": row.get("params"),
        "calibration_scores": _mapping(_mapping(row.get("calibration")).get("scores")),
        "holdout_scores": _mapping(_mapping(row.get("holdout")).get("scores")),
        "generalization_delta": row.get("generalization_delta"),
    }


def detail_rows(
    scores: object,
    context: Mapping[str, object],
    *,
    limit: int,
) -> list[dict[str, object]]:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    labels = [str(value) for value in context["labels"]]
    values = np.asarray(scores, dtype=np.float32)
    rows = []
    for offset, component_index in enumerate(indices):
        if component_index < 0 or not np.isfinite(expected[offset]):
            continue
        observed = float(values[int(component_index)])
        rows.append(
            {
                "label": labels[offset],
                "expected": _rounded(float(expected[offset])),
                "observed": _rounded(observed),
                "absolute_error": _rounded(abs(observed - float(expected[offset]))),
                "direction": "too_low" if observed < expected[offset] else "too_high",
            }
        )
    return sorted(rows, key=lambda row: float(row["absolute_error"] or 0.0), reverse=True)[:limit]


def detailed_candidate_ids(
    leaderboards: Mapping[str, Sequence[Mapping[str, object]]],
) -> tuple[str, ...]:
    ids: list[str] = []
    for key in ("holdout_balanced", "holdout_guardrail", "holdout_pairwise", "holdout_mae"):
        for row in leaderboards.get(key, ())[:5]:
            candidate_id = str(row.get("candidate_id") or "")
            if candidate_id:
                ids.append(candidate_id)
    return tuple(dict.fromkeys(ids))


def candidate_params(candidate: StitchCandidate) -> dict[str, object]:
    return {
        "gate_signal": candidate.gate_signal,
        "gate_threshold": _rounded(candidate.gate_threshold),
        "gate_mode": candidate.gate_mode,
        "blend_strength": _rounded(candidate.blend_strength),
        "blend_space": candidate.blend_space,
        "normalize_after_blend": candidate.normalize_after_blend,
    }


def _score(row: Mapping[str, object], dataset: str, score_key: str) -> float | None:
    return _optional_float(_mapping(_mapping(row.get(dataset)).get("scores")).get(score_key))


def _stitch_id(
    *,
    signal: str,
    threshold: float,
    gate_mode: str,
    strength: float,
    blend_space: str,
    normalize_after: bool,
) -> str:
    threshold_id = f"{threshold:g}".replace(".", "p")
    strength_id = f"{strength:g}".replace(".", "p")
    norm_id = "renorm" if normalize_after else "postnorm"
    return f"stitch_g{signal}_t{threshold_id}_{gate_mode}_s{strength_id}_{blend_space}_{norm_id}"


def _best_holdout_candidate_id(payload: Mapping[str, object]) -> str:
    candidate_id = _mapping(_mapping(payload.get("summary")).get("best_holdout_balanced")).get(
        "candidate_id"
    )
    if not candidate_id:
        raise ValueError("Could not find summary.best_holdout_balanced.candidate_id")
    return str(candidate_id)


def _candidate_by_id(candidate_id: str) -> object:
    for family in ("v1", "v2", "ordinary_refine"):
        for candidate in generate_candidates(candidate_family=family):
            if candidate.candidate_id == candidate_id:
                return candidate
    raise ValueError(f"Candidate not found in known source-arbitration families: {candidate_id}")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja Stitched Source-Arbitration Search",
        "",
        "Status: generated sidecar experiment",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "## Inputs",
        "",
        f"- v1 candidate: `{_escape(inputs.get('v1_candidate_id'))}`",
        f"- ordinary-cap candidate: `{_escape(inputs.get('cap_candidate_id'))}`",
        f"- Candidate count: `{_escape(inputs.get('candidate_count'))}`",
        "",
        "## Best Candidates",
        "",
        "| View | Candidate | Balanced | Pairwise | Beginner core | High tail | Params |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for label, row in (
        ("Best holdout", _mapping(summary.get("best_holdout_balanced"))),
        ("Best guardrail", _mapping(summary.get("best_holdout_guardrail"))),
        ("Best calibration", _mapping(summary.get("best_calibration_balanced"))),
    ):
        lines.append(_summary_row(label, row))
    lines.extend(["", "## Holdout Leaderboard", ""])
    lines.extend(
        _leaderboard_markdown(_mapping(report.get("leaderboards")).get("holdout_balanced"))
    )
    lines.extend(["", "## Guardrail Leaderboard", ""])
    lines.append(
        "Requires holdout pairwise >= "
        f"`{GUARDRAIL_PAIRWISE_MIN}`, beginner-core >= "
        f"`{GUARDRAIL_BEGINNER_CORE_MIN}`, and high-tail >= `{GUARDRAIL_HIGH_TAIL_MIN}`."
    )
    lines.extend([""])
    lines.extend(
        _leaderboard_markdown(_mapping(report.get("leaderboards")).get("holdout_guardrail"))
    )
    lines.extend(["", "## Detailed Samples", ""])
    for row in [
        dict(value) for value in report.get("detailed_results", ()) if isinstance(value, Mapping)
    ][:3]:
        lines.extend(_detailed_markdown(row))
    return "\n".join(lines).rstrip() + "\n"


def _summary_row(label: str, row: Mapping[str, object]) -> str:
    holdout = _mapping(row.get("holdout_scores"))
    return (
        f"| {_escape(label)} | `{_escape(row.get('candidate_id'))}` | "
        f"{_escape(holdout.get('balanced_score'))} | "
        f"{_escape(holdout.get('pairwise_order_score'))} | "
        f"{_escape(holdout.get('beginner_core_score'))} | "
        f"{_escape(holdout.get('high_tail_score'))} | "
        f"`{_escape(_compact_params(_mapping(row.get('params'))))}` |"
    )


def _leaderboard_markdown(value: object) -> list[str]:
    rows = (
        [dict(row) for row in value if isinstance(row, Mapping)]
        if isinstance(value, Sequence)
        else []
    )
    lines = [
        "| Rank | Candidate | Balanced | Pairwise | Beginner core | High tail | Params |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for rank, row in enumerate(rows[:20], start=1):
        holdout = _mapping(row.get("holdout_scores"))
        lines.append(
            f"| {rank} | `{_escape(row.get('candidate_id'))}` | "
            f"{_escape(holdout.get('balanced_score'))} | "
            f"{_escape(holdout.get('pairwise_order_score'))} | "
            f"{_escape(holdout.get('beginner_core_score'))} | "
            f"{_escape(holdout.get('high_tail_score'))} | "
            f"`{_escape(_compact_params(_mapping(row.get('params'))))}` |"
        )
    return lines


def _detailed_markdown(row: Mapping[str, object]) -> list[str]:
    details = _mapping(row.get("details"))
    lines = [
        f"### `{_escape(row.get('candidate_id'))}`",
        "",
        "Largest holdout errors:",
        "",
        "| Label | Expected | Observed | Error | Direction |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for error in [
        dict(value) for value in details.get("holdout_errors", ()) if isinstance(value, Mapping)
    ][:8]:
        lines.append(
            f"| {_escape(error.get('label'))} | {_escape(error.get('expected'))} | "
            f"{_escape(error.get('observed'))} | {_escape(error.get('absolute_error'))} | "
            f"{_escape(error.get('direction'))} |"
        )
    return lines


def _compact_params(params: Mapping[str, object]) -> str:
    return ",".join(
        f"{key}={params.get(key)}"
        for key in (
            "gate_signal",
            "gate_threshold",
            "gate_mode",
            "blend_strength",
            "blend_space",
            "normalize_after_blend",
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
