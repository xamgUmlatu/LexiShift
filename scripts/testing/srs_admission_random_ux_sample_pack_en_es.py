#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import secrets
import shutil
import sys
import tempfile
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.engine import (  # noqa: E402
    SetAdmissionPreviewJobConfig,
    preview_srs_admission,
)
from lexishift_core.helper.pair_resources import resolve_pair_resources  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.learner_difficulty import (  # noqa: E402
    CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV,
    clear_corrected_learner_difficulty_cache,
)
from lexishift_core.srs.set_strategy import STRATEGY_PROFILE_BOOTSTRAP  # noqa: E402
from lexishift_core.srs.topic_overlay import EN_ES_REVIEWED_OVERLAY_FILENAME  # noqa: E402

REPORT_SCHEMA_VERSION = 1
DEFAULT_PAIR = "en-es"
DEFAULT_CONFIG_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_admission_product_acceptance_configs_en_es.json"
)
DEFAULT_OVERLAY_SOURCE_PATH = (
    PROJECT_ROOT / "docs" / "test_outputs" / EN_ES_REVIEWED_OVERLAY_FILENAME
)
DEFAULT_CORRECTED_RANKING_CSV = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_en_es_latest.csv"
)
DEFAULT_TAXONOMY_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_topic_preference_taxonomy_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_random_ux_sample_pack_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_random_ux_sample_pack_en_es_latest.md"
)
DEFAULT_DRAW_COUNT = 3
DEFAULT_PREVIEW_COUNT = 60
DEFAULT_MARKDOWN_WORD_LIMIT_PER_DRAW = 16
LENIENCY_MARGIN = 0.10
RUNTIME_OVERLAY_MIN_MEMBERSHIP = 1.0


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_report(
    *,
    config_json: Path,
    pair: str,
    frequency_db: Path | None,
    overlay_source_path: Path | None,
    corrected_ranking_csv: Path | None,
    taxonomy_json: Path | None,
    scenario_filter: Sequence[str],
    set_top_n: int | None,
    initial_active_count: int | None,
    preview_count: int | None,
    preview_sampling_mode: str | None,
    draw_count: int,
    random_seed: int | None,
    markdown_word_limit_per_draw: int,
) -> dict[str, Any]:
    config = load_json_mapping(config_json)
    defaults = dict(config.get("defaults") or {})
    resolved_set_top_n = int(set_top_n or defaults.get("set_top_n") or 10000)
    resolved_initial_active_count = int(
        initial_active_count or defaults.get("initial_active_count") or 80
    )
    resolved_preview_count = int(
        preview_count or defaults.get("preview_count") or DEFAULT_PREVIEW_COUNT
    )
    resolved_preview_sampling_mode = str(
        preview_sampling_mode or defaults.get("preview_sampling_mode") or "reserved_topic_lane"
    )
    resolved_draw_count = max(1, int(draw_count or DEFAULT_DRAW_COUNT))
    seed_source = "explicit" if random_seed is not None else "system_entropy"
    root_seed = int(random_seed) if random_seed is not None else secrets.randbits(63)
    seed_rng = random.Random(root_seed)
    selected_scenarios = filter_scenarios(
        [row for row in config.get("scenarios", []) if isinstance(row, Mapping)],
        scenario_filter=scenario_filter,
    )
    resolved_frequency_db = resolve_frequency_db(pair=pair, frequency_db=frequency_db)
    resolved_overlay_source_path = overlay_source_path
    if resolved_overlay_source_path is None and DEFAULT_OVERLAY_SOURCE_PATH.exists():
        resolved_overlay_source_path = DEFAULT_OVERLAY_SOURCE_PATH
    overlay_inventory = inspect_overlay(resolved_overlay_source_path)
    taxonomy_summary = load_taxonomy_summary(taxonomy_json, overlay_inventory)
    corrected_ranking = load_corrected_ranking(corrected_ranking_csv)

    with tempfile.TemporaryDirectory(prefix="lexishift-srs-enes-random-ux-") as tmp:
        paths = build_helper_paths(Path(tmp))
        copied_overlay_path = copy_overlay_source(paths, resolved_overlay_source_path)
        with corrected_ranking_runtime_env(corrected_ranking_csv):
            scenario_reports = []
            for scenario_index, scenario in enumerate(selected_scenarios, start=1):
                draws = []
                for draw_index in range(1, resolved_draw_count + 1):
                    draw_seed = seed_rng.randrange(1, 2_147_483_647)
                    draw = run_scenario(
                        paths=paths,
                        pair=pair,
                        frequency_db=resolved_frequency_db,
                        scenario=scenario,
                        set_top_n=resolved_set_top_n,
                        initial_active_count=resolved_initial_active_count,
                        preview_count=resolved_preview_count,
                        preview_sampling_mode=resolved_preview_sampling_mode,
                        preview_seed=draw_seed,
                        corrected_ranking=corrected_ranking,
                    )
                    draw["draw_index"] = draw_index
                    draw["preview_seed"] = draw_seed
                    draw["admitted_words"] = annotate_words_for_review(
                        draw.get("admitted_words"),
                        proficiency=safe_float(draw.get("proficiency")),
                    )
                    draw["draw_summary"] = summarize_words(
                        draw.get("admitted_words"),
                        proficiency=safe_float(draw.get("proficiency")),
                    )
                    draws.append(draw)
                scenario_reports.append(
                    summarize_random_scenario(
                        scenario=scenario,
                        scenario_index=scenario_index,
                        draws=draws,
                    )
                )

    findings = build_findings(
        scenario_reports=scenario_reports, overlay_inventory=overlay_inventory
    )
    summary = summarize_findings(findings)
    summary.update(
        {
            "scenario_count": len(scenario_reports),
            "draw_count_per_scenario": resolved_draw_count,
            "draw_count_total": sum(len(row.get("draws") or []) for row in scenario_reports),
            "topic_scenario_count": sum(
                1 for scenario in scenario_reports if scenario.get("requested_topics")
            ),
            "topic_scenarios_with_movers": sum(
                1
                for scenario in scenario_reports
                if scenario.get("requested_topics")
                and int(dict(scenario.get("aggregate") or {}).get("topic_mover_total") or 0)
            ),
            "overlay_runtime_supported_topic_count": sum(
                1
                for topic in overlay_inventory.get("topics", [])
                if isinstance(topic, Mapping)
                and int(topic.get("runtime_supported_row_count") or 0) > 0
            ),
        }
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": now_iso_utc(),
        "pair": pair,
        "runtime_scope": "randomized_admission_preview_only",
        "method": {
            "strategy": STRATEGY_PROFILE_BOOTSTRAP,
            "profile_shape": "single proficiency estimate plus optional topic_weights/interests",
            "sampling_design": (
                "Each draw builds the same profile-shaped planned active set, then samples a "
                "smaller preview from that active set using a fresh per-draw random seed."
            ),
            "randomness": (
                "True-random root seed from system entropy unless --random-seed is provided; "
                "all per-draw seeds are recorded for replay."
            ),
            "difficulty_source": (
                "profile_bootstrap reads the corrected en-es learner-difficulty CSV through "
                f"{CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV} when available; otherwise it "
                "falls back to runtime commonness signals."
            ),
            "leniency_read": (
                "difficulty_minus_proficiency and above-proficiency counts are reported "
                "separately for topic movers and non-topic words."
            ),
            "state_mutation": "none; previews run under a temporary helper data root",
        },
        "parameters": {
            "set_top_n": resolved_set_top_n,
            "initial_active_count": resolved_initial_active_count,
            "preview_count": resolved_preview_count,
            "preview_sampling_mode": resolved_preview_sampling_mode,
            "draw_count": resolved_draw_count,
            "root_random_seed": root_seed,
            "random_seed_source": seed_source,
            "markdown_word_limit_per_draw": markdown_word_limit_per_draw,
        },
        "inputs": {
            "config_json": str(config_json),
            "frequency_db": str(resolved_frequency_db),
            "overlay_source_path": str(resolved_overlay_source_path)
            if resolved_overlay_source_path
            else None,
            "copied_overlay_path": str(copied_overlay_path) if copied_overlay_path else None,
            "corrected_ranking_csv": str(corrected_ranking_csv) if corrected_ranking_csv else None,
            "corrected_ranking_available": bool(corrected_ranking),
            "taxonomy_json": str(taxonomy_json) if taxonomy_json else None,
        },
        "overlay_inventory": overlay_inventory,
        "taxonomy_summary": taxonomy_summary,
        "summary": summary,
        "findings": findings,
        "scenarios": scenario_reports,
    }


def run_scenario(
    *,
    paths: object,
    pair: str,
    frequency_db: Path,
    scenario: Mapping[str, object],
    set_top_n: int,
    initial_active_count: int,
    preview_count: int,
    preview_sampling_mode: str,
    preview_seed: int,
    corrected_ranking: Mapping[str, Mapping[str, object]],
) -> dict[str, Any]:
    profile_context = build_profile_context(scenario)
    payload = preview_srs_admission(
        paths,
        config=SetAdmissionPreviewJobConfig(
            pair=pair,
            set_source_db=frequency_db,
            strategy=STRATEGY_PROFILE_BOOTSTRAP,
            set_top_n=set_top_n,
            initial_active_count=initial_active_count,
            preview_count=preview_count,
            preview_sampling_mode=preview_sampling_mode,
            preview_seed=preview_seed,
            profile_context=profile_context,
            trigger="enes_random_ux_sample_pack",
        ),
    )
    preview = dict(payload.get("preview") or {})
    profile_bootstrap = dict(preview.get("profile_bootstrap") or {})
    admitted_words = [
        simplify_admitted_word(entry, corrected_ranking=corrected_ranking)
        for entry in preview.get("admitted_words", ())
        if isinstance(entry, Mapping)
    ]
    topic_movers = [entry for entry in admitted_words if entry.get("topic_affinity_source")]
    return {
        "name": str(scenario.get("name") or ""),
        "description": str(scenario.get("description") or ""),
        "proficiency": safe_float(scenario.get("proficiency")),
        "requested_topics": list(normalize_weight_map(scenario.get("topic_weights")).keys()),
        "requested_profile_context": profile_context,
        "effective_profile_context": dict(profile_bootstrap.get("profile_context") or {}),
        "plan": summarize_plan(payload.get("plan")),
        "preview_counts": {
            key: preview.get(key)
            for key in (
                "selected_count",
                "selected_unique_count",
                "admitted_count",
                "sample_count_requested",
                "sample_count_effective",
                "sampling_mode",
                "sampling_pool_count",
            )
        },
        "top_lemmas": [str(entry.get("lemma") or "") for entry in admitted_words],
        "admitted_words": admitted_words,
        "topic_mover_count": len(topic_movers),
        "topic_mover_counts": topic_mover_counts(topic_movers),
        "top_topic_movers": topic_movers[:10],
        "active_topic_support": summarize_active_topic_support(
            profile_bootstrap.get("active_topic_support")
        ),
        "topic_depth_by_level": summarize_topic_depth(
            profile_bootstrap.get("topic_depth_by_level")
        ),
        "profile_topic_overlay": summarize_overlay(
            dict(profile_bootstrap.get("profile_topic_overlay") or {})
        ),
    }


def simplify_admitted_word(
    entry: Mapping[str, object],
    *,
    corrected_ranking: Mapping[str, Mapping[str, object]],
) -> dict[str, Any]:
    signals = entry.get("signals") if isinstance(entry.get("signals"), Mapping) else {}
    traits = (
        entry.get("candidate_traits") if isinstance(entry.get("candidate_traits"), Mapping) else {}
    )
    lemma = str(entry.get("lemma") or "")
    corrected = dict(corrected_ranking.get(lemma) or {})
    runtime_difficulty = signal_value(signals, "difficulty_estimate")
    corrected_difficulty = safe_float(corrected.get("corrected_difficulty"))
    mismatch = (
        runtime_difficulty is not None
        and corrected_difficulty is not None
        and abs(runtime_difficulty - corrected_difficulty) >= 0.20
    )
    return {
        "lemma": lemma,
        "reading": corrected.get("reading"),
        "display_form": corrected.get("display_form"),
        "corrected_rank": corrected.get("corrected_rank"),
        "corrected_difficulty": rounded_or_none(corrected_difficulty),
        "corrected_band": corrected.get("corrected_band"),
        "runtime_difficulty_estimate": rounded_or_none(runtime_difficulty),
        "runtime_difficulty_proxy": traits.get("difficulty_proxy"),
        "runtime_difficulty_sources": traits.get("difficulty_sources"),
        "difficulty_mismatch_large": bool(mismatch),
        "candidate_state": corrected.get("candidate_state") or traits.get("candidate_state"),
        "admission_override": corrected.get("admission_override"),
        "correction_types": corrected.get("correction_types"),
        "topic_stretch_allowed": corrected.get("topic_stretch_allowed"),
        "manual_correction_active": corrected.get("manual_correction_active"),
        "pos_bucket": entry.get("pos_bucket"),
        "base_rank": entry.get("base_rank"),
        "reranked_rank": entry.get("reranked_rank"),
        "rank_delta": entry.get("rank_delta"),
        "profile_score": entry.get("profile_score"),
        "selection_mass": entry.get("selection_mass"),
        "base_weight": entry.get("base_weight"),
        "admission_weight": entry.get("admission_weight"),
        "topic_affinity": signal_value(signals, "topic_affinity"),
        "topic_affinity_source": signals.get("topic_affinity_source"),
        "scarcity_bonus": signal_value(signals, "scarcity_bonus"),
        "proficiency_fit": signal_value(signals, "proficiency_fit"),
        "readiness_multiplier": signal_value(signals, "readiness_multiplier"),
        "readiness_lower_bound": signal_value(signals, "readiness_lower_bound"),
        "readiness_upper_bound": signal_value(signals, "readiness_upper_bound"),
        "active_profile_drivers": entry.get("active_profile_drivers", []),
        "explanation": entry.get("explanation"),
    }


def annotate_words_for_review(
    words: object,
    *,
    proficiency: float | None,
) -> list[dict[str, Any]]:
    annotated = []
    for word in words if isinstance(words, Sequence) else []:
        if not isinstance(word, Mapping):
            continue
        row = dict(word)
        difficulty = word_difficulty(row)
        row["difficulty_for_summary"] = rounded_or_none(difficulty)
        if difficulty is not None and proficiency is not None:
            delta = difficulty - proficiency
            row["difficulty_minus_proficiency"] = round(delta, 6)
            row["above_proficiency"] = difficulty > proficiency
            row["above_proficiency_plus_0_10"] = difficulty > proficiency + LENIENCY_MARGIN
        else:
            row["difficulty_minus_proficiency"] = None
            row["above_proficiency"] = False
            row["above_proficiency_plus_0_10"] = False
        row["is_topic_mover"] = bool(row.get("topic_affinity_source"))
        annotated.append(row)
    return annotated


def summarize_random_scenario(
    *,
    scenario: Mapping[str, object],
    scenario_index: int,
    draws: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    all_words = [
        word
        for draw in draws
        for word in draw.get("admitted_words", [])
        if isinstance(word, Mapping)
    ]
    aggregate = summarize_words(all_words, proficiency=safe_float(scenario.get("proficiency")))
    aggregate["unique_lemma_count"] = len({str(word.get("lemma") or "") for word in all_words})
    aggregate["topic_mover_total"] = sum(1 for word in all_words if word.get("is_topic_mover"))
    aggregate["topic_mover_share"] = share(
        aggregate.get("topic_mover_total"),
        aggregate.get("count"),
    )
    return {
        "scenario_index": scenario_index,
        "name": str(scenario.get("name") or ""),
        "description": str(scenario.get("description") or ""),
        "proficiency": safe_float(scenario.get("proficiency")),
        "requested_topics": list(normalize_weight_map(scenario.get("topic_weights")).keys()),
        "requested_profile_context": build_profile_context(scenario),
        "aggregate": aggregate,
        "draws": list(draws),
    }


def summarize_words(
    words: object,
    *,
    proficiency: float | None,
) -> dict[str, Any]:
    rows = (
        [dict(row) for row in words if isinstance(row, Mapping)]
        if isinstance(words, Sequence)
        else []
    )
    topic_rows = [
        row for row in rows if row.get("is_topic_mover") or row.get("topic_affinity_source")
    ]
    non_topic_rows = [row for row in rows if row not in topic_rows]
    return {
        "count": len(rows),
        "difficulty": distribution([word_difficulty(row) for row in rows]),
        "difficulty_minus_proficiency": distribution(
            [difficulty_minus_proficiency(row, proficiency) for row in rows]
        ),
        "topic_movers": summarize_word_group(topic_rows, proficiency=proficiency),
        "non_topic": summarize_word_group(non_topic_rows, proficiency=proficiency),
        "topic_mover_counts": topic_mover_counts(topic_rows),
    }


def summarize_word_group(
    rows: Sequence[Mapping[str, object]],
    *,
    proficiency: float | None,
) -> dict[str, Any]:
    count = len(rows)
    above = [
        row
        for row in rows
        if difficulty_minus_proficiency(row, proficiency) is not None
        and float(difficulty_minus_proficiency(row, proficiency) or 0.0) > 0.0
    ]
    above_margin = [
        row
        for row in rows
        if difficulty_minus_proficiency(row, proficiency) is not None
        and float(difficulty_minus_proficiency(row, proficiency) or 0.0) > LENIENCY_MARGIN
    ]
    return {
        "count": count,
        "difficulty": distribution([word_difficulty(row) for row in rows]),
        "difficulty_minus_proficiency": distribution(
            [difficulty_minus_proficiency(row, proficiency) for row in rows]
        ),
        "above_proficiency_count": len(above),
        "above_proficiency_share": share(len(above), count),
        "above_proficiency_plus_0_10_count": len(above_margin),
        "above_proficiency_plus_0_10_share": share(len(above_margin), count),
        "max_positive_delta_examples": max_positive_delta_examples(rows, proficiency=proficiency),
    }


def build_findings(
    *,
    scenario_reports: Sequence[Mapping[str, object]],
    overlay_inventory: Mapping[str, object],
) -> list[dict[str, Any]]:
    findings = [
        finding(
            "PASS" if overlay_inventory.get("exists") else "WARN",
            "TOPIC_OVERLAY_AVAILABLE",
            "Merged reviewed en-es topic overlay was available for random UX samples."
            if overlay_inventory.get("exists")
            else "No merged reviewed en-es topic overlay was available.",
            {
                "row_count": overlay_inventory.get("row_count"),
                "runtime_supported_row_count": overlay_inventory.get("runtime_supported_row_count"),
            },
        )
    ]
    for scenario in scenario_reports:
        aggregate = dict(scenario.get("aggregate") or {})
        topic_mover_total = int(aggregate.get("topic_mover_total") or 0)
        requested_topics = list(scenario.get("requested_topics") or [])
        if not requested_topics:
            findings.append(
                finding(
                    "PASS",
                    f"RANDOM_NEUTRAL_SAMPLE:{scenario.get('name')}",
                    "Neutral random sample generated.",
                    {"sample_count": aggregate.get("count")},
                )
            )
            continue
        findings.append(
            finding(
                "PASS" if topic_mover_total else "WARN",
                f"RANDOM_TOPIC_SAMPLE:{scenario.get('name')}",
                "Random UX samples included topic movers."
                if topic_mover_total
                else "Random UX samples did not include topic movers.",
                {
                    "requested_topics": requested_topics,
                    "sample_count": aggregate.get("count"),
                    "topic_mover_total": topic_mover_total,
                    "topic_mover_share": aggregate.get("topic_mover_share"),
                },
            )
        )
    return findings


def render_markdown(report: Mapping[str, object]) -> str:
    summary = dict(report.get("summary") or {})
    params = dict(report.get("parameters") or {})
    inputs = dict(report.get("inputs") or {})
    lines = [
        "# en-es SRS Admission Random UX Sample Pack",
        "",
        f"- status: `{summary.get('status')}`",
        (
            "- findings: "
            f"pass={summary.get('pass_count')} "
            f"warn={summary.get('warn_count')} "
            f"fail={summary.get('fail_count')}"
        ),
        f"- scenarios: `{summary.get('scenario_count')}`",
        f"- draws: `{summary.get('draw_count_total')}`",
        f"- topic scenarios with movers: `{summary.get('topic_scenarios_with_movers')}` / `{summary.get('topic_scenario_count')}`",
        f"- runtime scope: `{report.get('runtime_scope')}`",
        "",
        "## Method",
        "",
        f"- strategy: `{dict(report.get('method') or {}).get('strategy')}`",
        f"- sampling design: {dict(report.get('method') or {}).get('sampling_design')}",
        f"- randomness: {dict(report.get('method') or {}).get('randomness')}",
        f"- difficulty source: {dict(report.get('method') or {}).get('difficulty_source')}",
        f"- leniency read: {dict(report.get('method') or {}).get('leniency_read')}",
        "",
        "## Inputs",
        "",
        f"- config_json: `{inputs.get('config_json')}`",
        f"- frequency_db: `{inputs.get('frequency_db')}`",
        f"- overlay_source_path: `{inputs.get('overlay_source_path')}`",
        f"- corrected_ranking_available: `{inputs.get('corrected_ranking_available')}`",
        f"- set_top_n: `{params.get('set_top_n')}`",
        f"- initial_active_count: `{params.get('initial_active_count')}`",
        f"- preview_count: `{params.get('preview_count')}`",
        f"- preview_sampling_mode: `{params.get('preview_sampling_mode')}`",
        f"- draw_count: `{params.get('draw_count')}`",
        f"- root_random_seed: `{params.get('root_random_seed')}`",
        f"- random_seed_source: `{params.get('random_seed_source')}`",
        "",
        "## Scenario Summary",
        "",
        (
            "| Scenario | Prof | Topics | Unique | Topic Share | Diff p25/med/p75/max | "
            "Topic Δ max | Non-topic Δ max | Sample |"
        ),
        "| --- | ---: | --- | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for scenario in report.get("scenarios", ()):
        if not isinstance(scenario, Mapping):
            continue
        aggregate = dict(scenario.get("aggregate") or {})
        diff = dict(aggregate.get("difficulty") or {})
        topic = dict(
            dict(aggregate.get("topic_movers") or {}).get("difficulty_minus_proficiency") or {}
        )
        non_topic = dict(
            dict(aggregate.get("non_topic") or {}).get("difficulty_minus_proficiency") or {}
        )
        topics = (
            ", ".join(str(topic_id) for topic_id in scenario.get("requested_topics", [])) or "-"
        )
        first_draw = next(
            (draw for draw in scenario.get("draws", []) if isinstance(draw, Mapping)),
            {},
        )
        sample = ", ".join(str(value) for value in list(first_draw.get("top_lemmas") or [])[:6])
        lines.append(
            f"| `{scenario.get('name')}` | {fmt(scenario.get('proficiency'))} | "
            f"{topics} | {aggregate.get('unique_lemma_count')} | "
            f"{fmt(aggregate.get('topic_mover_share'))} | "
            f"{fmt(diff.get('p25'))}/{fmt(diff.get('median'))}/{fmt(diff.get('p75'))}/{fmt(diff.get('max'))} | "
            f"{fmt(topic.get('max'))} | {fmt(non_topic.get('max'))} | {sample} |"
        )
    lines.extend(["", "## Scenario Details", ""])
    limit = int(params.get("markdown_word_limit_per_draw") or DEFAULT_MARKDOWN_WORD_LIMIT_PER_DRAW)
    for scenario in report.get("scenarios", ()):
        if isinstance(scenario, Mapping):
            lines.extend(render_scenario_detail(scenario, word_limit_per_draw=limit))
    lines.extend(["", "## Findings", ""])
    for item in report.get("findings", ()):
        if isinstance(item, Mapping):
            lines.append(f"- `{item.get('level')}` `{item.get('code')}`: {item.get('message')}")
    return "\n".join(lines).rstrip() + "\n"


def render_scenario_detail(
    scenario: Mapping[str, object],
    *,
    word_limit_per_draw: int,
) -> list[str]:
    lines = [
        f"### `{scenario.get('name')}`",
        "",
        str(scenario.get("description") or ""),
        "",
    ]
    aggregate = dict(scenario.get("aggregate") or {})
    topic_summary = dict(aggregate.get("topic_movers") or {})
    non_topic_summary = dict(aggregate.get("non_topic") or {})
    lines.extend(
        [
            "- aggregate: "
            f"unique=`{aggregate.get('unique_lemma_count')}` "
            f"topic_share=`{fmt(aggregate.get('topic_mover_share'))}` "
            f"topic_above+0.10=`{topic_summary.get('above_proficiency_plus_0_10_count')}` "
            f"non_topic_above+0.10=`{non_topic_summary.get('above_proficiency_plus_0_10_count')}`",
            "",
        ]
    )
    for draw in scenario.get("draws", []):
        if not isinstance(draw, Mapping):
            continue
        draw_summary = dict(draw.get("draw_summary") or {})
        diff = dict(draw_summary.get("difficulty") or {})
        lines.extend(
            [
                f"#### Draw {draw.get('draw_index')} seed `{draw.get('preview_seed')}`",
                "",
                "- draw summary: "
                f"topic_movers=`{draw.get('topic_mover_count')}` "
                f"diff_p25/med/p75/max=`{fmt(diff.get('p25'))}/{fmt(diff.get('median'))}/{fmt(diff.get('p75'))}/{fmt(diff.get('max'))}`",
                "",
                ("| # | Lemma | Diff | Δ vs Prof | Topic | Prof Fit | Ready Window | Rank Δ |"),
                "| ---: | --- | ---: | ---: | --- | ---: | --- | ---: |",
            ]
        )
        words = [row for row in draw.get("admitted_words", []) if isinstance(row, Mapping)][
            :word_limit_per_draw
        ]
        for index, word in enumerate(words, start=1):
            ready_window = (
                f"{fmt(word.get('readiness_lower_bound'))}-{fmt(word.get('readiness_upper_bound'))}"
            )
            lines.append(
                f"| {index} | `{word.get('lemma')}` | "
                f"{fmt(word.get('difficulty_for_summary'))} | "
                f"{fmt(word.get('difficulty_minus_proficiency'))} | "
                f"{word.get('topic_affinity_source') or ''} | "
                f"{fmt(word.get('proficiency_fit'))} | {ready_window} | "
                f"{word.get('rank_delta')} |"
            )
        lines.append("")
    return lines


def write_report(report: Mapping[str, object], *, json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")


def resolve_frequency_db(*, pair: str, frequency_db: Path | None) -> Path:
    if frequency_db is not None:
        resolved = frequency_db.expanduser()
    else:
        paths = build_helper_paths()
        _jmdict, _translation, resolved_frequency = resolve_pair_resources(
            paths,
            pair=pair,
            jmdict_path=None,
            translation_dict_path=None,
            set_source_db=None,
        )
        if resolved_frequency is None:
            raise ValueError(f"Could not resolve a default frequency DB for {pair}.")
        resolved = resolved_frequency
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def copy_overlay_source(paths: object, overlay_source_path: Path | None) -> Path | None:
    if overlay_source_path is None:
        return None
    source = overlay_source_path.expanduser()
    if not source.exists():
        return None
    target = Path(getattr(paths, "srs_dir")) / "topic_overlays" / EN_ES_REVIEWED_OVERLAY_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


@contextmanager
def corrected_ranking_runtime_env(path: Path | None):
    previous = os.environ.get(CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV)
    clear_corrected_learner_difficulty_cache()
    if path is not None and path.exists():
        os.environ[CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV] = str(path)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV, None)
        else:
            os.environ[CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV] = previous
        clear_corrected_learner_difficulty_cache()


def load_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def load_corrected_ranking(path: Path | None) -> dict[str, dict[str, object]]:
    if path is None or not path.exists():
        return {}
    by_lemma_rows: dict[str, list[dict[str, object]]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            lemma = str(row.get("lemma") or "").strip()
            if lemma:
                by_lemma_rows.setdefault(lemma, []).append(
                    {
                        "corrected_rank": int_or_none(row.get("rank")),
                        "reading": str(row.get("reading") or "").strip() or None,
                        "corrected_difficulty": safe_float(row.get("score")),
                        "corrected_band": str(row.get("band") or "").strip() or None,
                        "candidate_state": str(row.get("candidate_state") or "").strip() or None,
                        "correction_types": str(row.get("correction_types") or "").strip() or None,
                        "display_form": str(row.get("display_form") or "").strip() or None,
                        "admission_override": str(row.get("admission_override") or "").strip()
                        or None,
                        "topic_stretch_allowed": str(row.get("topic_stretch_allowed") or "").strip()
                        or None,
                        "manual_correction_active": str(
                            row.get("manual_correction_active") or ""
                        ).strip()
                        or None,
                    }
                )
    return {lemma: rows[0] for lemma, rows in by_lemma_rows.items() if len(rows) == 1}


def inspect_overlay(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {
            "path": str(path) if path else None,
            "exists": False,
            "status": "missing",
            "row_count": 0,
            "runtime_supported_row_count": 0,
            "topics": [],
        }
    payload = load_json_mapping(path)
    rows = [row for row in payload.get("rows", []) if isinstance(row, Mapping)]
    all_counts = Counter(str(row.get("topic") or "") for row in rows if row.get("topic"))
    runtime_counts = Counter(
        str(row.get("topic") or "")
        for row in rows
        if row.get("topic")
        and (safe_float(row.get("membership")) or 0.0) >= RUNTIME_OVERLAY_MIN_MEMBERSHIP
    )
    topics = sorted(set(all_counts) | set(runtime_counts))
    return {
        "path": str(path),
        "exists": True,
        "status": str(payload.get("status") or ""),
        "overlay_id": str(payload.get("overlay_id") or ""),
        "promotion_state": str(
            dict(payload.get("overlay_policy") or {}).get("promotion_state") or ""
        ),
        "row_count": len(rows),
        "runtime_supported_row_count": sum(runtime_counts.values()),
        "runtime_min_membership": RUNTIME_OVERLAY_MIN_MEMBERSHIP,
        "topics": [
            {
                "topic": topic,
                "row_count": int(all_counts.get(topic, 0)),
                "runtime_supported_row_count": int(runtime_counts.get(topic, 0)),
            }
            for topic in topics
        ],
    }


def load_taxonomy_summary(
    path: Path | None,
    overlay_inventory: Mapping[str, object],
) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"path": str(path) if path else None, "exists": False, "families": []}
    payload = load_json_mapping(path)
    overlay_topics = {
        str(entry.get("topic") or ""): dict(entry)
        for entry in (overlay_inventory.get("topics") or [])
        if isinstance(entry, Mapping)
    }
    families = []
    for family in payload.get("families", []):
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("id") or "")
        overlay_entry = overlay_topics.get(family_id, {})
        families.append(
            {
                "id": family_id,
                "display_name": str(family.get("display_name") or ""),
                "readiness_state": str(family.get("readiness_state") or ""),
                "overlay_row_count": int(overlay_entry.get("row_count") or 0),
                "runtime_supported_row_count": int(
                    overlay_entry.get("runtime_supported_row_count") or 0
                ),
            }
        )
    return {
        "path": str(path),
        "exists": True,
        "taxonomy_id": str(payload.get("taxonomy_id") or ""),
        "families": families,
    }


def build_profile_context(scenario: Mapping[str, object]) -> dict[str, object]:
    context: dict[str, object] = {}
    proficiency = safe_float(scenario.get("proficiency"))
    if proficiency is not None:
        context["proficiency"] = {"estimated_value": clamp01(proficiency)}
    topic_weights = normalize_weight_map(scenario.get("topic_weights"))
    interests = normalize_string_sequence(scenario.get("interests"))
    if topic_weights:
        context["topic_weights"] = topic_weights
        if not interests:
            interests = tuple(topic_weights.keys())
    if interests:
        context["interests"] = list(interests)
    extra_context = scenario.get("profile_context")
    if isinstance(extra_context, Mapping):
        context.update(dict(extra_context))
    return context


def normalize_weight_map(value: object) -> dict[str, float]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, float] = {}
    for key, raw_weight in value.items():
        topic = str(key or "").strip()
        weight = safe_float(raw_weight)
        if not topic or weight is None or weight <= 0.0:
            continue
        normalized[topic] = clamp01(weight)
    return normalized


def normalize_string_sequence(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        if not value.strip():
            return tuple()
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return tuple()
    return tuple(str(item).strip() for item in value if str(item).strip())


def filter_scenarios(
    scenarios: Sequence[Mapping[str, object]],
    *,
    scenario_filter: Sequence[str],
) -> list[Mapping[str, object]]:
    wanted = {str(name).strip() for name in scenario_filter if str(name).strip()}
    if not wanted:
        return list(scenarios)
    return [scenario for scenario in scenarios if str(scenario.get("name") or "") in wanted]


def summarize_plan(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    keys = ("strategy_requested", "strategy_effective", "execution_mode", "can_execute")
    return {key: value.get(key) for key in keys if key in value}


def summarize_overlay(overlay: Mapping[str, object]) -> dict[str, Any]:
    if not overlay:
        return {}
    keys = (
        "status",
        "reason",
        "application_status",
        "runtime_scope",
        "active_topics",
        "available_row_count",
        "applicable_row_count",
        "matched_seed_count",
        "eligible_row_count",
        "applied_seed_count",
        "applied_row_count",
        "applied_topics",
        "source_path",
        "promotion_state",
    )
    return {key: overlay.get(key) for key in keys if key in overlay}


def summarize_active_topic_support(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    topics = []
    for entry in value.get("topics", ()):
        if not isinstance(entry, Mapping):
            continue
        topics.append(
            {
                "topic": entry.get("topic"),
                "candidate_count": entry.get("candidate_count"),
                "candidate_ratio": entry.get("candidate_ratio"),
                "support_mass": entry.get("support_mass"),
                "support_mass_ratio": entry.get("support_mass_ratio"),
                "scarcity_readiness": entry.get("scarcity_readiness"),
                "top_examples": list(entry.get("top_examples") or []),
            }
        )
    return {
        "scope": value.get("scope"),
        "total_candidates": value.get("total_candidates"),
        "total_base_mass": value.get("total_base_mass"),
        "topics": topics,
    }


def summarize_topic_depth(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    topics = []
    for topic_entry in value.get("topics", []):
        if not isinstance(topic_entry, Mapping):
            continue
        topics.append(
            {
                "topic": topic_entry.get("topic"),
                "requested_weight": topic_entry.get("requested_weight"),
                "candidate_count": topic_entry.get("candidate_count"),
                "ready_candidate_count": topic_entry.get("ready_candidate_count"),
                "high_readiness_candidate_count": topic_entry.get("high_readiness_candidate_count"),
                "max_difficulty": topic_entry.get("max_difficulty"),
                "bands": [
                    {
                        "band": band.get("band"),
                        "candidate_count": band.get("candidate_count"),
                        "ready_candidate_count": band.get("ready_candidate_count"),
                        "high_readiness_candidate_count": band.get(
                            "high_readiness_candidate_count"
                        ),
                        "top_examples": list(band.get("top_examples") or [])[:3],
                    }
                    for band in topic_entry.get("bands", [])
                    if isinstance(band, Mapping)
                ],
            }
        )
    return {
        "version": value.get("version"),
        "topics": topics,
    }


def topic_mover_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        source = str(row.get("topic_affinity_source") or "")
        if source.startswith("topic_hint:"):
            topic = source.removeprefix("topic_hint:").split("->")[-1]
            counts[topic] += 1
        elif source.startswith("lexical:"):
            counts[source] += 1
    return dict(sorted(counts.items()))


def max_positive_delta_examples(
    rows: Sequence[Mapping[str, object]],
    *,
    proficiency: float | None,
    limit: int = 8,
) -> list[dict[str, object]]:
    examples = []
    for row in rows:
        delta = difficulty_minus_proficiency(row, proficiency)
        if delta is None or delta <= 0.0:
            continue
        examples.append(
            {
                "lemma": row.get("lemma"),
                "difficulty": rounded_or_none(word_difficulty(row)),
                "difficulty_minus_proficiency": round(delta, 6),
                "topic_affinity_source": row.get("topic_affinity_source"),
                "reranked_rank": row.get("reranked_rank"),
            }
        )
    examples.sort(
        key=lambda row: (
            -float(row.get("difficulty_minus_proficiency") or 0.0),
            str(row.get("lemma") or ""),
        )
    )
    return examples[:limit]


def distribution(values: Sequence[float | None]) -> dict[str, float | int | None]:
    parsed = sorted(float(value) for value in values if value is not None)
    if not parsed:
        return {
            "count": 0,
            "min": None,
            "p10": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p90": None,
            "max": None,
            "mean": None,
        }
    return {
        "count": len(parsed),
        "min": round(parsed[0], 6),
        "p10": percentile(parsed, 0.10),
        "p25": percentile(parsed, 0.25),
        "median": percentile(parsed, 0.50),
        "p75": percentile(parsed, 0.75),
        "p90": percentile(parsed, 0.90),
        "max": round(parsed[-1], 6),
        "mean": round(sum(parsed) / len(parsed), 6),
    }


def percentile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    index = round((len(sorted_values) - 1) * max(0.0, min(1.0, float(q))))
    return round(float(sorted_values[index]), 6)


def word_difficulty(row: Mapping[str, object]) -> float | None:
    corrected = safe_float(row.get("corrected_difficulty"))
    if corrected is not None:
        return corrected
    return safe_float(row.get("runtime_difficulty_estimate"))


def difficulty_minus_proficiency(
    row: Mapping[str, object],
    proficiency: float | None,
) -> float | None:
    difficulty = word_difficulty(row)
    if difficulty is None or proficiency is None:
        return None
    return difficulty - proficiency


def finding(
    level: str,
    code: str,
    message: str,
    details: object | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"level": level, "code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return payload


def summarize_findings(findings: Sequence[Mapping[str, object]]) -> dict[str, Any]:
    counts = Counter(str(finding.get("level") or "").upper() for finding in findings)
    fail_count = int(counts.get("FAIL", 0))
    warn_count = int(counts.get("WARN", 0))
    return {
        "status": "FAIL" if fail_count else "WARN" if warn_count else "PASS",
        "pass_count": int(counts.get("PASS", 0)),
        "warn_count": warn_count,
        "fail_count": fail_count,
    }


def signal_value(signals: Mapping[str, object], key: str) -> float | None:
    return rounded_or_none(safe_float(signals.get(key)))


def safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def int_or_none(value: object) -> int | None:
    parsed = safe_float(value)
    if parsed is None:
        return None
    return int(parsed)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def share(numerator: object, denominator: object) -> float:
    parsed_denominator = safe_float(denominator)
    parsed_numerator = safe_float(numerator)
    if not parsed_denominator or parsed_numerator is None:
        return 0.0
    return round(parsed_numerator / parsed_denominator, 6)


def rounded_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def fmt(value: object) -> str:
    parsed = safe_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.3f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate randomized en-es SRS admission UX samples."
    )
    parser.add_argument("--config-json", type=Path, default=DEFAULT_CONFIG_JSON)
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--overlay-source-path", type=Path, default=DEFAULT_OVERLAY_SOURCE_PATH)
    parser.add_argument("--corrected-ranking-csv", type=Path, default=DEFAULT_CORRECTED_RANKING_CSV)
    parser.add_argument("--taxonomy-json", type=Path, default=DEFAULT_TAXONOMY_JSON)
    parser.add_argument("--scenario-filter", default="")
    parser.add_argument("--set-top-n", type=int)
    parser.add_argument("--initial-active-count", type=int)
    parser.add_argument("--preview-count", type=int, default=DEFAULT_PREVIEW_COUNT)
    parser.add_argument(
        "--preview-sampling-mode",
        choices=("reserved_topic_lane", "weighted_without_replacement", "ranked"),
        default="reserved_topic_lane",
    )
    parser.add_argument("--draw-count", type=int, default=DEFAULT_DRAW_COUNT)
    parser.add_argument("--random-seed", type=int)
    parser.add_argument(
        "--markdown-word-limit-per-draw",
        type=int,
        default=DEFAULT_MARKDOWN_WORD_LIMIT_PER_DRAW,
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenario_filter = tuple(
        part.strip() for part in str(args.scenario_filter or "").split(",") if part.strip()
    )
    report = build_report(
        config_json=Path(args.config_json).expanduser(),
        pair=str(args.pair or DEFAULT_PAIR),
        frequency_db=args.frequency_db,
        overlay_source_path=args.overlay_source_path,
        corrected_ranking_csv=args.corrected_ranking_csv,
        taxonomy_json=args.taxonomy_json,
        scenario_filter=scenario_filter,
        set_top_n=args.set_top_n,
        initial_active_count=args.initial_active_count,
        preview_count=args.preview_count,
        preview_sampling_mode=args.preview_sampling_mode,
        draw_count=args.draw_count,
        random_seed=args.random_seed,
        markdown_word_limit_per_draw=args.markdown_word_limit_per_draw,
    )
    write_report(report, json_out=Path(args.json_out), markdown_out=Path(args.markdown_out))
    summary = dict(report["summary"])
    params = dict(report["parameters"])
    print(f"json_out: {args.json_out}")
    print(f"markdown_out: {args.markdown_out}")
    print(
        "summary: "
        f"status={summary['status']} pass={summary['pass_count']} "
        f"warn={summary['warn_count']} fail={summary['fail_count']} "
        f"draws={summary['draw_count_total']} root_seed={params['root_random_seed']}"
    )
    return 1 if summary["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
