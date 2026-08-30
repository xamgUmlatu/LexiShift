#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from build_aozora_lexical_context_features_ja import (  # noqa: E402
    _iter_token_rows as _iter_aozora_token_rows,
    _token_summary as _aozora_token_summary,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _optional_float,
    _repo_or_home_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    _view_with_target_curve_override,
    family_parts,
    generate_candidates,
    normalized_scores_for_candidate,
)


PAIR = "en-ja"
DATA_ROOT = Path.home() / "Library" / "Application Support" / "LexiShift" / "LexiShift"
DEFAULT_SOURCE_ARBITRATION_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_arbitration_base_family_rescue_refine_warp_p60_g155_en_ja_latest.json"
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
DEFAULT_AOZORA_SQLITE = DATA_ROOT / "frequency_packs" / "freq-ja-aozora-word" / "main.sqlite"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_context_review_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_context_review_en_ja_latest.md"
)
DEFAULT_FOCUS_ROWS = (
    ("宿る", "やどる"),
    ("黒潮", "くろしお"),
    ("亡骸", "なきがら"),
    ("而して", "しこうして"),
    ("郡", "ぐん"),
    ("ゲバ棒", "げばぼう"),
    ("サビ残", "さびざん"),
    ("辛い", "つらい"),
    ("彼奴", "きゃつ"),
    ("ジョバンニ", "じょばんに"),
    ("氣", ""),
    ("饗する", "きょうする"),
    ("黒丸", "くろまる"),
    ("レバー", "ればー"),
    ("耐え凌ぐ", "たえしのぐ"),
)
FEATURE_FIELDS = (
    "accessibility_weighted_mean",
    "accessible_work_exposure",
    "hard_work_exposure",
    "modern_orthography_exposure",
    "old_orthography_exposure",
    "child_or_youth_exposure",
    "modern_child_exposure",
    "modern_child_accessible_context",
    "old_literary_risk_context",
    "child_old_risk_context",
    "context_confidence",
    "context_coverage",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an en-ja learner-difficulty review pack joining current model "
            "errors with Aozora lexical-context features."
        )
    )
    parser.add_argument(
        "--source-arbitration-json", type=Path, default=DEFAULT_SOURCE_ARBITRATION_JSON
    )
    parser.add_argument("--component-matrix", type=Path, default=None)
    parser.add_argument("--candidate-id", default="")
    parser.add_argument("--candidate-family", default="")
    parser.add_argument(
        "--target-curve-override",
        choices=("component", "warp_p60_g155"),
        default="",
    )
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--aozora-sqlite", type=Path, default=DEFAULT_AOZORA_SQLITE)
    parser.add_argument(
        "--focus",
        action="append",
        default=[],
        help=(
            "Extra focus row in lemma[/reading] form. Reading should be hiragana/katakana "
            "when supplied. May be repeated."
        ),
    )
    parser.add_argument("--largest-error-limit", type=int, default=60)
    parser.add_argument("--group-limit", type=int, default=30)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        source_arbitration_json=_resolve_path(args.source_arbitration_json),
        component_matrix_path=(
            _resolve_path(args.component_matrix) if args.component_matrix else None
        ),
        candidate_id=str(args.candidate_id or ""),
        candidate_family=str(args.candidate_family or ""),
        target_curve_override=str(args.target_curve_override or ""),
        calibration_json=_resolve_path(args.calibration_json),
        holdout_json=_resolve_path(args.holdout_json),
        validation_json=_resolve_path(args.validation_json),
        aozora_sqlite=_resolve_path(args.aozora_sqlite),
        extra_focus_rows=tuple(args.focus),
        largest_error_limit=max(1, int(args.largest_error_limit)),
        group_limit=max(1, int(args.group_limit)),
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
    source_arbitration_json: Path,
    component_matrix_path: Path | None,
    candidate_id: str,
    candidate_family: str,
    target_curve_override: str,
    calibration_json: Path,
    holdout_json: Path,
    validation_json: Path,
    aozora_sqlite: Path,
    extra_focus_rows: Sequence[str],
    largest_error_limit: int,
    group_limit: int,
) -> dict[str, Any]:
    source_report = _load_json(source_arbitration_json)
    selected = _selected_candidate_metadata(
        source_report,
        candidate_id=candidate_id,
        candidate_family=candidate_family,
        target_curve_override=target_curve_override,
        component_matrix_path=component_matrix_path,
    )
    component_matrix = _resolve_path(Path(str(selected["component_matrix"])))
    component = np.load(component_matrix)
    view = _view_with_target_curve_override(
        ComponentView.from_npz(component),
        target_curve_override=str(selected["target_curve_override"]),
    )
    candidates = generate_candidates(candidate_family=str(selected["candidate_family"]))
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    candidate = candidate_by_id.get(str(selected["candidate_id"]))
    if candidate is None:
        raise SystemExit(
            "Candidate id is not generated by candidate family: "
            f"{selected['candidate_id']} ({selected['candidate_family']})"
        )
    scores = np.asarray(
        normalized_scores_for_candidate(candidate, view, parts=family_parts(view)),
        dtype=np.float32,
    )
    score_rank = _score_ranks(scores)
    label_rows = _load_all_labels(
        calibration_json=calibration_json,
        holdout_json=holdout_json,
        validation_json=validation_json,
    )
    focus_specs = tuple(DEFAULT_FOCUS_ROWS) + tuple(
        _parse_focus_row(value) for value in extra_focus_rows
    )
    needed_terms = {row["lemma"] for row in label_rows if str(row.get("lemma") or "")} | {
        lemma for lemma, _reading in focus_specs if lemma
    }
    aozora_by_term = _load_aozora_rows(aozora_sqlite, terms=tuple(sorted(needed_terms)))
    component_lookup = _component_lookup(view=view, scores=scores, score_rank=score_rank)

    labeled_review_rows = [
        _review_row_for_label(
            row,
            component_lookup=component_lookup,
            aozora_by_term=aozora_by_term,
        )
        for row in label_rows
    ]
    focus_rows = _focus_rows(
        focus_specs,
        component_lookup=component_lookup,
        aozora_by_term=aozora_by_term,
    )
    numeric_rows = [
        row for row in labeled_review_rows if row.get("found") and row.get("expected") is not None
    ]
    summary = _summary(numeric_rows)
    largest_errors = sorted(
        numeric_rows,
        key=lambda row: float(row.get("absolute_error") or 0.0),
        reverse=True,
    )[:largest_error_limit]
    too_low_old_literary = sorted(
        [row for row in numeric_rows if _too_low_old_literary_candidate(row)],
        key=lambda row: (
            -_feature_value(row, "old_literary_risk_context"),
            -float(row.get("absolute_error") or 0.0),
        ),
    )[:group_limit]
    too_high_accessible = sorted(
        [row for row in numeric_rows if _too_high_accessible_candidate(row)],
        key=lambda row: (
            -max(
                _feature_value(row, "accessible_work_exposure"),
                _feature_value(row, "modern_child_accessible_context"),
            ),
            -float(row.get("absolute_error") or 0.0),
        ),
    )[:group_limit]
    missing_or_weak = sorted(
        [row for row in numeric_rows if _feature_value(row, "context_confidence") < 0.20],
        key=lambda row: float(row.get("absolute_error") or 0.0),
        reverse=True,
    )[:group_limit]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "model_behavior_changed": False,
        "method": {
            "purpose": (
                "Qualitative sidecar review pack: join current source-arbitration "
                "scores and reviewed labels with Aozora lexical-context features."
            ),
            "interpretation": (
                "Aozora features are explanatory candidates only. They are not wired "
                "into the accepted scorer by this artifact."
            ),
            "candidate_id": selected["candidate_id"],
            "candidate_family": selected["candidate_family"],
            "target_curve_override": selected["target_curve_override"],
            "feature_join": (
                "Aozora rows are matched by lemma as surface/base_form and, when "
                "available, exact reading after kana normalization. If exact reading "
                "has no Aozora match, all lemma rows are retained with fallback status."
            ),
        },
        "inputs": {
            "source_arbitration_json": _repo_or_home_path(source_arbitration_json),
            "component_matrix": _repo_or_home_path(component_matrix),
            "calibration_json": _repo_or_home_path(calibration_json),
            "holdout_json": _repo_or_home_path(holdout_json),
            "validation_json": _repo_or_home_path(validation_json),
            "aozora_sqlite": _repo_or_home_path(aozora_sqlite),
            "label_count": len(label_rows),
            "numeric_mapped_count": len(numeric_rows),
        },
        "summary": summary,
        "largest_errors": largest_errors,
        "potential_actionable_groups": {
            "too_low_with_old_literary_signal": too_low_old_literary,
            "too_high_with_accessible_signal": too_high_accessible,
            "missing_or_low_confidence_aozora": missing_or_weak,
        },
        "focus_rows": focus_rows,
        "all_labeled_rows": labeled_review_rows,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "source_arbitration_json": source_arbitration_json,
                "component_matrix": component_matrix,
                "calibration_json": calibration_json,
                "holdout_json": holdout_json,
                "validation_json": validation_json,
                "aozora_sqlite": aozora_sqlite,
            },
            code_paths={
                **_srs_difficulty_code_paths(),
                "source_arbitration": (
                    SCRIPT_DIR / "srs_learner_difficulty_source_arbitration_en_ja.py"
                ),
                "aozora_context_feature_builder": (
                    SCRIPT_DIR / "build_aozora_lexical_context_features_ja.py"
                ),
                "aozora_context_review": Path(__file__),
            },
            argv=sys.argv,
        ),
    }


def _selected_candidate_metadata(
    source_report: Mapping[str, Any],
    *,
    candidate_id: str,
    candidate_family: str,
    target_curve_override: str,
    component_matrix_path: Path | None,
) -> dict[str, str]:
    inputs = _mapping(source_report.get("inputs"))
    method = _mapping(source_report.get("method"))
    summary = _mapping(source_report.get("summary"))
    selected = _mapping(summary.get("best_holdout_balanced")) or _mapping(
        summary.get("best_calibration_balanced")
    )
    selected_id = candidate_id or str(selected.get("candidate_id") or "")
    if not selected_id:
        rows = _as_list(source_report.get("candidate_results"))
        if rows:
            selected_id = str(_mapping(rows[0]).get("candidate_id") or "")
    if not selected_id:
        raise SystemExit("Could not infer candidate id; pass --candidate-id.")
    selected_family = (
        candidate_family
        or str(inputs.get("candidate_family") or "")
        or str(method.get("candidate_family") or "")
    )
    if not selected_family:
        selected_family = str(_mapping(selected.get("params")).get("candidate_family") or "")
    if not selected_family:
        raise SystemExit("Could not infer candidate family; pass --candidate-family.")
    selected_curve = target_curve_override or str(
        method.get("target_curve_override") or "component"
    )
    matrix = component_matrix_path or Path(str(inputs.get("component_matrix") or ""))
    if not str(matrix):
        raise SystemExit("Could not infer component matrix; pass --component-matrix.")
    return {
        "candidate_id": selected_id,
        "candidate_family": selected_family,
        "target_curve_override": selected_curve,
        "component_matrix": str(matrix),
    }


def _load_all_labels(
    *, calibration_json: Path, holdout_json: Path, validation_json: Path
) -> list[dict[str, Any]]:
    rows = []
    seen: set[tuple[str, str, str]] = set()
    for dataset, path in (
        ("calibration", calibration_json),
        ("holdout", holdout_json),
        ("stitch_validation", validation_json),
    ):
        if not path.exists():
            continue
        payload = _load_json(path)
        for label in _as_list(payload.get("labels")):
            if not isinstance(label, Mapping):
                continue
            expected = _optional_float(label.get("expected_learner_difficulty"))
            if expected is None:
                continue
            lemma = str(label.get("lemma") or "").strip()
            reading = str(label.get("expected_reading") or label.get("reading") or "").strip()
            if not lemma:
                continue
            key = (dataset, lemma, reading)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "dataset": dataset,
                    "lemma": lemma,
                    "reading": reading,
                    "label": f"{lemma}/{reading}" if reading else lemma,
                    "expected": float(expected),
                    "expected_band": _review_difficulty_band(float(expected)),
                    "expected_candidate_state": str(label.get("expected_candidate_state") or ""),
                    "expected_problem_class": str(label.get("expected_problem_class") or ""),
                    "rationale": str(label.get("rationale") or label.get("notes") or ""),
                    "review_row_number": label.get("review_row_number"),
                }
            )
    return rows


def _component_lookup(
    *, view: ComponentView, scores: np.ndarray, score_rank: np.ndarray
) -> dict[str, Any]:
    exact: dict[tuple[str, str], dict[str, Any]] = {}
    by_lemma: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, (lemma, reading, identity, candidate_state) in enumerate(
        zip(view.lemmas, view.readings, view.identities, view.candidate_states)
    ):
        row = {
            "component_index": int(index),
            "lemma": str(lemma),
            "reading": str(reading),
            "label": f"{lemma}/{reading}" if str(reading) else str(lemma),
            "identity_key": str(identity),
            "candidate_state": str(candidate_state),
            "score": float(scores[index]),
            "score_rank": int(score_rank[index]),
        }
        exact[(row["lemma"], row["reading"])] = row
        by_lemma[row["lemma"]].append(row)
    for rows in by_lemma.values():
        rows.sort(key=lambda row: (float(row["score"]), str(row["reading"])))
    return {"exact": exact, "by_lemma": dict(by_lemma)}


def _review_row_for_label(
    label: Mapping[str, Any],
    *,
    component_lookup: Mapping[str, Any],
    aozora_by_term: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    lemma = str(label.get("lemma") or "")
    reading = str(label.get("reading") or "")
    component = _select_component(lemma, reading, component_lookup)
    score = _optional_float(component.get("score")) if component else None
    expected = _optional_float(label.get("expected"))
    delta = score - expected if score is not None and expected is not None else None
    features = _aggregate_aozora_features(lemma, reading, aozora_by_term.get(lemma, ()))
    row = {
        **dict(label),
        "found": bool(component),
        "component": component,
        "score": _rounded(score),
        "score_band": _review_difficulty_band(score) if score is not None else "",
        "signed_error": _rounded(delta),
        "absolute_error": _rounded(abs(delta)) if delta is not None else None,
        "direction": "too_high"
        if delta and delta > 0
        else "too_low"
        if delta and delta < 0
        else "match",
        "aozora": features,
        "interpretation": _interpret_row(delta, features),
    }
    return row


def _focus_rows(
    focus_specs: Sequence[tuple[str, str]],
    *,
    component_lookup: Mapping[str, Any],
    aozora_by_term: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    seen: set[tuple[str, str]] = set()
    for lemma, reading in focus_specs:
        if not lemma:
            continue
        key = (lemma, reading)
        if key in seen:
            continue
        seen.add(key)
        component = _select_component(lemma, reading, component_lookup)
        features = _aggregate_aozora_features(lemma, reading, aozora_by_term.get(lemma, ()))
        rows.append(
            {
                "lemma": lemma,
                "reading": reading,
                "label": f"{lemma}/{reading}" if reading else lemma,
                "found": bool(component),
                "component": component,
                "score": _rounded(component.get("score") if component else None),
                "score_band": _review_difficulty_band(component.get("score")) if component else "",
                "aozora": features,
                "interpretation": _interpret_row(None, features),
            }
        )
    return rows


def _select_component(
    lemma: str,
    reading: str,
    component_lookup: Mapping[str, Any],
) -> dict[str, Any]:
    exact = _mapping(component_lookup.get("exact"))
    by_lemma = _mapping(component_lookup.get("by_lemma"))
    if reading:
        row = exact.get((lemma, reading))
        if isinstance(row, Mapping):
            return dict(row)
    rows = by_lemma.get(lemma)
    if isinstance(rows, list) and rows:
        if reading:
            katakana = _kana_to_katakana(reading)
            for row in rows:
                if _kana_to_katakana(str(row.get("reading") or "")) == katakana:
                    return dict(row)
        return dict(rows[0])
    return {}


def _load_aozora_rows(
    sqlite_path: Path,
    *,
    terms: Sequence[str],
) -> dict[str, list[dict[str, Any]]]:
    if not sqlite_path.exists():
        return {}
    unique_terms = tuple(sorted({term for term in terms if term}))
    if not unique_terms:
        return {}
    rows_by_term: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        for row in _iter_aozora_token_rows(
            conn,
            surfaces=unique_terms,
            pos_major=(),
            min_token_count=1,
            limit=0,
        ):
            summary = _aozora_token_summary(row)
            payload = {
                "surface": str(row["surface"] or ""),
                "base_form": str(row["base_form"] or ""),
                "reading": str(row["reading"] or ""),
                "pos_major": str(row["pos_major"] or ""),
                "pos_sub1": str(row["pos_sub1"] or ""),
                "token_count": int(summary["token_count"]),
                "work_count": int(summary["work_count"]),
                "author_count": int(summary["author_count"]),
                **{field: float(summary[field]) for field in FEATURE_FIELDS},
            }
            if payload["surface"] in unique_terms:
                rows_by_term[payload["surface"]].append(payload)
            if payload["base_form"] in unique_terms:
                rows_by_term[payload["base_form"]].append(payload)
    for rows in rows_by_term.values():
        rows.sort(key=lambda row: (-(row.get("token_count") or 0), str(row.get("reading") or "")))
    return dict(rows_by_term)


def _aggregate_aozora_features(
    lemma: str,
    reading: str,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not rows:
        return {
            "match_status": "missing",
            "row_count": 0,
            "token_count": 0,
            "work_count_max": 0,
            "author_count_max": 0,
            "features": {},
            "top_rows": [],
        }
    target_reading = _kana_to_katakana(reading)
    exact_rows = [
        row
        for row in rows
        if target_reading and _kana_to_katakana(str(row.get("reading") or "")) == target_reading
    ]
    selected_rows = exact_rows if exact_rows else list(rows)
    weights = [max(0, int(_optional_float(row.get("token_count")) or 0)) for row in selected_rows]
    denominator = max(1, sum(weights))
    features = {}
    for field in FEATURE_FIELDS:
        if field == "context_confidence":
            features[field] = _rounded(
                max(_optional_float(row.get(field)) or 0.0 for row in selected_rows)
            )
            continue
        features[field] = _rounded(
            sum(
                ((_optional_float(row.get(field)) or 0.0) * weight)
                for row, weight in zip(selected_rows, weights)
            )
            / denominator
        )
    return {
        "match_status": "exact_reading" if exact_rows else "lemma_only_fallback",
        "row_count": len(selected_rows),
        "token_count": sum(weights),
        "work_count_max": max(
            int(_optional_float(row.get("work_count")) or 0) for row in selected_rows
        ),
        "author_count_max": max(
            int(_optional_float(row.get("author_count")) or 0) for row in selected_rows
        ),
        "features": features,
        "top_rows": [
            {
                "surface": row.get("surface"),
                "base_form": row.get("base_form"),
                "reading": row.get("reading"),
                "pos": f"{row.get('pos_major')}-{row.get('pos_sub1')}",
                "token_count": row.get("token_count"),
                "work_count": row.get("work_count"),
                "author_count": row.get("author_count"),
                "access": _rounded(row.get("accessibility_weighted_mean")),
                "accessible": _rounded(row.get("accessible_work_exposure")),
                "hard": _rounded(row.get("hard_work_exposure")),
                "old_risk": _rounded(row.get("old_literary_risk_context")),
                "modern_child": _rounded(row.get("modern_child_accessible_context")),
                "confidence": _rounded(row.get("context_confidence")),
            }
            for row in selected_rows[:6]
        ],
    }


def _summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    joined = [row for row in rows if _mapping(row.get("aozora")).get("match_status") != "missing"]
    correlations = {
        "underprediction_vs_old_literary_risk": _correlation(
            [_underprediction(row) for row in joined],
            [_feature_value(row, "old_literary_risk_context") for row in joined],
        ),
        "underprediction_vs_hard_exposure": _correlation(
            [_underprediction(row) for row in joined],
            [_feature_value(row, "hard_work_exposure") for row in joined],
        ),
        "overprediction_vs_accessible_exposure": _correlation(
            [_overprediction(row) for row in joined],
            [_feature_value(row, "accessible_work_exposure") for row in joined],
        ),
        "overprediction_vs_modern_child_accessible": _correlation(
            [_overprediction(row) for row in joined],
            [_feature_value(row, "modern_child_accessible_context") for row in joined],
        ),
    }
    return {
        "numeric_row_count": len(rows),
        "aozora_joined_count": len(joined),
        "aozora_missing_count": len(rows) - len(joined),
        "mae": _rounded(
            sum(float(row.get("absolute_error") or 0.0) for row in rows) / max(1, len(rows))
        ),
        "too_high_count": sum(1 for row in rows if str(row.get("direction")) == "too_high"),
        "too_low_count": sum(1 for row in rows if str(row.get("direction")) == "too_low"),
        "candidate_old_literary_fix_count": sum(
            1 for row in rows if _too_low_old_literary_candidate(row)
        ),
        "candidate_accessible_fix_count": sum(
            1 for row in rows if _too_high_accessible_candidate(row)
        ),
        "correlations": correlations,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = _mapping(report.get("summary"))
    method = _mapping(report.get("method"))
    lines = [
        "# en-ja Aozora Lexical Context Review",
        "",
        "## Summary",
        "",
        f"- Candidate: `{_escape(method.get('candidate_id'))}`",
        f"- Candidate family: `{_escape(method.get('candidate_family'))}`",
        f"- Target curve: `{_escape(method.get('target_curve_override'))}`",
        f"- Numeric labeled rows: `{_escape(summary.get('numeric_row_count'))}`",
        f"- Aozora joined rows: `{_escape(summary.get('aozora_joined_count'))}`",
        f"- Aozora missing rows: `{_escape(summary.get('aozora_missing_count'))}`",
        f"- Current labeled MAE: `{_escape(summary.get('mae'))}`",
        f"- Candidate old/literary-fix rows: `{_escape(summary.get('candidate_old_literary_fix_count'))}`",
        f"- Candidate accessible-fix rows: `{_escape(summary.get('candidate_accessible_fix_count'))}`",
        "",
        "This is a review artifact only. It does not change scorer behavior.",
        "",
        "## Feature Correlations",
        "",
        "| Pair | r |",
        "| --- | ---: |",
    ]
    for key, value in _mapping(summary.get("correlations")).items():
        lines.append(f"| `{_escape(key)}` | {_escape(value)} |")
    lines.extend(
        [
            "",
            "## Largest Labeled Errors",
            "",
            _review_table(report.get("largest_errors") or []),
            "",
            "## Potential Old/Literary Underpredictions",
            "",
            _review_table(
                _mapping(report.get("potential_actionable_groups")).get(
                    "too_low_with_old_literary_signal"
                )
                or []
            ),
            "",
            "## Potential Accessible Overpredictions",
            "",
            _review_table(
                _mapping(report.get("potential_actionable_groups")).get(
                    "too_high_with_accessible_signal"
                )
                or []
            ),
            "",
            "## Focus Rows",
            "",
            _review_table(report.get("focus_rows") or [], include_expected=False),
            "",
            "## Caveats",
            "",
            "- Aozora context is literary/book exposure, not a general frequency replacement.",
            "- Token-level features use broad `token_context_profile` aggregates, not a full token-by-work bridge.",
            "- `lemma_only_fallback` rows should be treated cautiously when readings differ.",
            "",
        ]
    )
    return "\n".join(lines)


def _review_table(rows: Sequence[Mapping[str, Any]], *, include_expected: bool = True) -> str:
    if not rows:
        return "_No rows._"
    headers = [
        "Dataset" if include_expected else "Source",
        "Label",
        "Expected" if include_expected else "Score",
        "Score" if include_expected else "Band",
        "Err" if include_expected else "Rank",
        "Aozora",
        "Access",
        "Hard",
        "OldRisk",
        "ModChild",
        "Conf",
        "Interpretation",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows[:80]:
        aozora = _mapping(row.get("aozora"))
        component = _mapping(row.get("component"))
        feature = _mapping(aozora.get("features"))
        if include_expected:
            first_cells = [
                str(row.get("dataset") or ""),
                str(row.get("label") or ""),
                _fmt(row.get("expected")),
                _fmt(row.get("score")),
                _fmt(row.get("signed_error")),
            ]
        else:
            first_cells = [
                "focus",
                str(row.get("label") or ""),
                _fmt(row.get("score")),
                str(row.get("score_band") or ""),
                str(component.get("score_rank") or ""),
            ]
        cells = [
            *first_cells,
            str(aozora.get("match_status") or ""),
            _fmt(feature.get("accessibility_weighted_mean")),
            _fmt(feature.get("hard_work_exposure")),
            _fmt(feature.get("old_literary_risk_context")),
            _fmt(feature.get("modern_child_accessible_context")),
            _fmt(feature.get("context_confidence")),
            str(row.get("interpretation") or ""),
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _interpret_row(delta: float | None, aozora: Mapping[str, Any]) -> str:
    if aozora.get("match_status") == "missing":
        return "no_aozora_context"
    old_risk = _feature_value({"aozora": aozora}, "old_literary_risk_context")
    hard = _feature_value({"aozora": aozora}, "hard_work_exposure")
    accessible = _feature_value({"aozora": aozora}, "accessible_work_exposure")
    modern_child = _feature_value({"aozora": aozora}, "modern_child_accessible_context")
    confidence = _feature_value({"aozora": aozora}, "context_confidence")
    if confidence < 0.20:
        return "weak_aozora_context"
    if delta is not None and delta < -0.08 and max(old_risk, hard) >= 0.25:
        return "old_or_hard_context_may_raise"
    if delta is not None and delta > 0.08 and max(accessible, modern_child) >= 0.25:
        return "accessible_context_may_lower"
    if modern_child >= 0.50:
        return "modern_child_accessible_context"
    if old_risk >= 0.45:
        return "old_literary_context"
    if accessible >= 0.50:
        return "accessible_context"
    return "mixed_or_neutral_context"


def _too_low_old_literary_candidate(row: Mapping[str, Any]) -> bool:
    return (
        float(row.get("signed_error") or 0.0) < -0.08
        and max(
            _feature_value(row, "old_literary_risk_context"),
            _feature_value(row, "hard_work_exposure"),
        )
        >= 0.25
        and _feature_value(row, "context_confidence") >= 0.35
    )


def _too_high_accessible_candidate(row: Mapping[str, Any]) -> bool:
    return (
        float(row.get("signed_error") or 0.0) > 0.08
        and max(
            _feature_value(row, "accessible_work_exposure"),
            _feature_value(row, "modern_child_accessible_context"),
        )
        >= 0.25
        and _feature_value(row, "context_confidence") >= 0.35
    )


def _feature_value(row: Mapping[str, Any], name: str) -> float:
    return float(
        _optional_float(_mapping(_mapping(row.get("aozora")).get("features")).get(name)) or 0.0
    )


def _underprediction(row: Mapping[str, Any]) -> float:
    return max(0.0, -float(row.get("signed_error") or 0.0))


def _overprediction(row: Mapping[str, Any]) -> float:
    return max(0.0, float(row.get("signed_error") or 0.0))


def _correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) < 3 or len(right) < 3:
        return None
    x = np.asarray(left, dtype=np.float32)
    y = np.asarray(right, dtype=np.float32)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        return None
    if float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return None
    return _rounded(float(np.corrcoef(x, y)[0, 1]))


def _score_ranks(scores: np.ndarray) -> np.ndarray:
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=np.int64)
    ranks[order] = np.arange(1, len(scores) + 1)
    return ranks


def _parse_focus_row(value: str) -> tuple[str, str]:
    text = str(value or "").strip()
    if "/" not in text:
        return text, ""
    lemma, reading = text.rsplit("/", 1)
    return lemma.strip(), reading.strip()


def _kana_to_katakana(value: str) -> str:
    chars = []
    for char in str(value or ""):
        code = ord(char)
        if 0x3041 <= code <= 0x3096:
            chars.append(chr(code + 0x60))
        else:
            chars.append(char)
    return "".join(chars)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _resolve_path(value: Path) -> Path:
    if value.is_absolute():
        return value
    return (PROJECT_ROOT / value).resolve()


def _fmt(value: Any) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.3f}"


def _review_difficulty_band(value: Any) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    if parsed < 0.20:
        return "0.00-0.20"
    if parsed < 0.40:
        return "0.20-0.40"
    if parsed < 0.60:
        return "0.40-0.60"
    if parsed < 0.80:
        return "0.60-0.80"
    if parsed < 0.90:
        return "0.80-0.90"
    return "0.90-1.00"


if __name__ == "__main__":
    raise SystemExit(main())
