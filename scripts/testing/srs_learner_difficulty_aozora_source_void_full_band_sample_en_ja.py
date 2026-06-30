#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_aozora_source_void_tiebreak_bakeoff_en_ja import (  # noqa: E402
    _apply_tiebreak_variant,
    _tiebreak_evidence,
    _tiebreak_variant_specs,
)
from srs_learner_difficulty_aozora_tail_bakeoff_en_ja import (  # noqa: E402
    DEFAULT_AOZORA_SQLITE,
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_SOURCE_ARBITRATION_JSON,
    DEFAULT_VALIDATION_JSON,
    _aozora_feature_arrays,
    _component_signal_arrays,
    _current_scores,
    _load_json,
    _sample_row,
    _selected_candidate_metadata,
    ComponentView,
    _view_with_target_curve_override,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
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


PAIR = "en-ja"
DEFAULT_VARIANT_ID = (
    "aozgraded_gl088_gu098_sf08_gp2_mv005_aw125_vw0_ob0_hb0_ab0_db0_lf05"
    "_tr1000_wr30_cmwork_heavy_sp075_pwc8_adw0"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_source_void_full_band_sample_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_source_void_full_band_sample_en_ja_latest.md"
)
BAND_WIDTH = 0.05


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate full 0.00-1.00 qualitative band samples after applying a "
            "selected Aozora source-void tiebreaker variant. This is a sidecar "
            "diagnostic and does not change scorer behavior."
        )
    )
    parser.add_argument(
        "--source-arbitration-json", type=Path, default=DEFAULT_SOURCE_ARBITRATION_JSON
    )
    parser.add_argument("--component-matrix", type=Path, default=None)
    parser.add_argument("--candidate-id", default="")
    parser.add_argument("--candidate-family", default="")
    parser.add_argument(
        "--target-curve-override",
        choices=("component", "warp_p60_g155"),
        default="",
    )
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--aozora-sqlite", type=Path, default=DEFAULT_AOZORA_SQLITE)
    parser.add_argument("--variant-id", default=DEFAULT_VARIANT_ID)
    parser.add_argument("--sample-per-band", type=int, default=18)
    parser.add_argument("--move-limit", type=int, default=60)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        source_arbitration_json=_resolve_path(args.source_arbitration_json),
        component_matrix_path=(
            _resolve_path(args.component_matrix) if args.component_matrix else None
        ),
        candidate_id=str(args.candidate_id or ""),
        candidate_family=str(args.candidate_family or ""),
        target_curve_override=str(args.target_curve_override or ""),
        calibration_json=_resolve_path(args.calibration_json),
        holdout_json=_resolve_path(args.holdout_json),
        validation_json=_resolve_path(args.validation_json),
        aozora_sqlite=_resolve_path(args.aozora_sqlite),
        variant_id=str(args.variant_id or DEFAULT_VARIANT_ID),
        sample_per_band=max(1, int(args.sample_per_band)),
        move_limit=max(1, int(args.move_limit)),
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
    source_arbitration_json: Path,
    component_matrix_path: Path | None,
    candidate_id: str,
    candidate_family: str,
    target_curve_override: str,
    calibration_json: Path,
    holdout_json: Path,
    validation_json: Path,
    aozora_sqlite: Path,
    variant_id: str,
    sample_per_band: int,
    move_limit: int,
) -> dict[str, Any]:
    source_report = _load_json(source_arbitration_json)
    selected = _selected_candidate_metadata(
        source_report,
        candidate_id=candidate_id,
        candidate_family=candidate_family,
        target_curve_override=target_curve_override,
        component_matrix_path=component_matrix_path,
    )
    component_matrix = _resolve_path(Path(str(selected["component_matrix"])))
    component = np.load(component_matrix)
    view = _view_with_target_curve_override(
        ComponentView.from_npz(component),
        target_curve_override=str(selected["target_curve_override"]),
    )
    current_scores = _current_scores(view=view, selected=selected)
    aozora = _aozora_feature_arrays(view=view, aozora_sqlite=aozora_sqlite)
    component_signals = _component_signal_arrays(view)
    variant = _variant_by_id(variant_id)
    scores = _apply_tiebreak_variant(
        current_scores=current_scores,
        evidence=_tiebreak_evidence(
            current_scores=current_scores,
            target_positions=np.asarray(view.target_positions, dtype=np.float32),
            aozora=aozora,
            component_signals=component_signals,
        ),
        variant=variant,
    )
    labels = _label_lookup(
        calibration_json=calibration_json,
        holdout_json=holdout_json,
        validation_json=validation_json,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "model_behavior_changed": False,
        "method": {
            "purpose": (
                "Full thin-band qualitative review after applying the selected "
                "capped Aozora source-void tiebreaker as a sidecar second pass."
            ),
            "candidate_id": selected["candidate_id"],
            "candidate_family": selected["candidate_family"],
            "target_curve_override": selected["target_curve_override"],
            "variant_id": variant_id,
            "formula": (
                "score = current + eligible(current >= score_floor) * "
                "smoothstep(gate_lower, gate_upper, current)^gate_power * max_move "
                "* (void_weight * source_void - attested_weight * credible_attestation), "
                "clipped to +/- max_move. Bands are sampled from the post-nudge score."
            ),
        },
        "inputs": {
            "source_arbitration_json": _repo_or_home_path(source_arbitration_json),
            "component_matrix": _repo_or_home_path(component_matrix),
            "calibration_json": _repo_or_home_path(calibration_json),
            "holdout_json": _repo_or_home_path(holdout_json),
            "validation_json": _repo_or_home_path(validation_json),
            "aozora_sqlite": _repo_or_home_path(aozora_sqlite),
            "component_count": int(len(scores)),
            "sample_per_band": int(sample_per_band),
            "move_limit": int(move_limit),
        },
        "variant": dict(variant),
        "movement_summary": _movement_summary(scores=scores, current_scores=current_scores),
        "band_counts": _band_counts(scores=scores, current_scores=current_scores),
        "band_samples": _band_samples(
            scores=scores,
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            labels=labels,
            per_band=sample_per_band,
        ),
        "largest_down_moves": _move_samples(
            scores=scores,
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            labels=labels,
            direction="down",
            limit=move_limit,
        ),
        "largest_up_moves": _move_samples(
            scores=scores,
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            labels=labels,
            direction="up",
            limit=move_limit,
        ),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "source_arbitration_json": source_arbitration_json,
                "component_matrix": component_matrix,
                "calibration_json": calibration_json,
                "holdout_json": holdout_json,
                "validation_json": validation_json,
                "aozora_sqlite": aozora_sqlite,
            },
            code_paths={
                **_srs_difficulty_code_paths(),
                "source_arbitration": (
                    SCRIPT_DIR / "srs_learner_difficulty_source_arbitration_en_ja.py"
                ),
                "aozora_tail_bakeoff": (
                    SCRIPT_DIR / "srs_learner_difficulty_aozora_tail_bakeoff_en_ja.py"
                ),
                "aozora_source_void_tiebreak_bakeoff": (
                    SCRIPT_DIR
                    / "srs_learner_difficulty_aozora_source_void_tiebreak_bakeoff_en_ja.py"
                ),
                "aozora_source_void_full_band_sample": Path(__file__),
            },
            argv=sys.argv,
        ),
    }


def _variant_by_id(variant_id: str) -> Mapping[str, Any]:
    for variant in _tiebreak_variant_specs():
        if str(variant.get("variant_id")) == variant_id:
            return variant
    raise SystemExit(f"Unknown Aozora source-void variant id: {variant_id}")


def _label_lookup(
    *,
    calibration_json: Path,
    holdout_json: Path,
    validation_json: Path,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    output: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for dataset, path in (
        ("calibration", calibration_json),
        ("holdout", holdout_json),
        ("stitch_validation", validation_json),
    ):
        if not path.exists():
            continue
        payload = _load_json(path)
        for row in payload.get("labels") or []:
            if not isinstance(row, Mapping):
                continue
            expected = _optional_float(row.get("expected_learner_difficulty"))
            lemma = str(row.get("lemma") or "").strip()
            reading = str(row.get("expected_reading") or row.get("reading") or "").strip()
            if not lemma or expected is None:
                continue
            output.setdefault((lemma, reading), []).append(
                {
                    "dataset": dataset,
                    "expected": _rounded(float(expected)),
                    "state": str(row.get("expected_candidate_state") or ""),
                    "problem_class": str(row.get("expected_problem_class") or ""),
                }
            )
    return output


def _movement_summary(*, scores: np.ndarray, current_scores: np.ndarray) -> dict[str, Any]:
    delta = np.asarray(scores, dtype=np.float32) - np.asarray(current_scores, dtype=np.float32)
    moved = np.abs(delta) > 0.0005
    moved_count = int(moved.sum())
    down = delta < -0.0005
    up = delta > 0.0005
    if moved_count == 0:
        return {
            "moved_count": 0,
            "down_count": 0,
            "up_count": 0,
            "mean_abs_delta": 0.0,
            "p90_abs_delta": 0.0,
            "max_down_delta": 0.0,
            "max_up_delta": 0.0,
        }
    return {
        "moved_count": moved_count,
        "down_count": int(down.sum()),
        "up_count": int(up.sum()),
        "mean_abs_delta": _rounded(float(np.abs(delta[moved]).mean())),
        "p90_abs_delta": _rounded(float(np.quantile(np.abs(delta[moved]), 0.90))),
        "max_down_delta": _rounded(float(delta.min())),
        "max_up_delta": _rounded(float(delta.max())),
    }


def _band_counts(*, scores: np.ndarray, current_scores: np.ndarray) -> list[dict[str, Any]]:
    output = []
    delta = np.asarray(scores, dtype=np.float32) - np.asarray(current_scores, dtype=np.float32)
    for start, end in _bands():
        mask = _band_mask(scores, start, end)
        current_mask = _band_mask(current_scores, start, end)
        moved_mask = mask & (np.abs(delta) > 0.0005)
        output.append(
            {
                "band": _band_label(start, end),
                "count": int(mask.sum()),
                "current_count": int(current_mask.sum()),
                "moved_in_band": int(moved_mask.sum()),
                "mean_delta_in_band": (
                    _rounded(float(delta[mask].mean())) if int(mask.sum()) else None
                ),
            }
        )
    return output


def _band_samples(
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
    labels: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
    per_band: int,
) -> list[dict[str, Any]]:
    output = []
    for start, end in _bands():
        mask = _band_mask(scores, start, end)
        indices = np.where(mask)[0]
        ordered = indices[np.argsort(scores[indices], kind="stable")]
        sample_indices = _quantile_indices(ordered, per_band)
        output.append(
            {
                "band": _band_label(start, end),
                "count": int(len(indices)),
                "samples": [
                    _sample_row_with_label(
                        int(index),
                        scores=scores,
                        current_scores=current_scores,
                        view=view,
                        aozora=aozora,
                        labels=labels,
                    )
                    for index in sample_indices
                ],
            }
        )
    return output


def _move_samples(
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
    labels: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
    direction: str,
    limit: int,
) -> list[dict[str, Any]]:
    delta = np.asarray(scores, dtype=np.float32) - np.asarray(current_scores, dtype=np.float32)
    if direction == "down":
        order = np.argsort(delta, kind="stable")
        selected = [int(index) for index in order if delta[index] < -0.001]
    else:
        order = np.argsort(-delta, kind="stable")
        selected = [int(index) for index in order if delta[index] > 0.001]
    return [
        _sample_row_with_label(
            int(index),
            scores=scores,
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            labels=labels,
        )
        for index in selected[:limit]
    ]


def _sample_row_with_label(
    index: int,
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
    labels: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    row = _sample_row(
        index,
        scores=scores,
        current_scores=current_scores,
        view=view,
        aozora=aozora,
    )
    row["expected_labels"] = list(
        labels.get((str(row.get("lemma") or ""), str(row.get("reading") or "")), [])
    )
    return row


def render_markdown(report: Mapping[str, Any]) -> str:
    method = _mapping(report.get("method"))
    movement = _mapping(report.get("movement_summary"))
    lines = [
        "# en-ja Aozora Source-Void Full-Band Sample Pack",
        "",
        "## Summary",
        "",
        f"- Candidate: `{_escape(method.get('candidate_id'))}`",
        f"- Candidate family: `{_escape(method.get('candidate_family'))}`",
        f"- Target curve: `{_escape(method.get('target_curve_override'))}`",
        f"- Aozora variant: `{_escape(method.get('variant_id'))}`",
        f"- Component count: `{_escape(_mapping(report.get('inputs')).get('component_count'))}`",
        f"- Samples per 0.05 band: `{_escape(_mapping(report.get('inputs')).get('sample_per_band'))}`",
        "",
        "This is a qualitative sidecar only. It does not change scorer behavior.",
        "",
        "Movement summary:",
        "",
        _movement_table([movement]),
        "",
        "## Band Counts",
        "",
        _band_count_table(report.get("band_counts") or []),
        "",
        "## Band Samples",
        "",
    ]
    for band in report.get("band_samples") or []:
        row = _mapping(band)
        lines.extend(
            [
                f"### Band `{_escape(row.get('band'))}` count `{_escape(row.get('count'))}`",
                "",
                _sample_table(row.get("samples") or []),
                "",
            ]
        )
    lines.extend(
        [
            "## Largest Down Moves",
            "",
            _sample_table(report.get("largest_down_moves") or []),
            "",
            "## Largest Up Moves",
            "",
            _sample_table(report.get("largest_up_moves") or []),
            "",
            "## Caveats",
            "",
            "- Samples are quantile picks inside each post-nudge 0.05 band.",
            "- The current column is the base source-arbitration score before the Aozora tiebreaker.",
            "- Aozora means book/literary attestation, so these samples still need qualitative review.",
            "",
        ]
    )
    return "\n".join(lines)


def _movement_table(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "| Moved | Down | Up | MeanAbsDelta | P90AbsDelta | MaxDown | MaxUp |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        cells = [
            str(row.get("moved_count") or 0),
            str(row.get("down_count") or 0),
            str(row.get("up_count") or 0),
            _fmt(row.get("mean_abs_delta")),
            _fmt(row.get("p90_abs_delta")),
            _fmt(row.get("max_down_delta")),
            _fmt(row.get("max_up_delta")),
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _band_count_table(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "| Band | Count | CurrentCount | MovedInBand | MeanDeltaInBand |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        cells = [
            str(row.get("band") or ""),
            str(row.get("count") or 0),
            str(row.get("current_count") or 0),
            str(row.get("moved_in_band") or 0),
            _fmt(row.get("mean_delta_in_band")),
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _sample_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Word | Score | Current | Delta | Aozora | Tok | Works | Authors | Conf | Old | Hard | Access | Expected |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        label = (
            f"{row.get('lemma')}/{row.get('reading')}"
            if row.get("reading")
            else str(row.get("lemma") or "")
        )
        cells = [
            label,
            _fmt(row.get("score")),
            _fmt(row.get("current")),
            _fmt(row.get("delta")),
            str(row.get("match_status") or ""),
            str(row.get("token_count") or 0),
            str(row.get("work_count") or 0),
            str(row.get("author_count") or 0),
            _fmt(row.get("confidence")),
            _fmt(row.get("old_risk")),
            _fmt(row.get("hard")),
            _fmt(row.get("access")),
            _expected_label(row.get("expected_labels") or []),
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _expected_label(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return ""
    parts = []
    for row in rows:
        dataset = str(row.get("dataset") or "")
        expected = _fmt(row.get("expected"))
        parts.append(f"{dataset}:{expected}")
    return ", ".join(parts)


def _bands() -> list[tuple[float, float]]:
    return [(i * BAND_WIDTH, (i + 1) * BAND_WIDTH) for i in range(int(1.0 / BAND_WIDTH))]


def _band_mask(scores: np.ndarray, start: float, end: float) -> np.ndarray:
    if end >= 1.0:
        return (scores >= start) & (scores <= end)
    return (scores >= start) & (scores < end)


def _band_label(start: float, end: float) -> str:
    return f"{start:.2f}-{min(end, 1.0):.2f}"


def _quantile_indices(indices: np.ndarray, count: int) -> list[int]:
    if len(indices) == 0:
        return []
    offsets = np.linspace(0, len(indices) - 1, num=min(count, len(indices)), dtype=int)
    return [int(indices[offset]) for offset in offsets]


def _fmt(value: Any) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.3f}"


def _resolve_path(value: Path) -> Path:
    if value.is_absolute():
        return value
    return (PROJECT_ROOT / value).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
