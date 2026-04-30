#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_veto_system_registry_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / ("semantic_veto_system_registry_latest.json")
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / ("semantic_veto_system_registry_latest.md")
)

PASS_STATE_ORDER = {
    "in_progress": 0,
    "queued_next": 1,
    "blocked": 2,
    "needs_refresh": 3,
    "parked": 4,
}
ENTRY_STATE_ORDER = {
    "current_runtime": 0,
    "current_candidate": 1,
    "current_research": 2,
    "supporting_current": 3,
    "current_reference": 4,
    "generated_evidence": 5,
    "diagnostic_only": 6,
    "queued_audit": 7,
    "historical_reference": 8,
    "superseded": 9,
}
CURRENT_STATES = {
    "current_runtime",
    "current_reference",
    "current_research",
    "current_candidate",
    "supporting_current",
}
FORBIDDEN_PROMOTION_STATES = {"runtime_ready", "promoted", "default_on"}
ACTION_STATUS_ORDER = {
    "active": 0,
    "queued": 1,
    "blocked": 2,
    "done": 3,
}
ACTION_PRIORITY_ORDER = {
    "P0": 0,
    "P1": 1,
    "P2": 2,
    "P3": 3,
}


def main() -> int:
    args = _parse_args()
    report = build_semantic_veto_system_registry_report(registry_path=args.registry)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    if args.fail_on_issue and report["status"] != "ok":
        return 1
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_semantic_veto_system_registry_report(
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    registry = _load_json(registry_path)
    entries = _mapping_rows(registry.get("entries"))
    passes = _mapping_rows(registry.get("pass_checklist"))
    state_definitions = _as_mapping(registry.get("state_definitions"))
    component_definitions = _as_mapping(registry.get("component_definitions"))
    issues = _audit_registry(
        registry=registry,
        entries=entries,
        passes=passes,
        state_definitions=state_definitions,
        component_definitions=component_definitions,
    )
    sorted_entries = sorted(
        entries,
        key=lambda entry: (
            ENTRY_STATE_ORDER.get(str(entry.get("state") or ""), 99),
            str(entry.get("component") or ""),
            str(entry.get("artifact_id") or ""),
        ),
    )
    sorted_passes = sorted(
        passes,
        key=lambda row: (
            PASS_STATE_ORDER.get(str(row.get("state") or ""), 99),
            str(row.get("pass_id") or ""),
        ),
    )
    return {
        "schema_version": 1,
        "status": "ok" if not issues else "review",
        "generated_at": generated_at,
        "registry_path": str(registry_path),
        "registry_id": str(registry.get("registry_id") or ""),
        "purpose": str(registry.get("purpose") or ""),
        "entry_count": len(entries),
        "pass_count": len(passes),
        "state_counts": dict(sorted(Counter(_text(row.get("state")) for row in entries).items())),
        "component_counts": dict(
            sorted(Counter(_text(row.get("component")) for row in entries).items())
        ),
        "pass_state_counts": dict(
            sorted(Counter(_text(row.get("state")) for row in passes).items())
        ),
        "current_candidate": dict(_as_mapping(registry.get("current_candidate"))),
        "data_artifact_lanes": [
            _public_data_lane(row) for row in _mapping_rows(registry.get("data_artifact_lanes"))
        ],
        "action_items": [
            _public_action_item(row) for row in _sorted_action_items(registry.get("action_items"))
        ],
        "issues": issues,
        "next_passes": [
            _public_pass(row)
            for row in sorted_passes
            if str(row.get("state") or "") in {"in_progress", "queued_next", "needs_refresh"}
        ],
        "risk_rows": [
            _public_entry(row)
            for row in sorted_entries
            if str(row.get("risk") or "").strip()
            and str(row.get("state") or "") not in {"historical_reference", "superseded"}
        ],
        "passes": [_public_pass(row) for row in sorted_passes],
        "entries": [_public_entry(row) for row in sorted_entries],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    candidate = _as_mapping(report.get("current_candidate"))
    result = _as_mapping(candidate.get("current_result"))
    lines = [
        "# Semantic Veto System Registry",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Registry: `{report.get('registry_path', '')}`",
        f"- Entries: `{int(report.get('entry_count') or 0)}`",
        f"- Passes: `{int(report.get('pass_count') or 0)}`",
        "",
        "## Current Candidate",
        "",
        f"- Candidate: `{candidate.get('candidate_id', '')}`",
        f"- Production status: `{candidate.get('production_status', '')}`",
        f"- Runtime policy change: `{candidate.get('runtime_policy_change', '')}`",
        f"- Control: {candidate.get('control', '')}",
        f"- Summary: {candidate.get('candidate_summary', '')}",
        f"- Active/shadow: `{result.get('active_shadow_harmful_replacements', '')}` harmful / "
        f"`{result.get('active_shadow_false_abstains', '')}` false abstains / "
        f"`{result.get('active_shadow_decision_accuracy', '')}` accuracy",
        f"- Phrase/no-winner before replay: "
        f"`{result.get('unrescued_phrase_harmful_replacements', '')}` harmful",
        f"- Rescue replay passing policies: "
        f"`{result.get('rescue_replay_passing_policy_count', '')}`",
        f"- Scorer-backed rescue policy: "
        f"`{result.get('scorer_backed_policy_harmful_replacements', '')}` harmful / "
        f"`{result.get('scorer_backed_policy_false_abstains', '')}` false abstains / "
        f"`{result.get('scorer_backed_policy_cases', '')}` cases",
        f"- Next breadth gate: `{result.get('next_breadth_gate', '')}`",
        "",
        "## Audit",
        "",
    ]
    issues = _mapping_rows(report.get("issues"))
    if issues:
        for issue in issues:
            lines.append(
                f"- `{issue.get('severity', '')}` `{issue.get('subject', '')}`: "
                f"{issue.get('message', '')}"
            )
    else:
        lines.append("- No registry issues detected.")

    lines.extend(["", "## Next Passes", ""])
    for row in _mapping_rows(report.get("next_passes")):
        lines.append(
            f"- `{row.get('pass_id', '')}` ({row.get('state', '')}): {row.get('lens', '')}"
        )

    action_items = _mapping_rows(report.get("action_items"))
    if action_items:
        lines.extend(["", "## Action Items", ""])
        lines.append(
            "| Priority | Status | Action | Pass | Source | Evidence Needed | Validation |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for row in action_items:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_md(str(row.get("priority") or "")),
                        _escape_md(str(row.get("status") or "")),
                        _escape_md(str(row.get("action") or "")),
                        _escape_md(str(row.get("pass_id") or "")),
                        _escape_md(_join_inline(row.get("source_artifacts"))),
                        _escape_md(str(row.get("evidence_needed") or "")),
                        _escape_md(str(row.get("validation") or "")),
                    ]
                )
                + " |"
            )

    lines.extend(["", "## Counts", ""])
    lines.append("### Entry States")
    for state, count in sorted((_as_mapping(report.get("state_counts"))).items()):
        lines.append(f"- `{state}`: `{count}`")
    lines.append("")
    lines.append("### Components")
    for component, count in sorted((_as_mapping(report.get("component_counts"))).items()):
        lines.append(f"- `{component}`: `{count}`")

    data_lanes = _mapping_rows(report.get("data_artifact_lanes"))
    if data_lanes:
        lines.extend(["", "## Data Artifact Lanes", ""])
        lines.append(
            "| Lane | Status | Durable Inputs | Generated Reports | Control Artifacts | Cracks |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for row in data_lanes:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_md(str(row.get("lane_id") or "")),
                        _escape_md(str(row.get("status") or "")),
                        _escape_md(_join_inline(row.get("durable_inputs"))),
                        _escape_md(_join_inline(row.get("generated_reports"))),
                        _escape_md(_join_inline(row.get("control_artifacts"))),
                        _escape_md(_join_inline(row.get("local_artifact_cracks"))),
                    ]
                )
                + " |"
            )
        lines.extend(["", "### Data Rerun Order", ""])
        for row in data_lanes:
            lines.append(
                f"- `{row.get('lane_id', '')}`: " + _escape_md(_join_inline(row.get("rerun_order")))
            )

    lines.extend(["", "## Risk Rows", ""])
    lines.append("| Artifact | State | Component | Risk | Next Pass |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in _mapping_rows(report.get("risk_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("artifact_id") or "")),
                    _escape_md(str(row.get("state") or "")),
                    _escape_md(str(row.get("component") or "")),
                    _escape_md(str(row.get("risk") or "")),
                    _escape_md(str(row.get("next_audit_pass") or "")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Entries", ""])
    lines.append("| Artifact | State | Component | Path | Current Use |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in _mapping_rows(report.get("entries")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("artifact_id") or "")),
                    _escape_md(str(row.get("state") or "")),
                    _escape_md(str(row.get("component") or "")),
                    _escape_md(str(row.get("path") or "")),
                    _escape_md(str(row.get("current_use") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render and audit the en-es semantic-veto system registry."
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-issue", action="store_true")
    return parser.parse_args()


def _audit_registry(
    *,
    registry: Mapping[str, object],
    entries: Sequence[Mapping[str, object]],
    passes: Sequence[Mapping[str, object]],
    state_definitions: Mapping[str, object],
    component_definitions: Mapping[str, object],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    state_ids = {str(key) for key in state_definitions}
    component_ids = {str(key) for key in component_definitions}
    pass_ids: set[str] = set()
    for pass_row in passes:
        pass_id = _text(pass_row.get("pass_id"))
        pass_state = _text(pass_row.get("state"))
        if not pass_id:
            issues.append(_issue("pass", "error", "A pass row is missing pass_id."))
            continue
        if pass_id in pass_ids:
            issues.append(_issue(pass_id, "error", "Duplicate pass_id."))
        pass_ids.add(pass_id)
        if pass_state not in PASS_STATE_ORDER:
            issues.append(_issue(pass_id, "error", f"Unsupported pass state {pass_state!r}."))
        if not _text(pass_row.get("lens")):
            issues.append(_issue(pass_id, "error", "Pass row is missing lens."))
        if not pass_row.get("primary_outputs"):
            issues.append(_issue(pass_id, "warning", "Pass row has no primary outputs."))

    seen_entries: set[str] = set()
    for entry in entries:
        artifact_id = _text(entry.get("artifact_id"))
        if not artifact_id:
            issues.append(_issue("entry", "error", "An entry is missing artifact_id."))
            continue
        if artifact_id in seen_entries:
            issues.append(_issue(artifact_id, "error", "Duplicate artifact_id."))
        seen_entries.add(artifact_id)
        state = _text(entry.get("state"))
        component = _text(entry.get("component"))
        if state not in state_ids:
            issues.append(_issue(artifact_id, "error", f"Unsupported entry state {state!r}."))
        if component not in component_ids:
            issues.append(_issue(artifact_id, "error", f"Unsupported component {component!r}."))
        path = _text(entry.get("path"))
        if not path:
            issues.append(_issue(artifact_id, "error", "Entry is missing path."))
        elif not (PROJECT_ROOT / path).exists():
            issues.append(_issue(artifact_id, "warning", f"Path does not exist: {path}"))
        if state in CURRENT_STATES:
            if not _text(entry.get("owner_doc")):
                issues.append(_issue(artifact_id, "error", "Current entry lacks owner_doc."))
            if not entry.get("verification_artifacts"):
                issues.append(
                    _issue(artifact_id, "warning", "Current entry lacks verification artifacts.")
                )
        next_pass = _text(entry.get("next_audit_pass"))
        if next_pass and next_pass not in pass_ids:
            issues.append(_issue(artifact_id, "error", f"Unknown next_audit_pass {next_pass!r}."))
        if state == "current_candidate" and not entry.get("verification_artifacts"):
            issues.append(
                _issue(artifact_id, "error", "Candidate entry needs verification artifacts.")
            )

    known_entries = {str(row.get("artifact_id") or "") for row in entries}
    lane_ids = {
        _text(row.get("lane_id")) for row in _mapping_rows(registry.get("data_artifact_lanes"))
    }
    for lane in _mapping_rows(registry.get("data_artifact_lanes")):
        lane_id = _text(lane.get("lane_id"))
        if not lane_id:
            issues.append(_issue("data_artifact_lanes", "error", "A lane row is missing lane_id."))
            continue
        if not lane.get("durable_inputs"):
            issues.append(_issue(lane_id, "warning", "Data lane has no durable inputs."))
        for key in ("durable_inputs", "generated_reports", "control_artifacts", "rerun_order"):
            for artifact_id in lane.get(key) or ():
                if str(artifact_id) not in known_entries:
                    issues.append(
                        _issue(
                            lane_id,
                            "error",
                            f"Unknown artifact_id {artifact_id!r} in data lane {key}.",
                        )
                    )

    known_action_refs = known_entries | lane_ids | pass_ids
    seen_actions: set[str] = set()
    for item in _mapping_rows(registry.get("action_items")):
        action_id = _text(item.get("action_id"))
        if not action_id:
            issues.append(_issue("action_items", "error", "An action item is missing action_id."))
            continue
        if action_id in seen_actions:
            issues.append(_issue(action_id, "error", "Duplicate action_id."))
        seen_actions.add(action_id)
        status = _text(item.get("status"))
        priority = _text(item.get("priority"))
        if status not in ACTION_STATUS_ORDER:
            issues.append(_issue(action_id, "error", f"Unsupported action status {status!r}."))
        if priority not in ACTION_PRIORITY_ORDER:
            issues.append(_issue(action_id, "error", f"Unsupported action priority {priority!r}."))
        pass_id = _text(item.get("pass_id"))
        if pass_id and pass_id not in pass_ids:
            issues.append(_issue(action_id, "error", f"Unknown action pass_id {pass_id!r}."))
        if not _text(item.get("action")):
            issues.append(_issue(action_id, "error", "Action item is missing action."))
        if not _text(item.get("evidence_needed")):
            issues.append(_issue(action_id, "warning", "Action item lacks evidence_needed."))
        if not _text(item.get("validation")):
            issues.append(_issue(action_id, "warning", "Action item lacks validation."))
        for artifact_id in item.get("source_artifacts") or ():
            if str(artifact_id) not in known_action_refs:
                issues.append(
                    _issue(
                        action_id,
                        "error",
                        f"Unknown source_artifact {artifact_id!r} in action item.",
                    )
                )

    candidate = _as_mapping(registry.get("current_candidate"))
    production_status = _text(candidate.get("production_status"))
    if production_status in FORBIDDEN_PROMOTION_STATES:
        issues.append(
            _issue(
                "current_candidate",
                "error",
                "Registry cannot mark a candidate runtime-ready without a runtime policy change.",
            )
        )
    if not _text(candidate.get("candidate_id")):
        issues.append(_issue("current_candidate", "error", "Missing candidate_id."))
    if not _as_mapping(candidate.get("current_result")):
        issues.append(_issue("current_candidate", "warning", "Missing current_result."))
    if not candidate.get("promotion_blockers"):
        issues.append(_issue("current_candidate", "warning", "Missing promotion blockers."))
    return issues


def _public_pass(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "pass_id": _text(row.get("pass_id")),
        "state": _text(row.get("state")),
        "lens": _text(row.get("lens")),
        "primary_outputs": [str(value) for value in row.get("primary_outputs") or ()],
        "cracks_to_watch": [str(value) for value in row.get("cracks_to_watch") or ()],
    }


def _public_entry(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "artifact_id": _text(row.get("artifact_id")),
        "title": _text(row.get("title")),
        "component": _text(row.get("component")),
        "state": _text(row.get("state")),
        "path": _text(row.get("path")),
        "role": _text(row.get("role")),
        "owner_doc": _text(row.get("owner_doc")),
        "current_use": _text(row.get("current_use")),
        "risk": _text(row.get("risk")),
        "next_audit_pass": _text(row.get("next_audit_pass")),
        "verification_artifacts": [str(value) for value in row.get("verification_artifacts") or ()],
    }


def _public_data_lane(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "lane_id": _text(row.get("lane_id")),
        "status": _text(row.get("status")),
        "purpose": _text(row.get("purpose")),
        "durable_inputs": [str(value) for value in row.get("durable_inputs") or ()],
        "generated_reports": [str(value) for value in row.get("generated_reports") or ()],
        "control_artifacts": [str(value) for value in row.get("control_artifacts") or ()],
        "local_artifact_cracks": [str(value) for value in row.get("local_artifact_cracks") or ()],
        "rerun_order": [str(value) for value in row.get("rerun_order") or ()],
    }


def _public_action_item(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "action_id": _text(row.get("action_id")),
        "priority": _text(row.get("priority")),
        "status": _text(row.get("status")),
        "pass_id": _text(row.get("pass_id")),
        "source_artifacts": [str(value) for value in row.get("source_artifacts") or ()],
        "action": _text(row.get("action")),
        "evidence_needed": _text(row.get("evidence_needed")),
        "validation": _text(row.get("validation")),
        "promotion_impact": _text(row.get("promotion_impact")),
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


def _sorted_action_items(value: object) -> list[Mapping[str, object]]:
    return sorted(
        _mapping_rows(value),
        key=lambda row: (
            ACTION_PRIORITY_ORDER.get(_text(row.get("priority")), 99),
            ACTION_STATUS_ORDER.get(_text(row.get("status")), 99),
            _text(row.get("action_id")),
        ),
    )


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _join_inline(value: object) -> str:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return ", ".join(f"`{item}`" for item in value)
    return ""


def _text(value: object) -> str:
    return str(value or "").strip()


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
