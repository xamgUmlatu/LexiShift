#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_decision_research_lanes_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_decision_research_lanes_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_decision_research_lanes_latest.md"
)

STATE_ORDER = {
    "queued_next": 0,
    "harness_ready_unswept": 1,
    "harness_partial": 2,
    "idea_recorded": 3,
    "active_source_program": 4,
    "swept_promising_control": 5,
    "swept_inconclusive": 6,
    "swept_negative": 7,
    "parked_second_lane": 8,
}
SWEEP_STATES = {
    "swept_promising_control",
    "swept_inconclusive",
    "swept_negative",
    "active_source_program",
}
FORBIDDEN_DONE_WORDS = ("done", "complete", "completed")


def main() -> int:
    args = _parse_args()
    report = build_research_lanes_report(ledger_path=args.ledger)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    if report["status"] != "ok" and args.fail_on_issue:
        return 1
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_research_lanes_report(*, ledger_path: Path = DEFAULT_LEDGER) -> dict[str, object]:
    ledger = _load_json(ledger_path)
    lanes = _mapping_rows(ledger.get("lanes"))
    issues = _audit_lanes(lanes)
    state_counts = Counter(str(lane.get("state") or "") for lane in lanes)
    sorted_lanes = sorted(
        lanes,
        key=lambda lane: (
            STATE_ORDER.get(str(lane.get("state") or ""), 99),
            str(lane.get("lane_id") or ""),
        ),
    )
    next_lanes = [
        _public_lane(lane)
        for lane in sorted_lanes
        if str(lane.get("state") or "") in {"queued_next", "harness_ready_unswept"}
    ]
    unswept_lanes = [
        _public_lane(lane)
        for lane in sorted_lanes
        if str(lane.get("state") or "")
        in {
            "idea_recorded",
            "queued_next",
            "harness_partial",
            "harness_ready_unswept",
            "parked_second_lane",
        }
    ]
    return {
        "schema_version": 1,
        "status": "ok" if not issues else "review",
        "generated_at": _utc_now(),
        "ledger_path": str(ledger_path),
        "lane_set_id": str(ledger.get("lane_set_id") or ""),
        "lane_count": len(lanes),
        "state_counts": dict(sorted(state_counts.items())),
        "methodology_rules": list(ledger.get("methodology_rules") or ()),
        "issues": issues,
        "next_lanes": next_lanes,
        "unswept_or_partial_lanes": unswept_lanes,
        "lanes": [_public_lane(lane) for lane in sorted_lanes],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# Semantic Decision Research Lanes",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Ledger: `{report.get('ledger_path', '')}`",
        f"- Lane count: `{int(report.get('lane_count') or 0)}`",
        "",
        "## Methodology Rules",
        "",
    ]
    for rule in report.get("methodology_rules") or ():
        lines.append(f"- {rule}")
    issues = _mapping_rows(report.get("issues"))
    lines.extend(["", "## Audit", ""])
    if issues:
        for issue in issues:
            lines.append(
                f"- `{issue.get('severity', '')}` `{issue.get('lane_id', '')}`: "
                f"{issue.get('message', '')}"
            )
    else:
        lines.append("- No methodology issues detected.")

    next_lanes = _mapping_rows(report.get("next_lanes"))
    if next_lanes:
        lines.extend(["", "## Next Lanes", ""])
        for lane in next_lanes:
            lines.append(
                f"- `{lane.get('lane_id', '')}` ({lane.get('state', '')}): "
                f"{lane.get('next_action', '')}"
            )

    lines.extend(["", "## State Counts", ""])
    for state, count in sorted((report.get("state_counts") or {}).items()):
        lines.append(f"- `{state}`: `{count}`")

    lines.extend(["", "## Lane Ledger", ""])
    lines.append("| Lane | State | Axis | Promotion | Current Read | Next Action |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for lane in _mapping_rows(report.get("lanes")):
        lines.append(
            "| "
            + " | ".join(
                (
                    _escape_md(str(lane.get("lane_id") or "")),
                    _escape_md(str(lane.get("state") or "")),
                    _escape_md(str(lane.get("primary_axis") or "")),
                    _escape_md(str(lane.get("promotion_status") or "")),
                    _escape_md(str(lane.get("current_read") or "")),
                    _escape_md(str(lane.get("next_action") or "")),
                )
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render and audit the semantic decision research lane ledger."
    )
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-issue", action="store_true")
    return parser.parse_args()


def _audit_lanes(lanes: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for lane in lanes:
        lane_id = str(lane.get("lane_id") or "").strip()
        state = str(lane.get("state") or "").strip()
        if not lane_id:
            issues.append(_issue("", "error", "Lane is missing lane_id."))
            continue
        if lane_id in seen_ids:
            issues.append(_issue(lane_id, "error", "Duplicate lane_id."))
        seen_ids.add(lane_id)
        if state not in STATE_ORDER:
            issues.append(_issue(lane_id, "error", f"Unsupported state {state!r}."))
        for key in ("state", "current_read", "next_action", "promotion_status"):
            value = str(lane.get(key) or "").casefold()
            if any(word in value for word in FORBIDDEN_DONE_WORDS):
                issues.append(
                    _issue(
                        lane_id,
                        "error",
                        f"Forbidden completion language appears in {key!r}; use explicit research states.",
                    )
                )
        artifacts = [str(path or "").strip() for path in lane.get("artifacts") or ()]
        if state in SWEEP_STATES and not artifacts:
            issues.append(_issue(lane_id, "error", "Swept/source-program lanes need artifacts."))
        for artifact in artifacts:
            artifact_path = PROJECT_ROOT / artifact
            if not artifact_path.exists():
                issues.append(_issue(lane_id, "warning", f"Artifact does not exist: {artifact}"))
        if str(lane.get("promotion_status") or "") in {"promoted", "runtime_ready"}:
            issues.append(
                _issue(
                    lane_id,
                    "error",
                    "Runtime promotion requires a production-policy change and quality-gate evidence, not just a lane ledger entry.",
                )
            )
    return issues


def _public_lane(lane: Mapping[str, object]) -> dict[str, object]:
    return {
        "lane_id": str(lane.get("lane_id") or ""),
        "state": str(lane.get("state") or ""),
        "primary_axis": str(lane.get("primary_axis") or ""),
        "changes": [str(value) for value in lane.get("changes") or ()],
        "artifacts": [str(value) for value in lane.get("artifacts") or ()],
        "current_read": str(lane.get("current_read") or ""),
        "next_action": str(lane.get("next_action") or ""),
        "promotion_status": str(lane.get("promotion_status") or ""),
    }


def _load_json(path: Path) -> Mapping[str, object]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _issue(lane_id: str, severity: str, message: str) -> dict[str, str]:
    return {"lane_id": lane_id, "severity": severity, "message": message}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
