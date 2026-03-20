#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return payload


def render_summary(payload: dict[str, Any], *, title: str = "SRS Journey Harness") -> str:
    scenario = payload.get("scenario")
    phases = payload.get("phases")
    findings = payload.get("findings")
    summary = payload.get("summary")
    signal_summary = payload.get("signal_summary")
    if not isinstance(scenario, dict):
        raise SystemExit("SRS journey JSON does not contain a 'scenario' object.")
    if not isinstance(phases, list):
        raise SystemExit("SRS journey JSON does not contain a 'phases' list.")
    if not isinstance(findings, list):
        raise SystemExit("SRS journey JSON does not contain a 'findings' list.")
    if not isinstance(summary, dict):
        raise SystemExit("SRS journey JSON does not contain a 'summary' object.")
    if signal_summary is not None and not isinstance(signal_summary, dict):
        raise SystemExit("SRS journey JSON does not contain a valid 'signal_summary' object.")

    lines = [
        f"# {title}",
        "",
        f"- Status: {str(summary.get('status') or 'UNKNOWN')}",
        (
            "- Findings: "
            f"pass={int(summary.get('pass_count') or 0)} "
            f"warn={int(summary.get('warn_count') or 0)} "
            f"fail={int(summary.get('fail_count') or 0)}"
        ),
        f"- Scenario: `{str(scenario.get('name') or '')}`",
        f"- Pair: `{str(scenario.get('pair') or '')}`",
        f"- Lane: `{str(scenario.get('lane') or '')}`",
        f"- Contract mode: `{str(scenario.get('contract_mode') or '')}`",
        f"- Generated at: `{str(payload.get('generated_at') or '')}`",
        "",
        "## Phases",
        "",
    ]

    for phase in phases:
        if not isinstance(phase, dict):
            continue
        lines.append(f"### {str(phase.get('label') or '<phase>')}")
        counts = phase.get("counts") if isinstance(phase.get("counts"), dict) else {}
        lines.append(
            "- Counts: "
            f"admitted={int(counts.get('admitted') or 0)} "
            f"due={int(counts.get('due') or 0)} "
            f"published={int(counts.get('published') or 0)}"
        )
        refresh = phase.get("refresh") if isinstance(phase.get("refresh"), dict) else {}
        refresh_payload = refresh.get("payload") if isinstance(refresh.get("payload"), dict) else {}
        if refresh.get("requested"):
            lines.append(
                "- Refresh: "
                f"applied={'yes' if bool(refresh_payload.get('applied')) else 'no'} "
                f"reason=`{str(refresh_payload.get('admission_refresh', {}).get('reason_code') or '')}`"
            )
        else:
            lines.append("- Refresh: not requested")
        deltas = phase.get("deltas") if isinstance(phase.get("deltas"), dict) else {}
        lines.append(
            "- Admitted delta: "
            f"in={', '.join(deltas.get('admitted_in', [])) or 'none'}; "
            f"out={', '.join(deltas.get('admitted_out', [])) or 'none'}"
        )
        lines.append(
            "- Due delta: "
            f"in={', '.join(deltas.get('due_in', [])) or 'none'}; "
            f"out={', '.join(deltas.get('due_out', [])) or 'none'}"
        )
        lines.append(
            "- Published delta: "
            f"in={', '.join(deltas.get('published_in', [])) or 'none'}; "
            f"out={', '.join(deltas.get('published_out', [])) or 'none'}"
        )
        events_applied = (
            phase.get("events_applied") if isinstance(phase.get("events_applied"), dict) else {}
        )
        event_counts = (
            events_applied.get("counts") if isinstance(events_applied.get("counts"), dict) else {}
        )
        lines.append(
            "- Events applied: "
            f"feedback={int(event_counts.get('feedback') or 0)} "
            f"exposure={int(event_counts.get('exposure') or 0)}"
        )
        relationships = (
            phase.get("relationships") if isinstance(phase.get("relationships"), dict) else {}
        )
        lines.append(
            "- Published not due: "
            f"{', '.join(relationships.get('published_not_due', [])) or 'none'}"
        )
        lines.append("")

    if signal_summary:
        event_types = (
            signal_summary.get("event_types")
            if isinstance(signal_summary.get("event_types"), dict)
            else {}
        )
        lines.extend(
            [
                "## Signal Log",
                "",
                f"- Event count: {int(signal_summary.get('event_count') or 0)}",
                f"- Unique lemmas: {int(signal_summary.get('unique_lemmas') or 0)}",
                (
                    "- Event types: "
                    f"feedback={int(event_types.get('feedback') or 0)} "
                    f"exposure={int(event_types.get('exposure') or 0)}"
                ),
                f"- Last event at: `{str(signal_summary.get('last_event_at') or '')}`",
                "",
            ]
        )

    final_phase = phases[-1] if phases else {}
    items = (
        final_phase.get("items")
        if isinstance(final_phase, dict) and isinstance(final_phase.get("items"), list)
        else []
    )
    stable_due = [
        item.get("lemma")
        for item in items
        if isinstance(item, dict) and item.get("cohort") == "stable" and item.get("in_due")
    ]
    difficult_due = [
        item.get("lemma")
        for item in items
        if isinstance(item, dict) and item.get("cohort") == "difficult" and item.get("in_due")
    ]

    lines.extend(
        [
            "## Cohort Check",
            "",
            f"- Stable cohort due in final phase: {', '.join(str(item) for item in stable_due) or 'none'}",
            f"- Difficult cohort due in final phase: {', '.join(str(item) for item in difficult_due) or 'none'}",
            "",
            "## Actionable Findings",
            "",
        ]
    )

    actionable = [
        item
        for item in findings
        if isinstance(item, dict) and str(item.get("level") or "") in {"WARN", "FAIL"}
    ]
    if actionable:
        for index, item in enumerate(actionable, start=1):
            phase = str(item.get("phase") or "")
            phase_prefix = f"[{phase}] " if phase else ""
            lines.append(
                f"{index}. [{str(item.get('level') or '')}] {phase_prefix}`{str(item.get('code') or '')}`: {str(item.get('message') or '')}"
            )
            details = str(item.get("details") or "").strip()
            if details:
                lines.append(f"   - {details}")
    else:
        lines.append("None.")

    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Markdown summaries from SRS journey JSON.")
    parser.add_argument(
        "--journey-json", type=Path, required=True, help="Path to SRS journey JSON."
    )
    parser.add_argument("--title", default="SRS Journey Harness", help="Summary title.")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown output path.")
    parser.add_argument(
        "--append-to", type=Path, help="Optional path to append the Markdown summary."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown = render_summary(_load_json(args.journey_json), title=str(args.title))
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(markdown, encoding="utf-8")
        print(f"markdown_out: {args.markdown_out}")
    if args.append_to:
        args.append_to.parent.mkdir(parents=True, exist_ok=True)
        with args.append_to.open("a", encoding="utf-8") as handle:
            handle.write(markdown)
            if not markdown.endswith("\n"):
                handle.write("\n")
        print(f"append_to: {args.append_to}")
    print(markdown, end="" if markdown.endswith("\n") else "\n")


if __name__ == "__main__":
    main()
