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
from semantic_veto_full_family_trusted_eval_seed_en_es import (  # noqa: E402
    APPROVAL_ID as REPAIRED_PILOT_APPROVAL_ID,
)
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _load_json,
    _mapping_rows,
    _repo_path,
    _resolve_repo_path,
)


DEFAULT_TRUSTED_SEED_JSON = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_trusted_eval_seed_v1.json"
)
DEFAULT_DEFERRED_FIX_JSON = (
    TEST_INPUTS_ROOT
    / "semantic_routing_cases"
    / "en_es_full_family_deferred_mapping_review_fix_v1.json"
)
DEFAULT_DATASET_OUT = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_trusted_eval_seed_v2.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_trusted_eval_seed_v2_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_trusted_eval_seed_v2_en_es_latest.md"
)
DEFAULT_DATASET_ID = "en_es_full_family_trusted_eval_seed_v2"
DEFERRED_FIX_APPROVAL_ID = "user_step8_deferred_mapping_review_fix_approval_2026_05_07"
DEFERRED_FIX_APPROVAL_NOTE = (
    "User approved the GPT-5.5-reviewed deferred mapping repair rows in chat "
    "so the workstream can move on to running trusted diagnostics."
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Promote the approved deferred mapping repair packet into a combined "
            "trusted eval seed v2 without overwriting the original v1 seed."
        )
    )
    parser.add_argument("--trusted-seed-json", type=Path, default=DEFAULT_TRUSTED_SEED_JSON)
    parser.add_argument("--deferred-fix-json", type=Path, default=DEFAULT_DEFERRED_FIX_JSON)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    trusted_seed_path = _resolve_repo_path(args.trusted_seed_json)
    deferred_fix_path = _resolve_repo_path(args.deferred_fix_json)
    dataset_path = _resolve_repo_path(args.dataset_out)
    json_path = _resolve_repo_path(args.json_out)
    markdown_path = _resolve_repo_path(args.markdown_out)

    load_sentence_veto_dataset(trusted_seed_path)
    load_sentence_veto_dataset(deferred_fix_path)
    report, dataset = build_trusted_eval_seed_v2_report(
        trusted_seed_payload=_load_json(trusted_seed_path),
        deferred_fix_payload=_load_json(deferred_fix_path),
        trusted_seed_path=trusted_seed_path,
        deferred_fix_path=deferred_fix_path,
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
    markdown_path.write_text(render_trusted_eval_seed_v2_markdown(report), encoding="utf-8")
    print(f"Wrote dataset artifact to {dataset_path}")
    print(f"Wrote JSON artifact to {json_path}")
    print(f"Wrote Markdown artifact to {markdown_path}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_trusted_eval_seed_v2_report(
    *,
    trusted_seed_payload: Mapping[str, object],
    deferred_fix_payload: Mapping[str, object],
    trusted_seed_path: Path | None = None,
    deferred_fix_path: Path | None = None,
    dataset_path: Path | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    generated_at = generated_at or _utc_now()
    existing_families = [
        _carry_forward_trusted_family(family)
        for family in _mapping_rows(trusted_seed_payload.get("families"))
    ]
    deferred_families = [
        _approve_deferred_fix_family(family)
        for family in _mapping_rows(deferred_fix_payload.get("families"))
    ]
    families = [*existing_families, *deferred_families]
    rejected_mappings = [
        dict(row) for row in _mapping_rows(deferred_fix_payload.get("rejected_mappings"))
    ]
    dataset = {
        "schema_version": 1,
        "pair": str(
            trusted_seed_payload.get("pair") or deferred_fix_payload.get("pair") or "en-es"
        ),
        "dataset_id": DEFAULT_DATASET_ID,
        "description": (
            "Combined trusted eval seed v2. Carries forward the user-approved "
            "repaired pilot seed and adds the user-approved deferred mapping "
            "review-fix rows."
        ),
        "manual_review_state": "approved_by_user",
        "approvals": [
            {
                "approval_id": REPAIRED_PILOT_APPROVAL_ID,
                "source_dataset": _repo_path(trusted_seed_path),
                "approved_rows": "trusted_eval_seed_v1_rows",
            },
            {
                "approval_id": DEFERRED_FIX_APPROVAL_ID,
                "approval_note": DEFERRED_FIX_APPROVAL_NOTE,
                "source_dataset": _repo_path(deferred_fix_path),
                "approved_rows": "all_deferred_mapping_review_fix_rows",
            },
        ],
        "families": families,
        "rejected_mappings": rejected_mappings,
    }
    case_rows = [case for family in families for case in _mapping_rows(family.get("cases"))]
    summary = {
        "trusted_family_count": len(families),
        "trusted_case_count": len(case_rows),
        "carried_forward_family_count": len(existing_families),
        "newly_approved_family_count": len(deferred_families),
        "newly_approved_case_count": sum(
            len(_mapping_rows(family.get("cases"))) for family in deferred_families
        ),
        "rejected_mapping_count": len(rejected_mappings),
        "manual_review_state": "approved_by_user",
        "row_quality_status": "trusted",
        "case_type_counts": dict(
            sorted(Counter(_first_dim(case, "manual_case_type") for case in case_rows).items())
        ),
        "approval_case_counts": dict(
            sorted(Counter(str(case.get("approval_id") or "") for case in case_rows).items())
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
            "full_family_trusted_eval_seed_v2_ready_for_scoring"
            if not issues
            else "full_family_trusted_eval_seed_v2_needs_repair"
        ),
        "generated_at": generated_at,
        "inputs": {
            "trusted_seed_path": _repo_path(trusted_seed_path),
            "trusted_seed_dataset_id": str(trusted_seed_payload.get("dataset_id") or ""),
            "deferred_fix_path": _repo_path(deferred_fix_path),
            "deferred_fix_dataset_id": str(deferred_fix_payload.get("dataset_id") or ""),
        },
        "outputs": {
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": DEFAULT_DATASET_ID,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "score_promotion": "none",
            "approval_boundary": (
                "v2 records two explicit approval ids: the original repaired pilot "
                "approval and the deferred mapping review-fix approval. It does not "
                "make a runtime policy change."
            ),
            "locked_eval_boundary": (
                "This is trusted data, not an untouched locked-eval split. It can be "
                "used for near-term diagnostics and data-quality scoring, but threshold "
                "promotion still needs a discovery/locked split."
            ),
        },
        "summary": summary,
        "e2e_checks": checks,
        "family_rows": [_family_report_row(family) for family in families],
        "rejected_mappings": rejected_mappings,
        "next_steps": [
            "Score this v2 trusted seed with TF-IDF and sentence-transformer diagnostics.",
            "Use the v2 seed as the near-term trusted data lane for scorer bakeoffs.",
            "Create or refresh a discovery/locked split before any threshold promotion claim.",
        ],
    }
    return report, dataset


def render_trusted_eval_seed_v2_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Full-Family Trusted Eval Seed v2",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{_as_mapping(report.get('outputs')).get('dataset_path', '')}`",
        f"- Trusted families: `{summary.get('trusted_family_count', 0)}`",
        f"- Trusted cases: `{summary.get('trusted_case_count', 0)}`",
        f"- Newly approved cases: `{summary.get('newly_approved_case_count', 0)}`",
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
    lines.extend(["", "## Rejected Mappings", "", _rejected_table(report.get("rejected_mappings"))])
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines).rstrip() + "\n"


def _carry_forward_trusted_family(family: Mapping[str, object]) -> dict[str, object]:
    carried = deepcopy(dict(family))
    metadata = dict(_as_mapping(carried.get("repair_metadata")))
    metadata.update(
        {
            "manual_review_state": "approved_by_user",
            "human_review_status": "approved_by_user",
            "row_quality_status": "trusted",
            "trusted_seed_v2_status": "carried_forward_from_v1",
        }
    )
    carried["repair_metadata"] = metadata
    carried["trusted_eval_metadata"] = {
        **dict(_as_mapping(carried.get("trusted_eval_metadata"))),
        "dataset_id": DEFAULT_DATASET_ID,
        "carried_forward_from": str(
            _as_mapping(carried.get("trusted_eval_metadata")).get("dataset_id")
            or "en_es_full_family_trusted_eval_seed_v1"
        ),
        "trusted_seed_v2_status": "carried_forward_from_v1",
        "trusted_now": True,
    }
    carried["cases"] = [
        _trusted_case_for_v2(case, status="carried_forward_from_v1")
        for case in _mapping_rows(carried.get("cases"))
    ]
    return carried


def _approve_deferred_fix_family(family: Mapping[str, object]) -> dict[str, object]:
    approved = deepcopy(dict(family))
    metadata = dict(_as_mapping(approved.get("repair_metadata")))
    metadata.update(
        {
            "manual_review_state": "approved_by_user",
            "human_review_status": "approved_by_user",
            "row_quality_status": "trusted",
            "approval_id": DEFERRED_FIX_APPROVAL_ID,
            "trusted_seed_v2_status": "newly_approved_deferred_fix",
            "trusted_now": True,
        }
    )
    approved["repair_metadata"] = metadata
    approved["trusted_eval_metadata"] = {
        "dataset_id": DEFAULT_DATASET_ID,
        "approval_id": DEFERRED_FIX_APPROVAL_ID,
        "approved_from": "en_es_full_family_deferred_mapping_review_fix_v1",
        "trusted_seed_v2_status": "newly_approved_deferred_fix",
        "trusted_now": True,
    }
    approved["cases"] = [
        _approved_deferred_fix_case(case) for case in _mapping_rows(approved.get("cases"))
    ]
    return approved


def _trusted_case_for_v2(case: Mapping[str, object], *, status: str) -> dict[str, object]:
    trusted = deepcopy(dict(case))
    trusted["human_review_status"] = "approved_by_user"
    trusted["row_quality_status"] = "trusted"
    trusted["trusted_eval_status"] = "trusted_seed_v2"
    trusted["trusted_seed_v2_status"] = status
    dims = dict(_as_mapping(trusted.get("slice_dimensions")))
    dims["dataset_lane"] = [DEFAULT_DATASET_ID]
    dims["manual_review_state"] = ["approved_by_user"]
    dims["row_quality_status"] = ["trusted"]
    dims["human_review_status"] = ["approved_by_user"]
    dims["trusted_eval_status"] = ["trusted_seed_v2"]
    dims["trusted_seed_v2_status"] = [status]
    trusted["slice_dimensions"] = dims
    tags = [
        str(tag)
        for tag in _sequence(trusted.get("slice_tags"))
        if str(tag)
        not in {
            "en_es_full_family_trusted_eval_seed_v1",
            "en_es_full_family_deferred_mapping_review_fix_v1",
            "agent_reviewed_user_review_pending",
            "trusted_eval_seed",
        }
    ]
    trusted["slice_tags"] = [
        DEFAULT_DATASET_ID,
        "approved_by_user",
        "trusted",
        "trusted_eval_seed_v2",
        status,
        *tags,
    ]
    return trusted


def _approved_deferred_fix_case(case: Mapping[str, object]) -> dict[str, object]:
    approved = _trusted_case_for_v2(case, status="newly_approved_deferred_fix")
    approved["approval_id"] = DEFERRED_FIX_APPROVAL_ID
    approved["notes"] = f"{str(approved.get('notes') or '').strip()} | approved_by_user"
    dims = dict(_as_mapping(approved.get("slice_dimensions")))
    dims["approval_id"] = [DEFERRED_FIX_APPROVAL_ID]
    approved["slice_dimensions"] = dims
    return approved


def _checks(dataset: Mapping[str, object]) -> dict[str, bool]:
    families = _mapping_rows(dataset.get("families"))
    cases = [case for family in families for case in _mapping_rows(family.get("cases"))]
    family_ids = {str(family.get("family_id") or "") for family in families}
    approval_ids = {str(case.get("approval_id") or "") for case in cases}
    return {
        "has_trusted_families": bool(families),
        "all_rows_approved_by_user": all(
            str(case.get("human_review_status") or "") == "approved_by_user" for case in cases
        ),
        "all_rows_trusted": all(
            str(case.get("row_quality_status") or "") == "trusted" for case in cases
        ),
        "no_pending_review_rows": all(
            _first_dim(case, "manual_review_state") == "approved_by_user" for case in cases
        ),
        "has_original_repaired_seed_rows": REPAIRED_PILOT_APPROVAL_ID in approval_ids,
        "has_deferred_fix_approval_rows": DEFERRED_FIX_APPROVAL_ID in approval_ids,
        "has_repaired_deferred_families": {
            "en-es:full-family-deferred-review-fix:bar:cercar",
            "en-es:full-family-deferred-review-fix:offset:distancia",
            "en-es:full-family-deferred-review-fix:crack:grieta",
        }.issubset(family_ids),
        "rejected_demand_mapping_absent": all(
            str(family.get("trigger") or "") != "demand" for family in families
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
        "seed_v2_status": str(metadata.get("trusted_seed_v2_status") or ""),
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
        "| Source | Target | Status | v2 Status | Cases | Positive | Shadow | No-Winner |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('source') or ''))}`",
                    f"`{_escape_md(str(row.get('target') or ''))}`",
                    f"`{_escape_md(str(row.get('repair_status') or ''))}`",
                    f"`{_escape_md(str(row.get('seed_v2_status') or ''))}`",
                    str(row.get("case_count") or 0),
                    str(row.get("positive_count") or 0),
                    str(row.get("shadow_negative_count") or 0),
                    str(row.get("phrase_no_winner_count") or 0),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _rejected_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rejected mappings._"
    lines = ["| Mapping | Status | Replacement |", "| --- | --- | --- |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('mapping_id') or ''))}`",
                    f"`{_escape_md(str(row.get('audit_status') or ''))}`",
                    f"`{_escape_md(str(row.get('replacement_mapping_id') or ''))}`",
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


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
