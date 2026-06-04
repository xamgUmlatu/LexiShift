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
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_example_frame_evidence_support import normalize_evidence_batch_payload  # noqa: E402
from semantic_llm_prompt_downstream_en_es import _load_json  # noqa: E402


DEFAULT_BASE_BATCH_JSON = (
    TEST_OUTPUTS_ROOT
    / "experiments"
    / "semantic_example_frame_batches"
    / "en-es-reverse-aux-example-frames-v10-20260425a_normalized_evidence.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_example_frame_batch_merge_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_example_frame_batch_merge_latest.md"
DEFAULT_MERGED_BATCH_OUT = (
    TEST_OUTPUTS_ROOT
    / "experiments"
    / "semantic_example_frame_batches"
    / "en-es-reverse-aux-plus-llm-missing-rows-latest_normalized_evidence.json"
)
DEFAULT_BATCH_ID = "en-es:example-frame-composite:reverse-aux-plus-llm-missing-rows-latest"
DEFAULT_SOURCE_ID = "reverse_aux_plus_llm_example_frame_missing_rows"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge normalized example-frame evidence batches into one virtual composite batch "
            "for contract/prototype probes."
        )
    )
    parser.add_argument("--base-batch-json", type=Path, default=DEFAULT_BASE_BATCH_JSON)
    parser.add_argument(
        "--add-batch-json",
        type=Path,
        action="append",
        default=[],
        help="Additional raw intake or normalized evidence batch. Repeat for multiple batches.",
    )
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--merged-batch-out", type=Path, default=DEFAULT_MERGED_BATCH_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_merged_example_frame_batch_report(
    *,
    base_batch_payload: Mapping[str, object],
    add_batch_payloads: Sequence[Mapping[str, object]],
    batch_id: str = DEFAULT_BATCH_ID,
    source_id: str = DEFAULT_SOURCE_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    normalized_batches = [
        normalize_evidence_batch_payload(base_batch_payload),
        *(normalize_evidence_batch_payload(payload) for payload in add_batch_payloads),
    ]
    rows: list[dict[str, object]] = []
    seen_keys: set[tuple[str, str, str, str]] = set()
    component_rows: list[dict[str, object]] = []
    for component_index, batch in enumerate(normalized_batches, start=1):
        batch_rows = [dict(row) for row in batch.get("rows", ()) if isinstance(row, Mapping)]
        accepted_count = 0
        duplicate_count = 0
        for row in batch_rows:
            row_key = _row_key(row)
            if row_key in seen_keys:
                duplicate_count += 1
                continue
            seen_keys.add(row_key)
            rows.append(row)
            accepted_count += 1
        component_rows.append(
            {
                "component_index": component_index,
                "batch_id": str(batch.get("batch_id") or "").strip(),
                "source_id": str(batch.get("source_id") or "").strip(),
                "source_type": str(batch.get("source_type") or "").strip(),
                "source_family": str(batch.get("source_family") or "").strip(),
                "input_row_count": len(batch_rows),
                "accepted_row_count": accepted_count,
                "duplicate_row_count": duplicate_count,
            }
        )

    merged_batch = {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_composite_v1",
        "batch_id": str(batch_id or "").strip() or DEFAULT_BATCH_ID,
        "pair": _first_text(normalized_batches, "pair") or "en-es",
        "source_type": "internal",
        "source_id": str(source_id or "").strip() or DEFAULT_SOURCE_ID,
        "source_family": "internal_rulegen_artifact",
        "roles": _merge_roles(rows),
        "generated_at": generated_at,
        "ingested_at": generated_at,
        "review_state": "unreviewed",
        "model_id": "mixed",
        "prompt_version": "example-frame-composite-v1",
        "row_count": len(rows),
        "rows": rows,
        "provenance": {
            "component_batches": component_rows,
        },
    }
    report = {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ok" if rows else "empty",
        "batch_id": merged_batch["batch_id"],
        "source_id": merged_batch["source_id"],
        "summary": _build_summary(rows, component_rows),
        "component_batches": component_rows,
        "merged_batch": merged_batch,
    }
    return report


def render_merged_example_frame_batch_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es Example-Frame Batch Merge",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Batch id: `{report.get('batch_id', '')}`",
        f"- Source id: `{report.get('source_id', '')}`",
        "",
        "## Summary",
        "",
        f"- Components: `{summary.get('component_count', 0)}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Relations: `{json.dumps(summary.get('relation_counts', {}), sort_keys=True)}`",
        "",
        "## Components",
        "",
        "| Component | Batch | Source | Rows In | Rows Kept | Duplicates |",
        "| ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for row in report.get("component_batches", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("component_index", "")),
                    f"`{row.get('batch_id', '')}`",
                    f"`{row.get('source_id', '')}`",
                    str(row.get("input_row_count", 0)),
                    str(row.get("accepted_row_count", 0)),
                    str(row.get("duplicate_row_count", 0)),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _build_summary(
    rows: Sequence[Mapping[str, object]],
    component_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    relation_counts: dict[str, int] = {}
    families: set[str] = set()
    for row in rows:
        relation_type = str(row.get("relation_type") or "").strip()
        relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1
        family_id = _row_family_id(row)
        if family_id:
            families.add(family_id)
    return {
        "component_count": len(component_rows),
        "row_count": len(rows),
        "family_count": len(families),
        "relation_counts": relation_counts,
    }


def _row_key(row: Mapping[str, object]) -> tuple[str, str, str, str]:
    return (
        str(row.get("source_id") or "").strip(),
        str(row.get("row_id") or "").strip(),
        str(row.get("relation_type") or "").strip(),
        str(row.get("evidence_text") or "").strip(),
    )


def _row_family_id(row: Mapping[str, object]) -> str:
    metadata = row.get("metadata")
    return str(metadata.get("family_id") or "").strip() if isinstance(metadata, Mapping) else ""


def _merge_roles(rows: Sequence[Mapping[str, object]]) -> list[str]:
    merged: list[str] = []
    for row in rows:
        roles = row.get("roles")
        if not isinstance(roles, Sequence) or isinstance(roles, (str, bytes)):
            continue
        for role in roles:
            text = str(role).strip()
            if text and text not in merged:
                merged.append(text)
    return merged or ["discrimination"]


def _first_text(batches: Sequence[Mapping[str, object]], key: str) -> str:
    for batch in batches:
        text = str(batch.get(key) or "").strip()
        if text:
            return text
    return ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    if not args.add_batch_json:
        raise SystemExit("At least one --add-batch-json is required.")
    report = build_merged_example_frame_batch_report(
        base_batch_payload=_load_json(args.base_batch_json),
        add_batch_payloads=[_load_json(path) for path in args.add_batch_json],
        batch_id=args.batch_id,
        source_id=args.source_id,
    )
    merged_batch = report["merged_batch"]
    _write_json(args.merged_batch_out, merged_batch)
    _write_json(
        args.json_out, {key: value for key, value in report.items() if key != "merged_batch"}
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_merged_example_frame_batch_markdown(report), encoding="utf-8"
    )
    print(f"Wrote merged batch to {args.merged_batch_out}")
    print(f"Wrote summary JSON to {args.json_out}")
    print(f"Wrote summary Markdown to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
