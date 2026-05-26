#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import math
from pathlib import Path
import random
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from srs_admission_preference_preview_en_es import (  # noqa: E402
    DEFAULT_PAIR,
    DEFAULT_SET_TOP_N,
    DEFAULT_ZIPF_BRIDGE_PATH,
    build_report as build_preference_preview_report,
)
from srs_admission_calibration_markdown import render_markdown, write_report  # noqa: E402,F401

REPORT_SCHEMA_VERSION = 1
DEFAULT_WEIGHTED_SEEDS = (11, 23, 37)
DEFAULT_ADMISSION_BUDGET = 10
DEFAULT_TOP_K_WINDOW, DEFAULT_TOPIC_LANE_MAX_SHARE = 60, 0.5
TEST_OUTPUTS_DIR = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_JSON_OUT = TEST_OUTPUTS_DIR / "srs_admission_calibration_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_DIR / "srs_admission_calibration_en_es_latest.md"


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_report(
    *,
    pair: str = DEFAULT_PAIR,
    frequency_db: Path | None = None,
    overlay_source_path: Path | None = None,
    overlay_source_paths: Sequence[Path] | None = None,
    set_top_n: int = DEFAULT_SET_TOP_N,
    admission_budget: int = DEFAULT_ADMISSION_BUDGET,
    top_k_window: int = DEFAULT_TOP_K_WINDOW,
    topic_lane_max_share: float = DEFAULT_TOPIC_LANE_MAX_SHARE,
    weighted_seeds: Sequence[int] = DEFAULT_WEIGHTED_SEEDS,
    augment_with_zipf_bridge: bool = True,
    zipf_bridge_path: Path | None = DEFAULT_ZIPF_BRIDGE_PATH,
    kaikki_forward_db: Path | None = None,
) -> dict[str, Any]:
    budget = max(1, int(admission_budget))
    ranked_preview = build_preference_preview_report(
        pair=pair,
        frequency_db=frequency_db,
        overlay_source_path=overlay_source_path,
        overlay_source_paths=overlay_source_paths,
        set_top_n=set_top_n,
        initial_active_count=budget,
        preview_count=budget,
        preview_sampling_mode="ranked",
        preview_seed=None,
        augment_with_zipf_bridge=augment_with_zipf_bridge,
        zipf_bridge_path=zipf_bridge_path,
        kaikki_forward_db=kaikki_forward_db,
    )
    weighted_previews = [
        build_preference_preview_report(
            pair=pair,
            frequency_db=frequency_db,
            overlay_source_path=overlay_source_path,
            overlay_source_paths=overlay_source_paths,
            set_top_n=set_top_n,
            initial_active_count=budget,
            preview_count=budget,
            preview_sampling_mode="weighted_without_replacement",
            preview_seed=int(seed),
            augment_with_zipf_bridge=augment_with_zipf_bridge,
            zipf_bridge_path=zipf_bridge_path,
            kaikki_forward_db=kaikki_forward_db,
        )
        for seed in weighted_seeds
    ]
    ranked_window_preview = build_preference_preview_report(
        pair=pair,
        frequency_db=frequency_db,
        overlay_source_path=overlay_source_path,
        overlay_source_paths=overlay_source_paths,
        set_top_n=set_top_n,
        initial_active_count=max(budget, int(top_k_window)),
        preview_count=max(budget, int(top_k_window)),
        preview_sampling_mode="ranked",
        preview_seed=None,
        augment_with_zipf_bridge=augment_with_zipf_bridge,
        zipf_bridge_path=zipf_bridge_path,
        kaikki_forward_db=kaikki_forward_db,
    )

    ranked_rows = _scenario_rows(ranked_preview)
    weighted_rows_by_seed = [
        {"seed": int(seed), "rows": _scenario_rows(preview)}
        for seed, preview in zip(weighted_seeds, weighted_previews, strict=True)
    ]
    weighted_summary_rows = _weighted_summary_rows(weighted_rows_by_seed)
    top_k_rows_by_seed = _simulate_top_k_rows_by_seed(
        ranked_window_preview,
        budget=budget,
        weighted_seeds=weighted_seeds,
    )
    top_k_summary_rows = _weighted_summary_rows(top_k_rows_by_seed)
    topic_lane_rows = _simulate_topic_lane_rows(
        ranked_window_preview,
        budget=budget,
        topic_lane_max_share=topic_lane_max_share,
    )
    comparisons = _build_comparisons(
        ranked_rows=ranked_rows,
        weighted_rows=weighted_summary_rows,
        top_k_rows=top_k_summary_rows,
        topic_lane_rows=topic_lane_rows,
    )
    findings = _build_findings(
        ranked_preview=ranked_preview,
        weighted_previews=weighted_previews,
        comparisons=comparisons,
    )
    summary = _summarize_findings(findings)
    summary.update(
        {
            "scenario_count": len(ranked_rows),
            "admission_budget": budget,
            "top_k_window": max(budget, int(top_k_window)),
            "weighted_seed_count": len(tuple(weighted_seeds)),
            "source_topic_scenarios_with_ranked_share": sum(
                1
                for row in ranked_rows
                if row["name"] != "neutral" and float(row["selected_topic_share"]) > 0.0
            ),
        }
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": now_iso_utc(),
        "pair": pair,
        "runtime_scope": "admission_calibration_preview_only",
        "interpretation": {
            "ranked_selected_topic_share": (
                "Deterministic share of the preview admission batch that matched active "
                "profile topics."
            ),
            "weighted_selected_topic_share": (
                "Empirical share across seeded weighted-without-replacement preview batches; "
                "use as a calibration signal, not a product guarantee."
            ),
            "mutation": "No product SRS store is mutated; previews run in temporary helper roots.",
        },
        "parameters": {
            "set_top_n": int(set_top_n),
            "admission_budget": budget,
            "top_k_window": max(budget, int(top_k_window)),
            "topic_lane_max_share": round(float(topic_lane_max_share), 6),
            "weighted_seeds": [int(seed) for seed in weighted_seeds],
            "augment_with_zipf_bridge": bool(augment_with_zipf_bridge),
        },
        "inputs": ranked_preview.get("inputs", {}),
        "source_summary": ranked_preview.get("source_summary", {}),
        "base_source_summary": ranked_preview.get("base_source_summary", {}),
        "source_augmentation": ranked_preview.get("source_augmentation", {}),
        "summary": summary,
        "findings": findings,
        "comparisons": comparisons,
        "ranked_rows": ranked_rows,
        "weighted_rows": weighted_summary_rows,
        "weighted_rows_by_seed": weighted_rows_by_seed,
        "top_k_weighted_rows": top_k_summary_rows,
        "topic_lane_rows": topic_lane_rows,
    }


def _scenario_rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    neutral = next(
        (scenario for scenario in report.get("scenarios", ()) if scenario.get("name") == "neutral"),
        {},
    )
    neutral_lemmas = [str(lemma) for lemma in neutral.get("top_lemmas", ())]
    return [
        _scenario_row(scenario, neutral_lemmas=neutral_lemmas)
        for scenario in report.get("scenarios", ())
        if isinstance(scenario, Mapping)
    ]


def _scenario_row(
    scenario: Mapping[str, Any],
    *,
    neutral_lemmas: Sequence[str],
) -> dict[str, Any]:
    admitted_words = [
        dict(row) for row in scenario.get("admitted_words", ()) if isinstance(row, Mapping)
    ]
    return _scenario_row_from_words(
        scenario,
        admitted_words=admitted_words,
        neutral_lemmas=neutral_lemmas,
    )


def _scenario_row_from_words(
    scenario: Mapping[str, Any],
    *,
    admitted_words: Sequence[Mapping[str, Any]],
    neutral_lemmas: Sequence[str],
) -> dict[str, Any]:
    selected_count = len(admitted_words)
    active_topics = _active_topics(scenario)
    topic_mover_count = sum(1 for row in admitted_words if _is_topic_mover(row, active_topics))
    topic_counts = Counter(
        _topic_from_affinity_source(row, active_topics)
        for row in admitted_words
        if _is_topic_mover(row, active_topics)
    )
    top_lemmas = [str(lemma) for lemma in scenario.get("top_lemmas", ())]
    if admitted_words:
        top_lemmas = [str(row.get("lemma") or "") for row in admitted_words]
    neutral_set = set(neutral_lemmas)
    return {
        "name": str(scenario.get("name") or ""),
        "description": str(scenario.get("description") or ""),
        "active_topics": active_topics,
        "selected_count": selected_count,
        "selected_topic_count": topic_mover_count,
        "selected_topic_share": _ratio(topic_mover_count, selected_count),
        "topic_mover_counts": {key: value for key, value in sorted(topic_counts.items()) if key},
        "average_difficulty": _average_metric(admitted_words, "difficulty_estimate"),
        "average_readiness": _average_metric(admitted_words, "readiness_multiplier"),
        "min_readiness": _min_metric(admitted_words, "readiness_multiplier"),
        "average_base_rank": _average_metric(admitted_words, "base_rank"),
        "top_lemmas": top_lemmas,
        "introduced_vs_neutral": [lemma for lemma in top_lemmas if lemma not in neutral_set],
        "neutral_overlap_count": len(set(top_lemmas) & neutral_set),
        "top_topic_movers": _top_topic_movers(scenario),
        "active_topic_support": _active_topic_support_rows(scenario, active_topics),
    }


def _active_topics(scenario: Mapping[str, Any]) -> list[str]:
    context = scenario.get("effective_profile_context")
    if not isinstance(context, Mapping):
        return []
    topic_weights = context.get("topic_weights")
    if not isinstance(topic_weights, Mapping):
        return []
    topics = [
        str(topic)
        for topic, weight in topic_weights.items()
        if str(topic).strip() and _safe_float(weight) > 0.0
    ]
    return sorted(topics)


def _max_topic_weight(scenario: Mapping[str, Any]) -> float:
    context = scenario.get("effective_profile_context")
    if not isinstance(context, Mapping):
        return 0.0
    topic_weights = context.get("topic_weights")
    if not isinstance(topic_weights, Mapping):
        return 0.0
    return max((_safe_float(value) for value in topic_weights.values()), default=0.0)


def _is_topic_mover(row: Mapping[str, Any], active_topics: Sequence[str]) -> bool:
    if not active_topics:
        return False
    source = str(row.get("topic_affinity_source") or "")
    if not source:
        return False
    return any(topic in source for topic in active_topics)


def _topic_from_affinity_source(row: Mapping[str, Any], active_topics: Sequence[str]) -> str:
    source = str(row.get("topic_affinity_source") or "")
    for topic in active_topics:
        if topic in source:
            return topic
    return ""


def _active_topic_support_rows(
    scenario: Mapping[str, Any],
    active_topics: Sequence[str],
) -> list[dict[str, Any]]:
    support = scenario.get("active_topic_support")
    if not isinstance(support, Mapping):
        return []
    active_set = set(active_topics)
    rows = []
    for row in support.get("topics", ()):
        if not isinstance(row, Mapping):
            continue
        topic = str(row.get("topic") or "")
        if topic not in active_set:
            continue
        rows.append(
            {
                "topic": topic,
                "candidate_count": int(row.get("candidate_count") or 0),
                "support_mass": _rounded(row.get("support_mass")),
                "scarcity_readiness": row.get("scarcity_readiness"),
                "top_examples": list(row.get("top_examples") or [])[:5],
            }
        )
    return rows


def _top_topic_movers(scenario: Mapping[str, Any]) -> list[dict[str, Any]]:
    movers = []
    for row in scenario.get("top_topic_movers", ()):
        if not isinstance(row, Mapping):
            continue
        movers.append(
            {
                "lemma": str(row.get("lemma") or ""),
                "base_rank": row.get("base_rank"),
                "reranked_rank": row.get("reranked_rank"),
                "rank_delta": row.get("rank_delta"),
                "topic_affinity_source": row.get("topic_affinity_source"),
                "readiness_multiplier": row.get("readiness_multiplier"),
            }
        )
    return movers[:8]


def _weighted_summary_rows(
    weighted_rows_by_seed: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_name: dict[str, list[dict[str, Any]]] = {}
    for seed_payload in weighted_rows_by_seed:
        for row in seed_payload.get("rows", ()):
            if isinstance(row, Mapping):
                rows_by_name.setdefault(str(row.get("name") or ""), []).append(dict(row))
    summary_rows = []
    for name, rows in sorted(rows_by_name.items()):
        shares = [float(row.get("selected_topic_share") or 0.0) for row in rows]
        counts = [int(row.get("selected_topic_count") or 0) for row in rows]
        lemma_counter = Counter(
            lemma for row in rows for lemma in row.get("top_lemmas", ()) if str(lemma).strip()
        )
        first_row = rows[0] if rows else {}
        summary_rows.append(
            {
                "name": name,
                "active_topics": list(first_row.get("active_topics") or []),
                "seed_count": len(rows),
                "mean_selected_topic_count": _mean(counts),
                "min_selected_topic_count": min(counts) if counts else 0,
                "max_selected_topic_count": max(counts) if counts else 0,
                "mean_selected_topic_share": _mean(shares),
                "min_selected_topic_share": min(shares) if shares else 0.0,
                "max_selected_topic_share": max(shares) if shares else 0.0,
                "top_lemma_frequency": [
                    {"lemma": lemma, "count": count}
                    for lemma, count in lemma_counter.most_common(8)
                ],
            }
        )
    return summary_rows


def _simulate_top_k_rows_by_seed(
    report: Mapping[str, Any],
    *,
    budget: int,
    weighted_seeds: Sequence[int],
) -> list[dict[str, Any]]:
    return [
        {
            "seed": int(seed),
            "rows": _scenario_rows_from_selector(
                report,
                selector=lambda scenario, seed=seed: _select_top_k_weighted_words(
                    scenario.get("admitted_words", ()),
                    budget=budget,
                    seed=int(seed),
                ),
            ),
        }
        for seed in weighted_seeds
    ]


def _simulate_topic_lane_rows(
    report: Mapping[str, Any],
    *,
    budget: int,
    topic_lane_max_share: float,
) -> list[dict[str, Any]]:
    scenarios = [
        scenario for scenario in report.get("scenarios", ()) if isinstance(scenario, Mapping)
    ]
    neutral = next((scenario for scenario in scenarios if scenario.get("name") == "neutral"), {})
    neutral_words = [
        dict(row) for row in neutral.get("admitted_words", ()) if isinstance(row, Mapping)
    ]
    neutral_selected = _select_topic_lane_words(
        neutral,
        neutral_words=neutral_words,
        budget=budget,
        topic_lane_max_share=topic_lane_max_share,
    )
    neutral_lemmas = [
        str(row.get("lemma") or "")
        for row in neutral_selected
        if str(row.get("lemma") or "").strip()
    ]
    return [
        _scenario_row_from_words(
            scenario,
            admitted_words=_select_topic_lane_words(
                scenario,
                neutral_words=neutral_words,
                budget=budget,
                topic_lane_max_share=topic_lane_max_share,
            ),
            neutral_lemmas=neutral_lemmas,
        )
        for scenario in scenarios
    ]


def _scenario_rows_from_selector(
    report: Mapping[str, Any],
    *,
    selector,
) -> list[dict[str, Any]]:
    scenarios = [
        scenario for scenario in report.get("scenarios", ()) if isinstance(scenario, Mapping)
    ]
    neutral = next((scenario for scenario in scenarios if scenario.get("name") == "neutral"), {})
    neutral_lemmas = [
        str(row.get("lemma") or "")
        for row in selector(neutral)
        if isinstance(row, Mapping) and str(row.get("lemma") or "").strip()
    ]
    return [
        _scenario_row_from_words(
            scenario,
            admitted_words=selector(scenario),
            neutral_lemmas=neutral_lemmas,
        )
        for scenario in scenarios
    ]


def _select_top_k_weighted_words(
    admitted_words: object,
    *,
    budget: int,
    seed: int,
) -> list[dict[str, Any]]:
    rows = [dict(row) for row in admitted_words if isinstance(row, Mapping)]
    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    pool = list(rows)
    while pool and len(selected) < budget:
        weights = [_selection_mass(row) for row in pool]
        total = sum(weights)
        if total <= 0.0:
            selected.extend(pool[: budget - len(selected)])
            break
        roll = rng.random() * total
        pick_index = len(pool) - 1
        for index, weight in enumerate(weights):
            roll -= weight
            if roll <= 0.0:
                pick_index = index
                break
        selected.append(pool.pop(pick_index))
    return selected


def _select_topic_lane_words(
    scenario: Mapping[str, Any],
    *,
    neutral_words: Sequence[Mapping[str, Any]],
    budget: int,
    topic_lane_max_share: float,
) -> list[dict[str, Any]]:
    rows = [dict(row) for row in scenario.get("admitted_words", ()) if isinstance(row, Mapping)]
    active_topics = _active_topics(scenario)
    max_weight = _max_topic_weight(scenario)
    if not active_topics or max_weight <= 0.0:
        return rows[:budget]
    topic_budget = min(
        budget,
        math.ceil(budget * max(0.0, min(1.0, max_weight)) * max(0.0, topic_lane_max_share)),
    )
    topic_rows = [row for row in rows if _is_topic_mover(row, active_topics)]
    selected: list[dict[str, Any]] = topic_rows[:topic_budget]
    selected_lemmas = {str(row.get("lemma") or "") for row in selected}
    topic_lemmas = {str(row.get("lemma") or "") for row in topic_rows}
    general_rows = [
        dict(row)
        for row in neutral_words
        if str(row.get("lemma") or "") not in selected_lemmas | topic_lemmas
    ]
    selected.extend(general_rows[: max(0, budget - len(selected))])
    selected_lemmas = {str(row.get("lemma") or "") for row in selected}
    if len(selected) < budget:
        selected.extend(row for row in rows if str(row.get("lemma") or "") not in selected_lemmas)
    return selected[:budget]


def _build_comparisons(
    *,
    ranked_rows: Sequence[Mapping[str, Any]],
    weighted_rows: Sequence[Mapping[str, Any]],
    top_k_rows: Sequence[Mapping[str, Any]],
    topic_lane_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    ranked = {str(row.get("name") or ""): row for row in ranked_rows}
    weighted = {str(row.get("name") or ""): row for row in weighted_rows}
    top_k = {str(row.get("name") or ""): row for row in top_k_rows}
    topic_lane = {str(row.get("name") or ""): row for row in topic_lane_rows}
    ranked_strength = [
        _row_share(ranked, "neutral"),
        _row_share(ranked, "animals_light_weight"),
        _row_share(ranked, "animals_interest"),
    ]
    weighted_strength = [
        _weighted_share(weighted, "neutral"),
        _weighted_share(weighted, "animals_light_weight"),
        _weighted_share(weighted, "animals_interest"),
    ]
    top_k_strength = [
        _weighted_share(top_k, "neutral"),
        _weighted_share(top_k, "animals_light_weight"),
        _weighted_share(top_k, "animals_interest"),
    ]
    topic_lane_strength = [
        _row_share(topic_lane, "neutral"),
        _row_share(topic_lane, "animals_light_weight"),
        _row_share(topic_lane, "animals_interest"),
    ]
    strong_animals = ranked.get("animals_interest", {})
    high_animals = ranked.get("animals_high_proficiency", {})
    return {
        "ranked_animals_strength_shares": ranked_strength,
        "ranked_animals_strength_monotonic": ranked_strength == sorted(ranked_strength),
        "weighted_animals_strength_mean_shares": weighted_strength,
        "weighted_animals_strength_monotonic": weighted_strength == sorted(weighted_strength),
        "weighted_animals_strength_visible": (
            weighted_strength[-1] > weighted_strength[0] and weighted_strength[-1] > 0.0
        ),
        "top_k_animals_strength_mean_shares": top_k_strength,
        "top_k_animals_strength_monotonic": top_k_strength == sorted(top_k_strength),
        "top_k_animals_strength_visible": (
            top_k_strength[-1] > top_k_strength[0] and top_k_strength[-1] > 0.0
        ),
        "topic_lane_animals_strength_shares": topic_lane_strength,
        "topic_lane_animals_strength_monotonic": topic_lane_strength == sorted(topic_lane_strength),
        "topic_lane_animals_strong_mixed": 0.0 < topic_lane_strength[-1] < 1.0,
        "high_proficiency_animals": {
            "strong_topic_share": _row_share(ranked, "animals_interest"),
            "high_proficiency_topic_share": _row_share(ranked, "animals_high_proficiency"),
            "strong_average_difficulty": strong_animals.get("average_difficulty"),
            "high_proficiency_average_difficulty": high_animals.get("average_difficulty"),
        },
    }


def _build_findings(
    *,
    ranked_preview: Mapping[str, Any],
    weighted_previews: Sequence[Mapping[str, Any]],
    comparisons: Mapping[str, Any],
) -> list[dict[str, Any]]:
    findings = []
    ranked_fail_count = int(dict(ranked_preview.get("summary") or {}).get("fail_count") or 0)
    weighted_fail_count = sum(
        int(dict(report.get("summary") or {}).get("fail_count") or 0)
        for report in weighted_previews
    )
    findings.append(
        _finding(
            "PASS" if ranked_fail_count == 0 and weighted_fail_count == 0 else "FAIL",
            "CALIBRATION_PREVIEWS_HAVE_NO_FAILURES",
            "Ranked and weighted admission previews completed without FAIL findings.",
            {"ranked_fail_count": ranked_fail_count, "weighted_fail_count": weighted_fail_count},
        )
    )
    findings.append(
        _finding(
            "PASS" if comparisons.get("ranked_animals_strength_monotonic") else "WARN",
            "RANKED_TOPIC_STRENGTH_MONOTONIC",
            "Ranked animals topic share is monotonic from neutral to light to strong.",
            comparisons.get("ranked_animals_strength_shares"),
        )
    )
    findings.append(
        _finding(
            "PASS"
            if comparisons.get("weighted_animals_strength_monotonic")
            and comparisons.get("weighted_animals_strength_visible")
            else "WARN",
            "WEIGHTED_TOPIC_STRENGTH_MONOTONIC",
            (
                "Weighted animals topic share mean is monotonic and visibly stronger than neutral."
                if comparisons.get("weighted_animals_strength_visible")
                else (
                    "Weighted animals topic share did not become visible in the seeded samples; "
                    "the full-pool weighted policy may be too diffuse for topic preferences."
                )
            ),
            {
                "shares": comparisons.get("weighted_animals_strength_mean_shares"),
                "visible": comparisons.get("weighted_animals_strength_visible"),
            },
        )
    )
    findings.append(
        _finding(
            "PASS"
            if comparisons.get("top_k_animals_strength_monotonic")
            and comparisons.get("top_k_animals_strength_visible")
            else "WARN",
            "TOP_K_WEIGHTED_TOPIC_SIGNAL_VISIBLE",
            (
                "Top-k weighted sampling makes the animals preference visible."
                if comparisons.get("top_k_animals_strength_visible")
                else "Top-k weighted sampling still did not make the animals preference visible."
            ),
            comparisons.get("top_k_animals_strength_mean_shares"),
        )
    )
    findings.append(
        _finding(
            "PASS"
            if comparisons.get("topic_lane_animals_strength_monotonic")
            and comparisons.get("topic_lane_animals_strong_mixed")
            else "WARN",
            "RESERVED_TOPIC_LANE_PRODUCES_MIXED_TOPIC_BATCH",
            (
                "Reserved topic-lane simulation produces a meaningful but mixed animals batch."
                if comparisons.get("topic_lane_animals_strong_mixed")
                else "Reserved topic-lane simulation did not produce the intended mixed batch."
            ),
            comparisons.get("topic_lane_animals_strength_shares"),
        )
    )
    high = dict(comparisons.get("high_proficiency_animals") or {})
    findings.append(
        _finding(
            "PASS",
            "HIGH_PROFICIENCY_TRADEOFF_VISIBLE",
            (
                "High-proficiency animals calibration exposes whether readiness suppresses "
                "too-easy topic items."
            ),
            high,
        )
    )
    return findings


def _finding(level: str, code: str, message: str, details: object | None = None) -> dict[str, Any]:
    payload = {"level": level, "code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return payload


def _summarize_findings(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(finding.get("level") or "").upper() for finding in findings)
    fail_count = int(counts.get("FAIL", 0))
    warn_count = int(counts.get("WARN", 0))
    return {
        "status": "FAIL" if fail_count else "WARN" if warn_count else "PASS",
        "pass_count": int(counts.get("PASS", 0)),
        "warn_count": warn_count,
        "fail_count": fail_count,
    }


def _row_share(rows_by_name: Mapping[str, Mapping[str, Any]], name: str) -> float:
    return float(rows_by_name.get(name, {}).get("selected_topic_share") or 0.0)


def _weighted_share(rows_by_name: Mapping[str, Mapping[str, Any]], name: str) -> float:
    return float(rows_by_name.get(name, {}).get("mean_selected_topic_share") or 0.0)


def _selection_mass(row: Mapping[str, Any]) -> float:
    for key in ("selection_mass", "profile_score", "admission_weight"):
        value = _safe_float(row.get(key))
        if value > 0.0:
            return value
    return 0.001


def _average_metric(rows: Sequence[Mapping[str, Any]], key: str) -> float | None:
    values = [_safe_float(row.get(key)) for row in rows]
    values = [value for value in values if value == value]
    return _mean(values) if values else None


def _min_metric(rows: Sequence[Mapping[str, Any]], key: str) -> float | None:
    values = [_safe_float(row.get(key)) for row in rows]
    values = [value for value in values if value == value]
    return round(min(values), 6) if values else None


def _mean(values: Sequence[float | int]) -> float:
    if not values:
        return 0.0
    return round(sum(float(value) for value in values) / len(values), 6)


def _ratio(numerator: int, denominator: int) -> float:
    return round(float(numerator) / float(denominator), 6) if denominator else 0.0


def _safe_float(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed == parsed else 0.0


def _rounded(value: object) -> float:
    return round(_safe_float(value), 6)


def _parse_weighted_seeds(value: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render en-es SRS admission calibration shares across preference profiles."
    )
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--overlay-source-path", type=Path)
    parser.add_argument("--overlay-source-paths", type=Path, nargs="*")
    parser.add_argument("--set-top-n", type=int, default=DEFAULT_SET_TOP_N)
    parser.add_argument("--admission-budget", type=int, default=DEFAULT_ADMISSION_BUDGET)
    parser.add_argument("--top-k-window", type=int, default=DEFAULT_TOP_K_WINDOW)
    parser.add_argument("--topic-lane-max-share", type=float, default=DEFAULT_TOPIC_LANE_MAX_SHARE)
    parser.add_argument(
        "--weighted-seeds",
        default=",".join(str(seed) for seed in DEFAULT_WEIGHTED_SEEDS),
        help="Comma-separated seed list for weighted-without-replacement calibration.",
    )
    parser.add_argument(
        "--augment-with-zipf-bridge",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--zipf-bridge-path", type=Path, default=DEFAULT_ZIPF_BRIDGE_PATH)
    parser.add_argument("--kaikki-forward-db", type=Path)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        pair=args.pair,
        frequency_db=args.frequency_db,
        overlay_source_path=args.overlay_source_path,
        overlay_source_paths=args.overlay_source_paths,
        set_top_n=args.set_top_n,
        admission_budget=args.admission_budget,
        top_k_window=args.top_k_window,
        topic_lane_max_share=args.topic_lane_max_share,
        weighted_seeds=_parse_weighted_seeds(args.weighted_seeds),
        augment_with_zipf_bridge=args.augment_with_zipf_bridge,
        zipf_bridge_path=args.zipf_bridge_path,
        kaikki_forward_db=args.kaikki_forward_db,
    )
    write_report(report, json_out=args.json_out, markdown_out=args.markdown_out)
    summary = report["summary"]
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
