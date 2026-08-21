#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_metrics,
    _summary_metrics,
)


PAIR = "en-de"
PRIMARY_STATE = "normal_vocab"
DEFAULT_ROWS_JSONL = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_de_rows_latest.jsonl"
)
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_de.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_de.json"
)
DEFAULT_PRODUCT_OBJECTIVE_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_product_objective_en_de.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_formula_sweep_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_formula_sweep_en_de_latest.md"
)
COARSE_SAMPLE_ANCHORS = (
    "_src0_",
    "_wf10_",
    "_wf22_",
    "_sub15_",
    "_modern20_",
    "_goethea1_60_",
    "_goethestem35_",
    "_pedagogical_mix_",
    "_wordfreq_tail18_",
    "_subtitles_tail10_",
    "_modern_child_tail_",
    "_absence_medium",
    "_learnbackoff",
    "_sensepos",
    "_domaincmp",
    "_function",
    "_smartguards",
    "_struct",
)
DEFAULT_PRODUCT_OBJECTIVE_SAMPLE_SIZE = 500
PRODUCT_OBJECTIVE_SAMPLE_SEED = "en-de-product-objective-distribution-v1"


@dataclass(frozen=True)
class FormulaCandidate:
    candidate_id: str
    rank_weight: float
    rank_gamma: float
    pmw_gamma: float
    warp_gamma: float
    wordfreq_weight: float
    wordfreq_gamma: float
    subtitles_weight: float
    subtitles_gamma: float
    up_weights: Mapping[str, float]
    down_weights: Mapping[str, float]
    up_cap: float
    down_cap: float
    description: str
    ease_backoff_weights: Mapping[str, float] = field(default_factory=dict)
    ease_backoff_cap: float = 0.0
    floor_weights: Mapping[str, float] = field(default_factory=dict)
    floor_cap: float = 0.0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run an en-de learner-difficulty formula sweep over sidecar signal-palette "
            "rows. This does not change production ranking or runtime behavior."
        )
    )
    parser.add_argument("--rows-jsonl", type=Path, default=DEFAULT_ROWS_JSONL)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument(
        "--product-objective-json", type=Path, default=DEFAULT_PRODUCT_OBJECTIVE_JSON
    )
    parser.add_argument(
        "--product-objective-sample-size",
        type=int,
        default=DEFAULT_PRODUCT_OBJECTIVE_SAMPLE_SIZE,
        help=(
            "Deterministic row sample used for the soft distribution objective. "
            "Zero disables the distribution part while keeping sentinel checks."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--candidate-grid",
        choices=("broad", "refined", "floor_refined"),
        default="broad",
        help=(
            "Candidate family to evaluate. `refined` focuses around the best coarse en-de "
            "region; `floor_refined` narrows around structural-floor winners."
        ),
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=0,
        help="Optional deterministic candidate cap. Zero evaluates all candidates.",
    )
    parser.add_argument(
        "--candidate-sample-mode",
        choices=("coarse", "head"),
        default="coarse",
        help=(
            "How to apply --max-candidates. `coarse` spreads candidates across the full "
            "grid; `head` keeps the original first-N smoke behavior."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        signal_rows=_load_jsonl(Path(args.rows_jsonl).expanduser()),
        calibration_payload=_load_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_json(Path(args.holdout_json).expanduser()),
        product_objective_payload=_load_optional_json(
            Path(args.product_objective_json).expanduser()
        ),
        product_objective_sample_size=max(0, int(args.product_objective_sample_size)),
        candidate_grid=str(args.candidate_grid),
        max_candidates=max(0, int(args.max_candidates)),
        candidate_sample_mode=str(args.candidate_sample_mode),
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
    signal_rows: Sequence[Mapping[str, object]],
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    product_objective_payload: Mapping[str, object] | None = None,
    product_objective_sample_size: int = DEFAULT_PRODUCT_OBJECTIVE_SAMPLE_SIZE,
    candidate_grid: str = "broad",
    max_candidates: int = 0,
    candidate_sample_mode: str = "coarse",
    generated_at: str | None = None,
) -> dict[str, object]:
    rows = [dict(row) for row in signal_rows if str(row.get("lemma") or "").strip()]
    if not rows:
        raise ValueError("signal_rows must contain rows")
    rows_by_lemma = {str(row.get("lemma") or "").strip().lower(): row for row in rows}
    calibration_labels = [
        _as_mapping(row) for row in _as_sequence(calibration_payload.get("labels"))
    ]
    holdout_labels = [_as_mapping(row) for row in _as_sequence(holdout_payload.get("labels"))]
    product_context = _build_product_objective_context(
        rows=rows,
        rows_by_lemma=rows_by_lemma,
        payload=_as_mapping(product_objective_payload),
        sample_size=max(0, int(product_objective_sample_size)),
    )
    all_candidates = list(generate_candidates(candidate_grid=candidate_grid))
    candidates = _select_candidates(
        all_candidates,
        max_candidates=max_candidates,
        sample_mode=candidate_sample_mode,
    )

    records = [
        _candidate_record(
            candidate=candidate,
            rows_by_lemma=rows_by_lemma,
            calibration_labels=calibration_labels,
            holdout_labels=holdout_labels,
            product_context=product_context,
        )
        for candidate in candidates
    ]
    raw_frequency_record = next(
        (record for record in records if record.get("candidate_id") == "raw_frequency_blend"),
        {},
    )
    calibration_top = sorted(records, key=_calibration_sort_key, reverse=True)[:30]
    holdout_guarded_top = sorted(records, key=_holdout_guarded_sort_key, reverse=True)[:30]
    stable_top = sorted(records, key=_stable_sort_key, reverse=True)[:30]
    product_top = sorted(records, key=_product_sort_key, reverse=True)[:30]
    selected = _unique_records(
        calibration_top[:5] + holdout_guarded_top[:5] + stable_top[:5] + product_top[:5],
        key="candidate_id",
    )
    selected_details = [
        _with_change_samples(
            record,
            rows=rows,
            candidate=_candidate_by_id(candidates, str(record.get("candidate_id"))),
            sample_limit=12,
        )
        for record in selected
    ]
    best_calibration = calibration_top[0] if calibration_top else {}
    best_guarded = holdout_guarded_top[0] if holdout_guarded_top else {}
    best_stable = stable_top[0] if stable_top else {}
    best_product = product_top[0] if product_top else {}
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_de_learner_difficulty_formula_sweep_ready",
        "generated_at": generated_at or _utc_now(),
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "method": {
            "formula_source": "srs_learner_difficulty_signal_palette_en_de row signals",
            "metric_source": "srs_learner_difficulty_piecewise_search_en_ja shared metric helpers",
            "candidate_grid": candidate_grid,
            "candidate_count": len(candidates),
            "total_candidate_count": len(all_candidates),
            "candidate_sample_mode": candidate_sample_mode if max_candidates else "full",
            "candidate_sample_limit": max_candidates or None,
            "product_objective_id": product_context.get("objective_id"),
            "product_objective_distribution_sample_count": product_context.get(
                "distribution_sample_count"
            ),
            "product_objective_sentinel_count": product_context.get("sentinel_count"),
            "product_objective_sentinel_policy": product_context.get("sentinel_policy"),
            "product_objective_policy": (
                "Soft development objective: blend calibration/holdout label score with "
                "a sampled full-corpus CDF target and sentinel ceiling/floor cohorts. "
                "This changes sidecar selection evidence only; it does not mutate scores."
            ),
            "primary_score_policy": (
                "Primary metrics exclude labels whose expected_candidate_state is not "
                "`normal_vocab`; restricted rows remain available for product cleanup but "
                "do not train numeric formula accuracy."
            ),
            "encoded_pillars": [
                "frequency curve shape",
                "modern frequency source blending",
                "form/POS quality guards",
                "cognate and English-transparency ease",
                "compound/length risk",
                "translation ambiguity/polysemy risk",
                "learner-source ambiguity backoff",
                "sense/POS artifact guards",
                "domain-compound floors",
                "function-word floors",
                "Wiktionary marked/form/ambiguity guards",
                "tail absence-of-signal risk",
                "learner-source CEFR/core-list soft ceilings",
                "Goethe official A1 exact soft ceiling",
                "Klexikon child/simple-concept tail ceiling",
                "wordfreq/OpenSubtitles modern tail rescue",
                "weak topic-documented tail/tiebreak ease",
                "global monotone warp",
            ],
            "topic_policy": (
                "topic_documented is optional and weak. It is treated as row/usefulness "
                "evidence mainly in the tail, not as admission-time topic preference."
            ),
        },
        "inputs": {
            "signal_row_count": len(rows),
            "calibration_id": calibration_payload.get("calibration_id"),
            "holdout_id": holdout_payload.get("holdout_id"),
            "calibration_count": len(calibration_labels),
            "holdout_count": len(holdout_labels),
            "product_objective_id": product_context.get("objective_id"),
            "product_sentinel_count": product_context.get("sentinel_count"),
            "product_distribution_sample_count": product_context.get("distribution_sample_count"),
            "product_sentinel_policy": product_context.get("sentinel_policy"),
        },
        "summary": {
            "raw_frequency_baseline": _compact_record(raw_frequency_record),
            "best_calibration_candidate": _compact_record(best_calibration),
            "best_holdout_guarded_candidate": _compact_record(best_guarded),
            "best_stable_candidate": _compact_record(best_stable),
            "best_product_candidate": _compact_record(best_product),
        },
        "leaderboards": {
            "calibration_top": calibration_top,
            "holdout_guarded_top": holdout_guarded_top,
            "stable_top": stable_top,
            "product_top": product_top,
        },
        "selected_candidate_details": selected_details,
        "limitations": [
            "The reviewed set is intentionally small; holdout is an overfitting check, not a second tuning target.",
            "Learner-source CEFR/core-list evidence is source-backed but not treated as official CEFR truth.",
            "Form artifacts with no reliable mechanical signal still need manual restriction or later source cleanup.",
        ],
    }


def generate_candidates(candidate_grid: str = "broad") -> tuple[FormulaCandidate, ...]:
    if candidate_grid == "broad":
        return _generate_broad_candidates()
    if candidate_grid == "refined":
        return _generate_refined_candidates()
    if candidate_grid == "floor_refined":
        return _generate_floor_refined_candidates()
    raise ValueError(f"Unsupported candidate grid: {candidate_grid}")


def _generate_broad_candidates() -> tuple[FormulaCandidate, ...]:
    base_shapes = tuple(
        product(
            (0.45, 0.60, 0.75, 0.90),
            (1.00, 1.35, 1.75, 2.20),
            (1.00, 1.40),
            (0.90, 1.00, 1.12),
        )
    )
    source_base_profiles = (
        ("src0", 0.00, 1.00, 0.00, 1.00),
        ("wf10", 0.10, 1.00, 0.00, 1.00),
        ("wf22", 0.22, 1.00, 0.00, 1.00),
        ("sub15", 0.00, 1.00, 0.15, 1.00),
        ("modern20", 0.12, 1.00, 0.08, 1.00),
    )
    ease_profiles = (
        ("ease0", {}, 0.0),
        ("cog04", {"cognate_ease": 0.04}, 0.08),
        ("cog08", {"cognate_ease": 0.08}, 0.14),
        ("cog12", {"cognate_ease": 0.12}, 0.18),
        ("cog08_common04", {"cognate_ease": 0.08, "common_gloss_ease": 0.04}, 0.16),
        ("common08", {"simple_common_gloss_ease": 0.08}, 0.14),
        ("common12", {"simple_common_gloss_ease": 0.12}, 0.18),
        ("learner25", {"learner_source_pull_down": 0.25}, 0.16),
        ("learner50", {"learner_source_pull_down": 0.50}, 0.24),
        ("learnercore25", {"learner_core_soft_ceiling": 0.25}, 0.16),
        ("learnercore45", {"learner_core_soft_ceiling": 0.45}, 0.24),
        (
            "learner35_cog04",
            {"learner_source_pull_down": 0.35, "cognate_ease": 0.04},
            0.24,
        ),
        ("goethea1_35", {"goethe_a1_soft_ceiling": 0.35}, 0.18),
        ("goethea1_60", {"goethe_a1_soft_ceiling": 0.60}, 0.26),
        ("goethestem20", {"goethe_stem_soft_ceiling": 0.20}, 0.12),
        ("goethestem35", {"goethe_stem_soft_ceiling": 0.35}, 0.18),
        ("basis20", {"odenet_basis_pull_down": 0.20}, 0.10),
        ("basis35", {"odenet_basis_pull_down": 0.35}, 0.14),
        (
            "learner30_basis20",
            {"learner_source_pull_down": 0.30, "odenet_basis_pull_down": 0.20},
            0.22,
        ),
        (
            "pedagogical_mix",
            {
                "goethe_a1_soft_ceiling": 0.45,
                "learner_core_soft_ceiling": 0.25,
                "odenet_basis_pull_down": 0.16,
            },
            0.28,
        ),
        (
            "cog04_common08",
            {"cognate_ease": 0.04, "simple_common_gloss_ease": 0.08},
            0.18,
        ),
        ("tail_common10", {"tail_common_gloss_ease": 0.10}, 0.16),
        (
            "cog10_common04_topic02",
            {"cognate_ease": 0.10, "common_gloss_ease": 0.04, "topic_tail_ease": 0.02},
            0.18,
        ),
        ("topic04", {"topic_tail_ease": 0.04}, 0.08),
        ("wordfreq_tail10", {"wordfreq_tail_rescue": 0.10}, 0.12),
        ("wordfreq_tail18", {"wordfreq_tail_rescue": 0.18}, 0.18),
        ("subtitles_tail10", {"subtitles_tail_rescue": 0.10}, 0.12),
        ("modern_tail16", {"modern_tail_rescue": 0.16}, 0.18),
        ("klexikon_cap15", {"klexikon_child_cap_070": 0.15}, 0.14),
        ("klexikon_cap25", {"klexikon_child_cap_060": 0.25}, 0.20),
        (
            "modern_child_tail",
            {
                "modern_tail_rescue": 0.12,
                "klexikon_child_cap_070": 0.15,
            },
            0.22,
        ),
    )
    guard_profiles = (
        ("guard0", {}, 0.0),
        ("poly04", {"polysemy_risk": 0.04}, 0.08),
        ("poly08", {"polysemy_risk": 0.08}, 0.12),
        ("learnercorefloor20", {"learner_core_soft_floor": 0.20}, 0.08),
        ("learnerfloor25", {"learner_source_pull_up": 0.25}, 0.10),
        ("len04", {"length_tail_risk": 0.04, "compound_tail_risk": 0.02}, 0.10),
        (
            "len06_poly04",
            {"length_tail_risk": 0.06, "compound_tail_risk": 0.04, "polysemy_risk": 0.04},
            0.16,
        ),
        ("long12", {"long_compound_heavy_risk": 0.12}, 0.22),
        (
            "long16_poly04",
            {"long_compound_heavy_risk": 0.16, "polysemy_risk": 0.04},
            0.30,
        ),
        ("nosig08", {"no_signal_tail_risk": 0.08}, 0.14),
        (
            "form06",
            {"participle_tail_risk": 0.06, "mixed_pos_tail_risk": 0.04},
            0.12,
        ),
        (
            "tail_light",
            {
                "length_tail_risk": 0.04,
                "compound_tail_risk": 0.03,
                "polysemy_risk": 0.04,
                "no_signal_tail_risk": 0.06,
                "participle_tail_risk": 0.04,
            },
            0.18,
        ),
        (
            "tail_medium",
            {
                "length_tail_risk": 0.07,
                "compound_tail_risk": 0.05,
                "polysemy_risk": 0.07,
                "no_signal_tail_risk": 0.10,
                "participle_tail_risk": 0.06,
                "other_pos_tail_risk": 0.04,
            },
            0.24,
        ),
        (
            "absence_medium",
            {
                "no_signal_tail_risk": 0.08,
                "broad_learner_absence_tail_risk": 0.05,
                "modern_source_absence_tail_risk": 0.04,
            },
            0.18,
        ),
        (
            "wiki_light",
            {
                "wiktionary_rare_dated_tail_risk": 0.06,
                "wiktionary_form_variant_tail_risk": 0.04,
                "wiktionary_ambiguity_tail_risk": 0.03,
            },
            0.12,
        ),
        (
            "wiki_medium",
            {
                "wiktionary_marked_tail_risk": 0.06,
                "wiktionary_rare_dated_tail_risk": 0.08,
                "wiktionary_form_variant_tail_risk": 0.06,
                "wiktionary_ambiguity_tail_risk": 0.05,
            },
            0.18,
        ),
        (
            "learnbackoff06",
            {
                "learner_ceiling_backoff": 0.06,
                "non_exact_learner_backoff": 0.04,
            },
            0.12,
        ),
        (
            "sensepos08_poly04",
            {
                "sense_pos_artifact_guard": 0.08,
                "polysemy_core_floor": 0.04,
            },
            0.14,
        ),
        (
            "domaincmp12",
            {
                "domain_compound_guard": 0.12,
                "learner_core_soft_floor": 0.08,
            },
            0.20,
        ),
        (
            "function08_sense04",
            {
                "function_word_guard": 0.08,
                "sense_pos_artifact_guard": 0.04,
            },
            0.14,
        ),
        (
            "smartguards_light",
            {
                "learner_ceiling_backoff": 0.04,
                "sense_pos_artifact_guard": 0.05,
                "domain_compound_guard": 0.08,
                "polysemy_core_floor": 0.04,
                "function_word_guard": 0.05,
                "non_exact_learner_backoff": 0.03,
            },
            0.18,
        ),
        (
            "smartguards_medium",
            {
                "learner_ceiling_backoff": 0.08,
                "sense_pos_artifact_guard": 0.08,
                "domain_compound_guard": 0.12,
                "polysemy_core_floor": 0.06,
                "function_word_guard": 0.08,
                "non_exact_learner_backoff": 0.05,
                "learner_core_soft_floor": 0.06,
            },
            0.24,
        ),
        (
            "struct_backoff_light",
            {},
            0.0,
            {
                "learner_ease_backoff_risk": 0.25,
                "sense_artifact_risk": 0.20,
                "polysemy_core_risk": 0.15,
                "function_word_risk": 0.20,
            },
            0.45,
            {},
            0.0,
        ),
        (
            "struct_floors_light",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_030": 0.50,
                "polysemy_core_floor_030": 0.45,
                "function_word_floor_030": 0.55,
                "domain_compound_floor_068": 0.65,
            },
            0.14,
        ),
        (
            "struct_floors_medium",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_030": 0.62,
                "polysemy_core_floor_030": 0.58,
                "function_word_floor_030": 0.68,
                "domain_compound_floor_068": 0.78,
                "intermediate_complexity_floor_040": 0.30,
            },
            0.20,
        ),
        (
            "struct_floors_domain_strong",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_030": 0.45,
                "polysemy_core_floor_030": 0.40,
                "function_word_floor_030": 0.50,
                "domain_compound_floor_072": 0.95,
                "intermediate_complexity_floor_040": 0.25,
            },
            0.24,
        ),
        (
            "struct_floors_sense_poly_strong",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_034": 0.75,
                "polysemy_core_floor_034": 0.70,
                "function_word_floor_030": 0.45,
                "domain_compound_floor_068": 0.55,
                "intermediate_complexity_floor_040": 0.30,
            },
            0.24,
        ),
        (
            "struct_combo_medium",
            {},
            0.0,
            {
                "learner_ease_backoff_risk": 0.35,
                "sense_artifact_risk": 0.25,
                "polysemy_core_risk": 0.20,
                "function_word_risk": 0.25,
                "domain_compound_risk": 0.20,
            },
            0.55,
            {
                "sense_artifact_floor_030": 0.55,
                "polysemy_core_floor_030": 0.50,
                "function_word_floor_030": 0.60,
                "domain_compound_floor_068": 0.75,
                "intermediate_complexity_floor_040": 0.35,
            },
            0.20,
        ),
    )
    return _candidate_grid_from_profiles(
        base_shapes=base_shapes,
        source_base_profiles=source_base_profiles,
        ease_profiles=ease_profiles,
        guard_profiles=guard_profiles,
        grid_label="Broad",
    )


def _generate_refined_candidates() -> tuple[FormulaCandidate, ...]:
    base_shapes = tuple(
        product(
            (0.55, 0.65, 0.75, 0.85),
            (1.20, 1.35, 1.50, 1.70),
            (1.00, 1.20, 1.40),
            (1.00, 1.08, 1.12, 1.18),
        )
    )
    source_base_profiles = (
        ("src0", 0.00, 1.00, 0.00, 1.00),
        ("wf06", 0.06, 1.00, 0.00, 1.00),
        ("wf10", 0.10, 1.00, 0.00, 1.00),
        ("wf16", 0.16, 1.00, 0.00, 1.00),
        ("wf22", 0.22, 1.00, 0.00, 1.00),
        ("sub08", 0.00, 1.00, 0.08, 1.00),
        ("modern14", 0.10, 1.00, 0.04, 1.00),
        ("modern20", 0.12, 1.00, 0.08, 1.00),
        ("modern28", 0.16, 1.00, 0.12, 1.00),
    )
    ease_profiles = (
        (
            "pedmix_light",
            {
                "goethe_a1_soft_ceiling": 0.35,
                "learner_core_soft_ceiling": 0.18,
                "odenet_basis_pull_down": 0.10,
            },
            0.22,
        ),
        (
            "pedagogical_mix",
            {
                "goethe_a1_soft_ceiling": 0.45,
                "learner_core_soft_ceiling": 0.25,
                "odenet_basis_pull_down": 0.16,
            },
            0.28,
        ),
        (
            "pedmix_strong",
            {
                "goethe_a1_soft_ceiling": 0.55,
                "learner_core_soft_ceiling": 0.35,
                "odenet_basis_pull_down": 0.20,
            },
            0.34,
        ),
        ("learnercore35", {"learner_core_soft_ceiling": 0.35}, 0.20),
        ("learnercore50", {"learner_core_soft_ceiling": 0.50}, 0.28),
        (
            "pedmix_modtail",
            {
                "goethe_a1_soft_ceiling": 0.45,
                "learner_core_soft_ceiling": 0.25,
                "odenet_basis_pull_down": 0.16,
                "modern_tail_rescue": 0.08,
            },
            0.32,
        ),
    )
    guard_profiles = (
        ("guard0", {}, 0.0),
        ("long12", {"long_compound_heavy_risk": 0.12}, 0.22),
        (
            "long16_poly04",
            {"long_compound_heavy_risk": 0.16, "polysemy_risk": 0.04},
            0.30,
        ),
        (
            "len06_poly04",
            {"length_tail_risk": 0.06, "compound_tail_risk": 0.04, "polysemy_risk": 0.04},
            0.16,
        ),
        (
            "tail_light",
            {
                "length_tail_risk": 0.04,
                "compound_tail_risk": 0.03,
                "polysemy_risk": 0.04,
                "no_signal_tail_risk": 0.06,
                "participle_tail_risk": 0.04,
            },
            0.18,
        ),
        (
            "tail_medium",
            {
                "length_tail_risk": 0.07,
                "compound_tail_risk": 0.05,
                "polysemy_risk": 0.07,
                "no_signal_tail_risk": 0.10,
                "participle_tail_risk": 0.06,
                "other_pos_tail_risk": 0.04,
            },
            0.24,
        ),
        (
            "wiki_light",
            {
                "wiktionary_rare_dated_tail_risk": 0.06,
                "wiktionary_form_variant_tail_risk": 0.04,
                "wiktionary_ambiguity_tail_risk": 0.03,
            },
            0.12,
        ),
        (
            "learnbackoff06",
            {
                "learner_ceiling_backoff": 0.06,
                "non_exact_learner_backoff": 0.04,
            },
            0.12,
        ),
        (
            "sensepos08_poly04",
            {
                "sense_pos_artifact_guard": 0.08,
                "polysemy_core_floor": 0.04,
            },
            0.14,
        ),
        (
            "domaincmp12",
            {
                "domain_compound_guard": 0.12,
                "learner_core_soft_floor": 0.08,
            },
            0.20,
        ),
        (
            "function08_sense04",
            {
                "function_word_guard": 0.08,
                "sense_pos_artifact_guard": 0.04,
            },
            0.14,
        ),
        (
            "smartguards_light",
            {
                "learner_ceiling_backoff": 0.04,
                "sense_pos_artifact_guard": 0.05,
                "domain_compound_guard": 0.08,
                "polysemy_core_floor": 0.04,
                "function_word_guard": 0.05,
                "non_exact_learner_backoff": 0.03,
            },
            0.18,
        ),
        (
            "smartguards_medium",
            {
                "learner_ceiling_backoff": 0.08,
                "sense_pos_artifact_guard": 0.08,
                "domain_compound_guard": 0.12,
                "polysemy_core_floor": 0.06,
                "function_word_guard": 0.08,
                "non_exact_learner_backoff": 0.05,
                "learner_core_soft_floor": 0.06,
            },
            0.24,
        ),
        (
            "smartguards_strong",
            {
                "learner_ceiling_backoff": 0.10,
                "sense_pos_artifact_guard": 0.11,
                "domain_compound_guard": 0.16,
                "polysemy_core_floor": 0.08,
                "function_word_guard": 0.10,
                "non_exact_learner_backoff": 0.07,
                "learner_core_soft_floor": 0.10,
            },
            0.30,
        ),
        (
            "struct_backoff_light",
            {},
            0.0,
            {
                "learner_ease_backoff_risk": 0.25,
                "sense_artifact_risk": 0.20,
                "polysemy_core_risk": 0.15,
                "function_word_risk": 0.20,
            },
            0.45,
            {},
            0.0,
        ),
        (
            "struct_backoff_medium",
            {},
            0.0,
            {
                "learner_ease_backoff_risk": 0.40,
                "sense_artifact_risk": 0.30,
                "polysemy_core_risk": 0.25,
                "function_word_risk": 0.30,
                "domain_compound_risk": 0.20,
            },
            0.65,
            {},
            0.0,
        ),
        (
            "struct_floors_light",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_030": 0.50,
                "polysemy_core_floor_030": 0.45,
                "function_word_floor_030": 0.55,
                "domain_compound_floor_068": 0.65,
            },
            0.14,
        ),
        (
            "struct_floors_medium",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_030": 0.62,
                "polysemy_core_floor_030": 0.58,
                "function_word_floor_030": 0.68,
                "domain_compound_floor_068": 0.78,
                "intermediate_complexity_floor_040": 0.30,
            },
            0.20,
        ),
        (
            "struct_floors_domain_strong",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_030": 0.45,
                "polysemy_core_floor_030": 0.40,
                "function_word_floor_030": 0.50,
                "domain_compound_floor_072": 0.95,
                "intermediate_complexity_floor_040": 0.25,
            },
            0.24,
        ),
        (
            "struct_floors_sense_poly_strong",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_034": 0.75,
                "polysemy_core_floor_034": 0.70,
                "function_word_floor_030": 0.45,
                "domain_compound_floor_068": 0.55,
                "intermediate_complexity_floor_040": 0.30,
            },
            0.24,
        ),
        (
            "struct_floors_balanced_high",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_034": 0.70,
                "polysemy_core_floor_034": 0.65,
                "function_word_floor_034": 0.70,
                "domain_compound_floor_072": 0.85,
                "intermediate_complexity_floor_044": 0.45,
            },
            0.28,
        ),
        (
            "struct_combo_light",
            {},
            0.0,
            {
                "learner_ease_backoff_risk": 0.25,
                "sense_artifact_risk": 0.20,
                "polysemy_core_risk": 0.15,
                "function_word_risk": 0.20,
                "domain_compound_risk": 0.15,
            },
            0.45,
            {
                "sense_artifact_floor_030": 0.45,
                "polysemy_core_floor_030": 0.40,
                "function_word_floor_030": 0.50,
                "domain_compound_floor_068": 0.60,
                "intermediate_complexity_floor_040": 0.25,
            },
            0.14,
        ),
        (
            "struct_combo_medium",
            {},
            0.0,
            {
                "learner_ease_backoff_risk": 0.35,
                "sense_artifact_risk": 0.25,
                "polysemy_core_risk": 0.20,
                "function_word_risk": 0.25,
                "domain_compound_risk": 0.20,
            },
            0.55,
            {
                "sense_artifact_floor_030": 0.55,
                "polysemy_core_floor_030": 0.50,
                "function_word_floor_030": 0.60,
                "domain_compound_floor_068": 0.75,
                "intermediate_complexity_floor_040": 0.35,
            },
            0.20,
        ),
        (
            "struct_combo_strong",
            {},
            0.0,
            {
                "learner_ease_backoff_risk": 0.45,
                "sense_artifact_risk": 0.35,
                "polysemy_core_risk": 0.30,
                "function_word_risk": 0.35,
                "domain_compound_risk": 0.25,
            },
            0.70,
            {
                "sense_artifact_floor_034": 0.60,
                "polysemy_core_floor_034": 0.55,
                "function_word_floor_034": 0.65,
                "domain_compound_floor_072": 0.85,
                "intermediate_complexity_floor_044": 0.45,
            },
            0.26,
        ),
    )
    return _candidate_grid_from_profiles(
        base_shapes=base_shapes,
        source_base_profiles=source_base_profiles,
        ease_profiles=ease_profiles,
        guard_profiles=guard_profiles,
        grid_label="Refined",
    )


def _generate_floor_refined_candidates() -> tuple[FormulaCandidate, ...]:
    base_shapes = tuple(
        product(
            (0.50, 0.55, 0.60, 0.65, 0.75),
            (1.35, 1.50, 1.70),
            (1.20, 1.40),
            (1.12, 1.18),
        )
    )
    source_base_profiles = (
        ("wf16", 0.16, 1.00, 0.00, 1.00),
        ("wf22", 0.22, 1.00, 0.00, 1.00),
        ("modern20", 0.12, 1.00, 0.08, 1.00),
        ("modern28", 0.16, 1.00, 0.12, 1.00),
    )
    ease_profiles = (
        ("learnercore45", {"learner_core_soft_ceiling": 0.45}, 0.26),
        ("learnercore50", {"learner_core_soft_ceiling": 0.50}, 0.28),
        (
            "pedmix_modtail",
            {
                "goethe_a1_soft_ceiling": 0.45,
                "learner_core_soft_ceiling": 0.25,
                "odenet_basis_pull_down": 0.16,
                "modern_tail_rescue": 0.08,
            },
            0.32,
        ),
        (
            "pedmix_strong",
            {
                "goethe_a1_soft_ceiling": 0.55,
                "learner_core_soft_ceiling": 0.35,
                "odenet_basis_pull_down": 0.20,
            },
            0.34,
        ),
    )
    guard_profiles = (
        (
            "sensepos08_poly04",
            {
                "sense_pos_artifact_guard": 0.08,
                "polysemy_core_floor": 0.04,
            },
            0.14,
        ),
        (
            "function08_sense04",
            {
                "function_word_guard": 0.08,
                "sense_pos_artifact_guard": 0.04,
            },
            0.14,
        ),
        (
            "struct_floors_light",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_030": 0.50,
                "polysemy_core_floor_030": 0.45,
                "function_word_floor_030": 0.55,
                "domain_compound_floor_068": 0.65,
            },
            0.14,
        ),
        (
            "struct_floors_medium",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_030": 0.62,
                "polysemy_core_floor_030": 0.58,
                "function_word_floor_030": 0.68,
                "domain_compound_floor_068": 0.78,
                "intermediate_complexity_floor_040": 0.30,
            },
            0.20,
        ),
        (
            "struct_floors_domain_strong",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_030": 0.45,
                "polysemy_core_floor_030": 0.40,
                "function_word_floor_030": 0.50,
                "domain_compound_floor_072": 0.95,
                "intermediate_complexity_floor_040": 0.25,
            },
            0.24,
        ),
        (
            "struct_floors_sense_poly_strong",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_034": 0.75,
                "polysemy_core_floor_034": 0.70,
                "function_word_floor_030": 0.45,
                "domain_compound_floor_068": 0.55,
                "intermediate_complexity_floor_040": 0.30,
            },
            0.24,
        ),
        (
            "struct_floors_balanced_high",
            {},
            0.0,
            {},
            0.0,
            {
                "sense_artifact_floor_034": 0.70,
                "polysemy_core_floor_034": 0.65,
                "function_word_floor_034": 0.70,
                "domain_compound_floor_072": 0.85,
                "intermediate_complexity_floor_044": 0.45,
            },
            0.28,
        ),
        (
            "struct_combo_medium",
            {},
            0.0,
            {
                "learner_ease_backoff_risk": 0.35,
                "sense_artifact_risk": 0.25,
                "polysemy_core_risk": 0.20,
                "function_word_risk": 0.25,
                "domain_compound_risk": 0.20,
            },
            0.55,
            {
                "sense_artifact_floor_030": 0.55,
                "polysemy_core_floor_030": 0.50,
                "function_word_floor_030": 0.60,
                "domain_compound_floor_068": 0.75,
                "intermediate_complexity_floor_040": 0.35,
            },
            0.20,
        ),
    )
    return _candidate_grid_from_profiles(
        base_shapes=base_shapes,
        source_base_profiles=source_base_profiles,
        ease_profiles=ease_profiles,
        guard_profiles=guard_profiles,
        grid_label="Floor-refined",
    )


def _candidate_grid_from_profiles(
    *,
    base_shapes: Sequence[tuple[float, float, float, float]],
    source_base_profiles: Sequence[tuple[str, float, float, float, float]],
    ease_profiles: Sequence[tuple[str, Mapping[str, float], float]],
    guard_profiles: Sequence[Sequence[object]],
    grid_label: str,
) -> tuple[FormulaCandidate, ...]:
    candidates: list[FormulaCandidate] = [_raw_frequency_candidate()]
    for rank_weight, rank_gamma, pmw_gamma, warp_gamma in base_shapes:
        for (
            source_id,
            wordfreq_weight,
            wordfreq_gamma,
            subtitles_weight,
            subtitles_gamma,
        ) in source_base_profiles:
            for ease_id, ease_weights, down_cap in ease_profiles:
                for raw_guard_profile in guard_profiles:
                    (
                        guard_id,
                        guard_weights,
                        up_cap,
                        ease_backoff_weights,
                        ease_backoff_cap,
                        floor_weights,
                        floor_cap,
                    ) = _unpack_guard_profile(raw_guard_profile)
                    candidate_id = (
                        f"rw{rank_weight:.2f}_rg{rank_gamma:.2f}_pg{pmw_gamma:.2f}_"
                        f"wg{warp_gamma:.2f}_{source_id}_{ease_id}_{guard_id}"
                    ).replace(".", "")
                    candidates.append(
                        FormulaCandidate(
                            candidate_id=candidate_id,
                            rank_weight=float(rank_weight),
                            rank_gamma=float(rank_gamma),
                            pmw_gamma=float(pmw_gamma),
                            warp_gamma=float(warp_gamma),
                            wordfreq_weight=float(wordfreq_weight),
                            wordfreq_gamma=float(wordfreq_gamma),
                            subtitles_weight=float(subtitles_weight),
                            subtitles_gamma=float(subtitles_gamma),
                            up_weights=guard_weights,
                            down_weights=ease_weights,
                            up_cap=float(up_cap),
                            down_cap=float(down_cap),
                            description=(
                                f"{grid_label} frequency curve plus optional en-de guards/eases: "
                                f"source={source_id}, ease={ease_id}, guard={guard_id}."
                            ),
                            ease_backoff_weights=ease_backoff_weights,
                            ease_backoff_cap=float(ease_backoff_cap),
                            floor_weights=floor_weights,
                            floor_cap=float(floor_cap),
                        )
                    )
    return tuple(candidates)


def _unpack_guard_profile(
    profile: Sequence[object],
) -> tuple[
    str,
    Mapping[str, float],
    float,
    Mapping[str, float],
    float,
    Mapping[str, float],
    float,
]:
    if len(profile) == 3:
        profile_id, up_weights, up_cap = profile
        return (
            str(profile_id),
            _float_weight_mapping(up_weights),
            _safe_float(up_cap) or 0.0,
            {},
            0.0,
            {},
            0.0,
        )
    if len(profile) == 7:
        (
            profile_id,
            up_weights,
            up_cap,
            ease_backoff_weights,
            ease_backoff_cap,
            floor_weights,
            floor_cap,
        ) = profile
        return (
            str(profile_id),
            _float_weight_mapping(up_weights),
            _safe_float(up_cap) or 0.0,
            _float_weight_mapping(ease_backoff_weights),
            _safe_float(ease_backoff_cap) or 0.0,
            _float_weight_mapping(floor_weights),
            _safe_float(floor_cap) or 0.0,
        )
    raise ValueError(f"Unsupported guard profile shape: {profile!r}")


def _float_weight_mapping(value: object) -> Mapping[str, float]:
    return {
        str(key): float(numeric)
        for key, raw in _as_mapping(value).items()
        if (numeric := _safe_float(raw)) is not None
    }


def _raw_frequency_candidate() -> FormulaCandidate:
    return FormulaCandidate(
        candidate_id="raw_frequency_blend",
        rank_weight=0.55,
        rank_gamma=1.0,
        pmw_gamma=1.0,
        warp_gamma=1.0,
        wordfreq_weight=0.0,
        wordfreq_gamma=1.0,
        subtitles_weight=0.0,
        subtitles_gamma=1.0,
        up_weights={},
        down_weights={},
        up_cap=0.0,
        down_cap=0.0,
        description="Baseline: raw signal-palette frequency_blend.",
    )


def _select_candidates(
    candidates: Sequence[FormulaCandidate],
    *,
    max_candidates: int,
    sample_mode: str,
) -> list[FormulaCandidate]:
    items = list(candidates)
    if max_candidates <= 0 or max_candidates >= len(items):
        return items
    if max_candidates == 1:
        return items[:1]
    if sample_mode == "head":
        return items[:max_candidates]
    if sample_mode != "coarse":
        raise ValueError(f"Unsupported candidate sample mode: {sample_mode}")
    selected_indices = {0}
    for anchor in COARSE_SAMPLE_ANCHORS:
        if len(selected_indices) >= max_candidates:
            break
        for index, candidate in enumerate(items[1:], start=1):
            if anchor in candidate.candidate_id:
                selected_indices.add(index)
                break
    tail_count = len(items) - 1
    remaining = max_candidates - len(selected_indices)
    if remaining == 1:
        selected_indices.add(len(items) - 1)
    elif remaining > 1:
        for slot in range(remaining):
            ratio = slot / max(1, remaining - 1)
            selected_indices.add(1 + round(ratio * (tail_count - 1)))
    if len(selected_indices) < max_candidates:
        stride = max(1, len(items) // max_candidates)
        for index in range(1, len(items), stride):
            selected_indices.add(index)
            if len(selected_indices) >= max_candidates:
                break
    if len(selected_indices) < max_candidates:
        for index in range(len(items)):
            selected_indices.add(index)
            if len(selected_indices) >= max_candidates:
                break
    return [items[index] for index in sorted(selected_indices)[:max_candidates]]


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _as_mapping(report.get("inputs"))
    summary = _as_mapping(report.get("summary"))
    method = _as_mapping(report.get("method"))
    lines = [
        "# en-de Learner Difficulty Formula Sweep",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Inputs",
        "",
        f"- Signal rows: `{inputs.get('signal_row_count')}`",
        f"- Calibration labels: `{inputs.get('calibration_count')}`",
        f"- Holdout labels: `{inputs.get('holdout_count')}`",
        f"- Candidate grid: `{method.get('candidate_grid')}`",
        f"- Candidates swept: `{method.get('candidate_count')}` / "
        f"`{method.get('total_candidate_count')}`",
        f"- Candidate sample mode: `{method.get('candidate_sample_mode')}`",
        "",
        "## Summary",
        "",
    ]
    for key, label in (
        ("raw_frequency_baseline", "raw frequency baseline"),
        ("best_calibration_candidate", "best calibration"),
        ("best_holdout_guarded_candidate", "best holdout-guarded"),
        ("best_stable_candidate", "best stable"),
        ("best_product_candidate", "best product-aware"),
    ):
        record = _as_mapping(summary.get(key))
        lines.append(
            f"- {label}: `{record.get('candidate_id')}` "
            f"(cal={_fmt(record.get('calibration_balanced'))}, "
            f"holdout={_fmt(record.get('holdout_balanced'))}, "
            f"cal MAE={_fmt(record.get('calibration_mae'))}, "
            f"holdout MAE={_fmt(record.get('holdout_mae'))}, "
            f"product={_fmt(record.get('product_objective_score'))}, "
            f"product stable={_fmt(record.get('product_stable_score'))})"
        )
    lines.extend(
        [
            "",
            "## Leaderboards",
            "",
        ]
    )
    for leaderboard_key, title in (
        ("calibration_top", "Calibration Top"),
        ("holdout_guarded_top", "Holdout-Guarded Top"),
        ("stable_top", "Stable Top"),
        ("product_top", "Product-Aware Top"),
    ):
        lines.extend(
            [
                f"### {title}",
                "",
                "| Candidate | Product Stable | Product Obj | Cal Balanced | Holdout Balanced | Cal MAE | Holdout MAE | Cal Pairwise | Holdout Pairwise |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for raw in _as_sequence(_as_mapping(report.get("leaderboards")).get(leaderboard_key))[:15]:
            row = _as_mapping(raw)
            lines.append(
                f"| `{row.get('candidate_id')}` | "
                f"{_fmt(_product_adjusted_at(row, 'stable_score'))} | "
                f"{_fmt(_product_objective_at(row, 'objective_score'))} | "
                f"{_fmt(_score_at(row, 'calibration_primary', 'balanced_score'))} | "
                f"{_fmt(_score_at(row, 'holdout_primary', 'balanced_score'))} | "
                f"{_fmt(_metric_at(row, 'calibration_primary', 'mae'))} | "
                f"{_fmt(_metric_at(row, 'holdout_primary', 'mae'))} | "
                f"{_fmt(_metric_at(row, 'calibration_primary', 'pairwise_accuracy'))} | "
                f"{_fmt(_metric_at(row, 'holdout_primary', 'pairwise_accuracy'))} |"
            )
        lines.append("")
    lines.extend(["## Selected Candidate Details", ""])
    for raw in _as_sequence(report.get("selected_candidate_details")):
        detail = _as_mapping(raw)
        lines.extend(
            [
                f"### `{detail.get('candidate_id')}`",
                "",
                str(detail.get("description") or ""),
                "",
                f"- Product objective: `{_fmt(_product_objective_at(detail, 'objective_score'))}` "
                f"(distribution={_fmt(_product_objective_at(detail, 'distribution_score'))}, "
                f"sentinel={_fmt(_product_objective_at(detail, 'sentinel_score'))})",
                f"- Sentinel components: mean={_fmt(_product_sentinel_at(detail, 'mean_score'))}, "
                f"cohort={_fmt(_product_sentinel_at(detail, 'cohort_balanced_score'))}, "
                f"severe={_fmt(_product_sentinel_at(detail, 'severe_violation_score'))}, "
                f"worst={_fmt(_product_sentinel_at(detail, 'worst_violation_score'))}, "
                f"severe rows={_product_sentinel_at(detail, 'severe_violation_count')}",
                f"- Product-adjusted stable score: `{_fmt(_product_adjusted_at(detail, 'stable_score'))}`",
                "",
                "| Split | Rows | Balanced | MAE | Bucket | Pairwise | High Tail |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for split_key, label in (
            ("calibration_primary", "calibration"),
            ("holdout_primary", "holdout"),
        ):
            item = _compact_eval(detail.get(split_key))
            lines.append(
                f"| {label} | {item.get('count', '')} | {_fmt(item.get('balanced_score'))} | "
                f"{_fmt(item.get('mae'))} | {_fmt(item.get('bucket_accuracy'))} | "
                f"{_fmt(item.get('pairwise_accuracy'))} | {_fmt(item.get('high_tail_score'))} |"
            )
        lines.extend(["", "Largest shifts from raw frequency:", ""])
        for row in _as_sequence(detail.get("largest_raw_frequency_shifts"))[:8]:
            item = _as_mapping(row)
            lines.append(
                f"- `{item.get('lemma')}`: {_fmt(item.get('raw_frequency'))} -> "
                f"{_fmt(item.get('candidate_score'))} ({_fmt_signed(item.get('delta'))})"
            )
        lines.append("")
    return "\n".join(lines)


def _build_product_objective_context(
    *,
    rows: Sequence[Mapping[str, object]],
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    payload: Mapping[str, object],
    sample_size: int,
) -> dict[str, object]:
    if not payload:
        return {
            "objective_id": None,
            "enabled": False,
            "sentinels": [],
            "distribution_rows": [],
            "target_decile_weights": [],
            "selection_weight": 0.0,
            "objective_weights": {"distribution": 0.0, "sentinel": 0.0},
            "sentinel_count": 0,
            "distribution_sample_count": 0,
        }
    distribution = _as_mapping(payload.get("distribution"))
    target_weights = _normalize_weights(_as_sequence(distribution.get("target_decile_weights")))
    sampled_rows = (
        _deterministic_product_sample(rows, limit=sample_size)
        if sample_size > 0 and target_weights
        else []
    )
    sentinel_specs = [_as_mapping(item) for item in _as_sequence(payload.get("sentinels"))]
    sentinel_items = []
    for spec in sentinel_specs:
        lemma = str(spec.get("lemma") or "").strip()
        row = rows_by_lemma.get(lemma.lower())
        sentinel_items.append(
            {
                "spec": spec,
                "lemma": lemma,
                "row": row,
                "missing": row is None,
            }
        )
    objective_weights = _as_mapping(payload.get("objective_weights"))
    return {
        "objective_id": payload.get("objective_id"),
        "enabled": True,
        "sentinels": sentinel_items,
        "distribution_rows": sampled_rows,
        "target_decile_weights": target_weights,
        "distribution_cdf_tolerance": _safe_float(distribution.get("cdf_tolerance")) or 0.20,
        "selection_weight": _clamp01(_safe_float(payload.get("selection_weight")) or 0.0),
        "objective_weights": {
            "distribution": _safe_float(objective_weights.get("distribution")) or 0.0,
            "sentinel": _safe_float(objective_weights.get("sentinel")) or 0.0,
        },
        "default_sentinel_margin": _safe_float(payload.get("default_sentinel_margin")) or 0.10,
        "sentinel_policy": _build_sentinel_policy(_as_mapping(payload.get("sentinel_policy"))),
        "sentinel_count": len(sentinel_items),
        "distribution_sample_count": len(sampled_rows),
    }


def _evaluate_product_objective(
    *,
    candidate: FormulaCandidate,
    product_context: Mapping[str, object],
) -> dict[str, object]:
    if not product_context.get("enabled"):
        return {
            "enabled": False,
            "objective_score": None,
            "distribution_score": None,
            "sentinel_score": None,
        }
    distribution_eval = _evaluate_distribution_objective(
        candidate=candidate,
        product_context=product_context,
    )
    sentinel_eval = _evaluate_sentinel_objective(
        candidate=candidate,
        product_context=product_context,
    )
    weights = _as_mapping(product_context.get("objective_weights"))
    parts = []
    distribution_score = _safe_float(distribution_eval.get("score"))
    sentinel_score = _safe_float(sentinel_eval.get("score"))
    distribution_weight = max(0.0, _safe_float(weights.get("distribution")) or 0.0)
    sentinel_weight = max(0.0, _safe_float(weights.get("sentinel")) or 0.0)
    if distribution_score is not None and distribution_weight > 0.0:
        parts.append((distribution_score, distribution_weight))
    if sentinel_score is not None and sentinel_weight > 0.0:
        parts.append((sentinel_score, sentinel_weight))
    if not parts:
        objective_score = None
    else:
        weight_sum = sum(weight for _, weight in parts)
        objective_score = _round_float(sum(score * weight for score, weight in parts) / weight_sum)
    return {
        "enabled": True,
        "objective_score": objective_score,
        "distribution_score": distribution_score,
        "sentinel_score": sentinel_score,
        "distribution": distribution_eval,
        "sentinel": sentinel_eval,
    }


def _evaluate_distribution_objective(
    *,
    candidate: FormulaCandidate,
    product_context: Mapping[str, object],
) -> dict[str, object]:
    rows = [_as_mapping(row) for row in _as_sequence(product_context.get("distribution_rows"))]
    target_weights = _normalize_weights(_as_sequence(product_context.get("target_decile_weights")))
    if not rows or not target_weights:
        return {
            "available": False,
            "score": None,
            "sample_count": len(rows),
            "reason": "missing_distribution_rows_or_target_weights",
        }
    counts = [0 for _ in range(10)]
    for row in rows:
        score = _score_row(candidate, row)
        if score is None:
            continue
        counts[min(9, int(_clamp01(score) * 10.0))] += 1
    observed_weights = _normalize_weights(counts)
    observed_cdf = _cumulative(observed_weights)
    target_cdf = _cumulative(target_weights)
    cdf_errors = [abs(observed - target) for observed, target in zip(observed_cdf, target_cdf)]
    cdf_mae = sum(cdf_errors) / len(cdf_errors)
    tolerance = max(0.0001, _safe_float(product_context.get("distribution_cdf_tolerance")) or 0.20)
    return {
        "available": True,
        "score": _round_float(max(0.0, 1.0 - (cdf_mae / tolerance))),
        "sample_count": len(rows),
        "cdf_mae": _round_float(cdf_mae),
        "cdf_tolerance": tolerance,
        "target_decile_weights": [_round_float(value) for value in target_weights],
        "observed_decile_weights": [_round_float(value) for value in observed_weights],
        "observed_decile_counts": counts,
        "tail_90_100_share": _round_float(observed_weights[-1]),
        "under_30_share": _round_float(sum(observed_weights[:3])),
    }


def _evaluate_sentinel_objective(
    *,
    candidate: FormulaCandidate,
    product_context: Mapping[str, object],
) -> dict[str, object]:
    sentinel_items = [_as_mapping(item) for item in _as_sequence(product_context.get("sentinels"))]
    if not sentinel_items:
        return {
            "available": False,
            "score": None,
            "evaluated_count": 0,
            "reason": "missing_sentinels",
        }
    weighted_violation = 0.0
    total_weight = 0.0
    rows = []
    missing = []
    default_margin = _safe_float(product_context.get("default_sentinel_margin")) or 0.10
    policy = _as_mapping(product_context.get("sentinel_policy"))
    severe_threshold = max(0.0001, _safe_float(policy.get("severe_threshold")) or 1.0)
    severe_budget = max(1.0, _safe_float(policy.get("severe_violation_budget")) or 4.0)
    worst_tolerance = max(
        0.0001,
        _safe_float(policy.get("worst_violation_tolerance")) or 2.0,
    )
    component_weights = _as_mapping(policy.get("component_weights"))
    cohort_violations: dict[str, dict[str, float]] = {}
    severe_count = 0
    weighted_severe_count = 0.0
    worst_normalized_violation = 0.0
    for item in sentinel_items:
        spec = _as_mapping(item.get("spec"))
        lemma = str(item.get("lemma") or spec.get("lemma") or "")
        row = _as_mapping(item.get("row"))
        if not row:
            missing.append(lemma)
            continue
        observed = _score_row(candidate, row)
        if observed is None:
            missing.append(lemma)
            continue
        floor = _safe_float(spec.get("floor"))
        ceiling = _safe_float(spec.get("ceiling"))
        margin = max(0.0001, _safe_float(spec.get("margin")) or default_margin)
        weight = max(0.0, _safe_float(spec.get("weight")) or 1.0)
        floor_gap = max(0.0, (floor if floor is not None else 0.0) - observed)
        ceiling_gap = max(0.0, observed - (ceiling if ceiling is not None else 1.0))
        violation = max(floor_gap, ceiling_gap)
        normalized_violation = violation / margin
        weighted_violation += weight * normalized_violation
        total_weight += weight
        cohort = str(spec.get("cohort") or "uncategorized")
        cohort_bucket = cohort_violations.setdefault(
            cohort, {"weighted_violation": 0.0, "weight": 0.0}
        )
        cohort_bucket["weighted_violation"] += weight * normalized_violation
        cohort_bucket["weight"] += weight
        worst_normalized_violation = max(worst_normalized_violation, normalized_violation)
        if normalized_violation >= severe_threshold:
            severe_count += 1
            weighted_severe_count += weight
        rows.append(
            {
                "lemma": lemma,
                "cohort": cohort,
                "observed": _round_float(observed),
                "floor": floor,
                "ceiling": ceiling,
                "violation": _round_float(violation),
                "normalized_violation": _round_float(normalized_violation),
                "weight": weight,
            }
        )
    mean_violation = weighted_violation / total_weight if total_weight > 0.0 else 0.0
    mean_score = _sentinel_violation_score(mean_violation)
    cohort_scores = []
    for cohort, bucket in sorted(cohort_violations.items()):
        cohort_weight = bucket["weight"]
        cohort_mean_violation = (
            bucket["weighted_violation"] / cohort_weight if cohort_weight > 0.0 else 0.0
        )
        cohort_scores.append(
            {
                "cohort": cohort,
                "score": _round_float(_sentinel_violation_score(cohort_mean_violation)),
                "mean_normalized_violation": _round_float(cohort_mean_violation),
                "weight": _round_float(cohort_weight),
            }
        )
    cohort_balanced_score = (
        sum(_safe_float(row.get("score")) or 0.0 for row in cohort_scores) / len(cohort_scores)
        if cohort_scores
        else None
    )
    severe_violation_score = _sentinel_violation_score(weighted_severe_count / severe_budget)
    worst_violation_score = _sentinel_violation_score(
        max(0.0, worst_normalized_violation - severe_threshold) / worst_tolerance
    )
    score_parts = [
        (
            mean_score,
            max(0.0, _safe_float(component_weights.get("mean")) or 0.0),
        ),
        (
            cohort_balanced_score,
            max(0.0, _safe_float(component_weights.get("cohort_balanced")) or 0.0),
        ),
        (
            severe_violation_score,
            max(0.0, _safe_float(component_weights.get("severe_violation")) or 0.0),
        ),
        (
            worst_violation_score,
            max(0.0, _safe_float(component_weights.get("worst_violation")) or 0.0),
        ),
    ]
    score_weight_sum = sum(weight for score, weight in score_parts if score is not None)
    if score_weight_sum <= 0.0:
        final_score = mean_score
    else:
        final_score = (
            sum(float(score) * weight for score, weight in score_parts if score is not None)
            / score_weight_sum
        )
    return {
        "available": total_weight > 0.0,
        "score": _round_float(final_score),
        "evaluated_count": len(rows),
        "missing_count": len(missing),
        "missing": missing[:20],
        "mean_normalized_violation": _round_float(mean_violation),
        "mean_score": _round_float(mean_score),
        "cohort_balanced_score": _round_float(cohort_balanced_score),
        "severe_violation_score": _round_float(severe_violation_score),
        "worst_violation_score": _round_float(worst_violation_score),
        "severe_threshold": severe_threshold,
        "severe_violation_budget": severe_budget,
        "severe_violation_count": severe_count,
        "weighted_severe_violation_count": _round_float(weighted_severe_count),
        "worst_normalized_violation": _round_float(worst_normalized_violation),
        "cohort_scores": cohort_scores,
        "worst_violations": sorted(
            rows,
            key=lambda row: _safe_float(row.get("normalized_violation")) or 0.0,
            reverse=True,
        )[:20],
    }


def _build_sentinel_policy(payload: Mapping[str, object]) -> dict[str, object]:
    weights = _as_mapping(payload.get("component_weights"))
    parsed_weights = {
        "mean": max(0.0, _safe_float(weights.get("mean")) or 0.40),
        "cohort_balanced": max(0.0, _safe_float(weights.get("cohort_balanced")) or 0.30),
        "severe_violation": max(0.0, _safe_float(weights.get("severe_violation")) or 0.15),
        "worst_violation": max(0.0, _safe_float(weights.get("worst_violation")) or 0.15),
    }
    if sum(parsed_weights.values()) <= 0.0:
        parsed_weights["mean"] = 1.0
    return {
        "component_weights": parsed_weights,
        "severe_threshold": max(0.0001, _safe_float(payload.get("severe_threshold")) or 1.0),
        "severe_violation_budget": max(
            1.0,
            _safe_float(payload.get("severe_violation_budget")) or 4.0,
        ),
        "worst_violation_tolerance": max(
            0.0001,
            _safe_float(payload.get("worst_violation_tolerance")) or 2.0,
        ),
    }


def _sentinel_violation_score(normalized_violation: float | None) -> float:
    if normalized_violation is None:
        return 1.0
    return max(0.0, 1.0 - max(0.0, float(normalized_violation)))


def _product_adjusted_scores(
    *,
    calibration_primary: Mapping[str, object],
    holdout_primary: Mapping[str, object],
    product_objective: Mapping[str, object],
    selection_weight: float,
) -> dict[str, object]:
    objective_score = _safe_float(product_objective.get("objective_score"))
    if objective_score is None or selection_weight <= 0.0:
        return {
            "enabled": False,
            "selection_weight": selection_weight,
            "calibration_score": None,
            "holdout_score": None,
            "stable_score": None,
        }
    cal = _safe_float(_as_mapping(calibration_primary.get("scores")).get("balanced_score"))
    holdout = _safe_float(_as_mapping(holdout_primary.get("scores")).get("balanced_score"))
    cal_adjusted = _blend_label_and_product_score(cal, objective_score, selection_weight)
    holdout_adjusted = _blend_label_and_product_score(holdout, objective_score, selection_weight)
    if cal_adjusted is None or holdout_adjusted is None:
        stable = None
    else:
        gap = abs(cal_adjusted - holdout_adjusted)
        stable = ((cal_adjusted + holdout_adjusted) / 2.0) - (gap * 0.35)
    return {
        "enabled": True,
        "selection_weight": selection_weight,
        "objective_score": objective_score,
        "calibration_score": _round_float(cal_adjusted),
        "holdout_score": _round_float(holdout_adjusted),
        "stable_score": _round_float(stable),
    }


def _blend_label_and_product_score(
    label_score: float | None,
    product_score: float,
    selection_weight: float,
) -> float | None:
    if label_score is None:
        return None
    weight = _clamp01(selection_weight)
    return ((1.0 - weight) * label_score) + (weight * product_score)


def _candidate_record(
    *,
    candidate: FormulaCandidate,
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    calibration_labels: Sequence[Mapping[str, object]],
    holdout_labels: Sequence[Mapping[str, object]],
    product_context: Mapping[str, object],
) -> dict[str, object]:
    calibration_primary = _evaluate_labels(
        labels=calibration_labels,
        rows_by_lemma=rows_by_lemma,
        candidate=candidate,
        primary_only=True,
    )
    holdout_primary = _evaluate_labels(
        labels=holdout_labels,
        rows_by_lemma=rows_by_lemma,
        candidate=candidate,
        primary_only=True,
    )
    product_objective = _evaluate_product_objective(
        candidate=candidate,
        product_context=product_context,
    )
    return {
        "candidate_id": candidate.candidate_id,
        "description": candidate.description,
        "profile": {
            "rank_weight": candidate.rank_weight,
            "rank_gamma": candidate.rank_gamma,
            "pmw_gamma": candidate.pmw_gamma,
            "warp_gamma": candidate.warp_gamma,
            "wordfreq_weight": candidate.wordfreq_weight,
            "wordfreq_gamma": candidate.wordfreq_gamma,
            "subtitles_weight": candidate.subtitles_weight,
            "subtitles_gamma": candidate.subtitles_gamma,
            "up_weights": dict(candidate.up_weights),
            "down_weights": dict(candidate.down_weights),
            "up_cap": candidate.up_cap,
            "down_cap": candidate.down_cap,
            "ease_backoff_weights": dict(candidate.ease_backoff_weights),
            "ease_backoff_cap": candidate.ease_backoff_cap,
            "floor_weights": dict(candidate.floor_weights),
            "floor_cap": candidate.floor_cap,
        },
        "calibration_primary": calibration_primary,
        "holdout_primary": holdout_primary,
        "calibration_all_numeric": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=False,
        ),
        "holdout_all_numeric": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=False,
        ),
        "product_objective": product_objective,
        "product_adjusted": _product_adjusted_scores(
            calibration_primary=calibration_primary,
            holdout_primary=holdout_primary,
            product_objective=product_objective,
            selection_weight=_safe_float(product_context.get("selection_weight")) or 0.0,
        ),
    }


def _evaluate_labels(
    *,
    labels: Sequence[Mapping[str, object]],
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    candidate: FormulaCandidate,
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
    row_pairs = []
    missing = []
    for label in selected:
        lemma = str(label.get("lemma") or "").strip()
        row = rows_by_lemma.get(lemma.lower())
        observed = _score_row(candidate, row) if row is not None else None
        if observed is None:
            missing.append(lemma)
            observed = float("nan")
        expected = _safe_float(label.get("expected_learner_difficulty"))
        expected_values.append(expected if expected is not None else float("nan"))
        observed_values.append(observed)
        expected_bands.append(str(label.get("expected_difficulty_band") or ""))
        label_names.append(lemma)
        expected_states.append(str(label.get("expected_candidate_state") or ""))
        observed_states.append(PRIMARY_STATE if row is not None else "")
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


def _score_row(candidate: FormulaCandidate, row: Mapping[str, object] | None) -> float | None:
    if row is None:
        return None
    if candidate.candidate_id == "raw_frequency_blend":
        return _round_float(_clamp01(_safe_float(row.get("frequency_blend")) or 0.0))
    rank_base = _clamp01(_safe_float(row.get("rank_base")) or 0.0)
    pmw_base = _clamp01(_safe_float(row.get("pmw_base")) or 0.0)
    rank_curve = rank_base ** max(0.01, candidate.rank_gamma)
    pmw_curve = pmw_base ** max(0.01, candidate.pmw_gamma)
    base_terms = [
        (rank_curve, candidate.rank_weight),
        (pmw_curve, 1.0 - candidate.rank_weight),
    ]
    wordfreq_base = _commonness_difficulty(
        row,
        known_key="wordfreq_de_known",
        score_key="wordfreq_de_commonness_score",
        gamma=candidate.wordfreq_gamma,
    )
    if wordfreq_base is not None and candidate.wordfreq_weight > 0.0:
        base_terms.append((wordfreq_base, candidate.wordfreq_weight))
    subtitles_base = _commonness_difficulty(
        row,
        known_key="opensubtitles_cistem_known",
        score_key="opensubtitles_cistem_frequency_score",
        gamma=candidate.subtitles_gamma,
    )
    if subtitles_base is not None and candidate.subtitles_weight > 0.0:
        base_terms.append((subtitles_base, candidate.subtitles_weight))
    base_weight_sum = sum(max(0.0, float(weight)) for _, weight in base_terms)
    if base_weight_sum <= 0.0:
        base = _clamp01(_safe_float(row.get("frequency_blend")) or 0.0)
    else:
        base = _clamp01(
            sum(float(value) * max(0.0, float(weight)) for value, weight in base_terms)
            / base_weight_sum
        )
    components = _derived_components(row, base=base)
    up_raw = sum(
        float(weight) * (_safe_float(components.get(component)) or 0.0)
        for component, weight in candidate.up_weights.items()
    )
    down_raw = sum(
        float(weight) * (_safe_float(components.get(component)) or 0.0)
        for component, weight in candidate.down_weights.items()
    )
    ease_backoff_raw = sum(
        float(weight) * (_safe_float(components.get(component)) or 0.0)
        for component, weight in candidate.ease_backoff_weights.items()
    )
    up = min(up_raw, candidate.up_cap)
    ease_backoff = min(ease_backoff_raw, candidate.ease_backoff_cap)
    down = min(down_raw, candidate.down_cap) * (1.0 - _clamp01(ease_backoff))
    score = _clamp01(base + up - down)
    floor_raw = sum(
        float(weight) * _dynamic_floor_component(component, score=score, components=components)
        for component, weight in candidate.floor_weights.items()
    )
    floor = min(floor_raw, candidate.floor_cap)
    score = _clamp01(score + floor)
    if candidate.warp_gamma != 1.0:
        score = score ** max(0.01, candidate.warp_gamma)
    return _round_float(_clamp01(score))


SOFT_FLOOR_COMPONENTS = {
    "sense_artifact_floor_030": ("sense_artifact_risk", 0.30),
    "sense_artifact_floor_034": ("sense_artifact_risk", 0.34),
    "polysemy_core_floor_030": ("polysemy_core_risk", 0.30),
    "polysemy_core_floor_034": ("polysemy_core_risk", 0.34),
    "function_word_floor_030": ("function_word_risk", 0.30),
    "function_word_floor_034": ("function_word_risk", 0.34),
    "domain_compound_floor_068": ("domain_compound_risk", 0.68),
    "domain_compound_floor_072": ("domain_compound_risk", 0.72),
    "intermediate_complexity_floor_040": ("intermediate_complexity_risk", 0.40),
    "intermediate_complexity_floor_044": ("intermediate_complexity_risk", 0.44),
}


def _dynamic_floor_component(
    component: str,
    *,
    score: float,
    components: Mapping[str, float],
) -> float:
    floor_spec = SOFT_FLOOR_COMPONENTS.get(component)
    if floor_spec is None:
        return _safe_float(components.get(component)) or 0.0
    risk_component, target = floor_spec
    risk = _safe_float(components.get(risk_component)) or 0.0
    return _clamp01(risk * max(0.0, target - score))


def _derived_components(row: Mapping[str, object], *, base: float) -> dict[str, float]:
    raw_pos = str(row.get("pos") or "")
    pos_bucket = str(row.get("pos_bucket") or "")
    translation_count = int(row.get("translation_count") or 0)
    reverse_count = int(row.get("reverse_support_count") or 0)
    has_sub = "SUB:" in raw_pos
    has_ver = "VER:" in raw_pos
    participle = 1.0 if "PA1" in raw_pos or "PA2" in raw_pos else 0.0
    mixed_pos = 1.0 if has_sub and has_ver else 0.0
    translation_score = _safe_float(row.get("translation_count_score")) or 0.0
    reverse_score = _safe_float(row.get("reverse_support_score")) or 0.0
    content_gate = _safe_float(row.get("content_pos_gate")) or 0.0
    length_score = _safe_float(row.get("length_risk")) or 0.0
    compound_score = _safe_float(row.get("compound_like")) or 0.0
    topic_documented = _safe_float(row.get("topic_documented")) or 0.0
    wiktionary_entry_ambiguity = _ramp(row.get("wiktionary_entry_count"), 1.0, 4.0)
    wiktionary_pos_ambiguity = _ramp(row.get("wiktionary_pos_count"), 1.0, 3.0)
    wiktionary_sense_ambiguity = _safe_float(row.get("wiktionary_sense_count_score")) or 0.0
    wiktionary_ambiguity = max(
        wiktionary_entry_ambiguity,
        wiktionary_pos_ambiguity,
        wiktionary_sense_ambiguity,
    )
    function_pos_gate = 1.0 if pos_bucket in {"adjective", "adverb"} or "ADV:" in raw_pos else 0.0
    low_core_gate = 1.0 - _ramp(base, 0.42, 0.76)
    tail35 = _ramp(base, 0.35, 0.85)
    tail55 = _ramp(base, 0.55, 0.95)
    learner_known = _safe_float(row.get("openlingo_learner_source_known")) or 0.0
    learner_confidence = _safe_float(row.get("openlingo_learner_source_confidence")) or 0.0
    learner_target = _safe_float(row.get("openlingo_learner_core_score"))
    learner_strength = _clamp01(learner_known * learner_confidence)
    learner_target_value = _clamp01(learner_target if learner_target is not None else base)
    learner_core_known = _safe_float(row.get("learner_source_known")) or 0.0
    learner_core_confidence = _safe_float(row.get("learner_source_confidence")) or 0.0
    learner_core_target = _safe_float(row.get("learner_core_score"))
    learner_core_strength = _clamp01(learner_core_known * learner_core_confidence)
    learner_core_target_value = _clamp01(
        learner_core_target if learner_core_target is not None else base
    )
    goethe_a1_known = _safe_float(row.get("goethe_official_a1_learner_source_known")) or 0.0
    goethe_a1_confidence = (
        _safe_float(row.get("goethe_official_a1_learner_source_confidence")) or 0.0
    )
    goethe_a1_target = _safe_float(row.get("goethe_official_a1_learner_core_score"))
    goethe_a1_strength = _clamp01(goethe_a1_known * goethe_a1_confidence)
    goethe_a1_target_value = _clamp01(goethe_a1_target if goethe_a1_target is not None else 0.08)
    goethe_stem_known = _safe_float(row.get("goethe_stem_learner_source_known")) or 0.0
    goethe_stem_confidence = _safe_float(row.get("goethe_stem_learner_source_confidence")) or 0.0
    goethe_stem_target = _safe_float(row.get("goethe_stem_learner_core_score"))
    goethe_stem_strength = _clamp01(goethe_stem_known * goethe_stem_confidence)
    goethe_stem_target_value = _clamp01(
        goethe_stem_target if goethe_stem_target is not None else base
    )
    odenet_basis_known = _safe_float(row.get("odenet_basis_learner_source_known")) or 0.0
    odenet_basis_confidence = _safe_float(row.get("odenet_basis_learner_source_confidence")) or 0.0
    odenet_basis_target = _safe_float(row.get("odenet_basis_learner_core_score"))
    odenet_basis_strength = _clamp01(odenet_basis_known * odenet_basis_confidence)
    odenet_basis_target_value = _clamp01(
        odenet_basis_target if odenet_basis_target is not None else base
    )
    learner_nonbeginner_signal = max(
        learner_core_strength * _ramp(learner_core_target_value, 0.12, 0.46),
        learner_strength * _ramp(learner_target_value, 0.12, 0.46),
    )
    klexikon_known = _safe_float(row.get("klexikon_title_known")) or 0.0
    exact_beginner_strength = max(goethe_a1_strength, klexikon_known)
    non_exact_beginner_gate = _clamp01(1.0 - (0.70 * exact_beginner_strength))
    semantic_breadth = _clamp01(
        0.60 * translation_score + 0.20 * reverse_score + 0.20 * wiktionary_ambiguity
    )
    grammar_diffuseness = _clamp01(
        0.50 * translation_score
        + 0.30 * (1.0 - reverse_score)
        + 0.20 * (1.0 if translation_count <= 0 else 0.0)
    )
    learner_core_ceiling_gap = _clamp01(
        max(0.0, base - learner_core_target_value) * learner_core_strength
    )
    learner_ceiling_ambiguity = _clamp01(
        0.35 * semantic_breadth
        + 0.25 * mixed_pos
        + 0.20 * function_pos_gate
        + 0.20 * (1.0 - content_gate)
    )
    intermediate_complexity = _clamp01(
        0.30 * length_score
        + 0.20 * compound_score
        + 0.30 * semantic_breadth
        + 0.20 * (1.0 - (_safe_float(row.get("english_translation_similarity_ease")) or 0.0))
    )
    sense_artifact_risk = _clamp01(
        mixed_pos
        * non_exact_beginner_gate
        * (0.35 + 0.45 * semantic_breadth + 0.20 * learner_nonbeginner_signal)
        * (0.35 + 0.65 * low_core_gate)
    )
    domain_compound_risk = _clamp01(
        (0.55 * length_score + 0.45 * compound_score)
        * (1.0 - (0.65 * max(klexikon_known, goethe_a1_strength)))
        * (0.35 + 0.65 * _ramp(base, 0.34, 0.76))
    )
    polysemy_core_risk = _clamp01(
        translation_score
        * non_exact_beginner_gate
        * (0.35 + 0.25 * mixed_pos + 0.20 * topic_documented + 0.20 * wiktionary_ambiguity)
        * (0.45 + 0.55 * low_core_gate)
    )
    function_word_risk = _clamp01(
        function_pos_gate
        * non_exact_beginner_gate
        * (0.35 + 0.45 * grammar_diffuseness + 0.20 * learner_nonbeginner_signal)
        * (0.45 + 0.55 * low_core_gate)
    )
    learner_ease_backoff_risk = _clamp01(
        non_exact_beginner_gate
        * (0.55 * learner_ceiling_ambiguity + 0.45 * intermediate_complexity)
    )
    intermediate_complexity_risk = _clamp01(
        non_exact_beginner_gate * intermediate_complexity * (0.35 + 0.65 * _ramp(base, 0.18, 0.72))
    )
    domain_source_signal = max(
        _safe_float(row.get("broad_learner_source_absent")) or 0.0,
        learner_core_strength * _ramp(learner_core_target_value, 0.24, 0.68),
        0.45 * (1.0 - reverse_score),
        0.35,
    )
    wordfreq_difficulty = _commonness_difficulty(
        row,
        known_key="wordfreq_de_known",
        score_key="wordfreq_de_commonness_score",
        gamma=1.0,
    )
    subtitles_difficulty = _commonness_difficulty(
        row,
        known_key="opensubtitles_cistem_known",
        score_key="opensubtitles_cistem_frequency_score",
        gamma=1.0,
    )
    external_modern_difficulty = _commonness_difficulty(
        row,
        known_key="external_modern_source_known",
        score_key="external_modern_frequency_score",
        gamma=1.0,
    )
    wordfreq_tail_strength = (_safe_float(row.get("wordfreq_de_known")) or 0.0) * tail35
    subtitles_tail_strength = (_safe_float(row.get("opensubtitles_cistem_known")) or 0.0) * tail35
    external_modern_tail_strength = (
        _safe_float(row.get("external_modern_source_known")) or 0.0
    ) * tail35
    broad_learner_absent = _safe_float(row.get("broad_learner_source_absent")) or 0.0
    external_modern_known = _safe_float(row.get("external_modern_source_known")) or 0.0
    return {
        "learner_source_pull_down": _clamp01(
            max(0.0, base - learner_target_value) * learner_strength
        ),
        "learner_source_pull_up": _clamp01(
            max(0.0, learner_target_value - base) * learner_strength
        ),
        "learner_core_soft_ceiling": _clamp01(learner_core_ceiling_gap),
        "learner_core_soft_floor": _clamp01(
            max(0.0, learner_core_target_value - base) * learner_core_strength
        ),
        "goethe_a1_soft_ceiling": _clamp01(
            max(0.0, base - goethe_a1_target_value) * goethe_a1_strength
        ),
        "goethe_stem_soft_ceiling": _clamp01(
            max(0.0, base - goethe_stem_target_value) * goethe_stem_strength
        ),
        "odenet_basis_pull_down": _clamp01(
            max(0.0, base - odenet_basis_target_value) * odenet_basis_strength
        ),
        "wordfreq_tail_rescue": _soft_ceiling_gap(
            base,
            target=wordfreq_difficulty,
            margin=0.06,
            strength=wordfreq_tail_strength,
        ),
        "subtitles_tail_rescue": _soft_ceiling_gap(
            base,
            target=subtitles_difficulty,
            margin=0.08,
            strength=subtitles_tail_strength,
        ),
        "modern_tail_rescue": _soft_ceiling_gap(
            base,
            target=external_modern_difficulty,
            margin=0.07,
            strength=external_modern_tail_strength,
        ),
        "klexikon_child_cap_060": _clamp01(max(0.0, base - 0.60) * klexikon_known * tail35),
        "klexikon_child_cap_070": _clamp01(max(0.0, base - 0.70) * klexikon_known * tail35),
        "simple_common_gloss_ease": _clamp01(
            (_safe_float(row.get("english_translation_frequency_ease")) or 0.0)
            * (_safe_float(row.get("reverse_support_score")) or 0.0)
            * (_safe_float(row.get("content_pos_gate")) or 0.0)
            * (1.0 - (0.45 * (_safe_float(row.get("translation_count_score")) or 0.0)))
        ),
        "cognate_ease": _clamp01(
            (_safe_float(row.get("english_translation_similarity_ease")) or 0.0)
            * (
                0.35
                + 0.35 * (_safe_float(row.get("reverse_support_score")) or 0.0)
                + 0.30 * (_safe_float(row.get("english_translation_frequency_ease")) or 0.0)
            )
        ),
        "common_gloss_ease": _clamp01(
            (_safe_float(row.get("english_translation_frequency_ease")) or 0.0)
            * (_safe_float(row.get("reverse_support_score")) or 0.0)
            * (_safe_float(row.get("content_pos_gate")) or 0.0)
        ),
        "tail_common_gloss_ease": _clamp01(
            (_safe_float(row.get("english_translation_frequency_ease")) or 0.0)
            * (_safe_float(row.get("reverse_support_score")) or 0.0)
            * (_safe_float(row.get("content_pos_gate")) or 0.0)
            * _ramp(base, 0.45, 0.85)
        ),
        "topic_tail_ease": _clamp01((_safe_float(row.get("topic_documented")) or 0.0) * tail35),
        "length_tail_risk": _clamp01(length_score * tail35),
        "compound_tail_risk": _clamp01(compound_score * tail35),
        "long_compound_heavy_risk": _clamp01(
            (0.70 * length_score + 0.30 * compound_score) * _ramp(base, 0.42, 0.78)
        ),
        "polysemy_risk": _clamp01(translation_score * (0.25 + (0.75 * _ramp(base, 0.18, 0.80)))),
        "learner_ceiling_backoff": _clamp01(learner_core_ceiling_gap * learner_ceiling_ambiguity),
        "non_exact_learner_backoff": _clamp01(
            learner_core_ceiling_gap * non_exact_beginner_gate * intermediate_complexity
        ),
        "learner_ease_backoff_risk": learner_ease_backoff_risk,
        "sense_artifact_risk": sense_artifact_risk,
        "domain_compound_risk": _clamp01(domain_compound_risk * domain_source_signal),
        "polysemy_core_risk": polysemy_core_risk,
        "function_word_risk": function_word_risk,
        "intermediate_complexity_risk": intermediate_complexity_risk,
        "sense_pos_artifact_guard": sense_artifact_risk,
        "domain_compound_guard": _clamp01(domain_compound_risk * domain_source_signal),
        "polysemy_core_floor": polysemy_core_risk,
        "function_word_guard": function_word_risk,
        "no_signal_tail_risk": _clamp01(
            (
                (1.0 if translation_count <= 0 else 0.0) * 0.70
                + (1.0 if reverse_count <= 0 else 0.0) * 0.30
            )
            * tail55
        ),
        "broad_learner_absence_tail_risk": _clamp01(broad_learner_absent * tail55),
        "modern_source_absence_tail_risk": _clamp01((1.0 - external_modern_known) * tail55),
        "wiktionary_marked_tail_risk": _clamp01(
            (_safe_float(row.get("wiktionary_marked_usage_flag")) or 0.0) * _ramp(base, 0.35, 0.85)
        ),
        "wiktionary_rare_dated_tail_risk": _clamp01(
            (_safe_float(row.get("wiktionary_rare_dated_flag")) or 0.0) * _ramp(base, 0.25, 0.80)
        ),
        "wiktionary_form_variant_tail_risk": _clamp01(
            (_safe_float(row.get("wiktionary_form_variant_score")) or 0.0) * _ramp(base, 0.25, 0.85)
        ),
        "wiktionary_ambiguity_tail_risk": _clamp01(
            (_safe_float(row.get("wiktionary_sense_count_score")) or 0.0)
            * (0.20 + (0.80 * _ramp(base, 0.35, 0.90)))
        ),
        "participle_tail_risk": _clamp01(participle * _ramp(base, 0.25, 0.85)),
        "mixed_pos_tail_risk": _clamp01(mixed_pos * 0.50 * _ramp(base, 0.30, 0.85)),
        "other_pos_tail_risk": _clamp01(
            (_safe_float(row.get("other_pos_risk")) or 0.0) * _ramp(base, 0.50, 0.95)
        ),
    }


def _with_change_samples(
    record: Mapping[str, object],
    *,
    rows: Sequence[Mapping[str, object]],
    candidate: FormulaCandidate | None,
    sample_limit: int,
) -> dict[str, object]:
    if candidate is None:
        return dict(record)
    scored = []
    for row in rows:
        raw = _safe_float(row.get("frequency_blend"))
        score = _score_row(candidate, row)
        if raw is None or score is None:
            continue
        scored.append(
            {
                "lemma": row.get("lemma"),
                "raw_frequency": _round_float(raw),
                "candidate_score": _round_float(score),
                "delta": _round_float(score - raw),
                "pos_bucket": row.get("pos_bucket"),
                "translations": list(_as_sequence(row.get("translations")))[:3],
            }
        )
    result = dict(record)
    result["largest_raw_frequency_shifts"] = sorted(
        scored,
        key=lambda row: abs(float(row.get("delta") or 0.0)),
        reverse=True,
    )[:sample_limit]
    return result


def _largest_errors(
    row_pairs: Sequence[tuple[Mapping[str, object], Mapping[str, object] | None, float]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    rows = []
    for label, row, observed in row_pairs:
        expected = _safe_float(label.get("expected_learner_difficulty"))
        if expected is None or not np.isfinite(observed):
            continue
        rows.append(
            {
                "lemma": label.get("lemma"),
                "expected": _round_float(expected),
                "observed": _round_float(observed),
                "abs_error": _round_float(abs(observed - expected)),
                "expected_band": label.get("expected_difficulty_band"),
                "observed_band": _difficulty_band(observed),
                "source_frequency_blend": _round_float(
                    _safe_float(_as_mapping(row).get("frequency_blend"))
                ),
                "review_flags": list(_as_sequence(label.get("review_flags"))),
            }
        )
    return sorted(rows, key=lambda item: float(item.get("abs_error") or 0.0), reverse=True)[:limit]


def _compact_record(record: Mapping[str, object]) -> dict[str, object]:
    return {
        "candidate_id": record.get("candidate_id"),
        "calibration_balanced": _score_at(record, "calibration_primary", "balanced_score"),
        "holdout_balanced": _score_at(record, "holdout_primary", "balanced_score"),
        "calibration_mae": _metric_at(record, "calibration_primary", "mae"),
        "holdout_mae": _metric_at(record, "holdout_primary", "mae"),
        "calibration_pairwise": _metric_at(record, "calibration_primary", "pairwise_accuracy"),
        "holdout_pairwise": _metric_at(record, "holdout_primary", "pairwise_accuracy"),
        "product_objective_score": _product_objective_at(record, "objective_score"),
        "product_distribution_score": _product_objective_at(record, "distribution_score"),
        "product_sentinel_score": _product_objective_at(record, "sentinel_score"),
        "product_calibration_score": _product_adjusted_at(record, "calibration_score"),
        "product_holdout_score": _product_adjusted_at(record, "holdout_score"),
        "product_stable_score": _product_adjusted_at(record, "stable_score"),
        "profile": record.get("profile"),
    }


def _compact_eval(item: object) -> dict[str, object]:
    row = _as_mapping(item)
    scores = _as_mapping(row.get("scores"))
    metrics = _as_mapping(row.get("metrics"))
    return {
        "count": row.get("label_count"),
        "balanced_score": scores.get("balanced_score"),
        "mae": metrics.get("mae"),
        "bucket_accuracy": metrics.get("bucket_accuracy"),
        "pairwise_accuracy": metrics.get("pairwise_accuracy"),
        "high_tail_score": scores.get("high_tail_score"),
    }


def _calibration_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    return (
        _score_at(row, "calibration_primary", "balanced_score") or -1.0,
        _score_at(row, "holdout_primary", "balanced_score") or -1.0,
        _metric_at(row, "calibration_primary", "pairwise_accuracy") or -1.0,
        -(_metric_at(row, "calibration_primary", "mae") or 999.0),
    )


def _holdout_guarded_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    return (
        min(
            _score_at(row, "calibration_primary", "balanced_score") or -1.0,
            _score_at(row, "holdout_primary", "balanced_score") or -1.0,
        ),
        _score_at(row, "calibration_primary", "balanced_score") or -1.0,
        _metric_at(row, "holdout_primary", "pairwise_accuracy") or -1.0,
        -(_metric_at(row, "holdout_primary", "mae") or 999.0),
    )


def _stable_sort_key(row: Mapping[str, object]) -> tuple[float, float, float]:
    cal = _score_at(row, "calibration_primary", "balanced_score") or -1.0
    holdout = _score_at(row, "holdout_primary", "balanced_score") or -1.0
    gap = abs(cal - holdout)
    mean_score = (cal + holdout) / 2.0
    return (mean_score - gap * 0.35, min(cal, holdout), -gap)


def _product_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    return (
        _product_adjusted_at(row, "stable_score") or -1.0,
        _product_adjusted_at(row, "holdout_score") or -1.0,
        _product_adjusted_at(row, "calibration_score") or -1.0,
        _product_objective_at(row, "objective_score") or -1.0,
    )


def _candidate_by_id(
    candidates: Sequence[FormulaCandidate],
    candidate_id: str,
) -> FormulaCandidate | None:
    for candidate in candidates:
        if candidate.candidate_id == candidate_id:
            return candidate
    return None


def _unique_records(
    records: Sequence[Mapping[str, object]],
    *,
    key: str,
) -> list[Mapping[str, object]]:
    result = []
    seen = set()
    for record in records:
        value = str(record.get(key) or "")
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(record)
    return result


def _score_at(row: Mapping[str, object], eval_key: str, score_key: str) -> float | None:
    return _safe_float(_as_mapping(_as_mapping(row.get(eval_key)).get("scores")).get(score_key))


def _metric_at(row: Mapping[str, object], eval_key: str, metric_key: str) -> float | None:
    return _safe_float(_as_mapping(_as_mapping(row.get(eval_key)).get("metrics")).get(metric_key))


def _product_objective_at(row: Mapping[str, object], key: str) -> float | None:
    return _safe_float(_as_mapping(row.get("product_objective")).get(key))


def _product_sentinel_at(row: Mapping[str, object], key: str) -> float | None:
    return _safe_float(
        _as_mapping(_as_mapping(row.get("product_objective")).get("sentinel")).get(key)
    )


def _product_adjusted_at(row: Mapping[str, object], key: str) -> float | None:
    return _safe_float(_as_mapping(row.get("product_adjusted")).get(key))


def _difficulty_band(value: float) -> str:
    if value < 0.20:
        return "beginner"
    if value < 0.40:
        return "core"
    if value < 0.60:
        return "intermediate"
    if value < 0.80:
        return "advanced"
    if value < 0.94:
        return "tail"
    return "recondite"


def _commonness_difficulty(
    row: Mapping[str, object],
    *,
    known_key: str,
    score_key: str,
    gamma: float,
) -> float | None:
    if (_safe_float(row.get(known_key)) or 0.0) <= 0.0:
        return None
    commonness = _safe_float(row.get(score_key))
    if commonness is None:
        return None
    difficulty = 1.0 - _clamp01(commonness)
    return _clamp01(difficulty ** max(0.01, float(gamma)))


def _soft_ceiling_gap(
    base: float,
    *,
    target: float | None,
    margin: float,
    strength: float,
) -> float:
    if target is None:
        return 0.0
    return _clamp01(max(0.0, base - _clamp01(target) - max(0.0, float(margin))) * strength)


def _ramp(value: object, low: float, high: float) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    if numeric <= low:
        return 0.0
    if numeric >= high:
        return 1.0
    return (numeric - low) / (high - low)


def _clamp01(value: object) -> float:
    return min(1.0, max(0.0, _safe_float(value) or 0.0))


def _round_float(value: object, digits: int = 6) -> float | None:
    numeric = _safe_float(value)
    return round(numeric, digits) if numeric is not None and np.isfinite(numeric) else None


def _safe_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_weights(values: Sequence[object]) -> list[float]:
    parsed = [max(0.0, _safe_float(value) or 0.0) for value in values]
    total = sum(parsed)
    if total <= 0.0:
        return []
    return [value / total for value in parsed]


def _cumulative(values: Sequence[float]) -> list[float]:
    result = []
    running = 0.0
    for value in values:
        running += float(value)
        result.append(running)
    return result


def _deterministic_product_sample(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[Mapping[str, object]]:
    if limit <= 0:
        return []
    if limit >= len(rows):
        return list(rows)
    return sorted(rows, key=_product_sample_key)[:limit]


def _product_sample_key(row: Mapping[str, object]) -> tuple[str, float]:
    lemma = str(row.get("lemma") or "")
    rank = _safe_float(row.get("core_rank")) or 999999999.0
    digest = hashlib.sha256(f"{PRODUCT_OBJECTIVE_SAMPLE_SEED}:{lemma}".encode("utf-8")).hexdigest()
    return (digest, rank)


def _load_optional_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    return _load_json(path)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[Mapping[str, object]]:
    rows: list[Mapping[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            if isinstance(row, Mapping):
                rows.append(row)
    return rows


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:.3f}"


def _fmt_signed(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:+.3f}"


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


if __name__ == "__main__":
    raise SystemExit(main())
