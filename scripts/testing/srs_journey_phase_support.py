from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Mapping, Sequence
from unittest.mock import patch

from lexishift_core.helper.engine import (
    SrsRefreshJobConfig,
    apply_exposure,
    apply_feedback,
    refresh_srs_set,
)
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.srs import load_srs_store
from lexishift_core.srs.signal_queue import load_signal_events

from srs_journey_harness_support import (
    JourneyPhasePlan,
    build_seed_candidates,
    patched_now,
    stub_run_rulegen_for_pair,
)
from srs_journey_installed_support import (
    cohort_map_from_role_assignments,
    update_role_assignments_from_refresh,
)
from srs_journey_review_support import (
    apply_selected_lemmas_to_refresh_audit,
    build_refresh_candidate_audit,
)
from srs_journey_runtime_support import (
    finding as _finding,
    resolve_exposure_plan_events,
    resolve_feedback_plan_events,
    snapshot_item as _snapshot_item,
)
from srs_journey_state_support import phase_deltas, phase_snapshot


def _apply_feedback_events(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    phase_time: datetime,
    events: Sequence[Mapping[str, str]],
) -> list[dict[str, object]]:
    applied: list[dict[str, object]] = []
    for index, event in enumerate(events):
        lemma = str(event.get("lemma") or "").strip()
        rating = str(event.get("rating") or "").strip()
        event_time = phase_time + timedelta(minutes=index)
        with patched_now(event_time):
            apply_feedback(paths, pair=pair, lemma=lemma, rating=rating, profile_id=profile_id)
        applied.append(
            {
                "index": index + 1,
                "ref": str(event.get("ref") or lemma),
                "lemma": lemma,
                "rating": rating,
                "ts": event_time.isoformat(),
                "cohort": str(event.get("cohort") or "frontier"),
            }
        )
    return applied


def _apply_exposure_events(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    phase_time: datetime,
    events: Sequence[Mapping[str, str]],
) -> list[dict[str, object]]:
    applied: list[dict[str, object]] = []
    for index, event in enumerate(events):
        lemma = str(event.get("lemma") or "").strip()
        event_time = phase_time + timedelta(minutes=index)
        with patched_now(event_time):
            apply_exposure(paths, pair=pair, lemma=lemma, profile_id=profile_id)
        applied.append(
            {
                "index": index + 1,
                "ref": str(event.get("ref") or lemma),
                "lemma": lemma,
                "ts": event_time.isoformat(),
                "cohort": str(event.get("cohort") or "frontier"),
            }
        )
    return applied


def run_phase(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    phase_plan: JourneyPhasePlan,
    phase_plans: Sequence[JourneyPhasePlan],
    previous_snapshot: Mapping[str, object] | None,
    refresh_config: SrsRefreshJobConfig,
    jmdict_path: Path,
    set_source_db: Path,
    seed_builder,
    use_stub_seed_candidates: bool,
    use_stub_rulegen: bool,
    cohort_by_lemma: Mapping[str, str],
    role_assignments: Mapping[str, str],
) -> tuple[dict[str, object], dict[str, str]]:
    resolved_feedback_events = resolve_feedback_plan_events(
        phase_plan.feedback_events,
        role_assignments=role_assignments,
        cohort_by_lemma=cohort_by_lemma,
    )
    resolved_exposure_events = resolve_exposure_plan_events(
        phase_plan.exposure_events,
        role_assignments=role_assignments,
        cohort_by_lemma=cohort_by_lemma,
    )
    feedback_events = _apply_feedback_events(
        paths,
        pair=pair,
        profile_id=profile_id,
        phase_time=phase_plan.observe_at,
        events=resolved_feedback_events,
    )
    exposure_events = _apply_exposure_events(
        paths,
        pair=pair,
        profile_id=profile_id,
        phase_time=phase_plan.observe_at,
        events=resolved_exposure_events,
    )
    refresh_payload: dict[str, object] | None = None
    refresh_audit: dict[str, object] | None = None
    updated_role_assignments = dict(role_assignments)
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
        updated_role_assignments = dict(role_assignments)
        updated_role_assignments = update_role_assignments_from_refresh(
            updated_role_assignments,
            phase_label=phase_plan.label,
            refresh_payload=refresh_payload,
        )
        cohort_by_lemma = cohort_map_from_role_assignments(
            cohort_by_lemma,
            updated_role_assignments,
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
    }, updated_role_assignments
