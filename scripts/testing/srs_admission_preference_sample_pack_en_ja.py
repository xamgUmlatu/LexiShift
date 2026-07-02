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
from lexishift_core.srs.set_strategy import STRATEGY_PROFILE_BOOTSTRAP  # noqa: E402
from lexishift_core.srs.topic_overlay import EN_JA_JMDICT_OVERLAY_FILENAME  # noqa: E402
from lexishift_core.srs.learner_difficulty import (  # noqa: E402
    CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV,
    CorrectedLearnerDifficultyMatch,
    clear_corrected_learner_difficulty_cache,
    lookup_corrected_en_ja_learner_difficulty,
    resolve_corrected_en_ja_learner_difficulty_csv_path,
)

REPORT_SCHEMA_VERSION = 1
DEFAULT_PAIR = "en-ja"
DEFAULT_CONFIG_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_admission_preference_sample_configs_en_ja.json"
)
DEFAULT_PROMOTION_OVERLAY_SOURCE_FILENAME = "srs_topic_autotag_promotion_overlay_en_ja_latest.json"
DEFAULT_OVERLAY_SOURCE_PATH = (
    PROJECT_ROOT / "docs" / "test_outputs" / DEFAULT_PROMOTION_OVERLAY_SOURCE_FILENAME
)
DEFAULT_CORRECTED_RANKING_CSV = resolve_corrected_en_ja_learner_difficulty_csv_path() or (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_en_ja_latest.csv"
)
DEFAULT_TAXONOMY_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_topic_preference_taxonomy_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_admission_preference_sample_pack_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_preference_sample_pack_en_ja_latest.md"
)
RUNTIME_OVERLAY_MIN_MEMBERSHIP = 1.0
MARKDOWN_WORD_LIMIT = 20


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


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


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def resolve_live_resources(
    *,
    pair: str,
    frequency_db: Path | None,
    jmdict_path: Path | None,
) -> tuple[Path, Path]:
    live_paths = build_helper_paths()
    resolved_jmdict, _translation, resolved_frequency = resolve_pair_resources(
        live_paths,
        pair=pair,
        jmdict_path=jmdict_path,
        translation_dict_path=None,
        set_source_db=frequency_db,
    )
    if resolved_frequency is None:
        raise ValueError(f"Could not resolve a default frequency DB for {pair}.")
    if resolved_jmdict is None:
        raise ValueError(f"Could not resolve a default JMDict path for {pair}.")
    if not resolved_frequency.exists():
        raise FileNotFoundError(resolved_frequency)
    if not resolved_jmdict.exists():
        raise FileNotFoundError(resolved_jmdict)
    return resolved_frequency, resolved_jmdict


def copy_overlay_source(paths: object, overlay_source_path: Path | None) -> Path | None:
    if overlay_source_path is None:
        return None
    source = overlay_source_path.expanduser()
    if not source.exists():
        return None
    srs_dir = getattr(paths, "srs_dir")
    target = Path(srs_dir) / "topic_overlays" / EN_JA_JMDICT_OVERLAY_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def inspect_overlay(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "path": None,
            "exists": False,
            "status": "missing",
            "row_count": 0,
            "runtime_supported_row_count": 0,
            "topics": [],
        }
    if not path.exists():
        return {
            "path": str(path),
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
    path: Path | None, overlay_inventory: Mapping[str, object]
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
                "axis": str(family.get("axis") or ""),
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


@contextmanager
def corrected_ranking_runtime_env(path: Path | None):
    previous = os.environ.get(CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV)
    clear_corrected_learner_difficulty_cache()
    if path is not None and path.exists():
        os.environ[CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV] = str(path)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV, None)
        else:
            os.environ[CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV] = previous
        clear_corrected_learner_difficulty_cache()


def int_or_none(value: object) -> int | None:
    parsed = safe_float(value)
    if parsed is None:
        return None
    return int(parsed)


def build_report(
    *,
    config_json: Path,
    pair: str,
    frequency_db: Path | None,
    jmdict_path: Path | None,
    overlay_source_path: Path | None,
    corrected_ranking_csv: Path | None,
    taxonomy_json: Path | None,
    scenario_filter: Sequence[str],
    set_top_n: int | None,
    initial_active_count: int | None,
    preview_count: int | None,
    preview_sampling_mode: str | None,
    preview_seed: int | None,
) -> dict[str, Any]:
    config = load_json_mapping(config_json)
    defaults = dict(config.get("defaults") or {})
    resolved_set_top_n = int(set_top_n or defaults.get("set_top_n") or 10000)
    resolved_initial_active_count = int(
        initial_active_count or defaults.get("initial_active_count") or 80
    )
    resolved_preview_count = int(preview_count or defaults.get("preview_count") or 40)
    resolved_preview_sampling_mode = str(
        preview_sampling_mode or defaults.get("preview_sampling_mode") or "reserved_topic_lane"
    )
    resolved_preview_seed = (
        int(preview_seed)
        if preview_seed is not None
        else int(defaults.get("preview_seed") or 314159)
    )
    selected_scenarios = filter_scenarios(
        [row for row in config.get("scenarios", []) if isinstance(row, Mapping)],
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
    overlay_inventory = inspect_overlay(resolved_overlay_source_path)
    taxonomy_summary = load_taxonomy_summary(taxonomy_json, overlay_inventory)
    corrected_ranking = load_corrected_ranking(corrected_ranking_csv)

    with tempfile.TemporaryDirectory(prefix="lexishift-srs-enja-pref-pack-") as tmp:
        paths = build_helper_paths(Path(tmp))
        copied_overlay_path = copy_overlay_source(paths, resolved_overlay_source_path)
        with corrected_ranking_runtime_env(corrected_ranking_csv):
            scenario_reports = [
                run_scenario(
                    paths=paths,
                    pair=pair,
                    frequency_db=resolved_frequency_db,
                    jmdict_path=resolved_jmdict_path,
                    scenario=scenario,
                    set_top_n=resolved_set_top_n,
                    initial_active_count=resolved_initial_active_count,
                    preview_count=resolved_preview_count,
                    preview_sampling_mode=resolved_preview_sampling_mode,
                    preview_seed=resolved_preview_seed,
                    corrected_ranking=corrected_ranking,
                    corrected_ranking_csv=corrected_ranking_csv,
                )
                for scenario in selected_scenarios
            ]

    comparisons = build_comparisons(scenario_reports)
    findings = build_findings(
        scenario_reports=scenario_reports,
        overlay_inventory=overlay_inventory,
        corrected_ranking_available=bool(corrected_ranking),
    )
    summary = summarize_findings(findings)
    summary.update(
        {
            "scenario_count": len(scenario_reports),
            "topic_scenario_count": sum(
                1 for scenario in scenario_reports if scenario.get("requested_topics")
            ),
            "topic_scenarios_with_movers": sum(
                1
                for scenario in scenario_reports
                if scenario.get("requested_topics") and int(scenario.get("topic_mover_count") or 0)
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
        "runtime_scope": "admission_preview_only",
        "method": {
            "strategy": STRATEGY_PROFILE_BOOTSTRAP,
            "profile_shape": "single proficiency estimate plus optional topic_weights/interests",
            "sampling_mode": resolved_preview_sampling_mode,
            "runtime_difficulty_source": (
                "profile_bootstrap uses the corrected en-ja learner-difficulty CSV through "
                "an explicit runtime hook when the CSV is available; otherwise it falls back "
                "to runtime commonness signals."
            ),
            "state_mutation": "none; previews run under a temporary helper data root",
        },
        "parameters": {
            "set_top_n": resolved_set_top_n,
            "initial_active_count": resolved_initial_active_count,
            "preview_count": resolved_preview_count,
            "preview_sampling_mode": resolved_preview_sampling_mode,
            "preview_seed": resolved_preview_seed,
        },
        "inputs": {
            "config_json": str(config_json),
            "frequency_db": str(resolved_frequency_db),
            "jmdict": str(resolved_jmdict_path),
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
        "comparisons": comparisons,
        "scenarios": scenario_reports,
    }


def filter_scenarios(
    scenarios: Sequence[Mapping[str, object]],
    *,
    scenario_filter: Sequence[str],
) -> list[Mapping[str, object]]:
    wanted = {str(name).strip() for name in scenario_filter if str(name).strip()}
    if not wanted:
        return list(scenarios)
    return [scenario for scenario in scenarios if str(scenario.get("name") or "") in wanted]


def run_scenario(
    *,
    paths: object,
    pair: str,
    frequency_db: Path,
    jmdict_path: Path,
    scenario: Mapping[str, object],
    set_top_n: int,
    initial_active_count: int,
    preview_count: int,
    preview_sampling_mode: str,
    preview_seed: int,
    corrected_ranking: Mapping[str, Mapping[str, object]],
    corrected_ranking_csv: Path | None,
) -> dict[str, Any]:
    profile_context = build_profile_context(scenario)
    payload = preview_srs_admission(
        paths,
        config=SetAdmissionPreviewJobConfig(
            pair=pair,
            jmdict_path=jmdict_path,
            set_source_db=frequency_db,
            strategy=STRATEGY_PROFILE_BOOTSTRAP,
            set_top_n=set_top_n,
            initial_active_count=initial_active_count,
            preview_count=preview_count,
            preview_sampling_mode=preview_sampling_mode,
            preview_seed=preview_seed,
            profile_context=profile_context,
            trigger="preference_sample_pack",
        ),
    )
    preview = dict(payload.get("preview") or {})
    profile_bootstrap = dict(preview.get("profile_bootstrap") or {})
    admitted_words = [
        simplify_admitted_word(
            entry,
            corrected_ranking=corrected_ranking,
            corrected_ranking_csv=corrected_ranking_csv,
        )
        for entry in preview.get("admitted_words", ())
        if isinstance(entry, Mapping)
    ]
    topic_movers = [entry for entry in admitted_words if entry.get("topic_affinity_source")]
    requested_topics = list(normalize_weight_map(scenario.get("topic_weights")).keys())
    overlay = summarize_overlay(dict(profile_bootstrap.get("profile_topic_overlay") or {}))
    topic_counts = topic_mover_counts(topic_movers)
    return {
        "name": str(scenario.get("name") or ""),
        "description": str(scenario.get("description") or ""),
        "proficiency": safe_float(scenario.get("proficiency")),
        "requested_topics": requested_topics,
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
        "topic_mover_counts": topic_counts,
        "top_topic_movers": topic_movers[:10],
        "difficulty_mismatch_count": sum(
            1 for entry in admitted_words if bool(entry.get("difficulty_mismatch_large"))
        ),
        "active_topic_support": summarize_active_topic_support(
            profile_bootstrap.get("active_topic_support")
        ),
        "topic_depth_by_level": summarize_topic_depth(
            profile_bootstrap.get("topic_depth_by_level")
        ),
        "profile_topic_overlay": overlay,
    }


def summarize_plan(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    keys = ("strategy_requested", "strategy_effective", "execution_mode", "can_execute")
    return {key: value.get(key) for key in keys if key in value}


def simplify_admitted_word(
    entry: Mapping[str, object],
    *,
    corrected_ranking: Mapping[str, Mapping[str, object]],
    corrected_ranking_csv: Path | None,
) -> dict[str, Any]:
    signals = entry.get("signals") if isinstance(entry.get("signals"), Mapping) else {}
    traits = (
        entry.get("candidate_traits") if isinstance(entry.get("candidate_traits"), Mapping) else {}
    )
    lemma = str(entry.get("lemma") or "")
    corrected = corrected_match_to_dict(
        lookup_corrected_en_ja_learner_difficulty(
            lemma=lemma,
            reading_candidates=tuple(traits.get("lexical_forms") or ()),
            csv_path=corrected_ranking_csv,
        )
    )
    if not corrected:
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
        "corrected_match_mode": corrected.get("corrected_match_mode"),
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


def corrected_match_to_dict(
    match: CorrectedLearnerDifficultyMatch | None,
) -> dict[str, object]:
    if match is None:
        return {}
    row = match.row
    return {
        "corrected_rank": row.rank,
        "reading": row.reading or None,
        "corrected_difficulty": row.score,
        "corrected_band": row.band,
        "candidate_state": row.candidate_state,
        "correction_types": ",".join(row.correction_types) or None,
        "display_form": row.display_form,
        "admission_override": row.admission_override,
        "topic_stretch_allowed": row.topic_stretch_allowed,
        "manual_correction_active": row.manual_correction_active,
        "corrected_match_mode": match.match_mode,
    }


def signal_value(signals: Mapping[str, object], key: str) -> float | None:
    return rounded_or_none(safe_float(signals.get(key)))


def rounded_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def topic_mover_counts(topic_movers: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in topic_movers:
        source = str(row.get("topic_affinity_source") or "")
        if source.startswith("topic_hint:"):
            topic = source.removeprefix("topic_hint:").split("->")[-1]
            counts[topic] += 1
        elif source.startswith("lexical:"):
            counts[source] += 1
    return dict(sorted(counts.items()))


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
    for topic_entry in value.get("topics", ()):
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
                "hardest_examples": list(topic_entry.get("hardest_examples") or [])[:5],
            }
        )
    return {
        "version": value.get("version"),
        "difficulty_proxy": value.get("difficulty_proxy"),
        "total_candidates": value.get("total_candidates"),
        "active_topic_count": value.get("active_topic_count"),
        "topics": topics,
    }


def summarize_overlay(overlay: Mapping[str, object]) -> dict[str, Any]:
    if not overlay:
        return {}
    keys = (
        "status",
        "reason",
        "application_status",
        "runtime_scope",
        "requested_topics",
        "supported_topics",
        "active_topics",
        "available_row_count",
        "applicable_row_count",
        "eligible_row_count",
        "matched_eligible_lemma_count",
        "unmatched_eligible_lemma_count",
        "matched_seed_count",
        "applied_seed_count",
        "applied_row_count",
        "applied_topics",
        "source_path",
        "promotion_state",
    )
    return {key: overlay.get(key) for key in keys if key in overlay}


def build_comparisons(scenarios: Sequence[Mapping[str, object]]) -> dict[str, Any]:
    neutrals_by_proficiency: dict[float, Mapping[str, object]] = {}
    for scenario in scenarios:
        if scenario.get("requested_topics"):
            continue
        proficiency = safe_float(scenario.get("proficiency"))
        if proficiency is not None:
            neutrals_by_proficiency[round(proficiency, 2)] = scenario
    comparisons: dict[str, Any] = {}
    for scenario in scenarios:
        if not scenario.get("requested_topics"):
            continue
        neutral = nearest_neutral(
            safe_float(scenario.get("proficiency")),
            neutrals_by_proficiency,
        )
        if neutral is None:
            continue
        name = str(scenario.get("name") or "")
        neutral_name = str(neutral.get("name") or "")
        top_lemmas = list(scenario.get("top_lemmas") or [])
        neutral_lemmas = list(neutral.get("top_lemmas") or [])
        comparisons[f"{name}_vs_{neutral_name}"] = {
            "scenario": name,
            "neutral_reference": neutral_name,
            "introduced_lemmas": [lemma for lemma in top_lemmas if lemma not in neutral_lemmas],
            "removed_neutral_lemmas": [
                lemma for lemma in neutral_lemmas if lemma not in top_lemmas
            ],
            "overlap_count": len(set(top_lemmas) & set(neutral_lemmas)),
            "topic_mover_count_delta": int(scenario.get("topic_mover_count") or 0)
            - int(neutral.get("topic_mover_count") or 0),
        }
    return comparisons


def nearest_neutral(
    proficiency: float | None,
    neutrals_by_proficiency: Mapping[float, Mapping[str, object]],
) -> Mapping[str, object] | None:
    if not neutrals_by_proficiency:
        return None
    if proficiency is None:
        return next(iter(neutrals_by_proficiency.values()))
    nearest_key = min(neutrals_by_proficiency, key=lambda value: abs(value - proficiency))
    return neutrals_by_proficiency[nearest_key]


def build_findings(
    *,
    scenario_reports: Sequence[Mapping[str, object]],
    overlay_inventory: Mapping[str, object],
    corrected_ranking_available: bool,
) -> list[dict[str, Any]]:
    findings = [
        finding(
            "PASS" if overlay_inventory.get("exists") else "WARN",
            "TOPIC_OVERLAY_AVAILABLE",
            "Product-shaped en-ja topic overlay was available for preview."
            if overlay_inventory.get("exists")
            else "No product-shaped en-ja topic overlay was available.",
            {
                "row_count": overlay_inventory.get("row_count"),
                "runtime_supported_row_count": overlay_inventory.get("runtime_supported_row_count"),
            },
        ),
        finding(
            "PASS" if corrected_ranking_available else "WARN",
            "CORRECTED_RANKING_DIAGNOSTIC_AVAILABLE",
            "Corrected learner-difficulty ranking was joined for diagnostics."
            if corrected_ranking_available
            else "Corrected learner-difficulty ranking was not available.",
        ),
    ]
    for scenario in scenario_reports:
        requested_topics = list(scenario.get("requested_topics") or [])
        if not requested_topics:
            findings.append(
                finding(
                    "PASS",
                    f"NEUTRAL_PROFILE_PREVIEW:{scenario.get('name')}",
                    "Neutral profile generated an admission preview.",
                    {"sample_count": len(scenario.get("admitted_words") or [])},
                )
            )
            continue
        overlay = dict(scenario.get("profile_topic_overlay") or {})
        topic_mover_count = int(scenario.get("topic_mover_count") or 0)
        if overlay.get("application_status") == "applied" and topic_mover_count > 0:
            level = "PASS"
            message = "Topic preference produced runtime topic movers."
        elif overlay.get("status") == "unavailable":
            level = "WARN"
            message = "Requested topic is unsupported by the current runtime overlay."
        elif overlay.get("application_status"):
            level = "WARN"
            message = "Topic overlay was present but produced no admitted topic movers."
        else:
            level = "WARN"
            message = "Topic preference did not activate an overlay."
        findings.append(
            finding(
                level,
                f"TOPIC_PROFILE_PREVIEW:{scenario.get('name')}",
                message,
                {
                    "requested_topics": requested_topics,
                    "topic_mover_count": topic_mover_count,
                    "overlay_status": overlay.get("status"),
                    "application_status": overlay.get("application_status"),
                    "active_topics": overlay.get("active_topics"),
                    "applied_seed_count": overlay.get("applied_seed_count"),
                },
            )
        )
    return findings


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
    counts = Counter(str(item.get("level") or "").upper() for item in findings)
    fail_count = int(counts.get("FAIL", 0))
    warn_count = int(counts.get("WARN", 0))
    return {
        "status": "FAIL" if fail_count else "WARN" if warn_count else "PASS",
        "pass_count": int(counts.get("PASS", 0)),
        "warn_count": warn_count,
        "fail_count": fail_count,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = dict(report.get("summary") or {})
    params = dict(report.get("parameters") or {})
    inputs = dict(report.get("inputs") or {})
    lines = [
        "# en-ja SRS Admission Preference Sample Pack",
        "",
        f"- status: `{summary.get('status')}`",
        (
            "- findings: "
            f"pass={summary.get('pass_count')} "
            f"warn={summary.get('warn_count')} "
            f"fail={summary.get('fail_count')}"
        ),
        f"- scenarios: `{summary.get('scenario_count')}`",
        f"- topic scenarios with movers: `{summary.get('topic_scenarios_with_movers')}` / `{summary.get('topic_scenario_count')}`",
        f"- runtime scope: `{report.get('runtime_scope')}`",
        "",
        "## Method",
        "",
        f"- strategy: `{dict(report.get('method') or {}).get('strategy')}`",
        f"- profile shape: {dict(report.get('method') or {}).get('profile_shape')}",
        f"- runtime difficulty source: {dict(report.get('method') or {}).get('runtime_difficulty_source')}",
        f"- state mutation: {dict(report.get('method') or {}).get('state_mutation')}",
        "",
        "## Inputs",
        "",
        f"- config_json: `{inputs.get('config_json')}`",
        f"- frequency_db: `{inputs.get('frequency_db')}`",
        f"- jmdict: `{inputs.get('jmdict')}`",
        f"- overlay_source_path: `{inputs.get('overlay_source_path')}`",
        f"- corrected_ranking_available: `{inputs.get('corrected_ranking_available')}`",
        f"- set_top_n: `{params.get('set_top_n')}`",
        f"- initial_active_count: `{params.get('initial_active_count')}`",
        f"- preview_count: `{params.get('preview_count')}`",
        f"- preview_sampling_mode: `{params.get('preview_sampling_mode')}`",
        "",
    ]
    lines.extend(render_overlay_inventory(report.get("overlay_inventory")))
    lines.extend(render_taxonomy_summary(report.get("taxonomy_summary")))
    lines.extend(
        [
            "## Scenario Summary",
            "",
            "| Scenario | Proficiency | Topics | Topic Movers | Overlay | Difficulty Mismatches | Top Lemmas |",
            "| --- | ---: | --- | ---: | --- | ---: | --- |",
        ]
    )
    for scenario in report.get("scenarios", ()):
        if not isinstance(scenario, Mapping):
            continue
        overlay = dict(scenario.get("profile_topic_overlay") or {})
        topics = ", ".join(str(topic) for topic in scenario.get("requested_topics", [])) or "-"
        top_lemmas = ", ".join(str(value) for value in list(scenario.get("top_lemmas") or [])[:8])
        overlay_label = str(overlay.get("application_status") or overlay.get("status") or "-")
        lines.append(
            f"| `{scenario.get('name')}` | {fmt(scenario.get('proficiency'))} | "
            f"{topics} | {scenario.get('topic_mover_count')} | {overlay_label} | "
            f"{scenario.get('difficulty_mismatch_count')} | {top_lemmas} |"
        )
    lines.extend(["", "## Findings", ""])
    for item in report.get("findings", ()):
        if not isinstance(item, Mapping):
            continue
        lines.append(f"- `{item.get('level')}` `{item.get('code')}`: {item.get('message')}")
    lines.extend(["", "## Scenario Details", ""])
    for scenario in report.get("scenarios", ()):
        if not isinstance(scenario, Mapping):
            continue
        lines.extend(render_scenario_detail(scenario))
    return "\n".join(lines).rstrip() + "\n"


def render_overlay_inventory(value: object) -> list[str]:
    overlay = dict(value or {}) if isinstance(value, Mapping) else {}
    lines = [
        "## Overlay Inventory",
        "",
        f"- status: `{overlay.get('status')}`",
        f"- overlay_id: `{overlay.get('overlay_id')}`",
        f"- row_count: `{overlay.get('row_count')}`",
        f"- runtime_supported_row_count: `{overlay.get('runtime_supported_row_count')}`",
        f"- runtime_min_membership: `{overlay.get('runtime_min_membership')}`",
        "",
        "| Topic | Rows | Runtime-Supported Rows |",
        "| --- | ---: | ---: |",
    ]
    for topic in overlay.get("topics", []):
        if not isinstance(topic, Mapping):
            continue
        lines.append(
            f"| `{topic.get('topic')}` | {topic.get('row_count')} | "
            f"{topic.get('runtime_supported_row_count')} |"
        )
    lines.append("")
    return lines


def render_taxonomy_summary(value: object) -> list[str]:
    taxonomy = dict(value or {}) if isinstance(value, Mapping) else {}
    lines = [
        "## Taxonomy Coverage",
        "",
        "| Family | Readiness | Overlay Rows | Runtime-Supported Rows |",
        "| --- | --- | ---: | ---: |",
    ]
    for family in taxonomy.get("families", []):
        if not isinstance(family, Mapping):
            continue
        lines.append(
            f"| `{family.get('id')}` | `{family.get('readiness_state')}` | "
            f"{family.get('overlay_row_count')} | {family.get('runtime_supported_row_count')} |"
        )
    lines.append("")
    return lines


def render_scenario_detail(scenario: Mapping[str, object]) -> list[str]:
    lines = [
        f"### `{scenario.get('name')}`",
        "",
        str(scenario.get("description") or ""),
        "",
    ]
    overlay = dict(scenario.get("profile_topic_overlay") or {})
    if overlay:
        lines.extend(
            [
                "- overlay: "
                f"status=`{overlay.get('status')}` "
                f"application=`{overlay.get('application_status')}` "
                f"active_topics=`{overlay.get('active_topics')}` "
                f"applied_seed_count=`{overlay.get('applied_seed_count')}`",
                "",
            ]
        )
    active_support = dict(scenario.get("active_topic_support") or {})
    support_topics = [
        entry for entry in active_support.get("topics", []) if isinstance(entry, Mapping)
    ]
    if support_topics:
        lines.extend(["Active topic support:", ""])
        for entry in support_topics:
            lines.append(
                "- "
                f"`{entry.get('topic')}` candidates={entry.get('candidate_count')} "
                f"mass={entry.get('support_mass')} "
                f"scarcity={entry.get('scarcity_readiness')} "
                f"examples={', '.join(str(v) for v in list(entry.get('top_examples') or [])[:5])}"
            )
        lines.append("")
    lines.extend(
        [
            "| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |",
            "| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |",
        ]
    )
    for index, word in enumerate(
        [row for row in scenario.get("admitted_words", []) if isinstance(row, Mapping)][
            :MARKDOWN_WORD_LIMIT
        ],
        start=1,
    ):
        corrected = fmt(word.get("corrected_difficulty"))
        runtime = fmt(word.get("runtime_difficulty_estimate"))
        topic = str(word.get("topic_affinity_source") or "")
        ready = fmt(word.get("readiness_multiplier"))
        base_to_rerank = f"{word.get('base_rank')} -> {word.get('reranked_rank')}"
        note = str(word.get("explanation") or "")
        lines.append(
            f"| {index} | `{word.get('lemma')}` | {word.get('reading') or ''} | "
            f"{corrected} | {runtime} | {topic} | {ready} | {base_to_rerank} | {note} |"
        )
    lines.append("")
    return lines


def fmt(value: object) -> str:
    parsed = safe_float(value)
    if parsed is None:
        return "-"
    return f"{parsed:.3f}"


def write_report(report: Mapping[str, object], *, json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate en-ja SRS admission samples for predefined user preference profiles."
    )
    parser.add_argument("--config-json", type=Path, default=DEFAULT_CONFIG_JSON)
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--jmdict", type=Path)
    parser.add_argument("--overlay-source-path", type=Path)
    parser.add_argument("--corrected-ranking-csv", type=Path, default=DEFAULT_CORRECTED_RANKING_CSV)
    parser.add_argument("--taxonomy-json", type=Path, default=DEFAULT_TAXONOMY_JSON)
    parser.add_argument("--scenario-filter", default="")
    parser.add_argument("--set-top-n", type=int)
    parser.add_argument("--initial-active-count", type=int)
    parser.add_argument("--preview-count", type=int)
    parser.add_argument(
        "--preview-sampling-mode",
        choices=("ranked", "reserved_topic_lane", "weighted_without_replacement"),
    )
    parser.add_argument("--preview-seed", type=int)
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
        taxonomy_json=args.taxonomy_json,
        scenario_filter=scenario_filter,
        set_top_n=args.set_top_n,
        initial_active_count=args.initial_active_count,
        preview_count=args.preview_count,
        preview_sampling_mode=args.preview_sampling_mode,
        preview_seed=args.preview_seed,
    )
    write_report(report, json_out=args.json_out, markdown_out=args.markdown_out)
    summary = dict(report["summary"])
    print(f"json_out: {args.json_out}")
    print(f"markdown_out: {args.markdown_out}")
    print(
        "summary: "
        f"status={summary['status']} pass={summary['pass_count']} "
        f"warn={summary['warn_count']} fail={summary['fail_count']}"
    )
    return 1 if summary["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
