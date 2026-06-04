#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time
from typing import Any
import uuid


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "core"))
from lexishift_core.helper.gui_startup_telemetry import (  # noqa: E402
    STARTUP_LAUNCH_MODE_ENV,
    STARTUP_LOG_PATH_ENV,
    STARTUP_REQUESTED_AT_ENV,
    STARTUP_RESOURCE_PAIR_ENV,
    STARTUP_SESSION_ID_ENV,
    STARTUP_SOURCE_ENV,
    utc_timestamp,
)

TOTAL_RE = re.compile(r"total ([0-9.]+) ms")
SINCE_REQUEST_RE = re.compile(r"since_request_ms=([0-9.]+)")


def _platform_data_root() -> Path:
    override = str(os.environ.get("LEXISHIFT_DATA_DIR", "") or "").strip()
    if override:
        return Path(override).expanduser()
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(home / "AppData" / "Roaming")
        return Path(base) / "LexiShift" / "LexiShift"
    return home / ".local" / "share" / "LexiShift" / "LexiShift"


def _default_startup_log_path(data_root: Path | None = None) -> Path:
    return (data_root or _platform_data_root()) / "startup_timing.log"


def _build_launch_command(app: Path, *, launch_mode: str, pair: str) -> list[str]:
    args = ["--open-resource-settings", "--resource-pair", pair]
    if launch_mode == "open":
        return ["open", str(app), "--args", *args]
    if launch_mode == "bundle-id":
        return ["open", "-b", "com.lexishift.app", "--args", *args]
    if launch_mode == "direct":
        executable = app / "Contents" / "MacOS" / "LexiShift"
        return [str(executable), *args]
    raise ValueError(f"Unsupported launch mode for subprocess launch: {launch_mode}")


def _startup_env(
    *,
    session_id: str,
    requested_at: str,
    launch_mode: str,
    pair: str,
    startup_log_path: Path,
) -> dict[str, str]:
    env = dict(os.environ)
    env[STARTUP_SESSION_ID_ENV] = session_id
    env[STARTUP_REQUESTED_AT_ENV] = requested_at
    env[STARTUP_SOURCE_ENV] = f"startup_measure_{launch_mode}"
    env[STARTUP_LAUNCH_MODE_ENV] = launch_mode
    env[STARTUP_RESOURCE_PAIR_ENV] = pair
    env[STARTUP_LOG_PATH_ENV] = str(startup_log_path)
    return env


def _wait_for_log_line(
    *,
    startup_log_path: Path,
    session_id: str,
    marker: str,
    timeout_seconds: float,
) -> str | None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            text = startup_log_path.read_text(encoding="utf-8")
        except OSError:
            time.sleep(0.1)
            continue
        for line in reversed(text.splitlines()):
            if f"session={session_id}" in line and marker in line:
                return line
        time.sleep(0.1)
    return None


def _extract_float(pattern: re.Pattern[str], text: str | None) -> float | None:
    if not text:
        return None
    match = pattern.search(text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _activate_existing_gui(*, pair: str, session_id: str) -> bool:
    sys.path.insert(0, str(REPO_ROOT / "core"))
    from lexishift_core.helper.gui_activation import activate_resource_settings

    return activate_resource_settings(pair=pair, session_id=session_id)


def _run_one(args: argparse.Namespace, *, index: int) -> dict[str, Any]:
    session_id = uuid.uuid4().hex
    requested_at = utc_timestamp()
    startup_log_path = (
        Path(args.startup_log).expanduser()
        if args.startup_log
        else (
            _default_startup_log_path(Path(args.data_root).expanduser())
            if args.data_root
            else _default_startup_log_path()
        )
    )
    startup_log_path.parent.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()
    line: str | None
    process_pid: int | None = None
    activated: bool | None = None
    command: list[str] = []
    if args.launch_mode == "activation":
        activated = _activate_existing_gui(pair=args.pair, session_id=session_id)
        line = _wait_for_log_line(
            startup_log_path=startup_log_path,
            session_id=session_id,
            marker="activation received",
            timeout_seconds=args.timeout,
        )
    else:
        command = _build_launch_command(
            Path(args.app).expanduser(), launch_mode=args.launch_mode, pair=args.pair
        )
        env = _startup_env(
            session_id=session_id,
            requested_at=requested_at,
            launch_mode=args.launch_mode,
            pair=args.pair,
            startup_log_path=startup_log_path,
        )
        process = subprocess.Popen(
            command,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        process_pid = process.pid
        line = _wait_for_log_line(
            startup_log_path=startup_log_path,
            session_id=session_id,
            marker="window shown",
            timeout_seconds=args.timeout,
        )
        if (
            args.terminate_direct_process
            and args.launch_mode == "direct"
            and process.poll() is None
        ):
            process.terminate()

    observed_elapsed_ms = (time.perf_counter() - start) * 1000.0
    status = "ok" if line else "timeout"
    if args.launch_mode == "activation" and activated is False:
        status = "activation_unavailable"
    activation_mode = args.launch_mode == "activation"
    since_request_ms = None if activation_mode else _extract_float(SINCE_REQUEST_RE, line)
    startup_total_ms = None if activation_mode else _extract_float(TOTAL_RE, line)
    pre_entry_ms = None
    if since_request_ms is not None and startup_total_ms is not None:
        pre_entry_ms = round(max(0.0, since_request_ms - startup_total_ms), 1)
    return {
        "index": index,
        "status": status,
        "session_id": session_id,
        "requested_at": requested_at,
        "launch_mode": args.launch_mode,
        "pair": args.pair,
        "command": command,
        "process_pid": process_pid,
        "activated": activated,
        "observed_elapsed_ms": round(observed_elapsed_ms, 1),
        "startup_total_ms": startup_total_ms,
        "since_request_ms": since_request_ms,
        "pre_entry_ms": pre_entry_ms,
        "matched_line": line,
    }


def _metric_summary(values: list[float]) -> dict[str, float | int] | None:
    if not values:
        return None
    return {
        "count": len(values),
        "min_ms": round(min(values), 1),
        "median_ms": round(statistics.median(values), 1),
        "max_ms": round(max(values), 1),
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok_values = [
        float(
            row["observed_elapsed_ms"]
            if row.get("launch_mode") == "activation"
            else row["since_request_ms"] or row["observed_elapsed_ms"]
        )
        for row in rows
        if row.get("status") == "ok"
    ]
    if not ok_values:
        return {"ok_count": 0, "timeout_count": len(rows)}
    return {
        "ok_count": len(ok_values),
        "timeout_count": len(rows) - len(ok_values),
        "min_ms": round(min(ok_values), 1),
        "median_ms": round(statistics.median(ok_values), 1),
        "max_ms": round(max(ok_values), 1),
        "pre_entry": _metric_summary(
            [float(row["pre_entry_ms"]) for row in rows if row.get("pre_entry_ms") is not None]
        ),
        "process_entry_to_window": _metric_summary(
            [
                float(row["startup_total_ms"])
                for row in rows
                if row.get("startup_total_ms") is not None
            ]
        ),
    }


def _write_json(path: str | None, payload: dict[str, Any]) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _markdown(payload: dict[str, Any]) -> str:
    def cell(value: Any) -> Any:
        return "" if value is None else value

    lines = [
        "# Packaged GUI Startup Measurement",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- app: `{payload['app']}`",
        f"- pair: `{payload['pair']}`",
        f"- launch_mode: `{payload['launch_mode']}`",
        f"- summary: `{payload['summary']}`",
        "",
        "| Run | Status | Session | Since request ms | Pre-entry ms | Startup total ms | Observed ms |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["runs"]:
        lines.append(
            "| "
            f"{row['index']} | {row['status']} | `{row['session_id']}` | "
            f"{cell(row.get('since_request_ms'))} | {cell(row.get('pre_entry_ms'))} | "
            f"{cell(row.get('startup_total_ms'))} | {row['observed_elapsed_ms']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _write_markdown(path: str | None, payload: dict[str, Any]) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_markdown(payload), encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Measure packaged LexiShift GUI startup.")
    parser.add_argument("--app", default="/Applications/LexiShift.app")
    parser.add_argument("--pair", default="en-es")
    parser.add_argument(
        "--launch-mode",
        choices=("open", "bundle-id", "direct", "activation"),
        default="open",
    )
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--data-root", default="")
    parser.add_argument("--startup-log", default="")
    parser.add_argument("--json-out", default="")
    parser.add_argument("--markdown-out", default="")
    parser.add_argument(
        "--terminate-direct-process",
        action="store_true",
        help="Terminate the directly launched process after a successful direct-mode measurement.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.repetitions < 1:
        parser.error("--repetitions must be at least 1")
    runs = [_run_one(args, index=index + 1) for index in range(args.repetitions)]
    payload = {
        "generated_at": utc_timestamp(),
        "app": args.app,
        "pair": args.pair,
        "launch_mode": args.launch_mode,
        "repetitions": args.repetitions,
        "summary": _summary(runs),
        "runs": runs,
    }
    _write_json(args.json_out, payload)
    _write_markdown(args.markdown_out, payload)
    print(json.dumps(payload["summary"], ensure_ascii=False))
    return 0 if all(row["status"] == "ok" for row in runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
