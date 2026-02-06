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
    RulegenJobConfig,
    apply_exposure,
    apply_feedback,
    load_snapshot,
    reset_srs_data,
    run_rulegen_job,
)
from lexishift_core.helper_paths import build_helper_paths
from lexishift_core.helper_status import load_status


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def cmd_status(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    status = load_status(paths.srs_status_path)
    _print_json(status.__dict__)
    return 0


def cmd_get_snapshot(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    try:
        payload = load_snapshot(paths, pair=args.pair)
    except FileNotFoundError:
        _print_json({"error": "snapshot_not_found", "path": str(paths.snapshot_path(args.pair))})
        return 1
    _print_json(payload)
    return 0


def cmd_run_rulegen(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    jmdict_path = Path(args.jmdict or (paths.language_packs_dir / "JMdict_e"))
    if not jmdict_path.exists():
        print(f"Missing JMDict path: {jmdict_path}", file=sys.stderr)
        return 2

    seed_db = Path(args.seed_db or (paths.frequency_packs_dir / "freq-ja-bccwj.sqlite"))

    try:
        payload = run_rulegen_job(
            paths,
            config=RulegenJobConfig(
                pair=args.pair,
                jmdict_path=jmdict_path,
                seed_db=seed_db if seed_db.exists() else None,
                seed_top_n=args.seed_top_n,
                confidence_threshold=args.confidence_threshold,
                snapshot_targets=args.snapshot_targets,
                snapshot_sources=args.snapshot_sources,
                seed_if_empty=not args.no_seed,
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
    )
    _print_json({"ok": True})
    return 0


def cmd_reset_srs(args: argparse.Namespace) -> int:
    paths = build_helper_paths()
    payload = reset_srs_data(paths, pair=args.pair)
    _print_json(payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LexiShift Helper CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show helper status")
    status.set_defaults(func=cmd_status)

    snapshot = sub.add_parser("get_snapshot", help="Print rulegen snapshot for a pair")
    snapshot.add_argument("--pair", default="en-ja")
    snapshot.set_defaults(func=cmd_get_snapshot)

    run = sub.add_parser("run_rulegen", help="Run rulegen for a language pair")
    run.add_argument("--pair", default="en-ja")
    run.add_argument("--jmdict", help="Path to JMdict_e folder")
    run.add_argument("--seed-db", help="Path to frequency SQLite for seeding (BCCWJ)")
    run.add_argument("--seed-top-n", type=int, default=2000)
    run.add_argument("--no-seed", action="store_true", help="Skip seeding when S is empty")
    run.add_argument("--confidence-threshold", type=float, default=0.0)
    run.add_argument("--snapshot-targets", type=int, default=50)
    run.add_argument("--snapshot-sources", type=int, default=6)
    run.set_defaults(func=cmd_run_rulegen)

    feedback = sub.add_parser("record_feedback", help="Record SRS feedback")
    feedback.add_argument("--pair", required=True)
    feedback.add_argument("--lemma", required=True)
    feedback.add_argument("--rating", required=True)
    feedback.add_argument("--source-type", default="extension")
    feedback.set_defaults(func=cmd_record_feedback)

    exposure = sub.add_parser("record_exposure", help="Record SRS exposure")
    exposure.add_argument("--pair", required=True)
    exposure.add_argument("--lemma", required=True)
    exposure.add_argument("--source-type", default="extension")
    exposure.set_defaults(func=cmd_record_exposure)

    reset = sub.add_parser("reset_srs", help="Reset SRS progress")
    reset.add_argument("--pair", help="Language pair to reset (omit to reset all).")
    reset.set_defaults(func=cmd_reset_srs)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
