#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
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
    apply_exposure,
    apply_feedback,
    build_seed_candidates as build_engine_seed_candidates,
    initialize_srs_set,
    refresh_srs_set,
)
from lexishift_core.helper.paths import HelperPaths, build_helper_paths  # noqa: E402
from lexishift_core.srs import SrsSettings, load_srs_store, save_srs_settings  # noqa: E402
from lexishift_core.srs.signal_queue import load_signal_events, summarize_signal_events  # noqa: E402

from srs_journey_harness_support import (  # noqa: E402
    CORE_SCENARIO_NAME,
    DEFAULT_PROFILE_ID,
    build_seed_candidates,
    cohort_by_lemma_for_pair,
    create_pair_resources,
    get_scenario,
    load_signal_log,
    patched_now,
    phase_deltas,
    phase_snapshot,
    scenario_candidate_universe,
    scenario_clock,
    scenario_cohorts,
    stub_run_rulegen_for_pair,
)
from srs_journey_review_support import (  # noqa: E402
    apply_selected_lemmas_to_refresh_audit,
    build_bootstrap_candidate_audit,
    build_refresh_candidate_audit,
)

DEFAULT_SCENARIO = CORE_SCENARIO_NAME
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
    cohort_by_lemma: Mapping[str, str],
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
                "cohort": cohort_by_lemma.get(lemma, "frontier"),
            }
        )
    return applied


def _apply_exposure_events(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    phase_time: datetime,
    events: Sequence[str],
    cohort_by_lemma: Mapping[str, str],
) -> list[dict[str, object]]:
    applied: list[dict[str, object]] = []
    for index, lemma in enumerate(events):
        event_time = phase_time + timedelta(minutes=index)
        with patched_now(event_time):
            apply_exposure(paths, pair=pair, lemma=lemma, profile_id=profile_id)
        applied.append(
            {
                "index": index + 1,
                "lemma": lemma,
                "ts": event_time.isoformat(),
                "cohort": cohort_by_lemma.get(lemma, "frontier"),
            }
        )
    return applied


from datetime import timedelta  # noqa: E402  # keep near clock helpers


def _snapshot_item(
    snapshot: Mapping[str, object] | None, lemma: str
) -> Mapping[str, object] | None:
    if not isinstance(snapshot, Mapping):
        return None
    items = snapshot.get("items")
    if not isinstance(items, list):
        return None
    for item in items:
        if isinstance(item, Mapping) and str(item.get("lemma") or "") == lemma:
            return item
    return None


def _run_phase(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    phase_plan,
    phase_plans: Sequence[object],
    previous_snapshot: Mapping[str, object] | None,
    refresh_config: SrsRefreshJobConfig,
    jmdict_path: Path,
    set_source_db: Path,
    seed_builder,
    use_stub_seed_candidates: bool,
    use_stub_rulegen: bool,
    cohort_by_lemma: Mapping[str, str],
) -> dict[str, object]:
    feedback_events = _apply_feedback_events(
        paths,
        pair=pair,
        profile_id=profile_id,
        phase_time=phase_plan.observe_at,
        events=phase_plan.feedback_events,
        cohort_by_lemma=cohort_by_lemma,
    )
    exposure_events = _apply_exposure_events(
        paths,
        pair=pair,
        profile_id=profile_id,
        phase_time=phase_plan.observe_at,
        events=phase_plan.exposure_events,
        cohort_by_lemma=cohort_by_lemma,
    )
    refresh_payload: dict[str, object] | None = None
    refresh_audit: dict[str, object] | None = None
    if phase_plan.refresh_at is not None:
        store_before = load_srs_store(paths.srs_store_path_for(profile_id))
        refresh_events = load_signal_events(paths.srs_signal_queue_path_for(profile_id))
        refresh_audit = build_refresh_candidate_audit(
            paths,
            pair=pair,
            set_source_db=set_source_db,
            jmdict_path=jmdict_path,
            set_top_n=int(refresh_config.set_top_n or 0),
            feedback_window_size=int(refresh_config.feedback_window_size or 0),
            allowed_pos=refresh_config.allowed_pos,
            store_before=store_before,
            events=refresh_events,
            cohort_by_lemma=cohort_by_lemma,
            seed_builder=seed_builder,
        )
        with ExitStack() as stack:
            stack.enter_context(patched_now(phase_plan.refresh_at))
            if use_stub_seed_candidates:
                stack.enter_context(
                    patch(
                        "lexishift_core.helper.engine.build_seed_candidates",
                        side_effect=build_seed_candidates,
                    )
                )
            if use_stub_rulegen:
                stack.enter_context(
                    patch(
                        "lexishift_core.helper.engine.run_rulegen_for_pair",
                        side_effect=stub_run_rulegen_for_pair,
                    )
                )
            refresh_payload = refresh_srs_set(paths, config=refresh_config)
        selected_lemmas = (
            (refresh_payload or {}).get("admission_refresh", {}).get("selected_lemmas", [])
        )
        refresh_audit = apply_selected_lemmas_to_refresh_audit(
            refresh_audit,
            selected_lemmas=selected_lemmas if isinstance(selected_lemmas, Sequence) else [],
        )
    with patched_now(phase_plan.observe_at):
        snapshot = phase_snapshot(
            paths,
            pair=pair,
            profile_id=profile_id,
            now=phase_plan.observe_at,
            cohort_by_lemma=cohort_by_lemma,
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
    elif phase_plan.label == "duplicate_feedback_burst":
        target_lemma = str(phase_plan.feedback_events[0][0] if phase_plan.feedback_events else "")
        target_previous = _snapshot_item(previous_snapshot, target_lemma)
        target_current = _snapshot_item(snapshot, target_lemma)
        previous_history_count = (
            int(target_previous.get("history_count") or 0) if target_previous else 0
        )
        current_history_count = (
            int(target_current.get("history_count") or 0) if target_current else 0
        )
        previous_exposures = int(target_previous.get("exposures") or 0) if target_previous else 0
        current_exposures = int(target_current.get("exposures") or 0) if target_current else 0
        expected_count = len(phase_plan.feedback_events)
        if (
            target_lemma
            and expected_count > 0
            and len(feedback_events) == expected_count
            and current_history_count - previous_history_count == expected_count
            and current_exposures - previous_exposures == expected_count
        ):
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_JOURNEY_DUPLICATE_FEEDBACK_RECORDED",
                    message="Duplicate feedback in one short session was recorded without deduplication.",
                    details=(
                        f"lemma={target_lemma} history_delta={current_history_count - previous_history_count} "
                        f"exposure_delta={current_exposures - previous_exposures}"
                    ),
                    phase=phase_plan.label,
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_JOURNEY_DUPLICATE_FEEDBACK_RECORDED",
                    message="Duplicate feedback burst was not preserved as separate scheduler events.",
                    details=json.dumps(snapshot, ensure_ascii=False),
                    phase=phase_plan.label,
                )
            )
    elif phase_plan.label == "exposure_only_pause_probe":
        expected_exposure_counts: dict[str, int] = {}
        for lemma in phase_plan.exposure_events:
            expected_exposure_counts[str(lemma)] = expected_exposure_counts.get(str(lemma), 0) + 1
        exposure_deltas: dict[str, int] = {}
        history_deltas: dict[str, int] = {}
        for lemma, expected_count in expected_exposure_counts.items():
            previous_item = _snapshot_item(previous_snapshot, lemma)
            current_item = _snapshot_item(snapshot, lemma)
            previous_exposures = int(previous_item.get("exposures") or 0) if previous_item else 0
            current_exposures = int(current_item.get("exposures") or 0) if current_item else 0
            previous_history = int(previous_item.get("history_count") or 0) if previous_item else 0
            current_history = int(current_item.get("history_count") or 0) if current_item else 0
            exposure_deltas[lemma] = current_exposures - previous_exposures
            history_deltas[lemma] = current_history - previous_history
        reason_code = str(
            (refresh_payload or {}).get("admission_refresh", {}).get("reason_code") or ""
        )
        exposure_matches = all(
            exposure_deltas.get(lemma) == expected_count
            for lemma, expected_count in expected_exposure_counts.items()
        )
        history_stable = all(delta == 0 for delta in history_deltas.values())
        if (
            len(exposure_events) == len(phase_plan.exposure_events)
            and exposure_matches
            and history_stable
            and refresh_payload
            and not bool(refresh_payload.get("applied"))
            and reason_code == "retention_low"
        ):
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_JOURNEY_EXPOSURE_ONLY_NON_AUTHORITATIVE",
                    message="Exposure-only events stayed visible without changing retention-based admission behavior.",
                    details=(
                        f"exposure_deltas={json.dumps(exposure_deltas, ensure_ascii=False, sort_keys=True)} "
                        f"history_deltas={json.dumps(history_deltas, ensure_ascii=False, sort_keys=True)} "
                        f"reason_code={reason_code}"
                    ),
                    phase=phase_plan.label,
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_JOURNEY_EXPOSURE_ONLY_NON_AUTHORITATIVE",
                    message="Exposure-only events changed behavior unexpectedly or were not preserved clearly.",
                    details=json.dumps(
                        {
                            "expected_exposure_counts": expected_exposure_counts,
                            "exposure_deltas": exposure_deltas,
                            "history_deltas": history_deltas,
                            "refresh_payload": refresh_payload,
                        },
                        ensure_ascii=False,
                    ),
                    phase=phase_plan.label,
                )
            )
    return {
        "label": phase_plan.label,
        "step_index": [item.label for item in phase_plans].index(phase_plan.label) + 1,
        "now": phase_plan.observe_at.isoformat(),
        "events_applied": {
            "feedback": feedback_events,
            "exposure": exposure_events,
            "counts": {
                "feedback": len(feedback_events),
                "exposure": len(exposure_events),
            },
        },
        "refresh": {
            "requested": phase_plan.refresh_at is not None,
            "payload": refresh_payload,
            "audit": refresh_audit,
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

    with _temp_paths() as paths:
        resources = create_pair_resources(paths, pair=pair)
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
                    freedict_de_en_path=resources["freedict_path"],
                    set_source_db=resources["frequency_db"],
                    set_top_n=scenario_def.set_top_n,
                    bootstrap_top_n=scenario_def.bootstrap_top_n,
                    initial_active_count=scenario_def.initial_active_count,
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

        refresh_config = SrsRefreshJobConfig(
            pair=pair,
            profile_id=profile_id,
            jmdict_path=resources["jmdict_path"],
            freedict_de_en_path=resources["freedict_path"],
            set_source_db=resources["frequency_db"],
            set_top_n=scenario_def.set_top_n,
            feedback_window_size=8,
            persist_store=True,
            trigger="srs_journey_harness",
        )

        phases: list[dict[str, object]] = []
        previous_snapshot: Mapping[str, object] | None = None
        for phase_plan in phase_plans:
            phase_report = _run_phase(
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
        return {
            "version": 2,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "plan_doc": str(PROJECT_ROOT / "docs" / "srs" / "srs_journey_harness_workstream.md"),
            "scenario": {
                "id": scenario,
                "name": scenario,
                "pair": pair,
                "lane": scenario_def.lane,
                "contract_mode": contract_mode,
                "profile_id": profile_id,
                "settings": {
                    "max_active_items": scenario_def.max_active_items,
                    "max_new_items_per_day": scenario_def.max_new_items_per_day,
                },
                "bootstrap": {
                    "set_top_n": scenario_def.set_top_n,
                    "bootstrap_top_n": scenario_def.bootstrap_top_n,
                    "initial_active_count": scenario_def.initial_active_count,
                    "replace_pair": True,
                },
                "candidate_universe": scenario_candidate_universe(pair=pair),
                "cohorts": scenario_cohorts(pair),
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
