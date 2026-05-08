#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"

DEFAULT_SOURCE_REQUEST_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_generation_requests_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_INPUTS_ROOT / "semantic_veto_evidence_gap_active_only_poc_requests_en_es.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_active_only_poc_requests_en_es_latest.md"
)
ACTIVE_SLOT = "active_evidence_expansion"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze the smallest meaningful active-only semantic-veto PoC generation batch "
            "from the existing evidence-gap control pilot request packet."
        )
    )
    parser.add_argument("--source-request-json", type=Path, default=DEFAULT_SOURCE_REQUEST_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_active_only_poc_request_report(
        source_payload=_load_json(args.source_request_json),
        source_path=args.source_request_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_active_only_poc_request_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_active_only_poc_request_report(
    *,
    source_payload: Mapping[str, object],
    source_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    source_requests = _mapping_rows(source_payload.get("requests"))
    active_requests = [
        dict(row) for row in source_requests if str(row.get("slot_type") or "") == ACTIVE_SLOT
    ]
    issues = _validate_active_only_batch(source_payload=source_payload, requests=active_requests)
    status = "ok" if not issues else "review"
    pilot = _as_mapping(source_payload.get("pilot"))
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "active_only_poc_generation_batch_frozen"
            if status == "ok"
            else "active_only_poc_generation_batch_needs_review"
        ),
        "generated_at": generated_at,
        "pair": str(source_payload.get("pair") or "en-es"),
        "pilot": {
            "pilot_id": str(pilot.get("pilot_id") or ""),
            "plan_status": str(pilot.get("plan_status") or ""),
            "request_kind": str(pilot.get("request_kind") or ""),
            "prompt_id": str(pilot.get("prompt_id") or ""),
            "source_request_packet": _repo_path(source_path),
        },
        "strict_flow": {
            "runtime_policy_change": "none",
            "llm_call": "none",
            "threshold_tuning": "none",
            "request_packet_role": "frozen_active_only_poc_generation_inputs",
            "generated_output_role": "candidate_active_evidence_only",
            "follow_through_rule": "run_once_admit_score_decide_without_open_ended_iteration",
        },
        "summary": _summary(active_requests),
        "request_checks": {
            "issue_count": len(issues),
            "issues": issues,
            "source_request_count": len(source_requests),
            "selected_slot_type": ACTIVE_SLOT,
            "selected_request_count": len(active_requests),
        },
        "requests": active_requests,
        "limitations": [
            "active evidence only",
            "not a full semantic-veto source coverage plan",
            "does not generate shadow or no-winner rows",
            "does not change runtime policy",
            "intended as one follow-through PoC batch, not a new iterative optimization loop",
        ],
        "next_steps": [
            "Run the frozen active-only request packet once with explicit live spend guards.",
            "Admit generated responses structurally before scoring.",
            "Run contribution and score-contribution reports against frozen repaired-full cases.",
            "Use the result as the PoC follow-through reading; do not keep cycling thresholds unless a new product goal is set.",
        ],
    }


def render_active_only_poc_request_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    checks = _as_mapping(report.get("request_checks"))
    lines = [
        "# en-es Semantic Veto Active-Only PoC Requests",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Prompt id: `{_as_mapping(report.get('pilot')).get('prompt_id', '')}`",
        f"- Source request packet: `{_as_mapping(report.get('pilot')).get('source_request_packet', '')}`",
        f"- Requests frozen: `{summary.get('request_count', 0)}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Expected generated items: `{summary.get('expected_generated_item_count', 0)}`",
        f"- Expected output-token budget: `{summary.get('expected_output_token_budget', 0)}`",
        "",
        "## Arm Summary",
        "",
        "| Arm | Requests | Families | Expected items |",
        "| --- | ---: | ---: | ---: |",
    ]
    for arm, row in _as_mapping(summary.get("requests_by_arm")).items():
        row_map = _as_mapping(row)
        lines.append(
            f"| `{_escape_md(str(arm))}` | {row_map.get('request_count', 0)} | "
            f"{row_map.get('family_count', 0)} | {row_map.get('expected_item_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Checks",
            "",
            f"- Source request count: `{checks.get('source_request_count', 0)}`",
            f"- Selected slot type: `{checks.get('selected_slot_type', '')}`",
            f"- Selected request count: `{checks.get('selected_request_count', 0)}`",
            f"- Issue count: `{checks.get('issue_count', 0)}`",
            "",
            "## Request Sample",
            "",
            "| Arm | Family | Trigger | Target | Items |",
            "| --- | --- | --- | --- | ---: |",
        ]
    )
    for row in _mapping_rows(report.get("requests"))[:12]:
        lines.append(
            f"| `{_escape_md(str(row.get('pilot_arm') or ''))}` | "
            f"`{_escape_md(str(row.get('family_id') or ''))}` | "
            f"`{_escape_md(str(row.get('trigger') or ''))}` | "
            f"`{_escape_md(str(row.get('active_target_lemma') or ''))}` | "
            f"{int(row.get('requested_items') or 0)} |"
        )
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _validate_active_only_batch(
    *,
    source_payload: Mapping[str, object],
    requests: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if int(source_payload.get("schema_version") or 0) != 1:
        issues.append(_issue("source", "error", "Source request packet must be schema_version=1."))
    if len(requests) != 24:
        issues.append(_issue("request_count", "error", "Expected exactly 24 active requests."))
    family_ids = [str(row.get("family_id") or "") for row in requests]
    if len(set(family_ids)) != len(requests):
        issues.append(
            _issue("families", "error", "Active-only batch must have one request per family.")
        )
    arm_counts = Counter(str(row.get("pilot_arm") or "") for row in requests)
    expected_arms = {"high_need": 8, "middle_control": 8, "low_control": 8}
    if dict(arm_counts) != expected_arms:
        issues.append(
            _issue(
                "arms", "error", f"Expected balanced arms {expected_arms}; got {dict(arm_counts)}."
            )
        )
    for row in requests:
        request_id = str(row.get("request_id") or "")
        if str(row.get("slot_type") or "") != ACTIVE_SLOT:
            issues.append(_issue(request_id, "error", "Non-active slot entered active-only batch."))
        if int(row.get("requested_items") or 0) != 2:
            issues.append(_issue(request_id, "error", "Active requests must ask for 2 items."))
        if not str(row.get("prompt_text") or "").strip():
            issues.append(_issue(request_id, "error", "Request is missing prompt_text."))
        if not str(row.get("trigger") or "").strip():
            issues.append(_issue(request_id, "error", "Request is missing trigger/source phrase."))
        if not str(row.get("active_target_lemma") or "").strip():
            issues.append(_issue(request_id, "error", "Request is missing active target lemma."))
    return issues


def _summary(requests: Sequence[Mapping[str, object]]) -> dict[str, object]:
    arms: dict[str, dict[str, object]] = {}
    for row in requests:
        arm = str(row.get("pilot_arm") or "")
        entry = arms.setdefault(
            arm,
            {
                "request_count": 0,
                "family_ids": set(),
                "expected_item_count": 0,
            },
        )
        entry["request_count"] = int(entry["request_count"]) + 1
        entry["family_ids"].add(str(row.get("family_id") or ""))
        entry["expected_item_count"] = int(entry["expected_item_count"]) + int(
            row.get("requested_items") or 0
        )
    requests_by_arm = {
        arm: {
            "request_count": int(row["request_count"]),
            "family_count": len(row["family_ids"]),
            "expected_item_count": int(row["expected_item_count"]),
        }
        for arm, row in sorted(arms.items())
    }
    return {
        "request_count": len(requests),
        "family_count": len({str(row.get("family_id") or "") for row in requests}),
        "expected_generated_item_count": sum(
            int(row.get("requested_items") or 0) for row in requests
        ),
        "estimated_input_tokens": sum(
            int(row.get("estimated_input_tokens") or 0) for row in requests
        ),
        "expected_output_token_budget": sum(
            int(row.get("expected_output_token_budget") or 0) for row in requests
        ),
        "requests_by_arm": requests_by_arm,
        "requests_by_slot_type": {
            ACTIVE_SLOT: {
                "request_count": len(requests),
                "expected_item_count": sum(
                    int(row.get("requested_items") or 0) for row in requests
                ),
            }
        },
    }


def _issue(subject: str, severity: str, message: str) -> dict[str, object]:
    return {
        "subject": subject,
        "severity": severity,
        "message": message,
    }


def _load_json(path: Path) -> Mapping[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
