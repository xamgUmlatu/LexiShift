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
    worst_rows,
)
from srs_learner_difficulty_model_family_search_en_ja import (  # noqa: E402
    _signal_arrays,
)
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _band_samples,
    _calibration_context,
    _difficulty_metrics,
    _escape,
    _mapping,
    _mapping_rows,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _summary_metrics,
    _target_curve_normalize,
    _utc_now,
)


DEFAULT_CALIBRATION_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_calibration_matrix_latest.npz"
)
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_component_matrix_latest.npz"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_curve_search_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_curve_search_en_ja_latest.md"
)

ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0)
TARGET_TRANSFORMS = ("identity", "logit", "tail_expanded")
SAMPLE_WEIGHT_MODES = ("uniform", "tail2", "beginner_tail")
DEFAULT_DETAIL_LIMIT = 20
DETAIL_CANDIDATE_LIMIT = 8
DEFAULT_CV_FOLDS = 5
CLUSTER_SIGNAL_COLUMNS = (
    "frequency",
    "frequency_unranked_risk",
    "frequency_unranked_rare_risk",
    "frequency_unranked_priority_risk",
    "frequency_unranked_tail_risk",
    "frequency_sqrt",
    "frequency_power2",
    "frequency_power3",
    "frequency_tail50",
    "frequency_tail65",
    "frequency_tail80",
    "frequency_tail90",
    "frequency_unranked_power2_risk",
    "frequency_unranked_power3_risk",
    "frequency_unranked_floor60_risk",
    "frequency_unranked_floor70_risk",
    "frequency_unranked_floor80_risk",
    "frequency_unranked_floor90_risk",
    "frequency_unranked_floor95_risk",
    "frequency_unranked_floor99_risk",
    "frequency_unranked_tail65_risk",
    "frequency_unranked_tail80_risk",
    "frequency_unranked_tail90_risk",
    "jmdict_priority",
    "kango_mid_signal",
    "kango_common_priority_risk",
    "rare_wago_tail_risk",
    "written_wago_tail_risk",
    "rare_wago_obscure_written_risk",
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_non_standard_reading_risk",
    "wtype_wago_ease",
    "wtype_kango_risk",
    "wtype_gairaigo_risk",
)

CORE_SIGNALS = (
    "frequency",
    "frequency_unranked_risk",
    "frequency_unranked_rare_risk",
    "frequency_unranked_priority_risk",
    "frequency_unranked_tail_risk",
    "frequency_sqrt",
    "frequency_power2",
    "frequency_power3",
    "frequency_tail50",
    "frequency_tail65",
    "frequency_tail80",
    "frequency_tail90",
    "frequency_unranked_power2_risk",
    "frequency_unranked_power3_risk",
    "frequency_unranked_floor60_risk",
    "frequency_unranked_floor70_risk",
    "frequency_unranked_floor80_risk",
    "frequency_unranked_floor90_risk",
    "frequency_unranked_floor95_risk",
    "frequency_unranked_floor99_risk",
    "frequency_unranked_tail65_risk",
    "frequency_unranked_tail80_risk",
    "frequency_unranked_tail90_risk",
    "jmdict_priority",
    "kango_mid_signal",
    "max_written_form_burden",
    "written_form_burden",
    "rare_wago_tail_risk",
    "written_wago_tail_risk",
)
ORIGIN_SIGNALS = (
    "wtype_wago_ease",
    "wtype_kango_risk",
    "wtype_gairaigo_risk",
    "wtype_mixed_risk",
    "wtype_proper_risk",
    "sahen_kango_ease_gate",
)
READING_SIGNALS = (
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_non_standard_reading_risk",
    "rare_wago_obscure_written_risk",
    "jmdict_marked_usage_risk",
    "jmdict_register_marked_risk",
)
KANJI_SIGNALS = (
    "kanji_burden",
    "kanji_curriculum_burden",
    "kanji_curriculum_missing_risk",
    "kanjivg_visual_complexity",
    "kanji_shape_burden",
    "stroke_count",
    "kango_kanji_burden",
    "wago_kanji_burden",
)
POS_SIGNALS = (
    "pos_plain_verb_gate",
    "pos_adjective_gate",
    "pos_common_noun_gate",
    "pos_sahen_noun_risk",
)
BASIS_TRANSFORMS = (
    "identity",
    "sqrt",
    "square",
    "head20",
    "head35",
    "tail20",
    "tail35",
    "tail50",
    "tail65",
    "tail80",
    "bump20",
    "bump35",
    "bump50",
    "bump65",
    "bump80",
)
HINGE_TRANSFORMS = (
    "identity",
    "head20",
    "head35",
    "tail20",
    "tail35",
    "tail50",
    "tail65",
    "tail80",
)
INTERACTION_SPECS = (
    ("frequency_unranked_risk", "frequency"),
    ("frequency_unranked_risk", "jmdict_priority"),
    ("frequency_unranked_rare_risk", "jmdict_priority"),
    ("frequency_unranked_floor60_risk", "jmdict_priority"),
    ("frequency_unranked_floor70_risk", "jmdict_priority"),
    ("frequency_unranked_floor80_risk", "jmdict_priority"),
    ("frequency_unranked_floor90_risk", "jmdict_priority"),
    ("frequency_unranked_floor95_risk", "jmdict_priority"),
    ("frequency_unranked_floor99_risk", "jmdict_priority"),
    ("frequency_tail65", "jmdict_priority"),
    ("frequency_tail80", "jmdict_priority"),
    ("kango_mid_signal", "max_written_form_burden"),
    ("wtype_kango_risk", "max_written_form_burden"),
    ("wtype_wago_ease", "max_written_form_burden"),
    ("wtype_wago_ease", "rare_wago_tail_risk"),
    ("rare_wago_tail_risk", "rare_non_standard_reading_risk"),
    ("rare_wago_tail_risk", "frequency"),
    ("written_wago_tail_risk", "frequency"),
    ("sahen_kango_ease_gate", "frequency"),
    ("wtype_gairaigo_risk", "frequency"),
    ("kango_common_priority_risk", "jmdict_priority"),
)


@dataclass(frozen=True)
class GatedFeatureSpec:
    gate_signal: str
    signals: tuple[str, ...]
    transforms: tuple[str, ...]


@dataclass(frozen=True)
class FeatureSetSpec:
    spec_id: str
    signals: tuple[str, ...]
    transforms: tuple[str, ...]
    include_missing: bool = False
    interactions: tuple[tuple[str, str], ...] = ()
    gated_features: tuple[GatedFeatureSpec, ...] = ()


@dataclass(frozen=True)
class CurveCandidate:
    candidate_id: str
    feature_set: str
    alpha: float
    target_transform: str
    sample_weight_mode: str
    feature_names: tuple[str, ...]
    coefficients: tuple[float, ...]
    intercept: float


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Research-only smooth curve search for en-ja learner difficulty. "
            "This fits regularized curve/interaction models to calibration labels "
            "and reports calibration plus fresh holdout behavior."
        )
    )
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--review-markdown", type=Path, default=DEFAULT_REVIEW_MARKDOWN)
    parser.add_argument("--detail-limit", type=int, default=DEFAULT_DETAIL_LIMIT)
    parser.add_argument("--top-limit", type=int, default=50)
    parser.add_argument("--cv-folds", type=int, default=DEFAULT_CV_FOLDS)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        component_matrix_path=_resolve_path(args.component_matrix),
        review_markdown=_resolve_path(args.review_markdown),
        detail_limit=max(1, int(args.detail_limit)),
        top_limit=max(1, int(args.top_limit)),
        cv_folds=max(0, int(args.cv_folds)),
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
    calibration_matrix_path: Path,
    component_matrix_path: Path,
    review_markdown: Path,
    detail_limit: int = DEFAULT_DETAIL_LIMIT,
    top_limit: int = 50,
    cv_folds: int = DEFAULT_CV_FOLDS,
) -> dict[str, object]:
    calibration = np.load(calibration_matrix_path)
    component = np.load(component_matrix_path)
    calibration_context = _calibration_context(calibration, component)
    holdout_rows = parse_holdout_review_markdown(review_markdown)
    holdout_context = dict(holdout_context_from_rows(holdout_rows, component))
    holdout_context["signal_rows"] = _signal_rows_for_context(holdout_context, component)
    signal_arrays = _signal_arrays(component)
    present_arrays = _present_arrays(component)
    feature_specs = _feature_set_specs()
    candidates: list[dict[str, object]] = []
    target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
    fold_ids = _calibration_fold_ids(calibration_context, fold_count=cv_folds)
    for spec in feature_specs:
        matrix, feature_names = _feature_matrix(
            spec,
            signal_arrays=signal_arrays,
            present_arrays=present_arrays,
        )
        if matrix.shape[1] == 0:
            continue
        for target_transform in TARGET_TRANSFORMS:
            y = _target_values(
                calibration_context["expected_values"],
                transform=target_transform,
            )
            for sample_weight_mode in SAMPLE_WEIGHT_MODES:
                sample_weights = _sample_weights(
                    calibration_context["expected_values"],
                    mode=sample_weight_mode,
                )
                for alpha in ALPHAS:
                    candidate = _fit_candidate(
                        matrix,
                        feature_names=feature_names,
                        calibration_context=calibration_context,
                        feature_set=spec.spec_id,
                        alpha=alpha,
                        target_transform=target_transform,
                        sample_weight_mode=sample_weight_mode,
                        y=y,
                        sample_weights=sample_weights,
                    )
                    raw = _predict(matrix, candidate)
                    normalized = _target_curve_normalize(raw, target_positions=target_positions)
                    cross_validation = _cross_validate_candidate(
                        matrix,
                        feature_names=feature_names,
                        calibration_context=calibration_context,
                        target_positions=target_positions,
                        feature_set=spec.spec_id,
                        alpha=alpha,
                        target_transform=target_transform,
                        sample_weight_mode=sample_weight_mode,
                        y=y,
                        sample_weights=sample_weights,
                        fold_ids=fold_ids,
                    )
                    candidates.append(
                        _candidate_result(
                            candidate,
                            normalized=normalized,
                            calibration_context=calibration_context,
                            holdout_context=holdout_context,
                            detail_limit=detail_limit,
                            cross_validation=cross_validation,
                        )
                    )
    ranked = _rank_candidates(candidates)
    _attach_band_samples(
        ranked[:DETAIL_CANDIDATE_LIMIT],
        component=component,
        feature_specs=feature_specs,
        signal_arrays=signal_arrays,
        present_arrays=present_arrays,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "calibration_matrix": calibration_matrix_path,
                "component_matrix": component_matrix_path,
                "review_markdown": review_markdown,
            },
            code_paths=_curve_search_code_paths(),
            version_constants={
                "target_curve": TARGET_CURVE_ID,
            },
            argv=sys.argv,
        ),
        "method": {
            "model": "regularized_smooth_curve_search",
            "normalization_curve_id": TARGET_CURVE_ID,
            "description": (
                "Fits ridge-style smooth feature curves and interactions to reviewed "
                "calibration labels, then applies full-population target-curve "
                "normalization before evaluating calibration and holdout."
            ),
            "guardrail_note": (
                "Holdout is reported for generalization only; it is not used in fitting."
            ),
        },
        "inputs": {
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "review_markdown": _repo_or_home_path(review_markdown),
            "calibration_label_count": int(len(calibration["calibration_lemmas"])),
            "holdout_numeric_count": int(np.isfinite(holdout_context["expected_values"]).sum()),
            "normalization_population_count": int(len(component["candidate_identity_keys"])),
            "feature_set_count": len(feature_specs),
            "candidate_count": len(candidates),
            "cv_folds": cv_folds,
            "alpha_grid": list(ALPHAS),
            "target_transforms": list(TARGET_TRANSFORMS),
            "sample_weight_modes": list(SAMPLE_WEIGHT_MODES),
        },
        "feature_sets": [_feature_set_json(spec) for spec in feature_specs],
        "leaderboards": _leaderboards(ranked),
        "exact_top": ranked[:top_limit],
    }


def _curve_search_code_paths() -> dict[str, Path]:
    return {
        "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
        "difficulty_signal_sweep": (SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py"),
        "difficulty_model_family_search": (
            SCRIPT_DIR / "srs_learner_difficulty_model_family_search_en_ja.py"
        ),
        "difficulty_holdout_eval": (SCRIPT_DIR / "srs_learner_difficulty_holdout_eval_en_ja.py"),
        "difficulty_piecewise_search": (
            SCRIPT_DIR / "srs_learner_difficulty_piecewise_search_en_ja.py"
        ),
        "difficulty_normalization": SCRIPT_DIR / "srs_learner_difficulty_normalization.py",
    }


def _attach_band_samples(
    rows: Sequence[Mapping[str, object]],
    *,
    component: object,
    feature_specs: Sequence[FeatureSetSpec],
    signal_arrays: Mapping[str, object],
    present_arrays: Mapping[str, object],
) -> None:
    specs_by_id = {spec.spec_id: spec for spec in feature_specs}
    matrices: dict[str, tuple[np.ndarray, tuple[str, ...]]] = {}
    target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
    for row in rows:
        if not isinstance(row, dict):
            continue
        feature_set = str(row.get("feature_set") or "")
        spec = specs_by_id.get(feature_set)
        if spec is None:
            continue
        if feature_set not in matrices:
            matrices[feature_set] = _feature_matrix(
                spec,
                signal_arrays=signal_arrays,
                present_arrays=present_arrays,
            )
        matrix, feature_names = matrices[feature_set]
        raw = _raw_from_candidate_row(row, matrix=matrix, feature_names=feature_names)
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        row["band_samples"] = _band_samples(
            normalized,
            component=component,
            segment_ids=np.zeros(len(normalized), dtype=np.int64),
            expert_ids=(str(row.get("candidate_id") or ""),),
            per_band=8,
        )


def _raw_from_candidate_row(
    row: Mapping[str, object],
    *,
    matrix: np.ndarray,
    feature_names: Sequence[str],
) -> np.ndarray:
    coefficient_rows = _mapping_rows(row.get("coefficients"))
    coefficient_by_feature = {
        str(item.get("feature") or ""): float(item.get("coefficient") or 0.0)
        for item in coefficient_rows
    }
    coefficients = np.asarray(
        [coefficient_by_feature.get(feature, 0.0) for feature in feature_names],
        dtype=np.float32,
    )
    intercept = float(row.get("intercept") or 0.0)
    return (matrix @ coefficients + np.float32(intercept)).astype(np.float32)


def _feature_set_specs() -> tuple[FeatureSetSpec, ...]:
    return (
        FeatureSetSpec(
            "core_identity",
            signals=CORE_SIGNALS,
            transforms=("identity",),
        ),
        FeatureSetSpec(
            "core_curves",
            signals=CORE_SIGNALS,
            transforms=("identity", "sqrt", "square", "tail50", "tail75"),
            include_missing=True,
        ),
        FeatureSetSpec(
            "origin_aware_curves",
            signals=(*CORE_SIGNALS, *ORIGIN_SIGNALS),
            transforms=("identity", "sqrt", "square", "tail50"),
            include_missing=True,
            interactions=INTERACTION_SPECS[:6],
        ),
        FeatureSetSpec(
            "reading_tail_curves",
            signals=(*CORE_SIGNALS, *READING_SIGNALS),
            transforms=("identity", "sqrt", "square", "tail50", "tail75"),
            include_missing=True,
            interactions=INTERACTION_SPECS[3:8],
        ),
        FeatureSetSpec(
            "kanji_origin_curves",
            signals=(*CORE_SIGNALS, *ORIGIN_SIGNALS, *KANJI_SIGNALS),
            transforms=("identity", "sqrt", "square", "tail50"),
            include_missing=True,
            interactions=INTERACTION_SPECS,
        ),
        FeatureSetSpec(
            "pos_origin_curves",
            signals=(*CORE_SIGNALS, *ORIGIN_SIGNALS, *POS_SIGNALS),
            transforms=("identity", "sqrt", "square", "tail50"),
            include_missing=True,
            interactions=INTERACTION_SPECS,
        ),
        FeatureSetSpec(
            "rich_curves",
            signals=(
                *CORE_SIGNALS,
                *ORIGIN_SIGNALS,
                *READING_SIGNALS,
                *KANJI_SIGNALS,
                *POS_SIGNALS,
            ),
            transforms=("identity", "sqrt", "square", "tail50", "tail75"),
            include_missing=True,
            interactions=INTERACTION_SPECS,
        ),
        FeatureSetSpec(
            "gam_core_hinges",
            signals=CORE_SIGNALS,
            transforms=HINGE_TRANSFORMS,
            include_missing=True,
        ),
        FeatureSetSpec(
            "gam_origin_hinges",
            signals=(*CORE_SIGNALS, *ORIGIN_SIGNALS, *READING_SIGNALS),
            transforms=HINGE_TRANSFORMS,
            include_missing=True,
            interactions=INTERACTION_SPECS,
        ),
        FeatureSetSpec(
            "gam_rich_hinges",
            signals=(
                *CORE_SIGNALS,
                *ORIGIN_SIGNALS,
                *READING_SIGNALS,
                *KANJI_SIGNALS,
                *POS_SIGNALS,
            ),
            transforms=HINGE_TRANSFORMS,
            include_missing=True,
            interactions=INTERACTION_SPECS,
        ),
        FeatureSetSpec(
            "rbf_core_curves",
            signals=CORE_SIGNALS,
            transforms=BASIS_TRANSFORMS,
            include_missing=True,
        ),
        FeatureSetSpec(
            "rbf_origin_reading_curves",
            signals=(*CORE_SIGNALS, *ORIGIN_SIGNALS, *READING_SIGNALS),
            transforms=BASIS_TRANSFORMS,
            include_missing=True,
            interactions=INTERACTION_SPECS,
        ),
        FeatureSetSpec(
            "rbf_conditional_moe_curves",
            signals=("frequency", "jmdict_priority", "max_written_form_burden"),
            transforms=(
                "identity",
                "sqrt",
                "square",
                "head20",
                "head35",
                "tail20",
                "tail35",
                "tail50",
                "tail65",
                "tail80",
                "bump20",
                "bump35",
                "bump50",
                "bump65",
                "bump80",
            ),
            include_missing=True,
            gated_features=(
                GatedFeatureSpec(
                    "wtype_wago_ease",
                    signals=(
                        "frequency",
                        "jmdict_priority",
                        "max_written_form_burden",
                        "rare_wago_tail_risk",
                        "written_wago_tail_risk",
                        "non_standard_reading_risk",
                    ),
                    transforms=BASIS_TRANSFORMS,
                ),
                GatedFeatureSpec(
                    "wtype_kango_risk",
                    signals=(
                        "frequency",
                        "jmdict_priority",
                        "kango_mid_signal",
                        "kango_common_priority_risk",
                        "max_written_form_burden",
                        "written_form_burden",
                    ),
                    transforms=BASIS_TRANSFORMS,
                ),
                GatedFeatureSpec(
                    "wtype_gairaigo_risk",
                    signals=("frequency", "jmdict_priority", "max_written_form_burden"),
                    transforms=BASIS_TRANSFORMS,
                ),
                GatedFeatureSpec(
                    "rare_non_standard_reading_risk",
                    signals=(
                        "frequency",
                        "jmdict_priority",
                        "rare_wago_tail_risk",
                        "written_wago_tail_risk",
                        "max_written_form_burden",
                    ),
                    transforms=BASIS_TRANSFORMS,
                ),
                GatedFeatureSpec(
                    "sahen_kango_ease_gate",
                    signals=(
                        "frequency",
                        "jmdict_priority",
                        "kango_mid_signal",
                        "written_form_burden",
                    ),
                    transforms=BASIS_TRANSFORMS,
                ),
            ),
        ),
        FeatureSetSpec(
            "soft_origin_moe_curves",
            signals=("frequency", "jmdict_priority"),
            transforms=("identity", "sqrt", "square", "tail50"),
            include_missing=True,
            gated_features=(
                GatedFeatureSpec(
                    "wtype_wago_ease",
                    signals=(
                        "frequency",
                        "jmdict_priority",
                        "max_written_form_burden",
                        "rare_wago_tail_risk",
                        "written_wago_tail_risk",
                        "non_standard_reading_risk",
                    ),
                    transforms=("identity", "sqrt", "square", "tail50"),
                ),
                GatedFeatureSpec(
                    "wtype_kango_risk",
                    signals=(
                        "frequency",
                        "jmdict_priority",
                        "kango_mid_signal",
                        "kango_common_priority_risk",
                        "max_written_form_burden",
                        "written_form_burden",
                    ),
                    transforms=("identity", "sqrt", "square", "tail50"),
                ),
                GatedFeatureSpec(
                    "wtype_gairaigo_risk",
                    signals=("frequency", "jmdict_priority", "max_written_form_burden"),
                    transforms=("identity", "sqrt", "square", "tail50"),
                ),
                GatedFeatureSpec(
                    "wtype_mixed_risk",
                    signals=(
                        "frequency",
                        "jmdict_priority",
                        "max_written_form_burden",
                        "rare_wago_tail_risk",
                    ),
                    transforms=("identity", "sqrt", "square", "tail50"),
                ),
            ),
        ),
        FeatureSetSpec(
            "soft_reading_moe_curves",
            signals=("frequency", "jmdict_priority", "max_written_form_burden"),
            transforms=("identity", "sqrt", "square", "tail50"),
            include_missing=True,
            gated_features=(
                GatedFeatureSpec(
                    "rare_non_standard_reading_risk",
                    signals=(
                        "frequency",
                        "jmdict_priority",
                        "rare_wago_tail_risk",
                        "written_wago_tail_risk",
                        "max_written_form_burden",
                    ),
                    transforms=("identity", "sqrt", "square", "tail50", "tail75"),
                ),
                GatedFeatureSpec(
                    "rare_wago_non_standard_reading_risk",
                    signals=(
                        "frequency",
                        "jmdict_priority",
                        "rare_wago_tail_risk",
                        "rare_wago_obscure_written_risk",
                    ),
                    transforms=("identity", "sqrt", "square", "tail50", "tail75"),
                ),
                GatedFeatureSpec(
                    "sahen_kango_ease_gate",
                    signals=(
                        "frequency",
                        "jmdict_priority",
                        "kango_mid_signal",
                        "written_form_burden",
                    ),
                    transforms=("identity", "sqrt", "square", "tail50"),
                ),
            ),
        ),
    )


def _feature_matrix(
    spec: FeatureSetSpec,
    *,
    signal_arrays: Mapping[str, object],
    present_arrays: Mapping[str, object],
) -> tuple[np.ndarray, tuple[str, ...]]:
    columns: list[np.ndarray] = []
    names: list[str] = []
    for signal in spec.signals:
        values = _safe_values(signal_arrays, signal)
        for transform in spec.transforms:
            transformed = _transform(values, transform)
            columns.append(transformed.astype(np.float32))
            names.append(f"{signal}:{transform}")
        if spec.include_missing and signal != "frequency":
            present = np.asarray(present_arrays.get(signal), dtype=bool)
            if present.shape == values.shape:
                columns.append((~present).astype(np.float32))
                names.append(f"{signal}:missing")
    for left, right in spec.interactions:
        left_values = _safe_values(signal_arrays, left)
        right_values = _safe_values(signal_arrays, right)
        columns.append((left_values * right_values).astype(np.float32))
        names.append(f"{left}*{right}")
    for gated in spec.gated_features:
        gate = _safe_values(signal_arrays, gated.gate_signal)
        for signal in gated.signals:
            values = _safe_values(signal_arrays, signal)
            for transform in gated.transforms:
                columns.append((gate * _transform(values, transform)).astype(np.float32))
                names.append(f"{gated.gate_signal}|{signal}:{transform}")
    if not columns:
        return np.empty((0, 0), dtype=np.float32), ()
    return np.column_stack(columns).astype(np.float32), tuple(names)


def _present_arrays(component: object) -> dict[str, object]:
    names = [str(value) for value in component["component_names"]]
    present = np.asarray(component["component_present"], dtype=bool)
    arrays: dict[str, object] = {
        "frequency": np.isfinite(np.asarray(component["frequency_values"], dtype=np.float32))
    }
    for index, name in enumerate(names):
        arrays[name] = present[:, index]
    return arrays


def _safe_values(signal_arrays: Mapping[str, object], signal: str) -> np.ndarray:
    values = signal_arrays.get(signal)
    if values is None:
        frequency = signal_arrays.get("frequency")
        if frequency is None:
            raise ValueError("frequency signal is required")
        return np.zeros_like(np.asarray(frequency, dtype=np.float32))
    return np.nan_to_num(np.asarray(values, dtype=np.float32), nan=0.0)


def _transform(values: object, transform: str) -> np.ndarray:
    parsed = np.clip(np.asarray(values, dtype=np.float32), 0.0, 1.0)
    if transform == "identity":
        return parsed
    if transform == "sqrt":
        return np.sqrt(parsed)
    if transform == "square":
        return parsed * parsed
    if transform == "head20":
        return _head(parsed, 0.20)
    if transform == "head35":
        return _head(parsed, 0.35)
    if transform == "tail20":
        return _ramp(parsed, 0.20, 1.00)
    if transform == "tail35":
        return _ramp(parsed, 0.35, 1.00)
    if transform == "tail50":
        return _ramp(parsed, 0.50, 1.00)
    if transform == "tail65":
        return _ramp(parsed, 0.65, 1.00)
    if transform == "tail75":
        return _ramp(parsed, 0.75, 1.00)
    if transform == "tail80":
        return _ramp(parsed, 0.80, 1.00)
    if transform == "bump20":
        return _bump(parsed, 0.20)
    if transform == "bump35":
        return _bump(parsed, 0.35)
    if transform == "bump50":
        return _bump(parsed, 0.50)
    if transform == "bump65":
        return _bump(parsed, 0.65)
    if transform == "bump80":
        return _bump(parsed, 0.80)
    raise ValueError(f"Unknown transform: {transform}")


def _ramp(values: object, lower: float, upper: float) -> np.ndarray:
    parsed = np.asarray(values, dtype=np.float32)
    return np.clip((parsed - lower) / (upper - lower), 0.0, 1.0)


def _head(values: object, upper: float) -> np.ndarray:
    parsed = np.asarray(values, dtype=np.float32)
    if upper <= 0.0:
        return np.zeros_like(parsed)
    return np.clip((upper - parsed) / upper, 0.0, 1.0)


def _bump(values: object, center: float, width: float = 0.16) -> np.ndarray:
    parsed = np.asarray(values, dtype=np.float32)
    scaled = (parsed - np.float32(center)) / np.float32(width)
    return np.exp(-0.5 * scaled * scaled).astype(np.float32)


def _target_values(expected_values: object, *, transform: str) -> np.ndarray:
    expected = np.asarray(expected_values, dtype=np.float32)
    clipped = np.clip(expected, 0.001, 0.999)
    if transform == "identity":
        return expected
    if transform == "logit":
        return np.log(clipped / (1.0 - clipped)).astype(np.float32)
    if transform == "tail_expanded":
        centered = (clipped - 0.5) * 2.0
        return (0.5 + 0.5 * np.sign(centered) * np.sqrt(np.abs(centered))).astype(np.float32)
    raise ValueError(f"Unknown target transform: {transform}")


def _sample_weights(expected_values: object, *, mode: str) -> np.ndarray:
    expected = np.asarray(expected_values, dtype=np.float32)
    weights = np.ones(len(expected), dtype=np.float32)
    if mode == "uniform":
        return weights
    finite = np.isfinite(expected)
    if mode == "tail2":
        weights[finite] = 1.0 + (2.0 * np.abs(expected[finite] - 0.5))
        return weights
    if mode == "beginner_tail":
        weights[finite] = 1.0
        weights[finite & (expected <= 0.20)] = 2.0
        weights[finite & (expected >= 0.88)] = 2.0
        return weights
    raise ValueError(f"Unknown sample weight mode: {mode}")


def _fit_candidate(
    matrix: np.ndarray,
    *,
    feature_names: Sequence[str],
    calibration_context: Mapping[str, object],
    feature_set: str,
    alpha: float,
    target_transform: str,
    sample_weight_mode: str,
    y: np.ndarray,
    sample_weights: np.ndarray,
    training_mask: object | None = None,
) -> CurveCandidate:
    indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    expected = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    valid = (indices >= 0) & np.isfinite(expected) & np.isfinite(y)
    if training_mask is not None:
        parsed_training_mask = np.asarray(training_mask, dtype=bool)
        if parsed_training_mask.shape != valid.shape:
            raise ValueError("Training mask must align to calibration rows.")
        valid &= parsed_training_mask
    if not bool(valid.any()):
        raise ValueError("No valid calibration rows available for curve fitting.")
    x_train = matrix[indices[valid]]
    y_train = y[valid]
    weights = sample_weights[valid]
    means = x_train.mean(axis=0)
    stds = x_train.std(axis=0)
    stds = np.where(stds < 1e-6, 1.0, stds)
    x_scaled = (x_train - means) / stds
    x_design = np.column_stack([np.ones(len(x_scaled), dtype=np.float32), x_scaled])
    sqrt_weights = np.sqrt(np.clip(weights, 0.0, None)).astype(np.float32)
    weighted_x = x_design * sqrt_weights[:, None]
    weighted_y = y_train * sqrt_weights
    penalty = np.eye(x_design.shape[1], dtype=np.float64) * float(alpha)
    penalty[0, 0] = 0.0
    lhs = weighted_x.T @ weighted_x + penalty
    rhs = weighted_x.T @ weighted_y
    try:
        solution = np.linalg.solve(lhs, rhs)
    except np.linalg.LinAlgError:
        solution = np.linalg.lstsq(lhs, rhs, rcond=None)[0]
    intercept = float(solution[0] - np.sum((solution[1:] * means) / stds))
    coefficients = tuple(float(value) for value in (solution[1:] / stds))
    return CurveCandidate(
        candidate_id=(
            f"ridge_curve__{feature_set}__a{_alpha_id(alpha)}__"
            f"y_{target_transform}__w_{sample_weight_mode}"
        ),
        feature_set=feature_set,
        alpha=float(alpha),
        target_transform=target_transform,
        sample_weight_mode=sample_weight_mode,
        feature_names=tuple(feature_names),
        coefficients=coefficients,
        intercept=intercept,
    )


def _predict(matrix: np.ndarray, candidate: CurveCandidate) -> np.ndarray:
    coefficients = np.asarray(candidate.coefficients, dtype=np.float32)
    return (matrix @ coefficients + np.float32(candidate.intercept)).astype(np.float32)


def _calibration_fold_ids(
    calibration_context: Mapping[str, object],
    *,
    fold_count: int,
) -> np.ndarray:
    expected = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    fold_ids = np.full(len(expected), -1, dtype=np.int64)
    if fold_count <= 1:
        return fold_ids
    valid = np.where((indices >= 0) & np.isfinite(expected))[0]
    if len(valid) < 2:
        return fold_ids
    effective_fold_count = min(int(fold_count), len(valid))
    ordered = valid[np.argsort(expected[valid], kind="stable")]
    fold_ids[ordered] = np.arange(len(ordered), dtype=np.int64) % effective_fold_count
    return fold_ids


def _subset_context(
    context: Mapping[str, object],
    selected: object,
) -> dict[str, object]:
    mask = np.asarray(selected, dtype=bool)
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    if mask.shape != expected.shape:
        raise ValueError("Context subset mask must align to context rows.")
    expected_bands = [str(value) for value in _sequence_values(context.get("expected_bands"))]
    labels = [str(value) for value in _sequence_values(context.get("labels"))]
    return {
        "component_indices": indices[mask],
        "expected_values": expected[mask],
        "expected_bands": [
            expected_bands[index] if index < len(expected_bands) else ""
            for index, keep in enumerate(mask)
            if bool(keep)
        ],
        "labels": [
            labels[index] if index < len(labels) else str(index)
            for index, keep in enumerate(mask)
            if bool(keep)
        ],
    }


def _cross_validate_candidate(
    matrix: np.ndarray,
    *,
    feature_names: Sequence[str],
    calibration_context: Mapping[str, object],
    target_positions: object,
    feature_set: str,
    alpha: float,
    target_transform: str,
    sample_weight_mode: str,
    y: np.ndarray,
    sample_weights: np.ndarray,
    fold_ids: object,
) -> dict[str, object]:
    fold_array = np.asarray(fold_ids, dtype=np.int64)
    folds = [int(value) for value in sorted(set(fold_array.tolist())) if int(value) >= 0]
    if len(folds) < 2:
        return {
            "fold_count": 0,
            "balanced_mean": None,
            "balanced_std": None,
            "mae_mean": None,
            "folds": [],
        }

    target_curve_positions = np.asarray(target_positions, dtype=np.float32)
    fold_rows: list[dict[str, object]] = []
    for fold_id in folds:
        validation_mask = fold_array == fold_id
        training_mask = (fold_array >= 0) & ~validation_mask
        if not bool(validation_mask.any()) or not bool(training_mask.any()):
            continue
        candidate = _fit_candidate(
            matrix,
            feature_names=feature_names,
            calibration_context=calibration_context,
            feature_set=feature_set,
            alpha=alpha,
            target_transform=target_transform,
            sample_weight_mode=sample_weight_mode,
            y=y,
            sample_weights=sample_weights,
            training_mask=training_mask,
        )
        raw = _predict(matrix, candidate)
        normalized = _target_curve_normalize(raw, target_positions=target_curve_positions)
        validation_context = _subset_context(calibration_context, validation_mask)
        observed = _observed_for_context(normalized, validation_context)
        metrics = _difficulty_metrics(
            expected_values=validation_context["expected_values"],
            observed_values=observed,
            expected_bands=validation_context["expected_bands"],
            labels=validation_context["labels"],
        )
        fold_rows.append(
            {
                "fold": fold_id,
                "validation_count": int(validation_mask.sum()),
                "scores": metrics["scores"],
                "metrics": _summary_metrics(metrics),
            }
        )

    return {
        "fold_count": len(fold_rows),
        "balanced_mean": _fold_score_mean(fold_rows, "scores", "balanced_score"),
        "balanced_std": _fold_score_std(fold_rows, "scores", "balanced_score"),
        "mae_mean": _fold_score_mean(fold_rows, "metrics", "mae"),
        "pairwise_mean": _fold_score_mean(fold_rows, "metrics", "pairwise_accuracy"),
        "bucket_mean": _fold_score_mean(fold_rows, "metrics", "bucket_accuracy"),
        "folds": fold_rows,
    }


def _fold_score_mean(
    rows: Sequence[Mapping[str, object]],
    section: str,
    key: str,
) -> float | None:
    values = [
        value
        for row in rows
        if (value := _optional_float(_mapping(row.get(section)).get(key))) is not None
    ]
    if not values:
        return None
    return _rounded(float(np.mean(np.asarray(values, dtype=np.float32))))


def _fold_score_std(
    rows: Sequence[Mapping[str, object]],
    section: str,
    key: str,
) -> float | None:
    values = [
        value
        for row in rows
        if (value := _optional_float(_mapping(row.get(section)).get(key))) is not None
    ]
    if len(values) < 2:
        return None
    return _rounded(float(np.std(np.asarray(values, dtype=np.float32))))


def _candidate_result(
    candidate: CurveCandidate,
    *,
    normalized: object,
    calibration_context: Mapping[str, object],
    holdout_context: Mapping[str, object],
    detail_limit: int,
    cross_validation: Mapping[str, object] | None = None,
) -> dict[str, object]:
    calibration_observed = _observed_for_context(normalized, calibration_context)
    holdout_observed = _observed_for_context(normalized, holdout_context)
    calibration_metrics = _difficulty_metrics(
        expected_values=calibration_context["expected_values"],
        observed_values=calibration_observed,
        expected_bands=calibration_context["expected_bands"],
        labels=calibration_context["labels"],
    )
    holdout_metrics = _difficulty_metrics(
        expected_values=holdout_context["expected_values"],
        observed_values=holdout_observed,
        expected_bands=holdout_context["expected_bands"],
        labels=holdout_context["labels"],
    )
    return {
        "candidate_id": candidate.candidate_id,
        "family": "regularized_smooth_curve",
        "feature_set": candidate.feature_set,
        "alpha": _rounded(candidate.alpha),
        "target_transform": candidate.target_transform,
        "sample_weight_mode": candidate.sample_weight_mode,
        "intercept": _rounded(candidate.intercept),
        "coefficient_count": len(candidate.coefficients),
        "coefficients": _coefficients(candidate),
        "top_coefficients": _top_coefficients(candidate, limit=14),
        "calibration": {
            "scores": calibration_metrics["scores"],
            "metrics": _summary_metrics(calibration_metrics),
            "difficulty_mismatches": calibration_metrics["difficulty_bucket"]["mismatches"],
            "wrong_pairwise_examples": calibration_metrics["pairwise_order"]["wrong_examples"][
                :detail_limit
            ],
        },
        "holdout": {
            "scores": holdout_metrics["scores"],
            "metrics": _summary_metrics(holdout_metrics),
            "worst_rows": worst_rows(holdout_context, holdout_observed, limit=detail_limit),
            "failure_clusters": _failure_clusters(
                holdout_context,
                holdout_observed,
                limit=detail_limit,
            ),
            "wrong_pairwise_examples": holdout_metrics["pairwise_order"]["wrong_examples"][
                :detail_limit
            ],
        },
        "cross_validation": dict(cross_validation or {}),
        "combined_scores": _combined_scores(calibration_metrics, holdout_metrics),
    }


def _observed_for_context(normalized: object, context: Mapping[str, object]) -> np.ndarray:
    values = np.asarray(normalized, dtype=np.float32)
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    observed = np.full(len(indices), np.nan, dtype=np.float32)
    valid = indices >= 0
    observed[valid] = values[indices[valid]]
    return observed


def _failure_clusters(
    context: Mapping[str, object],
    observed: object,
    *,
    limit: int,
) -> dict[str, object]:
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    observed_values = np.asarray(observed, dtype=np.float32)
    labels = [str(value) for value in context["labels"]]
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    rows: dict[str, list[dict[str, object]]] = {
        "beginner_easy_pushed_high": [],
        "mid_vocab_pushed_high": [],
        "upper_tail_pushed_low": [],
        "special_reading_pushed_low": [],
        "rare_wago_or_written_pushed_high": [],
        "common_kango_pushed_high": [],
    }
    signal_rows = _context_signal_rows(context)
    for index, label in enumerate(labels):
        if not np.isfinite(expected[index]) or not np.isfinite(observed_values[index]):
            continue
        delta = float(observed_values[index] - expected[index])
        absolute_error = abs(delta)
        if absolute_error < 0.25:
            continue
        signals = signal_rows[index] if index < len(signal_rows) else {}
        row = {
            "label": label,
            "expected": _rounded(float(expected[index])),
            "observed": _rounded(float(observed_values[index])),
            "absolute_error": _rounded(absolute_error),
            "direction": "too_high" if delta > 0 else "too_low",
            "component_index": int(indices[index]),
            "signals": signals,
        }
        if expected[index] <= 0.20 and delta > 0.25:
            rows["beginner_easy_pushed_high"].append(row)
        if expected[index] <= 0.50 and delta > 0.30:
            rows["mid_vocab_pushed_high"].append(row)
        if expected[index] >= 0.75 and delta < -0.25:
            rows["upper_tail_pushed_low"].append(row)
        if (
            delta < -0.25
            and max(
                _signal_value(signals, "non_standard_reading_risk"),
                _signal_value(signals, "rare_non_standard_reading_risk"),
                _signal_value(signals, "rare_wago_non_standard_reading_risk"),
            )
            >= 0.50
        ):
            rows["special_reading_pushed_low"].append(row)
        if (
            delta > 0.25
            and max(
                _signal_value(signals, "rare_wago_tail_risk"),
                _signal_value(signals, "written_wago_tail_risk"),
                _signal_value(signals, "rare_wago_obscure_written_risk"),
            )
            >= 0.25
        ):
            rows["rare_wago_or_written_pushed_high"].append(row)
        if (
            delta > 0.25
            and _signal_value(signals, "kango_mid_signal") >= 0.35
            and _signal_value(signals, "kango_common_priority_risk") <= 0.45
        ):
            rows["common_kango_pushed_high"].append(row)
    return {
        key: {
            "count": len(value),
            "examples": sorted(
                value,
                key=lambda row: float(row.get("absolute_error") or 0.0),
                reverse=True,
            )[:limit],
        }
        for key, value in rows.items()
    }


def _signal_rows_for_context(
    context: Mapping[str, object],
    component: object,
) -> list[dict[str, object]]:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    names = [str(value) for value in component["component_names"]]
    name_to_index = {name: index for index, name in enumerate(names)}
    values = np.asarray(component["component_values"], dtype=np.float32)
    present = np.asarray(component["component_present"], dtype=bool)
    rows: list[dict[str, object]] = []
    for row_index in indices:
        if row_index < 0:
            rows.append({})
            continue
        row: dict[str, object] = {}
        for signal in CLUSTER_SIGNAL_COLUMNS:
            if signal == "frequency":
                row[signal] = _rounded(float(component["frequency_values"][row_index]))
                continue
            column = name_to_index.get(signal)
            if column is None or not bool(present[row_index, column]):
                row[signal] = None
                continue
            row[signal] = _rounded(float(values[row_index, column]))
        rows.append(row)
    return rows


def _context_signal_rows(context: Mapping[str, object]) -> list[dict[str, object]]:
    rows = context.get("signal_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _signal_value(signals: Mapping[str, object], signal: str) -> float:
    parsed = _optional_float(signals.get(signal))
    return float(parsed) if parsed is not None else 0.0


def _combined_scores(
    calibration_metrics: Mapping[str, object],
    holdout_metrics: Mapping[str, object],
) -> dict[str, object]:
    calibration_score = _optional_float(
        _mapping(calibration_metrics.get("scores")).get("balanced_score")
    )
    holdout_score = _optional_float(_mapping(holdout_metrics.get("scores")).get("balanced_score"))
    if calibration_score is None or holdout_score is None:
        return {}
    return {
        "calibration_70_holdout_30": _rounded((0.7 * calibration_score) + (0.3 * holdout_score)),
        "calibration_50_holdout_50": _rounded((0.5 * calibration_score) + (0.5 * holdout_score)),
        "holdout_minus_calibration": _rounded(holdout_score - calibration_score),
    }


def _rank_candidates(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in sorted(
            rows,
            key=lambda row: (
                _optional_float(
                    _mapping(row.get("combined_scores")).get("calibration_70_holdout_30")
                )
                or -1.0,
                _optional_float(
                    _mapping(_mapping(row.get("calibration")).get("scores")).get("balanced_score")
                )
                or -1.0,
                _optional_float(
                    _mapping(_mapping(row.get("holdout")).get("scores")).get("balanced_score")
                )
                or -1.0,
            ),
            reverse=True,
        )
    ]


def _leaderboards(rows: Sequence[Mapping[str, object]], *, limit: int = 20) -> dict[str, object]:
    return {
        "combined_70_30": [
            _summary_row(row)
            for row in sorted(
                rows,
                key=lambda row: (
                    _optional_float(
                        _mapping(row.get("combined_scores")).get("calibration_70_holdout_30")
                    )
                    or -1.0
                ),
                reverse=True,
            )[:limit]
        ],
        "calibration_balanced": [
            _summary_row(row)
            for row in sorted(
                rows,
                key=lambda row: (
                    _optional_float(
                        _mapping(_mapping(row.get("calibration")).get("scores")).get(
                            "balanced_score"
                        )
                    )
                    or -1.0
                ),
                reverse=True,
            )[:limit]
        ],
        "holdout_balanced": [
            _summary_row(row)
            for row in sorted(
                rows,
                key=lambda row: (
                    _optional_float(
                        _mapping(_mapping(row.get("holdout")).get("scores")).get("balanced_score")
                    )
                    or -1.0
                ),
                reverse=True,
            )[:limit]
        ],
        "holdout_mae": [
            _summary_row(row)
            for row in sorted(
                rows,
                key=lambda row: (
                    _optional_float(
                        _mapping(_mapping(row.get("holdout")).get("scores")).get(
                            "numeric_mae_score"
                        )
                    )
                    or -1.0
                ),
                reverse=True,
            )[:limit]
        ],
        "cv_balanced_mean": [
            _summary_row(row)
            for row in sorted(
                rows,
                key=lambda row: (
                    _optional_float(_mapping(row.get("cross_validation")).get("balanced_mean"))
                    or -1.0
                ),
                reverse=True,
            )[:limit]
        ],
    }


def _summary_row(row: Mapping[str, object]) -> dict[str, object]:
    calibration = _mapping(row.get("calibration"))
    holdout = _mapping(row.get("holdout"))
    calibration_scores = _mapping(calibration.get("scores"))
    holdout_scores = _mapping(holdout.get("scores"))
    calibration_metrics = _mapping(calibration.get("metrics"))
    holdout_metrics = _mapping(holdout.get("metrics"))
    cross_validation = _mapping(row.get("cross_validation"))
    return {
        "candidate_id": row.get("candidate_id"),
        "feature_set": row.get("feature_set"),
        "alpha": row.get("alpha"),
        "target_transform": row.get("target_transform"),
        "sample_weight_mode": row.get("sample_weight_mode"),
        "combined_70_30": _mapping(row.get("combined_scores")).get("calibration_70_holdout_30"),
        "calibration_balanced": calibration_scores.get("balanced_score"),
        "calibration_mae": calibration_metrics.get("mae"),
        "holdout_balanced": holdout_scores.get("balanced_score"),
        "holdout_mae": holdout_metrics.get("mae"),
        "holdout_pairwise": holdout_metrics.get("pairwise_accuracy"),
        "cv_balanced_mean": cross_validation.get("balanced_mean"),
        "cv_balanced_std": cross_validation.get("balanced_std"),
        "cv_mae_mean": cross_validation.get("mae_mean"),
    }


def _top_coefficients(candidate: CurveCandidate, *, limit: int) -> list[dict[str, object]]:
    rows = _coefficients(candidate)
    ranked = sorted(rows, key=lambda row: abs(float(row["coefficient"] or 0.0)), reverse=True)[
        :limit
    ]
    return [dict(row) for row in ranked]


def _coefficients(candidate: CurveCandidate) -> list[dict[str, object]]:
    return [
        {
            "feature": feature,
            "coefficient": _rounded(coefficient),
            "direction": "raises_difficulty" if coefficient > 0 else "lowers_difficulty",
        }
        for feature, coefficient in zip(candidate.feature_names, candidate.coefficients)
        if abs(float(coefficient)) > 1e-9
    ]


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    method = _mapping(report.get("method"))
    lines = [
        "# en-ja Learner Difficulty Smooth Curve Search",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Model: `{_escape(method.get('model'))}`",
        f"- Calibration labels: `{_escape(inputs.get('calibration_label_count'))}`",
        f"- Holdout numeric rows: `{_escape(inputs.get('holdout_numeric_count'))}`",
        f"- Normalization population: `{_escape(inputs.get('normalization_population_count'))}`",
        f"- Feature sets: `{_escape(inputs.get('feature_set_count'))}`",
        f"- Evaluated curve candidates: `{_escape(inputs.get('candidate_count'))}`",
        f"- Cross-validation folds: `{_escape(inputs.get('cv_folds'))}`",
        "",
        "## Method",
        "",
        str(method.get("description") or ""),
        "",
        str(method.get("guardrail_note") or ""),
        "",
        "## Feature Sets",
        "",
    ]
    for spec in _mapping_rows(report.get("feature_sets")):
        lines.append(
            f"- `{_escape(spec.get('spec_id'))}`: signals `{_escape(len(_sequence_values(spec.get('signals'))))}`, "
            f"transforms `{_escape(', '.join(str(value) for value in _sequence_values(spec.get('transforms'))))}`, "
            f"interactions `{_escape(len(_sequence_values(spec.get('interactions'))))}`, "
            f"gated feature groups `{_escape(len(_sequence_values(spec.get('gated_features'))))}`"
        )
    lines.extend(["", "## Leaderboards", ""])
    for name, rows in _mapping(report.get("leaderboards")).items():
        lines.extend(
            [
                f"### `{_escape(name)}`",
                "",
                (
                    "| Rank | Candidate | Feature set | Combined | Cal balanced | "
                    "Cal MAE | Holdout balanced | Holdout MAE | Holdout pairwise | "
                    "CV balanced | CV std |"
                ),
                "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for index, row in enumerate(_mapping_rows(rows)[:12], start=1):
            lines.append(
                "| "
                f"{index} | "
                f"`{_escape(row.get('candidate_id'))}` | "
                f"`{_escape(row.get('feature_set'))}` | "
                f"`{_escape(row.get('combined_70_30'))}` | "
                f"`{_escape(row.get('calibration_balanced'))}` | "
                f"`{_escape(row.get('calibration_mae'))}` | "
                f"`{_escape(row.get('holdout_balanced'))}` | "
                f"`{_escape(row.get('holdout_mae'))}` | "
                f"`{_escape(row.get('holdout_pairwise'))}` | "
                f"`{_escape(row.get('cv_balanced_mean'))}` | "
                f"`{_escape(row.get('cv_balanced_std'))}` |"
            )
        lines.append("")
    lines.extend(["", "## Top Candidate Details", ""])
    for row in _mapping_rows(report.get("exact_top"))[:5]:
        lines.extend(_candidate_markdown(row))
    return "\n".join(lines).rstrip() + "\n"


def _candidate_markdown(row: Mapping[str, object]) -> list[str]:
    calibration = _mapping(row.get("calibration"))
    holdout = _mapping(row.get("holdout"))
    cross_validation = _mapping(row.get("cross_validation"))
    lines = [
        f"### `{_escape(row.get('candidate_id'))}`",
        "",
        f"- Feature set: `{_escape(row.get('feature_set'))}`",
        f"- Alpha: `{_escape(row.get('alpha'))}`",
        f"- Target transform: `{_escape(row.get('target_transform'))}`",
        f"- Sample weights: `{_escape(row.get('sample_weight_mode'))}`",
        f"- Combined scores: `{_compact_counts(row.get('combined_scores'))}`",
        f"- Calibration scores: `{_compact_counts(calibration.get('scores'))}`",
        f"- Calibration metrics: `{_compact_counts(calibration.get('metrics'))}`",
        f"- Holdout scores: `{_compact_counts(holdout.get('scores'))}`",
        f"- Holdout metrics: `{_compact_counts(holdout.get('metrics'))}`",
        f"- Cross-validation: `{_compact_cv(cross_validation)}`",
        "",
        "Top coefficients:",
        "",
    ]
    for item in _mapping_rows(row.get("top_coefficients"))[:12]:
        lines.append(
            f"- `{_escape(item.get('feature'))}` `{_escape(item.get('coefficient'))}` "
            f"({item.get('direction')})"
        )
    worst = _mapping_rows(holdout.get("worst_rows"))
    clusters = _mapping(holdout.get("failure_clusters"))
    if clusters:
        lines.extend(["", "Failure clusters:", ""])
        for name, cluster in clusters.items():
            cluster_map = _mapping(cluster)
            examples = ", ".join(
                str(item.get("label")) for item in _mapping_rows(cluster_map.get("examples"))[:5]
            )
            lines.append(
                f"- `{_escape(name)}` count `{_escape(cluster_map.get('count'))}`"
                + (f": {examples}" if examples else "")
            )
    if worst:
        lines.extend(["", "Worst holdout rows:", ""])
        for item in worst[:12]:
            lines.append(
                f"- `{_escape(item.get('label'))}` expected `{_escape(item.get('expected'))}`, "
                f"observed `{_escape(item.get('observed'))}`, "
                f"error `{_escape(item.get('absolute_error'))}`, "
                f"`{_escape(item.get('direction'))}`"
            )
    band_samples = _mapping_rows(row.get("band_samples"))
    if band_samples:
        lines.extend(["", "Band samples:", ""])
        for band in band_samples:
            samples = ", ".join(
                f"{sample.get('lemma')}({sample.get('reading')})"
                for sample in _mapping_rows(band.get("samples"))[:8]
            )
            lines.append(
                f"- `{_escape(band.get('band'))}` count `{_escape(band.get('count'))}`: {samples}"
            )
    lines.append("")
    return lines


def _feature_set_json(spec: FeatureSetSpec) -> dict[str, object]:
    return {
        "spec_id": spec.spec_id,
        "signals": list(spec.signals),
        "transforms": list(spec.transforms),
        "include_missing": spec.include_missing,
        "interactions": [list(pair) for pair in spec.interactions],
        "gated_features": [
            {
                "gate_signal": gated.gate_signal,
                "signals": list(gated.signals),
                "transforms": list(gated.transforms),
            }
            for gated in spec.gated_features
        ],
    }


def _compact_cv(value: object) -> str:
    cross_validation = _mapping(value)
    keys = (
        "fold_count",
        "balanced_mean",
        "balanced_std",
        "mae_mean",
        "pairwise_mean",
        "bucket_mean",
    )
    return ", ".join(
        f"{key}={_rounded(cross_validation.get(key))}" for key in keys if key in cross_validation
    )


def _compact_counts(value: object) -> str:
    if not isinstance(value, Mapping):
        return str(value)
    return ", ".join(f"{key}={_rounded(val)}" for key, val in value.items())


def _sequence_values(value: object) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return list(value)


def _alpha_id(alpha: float) -> str:
    return str(alpha).replace(".", "p")


if __name__ == "__main__":
    raise SystemExit(main())
