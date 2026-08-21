#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_DIR = Path(__file__).resolve().parent
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_admission_preference_sample_pack_en_ja import (  # noqa: E402
    DEFAULT_CONFIG_JSON,
    DEFAULT_CORRECTED_RANKING_CSV,
    DEFAULT_OVERLAY_SOURCE_PATH,
    corrected_match_to_dict,
    corrected_ranking_runtime_env,
    filter_scenarios,
    load_corrected_ranking,
    load_json_mapping,
    normalize_weight_map,
    resolve_live_resources,
    safe_float,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.rulegen_bootstrap_selection import (  # noqa: E402
    build_profile_bootstrap_selector_config,
    dedupe_profile_bootstrap_entries,
)
from lexishift_core.srs.admission_policy import resolve_default_pos_weights  # noqa: E402
from lexishift_core.srs.learner_difficulty import (  # noqa: E402
    lookup_corrected_en_ja_learner_difficulty,
)
from lexishift_core.srs.profile_bootstrap import (  # noqa: E402
    FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY,
    FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_PROFILE_BOOTSTRAP_POLICY,
    FRONTIER_GAUSSIAN_PROFILE_BOOTSTRAP_POLICY,
    ProfileBootstrapFrontierLaneEntry,
    ProfileBootstrapScoredEntry,
    score_seed_words_for_frontier_gaussian_hybrid_profile,
    score_seed_words_for_frontier_gaussian_profile,
    score_seed_words_for_profile,
)
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from lexishift_core.srs.selector import select_scored_candidates  # noqa: E402
from lexishift_core.srs.topic_overlay import apply_profile_topic_overlay_to_seeds  # noqa: E402

REPORT_SCHEMA_VERSION = 1
DEFAULT_PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_admission_frontier_gaussian_config_compare_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_admission_frontier_gaussian_config_compare_en_ja_latest.md"
)
DEFAULT_INITIAL_ACTIVE_COUNT = 40
DEFAULT_SET_TOP_N = 10000
MARKDOWN_DETAIL_LIMIT = 12
DEFAULT_EXTRA_PROBE_SCENARIOS: tuple[dict[str, object], ...] = (
    {
        "name": "probe_neutral_expert",
        "description": "No topic preference at p=0.93; targets the high-proficiency too-easy sampling concern.",
        "proficiency": 0.93,
    },
    {
        "name": "probe_plants_nature_mid",
        "description": "Plants/nature preference at p=0.44; mirrors setup-flow product testing.",
        "proficiency": 0.44,
        "topic_weights": {"plants_nature": 1.0},
    },
    {
        "name": "probe_plants_nature_upper",
        "description": "Plants/nature preference at p=0.62; mirrors setup-flow product testing.",
        "proficiency": 0.62,
        "topic_weights": {"plants_nature": 1.0},
    },
    {
        "name": "probe_plants_nature_advanced",
        "description": "Plants/nature preference at p=0.73; mirrors setup-flow product testing.",
        "proficiency": 0.73,
        "topic_weights": {"plants_nature": 1.0},
    },
)


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_profile_context(scenario: Mapping[str, object]) -> dict[str, object]:
    context: dict[str, object] = {}
    proficiency = safe_float(scenario.get("proficiency"))
    if proficiency is not None:
        context["proficiency"] = {"estimated_value": clamp01(proficiency)}
    topic_weights = normalize_weight_map(scenario.get("topic_weights"))
    if topic_weights:
        context["topic_weights"] = topic_weights
        context["interests"] = list(topic_weights)
    extra_context = scenario.get("profile_context")
    if isinstance(extra_context, Mapping):
        context.update(dict(extra_context))
    return context


def build_report(
    *,
    config_json: Path,
    pair: str,
    frequency_db: Path | None,
    jmdict_path: Path | None,
    overlay_source_path: Path | None,
    corrected_ranking_csv: Path | None,
    scenario_filter: Sequence[str],
    include_probe_scenarios: bool,
    set_top_n: int | None,
    initial_active_count: int | None,
    cache_dir: Path | None,
) -> dict[str, Any]:
    config = load_json_mapping(config_json)
    defaults = dict(config.get("defaults") or {})
    resolved_set_top_n = int(set_top_n or defaults.get("set_top_n") or DEFAULT_SET_TOP_N)
    resolved_initial_active_count = int(
        initial_active_count or defaults.get("initial_active_count") or DEFAULT_INITIAL_ACTIVE_COUNT
    )
    config_scenarios = [row for row in config.get("scenarios", []) if isinstance(row, Mapping)]
    all_scenarios = list(config_scenarios)
    if include_probe_scenarios:
        existing_names = {str(row.get("name") or "") for row in all_scenarios}
        all_scenarios.extend(
            row
            for row in DEFAULT_EXTRA_PROBE_SCENARIOS
            if str(row.get("name") or "") not in existing_names
        )
    selected_scenarios = filter_scenarios(
        all_scenarios,
        scenario_filter=scenario_filter,
    )
    resolved_frequency_db, resolved_jmdict_path = resolve_live_resources(
        pair=pair,
        frequency_db=frequency_db,
        jmdict_path=jmdict_path,
    )
    resolved_overlay_source_path = overlay_source_path
    if resolved_overlay_source_path is None and DEFAULT_OVERLAY_SOURCE_PATH.exists():
        resolved_overlay_source_path = DEFAULT_OVERLAY_SOURCE_PATH
    overlay_payload = (
        load_json_mapping(resolved_overlay_source_path)
        if (resolved_overlay_source_path and resolved_overlay_source_path.exists())
        else None
    )
    helper_paths = build_helper_paths()
    resolved_cache_dir = cache_dir or helper_paths.srs_seed_frontier_cache_dir()
    corrected_ranking = load_corrected_ranking(corrected_ranking_csv)

    with corrected_ranking_runtime_env(corrected_ranking_csv):
        seed_config = SeedSelectionConfig(
            language_pair=pair,
            top_n=resolved_set_top_n,
            jmdict_path=resolved_jmdict_path,
            require_jmdict=True,
            admission_pos_weights=resolve_default_pos_weights(language_pair=pair),
            cache_dir=resolved_cache_dir,
        )
        base_seeds = build_seed_candidates(
            frequency_db=resolved_frequency_db,
            config=seed_config,
        )
        scenario_reports = [
            run_scenario_compare(
                scenario=scenario,
                pair=pair,
                base_seeds=base_seeds,
                overlay_payload=overlay_payload,
                initial_active_count=resolved_initial_active_count,
                corrected_ranking=corrected_ranking,
                corrected_ranking_csv=corrected_ranking_csv,
            )
            for scenario in selected_scenarios
        ]

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": now_iso_utc(),
        "pair": pair,
        "runtime_scope": "offline_selector_comparison_only",
        "method": {
            "legacy_v5_selector": "profile_bootstrap_policy_v5 + reserved_topic_lane",
            "frontier_selector": FRONTIER_GAUSSIAN_PROFILE_BOOTSTRAP_POLICY.version,
            "hybrid_selector": FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY.version,
            "hybrid_soft_topic_selector": (
                FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_PROFILE_BOOTSTRAP_POLICY.version
            ),
            "state_mutation": "none except reusable seed-frontier cache reads/writes",
            "comparison_unit": (
                "same seed frontier, same corrected difficulty hook, same topic overlay, "
                "different final admission selector"
            ),
        },
        "parameters": {
            "set_top_n": resolved_set_top_n,
            "initial_active_count": resolved_initial_active_count,
            "scenario_count": len(scenario_reports),
            "config_scenario_count": len(config_scenarios),
            "extra_probe_scenarios_included": bool(include_probe_scenarios),
            "seed_count": len(base_seeds),
        },
        "inputs": {
            "config_json": str(config_json),
            "frequency_db": str(resolved_frequency_db),
            "jmdict": str(resolved_jmdict_path),
            "overlay_source_path": str(resolved_overlay_source_path)
            if resolved_overlay_source_path
            else None,
            "corrected_ranking_csv": str(corrected_ranking_csv) if corrected_ranking_csv else None,
            "corrected_ranking_available": bool(corrected_ranking),
            "cache_dir": str(resolved_cache_dir) if resolved_cache_dir else None,
        },
        "summary": summarize_report(scenario_reports),
        "scenarios": scenario_reports,
    }


def run_scenario_compare(
    *,
    scenario: Mapping[str, object],
    pair: str,
    base_seeds: Sequence[object],
    overlay_payload: Mapping[str, object] | None,
    initial_active_count: int,
    corrected_ranking: Mapping[str, Mapping[str, object]],
    corrected_ranking_csv: Path | None,
) -> dict[str, Any]:
    profile_context = build_profile_context(scenario)
    scenario_seeds, overlay_diagnostics = apply_profile_topic_overlay_to_seeds(
        base_seeds,
        overlay_payload=overlay_payload,
        profile_context=profile_context,
        pair=pair,
        diagnostics={},
    )
    current_entries, current_diagnostics = select_current_entries(
        scenario_seeds,
        profile_context=profile_context,
        selection_count=initial_active_count,
    )
    frontier_entries, frontier_diagnostics = score_seed_words_for_frontier_gaussian_profile(
        scenario_seeds,
        profile_context=profile_context,
        selection_count=initial_active_count,
        preview_limit=initial_active_count,
    )
    hybrid_entries, hybrid_diagnostics = score_seed_words_for_frontier_gaussian_hybrid_profile(
        scenario_seeds,
        profile_context=profile_context,
        selection_count=initial_active_count,
        preview_limit=initial_active_count,
    )
    hybrid_soft_entries, hybrid_soft_diagnostics = (
        score_seed_words_for_frontier_gaussian_hybrid_profile(
            scenario_seeds,
            profile_context=profile_context,
            selection_count=initial_active_count,
            preview_limit=initial_active_count,
            policy=FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_PROFILE_BOOTSTRAP_POLICY,
        )
    )
    current_words = [
        simplify_current_entry(
            entry,
            corrected_ranking=corrected_ranking,
            corrected_ranking_csv=corrected_ranking_csv,
        )
        for entry in current_entries
    ]
    frontier_words = [
        simplify_frontier_entry(
            entry,
            corrected_ranking=corrected_ranking,
            corrected_ranking_csv=corrected_ranking_csv,
        )
        for entry in frontier_entries
    ]
    hybrid_words = [
        simplify_frontier_entry(
            entry,
            corrected_ranking=corrected_ranking,
            corrected_ranking_csv=corrected_ranking_csv,
        )
        for entry in hybrid_entries
    ]
    hybrid_soft_words = [
        simplify_frontier_entry(
            entry,
            corrected_ranking=corrected_ranking,
            corrected_ranking_csv=corrected_ranking_csv,
        )
        for entry in hybrid_soft_entries
    ]
    current_lemmas = [str(row.get("lemma") or "") for row in current_words]
    frontier_lemmas = [str(row.get("lemma") or "") for row in frontier_words]
    hybrid_lemmas = [str(row.get("lemma") or "") for row in hybrid_words]
    hybrid_soft_lemmas = [str(row.get("lemma") or "") for row in hybrid_soft_words]
    current_set = set(current_lemmas)
    frontier_set = set(frontier_lemmas)
    hybrid_set = set(hybrid_lemmas)
    hybrid_soft_set = set(hybrid_soft_lemmas)
    proficiency = safe_float(scenario.get("proficiency"))
    return {
        "name": str(scenario.get("name") or ""),
        "description": str(scenario.get("description") or ""),
        "proficiency": proficiency,
        "requested_topics": list(normalize_weight_map(scenario.get("topic_weights")).keys()),
        "profile_context": profile_context,
        "overlay": summarize_overlay(overlay_diagnostics),
        "current": {
            "selection_policy": current_diagnostics.get("selection_policy"),
            "selector_policy_version": current_diagnostics.get("selector_policy_version"),
            "stats": summarize_words(current_words, proficiency=proficiency),
            "words": current_words,
        },
        "frontier": {
            "selection_policy": frontier_diagnostics.get("selection_policy"),
            "selector_policy_version": frontier_diagnostics.get("selector_policy_version"),
            "lane_targets": frontier_diagnostics.get("lane_targets"),
            "filled_lane_counts": frontier_diagnostics.get("filled_lane_counts"),
            "stats": summarize_words(frontier_words, proficiency=proficiency),
            "words": frontier_words,
        },
        "hybrid": {
            "selection_policy": hybrid_diagnostics.get("selection_policy"),
            "selector_policy_version": hybrid_diagnostics.get("selector_policy_version"),
            "lane_targets": hybrid_diagnostics.get("lane_targets"),
            "filled_lane_counts": hybrid_diagnostics.get("filled_lane_counts"),
            "hybrid_topic_depth": hybrid_diagnostics.get("hybrid_topic_depth"),
            "stats": summarize_words(hybrid_words, proficiency=proficiency),
            "words": hybrid_words,
        },
        "hybrid_soft": {
            "selection_policy": hybrid_soft_diagnostics.get("selection_policy"),
            "selector_policy_version": hybrid_soft_diagnostics.get("selector_policy_version"),
            "lane_targets": hybrid_soft_diagnostics.get("lane_targets"),
            "filled_lane_counts": hybrid_soft_diagnostics.get("filled_lane_counts"),
            "hybrid_topic_depth": hybrid_soft_diagnostics.get("hybrid_topic_depth"),
            "stats": summarize_words(hybrid_soft_words, proficiency=proficiency),
            "words": hybrid_soft_words,
        },
        "comparison": {
            "overlap_count": len(current_set & frontier_set),
            "current_hybrid_overlap_count": len(current_set & hybrid_set),
            "current_hybrid_soft_overlap_count": len(current_set & hybrid_soft_set),
            "frontier_hybrid_overlap_count": len(frontier_set & hybrid_set),
            "frontier_hybrid_soft_overlap_count": len(frontier_set & hybrid_soft_set),
            "hybrid_hybrid_soft_overlap_count": len(hybrid_set & hybrid_soft_set),
            "current_only": [lemma for lemma in current_lemmas if lemma not in frontier_set],
            "frontier_only": [lemma for lemma in frontier_lemmas if lemma not in current_set],
            "current_only_vs_hybrid": [
                lemma for lemma in current_lemmas if lemma not in hybrid_set
            ],
            "hybrid_only_vs_current": [
                lemma for lemma in hybrid_lemmas if lemma not in current_set
            ],
            "current_only_vs_hybrid_soft": [
                lemma for lemma in current_lemmas if lemma not in hybrid_soft_set
            ],
            "hybrid_soft_only_vs_current": [
                lemma for lemma in hybrid_soft_lemmas if lemma not in current_set
            ],
            "hybrid_only_vs_hybrid_soft": [
                lemma for lemma in hybrid_lemmas if lemma not in hybrid_soft_set
            ],
            "hybrid_soft_only_vs_hybrid": [
                lemma for lemma in hybrid_soft_lemmas if lemma not in hybrid_set
            ],
            "too_easy_delta": (
                int(summarize_words(frontier_words, proficiency=proficiency)["below_target_0_20"])
                - int(summarize_words(current_words, proficiency=proficiency)["below_target_0_20"])
            ),
            "hybrid_too_easy_delta": (
                int(summarize_words(hybrid_words, proficiency=proficiency)["below_target_0_20"])
                - int(summarize_words(current_words, proficiency=proficiency)["below_target_0_20"])
            ),
            "hybrid_soft_too_easy_delta": (
                int(
                    summarize_words(
                        hybrid_soft_words,
                        proficiency=proficiency,
                    )["below_target_0_20"]
                )
                - int(summarize_words(current_words, proficiency=proficiency)["below_target_0_20"])
            ),
            "near_target_delta": (
                int(summarize_words(frontier_words, proficiency=proficiency)["within_target_0_10"])
                - int(summarize_words(current_words, proficiency=proficiency)["within_target_0_10"])
            ),
            "hybrid_near_target_delta": (
                int(summarize_words(hybrid_words, proficiency=proficiency)["within_target_0_10"])
                - int(summarize_words(current_words, proficiency=proficiency)["within_target_0_10"])
            ),
            "hybrid_soft_near_target_delta": (
                int(
                    summarize_words(
                        hybrid_soft_words,
                        proficiency=proficiency,
                    )["within_target_0_10"]
                )
                - int(summarize_words(current_words, proficiency=proficiency)["within_target_0_10"])
            ),
        },
    }


def select_current_entries(
    seeds: Sequence[object],
    *,
    profile_context: Mapping[str, object],
    selection_count: int,
) -> tuple[list[ProfileBootstrapScoredEntry], Mapping[str, object]]:
    scored_entries, diagnostics = score_seed_words_for_profile(
        seeds,
        profile_context=profile_context,
        preview_limit=selection_count,
    )
    unique_entries = dedupe_profile_bootstrap_entries(scored_entries)
    selected_candidates = select_scored_candidates(
        [entry.scored_candidate for entry in unique_entries],
        config=build_profile_bootstrap_selector_config(
            selection_policy=str(diagnostics.get("selection_policy") or ""),
            selection_count=selection_count,
        ),
        selection_count=selection_count,
    )
    entry_by_lemma = {
        entry.scored_candidate.candidate.lemma: entry
        for entry in unique_entries
        if entry.scored_candidate.candidate.lemma
    }
    return [
        entry_by_lemma[candidate.candidate.lemma]
        for candidate in selected_candidates
        if candidate.candidate.lemma in entry_by_lemma
    ], diagnostics


def simplify_current_entry(
    entry: ProfileBootstrapScoredEntry,
    *,
    corrected_ranking: Mapping[str, Mapping[str, object]],
    corrected_ranking_csv: Path | None,
) -> dict[str, Any]:
    return simplify_entry_common(
        seed=entry.seed,
        traits=entry.traits.to_dict(),
        signals=entry.signal_pack.to_dict(),
        profile_score=entry.scored_candidate.breakdown.final_score,
        lane=None,
        lane_score=None,
        corrected_ranking=corrected_ranking,
        corrected_ranking_csv=corrected_ranking_csv,
    )


def simplify_frontier_entry(
    entry: ProfileBootstrapFrontierLaneEntry,
    *,
    corrected_ranking: Mapping[str, Mapping[str, object]],
    corrected_ranking_csv: Path | None,
) -> dict[str, Any]:
    lane = str(entry.selected_lane or "")
    return simplify_entry_common(
        seed=entry.seed,
        traits=entry.traits.to_dict(),
        signals=entry.signal_pack.to_dict(),
        profile_score=entry.source_entry.scored_candidate.breakdown.final_score,
        lane=lane,
        lane_score=safe_float(entry.lane_scores.get(lane)) if lane else None,
        corrected_ranking=corrected_ranking,
        corrected_ranking_csv=corrected_ranking_csv,
        frontier_fit=entry.frontier_fit.to_dict(),
    )


def simplify_entry_common(
    *,
    seed: object,
    traits: Mapping[str, object],
    signals: Mapping[str, object],
    profile_score: float,
    lane: str | None,
    lane_score: float | None,
    corrected_ranking: Mapping[str, Mapping[str, object]],
    corrected_ranking_csv: Path | None,
    frontier_fit: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    lemma = str(getattr(seed, "lemma", "") or "").strip()
    corrected = corrected_match_to_dict(
        lookup_corrected_en_ja_learner_difficulty(
            lemma=lemma,
            reading_candidates=tuple(traits.get("lexical_forms") or ()),
            csv_path=corrected_ranking_csv,
        )
    )
    if not corrected:
        corrected = dict(corrected_ranking.get(lemma) or {})
    return {
        "lemma": lemma,
        "reading": corrected.get("reading"),
        "display_form": corrected.get("display_form"),
        "pos_bucket": getattr(seed, "pos_bucket", None),
        "corrected_difficulty": rounded_or_none(safe_float(corrected.get("corrected_difficulty"))),
        "runtime_difficulty_estimate": rounded_or_none(
            safe_float(signals.get("difficulty_estimate"))
        ),
        "profile_score": rounded_or_none(float(profile_score)),
        "lane": lane,
        "lane_score": rounded_or_none(lane_score),
        "topic_affinity": rounded_or_none(safe_float(signals.get("topic_affinity"))),
        "topic_affinity_source": signals.get("topic_affinity_source"),
        "proficiency_fit": rounded_or_none(safe_float(signals.get("proficiency_fit"))),
        "readiness_multiplier": rounded_or_none(safe_float(signals.get("readiness_multiplier"))),
        "admission_suitability": rounded_or_none(safe_float(signals.get("admission_suitability"))),
        "candidate_state": traits.get("candidate_state"),
        "classification_reasons": list(traits.get("classification_reasons") or []),
        "frontier_fit": dict(frontier_fit or {}),
    }


def summarize_words(
    words: Sequence[Mapping[str, object]],
    *,
    proficiency: float | None,
) -> dict[str, object]:
    difficulties = [
        value
        for word in words
        for value in (safe_float(word.get("runtime_difficulty_estimate")),)
        if value is not None
    ]
    lane_counts = Counter(str(word.get("lane") or "-") for word in words)
    topic_count = sum(1 for word in words if word.get("topic_affinity_source"))
    if not difficulties:
        return {
            "count": len(words),
            "topic_count": topic_count,
            "difficulty_min": None,
            "difficulty_mean": None,
            "difficulty_median": None,
            "difficulty_max": None,
            "within_target_0_10": 0,
            "below_target_0_10": 0,
            "below_target_0_20": 0,
            "above_target_0_10": 0,
            "lane_counts": dict(sorted(lane_counts.items())),
        }
    if proficiency is None:
        within = below_10 = below_20 = above_10 = 0
    else:
        within = sum(1 for value in difficulties if abs(value - proficiency) <= 0.10)
        below_10 = sum(1 for value in difficulties if value < proficiency - 0.10)
        below_20 = sum(1 for value in difficulties if value < proficiency - 0.20)
        above_10 = sum(1 for value in difficulties if value > proficiency + 0.10)
    return {
        "count": len(words),
        "topic_count": topic_count,
        "difficulty_min": rounded_or_none(min(difficulties)),
        "difficulty_mean": rounded_or_none(statistics.fmean(difficulties)),
        "difficulty_median": rounded_or_none(statistics.median(difficulties)),
        "difficulty_max": rounded_or_none(max(difficulties)),
        "within_target_0_10": within,
        "below_target_0_10": below_10,
        "below_target_0_20": below_20,
        "above_target_0_10": above_10,
        "lane_counts": dict(sorted(lane_counts.items())),
    }


def summarize_report(scenarios: Sequence[Mapping[str, object]]) -> dict[str, object]:
    current_too_easy = 0
    frontier_too_easy = 0
    hybrid_too_easy = 0
    hybrid_soft_too_easy = 0
    current_near = 0
    frontier_near = 0
    hybrid_near = 0
    hybrid_soft_near = 0
    current_topic = 0
    frontier_topic = 0
    hybrid_topic = 0
    hybrid_soft_topic = 0
    for scenario in scenarios:
        current_stats = dict(dict(scenario.get("current") or {}).get("stats") or {})
        frontier_stats = dict(dict(scenario.get("frontier") or {}).get("stats") or {})
        hybrid_stats = dict(dict(scenario.get("hybrid") or {}).get("stats") or {})
        hybrid_soft_stats = dict(dict(scenario.get("hybrid_soft") or {}).get("stats") or {})
        current_too_easy += int(current_stats.get("below_target_0_20") or 0)
        frontier_too_easy += int(frontier_stats.get("below_target_0_20") or 0)
        hybrid_too_easy += int(hybrid_stats.get("below_target_0_20") or 0)
        hybrid_soft_too_easy += int(hybrid_soft_stats.get("below_target_0_20") or 0)
        current_near += int(current_stats.get("within_target_0_10") or 0)
        frontier_near += int(frontier_stats.get("within_target_0_10") or 0)
        hybrid_near += int(hybrid_stats.get("within_target_0_10") or 0)
        hybrid_soft_near += int(hybrid_soft_stats.get("within_target_0_10") or 0)
        current_topic += int(current_stats.get("topic_count") or 0)
        frontier_topic += int(frontier_stats.get("topic_count") or 0)
        hybrid_topic += int(hybrid_stats.get("topic_count") or 0)
        hybrid_soft_topic += int(hybrid_soft_stats.get("topic_count") or 0)
    return {
        "scenario_count": len(scenarios),
        "current_total_below_target_0_20": current_too_easy,
        "frontier_total_below_target_0_20": frontier_too_easy,
        "hybrid_total_below_target_0_20": hybrid_too_easy,
        "hybrid_soft_total_below_target_0_20": hybrid_soft_too_easy,
        "current_total_within_target_0_10": current_near,
        "frontier_total_within_target_0_10": frontier_near,
        "hybrid_total_within_target_0_10": hybrid_near,
        "hybrid_soft_total_within_target_0_10": hybrid_soft_near,
        "current_total_topic_count": current_topic,
        "frontier_total_topic_count": frontier_topic,
        "hybrid_total_topic_count": hybrid_topic,
        "hybrid_soft_total_topic_count": hybrid_soft_topic,
        "below_target_0_20_delta": frontier_too_easy - current_too_easy,
        "hybrid_below_target_0_20_delta": hybrid_too_easy - current_too_easy,
        "hybrid_soft_below_target_0_20_delta": hybrid_soft_too_easy - current_too_easy,
        "within_target_0_10_delta": frontier_near - current_near,
        "hybrid_within_target_0_10_delta": hybrid_near - current_near,
        "hybrid_soft_within_target_0_10_delta": hybrid_soft_near - current_near,
        "frontier_topic_count_delta": frontier_topic - current_topic,
        "hybrid_topic_count_delta": hybrid_topic - current_topic,
        "hybrid_soft_topic_count_delta": hybrid_soft_topic - current_topic,
    }


def summarize_overlay(value: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "application_status",
        "requested_topics",
        "active_topics",
        "eligible_row_count",
        "matched_eligible_lemma_count",
        "applied_seed_count",
        "applied_row_count",
        "applied_topics",
    )
    return {key: value.get(key) for key in keys if key in value}


def render_markdown(report: Mapping[str, object]) -> str:
    params = dict(report.get("parameters") or {})
    summary = dict(report.get("summary") or {})
    inputs = dict(report.get("inputs") or {})
    lines = [
        "# en-ja SRS Admission Frontier Gaussian Config Compare",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- runtime_scope: `{report.get('runtime_scope')}`",
        f"- scenarios: `{params.get('scenario_count')}`",
        f"- seed_count: `{params.get('seed_count')}`",
        f"- set_top_n: `{params.get('set_top_n')}`",
        f"- initial_active_count: `{params.get('initial_active_count')}`",
        f"- corrected_ranking_available: `{inputs.get('corrected_ranking_available')}`",
        "",
        "## Overall Summary",
        "",
        "| Metric | Legacy v5 | Frontier v1 | Hybrid v2 | Hybrid soft v3 | Frontier Delta | Hybrid Delta | Hybrid soft Delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| Below target by >0.20 | {summary.get('current_total_below_target_0_20')} | "
            f"{summary.get('frontier_total_below_target_0_20')} | "
            f"{summary.get('hybrid_total_below_target_0_20')} | "
            f"{summary.get('hybrid_soft_total_below_target_0_20')} | "
            f"{summary.get('below_target_0_20_delta')} | "
            f"{summary.get('hybrid_below_target_0_20_delta')} | "
            f"{summary.get('hybrid_soft_below_target_0_20_delta')} |"
        ),
        (
            f"| Within target ±0.10 | {summary.get('current_total_within_target_0_10')} | "
            f"{summary.get('frontier_total_within_target_0_10')} | "
            f"{summary.get('hybrid_total_within_target_0_10')} | "
            f"{summary.get('hybrid_soft_total_within_target_0_10')} | "
            f"{summary.get('within_target_0_10_delta')} | "
            f"{summary.get('hybrid_within_target_0_10_delta')} | "
            f"{summary.get('hybrid_soft_within_target_0_10_delta')} |"
        ),
        (
            f"| Topic selections | {summary.get('current_total_topic_count')} | "
            f"{summary.get('frontier_total_topic_count')} | "
            f"{summary.get('hybrid_total_topic_count')} | "
            f"{summary.get('hybrid_soft_total_topic_count')} | "
            f"{summary.get('frontier_topic_count_delta')} | "
            f"{summary.get('hybrid_topic_count_delta')} | "
            f"{summary.get('hybrid_soft_topic_count_delta')} |"
        ),
        "",
        "## Scenario Summary",
        "",
        "| Scenario | p | Topics | Legacy v5 mean/range | Legacy v5 topic/<p-.20 | Frontier mean/range | Frontier topic/<p-.20 | Hybrid mean/range | Hybrid topic/<p-.20 | Hybrid soft mean/range | Hybrid soft topic/<p-.20 | Hybrid soft lanes |",
        "| --- | ---: | --- | --- | ---: | --- | ---: | --- | ---: | --- | ---: | --- |",
    ]
    for scenario in report.get("scenarios", ()):
        if not isinstance(scenario, Mapping):
            continue
        current_stats = dict(dict(scenario.get("current") or {}).get("stats") or {})
        frontier_stats = dict(dict(scenario.get("frontier") or {}).get("stats") or {})
        hybrid_stats = dict(dict(scenario.get("hybrid") or {}).get("stats") or {})
        hybrid_soft_stats = dict(dict(scenario.get("hybrid_soft") or {}).get("stats") or {})
        topics = ", ".join(str(topic) for topic in scenario.get("requested_topics", ())) or "-"
        lines.append(
            "| "
            f"`{scenario.get('name')}` | "
            f"{fmt(scenario.get('proficiency'))} | "
            f"{topics} | "
            f"{range_label(current_stats)} | "
            f"{current_stats.get('topic_count')}/{current_stats.get('below_target_0_20')} | "
            f"{range_label(frontier_stats)} | "
            f"{frontier_stats.get('topic_count')}/{frontier_stats.get('below_target_0_20')} | "
            f"{range_label(hybrid_stats)} | "
            f"{hybrid_stats.get('topic_count')}/{hybrid_stats.get('below_target_0_20')} | "
            f"{range_label(hybrid_soft_stats)} | "
            f"{hybrid_soft_stats.get('topic_count')}/{hybrid_soft_stats.get('below_target_0_20')} | "
            f"{lane_label(hybrid_soft_stats.get('lane_counts'))} |"
        )
    lines.extend(["", "## Scenario Details", ""])
    for scenario in report.get("scenarios", ()):
        if isinstance(scenario, Mapping):
            lines.extend(render_scenario_detail(scenario))
    return "\n".join(lines).rstrip() + "\n"


def render_scenario_detail(scenario: Mapping[str, object]) -> list[str]:
    current_words = [
        word
        for word in dict(scenario.get("current") or {}).get("words", ())
        if isinstance(word, Mapping)
    ]
    frontier_words = [
        word
        for word in dict(scenario.get("frontier") or {}).get("words", ())
        if isinstance(word, Mapping)
    ]
    hybrid_words = [
        word
        for word in dict(scenario.get("hybrid") or {}).get("words", ())
        if isinstance(word, Mapping)
    ]
    hybrid_soft_words = [
        word
        for word in dict(scenario.get("hybrid_soft") or {}).get("words", ())
        if isinstance(word, Mapping)
    ]
    lines = [
        f"### `{scenario.get('name')}`",
        "",
        f"- proficiency: `{fmt(scenario.get('proficiency'))}`",
        f"- topics: `{', '.join(str(topic) for topic in scenario.get('requested_topics', ())) or '-'}`",
        f"- frontier lane targets: `{dict(dict(scenario.get('frontier') or {}).get('lane_targets') or {})}`",
        f"- frontier lane fills: `{dict(dict(scenario.get('frontier') or {}).get('filled_lane_counts') or {})}`",
        f"- hybrid lane targets: `{dict(dict(scenario.get('hybrid') or {}).get('lane_targets') or {})}`",
        f"- hybrid lane fills: `{dict(dict(scenario.get('hybrid') or {}).get('filled_lane_counts') or {})}`",
        f"- hybrid topic depth: `{dict(dict(scenario.get('hybrid') or {}).get('hybrid_topic_depth') or {})}`",
        f"- hybrid soft lane targets: `{dict(dict(scenario.get('hybrid_soft') or {}).get('lane_targets') or {})}`",
        f"- hybrid soft lane fills: `{dict(dict(scenario.get('hybrid_soft') or {}).get('filled_lane_counts') or {})}`",
        f"- hybrid soft topic depth: `{dict(dict(scenario.get('hybrid_soft') or {}).get('hybrid_topic_depth') or {})}`",
        "",
        "| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |",
        "| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |",
    ]
    for index in range(
        min(
            MARKDOWN_DETAIL_LIMIT,
            max(
                len(current_words),
                len(frontier_words),
                len(hybrid_words),
                len(hybrid_soft_words),
            ),
        )
    ):
        current = current_words[index] if index < len(current_words) else {}
        frontier = frontier_words[index] if index < len(frontier_words) else {}
        hybrid = hybrid_words[index] if index < len(hybrid_words) else {}
        hybrid_soft = hybrid_soft_words[index] if index < len(hybrid_soft_words) else {}
        lines.append(
            f"| {index + 1} | "
            f"{word_label(current)} | {fmt(current.get('runtime_difficulty_estimate'))} | "
            f"{topic_label(current)} | "
            f"{word_label(frontier)} | {fmt(frontier.get('runtime_difficulty_estimate'))} | "
            f"{frontier.get('lane') or '-'} | "
            f"{word_label(hybrid)} | {fmt(hybrid.get('runtime_difficulty_estimate'))} | "
            f"{hybrid.get('lane') or '-'} | "
            f"{word_label(hybrid_soft)} | "
            f"{fmt(hybrid_soft.get('runtime_difficulty_estimate'))} | "
            f"{hybrid_soft.get('lane') or '-'} | {topic_label(hybrid_soft)} |"
        )
    comparison = dict(scenario.get("comparison") or {})
    lines.extend(
        [
            "",
            f"- legacy_v5_only: `{', '.join(str(v) for v in list(comparison.get('current_only') or [])[:12])}`",
            f"- frontier_only: `{', '.join(str(v) for v in list(comparison.get('frontier_only') or [])[:12])}`",
            f"- legacy_v5_only_vs_hybrid: `{', '.join(str(v) for v in list(comparison.get('current_only_vs_hybrid') or [])[:12])}`",
            f"- hybrid_only_vs_legacy_v5: `{', '.join(str(v) for v in list(comparison.get('hybrid_only_vs_current') or [])[:12])}`",
            f"- hybrid_soft_only_vs_legacy_v5: `{', '.join(str(v) for v in list(comparison.get('hybrid_soft_only_vs_current') or [])[:12])}`",
            f"- hybrid_soft_only_vs_hybrid: `{', '.join(str(v) for v in list(comparison.get('hybrid_soft_only_vs_hybrid') or [])[:12])}`",
            "",
        ]
    )
    return lines


def word_label(word: Mapping[str, object]) -> str:
    lemma = str(word.get("lemma") or "")
    reading = str(word.get("reading") or "")
    if reading:
        return f"`{lemma}`/{reading}"
    return f"`{lemma}`" if lemma else "-"


def topic_label(word: Mapping[str, object]) -> str:
    source = str(word.get("topic_affinity_source") or "")
    if not source:
        return "-"
    return source.replace("topic_hint:", "")


def range_label(stats: Mapping[str, object]) -> str:
    return (
        f"{fmt(stats.get('difficulty_mean'))} "
        f"({fmt(stats.get('difficulty_min'))}-{fmt(stats.get('difficulty_max'))})"
    )


def lane_label(value: object) -> str:
    if not isinstance(value, Mapping):
        return "-"
    return ", ".join(f"{key}:{value[key]}" for key in sorted(value)) or "-"


def fmt(value: object) -> str:
    parsed = safe_float(value)
    if parsed is None:
        return "-"
    return f"{parsed:.3f}"


def rounded_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def write_report(report: Mapping[str, object], *, json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare current en-ja profile bootstrap admission with passive frontier-Gaussian lanes."
    )
    parser.add_argument("--config-json", type=Path, default=DEFAULT_CONFIG_JSON)
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--jmdict", type=Path)
    parser.add_argument("--overlay-source-path", type=Path)
    parser.add_argument("--corrected-ranking-csv", type=Path, default=DEFAULT_CORRECTED_RANKING_CSV)
    parser.add_argument("--scenario-filter", default="")
    parser.add_argument(
        "--no-extra-probe-scenarios",
        action="store_true",
        help="Only run scenarios from --config-json; omit the high-proficiency/product probes.",
    )
    parser.add_argument("--set-top-n", type=int)
    parser.add_argument("--initial-active-count", type=int, default=DEFAULT_INITIAL_ACTIVE_COUNT)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenario_filter = tuple(
        part.strip() for part in str(args.scenario_filter or "").split(",") if part.strip()
    )
    report = build_report(
        config_json=args.config_json,
        pair=args.pair,
        frequency_db=args.frequency_db,
        jmdict_path=args.jmdict,
        overlay_source_path=args.overlay_source_path,
        corrected_ranking_csv=args.corrected_ranking_csv,
        scenario_filter=scenario_filter,
        include_probe_scenarios=not args.no_extra_probe_scenarios,
        set_top_n=args.set_top_n,
        initial_active_count=args.initial_active_count,
        cache_dir=args.cache_dir,
    )
    write_report(report, json_out=args.json_out, markdown_out=args.markdown_out)
    summary = dict(report.get("summary") or {})
    print(f"json_out: {args.json_out}")
    print(f"markdown_out: {args.markdown_out}")
    print(
        "summary: "
        f"scenarios={summary.get('scenario_count')} "
        f"current_below_target_0_20={summary.get('current_total_below_target_0_20')} "
        f"frontier_below_target_0_20={summary.get('frontier_total_below_target_0_20')} "
        f"hybrid_below_target_0_20={summary.get('hybrid_total_below_target_0_20')} "
        f"hybrid_soft_below_target_0_20={summary.get('hybrid_soft_total_below_target_0_20')} "
        f"current_within_0_10={summary.get('current_total_within_target_0_10')} "
        f"frontier_within_0_10={summary.get('frontier_total_within_target_0_10')} "
        f"hybrid_within_0_10={summary.get('hybrid_total_within_target_0_10')} "
        f"hybrid_soft_within_0_10={summary.get('hybrid_soft_total_within_target_0_10')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
