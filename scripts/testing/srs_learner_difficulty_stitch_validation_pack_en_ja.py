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
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _target_curve_normalize,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    DEFAULT_COMPONENT_MATRIX,
    family_parts,
    raw_scores_for_candidate,
)
from srs_learner_difficulty_stitched_source_arbitration_en_ja import (  # noqa: E402
    DEFAULT_CAP_REPORT,
    DEFAULT_JSON_OUT as DEFAULT_STITCHED_REPORT,
    DEFAULT_V1_REPORT,
    _best_holdout_candidate_id,
    _candidate_by_id,
    generate_stitch_candidates,
    stitch_gate,
    stitched_scores,
)


PAIR = "en-ja"
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_ja.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_ja.json"
)
DEFAULT_SURFACE_HOLDOUT_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_learner_difficulty_holdout_en_ja_source_arbitration_surface_s010.json"
)
DEFAULT_RESIDUAL_LABEL_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_learner_difficulty_residual_shape_review_labels_en_ja.json"
)
DEFAULT_BLOCK_LABEL_JSONS = (
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_SURFACE_HOLDOUT_JSON,
    DEFAULT_RESIDUAL_LABEL_JSON,
)
DEFAULT_EXCLUDED_COMPONENT_INDICES = (18755,)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_stitch_validation_pack_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_stitch_validation_pack_en_ja_latest.md"
)
DEFAULT_REVIEW_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_stitch_validation_review_en_ja_latest.md"
)
VOCAB_STATES = frozenset({"normal_vocab"})
VOCAB_PROBLEM_CLASSES = frozenset({"normal_vocab"})
MIN_SCORE_DELTA = 0.05
BUCKET_SPECS = (
    (
        "ped_known_beginner_guard_edge",
        "Pedagogical-source beginner-edge row where small v1/cap shifts can affect guardrails.",
    ),
    (
        "ped_known_v1_higher_than_cap",
        "Pedagogical-source row where the stitch keeps v1 higher than ordinary-cap.",
    ),
    (
        "ped_unknown_cap_lower_than_v1",
        "No pedagogical source; stitch follows ordinary-cap lower than v1.",
    ),
    (
        "ped_unknown_cap_higher_than_v1",
        "No pedagogical source; stitch follows ordinary-cap higher than v1.",
    ),
    (
        "common_without_pedagogical_source",
        "No pedagogical source, but ordinary-source evidence says this may be common.",
    ),
    (
        "stitched_band_anchor",
        "Predicted-band anchor for qualitative inspection of the stitched ordering.",
    ),
)
REVIEW_SIGNAL_NAMES = (
    "frequency",
    "tubelex_frequency",
    "jmdict_priority",
    "jlpt_vocab_difficulty",
    "lesson_vocab_difficulty",
    "jlpt_vocab_beginner_core",
    "lesson_vocab_beginner_core",
    "max_written_form_burden",
    "kanji_curriculum_missing_risk",
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_tail_risk",
    "rare_wago_obscure_written_risk",
    "written_wago_tail_risk",
    "wtype_kango_risk",
    "wtype_gairaigo_risk",
    "wtype_wago_ease",
    "jmdict_marked_usage_risk",
    "jmdict_search_only_form_risk",
)
BAND_ANCHOR_CENTERS = (0.05, 0.15, 0.28, 0.42, 0.56, 0.70, 0.84, 0.94)


@dataclass(frozen=True)
class MatrixRow:
    index: int
    identity_key: str
    lemma: str
    reading: str
    candidate_state: str
    problem_class: str
    core_rank: float | None

    @property
    def label_key(self) -> str:
        return f"{self.lemma}\t{self.reading}"

    @property
    def label(self) -> str:
        return f"{self.lemma}/{self.reading}" if self.reading else self.lemma


@dataclass(frozen=True)
class ScoreContext:
    v1: object
    cap: object
    stitch: object
    stitch_gate: object
    parts: Mapping[str, object]
    review_signals: Mapping[str, object]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a fresh blind validation review pack for the en-ja "
            "v1/ordinary-cap stitched source-arbitration hypothesis."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--v1-candidate-id", default=None)
    parser.add_argument("--cap-candidate-id", default=None)
    parser.add_argument("--stitch-candidate-id", default=None)
    parser.add_argument(
        "--block-label-json",
        type=Path,
        action="append",
        default=list(DEFAULT_BLOCK_LABEL_JSONS),
        help=(
            "Existing reviewed label JSON to exclude from the fresh validation pack. "
            "May be passed multiple times."
        ),
    )
    parser.add_argument(
        "--exclude-label-key",
        action="append",
        default=[],
        help=(
            "Label key in the form 'lemma<TAB>reading' to exclude from this "
            "public review pack. May be passed multiple times."
        ),
    )
    parser.add_argument(
        "--exclude-component-index",
        type=int,
        action="append",
        default=list(DEFAULT_EXCLUDED_COMPONENT_INDICES),
        help="Component-matrix row index to exclude from this public review pack.",
    )
    parser.add_argument("--bucket-size", type=int, default=8)
    parser.add_argument("--min-delta", type=float, default=MIN_SCORE_DELTA)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--review-markdown-out", type=Path, default=DEFAULT_REVIEW_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        stitched_report_path=_resolve_path(args.stitched_report),
        v1_candidate_id=args.v1_candidate_id,
        cap_candidate_id=args.cap_candidate_id,
        stitch_candidate_id=args.stitch_candidate_id,
        block_label_jsons=tuple(_resolve_path(path) for path in args.block_label_json),
        excluded_label_keys=tuple(str(value) for value in args.exclude_label_key),
        excluded_component_indices=tuple(int(value) for value in args.exclude_component_index),
        bucket_size=max(1, int(args.bucket_size)),
        min_delta=max(0.0, float(args.min_delta)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    review_markdown_out = _resolve_path(args.review_markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    review_markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    review_markdown_out.write_text(render_blind_review_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    print(f"Wrote blind review Markdown artifact to {review_markdown_out}")
    return 0


def build_report(
    *,
    component_matrix_path: Path,
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    v1_candidate_id: str | None,
    cap_candidate_id: str | None,
    stitch_candidate_id: str | None,
    block_label_jsons: Sequence[Path],
    excluded_label_keys: Sequence[str],
    excluded_component_indices: Sequence[int],
    bucket_size: int,
    min_delta: float,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    view = ComponentView.from_npz(component)
    rows = matrix_rows(component)
    score_context, resolved_ids = score_context_for_models(
        view=view,
        component=component,
        v1_report_path=v1_report_path,
        cap_report_path=cap_report_path,
        stitched_report_path=stitched_report_path,
        v1_candidate_id=v1_candidate_id,
        cap_candidate_id=cap_candidate_id,
        stitch_candidate_id=stitch_candidate_id,
    )
    blocked_keys, blocked_sources = blocked_label_keys(block_label_jsons)
    blocked_keys.update(excluded_label_keys)
    candidate_pool = [
        row
        for row in rows
        if row.label_key not in blocked_keys
        and row.index not in excluded_component_indices
        and row.candidate_state in VOCAB_STATES
        and row.problem_class in VOCAB_PROBLEM_CLASSES
    ]
    selected = select_validation_rows(
        candidate_pool,
        context=score_context,
        bucket_size=bucket_size,
        min_delta=min_delta,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Create a fresh human-label validation slice for the hypothesis "
                "that pedagogical-source rows should use v1 while non-pedagogical "
                "rows should use the ordinary-cap source-arbitration model."
            ),
            "selection": (
                "Rows exclude current reviewed label files and are selected from "
                "unlabeled normal-vocab rows where the v1/cap/stitch choice is "
                "diagnostically meaningful."
            ),
            "blind_review": (
                "Use the separate blind review Markdown for scoring. The JSON and "
                "diagnostic Markdown intentionally include model scores for later "
                "evaluation and should not be used while assigning labels."
            ),
            "difficulty_scale": (
                "0.00 is first-Japanese-lesson material; 1.00 is recondite unused "
                "material that many native speakers would not know."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            "block_label_jsons": [_repo_or_home_path(path) for path in block_label_jsons],
            "blocked_label_count": len(blocked_keys),
            "blocked_sources": blocked_sources,
            "excluded_label_keys": list(excluded_label_keys),
            "excluded_component_indices": list(excluded_component_indices),
            "normal_vocab_candidate_pool_count": len(candidate_pool),
            "bucket_size": bucket_size,
            "min_delta": _rounded(min_delta),
            **resolved_ids,
        },
        "summary": {
            "selected_count": len(selected),
            "bucket_counts": bucket_counts(selected),
            "stitch_gate_summary": stitch_gate_summary(selected),
            "score_spread_summary": score_spread_summary(selected),
        },
        "selected_rows": selected,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
                "stitched_report": stitched_report_path,
                **{
                    f"block_label_json_{index}": path
                    for index, path in enumerate(block_label_jsons)
                },
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
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


def score_context_for_models(
    *,
    view: ComponentView,
    component: object,
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    v1_candidate_id: str | None,
    cap_candidate_id: str | None,
    stitch_candidate_id: str | None,
) -> tuple[ScoreContext, dict[str, object]]:
    v1_payload = load_json(v1_report_path)
    cap_payload = load_json(cap_report_path)
    stitched_payload = load_json(stitched_report_path)
    resolved_v1_id = v1_candidate_id or _best_holdout_candidate_id(v1_payload)
    resolved_cap_id = cap_candidate_id or _best_holdout_candidate_id(cap_payload)
    resolved_stitch_id = stitch_candidate_id or best_stitch_candidate_id(stitched_payload)
    v1_model = _candidate_by_id(resolved_v1_id)
    cap_model = _candidate_by_id(resolved_cap_id)
    stitch_candidate = stitch_candidate_by_id(resolved_stitch_id)
    parts = family_parts(view)
    target_positions = np.asarray(view.target_positions, dtype=np.float32)
    v1_raw = raw_scores_for_candidate(v1_model, view, parts=parts)
    cap_raw = raw_scores_for_candidate(cap_model, view, parts=parts)
    v1_normalized = _target_curve_normalize(v1_raw, target_positions=target_positions)
    cap_normalized = _target_curve_normalize(cap_raw, target_positions=target_positions)
    stitch_normalized = stitched_scores(
        stitch_candidate,
        parts=parts,
        target_positions=target_positions,
        v1_raw=v1_raw,
        cap_raw=cap_raw,
        v1_normalized=v1_normalized,
        cap_normalized=cap_normalized,
    )
    return (
        ScoreContext(
            v1=np.asarray(v1_normalized, dtype=np.float32),
            cap=np.asarray(cap_normalized, dtype=np.float32),
            stitch=np.asarray(stitch_normalized, dtype=np.float32),
            stitch_gate=np.asarray(stitch_gate(stitch_candidate, parts=parts), dtype=np.float32),
            parts=parts,
            review_signals=review_signal_arrays(component, view),
        ),
        {
            "v1_candidate_id": resolved_v1_id,
            "cap_candidate_id": resolved_cap_id,
            "stitch_candidate_id": resolved_stitch_id,
            "stitch_params": stitch_candidate_params(stitch_candidate),
        },
    )


def select_validation_rows(
    rows: Sequence[MatrixRow],
    *,
    context: ScoreContext,
    bucket_size: int,
    min_delta: float,
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    used_keys: set[str] = set()
    used_lemmas: set[str] = set()
    for bucket, _description in BUCKET_SPECS:
        if bucket == "stitched_band_anchor":
            bucket_rows = band_anchor_candidates(
                rows,
                context=context,
                used_keys=used_keys,
                used_lemmas=used_lemmas,
                limit=bucket_size,
            )
        else:
            bucket_rows = select_bucket_candidates(
                rows,
                context=context,
                bucket=bucket,
                used_keys=used_keys,
                used_lemmas=used_lemmas,
                limit=bucket_size,
                min_delta=min_delta,
            )
        for row in bucket_rows:
            selected_row = row_json(row, bucket=bucket, context=context)
            selected.append(selected_row)
            used_keys.add(row.label_key)
            used_lemmas.add(row.lemma)
    return selected


def select_bucket_candidates(
    rows: Sequence[MatrixRow],
    *,
    context: ScoreContext,
    bucket: str,
    used_keys: set[str],
    used_lemmas: set[str],
    limit: int,
    min_delta: float,
) -> list[MatrixRow]:
    candidates = [
        row
        for row in rows
        if row.label_key not in used_keys
        and row.lemma not in used_lemmas
        and bucket_membership(row, bucket=bucket, context=context, min_delta=min_delta)
    ]
    candidates = sorted(
        candidates,
        key=lambda row: (
            bucket_score(row, bucket=bucket, context=context),
            score_spread(row, context),
            -none_as_large(row.core_rank),
        ),
        reverse=True,
    )
    return diverse_by_band(candidates, context=context, limit=limit)


def bucket_membership(
    row: MatrixRow,
    *,
    bucket: str,
    context: ScoreContext,
    min_delta: float,
) -> bool:
    gate = gate_value(row, context)
    v1 = score_value(context.v1, row.index)
    cap = score_value(context.cap, row.index)
    stitch = score_value(context.stitch, row.index)
    if bucket == "ped_known_beginner_guard_edge":
        return gate >= 0.99 and stitch <= 0.35 and abs(stitch - cap) >= 0.003
    if bucket == "ped_known_v1_higher_than_cap":
        return gate >= 0.99 and (stitch - cap) >= min_delta
    if bucket == "ped_unknown_cap_lower_than_v1":
        return gate <= 0.01 and (stitch - v1) <= -min_delta
    if bucket == "ped_unknown_cap_higher_than_v1":
        return gate <= 0.01 and (stitch - v1) >= min_delta
    if bucket == "common_without_pedagogical_source":
        ordinary = part_value(context.parts, "ordinary_gate_mean", row.index)
        priority = part_value(context.parts, "ordinary_gate_priority", row.index)
        frequency = part_value(context.parts, "ordinary_gate_frequency", row.index)
        return (
            gate <= 0.01
            and max(ordinary, priority, frequency) >= 0.58
            and abs(stitch - v1) >= (min_delta * 0.5)
        )
    raise ValueError(f"unsupported bucket: {bucket}")


def bucket_score(row: MatrixRow, *, bucket: str, context: ScoreContext) -> float:
    v1 = score_value(context.v1, row.index)
    cap = score_value(context.cap, row.index)
    stitch = score_value(context.stitch, row.index)
    if bucket == "ped_known_beginner_guard_edge":
        return (0.35 - score_value(context.stitch, row.index)) + score_spread(row, context)
    if bucket.startswith("ped_known"):
        return abs(stitch - cap)
    if bucket.startswith("ped_unknown"):
        return abs(stitch - v1)
    if bucket == "common_without_pedagogical_source":
        ordinary = part_value(context.parts, "ordinary_gate_mean", row.index)
        priority = part_value(context.parts, "ordinary_gate_priority", row.index)
        frequency = part_value(context.parts, "ordinary_gate_frequency", row.index)
        return max(ordinary, priority, frequency) + abs(stitch - v1)
    return score_spread(row, context)


def diverse_by_band(
    rows: Sequence[MatrixRow],
    *,
    context: ScoreContext,
    limit: int,
) -> list[MatrixRow]:
    selected: list[MatrixRow] = []
    selected_lemmas: set[str] = set()
    band_counts: dict[int, int] = {}
    max_per_band = max(1, int(np.ceil(limit / 4)))
    for row in rows:
        if row.lemma in selected_lemmas:
            continue
        band = score_band(score_value(context.stitch, row.index))
        if band_counts.get(band, 0) >= max_per_band:
            continue
        selected.append(row)
        selected_lemmas.add(row.lemma)
        band_counts[band] = band_counts.get(band, 0) + 1
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        seen = {row.label_key for row in selected}
        for row in rows:
            if row.label_key in seen or row.lemma in selected_lemmas:
                continue
            selected.append(row)
            selected_lemmas.add(row.lemma)
            if len(selected) >= limit:
                break
    return selected


def band_anchor_candidates(
    rows: Sequence[MatrixRow],
    *,
    context: ScoreContext,
    used_keys: set[str],
    used_lemmas: set[str],
    limit: int,
) -> list[MatrixRow]:
    selected: list[MatrixRow] = []
    seen: set[str] = set()
    centers = BAND_ANCHOR_CENTERS[:limit]
    for center in centers:
        candidates = [
            row
            for row in rows
            if row.label_key not in used_keys
            and row.label_key not in seen
            and row.lemma not in used_lemmas
            and row.lemma not in {chosen.lemma for chosen in selected}
        ]
        if not candidates:
            break
        best = min(
            candidates,
            key=lambda row: (
                abs(score_value(context.stitch, row.index) - center),
                -score_spread(row, context),
                none_as_large(row.core_rank),
            ),
        )
        selected.append(best)
        seen.add(best.label_key)
    return selected


def row_json(row: MatrixRow, *, bucket: str, context: ScoreContext) -> dict[str, object]:
    v1 = score_value(context.v1, row.index)
    cap = score_value(context.cap, row.index)
    stitch = score_value(context.stitch, row.index)
    return {
        "review_id": row_review_id(row.index),
        "review_bucket": bucket,
        "review_bucket_description": dict(BUCKET_SPECS).get(bucket, ""),
        "candidate_identity_key": row.identity_key,
        "label_key": row.label_key,
        "lemma": row.lemma,
        "reading": row.reading,
        "label": row.label,
        "candidate_state": row.candidate_state,
        "problem_class": row.problem_class,
        "core_rank": _rounded(row.core_rank),
        "model_scores_hidden_during_review": {
            "v1": _rounded(v1),
            "ordinary_cap": _rounded(cap),
            "stitch": _rounded(stitch),
            "stitch_minus_v1": _rounded(stitch - v1),
            "stitch_minus_cap": _rounded(stitch - cap),
            "spread": _rounded(max(v1, cap, stitch) - min(v1, cap, stitch)),
        },
        "source_gate_signals": {
            "stitch_gate": _rounded(gate_value(row, context)),
            "ped_conf": _rounded(part_value(context.parts, "ped_conf", row.index)),
            "ordinary_gate_pedagogical": _rounded(
                part_value(context.parts, "ordinary_gate_pedagogical", row.index)
            ),
            "ordinary_gate_mean": _rounded(
                part_value(context.parts, "ordinary_gate_mean", row.index)
            ),
            "ordinary_gate_frequency": _rounded(
                part_value(context.parts, "ordinary_gate_frequency", row.index)
            ),
            "ordinary_gate_priority": _rounded(
                part_value(context.parts, "ordinary_gate_priority", row.index)
            ),
            "tail_floor_guard": _rounded(part_value(context.parts, "tail_floor_guard", row.index)),
            "reading_inheritance_risk": _rounded(
                part_value(context.parts, "reading_inheritance_risk", row.index)
            ),
        },
        "signals": {
            name: _rounded(value_at(values, row.index))
            for name, values in context.review_signals.items()
            if value_at(values, row.index) is not None
        },
    }


def matrix_rows(component: object) -> list[MatrixRow]:
    identity_keys = [str(value) for value in component["candidate_identity_keys"]]
    lemmas = [str(value) for value in component["lemmas"]]
    readings = [str(value) for value in component["readings"]]
    candidate_states = [str(value) for value in component["candidate_states"]]
    problem_classes = [str(value) for value in component["problem_classes"]]
    core_ranks = np.asarray(component["core_ranks"], dtype=np.float32)
    return [
        MatrixRow(
            index=index,
            identity_key=identity_keys[index],
            lemma=lemmas[index],
            reading=readings[index],
            candidate_state=candidate_states[index],
            problem_class=problem_classes[index],
            core_rank=float(core_ranks[index]) if np.isfinite(core_ranks[index]) else None,
        )
        for index in range(len(identity_keys))
    ]


def review_signal_arrays(component: object, view: ComponentView) -> dict[str, object]:
    signals: dict[str, object] = {}
    for name in REVIEW_SIGNAL_NAMES:
        try:
            values = view.value(name, fill=np.nan)
        except KeyError:
            continue
        signals[name] = np.asarray(values, dtype=np.float32)
    return signals


def blocked_label_keys(paths: Sequence[Path]) -> tuple[set[str], dict[str, int]]:
    keys: set[str] = set()
    counts: dict[str, int] = {}
    for path in paths:
        path_keys: set[str] = set()
        if path.exists():
            payload = load_json(path)
            for row in payload.get("labels", ()):
                if not isinstance(row, Mapping):
                    continue
                lemma = str(row.get("lemma") or "").strip()
                reading = str(row.get("expected_reading") or row.get("reading") or "").strip()
                if lemma:
                    path_keys.add(f"{lemma}\t{reading}")
        keys.update(path_keys)
        counts[_repo_or_home_path(path)] = len(path_keys)
    return keys, counts


def stitch_candidate_by_id(candidate_id: str) -> object:
    for candidate in generate_stitch_candidates():
        if candidate.candidate_id == candidate_id:
            return candidate
    raise ValueError(f"Stitch candidate not found: {candidate_id}")


def best_stitch_candidate_id(payload: Mapping[str, object]) -> str:
    summary = _mapping(payload.get("summary"))
    for key in ("best_holdout_guardrail", "best_holdout_balanced"):
        candidate_id = _mapping(summary.get(key)).get("candidate_id")
        if candidate_id:
            return str(candidate_id)
    raise ValueError("Could not find stitched summary candidate id")


def stitch_candidate_params(candidate: object) -> dict[str, object]:
    return {
        "gate_signal": getattr(candidate, "gate_signal"),
        "gate_threshold": _rounded(getattr(candidate, "gate_threshold")),
        "gate_mode": getattr(candidate, "gate_mode"),
        "blend_strength": _rounded(getattr(candidate, "blend_strength")),
        "blend_space": getattr(candidate, "blend_space"),
        "normalize_after_blend": getattr(candidate, "normalize_after_blend"),
    }


def bucket_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts = {bucket: 0 for bucket, _description in BUCKET_SPECS}
    for row in rows:
        bucket = str(row.get("review_bucket") or "")
        counts[bucket] = counts.get(bucket, 0) + 1
    return counts


def stitch_gate_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    values = [
        _optional_float(_mapping(row.get("source_gate_signals")).get("stitch_gate")) for row in rows
    ]
    parsed = [float(value) for value in values if value is not None]
    if not parsed:
        return {}
    return {
        "min": _rounded(min(parsed)),
        "max": _rounded(max(parsed)),
        "mean": _rounded(sum(parsed) / len(parsed)),
        "gate_zero_count": sum(value <= 0.01 for value in parsed),
        "gate_one_count": sum(value >= 0.99 for value in parsed),
    }


def score_spread_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    spreads = [
        _optional_float(_mapping(row.get("model_scores_hidden_during_review")).get("spread"))
        for row in rows
    ]
    parsed = [float(value) for value in spreads if value is not None]
    if not parsed:
        return {}
    return {
        "min": _rounded(min(parsed)),
        "max": _rounded(max(parsed)),
        "mean": _rounded(sum(parsed) / len(parsed)),
    }


def gate_value(row: MatrixRow, context: ScoreContext) -> float:
    return score_value(context.stitch_gate, row.index)


def score_spread(row: MatrixRow, context: ScoreContext) -> float:
    values = (
        score_value(context.v1, row.index),
        score_value(context.cap, row.index),
        score_value(context.stitch, row.index),
    )
    return max(values) - min(values)


def score_value(values: object, index: int) -> float:
    value = float(np.asarray(values, dtype=np.float32)[index])
    return 0.0 if not np.isfinite(value) else value


def part_value(parts: Mapping[str, object], name: str, index: int) -> float:
    value = float(np.asarray(parts[name], dtype=np.float32)[index])
    return 0.0 if not np.isfinite(value) else value


def value_at(values: object, index: int) -> float | None:
    value = float(np.asarray(values, dtype=np.float32)[index])
    return None if not np.isfinite(value) else value


def score_band(value: float) -> int:
    return min(9, max(0, int(value * 10.0)))


def none_as_large(value: float | None) -> float:
    return 1_000_000_000.0 if value is None else float(value)


def row_review_id(index: int) -> str:
    return f"sv-{index:05d}"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    summary = _mapping(report.get("summary"))
    lines = [
        "# en-ja Stitch Validation Pack",
        "",
        "Status: generated sidecar review scaffold",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "Use the blind review Markdown for labeling. This diagnostic report exposes model scores.",
        "",
        "## Inputs",
        "",
        f"- v1 candidate: `{_escape(inputs.get('v1_candidate_id'))}`",
        f"- ordinary-cap candidate: `{_escape(inputs.get('cap_candidate_id'))}`",
        f"- stitch candidate: `{_escape(inputs.get('stitch_candidate_id'))}`",
        f"- normal-vocab candidate pool: `{_escape(inputs.get('normal_vocab_candidate_pool_count'))}`",
        f"- blocked labels: `{_escape(inputs.get('blocked_label_count'))}`",
        f"- selected rows: `{_escape(summary.get('selected_count'))}`",
        "",
        "## Bucket Counts",
        "",
        "| Bucket | Count | Meaning |",
        "| --- | ---: | --- |",
    ]
    counts = _mapping(summary.get("bucket_counts"))
    for bucket, description in BUCKET_SPECS:
        lines.append(
            f"| `{_escape(bucket)}` | {_escape(counts.get(bucket))} | {_escape(description)} |"
        )
    lines.extend(["", "## Diagnostic Rows", ""])
    for bucket, _description in BUCKET_SPECS:
        bucket_rows = [
            row
            for row in report.get("selected_rows", ())
            if isinstance(row, Mapping) and row.get("review_bucket") == bucket
        ]
        lines.extend(bucket_markdown(bucket, bucket_rows))
    return "\n".join(lines).rstrip() + "\n"


def bucket_markdown(bucket: str, rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        f"### `{_escape(bucket)}`",
        "",
        "| # | Label | v1 | cap | stitch | gate | source signals |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for index, row in enumerate(rows, start=1):
        scores = _mapping(row.get("model_scores_hidden_during_review"))
        gates = _mapping(row.get("source_gate_signals"))
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _escape(str(row.get("label") or "")),
                    cell(scores.get("v1")),
                    cell(scores.get("ordinary_cap")),
                    cell(scores.get("stitch")),
                    cell(gates.get("stitch_gate")),
                    _escape(compact_gate_signals(gates)),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def compact_gate_signals(gates: Mapping[str, object]) -> str:
    keys = (
        "ped_conf",
        "ordinary_gate_pedagogical",
        "ordinary_gate_mean",
        "ordinary_gate_frequency",
        "ordinary_gate_priority",
        "tail_floor_guard",
    )
    return "; ".join(
        f"{key}={gates[key]}"
        for key in keys
        if key in gates and gates[key] not in (None, "", 0, 0.0)
    )


def cell(value: object) -> str:
    return "" if value is None else str(value)


def render_blind_review_markdown(report: Mapping[str, object]) -> str:
    rows = [row for row in report.get("selected_rows", ()) if isinstance(row, Mapping)]
    lines = [
        "# en-ja stitch validation blind review",
        "",
        "Assign `expected_difficulty` on the 0.00-1.00 learner-difficulty scale. "
        "Use `treatment` for decisions such as `vocab`, `topic_only`, `omit`, or `unsure`.",
        "",
        "Do not consult the diagnostic JSON/Markdown while assigning these labels; "
        "those files contain model scores for later evaluation.",
        "",
        "| # | lemma | reading | expected_difficulty | treatment | notes |",
        "| ---: | --- | --- | ---: | --- | --- |",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _escape(str(row.get("lemma") or "")),
                    _escape(str(row.get("reading") or "")),
                    "",
                    "",
                    "",
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
