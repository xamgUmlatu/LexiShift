#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
from typing import Iterator, Mapping, Sequence
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.helper.engine import (  # noqa: E402
    SrsRefreshJobConfig,
    SetInitializationJobConfig,
    apply_feedback,
    initialize_srs_set,
    refresh_srs_set,
)
from lexishift_core.helper.paths import HelperPaths, build_helper_paths  # noqa: E402
from lexishift_core.srs import SrsSettings, save_srs_settings  # noqa: E402

from srs_journey_harness_support import (  # noqa: E402
    COHORT_BY_LEMMA,
    DEFAULT_PAIR,
    DEFAULT_PROFILE_ID,
    PHASE_PLANS,
    build_seed_candidates,
    create_en_ja_resources,
    load_signal_log,
    patched_now,
    phase_deltas,
    phase_snapshot,
    scenario_candidate_universe,
    scenario_clock,
    stub_run_rulegen_for_pair,
)

DEFAULT_SCENARIO = "en-ja_core_journey_v1"
DEFAULT_CONTRACT_MODE = "observe_current_behavior"


@contextmanager
def _temp_paths() -> Iterator[HelperPaths]:
    with tempfile.TemporaryDirectory() as tmp:
        yield build_helper_paths(Path(tmp))


def _finding(
    *,
    level: str,
    code: str,
    message: str,
    details: str | None = None,
    phase: str | None = None,
) -> dict[str, object]:
    return {
        "level": level,
        "code": code,
        "message": message,
        "details": details,
        "phase": phase,
    }


def _summarize_findings(findings: Sequence[Mapping[str, object]]) -> dict[str, object]:
    pass_count = 0
    warn_count = 0
    fail_count = 0
    for item in findings:
        level = str(item.get("level") or "").upper()
        if level == "PASS":
            pass_count += 1
        elif level == "WARN":
            warn_count += 1
        elif level == "FAIL":
            fail_count += 1
    status = "FAIL" if fail_count else "WARN" if warn_count else "PASS"
    return {
        "status": status,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "should_fail": fail_count > 0,
    }


def _apply_feedback_events(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    phase_time: datetime,
    events: Sequence[tuple[str, str]],
) -> list[dict[str, object]]:
    applied: list[dict[str, object]] = []
    for index, (lemma, rating) in enumerate(events):
        event_time = phase_time + timedelta(minutes=index)
        with patched_now(event_time):
            apply_feedback(paths, pair=pair, lemma=lemma, rating=rating, profile_id=profile_id)
        applied.append(
            {
                "index": index + 1,
                "lemma": lemma,
                "rating": rating,
                "ts": event_time.isoformat(),
                "cohort": COHORT_BY_LEMMA.get(lemma, "frontier"),
            }
        )
    return applied


from datetime import timedelta  # noqa: E402  # keep near clock helpers


def _run_phase(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    phase_plan,
    previous_snapshot: Mapping[str, object] | None,
    refresh_config: SrsRefreshJobConfig,
) -> dict[str, object]:
    feedback_events = _apply_feedback_events(
        paths,
        pair=pair,
        profile_id=profile_id,
        phase_time=phase_plan.observe_at,
        events=phase_plan.feedback_events,
    )
    refresh_payload: dict[str, object] | None = None
    if phase_plan.refresh_at is not None:
        with (
            patched_now(phase_plan.refresh_at),
            patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                side_effect=build_seed_candidates,
            ),
            patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                side_effect=stub_run_rulegen_for_pair,
            ),
        ):
            refresh_payload = refresh_srs_set(paths, config=refresh_config)
    with patched_now(phase_plan.observe_at):
        snapshot = phase_snapshot(
            paths, pair=pair, profile_id=profile_id, now=phase_plan.observe_at
        )
    snapshot["deltas"] = phase_deltas(previous_snapshot, snapshot)
    findings: list[dict[str, object]] = []
    if phase_plan.label == "high_retention_growth":
        if (
            refresh_payload
            and bool(refresh_payload.get("applied"))
            and int(snapshot["counts"]["admitted"]) > 3
        ):
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_JOURNEY_HIGH_RETENTION_ADMITS",
                    message="High-retention phase admitted new frontier items.",
                    details=f"admitted={int(snapshot['counts']['admitted'])}",
                    phase=phase_plan.label,
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_JOURNEY_HIGH_RETENTION_ADMITS",
                    message="High-retention phase did not admit new frontier items.",
                    details=json.dumps(refresh_payload or {}, ensure_ascii=False),
                    phase=phase_plan.label,
                )
            )
    elif phase_plan.label == "low_retention_pause":
        reason_code = str(
            (refresh_payload or {}).get("admission_refresh", {}).get("reason_code") or ""
        )
        if (
            refresh_payload
            and not bool(refresh_payload.get("applied"))
            and reason_code == "retention_low"
        ):
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_JOURNEY_LOW_RETENTION_PAUSES",
                    message="Low-retention phase paused new admissions.",
                    details=f"reason_code={reason_code}",
                    phase=phase_plan.label,
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_JOURNEY_LOW_RETENTION_PAUSES",
                    message="Low-retention phase did not pause admissions as expected.",
                    details=json.dumps(refresh_payload or {}, ensure_ascii=False),
                    phase=phase_plan.label,
                )
            )
    elif phase_plan.label == "recovery_resume":
        if (
            refresh_payload
            and bool(refresh_payload.get("applied"))
            and int(snapshot["counts"]["admitted"]) > 5
        ):
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_JOURNEY_RECOVERY_RESUMES",
                    message="Recovery phase resumed new admissions.",
                    details=f"admitted={int(snapshot['counts']['admitted'])}",
                    phase=phase_plan.label,
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_JOURNEY_RECOVERY_RESUMES",
                    message="Recovery phase did not resume admissions as expected.",
                    details=json.dumps(refresh_payload or {}, ensure_ascii=False),
                    phase=phase_plan.label,
                )
            )
    return {
        "label": phase_plan.label,
        "step_index": [item.label for item in PHASE_PLANS].index(phase_plan.label) + 1,
        "now": phase_plan.observe_at.isoformat(),
        "events_applied": {
            "feedback": feedback_events,
            "exposure": [],
        },
        "refresh": {
            "requested": phase_plan.refresh_at is not None,
            "payload": refresh_payload,
            "ts": phase_plan.refresh_at.isoformat() if phase_plan.refresh_at else None,
        },
        **snapshot,
        "findings": findings,
    }


def build_report(
    *,
    scenario: str = DEFAULT_SCENARIO,
    contract_mode: str = DEFAULT_CONTRACT_MODE,
) -> dict[str, object]:
    if scenario != DEFAULT_SCENARIO:
        raise SystemExit(f"Unsupported SRS journey scenario: {scenario}")
    if contract_mode not in {"observe_current_behavior", "require_due_aware_publication"}:
        raise SystemExit(f"Unsupported contract mode: {contract_mode}")

    profile_id = DEFAULT_PROFILE_ID
    pair = DEFAULT_PAIR

    with _temp_paths() as paths:
        resources = create_en_ja_resources(paths)
        save_srs_settings(
            SrsSettings(max_active_items=8, max_new_items_per_day=2),
            paths.srs_settings_path,
        )
        with (
            patched_now(PHASE_PLANS[0].observe_at),
            patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                side_effect=stub_run_rulegen_for_pair,
            ),
        ):
            initialize_payload = initialize_srs_set(
                paths,
                config=SetInitializationJobConfig(
                    pair=pair,
                    profile_id=profile_id,
                    jmdict_path=resources["jmdict_path"],
                    set_source_db=resources["frequency_db"],
                    set_top_n=7,
                    bootstrap_top_n=7,
                    initial_active_count=3,
                    replace_pair=True,
                    trigger="srs_journey_harness",
                ),
            )

        findings: list[dict[str, object]] = []
        if bool(initialize_payload.get("applied")):
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_JOURNEY_BOOTSTRAP_APPLIED",
                    message="Bootstrap initialized the first active SRS inventory.",
                    details=f"admitted={int(initialize_payload.get('total_items_for_pair') or 0)}",
                    phase="bootstrap_publish",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_JOURNEY_BOOTSTRAP_APPLIED",
                    message="Bootstrap did not initialize the first active SRS inventory.",
                    details=json.dumps(initialize_payload, ensure_ascii=False),
                    phase="bootstrap_publish",
                )
            )

        refresh_config = SrsRefreshJobConfig(
            pair=pair,
            profile_id=profile_id,
            jmdict_path=resources["jmdict_path"],
            set_source_db=resources["frequency_db"],
            set_top_n=7,
            feedback_window_size=8,
            persist_store=True,
            trigger="srs_journey_harness",
        )

        phases: list[dict[str, object]] = []
        previous_snapshot: Mapping[str, object] | None = None
        for phase_plan in PHASE_PLANS:
            phase_report = _run_phase(
                paths,
                pair=pair,
                profile_id=profile_id,
                phase_plan=phase_plan,
                previous_snapshot=previous_snapshot,
                refresh_config=refresh_config,
            )
            previous_snapshot = phase_report
            phases.append(phase_report)
            findings.extend(phase_report["findings"])

        first_phase = phases[0]
        diagnostics = (
            first_phase["runtime"]["diagnostics"]
            if isinstance(first_phase.get("runtime"), Mapping)
            else {}
        )
        if (
            isinstance(diagnostics, Mapping)
            and diagnostics.get("store_exists")
            and diagnostics.get("ruleset_exists")
            and diagnostics.get("snapshot_exists")
        ):
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_JOURNEY_RUNTIME_ARTIFACTS_PRESENT",
                    message="Store, ruleset, and snapshot artifacts are present for the journey harness.",
                    phase="bootstrap_publish",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_JOURNEY_RUNTIME_ARTIFACTS_PRESENT",
                    message="Expected runtime artifacts are missing in the journey harness.",
                    details=json.dumps(diagnostics, ensure_ascii=False),
                    phase="bootstrap_publish",
                )
            )

        fade_phase = phases[-1]
        stable_due = [
            item
            for item in fade_phase["items"]
            if item.get("cohort") == "stable" and item.get("in_due")
        ]
        difficult_due = [
            item
            for item in fade_phase["items"]
            if item.get("cohort") == "difficult" and item.get("in_due")
        ]
        if not stable_due:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_JOURNEY_STABLE_COHORT_FADES",
                    message="Stable cohort faded out of the near-term due set.",
                    details="stable_due=0",
                    phase="fade_check",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_JOURNEY_STABLE_COHORT_FADES",
                    message="Stable cohort remained in the due set longer than expected.",
                    details=",".join(item["lemma"] for item in stable_due),
                    phase="fade_check",
                )
            )
        if difficult_due:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_JOURNEY_DIFFICULT_COHORT_STICKS",
                    message="Difficult cohort remained in the due set as expected.",
                    details=",".join(item["lemma"] for item in difficult_due),
                    phase="fade_check",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_JOURNEY_DIFFICULT_COHORT_STICKS",
                    message="Difficult cohort did not remain visible in the due set.",
                    phase="fade_check",
                )
            )

        publication_scope_phase = next(
            (
                phase
                for phase in phases
                if phase["counts"]["published"] > phase["counts"]["due"]
                and phase["relationships"]["published_not_due"]
            ),
            None,
        )
        if publication_scope_phase is None:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED",
                    message="Published set stayed within the observed due subset for this journey run.",
                )
            )
        else:
            level = "FAIL" if contract_mode == "require_due_aware_publication" else "WARN"
            findings.append(
                _finding(
                    level=level,
                    code="SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED",
                    message="Published set is broader than the due subset in the current journey run.",
                    details=(
                        f"phase={publication_scope_phase['label']} admitted={publication_scope_phase['counts']['admitted']} "
                        f"due={publication_scope_phase['counts']['due']} published={publication_scope_phase['counts']['published']}"
                    ),
                    phase=str(publication_scope_phase["label"]),
                )
            )

        summary = _summarize_findings(findings)
        signal_log = load_signal_log(paths, profile_id=profile_id)
        return {
            "version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "plan_doc": str(PROJECT_ROOT / "docs" / "srs" / "srs_journey_harness_workstream.md"),
            "scenario": {
                "name": scenario,
                "pair": pair,
                "lane": "deterministic_core_journey",
                "contract_mode": contract_mode,
                "profile_id": profile_id,
                "settings": {
                    "max_active_items": 8,
                    "max_new_items_per_day": 2,
                },
                "bootstrap": {
                    "set_top_n": 7,
                    "initial_active_count": 3,
                    "replace_pair": True,
                },
                "candidate_universe": scenario_candidate_universe(),
                "cohorts": {
                    "stable": ["alpha", "beta"],
                    "difficult": ["gamma"],
                    "frontier": ["delta", "epsilon", "zeta", "eta"],
                },
                "clock": scenario_clock(),
            },
            "initialize": initialize_payload,
            "phases": phases,
            "signal_log": signal_log,
            "summary": summary,
            "findings": findings,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the deterministic SRS journey harness and emit an item-level JSON report."
        )
    )
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO, help="Scenario name.")
    parser.add_argument(
        "--contract-mode",
        default=DEFAULT_CONTRACT_MODE,
        choices=("observe_current_behavior", "require_due_aware_publication"),
        help="Publication contract evaluation mode.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "srs_journey"
        / "srs_journey_en_ja_latest.json",
        help="Path to write the journey JSON report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(scenario=str(args.scenario), contract_mode=str(args.contract_mode))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json_out: {args.json_out}")
    summary = report.get("summary") or {}
    print(
        "summary: "
        f"status={str(summary.get('status') or 'UNKNOWN')} "
        f"pass={int(summary.get('pass_count') or 0)} "
        f"warn={int(summary.get('warn_count') or 0)} "
        f"fail={int(summary.get('fail_count') or 0)}"
    )


if __name__ == "__main__":
    main()
