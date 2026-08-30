#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV_IN = (
    PROJECT_ROOT
    / "core"
    / "lexishift_core"
    / "resources"
    / "srs"
    / "en_ja"
    / "learner_difficulty_corrected.csv"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_veto_candidate_review_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_veto_candidate_review_en_ja_latest.md"
)
DEFAULT_PRODUCT_SAMPLES_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_product_acceptance_en_ja_latest.json"
)
DEFAULT_RANDOM_SAMPLES_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_random_ux_sample_pack_en_ja_latest.json"
)

REPORT_SCHEMA_VERSION = 1
DEFAULT_CATEGORY_LIMIT = 24


@dataclass(frozen=True)
class Category:
    key: str
    title: str
    description: str
    limit: int


CATEGORIES = (
    Category(
        key="manual_watchlist",
        title="Manual watchlist",
        description=(
            "Rows already marked review/watch in the correction layer. These are "
            "included so the current open queue stays visible."
        ),
        limit=16,
    ),
    Category(
        key="active_hard_veto",
        title="Already active hard vetoes",
        description=(
            "Rows already carrying an explicit runtime-suppression correction. "
            "These are not new candidates; they are the high-confidence gate set "
            "we use as calibration examples for later review."
        ),
        limit=DEFAULT_CATEGORY_LIMIT,
    ),
    Category(
        key="unhandled_review_flags",
        title="Unhandled generated review flags",
        description=(
            "Rows with generated warning flags but no active manual correction. "
            "These are high-priority because the exporter already noticed a risk."
        ),
        limit=DEFAULT_CATEGORY_LIMIT,
    ),
    Category(
        key="same_surface_rare_reading",
        title="Same-surface rare readings",
        description=(
            "Common-looking written forms whose specific reading has weak exact "
            "support. These are likely to pollute early admission if left normal."
        ),
        limit=DEFAULT_CATEGORY_LIMIT,
    ),
    Category(
        key="single_kanji_component_like",
        title="Single-kanji component-like rows",
        description=(
            "One-character kanji rows with weak exact support and high same-surface "
            "or suspicion evidence. Many are better as components or restricted rows."
        ),
        limit=DEFAULT_CATEGORY_LIMIT,
    ),
    Category(
        key="kana_preferred_kanji_display",
        title="Kana-preferred kanji display",
        description=(
            "Rows whose written form is kanji but the evidence says kana is strongly "
            "preferred. These may only need display-only correction when the word is "
            "otherwise legitimate."
        ),
        limit=DEFAULT_CATEGORY_LIMIT,
    ),
    Category(
        key="low_support_early_rows",
        title="Low-support early rows",
        description=(
            "Early rows without exact JLPT or lesson support and with low exact "
            "commonness. These are broad safety candidates, not automatic defects."
        ),
        limit=DEFAULT_CATEGORY_LIMIT,
    ),
)

HYPOTHESIS_METADATA: Mapping[str, Mapping[str, str]] = {
    "manual_watchlist": {
        "hypothesis_family": "manual_open_queue",
        "enforcement_posture": "manual_resolution",
        "certainty": "review_required",
        "expected_accuracy": "depends_on_existing_manual_note",
        "failure_mode": "stale watch rows may no longer be actionable",
    },
    "active_hard_veto": {
        "hypothesis_family": "explicit_product_gate",
        "enforcement_posture": "already_hard_gated",
        "certainty": "high",
        "expected_accuracy": "very_high",
        "failure_mode": "manual correction may be overly conservative",
    },
    "unhandled_review_flags": {
        "hypothesis_family": "exporter_warning",
        "enforcement_posture": "review_only",
        "certainty": "medium",
        "expected_accuracy": "high_for_queueing_low_for_automatic_veto",
        "failure_mode": "flags mix display-only issues with true admission vetoes",
    },
    "same_surface_rare_reading": {
        "hypothesis_family": "same_surface_rare_reading",
        "enforcement_posture": "review_only",
        "certainty": "medium_high",
        "expected_accuracy": "good_below_mid_difficulty_no_auto_veto",
        "failure_mode": "valid literary or specialized readings can be real vocabulary",
    },
    "single_kanji_component_like": {
        "hypothesis_family": "single_kanji_component_like",
        "enforcement_posture": "review_only",
        "certainty": "medium",
        "expected_accuracy": "medium_type_dependent",
        "failure_mode": "some single-kanji rows are legitimate standalone vocabulary",
    },
    "kana_preferred_kanji_display": {
        "hypothesis_family": "kana_preferred_kanji_display",
        "enforcement_posture": "review_only",
        "certainty": "medium_high",
        "expected_accuracy": "good_for_display_review_not_for_veto",
        "failure_mode": "kanji display may still be acceptable for non-beginner rows",
    },
    "low_support_early_rows": {
        "hypothesis_family": "low_support_early_rows",
        "enforcement_posture": "review_only",
        "certainty": "low_medium",
        "expected_accuracy": "smoke_detector_only",
        "failure_mode": "many useful easy words are missing from exact support sources",
    },
}


def main() -> int:
    args = parse_args()
    csv_in = resolve_path(args.csv_in)
    report = build_report(
        csv_in=csv_in,
        category_limit=max(1, int(args.category_limit)),
        product_samples_json=resolve_optional_path(args.product_samples_json),
        random_samples_json=resolve_optional_path(args.random_samples_json),
    )
    json_out = resolve_path(args.json_out)
    markdown_out = resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a focused en-ja SRS admission-veto candidate review pack "
            "from the runtime corrected learner-difficulty CSV."
        )
    )
    parser.add_argument("--csv-in", type=Path, default=DEFAULT_CSV_IN)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--product-samples-json", type=Path, default=DEFAULT_PRODUCT_SAMPLES_JSON)
    parser.add_argument("--random-samples-json", type=Path, default=DEFAULT_RANDOM_SAMPLES_JSON)
    parser.add_argument(
        "--category-limit",
        type=int,
        default=DEFAULT_CATEGORY_LIMIT,
        help="Maximum rows per non-watchlist category.",
    )
    return parser.parse_args()


def build_report(
    *,
    csv_in: Path,
    category_limit: int,
    product_samples_json: Path | None = DEFAULT_PRODUCT_SAMPLES_JSON,
    random_samples_json: Path | None = DEFAULT_RANDOM_SAMPLES_JSON,
) -> dict[str, Any]:
    rows = load_rows(csv_in)
    visibility_index = load_admission_visibility(
        product_samples_json=product_samples_json,
        random_samples_json=random_samples_json,
    )
    category_reports = []
    selected_keys: set[tuple[str, str]] = set()
    for category in CATEGORIES:
        limit = category.limit if category.key == "manual_watchlist" else category_limit
        candidates = [
            row
            for row in rows
            if category_matches(row, category.key)
            and (
                category.key == "manual_watchlist"
                or (row["lemma"], row["reading"]) not in selected_keys
            )
        ]
        candidates = sorted(candidates, key=lambda row: (-review_risk(row), row["rank"]))
        sampled = candidates[:limit]
        if category.key != "manual_watchlist":
            selected_keys.update((row["lemma"], row["reading"]) for row in sampled)
        hypothesis_metadata = dict(HYPOTHESIS_METADATA.get(category.key, {}))
        category_reports.append(
            {
                "key": category.key,
                "title": category.title,
                "description": category.description,
                "hypothesis": hypothesis_metadata,
                "candidate_count": len(candidates),
                "shown_count": len(sampled),
                "candidate_distribution": summarize_hypothesis_rows(
                    candidates,
                    category_key=category.key,
                    visibility_index=visibility_index,
                ),
                "shown_distribution": summarize_hypothesis_rows(
                    sampled,
                    category_key=category.key,
                    visibility_index=visibility_index,
                ),
                "rows": [
                    review_row(row, category.key, visibility_index=visibility_index)
                    for row in sampled
                ],
            }
        )

    flattened_rows = [
        row for category in category_reports for row in list(category.get("rows") or [])
    ]
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": repo_path(csv_in),
        "method": {
            "scope": "runtime corrected learner-difficulty CSV",
            "purpose": (
                "Surface likely admission-veto/manual-correction candidates before "
                "product SRS admission sampling review."
            ),
            "selection": (
                "Rows are grouped by mechanical risk families: open manual watchlist, "
                "unhandled exporter flags, same-surface rare readings, single-kanji "
                "component-like rows, kana-preferred kanji display rows, and low-support "
                "early rows."
            ),
            "non_goal": (
                "The script does not decide corrections automatically; it only creates "
                "a reproducible review queue."
            ),
        },
        "summary": {
            "runtime_row_count": len(rows),
            "active_or_handled_correction_count": sum(1 for row in rows if handled(row)),
            "review_pack_row_count": len(flattened_rows),
            "unique_review_pack_row_count": len(
                {(row["lemma"], row["reading"]) for row in flattened_rows}
            ),
            "category_count": len(category_reports),
            "hard_veto_runtime_row_count": sum(1 for row in rows if hard_veto(row)),
            "product_visible_review_pack_row_count": sum(
                1
                for row in flattened_rows
                if int(dict(row.get("visibility") or {}).get("product_observation_count") or 0) > 0
            ),
            "random_visible_review_pack_row_count": sum(
                1
                for row in flattened_rows
                if int(dict(row.get("visibility") or {}).get("random_observation_count") or 0) > 0
            ),
            "product_exact_visible_review_pack_row_count": visible_row_count(
                flattened_rows,
                count_key="product_observation_count",
                match_mode="exact_reading",
            ),
            "random_exact_visible_review_pack_row_count": visible_row_count(
                flattened_rows,
                count_key="random_observation_count",
                match_mode="exact_reading",
            ),
            "product_lemma_fallback_visible_review_pack_row_count": visible_row_count(
                flattened_rows,
                count_key="product_observation_count",
                match_mode="lemma_any_reading",
            ),
            "random_lemma_fallback_visible_review_pack_row_count": visible_row_count(
                flattened_rows,
                count_key="random_observation_count",
                match_mode="lemma_any_reading",
            ),
        },
        "visibility_inputs": visibility_index["inputs"],
        "visibility_summary": visibility_index["summary"],
        "hypothesis_tracking": [hypothesis_tracking_row(category) for category in category_reports],
        "categories": category_reports,
    }


def load_rows(csv_in: Path) -> list[dict[str, Any]]:
    with csv_in.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw_row in reader:
            row = dict(raw_row)
            row["rank"] = to_int(row.get("rank"))
            for field in (
                "score",
                "model_score",
                "correction_delta",
                "exact_commonness",
                "jlpt_exact_known",
                "jlpt_raw_exact_known",
                "jlpt_normalized_only_known",
                "lesson_known",
                "kana_preferred",
                "rare_wago_obscure_written",
                "kanji_surface",
                "same_surface_risk",
                "hard_form",
                "soft_form",
                "reading_inheritance",
                "tail_guard",
                "suspicion_full",
            ):
                row[field] = to_float(row.get(field))
            rows.append(row)
    return rows


def category_matches(row: Mapping[str, Any], category_key: str) -> bool:
    if category_key == "manual_watchlist":
        return bool(str(row.get("manual_review") or "").strip()) or str(
            row.get("correction_status") or ""
        ).strip() in {"review", "watch"}
    if category_key == "active_hard_veto":
        return hard_veto(row)
    if handled(row):
        return False
    if category_key == "unhandled_review_flags":
        return bool(split_flags(row.get("review_flags"))) and row["score"] <= 0.7
    if category_key == "same_surface_rare_reading":
        return (
            row["score"] <= 0.62
            and row["same_surface_risk"] >= 0.82
            and row["exact_commonness"] <= 0.05
            and row["jlpt_exact_known"] <= 0.0
        )
    if category_key == "single_kanji_component_like":
        return (
            row["score"] <= 0.58
            and len(str(row.get("lemma") or "")) == 1
            and row["kanji_surface"] >= 0.5
            and row["jlpt_exact_known"] <= 0.0
            and row["lesson_known"] <= 0.0
            and (
                row["same_surface_risk"] >= 0.60
                or row["suspicion_full"] >= 0.75
                or row["exact_commonness"] <= 0.03
            )
        )
    if category_key == "kana_preferred_kanji_display":
        return (
            row["score"] <= 0.50
            and row["kanji_surface"] >= 0.5
            and row["kana_preferred"] >= 0.75
            and not str(row.get("display_form") or "").strip()
        )
    if category_key == "low_support_early_rows":
        return (
            row["score"] <= 0.36
            and row["exact_commonness"] <= 0.025
            and row["jlpt_exact_known"] <= 0.0
            and row["lesson_known"] <= 0.0
            and (
                row["suspicion_full"] >= 0.35
                or row["same_surface_risk"] >= 0.35
                or row["hard_form"] >= 0.8
            )
        )
    raise ValueError(f"unknown category: {category_key}")


def hard_veto(row: Mapping[str, Any]) -> bool:
    correction_types = set(split_flags(row.get("correction_types")))
    admission_override = str(row.get("admission_override") or "").strip()
    candidate_state = str(row.get("candidate_state") or "").strip()
    return bool(
        correction_types.intersection({"restricted_admission", "exclude_standalone_srs"})
        or admission_override == "exclude_standalone_srs"
        or candidate_state == "suppressed_default"
    )


def handled(row: Mapping[str, Any]) -> bool:
    if str(row.get("manual_correction_active") or "").strip():
        return True
    if str(row.get("correction_status") or "").strip() == "active":
        return True
    return bool(split_flags(row.get("correction_types")))


def review_risk(row: Mapping[str, Any]) -> float:
    score = float(row.get("score") or 0.0)
    risk = max(0.0, 0.65 - score) * 1.2
    risk += 1.10 * float(row.get("same_surface_risk") or 0.0)
    risk += 0.65 * float(row.get("suspicion_full") or 0.0)
    risk += 0.30 * float(row.get("hard_form") or 0.0)
    if float(row.get("kanji_surface") or 0.0) >= 0.5:
        risk += 0.25 * float(row.get("kana_preferred") or 0.0)
    if float(row.get("exact_commonness") or 0.0) <= 0.025:
        risk += 0.25
    if float(row.get("jlpt_exact_known") or 0.0) <= 0.0:
        risk += 0.20
    if float(row.get("lesson_known") or 0.0) <= 0.0:
        risk += 0.10
    if len(str(row.get("lemma") or "")) == 1 and float(row.get("kanji_surface") or 0.0) >= 0.5:
        risk += 0.20
    if split_flags(row.get("review_flags")):
        risk += 0.40
    if str(row.get("correction_status") or "").strip() in {"review", "watch"}:
        risk += 0.45
    return round(risk, 6)


def review_row(
    row: Mapping[str, Any],
    category_key: str,
    *,
    visibility_index: Mapping[str, Any],
) -> dict[str, Any]:
    visibility = visibility_for_row(row, visibility_index=visibility_index)
    hypothesis = dict(HYPOTHESIS_METADATA.get(category_key, {}))
    return {
        "rank": int(row.get("rank") or 0),
        "score": rounded(row.get("score")),
        "lemma": str(row.get("lemma") or ""),
        "reading": str(row.get("reading") or ""),
        "display": str(row.get("display_form") or row.get("lemma") or ""),
        "category": category_key,
        "hypothesis_family": str(hypothesis.get("hypothesis_family") or category_key),
        "enforcement_posture": str(hypothesis.get("enforcement_posture") or "review_only"),
        "certainty": str(hypothesis.get("certainty") or "unknown"),
        "analysis_band": analysis_band(row),
        "candidate_shape": candidate_shape(row),
        "recommendation": recommendation(row, category_key),
        "risk_score": review_risk(row),
        "candidate_state": str(row.get("candidate_state") or ""),
        "correction_types": split_flags(row.get("correction_types")),
        "admission_override": str(row.get("admission_override") or ""),
        "correction_status": str(row.get("correction_status") or ""),
        "review_flags": split_flags(row.get("review_flags")),
        "evidence": {
            "exact_commonness": rounded(row.get("exact_commonness")),
            "jlpt_exact_known": rounded(row.get("jlpt_exact_known")),
            "lesson_known": rounded(row.get("lesson_known")),
            "kana_preferred": rounded(row.get("kana_preferred")),
            "kanji_surface": rounded(row.get("kanji_surface")),
            "same_surface_risk": rounded(row.get("same_surface_risk")),
            "hard_form": rounded(row.get("hard_form")),
            "suspicion_full": rounded(row.get("suspicion_full")),
        },
        "visibility": visibility,
        "note": note(row, category_key),
    }


def recommendation(row: Mapping[str, Any], category_key: str) -> str:
    if category_key == "manual_watchlist":
        return "resolve_existing_review_status"
    if category_key == "active_hard_veto":
        return "already_hard_vetoed"
    if (
        float(row.get("same_surface_risk") or 0.0) >= 0.82
        and float(row.get("exact_commonness") or 0.0) <= 0.05
    ):
        if len(str(row.get("lemma") or "")) == 1:
            return "likely_restrict_or_score_floor"
        return "review_for_score_floor_or_restriction"
    if (
        float(row.get("kana_preferred") or 0.0) >= 0.75
        and float(row.get("kanji_surface") or 0.0) >= 0.5
    ):
        return "review_for_display_only_or_restriction"
    if float(row.get("exact_commonness") or 0.0) <= 0.025:
        return "review_low_support_early_placement"
    return "watch"


def note(row: Mapping[str, Any], category_key: str) -> str:
    pieces = []
    if split_flags(row.get("review_flags")):
        pieces.append("generated flags: " + ",".join(split_flags(row.get("review_flags"))))
    if float(row.get("same_surface_risk") or 0.0) >= 0.82:
        pieces.append("high same-surface risk")
    if float(row.get("exact_commonness") or 0.0) <= 0.025:
        pieces.append("low exact commonness")
    if (
        float(row.get("kana_preferred") or 0.0) >= 0.75
        and float(row.get("kanji_surface") or 0.0) >= 0.5
    ):
        pieces.append("kana-preferred kanji surface")
    if category_key == "manual_watchlist":
        status = str(row.get("correction_status") or "").strip()
        if status:
            pieces.append(f"manual status: {status}")
    return "; ".join(pieces)


def load_admission_visibility(
    *,
    product_samples_json: Path | None,
    random_samples_json: Path | None,
) -> dict[str, Any]:
    exact: dict[tuple[str, str], dict[str, Any]] = {}
    lemma: dict[str, dict[str, Any]] = {}
    inputs = {
        "product_samples_json": repo_path(product_samples_json) if product_samples_json else None,
        "product_samples_loaded": bool(product_samples_json and product_samples_json.exists()),
        "random_samples_json": repo_path(random_samples_json) if random_samples_json else None,
        "random_samples_loaded": bool(random_samples_json and random_samples_json.exists()),
    }
    if product_samples_json and product_samples_json.exists():
        payload = load_json(product_samples_json)
        for scenario in mapping_rows(payload.get("scenarios")):
            scenario_name = str(scenario.get("name") or "").strip()
            proficiency = to_float(scenario.get("proficiency"))
            requested_topics = string_list(scenario.get("requested_topics"))
            for word in mapping_rows(scenario.get("admitted_words")):
                add_visibility_observation(
                    exact,
                    lemma,
                    word,
                    source="product_acceptance",
                    scenario_name=scenario_name,
                    proficiency=proficiency,
                    requested_topics=requested_topics,
                )
    if random_samples_json and random_samples_json.exists():
        payload = load_json(random_samples_json)
        for scenario in mapping_rows(payload.get("scenarios")):
            scenario_name = str(scenario.get("name") or "").strip()
            proficiency = to_float(scenario.get("proficiency"))
            requested_topics = string_list(scenario.get("requested_topics"))
            for draw in mapping_rows(scenario.get("draws")):
                for word in mapping_rows(draw.get("admitted_words")):
                    add_visibility_observation(
                        exact,
                        lemma,
                        word,
                        source="random_ux",
                        scenario_name=scenario_name,
                        proficiency=proficiency,
                        requested_topics=requested_topics,
                    )
    finalized_exact = {key: finalize_visibility(value) for key, value in exact.items()}
    finalized_lemma = {key: finalize_visibility(value) for key, value in lemma.items()}
    product_count = sum(
        1 for value in finalized_exact.values() if int(value["product_observation_count"]) > 0
    )
    random_count = sum(
        1 for value in finalized_exact.values() if int(value["random_observation_count"]) > 0
    )
    return {
        "inputs": inputs,
        "exact": finalized_exact,
        "lemma": finalized_lemma,
        "summary": {
            "exact_visible_key_count": len(finalized_exact),
            "lemma_visible_key_count": len(finalized_lemma),
            "product_visible_exact_key_count": product_count,
            "random_visible_exact_key_count": random_count,
        },
    }


def add_visibility_observation(
    exact: dict[tuple[str, str], dict[str, Any]],
    lemma_index: dict[str, dict[str, Any]],
    word: Mapping[str, Any],
    *,
    source: str,
    scenario_name: str,
    proficiency: float,
    requested_topics: Sequence[str],
) -> None:
    lemma = str(word.get("lemma") or "").strip()
    if not lemma:
        return
    reading = str(word.get("reading") or "").strip()
    for stats in (
        exact.setdefault((lemma, reading), empty_visibility_stats()),
        lemma_index.setdefault(lemma, empty_visibility_stats()),
    ):
        stats["observation_count"] += 1
        if source == "product_acceptance":
            stats["product_observation_count"] += 1
        if source == "random_ux":
            stats["random_observation_count"] += 1
        stats["sample_sources"].add(source)
        if scenario_name:
            stats["scenario_names"].add(scenario_name)
        for topic in requested_topics:
            stats["requested_topics"].add(topic)
        topic = topic_from_word(word)
        if topic:
            stats["observed_topics"].add(topic)
        if bool(word.get("is_topic_mover")) or topic:
            stats["topic_mover_observation_count"] += 1
        difficulty = difficulty_from_word(word)
        if difficulty is not None:
            stats["max_observed_difficulty"] = max_optional(
                stats["max_observed_difficulty"],
                difficulty,
            )
            stats["min_observed_difficulty"] = min_optional(
                stats["min_observed_difficulty"],
                difficulty,
            )
            delta = difficulty - proficiency
            stats["max_difficulty_minus_proficiency"] = max_optional(
                stats["max_difficulty_minus_proficiency"],
                delta,
            )
        profile_score = optional_float(word.get("profile_score"))
        if profile_score is not None:
            stats["max_profile_score"] = max_optional(stats["max_profile_score"], profile_score)


def empty_visibility_stats() -> dict[str, Any]:
    return {
        "observation_count": 0,
        "product_observation_count": 0,
        "random_observation_count": 0,
        "topic_mover_observation_count": 0,
        "scenario_names": set(),
        "requested_topics": set(),
        "observed_topics": set(),
        "sample_sources": set(),
        "max_difficulty_minus_proficiency": None,
        "max_observed_difficulty": None,
        "min_observed_difficulty": None,
        "max_profile_score": None,
    }


def finalize_visibility(stats: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "observation_count": int(stats.get("observation_count") or 0),
        "product_observation_count": int(stats.get("product_observation_count") or 0),
        "random_observation_count": int(stats.get("random_observation_count") or 0),
        "topic_mover_observation_count": int(stats.get("topic_mover_observation_count") or 0),
        "scenario_names": sorted(str(value) for value in stats.get("scenario_names", set())),
        "requested_topics": sorted(str(value) for value in stats.get("requested_topics", set())),
        "observed_topics": sorted(str(value) for value in stats.get("observed_topics", set())),
        "sample_sources": sorted(str(value) for value in stats.get("sample_sources", set())),
        "max_difficulty_minus_proficiency": rounded_or_none(
            stats.get("max_difficulty_minus_proficiency")
        ),
        "max_observed_difficulty": rounded_or_none(stats.get("max_observed_difficulty")),
        "min_observed_difficulty": rounded_or_none(stats.get("min_observed_difficulty")),
        "max_profile_score": rounded_or_none(stats.get("max_profile_score")),
    }


def visibility_for_row(
    row: Mapping[str, Any],
    *,
    visibility_index: Mapping[str, Any],
) -> dict[str, Any]:
    lemma = str(row.get("lemma") or "").strip()
    reading = str(row.get("reading") or "").strip()
    exact = dict(visibility_index.get("exact") or {})
    lemma_index = dict(visibility_index.get("lemma") or {})
    exact_stats = exact.get((lemma, reading))
    if exact_stats:
        return {"match_mode": "exact_reading", **dict(exact_stats)}
    lemma_stats = lemma_index.get(lemma)
    if lemma_stats:
        return {"match_mode": "lemma_any_reading", **dict(lemma_stats)}
    return {"match_mode": "not_observed", **finalize_visibility(empty_visibility_stats())}


def summarize_hypothesis_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    category_key: str,
    visibility_index: Mapping[str, Any],
) -> dict[str, Any]:
    band_counts: Counter[str] = Counter()
    shape_counts: Counter[str] = Counter()
    recommendation_counts: Counter[str] = Counter()
    product_visible = 0
    random_visible = 0
    topic_mover_visible = 0
    exact_visible = 0
    lemma_fallback_visible = 0
    product_exact_visible = 0
    random_exact_visible = 0
    product_lemma_fallback_visible = 0
    random_lemma_fallback_visible = 0
    for row in rows:
        band_counts[analysis_band(row)] += 1
        shape_counts[candidate_shape(row)] += 1
        recommendation_counts[recommendation(row, category_key)] += 1
        visibility = visibility_for_row(row, visibility_index=visibility_index)
        match_mode = str(visibility.get("match_mode") or "")
        product_observation_count = int(visibility.get("product_observation_count") or 0)
        random_observation_count = int(visibility.get("random_observation_count") or 0)
        if int(visibility.get("product_observation_count") or 0) > 0:
            product_visible += 1
        if int(visibility.get("random_observation_count") or 0) > 0:
            random_visible += 1
        if int(visibility.get("topic_mover_observation_count") or 0) > 0:
            topic_mover_visible += 1
        if match_mode == "exact_reading" and int(visibility.get("observation_count") or 0) > 0:
            exact_visible += 1
        if match_mode == "lemma_any_reading" and int(visibility.get("observation_count") or 0) > 0:
            lemma_fallback_visible += 1
        if match_mode == "exact_reading" and product_observation_count > 0:
            product_exact_visible += 1
        if match_mode == "exact_reading" and random_observation_count > 0:
            random_exact_visible += 1
        if match_mode == "lemma_any_reading" and product_observation_count > 0:
            product_lemma_fallback_visible += 1
        if match_mode == "lemma_any_reading" and random_observation_count > 0:
            random_lemma_fallback_visible += 1
    return {
        "row_count": len(rows),
        "difficulty_band_counts": dict(sorted(band_counts.items())),
        "candidate_shape_counts": dict(sorted(shape_counts.items())),
        "recommendation_counts": dict(sorted(recommendation_counts.items())),
        "product_visible_row_count": product_visible,
        "random_visible_row_count": random_visible,
        "topic_mover_visible_row_count": topic_mover_visible,
        "exact_reading_visible_row_count": exact_visible,
        "lemma_fallback_visible_row_count": lemma_fallback_visible,
        "product_exact_visible_row_count": product_exact_visible,
        "random_exact_visible_row_count": random_exact_visible,
        "product_lemma_fallback_visible_row_count": product_lemma_fallback_visible,
        "random_lemma_fallback_visible_row_count": random_lemma_fallback_visible,
    }


def hypothesis_tracking_row(category: Mapping[str, Any]) -> dict[str, Any]:
    hypothesis = dict(category.get("hypothesis") or {})
    candidate_distribution = dict(category.get("candidate_distribution") or {})
    shown_distribution = dict(category.get("shown_distribution") or {})
    return {
        "category": str(category.get("key") or ""),
        "hypothesis_family": str(hypothesis.get("hypothesis_family") or ""),
        "enforcement_posture": str(hypothesis.get("enforcement_posture") or ""),
        "certainty": str(hypothesis.get("certainty") or ""),
        "expected_accuracy": str(hypothesis.get("expected_accuracy") or ""),
        "failure_mode": str(hypothesis.get("failure_mode") or ""),
        "candidate_count": int(category.get("candidate_count") or 0),
        "shown_count": int(category.get("shown_count") or 0),
        "candidate_distribution": candidate_distribution,
        "shown_distribution": shown_distribution,
    }


def analysis_band(row: Mapping[str, Any]) -> str:
    score = float(row.get("score") or 0.0)
    if score < 0.20:
        return "0.00-0.20"
    if score < 0.40:
        return "0.20-0.40"
    if score < 0.60:
        return "0.40-0.60"
    if score < 0.80:
        return "0.60-0.80"
    return "0.80-1.00"


def candidate_shape(row: Mapping[str, Any]) -> str:
    lemma = str(row.get("lemma") or "").strip()
    if not lemma:
        return "empty"
    if len(lemma) == 1 and float(row.get("kanji_surface") or 0.0) >= 0.5:
        return "single_kanji"
    if any(is_kanji(char) for char in lemma):
        return "kanji_compound_or_phrase"
    if all(is_katakana_like(char) for char in lemma):
        return "katakana"
    if all(is_hiragana_like(char) for char in lemma):
        return "hiragana"
    if any(ord(char) < 128 for char in lemma):
        return "latin_or_symbol_mixed"
    return "mixed_or_other"


def is_kanji(char: str) -> bool:
    codepoint = ord(char)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def is_hiragana_like(char: str) -> bool:
    codepoint = ord(char)
    return 0x3040 <= codepoint <= 0x309F or codepoint in {0x30FB, 0x30FC}


def is_katakana_like(char: str) -> bool:
    codepoint = ord(char)
    return 0x30A0 <= codepoint <= 0x30FF or codepoint in {0x30FB, 0x30FC}


def difficulty_from_word(word: Mapping[str, Any]) -> float | None:
    for key in ("difficulty_for_summary", "runtime_difficulty_estimate", "corrected_difficulty"):
        value = optional_float(word.get(key))
        if value is not None:
            return value
    return None


def topic_from_word(word: Mapping[str, Any]) -> str:
    source = str(word.get("topic_affinity_source") or "").strip()
    prefix = "topic_hint:"
    if source.startswith(prefix):
        return source[len(prefix) :].strip()
    topics = string_list(word.get("topics"))
    return topics[0] if topics else ""


def mapping_rows(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def load_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = dict(report.get("summary") or {})
    lines = [
        "# en-ja SRS Admission Veto Candidate Review",
        "",
        f"Source: `{report.get('source')}`",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "This pack is a review queue, not an automatic correction list. It is built "
        "from the runtime corrected learner-difficulty CSV.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Runtime rows | {int(summary.get('runtime_row_count') or 0)} |",
        f"| Active/handled correction rows | {int(summary.get('active_or_handled_correction_count') or 0)} |",
        f"| Active hard-veto rows | {int(summary.get('hard_veto_runtime_row_count') or 0)} |",
        f"| Review-pack rows | {int(summary.get('review_pack_row_count') or 0)} |",
        f"| Unique review-pack rows | {int(summary.get('unique_review_pack_row_count') or 0)} |",
        f"| Product-visible review-pack rows | {int(summary.get('product_visible_review_pack_row_count') or 0)} |",
        f"| Random-visible review-pack rows | {int(summary.get('random_visible_review_pack_row_count') or 0)} |",
        f"| Product exact-visible review-pack rows | {int(summary.get('product_exact_visible_review_pack_row_count') or 0)} |",
        f"| Random exact-visible review-pack rows | {int(summary.get('random_exact_visible_review_pack_row_count') or 0)} |",
        f"| Product lemma-fallback visible rows | {int(summary.get('product_lemma_fallback_visible_review_pack_row_count') or 0)} |",
        f"| Random lemma-fallback visible rows | {int(summary.get('random_lemma_fallback_visible_review_pack_row_count') or 0)} |",
        "",
        "## Hypothesis Tracking",
        "",
        "| Category | Posture | Certainty | Candidates | Shown | Visible | Dominant Bands | Dominant Shapes |",
        "| --- | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in list(report.get("hypothesis_tracking") or []):
        shown = dict(row.get("shown_distribution") or {})
        candidate = dict(row.get("candidate_distribution") or {})
        visible_text = (
            f"exact_p={int(shown.get('product_exact_visible_row_count') or 0)}; "
            f"exact_r={int(shown.get('random_exact_visible_row_count') or 0)}; "
            f"lemma_p={int(shown.get('product_lemma_fallback_visible_row_count') or 0)}; "
            f"lemma_r={int(shown.get('random_lemma_fallback_visible_row_count') or 0)}; "
            f"topic={int(shown.get('topic_mover_visible_row_count') or 0)}"
        )
        lines.append(
            "| "
            f"`{escape(str(row.get('category') or ''))}` | "
            f"`{escape(str(row.get('enforcement_posture') or ''))}` | "
            f"`{escape(str(row.get('certainty') or ''))}` | "
            f"{int(row.get('candidate_count') or 0)} | "
            f"{int(row.get('shown_count') or 0)} | "
            f"{visible_text} | "
            f"{escape(top_counter_text(candidate.get('difficulty_band_counts')))} | "
            f"{escape(top_counter_text(candidate.get('candidate_shape_counts')))} |"
        )
    lines.extend(["", ""])
    for category in list(report.get("categories") or []):
        hypothesis = dict(category.get("hypothesis") or {})
        lines.extend(
            [
                f"## {category.get('title')}",
                "",
                str(category.get("description") or ""),
                "",
                (
                    f"Hypothesis: `{hypothesis.get('hypothesis_family', category.get('key'))}`; "
                    f"posture: `{hypothesis.get('enforcement_posture', 'review_only')}`; "
                    f"certainty: `{hypothesis.get('certainty', 'unknown')}`."
                ),
                "",
                f"Expected accuracy: `{hypothesis.get('expected_accuracy', '')}`.",
                "",
                f"Known failure mode: `{hypothesis.get('failure_mode', '')}`.",
                "",
                (
                    f"Candidates found: `{int(category.get('candidate_count') or 0)}`; "
                    f"shown: `{int(category.get('shown_count') or 0)}`."
                ),
                "",
            ]
        )
        lines.extend(render_rows(category.get("rows") or []))
        lines.append("")
    return "\n".join(lines)


def render_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| Risk | Rank | Score | Band | Shape | Word | Reading | Recommendation | Visible | Evidence |",
        "| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        evidence = dict(row.get("evidence") or {})
        visibility = dict(row.get("visibility") or {})
        match_mode = str(visibility.get("match_mode") or "not_observed")
        visible_text = (
            f"{match_mode}; "
            f"p={int(visibility.get('product_observation_count') or 0)}; "
            f"r={int(visibility.get('random_observation_count') or 0)}; "
            f"topic={int(visibility.get('topic_mover_observation_count') or 0)}"
        )
        scenarios = list(visibility.get("scenario_names") or [])
        if scenarios:
            visible_text = f"{visible_text}; {','.join(str(item) for item in scenarios[:3])}"
        evidence_text = (
            f"exact={float(evidence.get('exact_commonness') or 0.0):.3f}; "
            f"jlpt={float(evidence.get('jlpt_exact_known') or 0.0):.0f}; "
            f"lesson={float(evidence.get('lesson_known') or 0.0):.0f}; "
            f"same={float(evidence.get('same_surface_risk') or 0.0):.3f}; "
            f"kana={float(evidence.get('kana_preferred') or 0.0):.3f}; "
            f"susp={float(evidence.get('suspicion_full') or 0.0):.3f}"
        )
        note_text = str(row.get("note") or "")
        if note_text:
            evidence_text = f"{evidence_text}; {note_text}"
        lines.append(
            "| "
            f"{float(row.get('risk_score') or 0.0):.3f} | "
            f"{int(row.get('rank') or 0)} | "
            f"{float(row.get('score') or 0.0):.6f} | "
            f"`{escape(str(row.get('analysis_band') or ''))}` | "
            f"`{escape(str(row.get('candidate_shape') or ''))}` | "
            f"`{escape(str(row.get('lemma') or ''))}` | "
            f"`{escape(str(row.get('reading') or ''))}` | "
            f"`{escape(str(row.get('recommendation') or ''))}` | "
            f"{escape(visible_text)} | "
            f"{escape(evidence_text)} |"
        )
    return lines


def top_counter_text(counter: object, *, limit: int = 3) -> str:
    if not isinstance(counter, Mapping):
        return ""
    items = sorted(
        ((str(key), int(value or 0)) for key, value in counter.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return ", ".join(f"{key}:{value}" for key, value in items[:limit])


def visible_row_count(
    rows: Sequence[Mapping[str, Any]],
    *,
    count_key: str,
    match_mode: str,
) -> int:
    count = 0
    for row in rows:
        visibility = dict(row.get("visibility") or {})
        if str(visibility.get("match_mode") or "") != match_mode:
            continue
        if int(visibility.get(count_key) or 0) > 0:
            count += 1
    return count


def split_flags(value: object) -> list[str]:
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def to_float(value: object) -> float:
    try:
        text = str(value if value is not None else "").strip()
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


def optional_float(value: object) -> float | None:
    try:
        text = str(value if value is not None else "").strip()
        return float(text) if text else None
    except ValueError:
        return None


def max_optional(left: object, right: float) -> float:
    parsed_left = optional_float(left)
    return right if parsed_left is None else max(parsed_left, right)


def min_optional(left: object, right: float) -> float:
    parsed_left = optional_float(left)
    return right if parsed_left is None else min(parsed_left, right)


def to_int(value: object) -> int:
    try:
        return int(float(str(value if value is not None else "").strip() or "0"))
    except ValueError:
        return 0


def rounded(value: object) -> float:
    return round(to_float(value), 6)


def rounded_or_none(value: object) -> float | None:
    parsed = optional_float(value)
    return round(parsed, 6) if parsed is not None else None


def escape(value: str) -> str:
    return value.replace("|", "\\|")


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def resolve_optional_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    return resolve_path(path)


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
