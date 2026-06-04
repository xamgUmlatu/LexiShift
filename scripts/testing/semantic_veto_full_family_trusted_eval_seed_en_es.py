#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_INPUTS_ROOT = DOCS_ROOT / "test_inputs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
SCRIPT_ROOT = Path(__file__).resolve().parent
for candidate in (str(SCRIPT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _load_json,
    _repo_path,
    _resolve_repo_path,
)


DEFAULT_REPAIRED_DATASET_JSON = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_pilot_v1.json"
)
DEFAULT_DATASET_OUT = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_trusted_eval_seed_v1.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_trusted_eval_seed_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_trusted_eval_seed_en_es_latest.md"
)
DEFAULT_DATASET_ID = "en_es_full_family_trusted_eval_seed_v1"
APPROVAL_ID = "user_step7_repaired_pilot_approval_2026_05_07"
APPROVAL_NOTE = (
    "User approved the agent-reviewed and repaired pilot rows in chat after the "
    "repair pass; deferred unaudited mappings remain excluded."
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Promote the repaired full-family pilot rows into a trusted eval seed "
            "after explicit user approval. Does not include deferred mappings."
        )
    )
    parser.add_argument("--repaired-dataset-json", type=Path, default=DEFAULT_REPAIRED_DATASET_JSON)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repaired_path = _resolve_repo_path(args.repaired_dataset_json)
    dataset_path = _resolve_repo_path(args.dataset_out)
    json_path = _resolve_repo_path(args.json_out)
    markdown_path = _resolve_repo_path(args.markdown_out)
    # Validate runtime shape, but use the raw payload so repair metadata remains
    # available for the trusted-seed report.
    load_sentence_veto_dataset(repaired_path)
    report, dataset = build_trusted_eval_seed_report(
        repaired_payload=_load_json(repaired_path),
        repaired_path=repaired_path,
        dataset_path=dataset_path,
    )
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_trusted_eval_seed_markdown(report), encoding="utf-8")
    print(f"Wrote dataset artifact to {dataset_path}")
    print(f"Wrote JSON artifact to {json_path}")
    print(f"Wrote Markdown artifact to {markdown_path}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_trusted_eval_seed_report(
    *,
    repaired_payload: Mapping[str, object],
    repaired_path: Path | None = None,
    dataset_path: Path | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    generated_at = generated_at or _utc_now()
    families = [_approved_family(row) for row in _mapping_rows(repaired_payload.get("families"))]
    deferred_families = [
        dict(row) for row in _mapping_rows(repaired_payload.get("deferred_families"))
    ]
    dataset = {
        "schema_version": 1,
        "pair": str(repaired_payload.get("pair") or "en-es"),
        "dataset_id": DEFAULT_DATASET_ID,
        "description": (
            "Trusted eval seed from the repaired full-family pilot after explicit "
            "user approval. Deferred unaudited mappings are not included."
        ),
        "manual_review_state": "approved_by_user",
        "approval": {
            "approval_id": APPROVAL_ID,
            "approval_note": APPROVAL_NOTE,
            "approved_source_dataset": _repo_path(repaired_path),
            "approved_rows": "all_repaired_rows",
            "excluded_rows": "deferred_source_target_mapping_audit_rows",
        },
        "families": families,
        "excluded_families": deferred_families,
    }
    case_rows = [case for family in families for case in _mapping_rows(family.get("cases"))]
    summary = {
        "trusted_family_count": len(families),
        "trusted_case_count": len(case_rows),
        "excluded_family_count": len(deferred_families),
        "manual_review_state": "approved_by_user",
        "row_quality_status": "trusted",
        "case_type_counts": dict(
            sorted(Counter(_first_dim(case, "manual_case_type") for case in case_rows).items())
        ),
        "source_band_case_counts": dict(
            sorted(Counter(_first_dim(case, "source_zipf_band_en") for case in case_rows).items())
        ),
        "family_repair_status_counts": dict(
            sorted(
                Counter(
                    str(_as_mapping(family.get("repair_metadata")).get("family_repair_status"))
                    for family in families
                ).items()
            )
        ),
    }
    checks = _checks(dataset)
    issues = [key for key, value in checks.items() if not value]
    report = {
        "schema_version": 1,
        "pair": str(dataset.get("pair") or "en-es"),
        "status": "review" if issues else "ok",
        "decision": (
            "full_family_trusted_eval_seed_ready_for_scoring"
            if not issues
            else "full_family_trusted_eval_seed_needs_repair"
        ),
        "generated_at": generated_at,
        "inputs": {
            "repaired_dataset_path": _repo_path(repaired_path),
            "repaired_dataset_id": str(repaired_payload.get("dataset_id") or ""),
            "approval_id": APPROVAL_ID,
        },
        "outputs": {
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": DEFAULT_DATASET_ID,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "score_promotion": "none",
            "approval_boundary": (
                "User approval applies only to repaired pilot rows. Deferred source-target "
                "mapping audit rows remain excluded."
            ),
            "locked_eval_boundary": (
                "This is a trusted seed, not a discovery/locked split. Do not tune "
                "thresholds on it and then claim locked-eval performance."
            ),
        },
        "summary": summary,
        "e2e_checks": checks,
        "family_rows": [_family_report_row(family) for family in families],
        "excluded_families": deferred_families,
        "next_steps": [
            "Score this trusted seed to establish the post-approval baseline.",
            "Create a separate discovery/locked split before threshold or scorer tuning.",
            "Audit excluded source-target mappings before adding them to any trusted lane.",
        ],
    }
    return report, dataset


def render_trusted_eval_seed_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Full-Family Trusted Eval Seed",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{_as_mapping(report.get('outputs')).get('dataset_path', '')}`",
        f"- Trusted families: `{summary.get('trusted_family_count', 0)}`",
        f"- Trusted cases: `{summary.get('trusted_case_count', 0)}`",
        f"- Excluded families: `{summary.get('excluded_family_count', 0)}`",
        "",
        "## Approval Boundary",
        "",
        str(_as_mapping(report.get("methodology")).get("approval_boundary") or ""),
        "",
        str(_as_mapping(report.get("methodology")).get("locked_eval_boundary") or ""),
        "",
        "## Summary",
        "",
        _summary_table(summary),
        "",
        "## Checks",
        "",
        "| Check | Value |",
        "| --- | --- |",
    ]
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(key)}` | `{value}` |")
    lines.extend(["", "## Trusted Families", "", _family_table(report.get("family_rows"))])
    lines.extend(["", "## Excluded Families", "", _excluded_table(report.get("excluded_families"))])
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines).rstrip() + "\n"


def _approved_family(family: Mapping[str, object]) -> dict[str, object]:
    approved = deepcopy(dict(family))
    metadata = dict(_as_mapping(approved.get("repair_metadata")))
    metadata.update(
        {
            "manual_review_state": "approved_by_user",
            "human_review_status": "approved_by_user",
            "row_quality_status": "trusted",
            "approval_id": APPROVAL_ID,
            "trusted_now": True,
        }
    )
    approved["repair_metadata"] = metadata
    approved["trusted_eval_metadata"] = {
        "dataset_id": DEFAULT_DATASET_ID,
        "approval_id": APPROVAL_ID,
        "approved_from": "en_es_full_family_repaired_pilot_v1",
        "trusted_now": True,
    }
    approved["cases"] = [_approved_case(case) for case in _mapping_rows(approved.get("cases"))]
    return approved


def _approved_case(case: Mapping[str, object]) -> dict[str, object]:
    approved = deepcopy(dict(case))
    approved["human_review_status"] = "approved_by_user"
    approved["row_quality_status"] = "trusted"
    approved["approval_id"] = APPROVAL_ID
    approved["trusted_eval_status"] = "trusted_seed"
    approved["notes"] = f"{str(approved.get('notes') or '').strip()} | approved_by_user"
    dims = dict(_as_mapping(approved.get("slice_dimensions")))
    dims["dataset_lane"] = [DEFAULT_DATASET_ID]
    dims["manual_review_state"] = ["approved_by_user"]
    dims["row_quality_status"] = ["trusted"]
    dims["human_review_status"] = ["approved_by_user"]
    dims["trusted_eval_status"] = ["trusted_seed"]
    dims["approval_id"] = [APPROVAL_ID]
    approved["slice_dimensions"] = dims
    tags = [
        str(tag)
        for tag in _sequence(approved.get("slice_tags"))
        if str(tag)
        not in {
            "en_es_full_family_repaired_pilot_v1",
            "agent_repaired_user_review_pending",
        }
    ]
    approved["slice_tags"] = [
        DEFAULT_DATASET_ID,
        "approved_by_user",
        "trusted",
        "trusted_eval_seed",
        *tags,
    ]
    return approved


def _checks(dataset: Mapping[str, object]) -> dict[str, bool]:
    families = _mapping_rows(dataset.get("families"))
    cases = [case for family in families for case in _mapping_rows(family.get("cases"))]
    return {
        "has_trusted_families": bool(families),
        "all_rows_approved_by_user": all(
            str(case.get("human_review_status") or "") == "approved_by_user" for case in cases
        ),
        "all_rows_trusted": all(
            str(case.get("row_quality_status") or "") == "trusted" for case in cases
        ),
        "no_deferred_families_in_trusted_rows": all(
            str(family.get("family_id") or "")
            not in {
                str(row.get("family_id") or "")
                for row in _mapping_rows(dataset.get("excluded_families"))
            }
            for family in families
        ),
        "has_active_shadow_and_no_winner_cases": {
            "positive_active",
            "shadow_negative",
            "phrase_no_winner",
        }.issubset({_first_dim(case, "manual_case_type") for case in cases}),
    }


def _family_report_row(family: Mapping[str, object]) -> dict[str, object]:
    active = _as_mapping(family.get("active"))
    cases = _mapping_rows(family.get("cases"))
    metadata = _as_mapping(family.get("repair_metadata"))
    return {
        "family_id": str(family.get("family_id") or ""),
        "source": str(family.get("trigger") or ""),
        "target": str(active.get("target_lemma") or ""),
        "repair_status": str(metadata.get("family_repair_status") or ""),
        "case_count": len(cases),
        "positive_count": sum(
            1 for case in cases if _first_dim(case, "manual_case_type") == "positive_active"
        ),
        "shadow_negative_count": sum(
            1 for case in cases if _first_dim(case, "manual_case_type") == "shadow_negative"
        ),
        "phrase_no_winner_count": sum(
            1 for case in cases if _first_dim(case, "manual_case_type") == "phrase_no_winner"
        ),
    }


def _summary_table(value: Mapping[str, object]) -> str:
    lines = ["| Key | Value |", "| --- | --- |"]
    for key, raw in value.items():
        rendered = (
            json.dumps(raw, ensure_ascii=False, sort_keys=True)
            if isinstance(raw, (dict, list, tuple))
            else str(raw)
        )
        lines.append(f"| `{_escape_md(str(key))}` | `{_escape_md(rendered)}` |")
    return "\n".join(lines)


def _family_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No trusted families._"
    lines = [
        "| Source | Target | Status | Cases | Positive | Shadow | No-Winner |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('source') or ''))}`",
                    f"`{_escape_md(str(row.get('target') or ''))}`",
                    f"`{_escape_md(str(row.get('repair_status') or ''))}`",
                    str(row.get("case_count") or 0),
                    str(row.get("positive_count") or 0),
                    str(row.get("shadow_negative_count") or 0),
                    str(row.get("phrase_no_winner_count") or 0),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _excluded_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No excluded families._"
    lines = ["| Source | Target | Reason | Notes |", "| --- | --- | --- | --- |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('source') or ''))}`",
                    f"`{_escape_md(str(row.get('target') or ''))}`",
                    f"`{_escape_md(str(row.get('deferred_reason') or ''))}`",
                    _escape_md(str(row.get("notes") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _first_dim(case: Mapping[str, object], key: str) -> str:
    values = _as_mapping(case.get("slice_dimensions")).get(key, [])
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)) and values:
        return str(values[0])
    return ""


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
