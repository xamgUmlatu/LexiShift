#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
)
from semantic_decision_rule_matrix_context import (  # noqa: E402
    _build_matrix_context_views,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
EXAMPLE_BATCH_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"

DEFAULT_BATCH_PATHS = (
    EXAMPLE_BATCH_ROOT
    / "en-es-reverse-aux-wordnet-def-example-all-v10-20260425a_cycle_sense_admitted_normalized_evidence.json",
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_source_row_alignment_audit_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_source_row_alignment_audit_en_es_latest.md"

WORD_RE = re.compile(r"[A-Za-z]+")


def main() -> int:
    args = _parse_args()
    report = build_source_row_alignment_report(
        batch_paths=args.batch,
        window_tokens=args.window_tokens,
        mask_token=args.mask_token,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_source_row_alignment_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_source_row_alignment_report(
    *,
    batch_paths: Sequence[Path],
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    batch_summaries: list[dict[str, object]] = []
    for batch_path in batch_paths:
        payload = _load_json(batch_path)
        if not isinstance(payload, Mapping):
            payload = {}
        raw_rows = payload.get("rows")
        if not isinstance(raw_rows, Sequence) or isinstance(raw_rows, (str, bytes)):
            raw_rows = ()
        batch_row_count = 0
        attached_like_count = 0
        for raw_row in raw_rows:
            if not isinstance(raw_row, Mapping):
                continue
            row = _alignment_row(
                raw_row,
                batch_path=batch_path,
                window_tokens=window_tokens,
                mask_token=mask_token,
            )
            if not row:
                continue
            rows.append(row)
            batch_row_count += 1
            if row["selector_ready"]:
                attached_like_count += 1
        batch_summaries.append(
            {
                "path": str(batch_path),
                "sha256": _file_sha256(batch_path),
                "declared_row_count": int(payload.get("row_count") or len(raw_rows)),
                "audited_row_count": batch_row_count,
                "selector_ready_row_count": attached_like_count,
            }
        )

    summary = _build_summary(rows)
    family_rows = _build_family_rows(rows)
    return {
        "schema_version": 1,
        "status": "ok",
        "generated_at": _utc_now(),
        "batch_summaries": batch_summaries,
        "summary": summary,
        "family_rows": family_rows,
        "audited_rows": rows,
        "sample_rows": rows[:40],
        "recommendation": _recommendation(summary),
    }


def render_source_row_alignment_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es Source Row Alignment Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Rows audited: `{summary.get('row_count', 0)}`",
        f"- Selector-ready rows: `{summary.get('selector_ready_row_count', 0)}`",
        f"- Trigger-present rows: `{summary.get('trigger_present_row_count', 0)}`",
        f"- Two-sided trigger-frame rows: `{summary.get('two_sided_frame_row_count', 0)}`",
        "",
        "## Recommendation",
        "",
        str(report.get("recommendation") or ""),
        "",
        "## Batch Coverage",
        "",
        "| Batch | Rows | Selector-Ready | SHA-256 |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in _mapping_rows(report.get("batch_summaries")):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row.get("path") or ""),
                    str(int(row.get("audited_row_count") or 0)),
                    str(int(row.get("selector_ready_row_count") or 0)),
                    str(row.get("sha256") or ""),
                )
            )
            + " |"
        )

    lines.extend(["", "## Source Families", ""])
    lines.append("| Source Family | Rows | Trigger-Present | Selector-Ready |")
    lines.append("| --- | ---: | ---: | ---: |")
    for row in _mapping_rows(summary.get("source_family_counts")):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row.get("source_family") or ""),
                    str(int(row.get("row_count") or 0)),
                    str(int(row.get("trigger_present_row_count") or 0)),
                    str(int(row.get("selector_ready_row_count") or 0)),
                )
            )
            + " |"
        )

    lines.extend(["", "## Relation Types", ""])
    lines.append("| Relation | Rows | Trigger-Present | Selector-Ready |")
    lines.append("| --- | ---: | ---: | ---: |")
    for row in _mapping_rows(summary.get("relation_type_counts")):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row.get("relation_type") or ""),
                    str(int(row.get("row_count") or 0)),
                    str(int(row.get("trigger_present_row_count") or 0)),
                    str(int(row.get("selector_ready_row_count") or 0)),
                )
            )
            + " |"
        )

    lines.extend(["", "## Family Readiness", ""])
    lines.append(
        "| Family | Active Rows | Shadow Rows | Active Selector-Ready | Shadow Selector-Ready | Ready For Dynamic Selection |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | --- |")
    for row in _mapping_rows(report.get("family_rows")):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row.get("family_id") or ""),
                    str(int(row.get("active_row_count") or 0)),
                    str(int(row.get("shadow_row_count") or 0)),
                    str(int(row.get("active_selector_ready_count") or 0)),
                    str(int(row.get("shadow_selector_ready_count") or 0)),
                    "`yes`" if row.get("ready_for_dynamic_selection") else "`no`",
                )
            )
            + " |"
        )

    lines.extend(["", "## Sample Rows", ""])
    lines.append("| Row | Relation | Trigger Present | Selector-Ready | Text |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in _mapping_rows(report.get("sample_rows"))[:20]:
        lines.append(
            "| "
            + " | ".join(
                (
                    _escape_md(str(row.get("row_id") or "")),
                    _escape_md(str(row.get("relation_type") or "")),
                    "`yes`" if row.get("trigger_present") else "`no`",
                    "`yes`" if row.get("selector_ready") else "`no`",
                    _escape_md(str(row.get("evidence_text") or "")),
                )
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _alignment_row(
    raw_row: Mapping[str, object],
    *,
    batch_path: Path,
    window_tokens: int,
    mask_token: str,
) -> dict[str, object]:
    evidence_text = str(raw_row.get("evidence_text") or "").strip()
    trigger = str(raw_row.get("normalized_trigger") or raw_row.get("trigger") or "").strip()
    if not evidence_text:
        return {}
    views = _build_matrix_context_views(
        evidence_text,
        source_phrase=trigger,
        mask_token=mask_token,
        window_tokens=window_tokens,
    )
    trigger_present = _contains_token(evidence_text, trigger)
    before_after = str(views.get("before_after_slot_context") or "").strip()
    two_sided_frame = "bridge=" in before_after
    selector_ready = bool(trigger_present and before_after)
    metadata = raw_row.get("metadata") if isinstance(raw_row.get("metadata"), Mapping) else {}
    relation_type = str(raw_row.get("relation_type") or "").strip()
    return {
        "batch_path": str(batch_path),
        "row_id": str(raw_row.get("row_id") or raw_row.get("evidence_id") or "").strip(),
        "evidence_id": str(raw_row.get("evidence_id") or "").strip(),
        "family_id": str(metadata.get("family_id") or "").strip(),
        "candidate_sense_id": _candidate_sense_id(raw_row),
        "source_family": str(raw_row.get("source_family") or "source_row").strip(),
        "source_id": str(raw_row.get("source_id") or "").strip(),
        "source_type": str(raw_row.get("source_type") or "").strip(),
        "relation_type": relation_type,
        "trigger": trigger,
        "trigger_present": trigger_present,
        "selector_ready": selector_ready,
        "two_sided_frame": two_sided_frame,
        "word_count": len(WORD_RE.findall(evidence_text)),
        "evidence_text": evidence_text,
        "before_after_slot_context": before_after,
        "surface_frame_context": str(views.get("surface_frame_context") or "").strip(),
        "dependency_role_context": str(views.get("dependency_role_context") or "").strip(),
    }


def _build_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    source_counts = _counter_rows(rows, "source_family")
    relation_counts = _counter_rows(rows, "relation_type")
    return {
        "row_count": len(rows),
        "trigger_present_row_count": sum(1 for row in rows if row.get("trigger_present")),
        "selector_ready_row_count": sum(1 for row in rows if row.get("selector_ready")),
        "two_sided_frame_row_count": sum(1 for row in rows if row.get("two_sided_frame")),
        "source_family_counts": source_counts,
        "relation_type_counts": relation_counts,
    }


def _counter_rows(rows: Sequence[Mapping[str, object]], key: str) -> list[dict[str, object]]:
    counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "row_count": 0,
            "trigger_present_row_count": 0,
            "selector_ready_row_count": 0,
        }
    )
    for row in rows:
        bucket = str(row.get(key) or "unknown").strip() or "unknown"
        counts[bucket]["row_count"] += 1
        if row.get("trigger_present"):
            counts[bucket]["trigger_present_row_count"] += 1
        if row.get("selector_ready"):
            counts[bucket]["selector_ready_row_count"] += 1
    label_key = "source_family" if key == "source_family" else "relation_type"
    return [
        {label_key: bucket, **values}
        for bucket, values in sorted(
            counts.items(),
            key=lambda item: (-item[1]["row_count"], item[0]),
        )
    ]


def _build_family_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    family_rows: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "active_row_count": 0,
            "shadow_row_count": 0,
            "active_selector_ready_count": 0,
            "shadow_selector_ready_count": 0,
        }
    )
    for row in rows:
        family_id = str(row.get("family_id") or "unknown").strip() or "unknown"
        relation_type = str(row.get("relation_type") or "").strip()
        is_active = relation_type == "anchor_cue"
        bucket = "active" if is_active else "shadow"
        family_rows[family_id][f"{bucket}_row_count"] += 1
        if row.get("selector_ready"):
            family_rows[family_id][f"{bucket}_selector_ready_count"] += 1
    result = []
    for family_id, counts in family_rows.items():
        result.append(
            {
                "family_id": family_id,
                **counts,
                "ready_for_dynamic_selection": bool(
                    counts["active_selector_ready_count"] and counts["shadow_selector_ready_count"]
                ),
            }
        )
    return sorted(
        result,
        key=lambda row: (
            bool(row.get("ready_for_dynamic_selection")),
            -int(row.get("active_selector_ready_count") or 0)
            - int(row.get("shadow_selector_ready_count") or 0),
            str(row.get("family_id") or ""),
        ),
    )


def _recommendation(summary: Mapping[str, object]) -> str:
    row_count = int(summary.get("row_count") or 0)
    selector_ready = int(summary.get("selector_ready_row_count") or 0)
    if not row_count:
        return "No source rows were available to audit."
    if selector_ready == 0:
        return (
            "The audited source rows are not suitable for context-conditioned frame selection: "
            "none contain the trigger with usable before/after context. Build sentence-like "
            "active and shadow rows before re-running selector bakeoffs."
        )
    ratio = selector_ready / row_count
    if ratio < 0.5:
        return (
            "The audited source rows only partially support context-conditioned selection. "
            "Use them for sparse semantic support, but build trigger-bearing sentence-frame "
            "rows before treating dynamic evidence selection as fairly tested."
        )
    return (
        "The audited source rows have enough trigger-bearing frame coverage for a context-"
        "conditioned selector bakeoff."
    )


def _contains_token(text: str, token: str) -> bool:
    wanted = str(token or "").strip().lower()
    if not wanted:
        return False
    return wanted in {match.group(0).lower() for match in WORD_RE.finditer(text)}


def _candidate_sense_id(row: Mapping[str, object]) -> str:
    metadata = row.get("metadata")
    if isinstance(metadata, Mapping):
        value = str(metadata.get("candidate_sense_id") or "").strip()
        if value:
            return value
    hint = row.get("candidate_sense_hint")
    if isinstance(hint, Mapping):
        return str(hint.get("target_key") or "").strip()
    return ""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit whether source evidence rows contain trigger-bearing frames."
    )
    parser.add_argument("--batch", type=Path, action="append", default=[])
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--window-tokens", type=int, default=DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS
    )
    parser.add_argument("--mask-token", default=DEFAULT_SENTENCE_VETO_MASK_TOKEN)
    args = parser.parse_args()
    if not args.batch:
        args.batch = list(DEFAULT_BATCH_PATHS)
    args.batch = [_resolve_path(path) for path in args.batch]
    return args


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
