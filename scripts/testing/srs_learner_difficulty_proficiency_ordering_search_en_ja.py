#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_CHALLENGE_OFFSET,
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_PROFICIENCY_POINTS,
    DEFAULT_WINDOW_SIGMA,
    DEFAULT_WINDOW_TOP_K,
    LabelContext,
    _calibration_context,
    _clamp01,
    _component_context,
    _context_summary,
    _escape,
    _label_context_from_json,
    _lane_metrics,
    _load_json,
    _mapping,
    _metric_path,
    _observed_for_context,
    _optional_float,
    _parse_float_csv,
    _proficiency_dataset_report,
    _raw_scores_for_weights,
    _repo_or_home_path,
    _rounded,
    _target_curve_normalize,
    _utc_now,
)


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_proficiency_ordering_search_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_proficiency_ordering_search_en_ja_latest.md"
)
DEFAULT_GRID_UNITS = 5
DEFAULT_FORMULA_RETAIN_LIMIT = 260
DEFAULT_RESULT_RETAIN_LIMIT = 120
DEFAULT_LEADERBOARD_LIMIT = 20
DEFAULT_MAX_SHIFTS = (None, 0.08, 0.15)
DEFAULT_TRANSFORMS: Mapping[str, object] = {
    "jlpt_vocab_curve": {"N5": 0.06, "N4": 0.28, "N3": 0.50, "N2": 0.72, "N1": 0.94},
    "jlpt_kanji_dampening_strength": 0.50,
}

FEATURE_SETS: Mapping[str, tuple[str, ...]] = {
    "core_progression": (
        "frequency",
        "jmdict_priority",
        "jlpt_vocab_difficulty",
        "lesson_vocab_difficulty",
        "written_form_burden",
        "kango_mid_signal",
    ),
    "curriculum_written": (
        "frequency",
        "jlpt_vocab_difficulty",
        "lesson_vocab_difficulty",
        "kanji_grade",
        "max_written_form_burden",
        "jmdict_priority",
    ),
    "written_depth": (
        "frequency",
        "max_written_form_burden",
        "written_form_burden",
        "kanji_burden",
        "old_jlpt_kanji",
        "kango_mid_signal",
    ),
    "rare_tail": (
        "frequency",
        "rare_wago_tail_risk",
        "rare_non_standard_reading_risk",
        "max_written_form_burden",
        "kango_mid_signal",
        "jmdict_priority",
    ),
    "entity_guard": (
        "frequency",
        "max_written_form_burden",
        "kango_mid_signal",
        "proper_acronym_entity_risk",
        "candidate_deprioritized_named_frequency_risk",
        "news_abbreviation_entity_risk",
    ),
    "source_register": (
        "frequency",
        "jmdict_priority",
        "jmdict_marked_usage_risk",
        "jmdict_register_marked_risk",
        "jmdict_sinitic_source",
        "jmdict_kana_preferred_risk",
    ),
    "name_acronym": (
        "frequency",
        "named_entity_frequency_risk",
        "proper_acronym_entity_risk",
        "news_abbreviation_entity_risk",
        "acronym_default_suppress_risk",
        "jmdict_priority",
    ),
    "wtype_origin": (
        "frequency",
        "wtype_kango_risk",
        "wtype_wago_ease",
        "wtype_gairaigo_risk",
        "wtype_proper_risk",
        "kango_mid_signal",
    ),
}


@dataclass(frozen=True)
class FormulaCandidate:
    formula_id: str
    feature_set_id: str
    weights: Mapping[str, float]
    max_shift_from_frequency: float | None
    transforms: Mapping[str, object]
    missing_features: tuple[str, ...]


@dataclass(frozen=True)
class LaneRule:
    target_state: str
    signals: tuple[str, ...]
    threshold: float


@dataclass(frozen=True)
class LanePolicy:
    policy_id: str
    description: str
    rules: tuple[LaneRule, ...]


LANE_POLICIES: tuple[LanePolicy, ...] = (
    LanePolicy("current", "Use the candidate states stored in the component matrix.", ()),
    LanePolicy(
        "acronym_conservative",
        "Move high-risk acronym-like normal vocab out of the normal lane.",
        (
            LaneRule(
                "deprioritized_vocab",
                (
                    "proper_acronym_entity_risk",
                    "news_abbreviation_entity_risk",
                    "jmdict_abbreviation_risk",
                    "acronym_shared_exact_risk",
                    "acronym_topic_only_risk",
                ),
                0.65,
            ),
            LaneRule(
                "suppressed_default",
                ("acronym_default_suppress_risk", "acronym_topic_only_risk"),
                0.82,
            ),
        ),
    ),
    LanePolicy(
        "entity_conservative",
        "Move high-risk name/entity-like normal vocab into the deprioritized lane.",
        (
            LaneRule(
                "deprioritized_vocab",
                (
                    "named_entity_risk",
                    "candidate_deprioritized_named_entity_risk",
                    "candidate_deprioritized_named_frequency_risk",
                    "geopolitical_entity_risk",
                    "proper_org_entity_risk",
                    "proper_place_entity_risk",
                    "proper_country_entity_risk",
                    "news_named_entity_risk",
                ),
                0.72,
            ),
        ),
    ),
    LanePolicy(
        "non_vocab_conservative",
        "Move high-risk non-vocabulary/search-only rows out of the normal lane.",
        (
            LaneRule(
                "deprioritized_vocab",
                (
                    "jmdict_non_vocab_risk",
                    "candidate_deprioritized_vocab_risk",
                    "jmdict_search_only_form_risk",
                    "jmdict_cross_reference_risk",
                ),
                0.78,
            ),
        ),
    ),
    LanePolicy(
        "acronym_entity_conservative",
        "Combine the conservative acronym and entity demotions.",
        (
            LaneRule(
                "deprioritized_vocab",
                (
                    "proper_acronym_entity_risk",
                    "news_abbreviation_entity_risk",
                    "jmdict_abbreviation_risk",
                    "named_entity_risk",
                    "candidate_deprioritized_named_entity_risk",
                    "candidate_deprioritized_named_frequency_risk",
                    "news_named_entity_risk",
                ),
                0.68,
            ),
            LaneRule(
                "suppressed_default",
                ("acronym_default_suppress_risk", "acronym_topic_only_risk"),
                0.84,
            ),
        ),
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search en-ja learner-difficulty formulas directly against the "
            "proficiency-ordering sidecar objective. This does not change runtime behavior."
        )
    )
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument(
        "--proficiency-points",
        default=",".join(str(value) for value in DEFAULT_PROFICIENCY_POINTS),
    )
    parser.add_argument("--challenge-offset", type=float, default=DEFAULT_CHALLENGE_OFFSET)
    parser.add_argument("--window-sigma", type=float, default=DEFAULT_WINDOW_SIGMA)
    parser.add_argument("--window-top-k", type=int, default=DEFAULT_WINDOW_TOP_K)
    parser.add_argument("--grid-units", type=int, default=DEFAULT_GRID_UNITS)
    parser.add_argument(
        "--max-shifts",
        default="none,0.08,0.15",
        help="Comma-separated max shifts from frequency. Use 'none' for no cap.",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=0,
        help="Optional formula-candidate limit for smoke runs. 0 evaluates all.",
    )
    parser.add_argument(
        "--formula-retain-limit",
        type=int,
        default=DEFAULT_FORMULA_RETAIN_LIMIT,
        help="Formula count retained before applying lane-policy overlays.",
    )
    parser.add_argument("--result-retain-limit", type=int, default=DEFAULT_RESULT_RETAIN_LIMIT)
    parser.add_argument("--leaderboard-limit", type=int, default=DEFAULT_LEADERBOARD_LIMIT)
    parser.add_argument("--detail-limit", type=int, default=20)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        component_matrix_path=_resolve_path(args.component_matrix),
        holdout_json_path=_resolve_path(args.holdout_json),
        proficiency_points=_parse_float_csv(args.proficiency_points),
        challenge_offset=float(args.challenge_offset),
        window_sigma=max(1e-6, float(args.window_sigma)),
        window_top_k=max(1, int(args.window_top_k)),
        grid_units=max(1, int(args.grid_units)),
        max_shifts=_parse_max_shift_csv(args.max_shifts),
        candidate_limit=max(0, int(args.candidate_limit)),
        formula_retain_limit=max(1, int(args.formula_retain_limit)),
        result_retain_limit=max(1, int(args.result_retain_limit)),
        leaderboard_limit=max(1, int(args.leaderboard_limit)),
        detail_limit=max(1, int(args.detail_limit)),
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
    holdout_json_path: Path,
    proficiency_points: Sequence[float] = DEFAULT_PROFICIENCY_POINTS,
    challenge_offset: float = DEFAULT_CHALLENGE_OFFSET,
    window_sigma: float = DEFAULT_WINDOW_SIGMA,
    window_top_k: int = DEFAULT_WINDOW_TOP_K,
    grid_units: int = DEFAULT_GRID_UNITS,
    max_shifts: Sequence[float | None] = DEFAULT_MAX_SHIFTS,
    candidate_limit: int = 0,
    formula_retain_limit: int = DEFAULT_FORMULA_RETAIN_LIMIT,
    result_retain_limit: int = DEFAULT_RESULT_RETAIN_LIMIT,
    leaderboard_limit: int = DEFAULT_LEADERBOARD_LIMIT,
    detail_limit: int = 20,
) -> dict[str, object]:
    calibration = np.load(calibration_matrix_path)
    component = np.load(component_matrix_path)
    component_context = _component_context(component)
    calibration_context = _calibration_context(calibration, component_context)
    holdout_context = _label_context_from_json(
        _load_json(holdout_json_path),
        component_context=component_context,
        context_id="holdout",
    )
    formulas = generate_formula_candidates(
        component_names=component_context.component_names,
        grid_units=grid_units,
        max_shifts=max_shifts,
    )
    if candidate_limit > 0:
        formulas = formulas[:candidate_limit]

    reference = _reference_reports(
        component_context=component_context,
        calibration_context=calibration_context,
        holdout_context=holdout_context,
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    retained_formulas = _retain_formulas_by_calibration(
        formulas,
        component_context=component_context,
        calibration_context=calibration_context,
        reference=reference["current_production"],
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
        limit=formula_retain_limit,
    )
    policy_contexts = _policy_contexts(
        component_context=component_context,
        calibration_context=calibration_context,
        holdout_context=holdout_context,
    )
    results = _evaluate_formula_policy_results(
        retained_formulas,
        policy_contexts=policy_contexts,
        component_context=component_context,
        reference=reference["current_production"],
        proficiency_points=proficiency_points,
        challenge_offset=challenge_offset,
        window_sigma=window_sigma,
        window_top_k=window_top_k,
        detail_limit=detail_limit,
    )
    retained_results = _retained_results(results, limit=result_retain_limit)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "search_run": True,
        "method": {
            "purpose": (
                "Sidecar search for formulas optimized directly against the "
                "single-proficiency ordering objective."
            ),
            "selection_rule": (
                "Formula weights are fitted on calibration only. Holdout is "
                "reported as a non-selector generalization check."
            ),
            "structural_difference_from_trace_sweep": (
                "This script generates new curated signal mixtures and lane "
                "overlays, then scores them under the proficiency-ordering metric. "
                "It does not compete on the older balanced sweep objective."
            ),
            "frontier_proxy": (
                "For user proficiency p, the ranking is judged by whether words "
                "near clamp(p + challenge_offset, 0, 1) surface in the frontier."
            ),
            "target_curve_id": TARGET_CURVE_ID,
            "feature_sets": {
                key: [name for name in value] for key, value in sorted(FEATURE_SETS.items())
            },
            "lane_policies": {policy.policy_id: policy.description for policy in LANE_POLICIES},
        },
        "parameters": {
            "grid_units": int(grid_units),
            "max_shifts": [_format_max_shift(value) for value in max_shifts],
            "candidate_limit": int(candidate_limit),
            "formula_retain_limit": int(formula_retain_limit),
            "result_retain_limit": int(result_retain_limit),
            "leaderboard_limit": int(leaderboard_limit),
            "proficiency_points": [round(float(value), 6) for value in proficiency_points],
            "challenge_offset": round(float(challenge_offset), 6),
            "window_sigma": round(float(window_sigma), 6),
            "window_top_k": int(window_top_k),
        },
        "inputs": {
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "generated_formula_count": len(
                generate_formula_candidates(
                    component_names=component_context.component_names,
                    grid_units=grid_units,
                    max_shifts=max_shifts,
                )
            ),
            "evaluated_formula_count": len(formulas),
            "retained_formula_count": len(retained_formulas),
            "evaluated_formula_policy_count": len(results),
            "calibration_label_count": len(calibration_context.labels),
            "holdout_label_count": len(holdout_context.labels),
            "normalization_population_count": len(component_context.lemmas),
        },
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "calibration_matrix": calibration_matrix_path,
                "component_matrix": component_matrix_path,
                "holdout_json": holdout_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "normalization": SCRIPT_DIR / "srs_learner_difficulty_normalization.py",
                "proficiency_ordering": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_en_ja.py",
            },
            version_constants={"target_curve": TARGET_CURVE_ID},
            argv=sys.argv,
        ),
        "dataset_summaries": {
            "calibration": _context_summary(calibration_context),
            "holdout": _context_summary(holdout_context),
        },
        "reference_candidates": reference,
        "lane_policy_diagnostics": {
            key: value["diagnostics"] for key, value in policy_contexts.items()
        },
        "leaderboards": {
            "calibration_proficiency_ordering": _leaderboard(
                results,
                dataset="calibration",
                limit=leaderboard_limit,
            ),
            "calibration_guardrail_passing": _leaderboard(
                [row for row in results if _guardrails_pass(row)],
                dataset="calibration",
                limit=leaderboard_limit,
            ),
            "holdout_of_calibration_winners": _leaderboard(
                sorted(
                    results,
                    key=lambda row: _candidate_metric(row, "calibration"),
                    reverse=True,
                )[:leaderboard_limit],
                dataset="holdout",
                limit=leaderboard_limit,
                keep_order=True,
            ),
            "holdout_proficiency_ordering_oracle": _leaderboard(
                results,
                dataset="holdout",
                limit=leaderboard_limit,
            ),
            "holdout_window_quality_oracle": _leaderboard(
                sorted(
                    results,
                    key=lambda row: _metric_path(
                        row,
                        "holdout",
                        "frontier_windows",
                        "average_window_score",
                    ),
                    reverse=True,
                ),
                dataset="holdout",
                limit=leaderboard_limit,
                keep_order=True,
            ),
        },
        "primary_candidates": {
            "calibration_selector": _candidate_summary(
                _top_candidate(results, "calibration"),
                dataset="calibration",
            ),
            "calibration_guardrail_selector": _candidate_summary(
                _top_candidate([row for row in results if _guardrails_pass(row)], "calibration"),
                dataset="calibration",
            ),
            "holdout_oracle": _candidate_summary(
                _top_candidate(results, "holdout"),
                dataset="holdout",
            ),
        },
        "retained_formulas": [_formula_summary(row) for row in retained_formulas[:50]],
        "candidate_results": retained_results,
    }


def generate_formula_candidates(
    *,
    component_names: Sequence[str],
    grid_units: int,
    max_shifts: Sequence[float | None] = DEFAULT_MAX_SHIFTS,
) -> list[FormulaCandidate]:
    available = set(str(name) for name in component_names)
    candidates: list[FormulaCandidate] = []
    seen = set()
    serial = 0
    for feature_set_id, features in sorted(FEATURE_SETS.items()):
        present_features = tuple(name for name in features if name in available)
        missing_features = tuple(name for name in features if name not in available)
        if "frequency" not in present_features or len(present_features) < 2:
            continue
        for integer_weights in _integer_weight_units(
            len(present_features),
            total_units=grid_units,
            required_index=present_features.index("frequency"),
        ):
            weights = {
                name: units / float(grid_units)
                for name, units in zip(present_features, integer_weights)
                if units > 0
            }
            for max_shift in max_shifts:
                key = (
                    tuple(sorted((name, round(value, 6)) for name, value in weights.items())),
                    _format_max_shift(max_shift),
                )
                if key in seen:
                    continue
                seen.add(key)
                serial += 1
                candidates.append(
                    FormulaCandidate(
                        formula_id=(
                            f"po_search_{serial:05d}__{feature_set_id}"
                            f"__cap{_format_max_shift(max_shift)}"
                        ),
                        feature_set_id=feature_set_id,
                        weights=weights,
                        max_shift_from_frequency=max_shift,
                        transforms=DEFAULT_TRANSFORMS,
                        missing_features=missing_features,
                    )
                )
    return candidates


def _integer_weight_units(
    width: int,
    *,
    total_units: int,
    required_index: int,
) -> Iterable[tuple[int, ...]]:
    current = [0] * width

    def visit(index: int, remaining: int) -> Iterable[tuple[int, ...]]:
        if index == width - 1:
            current[index] = remaining
            if current[required_index] > 0:
                yield tuple(current)
            return
        for value in range(remaining + 1):
            current[index] = value
            yield from visit(index + 1, remaining - value)

    yield from visit(0, total_units)


def _retain_formulas_by_calibration(
    formulas: Sequence[FormulaCandidate],
    *,
    component_context: object,
    calibration_context: LabelContext,
    reference: Mapping[str, object],
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
    limit: int,
) -> list[Mapping[str, object]]:
    rows = []
    for formula in formulas:
        normalized = _normalized_values_for_formula(formula, component_context)
        observed = _observed_for_context(normalized, calibration_context)
        calibration = _proficiency_dataset_report(
            calibration_context,
            observed,
            proficiency_points=proficiency_points,
            challenge_offset=challenge_offset,
            window_sigma=window_sigma,
            window_top_k=window_top_k,
            detail_limit=detail_limit,
        )
        rows.append(
            {
                "formula": formula,
                "calibration": calibration,
                "guardrails": _guardrail_report(calibration, reference["calibration"]),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            bool(_mapping(row.get("guardrails")).get("passes")),
            _metric_path(row, "calibration", "proficiency_ordering_score"),
            _metric_path(row, "calibration", "normal_vocab", "scores", "pairwise_order_score"),
            _metric_path(row, "calibration", "frontier_windows", "average_window_score"),
        ),
        reverse=True,
    )[:limit]


def _evaluate_formula_policy_results(
    retained_formulas: Sequence[Mapping[str, object]],
    *,
    policy_contexts: Mapping[str, Mapping[str, object]],
    component_context: object,
    reference: Mapping[str, object],
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
) -> list[dict[str, object]]:
    results = []
    for formula_row in retained_formulas:
        formula = formula_row["formula"]
        if not isinstance(formula, FormulaCandidate):
            continue
        normalized = _normalized_values_for_formula(formula, component_context)
        for policy_id, policy_row in policy_contexts.items():
            calibration_context = policy_row["calibration_context"]
            holdout_context = policy_row["holdout_context"]
            if not isinstance(calibration_context, LabelContext):
                continue
            if not isinstance(holdout_context, LabelContext):
                continue
            calibration_observed = _observed_for_context(normalized, calibration_context)
            holdout_observed = _observed_for_context(normalized, holdout_context)
            calibration = _proficiency_dataset_report(
                calibration_context,
                calibration_observed,
                proficiency_points=proficiency_points,
                challenge_offset=challenge_offset,
                window_sigma=window_sigma,
                window_top_k=window_top_k,
                detail_limit=detail_limit,
            )
            holdout = _proficiency_dataset_report(
                holdout_context,
                holdout_observed,
                proficiency_points=proficiency_points,
                challenge_offset=challenge_offset,
                window_sigma=window_sigma,
                window_top_k=window_top_k,
                detail_limit=detail_limit,
            )
            candidate_id = f"{formula.formula_id}__lane_{policy_id}"
            results.append(
                {
                    "candidate_id": candidate_id,
                    "source": "proficiency_ordering_search",
                    "feature_set_id": formula.feature_set_id,
                    "formula_id": formula.formula_id,
                    "lane_policy": policy_id,
                    "weights": {key: _rounded(value) for key, value in formula.weights.items()},
                    "max_shift_from_frequency": _rounded(formula.max_shift_from_frequency),
                    "transforms": formula.transforms,
                    "missing_features": list(formula.missing_features),
                    "calibration": calibration,
                    "holdout": holdout,
                    "guardrails": _guardrail_report(calibration, reference["calibration"]),
                    "generalization": {
                        "score_delta_holdout_minus_calibration": _rounded(
                            _metric_path(holdout, "proficiency_ordering_score")
                            - _metric_path(calibration, "proficiency_ordering_score")
                        ),
                        "normal_vocab_mae_delta_holdout_minus_calibration": _rounded(
                            _metric_path(holdout, "normal_vocab", "metrics", "mae")
                            - _metric_path(calibration, "normal_vocab", "metrics", "mae")
                        ),
                        "window_quality_delta_holdout_minus_calibration": _rounded(
                            _metric_path(holdout, "frontier_windows", "average_window_score")
                            - _metric_path(
                                calibration,
                                "frontier_windows",
                                "average_window_score",
                            )
                        ),
                    },
                }
            )
    return results


def _reference_reports(
    *,
    component_context: object,
    calibration_context: LabelContext,
    holdout_context: LabelContext,
    proficiency_points: Sequence[float],
    challenge_offset: float,
    window_sigma: float,
    window_top_k: int,
    detail_limit: int,
) -> dict[str, dict[str, object]]:
    references = {}
    for reference_id, normalized in (
        (
            "current_production",
            _target_curve_normalize(
                component_context.current_values,
                target_positions=component_context.target_curve_positions,
            ),
        ),
        (
            "frequency_only",
            _target_curve_normalize(
                np.nan_to_num(component_context.frequency_values, nan=0.0),
                target_positions=component_context.target_curve_positions,
            ),
        ),
    ):
        calibration_observed = _observed_for_context(normalized, calibration_context)
        holdout_observed = _observed_for_context(normalized, holdout_context)
        references[reference_id] = {
            "candidate_id": reference_id,
            "source": "reference",
            "lane_policy": "current",
            "calibration": _proficiency_dataset_report(
                calibration_context,
                calibration_observed,
                proficiency_points=proficiency_points,
                challenge_offset=challenge_offset,
                window_sigma=window_sigma,
                window_top_k=window_top_k,
                detail_limit=detail_limit,
            ),
            "holdout": _proficiency_dataset_report(
                holdout_context,
                holdout_observed,
                proficiency_points=proficiency_points,
                challenge_offset=challenge_offset,
                window_sigma=window_sigma,
                window_top_k=window_top_k,
                detail_limit=detail_limit,
            ),
        }
    return references


def _policy_contexts(
    *,
    component_context: object,
    calibration_context: LabelContext,
    holdout_context: LabelContext,
) -> dict[str, Mapping[str, object]]:
    rows = {}
    for policy in LANE_POLICIES:
        states, diagnostics = _apply_lane_policy_to_states(component_context, policy)
        if policy.policy_id == "current":
            rows[policy.policy_id] = {
                "calibration_context": calibration_context,
                "holdout_context": holdout_context,
                "diagnostics": {
                    **diagnostics,
                    "calibration_lane": _lane_metrics(calibration_context),
                    "holdout_lane": _lane_metrics(holdout_context),
                },
            }
            continue
        policy_calibration = _context_with_observed_states(calibration_context, states)
        policy_holdout = _context_with_observed_states(holdout_context, states)
        rows[policy.policy_id] = {
            "calibration_context": policy_calibration,
            "holdout_context": policy_holdout,
            "diagnostics": {
                **diagnostics,
                "calibration_lane": _lane_metrics(policy_calibration),
                "holdout_lane": _lane_metrics(policy_holdout),
            },
        }
    return rows


def _apply_lane_policy_to_states(
    component_context: object,
    policy: LanePolicy,
) -> tuple[object, dict[str, object]]:
    states = np.asarray(component_context.candidate_states, dtype="<U64").copy()
    if not policy.rules:
        return states, {
            "policy_id": policy.policy_id,
            "description": policy.description,
            "changed_count": 0,
            "deprioritized_count": 0,
            "suppressed_count": 0,
            "rule_trigger_counts": {},
            "missing_rule_signals": [],
        }
    normal_mask = states == "normal_vocab"
    deprioritize = np.zeros(len(states), dtype=bool)
    suppress = np.zeros(len(states), dtype=bool)
    trigger_counts = {}
    missing_signals = set()
    for rule in policy.rules:
        risk, used, missing = _max_signal(component_context, rule.signals)
        missing_signals.update(missing)
        if not used:
            continue
        mask = normal_mask & np.isfinite(risk) & (risk >= float(rule.threshold))
        trigger_counts[f"{rule.target_state}@{rule.threshold:.2f}:{'+'.join(used)}"] = int(
            mask.sum()
        )
        if rule.target_state == "suppressed_default":
            suppress |= mask
        elif rule.target_state == "deprioritized_vocab":
            deprioritize |= mask
    states[deprioritize] = "deprioritized_vocab"
    states[suppress] = "suppressed_default"
    changed = states != np.asarray(component_context.candidate_states, dtype="<U64")
    return states, {
        "policy_id": policy.policy_id,
        "description": policy.description,
        "changed_count": int(changed.sum()),
        "deprioritized_count": int((states == "deprioritized_vocab").sum()),
        "suppressed_count": int((states == "suppressed_default").sum()),
        "rule_trigger_counts": dict(sorted(trigger_counts.items())),
        "missing_rule_signals": sorted(missing_signals),
    }


def _max_signal(
    component_context: object,
    signal_names: Sequence[str],
) -> tuple[object, tuple[str, ...], tuple[str, ...]]:
    component_names = tuple(str(name) for name in component_context.component_names)
    name_to_index = {name: index for index, name in enumerate(component_names)}
    risk = np.zeros(len(component_context.lemmas), dtype=np.float32)
    used = []
    missing = []
    for name in signal_names:
        index = name_to_index.get(name)
        if index is None:
            missing.append(name)
            continue
        values = np.asarray(component_context.component_values[:, index], dtype=np.float32)
        present = np.asarray(component_context.component_present[:, index], dtype=bool)
        risk = np.maximum(risk, np.where(present, values, 0.0))
        used.append(name)
    return risk, tuple(used), tuple(missing)


def _context_with_observed_states(
    context: LabelContext,
    full_states: object,
) -> LabelContext:
    indices = np.asarray(context.component_indices, dtype=np.int64)
    observed = np.full(len(indices), "", dtype="<U64")
    valid = indices >= 0
    observed[valid] = np.asarray(full_states, dtype="<U64")[indices[valid]]
    return LabelContext(
        context_id=context.context_id,
        labels=context.labels,
        lemmas=context.lemmas,
        readings=context.readings,
        component_indices=context.component_indices,
        expected_values=context.expected_values,
        expected_bands=context.expected_bands,
        expected_candidate_states=context.expected_candidate_states,
        observed_candidate_states=observed,
        missing_rows=context.missing_rows,
    )


def _normalized_values_for_formula(
    formula: FormulaCandidate,
    component_context: object,
) -> object:
    raw = _raw_scores_for_weights(
        weights=formula.weights,
        max_shift_from_frequency=formula.max_shift_from_frequency,
        transforms=formula.transforms,
        context=component_context,
    )
    return _target_curve_normalize(raw, target_positions=component_context.target_curve_positions)


def _guardrail_report(
    candidate_report: Mapping[str, object],
    reference_report: Mapping[str, object],
) -> dict[str, object]:
    checks = {
        "score_not_below_reference": (
            _metric_path(candidate_report, "proficiency_ordering_score"),
            _metric_path(reference_report, "proficiency_ordering_score"),
            0.0,
        ),
        "normal_vocab_pairwise_within_002": (
            _metric_path(candidate_report, "normal_vocab", "scores", "pairwise_order_score"),
            _metric_path(reference_report, "normal_vocab", "scores", "pairwise_order_score"),
            0.02,
        ),
        "window_quality_within_003": (
            _metric_path(candidate_report, "frontier_windows", "average_window_score"),
            _metric_path(reference_report, "frontier_windows", "average_window_score"),
            0.03,
        ),
        "lane_f1_within_003": (
            _metric_path(candidate_report, "lane", "normal_vocab_f1"),
            _metric_path(reference_report, "lane", "normal_vocab_f1"),
            0.03,
        ),
        "default_lane_within_002": (
            _metric_path(candidate_report, "lane", "default_accept_accuracy"),
            _metric_path(reference_report, "lane", "default_accept_accuracy"),
            0.02,
        ),
    }
    rows = {}
    passes = True
    for key, (observed, reference, tolerance) in checks.items():
        passed = observed + tolerance >= reference
        rows[key] = {
            "observed": _rounded(observed),
            "reference": _rounded(reference),
            "tolerance": _rounded(tolerance),
            "passes": bool(passed),
        }
        passes = passes and passed
    return {"passes": bool(passes), "checks": rows}


def _guardrails_pass(row: Mapping[str, object]) -> bool:
    return bool(_mapping(row.get("guardrails")).get("passes"))


def _retained_results(
    results: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    selected = []
    seen = set()
    for dataset in ("calibration", "holdout"):
        ranked = sorted(
            results,
            key=lambda row: _candidate_metric(row, dataset),
            reverse=True,
        )
        for row in ranked:
            candidate_id = str(row.get("candidate_id") or "")
            if candidate_id and candidate_id not in seen:
                selected.append(dict(row))
                seen.add(candidate_id)
            if len(selected) >= limit:
                return selected
    return selected


def _leaderboard(
    candidates: Sequence[Mapping[str, object]],
    *,
    dataset: str,
    limit: int,
    keep_order: bool = False,
) -> list[dict[str, object]]:
    rows = list(candidates)
    if not keep_order:
        rows = sorted(
            rows,
            key=lambda row: _candidate_metric(row, dataset),
            reverse=True,
        )
    return [_candidate_summary(row, dataset=dataset) for row in rows[:limit]]


def _top_candidate(
    candidates: Sequence[Mapping[str, object]],
    dataset: str,
) -> Mapping[str, object]:
    if not candidates:
        return {}
    return max(candidates, key=lambda row: _candidate_metric(row, dataset))


def _candidate_metric(row: Mapping[str, object], dataset: str) -> float:
    return _metric_path(row, dataset, "proficiency_ordering_score")


def _candidate_summary(
    row: Mapping[str, object],
    *,
    dataset: str,
) -> dict[str, object]:
    dataset_report = _mapping(row.get(dataset))
    normal_vocab = _mapping(dataset_report.get("normal_vocab"))
    metrics = _mapping(normal_vocab.get("metrics"))
    scores = _mapping(normal_vocab.get("scores"))
    windows = _mapping(dataset_report.get("frontier_windows"))
    lane = _mapping(dataset_report.get("lane"))
    return {
        "candidate_id": row.get("candidate_id"),
        "source": row.get("source"),
        "feature_set_id": row.get("feature_set_id"),
        "formula_id": row.get("formula_id"),
        "lane_policy": row.get("lane_policy"),
        "guardrails_pass": _mapping(row.get("guardrails")).get("passes"),
        "proficiency_ordering_score": dataset_report.get("proficiency_ordering_score"),
        "normal_vocab_mae": metrics.get("mae"),
        "normal_vocab_bucket": metrics.get("bucket_accuracy"),
        "normal_vocab_pairwise": scores.get("pairwise_order_score"),
        "normal_vocab_spearman": metrics.get("spearman"),
        "window_quality": windows.get("average_window_score"),
        "normal_vocab_f1": lane.get("normal_vocab_f1"),
        "default_accept_accuracy": lane.get("default_accept_accuracy"),
        "calibration_score": _metric_path(row, "calibration", "proficiency_ordering_score"),
        "holdout_score": _metric_path(row, "holdout", "proficiency_ordering_score"),
    }


def _formula_summary(row: Mapping[str, object]) -> dict[str, object]:
    formula = row.get("formula")
    if not isinstance(formula, FormulaCandidate):
        return {}
    return {
        "formula_id": formula.formula_id,
        "feature_set_id": formula.feature_set_id,
        "weights": {key: _rounded(value) for key, value in formula.weights.items()},
        "max_shift_from_frequency": _rounded(formula.max_shift_from_frequency),
        "missing_features": list(formula.missing_features),
        "calibration_score_current_lane": _metric_path(
            row,
            "calibration",
            "proficiency_ordering_score",
        ),
        "guardrails_pass": _mapping(row.get("guardrails")).get("passes"),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    method = _mapping(report.get("method"))
    lines = [
        "# en-ja Learner Difficulty Proficiency Ordering Search Sidecar",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Search run: `{_escape(report.get('search_run'))}`",
        f"- Evaluated formulas: `{_escape(inputs.get('evaluated_formula_count'))}`",
        f"- Retained formulas: `{_escape(inputs.get('retained_formula_count'))}`",
        f"- Formula/policy results: `{_escape(inputs.get('evaluated_formula_policy_count'))}`",
        f"- Calibration labels: `{_escape(inputs.get('calibration_label_count'))}`",
        f"- Holdout labels: `{_escape(inputs.get('holdout_label_count'))}`",
        "",
        "## Method",
        "",
        str(method.get("purpose") or ""),
        "",
        str(method.get("selection_rule") or ""),
        "",
        str(method.get("structural_difference_from_trace_sweep") or ""),
        "",
        str(method.get("frontier_proxy") or ""),
        "",
    ]
    lines.extend(_reference_section(report))
    lines.extend(
        _leaderboard_section(
            report,
            "calibration_proficiency_ordering",
            "Calibration Selector",
            dataset_label="calibration",
        )
    )
    lines.extend(
        _leaderboard_section(
            report,
            "calibration_guardrail_passing",
            "Calibration Selector With Guardrails",
            dataset_label="calibration",
        )
    )
    lines.extend(
        _leaderboard_section(
            report,
            "holdout_of_calibration_winners",
            "Holdout Report For Calibration Winners",
            dataset_label="holdout",
        )
    )
    lines.extend(
        _leaderboard_section(
            report,
            "holdout_proficiency_ordering_oracle",
            "Holdout Oracle Diagnostic",
            dataset_label="holdout",
        )
    )
    lines.extend(_lane_policy_section(report))
    return "\n".join(lines).rstrip() + "\n"


def _reference_section(report: Mapping[str, object]) -> list[str]:
    references = _mapping(report.get("reference_candidates"))
    lines = ["## References", ""]
    lines.append("| Reference | Dataset | Score | MAE | Pairwise | Window | Lane F1 |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for reference_id, reference in sorted(references.items()):
        reference_row = _mapping(reference)
        for dataset in ("calibration", "holdout"):
            summary = _candidate_summary(reference_row, dataset=dataset)
            lines.append(
                f"| `{_escape(reference_id)}` | `{dataset}` | "
                f"`{_escape(summary.get('proficiency_ordering_score'))}` | "
                f"`{_escape(summary.get('normal_vocab_mae'))}` | "
                f"`{_escape(summary.get('normal_vocab_pairwise'))}` | "
                f"`{_escape(summary.get('window_quality'))}` | "
                f"`{_escape(summary.get('normal_vocab_f1'))}` |"
            )
    lines.append("")
    return lines


def _leaderboard_section(
    report: Mapping[str, object],
    key: str,
    title: str,
    *,
    dataset_label: str,
) -> list[str]:
    rows = _mapping_rows(_mapping(report.get("leaderboards")).get(key))
    lines = [f"## {title}", ""]
    if not rows:
        lines.extend(["No rows.", ""])
        return lines
    lines.append(
        "| Rank | Candidate | Feature Set | Lane | Guardrails | Score | "
        "MAE | Pairwise | Window | Cal Score | Holdout Score |"
    )
    lines.append("| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for index, row in enumerate(rows, start=1):
        lines.append(
            f"| {index} | `{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('feature_set_id'))}` | "
            f"`{_escape(row.get('lane_policy'))}` | "
            f"`{_escape(row.get('guardrails_pass'))}` | "
            f"`{_escape(row.get('proficiency_ordering_score'))}` | "
            f"`{_escape(row.get('normal_vocab_mae'))}` | "
            f"`{_escape(row.get('normal_vocab_pairwise'))}` | "
            f"`{_escape(row.get('window_quality'))}` | "
            f"`{_escape(row.get('calibration_score'))}` | "
            f"`{_escape(row.get('holdout_score'))}` |"
        )
    lines.append("")
    lines.append(f"Dataset scored in this table: `{dataset_label}`.")
    lines.append("")
    return lines


def _lane_policy_section(report: Mapping[str, object]) -> list[str]:
    diagnostics = _mapping(report.get("lane_policy_diagnostics"))
    lines = ["## Lane Policy Diagnostics", ""]
    lines.append("| Policy | Changed | Calibration F1 | Holdout F1 | Missing Signals |")
    lines.append("| --- | ---: | ---: | ---: | --- |")
    for policy_id, raw in sorted(diagnostics.items()):
        row = _mapping(raw)
        calibration_lane = _mapping(row.get("calibration_lane"))
        holdout_lane = _mapping(row.get("holdout_lane"))
        missing = ", ".join(str(value) for value in row.get("missing_rule_signals") or [])
        lines.append(
            f"| `{_escape(policy_id)}` | `{_escape(row.get('changed_count'))}` | "
            f"`{_escape(calibration_lane.get('normal_vocab_f1'))}` | "
            f"`{_escape(holdout_lane.get('normal_vocab_f1'))}` | "
            f"`{_escape(missing)}` |"
        )
    lines.append("")
    return lines


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _parse_max_shift_csv(raw: str) -> tuple[float | None, ...]:
    values: list[float | None] = []
    for part in str(raw or "").split(","):
        text = part.strip().lower()
        if not text:
            continue
        if text in {"none", "null", "no", "off"}:
            values.append(None)
        else:
            values.append(max(0.0, float(text)))
    return tuple(values) or DEFAULT_MAX_SHIFTS


def _format_max_shift(value: float | None) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return "none"
    return f"{int(round(_clamp01(parsed) * 100)):03d}"


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
