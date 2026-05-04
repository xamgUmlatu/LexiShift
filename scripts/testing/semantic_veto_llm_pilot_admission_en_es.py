#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping, Sequence

from semantic_veto_llm_pilot_admission_rendering import (
    _limitations,
    _next_steps,
    _public_row,
    render_semantic_veto_llm_pilot_admission_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN = PROJECT_ROOT / "docs" / "test_inputs" / "semantic_veto_llm_pilot_plan_en_es.json"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_llm_pilot_admission_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_llm_pilot_admission_en_es_latest.md"
)

REQUIRED_FLOW_STEPS = (
    "freeze_candidate",
    "select_pilot_families",
    "generate_rows",
    "admission_filter",
    "split_discovery_locked_eval",
    "score_candidate",
    "expand_or_diagnose",
)
REQUIRED_ADMISSION_FILTERS = (
    "required_fields_present",
    "known_pilot_family",
    "gold_decision_matches_gold_type",
    "trigger_present_in_sentence",
    "spanish_target_lemma_absent_from_sentence",
    "label_leakage_absent_from_sentence",
    "duplicate_sentence_absent",
    "duplicate_row_id_absent",
    "conditional_reason_present",
    "minimum_sentence_shape",
    "locked_eval_not_used_for_threshold_tuning",
)
REQUIRED_STRATA_AXES = (
    "word_order",
    "trigger_position",
    "context_distance",
    "morphology",
    "register",
    "difficulty",
)
LABEL_LEAKAGE_TERMS = (
    "abstain",
    "allow",
    "allowed",
    "candidate replacement",
    "gold decision",
    "hide this",
    "should be hidden",
    "should be replaced",
    "spanish replacement",
)
GOLD_TYPES = ("positive_active", "shadow_negative", "phrase_no_winner")
GOLD_DECISIONS = ("allow", "abstain")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the no-spend en-es semantic-veto LLM pilot plan and admit "
            "generated sentence rows into discovery versus locked-eval splits."
        )
    )
    parser.add_argument("--plan-json", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--generated-rows-json", type=Path)
    parser.add_argument(
        "--generation-requests-json",
        type=Path,
        help=(
            "Optional request-packet JSON from semantic_veto_llm_pilot_generation_requests_en_es.py. "
            "When supplied, generated row_ids must match the rendered request packet."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    generated_rows_payload = (
        _load_json(args.generated_rows_json) if args.generated_rows_json else None
    )
    generation_requests_payload = (
        _load_json(args.generation_requests_json) if args.generation_requests_json else None
    )
    report = build_semantic_veto_llm_pilot_admission_report(
        plan_payload=_load_json(args.plan_json),
        plan_path=args.plan_json,
        generated_rows_payload=generated_rows_payload,
        generated_rows_path=args.generated_rows_json,
        generation_requests_payload=generation_requests_payload,
        generation_requests_path=args.generation_requests_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_semantic_veto_llm_pilot_admission_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_semantic_veto_llm_pilot_admission_report(
    *,
    plan_payload: Mapping[str, object],
    plan_path: Path | None = None,
    generated_rows_payload: object | None = None,
    generated_rows_path: Path | None = None,
    generation_requests_payload: object | None = None,
    generation_requests_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    plan_issues = _validate_plan(plan_payload)
    families = _family_map(plan_payload)
    generated_rows = _generated_rows(generated_rows_payload)
    generated_rows_present = generated_rows_payload is not None
    expected_row_ids = _expected_row_ids(generation_requests_payload)
    row_results = (
        _admit_rows(
            rows=generated_rows,
            plan=plan_payload,
            families=families,
            expected_row_ids=expected_row_ids,
        )
        if generated_rows_present
        else []
    )
    admitted_rows = [row for row in row_results if row["admission_status"] == "admitted"]
    rejected_rows = [row for row in row_results if row["admission_status"] == "rejected"]
    coverage_rows = _family_coverage_rows(
        plan=plan_payload,
        admitted_rows=admitted_rows,
    )
    coverage_shortfalls = [row for row in coverage_rows if int(row.get("shortfall_count") or 0) > 0]
    request_alignment = _request_alignment_summary(
        generation_requests_payload=generation_requests_payload,
        generated_rows_payload=generated_rows_payload,
        generated_rows=generated_rows,
        admitted_rows=admitted_rows,
    )
    request_alignment_issues = [
        issue
        for issue in _mapping_rows(request_alignment.get("issues"))
        if str(issue.get("severity") or "") == "error"
    ]
    status = _status(
        generated_rows_present=generated_rows_present,
        plan_issues=plan_issues,
        rejected_rows=rejected_rows,
        coverage_shortfalls=coverage_shortfalls,
        request_alignment_issues=request_alignment_issues,
    )
    return {
        "schema_version": 1,
        "status": status,
        "decision": _decision(
            status=status,
            generated_rows_present=generated_rows_present,
            rejected_rows=rejected_rows,
            coverage_shortfalls=coverage_shortfalls,
            request_alignment_issues=request_alignment_issues,
        ),
        "generated_at": generated_at,
        "pair": str(plan_payload.get("pair") or ""),
        "pilot": {
            "plan_path": _repo_path(plan_path),
            "pilot_id": str(plan_payload.get("pilot_id") or ""),
            "status": str(plan_payload.get("status") or ""),
            "purpose": str(plan_payload.get("purpose") or ""),
            "generated_rows_path": _repo_path(generated_rows_path),
            "generated_rows_present": generated_rows_present,
            "generation_requests_path": _repo_path(generation_requests_path),
        },
        "candidate": dict(_as_mapping(plan_payload.get("candidate"))),
        "strict_flow": {
            "runtime_policy_change": str(
                _as_mapping(plan_payload.get("candidate")).get("runtime_policy_change") or ""
            ),
            "source_evidence_promotion": str(
                _as_mapping(plan_payload.get("candidate")).get("source_evidence_promotion") or ""
            ),
            "threshold_tuning_allowed_on_locked_eval": bool(
                _as_mapping(plan_payload.get("split_policy")).get(
                    "threshold_tuning_allowed_on_locked_eval"
                )
            ),
            "required_flow_steps": list(REQUIRED_FLOW_STEPS),
            "required_admission_filters": list(REQUIRED_ADMISSION_FILTERS),
        },
        "plan_checks": {
            "issue_count": len(plan_issues),
            "issues": plan_issues,
            "required_flow_steps_present": not _missing_flow_steps(plan_payload),
            "required_filters_present": not _missing_filters(plan_payload),
            "required_strata_present": not _missing_strata_axes(plan_payload),
        },
        "planning_summary": _planning_summary(plan_payload),
        "admission_summary": _admission_summary(
            generated_rows_present=generated_rows_present,
            generated_rows=generated_rows,
            admitted_rows=admitted_rows,
            rejected_rows=rejected_rows,
        ),
        "request_alignment": request_alignment,
        "split_summary": _split_summary(admitted_rows),
        "family_coverage": coverage_rows,
        "rejection_reasons": dict(
            sorted(
                Counter(
                    reason
                    for row in rejected_rows
                    for reason in _as_sequence(row.get("rejection_reasons"))
                ).items()
            )
        ),
        "admitted_rows": admitted_rows,
        "rejected_rows": rejected_rows,
        "next_steps": _next_steps(
            generated_rows_present=generated_rows_present,
            plan_issues=plan_issues,
            rejected_rows=rejected_rows,
            coverage_shortfalls=coverage_shortfalls,
            request_alignment_issues=request_alignment_issues,
        ),
        "limitations": _limitations(generated_rows_present=generated_rows_present),
    }


def _validate_plan(plan: Mapping[str, object]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if int(plan.get("schema_version") or 0) != 1:
        issues.append(_issue("schema_version", "error", "Expected schema_version 1."))
    if str(plan.get("pair") or "") != "en-es":
        issues.append(_issue("pair", "error", "Pilot plan must be for en-es."))
    if str(plan.get("status") or "") != "no_spend_preflight":
        issues.append(_issue("status", "error", "Pilot plan must start in no_spend_preflight."))
    candidate = _as_mapping(plan.get("candidate"))
    if not str(candidate.get("candidate_id") or "").strip():
        issues.append(_issue("candidate", "error", "Candidate id is missing."))
    if str(candidate.get("decision_shape") or "") != "allow_default_shadow_veto":
        issues.append(_issue("candidate", "error", "Candidate must freeze the veto-only shape."))
    if str(candidate.get("runtime_policy_change") or "") != "none":
        issues.append(_issue("candidate", "error", "Pilot admission cannot change runtime policy."))
    if str(candidate.get("source_evidence_promotion") or "") != "none":
        issues.append(
            _issue("candidate", "error", "Pilot admission cannot promote source evidence.")
        )
    for step_id in _missing_flow_steps(plan):
        issues.append(_issue(step_id, "error", "Required flow step is missing."))
    for filter_id in _missing_filters(plan):
        issues.append(_issue(filter_id, "error", "Required admission filter is missing."))
    for axis in _missing_strata_axes(plan):
        issues.append(_issue(axis, "error", "Required generation stratum is missing."))
    split_policy = _as_mapping(plan.get("split_policy"))
    modulo = int(split_policy.get("modulo") or 0)
    locked_remainders = [int(value) for value in split_policy.get("locked_eval_remainders") or ()]
    if modulo < 2:
        issues.append(_issue("split_policy", "error", "Split modulo must be at least 2."))
    if not locked_remainders:
        issues.append(_issue("split_policy", "error", "Locked-eval remainders are missing."))
    if any(remainder < 0 or remainder >= modulo for remainder in locked_remainders):
        issues.append(_issue("split_policy", "error", "Locked-eval remainders must fit modulo."))
    if bool(split_policy.get("threshold_tuning_allowed_on_locked_eval")):
        issues.append(
            _issue(
                "split_policy",
                "error",
                "Locked eval cannot be used for threshold tuning.",
            )
        )
    row_contract = _as_mapping(plan.get("row_contract"))
    missing_contract_fields = [
        field
        for field in (
            "row_id",
            "family_id",
            "trigger",
            "candidate_replacement",
            "sentence",
            "gold_decision",
            "gold_type",
            "active_sense",
            "gold_reason",
            "pos",
            "generator_id",
            "prompt_id",
        )
        if field not in set(str(value) for value in row_contract.get("required_fields") or ())
    ]
    for field in missing_contract_fields:
        issues.append(_issue(field, "error", "Required row-contract field is missing."))
    if set(row_contract.get("gold_types") or ()) != set(GOLD_TYPES):
        issues.append(_issue("gold_types", "error", "Gold type contract is incomplete."))
    if set(row_contract.get("gold_decisions") or ()) != set(GOLD_DECISIONS):
        issues.append(_issue("gold_decisions", "error", "Gold decision contract is incomplete."))
    family_ids: set[str] = set()
    for family in _mapping_rows(plan.get("pilot_families")):
        family_id = str(family.get("family_id") or "").strip()
        if not family_id:
            issues.append(_issue("pilot_families", "error", "A family lacks family_id."))
            continue
        if family_id in family_ids:
            issues.append(_issue(family_id, "error", "Duplicate pilot family id."))
        family_ids.add(family_id)
        for field in ("trigger", "candidate_replacement", "active_sense", "pos"):
            if not str(family.get(field) or "").strip():
                issues.append(_issue(family_id, "error", f"Family lacks {field}."))
        planned_rows = _as_mapping(family.get("planned_rows"))
        for gold_type in GOLD_TYPES:
            if int(planned_rows.get(gold_type) or 0) <= 0:
                issues.append(_issue(family_id, "error", f"Family lacks planned {gold_type} rows."))
    if not family_ids:
        issues.append(_issue("pilot_families", "error", "No pilot families configured."))
    return issues


def _admit_rows(
    *,
    rows: Sequence[Mapping[str, object]],
    plan: Mapping[str, object],
    families: Mapping[str, Mapping[str, object]],
    expected_row_ids: frozenset[str] | None = None,
) -> list[dict[str, object]]:
    row_contract = _as_mapping(plan.get("row_contract"))
    required_fields = [str(field) for field in row_contract.get("required_fields") or ()]
    decision_by_gold_type = {
        str(key): str(value)
        for key, value in _as_mapping(row_contract.get("decision_by_gold_type")).items()
    }
    conditional_fields = {
        str(key): [str(field) for field in value or ()]
        for key, value in _as_mapping(row_contract.get("conditional_fields")).items()
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes))
    }
    seen_row_ids: set[str] = set()
    seen_sentences: set[str] = set()
    results: list[dict[str, object]] = []
    for row in rows:
        reasons: list[str] = []
        row_id = str(row.get("row_id") or "").strip()
        family_id = str(row.get("family_id") or "").strip()
        sentence = str(row.get("sentence") or "").strip()
        normalized_sentence = _normalize_text(sentence)
        missing_fields = [field for field in required_fields if not str(row.get(field) or "")]
        reasons.extend(f"missing_required_field:{field}" for field in missing_fields)
        if expected_row_ids is not None and row_id and row_id not in expected_row_ids:
            reasons.append("unexpected_row_id")
        if row_id in seen_row_ids:
            reasons.append("duplicate_row_id")
        if row_id:
            seen_row_ids.add(row_id)
        if normalized_sentence in seen_sentences and normalized_sentence:
            reasons.append("duplicate_sentence")
        if normalized_sentence:
            seen_sentences.add(normalized_sentence)
        family = families.get(family_id)
        if family is None:
            reasons.append("unknown_family_id")
        else:
            reasons.extend(_row_family_mismatch_reasons(row=row, family=family))
        gold_type = str(row.get("gold_type") or "").strip()
        gold_decision = str(row.get("gold_decision") or "").strip()
        if gold_type not in GOLD_TYPES:
            reasons.append("unsupported_gold_type")
        if gold_decision not in GOLD_DECISIONS:
            reasons.append("unsupported_gold_decision")
        expected_decision = decision_by_gold_type.get(gold_type)
        if expected_decision and gold_decision != expected_decision:
            reasons.append("gold_decision_mismatch")
        for field in conditional_fields.get(gold_type, ()):
            if not str(row.get(field) or "").strip():
                reasons.append(f"missing_conditional_field:{field}")
        if sentence and not _contains_wordish(sentence, str(row.get("trigger") or "")):
            reasons.append("trigger_missing_from_sentence")
        if sentence and _contains_wordish(sentence, str(row.get("candidate_replacement") or "")):
            reasons.append("spanish_target_lemma_in_sentence")
        if _has_label_leakage(sentence):
            reasons.append("label_leakage_in_sentence")
        if sentence and not _minimum_sentence_shape(sentence):
            reasons.append("minimum_sentence_shape_failed")
        split = _split_for_row(row=row, plan=plan) if not reasons else ""
        public_row = _public_row(
            row=row, admission_status="admitted" if not reasons else "rejected"
        )
        public_row["rejection_reasons"] = sorted(set(reasons))
        public_row["split"] = split
        results.append(public_row)
    return results


def _row_family_mismatch_reasons(
    *,
    row: Mapping[str, object],
    family: Mapping[str, object],
) -> list[str]:
    reasons: list[str] = []
    for field in ("trigger", "candidate_replacement", "active_sense", "pos"):
        row_value = _normalize_text(str(row.get(field) or ""))
        family_value = _normalize_text(str(family.get(field) or ""))
        if row_value and family_value and row_value != family_value:
            reasons.append(f"family_mismatch:{field}")
    return reasons


def _split_for_row(*, row: Mapping[str, object], plan: Mapping[str, object]) -> str:
    split_policy = _as_mapping(plan.get("split_policy"))
    modulo = max(2, int(split_policy.get("modulo") or 2))
    locked_remainders = {int(value) for value in split_policy.get("locked_eval_remainders") or ()}
    row_id = str(row.get("row_id") or "")
    digest = hashlib.sha256(row_id.encode("utf-8")).hexdigest()
    remainder = int(digest[:8], 16) % modulo
    return "locked_eval" if remainder in locked_remainders else "discovery"


def _family_coverage_rows(
    *,
    plan: Mapping[str, object],
    admitted_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], int] = Counter(
        (
            str(row.get("family_id") or ""),
            str(row.get("gold_type") or ""),
        )
        for row in admitted_rows
    )
    rows: list[dict[str, object]] = []
    for family in _mapping_rows(plan.get("pilot_families")):
        family_id = str(family.get("family_id") or "")
        planned_rows = _as_mapping(family.get("planned_rows"))
        for gold_type in GOLD_TYPES:
            planned = int(planned_rows.get(gold_type) or 0)
            admitted = counts.get((family_id, gold_type), 0)
            rows.append(
                {
                    "family_id": family_id,
                    "trigger": str(family.get("trigger") or ""),
                    "gold_type": gold_type,
                    "planned_count": planned,
                    "admitted_count": admitted,
                    "shortfall_count": max(0, planned - admitted),
                }
            )
    return rows


def _planning_summary(plan: Mapping[str, object]) -> dict[str, object]:
    planned_by_type: Counter[str] = Counter()
    family_rows = []
    for family in _mapping_rows(plan.get("pilot_families")):
        planned_rows = _as_mapping(family.get("planned_rows"))
        family_total = 0
        for gold_type in GOLD_TYPES:
            count = int(planned_rows.get(gold_type) or 0)
            planned_by_type[gold_type] += count
            family_total += count
        family_rows.append(
            {
                "family_id": str(family.get("family_id") or ""),
                "trigger": str(family.get("trigger") or ""),
                "candidate_replacement": str(family.get("candidate_replacement") or ""),
                "pos": str(family.get("pos") or ""),
                "frequency_band": str(family.get("frequency_band") or ""),
                "ambiguity_class": str(family.get("ambiguity_class") or ""),
                "planned_count": family_total,
            }
        )
    return {
        "family_count": len(family_rows),
        "planned_row_count": sum(planned_by_type.values()),
        "planned_rows_by_type": dict(sorted(planned_by_type.items())),
        "generation_strata_axes": sorted(_as_mapping(plan.get("generation_strata")).keys()),
        "families": family_rows,
    }


def _admission_summary(
    *,
    generated_rows_present: bool,
    generated_rows: Sequence[Mapping[str, object]],
    admitted_rows: Sequence[Mapping[str, object]],
    rejected_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "generated_rows_present": generated_rows_present,
        "generated_row_count": len(generated_rows),
        "admitted_row_count": len(admitted_rows),
        "rejected_row_count": len(rejected_rows),
        "admitted_rows_by_type": dict(
            sorted(Counter(str(row.get("gold_type") or "") for row in admitted_rows).items())
        ),
        "rejected_rows_by_type": dict(
            sorted(Counter(str(row.get("gold_type") or "") for row in rejected_rows).items())
        ),
    }


def _split_summary(admitted_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    split_counts = Counter(str(row.get("split") or "") for row in admitted_rows)
    type_by_split: dict[str, dict[str, int]] = defaultdict(dict)
    for split, gold_type_counts in _nested_counter(admitted_rows).items():
        type_by_split[split] = dict(sorted(gold_type_counts.items()))
    return {
        "discovery_count": split_counts.get("discovery", 0),
        "locked_eval_count": split_counts.get("locked_eval", 0),
        "rows_by_split": dict(sorted(split_counts.items())),
        "gold_types_by_split": dict(sorted(type_by_split.items())),
    }


def _request_alignment_summary(
    *,
    generation_requests_payload: object | None,
    generated_rows_payload: object | None,
    generated_rows: Sequence[Mapping[str, object]],
    admitted_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    request_packet_expected_row_ids = _expected_row_ids(generation_requests_payload)
    selected_expected_row_ids = _selected_expected_row_ids(generated_rows_payload)
    expected_row_ids = selected_expected_row_ids or request_packet_expected_row_ids
    generated_row_ids = {
        str(row.get("row_id") or "").strip()
        for row in generated_rows
        if str(row.get("row_id") or "").strip()
    }
    admitted_row_ids = {
        str(row.get("row_id") or "").strip()
        for row in admitted_rows
        if str(row.get("row_id") or "").strip()
    }
    if expected_row_ids is None:
        return {
            "request_packet_present": False,
            "request_packet_expected_row_count": 0,
            "selected_expected_row_count": 0,
            "expected_row_count": 0,
            "generated_row_id_count": len(generated_row_ids),
            "matched_expected_row_count": 0,
            "admitted_expected_row_count": 0,
            "missing_expected_row_ids": [],
            "unexpected_row_ids": [],
            "issues": [],
        }
    missing_expected = sorted(expected_row_ids - generated_row_ids)
    unexpected = sorted(generated_row_ids - expected_row_ids)
    issues = []
    if missing_expected:
        issues.append(
            {
                "subject": "missing_expected_row_ids",
                "severity": "error",
                "message": f"{len(missing_expected)} expected generated rows are missing.",
            }
        )
    if unexpected:
        issues.append(
            {
                "subject": "unexpected_row_ids",
                "severity": "error",
                "message": f"{len(unexpected)} generated rows were not in the request packet.",
            }
        )
    return {
        "request_packet_present": True,
        "request_packet_expected_row_count": len(request_packet_expected_row_ids or ()),
        "selected_expected_row_count": len(selected_expected_row_ids or ()),
        "expected_row_count": len(expected_row_ids),
        "generated_row_id_count": len(generated_row_ids),
        "matched_expected_row_count": len(expected_row_ids & generated_row_ids),
        "admitted_expected_row_count": len(expected_row_ids & admitted_row_ids),
        "missing_expected_row_ids": missing_expected,
        "unexpected_row_ids": unexpected,
        "issues": issues,
    }


def _expected_row_ids(payload: object | None) -> frozenset[str] | None:
    if payload is None:
        return None
    if isinstance(payload, Mapping):
        rows = _mapping_rows(payload.get("requests"))
    else:
        rows = _mapping_rows(payload)
    return frozenset(
        str(row.get("expected_row_id") or "").strip()
        for row in rows
        if str(row.get("expected_row_id") or "").strip()
    )


def _selected_expected_row_ids(payload: object | None) -> frozenset[str] | None:
    if not isinstance(payload, Mapping):
        return None
    selected = payload.get("selected_expected_row_ids")
    if not isinstance(selected, Sequence) or isinstance(selected, (str, bytes)):
        return None
    values = frozenset(str(value).strip() for value in selected if str(value).strip())
    return values or None


def _nested_counter(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counts[str(row.get("split") or "")][str(row.get("gold_type") or "")] += 1
    return counts


def _status(
    *,
    generated_rows_present: bool,
    plan_issues: Sequence[Mapping[str, object]],
    rejected_rows: Sequence[Mapping[str, object]],
    coverage_shortfalls: Sequence[Mapping[str, object]],
    request_alignment_issues: Sequence[Mapping[str, object]],
) -> str:
    if plan_issues:
        return "review"
    if not generated_rows_present:
        return "ok"
    if rejected_rows or coverage_shortfalls or request_alignment_issues:
        return "review"
    return "ok"


def _decision(
    *,
    status: str,
    generated_rows_present: bool,
    rejected_rows: Sequence[Mapping[str, object]],
    coverage_shortfalls: Sequence[Mapping[str, object]],
    request_alignment_issues: Sequence[Mapping[str, object]],
) -> str:
    if status != "ok":
        if rejected_rows:
            return "generated_rows_need_repair"
        if coverage_shortfalls:
            return "pilot_coverage_incomplete"
        if request_alignment_issues:
            return "generation_request_alignment_failed"
        return "preflight_needs_repair"
    if not generated_rows_present:
        return "ready_for_generation"
    return "admitted_for_scoring"


def _generated_rows(payload: object | None) -> list[Mapping[str, object]]:
    if payload is None:
        return []
    if isinstance(payload, Mapping):
        return _mapping_rows(payload.get("rows"))
    return _mapping_rows(payload)


def _family_map(plan: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row.get("family_id") or ""): row for row in _mapping_rows(plan.get("pilot_families"))
    }


def _missing_flow_steps(plan: Mapping[str, object]) -> list[str]:
    present = {str(row.get("step_id") or "") for row in _mapping_rows(plan.get("flow_steps"))}
    return [step_id for step_id in REQUIRED_FLOW_STEPS if step_id not in present]


def _missing_filters(plan: Mapping[str, object]) -> list[str]:
    present = {
        str(row.get("filter_id") or "") for row in _mapping_rows(plan.get("admission_filters"))
    }
    return [filter_id for filter_id in REQUIRED_ADMISSION_FILTERS if filter_id not in present]


def _missing_strata_axes(plan: Mapping[str, object]) -> list[str]:
    strata = _as_mapping(plan.get("generation_strata"))
    return [axis for axis in REQUIRED_STRATA_AXES if not strata.get(axis)]


def _minimum_sentence_shape(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", sentence)
    return len(words) >= 6 and sentence[-1:] in {".", "!", "?"}


def _contains_wordish(sentence: str, term: str) -> bool:
    term = term.strip()
    if not term:
        return False
    pattern = r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])"
    return re.search(pattern, sentence, flags=re.IGNORECASE) is not None


def _has_label_leakage(sentence: str) -> bool:
    normalized_sentence = _normalize_text(sentence)
    for term in LABEL_LEAKAGE_TERMS:
        if " " in term:
            if term in normalized_sentence:
                return True
        elif _contains_wordish(sentence, term):
            return True
    return False


def _issue(subject: str, severity: str, message: str) -> dict[str, object]:
    return {"subject": subject, "severity": severity, "message": message}


def _load_json(path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def _repo_path(path: Path | None) -> str:
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
