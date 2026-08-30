#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import signal
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
PID_RE = re.compile(r"(?:^| )pid=([0-9]+)(?: |$)")
STARTUP_LINE_RE = re.compile(
    r"^\[startup\] (?P<label>.*?) \(\+(?P<delta_ms>[0-9.]+) ms, "
    r"total (?P<total_ms>[0-9.]+) ms\)"
)


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
    session_field: str = "session",
) -> str | None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            text = startup_log_path.read_text(encoding="utf-8")
        except OSError:
            time.sleep(0.1)
            continue
        for line in reversed(text.splitlines()):
            if f"{session_field}={session_id}" in line and marker in line:
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


def _extract_int(pattern: re.Pattern[str], text: str | None) -> int | None:
    if not text:
        return None
    match = pattern.search(text)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _terminate_started_app(app_pid: int, *, timeout_seconds: float = 5.0) -> str:
    try:
        os.kill(app_pid, signal.SIGTERM)
    except ProcessLookupError:
        return "already_exited"
    except OSError as exc:
        return f"error:{exc}"

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            os.kill(app_pid, 0)
        except ProcessLookupError:
            return "terminated"
        except OSError as exc:
            return f"error:{exc}"
        time.sleep(0.05)
    return "timeout"


def _session_checkpoint_rows(
    *,
    startup_log_path: Path,
    session_id: str,
    session_field: str = "session",
) -> list[dict[str, Any]]:
    try:
        text = startup_log_path.read_text(encoding="utf-8")
    except OSError:
        return []
    session_marker = f" {session_field}={session_id} "
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if session_marker not in f"{line} ":
            continue
        match = STARTUP_LINE_RE.search(line)
        if match is None:
            continue
        label = match.group("label")
        if session_field == "activation_session":
            label = label.partition(" activation_session=")[0]
        rows.append(
            {
                "label": label,
                "delta_ms": float(match.group("delta_ms")),
                "total_ms": float(match.group("total_ms")),
                "since_request_ms": _extract_float(SINCE_REQUEST_RE, line),
            }
        )
    return rows


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
    process: subprocess.Popen[bytes] | None = None
    if args.launch_mode == "activation":
        activated = _activate_existing_gui(pair=args.pair, session_id=session_id)
        line = _wait_for_log_line(
            startup_log_path=startup_log_path,
            session_id=session_id,
            marker=args.ready_marker,
            timeout_seconds=args.timeout,
            session_field="activation_session",
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
            marker=args.ready_marker,
            timeout_seconds=args.timeout,
        )

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
    checkpoints = _session_checkpoint_rows(
        startup_log_path=startup_log_path,
        session_id=session_id,
        session_field="activation_session" if activation_mode else "session",
    )
    app_pid = _extract_int(PID_RE, line)
    cleanup_status = "not_requested"
    should_terminate = args.terminate_launched_app or (
        args.terminate_direct_process and args.launch_mode == "direct"
    )
    if not activation_mode and should_terminate:
        if app_pid is not None:
            cleanup_status = _terminate_started_app(app_pid)
        elif process is not None and process.poll() is None:
            process.terminate()
            cleanup_status = "launcher_terminated"
        else:
            cleanup_status = "app_pid_unavailable"
    return {
        "index": index,
        "status": status,
        "session_id": session_id,
        "requested_at": requested_at,
        "launch_mode": args.launch_mode,
        "pair": args.pair,
        "ready_marker": args.ready_marker,
        "command": command,
        "process_pid": process_pid,
        "app_pid": app_pid,
        "cleanup_status": cleanup_status,
        "activated": activated,
        "observed_elapsed_ms": round(observed_elapsed_ms, 1),
        "startup_total_ms": startup_total_ms,
        "since_request_ms": since_request_ms,
        "pre_entry_ms": pre_entry_ms,
        "checkpoint_count": len(checkpoints),
        "checkpoints": checkpoints,
        "matched_line": line,
    }


def _metric_summary(values: list[float]) -> dict[str, float | int] | None:
    if not values:
        return None
    return {
        "count": len(values),
        "min_ms": round(min(values), 1),
        "median_ms": round(statistics.median(values), 1),
        "p95_ms": round(_percentile(values, 0.95), 1),
        "max_ms": round(max(values), 1),
    }


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    weight = position - lower_index
    return ordered[lower_index] * (1.0 - weight) + ordered[upper_index] * weight


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
        "p95_ms": round(_percentile(ok_values, 0.95), 1),
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


def _budget_failures(summary: dict[str, Any], args: argparse.Namespace) -> list[str]:
    failures: list[str] = []
    if summary.get("ok_count", 0) != args.repetitions:
        failures.append("not all repetitions reached the ready marker")
    median_ms = summary.get("median_ms")
    if args.max_median_ms is not None and (
        median_ms is None or float(median_ms) > args.max_median_ms
    ):
        failures.append(f"median {median_ms} ms exceeds {args.max_median_ms:.1f} ms")
    p95_ms = summary.get("p95_ms")
    if args.max_p95_ms is not None and (p95_ms is None or float(p95_ms) > args.max_p95_ms):
        failures.append(f"p95 {p95_ms} ms exceeds {args.max_p95_ms:.1f} ms")
    return failures


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
        f"- ready_marker: `{payload['ready_marker']}`",
        f"- summary: `{payload['summary']}`",
        f"- budget: `{payload['budget']}`",
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
    parser.add_argument(
        "--ready-marker",
        default="settings_dialog.shown",
        help="Startup checkpoint that marks a successful cold resource-settings launch.",
    )
    parser.add_argument("--json-out", default="")
    parser.add_argument("--markdown-out", default="")
    parser.add_argument(
        "--terminate-direct-process",
        action="store_true",
        help="Terminate the directly launched process after a successful direct-mode measurement.",
    )
    parser.add_argument(
        "--terminate-launched-app",
        action="store_true",
        help="Terminate only the app PID recorded for each measured cold-launch session.",
    )
    parser.add_argument("--max-median-ms", type=float)
    parser.add_argument("--max-p95-ms", type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.repetitions < 1:
        parser.error("--repetitions must be at least 1")
    runs = [_run_one(args, index=index + 1) for index in range(args.repetitions)]
    summary = _summary(runs)
    budget_failures = _budget_failures(summary, args)
    payload = {
        "generated_at": utc_timestamp(),
        "app": args.app,
        "pair": args.pair,
        "launch_mode": args.launch_mode,
        "ready_marker": args.ready_marker,
        "repetitions": args.repetitions,
        "summary": summary,
        "budget": {
            "max_median_ms": args.max_median_ms,
            "max_p95_ms": args.max_p95_ms,
            "passed": not budget_failures,
            "failures": budget_failures,
        },
        "runs": runs,
    }
    _write_json(args.json_out, payload)
    _write_markdown(args.markdown_out, payload)
    print(json.dumps({"summary": summary, "budget": payload["budget"]}, ensure_ascii=False))
    return 0 if not budget_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
