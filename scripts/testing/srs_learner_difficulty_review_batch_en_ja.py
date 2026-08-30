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

from srs_learner_difficulty_model_family_meta_search_en_ja import (  # noqa: E402
    _calibration_context,
    _candidate_raw_scores,
    _expert_from_json,
    _load_json,
    _mapping,
    _mapping_rows,
    _meta_from_row,
    _model_candidate_from_row,
    _raw_for_meta_candidate,
    _raw_scores_for_expert,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _signal_arrays,
    _split_context,
    _target_curve_normalize,
    _utc_now,
)


PAIR = "en-ja"
VOCAB_STATES = frozenset({"normal_vocab", "deprioritized_vocab"})
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_component_matrix_latest.npz"
)
DEFAULT_CALIBRATION_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_prototype_s010_calibration_matrix_latest.npz"
)
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_ja.json"
)
DEFAULT_FAMILY_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_search_en_ja_latest.json"
)
DEFAULT_META_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_meta_search_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_review_batch_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_review_batch_en_ja_latest.md"
)
DEFAULT_HOLDOUT_REVIEW_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_holdout_review_en_ja.md"
)
DEFAULT_ACTIVE_REVIEW_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_active_review_en_ja.md"
)

DISPLAY_SIGNALS = (
    "frequency",
    "jmdict_priority",
    "jmdict_kana_preferred_risk",
    "jmdict_non_vocab_risk",
    "jmnedict_name_risk",
    "kango_common_priority_risk",
    "kango_mid_signal",
    "kanji_curriculum_missing_risk",
    "max_written_form_burden",
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_obscure_written_risk",
    "rare_wago_tail_risk",
    "written_wago_tail_risk",
    "wtype_gairaigo_risk",
    "wtype_kango_risk",
    "wtype_proper_risk",
    "wtype_wago_ease",
)
ACTIVE_REVIEW_ORDER = (
    "model_disagreement",
    "rare_wago_tail",
    "common_kango_floor",
    "beginner_kanji_guard",
    "non_standard_reading",
    "proper_or_topic_boundary",
    "gairaigo_tail",
    "signal_conflict",
    "band_boundary",
)


@dataclass(frozen=True)
class MatrixRow:
    index: int
    identity_key: str
    lemma: str
    reading: str
    candidate_state: str
    problem_class: str
    core_rank: float | None
    current_value: float | None
    frequency_value: float | None
    target_curve_position: float | None
    signals: Mapping[str, float | None]

    @property
    def label_key(self) -> str:
        return f"{self.lemma}\t{self.reading}"

    @property
    def label(self) -> str:
        return f"{self.lemma}/{self.reading}" if self.reading else self.lemma

    @property
    def kanji(self) -> tuple[str, ...]:
        return tuple(_kanji_chars(self.lemma))


@dataclass(frozen=True)
class ModelPredictionContext:
    candidate_ids: tuple[str, ...]
    predictions: Mapping[str, object]
    spread: object


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate review-only en-ja learner-difficulty candidate batches "
            "before running another sweep."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--family-json", type=Path, default=DEFAULT_FAMILY_JSON)
    parser.add_argument("--meta-json", type=Path, default=DEFAULT_META_JSON)
    parser.add_argument(
        "--target-count",
        type=int,
        default=0,
        help=(
            "Candidates per review set. The default 0 uses the current numeric "
            "vocab calibration-label count."
        ),
    )
    parser.add_argument("--model-prediction-count", type=int, default=8)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--holdout-review-markdown-out",
        type=Path,
        default=DEFAULT_HOLDOUT_REVIEW_MARKDOWN_OUT,
    )
    parser.add_argument(
        "--active-review-markdown-out",
        type=Path,
        default=DEFAULT_ACTIVE_REVIEW_MARKDOWN_OUT,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        calibration_json_path=_resolve_path(args.calibration_json),
        family_json_path=_resolve_path(args.family_json),
        meta_json_path=_resolve_path(args.meta_json),
        target_count=int(args.target_count),
        model_prediction_count=max(0, int(args.model_prediction_count)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    holdout_review_markdown_out = _resolve_path(args.holdout_review_markdown_out)
    active_review_markdown_out = _resolve_path(args.active_review_markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    holdout_review_markdown_out.parent.mkdir(parents=True, exist_ok=True)
    active_review_markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    holdout_review_markdown_out.write_text(
        render_simple_review_markdown(
            report,
            rows_key="fresh_holdout_candidates",
            title="en-ja learner difficulty fresh holdout review",
            purpose=(
                "Independent second test-set scaffold. Fill only human-reviewed "
                "difficulty or treatment values; do not copy model scores from the "
                "diagnostic report."
            ),
        ),
        encoding="utf-8",
    )
    active_review_markdown_out.write_text(
        render_simple_review_markdown(
            report,
            rows_key="active_review_candidates",
            title="en-ja learner difficulty active review",
            purpose=(
                "Optional diagnostic pool for current uncertainty areas. Promote "
                "only rows that receive human-reviewed difficulty or treatment values."
            ),
        ),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    print(f"Wrote holdout review Markdown artifact to {holdout_review_markdown_out}")
    print(f"Wrote active review Markdown artifact to {active_review_markdown_out}")
    return 0


def build_report(
    *,
    component_matrix_path: Path,
    calibration_matrix_path: Path,
    calibration_json_path: Path,
    family_json_path: Path,
    meta_json_path: Path,
    target_count: int = 0,
    model_prediction_count: int = 8,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    rows = _matrix_rows(component)
    calibration = _load_json(calibration_json_path)
    calibration_rows = _mapping_rows(calibration.get("labels"))
    numeric_label_count = _numeric_vocab_label_count(calibration_rows)
    effective_target_count = target_count if target_count > 0 else numeric_label_count
    blocked_keys = _label_keys(calibration_rows)
    blocked_kanji = _label_kanji(calibration_rows)
    prediction_context, prediction_error = _load_model_prediction_context(
        component=component,
        calibration_matrix_path=calibration_matrix_path,
        family_json_path=family_json_path,
        meta_json_path=meta_json_path,
        model_prediction_count=model_prediction_count,
    )
    active_candidates = _select_active_review_candidates(
        rows,
        target_count=effective_target_count,
        blocked_keys=blocked_keys,
        prediction_context=prediction_context,
    )
    active_kanji = {kanji for row in active_candidates for kanji in row["kanji"]}
    holdout_candidates = _select_holdout_candidates(
        rows,
        target_count=effective_target_count,
        blocked_keys=blocked_keys | {str(row["label_key"]) for row in active_candidates},
        blocked_kanji=blocked_kanji | active_kanji,
        prediction_context=prediction_context,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Review-only extension plan for learner-difficulty calibration. "
                "Rows are candidates for human review and are not consumed by "
                "sweeps until promoted into an accepted calibration file."
            ),
            "active_review": (
                "Targets current uncertainty: model disagreement, rare wago tails, "
                "common kango floors, beginner kanji guards, non-standard readings, "
                "proper/topic boundaries, gairaigo tails, signal conflict, and band boundaries."
            ),
            "fresh_holdout": (
                "Same candidate count as the active review set, restricted to rows "
                "whose kanji do not overlap current calibration labels or active-review candidates."
            ),
            "target_count_source": (
                "explicit_cli"
                if target_count > 0
                else "current_numeric_vocab_calibration_label_count"
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "calibration_json": _repo_or_home_path(calibration_json_path),
            "family_json": _repo_or_home_path(family_json_path),
            "meta_json": _repo_or_home_path(meta_json_path),
            "normalization_population_count": len(rows),
            "current_calibration_label_count": len(calibration_rows),
            "current_numeric_vocab_label_count": numeric_label_count,
            "target_count_per_set": effective_target_count,
            "model_prediction_count_requested": model_prediction_count,
        },
        "model_prediction_context": {
            "available": prediction_context is not None,
            "candidate_ids": list(prediction_context.candidate_ids)
            if prediction_context is not None
            else [],
            "error": prediction_error,
        },
        "counts": {
            "active_review_candidates": len(active_candidates),
            "fresh_holdout_candidates": len(holdout_candidates),
            "fresh_holdout_unique_kanji": len(
                {kanji for row in holdout_candidates for kanji in row["kanji"]}
            ),
        },
        "selection_warnings": _selection_warnings(
            target_count=effective_target_count,
            active_candidates=active_candidates,
            holdout_candidates=holdout_candidates,
        ),
        "active_review_candidates": active_candidates,
        "fresh_holdout_candidates": holdout_candidates,
    }


def _matrix_rows(component: object) -> list[MatrixRow]:
    names = [str(value) for value in component["component_names"]]
    name_to_index = {name: index for index, name in enumerate(names)}
    values = np.asarray(component["component_values"], dtype=np.float32)
    present = np.asarray(component["component_present"], dtype=bool)
    identity_keys = [str(value) for value in component["candidate_identity_keys"]]
    lemmas = [str(value) for value in component["lemmas"]]
    readings = [str(value) for value in component["readings"]]
    candidate_states = [str(value) for value in component["candidate_states"]]
    problem_classes = [str(value) for value in component["problem_classes"]]
    core_ranks = np.asarray(component["core_ranks"], dtype=np.float32)
    current_values = np.asarray(component["current_values"], dtype=np.float32)
    frequency_values = np.asarray(component["frequency_values"], dtype=np.float32)
    target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
    row_count = len(identity_keys)
    rows: list[MatrixRow] = []
    for index in range(row_count):
        signals: dict[str, float | None] = {}
        for name in DISPLAY_SIGNALS:
            column = name_to_index.get(name)
            signals[name] = (
                _float_or_none(values[index, column])
                if column is not None and bool(present[index, column])
                else None
            )
        rows.append(
            MatrixRow(
                index=index,
                identity_key=identity_keys[index],
                lemma=lemmas[index],
                reading=readings[index],
                candidate_state=candidate_states[index],
                problem_class=problem_classes[index],
                core_rank=_float_or_none(core_ranks[index]),
                current_value=_float_or_none(current_values[index]),
                frequency_value=_float_or_none(frequency_values[index]),
                target_curve_position=_float_or_none(target_positions[index]),
                signals=signals,
            )
        )
    return rows


def _load_model_prediction_context(
    *,
    component: object,
    calibration_matrix_path: Path,
    family_json_path: Path,
    meta_json_path: Path,
    model_prediction_count: int,
) -> tuple[ModelPredictionContext | None, str]:
    if model_prediction_count <= 0:
        return None, ""
    if not calibration_matrix_path.exists():
        return None, f"missing calibration matrix: {_repo_or_home_path(calibration_matrix_path)}"
    if not family_json_path.exists():
        return None, f"missing family json: {_repo_or_home_path(family_json_path)}"
    if not meta_json_path.exists():
        return None, f"missing meta json: {_repo_or_home_path(meta_json_path)}"
    try:
        family_report = _load_json(family_json_path)
        meta_report = _load_json(meta_json_path)
        meta_rows = _selected_meta_rows(meta_report, limit=model_prediction_count)
        meta_candidates = [_meta_from_row(row) for row in meta_rows]
        required_family_ids = {
            expert_id for candidate in meta_candidates for expert_id in candidate.expert_ids
        }
        family_by_id = {
            candidate.candidate_id: candidate
            for candidate in (
                _model_candidate_from_row(row)
                for row in _mapping_rows(family_report.get("exact_top"))
            )
        }
        missing = sorted(required_family_ids - set(family_by_id))
        if missing:
            return None, f"missing family candidates: {', '.join(missing[:5])}"
        experts = [
            _expert_from_json(row) for row in _mapping_rows(family_report.get("expert_pool"))
        ]
        raw_by_expert = {
            expert.variant_id: _raw_scores_for_expert(expert, component) for expert in experts
        }
        signal_arrays = _signal_arrays(component)
        raw_by_family_candidate = {
            candidate_id: _candidate_raw_scores(
                family_by_id[candidate_id],
                raw_by_expert=raw_by_expert,
                signal_arrays=signal_arrays,
            )
            for candidate_id in required_family_ids
        }
        calibration = np.load(calibration_matrix_path)
        calibration_context = _calibration_context(calibration, component)
        split_context = _split_context(component, calibration_context)
        target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
        predictions: dict[str, object] = {}
        for candidate in meta_candidates:
            raw, _leaf_ids = _raw_for_meta_candidate(
                candidate,
                raw_by_family_candidate=raw_by_family_candidate,
                split_context=split_context,
            )
            predictions[candidate.candidate_id] = _target_curve_normalize(
                raw,
                target_positions=target_positions,
            )
        if not predictions:
            return None, "no selected meta candidates"
        matrix = np.vstack(
            [np.asarray(values, dtype=np.float32) for values in predictions.values()]
        )
        spread = np.nanmax(matrix, axis=0) - np.nanmin(matrix, axis=0)
        return (
            ModelPredictionContext(
                candidate_ids=tuple(predictions),
                predictions=predictions,
                spread=spread.astype(np.float32),
            ),
            "",
        )
    except Exception as exc:  # pragma: no cover - defensive report path
        return None, f"{type(exc).__name__}: {exc}"


def _selected_meta_rows(report: Mapping[str, object], *, limit: int) -> list[Mapping[str, object]]:
    rows: list[Mapping[str, object]] = []
    seen: set[str] = set()

    def add(row: Mapping[str, object]) -> None:
        candidate_id = str(row.get("candidate_id") or "")
        if candidate_id and candidate_id not in seen and len(rows) < limit:
            rows.append(row)
            seen.add(candidate_id)

    for row in _mapping_rows(report.get("constrained_top")):
        add(row)
    for row in _mapping_rows(report.get("exact_top")):
        add(row)
    for leaderboard in _mapping(report.get("leaderboards")).values():
        for row in _mapping_rows(leaderboard):
            add(row)
    return rows[:limit]


def _select_active_review_candidates(
    rows: Sequence[MatrixRow],
    *,
    target_count: int,
    blocked_keys: set[str],
    prediction_context: ModelPredictionContext | None,
) -> list[dict[str, object]]:
    candidates: dict[str, list[tuple[float, MatrixRow, tuple[str, ...]]]] = {
        bucket: [] for bucket in ACTIVE_REVIEW_ORDER
    }
    for row in rows:
        if row.label_key in blocked_keys or row.candidate_state not in VOCAB_STATES:
            continue
        reasons = _active_review_reasons(row, prediction_context=prediction_context)
        for reason, score in reasons.items():
            if reason in candidates and score > 0.0:
                candidates[reason].append((score, row, tuple(sorted(reasons))))
    for bucket, bucket_rows in candidates.items():
        candidates[bucket] = sorted(
            bucket_rows,
            key=lambda item: (
                item[0],
                _model_spread(item[1], prediction_context),
                -(_none_as_large(item[1].core_rank)),
            ),
            reverse=True,
        )
    selected: list[dict[str, object]] = []
    seen: set[str] = set()
    bucket_index = 0
    while len(selected) < target_count and any(candidates.values()):
        bucket = ACTIVE_REVIEW_ORDER[bucket_index % len(ACTIVE_REVIEW_ORDER)]
        bucket_index += 1
        while candidates[bucket]:
            _score, row, reasons = candidates[bucket].pop(0)
            if row.label_key in seen:
                continue
            selected.append(
                _candidate_json(
                    row,
                    review_set="active_review",
                    review_bucket=bucket,
                    review_reasons=reasons,
                    prediction_context=prediction_context,
                )
            )
            seen.add(row.label_key)
            break
    return selected


def _select_holdout_candidates(
    rows: Sequence[MatrixRow],
    *,
    target_count: int,
    blocked_keys: set[str],
    blocked_kanji: set[str],
    prediction_context: ModelPredictionContext | None,
) -> list[dict[str, object]]:
    usable = [
        row
        for row in rows
        if row.label_key not in blocked_keys
        and row.candidate_state == "normal_vocab"
        and row.problem_class == "normal_vocab"
        and row.kanji
        and not set(row.kanji) & blocked_kanji
    ]
    quotas = _band_quotas(target_count, band_count=20)
    selected: list[dict[str, object]] = []
    seen: set[str] = set()
    used_kanji = set(blocked_kanji)
    bands = _rows_by_band(usable, band_count=20)
    for band_index, quota in enumerate(quotas):
        for row in _rank_holdout_band(bands.get(band_index, ()), band_index=band_index):
            if quota <= 0:
                break
            if row.label_key in seen or set(row.kanji) & used_kanji:
                continue
            selected.append(
                _candidate_json(
                    row,
                    review_set="fresh_holdout",
                    review_bucket=f"band_{band_index:02d}",
                    review_reasons=("fresh_disjoint_kanji_holdout",),
                    prediction_context=prediction_context,
                )
            )
            seen.add(row.label_key)
            used_kanji.update(row.kanji)
            quota -= 1
    if len(selected) < target_count:
        for row in sorted(
            usable,
            key=lambda item: (
                _model_spread(item, prediction_context),
                -(_none_as_large(item.core_rank)),
            ),
            reverse=True,
        ):
            if len(selected) >= target_count:
                break
            if row.label_key in seen or set(row.kanji) & used_kanji:
                continue
            selected.append(
                _candidate_json(
                    row,
                    review_set="fresh_holdout",
                    review_bucket="backfill_disjoint_kanji",
                    review_reasons=("fresh_disjoint_kanji_holdout", "quota_backfill"),
                    prediction_context=prediction_context,
                )
            )
            seen.add(row.label_key)
            used_kanji.update(row.kanji)
    return selected[:target_count]


def _active_review_reasons(
    row: MatrixRow,
    *,
    prediction_context: ModelPredictionContext | None,
) -> dict[str, float]:
    frequency = _signal(row, "frequency")
    priority = _signal(row, "jmdict_priority")
    max_burden = _signal(row, "max_written_form_burden")
    rare_wago_tail = max(
        _signal(row, "rare_wago_tail_risk"),
        _signal(row, "written_wago_tail_risk"),
        _signal(row, "rare_wago_obscure_written_risk"),
    )
    common_kango = max(
        _signal(row, "kango_mid_signal"),
        _signal(row, "kango_common_priority_risk"),
    )
    non_standard = max(
        _signal(row, "non_standard_reading_risk"),
        _signal(row, "rare_non_standard_reading_risk"),
    )
    reasons: dict[str, float] = {}
    spread = _model_spread(row, prediction_context)
    if spread >= 0.08:
        reasons["model_disagreement"] = min(1.0, spread * 3.0)
    if rare_wago_tail >= 0.20:
        reasons["rare_wago_tail"] = rare_wago_tail
    if common_kango >= 0.20 and frequency <= 0.75:
        reasons["common_kango_floor"] = (common_kango * 0.7) + ((1.0 - frequency) * 0.3)
    if priority >= 0.5 and max_burden >= 0.35 and frequency <= 0.55:
        reasons["beginner_kanji_guard"] = (
            (priority * 0.4) + (max_burden * 0.4) + ((1.0 - frequency) * 0.2)
        )
    if non_standard >= 0.20:
        reasons["non_standard_reading"] = non_standard
    if row.candidate_state == "deprioritized_vocab" or row.problem_class == "proper_noun":
        reasons["proper_or_topic_boundary"] = max(0.2, _signal(row, "wtype_proper_risk"))
    if _signal(row, "wtype_gairaigo_risk") >= 0.5 and frequency >= 0.55:
        reasons["gairaigo_tail"] = max(0.2, frequency)
    conflict = abs(max_burden - frequency)
    if conflict >= 0.35:
        reasons["signal_conflict"] = conflict
    if _band_boundary_distance(row.target_curve_position) <= 0.006:
        reasons["band_boundary"] = 0.25 + (
            0.006 - _band_boundary_distance(row.target_curve_position)
        )
    return reasons


def _candidate_json(
    row: MatrixRow,
    *,
    review_set: str,
    review_bucket: str,
    review_reasons: Sequence[str],
    prediction_context: ModelPredictionContext | None,
) -> dict[str, object]:
    return {
        "review_set": review_set,
        "review_bucket": review_bucket,
        "review_reasons": list(review_reasons),
        "candidate_identity_key": row.identity_key,
        "label_key": row.label_key,
        "lemma": row.lemma,
        "reading": row.reading,
        "label": row.label,
        "kanji": list(row.kanji),
        "candidate_state": row.candidate_state,
        "problem_class": row.problem_class,
        "core_rank": _rounded(row.core_rank),
        "target_curve_position": _rounded(row.target_curve_position),
        "current_value": _rounded(row.current_value),
        "frequency_value": _rounded(row.frequency_value),
        "signals": {
            name: _rounded(value)
            for name, value in row.signals.items()
            if value is not None and (name == "frequency" or abs(float(value)) > 1e-9)
        },
        "model_predictions": _model_prediction_json(row, prediction_context),
        "review_prompt": _review_prompt(review_set, review_bucket),
    }


def _model_prediction_json(
    row: MatrixRow,
    prediction_context: ModelPredictionContext | None,
) -> dict[str, object]:
    if prediction_context is None:
        return {"available": False}
    values = [
        {
            "candidate_id": candidate_id,
            "difficulty": _rounded(
                np.asarray(prediction_context.predictions[candidate_id])[row.index]
            ),
        }
        for candidate_id in prediction_context.candidate_ids[:4]
    ]
    return {
        "available": True,
        "spread": _rounded(_model_spread(row, prediction_context)),
        "sampled_candidates": values,
    }


def _review_prompt(review_set: str, review_bucket: str) -> str:
    if review_set == "fresh_holdout":
        return "Assign an independent target difficulty or mark omit; do not use it in sweeps until accepted."
    prompts = {
        "model_disagreement": "Resolve which model family is closer by assigning a target difficulty or pairwise anchors.",
        "rare_wago_tail": "Decide whether this is truly advanced written/vocabulary material or a common learner word.",
        "common_kango_floor": "Check whether the kango/commonness signals should pull this down.",
        "beginner_kanji_guard": "Check whether kanji form burden is overrating a core beginner word.",
        "non_standard_reading": "Decide whether the reading makes this harder than the lemma alone suggests.",
        "proper_or_topic_boundary": "Decide admit, topic-sensitive admit, or omit/deprioritize.",
        "gairaigo_tail": "Check whether katakana/gairaigo rarity is real difficulty or corpus sparsity.",
        "signal_conflict": "Resolve conflicting source signals.",
        "band_boundary": "Use as a band-edge calibration point.",
    }
    return prompts.get(review_bucket, "Review and assign a target difficulty or omit state.")


def _rows_by_band(rows: Sequence[MatrixRow], *, band_count: int) -> dict[int, list[MatrixRow]]:
    bands: dict[int, list[MatrixRow]] = {index: [] for index in range(band_count)}
    for row in rows:
        band = min(
            band_count - 1,
            max(0, int(float(row.target_curve_position or 0.0) * band_count)),
        )
        bands[band].append(row)
    return bands


def _rank_holdout_band(rows: Sequence[MatrixRow], *, band_index: int) -> list[MatrixRow]:
    center = (band_index + 0.5) / 20.0
    return sorted(
        rows,
        key=lambda row: (
            abs(float(row.target_curve_position or 0.0) - center),
            _none_as_large(row.core_rank),
            row.label,
        ),
    )


def _band_quotas(target_count: int, *, band_count: int) -> list[int]:
    base, remainder = divmod(max(0, target_count), band_count)
    return [base + (1 if index < remainder else 0) for index in range(band_count)]


def _selection_warnings(
    *,
    target_count: int,
    active_candidates: Sequence[Mapping[str, object]],
    holdout_candidates: Sequence[Mapping[str, object]],
) -> list[str]:
    warnings: list[str] = []
    if len(active_candidates) < target_count:
        warnings.append(f"active review underfilled: {len(active_candidates)} of {target_count}")
    if len(holdout_candidates) < target_count:
        warnings.append(f"fresh holdout underfilled: {len(holdout_candidates)} of {target_count}")
    return warnings


def _numeric_vocab_label_count(labels: Sequence[Mapping[str, object]]) -> int:
    return sum(
        1
        for row in labels
        if str(row.get("expected_candidate_state") or "") in VOCAB_STATES
        and row.get("expected_learner_difficulty") is not None
    )


def _label_keys(labels: Sequence[Mapping[str, object]]) -> set[str]:
    keys: set[str] = set()
    for row in labels:
        lemma = str(row.get("lemma") or "").strip()
        reading = str(row.get("expected_reading") or row.get("reading") or "").strip()
        if lemma:
            keys.add(f"{lemma}\t{reading}")
    return keys


def _label_kanji(labels: Sequence[Mapping[str, object]]) -> set[str]:
    return {kanji for row in labels for kanji in _kanji_chars(str(row.get("lemma") or ""))}


def _kanji_chars(value: str) -> set[str]:
    return {
        char
        for char in value
        if ("\u3400" <= char <= "\u4dbf")
        or ("\u4e00" <= char <= "\u9fff")
        or ("\uf900" <= char <= "\ufaff")
    }


def _signal(row: MatrixRow, name: str) -> float:
    value = row.signals.get(name)
    return 0.0 if value is None else float(value)


def _model_spread(
    row: MatrixRow,
    prediction_context: ModelPredictionContext | None,
) -> float:
    if prediction_context is None:
        return 0.0
    value = np.asarray(prediction_context.spread, dtype=np.float32)[row.index]
    return 0.0 if not np.isfinite(value) else float(value)


def _band_boundary_distance(value: float | None) -> float:
    if value is None:
        return 1.0
    parsed = float(value)
    nearest = round(parsed / 0.05) * 0.05
    return abs(parsed - nearest)


def _none_as_large(value: float | None) -> float:
    return 1_000_000_000.0 if value is None else float(value)


def _float_or_none(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(parsed) else parsed


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    counts = _mapping(report.get("counts"))
    prediction = _mapping(report.get("model_prediction_context"))
    lines = [
        "# en-ja learner difficulty review batch",
        "",
        "This is review-only material. It is not an accepted calibration set and no sweeps were run to create it.",
        "",
        "## Summary",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Current numeric vocab labels: `{inputs.get('current_numeric_vocab_label_count')}`",
        f"- Target count per set: `{inputs.get('target_count_per_set')}`",
        f"- Active review candidates: `{counts.get('active_review_candidates')}`",
        f"- Fresh holdout candidates: `{counts.get('fresh_holdout_candidates')}`",
        f"- Fresh holdout unique kanji: `{counts.get('fresh_holdout_unique_kanji')}`",
        f"- Model predictions available: `{prediction.get('available')}`",
    ]
    if prediction.get("error"):
        lines.append(f"- Model prediction error: `{_escape(str(prediction.get('error')))}`")
    warnings = list(report.get("selection_warnings") or [])
    if warnings:
        lines.extend(["", "## Selection Warnings", ""])
        lines.extend(f"- {_escape(str(value))}" for value in warnings)
    lines.extend(
        [
            "",
            "## Active Review Candidates",
            "",
            _candidate_table(_mapping_rows(report.get("active_review_candidates"))),
            "",
            "## Fresh Holdout Candidates",
            "",
            _candidate_table(_mapping_rows(report.get("fresh_holdout_candidates"))),
            "",
        ]
    )
    return "\n".join(lines)


def render_simple_review_markdown(
    report: Mapping[str, object],
    *,
    rows_key: str,
    title: str,
    purpose: str,
) -> str:
    rows = _mapping_rows(report.get(rows_key))
    return "\n".join(
        [
            f"# {title}",
            "",
            purpose,
            "",
            "Fill `expected_difficulty` with a `0.00`-`1.00` value when the row "
            "should be admitted as vocabulary. Use `treatment` for non-vocab "
            "decisions such as `omit`, `topic_only`, `pattern`, or `unsure`.",
            "",
            _simple_review_table(rows),
            "",
        ]
    )


def _simple_review_table(rows: Sequence[Mapping[str, object]]) -> str:
    header = (
        "| # | lemma | reading | expected_difficulty | treatment | notes |\n"
        "|---:|---|---|---:|---|---|"
    )
    body = [
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
        for index, row in enumerate(rows, start=1)
    ]
    return "\n".join([header, *body])


def _candidate_table(rows: Sequence[Mapping[str, object]]) -> str:
    header = (
        "| # | lemma | reading | bucket | reasons | curve | model spread | state | signals |\n"
        "|---:|---|---|---|---|---:|---:|---|---|"
    )
    body: list[str] = []
    for index, row in enumerate(rows, start=1):
        signals = _compact_signals(_mapping(row.get("signals")))
        body.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _escape(str(row.get("lemma") or "")),
                    _escape(str(row.get("reading") or "")),
                    _escape(str(row.get("review_bucket") or "")),
                    _escape(", ".join(str(value) for value in row.get("review_reasons") or ())),
                    str(row.get("target_curve_position") or ""),
                    str(_mapping(row.get("model_predictions")).get("spread") or ""),
                    _escape(str(row.get("candidate_state") or "")),
                    _escape(signals),
                ]
            )
            + " |"
        )
    return "\n".join([header, *body])


def _compact_signals(signals: Mapping[str, object]) -> str:
    keys = (
        "frequency",
        "jmdict_priority",
        "kango_mid_signal",
        "rare_wago_tail_risk",
        "written_wago_tail_risk",
        "max_written_form_burden",
        "non_standard_reading_risk",
        "wtype_kango_risk",
        "wtype_wago_ease",
    )
    cells = [
        f"{key}={signals[key]}"
        for key in keys
        if key in signals and signals[key] not in (None, 0, 0.0)
    ]
    return "; ".join(cells)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
