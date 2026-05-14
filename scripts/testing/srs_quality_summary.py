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


def render_summary(
    payload: dict[str, Any],
    *,
    title: str = "SRS Quality Harness",
    max_findings: int = 10,
) -> str:
    summary = payload.get("summary")
    findings = payload.get("findings")
    scenarios = payload.get("pair_bootstrap_scenarios")
    if not isinstance(summary, dict):
        raise SystemExit("SRS quality JSON does not contain a 'summary' object.")
    if not isinstance(findings, list):
        raise SystemExit("SRS quality JSON does not contain a 'findings' list.")
    if not isinstance(scenarios, list):
        raise SystemExit("SRS quality JSON does not contain 'pair_bootstrap_scenarios'.")

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
        f"- Fail on warn: {'yes' if bool(payload.get('fail_on_warn')) else 'no'}",
        f"- Synthetic pairs: {', '.join(str(pair) for pair in payload.get('supported_pairs', [])) or 'none'}",
    ]

    unsupported_pairs = payload.get("unsupported_pairs")
    if isinstance(unsupported_pairs, list) and unsupported_pairs:
        lines.append(
            f"- Unsupported requested pairs: {', '.join(str(pair) for pair in unsupported_pairs)}"
        )

    lines.extend(["", "## Bootstrap Scenarios", ""])
    if not scenarios:
        lines.append("No bootstrap scenarios ran.")
    else:
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                continue
            lines.append(f"### {str(scenario.get('pair') or '<unknown>')}")
            lines.append(
                "- Store/Due/Published targets: "
                f"{int(scenario.get('store_items_for_pair') or 0)}/"
                f"{int(scenario.get('due_count') or 0)}/"
                f"{int(scenario.get('snapshot_target_count') or 0)}"
            )
            lines.append(
                f"- Ruleset unique targets: {int(scenario.get('ruleset_unique_targets') or 0)}"
            )
            lines.append(
                "- SRS due metadata/runtime-active targets: "
                f"{int(scenario.get('srs_due_metadata_count') or 0)}/"
                f"{int(scenario.get('runtime_due_active_count') or 0)}"
            )
            diagnostics = scenario.get("diagnostics")
            if isinstance(diagnostics, dict):
                lines.append(
                    "- Runtime artifacts: "
                    f"store={'yes' if diagnostics.get('store_exists') else 'no'} "
                    f"ruleset={'yes' if diagnostics.get('ruleset_exists') else 'no'} "
                    f"snapshot={'yes' if diagnostics.get('snapshot_exists') else 'no'}"
                )
            lines.append("")

    feedback = payload.get("feedback_cycle_scenario")
    if isinstance(feedback, dict):
        lines.extend(["## Feedback Cycle", ""])
        for phase in feedback.get("phases", []):
            if not isinstance(phase, dict):
                continue
            lines.append(
                "- "
                f"{str(phase.get('label') or '<phase>')}: "
                f"applied={'yes' if bool(phase.get('applied')) else 'no'}, "
                f"reason=`{str(phase.get('reason_code') or '')}`, "
                f"total_items={int(phase.get('total_items_for_pair') or 0)}, "
                f"ruleset={int(phase.get('ruleset_count') or 0)}, "
                f"runtime_due_active={int(phase.get('runtime_due_active_count') or 0)}"
            )
        lines.append("")

    actionable = [
        item
        for item in findings
        if isinstance(item, dict) and str(item.get("level") or "") in {"FAIL", "WARN"}
    ]
    lines.append("## Actionable Findings")
    if actionable:
        lines.append("")
        for index, item in enumerate(actionable[: max(1, int(max_findings))], start=1):
            pair = str(item.get("pair") or "")
            pair_prefix = f"[{pair}] " if pair else ""
            lines.append(
                f"{index}. [{str(item.get('level') or '')}] {pair_prefix}`{str(item.get('code') or '')}`: {str(item.get('message') or '')}"
            )
            details = str(item.get("details") or "").strip()
            if details:
                lines.append(f"   - {details}")
    else:
        lines.extend(["", "None."])

    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Markdown summaries from SRS quality JSON.")
    parser.add_argument(
        "--quality-json", type=Path, required=True, help="Path to SRS quality JSON."
    )
    parser.add_argument("--title", default="SRS Quality Harness", help="Summary title.")
    parser.add_argument(
        "--max-findings",
        type=int,
        default=10,
        help="Maximum number of FAIL/WARN findings to include.",
    )
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown output path.")
    parser.add_argument(
        "--append-to", type=Path, help="Optional path to append the Markdown summary."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown = render_summary(
        _load_json(args.quality_json),
        title=str(args.title),
        max_findings=int(args.max_findings),
    )
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
