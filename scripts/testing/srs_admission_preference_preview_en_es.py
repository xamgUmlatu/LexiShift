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

from lexishift_core.helper.engine import (  # noqa: E402
    SetAdmissionPreviewJobConfig,
    preview_srs_admission,
)
from lexishift_core.helper.pair_resources import resolve_pair_resources  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.topic_overlay import ANIMALS_PLANTS_OVERLAY_FILENAME  # noqa: E402

REPORT_SCHEMA_VERSION = 1
DEFAULT_PAIR = "en-es"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_preference_preview_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_admission_preference_preview_en_es_latest.md"
)

SCENARIOS: tuple[dict[str, object], ...] = (
    {
        "name": "neutral",
        "description": "No user preference signals.",
        "profile_context": {},
    },
    {
        "name": "animals_interest",
        "description": "Strong explicit animals interest from the UX chip.",
        "profile_context": {"interests": ["animals"]},
    },
    {
        "name": "animals_light_weight",
        "description": "Scalar animals preference below the full chip weight.",
        "profile_context": {"topic_weights": {"animals": 0.35}},
    },
    {
        "name": "plants_nature_interest",
        "description": "Strong explicit plants/nature interest from the UX chip.",
        "profile_context": {"interests": ["plants_nature"]},
    },
    {
        "name": "animals_plants_interest",
        "description": "Combined animals plus plants/nature interests.",
        "profile_context": {"interests": ["animals", "plants_nature"]},
    },
    {
        "name": "weighted_plants_over_animals",
        "description": "Scalar topic weights preferring plants/nature over animals.",
        "profile_context": {"topic_weights": {"plants_nature": 1.0, "animals": 0.25}},
    },
    {
        "name": "finance_control",
        "description": "Control preference for an unsupported topic in the current metadata.",
        "profile_context": {"interests": ["finance"]},
    },
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
    set_top_n: int = 2000,
    initial_active_count: int = 120,
    preview_count: int = 20,
    preview_sampling_mode: str = "ranked",
    preview_seed: int | None = None,
) -> dict[str, Any]:
    resolved_frequency_db = resolve_frequency_db(pair, frequency_db)
    if not resolved_frequency_db.exists():
        raise FileNotFoundError(resolved_frequency_db)
    source_summary = inspect_frequency_db(resolved_frequency_db)

    with tempfile.TemporaryDirectory(prefix="lexishift-srs-pref-preview-") as tmp:
        paths = build_helper_paths(Path(tmp))
        copied_overlay_path = copy_overlay_fixture(
            paths.srs_dir,
            overlay_source_path=overlay_source_path,
        )
        scenario_reports = [
            run_scenario(
                paths=paths,
                pair=pair,
                frequency_db=resolved_frequency_db,
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
        source_summary=source_summary,
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
            "frequency_db_row_count": source_summary.get("row_count"),
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
            "overlay_source_path": str(overlay_source_path) if overlay_source_path else None,
            "copied_overlay_path": str(copied_overlay_path) if copied_overlay_path else None,
        },
        "source_summary": source_summary,
        "summary": summary,
        "findings": findings,
        "comparisons": comparisons,
        "scenarios": scenario_reports,
    }


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
        "admission_weight": entry.get("admission_weight"),
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
) -> list[dict[str, Any]]:
    findings = [
        finding(
            "PASS",
            "FREQUENCY_DB_READABLE",
            f"Frequency DB has {source_summary.get('row_count')} rows.",
        )
    ]
    animals = scenarios["animals_interest"]
    plants = scenarios["plants_nature_interest"]
    weighted = scenarios["weighted_plants_over_animals"]
    finance = scenarios["finance_control"]
    findings.append(
        finding_for_movers(
            scenario=animals,
            code="ANIMALS_INTEREST_MOVES_ADMISSION",
            topic="animals",
        )
    )
    findings.append(
        finding_for_movers(
            scenario=plants,
            code="PLANTS_NATURE_INTEREST_MOVES_ADMISSION",
            topic="plants_nature",
        )
    )
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
    findings.append(
        finding(
            "PASS" if int(finance.get("topic_mover_count") or 0) == 0 else "WARN",
            "UNSUPPORTED_TOPIC_CONTROL_STAYS_NEUTRAL",
            "Finance control remains neutral because current tested metadata has no finance support."
            if int(finance.get("topic_mover_count") or 0) == 0
            else "Finance control moved admission; inspect whether finance metadata is now available.",
        )
    )
    return findings


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
        f"- Runtime scope: {report.get('runtime_scope')}",
        "",
        "## Inputs",
        "",
        f"- frequency_db: `{dict(report.get('inputs') or {}).get('frequency_db')}`",
        f"- set_top_n: {dict(report.get('parameters') or {}).get('set_top_n')}",
        f"- initial_active_count: {dict(report.get('parameters') or {}).get('initial_active_count')}",
        f"- preview_count: {dict(report.get('parameters') or {}).get('preview_count')}",
        "",
        "## Scenario Summary",
        "",
        "| Scenario | Topic movers | Overlay application | Top lemmas |",
        "| --- | ---: | --- | --- |",
    ]
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
    parser.add_argument("--set-top-n", type=int, default=2000)
    parser.add_argument("--initial-active-count", type=int, default=120)
    parser.add_argument("--preview-count", type=int, default=20)
    parser.add_argument(
        "--preview-sampling-mode",
        choices=("ranked", "weighted_without_replacement"),
        default="ranked",
    )
    parser.add_argument("--preview-seed", type=int)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        pair=args.pair,
        frequency_db=args.frequency_db,
        overlay_source_path=args.overlay_source_path,
        set_top_n=args.set_top_n,
        initial_active_count=args.initial_active_count,
        preview_count=args.preview_count,
        preview_sampling_mode=args.preview_sampling_mode,
        preview_seed=args.preview_seed,
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
