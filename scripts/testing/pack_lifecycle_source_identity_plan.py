#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
GUI_SRC = PROJECT_ROOT / "apps" / "gui" / "src"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (CORE_ROOT, GUI_SRC):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from language_packs_catalog import build_pack_catalogs  # noqa: E402
from lexishift_core.helper.pack_source_identity import (  # noqa: E402
    SOURCE_IDENTITY_CLASSIFICATIONS,
    classify_pack_source_identity,
)


DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_source_identity_plan_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_source_identity_plan_latest.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify catalog pack source-version/source-dump identity candidates. "
            "The command is read-only: it does not write provenance sidecars or "
            "promote any candidate value into durable source identity."
        )
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_source_identity_plan()
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_source_identity_plan_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_source_identity_plan(*, generated_at: str | None = None) -> dict[str, object]:
    catalogs = build_pack_catalogs()
    rows: list[dict[str, object]] = []
    for family, packs in (
        ("language", catalogs.language_packs),
        ("frequency", catalogs.frequency_packs),
        ("embedding", catalogs.embedding_packs),
        ("embedding", catalogs.cross_embedding_packs),
    ):
        for pack in packs:
            rows.append(_classify_pack(family=family, pack=pack))

    summary = _summary(rows)
    return {
        "schema_version": 1,
        "generated_at": generated_at or _utc_now(),
        "status": "review" if summary["needs_decision_count"] else "ok",
        "decision": (
            "source_identity_classification_needs_review"
            if summary["needs_decision_count"]
            else "source_identity_candidates_classified"
        ),
        "mutation": "none",
        "runtime_policy_change": "none",
        "summary": summary,
        "packs": rows,
        "boundaries": [
            "does_not_write_source_version_or_source_dump",
            "does_not_approve_source_licenses",
            "does_not_pin_rolling_remote_sources",
            "does_not_change_pack_catalogs_or_runtime_defaults",
        ],
    }


def render_source_identity_plan_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# Pack Lifecycle Source Identity Plan",
        "",
        f"- Generated at: `{report.get('generated_at')}`",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Mutation: `{report.get('mutation')}`",
        f"- Runtime policy change: `{report.get('runtime_policy_change')}`",
        f"- Safe to write: `{summary.get('safe_to_write_count')}`",
        f"- Needs decision: `{summary.get('needs_decision_count')}`",
        "",
        "## Classification Summary",
        "",
        "| Classification | Count |",
        "| --- | --- |",
    ]
    classification_counts = _as_mapping(summary.get("classification_counts"))
    for classification in SOURCE_IDENTITY_CLASSIFICATIONS:
        lines.append(f"| `{classification}` | `{classification_counts.get(classification, 0)}` |")
    lines.extend(
        [
            "",
            "## Pack Candidates",
            "",
            "| Family | Pack | Classification | Field | Candidate | Rationale | Recommended Action |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("packs")):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('family') or ''))}`",
                    f"`{_escape_md(str(row.get('pack_id') or ''))}`",
                    f"`{_escape_md(str(row.get('classification') or ''))}`",
                    f"`{_escape_md(str(row.get('candidate_field') or ''))}`",
                    f"`{_escape_md(str(row.get('candidate_value') or ''))}`",
                    _escape_md(str(row.get("rationale") or "")),
                    _escape_md(str(row.get("recommended_action") or "")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Boundaries", ""])
    lines.extend(f"- `{item}`" for item in _string_sequence(report.get("boundaries")))
    return "\n".join(lines) + "\n"


def _classify_pack(*, family: str, pack: object) -> dict[str, object]:
    decision = classify_pack_source_identity(pack)
    return _row(
        family=family,
        pack=pack,
        candidate_field=decision.candidate_field,
        candidate_value=decision.candidate_value,
        classification=decision.classification,
        rationale=decision.rationale,
        recommended_action=decision.recommended_action,
    )


def _row(
    *,
    family: str,
    pack: object,
    candidate_field: str,
    candidate_value: str,
    classification: str,
    rationale: str,
    recommended_action: str,
) -> dict[str, object]:
    return {
        "family": family,
        "pack_id": _text(getattr(pack, "pack_id", "")),
        "source_name": _text(getattr(pack, "source", "")),
        "build_mode": _text(getattr(pack, "build_mode", "download_only")) or "download_only",
        "filename": _text(getattr(pack, "filename", "")),
        "source_filename": _text(getattr(pack, "source_filename", "")),
        "source_url": _text(getattr(pack, "url", "")),
        "candidate_field": candidate_field,
        "candidate_value": candidate_value,
        "classification": classification,
        "rationale": rationale,
        "recommended_action": recommended_action,
    }


def _summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    counts = {classification: 0 for classification in SOURCE_IDENTITY_CLASSIFICATIONS}
    for row in rows:
        classification = str(row.get("classification") or "unknown")
        counts[classification] = counts.get(classification, 0) + 1
    needs_decision = sum(
        counts.get(classification, 0)
        for classification in ("label_only", "needs_policy", "source_bundle_needed", "unknown")
    )
    return {
        "pack_count": len(rows),
        "classification_counts": counts,
        "safe_to_write_count": counts.get("safe_to_write", 0),
        "needs_decision_count": needs_decision,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_sequence(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [str(item) for item in value]


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
