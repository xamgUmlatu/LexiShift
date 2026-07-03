#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (CORE_ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.use_cases.refresh_set import (  # noqa: E402
    _profile_growth_selector_candidates,
)
from lexishift_core.srs import SrsSettings, SrsStore  # noqa: E402
from lexishift_core.srs.admission_refresh import (  # noqa: E402
    AdmissionRefreshPolicy,
    preview_browsing_admission_refresh,
)
from lexishift_core.srs.browsing_admission import (  # noqa: E402
    BrowsingSignalIngestPolicy,
    BrowsingSignalPacket,
    BrowsingSignalPacketEntry,
    BrowsingSignalStore,
    aggregate_target_key,
    browsing_raw_value,
    browsing_signal_value,
    ingest_browsing_signal_packet,
)
from lexishift_core.srs.profile_bootstrap import DEFAULT_PROFILE_BOOTSTRAP_POLICY  # noqa: E402
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from lexishift_core.srs.set_strategy import STRATEGY_PROFILE_GROWTH  # noqa: E402
from lexishift_core.srs.time import parse_ts  # noqa: E402
from lexishift_core.srs.topic_overlay import (  # noqa: E402
    apply_profile_topic_overlay_to_seeds,
    resolve_preview_profile_topic_overlay,
)
from srs_admission_preference_sample_pack_en_ja import (  # noqa: E402
    DEFAULT_CORRECTED_RANKING_CSV,
    DEFAULT_OVERLAY_SOURCE_PATH,
    DEFAULT_PAIR,
    build_profile_context,
    copy_overlay_source,
    corrected_ranking_runtime_env,
    load_json_mapping,
    resolve_live_resources,
    safe_float,
)
from srs_browsing_admission_implicit_sample_pack_en_ja import (  # noqa: E402
    compact_browsing_preview,
    compact_overlay_payload,
    compact_profile_growth_payload,
    evaluate_scenario as evaluate_preview_expectations,
    fail_finding,
    filter_scenarios,
    pass_finding,
    scenario_status,
    summarize_findings,
)
from srs_browsing_admission_saved_page_pack_en_ja import (  # noqa: E402
    build_signal_entries,
)
from srs_browsing_admission_saved_page_support import (  # noqa: E402
    SavedPagePolicy,
    build_jmdict_indexes,
    collect_source_counts,
    counter_preview,
    document_summary,
    load_saved_documents,
    repo_path,
    resolve_pair_data_paths,
    ruby_preview,
)


REPORT_SCHEMA_VERSION = 1
DEFAULT_CONFIG_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_browsing_admission_saved_page_admission_configs_en_ja.json"
)
DEFAULT_MANIFEST_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_browsing_admission_saved_pages_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_browsing_admission_saved_page_admission_pack_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_browsing_admission_saved_page_admission_pack_en_ja_latest.md"
)
DEFAULT_ROW_LIMIT = 60
SAVED_PAGE_PROFILE_ID = "saved_page_admission_pack"
SAVED_PAGE_CAPTURED_AT = "2026-07-03T00:00:00Z"


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(
    *,
    config_json: Path,
    manifest_json: Path,
    pair: str,
    frequency_db: Path | None,
    jmdict_path: Path | None,
    overlay_source_path: Path | None,
    corrected_ranking_csv: Path | None,
    scenario_filter: Sequence[str],
    set_top_n: int | None,
    admission_budget: int | None,
    max_active_items: int | None,
    row_limit: int | None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    config = load_json_mapping(config_json)
    defaults = dict(config.get("defaults") or {})
    resolved_pair = str(config.get("pair") or pair or DEFAULT_PAIR)
    resolved_set_top_n = int(set_top_n or defaults.get("set_top_n") or 12000)
    resolved_admission_budget = int(admission_budget or defaults.get("admission_budget") or 8)
    resolved_max_active_items = int(max_active_items or defaults.get("max_active_items") or 20)
    resolved_row_limit = int(row_limit or defaults.get("row_limit") or DEFAULT_ROW_LIMIT)
    selected_scenarios = filter_scenarios(
        [row for row in config.get("scenarios", []) if isinstance(row, Mapping)],
        scenario_filter=scenario_filter,
    )
    resolved_frequency_db, resolved_jmdict_path = resolve_live_resources(
        pair=resolved_pair,
        frequency_db=frequency_db,
        jmdict_path=jmdict_path,
    )
    saved_page_aggregate = build_saved_page_aggregate(
        manifest_json=manifest_json,
        pair=resolved_pair,
        jmdict_path=resolved_jmdict_path,
        frequency_db=resolved_frequency_db,
        policy=SavedPagePolicy(),
    )
    resolved_overlay_source_path = overlay_source_path
    if resolved_overlay_source_path is None and DEFAULT_OVERLAY_SOURCE_PATH.exists():
        resolved_overlay_source_path = DEFAULT_OVERLAY_SOURCE_PATH

    with tempfile.TemporaryDirectory(prefix="lexishift-srs-saved-page-admission-enja-") as tmp:
        paths = build_helper_paths(Path(tmp))
        copied_overlay_path = copy_overlay_source(paths, resolved_overlay_source_path)
        seed_cache_dir = Path(tmp) / "seed_cache"
        with corrected_ranking_runtime_env(corrected_ranking_csv):
            base_seeds = build_seed_candidates(
                frequency_db=resolved_frequency_db,
                config=SeedSelectionConfig(
                    language_pair=resolved_pair,
                    top_n=resolved_set_top_n,
                    jmdict_path=resolved_jmdict_path,
                    cache_dir=seed_cache_dir,
                ),
            )
            scenario_reports = [
                run_scenario(
                    paths=paths,
                    pair=resolved_pair,
                    base_seeds=base_seeds,
                    browsing_store=saved_page_aggregate["store"],
                    scenario=scenario,
                    admission_budget=resolved_admission_budget,
                    max_active_items=resolved_max_active_items,
                    row_limit=resolved_row_limit,
                )
                for scenario in selected_scenarios
            ]

    findings = build_findings(scenario_reports)
    summary = summarize_findings(findings)
    summary.update(
        {
            "scenario_count": len(scenario_reports),
            "scenario_pass_count": sum(
                1 for row in scenario_reports if row.get("status") == "pass"
            ),
            "scenario_warn_count": sum(
                1 for row in scenario_reports if row.get("status") == "warn"
            ),
            "scenario_fail_count": sum(
                1 for row in scenario_reports if row.get("status") == "fail"
            ),
            "saved_page_signal_count": saved_page_aggregate["summary"]["signal_count"],
            "saved_page_store_item_count": saved_page_aggregate["summary"]["store_item_count"],
        }
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": generated_at or now_iso_utc(),
        "pair": resolved_pair,
        "runtime_scope": "preview_only_saved_page_browsing_admission",
        "method": {
            "strategy": STRATEGY_PROFILE_GROWTH,
            "candidate_source": (
                "Real en-ja seed frontier plus profile-growth scoring; saved-page browsing "
                "effects enter only through preview_browsing_admission_refresh."
            ),
            "saved_page_signal_scope": (
                "Local saved-page fixtures are converted to reading-aware browsing aggregate "
                "keys, then compared against the real candidate frontier."
            ),
            "production_effect": (
                "None. This harness builds a temporary browsing store and never mutates live "
                "SRS state."
            ),
        },
        "parameters": {
            "set_top_n": resolved_set_top_n,
            "admission_budget": resolved_admission_budget,
            "max_active_items": resolved_max_active_items,
            "row_limit": resolved_row_limit,
        },
        "inputs": {
            "config_json": repo_path(config_json),
            "manifest_json": repo_path(manifest_json),
            "frequency_db": str(resolved_frequency_db),
            "jmdict": str(resolved_jmdict_path),
            "overlay_source_path": str(resolved_overlay_source_path)
            if resolved_overlay_source_path
            else None,
            "copied_overlay_path": str(copied_overlay_path) if copied_overlay_path else None,
            "corrected_ranking_csv": str(corrected_ranking_csv) if corrected_ranking_csv else None,
        },
        "summary": summary,
        "saved_page_aggregate": {
            key: value for key, value in saved_page_aggregate.items() if key != "store"
        },
        "findings": findings,
        "scenarios": scenario_reports,
    }


def build_saved_page_aggregate(
    *,
    manifest_json: Path,
    pair: str,
    jmdict_path: Path,
    frequency_db: Path | None,
    policy: SavedPagePolicy,
) -> dict[str, Any]:
    manifest = load_json_mapping(manifest_json)
    resolved_jmdict_path, resolved_frequency_db = resolve_pair_data_paths(
        pair=pair,
        jmdict_path=jmdict_path,
        frequency_db=frequency_db,
    )
    documents = load_saved_documents(manifest)
    source_counts = collect_source_counts(documents)
    target_text = "\n".join(document.text for document in documents if document.side == "target")
    source_index, target_index, exact_pairs, jmdict_summary = build_jmdict_indexes(
        resolved_jmdict_path,
        source_terms=set(source_counts),
        target_text=target_text,
        frequency_db=resolved_frequency_db,
        policy=policy,
    )
    signals, signal_debug = build_signal_entries(
        documents=documents,
        source_counts=source_counts,
        source_index=source_index,
        target_index=target_index,
        exact_pairs=exact_pairs,
        policy=policy,
    )
    ingest_policy = BrowsingSignalIngestPolicy(
        max_signals_per_packet=300,
        max_count_per_signal=policy.max_count_per_signal,
        max_items_per_store=1000,
    )
    packet = BrowsingSignalPacket(
        pair=pair,
        profile_id=SAVED_PAGE_PROFILE_ID,
        captured_at=SAVED_PAGE_CAPTURED_AT,
        signals=tuple(packet_entry_from_signal(signal) for signal in signals),
    )
    ingest_result = ingest_browsing_signal_packet(
        BrowsingSignalStore(pair=pair, profile_id=SAVED_PAGE_PROFILE_ID),
        packet,
        policy=ingest_policy,
        now=parse_ts(SAVED_PAGE_CAPTURED_AT),
    )
    store = ingest_result.store
    return {
        "store": store,
        "summary": {
            "signal_count": len(signals),
            "store_item_count": len(store.items),
            "source_term_count": len(source_counts),
            "target_document_count": sum(1 for document in documents if document.side == "target"),
            "source_document_count": sum(1 for document in documents if document.side == "source"),
        },
        "policy": policy.to_dict(),
        "ingest_policy": ingest_policy.__dict__,
        "ingest_result": ingest_result.to_dict(),
        "inputs": {
            "manifest_json": repo_path(manifest_json),
            "jmdict_path": str(resolved_jmdict_path),
            "frequency_db": str(resolved_frequency_db),
            "documents": [document_summary(document) for document in documents],
        },
        "jmdict": jmdict_summary,
        "extraction": {
            "source_terms": counter_preview(source_counts),
            "ruby_pair_count": sum(sum(document.ruby_pairs.values()) for document in documents),
            "top_ruby_pairs": ruby_preview(documents),
        },
        "signals": {
            "count": len(signals),
            "top": signal_debug[:30],
        },
        "store_preview": store_preview(store, ingest_policy),
    }


def packet_entry_from_signal(signal: Mapping[str, object]) -> BrowsingSignalPacketEntry:
    return BrowsingSignalPacketEntry(
        target_lemma=str(signal.get("target_lemma") or signal.get("lemma") or "").strip(),
        target_key=str(signal.get("target_key") or "").strip(),
        target_reading=str(signal.get("target_reading") or signal.get("reading") or "").strip(),
        side=str(signal.get("side") or "").strip(),
        count=safe_float(signal.get("count")) or 1.0,
        source_mapping_confidence=safe_float(signal.get("source_mapping_confidence")) or 1.0,
        reading_confidence=safe_float(signal.get("reading_confidence")) or 1.0,
        observation_source=str(signal.get("observation_source") or "").strip(),
    )


def store_preview(
    store: BrowsingSignalStore,
    policy: BrowsingSignalIngestPolicy,
    *,
    limit: int = 30,
) -> list[dict[str, object]]:
    rows = []
    for aggregate in store.items.values():
        rows.append(
            {
                "target_key": aggregate_target_key(aggregate),
                "target_lemma": aggregate.target_lemma,
                "target_reading": aggregate.target_reading,
                "source_hit_count": round(float(aggregate.source_hit_count), 6),
                "target_hit_count": round(float(aggregate.target_hit_count), 6),
                "replacement_exposure_count": round(float(aggregate.replacement_exposure_count), 6),
                "source_mapping_confidence": round(float(aggregate.source_mapping_confidence), 6),
                "reading_confidence": round(float(aggregate.reading_confidence), 6),
                "raw_value": round(browsing_raw_value(aggregate, policy=policy), 6),
                "signal_value": round(browsing_signal_value(aggregate, policy=policy), 6),
                "observation_sources": list(aggregate.observation_sources),
            }
        )
    rows.sort(
        key=lambda row: (
            -(safe_float(row.get("raw_value")) or 0.0),
            str(row.get("target_key") or ""),
        )
    )
    return rows[:limit]


def run_scenario(
    *,
    paths: object,
    pair: str,
    base_seeds: Sequence[object],
    browsing_store: BrowsingSignalStore,
    scenario: Mapping[str, object],
    admission_budget: int,
    max_active_items: int,
    row_limit: int,
) -> dict[str, Any]:
    profile_context = build_profile_context(scenario)
    overlay_payload, overlay_diagnostics = resolve_preview_profile_topic_overlay(
        paths,
        pair=pair,
        profile_context=profile_context,
    )
    seeds, overlay_application = apply_profile_topic_overlay_to_seeds(
        base_seeds,
        overlay_payload=overlay_payload,
        profile_context=profile_context,
        pair=pair,
        diagnostics=overlay_diagnostics,
    )
    candidates, profile_diagnostics = _profile_growth_selector_candidates(
        seeds,
        profile_context=profile_context,
    )
    blocked_lemmas = {
        str(lemma or "").strip()
        for lemma in scenario.get("blocked_lemmas", [])
        if str(lemma or "").strip()
    }
    policy = AdmissionRefreshPolicy(
        max_active_items_override=max_active_items,
        max_new_items_override=admission_budget,
        selector_config=DEFAULT_PROFILE_BOOTSTRAP_POLICY.selector_config,
        blocked_lemmas=blocked_lemmas or None,
    )
    preview = preview_browsing_admission_refresh(
        store=SrsStore(),
        settings=SrsSettings(
            max_active_items=max_active_items,
            max_new_items_per_day=admission_budget,
        ),
        pair=pair,
        candidates=candidates,
        events=(),
        browsing_store=browsing_store,
        policy=policy,
        row_limit=row_limit,
    )
    compact_preview = compact_browsing_preview(preview, candidate_count=len(candidates))
    scenario_findings = evaluate_scenario(
        scenario=scenario,
        preview=compact_preview,
        blocked_lemmas=blocked_lemmas,
    )
    return {
        "name": str(scenario.get("name") or ""),
        "description": str(scenario.get("description") or ""),
        "status": scenario_status(scenario_findings),
        "proficiency": safe_float(scenario.get("proficiency")),
        "topic_weights": dict(scenario.get("topic_weights") or {}),
        "blocked_lemmas": sorted(blocked_lemmas),
        "expectations": dict(scenario.get("expectations") or {}),
        "profile_context": profile_context,
        "overlay": compact_overlay_payload(overlay_application),
        "profile_growth": compact_profile_growth_payload(profile_diagnostics),
        "browsing_preview": compact_preview,
        "qualitative_delta": qualitative_delta(compact_preview),
        "findings": scenario_findings,
    }


def evaluate_scenario(
    *,
    scenario: Mapping[str, object],
    preview: Mapping[str, object],
    blocked_lemmas: set[str],
) -> list[dict[str, Any]]:
    findings = evaluate_preview_expectations(
        scenario=scenario,
        preview=preview,
        blocked_lemmas=blocked_lemmas,
    )
    expectations = dict(scenario.get("expectations") or {})
    min_matching_signal_count = int(expectations.get("min_matching_signal_count") or 0)
    if min_matching_signal_count:
        matching_signal_count = int(preview.get("matching_signal_count") or 0)
        if matching_signal_count >= min_matching_signal_count:
            findings.append(
                pass_finding(
                    "MIN_MATCHING_SIGNAL_COUNT",
                    (
                        "Saved-page aggregate matched enough real admission candidates "
                        f"({matching_signal_count} >= {min_matching_signal_count})."
                    ),
                )
            )
        else:
            findings.append(
                fail_finding(
                    "MIN_MATCHING_SIGNAL_COUNT",
                    (
                        "Saved-page aggregate matched too few real admission candidates "
                        f"({matching_signal_count} < {min_matching_signal_count})."
                    ),
                )
            )
    strong = dict(dict(preview.get("simulations") or {}).get("strong") or {})
    strong_rows = [
        row
        for row in strong.get("browsing_signal_rows", [])
        if isinstance(row, Mapping) and "effective_browsing_signal" in row
    ]
    if strong_rows:
        findings.append(
            pass_finding(
                "EFFECTIVE_SIGNAL_FIELDS_PRESENT",
                "Strong preview rows expose raw and effective browsing signal fields.",
            )
        )
    return findings


def qualitative_delta(preview: Mapping[str, object]) -> dict[str, object]:
    simulations = dict(preview.get("simulations") or {})
    off = dict(simulations.get("off") or {})
    balanced = dict(simulations.get("balanced") or {})
    strong = dict(simulations.get("strong") or {})
    off_selected = tuple(str(item) for item in off.get("selected_lemmas") or ())
    balanced_selected = tuple(str(item) for item in balanced.get("selected_lemmas") or ())
    strong_selected = tuple(str(item) for item in strong.get("selected_lemmas") or ())
    return {
        "balanced_added_vs_off": ordered_difference(balanced_selected, off_selected),
        "strong_added_vs_off": ordered_difference(strong_selected, off_selected),
        "strong_added_vs_balanced": ordered_difference(strong_selected, balanced_selected),
        "strong_removed_vs_off": ordered_difference(off_selected, strong_selected),
    }


def ordered_difference(left: Sequence[str], right: Sequence[str]) -> list[str]:
    right_set = set(right)
    return [item for item in left if item not in right_set]


def build_findings(scenarios: Sequence[Mapping[str, object]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    failing = [str(row.get("name") or "") for row in scenarios if row.get("status") == "fail"]
    warning = [str(row.get("name") or "") for row in scenarios if row.get("status") == "warn"]
    if failing:
        findings.append(
            {
                "level": "FAIL",
                "code": "SCENARIO_FAILURES",
                "message": "One or more saved-page browsing admission scenarios failed.",
                "details": {"scenarios": failing},
            }
        )
    elif warning:
        findings.append(
            {
                "level": "WARN",
                "code": "SCENARIO_WARNINGS",
                "message": "One or more saved-page browsing admission scenarios warned.",
                "details": {"scenarios": warning},
            }
        )
    else:
        findings.append(
            {
                "level": "PASS",
                "code": "ALL_SCENARIOS_PASS",
                "message": (
                    "All saved-page browsing admission scenarios satisfied configured expectations."
                ),
            }
        )
    return findings


def render_markdown(report: Mapping[str, object]) -> str:
    summary = dict(report.get("summary") or {})
    saved_page = dict(report.get("saved_page_aggregate") or {})
    aggregate_summary = dict(saved_page.get("summary") or {})
    lines = [
        "# SRS Browsing Admission Saved-Page Admission Pack (en-ja)",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Scenarios: `{summary.get('scenario_count', 0)}`",
        f"- Scenario pass/warn/fail: `{summary.get('scenario_pass_count', 0)}` / "
        f"`{summary.get('scenario_warn_count', 0)}` / `{summary.get('scenario_fail_count', 0)}`",
        f"- Saved-page signals: `{aggregate_summary.get('signal_count', 0)}`",
        f"- Saved-page aggregate items: `{aggregate_summary.get('store_item_count', 0)}`",
        f"- Runtime scope: `{report.get('runtime_scope', '')}`",
        "",
        "## Interpretation",
        "",
        (
            "This pack starts after saved-page extraction has produced target-key browsing "
            "signals. It tests whether those signals materially affect a real en-ja "
            "profile-growth admission frontier, while remaining preview-only."
        ),
        "",
        "## Saved-Page Aggregate",
        "",
        "| Target | Raw | Signal | Source | Target | Reading | Sources |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in saved_page.get("store_preview", [])[:16]:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            f"`{row.get('target_key', '')}` | "
            f"{row.get('raw_value', '')} | "
            f"{row.get('signal_value', '')} | "
            f"{row.get('source_hit_count', '')} | "
            f"{row.get('target_hit_count', '')} | "
            f"{row.get('reading_confidence', '')} | "
            f"`{', '.join(row.get('observation_sources') or [])}` |"
        )
    lines.extend(["", "## Scenarios", ""])
    for scenario in report.get("scenarios", []):
        if not isinstance(scenario, Mapping):
            continue
        preview = dict(scenario.get("browsing_preview") or {})
        simulations = dict(preview.get("simulations") or {})
        delta = dict(scenario.get("qualitative_delta") or {})
        lines.extend(
            [
                f"### {scenario.get('name', '')}",
                "",
                f"- Status: `{scenario.get('status', '')}`",
                f"- Proficiency: `{scenario.get('proficiency', '')}`",
                f"- Topic weights: `{json.dumps(scenario.get('topic_weights') or {}, ensure_ascii=False)}`",
                f"- Matching signals: `{preview.get('matching_signal_count', 0)}` / aggregate items `{preview.get('aggregate_item_count', 0)}`",
                f"- Candidate pool: `{preview.get('candidate_pool_effective', 0)}`",
                f"- Strong added vs off: `{', '.join(delta.get('strong_added_vs_off') or [])}`",
                "",
                "| Strength | Browsing lane | Driven | Signal volume | Selected |",
                "| --- | ---: | ---: | ---: | --- |",
            ]
        )
        for strength in ("off", "balanced", "strong"):
            sim = dict(simulations.get(strength) or {})
            selected = ", ".join(str(item) for item in sim.get("selected_lemmas", [])[:12])
            lines.append(
                f"| `{strength}` | {sim.get('browsing_lane_count', 0)} | "
                f"{sim.get('browsing_driven_count', 0)} | "
                f"{round(safe_float(sim.get('signal_volume')) or 0.0, 6)} | {selected} |"
            )
        strong = dict(simulations.get("strong") or {})
        rows = [row for row in strong.get("browsing_signal_rows", []) if isinstance(row, Mapping)]
        if rows:
            lines.extend(
                [
                    "",
                    "Strong browsing rows:",
                    "",
                    "| Target | Raw | Effective | Quality | Specificity | Boost | Selected |",
                    "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
                ]
            )
            for row in rows[:10]:
                lines.append(
                    "| "
                    f"`{row.get('target_key') or row.get('lemma') or ''}` | "
                    f"{row.get('browsing_signal', '')} | "
                    f"{row.get('effective_browsing_signal', '')} | "
                    f"{row.get('browsing_quality_multiplier', '')} | "
                    f"{row.get('browsing_specificity_multiplier', '')} | "
                    f"{row.get('browsing_boost', '')} | "
                    f"`{row.get('selected', '')}` |"
                )
        lines.extend(["", "Findings:"])
        for finding in scenario.get("findings", []):
            if isinstance(finding, Mapping):
                lines.append(
                    f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
                    f"{finding.get('message', '')}"
                )
        lines.append("")
    lines.extend(
        [
            "## Findings",
            "",
            "| Level | Code | Message |",
            "| --- | --- | --- |",
        ]
    )
    for finding in report.get("findings", []):
        if isinstance(finding, Mapping):
            lines.append(
                f"| `{finding.get('level', '')}` | `{finding.get('code', '')}` | "
                f"{finding.get('message', '')} |"
            )
    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build en-ja saved-page browsing admission preview sample pack."
    )
    parser.add_argument("--config-json", type=Path, default=DEFAULT_CONFIG_JSON)
    parser.add_argument("--manifest-json", type=Path, default=DEFAULT_MANIFEST_JSON)
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--jmdict", type=Path)
    parser.add_argument("--overlay-json", type=Path)
    parser.add_argument("--corrected-ranking-csv", type=Path, default=DEFAULT_CORRECTED_RANKING_CSV)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--set-top-n", type=int)
    parser.add_argument("--admission-budget", type=int)
    parser.add_argument("--max-active-items", type=int)
    parser.add_argument("--row-limit", type=int)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        config_json=args.config_json,
        manifest_json=args.manifest_json,
        pair=str(args.pair),
        frequency_db=args.frequency_db,
        jmdict_path=args.jmdict,
        overlay_source_path=args.overlay_json,
        corrected_ranking_csv=args.corrected_ranking_csv,
        scenario_filter=args.scenario,
        set_top_n=args.set_top_n,
        admission_budget=args.admission_budget,
        max_active_items=args.max_active_items,
        row_limit=args.row_limit,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"json_out: {args.json_out}")
    print(f"markdown_out: {args.markdown_out}")
    print(
        "summary: "
        f"status={report['summary']['status']} "
        f"pass={report['summary']['pass_count']} "
        f"warn={report['summary']['warn_count']} "
        f"fail={report['summary']['fail_count']}"
    )
    if args.fail_on_review and report["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
