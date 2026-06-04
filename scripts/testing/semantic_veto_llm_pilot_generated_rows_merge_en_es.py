#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_veto_llm_pilot_admission_en_es import (  # noqa: E402
    _as_mapping,
    _load_json,
    _mapping_rows,
)


DEFAULT_GENERATION_REQUESTS_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_llm_pilot_generation_requests_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_llm_pilot_generated_rows_merge_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_llm_pilot_generated_rows_merge_en_es_latest.md"
)
DEFAULT_GENERATED_ROWS_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_veto_llm_pilot_generated_rows_en_es_latest.json"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Assemble an en-es semantic-veto LLM pilot generated-row payload from a "
            "base batch plus targeted repair batches."
        )
    )
    parser.add_argument("--base-generated-rows-json", type=Path, required=True)
    parser.add_argument(
        "--overlay-generated-rows-json",
        type=Path,
        action="append",
        default=[],
        help="Repair payloads applied in order; later payloads replace earlier rows.",
    )
    parser.add_argument(
        "--generation-requests-json",
        type=Path,
        default=DEFAULT_GENERATION_REQUESTS_JSON,
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--generated-rows-out", type=Path, default=DEFAULT_GENERATED_ROWS_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bundle = build_semantic_veto_llm_pilot_generated_rows_merge_bundle(
        base_generated_rows_payload=_load_json(args.base_generated_rows_json),
        overlay_generated_rows_payloads=[
            _load_json(path) for path in args.overlay_generated_rows_json
        ],
        generation_requests_payload=_load_json(args.generation_requests_json),
        base_generated_rows_path=args.base_generated_rows_json,
        overlay_generated_rows_paths=args.overlay_generated_rows_json,
        generation_requests_path=args.generation_requests_json,
    )
    write_semantic_veto_llm_pilot_generated_rows_merge_bundle(
        bundle=bundle,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
        generated_rows_out=args.generated_rows_out,
    )
    report = bundle["report"]
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    print(f"Wrote assembled generated rows to {args.generated_rows_out}")
    print(f"Merge status: {report['status']}")
    print(f"Rows: {report['summary']['assembled_row_count']}")
    return 0


def build_semantic_veto_llm_pilot_generated_rows_merge_bundle(
    *,
    base_generated_rows_payload: Mapping[str, object],
    overlay_generated_rows_payloads: Sequence[Mapping[str, object]],
    generation_requests_payload: Mapping[str, object],
    base_generated_rows_path: Path | None = None,
    overlay_generated_rows_paths: Sequence[Path] | None = None,
    generation_requests_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    overlay_paths = list(overlay_generated_rows_paths or [])
    rows_by_id: dict[str, dict[str, object]] = {}
    row_source_by_id: dict[str, str] = {}
    replacements: list[dict[str, object]] = []
    _apply_payload_rows(
        payload=base_generated_rows_payload,
        rows_by_id=rows_by_id,
        row_source_by_id=row_source_by_id,
        source_path=base_generated_rows_path,
        replacements=replacements,
        source_kind="base",
    )
    for index, overlay_payload in enumerate(overlay_generated_rows_payloads):
        source_path = overlay_paths[index] if index < len(overlay_paths) else None
        _apply_payload_rows(
            payload=overlay_payload,
            rows_by_id=rows_by_id,
            row_source_by_id=row_source_by_id,
            source_path=source_path,
            replacements=replacements,
            source_kind="overlay",
        )

    expected_row_ids = _expected_row_ids(
        base_generated_rows_payload=base_generated_rows_payload,
        generation_requests_payload=generation_requests_payload,
    )
    request_ids = _selected_request_ids(
        base_generated_rows_payload=base_generated_rows_payload,
        generation_requests_payload=generation_requests_payload,
    )
    expected_set = set(expected_row_ids)
    row_ids = set(rows_by_id)
    missing_row_ids = sorted(expected_set - row_ids)
    unexpected_row_ids = sorted(row_ids - expected_set)
    ordered_row_ids = [row_id for row_id in expected_row_ids if row_id in rows_by_id]
    ordered_row_ids.extend(row_id for row_id in sorted(unexpected_row_ids))
    assembled_rows = [rows_by_id[row_id] for row_id in ordered_row_ids]
    report = {
        "schema_version": 1,
        "status": "ok" if not missing_row_ids and not unexpected_row_ids else "review",
        "generated_at": generated_at,
        "pair": str(base_generated_rows_payload.get("pair") or ""),
        "base_generated_rows_json": _display_path(base_generated_rows_path),
        "overlay_generated_rows_json": [_display_path(path) for path in overlay_paths],
        "generation_requests_json": _display_path(generation_requests_path),
        "summary": {
            "expected_row_count": len(expected_row_ids),
            "assembled_row_count": len(assembled_rows),
            "base_row_count": len(_mapping_rows(base_generated_rows_payload.get("rows"))),
            "overlay_payload_count": len(overlay_generated_rows_payloads),
            "replacement_count": len(replacements),
            "missing_row_count": len(missing_row_ids),
            "unexpected_row_count": len(unexpected_row_ids),
        },
        "missing_row_ids": missing_row_ids,
        "unexpected_row_ids": unexpected_row_ids,
        "replacements": replacements,
        "row_sources": [
            {"row_id": row_id, "source": row_source_by_id.get(row_id, "")}
            for row_id in ordered_row_ids
        ],
    }
    assembled_payload = {
        **dict(base_generated_rows_payload),
        "generated_at": generated_at,
        "selected_request_ids": request_ids,
        "selected_expected_row_ids": expected_row_ids,
        "rows": assembled_rows,
        "assembly": {
            "generated_at": generated_at,
            "base_generated_rows_json": _display_path(base_generated_rows_path),
            "overlay_generated_rows_json": [_display_path(path) for path in overlay_paths],
            "generation_requests_json": _display_path(generation_requests_path),
            "replacement_count": len(replacements),
            "replacements": replacements,
            "row_sources": report["row_sources"],
        },
    }
    return {
        "report": report,
        "generated_rows_payload": assembled_payload,
    }


def write_semantic_veto_llm_pilot_generated_rows_merge_bundle(
    *,
    bundle: Mapping[str, object],
    json_out: Path,
    markdown_out: Path,
    generated_rows_out: Path,
) -> None:
    report = _as_mapping(bundle.get("report"))
    generated_rows_payload = _as_mapping(bundle.get("generated_rows_payload"))
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(render_generated_rows_merge_markdown(report), encoding="utf-8")
    generated_rows_out.parent.mkdir(parents=True, exist_ok=True)
    generated_rows_out.write_text(
        json.dumps(generated_rows_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def render_generated_rows_merge_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto LLM Pilot Generated Row Assembly",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Base rows: `{report.get('base_generated_rows_json', '')}`",
        f"- Generation requests: `{report.get('generation_requests_json', '')}`",
        "",
        "## Summary",
        "",
        f"- Expected rows: `{summary.get('expected_row_count', 0)}`",
        f"- Assembled rows: `{summary.get('assembled_row_count', 0)}`",
        f"- Base rows: `{summary.get('base_row_count', 0)}`",
        f"- Overlay payloads: `{summary.get('overlay_payload_count', 0)}`",
        f"- Replacements: `{summary.get('replacement_count', 0)}`",
        f"- Missing rows: `{summary.get('missing_row_count', 0)}`",
        f"- Unexpected rows: `{summary.get('unexpected_row_count', 0)}`",
        "",
        "## Overlays",
        "",
    ]
    overlays = [str(path) for path in report.get("overlay_generated_rows_json") or []]
    if overlays:
        lines.extend(f"- `{path}`" for path in overlays)
    else:
        lines.append("- `none`")
    lines.extend(["", "## Replacements", ""])
    replacements = _mapping_rows(report.get("replacements"))
    if replacements:
        lines.extend(
            (
                f"- `{row.get('row_id', '')}` from `{row.get('old_source', '')}` "
                f"to `{row.get('new_source', '')}`"
            )
            for row in replacements
        )
    else:
        lines.append("- `none`")
    lines.extend(["", "## Gaps", ""])
    lines.append(f"- Missing: `{', '.join(report.get('missing_row_ids') or []) or 'none'}`")
    lines.append(f"- Unexpected: `{', '.join(report.get('unexpected_row_ids') or []) or 'none'}`")
    return "\n".join(lines) + "\n"


def _apply_payload_rows(
    *,
    payload: Mapping[str, object],
    rows_by_id: dict[str, dict[str, object]],
    row_source_by_id: dict[str, str],
    source_path: Path | None,
    replacements: list[dict[str, object]],
    source_kind: str,
) -> None:
    source = _display_path(source_path) or source_kind
    for row in _mapping_rows(payload.get("rows")):
        row_id = str(row.get("row_id") or "").strip()
        if not row_id:
            continue
        if row_id in rows_by_id:
            replacements.append(
                {
                    "row_id": row_id,
                    "old_source": row_source_by_id.get(row_id, ""),
                    "new_source": source,
                }
            )
        rows_by_id[row_id] = dict(row)
        row_source_by_id[row_id] = source


def _expected_row_ids(
    *,
    base_generated_rows_payload: Mapping[str, object],
    generation_requests_payload: Mapping[str, object],
) -> list[str]:
    request_ids = [
        str(row.get("expected_row_id") or "").strip()
        for row in _mapping_rows(generation_requests_payload.get("requests"))
        if str(row.get("expected_row_id") or "").strip()
    ]
    if request_ids:
        return request_ids
    selected_ids = [
        str(row_id).strip()
        for row_id in base_generated_rows_payload.get("selected_expected_row_ids") or []
        if str(row_id).strip()
    ]
    return selected_ids


def _selected_request_ids(
    *,
    base_generated_rows_payload: Mapping[str, object],
    generation_requests_payload: Mapping[str, object],
) -> list[str]:
    request_ids = [
        str(row.get("request_id") or "").strip()
        for row in _mapping_rows(generation_requests_payload.get("requests"))
        if str(row.get("request_id") or "").strip()
    ]
    if request_ids:
        return request_ids
    selected_ids = [
        str(request_id).strip()
        for request_id in base_generated_rows_payload.get("selected_request_ids") or []
        if str(request_id).strip()
    ]
    return selected_ids


def _display_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
