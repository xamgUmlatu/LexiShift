#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
DEV_ROOT = PROJECT_ROOT / "scripts" / "dev"
if str(DEV_ROOT) not in sys.path:
    sys.path.insert(0, str(DEV_ROOT))

from lexishift_core.helper.engine import (  # noqa: E402
    SetAdmissionPreviewJobConfig,
    preview_srs_admission,
)
from lexishift_core.helper.pair_resources import resolve_pair_resources  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.topic_overlay import ANIMALS_PLANTS_OVERLAY_FILENAME  # noqa: E402
from srs_admission_lab_server import (  # noqa: E402
    DEFAULT_TOPIC_OVERLAY_SOURCE_PATHS,
    DEFAULT_ZIPF_BRIDGE_PATH,
    prepare_overlay_source_for_lab,
)
from srs_admission_lab_source_support import (  # noqa: E402
    prepare_lab_frequency_db,
    resolve_kaikki_forward_db,
)
from srs_admission_preference_scenarios_en_es import (  # noqa: E402
    EXPECTED_TOPIC_SCENARIOS,
    SCENARIOS,
)

REPORT_SCHEMA_VERSION = 1
DEFAULT_PAIR = "en-es"
DEFAULT_SET_TOP_N = 10000
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_preference_preview_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_preference_preview_en_es_latest.md"
)


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_frequency_db(pair: str, frequency_db: Path | None) -> Path:
    if frequency_db is not None:
        return frequency_db.expanduser()
    paths = build_helper_paths()
    _jmdict_path, _translation_dict_path, resolved_frequency_db = resolve_pair_resources(
        paths,
        pair=pair,
        jmdict_path=None,
        translation_dict_path=None,
        set_source_db=None,
    )
    if resolved_frequency_db is None:
        raise ValueError(f"Could not resolve a default frequency DB for {pair}.")
    return resolved_frequency_db


def build_report(
    *,
    pair: str = DEFAULT_PAIR,
    frequency_db: Path | None = None,
    overlay_source_path: Path | None = None,
    overlay_source_paths: Sequence[Path] | None = None,
    set_top_n: int = DEFAULT_SET_TOP_N,
    initial_active_count: int = 120,
    preview_count: int = 20,
    preview_sampling_mode: str = "ranked",
    preview_seed: int | None = None,
    augment_with_zipf_bridge: bool = True,
    zipf_bridge_path: Path | None = DEFAULT_ZIPF_BRIDGE_PATH,
    kaikki_forward_db: Path | None = None,
) -> dict[str, Any]:
    resolved_frequency_db = resolve_frequency_db(pair, frequency_db)
    if not resolved_frequency_db.exists():
        raise FileNotFoundError(resolved_frequency_db)
    base_source_summary = inspect_frequency_db(resolved_frequency_db)
    configured_overlay_paths = configured_overlay_source_paths(
        overlay_source_path=overlay_source_path,
        overlay_source_paths=overlay_source_paths,
    )
    resolved_kaikki_forward_db = resolve_kaikki_forward_db(pair, kaikki_forward_db)

    with tempfile.TemporaryDirectory(prefix="lexishift-srs-pref-preview-") as tmp:
        tmp_root = Path(tmp)
        paths = build_helper_paths(tmp_root)
        merged_overlay_source_path = prepare_overlay_source_for_lab(
            work_dir=tmp_root,
            pair=pair,
            overlay_source_paths=configured_overlay_paths,
        )
        preview_frequency_db, source_augmentation = prepare_lab_frequency_db(
            base_frequency_db=resolved_frequency_db,
            pair=pair,
            work_dir=tmp_root,
            overlay_source_path=merged_overlay_source_path,
            augment_with_zipf_bridge=augment_with_zipf_bridge,
            zipf_bridge_path=zipf_bridge_path,
            kaikki_forward_db=resolved_kaikki_forward_db,
        )
        preview_source_summary = inspect_frequency_db(preview_frequency_db)
        copied_overlay_path = copy_overlay_fixture(
            paths.srs_dir,
            overlay_source_path=merged_overlay_source_path,
        )
        scenario_reports = [
            run_scenario(
                paths=paths,
                pair=pair,
                frequency_db=preview_frequency_db,
                scenario=scenario,
                set_top_n=set_top_n,
                initial_active_count=initial_active_count,
                preview_count=preview_count,
                preview_sampling_mode=preview_sampling_mode,
                preview_seed=preview_seed,
            )
            for scenario in SCENARIOS
        ]

    scenario_by_name = {scenario["name"]: scenario for scenario in scenario_reports}
    comparisons = build_comparisons(
        neutral=scenario_by_name["neutral"],
        scenarios=scenario_reports,
    )
    findings = build_findings(
        scenarios=scenario_by_name,
        source_summary=preview_source_summary,
        source_augmentation=source_augmentation,
    )
    summary = summarize_findings(findings)
    summary.update(
        {
            "scenario_count": len(scenario_reports),
            "preference_scenarios_with_topic_movers": sum(
                1
                for scenario in scenario_reports
                if scenario["name"] != "neutral" and scenario["topic_mover_count"] > 0
            ),
            "frequency_db_row_count": preview_source_summary.get("row_count"),
            "base_frequency_db_row_count": base_source_summary.get("row_count"),
            "source_topic_scenarios_with_movers": sum(
                1
                for scenario_name, topic, _code in EXPECTED_TOPIC_SCENARIOS
                if int(
                    dict(
                        scenario_by_name.get(scenario_name, {}).get("topic_mover_counts") or {}
                    ).get(topic, 0)
                )
                > 0
            ),
        }
    )

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": now_iso_utc(),
        "pair": pair,
        "runtime_scope": "admission_preview_only",
        "parameters": {
            "set_top_n": int(set_top_n),
            "initial_active_count": int(initial_active_count),
            "preview_count": int(preview_count),
            "preview_sampling_mode": preview_sampling_mode,
            "preview_seed": preview_seed,
        },
        "inputs": {
            "frequency_db": str(resolved_frequency_db),
            "frequency_db_exists": resolved_frequency_db.exists(),
            "preview_frequency_db": str(preview_frequency_db),
            "overlay_source_path": str(overlay_source_path) if overlay_source_path else None,
            "overlay_source_paths": [str(path) for path in configured_overlay_paths],
            "merged_overlay_source_path": (
                str(merged_overlay_source_path) if merged_overlay_source_path else None
            ),
            "copied_overlay_path": str(copied_overlay_path) if copied_overlay_path else None,
            "augment_with_zipf_bridge": bool(augment_with_zipf_bridge),
            "zipf_bridge_path": str(zipf_bridge_path) if zipf_bridge_path else None,
            "kaikki_forward_db": str(resolved_kaikki_forward_db)
            if resolved_kaikki_forward_db
            else None,
        },
        "source_summary": preview_source_summary,
        "base_source_summary": base_source_summary,
        "source_augmentation": source_augmentation,
        "summary": summary,
        "findings": findings,
        "comparisons": comparisons,
        "scenarios": scenario_reports,
    }


def configured_overlay_source_paths(
    *,
    overlay_source_path: Path | None,
    overlay_source_paths: Sequence[Path] | None,
) -> tuple[Path, ...]:
    if overlay_source_path is not None:
        return (overlay_source_path,)
    if overlay_source_paths is not None:
        return tuple(Path(path) for path in overlay_source_paths)
    return tuple(DEFAULT_TOPIC_OVERLAY_SOURCE_PATHS)


def copy_overlay_fixture(
    srs_dir: Path,
    *,
    overlay_source_path: Path | None,
) -> Path | None:
    if overlay_source_path is None:
        return None
    source = overlay_source_path.expanduser()
    if not source.exists():
        raise FileNotFoundError(source)
    target = srs_dir / "topic_overlays" / ANIMALS_PLANTS_OVERLAY_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


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
    preview_seed: int | None,
) -> dict[str, Any]:
    profile_context = dict(scenario.get("profile_context") or {})
    payload = preview_srs_admission(
        paths,
        config=SetAdmissionPreviewJobConfig(
            pair=pair,
            set_source_db=frequency_db,
            strategy="profile_bootstrap",
            set_top_n=set_top_n,
            initial_active_count=initial_active_count,
            preview_count=preview_count,
            preview_sampling_mode=preview_sampling_mode,
            preview_seed=preview_seed,
            profile_context=profile_context,
            trigger="preference_preview_report",
        ),
    )
    preview = dict(payload.get("preview") or {})
    profile_bootstrap = dict(preview.get("profile_bootstrap") or {})
    admitted_words = [
        simplify_admitted_word(entry)
        for entry in preview.get("admitted_words", ())
        if isinstance(entry, Mapping)
    ]
    topic_movers = [
        entry for entry in admitted_words if str(entry.get("topic_affinity_source") or "").strip()
    ]
    positive_movers = [entry for entry in admitted_words if int(entry.get("rank_delta") or 0) > 0]
    overlay = dict(profile_bootstrap.get("profile_topic_overlay") or {})
    topic_counts = Counter(
        str(entry.get("topic_affinity_source") or "").replace("topic_hint:", "")
        for entry in topic_movers
        if str(entry.get("topic_affinity_source") or "").startswith("topic_hint:")
    )
    return {
        "name": str(scenario.get("name") or ""),
        "description": str(scenario.get("description") or ""),
        "requested_profile_context": profile_context,
        "effective_profile_context": dict(profile_bootstrap.get("profile_context") or {}),
        "plan": {
            key: payload.get("plan", {}).get(key)
            for key in ("strategy_requested", "strategy_effective", "execution_mode", "can_execute")
            if isinstance(payload.get("plan"), Mapping)
        },
        "preview_counts": {
            key: preview.get(key)
            for key in (
                "selected_count",
                "selected_unique_count",
                "admitted_count",
                "sample_count_requested",
                "sample_count_effective",
                "sampling_mode",
            )
        },
        "top_lemmas": [str(entry.get("lemma") or "") for entry in admitted_words],
        "admitted_words": admitted_words,
        "topic_mover_count": len(topic_movers),
        "positive_mover_count": len(positive_movers),
        "topic_mover_counts": dict(sorted(topic_counts.items())),
        "top_topic_movers": topic_movers[:10],
        "active_topic_support": summarize_active_topic_support(
            profile_bootstrap.get("active_topic_support")
        ),
        "profile_topic_overlay": summarize_overlay(overlay),
    }


def simplify_admitted_word(entry: Mapping[str, object]) -> dict[str, Any]:
    signals = entry.get("signals") if isinstance(entry.get("signals"), Mapping) else {}
    return {
        "lemma": str(entry.get("lemma") or ""),
        "pos_bucket": entry.get("pos_bucket"),
        "base_rank": entry.get("base_rank"),
        "reranked_rank": entry.get("reranked_rank"),
        "rank_delta": entry.get("rank_delta"),
        "profile_score": entry.get("profile_score"),
        "selection_mass": entry.get("selection_mass"),
        "admission_weight": entry.get("admission_weight"),
        "difficulty_estimate": signals.get("difficulty_estimate")
        if isinstance(signals, Mapping)
        else None,
        "proficiency_fit": signals.get("proficiency_fit") if isinstance(signals, Mapping) else None,
        "challenge_fit": signals.get("challenge_fit") if isinstance(signals, Mapping) else None,
        "readiness_multiplier": signals.get("readiness_multiplier")
        if isinstance(signals, Mapping)
        else None,
        "readiness_lower_bound": signals.get("readiness_lower_bound")
        if isinstance(signals, Mapping)
        else None,
        "readiness_upper_bound": signals.get("readiness_upper_bound")
        if isinstance(signals, Mapping)
        else None,
        "topic_affinity_source": (
            signals.get("topic_affinity_source") if isinstance(signals, Mapping) else None
        ),
        "topic_affinity": signals.get("topic_affinity") if isinstance(signals, Mapping) else None,
        "scarcity_bonus": signals.get("scarcity_bonus") if isinstance(signals, Mapping) else None,
        "explanation": entry.get("explanation"),
    }


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
                "support_mass": entry.get("support_mass"),
                "scarcity_readiness": entry.get("scarcity_readiness"),
                "top_examples": entry.get("top_examples", []),
            }
        )
    return {
        "scope": value.get("scope"),
        "total_candidates": value.get("total_candidates"),
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


def build_comparisons(
    *,
    neutral: Mapping[str, object],
    scenarios: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    neutral_lemmas = list(neutral.get("top_lemmas") or [])
    comparisons = {}
    for scenario in scenarios:
        name = str(scenario.get("name") or "")
        if name == "neutral":
            continue
        top_lemmas = list(scenario.get("top_lemmas") or [])
        comparisons[f"{name}_vs_neutral"] = {
            "introduced_lemmas": [lemma for lemma in top_lemmas if lemma not in neutral_lemmas],
            "removed_neutral_lemmas": [
                lemma for lemma in neutral_lemmas if lemma not in top_lemmas
            ],
            "top_20_overlap_count": len(set(top_lemmas) & set(neutral_lemmas)),
            "topic_mover_count_delta": int(scenario.get("topic_mover_count") or 0)
            - int(neutral.get("topic_mover_count") or 0),
        }
    return comparisons


def build_findings(
    *,
    scenarios: Mapping[str, Mapping[str, object]],
    source_summary: Mapping[str, object],
    source_augmentation: Mapping[str, object],
) -> list[dict[str, Any]]:
    findings = [
        finding(
            "PASS",
            "FREQUENCY_DB_READABLE",
            f"Frequency DB has {source_summary.get('row_count')} rows.",
        )
    ]
    findings.append(
        finding(
            "PASS" if source_augmentation.get("status") == "applied" else "WARN",
            "ZIPF_AUGMENTED_LAB_SOURCE_AVAILABLE",
            "Dev-only Zipf bridge source was applied for the preference preview."
            if source_augmentation.get("status") == "applied"
            else "Dev-only Zipf bridge source was not applied for the preference preview.",
            source_augmentation,
        )
    )
    for scenario_name, topic, code in EXPECTED_TOPIC_SCENARIOS:
        scenario = scenarios.get(scenario_name)
        if not scenario:
            findings.append(finding("WARN", code, f"{scenario_name} scenario was not available."))
            continue
        findings.append(
            finding_for_movers(
                scenario=scenario,
                code=code,
                topic=topic,
            )
        )
    travel = scenarios.get("travel_places_transport_interest", {})
    travel_counts = dict(travel.get("topic_mover_counts") or {})
    travel_overlay = dict(travel.get("profile_topic_overlay") or {})
    findings.append(
        finding(
            "PASS" if travel_overlay.get("application_status") == "applied" else "WARN",
            "TRAVEL_BETA_TOPIC_EXPOSES_LIMIT",
            "Travel/place/transport preference produced runtime movers."
            if int(travel_counts.get("travel_places_transport", 0)) > 0
            else "Travel/place/transport remains beta-limited in the lab preview.",
            {
                "topic_movers": int(travel_counts.get("travel_places_transport", 0)),
                "application_status": travel_overlay.get("application_status"),
                "eligible_row_count": travel_overlay.get("eligible_row_count"),
                "applied_seed_count": travel_overlay.get("applied_seed_count"),
            },
        )
    )
    weighted = scenarios["weighted_plants_over_animals"]
    weighted_counts = dict(weighted.get("topic_mover_counts") or {})
    findings.append(
        finding(
            "PASS" if int(weighted_counts.get("plants_nature", 0)) > 0 else "WARN",
            "SCALAR_TOPIC_WEIGHTS_AFFECT_PRIORITY",
            "Weighted plants-over-animals profile surfaces plants/nature movers."
            if int(weighted_counts.get("plants_nature", 0)) > 0
            else "Weighted plants-over-animals profile did not surface plants/nature movers.",
        )
    )
    light = scenarios.get("animals_light_weight", {})
    strong = scenarios.get("animals_interest", {})
    findings.append(
        finding(
            "PASS"
            if int(strong.get("topic_mover_count") or 0) >= int(light.get("topic_mover_count") or 0)
            else "WARN",
            "TOPIC_STRENGTH_IS_MONOTONIC_IN_SMOKE",
            "Full animals preference produced at least as many topic movers as light animals weight."
            if int(strong.get("topic_mover_count") or 0) >= int(light.get("topic_mover_count") or 0)
            else "Light animals weight produced more topic movers than full animals preference.",
            {
                "animals_light_weight_movers": int(light.get("topic_mover_count") or 0),
                "animals_interest_movers": int(strong.get("topic_mover_count") or 0),
            },
        )
    )
    findings.append(high_proficiency_finding(scenarios.get("animals_high_proficiency", {})))
    return findings


def high_proficiency_finding(scenario: Mapping[str, object]) -> dict[str, Any]:
    animal_movers = [
        row
        for row in scenario.get("admitted_words", ())
        if isinstance(row, Mapping)
        and str(row.get("topic_affinity_source") or "").startswith("topic_hint:animals")
    ]
    too_easy = [
        str(row.get("lemma") or "")
        for row in animal_movers
        if _safe_float(row.get("readiness_multiplier")) is not None
        and (_safe_float(row.get("readiness_multiplier")) or 0.0) < 0.5
    ]
    return finding(
        "PASS" if not too_easy else "WARN",
        "HIGH_PROFICIENCY_SUPPRESSES_TOO_EASY_TOPIC_ITEMS",
        "High-proficiency animals scenario selected ready animal movers."
        if animal_movers and not too_easy
        else "High-proficiency animals scenario suppressed too-easy animal movers."
        if not too_easy
        else "High-proficiency animals scenario needs inspection for topic readiness.",
        {
            "animal_mover_count": len(animal_movers),
            "too_easy_animal_movers": too_easy,
            "top_lemmas": list(scenario.get("top_lemmas") or [])[:10],
        },
    )


def finding_for_movers(
    *,
    scenario: Mapping[str, object],
    code: str,
    topic: str,
) -> dict[str, Any]:
    count = int(dict(scenario.get("topic_mover_counts") or {}).get(topic, 0))
    overlay = dict(scenario.get("profile_topic_overlay") or {})
    return finding(
        "PASS" if count > 0 and overlay.get("application_status") == "applied" else "WARN",
        code,
        f"{topic} preference produced {count} topic movers in the admission preview.",
        {
            "application_status": overlay.get("application_status"),
            "applied_seed_count": overlay.get("applied_seed_count"),
            "applied_row_count": overlay.get("applied_row_count"),
        },
    )


def finding(
    level: str,
    code: str,
    message: str,
    details: object | None = None,
) -> dict[str, Any]:
    payload = {"level": level, "code": code, "message": message}
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


def _safe_float(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None


def inspect_frequency_db(path: Path) -> dict[str, Any]:
    with sqlite3.connect(path) as conn:
        row_count = int(conn.execute("select count(*) from frequency").fetchone()[0])
        distinct_lemma_count = int(
            conn.execute(
                "select count(distinct lemma) from frequency where coalesce(lemma, '') != ''"
            ).fetchone()[0]
        )
        columns = [row[1] for row in conn.execute("pragma table_info(frequency)").fetchall()]
    return {
        "path": str(path),
        "row_count": row_count,
        "distinct_non_empty_lemma_count": distinct_lemma_count,
        "columns": columns,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = dict(report.get("summary") or {})
    lines = [
        "# SRS Admission Preference Preview - en-es",
        "",
        f"- Status: {summary.get('status')}",
        f"- Findings: pass={summary.get('pass_count')} warn={summary.get('warn_count')} fail={summary.get('fail_count')}",
        f"- Frequency DB rows: {summary.get('frequency_db_row_count')}",
        f"- Base frequency DB rows: {summary.get('base_frequency_db_row_count')}",
        f"- Runtime scope: {report.get('runtime_scope')}",
        "",
        "## Inputs",
        "",
        f"- frequency_db: `{dict(report.get('inputs') or {}).get('frequency_db')}`",
        f"- preview_frequency_db: `{dict(report.get('inputs') or {}).get('preview_frequency_db')}`",
        f"- merged_overlay_source_path: `{dict(report.get('inputs') or {}).get('merged_overlay_source_path')}`",
        f"- set_top_n: {dict(report.get('parameters') or {}).get('set_top_n')}",
        f"- initial_active_count: {dict(report.get('parameters') or {}).get('initial_active_count')}",
        f"- preview_count: {dict(report.get('parameters') or {}).get('preview_count')}",
        "",
        "## Source Augmentation",
        "",
    ]
    augmentation = dict(report.get("source_augmentation") or {})
    lines.extend(
        [
            f"- status: `{augmentation.get('status')}`",
            f"- output_row_count: {augmentation.get('output_row_count')}",
            f"- added_row_count: {augmentation.get('added_row_count')}",
            f"- overlay_topic_lemma_count: {augmentation.get('overlay_topic_lemma_count')}",
            f"- overlay_missing_without_bridge_count: {augmentation.get('overlay_missing_without_bridge_count')}",
            "",
        ]
    )
    lines.extend(
        [
            "## Scenario Summary",
            "",
            "| Scenario | Topic movers | Overlay application | Top lemmas |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for scenario in report.get("scenarios", ()):
        if not isinstance(scenario, Mapping):
            continue
        overlay = dict(scenario.get("profile_topic_overlay") or {})
        top_lemmas = ", ".join(str(value) for value in list(scenario.get("top_lemmas") or [])[:8])
        lines.append(
            f"| {scenario.get('name')} | {scenario.get('topic_mover_count')} | "
            f"{overlay.get('application_status', 'n/a')} | {top_lemmas} |"
        )
    lines.extend(["", "## Findings", ""])
    for item in report.get("findings", ()):
        if not isinstance(item, Mapping):
            continue
        lines.append(f"- {item.get('level')}: `{item.get('code')}` - {item.get('message')}")
    lines.extend(["", "## Top Topic Movers", ""])
    for scenario in report.get("scenarios", ()):
        if not isinstance(scenario, Mapping):
            continue
        movers = list(scenario.get("top_topic_movers") or [])
        if not movers:
            continue
        lines.append(f"### {scenario.get('name')}")
        for mover in movers[:8]:
            if not isinstance(mover, Mapping):
                continue
            lines.append(
                "- "
                f"{mover.get('lemma')}: base_rank={mover.get('base_rank')}, "
                f"reranked_rank={mover.get('reranked_rank')}, "
                f"delta={mover.get('rank_delta')}, "
                f"source={mover.get('topic_affinity_source')}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: Mapping[str, object], *, json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare en-es SRS admission previews across preference profiles."
    )
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--overlay-source-path", type=Path)
    parser.add_argument(
        "--overlay-source-paths",
        type=Path,
        nargs="*",
        help="Optional overlay artifact paths. Defaults to the admission lab overlay stack.",
    )
    parser.add_argument("--set-top-n", type=int, default=DEFAULT_SET_TOP_N)
    parser.add_argument("--initial-active-count", type=int, default=120)
    parser.add_argument("--preview-count", type=int, default=20)
    parser.add_argument(
        "--preview-sampling-mode",
        choices=("ranked", "weighted_without_replacement"),
        default="ranked",
    )
    parser.add_argument("--preview-seed", type=int)
    parser.add_argument(
        "--augment-with-zipf-bridge",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use the dev-only Zipf bridge augmentation to smoke the expanded 10k source path.",
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
        initial_active_count=args.initial_active_count,
        preview_count=args.preview_count,
        preview_sampling_mode=args.preview_sampling_mode,
        preview_seed=args.preview_seed,
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
