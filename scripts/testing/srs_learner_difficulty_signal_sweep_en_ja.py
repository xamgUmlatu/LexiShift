#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections.abc import Iterable
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
import json
import lzma
import math
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence

try:  # Optional fast path for large target-curve sweeps.
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - exercised only on minimal envs.
    np = None  # type: ignore[assignment]

try:  # Research-only sidecar signal; product promotion needs source/licensing review.
    from wordfreq import zipf_frequency as _wordfreq_zipf_frequency
except ModuleNotFoundError:  # pragma: no cover - depends on local research env.
    _wordfreq_zipf_frequency = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(CORE_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import (  # noqa: E402
    attach_provenance_to_npz_metadata,
    build_artifact_provenance,
)
from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_frequency_db_path,
    default_japanese_lesson_vocabulary_path,
    default_jmdict_path,
    default_jmnedict_path,
    default_jlpt_vocabulary_path,
    default_kanjidic2_path,
    default_kanjivg_path,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.resources.japanese_learner_signals import (  # noqa: E402
    JAPANESE_LEARNER_SIGNALS_VERSION,
    JA_ACRONYM_SIGNAL_VERSION,
    JMDICT_LEXICAL_INDEX_VERSION,
)
from lexishift_core.resources.japanese_script import contains_kanji  # noqa: E402
from lexishift_core.srs.candidate_classification import (  # noqa: E402
    CANDIDATE_CLASSIFICATION_VERSION,
)
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from srs_learner_difficulty_audit_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_JSON,
    PAIR,
    _build_calibration_rows,
    _calibration_metrics,
    _dedupe_seeds,
    _difficulty_band_for_value,
    _difficulty_absolute_error,
    _difficulty_summary,
    _repo_or_home_path,
    _resolve_path,
    _seed_row,
)
from srs_learner_difficulty_normalization import (  # noqa: E402
    DEFAULT_BAND_WIDTH,
    DEFAULT_TARGET_BAND_WEIGHTS,
    TARGET_CURVE_ID,
    difficulty_bands,
    normalize_rows_by_target_curve,
    parse_band_weights_csv,
    target_band_counts,
)


DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_signal_sweep_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_signal_sweep_en_ja_latest.md"
)
DEFAULT_PROFICIENCY_LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)
DEFAULT_EXAMPLE_LIMIT = 10
ENGLISH_SOURCE_LANGUAGE_CODES = frozenset({"en", "eng", "english"})
NATIVE_OR_SINITIC_SOURCE_LANGUAGE_CODES = frozenset(
    {"jpn", "japanese", "ja", "chi", "chn", "chinese", "zh"}
)
SOURCE_TEXT_WORD_RE = re.compile(r"[a-z]+(?:[-'][a-z]+)*")
DEFAULT_WINDOW_SIZE = 40
DEFAULT_SCORE_NORMALIZATION = "target_curve"
COMPONENT_CACHE_KEY = "_difficulty_components"
SCORE_NORMALIZATIONS = frozenset({"raw", "target_curve"})
DIFFICULTY_COMPONENT_MAX_RANK = 2500.0
TUBELEX_SIGNAL_VERSION = 1
TUBELEX_DEFAULT_PACK_ID = "freq-ja-tubelex"
TUBELEX_DEFAULT_FILENAME = "tubelex-ja-lemma-pos.tsv.xz"
TUBELEX_COMPONENT_MAX_RANK = 100000.0
VOCAB_STATES = frozenset({"normal_vocab", "deprioritized_vocab"})
DEFAULT_JLPT_VOCAB_CURVE = {5: 0.08, 4: 0.22, 3: 0.42, 2: 0.65, 1: 0.85}
JLPT_DAMPENED_KANJI_COMPONENTS = frozenset(
    {
        "old_jlpt_kanji",
        "kanji_grade",
        "kanji_frequency_rank",
        "stroke_count",
        "kanjivg_visual_complexity",
        "kanji_curriculum_burden",
        "kanji_shape_burden",
        "max_kanji_shape_burden",
        "kanji_burden",
        "max_kanji_burden",
        "written_form_burden",
        "max_written_form_burden",
        "kango_old_jlpt_kanji",
        "kango_kanji_grade",
        "kango_visual_complexity",
        "kango_kanji_burden",
        "kango_uncommon_kanji_burden",
        "kango_mid_signal",
    }
)
DEFAULT_GRID_SIGNALS = (
    "frequency",
    "jmdict_priority",
    "kanji_grade",
    "kanji_curriculum_missing_risk",
    "rare_non_standard_reading_risk",
    "old_jlpt_kanji",
    "stroke_count",
    "kanjivg_visual_complexity",
)
DEFAULT_GRID_CAPS = (None, 0.05, 0.08, 0.10, 0.15)
DEFAULT_LEADERBOARD_LIMIT = 20
DEFAULT_RETAIN_VARIANT_LIMIT = 100
SWEEP_SCORE_KEYS = (
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
PAIRWISE_MIN_EXPECTED_GAP = 0.03
PAIRWISE_TIE_TOLERANCE = 0.01
BEGINNER_CORE_MAX = 0.20
BEGINNER_CORE_OBSERVED_CEILING = 0.25
BEGINNER_BROAD_MAX = 0.40
BEGINNER_BROAD_OBSERVED_CEILING = 0.50
UPPER_TAIL_MIN = 0.88
UPPER_TAIL_OBSERVED_FLOOR = 0.80
HIGH_TAIL_MIN = 0.94
HIGH_TAIL_OBSERVED_FLOOR = 0.88


@dataclass(frozen=True)
class PiecewiseFormulaSection:
    section_id: str
    center: float
    radius: float
    weights: Mapping[str, float]
    max_shift_from_frequency: float | None = None


@dataclass(frozen=True)
class FormulaVariant:
    variant_id: str
    description: str
    weights: Mapping[str, float]
    use_current_value: bool = False
    max_shift_from_frequency: float | None = None
    piecewise_sections: tuple[PiecewiseFormulaSection, ...] = ()
    jlpt_vocab_curve: Mapping[int, float] | None = None
    jlpt_kanji_dampening_strength: float = 0.0


@dataclass(frozen=True)
class TargetCurveScoringContext:
    component_names: tuple[str, ...]
    component_values: object
    component_present: object
    current_values: object
    frequency_values: object
    jlpt_vocab_levels: object
    dedupe_values: tuple[str, ...]
    dedupe_to_index: Mapping[str, int]
    normalized_positions: object


@dataclass(frozen=True)
class TubelexFrequencyEntry:
    word: str
    pos: str
    rank: int
    count: float
    videos: float
    channels: float


@dataclass(frozen=True)
class TubelexFrequencyIndex:
    source_path: Path
    source_variant: str
    row_count: int
    max_count: float
    max_videos: float
    max_channels: float
    by_word: Mapping[str, TubelexFrequencyEntry]
    by_word_pos: Mapping[tuple[str, str], TubelexFrequencyEntry]


FORMULA_VARIANTS: tuple[FormulaVariant, ...] = (
    FormulaVariant(
        variant_id="current_production",
        description="Current runtime estimate: exact en-ja overlay where present, otherwise frequency.",
        weights={},
        use_current_value=True,
    ),
    FormulaVariant(
        variant_id="frequency_only",
        description="Pure BCCWJ frequency difficulty proxy.",
        weights={"frequency": 1.0},
    ),
    FormulaVariant(
        variant_id="priority_light",
        description="Mostly frequency, with a light JMDict priority correction.",
        weights={"frequency": 0.80, "jmdict_priority": 0.20},
    ),
    FormulaVariant(
        variant_id="priority_light_capped",
        description=(
            "Light JMDict priority correction, capped so priority cannot dominate frequency."
        ),
        weights={"frequency": 0.80, "jmdict_priority": 0.20},
        max_shift_from_frequency=0.08,
    ),
    FormulaVariant(
        variant_id="name_guarded_frequency",
        description=(
            "Frequency with gated entity-suppression risk as a conservative admission guard."
        ),
        weights={"frequency": 0.90, "ordinary_ladder_entity_suppression_risk": 0.10},
        max_shift_from_frequency=0.08,
    ),
    FormulaVariant(
        variant_id="lexical_guarded_frequency",
        description=(
            "Frequency with gated JMDict non-ladder lexical cues as a conservative guard."
        ),
        weights={"frequency": 0.90, "jmdict_non_ladder_entry_risk": 0.10},
        max_shift_from_frequency=0.08,
    ),
    FormulaVariant(
        variant_id="script_complexity_probe",
        description="Research probe: frequency with a light deterministic script-shape nudge.",
        weights={"frequency": 0.90, "script_complexity": 0.10},
        max_shift_from_frequency=0.08,
    ),
    FormulaVariant(
        variant_id="visual_complexity_probe",
        description=(
            "Research probe: frequency with light KANJIDIC2 and KanjiVG visual-complexity nudges."
        ),
        weights={
            "frequency": 0.80,
            "kanji_grade": 0.10,
            "kanjivg_visual_complexity": 0.10,
        },
        max_shift_from_frequency=0.08,
    ),
    FormulaVariant(
        variant_id="rare_wago_curriculum_gap_probe",
        description=(
            "Research probe: frequency with explicit no-priority rare-wago and "
            "missing-kanji-curriculum metadata risk."
        ),
        weights={
            "frequency": 0.55,
            "jmdict_priority": 0.10,
            "rare_wago_risk": 0.15,
            "rare_wago_missing_curriculum_risk": 0.20,
        },
        max_shift_from_frequency=0.20,
    ),
    FormulaVariant(
        variant_id="reading_irregularity_probe",
        description=(
            "Research probe: frequency with rarity-gated KANJIDIC2 reading irregularity risk."
        ),
        weights={
            "frequency": 0.65,
            "jmdict_priority": 0.10,
            "rare_non_standard_reading_risk": 0.25,
        },
        max_shift_from_frequency=0.20,
    ),
    FormulaVariant(
        variant_id="priority_kanji_balanced",
        description="Frequency plus JMDict priority plus KANJIDIC2 kanji grade.",
        weights={"frequency": 0.55, "jmdict_priority": 0.25, "kanji_grade": 0.20},
    ),
    FormulaVariant(
        variant_id="priority_kanji_balanced_capped",
        description=("Balanced signal blend, capped to treat learner signals as nudges."),
        weights={"frequency": 0.55, "jmdict_priority": 0.25, "kanji_grade": 0.20},
        max_shift_from_frequency=0.10,
    ),
    FormulaVariant(
        variant_id="kanji_rank_balanced",
        description="Balanced frequency/priority with kanji grade and KANJIDIC2 frequency rank.",
        weights={
            "frequency": 0.45,
            "jmdict_priority": 0.25,
            "kanji_grade": 0.20,
            "kanji_frequency_rank": 0.10,
        },
    ),
    FormulaVariant(
        variant_id="pedagogy_heavy",
        description="Higher reliance on explicit learner-facing kanji signals.",
        weights={
            "frequency": 0.25,
            "jmdict_priority": 0.25,
            "kanji_grade": 0.25,
            "old_jlpt_kanji": 0.15,
            "stroke_count": 0.10,
        },
    ),
    FormulaVariant(
        variant_id="piecewise_pedagogy_mid_tail_v1",
        description=(
            "Experimental smooth piecewise blend: pedagogical early band, "
            "bucket-oriented middle, and rarity/complexity upper tail."
        ),
        weights={},
        piecewise_sections=(
            PiecewiseFormulaSection(
                section_id="early_pedagogical",
                center=0.15,
                radius=0.35,
                weights={
                    "frequency": 0.30,
                    "kanji_grade": 0.10,
                    "kanjivg_visual_complexity": 0.10,
                    "old_jlpt_kanji": 0.40,
                    "script_complexity": 0.10,
                },
                max_shift_from_frequency=0.15,
            ),
            PiecewiseFormulaSection(
                section_id="middle_bucket",
                center=0.55,
                radius=0.35,
                weights={
                    "frequency": 0.20,
                    "jmdict_priority": 0.10,
                    "ordinary_ladder_entity_suppression_risk": 0.20,
                    "old_jlpt_kanji": 0.50,
                },
            ),
            PiecewiseFormulaSection(
                section_id="upper_tail_complexity",
                center=0.90,
                radius=0.30,
                weights={
                    "frequency": 0.20,
                    "kanji_frequency_rank": 0.20,
                    "script_complexity": 0.20,
                    "stroke_count": 0.40,
                },
            ),
        ),
    ),
    FormulaVariant(
        variant_id="piecewise_pedagogy_mid_visual_tail_v1",
        description=(
            "Experimental smooth piecewise blend with stronger visual complexity "
            "through the middle and upper tail."
        ),
        weights={},
        piecewise_sections=(
            PiecewiseFormulaSection(
                section_id="early_pedagogical",
                center=0.15,
                radius=0.35,
                weights={
                    "frequency": 0.30,
                    "jmdict_priority": 0.10,
                    "kanji_grade": 0.10,
                    "old_jlpt_kanji": 0.40,
                    "script_complexity": 0.10,
                },
                max_shift_from_frequency=0.15,
            ),
            PiecewiseFormulaSection(
                section_id="middle_visual",
                center=0.55,
                radius=0.35,
                weights={
                    "frequency": 0.25,
                    "jmdict_priority": 0.10,
                    "kanjivg_visual_complexity": 0.30,
                    "old_jlpt_kanji": 0.25,
                    "script_complexity": 0.10,
                },
            ),
            PiecewiseFormulaSection(
                section_id="upper_visual_tail",
                center=0.90,
                radius=0.30,
                weights={
                    "frequency": 0.15,
                    "kanji_frequency_rank": 0.15,
                    "kanjivg_visual_complexity": 0.35,
                    "script_complexity": 0.15,
                    "stroke_count": 0.20,
                },
            ),
        ),
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Research-only sweep over en-ja learner-difficulty signal formulae. "
            "This script does not change production runtime behavior."
        )
    )
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--jmdict", type=Path)
    parser.add_argument("--jmnedict", type=Path)
    parser.add_argument("--kanjidic2", type=Path)
    parser.add_argument("--kanjivg", type=Path)
    parser.add_argument("--jlpt-vocabulary", type=Path)
    parser.add_argument("--lesson-vocabulary", type=Path)
    parser.add_argument(
        "--tubelex-frequency-tsv",
        type=Path,
        default=None,
        help=(
            "Optional TUBELEX Japanese frequency TSV.xz sidecar. If omitted, the "
            "default local freq-ja-tubelex/tubelex-ja-lemma-pos.tsv.xz file is used "
            "when present."
        ),
    )
    parser.add_argument(
        "--no-tubelex-frequency",
        action="store_true",
        help="Disable auto-discovery of the local TUBELEX Japanese frequency sidecar.",
    )
    parser.add_argument("--top-n", type=int, default=None)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument(
        "--proficiency-levels",
        default=",".join(f"{value:.2f}" for value in DEFAULT_PROFICIENCY_LEVELS),
    )
    parser.add_argument("--window-size", type=int, default=DEFAULT_WINDOW_SIZE)
    parser.add_argument("--example-limit", type=int, default=DEFAULT_EXAMPLE_LIMIT)
    parser.add_argument(
        "--score-normalization",
        choices=sorted(SCORE_NORMALIZATIONS),
        default=DEFAULT_SCORE_NORMALIZATION,
        help=(
            "Whether calibration scoring uses raw formula values or the same monotonic "
            "target-curve normalization used by the contender sample report."
        ),
    )
    parser.add_argument(
        "--target-band-weights",
        default=",".join(f"{value:g}" for value in DEFAULT_TARGET_BAND_WEIGHTS),
        help="Comma-separated target band weights used when --score-normalization=target_curve.",
    )
    parser.add_argument(
        "--band-width",
        type=float,
        default=DEFAULT_BAND_WIDTH,
        help="Difficulty band width for target-curve normalization.",
    )
    parser.add_argument(
        "--variant-mode",
        choices=("presets", "grid"),
        default="presets",
        help="Use hand-authored preset variants or generate a normalized weight grid.",
    )
    parser.add_argument(
        "--calibration-only",
        action="store_true",
        help=(
            "Score variants only against calibration labels. This skips full frontier "
            "and proficiency-window generation so large grids stay tractable."
        ),
    )
    parser.add_argument(
        "--grid-signals",
        default=",".join(DEFAULT_GRID_SIGNALS),
        help="Comma-separated signal names to include when --variant-mode=grid.",
    )
    parser.add_argument(
        "--grid-step",
        type=float,
        default=0.10,
        help="Normalized weight increment for grid mode, for example 0.10 or 0.05.",
    )
    parser.add_argument(
        "--grid-caps",
        default=",".join(
            "none" if value is None else f"{value:.2f}" for value in DEFAULT_GRID_CAPS
        ),
        help="Comma-separated max-shift caps for grid mode; use 'none' for uncapped.",
    )
    parser.add_argument(
        "--grid-min-weights",
        default="",
        help=(
            "Optional comma-separated minimum weights as signal=value pairs. "
            "Example: frequency=0.20 forces frequency to be a real factor."
        ),
    )
    parser.add_argument(
        "--grid-max-weights",
        default="",
        help=(
            "Optional comma-separated maximum weights as signal=value pairs. "
            "Example: old_jlpt_kanji=0.60 prevents one signal from dominating."
        ),
    )
    parser.add_argument(
        "--grid-center",
        default="",
        help=(
            "Optional local-search center as comma-separated signal=value pairs. "
            "Signals not listed are treated as 0."
        ),
    )
    parser.add_argument(
        "--grid-radius",
        type=float,
        default=None,
        help=(
            "Optional local-search max per-signal distance from --grid-center. "
            "Only applies in grid mode when --grid-center is set."
        ),
    )
    parser.add_argument(
        "--jlpt-vocab-curve-grid",
        action="store_true",
        help=(
            "Expand each formula variant over a monotonic grid of word-level JLPT "
            "difficulty mappings. By default the baked source mapping is left unchanged."
        ),
    )
    parser.add_argument(
        "--jlpt-vocab-n5-values",
        default=f"{DEFAULT_JLPT_VOCAB_CURVE[5]:g}",
        help="Comma-separated N5 difficulty values used with --jlpt-vocab-curve-grid.",
    )
    parser.add_argument(
        "--jlpt-vocab-n4-values",
        default=f"{DEFAULT_JLPT_VOCAB_CURVE[4]:g}",
        help="Comma-separated N4 difficulty values used with --jlpt-vocab-curve-grid.",
    )
    parser.add_argument(
        "--jlpt-vocab-n3-values",
        default=f"{DEFAULT_JLPT_VOCAB_CURVE[3]:g}",
        help="Comma-separated N3 difficulty values used with --jlpt-vocab-curve-grid.",
    )
    parser.add_argument(
        "--jlpt-vocab-n2-values",
        default=f"{DEFAULT_JLPT_VOCAB_CURVE[2]:g}",
        help="Comma-separated N2 difficulty values used with --jlpt-vocab-curve-grid.",
    )
    parser.add_argument(
        "--jlpt-vocab-n1-values",
        default=f"{DEFAULT_JLPT_VOCAB_CURVE[1]:g}",
        help="Comma-separated N1 difficulty values used with --jlpt-vocab-curve-grid.",
    )
    parser.add_argument(
        "--jlpt-kanji-dampening-strengths",
        default="0",
        help=(
            "Comma-separated strengths for pulling kanji-burden components down toward "
            "the direct JLPT vocab anchor when one is present. 0 preserves old behavior; "
            "1 fully caps dampened kanji components at the JLPT anchor."
        ),
    )
    parser.add_argument(
        "--max-variants",
        type=int,
        default=None,
        help="Optional safety limit on generated/evaluated variants.",
    )
    parser.add_argument(
        "--leaderboard-limit",
        type=int,
        default=DEFAULT_LEADERBOARD_LIMIT,
        help="How many variants to retain per metric leaderboard in calibration-only mode.",
    )
    parser.add_argument(
        "--retain-variant-limit",
        type=int,
        default=DEFAULT_RETAIN_VARIANT_LIMIT,
        help="Maximum detailed variants retained in calibration-only mode.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--trace-json-out",
        type=Path,
        default=None,
        help=(
            "Optional compact trace JSON for calibration-only sweeps. Stores every "
            "variant's aggregate metrics and weights for post-hoc ranking."
        ),
    )
    parser.add_argument(
        "--trace-calibration-matrix-out",
        type=Path,
        default=None,
        help=(
            "Optional NPZ matrix for calibration-only sweeps. Stores every retained "
            "calibration label's observed difficulty for every evaluated variant."
        ),
    )
    parser.add_argument(
        "--component-matrix-out",
        type=Path,
        default=None,
        help=(
            "Optional NPZ matrix of normalization-population signal components. "
            "This is reusable for offline piecewise/formula research."
        ),
    )
    parser.add_argument(
        "--component-matrix-components",
        choices=("variant", "all"),
        default="variant",
        help=(
            "Which difficulty components to include in --component-matrix-out. "
            "'variant' preserves the old behavior and includes only components "
            "referenced by generated variants; 'all' includes every component "
            "exposed by difficulty_components(...)."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        jmdict_path=args.jmdict,
        jmnedict_path=args.jmnedict,
        kanjidic2_path=args.kanjidic2,
        kanjivg_path=args.kanjivg,
        jlpt_vocabulary_path=args.jlpt_vocabulary,
        lesson_vocabulary_path=args.lesson_vocabulary,
        tubelex_frequency_tsv=args.tubelex_frequency_tsv,
        use_default_tubelex_frequency=not bool(args.no_tubelex_frequency),
        top_n=max(1, int(args.top_n)) if args.top_n is not None else None,
        calibration_json=_resolve_path(args.calibration_json),
        proficiency_levels=_parse_float_csv(args.proficiency_levels),
        window_size=max(1, int(args.window_size)),
        example_limit=max(1, int(args.example_limit)),
        score_normalization=str(args.score_normalization),
        target_band_weights=parse_band_weights_csv(args.target_band_weights),
        band_width=float(args.band_width),
        variant_mode=str(args.variant_mode),
        calibration_only=bool(args.calibration_only),
        grid_signals=_parse_signal_csv(args.grid_signals),
        grid_step=float(args.grid_step),
        grid_caps=_parse_grid_caps(args.grid_caps),
        grid_min_weights=_parse_weight_mapping_csv(args.grid_min_weights),
        grid_max_weights=_parse_weight_mapping_csv(args.grid_max_weights),
        grid_center=_parse_weight_mapping_csv(args.grid_center),
        grid_radius=(max(0.0, float(args.grid_radius)) if args.grid_radius is not None else None),
        jlpt_vocab_curves=_jlpt_vocab_curves_from_args(args),
        jlpt_kanji_dampening_strengths=_parse_float_values_csv(
            args.jlpt_kanji_dampening_strengths,
            (0.0,),
        ),
        max_variants=(max(1, int(args.max_variants)) if args.max_variants is not None else None),
        leaderboard_limit=max(1, int(args.leaderboard_limit)),
        retain_variant_limit=max(1, int(args.retain_variant_limit)),
        include_compact_trace=args.trace_json_out is not None,
        include_calibration_matrix=args.trace_calibration_matrix_out is not None,
        include_component_matrix=args.component_matrix_out is not None,
        component_matrix_components=str(args.component_matrix_components),
    )
    compact_trace = report.pop("_compact_trace", None)
    calibration_matrix = report.pop("_calibration_prediction_matrix", None)
    component_matrix = report.pop("_component_matrix", None)
    provenance = report.get("provenance")
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    if args.trace_json_out is not None:
        if compact_trace is None:
            raise ValueError("--trace-json-out requires --calibration-only.")
        if isinstance(compact_trace, dict) and isinstance(provenance, Mapping):
            compact_trace["provenance"] = dict(provenance)
        trace_json_out = _resolve_path(args.trace_json_out)
        trace_json_out.parent.mkdir(parents=True, exist_ok=True)
        trace_json_out.write_text(
            json.dumps(compact_trace, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote trace JSON artifact to {trace_json_out}")
    if args.trace_calibration_matrix_out is not None:
        if calibration_matrix is None:
            raise ValueError("--trace-calibration-matrix-out requires --calibration-only.")
        if isinstance(provenance, Mapping):
            calibration_matrix = attach_provenance_to_npz_metadata(
                calibration_matrix,
                provenance,
            )
        _write_npz_artifact(_resolve_path(args.trace_calibration_matrix_out), calibration_matrix)
        print(
            "Wrote calibration matrix artifact to "
            f"{_resolve_path(args.trace_calibration_matrix_out)}"
        )
    if args.component_matrix_out is not None:
        if component_matrix is None:
            raise ValueError("--component-matrix-out could not be built; NumPy may be unavailable.")
        if isinstance(provenance, Mapping):
            component_matrix = attach_provenance_to_npz_metadata(
                component_matrix,
                provenance,
            )
        _write_npz_artifact(_resolve_path(args.component_matrix_out), component_matrix)
        print(f"Wrote component matrix artifact to {_resolve_path(args.component_matrix_out)}")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    frequency_db: Path | None,
    jmdict_path: Path | None,
    jmnedict_path: Path | None,
    kanjidic2_path: Path | None,
    kanjivg_path: Path | None,
    jlpt_vocabulary_path: Path | None,
    lesson_vocabulary_path: Path | None,
    top_n: int | None,
    calibration_json: Path,
    proficiency_levels: Sequence[float],
    window_size: int,
    example_limit: int,
    score_normalization: str = DEFAULT_SCORE_NORMALIZATION,
    target_band_weights: Sequence[float] = DEFAULT_TARGET_BAND_WEIGHTS,
    band_width: float = DEFAULT_BAND_WIDTH,
    variant_mode: str = "presets",
    calibration_only: bool = False,
    grid_signals: Sequence[str] = DEFAULT_GRID_SIGNALS,
    grid_step: float = 0.10,
    grid_caps: Sequence[float | None] = DEFAULT_GRID_CAPS,
    grid_min_weights: Mapping[str, float] | None = None,
    grid_max_weights: Mapping[str, float] | None = None,
    grid_center: Mapping[str, float] | None = None,
    grid_radius: float | None = None,
    jlpt_vocab_curves: Sequence[Mapping[int, float] | None] = (None,),
    jlpt_kanji_dampening_strengths: Sequence[float] = (0.0,),
    max_variants: int | None = None,
    leaderboard_limit: int = DEFAULT_LEADERBOARD_LIMIT,
    retain_variant_limit: int = DEFAULT_RETAIN_VARIANT_LIMIT,
    include_compact_trace: bool = False,
    include_calibration_matrix: bool = False,
    include_component_matrix: bool = False,
    component_matrix_components: str = "variant",
    tubelex_frequency_tsv: Path | None = None,
    use_default_tubelex_frequency: bool = True,
) -> dict[str, object]:
    if (include_calibration_matrix or include_component_matrix) and np is None:
        raise ValueError("NumPy is required for matrix artifacts.")
    if score_normalization not in SCORE_NORMALIZATIONS:
        raise ValueError(f"Unsupported score normalization: {score_normalization}")
    paths = build_helper_paths()
    resolved_frequency_db = _resolve_frequency_db(frequency_db, paths.frequency_packs_dir)
    resolved_tubelex_frequency_tsv = _resolve_tubelex_frequency_tsv(
        tubelex_frequency_tsv,
        paths.frequency_packs_dir,
        use_default=use_default_tubelex_frequency,
    )
    resolved_jmdict_path = _resolve_jmdict_path(jmdict_path, paths.language_packs_dir)
    resolved_jmnedict_path = _resolve_jmnedict_path(jmnedict_path, paths.language_packs_dir)
    resolved_kanjidic2_path = _resolve_kanjidic2_path(
        kanjidic2_path,
        paths.language_packs_dir,
    )
    resolved_kanjivg_path = _resolve_kanjivg_path(
        kanjivg_path,
        paths.language_packs_dir,
    )
    resolved_jlpt_vocabulary_path = _resolve_jlpt_vocabulary_path(
        jlpt_vocabulary_path,
        paths.language_packs_dir,
    )
    resolved_lesson_vocabulary_path = _resolve_lesson_vocabulary_path(
        lesson_vocabulary_path,
        paths.language_packs_dir,
    )
    stopwords_path = paths.srs_dir / "stopwords" / "stopwords-ja.json"
    seeds = build_seed_candidates(
        frequency_db=resolved_frequency_db,
        config=SeedSelectionConfig(
            language_pair=PAIR,
            top_n=top_n,
            require_jmdict=True,
            jmdict_path=resolved_jmdict_path,
            jmnedict_path=resolved_jmnedict_path,
            kanjidic2_path=resolved_kanjidic2_path,
            kanjivg_path=resolved_kanjivg_path,
            jlpt_vocabulary_path=resolved_jlpt_vocabulary_path,
            lesson_vocabulary_path=resolved_lesson_vocabulary_path,
            stopwords_path=stopwords_path if stopwords_path.exists() else None,
            source_label="freq-ja-bccwj",
        ),
    )
    tubelex_frequency_index = (
        load_tubelex_frequency_index(resolved_tubelex_frequency_tsv)
        if resolved_tubelex_frequency_tsv is not None
        else None
    )
    seed_rows = [
        _row_with_difficulty_components(
            _row_with_tubelex_frequency(_seed_row(seed), tubelex_frequency_index)
        )
        for seed in _dedupe_seeds(seeds)
    ]
    normalization_population_rows = _normalization_population_rows(seed_rows)
    base_calibration_rows = _build_calibration_rows(
        calibration_json=calibration_json,
        seed_rows=seed_rows,
    )
    variant_source = list(
        _iter_formula_variants(
            variant_mode=variant_mode,
            grid_signals=grid_signals,
            grid_step=grid_step,
            grid_caps=grid_caps,
            grid_min_weights=grid_min_weights,
            grid_max_weights=grid_max_weights,
            grid_center=grid_center,
            grid_radius=grid_radius,
            jlpt_vocab_curves=jlpt_vocab_curves,
            jlpt_kanji_dampening_strengths=jlpt_kanji_dampening_strengths,
            max_variants=max_variants,
        )
    )
    component_names = _matrix_component_names(
        variant_source,
        normalization_population_rows=normalization_population_rows,
        component_matrix_components=component_matrix_components,
    )
    target_curve_context = (
        _build_target_curve_scoring_context(
            normalization_population_rows,
            component_names=component_names,
            target_band_weights=target_band_weights,
            band_width=band_width,
        )
        if score_normalization == "target_curve"
        else None
    )
    component_matrix = (
        _component_matrix_payload(
            normalization_population_rows,
            component_names=component_names,
            target_band_weights=target_band_weights,
            band_width=band_width,
            target_curve_context=target_curve_context,
        )
        if include_component_matrix
        else None
    )
    sweep_summary: dict[str, object] | None = None
    compact_trace: dict[str, object] | None = None
    calibration_prediction_matrix: dict[str, object] | None = None
    if calibration_only:
        variants, sweep_summary, compact_trace, calibration_prediction_matrix = (
            _calibration_only_sweep(
                variants=variant_source,
                seed_rows=seed_rows,
                normalization_population_rows=normalization_population_rows,
                target_curve_context=target_curve_context,
                calibration_rows=base_calibration_rows,
                score_normalization=score_normalization,
                target_band_weights=target_band_weights,
                band_width=band_width,
                leaderboard_limit=leaderboard_limit,
                retain_variant_limit=retain_variant_limit,
                include_compact_trace=include_compact_trace,
                include_calibration_matrix=include_calibration_matrix,
            )
        )
    else:
        if include_compact_trace or include_calibration_matrix:
            raise ValueError("Trace outputs are currently supported only with --calibration-only.")
        variants = [
            _variant_report(
                variant,
                seed_rows=seed_rows,
                normalization_population_rows=normalization_population_rows,
                target_curve_context=target_curve_context,
                calibration_rows=base_calibration_rows,
                proficiency_levels=proficiency_levels,
                window_size=window_size,
                example_limit=example_limit,
                score_normalization=score_normalization,
                target_band_weights=target_band_weights,
                band_width=band_width,
            )
            for variant in variant_source
        ]
    report = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweep_summary": sweep_summary,
        "inputs": {
            "frequency_db": _repo_or_home_path(resolved_frequency_db),
            "jmdict": _repo_or_home_path(resolved_jmdict_path),
            "jmnedict": (
                _repo_or_home_path(resolved_jmnedict_path) if resolved_jmnedict_path else None
            ),
            "kanjidic2": (
                _repo_or_home_path(resolved_kanjidic2_path) if resolved_kanjidic2_path else None
            ),
            "kanjivg": (
                _repo_or_home_path(resolved_kanjivg_path) if resolved_kanjivg_path else None
            ),
            "jlpt_vocabulary": (
                _repo_or_home_path(resolved_jlpt_vocabulary_path)
                if resolved_jlpt_vocabulary_path
                else None
            ),
            "lesson_vocabulary": (
                _repo_or_home_path(resolved_lesson_vocabulary_path)
                if resolved_lesson_vocabulary_path
                else None
            ),
            "tubelex_frequency_tsv": (
                _repo_or_home_path(resolved_tubelex_frequency_tsv)
                if resolved_tubelex_frequency_tsv
                else None
            ),
            "tubelex_frequency_source": (
                {
                    "source_variant": tubelex_frequency_index.source_variant,
                    "row_count": tubelex_frequency_index.row_count,
                    "max_count": _rounded(tubelex_frequency_index.max_count),
                    "max_videos": _rounded(tubelex_frequency_index.max_videos),
                    "max_channels": _rounded(tubelex_frequency_index.max_channels),
                }
                if tubelex_frequency_index is not None
                else None
            ),
            "calibration_json": _repo_or_home_path(calibration_json),
            "candidate_frontier": "limited" if top_n is not None else "all",
            "top_n": top_n,
            "seed_count": len(seed_rows),
            "normalization_population": (
                "deduped_display_vocab_rows" if score_normalization == "target_curve" else None
            ),
            "normalization_population_count": (
                len(normalization_population_rows)
                if score_normalization == "target_curve"
                else None
            ),
            "normalization_candidate_states": (
                sorted(VOCAB_STATES) if score_normalization == "target_curve" else []
            ),
            "window_size": int(window_size),
            "proficiency_levels": [round(float(value), 4) for value in proficiency_levels],
            "score_normalization": score_normalization,
            "normalization_curve_id": (
                TARGET_CURVE_ID if score_normalization == "target_curve" else None
            ),
            "target_band_weights": [round(float(value), 8) for value in target_band_weights],
            "band_width": band_width,
            "variant_mode": variant_mode,
            "calibration_only": calibration_only,
            "grid_signals": list(grid_signals),
            "grid_step": grid_step,
            "grid_caps": [None if value is None else round(float(value), 6) for value in grid_caps],
            "grid_min_weights": dict(grid_min_weights or {}),
            "grid_max_weights": dict(grid_max_weights or {}),
            "grid_center": dict(grid_center or {}),
            "grid_radius": grid_radius,
            "jlpt_vocab_curves": [_jlpt_curve_json(curve) for curve in jlpt_vocab_curves],
            "jlpt_kanji_dampening_strengths": [
                round(float(value), 6) for value in jlpt_kanji_dampening_strengths
            ],
            "max_variants": max_variants,
            "variant_count": len(variant_source),
            "component_matrix_components": component_matrix_components,
            "leaderboard_limit": leaderboard_limit,
            "retain_variant_limit": retain_variant_limit,
        },
        "signal_coverage": _signal_coverage(seed_rows),
        "formula_variants": variants,
    }
    if compact_trace is not None:
        report["_compact_trace"] = compact_trace
    if calibration_prediction_matrix is not None:
        report["_calibration_prediction_matrix"] = calibration_prediction_matrix
    if component_matrix is not None:
        report["_component_matrix"] = component_matrix
    report["provenance"] = build_artifact_provenance(
        producer_script=Path(__file__),
        input_paths={
            "frequency_db": resolved_frequency_db,
            "jmdict": resolved_jmdict_path,
            "jmnedict": resolved_jmnedict_path,
            "kanjidic2": resolved_kanjidic2_path,
            "kanjivg": resolved_kanjivg_path,
            "jlpt_vocabulary": resolved_jlpt_vocabulary_path,
            "lesson_vocabulary": resolved_lesson_vocabulary_path,
            "tubelex_frequency": resolved_tubelex_frequency_tsv,
            "calibration_json": calibration_json,
            "stopwords": stopwords_path if stopwords_path.exists() else None,
        },
        code_paths=_srs_difficulty_code_paths(),
        version_constants={
            "candidate_classification": CANDIDATE_CLASSIFICATION_VERSION,
            "japanese_learner_signals": JAPANESE_LEARNER_SIGNALS_VERSION,
            "jmdict_lexical_index": JMDICT_LEXICAL_INDEX_VERSION,
            "ja_acronym_signal": JA_ACRONYM_SIGNAL_VERSION,
            "target_curve": TARGET_CURVE_ID,
            "tubelex_frequency_signal": TUBELEX_SIGNAL_VERSION,
        },
        argv=sys.argv,
    )
    return report


def _iter_formula_variants(
    *,
    variant_mode: str,
    grid_signals: Sequence[str],
    grid_step: float,
    grid_caps: Sequence[float | None],
    grid_min_weights: Mapping[str, float] | None,
    grid_max_weights: Mapping[str, float] | None,
    grid_center: Mapping[str, float] | None,
    grid_radius: float | None,
    jlpt_vocab_curves: Sequence[Mapping[int, float] | None],
    jlpt_kanji_dampening_strengths: Sequence[float],
    max_variants: int | None,
) -> Iterable[FormulaVariant]:
    emitted = 0
    if variant_mode == "presets":
        base_variants: Iterable[FormulaVariant] = FORMULA_VARIANTS
    elif variant_mode == "grid":
        base_variants = _iter_grid_variants(
            signals=grid_signals,
            step=grid_step,
            caps=grid_caps,
            min_weights=grid_min_weights,
            max_weights=grid_max_weights,
            center=grid_center,
            radius=grid_radius,
            max_variants=None,
        )
    else:
        raise ValueError(f"Unsupported variant mode: {variant_mode}")
    for variant in base_variants:
        for expanded in _expand_formula_variant_jlpt_transforms(
            variant,
            jlpt_vocab_curves=jlpt_vocab_curves,
            jlpt_kanji_dampening_strengths=jlpt_kanji_dampening_strengths,
        ):
            if max_variants is not None and emitted >= max_variants:
                return
            yield expanded
            emitted += 1


def _expand_formula_variant_jlpt_transforms(
    variant: FormulaVariant,
    *,
    jlpt_vocab_curves: Sequence[Mapping[int, float] | None],
    jlpt_kanji_dampening_strengths: Sequence[float],
) -> Iterable[FormulaVariant]:
    if variant.use_current_value:
        yield variant
        return
    curves = tuple(jlpt_vocab_curves) or (None,)
    strengths = tuple(jlpt_kanji_dampening_strengths) or (0.0,)
    for curve in curves:
        normalized_curve = _normalized_jlpt_vocab_curve(curve) if curve else None
        for strength in strengths:
            normalized_strength = _clamp01(float(strength))
            if normalized_curve is None and normalized_strength <= 0.0:
                yield variant
                continue
            suffix_parts: list[str] = []
            description_parts: list[str] = [variant.description]
            if normalized_curve is not None:
                suffix_parts.append(f"jlpt{_jlpt_curve_id(normalized_curve)}")
                description_parts.append(
                    f"JLPT vocab curve override {_jlpt_curve_json(normalized_curve)}"
                )
            if normalized_strength > 0.0:
                suffix_parts.append(f"kd{int(round(normalized_strength * 100)):03d}")
                description_parts.append(
                    f"JLPT-backed kanji dampening strength {normalized_strength:g}"
                )
            yield FormulaVariant(
                variant_id=f"{variant.variant_id}__{'__'.join(suffix_parts)}",
                description="; ".join(description_parts),
                weights=dict(variant.weights),
                use_current_value=variant.use_current_value,
                max_shift_from_frequency=variant.max_shift_from_frequency,
                piecewise_sections=variant.piecewise_sections,
                jlpt_vocab_curve=normalized_curve,
                jlpt_kanji_dampening_strength=normalized_strength,
            )


def _iter_grid_variants(
    *,
    signals: Sequence[str],
    step: float,
    caps: Sequence[float | None],
    min_weights: Mapping[str, float] | None = None,
    max_weights: Mapping[str, float] | None = None,
    center: Mapping[str, float] | None = None,
    radius: float | None = None,
    max_variants: int | None = None,
) -> Iterable[FormulaVariant]:
    if not signals:
        raise ValueError("Grid mode requires at least one signal.")
    if step <= 0.0 or step > 1.0:
        raise ValueError("--grid-step must be greater than 0 and at most 1.")
    units = round(1.0 / step)
    if not math.isclose(units * step, 1.0, abs_tol=1e-9):
        raise ValueError("--grid-step must divide 1.0 exactly enough for a normalized grid.")
    emitted = 0
    for cap in caps:
        for vector in _integer_weight_vectors(len(signals), units):
            weights = {
                signal: round(unit / units, 6) for signal, unit in zip(signals, vector) if unit > 0
            }
            if not _within_grid_weight_bounds(
                weights,
                signals=signals,
                min_weights=min_weights,
                max_weights=max_weights,
            ):
                continue
            if not _within_grid_neighborhood(
                weights,
                signals=signals,
                center=center,
                radius=radius,
            ):
                continue
            if max_variants is not None and emitted >= max_variants:
                return
            cap_label = "none" if cap is None else f"{int(round(cap * 1000)):03d}"
            variant_id = f"grid_s{units:02d}_c{cap_label}_{emitted + 1:06d}"
            yield FormulaVariant(
                variant_id=variant_id,
                description=(
                    f"Generated grid formula with step={step:g}, cap={cap}, "
                    f"signals={','.join(signals)}."
                ),
                weights=weights,
                max_shift_from_frequency=cap,
            )
            emitted += 1


def _within_grid_weight_bounds(
    weights: Mapping[str, float],
    *,
    signals: Sequence[str],
    min_weights: Mapping[str, float] | None,
    max_weights: Mapping[str, float] | None,
) -> bool:
    for signal in signals:
        value = float(weights.get(signal, 0.0))
        minimum = None if min_weights is None else min_weights.get(signal)
        maximum = None if max_weights is None else max_weights.get(signal)
        if minimum is not None and value < float(minimum) - 1e-9:
            return False
        if maximum is not None and value > float(maximum) + 1e-9:
            return False
    return True


def _within_grid_neighborhood(
    weights: Mapping[str, float],
    *,
    signals: Sequence[str],
    center: Mapping[str, float] | None,
    radius: float | None,
) -> bool:
    if not center:
        return True
    if radius is None:
        return True
    for signal in signals:
        if abs(float(weights.get(signal, 0.0)) - float(center.get(signal, 0.0))) > radius:
            return False
    return True


def _integer_weight_vectors(length: int, total_units: int) -> Iterable[tuple[int, ...]]:
    if length <= 0:
        return
    if length == 1:
        yield (total_units,)
        return
    for head in range(total_units + 1):
        for tail in _integer_weight_vectors(length - 1, total_units - head):
            yield (head, *tail)


def _calibration_only_sweep(
    *,
    variants: Sequence[FormulaVariant],
    seed_rows: Sequence[Mapping[str, object]],
    normalization_population_rows: Sequence[Mapping[str, object]],
    target_curve_context: TargetCurveScoringContext | None,
    calibration_rows: Sequence[Mapping[str, object]],
    score_normalization: str,
    target_band_weights: Sequence[float],
    band_width: float,
    leaderboard_limit: int,
    retain_variant_limit: int,
    include_compact_trace: bool,
    include_calibration_matrix: bool,
) -> tuple[
    list[dict[str, object]],
    dict[str, object],
    dict[str, object] | None,
    dict[str, object] | None,
]:
    seed_by_identity = {
        str(row.get("candidate_identity_key") or ""): row
        for row in seed_rows
        if row.get("candidate_identity_key")
    }
    records: list[dict[str, object]] = []
    matrix_values = None
    if include_calibration_matrix:
        if np is None:
            raise ValueError("NumPy is required for --trace-calibration-matrix-out.")
        matrix_values = np.full(  # type: ignore[union-attr]
            (len(variants), len(calibration_rows)),
            np.nan,  # type: ignore[union-attr]
            dtype=np.float32,  # type: ignore[union-attr]
        )
    for variant_index, variant in enumerate(variants):
        if matrix_values is None:
            record = _calibration_only_score_record(
                variant,
                seed_by_identity=seed_by_identity,
                normalization_population_rows=normalization_population_rows,
                target_curve_context=target_curve_context,
                calibration_rows=calibration_rows,
                score_normalization=score_normalization,
                target_band_weights=target_band_weights,
                band_width=band_width,
            )
        else:
            metrics, success_metrics, variant_calibration_rows = _variant_calibration_metrics(
                variant,
                seed_by_identity=seed_by_identity,
                normalization_population_rows=normalization_population_rows,
                target_curve_context=target_curve_context,
                calibration_rows=calibration_rows,
                score_normalization=score_normalization,
                target_band_weights=target_band_weights,
                band_width=band_width,
                include_rows=True,
            )
            record = _calibration_only_score_record_from_metrics(
                variant,
                metrics=metrics,
                success_metrics=success_metrics,
            )
            for calibration_index, row in enumerate(variant_calibration_rows):
                value = _optional_float(row.get("observed_current_difficulty_proxy"))
                if value is not None:
                    matrix_values[variant_index, calibration_index] = value
        records.append(record)
    leaderboards = _score_leaderboards(records, limit=leaderboard_limit)
    retained_ids = _retained_variant_ids(
        leaderboards,
        records=records,
        retain_variant_limit=retain_variant_limit,
    )
    variant_by_id = {variant.variant_id: variant for variant in variants}
    retained_reports = [
        _calibration_only_variant_report(
            variant_by_id[variant_id],
            seed_by_identity=seed_by_identity,
            normalization_population_rows=normalization_population_rows,
            target_curve_context=target_curve_context,
            calibration_rows=calibration_rows,
            score_normalization=score_normalization,
            target_band_weights=target_band_weights,
            band_width=band_width,
        )
        for variant_id in retained_ids
        if variant_id in variant_by_id
    ]
    sweep_summary = {
        "mode": "calibration_only",
        "score_normalization": score_normalization,
        "normalization_curve_id": (
            TARGET_CURVE_ID if score_normalization == "target_curve" else None
        ),
        "normalization_population": (
            "deduped_display_vocab_rows" if score_normalization == "target_curve" else None
        ),
        "normalization_population_count": (
            len(normalization_population_rows) if score_normalization == "target_curve" else None
        ),
        "evaluated_variant_count": len(records),
        "retained_variant_count": len(retained_reports),
        "leaderboard_limit": leaderboard_limit,
        "retain_variant_limit": retain_variant_limit,
        "score_keys": list(SWEEP_SCORE_KEYS),
        "leaderboards": leaderboards,
    }
    compact_trace = (
        _compact_trace_payload(
            records=records,
            calibration_rows=calibration_rows,
            score_normalization=score_normalization,
            target_band_weights=target_band_weights,
            band_width=band_width,
            normalization_population_count=(
                len(normalization_population_rows)
                if score_normalization == "target_curve"
                else None
            ),
        )
        if include_compact_trace
        else None
    )
    calibration_matrix = (
        _calibration_matrix_payload(
            records=records,
            calibration_rows=calibration_rows,
            matrix_values=matrix_values,
            score_normalization=score_normalization,
            target_band_weights=target_band_weights,
            band_width=band_width,
            normalization_population_count=(
                len(normalization_population_rows)
                if score_normalization == "target_curve"
                else None
            ),
        )
        if matrix_values is not None
        else None
    )
    return retained_reports, sweep_summary, compact_trace, calibration_matrix


def _calibration_only_score_record(
    variant: FormulaVariant,
    *,
    seed_by_identity: Mapping[str, Mapping[str, object]],
    normalization_population_rows: Sequence[Mapping[str, object]],
    target_curve_context: TargetCurveScoringContext | None,
    calibration_rows: Sequence[Mapping[str, object]],
    score_normalization: str,
    target_band_weights: Sequence[float],
    band_width: float,
) -> dict[str, object]:
    metrics, success_metrics = _variant_calibration_metrics(
        variant,
        seed_by_identity=seed_by_identity,
        normalization_population_rows=normalization_population_rows,
        target_curve_context=target_curve_context,
        calibration_rows=calibration_rows,
        score_normalization=score_normalization,
        target_band_weights=target_band_weights,
        band_width=band_width,
    )
    return _calibration_only_score_record_from_metrics(
        variant,
        metrics=metrics,
        success_metrics=success_metrics,
    )


def _calibration_only_score_record_from_metrics(
    variant: FormulaVariant,
    *,
    metrics: Mapping[str, object],
    success_metrics: Mapping[str, object],
) -> dict[str, object]:
    difficulty = _mapping(metrics.get("difficulty_bucket"))
    difficulty_value = _mapping(metrics.get("difficulty_value"))
    scores = _mapping(success_metrics.get("scores"))
    pairwise = _mapping(success_metrics.get("pairwise_order"))
    rank_correlation = _mapping(success_metrics.get("rank_correlation"))
    return {
        "variant_id": variant.variant_id,
        "weights": dict(variant.weights),
        "piecewise_sections": _piecewise_sections_json(variant),
        "max_shift_from_frequency": variant.max_shift_from_frequency,
        "transforms": _variant_transform_json(variant),
        "scores": dict(scores),
        "difficulty": {
            "mae": difficulty_value.get("mae"),
            "rmse": difficulty_value.get("rmse"),
            "bucket_accuracy": difficulty.get("accuracy"),
            "mismatch_count": difficulty.get("mismatch_count"),
        },
        "pairwise_order": {
            "accuracy": pairwise.get("accuracy"),
            "strict_accuracy": pairwise.get("strict_accuracy"),
            "wrong_count": pairwise.get("wrong_count"),
            "comparable_count": pairwise.get("comparable_count"),
        },
        "rank_correlation": {
            "spearman": rank_correlation.get("spearman"),
            "pearson": rank_correlation.get("pearson"),
        },
    }


def _calibration_only_variant_report(
    variant: FormulaVariant,
    *,
    seed_by_identity: Mapping[str, Mapping[str, object]],
    normalization_population_rows: Sequence[Mapping[str, object]],
    target_curve_context: TargetCurveScoringContext | None,
    calibration_rows: Sequence[Mapping[str, object]],
    score_normalization: str,
    target_band_weights: Sequence[float],
    band_width: float,
) -> dict[str, object]:
    metrics, success_metrics, variant_calibration_rows = _variant_calibration_metrics(
        variant,
        seed_by_identity=seed_by_identity,
        normalization_population_rows=normalization_population_rows,
        target_curve_context=target_curve_context,
        calibration_rows=calibration_rows,
        score_normalization=score_normalization,
        target_band_weights=target_band_weights,
        band_width=band_width,
        include_rows=True,
    )
    return {
        "variant_id": variant.variant_id,
        "description": variant.description,
        "weights": dict(variant.weights),
        "piecewise_sections": _piecewise_sections_json(variant),
        "max_shift_from_frequency": variant.max_shift_from_frequency,
        "transforms": _variant_transform_json(variant),
        "calibration": {
            "metrics": metrics,
            "success_metrics": success_metrics,
            "difficulty_mismatches": [
                row
                for row in variant_calibration_rows
                if row.get("difficulty_status") == "mismatch"
            ],
        },
        "frontier": None,
        "proficiency_windows": [],
    }


def _variant_calibration_metrics(
    variant: FormulaVariant,
    *,
    seed_by_identity: Mapping[str, Mapping[str, object]],
    normalization_population_rows: Sequence[Mapping[str, object]],
    target_curve_context: TargetCurveScoringContext | None,
    calibration_rows: Sequence[Mapping[str, object]],
    score_normalization: str,
    target_band_weights: Sequence[float],
    band_width: float,
    include_rows: bool = False,
) -> (
    tuple[dict[str, object], dict[str, object]]
    | tuple[
        dict[str, object],
        dict[str, object],
        list[dict[str, object]],
    ]
):
    identities = tuple(
        identity
        for row in calibration_rows
        for identity in [str(row.get("candidate_identity_key") or "")]
        if identity and seed_by_identity.get(identity) is not None
    )
    values_by_identity = _variant_values_by_identity(
        variant,
        seed_by_identity=seed_by_identity,
        identities=identities,
        normalization_population_rows=normalization_population_rows,
        target_curve_context=target_curve_context,
        score_normalization=score_normalization,
        target_band_weights=target_band_weights,
        band_width=band_width,
    )
    variant_calibration_rows = [
        _calibration_row_for_variant(row, values_by_identity) for row in calibration_rows
    ]
    metrics = _calibration_metrics(variant_calibration_rows)
    success_metrics = _success_metrics_for_calibration(
        variant_calibration_rows,
        calibration_metrics=metrics,
    )
    if include_rows:
        return metrics, success_metrics, variant_calibration_rows
    return metrics, success_metrics


def _score_leaderboards(
    records: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> dict[str, list[dict[str, object]]]:
    leaderboards: dict[str, list[dict[str, object]]] = {}
    for score_key in SWEEP_SCORE_KEYS:
        ranked = sorted(
            records,
            key=lambda record: (
                _optional_float(_mapping(record.get("scores")).get(score_key))
                if _optional_float(_mapping(record.get("scores")).get(score_key)) is not None
                else -1.0
            ),
            reverse=True,
        )
        leaderboards[score_key] = [
            _leaderboard_record(record, score_key=score_key) for record in ranked[:limit]
        ]
    return leaderboards


def _leaderboard_record(
    record: Mapping[str, object],
    *,
    score_key: str,
) -> dict[str, object]:
    scores = _mapping(record.get("scores"))
    difficulty = _mapping(record.get("difficulty"))
    pairwise = _mapping(record.get("pairwise_order"))
    rank_correlation = _mapping(record.get("rank_correlation"))
    return {
        "variant_id": record.get("variant_id"),
        "score_key": score_key,
        "score": scores.get(score_key),
        "balanced_score": scores.get("balanced_score"),
        "numeric_mae_score": scores.get("numeric_mae_score"),
        "mae": difficulty.get("mae"),
        "bucket_accuracy": difficulty.get("bucket_accuracy"),
        "pairwise_order_score": scores.get("pairwise_order_score"),
        "pairwise_wrong_count": pairwise.get("wrong_count"),
        "spearman": rank_correlation.get("spearman"),
        "beginner_core_score": scores.get("beginner_core_score"),
        "high_tail_score": scores.get("high_tail_score"),
        "max_shift_from_frequency": record.get("max_shift_from_frequency"),
        "transforms": record.get("transforms"),
        "weights": record.get("weights"),
        "piecewise_sections": record.get("piecewise_sections"),
    }


def _piecewise_sections_json(variant: FormulaVariant) -> list[dict[str, object]]:
    return [
        {
            "section_id": section.section_id,
            "center": _rounded(section.center),
            "radius": _rounded(section.radius),
            "weights": dict(section.weights),
            "max_shift_from_frequency": _rounded(section.max_shift_from_frequency),
        }
        for section in variant.piecewise_sections
    ]


def _variant_transform_json(variant: FormulaVariant) -> dict[str, object]:
    transforms: dict[str, object] = {}
    jlpt_curve = _jlpt_curve_json(variant.jlpt_vocab_curve)
    if jlpt_curve is not None:
        transforms["jlpt_vocab_curve"] = jlpt_curve
    dampening = _clamp01(float(variant.jlpt_kanji_dampening_strength))
    if dampening > 0.0:
        transforms["jlpt_kanji_dampening_strength"] = round(dampening, 6)
        transforms["jlpt_kanji_dampened_components"] = sorted(JLPT_DAMPENED_KANJI_COMPONENTS)
    return transforms


def _retained_variant_ids(
    leaderboards: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    records: Sequence[Mapping[str, object]],
    retain_variant_limit: int,
) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    for score_key in SWEEP_SCORE_KEYS:
        for row in leaderboards.get(score_key, ()):
            variant_id = str(row.get("variant_id") or "")
            if variant_id and variant_id not in seen:
                seen.add(variant_id)
                selected.append(variant_id)
                if len(selected) >= retain_variant_limit:
                    return selected
    if len(selected) >= retain_variant_limit:
        return selected
    records_by_id = {
        str(record.get("variant_id") or ""): record
        for record in records
        if record.get("variant_id")
    }
    balanced = sorted(
        records_by_id,
        key=lambda variant_id: (
            _optional_float(_mapping(records_by_id[variant_id].get("scores")).get("balanced_score"))
            or -1.0
        ),
        reverse=True,
    )
    for variant_id in balanced:
        if variant_id not in seen:
            selected.append(variant_id)
            seen.add(variant_id)
            if len(selected) >= retain_variant_limit:
                break
    return selected


def _variant_report(
    variant: FormulaVariant,
    *,
    seed_rows: Sequence[Mapping[str, object]],
    normalization_population_rows: Sequence[Mapping[str, object]],
    target_curve_context: TargetCurveScoringContext | None,
    calibration_rows: Sequence[Mapping[str, object]],
    proficiency_levels: Sequence[float],
    window_size: int,
    example_limit: int,
    score_normalization: str,
    target_band_weights: Sequence[float],
    band_width: float,
) -> dict[str, object]:
    seed_by_identity = {
        str(row.get("candidate_identity_key") or ""): row
        for row in seed_rows
        if row.get("candidate_identity_key")
    }
    values_by_identity = _variant_values_by_identity(
        variant,
        seed_by_identity=seed_by_identity,
        identities=tuple(seed_by_identity),
        normalization_population_rows=normalization_population_rows,
        target_curve_context=target_curve_context,
        score_normalization=score_normalization,
        target_band_weights=target_band_weights,
        band_width=band_width,
    )
    scored_rows = [
        {**dict(row), "variant_difficulty": values_by_identity[str(row["candidate_identity_key"])]}
        for row in seed_rows
        if str(row.get("candidate_identity_key") or "") in values_by_identity
    ]
    variant_calibration_rows = [
        _calibration_row_for_variant(row, values_by_identity) for row in calibration_rows
    ]
    metrics = _calibration_metrics(variant_calibration_rows)
    success_metrics = _success_metrics_for_calibration(
        variant_calibration_rows,
        calibration_metrics=metrics,
    )
    return {
        "variant_id": variant.variant_id,
        "description": variant.description,
        "weights": dict(variant.weights),
        "piecewise_sections": _piecewise_sections_json(variant),
        "max_shift_from_frequency": variant.max_shift_from_frequency,
        "transforms": _variant_transform_json(variant),
        "score_normalization": score_normalization,
        "calibration": {
            "metrics": metrics,
            "success_metrics": success_metrics,
            "difficulty_mismatches": [
                row
                for row in variant_calibration_rows
                if row.get("difficulty_status") == "mismatch"
            ],
        },
        "frontier": _frontier_formula_summary(scored_rows),
        "proficiency_windows": [
            _proficiency_window(
                scored_rows,
                proficiency=float(proficiency),
                window_size=window_size,
                example_limit=example_limit,
            )
            for proficiency in proficiency_levels
        ],
    }


def _variant_values_by_identity(
    variant: FormulaVariant,
    *,
    seed_by_identity: Mapping[str, Mapping[str, object]],
    identities: Sequence[str],
    normalization_population_rows: Sequence[Mapping[str, object]],
    target_curve_context: TargetCurveScoringContext | None,
    score_normalization: str,
    target_band_weights: Sequence[float],
    band_width: float,
) -> dict[str, float]:
    if score_normalization == "raw":
        return {
            identity: estimate_variant_difficulty(seed_row, variant)
            for identity in identities
            for seed_row in [seed_by_identity.get(identity)]
            if identity and seed_row is not None
        }
    if score_normalization != "target_curve":
        raise ValueError(f"Unsupported score normalization: {score_normalization}")
    if target_curve_context is not None:
        normalized_values = _target_curve_values_for_variant(variant, target_curve_context)
        values: dict[str, float] = {}
        for identity in identities:
            seed_row = seed_by_identity.get(identity)
            if seed_row is None:
                continue
            if _is_vocab_row(seed_row):
                index = target_curve_context.dedupe_to_index.get(
                    _normalization_dedupe_value(seed_row)
                )
                if index is not None:
                    values[identity] = float(normalized_values[index])
                    continue
            values[identity] = estimate_variant_difficulty(seed_row, variant)
        return values
    normalized_by_dedupe = _target_curve_values_by_dedupe(
        variant,
        normalization_population_rows=normalization_population_rows,
        target_band_weights=target_band_weights,
        band_width=band_width,
    )
    values: dict[str, float] = {}
    for identity in identities:
        seed_row = seed_by_identity.get(identity)
        if seed_row is None:
            continue
        if _is_vocab_row(seed_row):
            normalized = normalized_by_dedupe.get(_normalization_dedupe_value(seed_row))
            if normalized is not None:
                values[identity] = normalized
                continue
        values[identity] = estimate_variant_difficulty(seed_row, variant)
    return values


def _build_target_curve_scoring_context(
    normalization_population_rows: Sequence[Mapping[str, object]],
    *,
    component_names: Sequence[str],
    target_band_weights: Sequence[float],
    band_width: float,
) -> TargetCurveScoringContext | None:
    if np is None or not normalization_population_rows:
        return None
    names = _component_context_names(normalization_population_rows, component_names)
    component_values = np.zeros((len(normalization_population_rows), len(names)), dtype=float)
    component_present = np.zeros((len(normalization_population_rows), len(names)), dtype=bool)
    current_values = np.zeros(len(normalization_population_rows), dtype=float)
    frequency_values = np.full(len(normalization_population_rows), np.nan, dtype=float)
    jlpt_vocab_levels = np.full(len(normalization_population_rows), np.nan, dtype=float)
    dedupe_values: list[str] = []
    for row_index, row in enumerate(normalization_population_rows):
        components = _difficulty_components_for_row(row)
        for component_index, name in enumerate(names):
            value = _optional_float(components.get(name))
            if value is None:
                continue
            component_values[row_index, component_index] = value
            component_present[row_index, component_index] = True
            if name == "frequency":
                frequency_values[row_index] = value
        current_values[row_index] = _optional_float(row.get("current_difficulty_proxy")) or 0.0
        jlpt_level = _jlpt_vocab_easiest_level(row)
        if jlpt_level is not None:
            jlpt_vocab_levels[row_index] = float(jlpt_level)
        dedupe_values.append(_normalization_dedupe_value(row))
    return TargetCurveScoringContext(
        component_names=names,
        component_values=component_values,
        component_present=component_present,
        current_values=current_values,
        frequency_values=frequency_values,
        jlpt_vocab_levels=jlpt_vocab_levels,
        dedupe_values=tuple(dedupe_values),
        dedupe_to_index={value: index for index, value in enumerate(dedupe_values)},
        normalized_positions=_target_curve_positions(
            total_count=len(normalization_population_rows),
            target_band_weights=target_band_weights,
            band_width=band_width,
        ),
    )


def _component_context_names(
    rows: Sequence[Mapping[str, object]],
    component_names: Sequence[str],
) -> tuple[str, ...]:
    names = set(component_names) | {"frequency"}
    for row in rows:
        for name, value in _difficulty_components_for_row(row).items():
            if _optional_float(value) is not None:
                names.add(str(name))
    return tuple(sorted(names))


def _target_curve_values_for_variant(
    variant: FormulaVariant,
    context: TargetCurveScoringContext,
) -> object:
    raw_scores = _target_curve_raw_scores_for_variant(variant, context)
    order = np.argsort(raw_scores, kind="stable")  # type: ignore[union-attr]
    normalized = np.empty_like(raw_scores)  # type: ignore[union-attr]
    normalized[order] = context.normalized_positions
    return normalized


def _target_curve_raw_scores_for_variant(
    variant: FormulaVariant,
    context: TargetCurveScoringContext,
) -> object:
    if variant.use_current_value:
        return np.clip(context.current_values, 0.0, 1.0)  # type: ignore[union-attr]
    if variant.piecewise_sections:
        return _target_curve_raw_scores_for_piecewise_variant(variant, context)
    return _target_curve_raw_scores_for_weights(
        weights=variant.weights,
        max_shift_from_frequency=variant.max_shift_from_frequency,
        context=context,
        variant=variant,
    )


def _target_curve_raw_scores_for_piecewise_variant(
    variant: FormulaVariant,
    context: TargetCurveScoringContext,
) -> object:
    frequency = np.nan_to_num(context.frequency_values, nan=0.0)  # type: ignore[union-attr]
    section_scores = []
    section_influences = []
    for section in variant.piecewise_sections:
        section_scores.append(
            _target_curve_raw_scores_for_weights(
                weights=section.weights,
                max_shift_from_frequency=section.max_shift_from_frequency,
                context=context,
                variant=variant,
            )
        )
        radius = max(1e-9, float(section.radius))
        section_influences.append(
            np.maximum(  # type: ignore[union-attr]
                0.0,
                1.0 - (np.abs(frequency - float(section.center)) / radius),  # type: ignore[union-attr]
            )
        )
    scores = np.stack(section_scores, axis=1)  # type: ignore[union-attr]
    influences = np.stack(section_influences, axis=1)  # type: ignore[union-attr]
    influence_sum = influences.sum(axis=1)
    if bool((influence_sum <= 0.0).any()):
        centers = np.array([float(section.center) for section in variant.piecewise_sections])  # type: ignore[union-attr]
        nearest = np.argmin(np.abs(frequency[:, None] - centers[None, :]), axis=1)  # type: ignore[union-attr]
        fallback_influences = np.zeros_like(influences)  # type: ignore[union-attr]
        fallback_influences[np.arange(len(frequency)), nearest] = 1.0  # type: ignore[union-attr]
        influences = np.where(influence_sum[:, None] > 0.0, influences, fallback_influences)  # type: ignore[union-attr]
        influence_sum = influences.sum(axis=1)
    raw = (scores * influences).sum(axis=1) / influence_sum
    if variant.max_shift_from_frequency is not None:
        max_shift = max(0.0, float(variant.max_shift_from_frequency))
        capped = np.minimum(
            context.frequency_values + max_shift,
            np.maximum(context.frequency_values - max_shift, raw),
        )  # type: ignore[union-attr]
        raw = np.where(np.isnan(context.frequency_values), raw, capped)  # type: ignore[union-attr]
    return np.clip(raw, 0.0, 1.0)  # type: ignore[union-attr]


def _target_curve_raw_scores_for_weights(
    *,
    weights: Mapping[str, float],
    max_shift_from_frequency: float | None,
    context: TargetCurveScoringContext,
    variant: FormulaVariant,
) -> object:
    weights = np.array(  # type: ignore[union-attr]
        [max(0.0, float(weights.get(name, 0.0))) for name in context.component_names],
        dtype=float,
    )
    active = weights > 0.0
    if not bool(active.any()):
        fallback = np.nan_to_num(context.frequency_values, nan=0.0)  # type: ignore[union-attr]
        return np.clip(fallback, 0.0, 1.0)  # type: ignore[union-attr]
    active_weights = weights[active]
    component_values, component_present = _variant_component_arrays(context, variant)
    values = component_values[:, active]
    present = component_present[:, active]
    numerator = (values * present * active_weights).sum(axis=1)
    denominator = (present * active_weights).sum(axis=1)
    fallback = np.nan_to_num(context.frequency_values, nan=0.0)  # type: ignore[union-attr]
    raw = fallback.copy()
    np.divide(numerator, denominator, out=raw, where=denominator > 0.0)  # type: ignore[union-attr]
    if max_shift_from_frequency is not None:
        max_shift = max(0.0, float(max_shift_from_frequency))
        frequency = context.frequency_values
        capped = np.minimum(frequency + max_shift, np.maximum(frequency - max_shift, raw))  # type: ignore[union-attr]
        raw = np.where(np.isnan(frequency), raw, capped)  # type: ignore[union-attr]
    return np.clip(raw, 0.0, 1.0)  # type: ignore[union-attr]


def _variant_component_arrays(
    context: TargetCurveScoringContext,
    variant: FormulaVariant,
) -> tuple[object, object]:
    if not _variant_has_component_transforms(variant):
        return context.component_values, context.component_present
    values = context.component_values.copy()  # type: ignore[union-attr]
    present = context.component_present.copy()  # type: ignore[union-attr]
    name_to_index = {name: index for index, name in enumerate(context.component_names)}
    anchor = _jlpt_vocab_anchor_array(context, variant)
    anchor_present = ~np.isnan(anchor)  # type: ignore[union-attr]
    jlpt_index = name_to_index.get("jlpt_vocab_difficulty")
    if jlpt_index is not None and variant.jlpt_vocab_curve is not None:
        values[:, jlpt_index] = np.nan_to_num(anchor, nan=0.0)  # type: ignore[index,union-attr]
        present[:, jlpt_index] = anchor_present  # type: ignore[index]
    strength = _clamp01(float(variant.jlpt_kanji_dampening_strength))
    if strength <= 0.0:
        return values, present
    for name in JLPT_DAMPENED_KANJI_COMPONENTS:
        index = name_to_index.get(name)
        if index is None:
            continue
        component_present = present[:, index] & anchor_present  # type: ignore[index]
        if not bool(component_present.any()):
            continue
        original = values[:, index]  # type: ignore[index]
        capped = original - (strength * np.maximum(0.0, original - anchor))  # type: ignore[operator,union-attr]
        values[:, index] = np.where(component_present, capped, original)  # type: ignore[index,union-attr]
    return values, present


def _jlpt_vocab_anchor_array(
    context: TargetCurveScoringContext,
    variant: FormulaVariant,
) -> object:
    if variant.jlpt_vocab_curve is None:
        index = (
            context.component_names.index("jlpt_vocab_difficulty")
            if "jlpt_vocab_difficulty" in context.component_names
            else None
        )
        if index is None:
            return np.full(len(context.jlpt_vocab_levels), np.nan, dtype=float)  # type: ignore[arg-type,union-attr]
        values = context.component_values[:, index].copy()  # type: ignore[index,union-attr]
        present = context.component_present[:, index]  # type: ignore[index]
        return np.where(present, values, np.nan)  # type: ignore[union-attr]
    anchor = np.full(len(context.jlpt_vocab_levels), np.nan, dtype=float)  # type: ignore[arg-type,union-attr]
    for level, value in _normalized_jlpt_vocab_curve(variant.jlpt_vocab_curve).items():
        anchor = np.where(  # type: ignore[assignment,union-attr]
            context.jlpt_vocab_levels == float(level),
            float(value),
            anchor,
        )
    return anchor


def _target_curve_positions(
    *,
    total_count: int,
    target_band_weights: Sequence[float],
    band_width: float,
) -> object:
    bands = difficulty_bands(band_width)
    counts = target_band_counts(total_count, target_band_weights)
    positions = np.empty(total_count, dtype=float)  # type: ignore[union-attr]
    cursor = 0
    for band, count in zip(bands, counts):
        if count <= 0:
            continue
        offsets = np.arange(count, dtype=float)  # type: ignore[union-attr]
        positions[cursor : cursor + count] = band.start + (
            ((offsets + 0.5) / count) * (band.end - band.start)
        )
        cursor += count
    return positions


def _variant_component_names(variants: Sequence[FormulaVariant]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                component
                for variant in variants
                for component, weight in _variant_weight_items(variant)
                if weight > 0.0
            }
        )
    )


def _matrix_component_names(
    variants: Sequence[FormulaVariant],
    *,
    normalization_population_rows: Sequence[Mapping[str, object]],
    component_matrix_components: str,
) -> tuple[str, ...]:
    if component_matrix_components == "variant":
        return _variant_component_names(variants)
    if component_matrix_components == "all":
        return tuple(
            sorted(
                {
                    str(name)
                    for row in normalization_population_rows
                    for name in _difficulty_components_for_row(row)
                }
            )
        )
    raise ValueError(f"Unsupported component matrix component mode: {component_matrix_components}")


def _variant_weight_items(variant: FormulaVariant) -> Iterable[tuple[str, float]]:
    yield from variant.weights.items()
    for section in variant.piecewise_sections:
        yield from section.weights.items()


def _target_curve_values_by_dedupe(
    variant: FormulaVariant,
    *,
    normalization_population_rows: Sequence[Mapping[str, object]],
    target_band_weights: Sequence[float],
    band_width: float,
) -> dict[str, float]:
    scored_rows = []
    for row in normalization_population_rows:
        scored = dict(row)
        scored["raw_variant_difficulty"] = estimate_variant_difficulty(row, variant)
        scored_rows.append(scored)
    normalized_rows, _metadata = normalize_rows_by_target_curve(
        scored_rows,
        score_key="raw_variant_difficulty",
        output_key="variant_difficulty",
        band_weights=target_band_weights,
        band_width=band_width,
    )
    return {
        _normalization_dedupe_value(row): float(row["variant_difficulty"])
        for row in normalized_rows
        if row.get("variant_difficulty") is not None
    }


def _normalization_population_rows(
    seed_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in seed_rows:
        if not _is_vocab_row(row):
            continue
        grouped.setdefault(_normalization_dedupe_value(row), []).append(row)
    canonical = [
        dict(sorted(group, key=_normalization_canonical_sort_key)[0]) for group in grouped.values()
    ]
    return sorted(canonical, key=_normalization_row_sort_key)


def _normalization_dedupe_value(row: Mapping[str, object]) -> str:
    return f"{row.get('lemma') or ''}\t{row.get('reading') or ''}"


def _normalization_canonical_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _state_priority(row),
        _problem_priority(row),
        _optional_float(row.get("core_rank")) or float("inf"),
        str(row.get("pos") or ""),
        str(row.get("candidate_identity_key") or ""),
    )


def _normalization_row_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _optional_float(row.get("core_rank")) or float("inf"),
        str(row.get("lemma") or ""),
        str(row.get("reading") or ""),
        str(row.get("candidate_identity_key") or ""),
    )


def _state_priority(row: Mapping[str, object]) -> int:
    state = str(row.get("candidate_state") or "")
    if state == "normal_vocab":
        return 0
    if state == "deprioritized_vocab":
        return 1
    return 2


def _problem_priority(row: Mapping[str, object]) -> int:
    problem = str(row.get("problem_class") or "")
    if problem == "normal_vocab":
        return 0
    if problem == "proper_noun":
        return 1
    return 2


def _is_vocab_row(row: Mapping[str, object]) -> bool:
    return str(row.get("candidate_state") or "").strip() in VOCAB_STATES


def estimate_variant_difficulty(row: Mapping[str, object], variant: FormulaVariant) -> float:
    if variant.use_current_value:
        value = _optional_float(row.get("current_difficulty_proxy"))
        return _clamp01(value if value is not None else 0.0)
    components = _difficulty_components_for_variant(row, variant)
    if variant.piecewise_sections:
        value = _estimate_piecewise_difficulty(components, variant)
    else:
        value = _estimate_weighted_difficulty(
            components,
            variant.weights,
            max_shift_from_frequency=variant.max_shift_from_frequency,
        )
    return _clamp01(value)


def _estimate_piecewise_difficulty(
    components: Mapping[str, object],
    variant: FormulaVariant,
) -> float:
    frequency_value = _optional_float(components.get("frequency")) or 0.0
    weighted_value = 0.0
    influence_sum = 0.0
    nearest: tuple[float, PiecewiseFormulaSection] | None = None
    for section in variant.piecewise_sections:
        distance = abs(frequency_value - float(section.center))
        if nearest is None or distance < nearest[0]:
            nearest = (distance, section)
        influence = _piecewise_section_influence(frequency_value, section)
        if influence <= 0.0:
            continue
        section_value = _estimate_weighted_difficulty(
            components,
            section.weights,
            max_shift_from_frequency=section.max_shift_from_frequency,
        )
        weighted_value += influence * section_value
        influence_sum += influence
    if influence_sum <= 0.0:
        if nearest is None:
            return frequency_value
        weighted_value = _estimate_weighted_difficulty(
            components,
            nearest[1].weights,
            max_shift_from_frequency=nearest[1].max_shift_from_frequency,
        )
        influence_sum = 1.0
    value = weighted_value / influence_sum
    frequency_component = _optional_float(components.get("frequency"))
    if variant.max_shift_from_frequency is not None and frequency_component is not None:
        max_shift = max(0.0, float(variant.max_shift_from_frequency))
        value = min(
            float(frequency_component) + max_shift,
            max(float(frequency_component) - max_shift, value),
        )
    return _clamp01(value)


def _estimate_weighted_difficulty(
    components: Mapping[str, object],
    weights: Mapping[str, float],
    *,
    max_shift_from_frequency: float | None,
) -> float:
    numerator = 0.0
    denominator = 0.0
    for component, weight in weights.items():
        if weight <= 0:
            continue
        value = _optional_float(components.get(component))
        if value is None:
            continue
        numerator += float(weight) * float(value)
        denominator += float(weight)
    if denominator <= 0.0:
        fallback = _optional_float(components.get("frequency"))
        return _clamp01(fallback if fallback is not None else 0.0)
    value = numerator / denominator
    frequency_value = _optional_float(components.get("frequency"))
    if max_shift_from_frequency is not None and frequency_value is not None:
        max_shift = max(0.0, float(max_shift_from_frequency))
        value = min(
            float(frequency_value) + max_shift, max(float(frequency_value) - max_shift, value)
        )
    return _clamp01(value)


def _piecewise_section_influence(
    frequency_value: float,
    section: PiecewiseFormulaSection,
) -> float:
    radius = max(1e-9, float(section.radius))
    return max(0.0, 1.0 - (abs(frequency_value - float(section.center)) / radius))


def variant_difficulty_diagnostics(
    row: Mapping[str, object],
    variant: FormulaVariant,
) -> dict[str, object]:
    base_components = _difficulty_components_for_row(row)
    components = _difficulty_components_for_variant(row, variant)
    component_values = {
        key: _rounded(value)
        for key, value in sorted(components.items())
        if _optional_float(value) is not None
    }
    transform_detail = _variant_transform_json(variant)
    if variant.use_current_value:
        return {
            "mode": "current_value",
            "component_values": component_values,
            "base_component_values": {
                key: _rounded(value)
                for key, value in sorted(base_components.items())
                if _optional_float(value) is not None
            },
            "transforms": transform_detail,
            "final_raw_difficulty": _rounded(estimate_variant_difficulty(row, variant)),
        }
    if variant.piecewise_sections:
        frequency_value = _optional_float(components.get("frequency")) or 0.0
        section_rows = []
        for section in variant.piecewise_sections:
            section_value, contributions = _weighted_formula_diagnostics(
                components,
                section.weights,
                max_shift_from_frequency=section.max_shift_from_frequency,
            )
            section_rows.append(
                {
                    "section_id": section.section_id,
                    "center": _rounded(section.center),
                    "radius": _rounded(section.radius),
                    "influence": _rounded(_piecewise_section_influence(frequency_value, section)),
                    "value": _rounded(section_value),
                    "max_shift_from_frequency": _rounded(section.max_shift_from_frequency),
                    "weights": dict(section.weights),
                    "contributions": contributions,
                }
            )
        return {
            "mode": "piecewise",
            "component_values": component_values,
            "base_component_values": {
                key: _rounded(value)
                for key, value in sorted(base_components.items())
                if _optional_float(value) is not None
            },
            "transforms": transform_detail,
            "anchor_signal": "frequency",
            "anchor_value": _rounded(frequency_value),
            "sections": section_rows,
            "final_raw_difficulty": _rounded(estimate_variant_difficulty(row, variant)),
        }
    value, contributions = _weighted_formula_diagnostics(
        components,
        variant.weights,
        max_shift_from_frequency=variant.max_shift_from_frequency,
    )
    return {
        "mode": "linear",
        "component_values": component_values,
        "base_component_values": {
            key: _rounded(value)
            for key, value in sorted(base_components.items())
            if _optional_float(value) is not None
        },
        "transforms": transform_detail,
        "contributions": contributions,
        "max_shift_from_frequency": _rounded(variant.max_shift_from_frequency),
        "final_raw_difficulty": _rounded(value),
    }


def _weighted_formula_diagnostics(
    components: Mapping[str, object],
    weights: Mapping[str, float],
    *,
    max_shift_from_frequency: float | None,
) -> tuple[float, list[dict[str, object]]]:
    active: list[tuple[str, float, float]] = []
    for component, weight in weights.items():
        if weight <= 0.0:
            continue
        value = _optional_float(components.get(component))
        if value is None:
            continue
        active.append((component, float(weight), float(value)))
    denominator = sum(weight for _component, weight, _value in active)
    if denominator <= 0.0:
        fallback = _optional_float(components.get("frequency")) or 0.0
        return _clamp01(fallback), []
    raw_value = sum(weight * value for _component, weight, value in active) / denominator
    value = raw_value
    frequency_value = _optional_float(components.get("frequency"))
    if max_shift_from_frequency is not None and frequency_value is not None:
        max_shift = max(0.0, float(max_shift_from_frequency))
        value = min(
            float(frequency_value) + max_shift, max(float(frequency_value) - max_shift, value)
        )
    return _clamp01(value), [
        {
            "component": component,
            "weight": _rounded(weight),
            "value": _rounded(component_value),
            "weighted_share": _rounded(weight / denominator),
            "weighted_value": _rounded((weight / denominator) * component_value),
        }
        for component, weight, component_value in active
    ]


def load_tubelex_frequency_index(path: Path) -> TubelexFrequencyIndex:
    resolved = _resolve_path(path)
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    _raise_csv_field_size_limit()
    by_word: dict[str, TubelexFrequencyEntry] = {}
    by_word_pos: dict[tuple[str, str], TubelexFrequencyEntry] = {}
    max_count = 0.0
    max_videos = 0.0
    max_channels = 0.0
    row_count = 0
    with lzma.open(resolved, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = set(reader.fieldnames or ())
        required = {"word", "count", "videos", "channels"}
        missing = sorted(required - fieldnames)
        if missing:
            raise ValueError(f"TUBELEX frequency file is missing columns: {missing}")
        for rank, raw_row in enumerate(reader, start=1):
            word = str(raw_row.get("word") or "").strip()
            if not word:
                continue
            count = _optional_float(raw_row.get("count"))
            videos = _optional_float(raw_row.get("videos"))
            channels = _optional_float(raw_row.get("channels"))
            if count is None or videos is None or channels is None:
                continue
            pos = str(raw_row.get("pos") or "").strip()
            entry = TubelexFrequencyEntry(
                word=word,
                pos=pos,
                rank=rank,
                count=float(count),
                videos=float(videos),
                channels=float(channels),
            )
            row_count += 1
            max_count = max(max_count, entry.count)
            max_videos = max(max_videos, entry.videos)
            max_channels = max(max_channels, entry.channels)
            existing_word = by_word.get(word)
            if existing_word is None or _prefer_tubelex_entry(entry, existing_word):
                by_word[word] = entry
            if pos:
                key = (word, pos)
                existing_word_pos = by_word_pos.get(key)
                if existing_word_pos is None or _prefer_tubelex_entry(entry, existing_word_pos):
                    by_word_pos[key] = entry
    return TubelexFrequencyIndex(
        source_path=resolved,
        source_variant=_tubelex_source_variant(resolved),
        row_count=row_count,
        max_count=max_count,
        max_videos=max_videos,
        max_channels=max_channels,
        by_word=by_word,
        by_word_pos=by_word_pos,
    )


def _raise_csv_field_size_limit() -> None:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit = int(limit / 10)


def _prefer_tubelex_entry(
    candidate: TubelexFrequencyEntry,
    incumbent: TubelexFrequencyEntry,
) -> bool:
    if candidate.count != incumbent.count:
        return candidate.count > incumbent.count
    return candidate.rank < incumbent.rank


def _tubelex_source_variant(path: Path) -> str:
    name = path.name
    if name.endswith(".tsv.xz"):
        return name[: -len(".tsv.xz")]
    return path.stem


def _row_with_tubelex_frequency(
    row: Mapping[str, object],
    index: TubelexFrequencyIndex | None,
) -> dict[str, object]:
    updated = dict(row)
    if index is None:
        return updated
    match = _tubelex_entry_for_row(row, index)
    if match is None:
        return updated
    entry, match_kind = match
    profile = _tubelex_frequency_profile(
        entry,
        index,
        match_kind=match_kind,
        bccwj_frequency_difficulty=_optional_float(row.get("frequency_difficulty_proxy")),
    )
    learner_signals = dict(_mapping(updated.get("learner_signals")))
    learner_signals["tubelex_frequency"] = profile
    updated["learner_signals"] = learner_signals
    sources = [
        str(source)
        for source in (updated.get("learner_signal_sources") or ())
        if str(source or "").strip()
    ]
    if "tubelex_frequency" not in sources:
        sources.append("tubelex_frequency")
    updated["learner_signal_sources"] = sources
    updated["tubelex_frequency_profile"] = profile
    return updated


def _tubelex_entry_for_row(
    row: Mapping[str, object],
    index: TubelexFrequencyIndex,
) -> tuple[TubelexFrequencyEntry, str] | None:
    pos_candidates = _tubelex_pos_candidates(row)
    for word in _tubelex_word_candidates(row):
        for pos in pos_candidates:
            entry = index.by_word_pos.get((word, pos))
            if entry is not None:
                return entry, "word_pos_exact"
        entry = index.by_word.get(word)
        if entry is not None:
            return entry, "word"
    return None


def _tubelex_word_candidates(row: Mapping[str, object]) -> tuple[str, ...]:
    identity = _mapping(row.get("candidate_identity"))
    values: list[str] = []
    for value in (
        row.get("lemma"),
        row.get("sublemma"),
        identity.get("surface"),
        identity.get("reading"),
        row.get("reading"),
    ):
        text = str(value or "").strip()
        if text:
            values.append(text)
    return tuple(dict.fromkeys(values))


def _tubelex_pos_candidates(row: Mapping[str, object]) -> tuple[str, ...]:
    pos = str(row.get("pos") or "").strip()
    if not pos:
        return ()
    values = [pos]
    while "-" in pos:
        pos = pos.rsplit("-", 1)[0]
        if pos:
            values.append(pos)
    return tuple(dict.fromkeys(values))


def _tubelex_frequency_profile(
    entry: TubelexFrequencyEntry,
    index: TubelexFrequencyIndex,
    *,
    match_kind: str,
    bccwj_frequency_difficulty: float | None,
) -> dict[str, object]:
    rank_difficulty = _rank_difficulty_with_cap(
        entry.rank,
        max_rank=min(max(float(index.row_count), 1.0), TUBELEX_COMPONENT_MAX_RANK),
    )
    count_difficulty = _inverse_log_magnitude_difficulty(entry.count, index.max_count)
    videos_difficulty = _inverse_log_magnitude_difficulty(entry.videos, index.max_videos)
    channels_difficulty = _inverse_log_magnitude_difficulty(entry.channels, index.max_channels)
    frequency_difficulty = _mean_component(count_difficulty, rank_difficulty)
    dispersion_difficulty = _mean_component(videos_difficulty, channels_difficulty)
    return {
        "version": TUBELEX_SIGNAL_VERSION,
        "source": "tubelex",
        "source_variant": index.source_variant,
        "match_kind": match_kind,
        "word": entry.word,
        "pos": entry.pos or None,
        "rank": entry.rank,
        "count": _rounded(entry.count),
        "videos": _rounded(entry.videos),
        "channels": _rounded(entry.channels),
        "rank_difficulty": _rounded(rank_difficulty),
        "count_difficulty": _rounded(count_difficulty),
        "videos_difficulty": _rounded(videos_difficulty),
        "channels_difficulty": _rounded(channels_difficulty),
        "frequency_difficulty": _rounded(frequency_difficulty),
        "dispersion_difficulty": _rounded(dispersion_difficulty),
        "spoken_rescue": _rounded(
            _positive_delta_component(bccwj_frequency_difficulty, frequency_difficulty)
        ),
        "written_only_risk": _rounded(
            _positive_delta_component(frequency_difficulty, bccwj_frequency_difficulty)
        ),
        "bccwj_gap_abs": _rounded(
            _absolute_delta_component(frequency_difficulty, bccwj_frequency_difficulty)
        ),
    }


def _rank_difficulty_with_cap(value: float | None, *, max_rank: float) -> float | None:
    if value is None or value <= 0.0:
        return None
    if max_rank <= 1.0:
        return 0.0
    return _clamp01(math.log1p(value) / math.log1p(max_rank))


def _inverse_log_magnitude_difficulty(value: float | None, maximum: float | None) -> float | None:
    if value is None:
        return None
    if maximum is None or maximum <= 0.0:
        return None
    return _clamp01(1.0 - (math.log1p(max(0.0, float(value))) / math.log1p(maximum)))


def _positive_delta_component(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _clamp01(max(0.0, float(left) - float(right)))


def _absolute_delta_component(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _clamp01(abs(float(left) - float(right)))


def difficulty_components(row: Mapping[str, object]) -> dict[str, float | None]:
    signals = _mapping(row.get("learner_signals"))
    source_frequency_profile = _mapping(row.get("source_frequency_profile"))
    script_signal = _mapping(signals.get("japanese_script"))
    jmdict = _mapping(signals.get("jmdict_priority"))
    jmdict_lexical = _mapping(signals.get("jmdict_lexical"))
    kanjidic2 = _mapping(signals.get("kanjidic2"))
    jmnedict = _mapping(signals.get("jmnedict_name"))
    kanjivg = _mapping(signals.get("kanjivg"))
    jlpt_vocab = _mapping(signals.get("jlpt_vocabulary"))
    lesson_vocab = _mapping(signals.get("lesson_vocabulary"))
    acronym = _mapping(signals.get("ja_acronym"))
    tubelex = _mapping(signals.get("tubelex_frequency"))
    priority_score = _optional_float(jmdict.get("priority_score"))
    lexical_non_vocab_score = _optional_float(jmdict_lexical.get("non_vocab_signal_score"))
    name_signal_score = _optional_float(jmnedict.get("name_signal_score"))
    grade_proxy = _optional_float(kanjidic2.get("kanji_grade_difficulty_proxy"))
    rank_mean = _optional_float(kanjidic2.get("freq_rank_mean"))
    jlpt_hardest = _optional_float(kanjidic2.get("old_jlpt_hardest_level"))
    stroke_mean = _optional_float(kanjidic2.get("stroke_count_mean"))
    stroke_max = _optional_float(kanjidic2.get("stroke_count_max"))
    visual_complexity = _optional_float(kanjivg.get("visual_complexity_proxy_mean"))
    visual_complexity_max = _optional_float(kanjivg.get("visual_complexity_proxy_max"))
    jlpt_vocab_difficulty = _optional_float(jlpt_vocab.get("difficulty_score"))
    jlpt_vocab_beginner_core = _optional_float(jlpt_vocab.get("beginner_core_score"))
    jlpt_vocab_exact_difficulty = _optional_float(jlpt_vocab.get("exact_difficulty_score"))
    jlpt_vocab_exact_beginner_core = _optional_float(jlpt_vocab.get("exact_beginner_core_score"))
    lesson_vocab_difficulty = _optional_float(lesson_vocab.get("difficulty_score"))
    lesson_vocab_beginner_core = _optional_float(lesson_vocab.get("beginner_core_score"))
    acronym_class = str(acronym.get("recommended_acronym_class") or "").strip()
    acronym_state = str(acronym.get("recommended_candidate_state") or "").strip()
    acronym_known = bool(acronym)
    tubelex_frequency_difficulty = _optional_float(tubelex.get("frequency_difficulty"))
    tubelex_rank_difficulty = _optional_float(tubelex.get("rank_difficulty"))
    tubelex_count_difficulty = _optional_float(tubelex.get("count_difficulty"))
    tubelex_dispersion_difficulty = _optional_float(tubelex.get("dispersion_difficulty"))
    tubelex_videos_difficulty = _optional_float(tubelex.get("videos_difficulty"))
    tubelex_channels_difficulty = _optional_float(tubelex.get("channels_difficulty"))
    tubelex_spoken_rescue = _optional_float(tubelex.get("spoken_rescue"))
    tubelex_written_only_risk = _optional_float(tubelex.get("written_only_risk"))
    tubelex_bccwj_gap_abs = _optional_float(tubelex.get("bccwj_gap_abs"))
    script_complexity = _optional_float(script_signal.get("script_complexity_score"))
    core_rank = _optional_float(row.get("core_rank"))
    core_rank_known = "core_rank" in row
    frequency_difficulty = _optional_float(row.get("frequency_difficulty_proxy"))
    tubelex_bccwj_min_frequency = _min_component(
        frequency_difficulty,
        tubelex_frequency_difficulty,
    )
    tubelex_bccwj_mean_frequency = _mean_component(
        frequency_difficulty,
        tubelex_frequency_difficulty,
    )
    tubelex_bccwj_max_frequency = _max_component(
        frequency_difficulty,
        tubelex_frequency_difficulty,
    )
    tubelex_bccwj_agreement_hard = _sqrt_product_component(
        frequency_difficulty,
        tubelex_frequency_difficulty,
    )
    frequency_sqrt = _power_component(frequency_difficulty, exponent=0.5)
    frequency_power2 = _power_component(frequency_difficulty, exponent=2.0)
    frequency_power3 = _power_component(frequency_difficulty, exponent=3.0)
    frequency_ease = _inverse_component(frequency_difficulty)
    frequency_tail50 = _difficulty_ramp(frequency_difficulty, lower=0.50, upper=1.00)
    frequency_tail65 = _difficulty_ramp(frequency_difficulty, lower=0.65, upper=1.00)
    frequency_tail80 = _difficulty_ramp(frequency_difficulty, lower=0.80, upper=1.00)
    frequency_tail90 = _difficulty_ramp(frequency_difficulty, lower=0.90, upper=1.00)
    lexical_groups = _string_set(jmdict_lexical.get("lexical_class_groups"))
    jmdict_pos_values = _string_set(jmdict_lexical.get("pos_values"))
    jmdict_gloss_values = _string_set(jmdict_lexical.get("gloss_values"))
    jmdict_source_language_values = _lower_string_set(jmdict_lexical.get("source_language_values"))
    jmdict_source_language_codes = _jmdict_source_language_codes(jmdict_source_language_values)
    jmdict_source_text_values = _jmdict_source_text_values(jmdict_source_language_values)
    jmdict_priority_tags = _lower_string_set(
        (
            *_string_set(jmdict.get("direct_tags")),
            *_string_set(jmdict.get("entry_tags")),
        )
    )
    jmdict_misc_values = _lower_string_set(jmdict_lexical.get("misc_values"))
    jmdict_field_values = _lower_string_set(jmdict_lexical.get("field_values"))
    jmnedict_name_type_groups = _lower_string_set(jmnedict.get("name_type_groups"))
    jmdict_priority_difficulty = (
        _clamp01(1.0 - priority_score) if priority_score is not None else None
    )
    pedagogical_core_ease = _max_component(
        jlpt_vocab_beginner_core,
        lesson_vocab_beginner_core,
    )
    ordinary_vocab_protection = _max_component(
        frequency_ease,
        priority_score,
        pedagogical_core_ease,
    )
    ordinary_vocab_residual = _inverse_component(ordinary_vocab_protection)
    ordinary_vocab_residual_or_one = (
        ordinary_vocab_residual if ordinary_vocab_residual is not None else 1.0
    )
    old_jlpt_difficulty = _old_jlpt_difficulty(jlpt_hardest)
    stroke_difficulty = _stroke_difficulty(stroke_mean)
    stroke_difficulty_max = _stroke_difficulty(stroke_max)
    kanji_curriculum_burden = _mean_component(
        old_jlpt_difficulty,
        grade_proxy,
        _rank_difficulty(rank_mean),
    )
    kanji_shape_burden = _mean_component(
        visual_complexity,
        stroke_difficulty,
    )
    max_kanji_shape_burden = _max_component(
        visual_complexity_max,
        stroke_difficulty_max,
        visual_complexity,
        stroke_difficulty,
    )
    kanji_curriculum_missing_risk = _kanji_curriculum_missing_risk(
        kanjidic2,
        grade_proxy=grade_proxy,
        rank_mean=rank_mean,
        old_jlpt_hardest=jlpt_hardest,
        stroke_mean=stroke_mean,
        visual_complexity=visual_complexity,
    )
    kanji_burden = _mean_component(
        old_jlpt_difficulty,
        grade_proxy,
        visual_complexity,
        stroke_difficulty,
    )
    max_kanji_burden = _max_component(
        old_jlpt_difficulty,
        grade_proxy,
        visual_complexity_max,
        stroke_difficulty_max,
    )
    written_form_burden = _mean_component(
        visual_complexity,
        stroke_difficulty,
        script_complexity,
    )
    max_written_form_burden = _max_component(
        visual_complexity_max,
        stroke_difficulty_max,
        script_complexity,
    )
    wtype = _normalized_wtype(row.get("wtype"))
    pos = str(row.get("pos") or "")
    kango_risk = _binary_component(wtype == "kango", known=bool(wtype))
    wago_ease = _binary_component(wtype == "wago", known=bool(wtype))
    non_wago_risk = _binary_component(wtype != "wago", known=bool(wtype))
    gairaigo_risk = _binary_component(wtype == "gairaigo", known=bool(wtype))
    mixed_risk = _binary_component(wtype == "mixed", known=bool(wtype))
    proper_risk = _binary_component(wtype == "proper", known=bool(wtype))
    plain_verb_gate = _binary_component(_is_plain_verb_pos(pos), known=bool(pos))
    adjective_gate = _binary_component(_is_adjective_pos(pos), known=bool(pos))
    sahen_noun_risk = _binary_component(_is_sahen_noun_pos(pos), known=bool(pos))
    common_noun_gate = _binary_component(_is_common_noun_pos(pos), known=bool(pos))
    proper_noun_pos_risk = _binary_component("固有名詞" in pos, known=bool(pos))
    proper_place_pos_risk = _binary_component(
        "固有名詞-地名" in pos,
        known=bool(pos),
    )
    proper_country_pos_risk = _binary_component("地名-国" in pos, known=bool(pos))
    problem_class_proper_risk = _binary_component(
        str(row.get("problem_class") or "") == "proper_noun",
        known="problem_class" in row,
    )
    candidate_deprioritized_vocab_risk = _binary_component(
        str(row.get("candidate_state") or "") == "deprioritized_vocab",
        known="candidate_state" in row,
    )
    frequency_unranked_risk = _binary_component(
        core_rank is None or core_rank <= 0.0,
        known=core_rank_known,
    )
    frequency_rank_known = _binary_component(
        core_rank is not None and core_rank > 0.0,
        known=True,
    )
    frequency_value_known = _binary_component(frequency_difficulty is not None, known=True)
    jmdict_priority_known = _binary_component(priority_score is not None, known=True)
    jmdict_lexical_known = _binary_component(bool(jmdict_lexical), known=True)
    jmnedict_name_known = _binary_component(bool(jmnedict), known=True)
    jlpt_vocab_known = _binary_component(jlpt_vocab_difficulty is not None, known=True)
    jlpt_vocab_exact_known = _binary_component(
        bool(jlpt_vocab.get("exact_match")),
        known=bool(jlpt_vocab),
    )
    jlpt_vocab_surface_known = _binary_component(
        bool(jlpt_vocab.get("surface_match")),
        known=bool(jlpt_vocab),
    )
    jlpt_vocab_reading_known = _binary_component(
        bool(jlpt_vocab.get("reading_match")),
        known=bool(jlpt_vocab),
    )
    lesson_vocab_known = _binary_component(
        lesson_vocab_difficulty is not None,
        known=True,
    )
    kanjidic2_known = _binary_component(bool(kanjidic2), known=True)
    kanjivg_known = _binary_component(bool(kanjivg), known=True)
    acronym_signal_known = _binary_component(acronym_known, known=True)
    tubelex_frequency_known = _binary_component(bool(tubelex), known=True)
    bccwj_domain_rank_known = _binary_component(
        (_optional_float(source_frequency_profile.get("domain_rank_known_count")) or 0.0) > 0.0,
        known=True,
    )
    pedagogical_source_known = _max_component(jlpt_vocab_known, lesson_vocab_known)
    lexical_source_known = _max_component(jmdict_priority_known, jmdict_lexical_known)
    frequency_source_known = _max_component(frequency_value_known, tubelex_frequency_known)
    orthographic_source_known = _max_component(kanjidic2_known, kanjivg_known)
    source_known_values = (
        frequency_value_known,
        frequency_rank_known,
        jmdict_priority_known,
        jmdict_lexical_known,
        jmnedict_name_known,
        jlpt_vocab_known,
        lesson_vocab_known,
        kanjidic2_known,
        kanjivg_known,
        acronym_signal_known,
        tubelex_frequency_known,
        bccwj_domain_rank_known,
    )
    source_coverage_count = _count_component(
        sum(1.0 for value in source_known_values if value and value > 0.0),
        scale=float(len(source_known_values)),
    )
    lexical_known = bool(lexical_groups)
    particle_auxiliary_class = _binary_component(
        "particle_or_auxiliary" in lexical_groups,
        known=lexical_known,
    )
    numeric_class = _binary_component("numeric" in lexical_groups, known=lexical_known)
    affix_counter_class = _binary_component(
        "affix_or_counter" in lexical_groups,
        known=lexical_known,
    )
    function_discourse_class = _binary_component(
        "function_or_discourse_word" in lexical_groups,
        known=lexical_known,
    )
    proper_noun_lexical_overlap = _binary_component(
        "proper_noun" in lexical_groups,
        known=lexical_known,
    )
    jmdict_non_ladder_entry_risk = _product_component(
        lexical_non_vocab_score,
        ordinary_vocab_residual_or_one,
    )
    marked_usage_risk = _binary_component(
        "marked_usage" in lexical_groups,
        known=lexical_known,
    )
    kana_preferred_risk = _binary_component(
        "kana_preferred" in lexical_groups,
        known=lexical_known,
    )
    non_standard_reading_risk = _non_standard_reading_risk(row, kanjidic2)
    register_marked_risk = _binary_component(
        "register_marked" in lexical_groups,
        known=lexical_known,
    )
    dialect_risk = _binary_component("dialect_marked" in lexical_groups, known=lexical_known)
    loanword_source_risk = _binary_component(
        "loanword_source" in lexical_groups,
        known=lexical_known,
    )
    english_source_flag = _binary_component(
        bool(jmdict_source_language_codes & ENGLISH_SOURCE_LANGUAGE_CODES),
        known=bool(jmdict_lexical),
    )
    non_english_loan_source_flag = _binary_component(
        any(
            value not in ENGLISH_SOURCE_LANGUAGE_CODES
            and value not in NATIVE_OR_SINITIC_SOURCE_LANGUAGE_CODES
            for value in jmdict_source_language_codes
        ),
        known=bool(jmdict_lexical),
    )
    english_source_frequency_ease = _jmdict_english_source_frequency_ease(
        jmdict_source_language_codes,
        jmdict_source_text_values,
    )
    english_source_frequency_risk = _inverse_component(english_source_frequency_ease)
    english_gloss_frequency_ease = _jmdict_english_gloss_frequency_ease(jmdict_gloss_values)
    english_gloss_frequency_risk = _inverse_component(english_gloss_frequency_ease)
    sinitic_source = _binary_component(
        "sinitic_source" in lexical_groups,
        known=lexical_known,
    )
    source_text_present = _binary_component(
        "source_text_present" in lexical_groups,
        known=lexical_known,
    )
    source_type_marked = _binary_component(
        "source_type_marked" in lexical_groups,
        known=lexical_known,
    )
    wasei_source = _binary_component("wasei_source" in lexical_groups, known=lexical_known)
    kanji_form_marked_risk = _binary_component(
        "kanji_form_marked" in lexical_groups,
        known=lexical_known,
    )
    reading_form_marked_risk = _binary_component(
        "reading_form_marked" in lexical_groups,
        known=lexical_known,
    )
    search_only_form_risk = _binary_component(
        "search_only_form" in lexical_groups,
        known=lexical_known,
    )
    sense_restricted_risk = _binary_component(
        "sense_restricted" in lexical_groups,
        known=lexical_known,
    )
    reading_restricted_risk = _binary_component(
        "reading_restricted" in lexical_groups,
        known=lexical_known,
    )
    no_kanji_reading_risk = _binary_component(
        "no_kanji_reading" in lexical_groups,
        known=lexical_known,
    )
    polysemy_risk = _binary_component(
        "polysemous_entry" in lexical_groups,
        known=lexical_known,
    )
    sense_info_risk = _binary_component(
        "sense_info_marked" in lexical_groups,
        known=lexical_known,
    )
    cross_reference_risk = _binary_component(
        "cross_reference" in lexical_groups,
        known=lexical_known,
    )
    jmdict_news_priority_risk = _binary_component(
        any(tag.startswith("news") for tag in jmdict_priority_tags),
        known=bool(jmdict_priority_tags),
    )
    jmdict_news_priority_commonness = jmdict_news_priority_risk
    jmdict_foreign_priority_risk = _binary_component(
        any(tag.startswith("gai") for tag in jmdict_priority_tags),
        known=bool(jmdict_priority_tags),
    )
    jmdict_abbreviation_risk = _binary_component(
        "abbreviation" in jmdict_misc_values,
        known=bool(jmdict_misc_values),
    )
    jmdict_organization_misc_risk = _binary_component(
        "organization name" in jmdict_misc_values,
        known=bool(jmdict_misc_values),
    )
    jmdict_news_or_policy_domain_risk = _binary_component(
        bool(jmdict_field_values & {"business", "economics", "law", "politics"}),
        known=bool(jmdict_field_values),
    )
    jmdict_field_marked_risk = _binary_component(
        bool(jmdict_field_values),
        known=bool(jmdict_lexical),
    )
    jmnedict_person_name_risk = _binary_component(
        "person_name" in jmnedict_name_type_groups,
        known=bool(jmnedict_name_type_groups),
    )
    jmnedict_place_name_risk = _binary_component(
        "place_name" in jmnedict_name_type_groups,
        known=bool(jmnedict_name_type_groups),
    )
    jmnedict_org_product_name_risk = _binary_component(
        "organization_or_product_name" in jmnedict_name_type_groups,
        known=bool(jmnedict_name_type_groups),
    )
    jmnedict_creative_or_special_name_risk = _binary_component(
        bool(
            jmnedict_name_type_groups
            & {"creative_work_or_character_name", "mythic_or_special_name"}
        ),
        known=bool(jmnedict_name_type_groups),
    )
    proper_acronym_entity_risk = _max_component(
        _optional_float(acronym.get("proper_name_risk")),
        _binary_component(acronym_class == "proper_name_acronym", known=acronym_known),
    )
    proper_place_entity_overlap = _max_component(
        proper_place_pos_risk,
        jmnedict_place_name_risk,
    )
    proper_country_entity_overlap = _max_component(
        proper_country_pos_risk,
        _product_component(jmnedict_place_name_risk, jmdict_foreign_priority_risk),
    )
    proper_org_entity_overlap = _max_component(
        jmnedict_org_product_name_risk,
        jmdict_organization_misc_risk,
    )
    named_entity_overlap = _max_component(
        proper_noun_pos_risk,
        problem_class_proper_risk,
        jmnedict_person_name_risk,
        proper_place_entity_overlap,
        proper_org_entity_overlap,
        proper_acronym_entity_risk,
        jmnedict_creative_or_special_name_risk,
    )
    entity_unknown_gate = (
        1.0
        if (
            candidate_deprioritized_vocab_risk is None
            and frequency_tail65 is None
            and ordinary_vocab_residual is None
        )
        else None
    )
    entity_suppression_gate = _max_component(
        candidate_deprioritized_vocab_risk,
        frequency_tail65,
        ordinary_vocab_residual,
        entity_unknown_gate,
    )
    proper_place_entity_risk = _product_component(
        proper_place_entity_overlap,
        entity_suppression_gate,
    )
    proper_country_entity_risk = _product_component(
        proper_country_entity_overlap,
        entity_suppression_gate,
    )
    proper_org_entity_risk = _product_component(
        proper_org_entity_overlap,
        entity_suppression_gate,
    )
    named_entity_risk = _product_component(
        named_entity_overlap,
        entity_suppression_gate,
    )
    ordinary_ladder_entity_suppression_risk = named_entity_risk
    news_or_policy_topic_risk = _max_component(
        jmdict_news_or_policy_domain_risk,
    )
    news_or_policy_frequency_risk = _product_component(
        news_or_policy_topic_risk,
        frequency_difficulty,
    )
    news_named_entity_risk = _product_component(
        news_or_policy_topic_risk,
        named_entity_risk,
    )
    named_entity_frequency_risk = _product_component(
        named_entity_risk,
        frequency_difficulty,
    )
    news_named_frequency_risk = _product_component(
        news_named_entity_risk,
        frequency_difficulty,
    )
    news_abbreviation_entity_risk = _product_component(
        news_or_policy_topic_risk,
        jmdict_abbreviation_risk,
        named_entity_risk,
    )
    geopolitical_entity_risk = _max_component(
        proper_country_entity_risk,
        _product_component(proper_place_entity_risk, news_or_policy_topic_risk),
    )
    geopolitical_frequency_risk = _product_component(
        geopolitical_entity_risk,
        frequency_difficulty,
    )
    candidate_deprioritized_named_entity_risk = _product_component(
        candidate_deprioritized_vocab_risk,
        named_entity_risk,
    )
    candidate_deprioritized_named_frequency_risk = _product_component(
        candidate_deprioritized_named_entity_risk,
        frequency_difficulty,
    )
    lesson_name_contamination_risk = _product_component(
        _binary_component(lesson_vocab_difficulty is not None, known=True),
        named_entity_overlap,
    )
    lesson_name_contamination_frequency_risk = _product_component(
        lesson_name_contamination_risk,
        frequency_difficulty,
    )
    kango_kanji_burden = _interaction_component(kango_risk, kanji_burden)
    wago_kanji_burden = _interaction_component(wago_ease, kanji_burden)
    rare_wago_risk = _product_component(
        wago_ease,
        frequency_difficulty,
        _priority_rarity_multiplier(jmdict_priority_difficulty),
    )
    frequency_unranked_rare_risk = _product_component(
        frequency_unranked_risk,
        frequency_difficulty,
    )
    frequency_unranked_priority_risk = _product_component(
        frequency_unranked_risk,
        frequency_difficulty,
        _priority_rarity_multiplier(jmdict_priority_difficulty),
    )
    frequency_unranked_tail_risk = _product_component(
        frequency_unranked_risk,
        _difficulty_ramp(frequency_difficulty, lower=0.85, upper=1.00),
    )
    frequency_unranked_power2_risk = _product_component(
        frequency_unranked_risk,
        frequency_power2,
    )
    frequency_unranked_power3_risk = _product_component(
        frequency_unranked_risk,
        frequency_power3,
    )
    frequency_unranked_floor60_risk = _gated_floor_component(
        frequency_unranked_risk,
        frequency_difficulty,
        floor=0.60,
    )
    frequency_unranked_floor70_risk = _gated_floor_component(
        frequency_unranked_risk,
        frequency_difficulty,
        floor=0.70,
    )
    frequency_unranked_floor80_risk = _gated_floor_component(
        frequency_unranked_risk,
        frequency_difficulty,
        floor=0.80,
    )
    frequency_unranked_floor90_risk = _gated_floor_component(
        frequency_unranked_risk,
        frequency_difficulty,
        floor=0.90,
    )
    frequency_unranked_floor95_risk = _gated_floor_component(
        frequency_unranked_risk,
        frequency_difficulty,
        floor=0.95,
    )
    frequency_unranked_floor99_risk = _gated_floor_component(
        frequency_unranked_risk,
        frequency_difficulty,
        floor=0.99,
    )
    frequency_unranked_tail65_risk = _product_component(
        frequency_unranked_risk,
        frequency_tail65,
    )
    frequency_unranked_tail80_risk = _product_component(
        frequency_unranked_risk,
        frequency_tail80,
    )
    frequency_unranked_tail90_risk = _product_component(
        frequency_unranked_risk,
        frequency_tail90,
    )
    jmdict_entry_count = _count_component(
        _optional_float(jmdict_lexical.get("entry_count")),
        scale=6.0,
    )
    jmdict_pos_count = (
        _count_component(float(len(jmdict_pos_values)), scale=6.0) if jmdict_lexical else None
    )
    jmdict_field_count = (
        _count_component(float(len(jmdict_field_values)), scale=6.0) if jmdict_lexical else None
    )
    jmdict_kanji_form_count = _count_component(
        _optional_float(jmdict_lexical.get("kanji_form_count")),
        scale=8.0,
    )
    jmdict_reading_form_count = _count_component(
        _optional_float(jmdict_lexical.get("reading_form_count")),
        scale=8.0,
    )
    jmdict_form_count = _count_component(
        _optional_float(jmdict_lexical.get("form_count")),
        scale=12.0,
    )
    jmdict_gloss_count = _count_component(
        _optional_float(jmdict_lexical.get("gloss_count")),
        scale=8.0,
    )
    jmdict_sense_count = _count_component(
        _optional_float(jmdict_lexical.get("sense_count")),
        scale=6.0,
    )
    jmdict_entry_ambiguity = _excess_count_component(
        _optional_float(jmdict_lexical.get("entry_count")),
        baseline=1.0,
        scale=4.0,
    )
    jmdict_pos_ambiguity = (
        _excess_count_component(float(len(jmdict_pos_values)), baseline=1.0, scale=4.0)
        if jmdict_lexical
        else None
    )
    jmdict_kanji_form_ambiguity = _excess_count_component(
        _optional_float(jmdict_lexical.get("kanji_form_count")),
        baseline=1.0,
        scale=6.0,
    )
    jmdict_reading_form_ambiguity = _excess_count_component(
        _optional_float(jmdict_lexical.get("reading_form_count")),
        baseline=1.0,
        scale=6.0,
    )
    jmdict_form_ambiguity = _excess_count_component(
        _optional_float(jmdict_lexical.get("form_count")),
        baseline=2.0,
        scale=8.0,
    )
    jmdict_sense_ambiguity = _excess_count_component(
        _optional_float(jmdict_lexical.get("sense_count")),
        baseline=1.0,
        scale=8.0,
    )
    jmdict_gloss_ambiguity = _excess_count_component(
        _optional_float(jmdict_lexical.get("gloss_count")),
        baseline=1.0,
        scale=12.0,
    )
    restriction_counts = [
        _optional_float(jmdict_lexical.get("sense_restriction_count")),
        _optional_float(jmdict_lexical.get("reading_restriction_count")),
        _optional_float(jmdict_lexical.get("no_kanji_reading_count")),
    ]
    jmdict_restriction_count = (
        _count_component(
            sum(value for value in restriction_counts if value is not None),
            scale=6.0,
        )
        if any(value is not None for value in restriction_counts)
        else None
    )
    jmdict_ambiguity_risk = _max_component(
        jmdict_entry_ambiguity,
        jmdict_pos_ambiguity,
        jmdict_kanji_form_ambiguity,
        jmdict_reading_form_ambiguity,
        jmdict_form_ambiguity,
        jmdict_sense_ambiguity,
        jmdict_gloss_ambiguity,
    )
    jmdict_reading_complexity_risk = _max_component(
        reading_form_marked_risk,
        reading_restricted_risk,
        no_kanji_reading_risk,
        non_standard_reading_risk,
        jmdict_reading_form_ambiguity,
    )
    jmdict_restriction_complexity_risk = _max_component(
        sense_restricted_risk,
        reading_restricted_risk,
        no_kanji_reading_risk,
        jmdict_restriction_count,
    )
    common_jmdict_ambiguity_risk = _product_component(
        frequency_ease,
        jmdict_ambiguity_risk,
    )
    common_reading_complexity_risk = _product_component(
        frequency_ease,
        jmdict_reading_complexity_risk,
    )
    common_restriction_complexity_risk = _product_component(
        frequency_ease,
        jmdict_restriction_complexity_risk,
    )
    bccwj_domain_rank_coverage = _count_component(
        _optional_float(source_frequency_profile.get("domain_rank_known_count")),
        scale=24.0,
    )
    bccwj_domain_rank_spread = _rank_spread_component(
        _optional_float(source_frequency_profile.get("domain_rank_spread"))
    )
    bccwj_domain_rank_variability = bccwj_domain_rank_spread
    bccwj_domain_profile_variability = _sqrt_product_component(
        bccwj_domain_rank_coverage,
        bccwj_domain_rank_spread,
    )
    bccwj_domain_profile_risk = bccwj_domain_profile_variability
    bccwj_rank_spread = _rank_spread_component(
        _optional_float(source_frequency_profile.get("rank_spread"))
    )
    bccwj_rank_variability = bccwj_rank_spread
    jmdict_register_domain_risk = _max_component(
        register_marked_risk,
        dialect_risk,
        source_type_marked,
        jmdict_field_marked_risk,
    )
    common_register_domain_risk = _product_component(
        frequency_ease,
        jmdict_register_domain_risk,
    )
    common_kango_register_domain_risk = _product_component(
        kango_risk,
        frequency_ease,
        jmdict_register_domain_risk,
    )
    gairaigo_english_source_ease = _product_component(
        gairaigo_risk,
        english_source_flag,
        _max_component(english_source_frequency_ease, 0.35),
    )
    gairaigo_english_gloss_frequency_ease = _product_component(
        gairaigo_risk,
        english_gloss_frequency_ease,
    )
    gairaigo_non_english_source_risk = _product_component(
        gairaigo_risk,
        non_english_loan_source_flag,
    )
    gairaigo_english_rare_source_risk = _product_component(
        gairaigo_risk,
        english_source_flag,
        english_source_frequency_risk,
    )
    gairaigo_domain_source_risk = _product_component(
        gairaigo_risk,
        _max_component(
            jmdict_register_domain_risk,
            jmdict_field_marked_risk,
            jmdict_abbreviation_risk,
            source_type_marked,
            wasei_source,
        ),
    )
    gairaigo_marked_source_risk = _product_component(
        gairaigo_risk,
        _max_component(
            non_english_loan_source_flag,
            gairaigo_english_rare_source_risk,
            jmdict_register_domain_risk,
            jmdict_abbreviation_risk,
            source_type_marked,
            wasei_source,
        ),
    )
    common_kango_written_burden = _product_component(
        kango_risk,
        frequency_ease,
        max_written_form_burden,
    )
    common_kango_ambiguity_risk = _product_component(
        kango_risk,
        frequency_ease,
        jmdict_ambiguity_risk,
    )
    common_kango_complexity_risk = _max_component(
        common_kango_register_domain_risk,
        common_kango_written_burden,
        common_kango_ambiguity_risk,
    )
    kanjidic_nanori_reading_count_score = _count_component(
        _optional_float(kanjidic2.get("nanori_reading_count")),
        scale=4.0,
    )
    kanjidic_variant_type_count_score = _count_component(
        _optional_float(kanjidic2.get("variant_type_count")),
        scale=2.0,
    )
    rare_wago_written_risk = _product_component(
        rare_wago_risk,
        written_form_burden,
    )
    rare_wago_max_kanji_burden = _product_component(
        rare_wago_risk,
        max_kanji_burden,
    )
    rare_wago_max_written_burden = _product_component(
        rare_wago_risk,
        max_written_form_burden,
    )
    rare_wago_marked_usage_risk = _product_component(
        wago_ease,
        frequency_difficulty,
        marked_usage_risk,
        _priority_rarity_multiplier(jmdict_priority_difficulty),
    )
    rare_wago_missing_curriculum_risk = _product_component(
        rare_wago_risk,
        kanji_curriculum_missing_risk,
    )
    rare_wago_missing_curriculum_shape_risk = _product_component(
        rare_wago_missing_curriculum_risk,
        max_kanji_shape_burden,
    )
    upper_reading_rarity = _upper_reading_rarity_multiplier(frequency_difficulty)
    rare_non_standard_reading_risk = _product_component(
        non_standard_reading_risk,
        upper_reading_rarity,
        _priority_rarity_multiplier(jmdict_priority_difficulty),
    )
    rare_wago_non_standard_reading_risk = _product_component(
        wago_ease,
        non_standard_reading_risk,
        upper_reading_rarity,
        _priority_rarity_multiplier(jmdict_priority_difficulty),
    )
    rare_wago_obscure_written_risk = _max_component(
        rare_wago_max_kanji_burden,
        rare_wago_max_written_burden,
        rare_wago_marked_usage_risk,
        rare_wago_missing_curriculum_risk,
        rare_wago_non_standard_reading_risk,
    )
    rare_wago_tail_risk = _product_component(
        wago_ease,
        _difficulty_ramp(frequency_difficulty, lower=0.90, upper=1.00),
        _max_component(
            rare_wago_obscure_written_risk,
            rare_non_standard_reading_risk,
            rare_wago_non_standard_reading_risk,
        ),
    )
    written_wago_tail_risk = _product_component(
        wago_ease,
        _difficulty_ramp(frequency_difficulty, lower=0.65, upper=1.00),
        _sqrt_product_component(max_written_form_burden, written_form_burden),
    )
    kango_common_priority_risk = _product_component(
        kango_risk,
        frequency_difficulty,
        jmdict_priority_difficulty,
    )
    kango_uncommon_kanji_burden = _product_component(
        kango_kanji_burden,
        frequency_difficulty,
        _priority_rarity_multiplier(jmdict_priority_difficulty),
    )
    kango_mid_signal = _interaction_component(
        kango_risk,
        _clamp_optional(
            _weighted_average(
                (
                    (_sqrt_product_component(frequency_difficulty, kango_kanji_burden), 0.85),
                    (kango_uncommon_kanji_burden, 0.15),
                )
            )
        ),
    )
    sahen_kango_ease_gate = _interaction_component(sahen_noun_risk, kango_risk)
    return {
        "frequency": frequency_difficulty,
        "frequency_unranked_risk": frequency_unranked_risk,
        "frequency_unranked_rare_risk": frequency_unranked_rare_risk,
        "frequency_unranked_priority_risk": frequency_unranked_priority_risk,
        "frequency_unranked_tail_risk": frequency_unranked_tail_risk,
        "frequency_sqrt": frequency_sqrt,
        "frequency_power2": frequency_power2,
        "frequency_power3": frequency_power3,
        "frequency_ease": frequency_ease,
        "frequency_tail50": frequency_tail50,
        "frequency_tail65": frequency_tail65,
        "frequency_tail80": frequency_tail80,
        "frequency_tail90": frequency_tail90,
        "frequency_unranked_power2_risk": frequency_unranked_power2_risk,
        "frequency_unranked_power3_risk": frequency_unranked_power3_risk,
        "frequency_unranked_floor60_risk": frequency_unranked_floor60_risk,
        "frequency_unranked_floor70_risk": frequency_unranked_floor70_risk,
        "frequency_unranked_floor80_risk": frequency_unranked_floor80_risk,
        "frequency_unranked_floor90_risk": frequency_unranked_floor90_risk,
        "frequency_unranked_floor95_risk": frequency_unranked_floor95_risk,
        "frequency_unranked_floor99_risk": frequency_unranked_floor99_risk,
        "frequency_unranked_tail65_risk": frequency_unranked_tail65_risk,
        "frequency_unranked_tail80_risk": frequency_unranked_tail80_risk,
        "frequency_unranked_tail90_risk": frequency_unranked_tail90_risk,
        "frequency_rank_known": frequency_rank_known,
        "frequency_value_known": frequency_value_known,
        "frequency_source_known": frequency_source_known,
        "source_coverage_count": source_coverage_count,
        "tubelex_frequency": tubelex_frequency_difficulty,
        "tubelex_frequency_known": tubelex_frequency_known,
        "tubelex_rank_difficulty": tubelex_rank_difficulty,
        "tubelex_count_difficulty": tubelex_count_difficulty,
        "tubelex_dispersion_difficulty": tubelex_dispersion_difficulty,
        "tubelex_videos_difficulty": tubelex_videos_difficulty,
        "tubelex_channels_difficulty": tubelex_channels_difficulty,
        "tubelex_spoken_rescue": tubelex_spoken_rescue,
        "tubelex_written_only_risk": tubelex_written_only_risk,
        "tubelex_bccwj_gap_abs": tubelex_bccwj_gap_abs,
        "tubelex_bccwj_min_frequency": tubelex_bccwj_min_frequency,
        "tubelex_bccwj_mean_frequency": tubelex_bccwj_mean_frequency,
        "tubelex_bccwj_max_frequency": tubelex_bccwj_max_frequency,
        "tubelex_bccwj_agreement_hard": tubelex_bccwj_agreement_hard,
        "script_complexity": script_complexity,
        "jmdict_priority": jmdict_priority_difficulty,
        "jmdict_priority_known": jmdict_priority_known,
        "jmdict_lexical_known": jmdict_lexical_known,
        "lexical_source_known": lexical_source_known,
        "jmdict_non_vocab_raw_class_score": lexical_non_vocab_score,
        "jmdict_particle_auxiliary_class": particle_auxiliary_class,
        "jmdict_numeric_class": numeric_class,
        "jmdict_affix_counter_class": affix_counter_class,
        "jmdict_function_discourse_class": function_discourse_class,
        "jmdict_proper_noun_overlap": proper_noun_lexical_overlap,
        "jmdict_non_ladder_entry_risk": jmdict_non_ladder_entry_risk,
        "jmdict_non_vocab_risk": jmdict_non_ladder_entry_risk,
        "jmnedict_name_risk": name_signal_score,
        "jmnedict_name_overlap": name_signal_score,
        "jmnedict_name_known": jmnedict_name_known,
        "kanji_grade": grade_proxy,
        "kanjidic2_known": kanjidic2_known,
        "kanji_frequency_rank": _rank_difficulty(rank_mean),
        "old_jlpt_kanji": old_jlpt_difficulty,
        "stroke_count": stroke_difficulty,
        "kanjivg_visual_complexity": visual_complexity,
        "kanjivg_known": kanjivg_known,
        "orthographic_source_known": orthographic_source_known,
        "jlpt_vocab_difficulty": jlpt_vocab_difficulty,
        "jlpt_vocab_beginner_core": jlpt_vocab_beginner_core,
        "jlpt_vocab_known": jlpt_vocab_known,
        "jlpt_vocab_exact_difficulty": jlpt_vocab_exact_difficulty,
        "jlpt_vocab_exact_beginner_core": jlpt_vocab_exact_beginner_core,
        "jlpt_vocab_exact_known": jlpt_vocab_exact_known,
        "jlpt_vocab_surface_known": jlpt_vocab_surface_known,
        "jlpt_vocab_reading_known": jlpt_vocab_reading_known,
        "lesson_vocab_difficulty": lesson_vocab_difficulty,
        "lesson_vocab_beginner_core": lesson_vocab_beginner_core,
        "lesson_vocab_known": lesson_vocab_known,
        "pedagogical_source_known": pedagogical_source_known,
        "acronym_signal_known": acronym_signal_known,
        "acronym_surface_confidence": _optional_float(acronym.get("surface_confidence")),
        "acronym_mixed_code_confidence": _optional_float(acronym.get("mixed_code_confidence")),
        "acronym_spellout_reading": _optional_float(acronym.get("reading_spellout_confidence")),
        "acronym_identity_gloss": _optional_float(acronym.get("identity_gloss_confidence")),
        "acronym_expanded_gloss": _optional_float(acronym.get("expanded_gloss_confidence")),
        "acronym_japanese_specific_usage": _optional_float(
            acronym.get("japanese_specific_usage_confidence")
        ),
        "acronym_domain_concentration": _max_component(
            _optional_float(acronym.get("domain_concentration")),
            _optional_float(acronym.get("field_domain_confidence")),
        ),
        "acronym_proper_name_risk": _optional_float(acronym.get("proper_name_risk")),
        "acronym_real_usage_confidence": _optional_float(acronym.get("real_usage_confidence")),
        "acronym_default_suppress_risk": _binary_component(
            acronym_state == "suppressed_default",
            known=acronym_known,
        ),
        "acronym_topic_only_risk": _binary_component(
            acronym_state == "topic_only",
            known=acronym_known,
        ),
        "acronym_shared_exact_risk": _binary_component(
            acronym_class == "shared_exact_acronym",
            known=acronym_known,
        ),
        "acronym_japanese_specific_gate": _binary_component(
            acronym_class == "japanese_specific_acronym",
            known=acronym_known,
        ),
        "kanji_curriculum_burden": kanji_curriculum_burden,
        "kanji_shape_burden": kanji_shape_burden,
        "max_kanji_shape_burden": max_kanji_shape_burden,
        "kanji_curriculum_missing_risk": kanji_curriculum_missing_risk,
        "kanji_burden": kanji_burden,
        "max_kanji_burden": max_kanji_burden,
        "written_form_burden": written_form_burden,
        "max_written_form_burden": max_written_form_burden,
        "jmdict_marked_usage_flag": marked_usage_risk,
        "jmdict_marked_usage_risk": marked_usage_risk,
        "jmdict_kana_preferred_flag": kana_preferred_risk,
        "jmdict_kana_preferred_risk": kana_preferred_risk,
        "non_standard_reading_risk": non_standard_reading_risk,
        "jmdict_register_marked_flag": register_marked_risk,
        "jmdict_register_marked_risk": register_marked_risk,
        "jmdict_dialect_flag": dialect_risk,
        "jmdict_dialect_risk": dialect_risk,
        "jmdict_loanword_source_flag": loanword_source_risk,
        "jmdict_loanword_source_risk": loanword_source_risk,
        "jmdict_english_source_flag": english_source_flag,
        "jmdict_non_english_loan_source_flag": non_english_loan_source_flag,
        "jmdict_english_source_frequency_ease": english_source_frequency_ease,
        "jmdict_english_source_frequency_risk": english_source_frequency_risk,
        "jmdict_english_gloss_frequency_ease": english_gloss_frequency_ease,
        "jmdict_english_gloss_frequency_risk": english_gloss_frequency_risk,
        "jmdict_sinitic_source_flag": sinitic_source,
        "jmdict_sinitic_source": sinitic_source,
        "jmdict_source_text_flag": source_text_present,
        "jmdict_source_text_present": source_text_present,
        "jmdict_source_type_flag": source_type_marked,
        "jmdict_source_type_marked": source_type_marked,
        "jmdict_wasei_source_flag": wasei_source,
        "jmdict_wasei_source": wasei_source,
        "jmdict_kanji_form_marked_flag": kanji_form_marked_risk,
        "jmdict_kanji_form_marked_risk": kanji_form_marked_risk,
        "jmdict_reading_form_marked_flag": reading_form_marked_risk,
        "jmdict_reading_form_marked_risk": reading_form_marked_risk,
        "jmdict_search_only_form_flag": search_only_form_risk,
        "jmdict_search_only_form_risk": search_only_form_risk,
        "jmdict_sense_restricted_flag": sense_restricted_risk,
        "jmdict_sense_restricted_risk": sense_restricted_risk,
        "jmdict_reading_restricted_flag": reading_restricted_risk,
        "jmdict_reading_restricted_risk": reading_restricted_risk,
        "jmdict_no_kanji_reading_flag": no_kanji_reading_risk,
        "jmdict_no_kanji_reading_risk": no_kanji_reading_risk,
        "jmdict_polysemy_flag": polysemy_risk,
        "jmdict_polysemy_risk": polysemy_risk,
        "jmdict_sense_info_flag": sense_info_risk,
        "jmdict_sense_info_risk": sense_info_risk,
        "jmdict_cross_reference_flag": cross_reference_risk,
        "jmdict_cross_reference_risk": cross_reference_risk,
        "jmdict_news_priority_risk": jmdict_news_priority_risk,
        "jmdict_news_priority_commonness": jmdict_news_priority_commonness,
        "jmdict_foreign_priority_commonness": jmdict_foreign_priority_risk,
        "jmdict_foreign_priority_risk": jmdict_foreign_priority_risk,
        "jmdict_abbreviation_flag": jmdict_abbreviation_risk,
        "jmdict_abbreviation_risk": jmdict_abbreviation_risk,
        "jmdict_organization_misc_flag": jmdict_organization_misc_risk,
        "jmdict_organization_misc_risk": jmdict_organization_misc_risk,
        "jmdict_news_or_policy_field_flag": jmdict_news_or_policy_domain_risk,
        "jmdict_news_or_policy_domain_risk": jmdict_news_or_policy_domain_risk,
        "jmdict_field_marked_flag": jmdict_field_marked_risk,
        "jmdict_field_marked_risk": jmdict_field_marked_risk,
        "jmnedict_person_name_risk": jmnedict_person_name_risk,
        "jmnedict_person_name_overlap": jmnedict_person_name_risk,
        "jmnedict_place_name_risk": jmnedict_place_name_risk,
        "jmnedict_place_name_overlap": jmnedict_place_name_risk,
        "jmnedict_org_product_name_risk": jmnedict_org_product_name_risk,
        "jmnedict_org_product_name_overlap": jmnedict_org_product_name_risk,
        "jmnedict_creative_or_special_name_risk": jmnedict_creative_or_special_name_risk,
        "jmnedict_creative_or_special_name_overlap": jmnedict_creative_or_special_name_risk,
        "proper_noun_pos_risk": proper_noun_pos_risk,
        "proper_noun_pos_flag": proper_noun_pos_risk,
        "proper_place_pos_risk": proper_place_pos_risk,
        "proper_place_pos_flag": proper_place_pos_risk,
        "proper_country_pos_risk": proper_country_pos_risk,
        "proper_country_pos_flag": proper_country_pos_risk,
        "problem_class_proper_risk": problem_class_proper_risk,
        "problem_class_proper_flag": problem_class_proper_risk,
        "candidate_deprioritized_vocab_risk": candidate_deprioritized_vocab_risk,
        "proper_acronym_entity_risk": proper_acronym_entity_risk,
        "proper_place_entity_overlap": proper_place_entity_overlap,
        "proper_place_entity_risk": proper_place_entity_risk,
        "proper_country_entity_overlap": proper_country_entity_overlap,
        "proper_country_entity_risk": proper_country_entity_risk,
        "proper_org_entity_overlap": proper_org_entity_overlap,
        "proper_org_entity_risk": proper_org_entity_risk,
        "named_entity_overlap": named_entity_overlap,
        "ordinary_vocab_protection": ordinary_vocab_protection,
        "entity_suppression_gate": entity_suppression_gate,
        "ordinary_ladder_entity_suppression_risk": ordinary_ladder_entity_suppression_risk,
        "named_entity_risk": named_entity_risk,
        "news_or_policy_topic_risk": news_or_policy_topic_risk,
        "news_or_policy_frequency_risk": news_or_policy_frequency_risk,
        "news_named_entity_risk": news_named_entity_risk,
        "named_entity_frequency_risk": named_entity_frequency_risk,
        "news_named_frequency_risk": news_named_frequency_risk,
        "news_abbreviation_entity_risk": news_abbreviation_entity_risk,
        "geopolitical_entity_risk": geopolitical_entity_risk,
        "geopolitical_frequency_risk": geopolitical_frequency_risk,
        "candidate_deprioritized_named_entity_risk": candidate_deprioritized_named_entity_risk,
        "candidate_deprioritized_named_frequency_risk": candidate_deprioritized_named_frequency_risk,
        "lesson_name_contamination_risk": lesson_name_contamination_risk,
        "lesson_name_contamination_frequency_risk": lesson_name_contamination_frequency_risk,
        "jmdict_entry_count": jmdict_entry_count,
        "jmdict_pos_count": jmdict_pos_count,
        "jmdict_field_count": jmdict_field_count,
        "jmdict_kanji_form_count": jmdict_kanji_form_count,
        "jmdict_reading_form_count": jmdict_reading_form_count,
        "jmdict_form_count": jmdict_form_count,
        "jmdict_gloss_count": jmdict_gloss_count,
        "jmdict_sense_count": jmdict_sense_count,
        "jmdict_restriction_count": jmdict_restriction_count,
        "jmdict_entry_ambiguity": jmdict_entry_ambiguity,
        "jmdict_pos_ambiguity": jmdict_pos_ambiguity,
        "jmdict_kanji_form_ambiguity": jmdict_kanji_form_ambiguity,
        "jmdict_reading_form_ambiguity": jmdict_reading_form_ambiguity,
        "jmdict_form_ambiguity": jmdict_form_ambiguity,
        "jmdict_sense_ambiguity": jmdict_sense_ambiguity,
        "jmdict_gloss_ambiguity": jmdict_gloss_ambiguity,
        "jmdict_ambiguity_score": jmdict_ambiguity_risk,
        "jmdict_ambiguity_risk": jmdict_ambiguity_risk,
        "jmdict_reading_complexity_score": jmdict_reading_complexity_risk,
        "jmdict_reading_complexity_risk": jmdict_reading_complexity_risk,
        "jmdict_restriction_complexity_score": jmdict_restriction_complexity_risk,
        "jmdict_restriction_complexity_risk": jmdict_restriction_complexity_risk,
        "common_jmdict_ambiguity_score": common_jmdict_ambiguity_risk,
        "common_jmdict_ambiguity_risk": common_jmdict_ambiguity_risk,
        "common_reading_complexity_score": common_reading_complexity_risk,
        "common_reading_complexity_risk": common_reading_complexity_risk,
        "common_restriction_complexity_score": common_restriction_complexity_risk,
        "common_restriction_complexity_risk": common_restriction_complexity_risk,
        "jmdict_register_domain_flag": jmdict_register_domain_risk,
        "jmdict_register_domain_score": jmdict_register_domain_risk,
        "jmdict_register_domain_risk": jmdict_register_domain_risk,
        "common_register_domain_score": common_register_domain_risk,
        "common_register_domain_risk": common_register_domain_risk,
        "common_kango_register_domain_score": common_kango_register_domain_risk,
        "common_kango_register_domain_risk": common_kango_register_domain_risk,
        "gairaigo_english_source_ease": gairaigo_english_source_ease,
        "gairaigo_english_gloss_frequency_ease": gairaigo_english_gloss_frequency_ease,
        "gairaigo_non_english_source_risk": gairaigo_non_english_source_risk,
        "gairaigo_english_rare_source_risk": gairaigo_english_rare_source_risk,
        "gairaigo_domain_source_risk": gairaigo_domain_source_risk,
        "gairaigo_marked_source_risk": gairaigo_marked_source_risk,
        "common_kango_written_burden": common_kango_written_burden,
        "common_kango_ambiguity_score": common_kango_ambiguity_risk,
        "common_kango_ambiguity_risk": common_kango_ambiguity_risk,
        "common_kango_complexity_score": common_kango_complexity_risk,
        "common_kango_complexity_risk": common_kango_complexity_risk,
        "kanjidic_nanori_reading_count_score": kanjidic_nanori_reading_count_score,
        "kanjidic_nanori_reading_risk": kanjidic_nanori_reading_count_score,
        "kanjidic_meaning_count": _count_component(
            _optional_float(kanjidic2.get("meaning_count")),
            scale=8.0,
        ),
        "kanjidic_radical_value_count": _count_component(
            _optional_float(kanjidic2.get("radical_value_count")),
            scale=4.0,
        ),
        "kanjidic_variant_type_count_score": kanjidic_variant_type_count_score,
        "kanjidic_variant_type_risk": kanjidic_variant_type_count_score,
        "kanjidic_query_code_coverage": _count_component(
            _optional_float(kanjidic2.get("query_code_type_count")),
            scale=4.0,
        ),
        "kanjidic_reference_depth": _count_component(
            _optional_float(kanjidic2.get("dictionary_reference_type_count")),
            scale=20.0,
        ),
        "kanjivg_phonetic_component": _count_component(
            _optional_float(kanjivg.get("phonetic_component_count")),
            scale=4.0,
        ),
        "kanjivg_variant_structure": _count_component(
            _optional_float(kanjivg.get("variant_count")),
            scale=2.0,
        ),
        "kanjivg_position_detail": _count_component(
            _optional_float(kanjivg.get("position_value_count")),
            scale=4.0,
        ),
        "bccwj_domain_rank_coverage": bccwj_domain_rank_coverage,
        "bccwj_domain_rank_known": bccwj_domain_rank_known,
        "bccwj_domain_rank_spread": bccwj_domain_rank_spread,
        "bccwj_domain_rank_variability": bccwj_domain_rank_variability,
        "bccwj_domain_profile_variability": bccwj_domain_profile_variability,
        "bccwj_domain_profile_risk": bccwj_domain_profile_risk,
        "bccwj_rank_spread": bccwj_rank_spread,
        "bccwj_rank_variability": bccwj_rank_variability,
        "bccwj_pmw_spread": _magnitude_spread_component(
            _optional_float(source_frequency_profile.get("pmw_spread")),
            _optional_float(source_frequency_profile.get("pmw_max")),
        ),
        "bccwj_fixed_variable_rank_delta": _signed_rank_delta_component(
            _optional_float(source_frequency_profile.get("fixed_variable_rank_delta"))
        ),
        "wtype_kango_risk": kango_risk,
        "wtype_wago_ease": wago_ease,
        "wtype_non_wago_risk": non_wago_risk,
        "wtype_gairaigo_risk": gairaigo_risk,
        "wtype_mixed_risk": mixed_risk,
        "wtype_proper_flag": proper_risk,
        "wtype_proper_risk": proper_risk,
        "pos_plain_verb_gate": plain_verb_gate,
        "pos_adjective_gate": adjective_gate,
        "pos_sahen_noun_risk": sahen_noun_risk,
        "pos_common_noun_gate": common_noun_gate,
        "kango_old_jlpt_kanji": _interaction_component(kango_risk, old_jlpt_difficulty),
        "kango_kanji_grade": _interaction_component(kango_risk, grade_proxy),
        "kango_visual_complexity": _interaction_component(kango_risk, visual_complexity),
        "kango_kanji_burden": kango_kanji_burden,
        "kango_common_priority_risk": kango_common_priority_risk,
        "kango_uncommon_kanji_burden": kango_uncommon_kanji_burden,
        "wago_old_jlpt_kanji": _interaction_component(wago_ease, old_jlpt_difficulty),
        "wago_kanji_grade": _interaction_component(wago_ease, grade_proxy),
        "wago_visual_complexity": _interaction_component(wago_ease, visual_complexity),
        "wago_kanji_burden": wago_kanji_burden,
        "rare_wago_risk": rare_wago_risk,
        "rare_wago_written_risk": rare_wago_written_risk,
        "rare_wago_max_kanji_burden": rare_wago_max_kanji_burden,
        "rare_wago_max_written_burden": rare_wago_max_written_burden,
        "rare_wago_marked_usage_risk": rare_wago_marked_usage_risk,
        "rare_wago_missing_curriculum_risk": rare_wago_missing_curriculum_risk,
        "rare_wago_missing_curriculum_shape_risk": rare_wago_missing_curriculum_shape_risk,
        "rare_non_standard_reading_risk": rare_non_standard_reading_risk,
        "rare_wago_non_standard_reading_risk": rare_wago_non_standard_reading_risk,
        "rare_wago_obscure_written_risk": rare_wago_obscure_written_risk,
        "rare_wago_tail_risk": rare_wago_tail_risk,
        "written_wago_tail_risk": written_wago_tail_risk,
        "kango_mid_signal": kango_mid_signal,
        "sahen_kango_risk": sahen_kango_ease_gate,
        "sahen_kango_ease_gate": sahen_kango_ease_gate,
    }


def _kanji_curriculum_missing_risk(
    kanjidic2: Mapping[str, object],
    *,
    grade_proxy: float | None,
    rank_mean: float | None,
    old_jlpt_hardest: float | None,
    stroke_mean: float | None,
    visual_complexity: float | None,
) -> float | None:
    known_kanji_count = _optional_float(kanjidic2.get("known_kanji_count"))
    if known_kanji_count is None or known_kanji_count <= 0.0:
        return None
    curriculum_known_count = _optional_float(kanjidic2.get("curriculum_signal_known_count"))
    if curriculum_known_count is not None:
        return _clamp01(1.0 - (curriculum_known_count / known_kanji_count))
    has_shape_or_stroke_signal = stroke_mean is not None or visual_complexity is not None
    has_curriculum_signal = (
        grade_proxy is not None or rank_mean is not None or old_jlpt_hardest is not None
    )
    if not has_shape_or_stroke_signal:
        return None
    return 0.0 if has_curriculum_signal else 1.0


def _non_standard_reading_risk(
    row: Mapping[str, object],
    kanjidic2: Mapping[str, object],
) -> float | None:
    lemma = str(row.get("lemma") or "").strip()
    reading = _normalize_japanese_reading(row.get("reading"))
    if not lemma or not reading or not any(contains_kanji(char) for char in lemma):
        return None
    character_readings = _kanjidic2_character_reading_options(kanjidic2)
    if not character_readings:
        return None
    options_by_char: dict[str, tuple[str, ...]] = {}
    for entry in character_readings:
        kanji = str(entry.get("kanji") or "").strip()
        if not kanji:
            continue
        readings = _unique_reading_options(
            *(_string_set(entry.get("on_readings"))),
            *(_string_set(entry.get("kun_readings"))),
        )
        if readings:
            options_by_char[kanji] = readings
    if not options_by_char:
        return None
    if any(contains_kanji(char) and char not in options_by_char for char in lemma):
        return None
    return 0.0 if _reading_matches_character_options(lemma, reading, options_by_char) else 1.0


def _kanjidic2_character_reading_options(
    kanjidic2: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    raw_entries = kanjidic2.get("character_readings")
    if not isinstance(raw_entries, Iterable) or isinstance(raw_entries, (str, bytes)):
        return ()
    entries: list[Mapping[str, object]] = []
    for entry in raw_entries:
        if isinstance(entry, Mapping):
            entries.append(entry)
    return tuple(entries)


def _reading_matches_character_options(
    lemma: str,
    reading: str,
    options_by_char: Mapping[str, Sequence[str]],
) -> bool:
    positions = {0}
    for char in lemma:
        next_positions: set[int] = set()
        if contains_kanji(char):
            options = options_by_char.get(char, ())
        else:
            options = (_normalize_japanese_reading(char),)
        for position in positions:
            for option in options:
                if option and reading.startswith(option, position):
                    next_positions.add(position + len(option))
        if not next_positions:
            return False
        positions = next_positions
    return len(reading) in positions


def _unique_reading_options(*values: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            {normalized for value in values if (normalized := _normalize_japanese_reading(value))},
            key=lambda value: (len(value), value),
            reverse=True,
        )
    )


def _normalize_japanese_reading(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    chars: list[str] = []
    for char in text:
        codepoint = ord(char)
        if 0x30A1 <= codepoint <= 0x30F6:
            chars.append(chr(codepoint - 0x60))
        elif char in {"・", ".", "．", "-", "‐", "‑", "‒", "–", "—", "〜", "~", " ", "　"}:
            continue
        else:
            chars.append(char)
    return "".join(chars)


def _normalized_wtype(value: object) -> str:
    raw = str(value or "").strip()
    if raw == "和":
        return "wago"
    if raw == "漢":
        return "kango"
    if raw == "外":
        return "gairaigo"
    if raw == "混":
        return "mixed"
    if raw == "固":
        return "proper"
    return ""


def _binary_component(value: bool, *, known: bool) -> float | None:
    if not known:
        return None
    return 1.0 if value else 0.0


def _interaction_component(
    gate: float | None,
    value: float | None,
) -> float | None:
    if gate is None or value is None:
        return None
    return _clamp01(gate * value)


def _product_component(*values: float | None) -> float | None:
    result = 1.0
    for value in values:
        if value is None:
            return None
        result *= value
    return _clamp01(result)


def _sqrt_product_component(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _clamp01(math.sqrt(max(0.0, float(left)) * max(0.0, float(right))))


def _power_component(value: float | None, *, exponent: float) -> float | None:
    if value is None:
        return None
    if exponent <= 0.0:
        raise ValueError("component exponent must be positive")
    return _clamp01(max(0.0, float(value)) ** float(exponent))


def _inverse_component(value: float | None) -> float | None:
    if value is None:
        return None
    return _clamp01(1.0 - float(value))


def _gated_floor_component(
    gate: float | None,
    value: float | None,
    *,
    floor: float,
) -> float | None:
    if gate is None or value is None:
        return None
    if gate <= 0.0:
        return 0.0
    return _clamp01(max(float(floor), float(value)) * float(gate))


def _max_component(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return _clamp01(max(present))


def _min_component(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return _clamp01(min(present))


def _mean_component(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return _clamp01(sum(present) / len(present))


def _count_component(value: float | None, *, scale: float) -> float | None:
    if value is None:
        return None
    if scale <= 0.0:
        raise ValueError("component scale must be positive")
    return _clamp01(float(value) / float(scale))


def _excess_count_component(
    value: float | None,
    *,
    baseline: float,
    scale: float,
) -> float | None:
    if value is None:
        return None
    if scale <= 0.0:
        raise ValueError("component scale must be positive")
    return _clamp01(max(0.0, float(value) - float(baseline)) / float(scale))


def _rank_spread_component(value: float | None) -> float | None:
    if value is None or value <= 0.0:
        return None if value is None else 0.0
    return _clamp01(math.log1p(value) / math.log1p(DIFFICULTY_COMPONENT_MAX_RANK))


def _magnitude_spread_component(spread: float | None, maximum: float | None) -> float | None:
    if spread is None:
        return None
    if maximum is None or maximum <= 0.0:
        return 0.0
    return _clamp01(float(spread) / float(maximum))


def _signed_rank_delta_component(value: float | None) -> float | None:
    if value is None:
        return None
    return _clamp01(
        (float(value) + DIFFICULTY_COMPONENT_MAX_RANK) / (DIFFICULTY_COMPONENT_MAX_RANK * 2.0)
    )


def _clamp_optional(value: float | None) -> float | None:
    if value is None:
        return None
    return _clamp01(float(value))


def _string_set(value: object) -> frozenset[str]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, Iterable):
        values = tuple(value)
    else:
        values = ()
    return frozenset(str(item or "").strip() for item in values if str(item or "").strip())


def _lower_string_set(value: object) -> frozenset[str]:
    return frozenset(item.lower() for item in _string_set(value))


def _jmdict_source_language_codes(values: Iterable[str]) -> frozenset[str]:
    return frozenset(
        value
        for value in values
        if value
        and value != "wasei"
        and not value.startswith("text:")
        and not value.startswith("type:")
    )


def _jmdict_source_text_values(values: Iterable[str]) -> tuple[str, ...]:
    prefix = "text:"
    return tuple(
        value.removeprefix(prefix).strip()
        for value in sorted(values)
        if value.startswith(prefix) and value.removeprefix(prefix).strip()
    )


def _jmdict_english_source_frequency_ease(
    source_language_codes: Iterable[str],
    source_text_values: Sequence[str],
) -> float | None:
    codes = frozenset(source_language_codes)
    if not codes & ENGLISH_SOURCE_LANGUAGE_CODES:
        return None
    scores = [
        score
        for text in source_text_values
        if (score := _english_source_frequency_ease(text)) is not None
    ]
    return max(scores) if scores else None


def _jmdict_english_gloss_frequency_ease(gloss_values: Iterable[str]) -> float | None:
    scores = [
        score for text in gloss_values if (score := _english_gloss_frequency_ease(text)) is not None
    ]
    return max(scores) if scores else None


@lru_cache(maxsize=8192)
def _english_source_frequency_ease(text: str) -> float | None:
    return _english_frequency_ease_from_text(text, max_tokens=4)


@lru_cache(maxsize=32768)
def _english_gloss_frequency_ease(text: str) -> float | None:
    # Glosses are sense descriptions, not etymologies. Keep this deliberately weak
    # by using only short English glosses and ignoring long explanatory strings.
    return _english_frequency_ease_from_text(text, max_tokens=3)


def _english_frequency_ease_from_text(text: str, *, max_tokens: int) -> float | None:
    if _wordfreq_zipf_frequency is None:
        return None
    normalized = str(text or "").strip().lower()
    if not normalized:
        return None
    normalized = normalized.split("(", 1)[0].strip()
    tokens = SOURCE_TEXT_WORD_RE.findall(normalized)
    if not tokens:
        return None
    if len(tokens) > max_tokens:
        return None
    candidates = [" ".join(tokens), *tokens]
    scores = [
        float(_wordfreq_zipf_frequency(candidate, "en")) for candidate in candidates if candidate
    ]
    best = max(scores) if scores else 0.0
    if best <= 0.0:
        return None
    # Zipf 3 is uncommon but recognizable; Zipf 6+ is very common.
    return _clamp01((best - 3.0) / 3.0)


def _priority_rarity_multiplier(jmdict_priority_difficulty: float | None) -> float | None:
    if jmdict_priority_difficulty is None:
        return None
    return _clamp01(0.35 + 0.65 * jmdict_priority_difficulty)


def _upper_reading_rarity_multiplier(frequency_difficulty: float | None) -> float | None:
    if frequency_difficulty is None:
        return None
    # Reading irregularity is noisy for common beginner words such as 今日.
    # Treat it as an upper-band risk once frequency-side difficulty is >= 0.60.
    return _clamp01((float(frequency_difficulty) - 0.60) / 0.40)


def _difficulty_ramp(
    value: float | None,
    *,
    lower: float,
    upper: float,
) -> float | None:
    if value is None:
        return None
    if upper <= lower:
        raise ValueError("difficulty ramp upper bound must be greater than lower bound")
    return _clamp01((float(value) - lower) / (upper - lower))


def _is_plain_verb_pos(pos: str) -> bool:
    return pos.startswith("動詞") and "サ変" not in pos


def _is_adjective_pos(pos: str) -> bool:
    return pos.startswith("形容詞") or pos.startswith("形状詞")


def _is_sahen_noun_pos(pos: str) -> bool:
    return "サ変可能" in pos


def _is_common_noun_pos(pos: str) -> bool:
    return pos.startswith("名詞-普通名詞")


def _row_with_difficulty_components(row: Mapping[str, object]) -> dict[str, object]:
    cached = dict(row)
    cached[COMPONENT_CACHE_KEY] = difficulty_components(row)
    return cached


def _difficulty_components_for_row(row: Mapping[str, object]) -> Mapping[str, object]:
    cached = row.get(COMPONENT_CACHE_KEY)
    if isinstance(cached, Mapping):
        return cached
    return difficulty_components(row)


def _difficulty_components_for_variant(
    row: Mapping[str, object],
    variant: FormulaVariant,
) -> dict[str, object]:
    components = dict(_difficulty_components_for_row(row))
    if not _variant_has_component_transforms(variant):
        return components
    anchor = _jlpt_vocab_anchor_for_row(row, components, variant)
    if anchor is None:
        return components
    if variant.jlpt_vocab_curve is not None:
        components["jlpt_vocab_difficulty"] = anchor
    strength = _clamp01(float(variant.jlpt_kanji_dampening_strength))
    if strength <= 0.0:
        return components
    for name in JLPT_DAMPENED_KANJI_COMPONENTS:
        value = _optional_float(components.get(name))
        if value is None:
            continue
        components[name] = _clamp01(value - (strength * max(0.0, value - anchor)))
    return components


def _variant_has_component_transforms(variant: FormulaVariant) -> bool:
    return (
        variant.jlpt_vocab_curve is not None or float(variant.jlpt_kanji_dampening_strength) > 0.0
    )


def _jlpt_vocab_anchor_for_row(
    row: Mapping[str, object],
    components: Mapping[str, object],
    variant: FormulaVariant,
) -> float | None:
    if variant.jlpt_vocab_curve is None:
        return _optional_float(components.get("jlpt_vocab_difficulty"))
    level = _jlpt_vocab_easiest_level(row)
    if level is None:
        return None
    return _normalized_jlpt_vocab_curve(variant.jlpt_vocab_curve).get(level)


def _jlpt_vocab_easiest_level(row: Mapping[str, object]) -> int | None:
    signals = _mapping(row.get("learner_signals"))
    jlpt_vocab = _mapping(signals.get("jlpt_vocabulary"))
    level = _optional_float(jlpt_vocab.get("easiest_level"))
    if level is None:
        return None
    rounded = int(round(level))
    return rounded if rounded in DEFAULT_JLPT_VOCAB_CURVE else None


def _calibration_row_for_variant(
    row: Mapping[str, object],
    values_by_identity: Mapping[str, float],
) -> dict[str, object]:
    result = dict(row)
    identity_key = str(result.get("candidate_identity_key") or "")
    value = values_by_identity.get(identity_key)
    observed_band = _difficulty_band_for_value(value)
    expected_band = str(result.get("expected_difficulty_band") or "").strip()
    result["observed_current_difficulty_proxy"] = (
        round(float(value), 6) if value is not None else None
    )
    result["difficulty_absolute_error"] = _difficulty_absolute_error(
        result.get("expected_learner_difficulty"),
        value,
    )
    result["observed_difficulty_band"] = observed_band
    if not expected_band:
        result["difficulty_status"] = "not_labeled"
    elif not observed_band:
        result["difficulty_status"] = "missing"
    elif observed_band == expected_band:
        result["difficulty_status"] = "match"
    else:
        result["difficulty_status"] = "mismatch"
    return result


def _success_metrics_for_calibration(
    rows: Sequence[Mapping[str, object]],
    *,
    calibration_metrics: Mapping[str, object],
) -> dict[str, object]:
    numeric_rows = _numeric_calibration_rows(rows)
    difficulty_bucket = _mapping(calibration_metrics.get("difficulty_bucket"))
    difficulty_value = _mapping(calibration_metrics.get("difficulty_value"))
    default_decision = _mapping(calibration_metrics.get("default_vocab_decision"))

    pairwise_order = _pairwise_order_metrics(numeric_rows)
    rank_correlation = _rank_correlation_metrics(numeric_rows)
    beginner_core = _segment_threshold_metrics(
        numeric_rows,
        segment_id="beginner_core",
        expected_max=BEGINNER_CORE_MAX,
        observed_ceiling=BEGINNER_CORE_OBSERVED_CEILING,
    )
    beginner_broad = _segment_threshold_metrics(
        numeric_rows,
        segment_id="beginner_broad",
        expected_max=BEGINNER_BROAD_MAX,
        observed_ceiling=BEGINNER_BROAD_OBSERVED_CEILING,
    )
    upper_tail = _segment_threshold_metrics(
        numeric_rows,
        segment_id="upper_tail",
        expected_min=UPPER_TAIL_MIN,
        observed_floor=UPPER_TAIL_OBSERVED_FLOOR,
    )
    high_tail = _segment_threshold_metrics(
        numeric_rows,
        segment_id="high_tail",
        expected_min=HIGH_TAIL_MIN,
        observed_floor=HIGH_TAIL_OBSERVED_FLOOR,
    )
    separation = _tail_separation_metrics(numeric_rows)
    scores = _success_score_summary(
        difficulty_bucket=difficulty_bucket,
        difficulty_value=difficulty_value,
        default_decision=default_decision,
        pairwise_order=pairwise_order,
        rank_correlation=rank_correlation,
        beginner_core=beginner_core,
        beginner_broad=beginner_broad,
        upper_tail=upper_tail,
        high_tail=high_tail,
        separation=separation,
    )
    return {
        "metric_notes": {
            "pairwise_min_expected_gap": PAIRWISE_MIN_EXPECTED_GAP,
            "pairwise_tie_tolerance": PAIRWISE_TIE_TOLERANCE,
            "beginner_core": (
                f"expected<={BEGINNER_CORE_MAX:.2f}, observed<={BEGINNER_CORE_OBSERVED_CEILING:.2f}"
            ),
            "beginner_broad": (
                f"expected<={BEGINNER_BROAD_MAX:.2f}, "
                f"observed<={BEGINNER_BROAD_OBSERVED_CEILING:.2f}"
            ),
            "upper_tail": (
                f"expected>={UPPER_TAIL_MIN:.2f}, observed>={UPPER_TAIL_OBSERVED_FLOOR:.2f}"
            ),
            "high_tail": (
                f"expected>={HIGH_TAIL_MIN:.2f}, observed>={HIGH_TAIL_OBSERVED_FLOOR:.2f}"
            ),
        },
        "scores": scores,
        "pairwise_order": pairwise_order,
        "rank_correlation": rank_correlation,
        "segments": {
            "beginner_core": beginner_core,
            "beginner_broad": beginner_broad,
            "upper_tail": upper_tail,
            "high_tail": high_tail,
        },
        "separation": separation,
    }


def _numeric_calibration_rows(
    rows: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    numeric_rows: list[Mapping[str, object]] = []
    for row in rows:
        if row.get("status") == "missing":
            continue
        expected = _optional_float(row.get("expected_learner_difficulty"))
        observed = _optional_float(row.get("observed_current_difficulty_proxy"))
        if expected is None or observed is None:
            continue
        numeric_rows.append(row)
    return numeric_rows


def _pairwise_order_metrics(
    rows: Sequence[Mapping[str, object]],
    *,
    min_expected_gap: float = PAIRWISE_MIN_EXPECTED_GAP,
    tie_tolerance: float = PAIRWISE_TIE_TOLERANCE,
) -> dict[str, object]:
    comparable_count = 0
    correct_count = 0
    tie_count = 0
    wrong_count = 0
    wrong_examples: list[dict[str, object]] = []
    for left_index, left in enumerate(rows):
        left_expected = _optional_float(left.get("expected_learner_difficulty"))
        left_observed = _optional_float(left.get("observed_current_difficulty_proxy"))
        if left_expected is None or left_observed is None:
            continue
        for right in rows[left_index + 1 :]:
            right_expected = _optional_float(right.get("expected_learner_difficulty"))
            right_observed = _optional_float(right.get("observed_current_difficulty_proxy"))
            if right_expected is None or right_observed is None:
                continue
            expected_gap = right_expected - left_expected
            if abs(expected_gap) < min_expected_gap:
                continue
            comparable_count += 1
            observed_gap = right_observed - left_observed
            if abs(observed_gap) <= tie_tolerance:
                tie_count += 1
                continue
            expected_sign = 1 if expected_gap > 0 else -1
            observed_sign = 1 if observed_gap > 0 else -1
            if observed_sign == expected_sign:
                correct_count += 1
            else:
                wrong_count += 1
                if len(wrong_examples) < 20:
                    easier = left if expected_sign > 0 else right
                    harder = right if expected_sign > 0 else left
                    wrong_examples.append(
                        {
                            "expected_easier": _calibration_label(easier),
                            "expected_harder": _calibration_label(harder),
                            "expected_gap": _rounded(abs(expected_gap)),
                            "observed_gap": _rounded(
                                (
                                    _optional_float(harder.get("observed_current_difficulty_proxy"))
                                    or 0.0
                                )
                                - (
                                    _optional_float(easier.get("observed_current_difficulty_proxy"))
                                    or 0.0
                                )
                            ),
                        }
                    )
    return {
        "comparable_count": comparable_count,
        "correct_count": correct_count,
        "tie_count": tie_count,
        "wrong_count": wrong_count,
        "accuracy": _rounded(_ratio_or_none(correct_count + (0.5 * tie_count), comparable_count)),
        "strict_accuracy": _rounded(_ratio_or_none(correct_count, comparable_count)),
        "wrong_examples": wrong_examples,
    }


def _rank_correlation_metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    expected_values: list[float] = []
    observed_values: list[float] = []
    for row in rows:
        expected = _optional_float(row.get("expected_learner_difficulty"))
        observed = _optional_float(row.get("observed_current_difficulty_proxy"))
        if expected is None or observed is None:
            continue
        expected_values.append(expected)
        observed_values.append(observed)
    spearman = _spearman_correlation(expected_values, observed_values)
    pearson = _pearson_correlation(expected_values, observed_values)
    return {
        "evaluated_count": len(expected_values),
        "spearman": _rounded(spearman),
        "pearson": _rounded(pearson),
    }


def _segment_threshold_metrics(
    rows: Sequence[Mapping[str, object]],
    *,
    segment_id: str,
    expected_min: float | None = None,
    expected_max: float | None = None,
    observed_floor: float | None = None,
    observed_ceiling: float | None = None,
) -> dict[str, object]:
    segment_rows: list[Mapping[str, object]] = []
    for row in rows:
        expected = _optional_float(row.get("expected_learner_difficulty"))
        if expected is None:
            continue
        if expected_min is not None and expected < expected_min:
            continue
        if expected_max is not None and expected > expected_max:
            continue
        segment_rows.append(row)

    pass_count = 0
    misses: list[dict[str, object]] = []
    errors: list[float] = []
    observed_values: list[float] = []
    for row in segment_rows:
        observed = _optional_float(row.get("observed_current_difficulty_proxy"))
        expected = _optional_float(row.get("expected_learner_difficulty"))
        if observed is None or expected is None:
            continue
        observed_values.append(observed)
        errors.append(abs(observed - expected))
        floor_ok = observed_floor is None or observed >= observed_floor
        ceiling_ok = observed_ceiling is None or observed <= observed_ceiling
        if floor_ok and ceiling_ok:
            pass_count += 1
        elif len(misses) < 20:
            misses.append(
                {
                    "lemma": row.get("lemma"),
                    "reading": row.get("reading"),
                    "expected_learner_difficulty": _rounded(expected),
                    "observed_current_difficulty_proxy": _rounded(observed),
                }
            )
    return {
        "segment_id": segment_id,
        "expected_min": expected_min,
        "expected_max": expected_max,
        "observed_floor": observed_floor,
        "observed_ceiling": observed_ceiling,
        "count": len(segment_rows),
        "pass_count": pass_count,
        "pass_rate": _rounded(_ratio_or_none(pass_count, len(segment_rows))),
        "mae": _rounded(_mean(errors)),
        "observed_min": _rounded(min(observed_values) if observed_values else None),
        "observed_max": _rounded(max(observed_values) if observed_values else None),
        "observed_avg": _rounded(_mean(observed_values)),
        "misses": misses,
    }


def _tail_separation_metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    beginner_values = [
        observed
        for row in rows
        for expected in [_optional_float(row.get("expected_learner_difficulty"))]
        for observed in [_optional_float(row.get("observed_current_difficulty_proxy"))]
        if expected is not None and observed is not None and expected <= BEGINNER_CORE_MAX
    ]
    high_tail_values = [
        observed
        for row in rows
        for expected in [_optional_float(row.get("expected_learner_difficulty"))]
        for observed in [_optional_float(row.get("observed_current_difficulty_proxy"))]
        if expected is not None and observed is not None and expected >= HIGH_TAIL_MIN
    ]
    beginner_avg = _mean(beginner_values)
    high_tail_avg = _mean(high_tail_values)
    mean_gap = (
        high_tail_avg - beginner_avg
        if high_tail_avg is not None and beginner_avg is not None
        else None
    )
    minmax_gap = (
        min(high_tail_values) - max(beginner_values)
        if high_tail_values and beginner_values
        else None
    )
    return {
        "beginner_count": len(beginner_values),
        "high_tail_count": len(high_tail_values),
        "beginner_observed_avg": _rounded(beginner_avg),
        "high_tail_observed_avg": _rounded(high_tail_avg),
        "mean_gap": _rounded(mean_gap),
        "minmax_gap": _rounded(minmax_gap),
    }


def _success_score_summary(
    *,
    difficulty_bucket: Mapping[str, object],
    difficulty_value: Mapping[str, object],
    default_decision: Mapping[str, object],
    pairwise_order: Mapping[str, object],
    rank_correlation: Mapping[str, object],
    beginner_core: Mapping[str, object],
    beginner_broad: Mapping[str, object],
    upper_tail: Mapping[str, object],
    high_tail: Mapping[str, object],
    separation: Mapping[str, object],
) -> dict[str, object]:
    numeric_mae = _optional_float(difficulty_value.get("mae"))
    rank_score = _correlation_to_score(_optional_float(rank_correlation.get("spearman")))
    separation_gap = _optional_float(separation.get("mean_gap"))
    scores = {
        "numeric_mae_score": _rounded(_score_from_mae(numeric_mae)),
        "bucket_accuracy_score": _rounded(_optional_float(difficulty_bucket.get("accuracy"))),
        "pairwise_order_score": _rounded(_optional_float(pairwise_order.get("accuracy"))),
        "rank_correlation_score": _rounded(rank_score),
        "beginner_core_score": _rounded(_optional_float(beginner_core.get("pass_rate"))),
        "beginner_broad_score": _rounded(_optional_float(beginner_broad.get("pass_rate"))),
        "upper_tail_score": _rounded(_optional_float(upper_tail.get("pass_rate"))),
        "high_tail_score": _rounded(_optional_float(high_tail.get("pass_rate"))),
        "tail_separation_score": _rounded(
            _clamp01(separation_gap / 0.70) if separation_gap is not None else None
        ),
        "default_decision_score": _rounded(_optional_float(default_decision.get("accuracy"))),
    }
    balanced_score = _weighted_average(
        (
            (scores["numeric_mae_score"], 0.16),
            (scores["bucket_accuracy_score"], 0.12),
            (scores["pairwise_order_score"], 0.20),
            (scores["rank_correlation_score"], 0.10),
            (scores["beginner_core_score"], 0.12),
            (scores["beginner_broad_score"], 0.08),
            (scores["upper_tail_score"], 0.10),
            (scores["high_tail_score"], 0.06),
            (scores["tail_separation_score"], 0.03),
            (scores["default_decision_score"], 0.03),
        )
    )
    return {
        **scores,
        "balanced_score": _rounded(balanced_score),
    }


def _spearman_correlation(
    expected_values: Sequence[float],
    observed_values: Sequence[float],
) -> float | None:
    if len(expected_values) != len(observed_values) or len(expected_values) < 2:
        return None
    return _pearson_correlation(_ranks(expected_values), _ranks(observed_values))


def _pearson_correlation(
    left_values: Sequence[float],
    right_values: Sequence[float],
) -> float | None:
    if len(left_values) != len(right_values) or len(left_values) < 2:
        return None
    left_mean = _mean(left_values)
    right_mean = _mean(right_values)
    if left_mean is None or right_mean is None:
        return None
    left_centered = [value - left_mean for value in left_values]
    right_centered = [value - right_mean for value in right_values]
    numerator = sum(left * right for left, right in zip(left_centered, right_centered))
    left_norm = math.sqrt(sum(value * value for value in left_centered))
    right_norm = math.sqrt(sum(value * value for value in right_centered))
    if left_norm <= 0.0 or right_norm <= 0.0:
        return None
    return numerator / (left_norm * right_norm)


def _ranks(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average_rank = ((index + 1) + end) / 2.0
        for original_index, _value in indexed[index:end]:
            ranks[original_index] = average_rank
        index = end
    return ranks


def _score_from_mae(value: float | None) -> float | None:
    if value is None:
        return None
    return _clamp01(1.0 - value)


def _correlation_to_score(value: float | None) -> float | None:
    if value is None:
        return None
    return _clamp01((value + 1.0) / 2.0)


def _weighted_average(values_and_weights: Sequence[tuple[object, float]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for value, weight in values_and_weights:
        parsed = _optional_float(value)
        if parsed is None or weight <= 0.0:
            continue
        numerator += parsed * weight
        denominator += weight
    if denominator <= 0.0:
        return None
    return numerator / denominator


def _ratio_or_none(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator) / float(denominator)


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _calibration_label(row: Mapping[str, object]) -> str:
    reading = str(row.get("reading") or "").strip()
    if reading:
        return f"{row.get('lemma')} / {reading}"
    return str(row.get("lemma") or "")


def _frontier_formula_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    vocab_rows = [
        row for row in rows if str(row.get("candidate_state") or "").strip() in VOCAB_STATES
    ]
    return {
        "difficulty_summary_all": _difficulty_summary(rows, key="variant_difficulty"),
        "difficulty_summary_vocab": _difficulty_summary(vocab_rows, key="variant_difficulty"),
        "band_counts_all": _band_counts(rows),
        "band_counts_vocab": _band_counts(vocab_rows),
    }


def _proficiency_window(
    rows: Sequence[Mapping[str, object]],
    *,
    proficiency: float,
    window_size: int,
    example_limit: int,
) -> dict[str, object]:
    target = _proficiency_target(proficiency)
    vocab_rows = [
        row
        for row in rows
        if str(row.get("candidate_state") or "").strip() in VOCAB_STATES
        and _optional_float(row.get("variant_difficulty")) is not None
    ]
    ordered = sorted(
        vocab_rows,
        key=lambda row: (
            abs(float(row.get("variant_difficulty") or 0.0) - target),
            float(row.get("core_rank") or 0.0),
            str(row.get("lemma") or ""),
        ),
    )
    window = ordered[: max(1, int(window_size))]
    examples = [
        {
            "lemma": row.get("lemma"),
            "reading": row.get("reading"),
            "pos": row.get("pos"),
            "difficulty": _rounded(row.get("variant_difficulty")),
            "frequency_difficulty": row.get("frequency_difficulty_proxy"),
            "current_difficulty": row.get("current_difficulty_proxy"),
            "candidate_state": row.get("candidate_state"),
            "problem_class": row.get("problem_class"),
            "learner_signal_sources": row.get("learner_signal_sources"),
        }
        for row in window[: max(1, int(example_limit))]
    ]
    return {
        "proficiency": round(float(proficiency), 4),
        "target": round(float(target), 6),
        "window_size": len(window),
        "difficulty_summary": _difficulty_summary(window, key="variant_difficulty"),
        "band_counts": _band_counts(window),
        "problem_class_counts": _counts(row.get("problem_class") for row in window),
        "examples": examples,
    }


def _signal_coverage(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    source_counts: Counter[str] = Counter()
    component_counts: Counter[str] = Counter()
    for row in rows:
        for source in row.get("learner_signal_sources") or ():
            source_counts[str(source)] += 1
        for component, value in _difficulty_components_for_row(row).items():
            if value is not None:
                component_counts[component] += 1
    return {
        "row_count": len(rows),
        "source_counts": dict(sorted(source_counts.items())),
        "component_counts": dict(sorted(component_counts.items())),
    }


def _compact_trace_payload(
    *,
    records: Sequence[Mapping[str, object]],
    calibration_rows: Sequence[Mapping[str, object]],
    score_normalization: str,
    target_band_weights: Sequence[float],
    band_width: float,
    normalization_population_count: int | None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "trace_kind": "learner_difficulty_calibration_only_variant_trace",
        "score_normalization": score_normalization,
        "normalization_curve_id": (
            TARGET_CURVE_ID if score_normalization == "target_curve" else None
        ),
        "normalization_population_count": normalization_population_count,
        "target_band_weights": [round(float(value), 8) for value in target_band_weights],
        "band_width": band_width,
        "score_keys": list(SWEEP_SCORE_KEYS),
        "calibration_rows": _compact_calibration_rows(calibration_rows),
        "variant_records": [dict(record) for record in records],
    }


def _calibration_matrix_payload(
    *,
    records: Sequence[Mapping[str, object]],
    calibration_rows: Sequence[Mapping[str, object]],
    matrix_values: object,
    score_normalization: str,
    target_band_weights: Sequence[float],
    band_width: float,
    normalization_population_count: int | None,
) -> dict[str, object]:
    if np is None:
        raise ValueError("NumPy is required for calibration matrix artifacts.")
    expected_values = [
        _optional_float(row.get("expected_learner_difficulty")) for row in calibration_rows
    ]
    return {
        "metadata_json": json.dumps(
            {
                "schema_version": 1,
                "generated_at": _utc_now(),
                "language_pair": PAIR,
                "matrix_kind": "learner_difficulty_calibration_predictions",
                "score_normalization": score_normalization,
                "normalization_curve_id": (
                    TARGET_CURVE_ID if score_normalization == "target_curve" else None
                ),
                "normalization_population_count": normalization_population_count,
                "target_band_weights": [round(float(value), 8) for value in target_band_weights],
                "band_width": band_width,
                "row_axis": "variant",
                "column_axis": "calibration_label",
                "missing_value": "NaN",
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        "variant_ids": _np_string_array(record.get("variant_id") for record in records),
        "variant_transforms": _np_string_array(
            json.dumps(record.get("transforms") or {}, ensure_ascii=False, sort_keys=True)
            for record in records
        ),
        "calibration_identity_keys": _np_string_array(
            row.get("candidate_identity_key") for row in calibration_rows
        ),
        "calibration_lemmas": _np_string_array(row.get("lemma") for row in calibration_rows),
        "calibration_readings": _np_string_array(
            row.get("observed_reading") or row.get("expected_reading") for row in calibration_rows
        ),
        "expected_values": np.array(  # type: ignore[union-attr]
            [np.nan if value is None else value for value in expected_values],  # type: ignore[union-attr]
            dtype=np.float32,  # type: ignore[union-attr]
        ),
        "expected_bands": _np_string_array(
            row.get("expected_difficulty_band") for row in calibration_rows
        ),
        "expected_candidate_states": _np_string_array(
            row.get("expected_candidate_state") for row in calibration_rows
        ),
        "observed_candidate_states": _np_string_array(
            row.get("observed_candidate_state") for row in calibration_rows
        ),
        "expected_presentation_modes": _np_string_array(
            row.get("expected_presentation_mode") for row in calibration_rows
        ),
        "observed_presentation_modes": _np_string_array(
            row.get("observed_presentation_mode") for row in calibration_rows
        ),
        "expected_problem_classes": _np_string_array(
            row.get("expected_problem_class") for row in calibration_rows
        ),
        "observed_problem_classes": _np_string_array(
            row.get("observed_problem_class") for row in calibration_rows
        ),
        "observed_values": matrix_values,
    }


def _component_matrix_payload(
    normalization_population_rows: Sequence[Mapping[str, object]],
    *,
    component_names: Sequence[str],
    target_band_weights: Sequence[float],
    band_width: float,
    target_curve_context: TargetCurveScoringContext | None,
) -> dict[str, object]:
    if np is None:
        raise ValueError("NumPy is required for component matrix artifacts.")
    context = target_curve_context or _build_target_curve_scoring_context(
        normalization_population_rows,
        component_names=component_names,
        target_band_weights=target_band_weights,
        band_width=band_width,
    )
    if context is None:
        raise ValueError("Could not build component matrix context.")
    return {
        "metadata_json": json.dumps(
            {
                "schema_version": 1,
                "generated_at": _utc_now(),
                "language_pair": PAIR,
                "matrix_kind": "learner_difficulty_normalization_component_matrix",
                "normalization_population": "deduped_display_vocab_rows",
                "normalization_population_count": len(normalization_population_rows),
                "target_band_weights": [round(float(value), 8) for value in target_band_weights],
                "band_width": band_width,
                "row_axis": "normalization_population_row",
                "column_axis": "difficulty_component",
                "missing_component_value": "component_present=false",
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        "component_names": _np_string_array(context.component_names),
        "component_values": np.asarray(context.component_values, dtype=np.float32),  # type: ignore[union-attr]
        "component_present": np.asarray(context.component_present, dtype=bool),  # type: ignore[union-attr]
        "current_values": np.asarray(context.current_values, dtype=np.float32),  # type: ignore[union-attr]
        "frequency_values": np.asarray(context.frequency_values, dtype=np.float32),  # type: ignore[union-attr]
        "jlpt_vocab_levels": np.asarray(context.jlpt_vocab_levels, dtype=np.float32),  # type: ignore[union-attr]
        "target_curve_positions": np.asarray(  # type: ignore[union-attr]
            context.normalized_positions,
            dtype=np.float32,  # type: ignore[union-attr]
        ),
        "dedupe_values": _np_string_array(context.dedupe_values),
        "candidate_identity_keys": _np_string_array(
            row.get("candidate_identity_key") for row in normalization_population_rows
        ),
        "lemmas": _np_string_array(row.get("lemma") for row in normalization_population_rows),
        "readings": _np_string_array(row.get("reading") for row in normalization_population_rows),
        "candidate_states": _np_string_array(
            row.get("candidate_state") for row in normalization_population_rows
        ),
        "problem_classes": _np_string_array(
            row.get("problem_class") for row in normalization_population_rows
        ),
        "core_ranks": np.array(  # type: ignore[union-attr]
            [
                np.nan
                if _optional_float(row.get("core_rank")) is None
                else float(_optional_float(row.get("core_rank")) or 0.0)
                for row in normalization_population_rows
            ],
            dtype=np.float32,  # type: ignore[union-attr]
        ),
    }


def _compact_calibration_rows(
    calibration_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "candidate_identity_key": row.get("candidate_identity_key"),
            "lemma": row.get("lemma"),
            "reading": row.get("observed_reading") or row.get("expected_reading"),
            "expected_learner_difficulty": row.get("expected_learner_difficulty"),
            "expected_difficulty_band": row.get("expected_difficulty_band"),
            "expected_candidate_state": row.get("expected_candidate_state"),
            "observed_candidate_state": row.get("observed_candidate_state"),
            "expected_presentation_mode": row.get("expected_presentation_mode"),
            "observed_presentation_mode": row.get("observed_presentation_mode"),
            "expected_problem_class": row.get("expected_problem_class"),
            "observed_problem_class": row.get("observed_problem_class"),
            "status": row.get("status"),
        }
        for row in calibration_rows
    ]


def _np_string_array(values: Iterable[object]) -> object:
    if np is None:
        raise ValueError("NumPy is required for string arrays.")
    return np.array(  # type: ignore[union-attr]
        ["" if value is None else str(value) for value in values],
        dtype=str,
    )


def _write_npz_artifact(path: Path, arrays: Mapping[str, object]) -> None:
    if np is None:
        raise ValueError("NumPy is required for NPZ artifacts.")
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **dict(arrays))  # type: ignore[union-attr]


def _resolve_frequency_db(value: Path | None, frequency_packs_dir: Path) -> Path:
    if value is not None:
        return _resolve_path(value)
    resolved = default_frequency_db_path(PAIR, frequency_packs_dir=frequency_packs_dir)
    if resolved is None:
        raise FileNotFoundError("Could not resolve default en-ja frequency DB.")
    return resolved


def _resolve_tubelex_frequency_tsv(
    value: Path | None,
    frequency_packs_dir: Path,
    *,
    use_default: bool,
) -> Path | None:
    if value is not None:
        resolved = _resolve_path(value)
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        return resolved
    if not use_default:
        return None
    candidate = frequency_packs_dir / TUBELEX_DEFAULT_PACK_ID / TUBELEX_DEFAULT_FILENAME
    return candidate if candidate.is_file() else None


def _resolve_jmdict_path(value: Path | None, language_packs_dir: Path) -> Path:
    if value is not None:
        return _resolve_path(value)
    resolved = default_jmdict_path(PAIR, language_packs_dir=language_packs_dir)
    if resolved is None:
        raise FileNotFoundError("Could not resolve default en-ja JMDict path.")
    return resolved


def _resolve_kanjidic2_path(value: Path | None, language_packs_dir: Path) -> Path | None:
    if value is not None:
        return _resolve_path(value)
    resolved = default_kanjidic2_path(PAIR, language_packs_dir=language_packs_dir)
    return resolved if resolved and resolved.exists() else None


def _resolve_jmnedict_path(value: Path | None, language_packs_dir: Path) -> Path | None:
    if value is not None:
        return _resolve_path(value)
    resolved = default_jmnedict_path(PAIR, language_packs_dir=language_packs_dir)
    return resolved if resolved and resolved.exists() else None


def _resolve_kanjivg_path(value: Path | None, language_packs_dir: Path) -> Path | None:
    if value is not None:
        return _resolve_path(value)
    resolved = default_kanjivg_path(PAIR, language_packs_dir=language_packs_dir)
    return resolved if resolved and resolved.exists() else None


def _resolve_jlpt_vocabulary_path(
    value: Path | None,
    language_packs_dir: Path,
) -> Path | None:
    if value is not None:
        return _resolve_path(value)
    resolved = default_jlpt_vocabulary_path(PAIR, language_packs_dir=language_packs_dir)
    return resolved if resolved and resolved.exists() else None


def _resolve_lesson_vocabulary_path(
    value: Path | None,
    language_packs_dir: Path,
) -> Path | None:
    if value is not None:
        return _resolve_path(value)
    resolved = default_japanese_lesson_vocabulary_path(
        PAIR,
        language_packs_dir=language_packs_dir,
    )
    return resolved if resolved and resolved.exists() else None


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja Learner Difficulty Signal Sweep",
        "",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Frequency DB: `{inputs.get('frequency_db', '')}`",
        f"- TUBELEX frequency TSV: `{inputs.get('tubelex_frequency_tsv', '')}`",
        f"- JMDict: `{inputs.get('jmdict', '')}`",
        f"- JMnedict: `{inputs.get('jmnedict', '')}`",
        f"- KANJIDIC2: `{inputs.get('kanjidic2', '')}`",
        f"- KanjiVG: `{inputs.get('kanjivg', '')}`",
        f"- JLPT vocabulary: `{inputs.get('jlpt_vocabulary', '')}`",
        f"- Lesson vocabulary: `{inputs.get('lesson_vocabulary', '')}`",
        f"- Seed count: `{inputs.get('seed_count', 0)}`",
        f"- Score normalization: `{inputs.get('score_normalization', '')}`",
        f"- Normalization curve: `{inputs.get('normalization_curve_id', '')}`",
        (
            "- Normalization population: "
            f"`{inputs.get('normalization_population_count', '')}` "
            f"({inputs.get('normalization_population', '')})"
        ),
        f"- Grid signals: `{_escape(', '.join(_sequence_values(inputs.get('grid_signals'))))}`",
        f"- Grid min weights: `{_compact_counts(inputs.get('grid_min_weights'))}`",
        f"- Grid max weights: `{_compact_counts(inputs.get('grid_max_weights'))}`",
        f"- JLPT vocab curves: `{_compact_curve_list(inputs.get('jlpt_vocab_curves'))}`",
        (
            "- JLPT kanji dampening strengths: "
            f"`{_escape(', '.join(_sequence_values(inputs.get('jlpt_kanji_dampening_strengths'))))}`"
        ),
        "",
        "## Signal Coverage",
        "",
    ]
    coverage = _mapping(report.get("signal_coverage"))
    sweep_summary = _mapping(report.get("sweep_summary"))
    lines.extend(
        [
            f"- Source counts: `{_compact_counts(coverage.get('source_counts'))}`",
            f"- Component counts: `{_compact_counts(coverage.get('component_counts'))}`",
        ]
    )
    if sweep_summary:
        lines.extend(_sweep_summary_markdown(sweep_summary))
    lines.extend(
        [
            "",
            "## Formula Summary",
            "",
            (
                "| Variant | Balanced | Numeric MAE | Bucket | Pairwise | Spearman | "
                "Beginner | High tail | Default | Mismatches |"
            ),
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for variant in _mapping_rows(report.get("formula_variants")):
        metrics = _mapping(_mapping(variant.get("calibration")).get("metrics"))
        success = _mapping(_mapping(variant.get("calibration")).get("success_metrics"))
        scores = _mapping(success.get("scores"))
        rank_correlation = _mapping(success.get("rank_correlation"))
        difficulty = _mapping(metrics.get("difficulty_bucket"))
        difficulty_value = _mapping(metrics.get("difficulty_value"))
        lines.append(
            "| "
            f"`{_escape(variant.get('variant_id'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(difficulty_value.get('mae'))}` | "
            f"`{_escape(difficulty.get('accuracy'))}` | "
            f"`{_escape(scores.get('pairwise_order_score'))}` | "
            f"`{_escape(rank_correlation.get('spearman'))}` | "
            f"`{_escape(scores.get('beginner_core_score'))}` | "
            f"`{_escape(scores.get('high_tail_score'))}` | "
            f"`{_escape(scores.get('default_decision_score'))}` | "
            f"`{_escape(difficulty.get('mismatch_count'))}` |"
        )
    lines.extend(["", "## Variant Details", ""])
    for variant in _mapping_rows(report.get("formula_variants")):
        lines.extend(_variant_markdown(variant))
    return "\n".join(lines).rstrip() + "\n"


def _sweep_summary_markdown(sweep_summary: Mapping[str, object]) -> list[str]:
    lines = [
        "",
        "## Calibration-Only Sweep Summary",
        "",
        f"- Mode: `{_escape(sweep_summary.get('mode'))}`",
        f"- Score normalization: `{_escape(sweep_summary.get('score_normalization'))}`",
        f"- Normalization curve: `{_escape(sweep_summary.get('normalization_curve_id'))}`",
        (
            "- Normalization population: "
            f"`{_escape(sweep_summary.get('normalization_population_count'))}` "
            f"({_escape(sweep_summary.get('normalization_population'))})"
        ),
        f"- Evaluated variants: `{_escape(sweep_summary.get('evaluated_variant_count'))}`",
        f"- Retained detailed variants: `{_escape(sweep_summary.get('retained_variant_count'))}`",
        f"- Leaderboard limit: `{_escape(sweep_summary.get('leaderboard_limit'))}`",
        "",
        "### Leaderboards",
        "",
    ]
    leaderboards = _mapping(sweep_summary.get("leaderboards"))
    for score_key in SWEEP_SCORE_KEYS:
        rows = _mapping_rows(leaderboards.get(score_key))[:10]
        if not rows:
            continue
        lines.extend(
            [
                f"#### `{score_key}`",
                "",
                (
                    "| Rank | Variant | Score | Balanced | MAE | Bucket | Pairwise | "
                    "Beginner | High tail | Cap | Transforms | Weights |"
                ),
                (
                    "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
                    "---: | --- | --- |"
                ),
            ]
        )
        for index, row in enumerate(rows, start=1):
            lines.append(
                "| "
                f"{index} | "
                f"`{_escape(row.get('variant_id'))}` | "
                f"`{_escape(row.get('score'))}` | "
                f"`{_escape(row.get('balanced_score'))}` | "
                f"`{_escape(row.get('mae'))}` | "
                f"`{_escape(row.get('bucket_accuracy'))}` | "
                f"`{_escape(row.get('pairwise_order_score'))}` | "
                f"`{_escape(row.get('beginner_core_score'))}` | "
                f"`{_escape(row.get('high_tail_score'))}` | "
                f"`{_escape(row.get('max_shift_from_frequency'))}` | "
                f"`{_compact_transforms(row.get('transforms'))}` | "
                f"`{_compact_counts(row.get('weights'))}` |"
            )
        lines.append("")
    return lines


def _variant_markdown(variant: Mapping[str, object]) -> list[str]:
    metrics = _mapping(_mapping(variant.get("calibration")).get("metrics"))
    success = _mapping(_mapping(variant.get("calibration")).get("success_metrics"))
    scores = _mapping(success.get("scores"))
    pairwise = _mapping(success.get("pairwise_order"))
    rank_correlation = _mapping(success.get("rank_correlation"))
    segments = _mapping(success.get("segments"))
    beginner_core = _mapping(segments.get("beginner_core"))
    beginner_broad = _mapping(segments.get("beginner_broad"))
    upper_tail = _mapping(segments.get("upper_tail"))
    high_tail = _mapping(segments.get("high_tail"))
    separation = _mapping(success.get("separation"))
    difficulty = _mapping(metrics.get("difficulty_bucket"))
    difficulty_value = _mapping(metrics.get("difficulty_value"))
    lines = [
        f"### `{_escape(variant.get('variant_id'))}`",
        "",
        f"- Description: {_escape(variant.get('description'))}",
        f"- Weights: `{_compact_counts(variant.get('weights'))}`",
        f"- Max shift from frequency: `{_escape(variant.get('max_shift_from_frequency'))}`",
        f"- Transforms: `{_compact_transforms(variant.get('transforms'))}`",
        (
            "- Difficulty bucket: "
            f"`accuracy={_escape(difficulty.get('accuracy'))}, "
            f"match={_escape(difficulty.get('match_count'))}, "
            f"mismatch={_escape(difficulty.get('mismatch_count'))}, "
            f"missing={_escape(difficulty.get('missing_count'))}`"
        ),
        (
            "- Difficulty numeric error: "
            f"`mae={_escape(difficulty_value.get('mae'))}, "
            f"rmse={_escape(difficulty_value.get('rmse'))}, "
            f"within_0_10={_escape(difficulty_value.get('within_0_10'))} / "
            f"{_escape(difficulty_value.get('evaluated_count'))}`"
        ),
        (
            "- Success scores: "
            f"`balanced={_escape(scores.get('balanced_score'))}, "
            f"pairwise={_escape(scores.get('pairwise_order_score'))}, "
            f"spearman_score={_escape(scores.get('rank_correlation_score'))}, "
            f"beginner_core={_escape(scores.get('beginner_core_score'))}, "
            f"high_tail={_escape(scores.get('high_tail_score'))}, "
            f"default={_escape(scores.get('default_decision_score'))}`"
        ),
        (
            "- Pairwise order: "
            f"`accuracy={_escape(pairwise.get('accuracy'))}, "
            f"strict={_escape(pairwise.get('strict_accuracy'))}, "
            f"correct={_escape(pairwise.get('correct_count'))}, "
            f"ties={_escape(pairwise.get('tie_count'))}, "
            f"wrong={_escape(pairwise.get('wrong_count'))}, "
            f"comparable={_escape(pairwise.get('comparable_count'))}`"
        ),
        (
            "- Rank correlation: "
            f"`spearman={_escape(rank_correlation.get('spearman'))}, "
            f"pearson={_escape(rank_correlation.get('pearson'))}`"
        ),
        (
            "- Segment checks: "
            f"`beginner_core={_escape(beginner_core.get('pass_count'))}/"
            f"{_escape(beginner_core.get('count'))}, "
            f"beginner_broad={_escape(beginner_broad.get('pass_count'))}/"
            f"{_escape(beginner_broad.get('count'))}, "
            f"upper_tail={_escape(upper_tail.get('pass_count'))}/"
            f"{_escape(upper_tail.get('count'))}, "
            f"high_tail={_escape(high_tail.get('pass_count'))}/"
            f"{_escape(high_tail.get('count'))}`"
        ),
        (
            "- Beginner/high-tail separation: "
            f"`mean_gap={_escape(separation.get('mean_gap'))}, "
            f"minmax_gap={_escape(separation.get('minmax_gap'))}`"
        ),
    ]
    mismatches = _mapping_rows(_mapping(variant.get("calibration")).get("difficulty_mismatches"))
    if mismatches:
        mismatch_text = ", ".join(
            (
                f"{row.get('lemma')} "
                f"({row.get('expected_difficulty_band')}->{row.get('observed_difficulty_band')})"
            )
            for row in mismatches[:12]
        )
        lines.append(f"- Difficulty mismatches: {mismatch_text}")
    lines.extend(["", "Proficiency windows:", ""])
    for window in _mapping_rows(variant.get("proficiency_windows")):
        summary = _mapping(window.get("difficulty_summary"))
        examples = ", ".join(
            str(row.get("lemma") or "")
            for row in _mapping_rows(window.get("examples"))[:8]
            if row.get("lemma")
        )
        lines.append(
            "- "
            f"`p={window.get('proficiency')}` target `{window.get('target')}` "
            f"avg `{summary.get('avg')}` examples: {examples}"
        )
    lines.append("")
    return lines


def _rank_difficulty(rank_mean: float | None) -> float | None:
    if rank_mean is None or rank_mean <= 0.0:
        return None
    return _clamp01(math.log1p(rank_mean) / math.log1p(DIFFICULTY_COMPONENT_MAX_RANK))


def _old_jlpt_difficulty(level: float | None) -> float | None:
    if level is None:
        return None
    rounded = int(round(float(level)))
    mapping = {4: 0.25, 3: 0.45, 2: 0.70, 1: 0.90}
    return mapping.get(rounded)


def _stroke_difficulty(stroke_mean: float | None) -> float | None:
    if stroke_mean is None:
        return None
    return _clamp01((float(stroke_mean) - 2.0) / 20.0)


def _proficiency_target(proficiency: float) -> float:
    return _clamp01(0.20 + (0.72 * float(proficiency)))


def _band_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return _counts(_difficulty_band_for_value(row.get("variant_difficulty")) for row in rows)


def _counts(values: object) -> dict[str, int]:
    counter: Counter[str] = Counter()
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
        return {}
    for value in values:
        key = str(value or "").strip() or "(blank)"
        counter[key] += 1
    return dict(sorted(counter.items()))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence_values(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        return []
    return [str(item) for item in value]


def _optional_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _rounded(value: object) -> float | None:
    parsed = _optional_float(value)
    return round(parsed, 6) if parsed is not None else None


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _jlpt_vocab_curves_from_args(
    args: argparse.Namespace,
) -> tuple[Mapping[int, float] | None, ...]:
    if not bool(args.jlpt_vocab_curve_grid):
        return (None,)
    curves: list[Mapping[int, float]] = []
    for n5 in _parse_float_values_csv(args.jlpt_vocab_n5_values, (DEFAULT_JLPT_VOCAB_CURVE[5],)):
        for n4 in _parse_float_values_csv(
            args.jlpt_vocab_n4_values, (DEFAULT_JLPT_VOCAB_CURVE[4],)
        ):
            for n3 in _parse_float_values_csv(
                args.jlpt_vocab_n3_values, (DEFAULT_JLPT_VOCAB_CURVE[3],)
            ):
                for n2 in _parse_float_values_csv(
                    args.jlpt_vocab_n2_values, (DEFAULT_JLPT_VOCAB_CURVE[2],)
                ):
                    for n1 in _parse_float_values_csv(
                        args.jlpt_vocab_n1_values, (DEFAULT_JLPT_VOCAB_CURVE[1],)
                    ):
                        curve = _normalized_jlpt_vocab_curve({5: n5, 4: n4, 3: n3, 2: n2, 1: n1})
                        if _is_monotonic_jlpt_vocab_curve(curve):
                            curves.append(curve)
    if not curves:
        raise ValueError("--jlpt-vocab-curve-grid produced no monotonic JLPT curves.")
    return tuple(_dedupe_jlpt_vocab_curves(curves))


def _parse_float_values_csv(value: str, default: Sequence[float]) -> tuple[float, ...]:
    parsed = []
    for item in str(value or "").split(","):
        text = item.strip()
        if not text:
            continue
        parsed.append(_clamp01(float(text)))
    return tuple(parsed) or tuple(_clamp01(float(item)) for item in default)


def _normalized_jlpt_vocab_curve(curve: Mapping[int, float] | None) -> dict[int, float]:
    source = curve or DEFAULT_JLPT_VOCAB_CURVE
    return {
        level: _clamp01(float(source.get(level, DEFAULT_JLPT_VOCAB_CURVE[level])))
        for level in (5, 4, 3, 2, 1)
    }


def _is_monotonic_jlpt_vocab_curve(curve: Mapping[int, float]) -> bool:
    values = [float(curve[level]) for level in (5, 4, 3, 2, 1)]
    return all(left <= right for left, right in zip(values, values[1:]))


def _dedupe_jlpt_vocab_curves(
    curves: Sequence[Mapping[int, float]],
) -> tuple[Mapping[int, float], ...]:
    seen: set[tuple[float, ...]] = set()
    deduped: list[Mapping[int, float]] = []
    for curve in curves:
        key = tuple(round(float(curve[level]), 6) for level in (5, 4, 3, 2, 1))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(curve)
    return tuple(deduped)


def _jlpt_curve_id(curve: Mapping[int, float]) -> str:
    return "_".join(
        f"n{level}_{int(round(float(curve[level]) * 100)):02d}" for level in (5, 4, 3, 2, 1)
    )


def _jlpt_curve_json(curve: Mapping[int, float] | None) -> dict[str, float] | None:
    if curve is None:
        return None
    normalized = _normalized_jlpt_vocab_curve(curve)
    return {f"N{level}": round(float(normalized[level]), 6) for level in (5, 4, 3, 2, 1)}


def _parse_float_csv(value: str) -> tuple[float, ...]:
    parsed = []
    for item in str(value or "").split(","):
        text = item.strip()
        if not text:
            continue
        parsed.append(_clamp01(float(text)))
    return tuple(parsed) or DEFAULT_PROFICIENCY_LEVELS


def _parse_signal_csv(value: str) -> tuple[str, ...]:
    signals = tuple(item.strip() for item in str(value or "").split(",") if item.strip())
    return signals or DEFAULT_GRID_SIGNALS


def _parse_grid_caps(value: str) -> tuple[float | None, ...]:
    caps: list[float | None] = []
    for item in str(value or "").split(","):
        text = item.strip().lower()
        if not text:
            continue
        if text in {"none", "null", "uncapped"}:
            caps.append(None)
            continue
        caps.append(_clamp01(float(text)))
    return tuple(caps) or DEFAULT_GRID_CAPS


def _parse_weight_mapping_csv(value: str) -> dict[str, float]:
    weights: dict[str, float] = {}
    for item in str(value or "").split(","):
        text = item.strip()
        if not text:
            continue
        if "=" not in text:
            raise ValueError(f"Expected signal=value item, got: {text}")
        signal, raw_value = text.split("=", 1)
        signal = signal.strip()
        if not signal:
            raise ValueError(f"Expected non-empty signal name in item: {text}")
        weights[signal] = _clamp01(float(raw_value.strip()))
    return weights


def _compact_counts(value: object) -> str:
    mapping = _mapping(value)
    if not mapping:
        return ""
    return ", ".join(f"{key}={mapping[key]}" for key in sorted(mapping))


def _compact_transforms(value: object) -> str:
    transforms = _mapping(value)
    if not transforms:
        return ""
    parts: list[str] = []
    curve = _mapping(transforms.get("jlpt_vocab_curve"))
    if curve:
        parts.append(f"jlpt_curve=({_compact_counts(curve)})")
    dampening = transforms.get("jlpt_kanji_dampening_strength")
    if dampening is not None:
        parts.append(f"kanji_dampen={dampening}")
    return ", ".join(parts)


def _compact_curve_list(value: object) -> str:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        return ""
    labels: list[str] = []
    items = list(value)
    for item in items[:3]:
        curve = _mapping(item)
        labels.append(_compact_counts(curve) if curve else "default")
    if len(items) > len(labels):
        labels.append(f"... +{len(items) - len(labels)}")
    return "; ".join(labels)


def _escape(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _srs_difficulty_code_paths() -> dict[str, Path]:
    return {
        "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
        "seed": CORE_ROOT / "lexishift_core" / "srs" / "seed.py",
        "candidate_classification": (
            CORE_ROOT / "lexishift_core" / "srs" / "candidate_classification.py"
        ),
        "candidate_identity": CORE_ROOT / "lexishift_core" / "srs" / "candidate_identity.py",
        "learner_difficulty": CORE_ROOT / "lexishift_core" / "srs" / "learner_difficulty.py",
        "japanese_learner_signals": (
            CORE_ROOT / "lexishift_core" / "resources" / "japanese_learner_signals.py"
        ),
        "difficulty_audit": SCRIPT_DIR / "srs_learner_difficulty_audit_en_ja.py",
        "difficulty_normalization": SCRIPT_DIR / "srs_learner_difficulty_normalization.py",
    }


if __name__ == "__main__":
    raise SystemExit(main())
