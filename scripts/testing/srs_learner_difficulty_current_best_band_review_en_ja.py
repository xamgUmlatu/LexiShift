#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Callable, Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
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
    generate_candidates,
    raw_scores_for_candidate,
)


PAIR = "en-ja"
DEFAULT_COMBO_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_arbitration_same_surface_combo_en_ja_latest.json"
)
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
    / "srs_learner_difficulty_current_best_band_review_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_current_best_band_review_en_ja_latest.md"
)

FEATURE_COMPONENTS = {
    "freq": "frequency",
    "priority": "jmdict_priority",
    "jlpt": "jlpt_vocab_difficulty",
    "lesson": "lesson_vocab_difficulty",
    "wago": "wtype_wago_ease",
    "kango": "wtype_kango_risk",
    "gairaigo": "wtype_gairaigo_risk",
    "loan": "jmdict_loanword_source_risk",
    "domain": "jmdict_register_domain_risk",
    "common_domain": "common_register_domain_risk",
    "entity": "candidate_deprioritized_named_entity_risk",
    "name": "named_entity_risk",
    "acronym": "proper_acronym_entity_risk",
    "rare_read": "rare_non_standard_reading_risk",
    "rare_wago_read": "rare_wago_non_standard_reading_risk",
    "marked_reading": "jmdict_reading_form_marked_risk",
    "restricted_reading": "jmdict_reading_restricted_risk",
    "written": "written_form_burden",
    "max_written": "max_written_form_burden",
    "kanji_burden": "kanji_burden",
    "kango_mid": "kango_mid_signal",
    "kango_domain": "common_kango_register_domain_risk",
    "rare_wago_tail": "written_wago_tail_risk",
}
PART_FEATURES = {
    "same_risk": "same_surface_source_rank_gap_risk",
    "same_rare": "same_surface_rare_source_rank_gap_risk",
    "exact_common": "same_surface_exact_commonness",
    "exact_weak": "same_surface_exact_weakness",
    "same_pollution": "same_surface_pollution_risk",
    "same_rare_pollution": "same_surface_rare_pollution_risk",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a current-best en-ja learner-difficulty band and failure "
            "review pack from the latest source-arbitration combo winner."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--combo-json", type=Path, default=DEFAULT_COMBO_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--candidate-id", default=None)
    parser.add_argument(
        "--review-max-score",
        type=float,
        default=1.0,
        help=(
            "Only include predicted band samples and labeled review rows whose "
            "expected or observed score is at or below this value."
        ),
    )
    parser.add_argument("--sample-count", type=int, default=10)
    parser.add_argument("--detail-limit", type=int, default=18)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        combo_json_path=_resolve_path(args.combo_json),
        calibration_json_path=_resolve_path(args.calibration_json),
        holdout_json_path=_resolve_path(args.holdout_json),
        validation_json_path=_resolve_path(args.validation_json),
        candidate_id=args.candidate_id,
        review_max_score=min(1.0, max(0.05, float(args.review_max_score))),
        sample_count=max(1, int(args.sample_count)),
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
    combo_json_path: Path,
    calibration_json_path: Path,
    holdout_json_path: Path,
    validation_json_path: Path,
    candidate_id: str | None,
    review_max_score: float,
    sample_count: int,
    detail_limit: int,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    view = ComponentView.from_npz(component)
    parts = family_parts(view)
    features = feature_arrays(view, parts)
    combo_payload = load_json(combo_json_path)
    resolved_id = candidate_id or best_holdout_candidate_id(combo_payload)
    candidate = candidate_by_id(
        resolved_id,
        candidate_family=str(combo_payload["inputs"]["candidate_family"]),
    )
    raw = raw_scores_for_candidate(candidate, view, parts=parts)
    scores = np.asarray(
        _target_curve_normalize(raw, target_positions=view.target_positions),
        dtype=np.float32,
    )
    label_sets = {
        "calibration": labeled_rows(load_json(calibration_json_path), component, scores, features),
        "holdout": labeled_rows(load_json(holdout_json_path), component, scores, features),
        "stitch_validation": labeled_rows(
            load_json(validation_json_path), component, scores, features
        ),
    }
    review_label_sets = {
        name: [row for row in rows if row_in_review_scope(row, review_max_score=review_max_score)]
        for name, rows in label_sets.items()
    }
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Regenerate current-best band texture and mechanically expose "
                "remaining source-pattern failure candidates."
            ),
            "candidate_source": _repo_or_home_path(combo_json_path),
            "selection": "combo best_holdout_balanced unless --candidate-id is provided",
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "combo_json": _repo_or_home_path(combo_json_path),
            "calibration_json": _repo_or_home_path(calibration_json_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "validation_json": _repo_or_home_path(validation_json_path),
            "candidate_id": resolved_id,
            "population_count": int(len(scores)),
            "review_max_score": _rounded(review_max_score),
            "sample_count_per_band": sample_count,
            "detail_limit": detail_limit,
        },
        "candidate_summary": {
            "best_holdout_balanced": combo_payload["summary"].get("best_holdout_balanced"),
            "best_calibration_balanced": combo_payload["summary"].get("best_calibration_balanced"),
        },
        "band_samples": band_samples(
            scores,
            view=view,
            component=component,
            features=features,
            review_max_score=review_max_score,
            sample_count=sample_count,
        ),
        "labeled_error_summary": {
            name: labeled_error_summary(rows) for name, rows in review_label_sets.items()
        },
        "labeled_largest_errors": {
            name: sorted(rows, key=lambda row: -float(row["error"]))[:detail_limit]
            for name, rows in review_label_sets.items()
        },
        "labeled_pattern_counts": {
            name: pattern_counts(rows) for name, rows in review_label_sets.items()
        },
        "suspect_buckets": suspect_buckets(
            scores,
            view=view,
            component=component,
            features=features,
            review_max_score=review_max_score,
            limit=detail_limit,
        ),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "combo_json": combo_json_path,
                "calibration_json": calibration_json_path,
                "holdout_json": holdout_json_path,
                "validation_json": validation_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "current_best_band_review": Path(__file__),
                "source_arbitration": SCRIPT_DIR
                / "srs_learner_difficulty_source_arbitration_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def best_holdout_candidate_id(payload: Mapping[str, object]) -> str:
    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("Missing summary in combo JSON")
    row = summary.get("best_holdout_balanced")
    if not isinstance(row, Mapping):
        raise ValueError("Missing summary.best_holdout_balanced in combo JSON")
    candidate_id = str(row.get("candidate_id") or "")
    if not candidate_id:
        raise ValueError("Missing best-holdout candidate id")
    return candidate_id


def candidate_by_id(candidate_id: str, *, candidate_family: str) -> object:
    for candidate in generate_candidates(candidate_family=candidate_family):
        if candidate.candidate_id == candidate_id:
            return candidate
    raise ValueError(f"Candidate not found in {candidate_family}: {candidate_id}")


def feature_arrays(
    view: ComponentView,
    parts: Mapping[str, object],
) -> dict[str, np.ndarray]:
    arrays = {
        label: np.asarray(view.value(component_name, fill=np.nan), dtype=np.float32)
        for label, component_name in FEATURE_COMPONENTS.items()
    }
    for label, part_name in PART_FEATURES.items():
        arrays[label] = np.asarray(parts[part_name], dtype=np.float32)
    return arrays


def component_lookup(component: object) -> dict[tuple[str, str], int]:
    lookup: dict[tuple[str, str], int] = {}
    for index, (lemma, reading) in enumerate(zip(component["lemmas"], component["readings"])):
        lookup.setdefault((str(lemma), str(reading)), index)
    return lookup


def labeled_rows(
    payload: Mapping[str, object],
    component: object,
    scores: np.ndarray,
    features: Mapping[str, np.ndarray],
) -> list[dict[str, object]]:
    lookup = component_lookup(component)
    rows: list[dict[str, object]] = []
    for source_row in payload.get("labels", ()):
        if not isinstance(source_row, Mapping):
            continue
        treatment = str(source_row.get("treatment") or "vocab")
        if treatment != "vocab":
            continue
        expected = optional_float(source_row.get("expected_learner_difficulty"))
        if expected is None:
            continue
        lemma = str(source_row.get("lemma") or "").strip()
        reading = str(source_row.get("expected_reading") or source_row.get("reading") or "").strip()
        index = lookup.get((lemma, reading))
        if index is None:
            continue
        observed = float(scores[index])
        row = row_summary(index, scores, component=component, features=features)
        row.update(
            {
                "expected": _rounded(expected),
                "observed": _rounded(observed),
                "error": _rounded(abs(observed - expected)),
                "direction": (
                    "too_low"
                    if observed < expected
                    else "too_high"
                    if observed > expected
                    else "exact"
                ),
                "source_label": f"{lemma}/{reading}" if reading else lemma,
            }
        )
        rows.append(row)
    return rows


def optional_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(parsed):
        return None
    return parsed


def row_in_review_scope(row: Mapping[str, object], *, review_max_score: float) -> bool:
    expected = optional_float(row.get("expected"))
    observed = optional_float(row.get("observed"))
    score = optional_float(row.get("score"))
    return any(
        value is not None and value <= review_max_score for value in (expected, observed, score)
    )


def row_summary(
    index: int,
    scores: np.ndarray,
    *,
    component: object,
    features: Mapping[str, np.ndarray],
) -> dict[str, object]:
    return {
        "lemma": str(component["lemmas"][index]),
        "reading": str(component["readings"][index]),
        "label": f"{component['lemmas'][index]}/{component['readings'][index]}",
        "score": _rounded(float(scores[index])),
        "frequency": _rounded(float(component["frequency_values"][index])),
        "core_rank": _rounded(
            float(component["core_ranks"][index])
            if np.isfinite(float(component["core_ranks"][index]))
            else None
        ),
        "candidate_state": str(component["candidate_states"][index]),
        "problem_class": str(component["problem_classes"][index]),
        **{
            key: _rounded(float(values[index])) if np.isfinite(float(values[index])) else None
            for key, values in features.items()
        },
    }


def band_samples(
    scores: np.ndarray,
    *,
    view: ComponentView,
    component: object,
    features: Mapping[str, np.ndarray],
    review_max_score: float,
    sample_count: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for band_index in range(20):
        start = band_index * 0.05
        end = (band_index + 1) * 0.05
        if start >= review_max_score:
            break
        band_end = min(end, review_max_score)
        if band_index == 19 or band_end >= review_max_score:
            mask = (scores >= start) & (scores <= band_end)
        else:
            mask = (scores >= start) & (scores < band_end)
        indices = np.flatnonzero(mask)
        band_label = f"{start:.2f}-{band_end:.2f}"
        if len(indices) == 0:
            rows.append({"band": band_label, "count": 0, "samples": []})
            continue
        ordered = indices[np.argsort(scores[indices], kind="stable")]
        offsets = np.linspace(
            0,
            len(ordered) - 1,
            num=min(sample_count, len(ordered)),
            dtype=int,
        )
        rows.append(
            {
                "band": band_label,
                "count": int(len(indices)),
                "samples": [
                    row_summary(
                        int(ordered[offset]),
                        scores,
                        component=component,
                        features=features,
                    )
                    for offset in offsets
                ],
            }
        )
    _ = view
    return rows


def labeled_error_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    errors = np.asarray([float(row["error"]) for row in rows], dtype=np.float32)
    if len(errors) == 0:
        return {"count": 0}
    return {
        "count": int(len(errors)),
        "mae": _rounded(float(errors.mean())),
        "p90_error": _rounded(float(np.quantile(errors, 0.9))),
        "max_error": _rounded(float(errors.max())),
        "gt_0.10": int((errors > 0.10).sum()),
        "gt_0.15": int((errors > 0.15).sum()),
        "gt_0.20": int((errors > 0.20).sum()),
        "too_low_gt_0.15": int(
            sum(
                1
                for row in rows
                if row.get("direction") == "too_low" and float(row["error"]) > 0.15
            )
        ),
        "too_high_gt_0.15": int(
            sum(
                1
                for row in rows
                if row.get("direction") == "too_high" and float(row["error"]) > 0.15
            )
        ),
    }


def pattern_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    severe = [row for row in rows if float(row["error"]) > 0.15]
    too_low = [row for row in severe if row.get("direction") == "too_low"]
    too_high = [row for row in severe if row.get("direction") == "too_high"]
    return {
        "severe_count": len(severe),
        "too_low": signal_pattern_counts(too_low),
        "too_high": signal_pattern_counts(too_high),
    }


def signal_pattern_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    predicates: dict[str, Callable[[Mapping[str, object]], bool]] = {
        "same_surface": lambda row: as_float(row.get("same_rare_pollution")) >= 0.5,
        "entity_or_name": lambda row: (
            as_float(row.get("entity")) >= 0.5
            or as_float(row.get("name")) >= 0.5
            or str(row.get("problem_class")) == "proper_noun"
            or str(row.get("candidate_state")) == "deprioritized_vocab"
        ),
        "acronym": lambda row: (
            as_float(row.get("acronym")) >= 0.5
            or str(row.get("problem_class")) == "acronym_or_code"
        ),
        "loan_or_gairaigo": lambda row: (
            as_float(row.get("gairaigo")) >= 0.5 or as_float(row.get("loan")) >= 0.5
        ),
        "domain_register": lambda row: (
            as_float(row.get("domain")) >= 0.5
            or as_float(row.get("common_domain")) >= 0.5
            or as_float(row.get("kango_domain")) >= 0.5
        ),
        "kango": lambda row: as_float(row.get("kango")) >= 0.5,
        "wago": lambda row: as_float(row.get("wago")) >= 0.5,
        "rare_reading": lambda row: (
            as_float(row.get("rare_read")) >= 0.5
            or as_float(row.get("rare_wago_read")) >= 0.5
            or as_float(row.get("marked_reading")) >= 0.5
            or as_float(row.get("restricted_reading")) >= 0.5
        ),
        "high_written": lambda row: as_float(row.get("max_written")) >= 0.65,
    }
    return {
        name: int(sum(1 for row in rows if predicate(row)))
        for name, predicate in predicates.items()
    }


def as_float(value: object) -> float:
    parsed = optional_float(value)
    return parsed if parsed is not None else 0.0


def suspect_buckets(
    scores: np.ndarray,
    *,
    view: ComponentView,
    component: object,
    features: Mapping[str, np.ndarray],
    review_max_score: float,
    limit: int,
) -> dict[str, object]:
    states = np.asarray(component["candidate_states"])
    classes = np.asarray(component["problem_classes"])
    buckets: dict[str, np.ndarray] = {
        "low_band_non_normal_or_deprioritized": (
            (scores < 0.50) & ((states != "normal_vocab") | (classes != "normal_vocab"))
        ),
        "low_band_same_surface_rare_reading": (
            (scores < 0.45) & (features["same_rare_pollution"] >= 0.5)
        ),
        "low_band_domain_or_loanword": (
            (scores < 0.55)
            & (
                (features["gairaigo"] >= 0.5)
                | (features["loan"] >= 0.5)
                | (features["domain"] >= 0.5)
                | (features["common_domain"] >= 0.5)
            )
        ),
        "low_band_common_kango": (
            (scores < 0.35)
            & (features["kango"] >= 0.5)
            & ((features["kango_mid"] >= 0.30) | (features["max_written"] >= 0.35))
        ),
        "high_band_easy_source_or_priority": (
            (scores >= 0.60)
            & (
                (features["priority"] <= 0.25)
                | (features["jlpt"] <= 0.35)
                | (features["lesson"] <= 0.35)
            )
        ),
        "high_band_low_burden_wago": (
            (scores >= 0.70) & (features["wago"] >= 0.5) & (features["max_written"] <= 0.55)
        ),
    }
    review_mask = scores <= review_max_score
    _ = view
    return {
        name: bucket_rows(
            mask & review_mask,
            scores,
            component=component,
            features=features,
            limit=limit,
        )
        for name, mask in buckets.items()
    }


def bucket_rows(
    mask: np.ndarray,
    scores: np.ndarray,
    *,
    component: object,
    features: Mapping[str, np.ndarray],
    limit: int,
) -> dict[str, object]:
    indices = np.flatnonzero(mask)
    if len(indices) == 0:
        return {"count": 0, "rows": []}
    ordered = indices[np.argsort(scores[indices], kind="stable")]
    if len(ordered) > limit:
        offsets = np.linspace(0, len(ordered) - 1, num=limit, dtype=int)
        selected = ordered[offsets]
    else:
        selected = ordered
    return {
        "count": int(len(indices)),
        "rows": [
            row_summary(int(index), scores, component=component, features=features)
            for index in selected
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = report["inputs"]
    lines = [
        "# en-ja Current Best Band Review",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Sweeps run: `{_escape(report.get('sweeps_run'))}`",
        f"- Candidate: `{_escape(inputs.get('candidate_id'))}`",
        f"- Population: `{_escape(inputs.get('population_count'))}`",
        f"- Review max score: `{_escape(inputs.get('review_max_score'))}`",
        "",
        "## Candidate Scores",
        "",
    ]
    lines.extend(candidate_score_table(report.get("candidate_summary")))
    lines.extend(["", "## Labeled Error Summary", ""])
    lines.extend(labeled_summary_table(report.get("labeled_error_summary")))
    lines.extend(["", "## Severe Error Pattern Counts", ""])
    lines.extend(pattern_count_markdown(report.get("labeled_pattern_counts")))
    lines.extend(["", "## Predicted Band Samples", ""])
    for band in list(report.get("band_samples", ())):
        lines.extend(band_markdown(band))
    lines.extend(["", "## Largest Labeled Errors", ""])
    for name, rows in dict(report.get("labeled_largest_errors", {})).items():
        lines.extend(labeled_error_rows_markdown(str(name), rows))
    lines.extend(["", "## Suspect Buckets", ""])
    for name, bucket in dict(report.get("suspect_buckets", {})).items():
        lines.extend(bucket_markdown(str(name), bucket))
    return "\n".join(lines) + "\n"


def candidate_score_table(summary: object) -> list[str]:
    if not isinstance(summary, Mapping):
        return ["No candidate summary available."]
    rows = []
    for label in ("best_holdout_balanced", "best_calibration_balanced"):
        value = summary.get(label)
        if isinstance(value, Mapping):
            rows.append(
                {
                    "view": label,
                    "candidate": value.get("candidate_id"),
                    "cal": value.get("calibration_scores", {}).get("balanced_score")
                    if isinstance(value.get("calibration_scores"), Mapping)
                    else value.get("calibration_balanced"),
                    "hold": value.get("holdout_scores", {}).get("balanced_score")
                    if isinstance(value.get("holdout_scores"), Mapping)
                    else value.get("holdout_balanced"),
                    "pair": value.get("holdout_scores", {}).get("pairwise_order_score")
                    if isinstance(value.get("holdout_scores"), Mapping)
                    else value.get("holdout_pairwise"),
                }
            )
    lines = [
        "| View | Candidate | Calibration balanced | Holdout balanced | Holdout pairwise |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{_escape(row['view'])}` | `{_escape(row['candidate'])}` | "
            f"{_escape(row['cal'])} | {_escape(row['hold'])} | {_escape(row['pair'])} |"
        )
    return lines


def labeled_summary_table(value: object) -> list[str]:
    lines = [
        "| Set | Count | MAE | P90 error | Max error | >0.15 | Too low >0.15 | Too high >0.15 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, row in dict(value or {}).items():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"| `{_escape(name)}` | {_escape(row.get('count'))} | "
            f"{_escape(row.get('mae'))} | {_escape(row.get('p90_error'))} | "
            f"{_escape(row.get('max_error'))} | {_escape(row.get('gt_0.15'))} | "
            f"{_escape(row.get('too_low_gt_0.15'))} | "
            f"{_escape(row.get('too_high_gt_0.15'))} |"
        )
    return lines


def pattern_count_markdown(value: object) -> list[str]:
    lines = []
    for name, row in dict(value or {}).items():
        if not isinstance(row, Mapping):
            continue
        lines.extend(["", f"### `{_escape(name)}`", ""])
        lines.append(f"- Severe rows: `{_escape(row.get('severe_count'))}`")
        for direction in ("too_low", "too_high"):
            counts = row.get(direction)
            if not isinstance(counts, Mapping):
                continue
            lines.extend(["", f"{direction}:", ""])
            lines.extend(["| Pattern | Count |", "| --- | ---: |"])
            for pattern, count in counts.items():
                lines.append(f"| `{_escape(pattern)}` | {count} |")
    return lines


def band_markdown(band: object) -> list[str]:
    if not isinstance(band, Mapping):
        return []
    lines = [
        f"### `{_escape(band.get('band'))}` rows `{_escape(band.get('count'))}`",
        "",
    ]
    rows = list(band.get("samples", ()))
    if not rows:
        return lines + ["No rows.", ""]
    lines.extend(row_table(rows, include_expected=False))
    return lines + [""]


def labeled_error_rows_markdown(name: str, rows: object) -> list[str]:
    lines = [f"### `{_escape(name)}`", ""]
    if not rows:
        return lines + ["No rows.", ""]
    lines.extend(row_table(rows, include_expected=True))
    return lines + [""]


def bucket_markdown(name: str, bucket: object) -> list[str]:
    if not isinstance(bucket, Mapping):
        return []
    lines = [
        f"### `{_escape(name)}` rows `{_escape(bucket.get('count'))}`",
        "",
    ]
    rows = bucket.get("rows")
    if not rows:
        return lines + ["No rows.", ""]
    lines.extend(row_table(rows, include_expected=False))
    return lines + [""]


def row_table(rows: object, *, include_expected: bool) -> list[str]:
    headers = [
        "Row",
        "Score",
        "Exp",
        "Err",
        "Dir",
        "State",
        "Class",
        "Rank",
        "Freq",
        "Kango",
        "Wago",
        "Gairaigo",
        "Domain",
        "Entity",
        "Acr",
        "SameRare",
        "ExactCommon",
        "MaxWritten",
    ]
    if not include_expected:
        headers = [h for h in headers if h not in {"Exp", "Err", "Dir"}]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" if index == 0 else "---:" for index in range(len(headers))) + " |",
    ]
    for row in list(rows):
        if not isinstance(row, Mapping):
            continue
        values = [
            f"`{_escape(row.get('label') or row.get('source_label'))}`",
            _escape(row.get("score") if row.get("score") is not None else row.get("observed")),
        ]
        if include_expected:
            values.extend(
                [
                    _escape(row.get("expected")),
                    _escape(row.get("error")),
                    f"`{_escape(row.get('direction'))}`",
                ]
            )
        values.extend(
            [
                f"`{_escape(row.get('candidate_state'))}`",
                f"`{_escape(row.get('problem_class'))}`",
                _escape(row.get("core_rank")),
                _escape(row.get("frequency")),
                _escape(row.get("kango")),
                _escape(row.get("wago")),
                _escape(row.get("gairaigo")),
                _escape(row.get("domain")),
                _escape(row.get("entity")),
                _escape(row.get("acronym")),
                _escape(row.get("same_rare_pollution")),
                _escape(row.get("exact_common")),
                _escape(row.get("max_written")),
            ]
        )
        lines.append("| " + " | ".join(values) + " |")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
