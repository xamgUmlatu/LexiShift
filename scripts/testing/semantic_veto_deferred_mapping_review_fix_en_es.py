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
SCRIPT_ROOT = Path(__file__).resolve().parent
for candidate in (str(SCRIPT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _load_json,
    _mapping_rows,
    _repo_path,
    _resolve_repo_path,
)


DEFAULT_AUDIT_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_deferred_mapping_audit_en_es_latest.json"
DEFAULT_DATASET_OUT = (
    TEST_INPUTS_ROOT
    / "semantic_routing_cases"
    / "en_es_full_family_deferred_mapping_review_fix_v1.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_deferred_mapping_review_fix_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_deferred_mapping_review_fix_en_es_latest.md"
)
DEFAULT_DATASET_ID = "en_es_full_family_deferred_mapping_review_fix_v1"
MANUAL_REVIEW_STATE = "agent_reviewed_user_review_pending"


FIXED_FAMILY_SPECS: tuple[dict[str, object], ...] = (
    {
        "source": "bar",
        "target": "cercar",
        "source_zipf_band_en": "zipf_4_to_5_common",
        "target_zipf_band_es": "zipf_below_3_rare",
        "source_zipf_frequency_en": 4.94,
        "target_zipf_frequency_es": 2.62,
        "polysemy_band": "high_10_plus",
        "pos_shape": "cross_pos_polysemy",
        "source_cell_id": (
            "source_zipf=zipf_4_to_5_common::polysemy=high_10_plus::pos_shape=cross_pos_polysemy"
        ),
        "family_repair_status": "deferred_mapping_fixed_corrected_active_sense",
        "active": {
            "canonical_pos": "verb",
            "gloss": "fence off, block, or obstruct passage into a place",
        },
        "positive": (
            "The crew will bar the service entrance with temporary fencing.",
            "A locked gate can bar the narrow path to the reservoir.",
        ),
        "shadows": (
            {
                "target": "taberna",
                "canonical_pos": "noun",
                "gloss": "a place where drinks are served",
                "sentence": "She ordered mineral water at the bar after dinner.",
            },
            {
                "target": "barra",
                "canonical_pos": "noun",
                "gloss": "a rigid piece of metal or wood",
                "sentence": "The mechanic welded a steel bar across the frame.",
            },
        ),
        "no_winner": (
            {
                "sentence": "The settings page showed bar as the value of the layout test.",
                "subtype": "metalinguistic_token",
            },
        ),
        "review_note": (
            "The draft alcohol-bar active sense was rejected. This fixed family tests "
            "only the verb/blockage sense supported by the audit."
        ),
    },
    {
        "source": "offset",
        "target": "distancia",
        "source_zipf_band_en": "zipf_3_to_4_mid",
        "target_zipf_band_es": "zipf_4_to_5_common",
        "source_zipf_frequency_en": 3.99,
        "target_zipf_frequency_es": 4.89,
        "polysemy_band": "high_10_plus",
        "pos_shape": "cross_pos_polysemy",
        "source_cell_id": (
            "source_zipf=zipf_3_to_4_mid::polysemy=high_10_plus::pos_shape=cross_pos_polysemy"
        ),
        "family_repair_status": "deferred_mapping_fixed_corrected_active_sense",
        "active": {
            "canonical_pos": "noun",
            "gloss": (
                "the distance or displacement by which one thing is out of alignment with another"
            ),
        },
        "positive": (
            "Measure the offset from the centerline before drilling.",
            "A small offset between the sensor and the marker caused the error.",
        ),
        "shadows": (
            {
                "target": "compensar",
                "canonical_pos": "verb",
                "gloss": "counterbalance or make up for something",
                "sentence": "The rebate can offset the cost of the repairs.",
            },
            {
                "target": "compensación",
                "canonical_pos": "noun",
                "gloss": "a compensating equivalent or credit",
                "sentence": "The refund acted as an offset against the unpaid balance.",
            },
        ),
        "no_winner": (
            {
                "sentence": "The debug field named offset stayed empty after import.",
                "subtype": "metalinguistic_token",
            },
        ),
        "review_note": (
            "The draft outset active sense was rejected. This fixed family tests only "
            "the spatial/technical distance sense; broad target adequacy remains a "
            "review question."
        ),
    },
    {
        "source": "crack",
        "target": "grieta",
        "source_zipf_band_en": "zipf_4_to_5_common",
        "target_zipf_band_es": "zipf_3_to_4_mid",
        "source_zipf_frequency_en": 4.41,
        "target_zipf_frequency_es": 3.5,
        "polysemy_band": "high_10_plus",
        "pos_shape": "cross_pos_polysemy",
        "source_cell_id": (
            "source_zipf=zipf_4_to_5_common::polysemy=high_10_plus::pos_shape=cross_pos_polysemy"
        ),
        "family_repair_status": "representative_slot_replacement_for_rejected_mapping",
        "replaces_rejected_mapping": "demand->deducción",
        "active": {
            "canonical_pos": "noun",
            "gloss": "a thin split, cleft, or narrow opening in a solid surface",
        },
        "positive": (
            "A thin crack ran across the windshield.",
            "Moisture seeped through a crack in the basement wall.",
        ),
        "shadows": (
            {
                "target": "broma",
                "canonical_pos": "noun",
                "gloss": "a sharply humorous comment",
                "sentence": "His crack about the budget made the room laugh.",
            },
            {
                "target": "chasquido",
                "canonical_pos": "noun",
                "gloss": "a sharp sound made when something breaks or snaps",
                "sentence": "The crack of the branch echoed through the yard.",
            },
        ),
        "no_winner": (
            {
                "sentence": "The saved search tag crack appeared in the sidebar.",
                "subtype": "metalinguistic_token",
            },
        ),
        "review_note": (
            "This family replaces demand -> deducción in the same source-band, "
            "polysemy, and POS-shape cell because demand -> deducción failed the "
            "source-target audit."
        ),
    },
)

REJECTED_MAPPINGS: tuple[dict[str, str], ...] = (
    {
        "mapping_id": "demand->deducción",
        "family_id": "en-es:full-family-representative:demand:deduccion",
        "source": "demand",
        "target": "deducción",
        "audit_status": "reject_mapping_source_target_mismatch",
        "replacement_family_id": "en-es:full-family-deferred-review-fix:crack:grieta",
        "replacement_mapping_id": "crack->grieta",
    },
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Author agent-reviewed fixed rows for salvageable deferred full-family "
            "mappings and replace rejected mappings without mutating the trusted seed."
        )
    )
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    audit_path = _resolve_repo_path(args.audit_json)
    dataset_path = _resolve_repo_path(args.dataset_out)
    json_path = _resolve_repo_path(args.json_out)
    markdown_path = _resolve_repo_path(args.markdown_out)
    report, dataset = build_deferred_mapping_review_fix_report(
        audit_payload=_load_json(audit_path),
        audit_path=audit_path,
        dataset_path=dataset_path,
    )
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    # Validate the artifact that was actually written.
    load_sentence_veto_dataset(dataset_path)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_deferred_mapping_review_fix_markdown(report), encoding="utf-8")
    print(f"Wrote dataset artifact to {dataset_path}")
    print(f"Wrote JSON artifact to {json_path}")
    print(f"Wrote Markdown artifact to {markdown_path}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_deferred_mapping_review_fix_report(
    *,
    audit_payload: Mapping[str, object],
    audit_path: Path | None = None,
    dataset_path: Path | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    generated_at = generated_at or _utc_now()
    families = [_family_from_spec(spec) for spec in FIXED_FAMILY_SPECS]
    dataset = {
        "schema_version": 1,
        "pair": str(audit_payload.get("pair") or "en-es"),
        "dataset_id": DEFAULT_DATASET_ID,
        "description": (
            "Agent-reviewed fix packet for deferred full-family source-target mappings. "
            "Rows are repaired for semantic coherence but remain pending user review."
        ),
        "manual_review_state": MANUAL_REVIEW_STATE,
        "provenance": {
            "source_audit_artifact": _repo_path(audit_path),
            "source_audit_decision": str(audit_payload.get("decision") or ""),
            "trusted_seed_mutated": False,
        },
        "families": families,
        "rejected_mappings": [dict(row) for row in REJECTED_MAPPINGS],
    }
    case_rows = [case for family in families for case in _mapping_rows(family.get("cases"))]
    checks = _checks(dataset=dataset, audit_payload=audit_payload)
    issues = [key for key, value in checks.items() if not value]
    summary = {
        "fixed_family_count": len(families),
        "fixed_case_count": len(case_rows),
        "salvaged_mapping_count": 2,
        "replacement_family_count": 1,
        "rejected_mapping_count": len(REJECTED_MAPPINGS),
        "trusted_case_count": 0,
        "manual_review_state": MANUAL_REVIEW_STATE,
        "case_type_counts": dict(
            sorted(Counter(_first_dim(case, "manual_case_type") for case in case_rows).items())
        ),
        "family_repair_status_counts": dict(
            sorted(
                Counter(
                    str(_as_mapping(family.get("repair_metadata")).get("family_repair_status"))
                    for family in families
                ).items()
            )
        ),
        "source_cell_case_counts": dict(
            sorted(Counter(_first_dim(case, "source_cell_id") for case in case_rows).items())
        ),
    }
    report = {
        "schema_version": 1,
        "pair": str(dataset.get("pair") or "en-es"),
        "status": "review" if issues else "ok",
        "decision": (
            "deferred_mapping_review_fix_ready_for_user_review"
            if not issues
            else "deferred_mapping_review_fix_needs_repair"
        ),
        "generated_at": generated_at,
        "inputs": {
            "audit_path": _repo_path(audit_path),
            "audit_decision": str(audit_payload.get("decision") or ""),
        },
        "outputs": {
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": DEFAULT_DATASET_ID,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "score_promotion": "none",
            "trusted_seed_change": "none",
            "row_authority": MANUAL_REVIEW_STATE,
            "repair_policy": (
                "Repair only mappings the audit marked salvageable with corrected active "
                "sense; reject mismatched mappings; preserve the representative cell by "
                "adding a fresh replacement family from the same source-band/polysemy/POS "
                "shape; use independent contexts and real Spanish shadow targets."
            ),
        },
        "summary": summary,
        "e2e_checks": checks,
        "family_rows": [_family_report_row(family) for family in families],
        "rejected_mappings": [dict(row) for row in REJECTED_MAPPINGS],
        "next_steps": [
            "User reviews this fixed packet before any row enters trusted evaluation.",
            "Run sentence-veto diagnostics as a data-quality smoke test only.",
            "If approved, append these rows to a separate trusted addendum or rerun the trusted-seed builder with an explicit approval id.",
        ],
    }
    return report, dataset


def render_deferred_mapping_review_fix_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Deferred Mapping Review Fix",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{_as_mapping(report.get('outputs')).get('dataset_path', '')}`",
        f"- Fixed families: `{summary.get('fixed_family_count', 0)}`",
        f"- Fixed cases: `{summary.get('fixed_case_count', 0)}`",
        f"- Rejected mappings: `{summary.get('rejected_mapping_count', 0)}`",
        f"- Trusted rows: `{summary.get('trusted_case_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("repair_policy") or ""),
        "",
        "Rows are agent-reviewed and repaired, but they are not user-approved gold data.",
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
    lines.extend(["", "## Fixed Families", "", _family_table(report.get("family_rows"))])
    lines.extend(["", "## Rejected Mappings", "", _rejected_table(report.get("rejected_mappings"))])
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines).rstrip() + "\n"


def _family_from_spec(spec: Mapping[str, object]) -> dict[str, object]:
    source = str(spec.get("source") or "")
    target = str(spec.get("target") or "")
    family_id = f"en-es:full-family-deferred-review-fix:{_slug(source)}:{_slug(target)}"
    active_id = f"{family_id}:active"
    active_spec = _as_mapping(spec.get("active"))
    shadows = [
        _shadow_payload(family_id=family_id, source=source, index=index, spec=shadow)
        for index, shadow in enumerate(_mapping_rows(spec.get("shadows")), start=1)
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
                spec=spec,
                notes="agent-reviewed fixed active context",
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
                spec=spec,
                notes="agent-reviewed real Spanish shadow competitor context",
            )
        )
        del shadow["repair_sentence"]
        case_index += 1
    for row in _mapping_rows(spec.get("no_winner")):
        cases.append(
            _case_payload(
                family_id=family_id,
                index=case_index,
                source=source,
                sentence=str(row.get("sentence") or ""),
                gold_winner="none",
                gold_decision="abstain",
                manual_case_type="phrase_no_winner",
                spec=spec,
                notes=f"agent-reviewed no-winner context; subtype={row.get('subtype')}",
                no_winner_subtype=str(row.get("subtype") or "missing"),
            )
        )
        case_index += 1
    return {
        "family_id": family_id,
        "trigger": source,
        "active": {
            "sense_id": active_id,
            "target_lemma": target,
            "canonical_pos": str(active_spec.get("canonical_pos") or ""),
            "evidence_views": _evidence_views(
                sense_label=f"{source} -> {target}",
                gloss_text=str(active_spec.get("gloss") or ""),
            ),
        },
        "shadows": shadows,
        "cases": cases,
        "repair_metadata": {
            "manual_review_state": MANUAL_REVIEW_STATE,
            "human_review_status": "pending_user_review",
            "family_repair_status": str(spec.get("family_repair_status") or ""),
            "review_note": str(spec.get("review_note") or ""),
            "source_cell_id": str(spec.get("source_cell_id") or ""),
            "replaces_rejected_mapping": str(spec.get("replaces_rejected_mapping") or ""),
            "trusted_now": False,
        },
    }


def _shadow_payload(
    *,
    family_id: str,
    source: str,
    index: int,
    spec: Mapping[str, object],
) -> dict[str, object]:
    target = str(spec.get("target") or "")
    sense_id = f"{family_id}:shadow:{index}:{_slug(target)}"
    return {
        "sense_id": sense_id,
        "target_lemma": target,
        "canonical_pos": str(spec.get("canonical_pos") or ""),
        "evidence_views": _evidence_views(
            sense_label=f"{source} -> {target}",
            gloss_text=str(spec.get("gloss") or ""),
        ),
        "repair_sentence": str(spec.get("sentence") or ""),
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
    spec: Mapping[str, object],
    notes: str,
    no_winner_subtype: str = "not_applicable",
) -> dict[str, object]:
    source_band = str(spec.get("source_zipf_band_en") or "missing")
    target_band = str(spec.get("target_zipf_band_es") or "missing")
    polysemy = str(spec.get("polysemy_band") or "missing")
    pos_shape = str(spec.get("pos_shape") or "missing")
    source_cell_id = str(spec.get("source_cell_id") or "missing")
    repair_status = str(spec.get("family_repair_status") or "missing")
    return {
        "case_id": f"{family_id}:{index:03d}",
        "sentence": str(sentence or ""),
        "source_phrase": source,
        "gold_winner": gold_winner,
        "gold_decision": gold_decision,
        "row_quality_status": "agent_reviewed_user_review_pending",
        "human_review_status": "pending_user_review",
        "slice_tags": [
            DEFAULT_DATASET_ID,
            MANUAL_REVIEW_STATE,
            repair_status,
            f"source_zipf:{source_band}",
            f"target_zipf:{target_band}",
            f"polysemy:{polysemy}",
            f"pos_shape:{pos_shape}",
            f"source_cell:{source_cell_id}",
            manual_case_type,
            f"no_winner_subtype:{no_winner_subtype}",
        ],
        "slice_dimensions": {
            "dataset_lane": [DEFAULT_DATASET_ID],
            "manual_review_state": [MANUAL_REVIEW_STATE],
            "row_quality_status": ["agent_reviewed_user_review_pending"],
            "family_repair_status": [repair_status],
            "source_zipf_band_en": [source_band],
            "target_zipf_band_es": [target_band],
            "polysemy_band": [polysemy],
            "pos_shape": [pos_shape],
            "source_cell_id": [source_cell_id],
            "manual_case_type": [manual_case_type],
            "no_winner_subtype": [no_winner_subtype],
            "context_source": ["agent_reviewed_independent_context"],
        },
        "notes": notes,
    }


def _checks(
    *, dataset: Mapping[str, object], audit_payload: Mapping[str, object]
) -> dict[str, bool]:
    families = _mapping_rows(dataset.get("families"))
    cases = [case for family in families for case in _mapping_rows(family.get("cases"))]
    shadows = [shadow for family in families for shadow in _mapping_rows(family.get("shadows"))]
    family_ids = {str(family.get("family_id") or "") for family in families}
    audit_status = {
        str(row.get("mapping_id") or ""): str(row.get("audit_status") or "")
        for row in _mapping_rows(audit_payload.get("mapping_rows"))
    }
    return {
        "has_fixed_families": len(families) == 3,
        "salvageable_audit_rows_repaired": {
            "en-es:full-family-deferred-review-fix:bar:cercar",
            "en-es:full-family-deferred-review-fix:offset:distancia",
        }.issubset(family_ids)
        and audit_status.get("bar->cercar") == "salvageable_with_corrected_active_sense"
        and audit_status.get("offset->distancia") == "salvageable_with_corrected_active_sense",
        "rejected_mapping_not_repaired_as_same_pair": all(
            str(family.get("trigger") or "") != "demand" for family in families
        )
        and audit_status.get("demand->deducción") == "reject_mapping_source_target_mismatch",
        "replacement_family_same_source_cell": any(
            str(family.get("family_id") or "")
            == "en-es:full-family-deferred-review-fix:crack:grieta"
            and _as_mapping(family.get("repair_metadata")).get("source_cell_id")
            == (
                "source_zipf=zipf_4_to_5_common::polysemy=high_10_plus::"
                "pos_shape=cross_pos_polysemy"
            )
            for family in families
        ),
        "has_active_shadow_and_no_winner_cases": {
            "positive_active",
            "shadow_negative",
            "phrase_no_winner",
        }.issubset({_first_dim(case, "manual_case_type") for case in cases}),
        "all_rows_pending_user_review": all(
            str(case.get("human_review_status") or "") == "pending_user_review" for case in cases
        ),
        "no_placeholder_shadow_targets": all(
            "alternate sense" not in str(shadow.get("target_lemma") or "").lower()
            for shadow in shadows
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
        "no_trusted_rows_claimed": all(
            str(case.get("row_quality_status") or "") != "trusted" for case in cases
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
        "repair_status": str(metadata.get("family_repair_status") or ""),
        "source_cell_id": str(metadata.get("source_cell_id") or ""),
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
        "review_note": str(metadata.get("review_note") or ""),
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
        return "_No fixed families._"
    lines = [
        "| Source | Target | Status | Cases | Positive | Shadow | No-Winner | Review Note |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
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
                    _escape_md(str(row.get("review_note") or "")),
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


def _contains_source_as_token(*, sentence: str, source_phrase: str) -> bool:
    source_phrase = str(source_phrase or "").strip()
    if not source_phrase:
        return False
    pattern = r"(?<![A-Za-z0-9_])" + re.escape(source_phrase) + r"(?![A-Za-z0-9_])"
    return re.search(pattern, str(sentence or ""), flags=re.IGNORECASE) is not None


def _string_rows(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [str(item) for item in value if str(item or "").strip()]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "item"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
