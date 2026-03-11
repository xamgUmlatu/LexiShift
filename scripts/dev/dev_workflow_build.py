#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run(command: list[str]) -> int:
    print(f"+ {shlex.join(command)}", flush=True)
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    return int(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run local build safeties for repo surfaces that already have stable build paths."
        )
    )
    parser.add_argument(
        "--skip-bd",
        action="store_true",
        help="Skip BetterDiscord plugin build.",
    )
    parser.add_argument(
        "--skip-gui",
        action="store_true",
        help="Skip GUI PyInstaller build + validate.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional JSON report output path.",
    )
    args = parser.parse_args()

    commands: list[tuple[str, list[str]]] = []
    if not args.skip_bd:
        commands.append(
            ("betterdiscord_build", ["node", "apps/betterdiscord-plugin/build_plugin.js"])
        )
    if not args.skip_gui:
        commands.append(
            ("gui_build_validate", [sys.executable, "scripts/build/gui_app.py", "--validate"])
        )

    results: list[dict[str, object]] = []
    overall_exit_code = 0
    for label, command in commands:
        exit_code = _run(command)
        results.append(
            {
                "label": label,
                "command": command,
                "exit_code": exit_code,
            }
        )
        if exit_code != 0:
            overall_exit_code = exit_code
            break

    payload = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall_exit_code": overall_exit_code,
        "skip_bd": bool(args.skip_bd),
        "skip_gui": bool(args.skip_gui),
        "commands": results,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"json_out: {args.json_out}")

    if overall_exit_code != 0:
        raise SystemExit(overall_exit_code)


if __name__ == "__main__":
    main()
