from __future__ import annotations

import argparse
import sys
from typing import Callable

from lexishift_core.helper.engine import (
    SrsRebalanceJobConfig,
    SetAdmissionPreviewJobConfig,
    apply_srs_rebalance,
    plan_srs_rebalance,
    preview_srs_admission,
)
from lexishift_core.helper.paths import build_helper_paths


def register_srs_preview_and_rebalance_commands(
    subparsers,
    *,
    print_json_fn: Callable[[object], None],
    load_optional_json_fn: Callable[[str | None], dict | None],
    resolve_pair_resource_paths_fn: Callable[..., tuple[object, object, object]],
) -> None:
    def cmd_preview_srs_admission(args: argparse.Namespace) -> int:
        paths = build_helper_paths()
        jmdict_path, _translation_dict_path, set_source_db = resolve_pair_resource_paths_fn(
            paths,
            pair=args.pair,
            jmdict_arg=args.jmdict,
            translation_dict_arg=None,
            set_source_db_arg=args.set_source_db,
        )
        try:
            profile_context = load_optional_json_fn(args.profile_context_json)
            payload = preview_srs_admission(
                paths,
                config=SetAdmissionPreviewJobConfig(
                    pair=args.pair,
                    jmdict_path=jmdict_path,
                    set_source_db=set_source_db,
                    profile_id=args.profile_id or "default",
                    strategy=args.strategy,
                    objective=args.objective,
                    set_top_n=args.set_top_n,
                    bootstrap_top_n=args.bootstrap_top_n,
                    initial_active_count=args.initial_active_count,
                    max_active_items_hint=args.max_active_items_hint,
                    preview_count=args.preview_count,
                    preview_sampling_mode=args.preview_sampling_mode,
                    preview_seed=args.preview_seed,
                    profile_context=profile_context,
                    trigger=args.trigger,
                ),
            )
            print_json_fn(payload)
            return 0
        except Exception as exc:  # noqa: BLE001
            print(str(exc), file=sys.stderr)
            return 1

    def cmd_plan_srs_rebalance(args: argparse.Namespace) -> int:
        paths = build_helper_paths()
        jmdict_path, translation_dict_path, set_source_db = resolve_pair_resource_paths_fn(
            paths,
            pair=args.pair,
            jmdict_arg=args.jmdict,
            translation_dict_arg=args.translation_dict,
            set_source_db_arg=args.set_source_db,
        )
        try:
            profile_context = load_optional_json_fn(args.profile_context_json)
            payload = plan_srs_rebalance(
                paths,
                config=SrsRebalanceJobConfig(
                    pair=args.pair,
                    jmdict_path=jmdict_path,
                    translation_dict_path=translation_dict_path,
                    set_source_db=set_source_db,
                    profile_id=args.profile_id or "default",
                    strategy=args.strategy,
                    objective=args.objective,
                    set_top_n=args.set_top_n,
                    max_active_items=args.max_active_items,
                    profile_context=profile_context,
                    trigger=args.trigger,
                ),
            )
            print_json_fn(payload)
            return 0
        except Exception as exc:  # noqa: BLE001
            print(str(exc), file=sys.stderr)
            return 1

    def cmd_apply_srs_rebalance(args: argparse.Namespace) -> int:
        paths = build_helper_paths()
        jmdict_path, translation_dict_path, set_source_db = resolve_pair_resource_paths_fn(
            paths,
            pair=args.pair,
            jmdict_arg=args.jmdict,
            translation_dict_arg=args.translation_dict,
            set_source_db_arg=args.set_source_db,
        )
        try:
            profile_context = load_optional_json_fn(args.profile_context_json)
            payload = apply_srs_rebalance(
                paths,
                config=SrsRebalanceJobConfig(
                    pair=args.pair,
                    jmdict_path=jmdict_path,
                    translation_dict_path=translation_dict_path,
                    set_source_db=set_source_db,
                    profile_id=args.profile_id or "default",
                    strategy=args.strategy,
                    objective=args.objective,
                    set_top_n=args.set_top_n,
                    max_active_items=args.max_active_items,
                    profile_context=profile_context,
                    trigger=args.trigger,
                ),
            )
            print_json_fn(payload)
            return 0
        except Exception as exc:  # noqa: BLE001
            print(str(exc), file=sys.stderr)
            return 1

    preview_s = subparsers.add_parser(
        "preview_srs_admission",
        help="Preview profile-aware bootstrap admissions without mutating store",
    )
    preview_s.add_argument("--pair", default="en-ja")
    preview_s.add_argument("--profile-id", help="Profile id (default: default)")
    preview_s.add_argument("--jmdict", help="Path to JMdict_e folder used for seed/bootstrap.")
    preview_s.add_argument(
        "--set-source-db", help="Path to frequency SQLite used for candidate pool"
    )
    preview_s.add_argument(
        "--set-top-n",
        type=int,
        help="Bootstrap top-N cap (defaults from pair policy when omitted).",
    )
    preview_s.add_argument(
        "--bootstrap-top-n",
        type=int,
        help="Explicit bootstrap size for S (preferred over --set-top-n).",
    )
    preview_s.add_argument(
        "--initial-active-count",
        type=int,
        help="Initial active subset size within bootstrap S.",
    )
    preview_s.add_argument(
        "--max-active-items-hint",
        type=int,
        help="Hint for active workload cap during planning.",
    )
    preview_s.add_argument(
        "--preview-count",
        type=int,
        help="How many admitted words to include in the sample output.",
    )
    preview_s.add_argument(
        "--preview-sampling-mode",
        choices=("ranked", "weighted_without_replacement"),
        help="Preview selection mode for the returned sample.",
    )
    preview_s.add_argument(
        "--preview-seed",
        type=int,
        help="Optional sampling seed for weighted preview mode.",
    )
    preview_s.add_argument("--strategy", default="profile_bootstrap")
    preview_s.add_argument("--objective", default="bootstrap")
    preview_s.add_argument("--trigger", default="cli")
    preview_s.add_argument(
        "--profile-context-json", help="JSON object with profile context signals"
    )
    preview_s.set_defaults(func=cmd_preview_srs_admission)

    rebalance_plan = subparsers.add_parser(
        "plan_srs_rebalance",
        help="Preview inventory-aware rebalance decisions without mutating store",
    )
    rebalance_plan.add_argument("--pair", default="en-ja")
    rebalance_plan.add_argument("--profile-id", help="Profile id (default: default)")
    rebalance_plan.add_argument("--jmdict", help="Path to JMdict_e folder used for seed/bootstrap.")
    rebalance_plan.add_argument(
        "--translation-dict",
        help="Optional translation dictionary override for the follow-up rulegen step.",
    )
    rebalance_plan.add_argument(
        "--set-source-db",
        help="Path to frequency SQLite used for candidate pool",
    )
    rebalance_plan.add_argument(
        "--set-top-n",
        type=int,
        help="Candidate pool size used to build rebalance contenders.",
    )
    rebalance_plan.add_argument(
        "--max-active-items",
        type=int,
        help="Override max active items for the rebalance budget.",
    )
    rebalance_plan.add_argument("--strategy", default="profile_growth")
    rebalance_plan.add_argument("--objective", default="rebalance")
    rebalance_plan.add_argument("--trigger", default="cli")
    rebalance_plan.add_argument(
        "--profile-context-json",
        help="JSON object with profile context signals",
    )
    rebalance_plan.set_defaults(func=cmd_plan_srs_rebalance)

    rebalance_apply = subparsers.add_parser(
        "apply_srs_rebalance",
        help="Apply inventory-aware rebalance and republish helper artifacts",
    )
    rebalance_apply.add_argument("--pair", default="en-ja")
    rebalance_apply.add_argument("--profile-id", help="Profile id (default: default)")
    rebalance_apply.add_argument(
        "--jmdict", help="Path to JMdict_e folder used for seed/bootstrap."
    )
    rebalance_apply.add_argument(
        "--translation-dict",
        help="Optional translation dictionary override for the follow-up rulegen step.",
    )
    rebalance_apply.add_argument(
        "--set-source-db",
        help="Path to frequency SQLite used for candidate pool",
    )
    rebalance_apply.add_argument(
        "--set-top-n",
        type=int,
        help="Candidate pool size used to build rebalance contenders.",
    )
    rebalance_apply.add_argument(
        "--max-active-items",
        type=int,
        help="Override max active items for the rebalance budget.",
    )
    rebalance_apply.add_argument("--strategy", default="profile_growth")
    rebalance_apply.add_argument("--objective", default="rebalance")
    rebalance_apply.add_argument("--trigger", default="cli")
    rebalance_apply.add_argument(
        "--profile-context-json",
        help="JSON object with profile context signals",
    )
    rebalance_apply.set_defaults(func=cmd_apply_srs_rebalance)
