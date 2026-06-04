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
    _repo_path,
    _resolve_repo_path,
)


DEFAULT_REVIEW_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_agent_manual_review_en_es_latest.json"
)
DEFAULT_DATASET_OUT = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_pilot_v1.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_full_family_repair_pilot_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_full_family_repair_pilot_en_es_latest.md"
DEFAULT_DATASET_ID = "en_es_full_family_repaired_pilot_v1"
MANUAL_REVIEW_STATE = "agent_repaired_user_review_pending"


REPAIRED_FAMILY_SPECS: tuple[dict[str, object], ...] = (
    {
        "source": "break",
        "target": "quebrar",
        "source_zipf_band_en": "zipf_5_plus_very_common",
        "target_zipf_band_es": "zipf_3_to_4_mid",
        "polysemy_band": "high_10_plus",
        "pos_shape": "cross_pos_polysemy",
        "family_repair_status": "active_sense_corrected",
        "active": {
            "canonical_pos": "verb",
            "gloss": "become separated into pieces or crack under force",
        },
        "positive": (
            "The plate began to break along the rim.",
            "A cheap lock can break under sudden force.",
        ),
        "shadows": (
            {
                "target": "interrumpir",
                "canonical_pos": "verb",
                "gloss": "interrupt or stop an ongoing activity",
                "sentence": "A news alert can break the broadcast without warning.",
            },
            {
                "target": "oportunidad",
                "canonical_pos": "noun",
                "gloss": "an unexpected opportunity or lucky chance",
                "sentence": "Her internship became the big break that launched her career.",
            },
        ),
        "no_winner": (
            {
                "sentence": "The keyboard shortcut was labeled Break on the settings page.",
                "subtype": "named_entity_or_title",
            },
        ),
    },
    {
        "source": "bridle",
        "target": "reprimir",
        "source_zipf_band_en": "zipf_below_3_rare",
        "target_zipf_band_es": "zipf_3_to_4_mid",
        "polysemy_band": "medium_4_to_9",
        "pos_shape": "cross_pos_polysemy",
        "family_repair_status": "active_sense_corrected",
        "active": {
            "canonical_pos": "verb",
            "gloss": "restrain, repress, or hold back a reaction or action",
        },
        "positive": (
            "She tried to bridle her anger during the meeting.",
            "The manager had to bridle his frustration after the call.",
        ),
        "shadows": (
            {
                "target": "ofenderse",
                "canonical_pos": "verb",
                "gloss": "react with anger or offense",
                "sentence": "She began to bridle at the suggestion that the project had failed.",
            },
            {
                "target": "brida",
                "canonical_pos": "noun",
                "gloss": "headgear with reins used for riding or driving",
                "sentence": "The rider checked the bridle before the parade.",
            },
        ),
        "no_winner": (
            {
                "sentence": "The novel Bridle appeared in the catalog as a title.",
                "subtype": "named_entity_or_title",
            },
        ),
    },
    {
        "source": "december",
        "target": "diciembre",
        "source_zipf_band_en": "zipf_5_plus_very_common",
        "target_zipf_band_es": "zipf_5_plus_very_common",
        "polysemy_band": "low_1_to_3",
        "pos_shape": "single_sense",
        "family_repair_status": "aligned_mapping_contexts_rewritten",
        "active": {
            "canonical_pos": "noun",
            "gloss": "the twelfth month of the year",
        },
        "positive": (
            "The conference moved to December after the venue delay.",
            "Their lease expires in December.",
        ),
        "shadows": (),
        "no_winner": (
            {
                "sentence": "The album December stayed on the playlist for weeks.",
                "subtype": "named_entity_or_title",
            },
        ),
    },
    {
        "source": "emotion",
        "target": "emoción",
        "source_zipf_band_en": "zipf_4_to_5_common",
        "target_zipf_band_es": "zipf_4_to_5_common",
        "polysemy_band": "low_1_to_3",
        "pos_shape": "single_sense",
        "family_repair_status": "aligned_mapping_contexts_rewritten",
        "active": {
            "canonical_pos": "noun",
            "gloss": "a strong feeling",
        },
        "positive": (
            "The speech stirred strong emotion in the crowd.",
            "She hid every emotion during the interview.",
        ),
        "shadows": (),
        "no_winner": (
            {
                "sentence": "The startup Emotion released a new design tool.",
                "subtype": "named_entity_or_title",
            },
        ),
    },
    {
        "source": "dentist",
        "target": "dentista",
        "source_zipf_band_en": "zipf_3_to_4_mid",
        "target_zipf_band_es": "zipf_3_to_4_mid",
        "polysemy_band": "low_1_to_3",
        "pos_shape": "single_sense",
        "family_repair_status": "aligned_mapping_contexts_rewritten",
        "active": {
            "canonical_pos": "noun",
            "gloss": "a person qualified to practice dentistry",
        },
        "positive": (
            "The dentist repaired the chipped tooth before lunch.",
            "She booked an appointment with a dentist near the station.",
        ),
        "shadows": (),
        "no_winner": (
            {
                "sentence": "The game Dentist Pro appeared in the app store.",
                "subtype": "named_entity_or_title",
            },
        ),
    },
    {
        "source": "bouillon",
        "target": "caldo",
        "source_zipf_band_en": "zipf_below_3_rare",
        "target_zipf_band_es": "zipf_3_to_4_mid",
        "polysemy_band": "low_1_to_3",
        "pos_shape": "single_sense",
        "family_repair_status": "aligned_mapping_contexts_rewritten",
        "active": {
            "canonical_pos": "noun",
            "gloss": "a clear seasoned broth",
        },
        "positive": (
            "Add bouillon to the rice for a richer flavor.",
            "The recipe starts with bouillon and fresh herbs.",
        ),
        "shadows": (),
        "no_winner": (
            {
                "sentence": "The restaurant Bouillon opened a second location downtown.",
                "subtype": "named_entity_or_title",
            },
        ),
    },
    {
        "source": "control",
        "target": "gobernar",
        "source_zipf_band_en": "zipf_5_plus_very_common",
        "target_zipf_band_es": "zipf_4_to_5_common",
        "polysemy_band": "high_10_plus",
        "pos_shape": "cross_pos_polysemy",
        "family_repair_status": "active_sense_corrected",
        "active": {
            "canonical_pos": "verb",
            "gloss": "govern, rule, or exercise authority over a place or organization",
        },
        "positive": (
            "The coalition hoped to control parliament after the election.",
            "A small council continued to control the territory after the coup.",
        ),
        "shadows": (
            {
                "target": "controlar",
                "canonical_pos": "verb",
                "gloss": "operate, regulate, or manage a device or setting",
                "sentence": "Use the slider to control the volume.",
            },
            {
                "target": "grupo de control",
                "canonical_pos": "noun",
                "gloss": "a standard comparison group in an experiment",
                "sentence": "The study included a control group and a treatment group.",
            },
        ),
        "no_winner": (
            {
                "sentence": "The keyboard shortcut uses the Control key.",
                "subtype": "named_entity_or_title",
            },
        ),
    },
)

DEFERRED_FAMILIES: tuple[dict[str, str], ...] = (
    {
        "family_id": "en-es:full-family-representative:bar:cercar",
        "source": "bar",
        "target": "cercar",
        "deferred_reason": "source_target_mapping_audit_required",
        "notes": "The draft active sense was an alcohol bar; cercar needs separate dictionary-source confirmation before repair.",
    },
    {
        "family_id": "en-es:full-family-representative:offset:distancia",
        "source": "offset",
        "target": "distancia",
        "deferred_reason": "source_target_mapping_audit_required",
        "notes": "The draft active sense was onset/outset; distancia needs a technical offset/distance mapping audit before repair.",
    },
    {
        "family_id": "en-es:full-family-representative:demand:deduccion",
        "source": "demand",
        "target": "deducción",
        "deferred_reason": "source_target_mapping_audit_required",
        "notes": "The draft active sense was demand/request, which does not match deducción without unexpected source evidence.",
    },
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a repaired, agent-reviewed pilot semantic-veto dataset from the "
            "full-family human-review packet. This remains pending user review."
        )
    )
    parser.add_argument("--review-json", type=Path, default=DEFAULT_REVIEW_JSON)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    review_path = _resolve_repo_path(args.review_json)
    dataset_path = _resolve_repo_path(args.dataset_out)
    json_path = _resolve_repo_path(args.json_out)
    markdown_path = _resolve_repo_path(args.markdown_out)
    report, dataset = build_repaired_pilot_report(
        review_payload=_load_json(review_path),
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
    markdown_path.write_text(render_repaired_pilot_markdown(report), encoding="utf-8")
    print(f"Wrote dataset artifact to {dataset_path}")
    print(f"Wrote JSON artifact to {json_path}")
    print(f"Wrote Markdown artifact to {markdown_path}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_repaired_pilot_report(
    *,
    review_payload: Mapping[str, object] | None = None,
    review_path: Path | None = None,
    dataset_path: Path | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    generated_at = generated_at or _utc_now()
    families = [_family_from_spec(spec) for spec in REPAIRED_FAMILY_SPECS]
    dataset = {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": DEFAULT_DATASET_ID,
        "description": (
            "Agent-repaired pilot sentence-veto packet derived from the full-family "
            "manual review. Repaired for semantic coherence, but still pending user review."
        ),
        "manual_review_state": MANUAL_REVIEW_STATE,
        "provenance": {
            "source_review_artifact": _repo_path(review_path),
            "source_review_authority": str(
                _as_mapping(review_payload or {}).get("review_authority")
                or "codex_agent_recommendation_not_user_approval"
            ),
        },
        "families": families,
        "deferred_families": [dict(row) for row in DEFERRED_FAMILIES],
    }
    case_rows = [case for family in families for case in _mapping_rows(family.get("cases"))]
    summary = {
        "repaired_family_count": len(families),
        "repaired_case_count": len(case_rows),
        "deferred_family_count": len(DEFERRED_FAMILIES),
        "trusted_family_count": 0,
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
        "source_band_case_counts": dict(
            sorted(Counter(_first_dim(case, "source_zipf_band_en") for case in case_rows).items())
        ),
    }
    checks = _checks(dataset)
    issues = [key for key, value in checks.items() if not value]
    report = {
        "schema_version": 1,
        "pair": "en-es",
        "status": "review" if issues else "ok",
        "decision": (
            "full_family_repaired_pilot_ready_for_user_review"
            if not issues
            else "full_family_repaired_pilot_needs_repair"
        ),
        "generated_at": generated_at,
        "inputs": {
            "review_path": _repo_path(review_path),
            "review_artifact_id": str(_as_mapping(review_payload or {}).get("artifact_id") or ""),
            "review_authority": str(
                _as_mapping(review_payload or {}).get("review_authority")
                or "codex_agent_recommendation_not_user_approval"
            ),
        },
        "outputs": {
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": DEFAULT_DATASET_ID,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "score_promotion": "none",
            "row_authority": "agent_repaired_user_review_pending",
            "repair_policy": (
                "Keep only aligned or salvageable pilot families; correct active senses "
                "where salvageable; defer questionable source-target mappings; use real "
                "Spanish shadow targets; use standalone source tokens; replace definition "
                "fallbacks with independent contexts."
            ),
            "trusted_row_rule": (
                "Rows remain untrusted until the user reviews the repaired packet or a "
                "separate locked-eval artifact is created from it."
            ),
        },
        "summary": summary,
        "e2e_checks": checks,
        "family_rows": [_family_report_row(family) for family in families],
        "deferred_families": [dict(row) for row in DEFERRED_FAMILIES],
        "next_steps": [
            "User reviews the repaired packet before any row is counted as trusted.",
            "Run sentence-veto scoring as a diagnostic comparison against the unrepaired pilot.",
            "Audit deferred mappings before spending LLM generation or manual rewrite effort on them.",
            "If approved, split the repaired packet into discovery and locked-eval lanes before scorer tuning.",
        ],
    }
    return report, dataset


def render_repaired_pilot_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Full-Family Repaired Pilot",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{_as_mapping(report.get('outputs')).get('dataset_path', '')}`",
        f"- Repaired families: `{summary.get('repaired_family_count', 0)}`",
        f"- Repaired cases: `{summary.get('repaired_case_count', 0)}`",
        f"- Deferred families: `{summary.get('deferred_family_count', 0)}`",
        f"- Trusted rows: `{summary.get('trusted_case_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("repair_policy") or ""),
        "",
        "Rows are semantically repaired, but they are not user-approved gold data.",
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
    lines.extend(["", "## Deferred Families", "", _deferred_table(report.get("deferred_families"))])
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines).rstrip() + "\n"


def _family_from_spec(spec: Mapping[str, object]) -> dict[str, object]:
    source = str(spec.get("source") or "")
    target = str(spec.get("target") or "")
    family_id = f"en-es:full-family-repaired-pilot:{_slug(source)}:{_slug(target)}"
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
                notes="agent-repaired independent positive context",
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
                notes="agent-repaired shadow context with real Spanish competitor target",
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
                notes=f"agent-repaired no-winner context; subtype={row.get('subtype') or 'missing'}",
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
            "family_repair_status": str(spec.get("family_repair_status") or ""),
            "source_of_repair": "docs/test_outputs/semantic_veto_full_family_agent_manual_review_en_es_latest.json",
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
    repair_status = str(spec.get("family_repair_status") or "missing")
    return {
        "case_id": f"{family_id}:{index:03d}",
        "sentence": str(sentence or ""),
        "source_phrase": source,
        "gold_winner": gold_winner,
        "gold_decision": gold_decision,
        "row_quality_status": "agent_repaired_user_review_pending",
        "human_review_status": "pending_user_review",
        "slice_tags": [
            DEFAULT_DATASET_ID,
            MANUAL_REVIEW_STATE,
            repair_status,
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
            "row_quality_status": ["agent_repaired_user_review_pending"],
            "family_repair_status": [repair_status],
            "source_zipf_band_en": [source_band],
            "target_zipf_band_es": [target_band],
            "polysemy_band": [polysemy],
            "pos_shape": [pos_shape],
            "manual_case_type": [manual_case_type],
            "no_winner_subtype": [no_winner_subtype],
            "context_source": ["agent_curated_independent_context"],
        },
        "notes": notes,
    }


def _checks(dataset: Mapping[str, object]) -> dict[str, bool]:
    families = _mapping_rows(dataset.get("families"))
    cases = [case for family in families for case in _mapping_rows(family.get("cases"))]
    shadows = [shadow for family in families for shadow in _mapping_rows(family.get("shadows"))]
    return {
        "has_repaired_families": bool(families),
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


def _deferred_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No deferred families._"
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


def _contains_source_as_token(*, sentence: str, source_phrase: str) -> bool:
    source_phrase = str(source_phrase or "").strip()
    if not source_phrase:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(source_phrase)}(?!\w)", str(sentence or ""), re.I))


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_rows(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [str(row) for row in value if str(row)]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
