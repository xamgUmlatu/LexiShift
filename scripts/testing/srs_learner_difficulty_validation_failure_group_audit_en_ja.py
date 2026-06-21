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
    _difficulty_band,
    _difficulty_metrics,
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _summary_metrics,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_COMPONENT_MATRIX,
    family_parts,
)
from srs_learner_difficulty_stitch_validation_eval_en_ja import (  # noqa: E402
    DEFAULT_CAP_REPORT,
    DEFAULT_STITCHED_REPORT,
    DEFAULT_V1_REPORT,
    score_arrays_for_models,
)


PAIR = "en-ja"
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_ja.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_ja.json"
)
DEFAULT_VALIDATION_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_learner_difficulty_stitch_validation_labels_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_validation_failure_group_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_validation_failure_group_audit_en_ja_latest.md"
)
VOCAB_STATES = frozenset({"normal_vocab", "deprioritized_vocab"})
SCALAR_VALIDATION_TREATMENTS = frozenset({"", "vocab"})
MODEL_IDS = ("v1", "ordinary_cap", "stitch")


@dataclass(frozen=True)
class GroupTerm:
    signal: str
    min_value: float | None = None
    max_value: float | None = None


@dataclass(frozen=True)
class GroupSpec:
    group_id: str
    description: str
    terms: tuple[GroupTerm, ...]
    source: str = "field_knowledge"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit en-ja learner-difficulty failures across calibration, holdout, "
            "and fresh validation labels by source-computable groups."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--v1-candidate-id", default=None)
    parser.add_argument("--cap-candidate-id", default=None)
    parser.add_argument("--stitch-candidate-id", default=None)
    parser.add_argument("--min-group-count", type=int, default=3)
    parser.add_argument("--max-correction-abs", type=float, default=0.16)
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
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        stitched_report_path=_resolve_path(args.stitched_report),
        v1_candidate_id=args.v1_candidate_id,
        cap_candidate_id=args.cap_candidate_id,
        stitch_candidate_id=args.stitch_candidate_id,
        min_group_count=max(1, int(args.min_group_count)),
        max_correction_abs=max(0.01, float(args.max_correction_abs)),
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
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    v1_candidate_id: str | None,
    cap_candidate_id: str | None,
    stitch_candidate_id: str | None,
    min_group_count: int,
    max_correction_abs: float,
    detail_limit: int,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    calibration = np.load(calibration_matrix_path)
    view = ComponentView.from_npz(component)
    parts = family_parts(view)
    score_arrays, resolved_ids = score_arrays_for_models(
        view=view,
        parts=parts,
        v1_report_path=v1_report_path,
        cap_report_path=cap_report_path,
        stitched_report_path=stitched_report_path,
        v1_candidate_id=v1_candidate_id,
        cap_candidate_id=cap_candidate_id,
        stitch_candidate_id=stitch_candidate_id,
    )
    signal_arrays = signal_arrays_from_component(component)
    group_specs = group_specs_for_audit()
    group_masks = {spec.group_id: group_mask(spec, signal_arrays) for spec in group_specs}
    contexts = {
        "calibration": calibration_label_context(
            calibration,
            component,
            labels_payload=load_json(calibration_json_path),
        ),
        "holdout": json_label_context(
            load_json(holdout_json_path),
            component,
            dataset_id="holdout",
            scalar_treatments=SCALAR_VALIDATION_TREATMENTS,
        ),
        "stitch_validation": json_label_context(
            load_json(validation_json_path),
            component,
            dataset_id="stitch_validation",
            scalar_treatments={"vocab"},
        ),
    }
    overall = {
        dataset_id: dataset_model_metrics(context, score_arrays)
        for dataset_id, context in contexts.items()
    }
    group_reports = [
        group_report(
            spec,
            group_mask=group_masks[spec.group_id],
            contexts=contexts,
            score_arrays=score_arrays,
            min_group_count=min_group_count,
            detail_limit=detail_limit,
        )
        for spec in group_specs
    ]
    group_reports = [
        row
        for row in group_reports
        if any(
            _mapping(dataset).get("count", 0) for dataset in _mapping(row.get("datasets")).values()
        )
    ]
    correction_reports = [
        bounded_correction_report(
            row,
            group_mask=group_masks[str(row["group_id"])],
            contexts=contexts,
            cap_scores=score_arrays["ordinary_cap"],
            max_correction_abs=max_correction_abs,
            min_group_count=min_group_count,
        )
        for row in group_reports
    ]
    correction_reports = [
        row for row in correction_reports if row.get("calibration_support", 0) >= min_group_count
    ]
    source_quality = source_quality_summary(
        validation_payload=load_json(validation_json_path),
        detail_limit=detail_limit,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "holdout_used_for_selection": False,
        "method": {
            "purpose": (
                "Compare v1, ordinary-cap, and stitch failures across calibration, "
                "holdout, and the fresh stitch-validation labels using source-computable "
                "groups."
            ),
            "scalar_scope": (
                "Only finite expected_learner_difficulty rows in vocabulary-like lanes "
                "are scored. Topic-only, grammar, source-fix, and omit rows are reported "
                "separately as candidate-quality evidence."
            ),
            "bounded_correction_probe": (
                "For each group, fit one clipped ordinary-cap residual offset from "
                "calibration only, then report validation and holdout effects."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "calibration_json": _repo_or_home_path(calibration_json_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "validation_json": _repo_or_home_path(validation_json_path),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            "min_group_count": min_group_count,
            "max_correction_abs": _rounded(max_correction_abs),
            **resolved_ids,
        },
        "summary": {
            "dataset_scope": {
                dataset_id: dataset_scope_summary(context)
                for dataset_id, context in contexts.items()
            },
            "overall": overall,
            "distribution_mismatch": distribution_mismatch(group_reports),
            "largest_failure_groups": largest_failure_groups(
                group_reports, model_id="ordinary_cap"
            ),
            "correction_candidates": correction_candidate_summary(correction_reports),
            "source_quality": source_quality,
            "interpretation": interpretation(overall, correction_reports, source_quality),
        },
        "groups": group_reports,
        "bounded_correction_probes": correction_reports,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "calibration_json": calibration_json_path,
                "holdout_json": holdout_json_path,
                "validation_json": validation_json_path,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
                "stitched_report": stitched_report_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "stitch_validation_eval": SCRIPT_DIR
                / "srs_learner_difficulty_stitch_validation_eval_en_ja.py",
                "source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_source_arbitration_en_ja.py",
                "stitched_source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_stitched_source_arbitration_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "signal_sweep": SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def calibration_label_context(
    calibration: object,
    component: object,
    *,
    labels_payload: Mapping[str, object],
) -> dict[str, object]:
    raw_context = _calibration_context(calibration, component)
    expected = np.asarray(raw_context["expected_values"], dtype=np.float32)
    component_indices = np.asarray(raw_context["component_indices"], dtype=np.int64)
    expected_states = np.asarray(raw_context["expected_candidate_states"], dtype=str)
    scalar_candidate = np.isfinite(expected) & np.isin(expected_states, list(VOCAB_STATES))
    scalar = scalar_candidate & (component_indices >= 0)
    non_scalar_rows = []
    unmatched_rows = []
    labels_by_lemma = {
        str(row.get("lemma") or ""): row
        for row in labels_payload.get("labels", ())
        if isinstance(row, Mapping)
    }
    for index, label in enumerate(raw_context["labels"]):
        if scalar[index]:
            continue
        if scalar_candidate[index] and component_indices[index] < 0:
            unmatched_rows.append(
                {
                    "label": label,
                    "expected_candidate_state": str(expected_states[index]),
                    "expected_problem_class": str(raw_context["expected_problem_classes"][index]),
                    "expected_learner_difficulty": _rounded(float(expected[index])),
                    "reason": "missing_component_row",
                }
            )
            continue
        lemma = str(calibration["calibration_lemmas"][index])
        label_row = _mapping(labels_by_lemma.get(lemma))
        non_scalar_rows.append(
            {
                "label": label,
                "expected_candidate_state": str(expected_states[index]),
                "expected_problem_class": str(raw_context["expected_problem_classes"][index]),
                "expected_presentation_mode": str(
                    raw_context["expected_presentation_modes"][index]
                ),
                "has_numeric_target": bool(np.isfinite(expected[index])),
                "rationale": str(label_row.get("rationale") or "")[:180],
            }
        )
    return {
        "dataset_id": "calibration",
        "labels": select_list(raw_context["labels"], scalar),
        "expected_values": expected[scalar],
        "expected_bands": [_difficulty_band(float(value)) for value in expected[scalar]],
        "component_indices": component_indices[scalar],
        "expected_candidate_states": select_list(raw_context["expected_candidate_states"], scalar),
        "expected_problem_classes": select_list(raw_context["expected_problem_classes"], scalar),
        "expected_presentation_modes": select_list(
            raw_context["expected_presentation_modes"], scalar
        ),
        "non_scalar_rows": non_scalar_rows,
        "unmatched_rows": unmatched_rows,
    }


def json_label_context(
    payload: Mapping[str, object],
    component: object,
    *,
    dataset_id: str,
    scalar_treatments: set[str],
) -> dict[str, object]:
    lookup = component_lookup(component)
    labels: list[str] = []
    expected_values: list[float] = []
    component_indices: list[int] = []
    expected_states: list[str] = []
    expected_problem_classes: list[str] = []
    expected_presentation_modes: list[str] = []
    non_scalar_rows: list[dict[str, object]] = []
    unmatched_rows: list[dict[str, object]] = []
    for index, row in enumerate(payload.get("labels", ())):
        if not isinstance(row, Mapping):
            continue
        lemma = str(row.get("lemma") or "").strip()
        reading = str(row.get("expected_reading") or row.get("reading") or "").strip()
        label = f"{lemma}/{reading}" if reading else lemma
        value = _optional_float(row.get("expected_learner_difficulty"))
        treatment = str(row.get("treatment") or "")
        state = str(row.get("expected_candidate_state") or "")
        scalar = (
            value is not None
            and treatment in scalar_treatments
            and (not state or state in VOCAB_STATES)
        )
        if not scalar:
            non_scalar_rows.append(non_scalar_row(label, row, index=index))
            continue
        component_index = lookup.get((lemma, reading))
        if component_index is None:
            unmatched_rows.append({"label": label, "row_index": index})
            continue
        labels.append(label)
        expected_values.append(float(value))
        component_indices.append(int(component_index))
        expected_states.append(state or "normal_vocab")
        expected_problem_classes.append(str(row.get("expected_problem_class") or ""))
        expected_presentation_modes.append(str(row.get("expected_presentation_mode") or ""))
    expected = np.asarray(expected_values, dtype=np.float32)
    return {
        "dataset_id": dataset_id,
        "labels": labels,
        "expected_values": expected,
        "expected_bands": [_difficulty_band(float(value)) for value in expected],
        "component_indices": np.asarray(component_indices, dtype=np.int64),
        "expected_candidate_states": expected_states,
        "expected_problem_classes": expected_problem_classes,
        "expected_presentation_modes": expected_presentation_modes,
        "non_scalar_rows": non_scalar_rows,
        "unmatched_rows": unmatched_rows,
    }


def non_scalar_row(label: str, row: Mapping[str, object], *, index: int) -> dict[str, object]:
    return {
        "label": label,
        "row_index": row.get("review_row_number", index),
        "treatment": str(row.get("treatment") or ""),
        "expected_candidate_state": str(row.get("expected_candidate_state") or ""),
        "expected_problem_class": str(row.get("expected_problem_class") or ""),
        "expected_presentation_mode": str(row.get("expected_presentation_mode") or ""),
        "reference_difficulty": _rounded(row.get("reference_difficulty")),
        "has_numeric_target": row.get("expected_learner_difficulty") is not None,
        "rationale": str(row.get("rationale") or "")[:180],
    }


def component_lookup(component: object) -> dict[tuple[str, str], int]:
    lookup: dict[tuple[str, str], int] = {}
    for index, (lemma, reading) in enumerate(zip(component["lemmas"], component["readings"])):
        lookup.setdefault((str(lemma), str(reading)), int(index))
    return lookup


def select_list(values: object, mask: object) -> list[str]:
    parsed_values = list(values)
    parsed_mask = np.asarray(mask, dtype=bool)
    return [str(value) for value, selected in zip(parsed_values, parsed_mask) if selected]


def dataset_scope_summary(context: Mapping[str, object]) -> dict[str, object]:
    states = count_values(context.get("expected_candidate_states") or ())
    classes = count_values(context.get("expected_problem_classes") or ())
    return {
        "scalar_count": len(context.get("labels") or ()),
        "non_scalar_count": len(context.get("non_scalar_rows") or ()),
        "unmatched_count": len(context.get("unmatched_rows") or ()),
        "expected_state_counts": states,
        "expected_problem_class_counts": classes,
    }


def count_values(values: object) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def dataset_model_metrics(
    context: Mapping[str, object],
    score_arrays: Mapping[str, object],
) -> dict[str, object]:
    rows = []
    for model_id in MODEL_IDS:
        observed = observed_for_context(score_arrays[model_id], context)
        metrics = metrics_for_values(context, observed)
        rows.append(
            {
                "model_id": model_id,
                "scores": metrics["scores"],
                "metrics": _summary_metrics(metrics),
            }
        )
    return {
        "leaderboard": sorted(
            rows,
            key=lambda row: float(_mapping(row.get("scores")).get("balanced_score") or -1),
            reverse=True,
        )
    }


def metrics_for_values(context: Mapping[str, object], observed: object) -> dict[str, object]:
    return _difficulty_metrics(
        expected_values=context["expected_values"],
        observed_values=observed,
        expected_bands=context["expected_bands"],
        labels=context["labels"],
    )


def observed_for_context(scores: object, context: Mapping[str, object]) -> object:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    return np.asarray(scores, dtype=np.float32)[indices]


def group_specs_for_audit() -> list[GroupSpec]:
    return [
        GroupSpec("all_scalar", "All scalar vocabulary labels.", ()),
        GroupSpec(
            "curriculum_core",
            "Rows with beginner curriculum/JLPT core evidence.",
            (GroupTerm("curriculum_core_any", min_value=0.75),),
        ),
        GroupSpec(
            "pedagogical_known",
            "Rows known to JLPT or lesson vocabulary sources.",
            (GroupTerm("pedagogical_known_any", min_value=0.75),),
        ),
        GroupSpec(
            "native_common_priority",
            "Rows with strong ordinary frequency or JMDict priority evidence.",
            (GroupTerm("native_common_any", min_value=0.75),),
        ),
        GroupSpec(
            "common_loanword",
            "Loanword rows with ordinary/commonness support.",
            (
                GroupTerm("loanword_any", min_value=0.75),
                GroupTerm("frequency", max_value=0.55),
            ),
        ),
        GroupSpec(
            "domain_or_rare_loanword",
            "Loanword rows in a rarer or more domain-specific band.",
            (
                GroupTerm("loanword_any", min_value=0.75),
                GroupTerm("frequency", min_value=0.55),
            ),
        ),
        GroupSpec(
            "kango_general",
            "Kango rows, regardless of frequency.",
            (GroupTerm("wtype_kango_risk", min_value=0.75),),
        ),
        GroupSpec(
            "kango_priority",
            "Kango rows with common/priority support.",
            (
                GroupTerm("wtype_kango_risk", min_value=0.75),
                GroupTerm("jmdict_priority", min_value=0.25),
            ),
        ),
        GroupSpec(
            "transparent_wago_common",
            "Native/wago rows with limited rarity pressure.",
            (
                GroupTerm("wtype_wago_ease", min_value=0.75),
                GroupTerm("wago_written_or_rare", max_value=0.35),
            ),
        ),
        GroupSpec(
            "transparent_wago_rare",
            "Native/wago rows with meaningful rarity or written-form pressure.",
            (
                GroupTerm("wtype_wago_ease", min_value=0.75),
                GroupTerm("wago_written_or_rare", min_value=0.35),
            ),
        ),
        GroupSpec(
            "rare_wago_obscure_tail",
            "Native/wago rows in the clear rare/obscure written tail.",
            (
                GroupTerm("wtype_wago_ease", min_value=0.75),
                GroupTerm("wago_written_or_rare", min_value=0.65),
            ),
        ),
        GroupSpec(
            "nonstandard_or_rare_reading",
            "Rows with non-standard or rare reading pressure.",
            (GroupTerm("non_standard_any", min_value=0.50),),
        ),
        GroupSpec(
            "high_written_burden",
            "Rows with high written-form or kanji burden.",
            (GroupTerm("written_or_kanji_burden_any", min_value=0.70),),
        ),
        GroupSpec(
            "entity_or_acronym",
            "Rows with proper-name, entity, acronym, or abbreviation pressure.",
            (GroupTerm("entity_or_acronym_any", min_value=0.75),),
        ),
        GroupSpec(
            "marked_dictionary_usage",
            "Rows with JMDict field/register/marked usage pressure.",
            (GroupTerm("marked_dictionary_any", min_value=0.75),),
        ),
        GroupSpec(
            "extreme_frequency_tail",
            "Rows in the extreme frequency rarity tail.",
            (GroupTerm("frequency", min_value=0.90),),
        ),
        GroupSpec(
            "unranked_frequency_tail",
            "Rows with explicit unranked-frequency tail pressure.",
            (GroupTerm("frequency_unranked_tail_risk", min_value=0.75),),
        ),
    ]


def signal_arrays_from_component(component: object) -> dict[str, object]:
    values = np.asarray(component["component_values"], dtype=np.float32)
    present = np.asarray(component["component_present"], dtype=bool)
    arrays: dict[str, object] = {}
    for index, name in enumerate(component["component_names"]):
        arrays[str(name)] = np.where(present[:, index], values[:, index], 0.0)
    count = values.shape[0]
    arrays["wago_written_or_rare"] = max_signal(
        arrays,
        (
            "rare_wago_tail_risk",
            "written_wago_tail_risk",
            "rare_wago_obscure_written_risk",
            "rare_wago_written_risk",
        ),
        count=count,
    )
    arrays["non_standard_any"] = max_signal(
        arrays,
        (
            "non_standard_reading_risk",
            "rare_non_standard_reading_risk",
            "rare_wago_non_standard_reading_risk",
        ),
        count=count,
    )
    arrays["entity_or_acronym_any"] = max_signal(
        arrays,
        (
            "named_entity_risk",
            "candidate_deprioritized_named_entity_risk",
            "candidate_deprioritized_named_frequency_risk",
            "problem_class_proper_risk",
            "proper_acronym_entity_risk",
            "news_abbreviation_entity_risk",
            "acronym_topic_only_risk",
            "jmdict_abbreviation_risk",
        ),
        count=count,
    )
    arrays["curriculum_core_any"] = max_signal(
        arrays,
        ("jlpt_vocab_beginner_core", "lesson_vocab_beginner_core"),
        count=count,
    )
    arrays["pedagogical_known_any"] = max_signal(
        arrays,
        ("jlpt_vocab_known", "lesson_vocab_known", "curriculum_core_any"),
        count=count,
    )
    arrays["native_common_any"] = max_signal(
        arrays,
        ("frequency_ease", "jmdict_priority", "jmdict_news_priority_commonness"),
        count=count,
    )
    arrays["loanword_any"] = max_signal(
        arrays,
        (
            "wtype_gairaigo_risk",
            "jmdict_loanword_source_risk",
            "jmdict_foreign_priority_risk",
        ),
        count=count,
    )
    arrays["written_or_kanji_burden_any"] = max_signal(
        arrays,
        ("max_written_form_burden", "written_form_burden", "kanji_burden", "max_kanji_burden"),
        count=count,
    )
    arrays["marked_dictionary_any"] = max_signal(
        arrays,
        (
            "jmdict_marked_usage_risk",
            "jmdict_register_marked_risk",
            "jmdict_field_marked_risk",
            "jmdict_search_only_form_risk",
            "jmdict_kana_preferred_risk",
        ),
        count=count,
    )
    return arrays


def max_signal(
    arrays: Mapping[str, object],
    names: Sequence[str],
    *,
    count: int,
) -> object:
    values = [
        np.asarray(arrays.get(name, np.zeros(count, dtype=np.float32)), dtype=np.float32)
        for name in names
    ]
    return np.maximum.reduce(values) if values else np.zeros(count, dtype=np.float32)


def group_mask(spec: GroupSpec, signal_arrays: Mapping[str, object]) -> object:
    count = len(next(iter(signal_arrays.values()))) if signal_arrays else 0
    selected = np.ones(count, dtype=bool)
    for term in spec.terms:
        signal = np.asarray(
            signal_arrays.get(term.signal, np.zeros(count, dtype=np.float32)),
            dtype=np.float32,
        )
        if term.min_value is not None:
            selected &= signal >= float(term.min_value)
        if term.max_value is not None:
            selected &= signal <= float(term.max_value)
    return selected


def context_group_mask(context: Mapping[str, object], full_mask: object) -> object:
    indices = np.asarray(context["component_indices"], dtype=np.int64)
    parsed = np.asarray(full_mask, dtype=bool)
    valid = (indices >= 0) & (indices < len(parsed))
    selected = np.zeros(len(indices), dtype=bool)
    selected[valid] = parsed[indices[valid]]
    return selected


def group_report(
    spec: GroupSpec,
    *,
    group_mask: object,
    contexts: Mapping[str, Mapping[str, object]],
    score_arrays: Mapping[str, object],
    min_group_count: int,
    detail_limit: int,
) -> dict[str, object]:
    datasets = {}
    for dataset_id, context in contexts.items():
        selected = context_group_mask(context, group_mask)
        datasets[dataset_id] = group_dataset_report(
            context,
            selected=selected,
            score_arrays=score_arrays,
            min_group_count=min_group_count,
            detail_limit=detail_limit,
        )
    return {
        "group_id": spec.group_id,
        "description": spec.description,
        "source": spec.source,
        "full_vocab_count": int(np.asarray(group_mask, dtype=bool).sum()),
        "datasets": datasets,
    }


def group_dataset_report(
    context: Mapping[str, object],
    *,
    selected: object,
    score_arrays: Mapping[str, object],
    min_group_count: int,
    detail_limit: int,
) -> dict[str, object]:
    mask = np.asarray(selected, dtype=bool)
    count = int(mask.sum())
    total = len(context.get("labels") or ())
    if count == 0:
        return {"count": 0, "share": 0.0}
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    labels = [str(value) for value in context["labels"]]
    model_reports = {}
    for model_id in MODEL_IDS:
        observed = observed_for_context(score_arrays[model_id], context)
        errors = np.abs(observed[mask] - expected[mask])
        signed = observed[mask] - expected[mask]
        model_reports[model_id] = {
            "mae": _rounded(float(np.mean(errors))) if len(errors) else None,
            "signed_error_mean": _rounded(float(np.mean(signed))) if len(signed) else None,
            "observed_mean": _rounded(float(np.mean(observed[mask]))) if len(signed) else None,
        }
    winner = min(
        MODEL_IDS,
        key=lambda model_id: float(_mapping(model_reports[model_id]).get("mae") or 999.0),
    )
    details = []
    cap_observed = observed_for_context(score_arrays["ordinary_cap"], context)
    for index in np.flatnonzero(mask):
        details.append(
            {
                "label": labels[index],
                "expected": _rounded(float(expected[index])),
                "ordinary_cap": _rounded(float(cap_observed[index])),
                "absolute_error": _rounded(abs(float(cap_observed[index] - expected[index]))),
                "direction": "too_high" if cap_observed[index] > expected[index] else "too_low",
            }
        )
    details = sorted(
        details,
        key=lambda row: float(row.get("absolute_error") or 0.0),
        reverse=True,
    )[:detail_limit]
    return {
        "count": count,
        "share": _rounded(count / total if total else 0.0),
        "expected_mean": _rounded(float(np.mean(expected[mask]))),
        "winner_by_mae": winner if count >= min_group_count else "insufficient_support",
        "models": model_reports,
        "ordinary_cap_largest_errors": details,
    }


def bounded_correction_report(
    group: Mapping[str, object],
    *,
    group_mask: object,
    contexts: Mapping[str, Mapping[str, object]],
    cap_scores: object,
    max_correction_abs: float,
    min_group_count: int,
) -> dict[str, object]:
    calibration = contexts["calibration"]
    calibration_selected = context_group_mask(calibration, group_mask)
    calibration_observed = observed_for_context(cap_scores, calibration)
    calibration_expected = np.asarray(calibration["expected_values"], dtype=np.float32)
    support = int(calibration_selected.sum())
    if support < min_group_count:
        delta = 0.0
    else:
        residuals = (
            calibration_expected[calibration_selected] - calibration_observed[calibration_selected]
        )
        delta = float(np.clip(np.mean(residuals), -max_correction_abs, max_correction_abs))
    datasets = {}
    for dataset_id, context in contexts.items():
        selected = context_group_mask(context, group_mask)
        observed = observed_for_context(cap_scores, context)
        adjusted = np.array(observed, dtype=np.float32, copy=True)
        adjusted[selected] = np.clip(adjusted[selected] + delta, 0.0, 1.0)
        base_metrics = metrics_for_values(context, observed)
        adjusted_metrics = metrics_for_values(context, adjusted)
        datasets[dataset_id] = {
            "support": int(selected.sum()),
            "global": metric_delta_summary(base_metrics, adjusted_metrics),
            "group": group_mae_delta(context, observed, adjusted, selected),
        }
    return {
        "group_id": group.get("group_id"),
        "description": group.get("description"),
        "calibration_support": support,
        "delta": _rounded(delta),
        "datasets": datasets,
    }


def metric_delta_summary(
    base_metrics: Mapping[str, object],
    adjusted_metrics: Mapping[str, object],
) -> dict[str, object]:
    base_scores = _mapping(base_metrics.get("scores"))
    adjusted_scores = _mapping(adjusted_metrics.get("scores"))
    base_summary = _summary_metrics(base_metrics)
    adjusted_summary = _summary_metrics(adjusted_metrics)
    return {
        "balanced_delta": _rounded(
            optional_subtract(
                adjusted_scores.get("balanced_score"), base_scores.get("balanced_score")
            )
        ),
        "mae_reduction": _rounded(
            optional_subtract(base_summary.get("mae"), adjusted_summary.get("mae"))
        ),
        "pairwise_delta": _rounded(
            optional_subtract(
                adjusted_scores.get("pairwise_order_score"),
                base_scores.get("pairwise_order_score"),
            )
        ),
        "bucket_delta": _rounded(
            optional_subtract(
                adjusted_scores.get("bucket_accuracy_score"),
                base_scores.get("bucket_accuracy_score"),
            )
        ),
    }


def group_mae_delta(
    context: Mapping[str, object],
    base_observed: object,
    adjusted_observed: object,
    selected: object,
) -> dict[str, object]:
    mask = np.asarray(selected, dtype=bool)
    if not mask.any():
        return {"mae_reduction": None}
    expected = np.asarray(context["expected_values"], dtype=np.float32)
    base = np.asarray(base_observed, dtype=np.float32)
    adjusted = np.asarray(adjusted_observed, dtype=np.float32)
    base_mae = float(np.mean(np.abs(base[mask] - expected[mask])))
    adjusted_mae = float(np.mean(np.abs(adjusted[mask] - expected[mask])))
    return {
        "mae_reduction": _rounded(base_mae - adjusted_mae),
        "base_mae": _rounded(base_mae),
        "adjusted_mae": _rounded(adjusted_mae),
    }


def optional_subtract(left: object, right: object) -> float | None:
    left_value = _optional_float(left)
    right_value = _optional_float(right)
    if left_value is None or right_value is None:
        return None
    return float(left_value) - float(right_value)


def distribution_mismatch(groups: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows = []
    for group in groups:
        datasets = _mapping(group.get("datasets"))
        shares = {
            dataset_id: _optional_float(_mapping(value).get("share")) or 0.0
            for dataset_id, value in datasets.items()
        }
        if not shares:
            continue
        rows.append(
            {
                "group_id": group.get("group_id"),
                "description": group.get("description"),
                "full_vocab_count": group.get("full_vocab_count"),
                "shares": shares,
                "max_share_gap": _rounded(max(shares.values()) - min(shares.values())),
            }
        )
    return sorted(
        rows,
        key=lambda row: float(row.get("max_share_gap") or 0.0),
        reverse=True,
    )[:16]


def largest_failure_groups(
    groups: Sequence[Mapping[str, object]],
    *,
    model_id: str,
) -> list[dict[str, object]]:
    rows = []
    for group in groups:
        datasets = _mapping(group.get("datasets"))
        for dataset_id, dataset in datasets.items():
            parsed = _mapping(dataset)
            count = int(parsed.get("count") or 0)
            if count <= 0:
                continue
            model = _mapping(_mapping(parsed.get("models")).get(model_id))
            rows.append(
                {
                    "group_id": group.get("group_id"),
                    "dataset_id": dataset_id,
                    "count": count,
                    "mae": model.get("mae"),
                    "signed_error_mean": model.get("signed_error_mean"),
                    "winner_by_mae": parsed.get("winner_by_mae"),
                    "description": group.get("description"),
                }
            )
    return sorted(
        rows,
        key=lambda row: (float(row.get("mae") or 0.0), int(row.get("count") or 0)),
        reverse=True,
    )[:20]


def correction_candidate_summary(
    corrections: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    rows = []
    for row in corrections:
        datasets = _mapping(row.get("datasets"))
        validation = _mapping(_mapping(datasets.get("stitch_validation")).get("global"))
        holdout = _mapping(_mapping(datasets.get("holdout")).get("global"))
        calibration = _mapping(_mapping(datasets.get("calibration")).get("global"))
        rows.append(
            {
                "group_id": row.get("group_id"),
                "delta": row.get("delta"),
                "calibration_support": row.get("calibration_support"),
                "calibration_balanced_delta": calibration.get("balanced_delta"),
                "validation_balanced_delta": validation.get("balanced_delta"),
                "validation_mae_reduction": validation.get("mae_reduction"),
                "holdout_balanced_delta": holdout.get("balanced_delta"),
                "holdout_mae_reduction": holdout.get("mae_reduction"),
            }
        )
    return sorted(
        rows,
        key=lambda value: (
            float(value.get("validation_balanced_delta") or -999.0),
            float(value.get("holdout_balanced_delta") or -999.0),
            float(value.get("validation_mae_reduction") or -999.0),
        ),
        reverse=True,
    )[:16]


def source_quality_summary(
    *,
    validation_payload: Mapping[str, object],
    detail_limit: int,
) -> dict[str, object]:
    non_scalar = []
    for index, row in enumerate(validation_payload.get("labels", ())):
        if not isinstance(row, Mapping):
            continue
        treatment = str(row.get("treatment") or "")
        if treatment in ("omit", "topic_only", "grammar_item"):
            lemma = str(row.get("lemma") or "")
            reading = str(row.get("expected_reading") or "")
            non_scalar.append(
                non_scalar_row(f"{lemma}/{reading}" if reading else lemma, row, index=index)
            )
    return {
        "count": len(non_scalar),
        "treatment_counts": count_values(row.get("treatment") for row in non_scalar),
        "problem_class_counts": count_values(
            row.get("expected_problem_class") for row in non_scalar
        ),
        "examples": non_scalar[:detail_limit],
    }


def interpretation(
    overall: Mapping[str, object],
    corrections: Sequence[Mapping[str, object]],
    source_quality: Mapping[str, object],
) -> dict[str, object]:
    validation_leader = first_model(_mapping(overall.get("stitch_validation")))
    holdout_leader = first_model(_mapping(overall.get("holdout")))
    positive_validation_and_holdout = []
    for row in corrections:
        datasets = _mapping(row.get("datasets"))
        validation = _mapping(_mapping(datasets.get("stitch_validation")).get("global"))
        holdout = _mapping(_mapping(datasets.get("holdout")).get("global"))
        if (_optional_float(validation.get("balanced_delta")) or 0.0) > 0 and (
            _optional_float(holdout.get("balanced_delta")) or 0.0
        ) > 0:
            positive_validation_and_holdout.append(str(row.get("group_id")))
    return {
        "validation_balanced_leader": validation_leader,
        "holdout_balanced_leader": holdout_leader,
        "corrections_positive_on_validation_and_holdout": positive_validation_and_holdout[:8],
        "source_quality_rows": source_quality.get("count"),
        "recommended_next_decision": (
            "Prefer ordinary_cap as the anchor and inspect bounded corrections only "
            "if they improve both validation and holdout without being candidate-source "
            "quality issues."
        ),
    }


def first_model(dataset_report: Mapping[str, object]) -> str:
    rows = dataset_report.get("leaderboard") or ()
    if isinstance(rows, Sequence) and rows:
        first = rows[0]
        if isinstance(first, Mapping):
            return str(first.get("model_id") or "")
    return ""


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    lines = [
        "# en-ja Validation Failure Group Audit",
        "",
        "Status: generated sidecar diagnostic",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "## Scope",
        "",
        "| Dataset | Scalar rows | Non-scalar rows | Unmatched |",
        "| --- | ---: | ---: | ---: |",
    ]
    for dataset_id, row in _mapping(summary.get("dataset_scope")).items():
        parsed = _mapping(row)
        lines.append(
            f"| `{_escape(dataset_id)}` | {_escape(parsed.get('scalar_count'))} | "
            f"{_escape(parsed.get('non_scalar_count'))} | "
            f"{_escape(parsed.get('unmatched_count'))} |"
        )
    lines.extend(["", "## Overall Models", ""])
    lines.extend(overall_table(_mapping(summary.get("overall"))))
    lines.extend(["", "## Distribution Mismatch", ""])
    lines.extend(distribution_table(summary.get("distribution_mismatch")))
    lines.extend(["", "## Largest ordinary_cap Failure Groups", ""])
    lines.extend(failure_group_table(summary.get("largest_failure_groups")))
    lines.extend(["", "## Bounded Correction Probes", ""])
    lines.extend(correction_table(summary.get("correction_candidates")))
    lines.extend(["", "## Source Quality Rows", ""])
    lines.extend(source_quality_lines(_mapping(summary.get("source_quality"))))
    lines.extend(["", "## Interpretation", ""])
    interpretation_row = _mapping(summary.get("interpretation"))
    lines.append(
        f"- Validation balanced leader: `{_escape(interpretation_row.get('validation_balanced_leader'))}`"
    )
    lines.append(
        f"- Holdout balanced leader: `{_escape(interpretation_row.get('holdout_balanced_leader'))}`"
    )
    positives = interpretation_row.get("corrections_positive_on_validation_and_holdout") or []
    if positives:
        lines.append(
            "- Correction groups positive on validation and holdout: "
            + ", ".join(f"`{_escape(value)}`" for value in positives)
        )
    else:
        lines.append(
            "- No one-group bounded correction improved both validation and holdout balanced score."
        )
    lines.append(f"- Next decision: {_escape(interpretation_row.get('recommended_next_decision'))}")
    return "\n".join(lines).rstrip() + "\n"


def overall_table(overall: Mapping[str, object]) -> list[str]:
    lines = [
        "| Dataset | Rank | Model | Balanced | MAE | Bucket | Pairwise | Spearman |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for dataset_id, report in overall.items():
        for rank, row in enumerate(_mapping(report).get("leaderboard") or (), start=1):
            if not isinstance(row, Mapping):
                continue
            scores = _mapping(row.get("scores"))
            metrics = _mapping(row.get("metrics"))
            lines.append(
                f"| `{_escape(dataset_id)}` | {rank} | `{_escape(row.get('model_id'))}` | "
                f"{_escape(scores.get('balanced_score'))} | "
                f"{_escape(metrics.get('mae'))} | "
                f"{_escape(metrics.get('bucket_accuracy'))} | "
                f"{_escape(metrics.get('pairwise_accuracy'))} | "
                f"{_escape(metrics.get('spearman'))} |"
            )
    return lines


def distribution_table(rows: object) -> list[str]:
    lines = [
        "| Group | Calib share | Holdout share | Validation share | Max gap |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    for row in values[:12]:
        shares = _mapping(row.get("shares"))
        lines.append(
            f"| `{_escape(row.get('group_id'))}` | "
            f"{_escape(shares.get('calibration'))} | "
            f"{_escape(shares.get('holdout'))} | "
            f"{_escape(shares.get('stitch_validation'))} | "
            f"{_escape(row.get('max_share_gap'))} |"
        )
    return lines


def failure_group_table(rows: object) -> list[str]:
    lines = [
        "| Group | Dataset | Count | MAE | Bias | Winner |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    for row in values[:16]:
        lines.append(
            f"| `{_escape(row.get('group_id'))}` | `{_escape(row.get('dataset_id'))}` | "
            f"{_escape(row.get('count'))} | {_escape(row.get('mae'))} | "
            f"{_escape(row.get('signed_error_mean'))} | `{_escape(row.get('winner_by_mae'))}` |"
        )
    return lines


def correction_table(rows: object) -> list[str]:
    lines = [
        "| Group | Delta | Calib support | Val balanced | Val MAE red. | Holdout balanced | Holdout MAE red. |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    for row in values[:12]:
        lines.append(
            f"| `{_escape(row.get('group_id'))}` | {_escape(row.get('delta'))} | "
            f"{_escape(row.get('calibration_support'))} | "
            f"{_escape(row.get('validation_balanced_delta'))} | "
            f"{_escape(row.get('validation_mae_reduction'))} | "
            f"{_escape(row.get('holdout_balanced_delta'))} | "
            f"{_escape(row.get('holdout_mae_reduction'))} |"
        )
    return lines


def source_quality_lines(summary: Mapping[str, object]) -> list[str]:
    lines = [
        f"- Non-scalar validation rows: `{_escape(summary.get('count'))}`",
        f"- Treatment counts: `{_escape(summary.get('treatment_counts'))}`",
        "",
        "| Label | Treatment | Problem class | Reference | Rationale |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in summary.get("examples") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"| {_escape(row.get('label'))} | `{_escape(row.get('treatment'))}` | "
            f"`{_escape(row.get('expected_problem_class'))}` | "
            f"{_escape(row.get('reference_difficulty'))} | {_escape(row.get('rationale'))} |"
        )
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
