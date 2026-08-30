#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import (  # noqa: E402
    build_artifact_provenance,
    validate_artifact_freshness,
    utc_now,
)


DEFAULT_JSON_OUT = PROJECT_ROOT / "docs" / "test_outputs" / "artifact_freshness_latest.json"
DEFAULT_MARKDOWN_OUT = PROJECT_ROOT / "docs" / "test_outputs" / "artifact_freshness_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether generated testing artifacts include provenance and still "
            "match the live checkout files they were generated from."
        )
    )
    parser.add_argument("artifacts", nargs="+", type=Path)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--markdown-out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report([_resolve_path(path) for path in args.artifacts])
    if args.json_out is not None:
        json_out = _resolve_path(args.json_out)
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote JSON artifact to {json_out}")
    if args.markdown_out is not None:
        markdown_out = _resolve_path(args.markdown_out)
        markdown_out.parent.mkdir(parents=True, exist_ok=True)
        markdown_out.write_text(render_markdown(report), encoding="utf-8")
        print(f"Wrote Markdown artifact to {markdown_out}")
    print(render_markdown(report), end="")
    return 0 if report["summary"]["stale_count"] == 0 else 1


def build_report(artifacts: Sequence[Path]) -> dict[str, object]:
    results = [validate_artifact_freshness(path, project_root=PROJECT_ROOT) for path in artifacts]
    stale_count = sum(1 for result in results if not result.get("fresh"))
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={f"artifact_{index}": path for index, path in enumerate(artifacts)},
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
            },
            argv=sys.argv,
        ),
        "artifact_count": len(results),
        "summary": {
            "fresh_count": len(results) - stale_count,
            "stale_count": stale_count,
        },
        "results": results,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# Artifact Freshness Check",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Fresh: `{_escape(summary.get('fresh_count'))}`",
        f"- Stale: `{_escape(summary.get('stale_count'))}`",
        "",
        "| Artifact | Status | Failures | Warnings |",
        "| --- | --- | --- | --- |",
    ]
    for raw_result in report.get("results", ()) or ():
        result = raw_result if isinstance(raw_result, Mapping) else {}
        failures = ", ".join(str(item) for item in result.get("failures", ()) or ())
        warnings = ", ".join(str(item) for item in result.get("warnings", ()) or ())
        lines.append(
            "| "
            f"`{_escape(result.get('artifact'))}` | "
            f"`{_escape(result.get('status'))}` | "
            f"{_escape(failures)} | "
            f"{_escape(warnings)} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _escape(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
