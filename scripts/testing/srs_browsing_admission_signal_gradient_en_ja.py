#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
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
from lexishift_core.srs.browsing_admission import (  # noqa: E402
    browsing_raw_value,
    browsing_signal_value,
)
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from srs_admission_preference_sample_pack_en_ja import (  # noqa: E402
    DEFAULT_CORRECTED_RANKING_CSV,
    DEFAULT_OVERLAY_SOURCE_PATH,
    DEFAULT_PAIR,
    copy_overlay_source,
    corrected_ranking_runtime_env,
    load_json_mapping,
    resolve_live_resources,
    safe_float,
)
from srs_browsing_admission_implicit_sample_pack_en_ja import (  # noqa: E402
    DEFAULT_ROW_LIMIT,
    build_browsing_store,
    fail_finding,
    pass_finding,
    run_scenario,
    summarize_findings,
)


REPORT_SCHEMA_VERSION = 1
DEFAULT_CONFIG_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_browsing_admission_signal_gradient_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_browsing_admission_signal_gradient_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_browsing_admission_signal_gradient_en_ja_latest.md"
)


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
    group_filter: Sequence[str],
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
    scenarios = expand_gradient_scenarios(
        config,
        default_counts=defaults.get("counts"),
        group_filter=group_filter,
    )
    resolved_frequency_db, resolved_jmdict_path = resolve_live_resources(
        pair=pair,
        frequency_db=frequency_db,
        jmdict_path=jmdict_path,
    )
    resolved_overlay_source_path = overlay_source_path
    if resolved_overlay_source_path is None and DEFAULT_OVERLAY_SOURCE_PATH.exists():
        resolved_overlay_source_path = DEFAULT_OVERLAY_SOURCE_PATH

    with tempfile.TemporaryDirectory(prefix="lexishift-srs-gradient-enja-") as tmp:
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
            scenario_reports: list[dict[str, Any]] = []
            gradient_rows: list[dict[str, Any]] = []
            for scenario in scenarios:
                scenario_report = run_scenario(
                    paths=paths,
                    pair=pair,
                    base_seeds=base_seeds,
                    scenario=scenario,
                    admission_budget=resolved_admission_budget,
                    max_active_items=resolved_max_active_items,
                    row_limit=resolved_row_limit,
                )
                gradient_row = build_gradient_row(
                    pair=pair,
                    scenario=scenario,
                    scenario_report=scenario_report,
                )
                scenario_report["gradient"] = gradient_row
                scenario_reports.append(compact_scenario_report_for_gradient(scenario_report))
                gradient_rows.append(gradient_row)

    group_summaries = summarize_gradient_groups(gradient_rows)
    findings = build_gradient_findings(scenario_reports, group_summaries)
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
            "group_count": len(group_summaries),
        }
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": now_iso_utc(),
        "pair": pair,
        "runtime_scope": "preview_only_implicit_browsing_admission_signal_gradient",
        "method": {
            "candidate_source": (
                "Real en-ja seed frontier plus profile-growth scoring; scenarios vary only "
                "the already-resolved synthetic browsing aggregate counts."
            ),
            "gradient_scope": (
                "Target-lemma count gradients. This artifact tests sensitivity after lemma "
                "resolution, not live page-text extraction."
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
        "group_summaries": group_summaries,
        "gradient_rows": gradient_rows,
        "scenarios": scenario_reports,
    }


def expand_gradient_scenarios(
    config: Mapping[str, object],
    *,
    default_counts: object,
    group_filter: Sequence[str],
) -> list[dict[str, Any]]:
    wanted = {str(item).strip() for item in group_filter if str(item).strip()}
    scenarios: list[dict[str, Any]] = []
    for group in config.get("gradient_groups", []):
        if not isinstance(group, Mapping):
            continue
        group_name = str(group.get("name") or "").strip()
        if not group_name or (wanted and group_name not in wanted):
            continue
        lemmas = normalize_string_list(group.get("lemmas"))
        if not lemmas:
            continue
        side = str(group.get("side") or "target").strip() or "target"
        counts = normalize_count_values(group.get("counts") or default_counts)
        for count in counts:
            signals = []
            if count > 0.0:
                signals = [
                    {
                        "target_lemma": lemma,
                        "side": side,
                        "count": count,
                    }
                    for lemma in lemmas
                ]
            expectations: dict[str, object] = (
                {"empty_store_preserves_neutral": True}
                if count <= 0.0
                else {"matching_signals": True}
            )
            scenarios.append(
                {
                    "name": f"{group_name}_c{format_count_slug(count)}",
                    "description": f"{group.get('description', '')} Count={count:g}.",
                    "proficiency": safe_float(group.get("proficiency")),
                    "topic_weights": dict(group.get("topic_weights") or {}),
                    "signals": signals,
                    "expectations": expectations,
                    "gradient_group": group_name,
                    "gradient_count": count,
                    "gradient_side": side,
                    "gradient_lemmas": lemmas,
                }
            )
    return scenarios


def normalize_string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def normalize_count_values(value: object) -> list[float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    counts = []
    for raw_count in value:
        count = safe_float(raw_count)
        if count is None or count < 0.0:
            continue
        counts.append(float(count))
    return sorted(set(counts))


def format_count_slug(count: float) -> str:
    text = f"{count:g}".replace("-", "m").replace(".", "p")
    return text or "0"


def build_gradient_row(
    *,
    pair: str,
    scenario: Mapping[str, object],
    scenario_report: Mapping[str, object],
) -> dict[str, Any]:
    store = build_browsing_store(pair=pair, scenario=scenario)
    raw_values = [
        browsing_raw_value(store.items.get(lemma))
        for lemma in normalize_string_list(scenario.get("gradient_lemmas"))
    ]
    signal_values = [
        browsing_signal_value(store.items.get(lemma))
        for lemma in normalize_string_list(scenario.get("gradient_lemmas"))
    ]
    preview = dict(scenario_report.get("browsing_preview") or {})
    simulations = dict(preview.get("simulations") or {})
    return {
        "group": str(scenario.get("gradient_group") or ""),
        "scenario": str(scenario.get("name") or ""),
        "count": safe_float(scenario.get("gradient_count")) or 0.0,
        "side": str(scenario.get("gradient_side") or ""),
        "lemma_count": len(normalize_string_list(scenario.get("gradient_lemmas"))),
        "lemmas": normalize_string_list(scenario.get("gradient_lemmas")),
        "raw_per_lemma": round(raw_values[0], 6) if raw_values else 0.0,
        "signal_per_lemma": round(signal_values[0], 6) if signal_values else 0.0,
        "signal_total": round(sum(signal_values), 6),
        "matching_signal_count": int(preview.get("matching_signal_count") or 0),
        "aggregate_item_count": int(preview.get("aggregate_item_count") or 0),
        "strengths": {
            strength: compact_gradient_strength(dict(simulations.get(strength) or {}))
            for strength in ("off", "balanced", "strong")
        },
        "scenario_status": str(scenario_report.get("status") or ""),
    }


def compact_gradient_strength(simulation: Mapping[str, object]) -> dict[str, Any]:
    return {
        "browsing_budget": int(simulation.get("browsing_budget") or 0),
        "general_budget": int(simulation.get("general_budget") or 0),
        "signal_volume": safe_float(simulation.get("signal_volume")) or 0.0,
        "volume_factor": safe_float(simulation.get("volume_factor")) or 0.0,
        "browsing_lane_count": int(simulation.get("browsing_lane_count") or 0),
        "browsing_driven_count": int(simulation.get("browsing_driven_count") or 0),
        "browsing_lane_share": safe_float(simulation.get("browsing_lane_share")) or 0.0,
        "selected_lemmas": list(simulation.get("selected_lemmas") or []),
    }


def compact_scenario_report_for_gradient(report: Mapping[str, object]) -> dict[str, Any]:
    compact = dict(report)
    preview = dict(compact.get("browsing_preview") or {})
    simulations = {}
    for strength, payload in dict(preview.get("simulations") or {}).items():
        if not isinstance(payload, Mapping):
            continue
        sim = dict(payload)
        sim.pop("rows", None)
        sim.pop("selected_rows", None)
        simulations[strength] = sim
    preview["simulations"] = simulations
    compact["browsing_preview"] = preview
    return compact


def summarize_gradient_groups(rows: Sequence[Mapping[str, object]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("group") or "")].append(row)
    summaries = []
    for group, group_rows in sorted(grouped.items()):
        ordered = sorted(group_rows, key=lambda row: safe_float(row.get("count")) or 0.0)
        summaries.append(
            {
                "group": group,
                "side": str(ordered[0].get("side") or "") if ordered else "",
                "lemma_count": int(ordered[0].get("lemma_count") or 0) if ordered else 0,
                "first_balanced_lane_count": first_count_with_lane(ordered, "balanced"),
                "first_strong_lane_count": first_count_with_lane(ordered, "strong"),
                "max_balanced_lane_count": max_lane_count(ordered, "balanced"),
                "max_strong_lane_count": max_lane_count(ordered, "strong"),
                "balanced_lane_counts": [
                    lane_count_at_strength(row, "balanced") for row in ordered
                ],
                "strong_lane_counts": [lane_count_at_strength(row, "strong") for row in ordered],
                "counts": [safe_float(row.get("count")) or 0.0 for row in ordered],
                "signal_totals": [safe_float(row.get("signal_total")) or 0.0 for row in ordered],
            }
        )
    return summaries


def first_count_with_lane(rows: Sequence[Mapping[str, object]], strength: str) -> float | None:
    for row in rows:
        if lane_count_at_strength(row, strength) > 0:
            return safe_float(row.get("count")) or 0.0
    return None


def max_lane_count(rows: Sequence[Mapping[str, object]], strength: str) -> int:
    return max((lane_count_at_strength(row, strength) for row in rows), default=0)


def lane_count_at_strength(row: Mapping[str, object], strength: str) -> int:
    strengths = row.get("strengths")
    if not isinstance(strengths, Mapping):
        return 0
    payload = strengths.get(strength)
    if not isinstance(payload, Mapping):
        return 0
    return int(payload.get("browsing_lane_count") or 0)


def build_gradient_findings(
    scenarios: Sequence[Mapping[str, object]],
    group_summaries: Sequence[Mapping[str, object]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    failing = [str(row.get("name") or "") for row in scenarios if row.get("status") == "fail"]
    if failing:
        findings.append(
            fail_finding(
                "SCENARIO_FAILURES",
                f"Scenario failures: {', '.join(failing)}",
            )
        )
    else:
        findings.append(
            pass_finding(
                "ALL_SCENARIOS_PASS",
                "All count-gradient scenarios satisfied baseline preview expectations.",
            )
        )
    for summary in group_summaries:
        group = str(summary.get("group") or "")
        if is_nondecreasing(summary.get("signal_totals")):
            findings.append(
                pass_finding(
                    f"{group}:SIGNAL_TOTAL_MONOTONIC",
                    "Normalized signal volume is nondecreasing as count rises.",
                )
            )
        else:
            findings.append(
                fail_finding(
                    f"{group}:SIGNAL_TOTAL_MONOTONIC",
                    "Normalized signal volume decreased as count rose.",
                )
            )
        for strength in ("balanced", "strong"):
            key = f"{strength}_lane_counts"
            if is_nondecreasing(summary.get(key)):
                findings.append(
                    pass_finding(
                        f"{group}:{strength.upper()}_LANE_MONOTONIC",
                        f"{strength} browsing lane count is nondecreasing.",
                    )
                )
            else:
                findings.append(
                    fail_finding(
                        f"{group}:{strength.upper()}_LANE_MONOTONIC",
                        f"{strength} browsing lane count decreased.",
                    )
                )
    return findings


def is_nondecreasing(value: object) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return True
    parsed = [safe_float(item) for item in value]
    numbers = [item for item in parsed if item is not None]
    return all(left <= right for left, right in zip(numbers, numbers[1:]))


def render_markdown(report: Mapping[str, object]) -> str:
    summary = dict(report.get("summary") or {})
    lines = [
        "# SRS Browsing Admission Signal Gradient (en-ja)",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Groups: `{summary.get('group_count', 0)}`",
        f"- Scenarios: `{summary.get('scenario_count', 0)}`",
        f"- Scenario pass/warn/fail: `{summary.get('scenario_pass_count', 0)}` / "
        f"`{summary.get('scenario_warn_count', 0)}` / `{summary.get('scenario_fail_count', 0)}`",
        f"- Pair: `{report.get('pair', '')}`",
        f"- Runtime scope: `{report.get('runtime_scope', '')}`",
        "",
        "## Interpretation",
        "",
        "This artifact varies already-resolved browsing aggregate counts to show when weak, medium, and saturated history begins changing preview admission. It does not validate live page-text extraction or mutate SRS.",
        "",
        "## Group Thresholds",
        "",
        "| Group | Side | Lemmas | First balanced lane | First strong lane | Max balanced lane | Max strong lane |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary_row in report.get("group_summaries", []):
        if not isinstance(summary_row, Mapping):
            continue
        lines.append(
            "| "
            f"`{summary_row.get('group', '')}` | "
            f"`{summary_row.get('side', '')}` | "
            f"{summary_row.get('lemma_count', 0)} | "
            f"{format_optional_count(summary_row.get('first_balanced_lane_count'))} | "
            f"{format_optional_count(summary_row.get('first_strong_lane_count'))} | "
            f"{summary_row.get('max_balanced_lane_count', 0)} | "
            f"{summary_row.get('max_strong_lane_count', 0)} |"
        )
    lines.extend(["", "## Curves", ""])
    grouped_rows: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in report.get("gradient_rows", []):
        if isinstance(row, Mapping):
            grouped_rows[str(row.get("group") or "")].append(row)
    for group, rows in sorted(grouped_rows.items()):
        lines.extend(
            [
                f"### {group}",
                "",
                "| Count | Raw/lemma | Signal/lemma | Signal total | Balanced lane/driven | Strong lane/driven | Strong selected |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for row in sorted(rows, key=lambda item: safe_float(item.get("count")) or 0.0):
            balanced = strength_payload(row, "balanced")
            strong = strength_payload(row, "strong")
            selected = ", ".join(str(item) for item in strong.get("selected_lemmas", [])[:8])
            lines.append(
                "| "
                f"{safe_float(row.get('count')) or 0.0:g} | "
                f"{safe_float(row.get('raw_per_lemma')) or 0.0:.3f} | "
                f"{safe_float(row.get('signal_per_lemma')) or 0.0:.3f} | "
                f"{safe_float(row.get('signal_total')) or 0.0:.3f} | "
                f"{balanced.get('browsing_lane_count', 0)}/"
                f"{balanced.get('browsing_driven_count', 0)} | "
                f"{strong.get('browsing_lane_count', 0)}/"
                f"{strong.get('browsing_driven_count', 0)} | "
                f"{selected} |"
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


def format_optional_count(value: object) -> str:
    parsed = safe_float(value)
    if parsed is None:
        return "none"
    return f"{parsed:g}"


def strength_payload(row: Mapping[str, object], strength: str) -> Mapping[str, object]:
    strengths = row.get("strengths")
    if not isinstance(strengths, Mapping):
        return {}
    payload = strengths.get(strength)
    return payload if isinstance(payload, Mapping) else {}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build en-ja implicit browsing-admission signal gradient."
    )
    parser.add_argument("--config-json", type=Path, default=DEFAULT_CONFIG_JSON)
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--jmdict", type=Path)
    parser.add_argument("--overlay-json", type=Path)
    parser.add_argument("--corrected-ranking-csv", type=Path, default=DEFAULT_CORRECTED_RANKING_CSV)
    parser.add_argument("--group", action="append", default=[])
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
        group_filter=args.group,
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
