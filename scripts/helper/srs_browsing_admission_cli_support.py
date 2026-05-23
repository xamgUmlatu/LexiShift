from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Callable

from lexishift_core.helper.engine import ingest_browsing_admission_signals
from lexishift_core.helper.paths import build_helper_paths


def register_browsing_admission_ingest_command(
    subparsers,
    *,
    print_json_fn: Callable[[object], None],
) -> None:
    def cmd_ingest_browsing_admission_signals(args: argparse.Namespace) -> int:
        paths = build_helper_paths()
        try:
            payload = _load_json_file(args.signals_json)
            pair, profile_id, captured_at, opt_in, signals = _resolve_payload(args, payload)
            if not pair:
                raise ValueError("Browsing admission ingest requires --pair or payload.pair.")
            if not isinstance(signals, list):
                raise ValueError("Browsing admission ingest requires a signals array.")
            result = ingest_browsing_admission_signals(
                paths,
                pair=pair,
                signals=signals,
                profile_id=profile_id,
                captured_at=captured_at,
                opt_in=opt_in,
            )
            print_json_fn(result)
            return 0
        except Exception as exc:  # noqa: BLE001
            print(str(exc), file=sys.stderr)
            return 1

    browsing_ingest = subparsers.add_parser(
        "ingest_browsing_admission_signals",
        help="Dev-only opt-in ingest for bounded browsing-admission lemma aggregates.",
    )
    browsing_ingest.add_argument("--pair", help="Language pair (or payload.pair).")
    browsing_ingest.add_argument("--profile-id", help="Profile id (default: default).")
    browsing_ingest.add_argument(
        "--signals-json",
        required=True,
        help="JSON object/list of signals.",
    )
    browsing_ingest.add_argument("--captured-at", help="Optional packet capture timestamp.")
    browsing_ingest.add_argument(
        "--opt-in",
        action="store_true",
        help="Persist browsing admission signals for this explicit dev ingest.",
    )
    browsing_ingest.set_defaults(func=cmd_ingest_browsing_admission_signals)


def _load_json_file(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _resolve_payload(
    args: argparse.Namespace,
    payload: object,
) -> tuple[str, str, str | None, bool, object]:
    if isinstance(payload, dict):
        pair = args.pair or str(payload.get("pair", "")).strip()
        profile_id = args.profile_id or str(payload.get("profile_id", "")).strip() or "default"
        captured_at = args.captured_at or str(payload.get("captured_at", "")).strip() or None
        opt_in = bool(args.opt_in or payload.get("opt_in") is True)
        opt_in = opt_in or payload.get("browsing_admission_enabled") is True
        return pair, profile_id, captured_at, opt_in, payload.get("signals")
    if isinstance(payload, list):
        return (
            args.pair or "",
            args.profile_id or "default",
            args.captured_at,
            bool(args.opt_in),
            payload,
        )
    raise ValueError("Browsing admission signal JSON must be an object or list.")
