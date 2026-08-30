#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import sys
from typing import Callable, Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_cleaned_lane_eval_en_ja import (  # noqa: E402
    DEFAULT_SOURCE_PAIR_JSON,
    component_lookup,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_qualitative_failure_hypotheses_en_ja import (  # noqa: E402
    MatrixView,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
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
ANCHOR_MODEL = "ordinary_cap"
DEFAULT_READING_AUDIT_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_reading_specific_audit_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_reading_form_sample_eval_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_reading_form_sample_eval_en_ja_latest.md"
)

READING_FORM_SIGNALS = (
    "jmdict_reading_form_marked_risk",
    "jmdict_reading_restricted_risk",
    "jmdict_kana_preferred_risk",
    "jmdict_no_kanji_reading_risk",
    "jmdict_kanji_form_marked_risk",
    "jmdict_search_only_form_risk",
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_non_standard_reading_risk",
)
SNAPSHOT_SIGNALS = (
    "frequency",
    "frequency_unranked_risk",
    "jlpt_vocab_difficulty",
    "jlpt_vocab_beginner_core",
    "lesson_vocab_beginner_core",
    "jmdict_priority",
    "jmdict_kana_preferred_risk",
    "jmdict_no_kanji_reading_risk",
    "jmdict_kanji_form_marked_risk",
    "jmdict_reading_form_marked_risk",
    "jmdict_reading_restricted_risk",
    "jmdict_search_only_form_risk",
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_non_standard_reading_risk",
    "wtype_wago_ease",
    "wtype_kango_risk",
    "wtype_gairaigo_risk",
    "max_written_form_burden",
    "named_entity_risk",
)


@dataclass(frozen=True)
class ReviewedProbe:
    lemma: str
    reading: str
    role: str
    desired_direction: str
    review_call: str
    review_target_note: str


@dataclass(frozen=True)
class PolicySpec:
    policy_id: str
    description: str
    floor_for_row: Callable[[Mapping[str, object]], float | None]


REVIEWED_PROBES = (
    ReviewedProbe(
        lemma="辛い",
        reading="つらい",
        role="target_upshift",
        desired_direction="up",
        review_call="mildly too early",
        review_target_note=(
            "Latest qualitative review said roughly 0.10-0.20; existing scalar "
            "source label is 0.32."
        ),
    ),
    ReviewedProbe(
        lemma="真",
        reading="まこと",
        role="target_upshift",
        desired_direction="up",
        review_call="too early",
        review_target_note=(
            "Specific reading looked too easy in the 0.20-0.30 sample band; no "
            "numeric scalar label is present."
        ),
    ),
    ReviewedProbe(
        lemma="誘う",
        reading="いざなう",
        role="target_upshift",
        desired_direction="up",
        review_call="too early",
        review_target_note=(
            "Specific reading looked too easy in the 0.20-0.30 sample band; no "
            "numeric scalar label is present."
        ),
    ),
    ReviewedProbe(
        lemma="否",
        reading="いや",
        role="known_caveat",
        desired_direction="review_only",
        review_call="common reading, uncommon kanji spelling",
        review_target_note=(
            "Do not automatically correct unless the policy separates kana/common "
            "word ease from uncommon written-form burden."
        ),
    ),
    ReviewedProbe(
        lemma="ゲロ",
        reading="げろ",
        role="separate_downshift",
        desired_direction="down",
        review_call="too late",
        review_target_note=(
            "Opposite direction: likely a candidate-state/problem-class issue, not "
            "a reading upshift issue."
        ),
    ),
    ReviewedProbe(
        lemma="系",
        reading="けい",
        role="accepted_control",
        desired_direction="keep",
        review_call="acceptable",
        review_target_note="Accepted as currently placed.",
    ),
    ReviewedProbe(
        lemma="一本",
        reading="いっぽん",
        role="accepted_control",
        desired_direction="keep",
        review_call="probably easier but acceptable to leave",
        review_target_note=(
            "Useful control: do not let a broad nonstandard-reading rule pull this "
            "around unless a separate counter/transparency signal justifies it."
        ),
    ),
    ReviewedProbe(
        lemma="火",
        reading="か",
        role="false_positive_probe",
        desired_direction="review_only",
        review_call="same-surface onyomi probe",
        review_target_note=(
            "Useful probe for same-surface rank-gap rules: the row has an easier "
            "sibling 火/ひ but may not deserve a large penalty."
        ),
    ),
    ReviewedProbe(
        lemma="呉れる",
        reading="くれる",
        role="false_positive_probe",
        desired_direction="review_only",
        review_call="common kana-preferred probe",
        review_target_note=(
            "Useful probe for kana-preferred false positives: common word, uncommon kanji spelling."
        ),
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate same-surface reading/form sample failures and bounded "
            "sidecar policy probes for en-ja learner difficulty."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--source-pair-json", type=Path, default=DEFAULT_SOURCE_PAIR_JSON)
    parser.add_argument("--reading-audit-json", type=Path, default=DEFAULT_READING_AUDIT_JSON)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--anchor-model", default=ANCHOR_MODEL)
    parser.add_argument("--detail-limit", type=int, default=12)
    parser.add_argument("--review-limit", type=int, default=18)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        source_pair_json_path=_resolve_path(args.source_pair_json),
        reading_audit_json_path=_resolve_path(args.reading_audit_json),
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        stitched_report_path=_resolve_path(args.stitched_report),
        anchor_model=str(args.anchor_model),
        detail_limit=max(1, int(args.detail_limit)),
        review_limit=max(1, int(args.review_limit)),
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
    source_pair_json_path: Path,
    reading_audit_json_path: Path,
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    anchor_model: str,
    detail_limit: int,
    review_limit: int,
) -> dict[str, object]:
    component_payload = np.load(component_matrix_path)
    component_view = ComponentView.from_npz(component_payload)
    matrix = MatrixView.from_npz(component_payload)
    score_arrays, resolved_ids = score_arrays_for_models(
        view=component_view,
        parts=family_parts(component_view),
        v1_report_path=v1_report_path,
        cap_report_path=cap_report_path,
        stitched_report_path=stitched_report_path,
        v1_candidate_id=None,
        cap_candidate_id=None,
        stitch_candidate_id=None,
    )
    if anchor_model not in score_arrays:
        raise ValueError(f"Unknown anchor model: {anchor_model}")
    scores = {name: np.asarray(values, dtype=np.float32) for name, values in score_arrays.items()}
    anchor_scores = scores[anchor_model]
    lookup = component_lookup(component_payload)
    labels = scalar_labels(source_pair_json_path, lookup=lookup)
    groups = same_surface_groups(matrix)
    probe_rows = [
        reviewed_probe_row(
            probe,
            matrix=matrix,
            lookup=lookup,
            groups=groups,
            scores=scores,
            anchor_model=anchor_model,
            scalar_labels=labels,
        )
        for probe in REVIEWED_PROBES
    ]
    policy_specs = candidate_policies()
    policy_reports = [
        policy_report(
            spec,
            matrix=matrix,
            groups=groups,
            anchor_scores=anchor_scores,
            scalar_labels=labels,
            probe_rows=probe_rows,
            detail_limit=detail_limit,
        )
        for spec in policy_specs
    ]
    review_pack = same_surface_review_pack(
        matrix=matrix,
        groups=groups,
        anchor_scores=anchor_scores,
        all_scores=scores,
        scalar_labels=labels,
        review_limit=review_limit,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Isolate whether the suspicious reviewed rows are explained by "
                "source-backed reading/form specificity, same-surface sibling "
                "competition, or a separate candidate-classification problem."
            ),
            "anchor_model": anchor_model,
            "important_distinction": (
                "The older reading-specific audit is a broad nonstandard-reading "
                "floor search. This sidecar adds same-written-form sibling "
                "features and reports blast radius before any promotion."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "source_pair_json": _repo_or_home_path(source_pair_json_path),
            "reading_audit_json": _repo_or_home_path(reading_audit_json_path),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            "anchor_model": anchor_model,
            "resolved_model_ids": resolved_ids,
            "population_count": len(matrix.lemmas),
            "scalar_label_count": len(labels),
            "review_limit_per_bucket": review_limit,
        },
        "prior_broad_reading_audit": prior_reading_audit_summary(reading_audit_json_path),
        "reviewed_probe_rows": probe_rows,
        "policy_probes": policy_reports,
        "same_surface_review_pack": review_pack,
        "interpretation": interpretation(probe_rows, policy_reports),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "source_pair_json": source_pair_json_path,
                "reading_audit_json": reading_audit_json_path,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
                "stitched_report": stitched_report_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "reading_form_sample_eval": Path(__file__),
                "source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_source_arbitration_en_ja.py",
                "stitch_validation_eval": SCRIPT_DIR
                / "srs_learner_difficulty_stitch_validation_eval_en_ja.py",
            },
            version_constants={
                "artifact_kind": "srs_learner_difficulty_reading_form_sample_eval",
                "schema_version": 1,
            },
            argv=sys.argv,
        ),
    }


def scalar_labels(
    source_pair_json_path: Path,
    *,
    lookup: Mapping[tuple[str, str], int],
) -> dict[int, dict[str, object]]:
    payload = json.loads(source_pair_json_path.read_text(encoding="utf-8"))
    labels: dict[int, dict[str, object]] = {}
    for row in payload.get("rows", ()):
        if not isinstance(row, Mapping) or row.get("target") != "scalar_vocab":
            continue
        value = _optional_float(row.get("expected_learner_difficulty"))
        if value is None:
            continue
        index = lookup.get((str(row.get("lemma") or ""), str(row.get("reading") or "")))
        if index is None:
            continue
        labels[int(index)] = {
            "label": row.get("label") or f"{row.get('lemma')}/{row.get('reading')}",
            "expected_learner_difficulty": _rounded(value),
            "primary_pair_status": row.get("primary_pair_status"),
            "review_row_number": row.get("review_row_number"),
        }
    return labels


def same_surface_groups(matrix: MatrixView) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    for index, lemma in enumerate(matrix.lemmas):
        groups.setdefault(lemma, []).append(index)
    return groups


def reviewed_probe_row(
    probe: ReviewedProbe,
    *,
    matrix: MatrixView,
    lookup: Mapping[tuple[str, str], int],
    groups: Mapping[str, Sequence[int]],
    scores: Mapping[str, np.ndarray],
    anchor_model: str,
    scalar_labels: Mapping[int, Mapping[str, object]],
) -> dict[str, object]:
    index = lookup.get((probe.lemma, probe.reading))
    if index is None:
        return {
            "lemma": probe.lemma,
            "reading": probe.reading,
            "label": f"{probe.lemma}/{probe.reading}",
            "role": probe.role,
            "desired_direction": probe.desired_direction,
            "review_call": probe.review_call,
            "review_target_note": probe.review_target_note,
            "missing": True,
        }
    row = matrix_row(
        index,
        matrix=matrix,
        groups=groups,
        anchor_scores=scores[anchor_model],
        all_scores=scores,
        scalar_labels=scalar_labels,
    )
    return {
        **row,
        "role": probe.role,
        "desired_direction": probe.desired_direction,
        "review_call": probe.review_call,
        "review_target_note": probe.review_target_note,
        "diagnosis": row_diagnosis(row),
    }


def matrix_row(
    index: int,
    *,
    matrix: MatrixView,
    groups: Mapping[str, Sequence[int]],
    anchor_scores: np.ndarray,
    all_scores: Mapping[str, np.ndarray],
    scalar_labels: Mapping[int, Mapping[str, object]],
) -> dict[str, object]:
    signals = signal_snapshot(index, matrix=matrix)
    features = row_features(index, matrix=matrix, groups=groups, anchor_scores=anchor_scores)
    scalar_label = scalar_labels.get(index)
    row = {
        "index": index,
        "lemma": matrix.lemmas[index],
        "reading": matrix.readings[index],
        "label": f"{matrix.lemmas[index]}/{matrix.readings[index]}",
        "candidate_state": matrix.candidate_states[index],
        "problem_class": matrix.problem_classes[index],
        "core_rank": _rounded(finite_or_none(float(matrix.core_ranks[index]))),
        "scores": {
            name: _rounded(float(values[index])) for name, values in sorted(all_scores.items())
        },
        "anchor_observed": _rounded(float(anchor_scores[index])),
        "signals": signals,
        "active_reading_form_signals": active_signal_list(signals),
        "same_surface_features": features,
        "same_surface_siblings": sibling_rows(
            index,
            matrix=matrix,
            groups=groups,
            anchor_scores=anchor_scores,
        ),
        "scalar_label": scalar_label,
    }
    if scalar_label is not None:
        expected = float(scalar_label["expected_learner_difficulty"])
        row["anchor_abs_error_against_scalar_label"] = _rounded(
            abs(expected - float(anchor_scores[index]))
        )
        row["anchor_direction_against_scalar_label"] = (
            "too_low" if float(anchor_scores[index]) < expected else "too_high"
        )
    return row


def signal_snapshot(index: int, *, matrix: MatrixView) -> dict[str, object]:
    component_index = matrix.component_index()
    result: dict[str, object] = {}
    for name in SNAPSHOT_SIGNALS:
        column = component_index.get(name)
        result[name] = (
            None if column is None else _rounded(float(matrix.component_values[index, column]))
        )
    return result


def active_signal_list(signals: Mapping[str, object]) -> list[str]:
    active = []
    for name in READING_FORM_SIGNALS:
        value = _optional_float(signals.get(name))
        if value is not None and value > 0.0:
            active.append(f"{name}={_rounded(value)}")
    return active


def row_features(
    index: int,
    *,
    matrix: MatrixView,
    groups: Mapping[str, Sequence[int]],
    anchor_scores: np.ndarray,
) -> dict[str, object]:
    lemma = matrix.lemmas[index]
    siblings = [candidate for candidate in groups.get(lemma, ()) if candidate != index]
    distinct_sibling_readings = sorted({matrix.readings[candidate] for candidate in siblings})
    current_rank = finite_or_none(float(matrix.core_ranks[index]))
    sibling_ranks = [finite_or_none(float(matrix.core_ranks[candidate])) for candidate in siblings]
    finite_sibling_ranks = [rank for rank in sibling_ranks if rank is not None]
    best_sibling_rank = min(finite_sibling_ranks) if finite_sibling_ranks else None
    rank_disadvantage = rank_disadvantage_score(current_rank, best_sibling_rank)
    source_markedness = reading_form_source_strength(index, matrix=matrix)
    sibling_strengths = [
        reading_form_source_strength(candidate, matrix=matrix) for candidate in siblings
    ]
    sibling_min_strength = min(sibling_strengths) if sibling_strengths else None
    easiest_sibling_score = (
        min(float(anchor_scores[candidate]) for candidate in siblings) if siblings else None
    )
    hardest_sibling_score = (
        max(float(anchor_scores[candidate]) for candidate in siblings) if siblings else None
    )
    score_gap_to_easiest_sibling = (
        float(anchor_scores[index]) - easiest_sibling_score
        if easiest_sibling_score is not None
        else None
    )
    same_surface_risk = same_surface_competition_risk(
        sibling_count=len(siblings),
        source_markedness=source_markedness,
        rank_disadvantage=rank_disadvantage,
        unranked_vs_ranked=bool(current_rank is None and best_sibling_rank is not None),
    )
    return {
        "same_surface_alternative_count": len(distinct_sibling_readings),
        "same_surface_sibling_count": len(siblings),
        "distinct_sibling_readings": distinct_sibling_readings,
        "best_sibling_core_rank": _rounded(best_sibling_rank),
        "rank_disadvantage_score": _rounded(rank_disadvantage),
        "unranked_vs_ranked_sibling": bool(current_rank is None and best_sibling_rank is not None),
        "source_reading_form_strength": _rounded(source_markedness),
        "sibling_min_reading_form_strength": _rounded(sibling_min_strength),
        "reading_form_strength_delta_vs_min_sibling": _rounded(
            source_markedness - sibling_min_strength if sibling_min_strength is not None else None
        ),
        "easiest_sibling_anchor_score": _rounded(easiest_sibling_score),
        "hardest_sibling_anchor_score": _rounded(hardest_sibling_score),
        "score_gap_to_easiest_sibling": _rounded(score_gap_to_easiest_sibling),
        "same_surface_competition_risk": _rounded(same_surface_risk),
    }


def sibling_rows(
    index: int,
    *,
    matrix: MatrixView,
    groups: Mapping[str, Sequence[int]],
    anchor_scores: np.ndarray,
) -> list[dict[str, object]]:
    siblings = [
        candidate for candidate in groups.get(matrix.lemmas[index], ()) if candidate != index
    ]
    rows = []
    for candidate in siblings:
        rows.append(
            {
                "lemma": matrix.lemmas[candidate],
                "reading": matrix.readings[candidate],
                "candidate_state": matrix.candidate_states[candidate],
                "problem_class": matrix.problem_classes[candidate],
                "core_rank": _rounded(finite_or_none(float(matrix.core_ranks[candidate]))),
                "anchor_observed": _rounded(float(anchor_scores[candidate])),
                "source_reading_form_strength": _rounded(
                    reading_form_source_strength(candidate, matrix=matrix)
                ),
            }
        )
    rows.sort(
        key=lambda row: (
            float(row["anchor_observed"]),
            float(row["core_rank"]) if row.get("core_rank") is not None else float("inf"),
        )
    )
    return rows


def reading_form_source_strength(index: int, *, matrix: MatrixView) -> float:
    component_index = matrix.component_index()
    values = []
    for name in READING_FORM_SIGNALS:
        column = component_index.get(name)
        if column is not None:
            values.append(float(matrix.component_values[index, column]))
    return max(values) if values else 0.0


def rank_disadvantage_score(current_rank: float | None, best_sibling_rank: float | None) -> float:
    if best_sibling_rank is None:
        return 0.0
    if current_rank is None:
        return 1.0
    if current_rank <= best_sibling_rank:
        return 0.0
    ratio = max(1.0, current_rank / max(best_sibling_rank, 1.0))
    return min(1.0, math.log(ratio) / math.log(8.0))


def same_surface_competition_risk(
    *,
    sibling_count: int,
    source_markedness: float,
    rank_disadvantage: float,
    unranked_vs_ranked: bool,
) -> float:
    if sibling_count <= 0:
        return 0.0
    risk = 0.35 + 0.3 * max(0.0, min(1.0, source_markedness))
    risk += 0.25 * max(0.0, min(1.0, rank_disadvantage))
    if unranked_vs_ranked:
        risk += 0.1
    return max(0.0, min(1.0, risk))


def candidate_policies() -> list[PolicySpec]:
    return [
        PolicySpec(
            policy_id="same_surface_marked_floor16",
            description=(
                "If the same written form has another reading and a source "
                "reading/form signal is active, apply a very mild floor of 0.16."
            ),
            floor_for_row=lambda row: (
                0.16
                if same_surface_marked(row) and float(row.get("anchor_observed") or 0.0) < 0.16
                else None
            ),
        ),
        PolicySpec(
            policy_id="same_surface_marked_floor22",
            description=(
                "Same condition as marked_floor16, but tests whether a stronger "
                "0.22 floor has acceptable blast radius."
            ),
            floor_for_row=lambda row: (
                0.22
                if same_surface_marked(row) and float(row.get("anchor_observed") or 0.0) < 0.22
                else None
            ),
        ),
        PolicySpec(
            policy_id="same_surface_rank_gap_floor32",
            description=(
                "If the same written form has another reading and the current row "
                "is materially lower-ranked/unranked than a sibling, apply 0.32."
            ),
            floor_for_row=lambda row: (
                0.32
                if same_surface_rank_gap(row) and float(row.get("anchor_observed") or 0.0) < 0.32
                else None
            ),
        ),
        PolicySpec(
            policy_id="same_surface_rank_gap_floor40",
            description=(
                "Same rank-gap condition as floor32, testing a more aggressive 0.40 floor."
            ),
            floor_for_row=lambda row: (
                0.4
                if same_surface_rank_gap(row) and float(row.get("anchor_observed") or 0.0) < 0.4
                else None
            ),
        ),
        PolicySpec(
            policy_id="same_surface_dynamic_review_shape",
            description=(
                "Diagnostic shape: mild 0.16 for marked beginner/common rows, "
                "0.32 for same-surface rank-gap rows, and 0.38 for unranked or "
                "rare-reading rows. This is review-only, not a promotion candidate."
            ),
            floor_for_row=dynamic_review_floor,
        ),
    ]


def same_surface_marked(row: Mapping[str, object]) -> bool:
    features = _mapping(row.get("same_surface_features"))
    return (
        str(row.get("candidate_state")) == "normal_vocab"
        and int(features.get("same_surface_alternative_count") or 0) > 0
        and float(features.get("source_reading_form_strength") or 0.0) >= 0.5
    )


def same_surface_rank_gap(row: Mapping[str, object]) -> bool:
    features = _mapping(row.get("same_surface_features"))
    return (
        str(row.get("candidate_state")) == "normal_vocab"
        and int(features.get("same_surface_alternative_count") or 0) > 0
        and (
            bool(features.get("unranked_vs_ranked_sibling"))
            or float(features.get("rank_disadvantage_score") or 0.0) >= 0.2
        )
    )


def dynamic_review_floor(row: Mapping[str, object]) -> float | None:
    if str(row.get("candidate_state")) != "normal_vocab":
        return None
    features = _mapping(row.get("same_surface_features"))
    if int(features.get("same_surface_alternative_count") or 0) <= 0:
        return None
    anchor = float(row.get("anchor_observed") or 0.0)
    source_strength = float(features.get("source_reading_form_strength") or 0.0)
    rank_gap = float(features.get("rank_disadvantage_score") or 0.0)
    unranked = bool(features.get("unranked_vs_ranked_sibling"))
    signals = _mapping(row.get("signals"))
    rare_reading = max(
        float(signals.get("rare_non_standard_reading_risk") or 0.0),
        float(signals.get("rare_wago_non_standard_reading_risk") or 0.0),
    )
    if unranked or rare_reading >= 0.25:
        return 0.38 if anchor < 0.38 else None
    if rank_gap >= 0.2:
        return 0.32 if anchor < 0.32 else None
    if source_strength >= 0.5:
        return 0.16 if anchor < 0.16 else None
    return None


def policy_report(
    spec: PolicySpec,
    *,
    matrix: MatrixView,
    groups: Mapping[str, Sequence[int]],
    anchor_scores: np.ndarray,
    scalar_labels: Mapping[int, Mapping[str, object]],
    probe_rows: Sequence[Mapping[str, object]],
    detail_limit: int,
) -> dict[str, object]:
    matched_rows: list[dict[str, object]] = []
    changed_rows: list[dict[str, object]] = []
    for index in range(len(matrix.lemmas)):
        row = {
            "index": index,
            "lemma": matrix.lemmas[index],
            "reading": matrix.readings[index],
            "label": f"{matrix.lemmas[index]}/{matrix.readings[index]}",
            "candidate_state": matrix.candidate_states[index],
            "problem_class": matrix.problem_classes[index],
            "anchor_observed": _rounded(float(anchor_scores[index])),
            "signals": signal_snapshot(index, matrix=matrix),
            "same_surface_features": row_features(
                index,
                matrix=matrix,
                groups=groups,
                anchor_scores=anchor_scores,
            ),
        }
        floor = spec.floor_for_row(row)
        if floor is None:
            continue
        changed = float(anchor_scores[index]) < floor
        payload = {
            "label": row["label"],
            "lemma": row["lemma"],
            "reading": row["reading"],
            "candidate_state": row["candidate_state"],
            "problem_class": row["problem_class"],
            "anchor_observed": row["anchor_observed"],
            "policy_floor": _rounded(floor),
            "adjusted_observed": _rounded(max(float(anchor_scores[index]), floor)),
            "same_surface_features": row["same_surface_features"],
            "active_reading_form_signals": active_signal_list(_mapping(row["signals"])),
        }
        matched_rows.append(payload)
        if changed:
            changed_rows.append(payload)
    labeled_eval = labeled_policy_eval(
        spec,
        matrix=matrix,
        groups=groups,
        anchor_scores=anchor_scores,
        scalar_labels=scalar_labels,
    )
    reviewed_eval = reviewed_policy_eval(spec, probe_rows=probe_rows)
    changed_rows.sort(
        key=lambda row: (
            float(
                _mapping(row.get("same_surface_features")).get("same_surface_competition_risk")
                or 0.0
            ),
            float(row.get("policy_floor") or 0.0) - float(row.get("anchor_observed") or 0.0),
        ),
        reverse=True,
    )
    return {
        "policy_id": spec.policy_id,
        "description": spec.description,
        "full_matrix": {
            "would_match_count": len(matched_rows),
            "would_change_count": len(changed_rows),
            "would_change_examples": changed_rows[:detail_limit],
        },
        "scalar_label_eval": labeled_eval,
        "reviewed_probe_eval": reviewed_eval,
        "promotion_readiness": policy_promotion_readiness(
            labeled_eval,
            reviewed_eval,
            full_changed_count=len(changed_rows),
        ),
    }


def labeled_policy_eval(
    spec: PolicySpec,
    *,
    matrix: MatrixView,
    groups: Mapping[str, Sequence[int]],
    anchor_scores: np.ndarray,
    scalar_labels: Mapping[int, Mapping[str, object]],
) -> dict[str, object]:
    before_errors = []
    after_errors = []
    changed = []
    regressions = []
    improvements = []
    for index, label in scalar_labels.items():
        row = {
            "index": index,
            "lemma": matrix.lemmas[index],
            "reading": matrix.readings[index],
            "label": f"{matrix.lemmas[index]}/{matrix.readings[index]}",
            "candidate_state": matrix.candidate_states[index],
            "problem_class": matrix.problem_classes[index],
            "anchor_observed": _rounded(float(anchor_scores[index])),
            "signals": signal_snapshot(index, matrix=matrix),
            "same_surface_features": row_features(
                index,
                matrix=matrix,
                groups=groups,
                anchor_scores=anchor_scores,
            ),
        }
        expected = float(label["expected_learner_difficulty"])
        observed = float(anchor_scores[index])
        floor = spec.floor_for_row(row)
        adjusted = observed if floor is None else max(observed, floor)
        before = abs(expected - observed)
        after = abs(expected - adjusted)
        before_errors.append(before)
        after_errors.append(after)
        if floor is not None and adjusted > observed + 1e-9:
            payload = {
                "label": row["label"],
                "expected": _rounded(expected),
                "anchor_observed": _rounded(observed),
                "adjusted_observed": _rounded(adjusted),
                "before_abs_error": _rounded(before),
                "after_abs_error": _rounded(after),
            }
            changed.append(payload)
            if after > before + 1e-9:
                regressions.append(payload)
            elif after < before - 1e-9:
                improvements.append(payload)
    before_mae = float(np.mean(before_errors)) if before_errors else None
    after_mae = float(np.mean(after_errors)) if after_errors else None
    return {
        "count": len(before_errors),
        "changed_count": len(changed),
        "improvement_count": len(improvements),
        "regression_count": len(regressions),
        "anchor_mae": _rounded(before_mae),
        "adjusted_mae": _rounded(after_mae),
        "mae_reduction": _rounded(
            before_mae - after_mae if before_mae is not None and after_mae is not None else None
        ),
        "changed_rows": changed,
        "regression_rows": regressions,
    }


def reviewed_policy_eval(
    spec: PolicySpec,
    *,
    probe_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    rows = []
    counts = {
        "target_upshift_changed": 0,
        "accepted_control_changed": 0,
        "known_caveat_changed": 0,
        "separate_downshift_changed": 0,
        "false_positive_probe_changed": 0,
    }
    for row in probe_rows:
        if row.get("missing"):
            continue
        floor = spec.floor_for_row(row)
        anchor = float(row.get("anchor_observed") or 0.0)
        adjusted = anchor if floor is None else max(anchor, floor)
        changed = adjusted > anchor + 1e-9
        role = str(row.get("role"))
        if changed and role in {
            "target_upshift",
            "accepted_control",
            "known_caveat",
            "separate_downshift",
            "false_positive_probe",
        }:
            counts[f"{role}_changed"] += 1
        rows.append(
            {
                "label": row.get("label"),
                "role": role,
                "review_call": row.get("review_call"),
                "anchor_observed": row.get("anchor_observed"),
                "policy_floor": _rounded(floor),
                "adjusted_observed": _rounded(adjusted),
                "changed": changed,
                "diagnosis": row.get("diagnosis"),
            }
        )
    return {"counts": counts, "rows": rows}


def policy_promotion_readiness(
    labeled_eval: Mapping[str, object],
    reviewed_eval: Mapping[str, object],
    *,
    full_changed_count: int,
) -> str:
    counts = _mapping(reviewed_eval.get("counts"))
    if int(counts.get("separate_downshift_changed") or 0) > 0:
        return "reject_wrong_direction_probe_changed"
    if int(counts.get("accepted_control_changed") or 0) > 0:
        return "review_only_control_changed"
    if int(counts.get("false_positive_probe_changed") or 0) > 0:
        return "review_only_false_positive_probe_changed"
    if full_changed_count > 500:
        return "review_only_high_full_matrix_blast_radius"
    if float(labeled_eval.get("mae_reduction") or 0.0) <= 0.0:
        return "review_only_no_labeled_gain"
    if int(counts.get("target_upshift_changed") or 0) <= 0:
        return "review_only_misses_target_examples"
    return "possible_review_candidate_needs_more_labels"


def same_surface_review_pack(
    *,
    matrix: MatrixView,
    groups: Mapping[str, Sequence[int]],
    anchor_scores: np.ndarray,
    all_scores: Mapping[str, np.ndarray],
    scalar_labels: Mapping[int, Mapping[str, object]],
    review_limit: int,
) -> dict[str, object]:
    rows = [
        review_pack_row(
            index,
            matrix=matrix,
            groups=groups,
            anchor_scores=anchor_scores,
            all_scores=all_scores,
            scalar_labels=scalar_labels,
        )
        for index in range(len(matrix.lemmas))
        if matrix.candidate_states[index] == "normal_vocab"
    ]
    buckets = [
        review_bucket(
            "source_plus_rank_gap_unlabeled",
            (
                "Strongest upshift review candidates: same written form, source "
                "reading/form evidence, and a lower-ranked or unranked sibling gap."
            ),
            [
                row
                for row in rows
                if row.get("review_status") == "unlabeled"
                and same_surface_source_plus_rank_gap(row)
            ],
            sort_key=source_plus_rank_sort_key,
            limit=review_limit,
        ),
        review_bucket(
            "rank_gap_without_source_unlabeled",
            (
                "Ambiguous candidates: same written form and rank gap, but no "
                "explicit source markedness. This is where 真/まこと lives."
            ),
            [
                row
                for row in rows
                if row.get("review_status") == "unlabeled"
                and same_surface_rank_gap_without_source(row)
            ],
            sort_key=rank_gap_sort_key,
            limit=review_limit,
        ),
        review_bucket(
            "source_marked_common_caveats_unlabeled",
            (
                "Potential false positives: source form risk exists, but the row "
                "is common/beginner-ish or has no sibling rank disadvantage."
            ),
            [
                row
                for row in rows
                if row.get("review_status") == "unlabeled" and source_marked_common_caveat(row)
            ],
            sort_key=common_caveat_sort_key,
            limit=review_limit,
        ),
        review_bucket(
            "ordinary_variant_false_positive_controls",
            (
                "Controls for rank-gap policies: ordinary onyomi/kunyomi variants "
                "that may look risky numerically but should not all be penalized."
            ),
            [
                row
                for row in rows
                if row.get("review_status") == "unlabeled"
                and ordinary_variant_false_positive_control(row)
            ],
            sort_key=rank_gap_sort_key,
            limit=review_limit,
        ),
        review_bucket(
            "existing_scalar_same_surface_anchors",
            (
                "Already-labeled same-surface rows. Use these as calibration "
                "anchors before assigning new scores."
            ),
            [
                row
                for row in rows
                if row.get("review_status") == "existing_scalar_label"
                and int(
                    _mapping(row.get("same_surface_features")).get("same_surface_alternative_count")
                    or 0
                )
                > 0
                and (
                    float(
                        _mapping(row.get("same_surface_features")).get(
                            "source_reading_form_strength"
                        )
                        or 0.0
                    )
                    >= 0.5
                    or float(
                        _mapping(row.get("same_surface_features")).get("rank_disadvantage_score")
                        or 0.0
                    )
                    >= 0.2
                )
            ],
            sort_key=scalar_anchor_sort_key,
            limit=review_limit,
        ),
    ]
    return {
        "purpose": (
            "Human-label queue for deciding whether same-surface reading/form "
            "features can become a narrower correction than the broad reading audit."
        ),
        "selection": (
            "Rows are bucketed by source evidence and sibling-rank shape. Existing "
            "scalar labels are kept as anchors, not relabeling targets."
        ),
        "buckets": buckets,
    }


def review_pack_row(
    index: int,
    *,
    matrix: MatrixView,
    groups: Mapping[str, Sequence[int]],
    anchor_scores: np.ndarray,
    all_scores: Mapping[str, np.ndarray],
    scalar_labels: Mapping[int, Mapping[str, object]],
) -> dict[str, object]:
    row = matrix_row(
        index,
        matrix=matrix,
        groups=groups,
        anchor_scores=anchor_scores,
        all_scores=all_scores,
        scalar_labels=scalar_labels,
    )
    signals = _mapping(row.get("signals"))
    features = _mapping(row.get("same_surface_features"))
    return {
        "index": row.get("index"),
        "label": row.get("label"),
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "candidate_state": row.get("candidate_state"),
        "problem_class": row.get("problem_class"),
        "core_rank": row.get("core_rank"),
        "anchor_observed": row.get("anchor_observed"),
        "scores": row.get("scores"),
        "review_status": (
            "existing_scalar_label" if row.get("scalar_label") is not None else "unlabeled"
        ),
        "scalar_label": row.get("scalar_label"),
        "diagnosis": row_diagnosis(row),
        "review_prompt": review_prompt(row),
        "same_surface_features": row.get("same_surface_features"),
        "same_surface_siblings": row.get("same_surface_siblings"),
        "active_reading_form_signals": row.get("active_reading_form_signals"),
        "signal_summary": {
            "frequency": signals.get("frequency"),
            "frequency_unranked_risk": signals.get("frequency_unranked_risk"),
            "jlpt_vocab_difficulty": signals.get("jlpt_vocab_difficulty"),
            "jlpt_vocab_beginner_core": signals.get("jlpt_vocab_beginner_core"),
            "lesson_vocab_beginner_core": signals.get("lesson_vocab_beginner_core"),
            "jmdict_kana_preferred_risk": signals.get("jmdict_kana_preferred_risk"),
            "jmdict_reading_form_marked_risk": signals.get("jmdict_reading_form_marked_risk"),
            "jmdict_reading_restricted_risk": signals.get("jmdict_reading_restricted_risk"),
            "non_standard_reading_risk": signals.get("non_standard_reading_risk"),
            "rare_non_standard_reading_risk": signals.get("rare_non_standard_reading_risk"),
            "wtype_wago_ease": signals.get("wtype_wago_ease"),
            "wtype_kango_risk": signals.get("wtype_kango_risk"),
            "max_written_form_burden": signals.get("max_written_form_burden"),
            "same_surface_competition_risk": features.get("same_surface_competition_risk"),
        },
    }


def review_bucket(
    bucket_id: str,
    description: str,
    rows: Sequence[Mapping[str, object]],
    *,
    sort_key: Callable[[Mapping[str, object]], tuple[object, ...]],
    limit: int,
) -> dict[str, object]:
    selected = sorted(rows, key=sort_key, reverse=True)[:limit]
    return {
        "bucket_id": bucket_id,
        "description": description,
        "candidate_count": len(rows),
        "rows": selected,
    }


def same_surface_source_plus_rank_gap(row: Mapping[str, object]) -> bool:
    features = _mapping(row.get("same_surface_features"))
    return (
        int(features.get("same_surface_alternative_count") or 0) > 0
        and float(features.get("source_reading_form_strength") or 0.0) >= 0.5
        and (
            bool(features.get("unranked_vs_ranked_sibling"))
            or float(features.get("rank_disadvantage_score") or 0.0) >= 0.2
        )
        and float(row.get("anchor_observed") or 0.0) <= 0.55
    )


def same_surface_rank_gap_without_source(row: Mapping[str, object]) -> bool:
    features = _mapping(row.get("same_surface_features"))
    return (
        int(features.get("same_surface_alternative_count") or 0) > 0
        and float(features.get("source_reading_form_strength") or 0.0) < 0.5
        and float(features.get("rank_disadvantage_score") or 0.0) >= 0.2
        and not ordinary_variant_false_positive_control(row)
        and float(row.get("anchor_observed") or 0.0) <= 0.55
    )


def source_marked_common_caveat(row: Mapping[str, object]) -> bool:
    features = _mapping(row.get("same_surface_features"))
    signals = _mapping(row.get("signal_summary"))
    rank = _optional_float(row.get("core_rank"))
    common = (
        float(signals.get("frequency") or 0.0) <= 0.7
        or float(signals.get("jlpt_vocab_beginner_core") or 0.0) >= 0.35
        or float(signals.get("lesson_vocab_beginner_core") or 0.0) > 0.0
        or (rank is not None and rank <= 8000)
    )
    return (
        int(features.get("same_surface_alternative_count") or 0) > 0
        and float(features.get("source_reading_form_strength") or 0.0) >= 0.5
        and float(features.get("rank_disadvantage_score") or 0.0) < 0.2
        and common
        and float(row.get("anchor_observed") or 0.0) <= 0.35
    )


def ordinary_variant_false_positive_control(row: Mapping[str, object]) -> bool:
    features = _mapping(row.get("same_surface_features"))
    signals = _mapping(row.get("signal_summary"))
    anchor = float(row.get("anchor_observed") or 0.0)
    return (
        int(features.get("same_surface_alternative_count") or 0) > 0
        and float(features.get("source_reading_form_strength") or 0.0) < 0.5
        and float(features.get("rank_disadvantage_score") or 0.0) >= 0.2
        and (
            float(signals.get("jlpt_vocab_beginner_core") or 0.0) >= 0.35
            or (float(signals.get("frequency") or 0.0) <= 0.7 and anchor <= 0.18)
        )
        and anchor <= 0.35
    )


def source_plus_rank_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    features = _mapping(row.get("same_surface_features"))
    signals = _mapping(row.get("signal_summary"))
    return (
        bool(features.get("unranked_vs_ranked_sibling")),
        float(features.get("source_reading_form_strength") or 0.0),
        float(features.get("rank_disadvantage_score") or 0.0),
        float(signals.get("rare_non_standard_reading_risk") or 0.0),
        float(features.get("same_surface_competition_risk") or 0.0),
        -float(row.get("anchor_observed") or 0.0),
    )


def rank_gap_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    features = _mapping(row.get("same_surface_features"))
    return (
        float(features.get("rank_disadvantage_score") or 0.0),
        float(features.get("same_surface_competition_risk") or 0.0),
        int(features.get("same_surface_alternative_count") or 0),
        -float(row.get("anchor_observed") or 0.0),
    )


def common_caveat_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    features = _mapping(row.get("same_surface_features"))
    signals = _mapping(row.get("signal_summary"))
    return (
        float(features.get("source_reading_form_strength") or 0.0),
        float(signals.get("jlpt_vocab_beginner_core") or 0.0),
        -float(signals.get("frequency") or 0.0),
        -float(row.get("anchor_observed") or 0.0),
    )


def scalar_anchor_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    scalar = _mapping(row.get("scalar_label"))
    expected = float(scalar.get("expected_learner_difficulty") or 0.0)
    observed = float(row.get("anchor_observed") or 0.0)
    features = _mapping(row.get("same_surface_features"))
    return (
        abs(expected - observed),
        float(features.get("same_surface_competition_risk") or 0.0),
    )


def review_prompt(row: Mapping[str, object]) -> str:
    diagnosis = row_diagnosis(row)
    if diagnosis == "same_surface_plus_source_marking_and_rank_gap":
        return "Likely upshift candidate; judge whether this reading is materially later than its sibling."
    if diagnosis == "same_surface_rank_gap_without_source_marking":
        return "Ambiguous; decide whether rank gap reflects a real alternate-reading burden or an ordinary variant."
    if diagnosis == "source_marked_same_surface_reading":
        return "Caveat/control; decide whether source markedness should override common-word protection."
    return "Control; check whether this should stay near the current band."


def row_diagnosis(row: Mapping[str, object]) -> str:
    if row.get("candidate_state") != "normal_vocab":
        return "separate_candidate_classification_issue"
    features = _mapping(row.get("same_surface_features"))
    source = float(features.get("source_reading_form_strength") or 0.0)
    alternatives = int(features.get("same_surface_alternative_count") or 0)
    rank_gap = float(features.get("rank_disadvantage_score") or 0.0)
    if alternatives > 0 and source >= 0.5 and rank_gap >= 0.2:
        return "same_surface_plus_source_marking_and_rank_gap"
    if alternatives > 0 and source >= 0.5:
        return "source_marked_same_surface_reading"
    if alternatives > 0 and rank_gap >= 0.2:
        return "same_surface_rank_gap_without_source_marking"
    if source >= 0.5:
        return "source_marked_form_without_same_surface_sibling"
    return "no_strong_source_backed_reading_form_signal"


def prior_reading_audit_summary(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"available": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = _mapping(payload.get("summary"))
    interpretation_payload = _mapping(_mapping(summary.get("best")).get("summary"))
    full = _mapping(payload.get("best_full_matrix_review"))
    return {
        "available": True,
        "best_candidate_id": summary.get("best_candidate_id"),
        "promotion_readiness": _mapping(summary.get("interpretation")).get("promotion_readiness"),
        "validation_reading_delta": _mapping(summary.get("interpretation")).get(
            "validation_reading_delta"
        ),
        "holdout_all_delta": _mapping(summary.get("interpretation")).get("holdout_all_delta"),
        "would_match_count": full.get("would_match_count"),
        "would_change_count": full.get("would_change_count"),
        "common_protected_near_miss_count": full.get("common_protected_near_miss_count"),
        "candidate_summary": interpretation_payload,
    }


def interpretation(
    probe_rows: Sequence[Mapping[str, object]],
    policy_reports: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    best_low_blast = sorted(
        policy_reports,
        key=lambda report: (
            int(_mapping(report.get("full_matrix")).get("would_change_count") or 0),
            -float(_mapping(report.get("scalar_label_eval")).get("mae_reduction") or 0.0),
        ),
    )[0]
    return {
        "main_learning": (
            "The suspicious rows do not share one clean signal. 辛い/つらい and "
            "誘う/いざなう have source-backed reading/form evidence; 真/まこと "
            "mostly has same-surface sibling competition but no explicit source "
            "markedness; ゲロ/げろ is an opposite-direction classification issue."
        ),
        "what_this_enables": (
            "A future model can test a bounded floor that is conditional on "
            "same-written-form competition, rather than applying the broad "
            "nonstandard-reading floor to all rows."
        ),
        "what_it_does_not_solve": (
            "It does not by itself prove the correct numeric floor for unlabeled "
            "rows like 真/まこと or 誘う/いざなう; those still need labels or a "
            "review pack because current scalar labels only directly anchor 辛い/つらい."
        ),
        "lowest_blast_policy_probe": best_low_blast.get("policy_id"),
        "probe_diagnoses": {str(row.get("label")): row.get("diagnosis") for row in probe_rows},
    }


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    prior = _mapping(report.get("prior_broad_reading_audit"))
    interpretation_payload = _mapping(report.get("interpretation"))
    lines = [
        "# en-ja Reading/Form Sample Evaluation",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Sweeps run: `{_escape(report.get('sweeps_run'))}`",
        f"- Anchor model: `{_escape(inputs.get('anchor_model'))}`",
        f"- Component matrix: `{_escape(inputs.get('component_matrix'))}`",
        f"- Scalar labels inspected: `{_escape(inputs.get('scalar_label_count'))}`",
        "",
        "## Why This Exists",
        "",
        _escape(_mapping(report.get("method")).get("purpose")),
        "",
        "This is intentionally narrower than the prior broad reading audit.",
        "",
        "## Prior Broad Reading Audit",
        "",
    ]
    if prior.get("available"):
        lines.extend(
            [
                f"- Best candidate: `{_escape(prior.get('best_candidate_id'))}`",
                f"- Promotion readiness: `{_escape(prior.get('promotion_readiness'))}`",
                f"- Validation reading MAE reduction: `{_escape(prior.get('validation_reading_delta'))}`",
                f"- Holdout all-row MAE reduction: `{_escape(prior.get('holdout_all_delta'))}`",
                f"- Full-matrix matches/changes: `{_escape(prior.get('would_match_count'))}` / `{_escape(prior.get('would_change_count'))}`",
                f"- Common-protected near misses: `{_escape(prior.get('common_protected_near_miss_count'))}`",
            ]
        )
    else:
        lines.append("- Prior audit artifact not found.")
    lines.extend(["", "## Reviewed Probe Rows", ""])
    lines.extend(probe_table(report.get("reviewed_probe_rows")))
    lines.extend(["", "## Same-Surface Review Pack", ""])
    lines.extend(review_pack_markdown(_mapping(report.get("same_surface_review_pack"))))
    lines.extend(["", "## Policy Probes", ""])
    lines.extend(policy_table(report.get("policy_probes")))
    lines.extend(["", "## Policy Details", ""])
    for policy in _rows(report.get("policy_probes")):
        lines.extend(policy_detail_block(policy))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Main learning: {_escape(interpretation_payload.get('main_learning'))}",
            f"- What this enables: {_escape(interpretation_payload.get('what_this_enables'))}",
            f"- What it does not solve: {_escape(interpretation_payload.get('what_it_does_not_solve'))}",
            f"- Lowest-blast policy probe: `{_escape(interpretation_payload.get('lowest_blast_policy_probe'))}`",
            "",
        ]
    )
    return "\n".join(lines)


def probe_table(rows: object) -> list[str]:
    lines = [
        "| Entry | Role | Current | Scalar label | Siblings | Source form risk | Rank gap | Diagnosis | Review |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in _rows(rows):
        scalar = _mapping(row.get("scalar_label"))
        features = _mapping(row.get("same_surface_features"))
        scalar_value = scalar.get("expected_learner_difficulty")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape(row.get('label'))}`",
                    f"`{_escape(row.get('role'))}`",
                    f"`{_escape(row.get('anchor_observed'))}`",
                    f"`{_escape(scalar_value)}`" if scalar_value is not None else "",
                    f"`{_escape(features.get('same_surface_alternative_count'))}`",
                    f"`{_escape(features.get('source_reading_form_strength'))}`",
                    f"`{_escape(features.get('rank_disadvantage_score'))}`",
                    _escape(row.get("diagnosis")),
                    _escape(row.get("review_call")),
                ]
            )
            + " |"
        )
    return lines


def policy_table(rows: object) -> list[str]:
    lines = [
        "| Policy | Label MAE delta | Label changed | Full changes | Target changed | Controls changed | Readiness |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in _rows(rows):
        scalar = _mapping(row.get("scalar_label_eval"))
        full = _mapping(row.get("full_matrix"))
        reviewed = _mapping(row.get("reviewed_probe_eval"))
        counts = _mapping(reviewed.get("counts"))
        controls_changed = int(counts.get("accepted_control_changed") or 0) + int(
            counts.get("false_positive_probe_changed") or 0
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape(row.get('policy_id'))}`",
                    f"`{_escape(scalar.get('mae_reduction'))}`",
                    f"`{_escape(scalar.get('changed_count'))}`",
                    f"`{_escape(full.get('would_change_count'))}`",
                    f"`{_escape(counts.get('target_upshift_changed'))}`",
                    f"`{_escape(controls_changed)}`",
                    f"`{_escape(row.get('promotion_readiness'))}`",
                ]
            )
            + " |"
        )
    return lines


def review_pack_markdown(review_pack: Mapping[str, object]) -> list[str]:
    lines = [
        _escape(review_pack.get("purpose")),
        "",
        _escape(review_pack.get("selection")),
        "",
    ]
    for bucket in _rows(review_pack.get("buckets")):
        lines.append(f"### `{_escape(bucket.get('bucket_id'))}`")
        lines.append("")
        lines.append(_escape(bucket.get("description")))
        lines.append("")
        lines.append(f"- Candidate count: `{_escape(bucket.get('candidate_count'))}`")
        lines.append("")
        lines.extend(review_candidate_table(_rows(bucket.get("rows"))))
        lines.append("")
    return lines


def review_candidate_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["No rows selected."]
    lines = [
        "| Entry | Current | Scalar | Siblings | Source | Rank gap | Signals | Prompt |",
        "|---|---:|---:|---|---:|---:|---|---|",
    ]
    for row in rows:
        features = _mapping(row.get("same_surface_features"))
        scalar = _mapping(row.get("scalar_label"))
        signal_summary = _mapping(row.get("signal_summary"))
        sibling_labels = ", ".join(
            f"`{_escape(sibling.get('reading'))}`:{_escape(sibling.get('anchor_observed'))}"
            for sibling in _rows(row.get("same_surface_siblings"))[:3]
        )
        scalar_value = scalar.get("expected_learner_difficulty")
        signals = compact_signal_text(signal_summary)
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape(row.get('label'))}`",
                    f"`{_escape(row.get('anchor_observed'))}`",
                    f"`{_escape(scalar_value)}`" if scalar_value is not None else "",
                    sibling_labels,
                    f"`{_escape(features.get('source_reading_form_strength'))}`",
                    f"`{_escape(features.get('rank_disadvantage_score'))}`",
                    signals,
                    _escape(row.get("review_prompt")),
                ]
            )
            + " |"
        )
    return lines


def compact_signal_text(signals: Mapping[str, object]) -> str:
    parts = []
    for name in (
        "frequency",
        "frequency_unranked_risk",
        "jlpt_vocab_difficulty",
        "jlpt_vocab_beginner_core",
        "jmdict_kana_preferred_risk",
        "jmdict_reading_form_marked_risk",
        "jmdict_reading_restricted_risk",
        "rare_non_standard_reading_risk",
    ):
        value = signals.get(name)
        if value is None:
            continue
        numeric = _optional_float(value)
        if numeric is None:
            continue
        if name == "frequency" or numeric > 0.0:
            parts.append(f"`{name}={_escape(value)}`")
    return ", ".join(parts)


def policy_detail_block(policy: Mapping[str, object]) -> list[str]:
    full = _mapping(policy.get("full_matrix"))
    scalar = _mapping(policy.get("scalar_label_eval"))
    lines = [
        f"### `{_escape(policy.get('policy_id'))}`",
        "",
        _escape(policy.get("description")),
        "",
        f"- Full-matrix would change: `{_escape(full.get('would_change_count'))}`",
        f"- Scalar-label MAE reduction: `{_escape(scalar.get('mae_reduction'))}`",
    ]
    changed_rows = _rows(scalar.get("changed_rows"))
    if changed_rows:
        lines.append(
            "- Scalar-label changed rows: " + ", ".join(row_label(row) for row in changed_rows)
        )
    examples = _rows(full.get("would_change_examples"))
    if examples:
        lines.append("- Full-matrix examples: " + ", ".join(row_label(row) for row in examples[:8]))
    lines.append("")
    return lines


def row_label(row: Mapping[str, object]) -> str:
    return (
        f"`{_escape(row.get('label'))}` "
        f"({_escape(row.get('anchor_observed'))}->{_escape(row.get('adjusted_observed'))})"
    )


def finite_or_none(value: float) -> float | None:
    return value if math.isfinite(value) else None


def _rows(value: object) -> list[Mapping[str, object]]:
    return [row for row in value or [] if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
