#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterator, Mapping, Sequence
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.helper.engine import (  # noqa: E402
    SrsRefreshJobConfig,
    SetInitializationJobConfig,
    apply_feedback,
    get_srs_runtime_diagnostics,
    initialize_srs_set,
    refresh_srs_set,
)
from lexishift_core.helper.paths import HelperPaths, build_helper_paths  # noqa: E402
from lexishift_core.srs import (  # noqa: E402
    SrsItem,
    SrsSettings,
    SrsStore,
    load_srs_store,
    save_srs_settings,
    save_srs_store,
)
from lexishift_core.srs.scheduler import select_active_items  # noqa: E402
from srs_quality_harness_support import (  # noqa: E402
    browsing_preview_findings as _browsing_preview_findings,
    build_pair_resources as _build_pair_resources,
    build_seed_candidates as _build_seed_candidates,
    create_frequency_db as _create_frequency_db,
    prepare_report_for_publication,
    ruleset_due_active_target_count as _ruleset_due_active_target_count,
    ruleset_srs_due_metadata_count as _ruleset_srs_due_metadata_count,
    ruleset_unique_target_count as _ruleset_unique_target_count,
    seed_browsing_preview_store as _seed_browsing_preview_store,
    snapshot_delta as _snapshot_delta,
    snapshot_target_count as _snapshot_target_count,
    store_snapshot as _store_snapshot,
    summarize_findings,
    stub_run_rulegen_for_pair as _stub_run_rulegen_for_pair,
)

SUPPORTED_SYNTHETIC_PAIRS = {"en-ja", "en-de"}
DEFAULT_PAIRS = ("en-ja", "en-de")


def _count_items_for_pair(paths: HelperPaths, *, pair: str, profile_id: str) -> int:
    store = load_srs_store(paths.srs_store_path_for(profile_id))
    return len([item for item in store.items if item.language_pair == pair])


def _finding(
    *,
    level: str,
    code: str,
    message: str,
    pair: str | None = None,
    details: str | None = None,
) -> dict[str, Any]:
    return {
        "level": level,
        "code": code,
        "pair": pair,
        "message": message,
        "details": details,
    }


@contextmanager
def _temp_paths() -> Iterator[HelperPaths]:
    with tempfile.TemporaryDirectory() as tmp:
        yield build_helper_paths(Path(tmp))


def _run_pair_bootstrap_scenario(pair: str) -> dict[str, Any]:
    profile_id = "default"
    with _temp_paths() as paths:
        save_srs_settings(
            SrsSettings(max_active_items=100, max_new_items_per_day=8),
            paths.srs_settings_path,
        )
        _build_pair_resources(paths, pair=pair)

        init_payload = initialize_srs_set(
            paths,
            config=SetInitializationJobConfig(
                pair=pair,
                profile_id=profile_id,
                set_top_n=200,
                replace_pair=True,
            ),
        )
        _seed_browsing_preview_store(paths, pair=pair, profile_id=profile_id)
        refresh_payload = refresh_srs_set(
            paths,
            config=SrsRefreshJobConfig(
                pair=pair,
                profile_id=profile_id,
                set_top_n=200,
                feedback_window_size=40,
            ),
        )
        diagnostics = get_srs_runtime_diagnostics(paths, pair=pair, profile_id=profile_id)
        store = load_srs_store(paths.srs_store_path_for(profile_id))
        due_items = select_active_items(
            store.items,
            max_active=100,
            allowed_pairs=[pair],
        )
        ruleset_path = Path(str(diagnostics.get("ruleset_path") or ""))
        snapshot_path = Path(str(diagnostics.get("snapshot_path") or ""))
        ruleset_unique_targets = (
            _ruleset_unique_target_count(ruleset_path) if ruleset_path.exists() else 0
        )
        srs_due_metadata_count = (
            _ruleset_srs_due_metadata_count(ruleset_path) if ruleset_path.exists() else 0
        )
        runtime_due_active_count = (
            _ruleset_due_active_target_count(ruleset_path) if ruleset_path.exists() else 0
        )
        snapshot_target_count = (
            _snapshot_target_count(snapshot_path) if snapshot_path.exists() else 0
        )

        findings: list[dict[str, Any]] = []
        if bool(init_payload.get("applied")):
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_INITIALIZE_APPLIED",
                    pair=pair,
                    message="Initialization applied and published helper outputs.",
                    details=f"added_items={int(init_payload.get('added_items') or 0)}",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_INITIALIZE_NOT_APPLIED",
                    pair=pair,
                    message="Initialization did not apply.",
                    details=json.dumps(init_payload, ensure_ascii=False),
                )
            )

        if bool(refresh_payload.get("applied")):
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_REFRESH_APPLIED",
                    pair=pair,
                    message="Refresh applied and published helper outputs.",
                    details=f"added_items={int(refresh_payload.get('added_items') or 0)}",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_REFRESH_NOT_APPLIED",
                    pair=pair,
                    message="Refresh did not apply new SRS items.",
                    details=json.dumps(refresh_payload, ensure_ascii=False),
                )
            )

        findings.extend(_browsing_preview_findings(refresh_payload, pair=pair))

        artifacts_ok = (
            bool(diagnostics.get("store_exists"))
            and bool(diagnostics.get("ruleset_exists"))
            and bool(diagnostics.get("snapshot_exists"))
        )
        if artifacts_ok:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_RUNTIME_ARTIFACTS_PRESENT",
                    pair=pair,
                    message="Store, ruleset, and snapshot artifacts are present.",
                    details=(
                        f"store_items_for_pair={int(diagnostics.get('store_items_for_pair') or 0)} "
                        f"ruleset_rules_count={int(diagnostics.get('ruleset_rules_count') or 0)} "
                        f"snapshot_target_count={int(diagnostics.get('snapshot_target_count') or 0)}"
                    ),
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_RUNTIME_ARTIFACTS_MISSING",
                    pair=pair,
                    message="Expected runtime artifacts are missing.",
                    details=json.dumps(diagnostics, ensure_ascii=False),
                )
            )

        missing_inputs = diagnostics.get("missing_inputs", [])
        if isinstance(missing_inputs, list) and not missing_inputs:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_RUNTIME_INPUTS_PRESENT",
                    pair=pair,
                    message="Synthetic scenario resolved all helper inputs.",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_RUNTIME_INPUTS_MISSING",
                    pair=pair,
                    message="Synthetic scenario is missing helper inputs.",
                    details=json.dumps(missing_inputs, ensure_ascii=False),
                )
            )

        if due_items:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_DUE_QUEUE_NONEMPTY",
                    pair=pair,
                    message="Due-item selector returns active items for practice.",
                    details=f"due_count={len(due_items)}",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_DUE_QUEUE_EMPTY",
                    pair=pair,
                    message="Due-item selector returned no active items.",
                )
            )

        store_items_for_pair = int(diagnostics.get("store_items_for_pair") or 0)
        if (
            snapshot_target_count <= store_items_for_pair
            and ruleset_unique_targets <= store_items_for_pair
        ):
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_PUBLICATION_COUNTS_BOUNDED",
                    pair=pair,
                    message="Published targets do not exceed admitted store items.",
                    details=(
                        f"store_items_for_pair={store_items_for_pair} "
                        f"ruleset_unique_targets={ruleset_unique_targets} "
                        f"snapshot_target_count={snapshot_target_count}"
                    ),
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_PUBLICATION_COUNTS_EXCEED_STORE",
                    pair=pair,
                    message="Published targets exceed admitted store items.",
                    details=(
                        f"store_items_for_pair={store_items_for_pair} "
                        f"ruleset_unique_targets={ruleset_unique_targets} "
                        f"snapshot_target_count={snapshot_target_count}"
                    ),
                )
            )

        return {
            "pair": pair,
            "init": init_payload,
            "refresh": refresh_payload,
            "diagnostics": diagnostics,
            "store_items_for_pair": store_items_for_pair,
            "due_count": len(due_items),
            "ruleset_unique_targets": ruleset_unique_targets,
            "srs_due_metadata_count": srs_due_metadata_count,
            "runtime_due_active_count": runtime_due_active_count,
            "snapshot_target_count": snapshot_target_count,
            "findings": findings,
        }


def _run_feedback_cycle_scenario() -> dict[str, Any]:
    profile_id = "default"
    pair = "en-ja"
    with _temp_paths() as paths:
        jmdict_dir = Path(paths.data_root) / "jmdict"
        jmdict_dir.mkdir(parents=True, exist_ok=True)
        source_db = _create_frequency_db(Path(paths.data_root) / "freq.sqlite")
        save_srs_settings(
            SrsSettings(max_active_items=8, max_new_items_per_day=2),
            paths.srs_settings_path,
        )
        save_srs_store(
            SrsStore(
                items=(
                    SrsItem(
                        item_id="en-ja:alpha",
                        lemma="alpha",
                        language_pair=pair,
                        source_type="initial_set",
                    ),
                ),
                version=1,
            ),
            paths.srs_store_path_for(profile_id),
        )

        phases: list[dict[str, Any]] = []
        previous_snapshot = _store_snapshot(
            paths,
            pair=pair,
            profile_id=profile_id,
            max_active=8,
        )
        initial_snapshot = previous_snapshot

        def run_refresh(label: str) -> dict[str, Any]:
            nonlocal previous_snapshot
            before_refresh = _store_snapshot(
                paths,
                pair=pair,
                profile_id=profile_id,
                max_active=8,
            )
            result = refresh_srs_set(
                paths,
                config=SrsRefreshJobConfig(
                    pair=pair,
                    profile_id=profile_id,
                    jmdict_path=jmdict_dir,
                    set_source_db=source_db,
                    set_top_n=2000,
                    feedback_window_size=8,
                    persist_store=True,
                ),
            )
            after_refresh = _store_snapshot(
                paths,
                pair=pair,
                profile_id=profile_id,
                max_active=8,
            )
            total_for_pair = _count_items_for_pair(paths, pair=pair, profile_id=profile_id)
            rulegen_payload = result.get("rulegen") or {}
            ruleset_path = (
                Path(str(rulegen_payload.get("ruleset_path")))
                if rulegen_payload.get("ruleset_path")
                else paths.ruleset_path(pair, profile_id=profile_id)
            )
            snapshot_path = (
                Path(str(rulegen_payload.get("snapshot_path")))
                if rulegen_payload.get("snapshot_path")
                else paths.snapshot_path(pair, profile_id=profile_id)
            )
            phase = {
                "label": label,
                "applied": bool(result.get("applied")),
                "added_items": int(result.get("added_items") or 0),
                "selected_lemmas": list(
                    result.get("admission_refresh", {}).get("selected_lemmas", []) or []
                ),
                "total_items_for_pair": total_for_pair,
                "reason_code": str(result.get("admission_refresh", {}).get("reason_code", "")),
                "feedback_count": int(
                    result.get("admission_refresh", {})
                    .get("feedback_window", {})
                    .get("feedback_count", 0)
                ),
                "retention_ratio": result.get("admission_refresh", {})
                .get("feedback_window", {})
                .get("retention_ratio"),
                "ruleset_count": _ruleset_unique_target_count(ruleset_path)
                if ruleset_path.exists()
                else 0,
                "srs_due_metadata_count": _ruleset_srs_due_metadata_count(ruleset_path)
                if ruleset_path.exists()
                else 0,
                "runtime_due_active_count": _ruleset_due_active_target_count(ruleset_path)
                if ruleset_path.exists()
                else 0,
                "snapshot_target_count": _snapshot_target_count(snapshot_path)
                if snapshot_path.exists()
                else 0,
                "before_refresh": before_refresh,
                "after_refresh": after_refresh,
                "feedback_delta": _snapshot_delta(previous_snapshot, before_refresh),
                "refresh_delta": _snapshot_delta(before_refresh, after_refresh),
            }
            phase["due_count"] = int(after_refresh.get("due_count") or 0)
            phases.append(phase)
            previous_snapshot = after_refresh
            return phase

        with (
            patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                return_value=_build_seed_candidates(),
            ),
            patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                side_effect=_stub_run_rulegen_for_pair,
            ),
        ):
            for rating in ("good", "easy", "good", "easy", "good", "easy", "good", "easy"):
                apply_feedback(
                    paths, pair=pair, lemma="alpha", rating=rating, profile_id=profile_id
                )
            phase_1 = run_refresh("high_retention_1")

            for rating in ("again", "hard", "again", "hard", "again", "hard", "again", "hard"):
                apply_feedback(
                    paths, pair=pair, lemma="alpha", rating=rating, profile_id=profile_id
                )
            phase_2 = run_refresh("low_retention_pause")

            for rating in ("easy", "good", "easy", "good", "easy", "good", "easy", "good"):
                apply_feedback(
                    paths, pair=pair, lemma="alpha", rating=rating, profile_id=profile_id
                )
            phase_3 = run_refresh("high_retention_2")

        findings: list[dict[str, Any]] = []
        if [
            phase_1["total_items_for_pair"],
            phase_2["total_items_for_pair"],
            phase_3["total_items_for_pair"],
        ] == [3, 3, 5]:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_FEEDBACK_GROWTH_CURVE",
                    pair=pair,
                    message="Feedback cycle grows, pauses, then resumes SRS admissions as expected.",
                    details="totals=[3,3,5]",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_FEEDBACK_GROWTH_CURVE_BROKEN",
                    pair=pair,
                    message="Feedback cycle did not produce the expected growth/pause/growth curve.",
                    details=json.dumps(phases, ensure_ascii=False),
                )
            )

        if not phase_2["applied"] and phase_2["reason_code"] == "retention_low":
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_RETENTION_PAUSE_TRIGGERED",
                    pair=pair,
                    message="Low retention pauses new admissions.",
                    details=f"reason_code={phase_2['reason_code']}",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_RETENTION_PAUSE_MISSING",
                    pair=pair,
                    message="Low retention did not pause admissions as expected.",
                    details=json.dumps(phase_2, ensure_ascii=False),
                )
            )

        ruleset_aligned = all(
            int(phase["ruleset_count"]) == int(phase["snapshot_target_count"]) for phase in phases
        )
        if ruleset_aligned:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_FEEDBACK_RULESET_ALIGNMENT",
                    pair=pair,
                    message="Ruleset and snapshot target counts remain aligned across feedback phases.",
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_FEEDBACK_RULESET_MISMATCH",
                    pair=pair,
                    message="Ruleset and snapshot target counts diverged across feedback phases.",
                    details=json.dumps(phases, ensure_ascii=False),
                )
            )

        snapshot_contract_ok = (
            all(
                isinstance(phase.get("before_refresh"), Mapping)
                and isinstance(phase.get("after_refresh"), Mapping)
                and isinstance(phase.get("feedback_delta"), Mapping)
                and isinstance(phase.get("refresh_delta"), Mapping)
                for phase in phases
            )
            and phase_1["feedback_delta"].get("reviewed_lemmas") == ["alpha"]
            and "alpha" in phase_1["feedback_delta"].get("scheduler_changed_lemmas", [])
            and sorted(phase_1.get("selected_lemmas", []))
            == sorted(phase_1["refresh_delta"].get("added_lemmas", []))
            and phase_2.get("selected_lemmas") == []
            and int(phase_2["refresh_delta"].get("total_items_delta") or 0) == 0
            and sorted(phase_3.get("selected_lemmas", []))
            == sorted(phase_3["refresh_delta"].get("added_lemmas", []))
        )
        if snapshot_contract_ok:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_FEEDBACK_SNAPSHOTS_CAPTURED",
                    pair=pair,
                    message=(
                        "Feedback-cycle phases include before/after store snapshots and "
                        "separate feedback vs refresh deltas."
                    ),
                    details=(
                        f"phase1_reviewed={','.join(phase_1['feedback_delta']['reviewed_lemmas'])} "
                        f"phase1_added={','.join(phase_1['refresh_delta']['added_lemmas'])} "
                        f"phase3_added={','.join(phase_3['refresh_delta']['added_lemmas'])}"
                    ),
                )
            )
        else:
            findings.append(
                _finding(
                    level="FAIL",
                    code="SRS_FEEDBACK_SNAPSHOTS_INCOMPLETE",
                    pair=pair,
                    message="Feedback-cycle before/after snapshots are missing or inconsistent.",
                    details=json.dumps(phases, ensure_ascii=False),
                )
            )

        due_scope_broader_than_due = next(
            (
                phase
                for phase in phases
                if int(phase["total_items_for_pair"]) > int(phase["due_count"])
                and int(phase["ruleset_count"]) >= int(phase["total_items_for_pair"])
            ),
            None,
        )
        due_runtime_verified = (
            due_scope_broader_than_due is not None
            and int(due_scope_broader_than_due["srs_due_metadata_count"])
            >= int(due_scope_broader_than_due["ruleset_count"])
            and int(due_scope_broader_than_due["runtime_due_active_count"])
            <= int(due_scope_broader_than_due["due_count"])
        )
        if due_runtime_verified:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_DUE_AWARE_RUNTIME_GATE_VERIFIED",
                    pair=pair,
                    message=(
                        "Helper ruleset may remain broader than due, but due metadata supports "
                        "runtime due-aware serving."
                    ),
                    details=(
                        f"phase={due_scope_broader_than_due['label']} "
                        f"total_items={int(due_scope_broader_than_due['total_items_for_pair'])} "
                        f"due_count={int(due_scope_broader_than_due['due_count'])} "
                        f"ruleset_count={int(due_scope_broader_than_due['ruleset_count'])} "
                        "srs_due_metadata_count="
                        f"{int(due_scope_broader_than_due['srs_due_metadata_count'])} "
                        "runtime_due_active_count="
                        f"{int(due_scope_broader_than_due['runtime_due_active_count'])}"
                    ),
                )
            )
        elif due_scope_broader_than_due is not None:
            findings.append(
                _finding(
                    level="WARN",
                    code="SRS_DUE_AWARE_PUBLISH_UNVERIFIED",
                    pair=pair,
                    message="Published ruleset appears to cover admitted items beyond the due subset.",
                    details=(
                        f"phase={due_scope_broader_than_due['label']} "
                        f"total_items={int(due_scope_broader_than_due['total_items_for_pair'])} "
                        f"due_count={int(due_scope_broader_than_due['due_count'])} "
                        f"ruleset_count={int(due_scope_broader_than_due['ruleset_count'])}"
                    ),
                )
            )
        else:
            findings.append(
                _finding(
                    level="PASS",
                    code="SRS_DUE_AWARE_PUBLISH_WITHIN_DUE_SET",
                    pair=pair,
                    message="Feedback scenario did not expose publication broader than the due subset.",
                )
            )

        return {
            "pair": pair,
            "initial_snapshot": initial_snapshot,
            "phases": phases,
            "findings": findings,
        }


def build_report(
    *,
    pairs: Sequence[str] = DEFAULT_PAIRS,
    include_feedback: bool = True,
    fail_on_warn: bool = False,
) -> dict[str, Any]:
    normalized_pairs = [str(pair).strip().lower() for pair in pairs if str(pair).strip()]
    supported_pairs = [pair for pair in normalized_pairs if pair in SUPPORTED_SYNTHETIC_PAIRS]
    unsupported_pairs = [pair for pair in normalized_pairs if pair not in SUPPORTED_SYNTHETIC_PAIRS]

    findings: list[dict[str, Any]] = []
    pair_reports: list[dict[str, Any]] = []
    for pair in supported_pairs:
        pair_report = _run_pair_bootstrap_scenario(pair)
        pair_reports.append(pair_report)
        findings.extend(pair_report["findings"])

    if unsupported_pairs:
        findings.append(
            _finding(
                level="WARN",
                code="SRS_UNSUPPORTED_SYNTHETIC_PAIRS",
                message="Some requested pairs do not yet have synthetic SRS quality scenarios.",
                details=",".join(sorted(unsupported_pairs)),
            )
        )

    feedback_report: dict[str, Any] | None = None
    if include_feedback:
        feedback_report = _run_feedback_cycle_scenario()
        findings.extend(feedback_report["findings"])

    summary = summarize_findings(findings, fail_on_warn=fail_on_warn)
    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fail_on_warn": bool(fail_on_warn),
        "supported_pairs": supported_pairs,
        "unsupported_pairs": unsupported_pairs,
        "summary": summary,
        "pair_bootstrap_scenarios": pair_reports,
        "feedback_cycle_scenario": feedback_report,
        "findings": findings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a synthetic SRS quality harness that exercises bootstrap publication, runtime "
            "diagnostics, and feedback-driven refresh behavior."
        )
    )
    parser.add_argument(
        "--pairs",
        default=",".join(DEFAULT_PAIRS),
        help="Comma-separated pair list for synthetic bootstrap scenarios.",
    )
    parser.add_argument(
        "--no-feedback-scenario",
        action="store_true",
        help="Skip the feedback-cycle scenario.",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Exit non-zero when warnings are present.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "srs_quality_latest.json",
        help="Path to write the JSON report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pairs = [item.strip() for item in str(args.pairs).split(",") if item.strip()]
    report = build_report(
        pairs=pairs,
        include_feedback=not bool(args.no_feedback_scenario),
        fail_on_warn=bool(args.fail_on_warn),
    )
    published_report = prepare_report_for_publication(report)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(published_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"json_out: {args.json_out}")
    summary = published_report.get("summary") or {}
    print(
        "summary: "
        f"pass={int(summary.get('pass_count') or 0)} "
        f"warn={int(summary.get('warn_count') or 0)} "
        f"fail={int(summary.get('fail_count') or 0)}"
    )
    if bool(summary.get("should_fail")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
