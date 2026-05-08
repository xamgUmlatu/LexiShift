from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import itertools
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_difficulty_stratification_en_es import (  # noqa: E402
    FrequencyLookup,
    _optional_float,
    _repo_path,
)
from semantic_veto_heuristic_group_pilot_en_es import (  # noqa: E402
    GROUP_SPECS,
    _candidate_pool,
    _candidate_sort_key,
    _measured_triggers,
    _row_matches_spec,
)
from semantic_veto_product_quality_en_es import _as_mapping  # noqa: E402
from semantic_veto_representative_heuristic_band_sampler_en_es import (  # noqa: E402
    build_representative_heuristic_band_sampler_report,
    _cell_rows,
    _polysemy_band,
    _pos_shape,
    _rank_band,
    _representative_candidate_rows,
)
from semantic_veto_representative_target_family_construction_en_es import (  # noqa: E402
    build_representative_target_family_construction_report,
)
from semantic_veto_veto_only_probe_en_es import _mapping_rows  # noqa: E402
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_PILOT_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_group_pilot_en_es_latest.json"
DEFAULT_SAMPLE_SIZES = "4,8,16,32"
DEFAULT_SEEDS = (
    "representative_seed_v1,representative_seed_v2,representative_seed_v3,representative_seed_v4"
)
DEFAULT_CONSTRUCTION_STABILITY_SAMPLE_SIZES = "4,8,16"
DEFAULT_CONSTRUCTION_STABILITY_SEEDS = "methodology_seed_a,methodology_seed_b,methodology_seed_c"


def build_sampling_methodology_comparison_report(
    *,
    pilot_payload: Mapping[str, object],
    representative_sample_payload: Mapping[str, object],
    construction_payload: Mapping[str, object],
    source_frequency: FrequencyLookup,
    wordnet_index: WordNetIndex,
    difficulty_payload: Mapping[str, object] | None = None,
    pilot_json_path: Path | None = None,
    sample_json_path: Path | None = None,
    construction_json_path: Path | None = None,
    source_frequency_path: Path | None = None,
    wordnet_dir: Path | None = None,
    wiktionary_en_es_sqlite: Path | None = None,
    wiktionary_es_en_sqlite: Path | None = None,
    freedict_es_en_sqlite: Path | None = None,
    sample_sizes: Sequence[int] = (4, 8, 16, 32),
    seeds: Sequence[str] = (),
    construction_stability_sample_sizes: Sequence[int] = (),
    construction_stability_seeds: Sequence[str] = (),
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    difficulty_payload = difficulty_payload or {}
    measured_triggers = _measured_triggers(difficulty_payload)
    old_candidate_pool = _candidate_pool(
        source_frequency=source_frequency,
        wordnet_index=wordnet_index,
        measured_triggers=measured_triggers,
    )
    representative_candidate_rows = _representative_candidate_rows(
        source_frequency=source_frequency,
        wordnet_index=wordnet_index,
        measured_triggers=measured_triggers,
    )
    old_comparison = _old_pilot_comparison(
        pilot_payload=pilot_payload,
        candidate_pool=old_candidate_pool,
        representative_sample_payload=representative_sample_payload,
    )
    new_comparison = _new_sampler_comparison(
        representative_sample_payload=representative_sample_payload,
        construction_payload=construction_payload,
    )
    stability = _sampling_stability(
        candidate_rows=representative_candidate_rows,
        sample_sizes=sample_sizes,
        seeds=seeds,
    )
    construction_stability = _construction_stability(
        source_frequency=source_frequency,
        wordnet_index=wordnet_index,
        difficulty_payload=difficulty_payload,
        sample_sizes=construction_stability_sample_sizes,
        seeds=construction_stability_seeds,
        wiktionary_en_es_sqlite=wiktionary_en_es_sqlite,
        wiktionary_es_en_sqlite=wiktionary_es_en_sqlite,
        freedict_es_en_sqlite=freedict_es_en_sqlite,
        generated_at=generated_at,
    )
    checks = {
        "old_pilot_primary_rows_detected": old_comparison["primary_selected_trigger_count"] > 0,
        "representative_sample_rows_detected": new_comparison["sampled_trigger_count"] > 0,
        "representative_cells_cover_all_nonempty_cells": (
            new_comparison["sampled_nonempty_cell_count"] == new_comparison["nonempty_cell_count"]
        ),
        "stability_runs_cover_all_nonempty_cells": all(
            row["nonempty_cell_coverage_rate"] == 1.0 for row in stability.get("runs", [])
        ),
    }
    issues = [key for key, value in checks.items() if not value]
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "pair": "en-es",
        "status": status,
        "decision": (
            "sampling_methodology_comparison_established"
            if status == "ok"
            else "sampling_methodology_comparison_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "pilot_json": _repo_path(pilot_json_path),
            "representative_sample_json": _repo_path(sample_json_path),
            "representative_construction_json": _repo_path(construction_json_path),
            "source_frequency_path": _repo_path(source_frequency_path),
            "wordnet_dir": _repo_path(wordnet_dir),
        },
        "methodology": {
            "old_pilot_selection": (
                "six coarse rank/polysemy groups, group_size=4, sorted by source "
                "rank then descending WordNet sense/POS counts; useful as hard-case "
                "stress contrast but biased for band means"
            ),
            "representative_sampler_selection": (
                "fine source-rank x WordNet-polysemy x POS-shape cells, deterministic "
                "seeded hash order inside each cell, with sampling weights"
            ),
            "stability_scope": (
                "source-trigger sampling only. Downstream scoring sweeps cannot be "
                "rerun on the representative lane until target/shadow families and "
                "fixed scored contexts exist."
            ),
        },
        "comparison": {
            "old_heuristic_group_pilot": old_comparison,
            "representative_sampler": new_comparison,
            "delta": _delta(old_comparison=old_comparison, new_comparison=new_comparison),
        },
        "sampling_stability": stability,
        "construction_stability": construction_stability,
        "sweep_rerun_status": _sweep_rerun_status(),
        "e2e_checks": checks,
        "limitations": [
            "new_sampler_improves_source_band_representation_not_final_accuracy_by_itself",
            "target_family_construction_stability_is_coverage_not_final_scoring_accuracy",
            "old_formula_and_weight_sweeps_need_representative_case_traces_before_true_rerun",
            "equal_cell_sampling_requires_weights_for_candidate_universe_mean_estimates",
        ],
        "next_steps": [
            "Broaden or diagnose the missing_noun_or_verb_translation blocker before spending on LLM rows.",
            "After representative target/shadow families and fixed contexts exist, rerun heuristic difficulty surface, formula-shape bakeoff, formula-weight surface, and curve-guided expansion against the representative lane.",
        ],
    }


def _old_pilot_comparison(
    *,
    pilot_payload: Mapping[str, object],
    candidate_pool: Sequence[Mapping[str, object]],
    representative_sample_payload: Mapping[str, object],
) -> dict[str, object]:
    groups = _mapping_rows(pilot_payload.get("groups"))
    primary_groups = [row for row in groups if row.get("selection_mode") == "pre_outcome"]
    sentinel_groups = [row for row in groups if row.get("selection_mode") != "pre_outcome"]
    primary_rows = [row for group in primary_groups for row in _mapping_rows(group.get("triggers"))]
    sentinel_rows = [
        row for group in sentinel_groups for row in _mapping_rows(group.get("triggers"))
    ]
    nonempty_cells = _nonempty_cell_ids(representative_sample_payload)
    primary_cells = {_cell_id_for_row(row) for row in primary_rows if _cell_id_for_row(row)}
    return {
        "candidate_pool_count": int(
            _as_mapping(pilot_payload.get("summary")).get("candidate_pool_count")
            or len(candidate_pool)
        ),
        "primary_selected_trigger_count": len(primary_rows),
        "sentinel_trigger_count": len(sentinel_rows),
        "primary_group_count": len(primary_groups),
        "primary_new_cell_coverage_count": len(primary_cells & nonempty_cells),
        "primary_new_cell_coverage_rate": _ratio(
            len(primary_cells & nonempty_cells), len(nonempty_cells)
        ),
        "primary_selected_polysemy_counts": dict(
            sorted(Counter(_polysemy_band_for_public_row(row) for row in primary_rows).items())
        ),
        "primary_selected_pos_shape_counts": dict(
            sorted(Counter(_pos_shape_for_public_row(row) for row in primary_rows).items())
        ),
        "primary_group_bias": _primary_group_bias(candidate_pool=candidate_pool),
        "selection_rule": "source_rank_ascending_then_wordnet_sense_count_desc_then_pos_count_desc",
    }


def _new_sampler_comparison(
    *,
    representative_sample_payload: Mapping[str, object],
    construction_payload: Mapping[str, object],
) -> dict[str, object]:
    summary = _as_mapping(representative_sample_payload.get("summary"))
    sample_rows = _mapping_rows(representative_sample_payload.get("sampled_rows"))
    cells = _mapping_rows(representative_sample_payload.get("cells"))
    sampled_cells = {str(row.get("cell_id") or "") for row in sample_rows if row.get("cell_id")}
    nonempty_cells = {
        str(row.get("cell_id") or "") for row in cells if int(row.get("eligible_count") or 0) > 0
    }
    construction_summary = _as_mapping(construction_payload.get("summary"))
    return {
        "candidate_universe_count": int(summary.get("candidate_universe_count") or 0),
        "sampled_trigger_count": len(sample_rows),
        "cell_count": int(summary.get("cell_count") or len(cells)),
        "nonempty_cell_count": int(summary.get("nonempty_cell_count") or len(nonempty_cells)),
        "sampled_nonempty_cell_count": len(sampled_cells & nonempty_cells),
        "sampled_nonempty_cell_coverage_rate": _ratio(
            len(sampled_cells & nonempty_cells), len(nonempty_cells)
        ),
        "sample_per_cell": int(
            _as_mapping(representative_sample_payload.get("methodology")).get("sample_per_cell")
            or 0
        ),
        "weighted_estimation_available": all(
            row.get("cell_sampling_weight") for row in sample_rows
        ),
        "construction_attempt_count": int(construction_summary.get("attempted_sample_count") or 0),
        "source_ready_family_count": int(
            construction_summary.get("source_ready_family_count") or 0
        ),
        "weak_diagnostic_family_count": int(
            construction_summary.get("weak_diagnostic_family_count") or 0
        ),
        "blocked_count": int(construction_summary.get("blocked_count") or 0),
        "source_ready_rate": construction_summary.get("source_ready_rate"),
        "construction_reason_counts": dict(_as_mapping(construction_summary.get("reason_counts"))),
    }


def _delta(
    *,
    old_comparison: Mapping[str, object],
    new_comparison: Mapping[str, object],
) -> dict[str, object]:
    return {
        "sampled_trigger_multiplier_vs_old_primary": _round4(
            _safe_float(new_comparison.get("sampled_trigger_count"))
            / _safe_float(old_comparison.get("primary_selected_trigger_count"))
        ),
        "fine_cell_coverage_gain": _round4(
            _safe_float(new_comparison.get("sampled_nonempty_cell_coverage_rate"))
            - _safe_float(old_comparison.get("primary_new_cell_coverage_rate"))
        ),
        "representative_sample_removes_old_rank_sort_bias": True,
        "remaining_gap": "representative target-family/source-ready and scored-case sweeps still need rerun",
    }


def _primary_group_bias(candidate_pool: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows = []
    for spec in GROUP_SPECS:
        eligible = [row for row in candidate_pool if _row_matches_spec(row=row, spec=spec)]
        selected = sorted(eligible, key=_candidate_sort_key)[:4]
        selected_ranks = [_safe_float(row.get("source_rank")) for row in selected]
        eligible_ranks = [_safe_float(row.get("source_rank")) for row in eligible]
        rows.append(
            {
                "group_id": spec.group_id,
                "eligible_count": len(eligible),
                "selected_count": len(selected),
                "selected_share": _ratio(len(selected), len(eligible)),
                "selected_rank_min": _min(selected_ranks),
                "selected_rank_max": _max(selected_ranks),
                "selected_rank_mean": _mean(selected_ranks),
                "eligible_rank_min": _min(eligible_ranks),
                "eligible_rank_max": _max(eligible_ranks),
                "eligible_rank_mean": _mean(eligible_ranks),
            }
        )
    return rows


def _sampling_stability(
    *,
    candidate_rows: Sequence[Mapping[str, object]],
    sample_sizes: Sequence[int],
    seeds: Sequence[str],
) -> dict[str, object]:
    runs = []
    universe_counts = {
        "source_rank_band": Counter(
            str(row.get("source_rank_band") or "") for row in candidate_rows
        ),
        "polysemy_band": Counter(str(row.get("polysemy_band") or "") for row in candidate_rows),
        "pos_shape": Counter(str(row.get("pos_shape") or "") for row in candidate_rows),
    }
    nonempty_cell_count = len(
        {
            (
                str(row.get("source_rank_band") or ""),
                str(row.get("polysemy_band") or ""),
                str(row.get("pos_shape") or ""),
            )
            for row in candidate_rows
        }
    )
    for sample_per_cell in sample_sizes:
        for seed in seeds:
            cells = _cell_rows(
                candidate_rows=candidate_rows,
                sample_per_cell=max(1, int(sample_per_cell)),
                seed=seed,
            )
            sampled_rows = [
                row for cell in cells for row in _mapping_rows(cell.get("sampled_rows"))
            ]
            sampled_cells = {
                str(row.get("cell_id") or "") for row in sampled_rows if row.get("cell_id")
            }
            weighted_counts = _weighted_counts(sampled_rows)
            runs.append(
                {
                    "sample_per_cell": int(sample_per_cell),
                    "seed": seed,
                    "sampled_trigger_count": len(sampled_rows),
                    "sampled_nonempty_cell_count": len(sampled_cells),
                    "nonempty_cell_coverage_rate": _ratio(len(sampled_cells), nonempty_cell_count),
                    "weighted_rank_tvd": _tvd(
                        weighted_counts["source_rank_band"],
                        universe_counts["source_rank_band"],
                    ),
                    "weighted_polysemy_tvd": _tvd(
                        weighted_counts["polysemy_band"],
                        universe_counts["polysemy_band"],
                    ),
                    "weighted_pos_shape_tvd": _tvd(
                        weighted_counts["pos_shape"],
                        universe_counts["pos_shape"],
                    ),
                    "sample_triggers": sorted(
                        str(row.get("trigger") or "") for row in sampled_rows
                    ),
                }
            )
    by_size = []
    for sample_per_cell in sample_sizes:
        size_runs = [row for row in runs if row["sample_per_cell"] == int(sample_per_cell)]
        overlaps = [
            _jaccard(set(left["sample_triggers"]), set(right["sample_triggers"]))
            for left, right in itertools.combinations(size_runs, 2)
        ]
        by_size.append(
            {
                "sample_per_cell": int(sample_per_cell),
                "run_count": len(size_runs),
                "sampled_trigger_count_min": _min(
                    [float(row["sampled_trigger_count"]) for row in size_runs]
                ),
                "sampled_trigger_count_max": _max(
                    [float(row["sampled_trigger_count"]) for row in size_runs]
                ),
                "nonempty_cell_coverage_rate_min": _min(
                    [float(row["nonempty_cell_coverage_rate"] or 0.0) for row in size_runs]
                ),
                "nonempty_cell_coverage_rate_max": _max(
                    [float(row["nonempty_cell_coverage_rate"] or 0.0) for row in size_runs]
                ),
                "mean_pairwise_jaccard": _mean(overlaps),
                "weighted_rank_tvd_max": _max(
                    [float(row["weighted_rank_tvd"] or 0.0) for row in size_runs]
                ),
                "weighted_polysemy_tvd_max": _max(
                    [float(row["weighted_polysemy_tvd"] or 0.0) for row in size_runs]
                ),
                "weighted_pos_shape_tvd_max": _max(
                    [float(row["weighted_pos_shape_tvd"] or 0.0) for row in size_runs]
                ),
            }
        )
    for row in runs:
        row.pop("sample_triggers", None)
    return {
        "nonempty_cell_count": nonempty_cell_count,
        "seed_count": len(seeds),
        "sample_sizes": list(sample_sizes),
        "by_sample_size": by_size,
        "runs": runs,
    }


def _construction_stability(
    *,
    source_frequency: FrequencyLookup,
    wordnet_index: WordNetIndex,
    difficulty_payload: Mapping[str, object],
    sample_sizes: Sequence[int],
    seeds: Sequence[str],
    wiktionary_en_es_sqlite: Path | None,
    wiktionary_es_en_sqlite: Path | None,
    freedict_es_en_sqlite: Path | None,
    generated_at: str,
) -> dict[str, object]:
    if not sample_sizes or not seeds or wiktionary_en_es_sqlite is None:
        return {
            "status": "not_run",
            "reason": "construction_stability_inputs_not_provided",
            "by_sample_size": [],
            "runs": [],
        }
    runs = []
    for sample_per_cell in sample_sizes:
        for seed in seeds:
            sample_payload = build_representative_heuristic_band_sampler_report(
                source_frequency=source_frequency,
                wordnet_index=wordnet_index,
                difficulty_payload=difficulty_payload,
                sample_per_cell=int(sample_per_cell),
                seed=seed,
                generated_at=generated_at,
            )
            construction_payload = build_representative_target_family_construction_report(
                sample_payload=sample_payload,
                wiktionary_en_es_sqlite=wiktionary_en_es_sqlite,
                wiktionary_es_en_sqlite=wiktionary_es_en_sqlite,
                freedict_es_en_sqlite=freedict_es_en_sqlite,
                wordnet_index=wordnet_index,
                generated_at=generated_at,
            )
            summary = _as_mapping(construction_payload.get("summary"))
            runs.append(
                {
                    "sample_per_cell": int(sample_per_cell),
                    "seed": seed,
                    "attempted_sample_count": int(summary.get("attempted_sample_count") or 0),
                    "source_ready_family_count": int(summary.get("source_ready_family_count") or 0),
                    "weak_diagnostic_family_count": int(
                        summary.get("weak_diagnostic_family_count") or 0
                    ),
                    "blocked_count": int(summary.get("blocked_count") or 0),
                    "source_ready_rate": summary.get("source_ready_rate"),
                    "reason_counts": dict(_as_mapping(summary.get("reason_counts"))),
                }
            )
    by_size = []
    for sample_per_cell in sample_sizes:
        size_runs = [row for row in runs if row["sample_per_cell"] == int(sample_per_cell)]
        by_size.append(
            {
                "sample_per_cell": int(sample_per_cell),
                "run_count": len(size_runs),
                "attempted_sample_count_min": _min(
                    [float(row["attempted_sample_count"]) for row in size_runs]
                ),
                "attempted_sample_count_max": _max(
                    [float(row["attempted_sample_count"]) for row in size_runs]
                ),
                "source_ready_family_count_min": _min(
                    [float(row["source_ready_family_count"]) for row in size_runs]
                ),
                "source_ready_family_count_max": _max(
                    [float(row["source_ready_family_count"]) for row in size_runs]
                ),
                "source_ready_rate_min": _min(
                    [float(row["source_ready_rate"] or 0.0) for row in size_runs]
                ),
                "source_ready_rate_max": _max(
                    [float(row["source_ready_rate"] or 0.0) for row in size_runs]
                ),
                "source_ready_rate_mean": _mean(
                    [float(row["source_ready_rate"] or 0.0) for row in size_runs]
                ),
                "weak_diagnostic_family_count_min": _min(
                    [float(row["weak_diagnostic_family_count"]) for row in size_runs]
                ),
                "weak_diagnostic_family_count_max": _max(
                    [float(row["weak_diagnostic_family_count"]) for row in size_runs]
                ),
                "blocked_count_min": _min([float(row["blocked_count"]) for row in size_runs]),
                "blocked_count_max": _max([float(row["blocked_count"]) for row in size_runs]),
            }
        )
    return {
        "status": "ok",
        "sample_sizes": list(sample_sizes),
        "seed_count": len(seeds),
        "by_sample_size": by_size,
        "runs": runs,
    }


def _weighted_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, Counter[str]]:
    counts = {
        "source_rank_band": Counter(),
        "polysemy_band": Counter(),
        "pos_shape": Counter(),
    }
    for row in rows:
        weight = _safe_float(row.get("cell_sampling_weight"))
        counts["source_rank_band"][str(row.get("source_rank_band") or "")] += weight
        counts["polysemy_band"][str(row.get("polysemy_band") or "")] += weight
        counts["pos_shape"][str(row.get("pos_shape") or "")] += weight
    return counts


def _sweep_rerun_status() -> list[dict[str, str]]:
    return [
        {
            "sweep": "heuristic_difficulty_surface",
            "status": "blocked_until_representative_case_traces_exist",
            "reason": "The prior sweep consumes authored/scored case traces, while the representative lane currently has source-trigger and target-family coverage only.",
        },
        {
            "sweep": "formula_shape_bakeoff",
            "status": "blocked_until_representative_case_traces_exist",
            "reason": "Formula cells require observed positive/shadow/phrase outcomes; no representative scored contexts exist yet.",
        },
        {
            "sweep": "formula_weight_surface",
            "status": "blocked_until_representative_case_traces_exist",
            "reason": "Continuous weight surfaces need observed failure rates by cell, not just sampled source triggers.",
        },
        {
            "sweep": "curve_guided_expansion_plan",
            "status": "rerun_after_representative_surface_exists",
            "reason": "The current curve-guided queue came from the old authored stress lane; rerun it after representative cases are scored.",
        },
        {
            "sweep": "source_sampling_seed_scale_stability",
            "status": "rerun_now",
            "reason": "This report reruns the source sampling side for multiple sample sizes and seeds.",
        },
    ]


def _nonempty_cell_ids(payload: Mapping[str, object]) -> set[str]:
    return {
        str(row.get("cell_id") or "")
        for row in _mapping_rows(payload.get("cells"))
        if int(row.get("eligible_count") or 0) > 0 and row.get("cell_id")
    }


def _cell_id_for_row(row: Mapping[str, object]) -> str:
    rank = _optional_float(row.get("source_rank"))
    senses = int(row.get("wordnet_sense_count") or 0)
    pos_count = int(row.get("wordnet_pos_count") or 0)
    rank_band = _rank_band(float(rank or 0.0))
    polysemy_band = _polysemy_band(senses)
    pos = _pos_shape(sense_count=senses, pos_count=pos_count)
    if not rank_band or not polysemy_band or not pos:
        return ""
    return f"source_rank_band={rank_band}::polysemy_band={polysemy_band}::pos_shape={pos}"


def _polysemy_band_for_public_row(row: Mapping[str, object]) -> str:
    return _polysemy_band(int(row.get("wordnet_sense_count") or 0))


def _pos_shape_for_public_row(row: Mapping[str, object]) -> str:
    return _pos_shape(
        sense_count=int(row.get("wordnet_sense_count") or 0),
        pos_count=int(row.get("wordnet_pos_count") or 0),
    )


def _tvd(left: Counter[str], right: Counter[str]) -> float:
    left_total = sum(float(value) for value in left.values())
    right_total = sum(float(value) for value in right.values())
    if left_total <= 0 or right_total <= 0:
        return 0.0
    keys = set(left) | set(right)
    return _round4(
        0.5
        * sum(
            abs(float(left.get(key, 0.0)) / left_total - float(right.get(key, 0.0)) / right_total)
            for key in keys
        )
    )


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    return _round4(len(left & right) / len(left | right))


def _safe_float(value: object) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _ratio(numerator: int | float, denominator: int | float) -> float:
    denominator_float = float(denominator or 0.0)
    if denominator_float <= 0:
        return 0.0
    return _round4(float(numerator) / denominator_float)


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _mean(values: Sequence[float]) -> float | None:
    filtered = [float(value) for value in values if value is not None]
    if not filtered:
        return None
    return _round4(sum(filtered) / len(filtered))


def _min(values: Sequence[float]) -> float | None:
    filtered = [float(value) for value in values if value is not None]
    if not filtered:
        return None
    return _round4(min(filtered))


def _max(values: Sequence[float]) -> float | None:
    filtered = [float(value) for value in values if value is not None]
    if not filtered:
        return None
    return _round4(max(filtered))


def _fmt(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return str(round(value, 4))
    return str(value)


def _parse_int_list(value: str) -> list[int]:
    return [int(part.strip()) for part in str(value or "").split(",") if part.strip()]


def _parse_str_list(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").split(",") if part.strip()]
