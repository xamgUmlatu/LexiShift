#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
from typing import Iterator, Mapping
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.helper.engine import (  # noqa: E402
    SrsRefreshJobConfig,
    SetInitializationJobConfig,
    build_seed_candidates as build_engine_seed_candidates,
    initialize_srs_set,
)
from lexishift_core.helper.paths import HelperPaths, build_helper_paths  # noqa: E402
from lexishift_core.srs import SrsSettings, save_srs_settings  # noqa: E402
from lexishift_core.srs.signal_queue import summarize_signal_events  # noqa: E402

from srs_journey_harness_support import (  # noqa: E402
    CORE_SCENARIO_NAME,
    DEFAULT_PROFILE_ID,
    build_seed_candidates,
    cohort_by_lemma_for_pair,
    create_pair_resources,
    get_scenario,
    patched_now,
    scenario_candidate_universe,
    scenario_clock,
    scenario_cohorts,
    stub_run_rulegen_for_pair,
)
from srs_journey_phase_support import run_phase as _run_phase  # noqa: E402
from srs_journey_installed_support import (  # noqa: E402
    build_initial_role_assignments,
    cohort_map_from_role_assignments,
    installed_candidate_universe_from_bootstrap_audit,
    installed_pair_resources_available,
    scenario_cohorts_from_role_assignments,
)
from srs_journey_runtime_support import (  # noqa: E402
    finding as _finding,
    summarize_findings as _summarize_findings,
)
from srs_journey_state_support import load_signal_log  # noqa: E402
from srs_journey_review_support import (  # noqa: E402
    build_bootstrap_candidate_audit,
)

DEFAULT_SCENARIO = CORE_SCENARIO_NAME
DEFAULT_CONTRACT_MODE = "observe_current_behavior"


@contextmanager
def _temp_paths() -> Iterator[HelperPaths]:
    with tempfile.TemporaryDirectory() as tmp:
        yield build_helper_paths(Path(tmp))


def build_report(
    *,
    scenario: str = DEFAULT_SCENARIO,
    contract_mode: str = DEFAULT_CONTRACT_MODE,
) -> dict[str, object]:
    if contract_mode not in {"observe_current_behavior", "require_due_aware_publication"}:
        raise SystemExit(f"Unsupported contract mode: {contract_mode}")
    try:
        scenario_def = get_scenario(scenario)
    except KeyError as exc:
        raise SystemExit(str(exc)) from exc

    profile_id = DEFAULT_PROFILE_ID
    pair = scenario_def.pair
    phase_plans = scenario_def.phase_plans
    cohort_by_lemma = cohort_by_lemma_for_pair(pair)
    if scenario_def.resource_mode == "installed" and not installed_pair_resources_available(pair):
        raise SystemExit(f"Installed SRS journey resources are unavailable for pair: {pair}")

    with _temp_paths() as paths:
        resources = create_pair_resources(
            paths,
            pair=pair,
            resource_mode=scenario_def.resource_mode,
        )
        seed_builder = (
            build_seed_candidates
            if scenario_def.use_stub_seed_candidates
            else build_engine_seed_candidates
        )
        save_srs_settings(
            SrsSettings(
                max_active_items=scenario_def.max_active_items,
                max_new_items_per_day=scenario_def.max_new_items_per_day,
            ),
            paths.srs_settings_path,
        )
        with ExitStack() as stack:
            stack.enter_context(patched_now(phase_plans[0].observe_at))
            if scenario_def.use_stub_seed_candidates:
                stack.enter_context(
                    patch(
                        "lexishift_core.helper.engine.build_seed_candidates",
                        side_effect=build_seed_candidates,
                    )
                )
            if scenario_def.use_stub_rulegen:
                stack.enter_context(
                    patch(
                        "lexishift_core.helper.engine.run_rulegen_for_pair",
                        side_effect=stub_run_rulegen_for_pair,
                    )
                )
            initialize_payload = initialize_srs_set(
                paths,
                config=SetInitializationJobConfig(
                    pair=pair,
                    profile_id=profile_id,
                    jmdict_path=resources["jmdict_path"],
                    translation_dict_path=resources.get("translation_dict_path"),
                    set_source_db=resources["frequency_db"],
                    set_top_n=scenario_def.set_top_n,
                    bootstrap_top_n=scenario_def.bootstrap_top_n,
                    initial_active_count=scenario_def.initial_active_count,
                    replace_pair=True,
                    strategy=scenario_def.strategy,
                    profile_context=scenario_def.profile_context,
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
            initialize_payload["bootstrap_audit"] = build_bootstrap_candidate_audit(
                paths,
                pair=pair,
                jmdict_path=resources["jmdict_path"],
                set_source_db=resources["frequency_db"],
                set_top_n=int(initialize_payload.get("bootstrap_top_n") or 0),
                initial_active_count=int(initialize_payload.get("initial_active_count") or 0),
                cohort_by_lemma=cohort_by_lemma,
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

        role_assignments = build_initial_role_assignments(initialize_payload)
        cohort_by_lemma = cohort_map_from_role_assignments(
            cohort_by_lemma,
            role_assignments,
        )

        refresh_config = SrsRefreshJobConfig(
            pair=pair,
            profile_id=profile_id,
            jmdict_path=resources["jmdict_path"],
            translation_dict_path=resources.get("translation_dict_path"),
            set_source_db=resources["frequency_db"],
            set_top_n=scenario_def.set_top_n,
            feedback_window_size=8,
            persist_store=True,
            profile_context=scenario_def.profile_context,
            trigger="srs_journey_harness",
        )

        phases: list[dict[str, object]] = []
        previous_snapshot: Mapping[str, object] | None = None
        for phase_plan in phase_plans:
            phase_report, role_assignments = _run_phase(
                paths,
                pair=pair,
                profile_id=profile_id,
                phase_plan=phase_plan,
                phase_plans=phase_plans,
                previous_snapshot=previous_snapshot,
                refresh_config=refresh_config,
                jmdict_path=resources["jmdict_path"],
                set_source_db=resources["frequency_db"],
                seed_builder=seed_builder,
                use_stub_seed_candidates=scenario_def.use_stub_seed_candidates,
                use_stub_rulegen=scenario_def.use_stub_rulegen,
                cohort_by_lemma=cohort_by_lemma,
                role_assignments=role_assignments,
            )
            previous_snapshot = phase_report
            phases.append(phase_report)
            findings.extend(phase_report["findings"])
            cohort_by_lemma = cohort_map_from_role_assignments(
                cohort_by_lemma,
                role_assignments,
            )

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

        if scenario_def.expect_fade_checks:
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

        if not scenario_def.use_stub_rulegen:
            ruleset_sources_preview = first_phase["runtime"].get("ruleset_sources_preview", [])
            if ruleset_sources_preview and all(
                not str(source).startswith("journey_src_") for source in ruleset_sources_preview
            ):
                findings.append(
                    _finding(
                        level="PASS",
                        code="SRS_JOURNEY_REAL_PUBLICATION_ACTIVE",
                        message="Real rulegen/publication ran for the journey lane instead of the deterministic stub.",
                        details="sources="
                        + ", ".join(str(item) for item in ruleset_sources_preview),
                        phase="bootstrap_publish",
                    )
                )
            else:
                findings.append(
                    _finding(
                        level="FAIL",
                        code="SRS_JOURNEY_REAL_PUBLICATION_ACTIVE",
                        message="Real publication lane did not produce non-stub ruleset sources.",
                        details=json.dumps(ruleset_sources_preview, ensure_ascii=False),
                        phase="bootstrap_publish",
                    )
                )

            partial_publication_phase = next(
                (phase for phase in phases if phase["relationships"].get("due_not_published")),
                None,
            )
            if partial_publication_phase is None:
                findings.append(
                    _finding(
                        level="PASS",
                        code="SRS_JOURNEY_REAL_PUBLICATION_COMPLETE_FOR_DUE",
                        message="Real publication covered the due subset in the observed journey phases.",
                        phase="bootstrap_publish",
                    )
                )
            else:
                findings.append(
                    _finding(
                        level="WARN",
                        code="SRS_JOURNEY_REAL_PUBLICATION_COMPLETE_FOR_DUE",
                        message="Real publication left some due items unpublished in the observed journey phases.",
                        details=(
                            f"phase={partial_publication_phase['label']} "
                            f"due_not_published={','.join(partial_publication_phase['relationships']['due_not_published'])}"
                        ),
                        phase=str(partial_publication_phase["label"]),
                    )
                )

            word_package_coverage_phase = next(
                (
                    phase
                    for phase in phases
                    if phase["counts"]["admitted"]
                    != phase["runtime"]["diagnostics"].get("store_items_with_word_package_for_pair")
                ),
                None,
            )
            if word_package_coverage_phase is None:
                findings.append(
                    _finding(
                        level="PASS",
                        code="SRS_JOURNEY_REAL_WORD_PACKAGES_COMPLETE",
                        message="Real publication lane kept word-package coverage aligned with admitted items.",
                        phase="bootstrap_publish",
                    )
                )
            else:
                findings.append(
                    _finding(
                        level="WARN",
                        code="SRS_JOURNEY_REAL_WORD_PACKAGES_COMPLETE",
                        message="Some admitted items in the real publication lane are missing word-package coverage.",
                        details=(
                            f"phase={word_package_coverage_phase['label']} admitted={word_package_coverage_phase['counts']['admitted']} "
                            "with_word_package="
                            f"{word_package_coverage_phase['runtime']['diagnostics'].get('store_items_with_word_package_for_pair')}"
                        ),
                        phase=str(word_package_coverage_phase["label"]),
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
        signal_summary = summarize_signal_events(
            paths.srs_signal_queue_path_for(profile_id), pair=pair
        )
        if scenario_def.resource_mode == "installed":
            candidate_universe = installed_candidate_universe_from_bootstrap_audit(
                initialize_payload
            )
            cohorts = scenario_cohorts_from_role_assignments(role_assignments)
        else:
            candidate_universe = scenario_candidate_universe(pair=pair)
            cohorts = scenario_cohorts(pair)
        return {
            "version": 2,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "plan_doc": str(PROJECT_ROOT / "docs" / "srs" / "srs_journey_harness_workstream.md"),
            "scenario": {
                "id": scenario,
                "name": scenario,
                "pair": pair,
                "lane": scenario_def.lane,
                "resource_mode": scenario_def.resource_mode,
                "contract_mode": contract_mode,
                "profile_id": profile_id,
                "settings": {
                    "max_active_items": scenario_def.max_active_items,
                    "max_new_items_per_day": scenario_def.max_new_items_per_day,
                },
                "strategy": scenario_def.strategy,
                "profile_context": dict(scenario_def.profile_context or {}),
                "bootstrap": {
                    "set_top_n": scenario_def.set_top_n,
                    "bootstrap_top_n": scenario_def.bootstrap_top_n,
                    "initial_active_count": scenario_def.initial_active_count,
                    "replace_pair": True,
                },
                "candidate_universe": candidate_universe,
                "cohorts": cohorts,
                "role_assignments": role_assignments,
                "clock": scenario_clock(phase_plans),
            },
            "initialize": initialize_payload,
            "phases": phases,
            "signal_log": signal_log,
            "signal_summary": signal_summary,
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
