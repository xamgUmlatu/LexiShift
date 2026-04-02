#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.helper.engine import (
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
from lexishift_core.helper.profiles import get_profile_rulesets_snapshot, get_profiles_snapshot
from lexishift_core.helper.paths import build_helper_paths
from lexishift_core.helper.status import load_status
from lexishift_core.helper.lp_capabilities import (
    default_frequency_db_path,
    default_jmdict_path,
    default_translation_dictionary_path,
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
    jmdict_path = (
        Path(jmdict_arg)
        if jmdict_arg
        else default_jmdict_path(
            pair,
            language_packs_dir=paths.language_packs_dir,
        )
    )
    translation_dict_path = (
        Path(freedict_de_en_arg)
        if freedict_de_en_arg
        else default_translation_dictionary_path(
            pair,
            language_packs_dir=paths.language_packs_dir,
        )
    )
    set_source_db = (
        Path(set_source_db_arg)
        if set_source_db_arg
        else default_frequency_db_path(
            pair,
            frequency_packs_dir=paths.frequency_packs_dir,
        )
    )
    return jmdict_path, translation_dict_path, set_source_db


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
                "path": str(
                    paths.snapshot_path(args.pair, profile_id=args.profile_id or "default")
                ),
            }
        )
        return 1
    _print_json(payload)
    return 0


def cmd_srs_diagnostics(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    payload = get_srs_runtime_diagnostics(
        paths, pair=args.pair, profile_id=args.profile_id or "default"
    )
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
    if args.enable_pos_scoring:
        pos_scoring_enabled = True
    elif args.disable_pos_scoring:
        pos_scoring_enabled = False
    else:
        pos_scoring_enabled = None
    if args.enable_reverse_check:
        reverse_check_enabled = True
    elif args.disable_reverse_check:
        reverse_check_enabled = False
    else:
        reverse_check_enabled = None
    if args.include_variants:
        include_variants = True
    elif args.no_include_variants:
        include_variants = False
    else:
        include_variants = None
    if args.allow_multiword_glosses:
        allow_multiword_glosses = True
    elif args.disallow_multiword_glosses:
        allow_multiword_glosses = False
    else:
        allow_multiword_glosses = None

    try:
        payload = run_rulegen_job(
            paths,
            config=RulegenJobConfig(
                pair=args.pair,
                jmdict_path=jmdict_path,
                translation_dict_path=freedict_de_en_path,
                freedict_de_en_path=freedict_de_en_path,
                profile_id=args.profile_id or "default",
                set_source_db=set_source_db,
                set_top_n=args.set_top_n,
                confidence_threshold=args.confidence_threshold,
                max_definitions_per_target=args.max_definitions_per_target,
                max_rules_per_target=args.max_rules_per_target,
                semantic_demotion_scale=args.semantic_demotion_scale,
                include_variants=include_variants,
                allow_multiword_glosses=allow_multiword_glosses,
                pos_scoring_enabled=pos_scoring_enabled,
                pos_exact_match_bonus=args.pos_exact_match_bonus,
                pos_compatible_match_bonus=args.pos_compatible_match_bonus,
                score_weight_dict_priority=args.score_weight_dict_priority,
                score_weight_frequency_weight=args.score_weight_frequency_weight,
                score_weight_pos_match=args.score_weight_pos_match,
                score_weight_variant_penalty=args.score_weight_variant_penalty,
                score_weight_phrase_penalty=args.score_weight_phrase_penalty,
                score_weight_embedding=args.score_weight_embedding,
                reverse_check_enabled=reverse_check_enabled,
                reverse_check_match_bonus=args.reverse_check_match_bonus,
                reverse_check_near_bonus=args.reverse_check_near_bonus,
                reverse_check_near_rank_max=args.reverse_check_near_rank_max,
                reverse_check_far_hit_penalty=args.reverse_check_far_hit_penalty,
                reverse_check_miss_penalty=args.reverse_check_miss_penalty,
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
                translation_dict_path=freedict_de_en_path,
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
                translation_dict_path=freedict_de_en_path,
                freedict_de_en_path=freedict_de_en_path,
                set_source_db=set_source_db,
                profile_id=args.profile_id or "default",
                set_top_n=args.set_top_n,
                feedback_window_size=args.feedback_window_size,
                max_active_items=args.max_active_items,
                max_new_items=args.max_new_items,
                allowed_pos=args.allowed_pos,
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


def cmd_profile_rulesets_get(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    payload = get_profile_rulesets_snapshot(paths, profile_id=args.profile_id)
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
    run.add_argument(
        "--set-top-n", type=int, help="Top-N seed cap (defaults from pair policy when omitted)."
    )
    run.add_argument(
        "--no-initialize-if-empty",
        action="store_true",
        help="Skip S initialization when store is empty",
    )
    run.add_argument(
        "--no-persist-store", action="store_true", help="Do not write changes to srs_store.json"
    )
    run.add_argument(
        "--no-persist-outputs", action="store_true", help="Do not write ruleset/snapshot JSON files"
    )
    run.add_argument(
        "--no-status-update", action="store_true", help="Do not update helper status file"
    )
    run.add_argument(
        "--confidence-threshold",
        type=float,
        help="Override confidence threshold (defaults from pair tuning when omitted).",
    )
    run.add_argument(
        "--max-definitions-per-target",
        type=int,
        help=(
            "Top-K definitions retained per target before optional rule-count cap "
            "(defaults from pair tuning; pass 0 to disable)."
        ),
    )
    run.add_argument(
        "--max-rules-per-target",
        type=int,
        help=(
            "Optional final cap on emitted rules per target (includes variants). "
            "Defaults from pair tuning; pass 0 to disable."
        ),
    )
    run.add_argument(
        "--semantic-demotion-scale",
        type=float,
        help=(
            "Scale for metadata-driven semantic/polysemy demotion during definition ranking "
            "(defaults from pair tuning; 0 disables, 1 uses base penalties)."
        ),
    )
    variants_group = run.add_mutually_exclusive_group()
    variants_group.add_argument(
        "--include-variants",
        action="store_true",
        help="Force-enable variant expansion regardless of pair tuning defaults.",
    )
    variants_group.add_argument(
        "--no-include-variants",
        action="store_true",
        help="Force-disable variant expansion regardless of pair tuning defaults.",
    )
    multiword_gloss_group = run.add_mutually_exclusive_group()
    multiword_gloss_group.add_argument(
        "--allow-multiword-glosses",
        action="store_true",
        help="Allow dictionary glosses containing whitespace to emit rules.",
    )
    multiword_gloss_group.add_argument(
        "--disallow-multiword-glosses",
        action="store_true",
        help="Filter dictionary glosses containing whitespace.",
    )
    pos_scoring_group = run.add_mutually_exclusive_group()
    pos_scoring_group.add_argument(
        "--enable-pos-scoring",
        action="store_true",
        help="Force-enable POS congruence contribution to confidence scoring.",
    )
    pos_scoring_group.add_argument(
        "--disable-pos-scoring",
        action="store_true",
        help="Force-disable POS congruence contribution to confidence scoring.",
    )
    reverse_check_group = run.add_mutually_exclusive_group()
    reverse_check_group.add_argument(
        "--enable-reverse-check",
        action="store_true",
        help="Force-enable reverse dictionary consistency ranking adjustments.",
    )
    reverse_check_group.add_argument(
        "--disable-reverse-check",
        action="store_true",
        help="Force-disable reverse dictionary consistency ranking adjustments.",
    )
    run.add_argument(
        "--pos-exact-match-bonus",
        type=float,
        help="Override POS exact-match bonus (defaults from pair tuning).",
    )
    run.add_argument(
        "--pos-compatible-match-bonus",
        type=float,
        help="Override POS compatibility-class bonus (defaults from pair tuning).",
    )
    run.add_argument(
        "--score-weight-dict-priority",
        type=float,
        help="Override dictionary-priority score weight (defaults from pair tuning).",
    )
    run.add_argument(
        "--score-weight-frequency-weight",
        type=float,
        help="Override frequency score weight (defaults from pair tuning).",
    )
    run.add_argument(
        "--score-weight-pos-match",
        type=float,
        help="Override POS score weight (defaults from pair tuning).",
    )
    run.add_argument(
        "--score-weight-variant-penalty",
        type=float,
        help="Override variant penalty weight (defaults from pair tuning).",
    )
    run.add_argument(
        "--score-weight-phrase-penalty",
        type=float,
        help="Override phrase penalty weight (defaults from pair tuning).",
    )
    run.add_argument(
        "--score-weight-embedding",
        type=float,
        help="Override embedding score weight (defaults from pair tuning).",
    )
    run.add_argument(
        "--reverse-check-match-bonus",
        type=float,
        help="Override reverse-check rank-0 bonus (defaults from pair tuning).",
    )
    run.add_argument(
        "--reverse-check-near-bonus",
        type=float,
        help="Override reverse-check near-rank bonus (defaults from pair tuning).",
    )
    run.add_argument(
        "--reverse-check-near-rank-max",
        type=int,
        help="Override max reverse rank treated as near match (defaults from pair tuning).",
    )
    run.add_argument(
        "--reverse-check-far-hit-penalty",
        type=float,
        help="Override reverse-check penalty for hits beyond the near-rank window (defaults from pair tuning).",
    )
    run.add_argument(
        "--reverse-check-miss-penalty",
        type=float,
        help="Override reverse-check miss penalty (defaults from pair tuning).",
    )
    run.add_argument("--snapshot-targets", type=int, default=50)
    run.add_argument("--snapshot-sources", type=int, default=6)
    run.add_argument(
        "--sample-count", type=int, help="Sample N target lemmas from current S before rulegen."
    )
    run.add_argument(
        "--sample-strategy",
        choices=("weighted_priority", "uniform"),
        help="Sampling strategy used with --sample-count.",
    )
    run.add_argument(
        "--sample-seed", type=int, help="Optional RNG seed for deterministic sampling."
    )
    run.set_defaults(func=cmd_run_rulegen)

    init_s = sub.add_parser("init_srs_set", help="Initialize S for a language pair")
    init_s.add_argument("--pair", default="en-ja")
    init_s.add_argument("--profile-id", help="Profile id (default: default)")
    init_s.add_argument("--jmdict", help="Path to JMdict_e folder")
    init_s.add_argument("--freedict-de-en", help="Path to FreeDict DE->EN TEI file (deu-eng.tei)")
    init_s.add_argument("--set-source-db", help="Path to frequency SQLite used to initialize S")
    init_s.add_argument(
        "--set-top-n",
        type=int,
        help="Bootstrap top-N cap (defaults from pair policy when omitted).",
    )
    init_s.add_argument(
        "--replace-pair",
        action="store_true",
        help="Replace existing pair entries before initializing S",
    )
    init_s.add_argument(
        "--bootstrap-top-n",
        type=int,
        help="Explicit bootstrap size for S (preferred over --set-top-n).",
    )
    init_s.add_argument(
        "--initial-active-count", type=int, help="Initial active subset size within bootstrap S."
    )
    init_s.add_argument(
        "--max-active-items-hint", type=int, help="Hint for active workload cap during planning."
    )
    init_s.add_argument("--strategy", default="frequency_bootstrap")
    init_s.add_argument("--objective", default="bootstrap")
    init_s.add_argument("--trigger", default="cli")
    init_s.add_argument("--profile-context-json", help="JSON object with profile context signals")
    init_s.set_defaults(func=cmd_init_srs_set)

    plan_s = sub.add_parser(
        "plan_srs_set", help="Build a set planning decision without mutating store"
    )
    plan_s.add_argument("--pair", default="en-ja")
    plan_s.add_argument("--profile-id", help="Profile id (default: default)")
    plan_s.add_argument("--strategy", default="profile_bootstrap")
    plan_s.add_argument("--objective", default="bootstrap")
    plan_s.add_argument(
        "--set-top-n",
        type=int,
        help="Bootstrap top-N cap (defaults from pair policy when omitted).",
    )
    plan_s.add_argument(
        "--bootstrap-top-n",
        type=int,
        help="Explicit bootstrap size for S (preferred over --set-top-n).",
    )
    plan_s.add_argument(
        "--initial-active-count", type=int, help="Initial active subset size within bootstrap S."
    )
    plan_s.add_argument(
        "--max-active-items-hint", type=int, help="Hint for active workload cap during planning."
    )
    plan_s.add_argument("--replace-pair", action="store_true")
    plan_s.add_argument("--trigger", default="cli")
    plan_s.add_argument("--profile-context-json", help="JSON object with profile context signals")
    plan_s.set_defaults(func=cmd_plan_srs_set)

    refresh_s = sub.add_parser("refresh_srs_set", help="Apply feedback-driven admission refresh")
    refresh_s.add_argument("--pair", default="en-ja")
    refresh_s.add_argument("--profile-id", help="Profile id (default: default)")
    refresh_s.add_argument("--jmdict", help="Path to JMdict_e folder")
    refresh_s.add_argument(
        "--freedict-de-en", help="Path to FreeDict DE->EN TEI file (deu-eng.tei)"
    )
    refresh_s.add_argument(
        "--set-source-db", help="Path to frequency SQLite used for candidate pool"
    )
    refresh_s.add_argument(
        "--set-top-n",
        type=int,
        help="Refresh candidate pool size (defaults from pair policy when omitted).",
    )
    refresh_s.add_argument(
        "--feedback-window-size",
        type=int,
        help="Feedback window size (defaults from pair policy when omitted).",
    )
    refresh_s.add_argument(
        "--max-active-items", type=int, help="Override max active items for refresh planning."
    )
    refresh_s.add_argument(
        "--max-new-items", type=int, help="Override max new items/day for refresh planning."
    )
    refresh_s.add_argument(
        "--allowed-pos",
        nargs="+",
        help="Optional POS bucket allow-list for admission (e.g. noun adjective verb).",
    )
    refresh_s.add_argument(
        "--no-persist-store", action="store_true", help="Do not write changes to srs_store.json"
    )
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

    profiles_get = sub.add_parser(
        "profiles_get", help="Show helper profile snapshot from settings.json"
    )
    profiles_get.set_defaults(func=cmd_profiles_get)

    profile_rulesets_get = sub.add_parser(
        "profile_rulesets_get",
        help="Show manual rulesets for a profile from settings.json",
    )
    profile_rulesets_get.add_argument(
        "--profile-id", help="Profile id (default: resolved active profile)"
    )
    profile_rulesets_get.set_defaults(func=cmd_profile_rulesets_get)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
