#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
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
from lexishift_core.srs import SrsSettings, SrsStore  # noqa: E402
from lexishift_core.srs.admission_refresh import (  # noqa: E402
    AdmissionRefreshPolicy,
    preview_browsing_admission_refresh,
)
from lexishift_core.srs.browsing_admission import (  # noqa: E402
    BROWSING_SIGNAL_REPLACEMENT_EXPOSURE,
    BROWSING_SIGNAL_SOURCE,
    BROWSING_SIGNAL_TARGET,
    BrowsingSignalAggregate,
    BrowsingSignalStore,
)
from lexishift_core.srs.profile_bootstrap import DEFAULT_PROFILE_BOOTSTRAP_POLICY  # noqa: E402
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from lexishift_core.srs.set_strategy import STRATEGY_PROFILE_GROWTH  # noqa: E402
from lexishift_core.srs.topic_overlay import (  # noqa: E402
    apply_profile_topic_overlay_to_seeds,
    resolve_preview_profile_topic_overlay,
)
from lexishift_core.helper.use_cases.refresh_set import (  # noqa: E402
    _profile_growth_selector_candidates,
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


REPORT_SCHEMA_VERSION = 1
DEFAULT_CONFIG_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_browsing_admission_implicit_configs_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_browsing_admission_implicit_sample_pack_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_browsing_admission_implicit_sample_pack_en_ja_latest.md"
)
DEFAULT_ROW_LIMIT = 40


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_report(
    *,
    config_json: Path,
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
) -> dict[str, Any]:
    config = load_json_mapping(config_json)
    defaults = dict(config.get("defaults") or {})
    resolved_set_top_n = int(set_top_n or defaults.get("set_top_n") or 5000)
    resolved_admission_budget = int(admission_budget or defaults.get("admission_budget") or 8)
    resolved_max_active_items = int(max_active_items or defaults.get("max_active_items") or 20)
    resolved_row_limit = int(row_limit or defaults.get("row_limit") or DEFAULT_ROW_LIMIT)
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

    with tempfile.TemporaryDirectory(prefix="lexishift-srs-implicit-enja-") as tmp:
        paths = build_helper_paths(Path(tmp))
        copied_overlay_path = copy_overlay_source(paths, resolved_overlay_source_path)
        seed_cache_dir = Path(tmp) / "seed_cache"
        with corrected_ranking_runtime_env(corrected_ranking_csv):
            base_seeds = build_seed_candidates(
                frequency_db=resolved_frequency_db,
                config=SeedSelectionConfig(
                    language_pair=pair,
                    top_n=resolved_set_top_n,
                    jmdict_path=resolved_jmdict_path,
                    cache_dir=seed_cache_dir,
                ),
            )
            scenario_reports = [
                run_scenario(
                    paths=paths,
                    pair=pair,
                    base_seeds=base_seeds,
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
        }
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": now_iso_utc(),
        "pair": pair,
        "runtime_scope": "preview_only_implicit_browsing_admission",
        "method": {
            "strategy": STRATEGY_PROFILE_GROWTH,
            "candidate_source": (
                "Real en-ja seed frontier plus profile-growth scoring; browsing effects are "
                "applied only through preview_browsing_admission_refresh."
            ),
            "implicit_signal_scope": (
                "Synthetic target-lemma aggregates. This artifact does not test live page-text "
                "or source-language extraction."
            ),
            "production_effect": (
                "None. Current helper refresh still persists neutral/profile-growth admission; "
                "browsing output is a preview diagnostic."
            ),
        },
        "parameters": {
            "set_top_n": resolved_set_top_n,
            "admission_budget": resolved_admission_budget,
            "max_active_items": resolved_max_active_items,
            "row_limit": resolved_row_limit,
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
        },
        "summary": summary,
        "findings": findings,
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
    base_seeds: Sequence[object],
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
    browsing_store = build_browsing_store(
        pair=pair,
        scenario=scenario,
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
        "signal_count": len(normalize_signal_entries(scenario.get("signals"))),
        "signals": normalize_signal_entries(scenario.get("signals")),
        "blocked_lemmas": sorted(blocked_lemmas),
        "expectations": dict(scenario.get("expectations") or {}),
        "profile_context": profile_context,
        "overlay": compact_overlay_payload(overlay_application),
        "profile_growth": compact_profile_growth_payload(profile_diagnostics),
        "browsing_preview": compact_preview,
        "findings": scenario_findings,
    }


def build_browsing_store(
    *,
    pair: str,
    scenario: Mapping[str, object],
) -> BrowsingSignalStore:
    items: dict[str, BrowsingSignalAggregate] = {}
    for signal in normalize_signal_entries(scenario.get("signals")):
        lemma = str(signal.get("target_lemma") or "").strip()
        if not lemma:
            continue
        current = items.get(lemma) or BrowsingSignalAggregate(target_lemma=lemma)
        side = str(signal.get("side") or "").strip()
        count = safe_float(signal.get("count")) or 0.0
        confidence = safe_float(signal.get("source_mapping_confidence"))
        if side == BROWSING_SIGNAL_SOURCE:
            items[lemma] = BrowsingSignalAggregate(
                target_lemma=lemma,
                source_hit_count=current.source_hit_count + count,
                target_hit_count=current.target_hit_count,
                replacement_exposure_count=current.replacement_exposure_count,
                source_mapping_confidence=max(
                    current.source_mapping_confidence,
                    confidence if confidence is not None else 1.0,
                ),
            )
        elif side == BROWSING_SIGNAL_REPLACEMENT_EXPOSURE:
            items[lemma] = BrowsingSignalAggregate(
                target_lemma=lemma,
                source_hit_count=current.source_hit_count,
                target_hit_count=current.target_hit_count,
                replacement_exposure_count=current.replacement_exposure_count + count,
                source_mapping_confidence=current.source_mapping_confidence,
            )
        else:
            items[lemma] = BrowsingSignalAggregate(
                target_lemma=lemma,
                source_hit_count=current.source_hit_count,
                target_hit_count=current.target_hit_count + count,
                replacement_exposure_count=current.replacement_exposure_count,
                source_mapping_confidence=current.source_mapping_confidence,
            )
    return BrowsingSignalStore(pair=pair, profile_id="implicit_sample_pack", items=items)


def normalize_signal_entries(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    rows = []
    for entry in value:
        if not isinstance(entry, Mapping):
            continue
        lemma = str(entry.get("target_lemma") or entry.get("lemma") or "").strip()
        if not lemma:
            continue
        side = str(entry.get("side") or BROWSING_SIGNAL_TARGET).strip()
        if side not in {
            BROWSING_SIGNAL_SOURCE,
            BROWSING_SIGNAL_TARGET,
            BROWSING_SIGNAL_REPLACEMENT_EXPOSURE,
        }:
            side = BROWSING_SIGNAL_TARGET
        rows.append(
            {
                "target_lemma": lemma,
                "side": side,
                "count": safe_float(entry.get("count")) or 1.0,
                "source_mapping_confidence": safe_float(entry.get("source_mapping_confidence")),
            }
        )
    return rows


def compact_browsing_preview(
    preview: Mapping[str, object],
    *,
    candidate_count: int,
) -> dict[str, Any]:
    simulations = {
        name: compact_simulation_payload(payload)
        for name, payload in dict(preview.get("simulations") or {}).items()
        if isinstance(payload, Mapping)
    }
    return {
        "status": preview.get("status"),
        "scope": preview.get("scope"),
        "applied_to_actual_admission": preview.get("applied_to_actual_admission"),
        "runtime_srs_mutation": preview.get("runtime_srs_mutation"),
        "admission_budget": preview.get("admission_budget"),
        "candidate_pool_effective": preview.get("candidate_pool_effective"),
        "candidate_pool_input": candidate_count,
        "aggregate_item_count": preview.get("aggregate_item_count"),
        "matching_signal_count": preview.get("matching_signal_count"),
        "blocked_by_lifecycle": preview.get("blocked_by_lifecycle"),
        "blocked_lemmas": list(preview.get("blocked_lemmas") or []),
        "neutral_selected_lemmas": list(preview.get("neutral_selected_lemmas") or []),
        "simulations": simulations,
    }


def compact_simulation_payload(payload: Mapping[str, object]) -> dict[str, Any]:
    rows = [dict(row) for row in payload.get("rows", []) if isinstance(row, Mapping)]
    selected_rows = [row for row in rows if row.get("selected")]
    browsing_rows = [row for row in rows if (safe_float(row.get("browsing_signal")) or 0.0) > 0.0]
    return {
        "strength": payload.get("strength"),
        "admission_budget": payload.get("admission_budget"),
        "browsing_budget": payload.get("browsing_budget"),
        "general_budget": payload.get("general_budget"),
        "signal_volume": payload.get("signal_volume"),
        "volume_factor": payload.get("volume_factor"),
        "selected_lemmas": list(payload.get("selected_lemmas") or []),
        "neutral_selected_lemmas": list(payload.get("neutral_selected_lemmas") or []),
        "browsing_lane_count": payload.get("browsing_lane_count"),
        "browsing_relevant_selected_count": payload.get("browsing_relevant_selected_count"),
        "browsing_driven_count": payload.get("browsing_driven_count"),
        "browsing_lane_share": payload.get("browsing_lane_share"),
        "browsing_relevant_share": payload.get("browsing_relevant_share"),
        "browsing_driven_share": payload.get("browsing_driven_share"),
        "suppressed_count": payload.get("suppressed_count"),
        "row_count": payload.get("row_count"),
        "row_preview_count": payload.get("row_preview_count"),
        "selected_rows": selected_rows,
        "browsing_signal_rows": browsing_rows,
        "rows": rows,
    }


def compact_overlay_payload(payload: Mapping[str, object]) -> dict[str, Any]:
    keys = (
        "status",
        "reason",
        "application_status",
        "active_topics",
        "supported_topics",
        "applied_seed_count",
        "matched_seed_count",
        "eligible_row_count",
        "applied_topics",
    )
    return {key: payload.get(key) for key in keys if key in payload}


def compact_profile_growth_payload(payload: Mapping[str, object]) -> dict[str, Any]:
    active_topic_support = payload.get("active_topic_support")
    if isinstance(active_topic_support, Mapping):
        topics = [
            {
                "topic": row.get("topic"),
                "support_count": row.get("support_count"),
                "readiness": row.get("readiness"),
            }
            for row in active_topic_support.get("topics", [])
            if isinstance(row, Mapping)
        ]
    else:
        topics = []
    return {
        "selector_version": payload.get("selector_version"),
        "selection_policy": payload.get("selection_policy"),
        "active_topic_support": topics,
    }


def evaluate_scenario(
    *,
    scenario: Mapping[str, object],
    preview: Mapping[str, object],
    blocked_lemmas: set[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    expectations = dict(scenario.get("expectations") or {})
    simulations = dict(preview.get("simulations") or {})
    off = dict(simulations.get("off") or {})
    balanced = dict(simulations.get("balanced") or {})
    strong = dict(simulations.get("strong") or {})
    shares = [
        safe_float(off.get("browsing_lane_share")) or 0.0,
        safe_float(balanced.get("browsing_lane_share")) or 0.0,
        safe_float(strong.get("browsing_lane_share")) or 0.0,
    ]
    if shares == sorted(shares):
        findings.append(pass_finding("MONOTONIC_STRENGTH", "Browsing lane share is monotonic."))
    else:
        findings.append(
            fail_finding("MONOTONIC_STRENGTH", f"Lane shares are not monotonic: {shares}")
        )
    if (
        preview.get("runtime_srs_mutation") is False
        and preview.get("applied_to_actual_admission") is False
    ):
        findings.append(pass_finding("PREVIEW_ONLY", "Browsing preview did not mutate SRS."))
    else:
        findings.append(
            fail_finding("PREVIEW_ONLY", "Browsing preview reported mutation or application.")
        )
    if expectations.get("empty_store_preserves_neutral"):
        selected_sets = [
            tuple(off.get("selected_lemmas") or ()),
            tuple(balanced.get("selected_lemmas") or ()),
            tuple(strong.get("selected_lemmas") or ()),
        ]
        if selected_sets[0] == selected_sets[1] == selected_sets[2]:
            findings.append(
                pass_finding("EMPTY_STORE_BASELINE", "Empty store preserved neutral selection.")
            )
        else:
            findings.append(fail_finding("EMPTY_STORE_BASELINE", "Empty store changed selection."))
    if expectations.get("matching_signals"):
        if int(preview.get("matching_signal_count") or 0) > 0:
            findings.append(
                pass_finding("SIGNALS_MATCH_CANDIDATES", "Implicit signals matched candidates.")
            )
        else:
            findings.append(
                fail_finding("SIGNALS_MATCH_CANDIDATES", "No implicit signals matched candidates.")
            )
    if expectations.get("strong_has_browsing_lane"):
        if int(strong.get("browsing_lane_count") or 0) > 0:
            findings.append(
                pass_finding("STRONG_BROWSING_LANE", "Strong preset realized browsing lane.")
            )
        else:
            findings.append(
                fail_finding("STRONG_BROWSING_LANE", "Strong preset did not realize browsing lane.")
            )
    if expectations.get("blocked_lemmas_not_selected"):
        selected = set(str(item) for item in strong.get("selected_lemmas") or [])
        selected.update(str(item) for item in balanced.get("selected_lemmas") or [])
        blocked_selected = sorted(blocked_lemmas & selected)
        if not blocked_selected:
            findings.append(
                pass_finding("BLOCKED_LEMMAS_NOT_SELECTED", "Blocked lemmas were not selected.")
            )
        else:
            findings.append(
                fail_finding(
                    "BLOCKED_LEMMAS_NOT_SELECTED",
                    f"Blocked lemmas selected: {', '.join(blocked_selected)}",
                )
            )
    return findings


def pass_finding(code: str, message: str) -> dict[str, Any]:
    return {"level": "PASS", "code": code, "message": message}


def fail_finding(code: str, message: str) -> dict[str, Any]:
    return {"level": "FAIL", "code": code, "message": message}


def scenario_status(findings: Sequence[Mapping[str, object]]) -> str:
    if any(row.get("level") == "FAIL" for row in findings):
        return "fail"
    if any(row.get("level") == "WARN" for row in findings):
        return "warn"
    return "pass"


def build_findings(scenarios: Sequence[Mapping[str, object]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    failing = [str(row.get("name") or "") for row in scenarios if row.get("status") == "fail"]
    if failing:
        findings.append(
            {
                "level": "FAIL",
                "code": "SCENARIO_FAILURES",
                "message": "One or more implicit browsing scenarios failed.",
                "details": {"scenarios": failing},
            }
        )
    else:
        findings.append(
            {
                "level": "PASS",
                "code": "ALL_SCENARIOS_PASS",
                "message": "All implicit browsing scenarios satisfied configured expectations.",
            }
        )
    return findings


def summarize_findings(findings: Sequence[Mapping[str, object]]) -> dict[str, int | str]:
    counts = Counter(str(row.get("level") or "INFO").lower() for row in findings)
    status = "PASS"
    if counts.get("fail", 0):
        status = "FAIL"
    elif counts.get("warn", 0):
        status = "WARN"
    return {
        "status": status,
        "pass_count": int(counts.get("pass", 0)),
        "warn_count": int(counts.get("warn", 0)),
        "fail_count": int(counts.get("fail", 0)),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = dict(report.get("summary") or {})
    lines = [
        "# SRS Browsing Admission Implicit Sample Pack (en-ja)",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Scenarios: `{summary.get('scenario_count', 0)}`",
        f"- Scenario pass/warn/fail: `{summary.get('scenario_pass_count', 0)}` / "
        f"`{summary.get('scenario_warn_count', 0)}` / `{summary.get('scenario_fail_count', 0)}`",
        f"- Pair: `{report.get('pair', '')}`",
        f"- Runtime scope: `{report.get('runtime_scope', '')}`",
        "",
        "## Interpretation",
        "",
        "This pack tests backend implicit personalization after target lemmas are already resolved. It does not validate live browser text extraction.",
        "",
        "## Scenarios",
        "",
    ]
    for scenario in report.get("scenarios", []):
        if not isinstance(scenario, Mapping):
            continue
        preview = dict(scenario.get("browsing_preview") or {})
        simulations = dict(preview.get("simulations") or {})
        lines.extend(
            [
                f"### {scenario.get('name', '')}",
                "",
                f"- Status: `{scenario.get('status', '')}`",
                f"- Proficiency: `{scenario.get('proficiency', '')}`",
                f"- Topic weights: `{json.dumps(scenario.get('topic_weights') or {}, ensure_ascii=False)}`",
                f"- Signals: `{scenario.get('signal_count', 0)}`",
                f"- Matching signals: `{preview.get('matching_signal_count', 0)}` / aggregate items `{preview.get('aggregate_item_count', 0)}`",
                f"- Candidate pool: `{preview.get('candidate_pool_effective', 0)}`",
                "",
                "| Strength | Browsing lane | Driven | Selected |",
                "| --- | ---: | ---: | --- |",
            ]
        )
        for strength in ("off", "balanced", "strong"):
            sim = dict(simulations.get(strength) or {})
            selected = ", ".join(str(item) for item in sim.get("selected_lemmas", [])[:12])
            lines.append(
                f"| `{strength}` | {sim.get('browsing_lane_count', 0)} | "
                f"{sim.get('browsing_driven_count', 0)} | {selected} |"
            )
        lines.extend(["", "Findings:"])
        for finding in scenario.get("findings", []):
            if isinstance(finding, Mapping):
                lines.append(
                    f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
                    f"{finding.get('message', '')}"
                )
        browsing_rows = []
        strong = dict(simulations.get("strong") or {})
        for row in strong.get("browsing_signal_rows", [])[:8]:
            if isinstance(row, Mapping):
                browsing_rows.append(
                    f"`{row.get('lemma', '')}` signal={row.get('browsing_signal', '')} "
                    f"boost={row.get('browsing_boost', '')} selected={row.get('selected', '')}"
                )
        if browsing_rows:
            lines.extend(["", "Strong browsing rows:", *[f"- {row}" for row in browsing_rows]])
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
        description="Build en-ja implicit browsing-admission preview sample pack."
    )
    parser.add_argument("--config-json", type=Path, default=DEFAULT_CONFIG_JSON)
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
