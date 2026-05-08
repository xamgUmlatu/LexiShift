#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_INPUTS_ROOT = DOCS_ROOT / "test_inputs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(Path(__file__).resolve().parent),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _load_json,
    _mapping_rows,
    _repo_path,
    _resolve_repo_path,
)


DEFAULT_AGENT_REVIEW_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_agent_review_en_es_latest.json"
)
DEFAULT_DATASET_OUT = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_full_v1.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_full_family_repair_pool_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_full_family_repair_pool_en_es_latest.md"
DEFAULT_DATASET_ID = "en_es_full_family_repaired_full_v1"
DEFAULT_REPAIR_CASE_SPECS_JSON = (
    TEST_INPUTS_ROOT / "semantic_veto_full_family_repair_pool_specs_en_es.json"
)
MANUAL_REVIEW_STATE = "approved_by_user"
ROW_QUALITY_STATUS = "trusted"
HUMAN_REVIEW_STATUS = "approved_by_user"
APPROVAL_ID = "user_approved_full_repaired_dataset_2026_05_08"
REPAIR_SOURCE = "docs/test_outputs/semantic_veto_full_family_agent_review_en_es_latest.json"


def _load_default_repair_case_specs(
    path: Path = DEFAULT_REPAIR_CASE_SPECS_JSON,
) -> tuple[dict[str, object], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("repair_case_specs")
    if not isinstance(rows, list):
        raise ValueError(f"Repair case specs missing from {path}")
    return tuple(dict(row) for row in rows if isinstance(row, dict))


REPAIR_CASE_SPECS = _load_default_repair_case_specs()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize a repaired full-family semantic-veto candidate from the "
            "58-family agent review. Rows remain pending user review."
        )
    )
    parser.add_argument("--agent-review-json", type=Path, default=DEFAULT_AGENT_REVIEW_JSON)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    review_path = _resolve_repo_path(args.agent_review_json)
    dataset_path = _resolve_repo_path(args.dataset_out)
    json_path = _resolve_repo_path(args.json_out)
    markdown_path = _resolve_repo_path(args.markdown_out)
    report, dataset = build_full_family_repair_pool_report(
        agent_review_payload=_load_json(review_path),
        review_path=review_path,
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
    markdown_path.write_text(render_full_family_repair_pool_markdown(report), encoding="utf-8")
    print(f"Wrote dataset artifact to {dataset_path}")
    print(f"Wrote JSON artifact to {json_path}")
    print(f"Wrote Markdown artifact to {markdown_path}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_full_family_repair_pool_report(
    *,
    agent_review_payload: Mapping[str, object],
    review_path: Path | None = None,
    dataset_path: Path | None = None,
    repair_specs: Sequence[Mapping[str, object]] = REPAIR_CASE_SPECS,
    generated_at: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    generated_at = generated_at or _utc_now()
    review_rows = _mapping_rows(agent_review_payload.get("family_reviews"))
    repair_rows = [
        row for row in review_rows if str(row.get("scoring_action") or "") == "repair_pool"
    ]
    excluded_rows = [
        row
        for row in review_rows
        if str(row.get("scoring_action") or "") == "exclude_from_trusted_eval"
    ]
    specs_by_key = {_key(spec): spec for spec in repair_specs}
    repair_keys = {_key(row) for row in repair_rows}
    spec_keys = set(specs_by_key)
    coverage_issues = [
        f"missing_repair_spec:{source}->{target}"
        for source, target in sorted(repair_keys - spec_keys)
    ]
    coverage_issues.extend(
        f"unexpected_repair_spec:{source}->{target}"
        for source, target in sorted(spec_keys - repair_keys)
    )
    families = [
        _family_from_spec(review_row=row, spec=specs_by_key[_key(row)])
        for row in repair_rows
        if _key(row) in specs_by_key
    ]
    dataset = {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": DEFAULT_DATASET_ID,
        "description": (
            "Full repaired candidate from the 58-family representative sample agent "
            "review. Rows were semantically repaired by the agent and approved by the "
            "user for the next exploratory sweeps."
        ),
        "manual_review_state": MANUAL_REVIEW_STATE,
        "provenance": {
            "source_agent_review_artifact": _repo_path(review_path),
            "source_agent_review_authority": str(
                agent_review_payload.get("review_authority") or ""
            ),
            "approval_id": APPROVAL_ID,
            "trusted_now": True,
        },
        "families": families,
        "excluded_families": [_excluded_payload(row) for row in excluded_rows],
    }
    checks = _checks(dataset=dataset, expected_repair_count=len(repair_rows))
    issues = [key for key, value in checks.items() if not value]
    issues.extend(coverage_issues)
    summary = _summary(dataset=dataset, review_rows=review_rows, issues=issues)
    report = {
        "schema_version": 1,
        "pair": "en-es",
        "status": "ok" if not issues else "review",
        "decision": "full_family_repair_pool_user_approved_for_exploratory_sweeps"
        if not issues
        else "full_family_repair_pool_needs_repair",
        "generated_at": generated_at,
        "inputs": {
            "agent_review_path": _repo_path(review_path),
            "agent_review_decision": str(agent_review_payload.get("decision") or ""),
        },
        "outputs": {
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": DEFAULT_DATASET_ID,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "score_promotion": "none",
            "row_authority": MANUAL_REVIEW_STATE,
            "repair_policy": (
                "Materialize every repair-pool family from the full 58-family agent "
                "review, exclude rejected/artifact mappings, rewrite active contexts "
                "independently, keep source tokens standalone, use real Spanish shadow "
                "competitor targets only when a true competitor was authored, and mark "
                "the repaired rows as user-approved for exploratory sweeps."
            ),
            "shadow_policy": (
                "Draft same-target POS shadows are dropped. Shadow-negative rows are "
                "included only when the repaired spec names a distinct Spanish competitor."
            ),
            "trusted_row_rule": (
                "Rows are trusted for the repaired-full exploratory lane after explicit "
                "user approval. This still is not a final locked-eval proof or runtime "
                "promotion artifact."
            ),
        },
        "summary": summary,
        "e2e_checks": checks,
        "issues": issues,
        "family_rows": [_family_report_row(family) for family in families],
        "excluded_families": [_excluded_payload(row) for row in excluded_rows],
        "next_steps": [
            "Run sentence-veto diagnostics on this repaired-full candidate.",
            "Rerun band-formula and Zipf-boundary sweeps on this larger approved denominator.",
            "Use any promising ranking only for LLM data allocation until a locked-eval split confirms it.",
        ],
    }
    return report, dataset


def render_full_family_repair_pool_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Full-Family Repair Pool",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{_as_mapping(report.get('outputs')).get('dataset_path', '')}`",
        f"- Repaired families: `{summary.get('repaired_family_count', 0)}`",
        f"- Repaired cases: `{summary.get('repaired_case_count', 0)}`",
        f"- Excluded families: `{summary.get('excluded_family_count', 0)}`",
        f"- Trusted rows: `{summary.get('trusted_case_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("repair_policy") or ""),
        "",
        str(_as_mapping(report.get("methodology")).get("shadow_policy") or ""),
        "",
        "Rows are repaired for semantic coherence and user-approved for exploratory sweeps.",
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
    lines.extend(["", "## Repaired Families", "", _family_table(report.get("family_rows"))])
    lines.extend(["", "## Excluded Families", "", _excluded_table(report.get("excluded_families"))])
    lines.extend(["", "## Issues", "", _issue_list(report.get("issues"))])
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines).rstrip() + "\n"


def _family_from_spec(
    *, review_row: Mapping[str, object], spec: Mapping[str, object]
) -> dict[str, object]:
    source, target = _key(review_row)
    family_id = f"en-es:full-family-repaired-full:{_slug(source)}:{_slug(target)}"
    active_id = f"{family_id}:active"
    shadows = [
        _shadow_payload(family_id=family_id, source=source, index=index, row=row)
        for index, row in enumerate(_shadow_specs(spec), start=1)
    ]
    cases: list[dict[str, object]] = []
    case_index = 1
    for sentence in _string_rows(spec.get("positive")):
        cases.append(
            _case_payload(
                family_id=family_id,
                index=case_index,
                source=source,
                sentence=sentence,
                gold_winner=active_id,
                gold_decision="replace",
                manual_case_type="positive_active",
                review_row=review_row,
                no_winner_subtype="not_applicable",
                notes="full-repair independent positive context",
            )
        )
        case_index += 1
    for shadow in shadows:
        cases.append(
            _case_payload(
                family_id=family_id,
                index=case_index,
                source=source,
                sentence=str(shadow["repair_sentence"]),
                gold_winner=str(shadow["sense_id"]),
                gold_decision="abstain",
                manual_case_type="shadow_negative",
                review_row=review_row,
                no_winner_subtype="not_applicable",
                notes="full-repair shadow context with real Spanish competitor target",
            )
        )
        del shadow["repair_sentence"]
        case_index += 1
    no_winner_sentence = str(spec.get("no_winner") or "")
    if no_winner_sentence:
        cases.append(
            _case_payload(
                family_id=family_id,
                index=case_index,
                source=source,
                sentence=no_winner_sentence,
                gold_winner="none",
                gold_decision="abstain",
                manual_case_type="phrase_no_winner",
                review_row=review_row,
                no_winner_subtype="named_entity_or_title",
                notes="full-repair realistic no-winner title/code context",
            )
        )
    return {
        "family_id": family_id,
        "trigger": source,
        "active": {
            "sense_id": active_id,
            "target_lemma": target,
            "canonical_pos": str(spec.get("pos") or ""),
            "evidence_views": _evidence_views(
                sense_label=f"{source} -> {target}",
                gloss_text=str(review_row.get("corrected_active_gloss") or ""),
            ),
        },
        "shadows": shadows,
        "cases": cases,
        "repair_metadata": {
            "manual_review_state": MANUAL_REVIEW_STATE,
            "family_disposition": str(review_row.get("family_disposition") or ""),
            "active_sense_status": str(review_row.get("active_sense_status") or ""),
            "source_of_repair": REPAIR_SOURCE,
            "approval_id": APPROVAL_ID,
            "trusted_now": True,
        },
    }


def _shadow_payload(
    *,
    family_id: str,
    source: str,
    index: int,
    row: Mapping[str, str],
) -> dict[str, object]:
    target = str(row.get("target") or "")
    sense_id = f"{family_id}:shadow:{index}:{_slug(target)}"
    return {
        "sense_id": sense_id,
        "target_lemma": target,
        "canonical_pos": str(row.get("pos") or ""),
        "evidence_views": _evidence_views(
            sense_label=f"{source} -> {target}",
            gloss_text=str(row.get("gloss") or ""),
        ),
        "repair_sentence": str(row.get("sentence") or ""),
    }


def _case_payload(
    *,
    family_id: str,
    index: int,
    source: str,
    sentence: str,
    gold_winner: str,
    gold_decision: str,
    manual_case_type: str,
    review_row: Mapping[str, object],
    no_winner_subtype: str,
    notes: str,
) -> dict[str, object]:
    source_band = str(review_row.get("source_zipf_band_en") or "missing")
    target_band = str(review_row.get("target_zipf_band_es") or "missing")
    polysemy = str(review_row.get("polysemy_band") or "missing")
    pos_shape = str(review_row.get("pos_shape") or "missing")
    disposition = str(review_row.get("family_disposition") or "missing")
    active_status = str(review_row.get("active_sense_status") or "missing")
    return {
        "case_id": f"{family_id}:{index:03d}",
        "sentence": str(sentence or ""),
        "source_phrase": source,
        "gold_winner": gold_winner,
        "gold_decision": gold_decision,
        "row_quality_status": ROW_QUALITY_STATUS,
        "human_review_status": HUMAN_REVIEW_STATUS,
        "approval_id": APPROVAL_ID,
        "slice_tags": [
            DEFAULT_DATASET_ID,
            MANUAL_REVIEW_STATE,
            ROW_QUALITY_STATUS,
            f"approval_id:{APPROVAL_ID}",
            f"family_disposition:{disposition}",
            f"active_sense_status:{active_status}",
            f"source_zipf:{source_band}",
            f"target_zipf:{target_band}",
            f"polysemy:{polysemy}",
            f"pos_shape:{pos_shape}",
            manual_case_type,
            f"no_winner_subtype:{no_winner_subtype}",
        ],
        "slice_dimensions": {
            "dataset_lane": [DEFAULT_DATASET_ID],
            "manual_review_state": [MANUAL_REVIEW_STATE],
            "row_quality_status": [ROW_QUALITY_STATUS],
            "human_review_status": [HUMAN_REVIEW_STATUS],
            "approval_id": [APPROVAL_ID],
            "family_disposition": [disposition],
            "active_sense_status": [active_status],
            "source_zipf_band_en": [source_band],
            "target_zipf_band_es": [target_band],
            "polysemy_band": [polysemy],
            "pos_shape": [pos_shape],
            "manual_case_type": [manual_case_type],
            "no_winner_subtype": [no_winner_subtype],
            "context_source": ["agent_curated_full_repair_context"],
        },
        "notes": notes,
    }


def _excluded_payload(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "family_id": str(row.get("family_id") or ""),
        "source": str(row.get("trigger") or ""),
        "target": str(row.get("target_lemma") or ""),
        "source_zipf_band_en": str(row.get("source_zipf_band_en") or ""),
        "family_disposition": str(row.get("family_disposition") or ""),
        "active_sense_status": str(row.get("active_sense_status") or ""),
        "reason": str(row.get("notes") or ""),
    }


def _checks(*, dataset: Mapping[str, object], expected_repair_count: int) -> dict[str, bool]:
    families = _mapping_rows(dataset.get("families"))
    cases = [case for family in families for case in _mapping_rows(family.get("cases"))]
    shadows = [shadow for family in families for shadow in _mapping_rows(family.get("shadows"))]
    type_counts = Counter(_first_dim(case, "manual_case_type") for case in cases)
    families_with_positive = {
        str(family.get("family_id") or "")
        for family in families
        if any(
            _first_dim(case, "manual_case_type") == "positive_active"
            for case in _mapping_rows(family.get("cases"))
        )
    }
    families_with_no_winner = {
        str(family.get("family_id") or "")
        for family in families
        if any(
            _first_dim(case, "manual_case_type") == "phrase_no_winner"
            for case in _mapping_rows(family.get("cases"))
        )
    }
    return {
        "all_expected_repair_families_materialized": len(families) == int(expected_repair_count),
        "has_repaired_families": bool(families),
        "has_positive_shadow_and_no_winner_cases": all(
            type_counts.get(case_type, 0) > 0
            for case_type in ("positive_active", "shadow_negative", "phrase_no_winner")
        ),
        "every_family_has_positive_and_no_winner": len(families_with_positive) == len(families)
        and len(families_with_no_winner) == len(families),
        "all_rows_approved_by_user": all(
            str(case.get("human_review_status") or "") == HUMAN_REVIEW_STATUS for case in cases
        ),
        "all_approved_rows_trusted": all(
            str(case.get("row_quality_status") or "") == ROW_QUALITY_STATUS for case in cases
        ),
        "no_placeholder_shadow_targets": all(
            "alternate sense" not in str(shadow.get("target_lemma") or "").lower()
            for shadow in shadows
        ),
        "all_shadow_targets_are_real": all(
            str(shadow.get("target_lemma") or "") for shadow in shadows
        ),
        "all_cases_have_standalone_source_token": all(
            _contains_source_as_token(
                sentence=str(case.get("sentence") or ""),
                source_phrase=str(case.get("source_phrase") or ""),
            )
            for case in cases
        ),
        "no_definition_fallback_templates": all(
            not str(case.get("sentence") or "")
            .lower()
            .startswith(("the article used", "in this sentence,"))
            for case in cases
        ),
        "all_trusted_rows_have_approval_id": all(
            str(case.get("row_quality_status") or "") != ROW_QUALITY_STATUS
            or str(case.get("approval_id") or "") == APPROVAL_ID
            for case in cases
        ),
        "rejected_families_excluded": not _mapping_rows(dataset.get("excluded_families"))
        or all(
            str(row.get("source") or "") != str(family.get("trigger") or "")
            or str(row.get("target") or "")
            != str(_as_mapping(family.get("active")).get("target_lemma") or "")
            for row in _mapping_rows(dataset.get("excluded_families"))
            for family in families
        ),
    }


def _summary(
    *,
    dataset: Mapping[str, object],
    review_rows: Sequence[Mapping[str, object]],
    issues: Sequence[str],
) -> dict[str, object]:
    families = _mapping_rows(dataset.get("families"))
    cases = [case for family in families for case in _mapping_rows(family.get("cases"))]
    shadows = [shadow for family in families for shadow in _mapping_rows(family.get("shadows"))]
    return {
        "issues": list(issues),
        "reviewed_family_count": len(review_rows),
        "repaired_family_count": len(families),
        "repaired_case_count": len(cases),
        "excluded_family_count": len(_mapping_rows(dataset.get("excluded_families"))),
        "shadow_evidence_count": len(shadows),
        "trusted_case_count": sum(
            1 for case in cases if str(case.get("row_quality_status") or "") == ROW_QUALITY_STATUS
        ),
        "case_type_counts": dict(
            sorted(Counter(_first_dim(case, "manual_case_type") for case in cases).items())
        ),
        "source_band_case_counts": dict(
            sorted(Counter(_first_dim(case, "source_zipf_band_en") for case in cases).items())
        ),
        "family_disposition_counts": dict(
            sorted(
                Counter(
                    str(_as_mapping(family.get("repair_metadata")).get("family_disposition") or "")
                    for family in families
                ).items()
            )
        ),
        "active_sense_status_counts": dict(
            sorted(
                Counter(
                    str(_as_mapping(family.get("repair_metadata")).get("active_sense_status") or "")
                    for family in families
                ).items()
            )
        ),
    }


def _family_report_row(family: Mapping[str, object]) -> dict[str, object]:
    cases = _mapping_rows(family.get("cases"))
    metadata = _as_mapping(family.get("repair_metadata"))
    active = _as_mapping(family.get("active"))
    return {
        "family_id": str(family.get("family_id") or ""),
        "source": str(family.get("trigger") or ""),
        "target": str(active.get("target_lemma") or ""),
        "family_disposition": str(metadata.get("family_disposition") or ""),
        "active_sense_status": str(metadata.get("active_sense_status") or ""),
        "case_count": len(cases),
        "shadow_count": len(_mapping_rows(family.get("shadows"))),
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


def _evidence_views(*, sense_label: str, gloss_text: str) -> dict[str, str]:
    return {
        "sense_label": sense_label,
        "gloss_text": gloss_text,
        "sense_gloss_bundle": f"{sense_label} | {gloss_text}",
        "all_evidence_text": f"{sense_label} | {gloss_text}",
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
        return "_No repaired families._"
    lines = [
        "| Source | Target | Disposition | Cases | Positive | Shadow | No-Winner |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('source') or ''))}`",
                    f"`{_escape_md(str(row.get('target') or ''))}`",
                    f"`{_escape_md(str(row.get('family_disposition') or ''))}`",
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
    lines = ["| Source | Target | Disposition | Reason |", "| --- | --- | --- | --- |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('source') or ''))}`",
                    f"`{_escape_md(str(row.get('target') or ''))}`",
                    f"`{_escape_md(str(row.get('family_disposition') or ''))}`",
                    _escape_md(str(row.get("reason") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _issue_list(value: object) -> str:
    rows = [str(item) for item in value or ()]
    if not rows:
        return "- `none`"
    return "\n".join(f"- `{_escape_md(row)}`" for row in rows)


def _shadow_specs(spec: Mapping[str, object]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in spec.get("shadows") or ():
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)) or len(row) != 3:
            continue
        target, gloss, sentence = row
        rows.append(
            {
                "target": str(target),
                "pos": str(spec.get("pos") or ""),
                "gloss": str(gloss),
                "sentence": str(sentence),
            }
        )
    return rows


def _first_dim(case: Mapping[str, object], key: str) -> str:
    values = _as_mapping(case.get("slice_dimensions")).get(key, [])
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)) and values:
        return str(values[0])
    return ""


def _contains_source_as_token(*, sentence: str, source_phrase: str) -> bool:
    source_phrase = str(source_phrase or "").strip()
    if not source_phrase:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(source_phrase)}(?!\w)", str(sentence or ""), re.I))


def _string_rows(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [str(row) for row in value if str(row)]


def _key(row: Mapping[str, object]) -> tuple[str, str]:
    return (
        str(row.get("source") or row.get("trigger") or "").strip(),
        str(row.get("target") or row.get("target_lemma") or "").strip(),
    )


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
