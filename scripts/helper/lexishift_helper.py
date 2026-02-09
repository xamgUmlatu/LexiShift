#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.helper_engine import (
    get_srs_runtime_diagnostics,
    RulegenJobConfig,
    SrsRefreshJobConfig,
    SetInitializationJobConfig,
    SetPlanningJobConfig,
    apply_exposure,
    apply_feedback,
    initialize_srs_set,
    load_snapshot,
    plan_srs_set,
    refresh_srs_set,
    reset_srs_data,
    run_rulegen_job,
)
from lexishift_core.helper_profiles import get_profiles_snapshot
from lexishift_core.helper_paths import build_helper_paths
from lexishift_core.helper_status import load_status
from lexishift_core.lp_capabilities import (
    default_freedict_de_en_path,
    default_frequency_db_path,
    default_jmdict_path,
)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def _load_optional_json(value: Optional[str]) -> Optional[dict]:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON payload: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("JSON payload must be an object.")
    return parsed


def _resolve_pair_resource_paths(
    paths,
    *,
    pair: str,
    jmdict_arg: Optional[str],
    freedict_de_en_arg: Optional[str],
    set_source_db_arg: Optional[str],
) -> tuple[Optional[Path], Optional[Path], Optional[Path]]:
    jmdict_path = Path(jmdict_arg) if jmdict_arg else default_jmdict_path(
        pair,
        language_packs_dir=paths.language_packs_dir,
    )
    freedict_de_en_path = Path(freedict_de_en_arg) if freedict_de_en_arg else default_freedict_de_en_path(
        pair,
        language_packs_dir=paths.language_packs_dir,
    )
    set_source_db = Path(set_source_db_arg) if set_source_db_arg else default_frequency_db_path(
        pair,
        frequency_packs_dir=paths.frequency_packs_dir,
    )
    return jmdict_path, freedict_de_en_path, set_source_db


def cmd_status(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    profile_id = paths.normalize_profile_id(args.profile_id or "default")
    status = load_status(paths.srs_status_path_for(profile_id))
    payload = status.__dict__
    payload["profile_id"] = profile_id
    _print_json(payload)
    return 0


def cmd_get_snapshot(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    try:
        payload = load_snapshot(paths, pair=args.pair, profile_id=args.profile_id or "default")
    except FileNotFoundError:
        _print_json(
            {
                "error": "snapshot_not_found",
                "path": str(paths.snapshot_path(args.pair, profile_id=args.profile_id or "default")),
            }
        )
        return 1
    _print_json(payload)
    return 0


def cmd_srs_diagnostics(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    payload = get_srs_runtime_diagnostics(paths, pair=args.pair, profile_id=args.profile_id or "default")
    _print_json(payload)
    return 0


def cmd_run_rulegen(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    jmdict_path, freedict_de_en_path, set_source_db = _resolve_pair_resource_paths(
        paths,
        pair=args.pair,
        jmdict_arg=args.jmdict,
        freedict_de_en_arg=args.freedict_de_en,
        set_source_db_arg=args.set_source_db,
    )

    try:
        payload = run_rulegen_job(
            paths,
            config=RulegenJobConfig(
                pair=args.pair,
                jmdict_path=jmdict_path,
                freedict_de_en_path=freedict_de_en_path,
                profile_id=args.profile_id or "default",
                set_source_db=set_source_db,
                set_top_n=args.set_top_n,
                confidence_threshold=args.confidence_threshold,
                snapshot_targets=args.snapshot_targets,
                snapshot_sources=args.snapshot_sources,
                initialize_if_empty=not args.no_initialize_if_empty,
                persist_store=not args.no_persist_store,
                persist_outputs=not args.no_persist_outputs,
                update_status=not args.no_status_update,
                sample_count=args.sample_count,
                sample_strategy=args.sample_strategy,
                sample_seed=args.sample_seed,
            ),
        )
        _print_json(payload)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1


def cmd_init_srs_set(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    jmdict_path, freedict_de_en_path, set_source_db = _resolve_pair_resource_paths(
        paths,
        pair=args.pair,
        jmdict_arg=args.jmdict,
        freedict_de_en_arg=args.freedict_de_en,
        set_source_db_arg=args.set_source_db,
    )

    try:
        profile_context = _load_optional_json(args.profile_context_json)
        payload = initialize_srs_set(
            paths,
            config=SetInitializationJobConfig(
                pair=args.pair,
                jmdict_path=jmdict_path,
                freedict_de_en_path=freedict_de_en_path,
                set_source_db=set_source_db,
                profile_id=args.profile_id or "default",
                set_top_n=args.set_top_n,
                bootstrap_top_n=args.bootstrap_top_n,
                initial_active_count=args.initial_active_count,
                max_active_items_hint=args.max_active_items_hint,
                replace_pair=args.replace_pair,
                strategy=args.strategy,
                objective=args.objective,
                profile_context=profile_context,
                trigger=args.trigger,
            ),
        )
        _print_json(payload)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1


def cmd_plan_srs_set(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    try:
        profile_context = _load_optional_json(args.profile_context_json)
        payload = plan_srs_set(
            paths,
            config=SetPlanningJobConfig(
                pair=args.pair,
                profile_id=args.profile_id or "default",
                strategy=args.strategy,
                objective=args.objective,
                set_top_n=args.set_top_n,
                bootstrap_top_n=args.bootstrap_top_n,
                initial_active_count=args.initial_active_count,
                max_active_items_hint=args.max_active_items_hint,
                replace_pair=args.replace_pair,
                profile_context=profile_context,
                trigger=args.trigger,
            ),
        )
        _print_json(payload)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1


def cmd_refresh_srs_set(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    jmdict_path, freedict_de_en_path, set_source_db = _resolve_pair_resource_paths(
        paths,
        pair=args.pair,
        jmdict_arg=args.jmdict,
        freedict_de_en_arg=args.freedict_de_en,
        set_source_db_arg=args.set_source_db,
    )
    try:
        payload = refresh_srs_set(
            paths,
            config=SrsRefreshJobConfig(
                pair=args.pair,
                jmdict_path=jmdict_path,
                freedict_de_en_path=freedict_de_en_path,
                set_source_db=set_source_db,
                profile_id=args.profile_id or "default",
                set_top_n=args.set_top_n,
                feedback_window_size=args.feedback_window_size,
                max_active_items=args.max_active_items,
                max_new_items=args.max_new_items,
                persist_store=not args.no_persist_store,
                trigger=args.trigger,
            ),
        )
        _print_json(payload)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1


def cmd_record_feedback(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    apply_feedback(
        paths,
        pair=args.pair,
        lemma=args.lemma,
        rating=args.rating,
        source_type=args.source_type,
        profile_id=args.profile_id or "default",
    )
    _print_json({"ok": True})
    return 0


def cmd_record_exposure(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    apply_exposure(
        paths,
        pair=args.pair,
        lemma=args.lemma,
        source_type=args.source_type,
        profile_id=args.profile_id or "default",
    )
    _print_json({"ok": True})
    return 0


def cmd_reset_srs(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    payload = reset_srs_data(paths, pair=args.pair, profile_id=args.profile_id or "default")
    _print_json(payload)
    return 0


def cmd_profiles_get(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    payload = get_profiles_snapshot(paths)
    _print_json(payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LexiShift Helper CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show helper status")
    status.add_argument("--profile-id", help="Profile id (default: default)")
    status.set_defaults(func=cmd_status)

    snapshot = sub.add_parser("get_snapshot", help="Print rulegen snapshot for a pair")
    snapshot.add_argument("--pair", default="en-ja")
    snapshot.add_argument("--profile-id", help="Profile id (default: default)")
    snapshot.set_defaults(func=cmd_get_snapshot)

    diagnostics = sub.add_parser("srs_diagnostics", help="Show helper-side SRS runtime diagnostics")
    diagnostics.add_argument("--pair", default="en-ja")
    diagnostics.add_argument("--profile-id", help="Profile id (default: default)")
    diagnostics.set_defaults(func=cmd_srs_diagnostics)

    run = sub.add_parser("run_rulegen", help="Run rulegen for a language pair")
    run.add_argument("--pair", default="en-ja")
    run.add_argument("--profile-id", help="Profile id (default: default)")
    run.add_argument("--jmdict", help="Path to JMdict_e folder")
    run.add_argument("--freedict-de-en", help="Path to FreeDict DE->EN TEI file (deu-eng.tei)")
    run.add_argument("--set-source-db", help="Path to frequency SQLite for initializing S")
    run.add_argument("--set-top-n", type=int, help="Top-N seed cap (defaults from pair policy when omitted).")
    run.add_argument("--no-initialize-if-empty", action="store_true", help="Skip S initialization when store is empty")
    run.add_argument("--no-persist-store", action="store_true", help="Do not write changes to srs_store.json")
    run.add_argument("--no-persist-outputs", action="store_true", help="Do not write ruleset/snapshot JSON files")
    run.add_argument("--no-status-update", action="store_true", help="Do not update helper status file")
    run.add_argument("--confidence-threshold", type=float, default=0.0)
    run.add_argument("--snapshot-targets", type=int, default=50)
    run.add_argument("--snapshot-sources", type=int, default=6)
    run.add_argument("--sample-count", type=int, help="Sample N target lemmas from current S before rulegen.")
    run.add_argument(
        "--sample-strategy",
        choices=("weighted_priority", "uniform"),
        help="Sampling strategy used with --sample-count.",
    )
    run.add_argument("--sample-seed", type=int, help="Optional RNG seed for deterministic sampling.")
    run.set_defaults(func=cmd_run_rulegen)

    init_s = sub.add_parser("init_srs_set", help="Initialize S for a language pair")
    init_s.add_argument("--pair", default="en-ja")
    init_s.add_argument("--profile-id", help="Profile id (default: default)")
    init_s.add_argument("--jmdict", help="Path to JMdict_e folder")
    init_s.add_argument("--freedict-de-en", help="Path to FreeDict DE->EN TEI file (deu-eng.tei)")
    init_s.add_argument("--set-source-db", help="Path to frequency SQLite used to initialize S")
    init_s.add_argument("--set-top-n", type=int, help="Bootstrap top-N cap (defaults from pair policy when omitted).")
    init_s.add_argument("--replace-pair", action="store_true", help="Replace existing pair entries before initializing S")
    init_s.add_argument("--bootstrap-top-n", type=int, help="Explicit bootstrap size for S (preferred over --set-top-n).")
    init_s.add_argument("--initial-active-count", type=int, help="Initial active subset size within bootstrap S.")
    init_s.add_argument("--max-active-items-hint", type=int, help="Hint for active workload cap during planning.")
    init_s.add_argument("--strategy", default="frequency_bootstrap")
    init_s.add_argument("--objective", default="bootstrap")
    init_s.add_argument("--trigger", default="cli")
    init_s.add_argument("--profile-context-json", help="JSON object with profile context signals")
    init_s.set_defaults(func=cmd_init_srs_set)

    plan_s = sub.add_parser("plan_srs_set", help="Build a set planning decision without mutating store")
    plan_s.add_argument("--pair", default="en-ja")
    plan_s.add_argument("--profile-id", help="Profile id (default: default)")
    plan_s.add_argument("--strategy", default="profile_bootstrap")
    plan_s.add_argument("--objective", default="bootstrap")
    plan_s.add_argument("--set-top-n", type=int, help="Bootstrap top-N cap (defaults from pair policy when omitted).")
    plan_s.add_argument("--bootstrap-top-n", type=int, help="Explicit bootstrap size for S (preferred over --set-top-n).")
    plan_s.add_argument("--initial-active-count", type=int, help="Initial active subset size within bootstrap S.")
    plan_s.add_argument("--max-active-items-hint", type=int, help="Hint for active workload cap during planning.")
    plan_s.add_argument("--replace-pair", action="store_true")
    plan_s.add_argument("--trigger", default="cli")
    plan_s.add_argument("--profile-context-json", help="JSON object with profile context signals")
    plan_s.set_defaults(func=cmd_plan_srs_set)

    refresh_s = sub.add_parser("refresh_srs_set", help="Apply feedback-driven admission refresh")
    refresh_s.add_argument("--pair", default="en-ja")
    refresh_s.add_argument("--profile-id", help="Profile id (default: default)")
    refresh_s.add_argument("--jmdict", help="Path to JMdict_e folder")
    refresh_s.add_argument("--freedict-de-en", help="Path to FreeDict DE->EN TEI file (deu-eng.tei)")
    refresh_s.add_argument("--set-source-db", help="Path to frequency SQLite used for candidate pool")
    refresh_s.add_argument("--set-top-n", type=int, help="Refresh candidate pool size (defaults from pair policy when omitted).")
    refresh_s.add_argument("--feedback-window-size", type=int, help="Feedback window size (defaults from pair policy when omitted).")
    refresh_s.add_argument("--max-active-items", type=int, help="Override max active items for refresh planning.")
    refresh_s.add_argument("--max-new-items", type=int, help="Override max new items/day for refresh planning.")
    refresh_s.add_argument("--no-persist-store", action="store_true", help="Do not write changes to srs_store.json")
    refresh_s.add_argument("--trigger", default="cli")
    refresh_s.set_defaults(func=cmd_refresh_srs_set)

    feedback = sub.add_parser("record_feedback", help="Record SRS feedback")
    feedback.add_argument("--pair", required=True)
    feedback.add_argument("--profile-id", help="Profile id (default: default)")
    feedback.add_argument("--lemma", required=True)
    feedback.add_argument("--rating", required=True)
    feedback.add_argument("--source-type", default="extension")
    feedback.set_defaults(func=cmd_record_feedback)

    exposure = sub.add_parser("record_exposure", help="Record SRS exposure")
    exposure.add_argument("--pair", required=True)
    exposure.add_argument("--profile-id", help="Profile id (default: default)")
    exposure.add_argument("--lemma", required=True)
    exposure.add_argument("--source-type", default="extension")
    exposure.set_defaults(func=cmd_record_exposure)

    reset = sub.add_parser("reset_srs", help="Reset SRS progress")
    reset.add_argument("--pair", help="Language pair to reset (omit to reset all).")
    reset.add_argument("--profile-id", help="Profile id (default: default)")
    reset.set_defaults(func=cmd_reset_srs)

    profiles_get = sub.add_parser("profiles_get", help="Show helper profile snapshot from settings.json")
    profiles_get.set_defaults(func=cmd_profiles_get)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
