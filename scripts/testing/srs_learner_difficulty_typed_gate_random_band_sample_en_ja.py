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
from srs_learner_difficulty_aozora_tail_bakeoff_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_SOURCE_ARBITRATION_JSON,
    DEFAULT_VALIDATION_JSON,
    ComponentView,
    _current_scores,
    _label_context,
    _load_json,
    _selected_candidate_metadata,
    _variant_result,
    _view_with_target_curve_override,
)
from srs_learner_difficulty_early_exact_support_gate_bakeoff_en_ja import (  # noqa: E402
    _apply_variant,
    _early_gate_evidence,
    _movement_summary,
    _variant_specs,
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
from srs_learner_difficulty_source_arbitration_en_ja import family_parts  # noqa: E402


PAIR = "en-ja"
DEFAULT_VARIANT_ID = "exgate_typed_ec05_fl056_fh084_mr036_cru045_lr075_stb075_ts025_te045_sp075"
DEFAULT_SAMPLE_SEED = 20260627
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_typed_gate_random_band_sample_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_typed_gate_random_band_sample_en_ja_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate fixed-seed random 0.05-band samples for the typed early "
            "exact-support gate sidecar. Samples are selected mechanically, not "
            "hand-picked."
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
    parser.add_argument("--variant-id", default=DEFAULT_VARIANT_ID)
    parser.add_argument("--sample-seed", type=int, default=DEFAULT_SAMPLE_SEED)
    parser.add_argument("--sample-per-band", type=int, default=5)
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
        variant_id=str(args.variant_id or DEFAULT_VARIANT_ID),
        sample_seed=int(args.sample_seed),
        sample_per_band=max(1, int(args.sample_per_band)),
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
    variant_id: str,
    sample_seed: int,
    sample_per_band: int,
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
    evidence = _early_gate_evidence(view=view, parts=family_parts(view))
    variant = _variant_by_id(variant_id)
    scores = _apply_variant(
        current_scores=current_scores,
        evidence=evidence,
        variant=variant,
    )
    labels = _label_context(
        view=view,
        current_scores=current_scores,
        calibration_json=calibration_json,
        holdout_json=holdout_json,
        validation_json=validation_json,
    )
    variant_metrics = _variant_result(
        variant=variant,
        scores=scores,
        current_scores=current_scores,
        labels=labels,
    )
    variant_metrics.update(_movement_summary(scores=scores, current_scores=current_scores))
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "model_behavior_changed": False,
        "method": {
            "purpose": (
                "Fixed-seed random thin-band qualitative review for the typed clean "
                "early exact-support gate. This is a representative acceptance "
                "sampling pack, not a hand-picked diagnostic pack."
            ),
            "candidate_id": selected["candidate_id"],
            "candidate_family": selected["candidate_family"],
            "target_curve_override": selected["target_curve_override"],
            "variant_id": variant_id,
            "sample_seed": sample_seed,
            "sample_per_band": sample_per_band,
            "sampling": (
                "For each 0.05 post-variant score band, sample without replacement "
                "using numpy.default_rng(seed), then sort selected rows by score "
                "inside the band for readability."
            ),
        },
        "inputs": {
            "source_arbitration_json": _repo_or_home_path(source_arbitration_json),
            "component_matrix": _repo_or_home_path(component_matrix),
            "calibration_json": _repo_or_home_path(calibration_json),
            "holdout_json": _repo_or_home_path(holdout_json),
            "validation_json": _repo_or_home_path(validation_json),
            "component_count": int(len(current_scores)),
        },
        "variant_metrics": variant_metrics,
        "band_counts": _band_counts(scores=scores, current_scores=current_scores),
        "band_samples": _band_samples(
            scores=scores,
            current_scores=current_scores,
            view=view,
            evidence=evidence,
            per_band=sample_per_band,
            seed=sample_seed,
        ),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "source_arbitration_json": source_arbitration_json,
                "component_matrix": component_matrix,
                "calibration_json": calibration_json,
                "holdout_json": holdout_json,
                "validation_json": validation_json,
            },
            code_paths={
                **_srs_difficulty_code_paths(),
                "source_arbitration": (
                    SCRIPT_DIR / "srs_learner_difficulty_source_arbitration_en_ja.py"
                ),
                "aozora_tail_bakeoff": (
                    SCRIPT_DIR / "srs_learner_difficulty_aozora_tail_bakeoff_en_ja.py"
                ),
                "early_exact_support_gate_bakeoff": (
                    SCRIPT_DIR / "srs_learner_difficulty_early_exact_support_gate_bakeoff_en_ja.py"
                ),
                "typed_gate_random_band_sample": Path(__file__),
            },
            argv=sys.argv,
        ),
    }


def _variant_by_id(variant_id: str) -> dict[str, Any]:
    for variant in _variant_specs():
        if str(variant.get("variant_id")) == variant_id:
            return variant
    raise ValueError(f"Unknown variant id: {variant_id}")


def _band_counts(*, scores: np.ndarray, current_scores: np.ndarray) -> list[dict[str, Any]]:
    output = []
    delta = np.asarray(scores, dtype=np.float32) - np.asarray(current_scores, dtype=np.float32)
    for start, end in _bands():
        mask = _band_mask(scores, start, end)
        moved = mask & (np.abs(delta) > 0.0005)
        output.append(
            {
                "band": _band_label(start, end),
                "count": int(mask.sum()),
                "moved_count": int(moved.sum()),
                "mean_delta_in_band": (
                    _rounded(float(delta[mask].mean())) if bool(mask.any()) else 0.0
                ),
            }
        )
    return output


def _band_samples(
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    evidence: Mapping[str, np.ndarray],
    per_band: int,
    seed: int,
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    output = []
    for start, end in _bands():
        indices = np.where(_band_mask(scores, start, end))[0]
        if len(indices) <= per_band:
            sample_indices = np.array(indices, dtype=np.int64)
        else:
            sample_indices = rng.choice(indices, size=per_band, replace=False)
        sample_indices = sample_indices[np.argsort(scores[sample_indices], kind="stable")]
        output.append(
            {
                "band": _band_label(start, end),
                "count": int(len(indices)),
                "samples": [
                    _sample_row(
                        int(index),
                        scores=scores,
                        current_scores=current_scores,
                        view=view,
                        evidence=evidence,
                    )
                    for index in sample_indices
                ],
            }
        )
    return output


def _sample_row(
    index: int,
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    evidence: Mapping[str, np.ndarray],
) -> dict[str, Any]:
    return {
        "lemma": str(view.lemmas[index]),
        "reading": str(view.readings[index]),
        "score": _rounded(float(scores[index])),
        "current": _rounded(float(current_scores[index])),
        "delta": _rounded(float(scores[index] - current_scores[index])),
        "core_rank": (
            _rounded(float(view.core_ranks[index]))
            if np.isfinite(float(view.core_ranks[index]))
            else None
        ),
        "candidate_state": str(view.candidate_states[index]),
        "exact_commonness": _rounded(float(evidence["exact_commonness"][index])),
        "jlpt_exact_known": _rounded(float(evidence["jlpt_exact_known"][index])),
        "lesson_known": _rounded(float(evidence["lesson_known"][index])),
        "same_surface_risk": _rounded(float(evidence["same_surface_risk"][index])),
        "hard_form": _rounded(float(evidence["hard_form"][index])),
        "soft_form": _rounded(float(evidence["soft_form"][index])),
        "reading_inheritance": _rounded(float(evidence["reading_inheritance"][index])),
        "tail_guard": _rounded(float(evidence["tail_guard"][index])),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    method = _mapping(report.get("method"))
    metrics = _mapping(report.get("variant_metrics"))
    all_summary = _mapping(metrics.get("all_summary"))
    lines = [
        "# en-ja Typed Gate Random Band Sample",
        "",
        "## Summary",
        "",
        f"- Variant: `{_escape(method.get('variant_id'))}`",
        f"- Sample seed: `{_escape(method.get('sample_seed'))}`",
        f"- Samples per 0.05 band: `{_escape(method.get('sample_per_band'))}`",
        f"- Selection score: `{_escape(metrics.get('selection_score'))}`",
        f"- MAE: `{_escape(all_summary.get('mae'))}`",
        f"- Pairwise accuracy: `{_escape(all_summary.get('pairwise_accuracy'))}`",
        f"- Improved/regressed labels >=0.01: `{_escape(metrics.get('label_improved_count_0p01'))}` / `{_escape(metrics.get('label_regressed_count_0p01'))}`",
        "",
        "Samples are fixed-seed random selections within each post-variant score band.",
        "",
        "## Band Counts",
        "",
        _band_count_table(report.get("band_counts") or []),
        "",
        "## Random Band Samples",
        "",
    ]
    for band in report.get("band_samples") or []:
        row = _mapping(band)
        lines.extend(
            [
                f"### `{_escape(row.get('band'))}` count `{_escape(row.get('count'))}`",
                "",
                _sample_table(row.get("samples") or []),
                "",
            ]
        )
    return "\n".join(lines)


def _band_count_table(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "| Band | Count | Moved | Mean delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape(cell)
                for cell in (
                    str(row.get("band") or ""),
                    str(row.get("count") or 0),
                    str(row.get("moved_count") or 0),
                    _fmt(row.get("mean_delta_in_band")),
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _sample_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Word | Score | Current | Delta | Rank | Exact | JLPTx | Lesson | Same | Hard | Soft | Read | Tail |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        label = f"{row.get('lemma')}/{row.get('reading')}"
        cells = [
            label,
            _fmt(row.get("score")),
            _fmt(row.get("current")),
            _fmt(row.get("delta")),
            _fmt(row.get("core_rank")),
            _fmt(row.get("exact_commonness")),
            _fmt(row.get("jlpt_exact_known")),
            _fmt(row.get("lesson_known")),
            _fmt(row.get("same_surface_risk")),
            _fmt(row.get("hard_form")),
            _fmt(row.get("soft_form")),
            _fmt(row.get("reading_inheritance")),
            _fmt(row.get("tail_guard")),
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _bands() -> list[tuple[float, float]]:
    return [(index / 20.0, (index + 1) / 20.0) for index in range(20)]


def _band_mask(scores: np.ndarray, start: float, end: float) -> np.ndarray:
    if end >= 1.0:
        return (scores >= start) & (scores <= end)
    return (scores >= start) & (scores < end)


def _band_label(start: float, end: float) -> str:
    return f"{start:.2f}-{end:.2f}"


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
