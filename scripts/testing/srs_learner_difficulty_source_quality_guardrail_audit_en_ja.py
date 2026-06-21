#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _calibration_context,
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_COMPONENT_MATRIX,
)
from srs_learner_difficulty_validation_failure_group_audit_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_VALIDATION_JSON,
    component_lookup,
    count_values,
    load_json,
    max_signal,
    signal_arrays_from_component,
)


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_quality_guardrail_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_quality_guardrail_audit_en_ja_latest.md"
)
VOCAB_STATES = frozenset({"normal_vocab", "deprioritized_vocab"})
SCALAR_TREATMENTS = frozenset({"", "vocab"})
NON_SCALAR_TREATMENTS = frozenset({"topic_only", "omit", "grammar_item"})


@dataclass(frozen=True)
class GuardrailSpec:
    guardrail_id: str
    action: str
    description: str
    all_terms: tuple[str, ...] = ()
    any_terms: tuple[str, ...] = ()
    threshold: float = 0.75


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit whether existing en-ja source signals can separate candidate-quality "
            "problems from scalar difficulty-ordering problems."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--detail-limit", type=int, default=16)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        calibration_json_path=_resolve_path(args.calibration_json),
        holdout_json_path=_resolve_path(args.holdout_json),
        validation_json_path=_resolve_path(args.validation_json),
        detail_limit=max(1, int(args.detail_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    component_matrix_path: Path,
    calibration_matrix_path: Path,
    calibration_json_path: Path,
    holdout_json_path: Path,
    validation_json_path: Path,
    detail_limit: int,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    calibration = np.load(calibration_matrix_path)
    signals = guardrail_signal_arrays(component)
    labeled_rows = all_labeled_rows(
        component=component,
        calibration=calibration,
        calibration_payload=load_json(calibration_json_path),
        holdout_payload=load_json(holdout_json_path),
        validation_payload=load_json(validation_json_path),
    )
    guardrails = guardrail_specs()
    guardrail_reports = [
        guardrail_report(
            spec,
            mask=guardrail_mask(spec, signals),
            labeled_rows=labeled_rows,
            component=component,
            signals=signals,
            detail_limit=detail_limit,
        )
        for spec in guardrails
    ]
    union_masks = {
        "review_union": np.logical_or.reduce(
            [np.asarray(guardrail_mask(spec, signals), dtype=bool) for spec in guardrails]
        ),
        "source_fix_review_union": np.logical_or.reduce(
            [
                np.asarray(guardrail_mask(spec, signals), dtype=bool)
                for spec in guardrails
                if spec.action == "source_fix_review"
            ]
        ),
        "topic_review_union": np.logical_or.reduce(
            [
                np.asarray(guardrail_mask(spec, signals), dtype=bool)
                for spec in guardrails
                if spec.action == "topic_deprioritize_review"
            ]
        ),
    }
    union_reports = [
        guardrail_report(
            GuardrailSpec(
                guardrail_id=guardrail_id,
                action="review_union",
                description=f"Union of {guardrail_id.replace('_', ' ')} masks.",
            ),
            mask=mask,
            labeled_rows=labeled_rows,
            component=component,
            signals=signals,
            detail_limit=detail_limit,
        )
        for guardrail_id, mask in union_masks.items()
    ]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "method": {
            "purpose": (
                "Determine which non-ladder or source-quality labels are already "
                "detectable from existing source signals, and estimate collateral "
                "against scalar vocabulary labels."
            ),
            "guardrail_semantics": (
                "Most masks are review/deprioritization proposals, not automatic "
                "deletion rules. Source-reading mismatches require direct source "
                "validation before runtime behavior changes."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "calibration_json": _repo_or_home_path(calibration_json_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "validation_json": _repo_or_home_path(validation_json_path),
        },
        "summary": {
            "label_scope": label_scope(labeled_rows),
            "validation_non_scalar_rows": validation_non_scalar_rows(labeled_rows),
            "guardrail_leaderboard": guardrail_leaderboard(guardrail_reports),
            "union_reports": union_reports,
            "uncovered_validation_non_scalar": uncovered_validation_non_scalar(
                labeled_rows,
                np.asarray(union_masks["review_union"], dtype=bool),
                detail_limit=detail_limit,
            ),
            "interpretation": interpretation(guardrail_reports, union_reports),
        },
        "guardrails": guardrail_reports,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "calibration_json": calibration_json_path,
                "holdout_json": holdout_json_path,
                "validation_json": validation_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "failure_group_audit": SCRIPT_DIR
                / "srs_learner_difficulty_validation_failure_group_audit_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "signal_sweep": SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def all_labeled_rows(
    *,
    component: object,
    calibration: object,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    validation_payload: Mapping[str, object],
) -> list[dict[str, object]]:
    rows = calibration_rows(component, calibration, calibration_payload=calibration_payload)
    rows.extend(json_rows(component, holdout_payload, dataset_id="holdout"))
    rows.extend(json_rows(component, validation_payload, dataset_id="stitch_validation"))
    return rows


def calibration_rows(
    component: object,
    calibration: object,
    *,
    calibration_payload: Mapping[str, object],
) -> list[dict[str, object]]:
    context = _calibration_context(calibration, component)
    labels_by_lemma = {
        str(row.get("lemma") or ""): row
        for row in calibration_payload.get("labels", ())
        if isinstance(row, Mapping)
    }
    rows = []
    for index, label in enumerate(context["labels"]):
        lemma = str(calibration["calibration_lemmas"][index])
        label_row = _mapping(labels_by_lemma.get(lemma))
        component_index = int(np.asarray(context["component_indices"], dtype=np.int64)[index])
        expected_value = _optional_float(np.asarray(context["expected_values"])[index])
        state = str(np.asarray(context["expected_candidate_states"], dtype=str)[index])
        mode = str(np.asarray(context["expected_presentation_modes"], dtype=str)[index])
        problem_class = str(np.asarray(context["expected_problem_classes"], dtype=str)[index])
        if expected_value is not None and state in VOCAB_STATES and component_index >= 0:
            target = "scalar_vocab"
        elif component_index < 0:
            target = "unmatched"
        else:
            target = "non_scalar"
        rows.append(
            {
                "dataset_id": "calibration",
                "label": str(label),
                "component_index": component_index,
                "target": target,
                "treatment": "",
                "expected_candidate_state": state,
                "expected_problem_class": problem_class,
                "expected_presentation_mode": mode,
                "expected_learner_difficulty": _rounded(expected_value),
                "rationale": str(label_row.get("rationale") or "")[:180],
            }
        )
    return rows


def json_rows(
    component: object,
    payload: Mapping[str, object],
    *,
    dataset_id: str,
) -> list[dict[str, object]]:
    lookup = component_lookup(component)
    rows = []
    for index, row in enumerate(payload.get("labels", ())):
        if not isinstance(row, Mapping):
            continue
        lemma = str(row.get("lemma") or "").strip()
        reading = str(row.get("expected_reading") or row.get("reading") or "").strip()
        label = f"{lemma}/{reading}" if reading else lemma
        component_index = lookup.get((lemma, reading), -1)
        treatment = str(row.get("treatment") or "")
        expected_value = _optional_float(row.get("expected_learner_difficulty"))
        state = str(row.get("expected_candidate_state") or "")
        if (
            expected_value is not None
            and treatment in SCALAR_TREATMENTS
            and (not state or state in VOCAB_STATES)
            and component_index >= 0
        ):
            target = "scalar_vocab"
        elif component_index < 0:
            target = "unmatched"
        else:
            target = "non_scalar"
        rows.append(
            {
                "dataset_id": dataset_id,
                "label": label,
                "component_index": int(component_index),
                "target": target,
                "treatment": treatment,
                "expected_candidate_state": state,
                "expected_problem_class": str(row.get("expected_problem_class") or ""),
                "expected_presentation_mode": str(row.get("expected_presentation_mode") or ""),
                "expected_learner_difficulty": _rounded(expected_value),
                "reference_difficulty": _rounded(row.get("reference_difficulty")),
                "rationale": str(row.get("rationale") or "")[:180],
            }
        )
    return rows


def guardrail_signal_arrays(component: object) -> dict[str, object]:
    arrays = signal_arrays_from_component(component)
    count = len(component["lemmas"])
    arrays["reading_or_form_suspect_any"] = max_signal(
        arrays,
        (
            "jmdict_kana_preferred_risk",
            "jmdict_search_only_form_risk",
            "jmdict_reading_form_marked_risk",
            "jmdict_reading_restricted_risk",
            "jmdict_restriction_complexity_risk",
        ),
        count=count,
    )
    arrays["function_or_affix_any"] = max_signal(
        arrays,
        (
            "jmdict_particle_auxiliary_class",
            "jmdict_function_discourse_class",
            "jmdict_affix_counter_class",
        ),
        count=count,
    )
    arrays["dictionary_non_ladder_any"] = max_signal(
        arrays,
        ("jmdict_non_vocab_risk", "jmdict_non_ladder_entry_risk"),
        count=count,
    )
    arrays["field_register_or_marked_any"] = max_signal(
        arrays,
        (
            "jmdict_field_marked_risk",
            "jmdict_register_marked_risk",
            "jmdict_marked_usage_risk",
            "jmdict_search_only_form_risk",
        ),
        count=count,
    )
    arrays["abbrev_entity_or_field_any"] = max_signal(
        arrays,
        (
            "jmdict_abbreviation_risk",
            "entity_or_acronym_any",
            "field_register_or_marked_any",
        ),
        count=count,
    )
    arrays["rare_wago_source_quality_any"] = max_signal(
        arrays,
        (
            "rare_wago_tail_risk",
            "rare_wago_obscure_written_risk",
            "non_standard_any",
            "reading_or_form_suspect_any",
        ),
        count=count,
    )
    return arrays


def guardrail_specs() -> list[GuardrailSpec]:
    return [
        GuardrailSpec(
            "function_or_affix_review",
            "review",
            "Function-word, particle/auxiliary, affix, or counter-like entries.",
            any_terms=("function_or_affix_any",),
        ),
        GuardrailSpec(
            "dictionary_non_ladder_review",
            "source_fix_review",
            "Dictionary evidence says the entry is not a normal ladder vocabulary item.",
            any_terms=("dictionary_non_ladder_any",),
            threshold=0.30,
        ),
        GuardrailSpec(
            "reading_form_source_review",
            "source_fix_review",
            "Rare rows with kana-preferred, search-only, marked, or restricted form evidence.",
            all_terms=("frequency_tail90",),
            any_terms=("reading_or_form_suspect_any",),
            threshold=0.70,
        ),
        GuardrailSpec(
            "rare_wago_nonstandard_review",
            "review",
            "Rare native/wago rows with non-standard or obscure written-form pressure.",
            all_terms=("wtype_wago_ease", "frequency_tail90", "non_standard_any"),
            threshold=0.75,
        ),
        GuardrailSpec(
            "domain_marked_rare_review",
            "topic_deprioritize_review",
            "Rare rows with field, register, marked usage, or search-only evidence.",
            all_terms=("frequency_tail90",),
            any_terms=("field_register_or_marked_any",),
            threshold=0.75,
        ),
        GuardrailSpec(
            "rare_loanword_topic_review",
            "topic_deprioritize_review",
            "Rare or domain-like loanwords with abbreviation, entity, or field pressure.",
            all_terms=("wtype_gairaigo_risk", "frequency_tail90"),
            any_terms=("abbrev_entity_or_field_any",),
            threshold=0.75,
        ),
        GuardrailSpec(
            "entity_or_acronym_rare_review",
            "topic_deprioritize_review",
            "Rare rows with entity, proper-name, acronym, or abbreviation pressure.",
            all_terms=("frequency_tail90",),
            any_terms=("entity_or_acronym_any", "jmdict_abbreviation_risk"),
            threshold=0.75,
        ),
        GuardrailSpec(
            "kango_marked_rare_review",
            "review",
            "Rare kango rows with field/register/non-ladder pressure.",
            all_terms=("wtype_kango_risk", "frequency_tail90"),
            any_terms=("field_register_or_marked_any", "dictionary_non_ladder_any"),
            threshold=0.75,
        ),
    ]


def guardrail_mask(spec: GuardrailSpec, signals: Mapping[str, object]) -> object:
    count = len(next(iter(signals.values()))) if signals else 0
    selected = np.ones(count, dtype=bool)
    for name in spec.all_terms:
        selected &= (
            np.asarray(signals.get(name, np.zeros(count)), dtype=np.float32) >= spec.threshold
        )
    if spec.any_terms:
        any_selected = np.zeros(count, dtype=bool)
        for name in spec.any_terms:
            any_selected |= (
                np.asarray(signals.get(name, np.zeros(count)), dtype=np.float32) >= spec.threshold
            )
        selected &= any_selected
    return selected


def guardrail_report(
    spec: GuardrailSpec,
    *,
    mask: object,
    labeled_rows: Sequence[Mapping[str, object]],
    component: object,
    signals: Mapping[str, object],
    detail_limit: int,
) -> dict[str, object]:
    selected = np.asarray(mask, dtype=bool)
    rows = [row for row in labeled_rows if row.get("component_index", -1) >= 0]
    caught = [row for row in rows if selected[int(row["component_index"])]]
    validation_rows = [row for row in rows if row.get("dataset_id") == "stitch_validation"]
    validation_bad = [
        row
        for row in validation_rows
        if row.get("target") == "non_scalar"
        and str(row.get("treatment") or "") in NON_SCALAR_TREATMENTS
    ]
    validation_bad_caught = [row for row in validation_bad if selected[int(row["component_index"])]]
    validation_scalar = [row for row in validation_rows if row.get("target") == "scalar_vocab"]
    validation_scalar_caught = [
        row for row in validation_scalar if selected[int(row["component_index"])]
    ]
    all_scalar = [row for row in rows if row.get("target") == "scalar_vocab"]
    all_scalar_caught = [row for row in all_scalar if selected[int(row["component_index"])]]
    report = {
        "guardrail_id": spec.guardrail_id,
        "action": spec.action,
        "description": spec.description,
        "threshold": _rounded(spec.threshold),
        "full_vocab_count": int(selected.sum()),
        "validation_non_scalar_caught": len(validation_bad_caught),
        "validation_non_scalar_total": len(validation_bad),
        "validation_non_scalar_recall": _rounded(
            len(validation_bad_caught) / len(validation_bad) if validation_bad else None
        ),
        "validation_scalar_collateral": len(validation_scalar_caught),
        "validation_scalar_total": len(validation_scalar),
        "validation_precision_proxy": _rounded(
            len(validation_bad_caught)
            / (len(validation_bad_caught) + len(validation_scalar_caught))
            if validation_bad_caught or validation_scalar_caught
            else None
        ),
        "all_scalar_collateral": len(all_scalar_caught),
        "all_scalar_total": len(all_scalar),
        "caught_by_dataset_target": caught_by_dataset_target(caught),
        "caught_validation_non_scalar": enrich_rows(
            validation_bad_caught,
            component=component,
            signals=signals,
            limit=detail_limit,
        ),
        "validation_scalar_collateral_examples": enrich_rows(
            validation_scalar_caught,
            component=component,
            signals=signals,
            limit=detail_limit,
        ),
    }
    return report


def caught_by_dataset_target(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for row in rows:
        dataset = str(row.get("dataset_id") or "")
        target = str(row.get("target") or "")
        result.setdefault(dataset, {})
        result[dataset][target] = result[dataset].get(target, 0) + 1
    return result


def enrich_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    component: object,
    signals: Mapping[str, object],
    limit: int,
) -> list[dict[str, object]]:
    output = []
    for row in rows[:limit]:
        index = int(row["component_index"])
        output.append(
            {
                "label": row.get("label"),
                "dataset_id": row.get("dataset_id"),
                "target": row.get("target"),
                "treatment": row.get("treatment"),
                "expected_problem_class": row.get("expected_problem_class"),
                "expected_learner_difficulty": row.get("expected_learner_difficulty"),
                "reference_difficulty": row.get("reference_difficulty"),
                "component_state": str(component["candidate_states"][index]),
                "component_problem_class": str(component["problem_classes"][index]),
                "key_signals": key_signal_values(index, signals),
                "rationale": row.get("rationale"),
            }
        )
    return output


def key_signal_values(index: int, signals: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "frequency",
        "frequency_tail90",
        "wtype_gairaigo_risk",
        "wtype_wago_ease",
        "wtype_kango_risk",
        "field_register_or_marked_any",
        "reading_or_form_suspect_any",
        "function_or_affix_any",
        "dictionary_non_ladder_any",
        "entity_or_acronym_any",
        "jmdict_abbreviation_risk",
        "non_standard_any",
        "rare_wago_obscure_written_risk",
    )
    result = {}
    for key in keys:
        values = signals.get(key)
        if values is None:
            continue
        value = float(np.asarray(values, dtype=np.float32)[index])
        if abs(value) > 1e-6:
            result[key] = _rounded(value)
    return result


def label_scope(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "total_rows": len(rows),
        "by_dataset_target": caught_by_dataset_target(rows),
        "validation_treatment_counts": count_values(
            row.get("treatment") for row in rows if row.get("dataset_id") == "stitch_validation"
        ),
    }


def validation_non_scalar_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "label": row.get("label"),
            "treatment": row.get("treatment"),
            "expected_problem_class": row.get("expected_problem_class"),
            "reference_difficulty": row.get("reference_difficulty"),
            "rationale": row.get("rationale"),
        }
        for row in rows
        if row.get("dataset_id") == "stitch_validation" and row.get("target") == "non_scalar"
    ]


def guardrail_leaderboard(reports: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows = []
    for report in reports:
        rows.append(
            {
                "guardrail_id": report.get("guardrail_id"),
                "action": report.get("action"),
                "validation_non_scalar_recall": report.get("validation_non_scalar_recall"),
                "validation_precision_proxy": report.get("validation_precision_proxy"),
                "validation_non_scalar_caught": report.get("validation_non_scalar_caught"),
                "validation_scalar_collateral": report.get("validation_scalar_collateral"),
                "all_scalar_collateral": report.get("all_scalar_collateral"),
                "full_vocab_count": report.get("full_vocab_count"),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            float(row.get("validation_non_scalar_recall") or 0.0),
            float(row.get("validation_precision_proxy") or 0.0),
            -int(row.get("validation_scalar_collateral") or 0),
        ),
        reverse=True,
    )


def uncovered_validation_non_scalar(
    rows: Sequence[Mapping[str, object]],
    union_mask: object,
    *,
    detail_limit: int,
) -> list[dict[str, object]]:
    selected = np.asarray(union_mask, dtype=bool)
    output = []
    for row in rows:
        if row.get("dataset_id") != "stitch_validation" or row.get("target") != "non_scalar":
            continue
        index = int(row.get("component_index", -1))
        if index < 0 or selected[index]:
            continue
        output.append(
            {
                "label": row.get("label"),
                "treatment": row.get("treatment"),
                "expected_problem_class": row.get("expected_problem_class"),
                "rationale": row.get("rationale"),
            }
        )
    return output[:detail_limit]


def interpretation(
    reports: Sequence[Mapping[str, object]],
    union_reports: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    by_id = {str(row.get("guardrail_id")): row for row in reports}
    union_by_id = {str(row.get("guardrail_id")): row for row in union_reports}
    review_union = _mapping(union_by_id.get("review_union"))
    source_fix = _mapping(union_by_id.get("source_fix_review_union"))
    topic = _mapping(union_by_id.get("topic_review_union"))
    return {
        "review_union_validation_recall": review_union.get("validation_non_scalar_recall"),
        "review_union_validation_scalar_collateral": review_union.get(
            "validation_scalar_collateral"
        ),
        "source_fix_union_validation_recall": source_fix.get("validation_non_scalar_recall"),
        "topic_union_validation_recall": topic.get("validation_non_scalar_recall"),
        "strongest_single_guardrail": (
            guardrail_leaderboard(reports)[0].get("guardrail_id") if reports else None
        ),
        "source_reading_mismatch_note": (
            "Existing signals can flag source-fix rows for review, but they do not prove "
            "the exact reading mismatch; direct JMDict/JMnedict entry-pair validation is "
            "the necessary implementation step before runtime filtering."
        ),
        "recommended_next_step": (
            "Implement a deterministic source-pair validator sidecar for lemma/reading "
            "pairs, then use these guardrail masks as review/deprioritization candidates."
        ),
        "notable_single_guardrails": {
            key: {
                "recall": _mapping(value).get("validation_non_scalar_recall"),
                "precision_proxy": _mapping(value).get("validation_precision_proxy"),
                "scalar_collateral": _mapping(value).get("validation_scalar_collateral"),
            }
            for key, value in by_id.items()
            if key
            in (
                "reading_form_source_review",
                "rare_loanword_topic_review",
                "rare_wago_nonstandard_review",
                "function_or_affix_review",
                "dictionary_non_ladder_review",
            )
        },
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    lines = [
        "# en-ja Source Quality Guardrail Audit",
        "",
        "Status: generated sidecar diagnostic",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "## Scope",
        "",
        f"- Total labeled rows scanned: `{_escape(_mapping(summary.get('label_scope')).get('total_rows'))}`",
        f"- Validation non-scalar rows: `{len(summary.get('validation_non_scalar_rows') or [])}`",
        "",
        "## Guardrail Leaderboard",
        "",
        "| Guardrail | Action | Recall | Precision proxy | Validation scalar collateral | All scalar collateral | Full vocab count |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary.get("guardrail_leaderboard") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"| `{_escape(row.get('guardrail_id'))}` | `{_escape(row.get('action'))}` | "
            f"{_escape(row.get('validation_non_scalar_recall'))} | "
            f"{_escape(row.get('validation_precision_proxy'))} | "
            f"{_escape(row.get('validation_scalar_collateral'))} | "
            f"{_escape(row.get('all_scalar_collateral'))} | "
            f"{_escape(row.get('full_vocab_count'))} |"
        )
    lines.extend(["", "## Union Masks", ""])
    lines.extend(union_table(summary.get("union_reports")))
    lines.extend(["", "## Uncovered Validation Non-Scalar Rows", ""])
    uncovered = summary.get("uncovered_validation_non_scalar") or []
    if uncovered:
        lines.extend(non_scalar_table(uncovered))
    else:
        lines.append("All validation non-scalar rows are caught by at least one review mask.")
    lines.extend(["", "## Validation Non-Scalar Rows", ""])
    lines.extend(non_scalar_table(summary.get("validation_non_scalar_rows")))
    lines.extend(["", "## Interpretation", ""])
    interpretation_row = _mapping(summary.get("interpretation"))
    lines.append(
        f"- Review union recall: `{_escape(interpretation_row.get('review_union_validation_recall'))}`"
    )
    lines.append(
        "- Review union validation scalar collateral: "
        f"`{_escape(interpretation_row.get('review_union_validation_scalar_collateral'))}`"
    )
    lines.append(
        f"- Strongest single guardrail: `{_escape(interpretation_row.get('strongest_single_guardrail'))}`"
    )
    lines.append(
        f"- Source mismatch note: {_escape(interpretation_row.get('source_reading_mismatch_note'))}"
    )
    lines.append(f"- Next step: {_escape(interpretation_row.get('recommended_next_step'))}")
    lines.extend(["", "## Union Details", ""])
    lines.extend(guardrail_detail_sections(summary.get("union_reports")))
    lines.extend(["", "## Single Guardrail Details", ""])
    lines.extend(guardrail_detail_sections(report.get("guardrails")))
    return "\n".join(lines).rstrip() + "\n"


def union_table(rows: object) -> list[str]:
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    lines = [
        "| Mask | Recall | Precision proxy | Validation scalar collateral | All scalar collateral | Full vocab count |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in values:
        lines.append(
            f"| `{_escape(row.get('guardrail_id'))}` | "
            f"{_escape(row.get('validation_non_scalar_recall'))} | "
            f"{_escape(row.get('validation_precision_proxy'))} | "
            f"{_escape(row.get('validation_scalar_collateral'))} | "
            f"{_escape(row.get('all_scalar_collateral'))} | "
            f"{_escape(row.get('full_vocab_count'))} |"
        )
    return lines


def non_scalar_table(rows: object) -> list[str]:
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    lines = [
        "| Label | Treatment | Problem class | Reference | Rationale |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in values:
        lines.append(
            f"| {_escape(row.get('label'))} | `{_escape(row.get('treatment'))}` | "
            f"`{_escape(row.get('expected_problem_class'))}` | "
            f"{_escape(row.get('reference_difficulty'))} | {_escape(row.get('rationale'))} |"
        )
    return lines


def guardrail_detail_sections(rows: object) -> list[str]:
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    lines: list[str] = []
    for row in values:
        lines.append(f"### `{_escape(row.get('guardrail_id'))}`")
        lines.append("")
        lines.append(
            f"- Action: `{_escape(row.get('action'))}`; "
            f"validation recall: `{_escape(row.get('validation_non_scalar_recall'))}`; "
            f"validation scalar collateral: `{_escape(row.get('validation_scalar_collateral'))}`"
        )
        lines.append(f"- Description: {_escape(row.get('description'))}")
        caught_rows = row.get("caught_validation_non_scalar") or []
        lines.append("")
        lines.append("Caught validation non-scalar rows:")
        if caught_rows:
            lines.extend(enriched_row_table(caught_rows))
        else:
            lines.append("")
            lines.append("None.")
        collateral_rows = row.get("validation_scalar_collateral_examples") or []
        lines.append("")
        lines.append("Validation scalar collateral examples:")
        if collateral_rows:
            lines.extend(enriched_row_table(collateral_rows))
        else:
            lines.append("")
            lines.append("None.")
        lines.append("")
    return lines


def enriched_row_table(rows: object) -> list[str]:
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    lines = [
        "",
        "| Label | Expected | Problem class | Signals | Rationale |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in values:
        signals = _mapping(row.get("key_signals"))
        signal_bits = ", ".join(
            f"`{_escape(key)}={_escape(value)}`"
            for key, value in sorted(signals.items())
            if value is not None
        )
        lines.append(
            f"| {_escape(row.get('label'))} | {_escape(row.get('expected_learner_difficulty'))} | "
            f"`{_escape(row.get('expected_problem_class'))}` | {signal_bits} | "
            f"{_escape(row.get('rationale'))} |"
        )
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
