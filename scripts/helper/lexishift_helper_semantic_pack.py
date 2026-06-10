from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from lexishift_core.helper.paths import build_helper_paths
from lexishift_core.helper.use_cases.semantic_pack_install import (
    DEFAULT_PACK_ID,
    SemanticPackInstallConfig,
    install_semantic_pack,
)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def cmd_install_semantic_pack(args: argparse.Namespace) -> int:
    if not args.data_root and not args.allow_default_data_root:
        print(
            "install_semantic_pack requires --data-root for now, or "
            "--allow-default-data-root to target the platform default.",
            file=sys.stderr,
        )
        return 2
    paths = build_helper_paths(Path(args.data_root) if args.data_root else None)
    try:
        payload = install_semantic_pack(
            paths,
            config=SemanticPackInstallConfig(
                pair=args.pair,
                profile_id=args.profile_id or "default",
                semantic_inventory_path=args.semantic_inventory,
                pack_id=args.pack_id,
                generated_at=args.generated_at,
                copy_pack=not args.no_pack_copy,
                copy_only=args.copy_only,
                dry_run=args.dry_run,
                rule_source=args.rule_source,
                rule_source_type=args.rule_source_type,
            ),
        )
        _print_json(payload)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1


def register_install_semantic_pack_command(subparsers: argparse._SubParsersAction) -> None:
    install_semantic = subparsers.add_parser(
        "install_semantic_pack",
        help="Materialize a semantic inventory pack into a local helper profile",
    )
    install_semantic.add_argument("--pair", default="en-es")
    install_semantic.add_argument("--profile-id", help="Profile id (default: default)")
    install_semantic.add_argument(
        "--semantic-inventory",
        type=Path,
        help=(
            "Optional compiled semantic inventory JSON override. "
            "When omitted, the helper resolves --pack-id from an installed pack copy, "
            "semantic-pack catalog, or current repo dev pack."
        ),
    )
    install_semantic.add_argument(
        "--pack-id",
        default=DEFAULT_PACK_ID,
        help="Stable local pack id used under language_packs/<pair>/semantic_packs/.",
    )
    install_semantic.add_argument(
        "--data-root",
        type=Path,
        help=("Explicit LexiShift data root. Required unless --allow-default-data-root is set."),
    )
    install_semantic.add_argument(
        "--allow-default-data-root",
        action="store_true",
        help="Allow writing to the platform default or LEXISHIFT_DATA_DIR data root.",
    )
    install_semantic.add_argument(
        "--generated-at",
        default="",
        help="Optional generation timestamp override for deterministic tests.",
    )
    install_semantic.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview paths without writing profile artifacts.",
    )
    install_semantic.add_argument(
        "--no-pack-copy",
        action="store_true",
        help="Do not copy the semantic pack into language_packs before materialization.",
    )
    install_semantic.add_argument(
        "--copy-only",
        action="store_true",
        help="Copy the semantic pack into language_packs without overwriting profile artifacts.",
    )
    install_semantic.add_argument("--rule-source", default="semantic_pack_install")
    install_semantic.add_argument("--rule-source-type", default="semantic_veto_candidate")
    install_semantic.set_defaults(func=cmd_install_semantic_pack)
