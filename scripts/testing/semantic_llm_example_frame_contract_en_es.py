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

from semantic_example_frame_evidence_support import (  # noqa: E402
    ACTIVE_RELATION_TYPES,
    PHRASE_RELATION_TYPES,
    SHADOW_RELATION_TYPES,
    normalize_evidence_batch_payload,
    row_family_key,
    row_metadata_text,
    row_roles,
)
from semantic_llm_prompt_downstream_en_es import DEFAULT_LLM_BATCH_JSON  # noqa: E402


DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_contract_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_contract_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether a semantic evidence batch satisfies the prototype-admission "
            "example-frame source contract."
        )
    )
    parser.add_argument(
        "--batch-json",
        type=Path,
        default=DEFAULT_LLM_BATCH_JSON,
        help="Raw intake batch or normalized evidence batch JSON.",
    )
    parser.add_argument(
        "--required-family-json",
        type=Path,
        default=None,
        help=(
            "Optional queue, inventory, or dataset JSON whose `families[].family_id` values "
            "must all be present in the batch coverage report."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="Exit non-zero when the batch is not contract-complete.",
    )
    return parser.parse_args()


def build_example_frame_contract_report(
    batch_payload: Mapping[str, object],
    *,
    batch_path: Path | None = None,
    required_family_keys: Sequence[str] | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
    normalized_batch = normalize_evidence_batch_payload(batch_payload)
    rows = [dict(row) for row in normalized_batch.get("rows", ()) if isinstance(row, Mapping)]
    required_keys = _unique_required_family_keys(required_family_keys)
    family_rows = _build_family_rows(rows, required_family_keys=required_keys)
    summary = _build_summary(family_rows)
    status = "ok" if summary["contract_complete"] else "review"
    report: dict[str, object] = {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": status,
        "pair": str(normalized_batch.get("pair") or "").strip() or "en-es",
        "batch_path": str(batch_path) if batch_path else "",
        "batch_id": str(normalized_batch.get("batch_id") or "").strip(),
        "source_id": str(normalized_batch.get("source_id") or "").strip(),
        "prompt_version": str(normalized_batch.get("prompt_version") or "").strip(),
        "model_id": str(normalized_batch.get("model_id") or "").strip(),
        "row_count": len(rows),
        "contract": {
            "required_relation_sets": {
                "active_examples": sorted(ACTIVE_RELATION_TYPES),
                "shadow_examples": sorted(SHADOW_RELATION_TYPES),
                "phrase_control_examples": sorted(PHRASE_RELATION_TYPES),
            },
            "required_batch_role_for_phrase_rows": "phrase_containment",
            "runtime_publishable_required": False,
            "required_family_keys": required_keys,
        },
        "summary": summary,
        "family_rows": family_rows,
        "recommendation": _build_recommendation(summary),
    }
    return report


def _build_family_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    required_family_keys: Sequence[str],
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        grouped.setdefault(row_family_key(row), []).append(row)
    family_rows = []
    family_keys = sorted({*grouped.keys(), *required_family_keys})
    for family_key in family_keys:
        family_rows.append(_build_family_row(family_key, grouped.get(family_key, ())))
    return family_rows


def _build_family_row(
    family_key: str,
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    active_rows = _relation_rows(rows, ACTIVE_RELATION_TYPES)
    shadow_rows = _relation_rows(rows, SHADOW_RELATION_TYPES)
    phrase_rows = _relation_rows(rows, PHRASE_RELATION_TYPES)
    runtime_publishable_rows = [
        str(row.get("row_id") or "").strip() for row in rows if bool(row.get("runtime_publishable"))
    ]
    phrase_rows_missing_role = [
        str(row.get("row_id") or "").strip()
        for row in phrase_rows
        if "phrase_containment" not in row_roles(row)
    ]
    missing_requirements = []
    if not active_rows:
        missing_requirements.append("active_examples")
    if not shadow_rows:
        missing_requirements.append("shadow_examples")
    if not phrase_rows:
        missing_requirements.append("phrase_control_examples")
    if phrase_rows_missing_role:
        missing_requirements.append("phrase_containment_role")
    if runtime_publishable_rows:
        missing_requirements.append("runtime_publishable_false")
    first_row = rows[0] if rows else {}
    return {
        "family_key": family_key,
        "family_id": row_metadata_text(first_row, "family_id"),
        "trigger": str(first_row.get("trigger") or "").strip(),
        "active_target": str(first_row.get("active_target") or "").strip(),
        "active_example_count": len(active_rows),
        "shadow_example_count": len(shadow_rows),
        "phrase_control_example_count": len(phrase_rows),
        "row_count": len(rows),
        "contract_complete": not missing_requirements,
        "missing_requirements": missing_requirements,
        "active_row_ids": _row_ids(active_rows),
        "shadow_row_ids": _row_ids(shadow_rows),
        "phrase_control_row_ids": _row_ids(phrase_rows),
        "phrase_rows_missing_role": phrase_rows_missing_role,
        "runtime_publishable_row_ids": runtime_publishable_rows,
    }


def _relation_rows(
    rows: Sequence[Mapping[str, object]],
    relation_types: frozenset[str],
) -> list[Mapping[str, object]]:
    return [row for row in rows if str(row.get("relation_type") or "").strip() in relation_types]


def _build_summary(family_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    family_count = len(family_rows)
    complete_count = sum(1 for row in family_rows if bool(row.get("contract_complete")))
    missing_active = [
        str(row.get("family_key") or "")
        for row in family_rows
        if int(row.get("active_example_count") or 0) <= 0
    ]
    missing_shadow = [
        str(row.get("family_key") or "")
        for row in family_rows
        if int(row.get("shadow_example_count") or 0) <= 0
    ]
    missing_phrase = [
        str(row.get("family_key") or "")
        for row in family_rows
        if int(row.get("phrase_control_example_count") or 0) <= 0
    ]
    phrase_role_issues = [
        str(row.get("family_key") or "")
        for row in family_rows
        if row.get("phrase_rows_missing_role")
    ]
    publishable_issues = [
        str(row.get("family_key") or "")
        for row in family_rows
        if row.get("runtime_publishable_row_ids")
    ]
    return {
        "families_total": family_count,
        "contract_complete_family_count": complete_count,
        "contract_complete": bool(family_count) and complete_count == family_count,
        "missing_active_family_keys": missing_active,
        "missing_shadow_family_keys": missing_shadow,
        "missing_phrase_control_family_keys": missing_phrase,
        "phrase_role_issue_family_keys": phrase_role_issues,
        "runtime_publishable_issue_family_keys": publishable_issues,
    }


def _build_recommendation(summary: Mapping[str, object]) -> str:
    if bool(summary.get("contract_complete")):
        return (
            "This batch satisfies the no-spend example-frame source contract: every family "
            "has active, shadow, and phrase-control evidence while remaining non-publishable."
        )
    missing_shadow = len(_as_sequence(summary.get("missing_shadow_family_keys")))
    missing_phrase = len(_as_sequence(summary.get("missing_phrase_control_family_keys")))
    missing_active = len(_as_sequence(summary.get("missing_active_family_keys")))
    return (
        "Do not treat this batch as promotion-relevant for prototype admission. Missing "
        f"families: active={missing_active}, shadow={missing_shadow}, "
        f"phrase_control={missing_phrase}. Generate or ingest active, shadow, and "
        "phrase-control rows together before downstream spend."
    )


def render_example_frame_contract_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es Semantic Example-Frame Contract",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Source: `{report.get('source_id', '')}`",
        f"- Rows: `{report.get('row_count', 0)}`",
        f"- Complete families: `{summary.get('contract_complete_family_count', 0)}` / `{summary.get('families_total', 0)}`",
        "",
        "## Family Coverage",
        "",
        "| Family | Active | Shadow | Phrase Control | Status | Missing |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in report.get("family_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('family_key', '')}`",
                    str(row.get("active_example_count", 0)),
                    str(row.get("shadow_example_count", 0)),
                    str(row.get("phrase_control_example_count", 0)),
                    "`ok`" if bool(row.get("contract_complete")) else "`review`",
                    _join_code(row.get("missing_requirements")),
                ]
            )
            + " |"
        )
    if not report.get("family_rows"):
        lines.append("| `none` | 0 | 0 | 0 | `review` | `no_families` |")

    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _row_ids(rows: Sequence[Mapping[str, object]]) -> list[str]:
    return [
        str(row.get("row_id") or "").strip() for row in rows if str(row.get("row_id") or "").strip()
    ]


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _join_code(value: object) -> str:
    values = [str(item).strip() for item in _as_sequence(value) if str(item).strip()]
    return ", ".join(f"`{item}`" for item in values) if values else "none"


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _required_family_keys_from_payload(payload: Mapping[str, object]) -> list[str]:
    families = payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
        raise ValueError("required-family JSON must contain a `families` array.")
    keys: list[str] = []
    for family in families:
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        if family_id and family_id not in keys:
            keys.append(family_id)
    if not keys:
        raise ValueError("required-family JSON did not contain any `families[].family_id` values.")
    return keys


def _unique_required_family_keys(value: Sequence[str] | None) -> list[str]:
    keys: list[str] = []
    for item in value or ():
        text = str(item or "").strip()
        if text and text not in keys:
            keys.append(text)
    return keys


def main() -> int:
    args = _parse_args()
    batch_payload = _load_json(args.batch_json)
    required_family_keys = (
        _required_family_keys_from_payload(_load_json(args.required_family_json))
        if args.required_family_json
        else []
    )
    report = build_example_frame_contract_report(
        batch_payload,
        batch_path=args.batch_json,
        required_family_keys=required_family_keys,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_example_frame_contract_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
