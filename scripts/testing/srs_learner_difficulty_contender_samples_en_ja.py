#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(CORE_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_frequency_db_path,
    default_jmdict_path,
    default_jmnedict_path,
    default_kanjidic2_path,
    default_kanjivg_path,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from srs_learner_difficulty_audit_en_ja import (  # noqa: E402
    PAIR,
    _dedupe_seeds,
    _difficulty_summary,
    _repo_or_home_path,
    _resolve_path,
    _seed_row,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    FormulaVariant,
    PiecewiseFormulaSection,
    VOCAB_STATES,
    _rounded,
    estimate_variant_difficulty,
    variant_difficulty_diagnostics,
)
from srs_learner_difficulty_normalization import (  # noqa: E402
    DEFAULT_BAND_WIDTH,
    DEFAULT_TARGET_BAND_WEIGHTS,
    TARGET_CURVE_ID,
    DifficultyBand,
    difficulty_bands,
    normalize_rows_by_target_curve,
    parse_band_weights_csv,
)


DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_contender_samples_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_contender_samples_en_ja_latest.md"
)
DEFAULT_SAMPLE_COUNT = 10
DEFAULT_DEDUPE_KEY = "lemma_reading"
DEDUPE_KEYS = frozenset({"identity", "lemma", "lemma_reading"})


CONTENDERS: tuple[FormulaVariant, ...] = (
    FormulaVariant(
        variant_id="current_production",
        description=(
            "Current production learner-difficulty proxy: overlay where present, "
            "otherwise frequency."
        ),
        weights={},
        use_current_value=True,
    ),
    FormulaVariant(
        variant_id="target_curve_balanced_local_best",
        description=(
            "Best balanced target-curve local 0.05 sweep contender after "
            "curriculum-band normalization."
        ),
        weights={
            "jmdict_priority": 0.05,
            "old_jlpt_kanji": 0.95,
        },
        max_shift_from_frequency=0.15,
    ),
    FormulaVariant(
        variant_id="target_curve_freq_factor_balanced_local_best",
        description=(
            "Best balanced target-curve local sweep contender with frequency forced "
            "as a real weighted factor and extended risk/shape signals enabled."
        ),
        weights={
            "frequency": 0.20,
            "jmdict_priority": 0.10,
            "jmnedict_name_risk": 0.10,
            "old_jlpt_kanji": 0.60,
        },
        max_shift_from_frequency=0.10,
    ),
    FormulaVariant(
        variant_id="target_curve_freq_factor_balanced_full_s010_best",
        description=(
            "Best balanced target-curve full 0.10 sweep contender with frequency "
            "forced as a real weighted factor across extended signals."
        ),
        weights={
            "frequency": 0.20,
            "kanji_grade": 0.10,
            "kanjivg_visual_complexity": 0.30,
            "old_jlpt_kanji": 0.10,
            "script_complexity": 0.30,
        },
    ),
    FormulaVariant(
        variant_id="target_curve_freq_factor_numeric_local_best",
        description=(
            "Best numeric-MAE target-curve local sweep contender with frequency "
            "forced as a real weighted factor."
        ),
        weights={
            "frequency": 0.20,
            "kanjivg_visual_complexity": 0.20,
            "old_jlpt_kanji": 0.40,
            "script_complexity": 0.10,
            "stroke_count": 0.10,
        },
    ),
    FormulaVariant(
        variant_id="target_curve_freq_factor_numeric_full_s010_best",
        description=(
            "Best numeric-MAE target-curve full 0.10 sweep contender with frequency "
            "forced as a real weighted factor across extended signals."
        ),
        weights={
            "frequency": 0.20,
            "kanjivg_visual_complexity": 0.50,
            "old_jlpt_kanji": 0.20,
            "script_complexity": 0.10,
        },
    ),
    FormulaVariant(
        variant_id="target_curve_freq_factor_bucket_local_best",
        description=(
            "Best bucket-accuracy target-curve local sweep contender with frequency "
            "forced as a real weighted factor."
        ),
        weights={
            "frequency": 0.20,
            "jmdict_priority": 0.10,
            "jmnedict_name_risk": 0.20,
            "old_jlpt_kanji": 0.50,
        },
    ),
    FormulaVariant(
        variant_id="target_curve_freq_factor_pairwise_full_s010_best",
        description=(
            "Best pairwise-order target-curve full 0.10 sweep contender with "
            "frequency forced as a real weighted factor across extended signals."
        ),
        weights={
            "frequency": 0.30,
            "kanji_grade": 0.10,
            "kanjivg_visual_complexity": 0.10,
            "old_jlpt_kanji": 0.40,
            "script_complexity": 0.10,
        },
        max_shift_from_frequency=0.15,
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
                    "jmnedict_name_risk": 0.20,
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
    FormulaVariant(
        variant_id="target_curve_bucket_local_best",
        description=("Best bucket-accuracy target-curve local 0.05 sweep contender."),
        weights={
            "frequency": 0.05,
            "jmdict_priority": 0.05,
            "kanji_grade": 0.10,
            "old_jlpt_kanji": 0.80,
        },
    ),
    FormulaVariant(
        variant_id="target_curve_pairwise_local_best",
        description=("Best pairwise-order target-curve local 0.05 sweep contender."),
        weights={
            "frequency": 0.10,
            "old_jlpt_kanji": 0.90,
        },
        max_shift_from_frequency=0.10,
    ),
    FormulaVariant(
        variant_id="balanced_local_best",
        description="Best balanced local 0.05 sweep contender.",
        weights={
            "frequency": 0.25,
            "jmdict_priority": 0.60,
            "kanjivg_visual_complexity": 0.05,
            "old_jlpt_kanji": 0.10,
        },
    ),
    FormulaVariant(
        variant_id="mae_local_best",
        description="Best numeric-MAE local 0.05 sweep contender.",
        weights={
            "frequency": 0.20,
            "jmdict_priority": 0.15,
            "kanji_grade": 0.20,
            "kanjivg_visual_complexity": 0.05,
            "old_jlpt_kanji": 0.40,
        },
    ),
    FormulaVariant(
        variant_id="bucket_local_best",
        description="Best bucket-accuracy local 0.05 sweep contender.",
        weights={
            "frequency": 0.45,
            "jmdict_priority": 0.10,
            "kanji_grade": 0.05,
            "kanjivg_visual_complexity": 0.05,
            "old_jlpt_kanji": 0.35,
        },
        max_shift_from_frequency=0.15,
    ),
    FormulaVariant(
        variant_id="pedagogy_heavy_preset",
        description="Earlier hand-authored pedagogy-heavy preset reference.",
        weights={
            "frequency": 0.25,
            "jmdict_priority": 0.25,
            "kanji_grade": 0.25,
            "old_jlpt_kanji": 0.15,
            "stroke_count": 0.10,
        },
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Generate band-strict en-ja learner-difficulty samples for human review.")
    )
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--jmdict", type=Path)
    parser.add_argument("--jmnedict", type=Path)
    parser.add_argument("--kanjidic2", type=Path)
    parser.add_argument("--kanjivg", type=Path)
    parser.add_argument("--top-n", type=int, default=None)
    parser.add_argument("--band-width", type=float, default=DEFAULT_BAND_WIDTH)
    parser.add_argument(
        "--score-normalization",
        choices=("raw", "target_curve"),
        default="target_curve",
        help=(
            "Whether banding uses the raw formula score or a monotonic target-curve "
            "normalization. Samples always include raw_difficulty for comparison."
        ),
    )
    parser.add_argument(
        "--target-band-weights",
        default=",".join(f"{value:g}" for value in DEFAULT_TARGET_BAND_WEIGHTS),
        help="Comma-separated target band weights used when --score-normalization=target_curve.",
    )
    parser.add_argument("--sample-count", type=int, default=DEFAULT_SAMPLE_COUNT)
    parser.add_argument(
        "--dedupe-key",
        choices=sorted(DEDUPE_KEYS),
        default=DEFAULT_DEDUPE_KEY,
        help=(
            "Display-level dedupe before banding. lemma_reading keeps distinct readings "
            "such as 僕/ぼく vs 僕/しもべ separate."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        jmdict_path=args.jmdict,
        jmnedict_path=args.jmnedict,
        kanjidic2_path=args.kanjidic2,
        kanjivg_path=args.kanjivg,
        top_n=max(1, int(args.top_n)) if args.top_n is not None else None,
        band_width=float(args.band_width),
        score_normalization=str(args.score_normalization),
        target_band_weights=parse_band_weights_csv(args.target_band_weights),
        sample_count=max(1, int(args.sample_count)),
        dedupe_key=str(args.dedupe_key),
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
    frequency_db: Path | None,
    jmdict_path: Path | None,
    jmnedict_path: Path | None,
    kanjidic2_path: Path | None,
    kanjivg_path: Path | None,
    top_n: int | None,
    band_width: float,
    score_normalization: str,
    target_band_weights: Sequence[float],
    sample_count: int,
    dedupe_key: str,
) -> dict[str, object]:
    if dedupe_key not in DEDUPE_KEYS:
        raise ValueError(f"Unsupported dedupe key: {dedupe_key}")
    paths = build_helper_paths()
    resolved_frequency_db = _resolve_frequency_db(frequency_db, paths.frequency_packs_dir)
    resolved_jmdict_path = _resolve_jmdict_path(jmdict_path, paths.language_packs_dir)
    resolved_jmnedict_path = _resolve_optional_path(
        jmnedict_path,
        default_jmnedict_path(PAIR, language_packs_dir=paths.language_packs_dir),
    )
    resolved_kanjidic2_path = _resolve_optional_path(
        kanjidic2_path,
        default_kanjidic2_path(PAIR, language_packs_dir=paths.language_packs_dir),
    )
    resolved_kanjivg_path = _resolve_optional_path(
        kanjivg_path,
        default_kanjivg_path(PAIR, language_packs_dir=paths.language_packs_dir),
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
            stopwords_path=stopwords_path if stopwords_path.exists() else None,
            source_label="freq-ja-bccwj",
        ),
    )
    seed_rows = [_seed_row(seed) for seed in _dedupe_seeds(seeds)]
    vocab_seed_rows = [
        dict(row)
        for row in seed_rows
        if str(row.get("candidate_state") or "").strip() in VOCAB_STATES
    ]
    bands = difficulty_bands(band_width)
    variants = [
        _variant_report(
            variant,
            vocab_seed_rows=vocab_seed_rows,
            bands=bands,
            score_normalization=score_normalization,
            target_band_weights=target_band_weights,
            sample_count=sample_count,
            dedupe_key=dedupe_key,
        )
        for variant in CONTENDERS
    ]
    normalization_population = _normalization_population_report(
        seed_rows=seed_rows,
        vocab_seed_rows=vocab_seed_rows,
        variants=variants,
        dedupe_key=dedupe_key,
    )
    return {
        "schema_version": 3,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "methodology": {
            "sampling_mode": "band_strict",
            "score_normalization": score_normalization,
            "normalization_curve_id": (
                TARGET_CURVE_ID if score_normalization == "target_curve" else None
            ),
            "target_band_weights": [round(float(value), 8) for value in target_band_weights],
            "sample_selection": "deterministic_quantile_spread_within_band",
            "fallback_to_neighboring_bands": False,
            "dedupe_key": dedupe_key,
            "band_width": band_width,
            "sample_count_per_band": sample_count,
            "notes": [
                "Candidates are scored once per formula, optionally normalized with a monotonic target curve, deduped, partitioned into fixed absolute difficulty bands, then sampled only from their assigned band.",
                "When target-curve normalization is enabled, band counts add up to the deduped normalization population, not to the raw seed frontier.",
                "Underfilled or empty bands are reported directly; no nearest-neighbor backfill is used.",
            ],
        },
        "normalization_population": normalization_population,
        "normalization_target_band_counts": _normalization_target_band_counts(variants),
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
            "candidate_frontier": "limited" if top_n is not None else "all",
            "top_n": top_n,
            "seed_count": len(seed_rows),
            "vocab_seed_count": len(vocab_seed_rows),
        },
        "bands": [{"label": band.label, "start": band.start, "end": band.end} for band in bands],
        "variants": variants,
    }


def _normalization_population_report(
    *,
    seed_rows: Sequence[Mapping[str, object]],
    vocab_seed_rows: Sequence[Mapping[str, object]],
    variants: Sequence[Mapping[str, object]],
    dedupe_key: str,
) -> dict[str, object]:
    first_variant = _mapping(variants[0]) if variants else {}
    return {
        "scope": "deduped_display_vocab_rows",
        "description": (
            "Seed rows after vocabulary-lane filtering and display-level dedupe. "
            "Target-curve band counts add up to this population."
        ),
        "candidate_states_included": sorted(VOCAB_STATES),
        "candidate_state_counts_all_seed_rows": _counter_dict(
            str(row.get("candidate_state") or "") for row in seed_rows
        ),
        "candidate_state_counts_vocab_lane": _counter_dict(
            str(row.get("candidate_state") or "") for row in vocab_seed_rows
        ),
        "seed_count": len(seed_rows),
        "vocabulary_lane_seed_count": len(vocab_seed_rows),
        "raw_vocab_row_count": first_variant.get("raw_vocab_count"),
        "deduped_vocab_row_count": first_variant.get("deduped_vocab_count"),
        "normalization_population_count": first_variant.get("deduped_vocab_count"),
        "dedupe_key": dedupe_key,
        "target_curve_counts_add_to": "normalization_population_count",
    }


def _normalization_target_band_counts(
    variants: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    first_variant = _mapping(variants[0]) if variants else {}
    metadata = _mapping(first_variant.get("normalization_metadata"))
    return _mapping_rows(metadata.get("band_counts"))


def _counter_dict(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _variant_report(
    variant: FormulaVariant,
    *,
    vocab_seed_rows: Sequence[Mapping[str, object]],
    bands: Sequence[DifficultyBand],
    score_normalization: str,
    target_band_weights: Sequence[float],
    sample_count: int,
    dedupe_key: str,
) -> dict[str, object]:
    scored_rows = []
    for row in vocab_seed_rows:
        scored = dict(row)
        scored["raw_difficulty"] = estimate_variant_difficulty(row, variant)
        scored["difficulty"] = scored["raw_difficulty"]
        scored_rows.append(scored)
    canonical_raw_rows = _canonical_scored_rows(scored_rows, dedupe_key=dedupe_key)
    if score_normalization == "target_curve":
        canonical_rows, normalization_metadata = normalize_rows_by_target_curve(
            canonical_raw_rows,
            score_key="raw_difficulty",
            output_key="difficulty",
            band_weights=target_band_weights,
            band_width=bands[0].end - bands[0].start,
        )
        canonical_by_dedupe = {
            _dedupe_value(row, dedupe_key=dedupe_key): row for row in canonical_rows
        }
        normalized_scored_rows = []
        for row in scored_rows:
            canonical = canonical_by_dedupe.get(_dedupe_value(row, dedupe_key=dedupe_key))
            normalized = dict(row)
            if canonical is not None:
                normalized["difficulty"] = canonical.get("difficulty")
                normalized["difficulty_band"] = canonical.get("difficulty_band")
            normalized_scored_rows.append(normalized)
        scored_rows = normalized_scored_rows
    elif score_normalization == "raw":
        canonical_rows = canonical_raw_rows
        normalization_metadata = {"normalization": "raw"}
    else:
        raise ValueError(f"Unsupported score normalization: {score_normalization}")
    band_reports = [
        _band_report(
            band,
            variant=variant,
            raw_rows=scored_rows,
            canonical_rows=canonical_rows,
            sample_count=sample_count,
        )
        for band in bands
    ]
    return {
        "variant_id": variant.variant_id,
        "description": variant.description,
        "weights": dict(variant.weights),
        "piecewise_sections": _piecewise_sections_json(variant),
        "max_shift_from_frequency": variant.max_shift_from_frequency,
        "raw_vocab_count": len(scored_rows),
        "deduped_vocab_count": len(canonical_rows),
        "score_normalization": score_normalization,
        "normalization_metadata": normalization_metadata,
        "difficulty_summary_raw": _difficulty_summary(scored_rows, key="difficulty"),
        "difficulty_summary_deduped": _difficulty_summary(canonical_rows, key="difficulty"),
        "raw_formula_summary_deduped": _difficulty_summary(canonical_rows, key="raw_difficulty"),
        "bands": band_reports,
    }


def _band_report(
    band: DifficultyBand,
    *,
    variant: FormulaVariant,
    raw_rows: Sequence[Mapping[str, object]],
    canonical_rows: Sequence[Mapping[str, object]],
    sample_count: int,
) -> dict[str, object]:
    raw_band_rows = [row for row in raw_rows if _in_band(row.get("difficulty"), band)]
    canonical_band_rows = [row for row in canonical_rows if _in_band(row.get("difficulty"), band)]
    samples = _sample_band_rows(canonical_band_rows, sample_count=sample_count)
    midpoint = (band.start + band.end) / 2.0
    return {
        "label": band.label,
        "start": band.start,
        "end": band.end,
        "raw_count": len(raw_band_rows),
        "unique_count": len(canonical_band_rows),
        "sample_count": len(samples),
        "underfilled": len(canonical_band_rows) < sample_count,
        "difficulty_summary": _difficulty_summary(canonical_band_rows, key="difficulty"),
        "samples": [_sample_row(row, variant=variant, band_midpoint=midpoint) for row in samples],
    }


def _canonical_scored_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    dedupe_key: str,
) -> list[dict[str, object]]:
    if dedupe_key == "identity":
        return [dict(row) for row in rows]
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[_dedupe_value(row, dedupe_key=dedupe_key)].append(row)
    canonical = [dict(sorted(group, key=_canonical_row_sort_key)[0]) for group in grouped.values()]
    return sorted(canonical, key=_sample_sort_key)


def _sample_band_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_count: int,
) -> list[Mapping[str, object]]:
    ordered = sorted(rows, key=_sample_sort_key)
    if len(ordered) <= sample_count:
        return ordered
    selected = []
    seen_indexes: set[int] = set()
    for index in range(sample_count):
        position = int(((index + 0.5) * len(ordered)) / sample_count)
        position = min(len(ordered) - 1, max(0, position))
        while position in seen_indexes and position + 1 < len(ordered):
            position += 1
        while position in seen_indexes and position > 0:
            position -= 1
        seen_indexes.add(position)
        selected.append(ordered[position])
    return sorted(selected, key=_sample_sort_key)


def _in_band(value: object, band: DifficultyBand) -> bool:
    parsed = _optional_float(value)
    if parsed is None:
        return False
    if band.end >= 1.0:
        return band.start <= parsed <= band.end
    return band.start <= parsed < band.end


def _sample_row(
    row: Mapping[str, object],
    *,
    variant: FormulaVariant,
    band_midpoint: float,
) -> dict[str, object]:
    difficulty = _optional_float(row.get("difficulty"))
    return {
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "candidate_state": row.get("candidate_state"),
        "problem_class": row.get("problem_class"),
        "difficulty": _rounded(difficulty),
        "delta_from_band_midpoint": (
            _rounded(abs(difficulty - band_midpoint)) if difficulty is not None else None
        ),
        "raw_difficulty": _rounded(row.get("raw_difficulty")),
        "frequency_difficulty": _rounded(row.get("frequency_difficulty_proxy")),
        "current_difficulty": _rounded(row.get("current_difficulty_proxy")),
        "candidate_identity_key": row.get("candidate_identity_key"),
        "learner_signal_sources": row.get("learner_signal_sources"),
        "difficulty_diagnostics": variant_difficulty_diagnostics(row, variant),
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


def _dedupe_value(row: Mapping[str, object], *, dedupe_key: str) -> str:
    if dedupe_key == "lemma":
        return str(row.get("lemma") or "")
    if dedupe_key == "lemma_reading":
        return f"{row.get('lemma') or ''}\t{row.get('reading') or ''}"
    if dedupe_key == "identity":
        return str(row.get("candidate_identity_key") or "")
    raise ValueError(f"Unsupported dedupe key: {dedupe_key}")


def _canonical_row_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _state_priority(row),
        _problem_priority(row),
        _optional_float(row.get("core_rank")) or float("inf"),
        str(row.get("pos") or ""),
        str(row.get("candidate_identity_key") or ""),
    )


def _sample_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _optional_float(row.get("difficulty")) or 0.0,
        _stable_hash(_dedupe_value(row, dedupe_key="lemma_reading")),
        str(row.get("lemma") or ""),
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


def _stable_hash(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def _resolve_frequency_db(value: Path | None, frequency_packs_dir: Path) -> Path:
    if value is not None:
        return _resolve_path(value)
    resolved = default_frequency_db_path(PAIR, frequency_packs_dir=frequency_packs_dir)
    if resolved is None:
        raise FileNotFoundError("Could not resolve default en-ja frequency DB.")
    return resolved


def _resolve_jmdict_path(value: Path | None, language_packs_dir: Path) -> Path:
    if value is not None:
        return _resolve_path(value)
    resolved = default_jmdict_path(PAIR, language_packs_dir=language_packs_dir)
    if resolved is None:
        raise FileNotFoundError("Could not resolve default en-ja JMDict path.")
    return resolved


def _resolve_optional_path(value: Path | None, default: Path | None) -> Path | None:
    if value is not None:
        return _resolve_path(value)
    return default if default and default.exists() else None


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    methodology = _mapping(report.get("methodology"))
    population = _mapping(report.get("normalization_population"))
    lines = [
        "# en-ja Learner Difficulty Contender Samples",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Seed count: `{_escape(inputs.get('seed_count'))}`",
        f"- Vocabulary-lane seed count: `{_escape(inputs.get('vocab_seed_count'))}`",
        (
            "- Normalization population: "
            f"`{_escape(population.get('normalization_population_count'))}` "
            f"({_escape(population.get('scope'))})"
        ),
        (
            "- Target-curve band counts add to: "
            f"`{_escape(population.get('target_curve_counts_add_to'))}`"
        ),
        f"- Sampling mode: `{_escape(methodology.get('sampling_mode'))}`",
        f"- Score normalization: `{_escape(methodology.get('score_normalization'))}`",
        f"- Normalization curve: `{_escape(methodology.get('normalization_curve_id'))}`",
        f"- Sample selection: `{_escape(methodology.get('sample_selection'))}`",
        f"- Fallback to neighboring bands: `{_escape(methodology.get('fallback_to_neighboring_bands'))}`",
        f"- Dedupe key: `{_escape(methodology.get('dedupe_key'))}`",
        f"- Band width: `{_escape(methodology.get('band_width'))}`",
        f"- Samples per band: `{_escape(methodology.get('sample_count_per_band'))}`",
        "",
        "## Methodology",
        "",
    ]
    for note in _sequence_values(methodology.get("notes")):
        lines.append(f"- {_escape(note)}")
    lines.extend(_normalization_population_markdown(population))
    target_counts = _mapping_rows(report.get("normalization_target_band_counts"))
    if target_counts:
        lines.extend(_target_band_counts_markdown(target_counts))
    lines.extend(
        [
            "",
            "## Contenders",
            "",
            (
                "| Variant | Description | Cap | Weights | Piecewise | Raw Count | "
                "Deduped Count | Avg Difficulty | Raw Formula Avg |"
            ),
            "| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for variant in _mapping_rows(report.get("variants")):
        summary = _mapping(variant.get("difficulty_summary_deduped"))
        raw_summary = _mapping(variant.get("raw_formula_summary_deduped"))
        lines.append(
            "| "
            f"`{_escape(variant.get('variant_id'))}` | "
            f"{_escape(variant.get('description'))} | "
            f"`{_escape(variant.get('max_shift_from_frequency'))}` | "
            f"`{_compact_weights(variant.get('weights'))}` | "
            f"`{_compact_piecewise_sections(variant.get('piecewise_sections'))}` | "
            f"`{_escape(variant.get('raw_vocab_count'))}` | "
            f"`{_escape(variant.get('deduped_vocab_count'))}` | "
            f"`{_escape(summary.get('avg'))}` | "
            f"`{_escape(raw_summary.get('avg'))}` |"
        )
    for variant in _mapping_rows(report.get("variants")):
        lines.extend(_variant_markdown(variant))
    return "\n".join(lines).rstrip() + "\n"


def _normalization_population_markdown(population: Mapping[str, object]) -> list[str]:
    if not population:
        return []
    return [
        "",
        "## Normalization Population",
        "",
        f"- Scope: `{_escape(population.get('scope'))}`",
        f"- Candidate states included: `{_escape(', '.join(_sequence_values(population.get('candidate_states_included'))))}`",
        f"- Raw seed rows: `{_escape(population.get('seed_count'))}`",
        f"- Vocabulary-lane seed rows: `{_escape(population.get('vocabulary_lane_seed_count'))}`",
        f"- Raw vocab rows scored per contender: `{_escape(population.get('raw_vocab_row_count'))}`",
        f"- Deduped vocab rows normalized per contender: `{_escape(population.get('deduped_vocab_row_count'))}`",
        f"- Counts add to: `{_escape(population.get('target_curve_counts_add_to'))}`",
    ]


def _target_band_counts_markdown(
    target_counts: Sequence[Mapping[str, object]],
) -> list[str]:
    lines = [
        "",
        "## Target-Curve Band Counts",
        "",
        "| Band | Target Weight | Assigned Count |",
        "| --- | ---: | ---: |",
    ]
    for row in target_counts:
        lines.append(
            "| "
            f"`{_escape(row.get('label'))}` | "
            f"`{_escape(row.get('target_weight'))}` | "
            f"`{_escape(row.get('assigned_count'))}` |"
        )
    return lines


def _variant_markdown(variant: Mapping[str, object]) -> list[str]:
    lines = [
        "",
        f"## `{_escape(variant.get('variant_id'))}`",
        "",
        f"- Weights: `{_compact_weights(variant.get('weights'))}`",
        f"- Piecewise sections: `{_compact_piecewise_sections(variant.get('piecewise_sections'))}`",
        f"- Max shift from frequency: `{_escape(variant.get('max_shift_from_frequency'))}`",
        f"- Raw vocab rows: `{_escape(variant.get('raw_vocab_count'))}`",
        f"- Deduped display rows: `{_escape(variant.get('deduped_vocab_count'))}`",
        "",
        "### Band Counts",
        "",
        "| Band | Raw Count | Deduped Count | Samples | Underfilled | Avg Difficulty |",
        "| --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for band in _mapping_rows(variant.get("bands")):
        summary = _mapping(band.get("difficulty_summary"))
        lines.append(
            "| "
            f"`{_escape(band.get('label'))}` | "
            f"`{_escape(band.get('raw_count'))}` | "
            f"`{_escape(band.get('unique_count'))}` | "
            f"`{_escape(band.get('sample_count'))}` | "
            f"`{_escape(band.get('underfilled'))}` | "
            f"`{_escape(summary.get('avg'))}` |"
        )
    lines.extend(["", "### Samples", ""])
    for band in _mapping_rows(variant.get("bands")):
        lines.extend(
            [
                f"#### Band `{_escape(band.get('label'))}`",
                "",
                (
                    f"- Raw count: `{_escape(band.get('raw_count'))}`; "
                    f"deduped count: `{_escape(band.get('unique_count'))}`; "
                    f"sample count: `{_escape(band.get('sample_count'))}`; "
                    f"underfilled: `{_escape(band.get('underfilled'))}`"
                ),
                "",
            ]
        )
        samples = _mapping_rows(band.get("samples"))
        if not samples:
            lines.extend(["No samples in this band.", ""])
            continue
        lines.extend(
            [
                (
                    "| Lemma | Reading | Difficulty | Raw | Delta | Freq | Current | "
                    "Diagnostics | State | Problem | POS |"
                ),
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
            ]
        )
        for row in samples:
            lines.append(
                "| "
                f"{_escape(row.get('lemma'))} | "
                f"{_escape(row.get('reading'))} | "
                f"`{_escape(row.get('difficulty'))}` | "
                f"`{_escape(row.get('raw_difficulty'))}` | "
                f"`{_escape(row.get('delta_from_band_midpoint'))}` | "
                f"`{_escape(row.get('frequency_difficulty'))}` | "
                f"`{_escape(row.get('current_difficulty'))}` | "
                f"{_escape(_diagnostic_summary(row.get('difficulty_diagnostics')))} | "
                f"`{_escape(row.get('candidate_state'))}` | "
                f"`{_escape(row.get('problem_class'))}` | "
                f"{_escape(row.get('pos'))} |"
            )
        lines.append("")
    return lines


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence_values(value: object) -> list[object]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        return []
    return list(value)


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


def _compact_weights(value: object) -> str:
    mapping = _mapping(value)
    if not mapping:
        return ""
    return ", ".join(f"{key}={mapping[key]}" for key in sorted(mapping))


def _compact_piecewise_sections(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return ""
    sections = []
    for row in rows:
        sections.append(
            (
                f"{row.get('section_id')}@{row.get('center')}"
                f"/r{row.get('radius')}[{_compact_weights(row.get('weights'))}]"
            )
        )
    return "; ".join(sections)


def _diagnostic_summary(value: object) -> str:
    diagnostics = _mapping(value)
    mode = str(diagnostics.get("mode") or "")
    if mode == "piecewise":
        sections = [
            section
            for section in _mapping_rows(diagnostics.get("sections"))
            if _optional_float(section.get("influence")) is not None
            and (_optional_float(section.get("influence")) or 0.0) > 0.0
        ]
        section_text = ", ".join(
            (f"{section.get('section_id')} i={section.get('influence')} v={section.get('value')}")
            for section in sorted(
                sections,
                key=lambda item: _optional_float(item.get("influence")) or 0.0,
                reverse=True,
            )
        )
        return (
            f"anchor={diagnostics.get('anchor_value')}; "
            f"{section_text}; final={diagnostics.get('final_raw_difficulty')}"
        )
    contributions = _mapping_rows(diagnostics.get("contributions"))
    top = sorted(
        contributions,
        key=lambda item: _optional_float(item.get("weighted_value")) or 0.0,
        reverse=True,
    )[:3]
    parts = [f"{item.get('component')}={item.get('weighted_value')}" for item in top]
    final = diagnostics.get("final_raw_difficulty")
    return f"{', '.join(parts)}; final={final}" if parts else f"final={final}"


def _escape(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
