#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_llm_prompt_bakeoff_en_es import (  # noqa: E402
    DEFAULT_BATCH_DIR,
    _build_batch_id,
    _display_path,
    _load_json,
    _resolve_default_summary_paths,
    _select_request_rows,
    _slug,
)
from semantic_llm_prompt_reporting import render_prompt_preflight_markdown  # noqa: E402
from semantic_llm_prompt_smoke import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_FAMILY_INVENTORY_JSON,
    DEFAULT_PROMPT_SPEC_JSON,
    DEFAULT_QUEUE_JSON,
    DEFAULT_SLOT_MANIFEST_JSON,
    build_prompt_smoke_report,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402

DEFAULT_PREFLIGHT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_preflight_latest.json"
)
DEFAULT_PREFLIGHT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_preflight_latest.md"
)
DEFAULT_SHELL_RC = Path.home() / ".zshrc"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a no-spend preflight over the frozen en-es prompt bakeoff slice and "
            "render the selected requests, planned artifact paths, and local environment readiness."
        )
    )
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--slot-manifest-json", type=Path, default=DEFAULT_SLOT_MANIFEST_JSON)
    parser.add_argument("--family-inventory-json", type=Path, default=DEFAULT_FAMILY_INVENTORY_JSON)
    parser.add_argument("--prompt-spec-json", type=Path, default=DEFAULT_PROMPT_SPEC_JSON)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--stage",
        choices=("proxy", "target"),
        default="proxy",
        help="Bakeoff stage to preview.",
    )
    parser.add_argument(
        "--request-id",
        action="append",
        default=[],
        help="Optional request_id filter. Repeat to preview only a subset of rendered requests.",
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=0,
        help="Optional cap on the number of rendered requests after filtering.",
    )
    parser.add_argument(
        "--shell-rc",
        type=Path,
        default=DEFAULT_SHELL_RC,
        help="Shell rc file to inspect for OPENAI_API_KEY export hints.",
    )
    parser.add_argument("--batch-dir", type=Path, default=DEFAULT_BATCH_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_PREFLIGHT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_PREFLIGHT_MARKDOWN_OUT)
    return parser.parse_args()


def build_prompt_preflight_report(
    *,
    queue_payload: Mapping[str, object],
    slot_manifest_payload: Mapping[str, object],
    family_inventory_payload: Mapping[str, object],
    prompt_spec_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    stage: str,
    batch_dir: Path,
    shell_rc: Path,
    request_ids: Sequence[str] | None = None,
    max_requests: int = 0,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )

    smoke_report = build_prompt_smoke_report(
        queue_payload=queue_payload,
        slot_manifest_payload=slot_manifest_payload,
        family_inventory_payload=family_inventory_payload,
        prompt_spec_payload=prompt_spec_payload,
        dataset_payload=dataset_payload,
        stage=stage,
        generated_at=generated_at,
    )
    selected_request_rows = _select_request_rows(
        smoke_report.get("request_rows"),
        request_ids=request_ids,
        max_requests=max_requests,
    )
    stage_defaults = prompt_spec_payload.get("stage_defaults")
    if not isinstance(stage_defaults, Mapping):
        raise ValueError("Prompt spec is missing `stage_defaults`.")
    stage_config = stage_defaults.get(stage)
    if not isinstance(stage_config, Mapping):
        raise ValueError(f"Prompt spec is missing stage defaults for {stage!r}.")

    batch_id = _build_batch_id(
        pair=str(smoke_report.get("pair") or "en-es"),
        stage=stage,
        generated_at=generated_at,
        execution_mode="live",
        run_id="<RUN_ID>",
    )
    batch_slug = _slug(batch_id)
    journal_path = batch_dir / f"{batch_slug}_journal.jsonl"
    raw_response_bundle_path = batch_dir / f"{batch_slug}_raw_responses.json"
    intake_batch_path = batch_dir / f"{batch_slug}_intake_batch.json"
    normalized_batch_path = batch_dir / f"{batch_slug}_normalized_evidence.json"

    env_checks = _build_env_checks(shell_rc=shell_rc)
    current_shell_ready, sourced_shell_ready, local_env_ready = _compute_local_env_ready(env_checks)
    live_json_out, live_markdown_out = _resolve_default_summary_paths(stage, "live")
    live_command = _build_live_command(
        stage=stage,
        shell_rc=shell_rc,
        current_shell_ready=current_shell_ready,
        sourced_shell_ready=sourced_shell_ready,
        selected_request_count=len(selected_request_rows),
    )

    report = {
        "schema_version": 1,
        "status": _resolve_preflight_status(
            current_shell_ready=current_shell_ready,
            sourced_shell_ready=sourced_shell_ready,
        ),
        "generated_at": generated_at,
        "pair": str(smoke_report.get("pair") or "en-es"),
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "prompt_spec_id": str(prompt_spec_payload.get("spec_id") or "").strip(),
        "prompt_version": str(prompt_spec_payload.get("prompt_version") or "").strip(),
        "stage": stage,
        "selected_model_id": str(stage_config.get("model_id") or "").strip(),
        "selected_temperature": float(stage_config.get("temperature") or 0.0),
        "summary": {
            "selected_request_count": len(selected_request_rows),
            "selected_family_count": len(
                {
                    str(row.get("family_id") or "").strip()
                    for row in selected_request_rows
                    if str(row.get("family_id") or "").strip()
                }
            ),
            "selected_slot_count": len(
                {
                    str(row.get("prompt_slot") or "").strip()
                    for row in selected_request_rows
                    if str(row.get("prompt_slot") or "").strip()
                }
            ),
            "current_shell_ready": current_shell_ready,
            "sourced_shell_ready": sourced_shell_ready,
            "local_env_ready": local_env_ready,
            "live_spend_guarded": True,
        },
        "env_checks": env_checks,
        "planned_artifacts": {
            "journal_jsonl": _display_path(journal_path),
            "raw_response_bundle_json": _display_path(raw_response_bundle_path),
            "intake_batch_json": _display_path(intake_batch_path),
            "normalized_batch_json": _display_path(normalized_batch_path),
            "live_summary_json": _display_path(live_json_out),
            "live_summary_markdown": _display_path(live_markdown_out),
        },
        "request_rows": selected_request_rows,
        "live_command_example": live_command,
    }
    return report


def _build_env_checks(*, shell_rc: Path) -> list[dict[str, object]]:
    current_openai_installed = importlib.util.find_spec("openai") is not None
    current_key_visible = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    venv_openai_installed = _venv_has_openai(venv_python)
    shell_rc_has_key = _shell_rc_mentions_openai_key(shell_rc)
    return [
        {
            "check_id": "current_python_openai_sdk_installed",
            "status": "ok" if current_openai_installed else "missing",
            "notes": "The current Python environment used by this command must import `openai` for direct live execution.",
        },
        {
            "check_id": "current_shell_openai_api_key_visible",
            "status": "ok" if current_key_visible else "missing",
            "notes": "The current shell must expose `OPENAI_API_KEY`; this preflight does not source shell rc files automatically.",
        },
        {
            "check_id": "repo_venv_openai_sdk_installed",
            "status": "ok" if venv_openai_installed else "missing",
            "notes": f"Checks whether the repo venv at `{_display_path(venv_python)}` can import `openai`.",
        },
        {
            "check_id": "shell_rc_mentions_openai_api_key",
            "status": "ok" if shell_rc_has_key else "missing",
            "notes": f"Checks whether `{shell_rc}` appears to export `OPENAI_API_KEY` without printing the key.",
        },
        {
            "check_id": "quota_not_checked",
            "status": "warn",
            "notes": "This no-spend preflight does not make a live API call, so quota/billing remains unverified here.",
        },
    ]


def _compute_local_env_ready(
    env_checks: Sequence[Mapping[str, object]],
) -> tuple[bool, bool, bool]:
    statuses = {
        str(row.get("check_id") or "").strip(): str(row.get("status") or "").strip()
        for row in env_checks
    }
    current_shell_ready = (
        statuses.get("current_python_openai_sdk_installed") == "ok"
        and statuses.get("current_shell_openai_api_key_visible") == "ok"
    )
    sourced_shell_ready = (
        statuses.get("repo_venv_openai_sdk_installed") == "ok"
        and statuses.get("shell_rc_mentions_openai_api_key") == "ok"
    )
    return current_shell_ready, sourced_shell_ready, current_shell_ready or sourced_shell_ready


def _venv_has_openai(venv_python: Path) -> bool:
    if not venv_python.exists():
        return False
    result = subprocess.run(
        [
            str(venv_python),
            "-c",
            "import importlib.util; print(bool(importlib.util.find_spec('openai')))",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "True"


def _shell_rc_mentions_openai_key(shell_rc: Path) -> bool:
    if not shell_rc.exists():
        return False
    try:
        text = shell_rc.read_text(encoding="utf-8")
    except OSError:
        return False
    return "OPENAI_API_KEY" in text and "export" in text


def _resolve_preflight_status(*, current_shell_ready: bool, sourced_shell_ready: bool) -> str:
    if current_shell_ready:
        return "ready"
    if sourced_shell_ready:
        return "sourced-shell-ready"
    return "blocked"


def _build_live_command(
    *,
    stage: str,
    shell_rc: Path,
    current_shell_ready: bool,
    sourced_shell_ready: bool,
    selected_request_count: int,
) -> str:
    base = (
        f"PYTHONPATH=apps/gui/src:core .venv/bin/python scripts/testing/semantic_llm_prompt_bakeoff_en_es.py --stage {stage} --execute-live "
        "--run-id <RUN_ID> "
        f"--require-selected-request-count {selected_request_count} "
        "--input-rate-per-1m <INPUT_RATE> "
        "--output-rate-per-1m <OUTPUT_RATE> "
        "--max-estimated-cost-ceiling-usd <USD_CAP>"
    )
    if current_shell_ready or not sourced_shell_ready:
        return base
    return f"zsh -lc 'source {shell_rc} >/dev/null 2>&1; {base}'"


def main() -> int:
    args = _parse_args()
    report = build_prompt_preflight_report(
        queue_payload=_load_json(args.queue_json),
        slot_manifest_payload=_load_json(args.slot_manifest_json),
        family_inventory_payload=_load_json(args.family_inventory_json),
        prompt_spec_payload=_load_json(args.prompt_spec_json),
        dataset_payload=load_sentence_veto_dataset(args.dataset),
        stage=args.stage,
        batch_dir=args.batch_dir,
        shell_rc=args.shell_rc,
        request_ids=args.request_id,
        max_requests=args.max_requests,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_prompt_preflight_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    print(f"Status: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
