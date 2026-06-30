#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
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
from srs_learner_difficulty_aozora_context_review_en_ja import (  # noqa: E402
    DEFAULT_AOZORA_SQLITE,
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_SOURCE_ARBITRATION_JSON,
    DEFAULT_VALIDATION_JSON,
    FEATURE_FIELDS,
    _aggregate_aozora_features,
    _load_all_labels,
    _selected_candidate_metadata,
    _select_component,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_band,
    _difficulty_metrics,
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _rounded,
    _summary_metrics,
    _target_curve_normalize,
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
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_tail_bakeoff_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_tail_bakeoff_en_ja_latest.md"
)
SAMPLE_BANDS = (
    (0.55, 0.60),
    (0.60, 0.70),
    (0.70, 0.80),
    (0.80, 0.90),
    (0.90, 1.01),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Try bounded Aozora-attestation advanced-tail transforms against the "
            "current en-ja learner-difficulty source-arbitration model. This is a "
            "diagnostic sidecar and does not change scorer behavior."
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
    parser.add_argument("--top-variant-count", type=int, default=12)
    parser.add_argument("--sample-per-band", type=int, default=10)
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
        top_variant_count=max(1, int(args.top_variant_count)),
        sample_per_band=max(1, int(args.sample_per_band)),
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
    top_variant_count: int,
    sample_per_band: int,
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
    current_scores = _current_scores(view=view, selected=selected)
    labels = _label_context(
        view=view,
        current_scores=current_scores,
        calibration_json=calibration_json,
        holdout_json=holdout_json,
        validation_json=validation_json,
    )
    aozora = _aozora_feature_arrays(view=view, aozora_sqlite=aozora_sqlite)
    component_signals = _component_signal_arrays(view)
    variants = _variant_specs()
    baseline = _variant_result(
        variant={
            "variant_id": "current",
            "description": "Current accepted sidecar candidate; no Aozora tail transform.",
        },
        scores=current_scores,
        current_scores=current_scores,
        labels=labels,
    )
    rows: list[dict[str, Any]] = [baseline]
    for variant in variants:
        transformed = _apply_tail_variant(
            current_scores=current_scores,
            target_positions=np.asarray(view.target_positions, dtype=np.float32),
            aozora=aozora,
            component_signals=component_signals,
            variant=variant,
        )
        rows.append(
            _variant_result(
                variant=variant,
                scores=transformed,
                current_scores=current_scores,
                labels=labels,
            )
        )
    ranked = sorted(
        rows[1:],
        key=lambda row: (
            _optional_float(row.get("selection_score")) or -999.0,
            _optional_float(_mapping(row.get("all_summary")).get("pairwise_accuracy")) or -999.0,
            -(
                _optional_float(_mapping(row.get("holdout_tail60")).get("mae_delta_vs_current"))
                or 999.0
            ),
        ),
        reverse=True,
    )
    top_rows = ranked[:top_variant_count]
    aggressive_rows = _aggressive_spotlight_rows(ranked, limit=6)
    sample_variant_ids = _sample_variant_ids(ranked)
    sample_variant_ids.update(str(row.get("variant_id") or "") for row in aggressive_rows)
    spotlight_rows = [
        row for row in ranked if str(row.get("variant_id") or "") in sample_variant_ids
    ]
    samples = {
        str(row["variant_id"]): _variant_samples(
            variant_id=str(row["variant_id"]),
            scores=_apply_tail_variant(
                current_scores=current_scores,
                target_positions=np.asarray(view.target_positions, dtype=np.float32),
                aozora=aozora,
                component_signals=component_signals,
                variant=_variant_by_id(str(row["variant_id"]), variants),
            ),
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            per_band=sample_per_band,
        )
        for row in ranked
        if str(row["variant_id"]) in sample_variant_ids
    }
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "model_behavior_changed": False,
        "method": {
            "purpose": (
                "Advanced-tail sidecar bakeoff for Aozora attestation/context "
                "signals. Scores are adjusted only through smooth tail gates and "
                "then re-normalized onto the existing target curve."
            ),
            "candidate_id": selected["candidate_id"],
            "candidate_family": selected["candidate_family"],
            "target_curve_override": selected["target_curve_override"],
            "formula": (
                "raw = current - tail_gate * attestation_strength * attestation_lower "
                "* (1 - old_discount * old_literary_risk) * "
                "(1 - lower_dirty_block * marked_or_proper_risk) + tail_gate "
                "* old_raise * attestation_strength * old_literary_risk + "
                "tail_gate * missing_raise * low_cross_source_no_evidence; "
                "final = current + rank_blend * (target_curve_normalize(raw) - current). "
                "Refinement variants can taper raises near 1.00 and block old raises "
                "when Aozora context is also accessible."
            ),
        },
        "inputs": {
            "source_arbitration_json": _repo_or_home_path(source_arbitration_json),
            "component_matrix": _repo_or_home_path(component_matrix),
            "calibration_json": _repo_or_home_path(calibration_json),
            "holdout_json": _repo_or_home_path(holdout_json),
            "validation_json": _repo_or_home_path(validation_json),
            "aozora_sqlite": _repo_or_home_path(aozora_sqlite),
            "component_count": int(len(current_scores)),
            "label_count": len(labels["rows"]),
            "variant_count": len(variants),
        },
        "baseline": baseline,
        "top_variants": top_rows,
        "aggressive_spotlight_variants": aggressive_rows,
        "spotlight_variants": spotlight_rows,
        "variant_samples": samples,
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
                "aozora_context_review": (
                    SCRIPT_DIR / "srs_learner_difficulty_aozora_context_review_en_ja.py"
                ),
                "aozora_tail_bakeoff": Path(__file__),
            },
            argv=sys.argv,
        ),
    }


def _current_scores(*, view: ComponentView, selected: Mapping[str, str]) -> np.ndarray:
    candidates = generate_candidates(candidate_family=str(selected["candidate_family"]))
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    candidate = candidate_by_id.get(str(selected["candidate_id"]))
    if candidate is None:
        raise SystemExit(
            "Candidate id is not generated by candidate family: "
            f"{selected['candidate_id']} ({selected['candidate_family']})"
        )
    return np.asarray(
        normalized_scores_for_candidate(candidate, view, parts=family_parts(view)),
        dtype=np.float32,
    )


def _label_context(
    *,
    view: ComponentView,
    current_scores: np.ndarray,
    calibration_json: Path,
    holdout_json: Path,
    validation_json: Path,
) -> dict[str, Any]:
    lookup = _component_lookup(view=view, current_scores=current_scores)
    rows = _load_all_labels(
        calibration_json=calibration_json,
        holdout_json=holdout_json,
        validation_json=validation_json,
    )
    usable = []
    for row in rows:
        component = _select_component(str(row["lemma"]), str(row.get("reading") or ""), lookup)
        index = int(component.get("component_index", -1)) if component else -1
        expected = _optional_float(row.get("expected"))
        if index < 0 or expected is None:
            continue
        usable.append(
            {
                **row,
                "component_index": index,
                "expected": float(expected),
                "expected_band": _difficulty_band(float(expected)),
                "current_score": float(current_scores[index]),
            }
        )
    return {
        "rows": usable,
        "indices": np.asarray([row["component_index"] for row in usable], dtype=np.int64),
        "expected": np.asarray([row["expected"] for row in usable], dtype=np.float32),
        "expected_bands": [str(row["expected_band"]) for row in usable],
        "labels": [str(row["label"]) for row in usable],
        "datasets": np.asarray([str(row["dataset"]) for row in usable], dtype="<U32"),
        "current": np.asarray([row["current_score"] for row in usable], dtype=np.float32),
    }


def _component_lookup(*, view: ComponentView, current_scores: np.ndarray) -> dict[str, Any]:
    exact: dict[tuple[str, str], dict[str, Any]] = {}
    by_lemma: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, (lemma, reading, identity, candidate_state) in enumerate(
        zip(view.lemmas, view.readings, view.identities, view.candidate_states)
    ):
        row = {
            "component_index": int(index),
            "lemma": str(lemma),
            "reading": str(reading),
            "identity_key": str(identity),
            "candidate_state": str(candidate_state),
            "score": float(current_scores[index]),
        }
        exact[(row["lemma"], row["reading"])] = row
        by_lemma[row["lemma"]].append(row)
    for group in by_lemma.values():
        group.sort(key=lambda row: (float(row["score"]), str(row["reading"])))
    return {"exact": exact, "by_lemma": dict(by_lemma)}


def _aozora_feature_arrays(*, view: ComponentView, aozora_sqlite: Path) -> dict[str, Any]:
    terms = {str(lemma) for lemma in view.lemmas if str(lemma)}
    rows_by_term = _load_all_aozora_rows(aozora_sqlite, terms=terms)
    count = len(view.lemmas)
    features = {name: np.zeros(count, dtype=np.float32) for name in FEATURE_FIELDS}
    token_count = np.zeros(count, dtype=np.float32)
    work_count = np.zeros(count, dtype=np.float32)
    author_count = np.zeros(count, dtype=np.float32)
    match_status = np.full(count, "missing", dtype="<U24")
    for index, (lemma, reading) in enumerate(zip(view.lemmas, view.readings)):
        term_rows = rows_by_term.get(str(lemma), ())
        aggregate = _aggregate_aozora_features(str(lemma), str(reading), term_rows)
        match_status[index] = str(aggregate.get("match_status") or "missing")
        token_count[index] = float(_optional_float(aggregate.get("token_count")) or 0.0)
        work_count[index] = float(_optional_float(aggregate.get("work_count_max")) or 0.0)
        author_count[index] = float(_optional_float(aggregate.get("author_count_max")) or 0.0)
        payload = _mapping(aggregate.get("features"))
        for name in FEATURE_FIELDS:
            features[name][index] = float(_optional_float(payload.get(name)) or 0.0)
    return {
        "features": features,
        "token_count": token_count,
        "work_count": work_count,
        "author_count": author_count,
        "match_status": match_status,
    }


def _load_all_aozora_rows(
    sqlite_path: Path,
    *,
    terms: set[str],
) -> dict[str, list[dict[str, Any]]]:
    if not sqlite_path.exists() or not terms:
        return {}
    rows_by_term: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        for row in _iter_aozora_token_rows(
            conn,
            surfaces=(),
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
            for term in {payload["surface"], payload["base_form"]}:
                if term in terms:
                    rows_by_term[term].append(payload)
    for rows in rows_by_term.values():
        rows.sort(key=lambda row: (-(row.get("token_count") or 0), str(row.get("reading") or "")))
    return dict(rows_by_term)


def _component_signal_arrays(view: ComponentView) -> dict[str, np.ndarray]:
    names = (
        "source_coverage_count",
        "frequency_rank_known",
        "tubelex_frequency_known",
        "pedagogical_source_known",
        "jlpt_vocab_known",
        "jmdict_priority",
        "jmdict_marked_usage_risk",
        "jmdict_register_domain_risk",
        "jmdict_field_marked_risk",
        "jmdict_dialect_risk",
        "frequency_unranked_risk",
        "named_entity_risk",
        "jmnedict_name_risk",
        "problem_class_proper_risk",
        "wtype_proper_risk",
    )
    return {name: _component_signal(view, name) for name in names}


def _component_signal(view: ComponentView, name: str) -> np.ndarray:
    index = view.name_to_index.get(name)
    if index is None:
        return np.zeros(len(view.lemmas), dtype=np.float32)
    return np.asarray(view.values[:, index], dtype=np.float32)


def _variant_specs() -> list[dict[str, Any]]:
    variants = []
    seen: set[str] = set()
    for gate_lower, gate_upper in ((0.55, 0.82), (0.60, 0.88), (0.68, 0.94)):
        for attestation_lower in (0.02, 0.04, 0.06):
            for old_raise in (0.00, 0.04, 0.08, 0.12):
                for missing_raise in (0.00, 0.02, 0.04):
                    for old_discount in (0.50, 0.85, 1.00):
                        for lower_dirty_block in (0.00, 0.75, 1.00):
                            if attestation_lower == old_raise == missing_raise == 0.0:
                                continue
                            _append_variant(
                                variants,
                                seen,
                                variant_group="base",
                                gate_lower=gate_lower,
                                gate_upper=gate_upper,
                                attestation_lower=attestation_lower,
                                old_raise=old_raise,
                                missing_raise=missing_raise,
                                old_discount=old_discount,
                                lower_dirty_block=lower_dirty_block,
                            )
    for gate_lower, gate_upper in ((0.55, 0.82), (0.60, 0.88), (0.68, 0.94)):
        for old_raise in (0.08, 0.12):
            for missing_raise in (0.02, 0.04):
                for old_discount in (0.85, 1.00):
                    for lower_dirty_block in (0.00, 0.75, 1.00):
                        for raise_taper_start, raise_taper_strength in (
                            (0.88, 0.75),
                            (0.92, 1.00),
                        ):
                            for old_access_block in (0.00, 0.60, 1.00):
                                for rank_blend in (0.50, 0.75):
                                    _append_variant(
                                        variants,
                                        seen,
                                        variant_group="refine",
                                        gate_lower=gate_lower,
                                        gate_upper=gate_upper,
                                        attestation_lower=0.02,
                                        old_raise=old_raise,
                                        missing_raise=missing_raise,
                                        old_discount=old_discount,
                                        lower_dirty_block=lower_dirty_block,
                                        raise_taper_start=raise_taper_start,
                                        raise_taper_strength=raise_taper_strength,
                                        old_access_block=old_access_block,
                                        rank_blend=rank_blend,
                                    )
    return variants


def _append_variant(
    variants: list[dict[str, Any]],
    seen: set[str],
    *,
    variant_group: str,
    gate_lower: float,
    gate_upper: float,
    attestation_lower: float,
    old_raise: float,
    missing_raise: float,
    old_discount: float,
    lower_dirty_block: float,
    raise_taper_start: float = 1.01,
    raise_taper_strength: float = 0.0,
    old_access_block: float = 0.0,
    rank_blend: float = 1.0,
) -> None:
    variant_id = (
        f"aoztail_{variant_group}"
        f"_gl{_label_float(gate_lower)}_gu{_label_float(gate_upper)}"
        f"_al{_label_float(attestation_lower)}"
        f"_or{_label_float(old_raise)}"
        f"_mr{_label_float(missing_raise)}"
        f"_od{_label_float(old_discount)}"
        f"_db{_label_float(lower_dirty_block)}"
        f"_ts{_label_float(raise_taper_start)}"
        f"_tt{_label_float(raise_taper_strength)}"
        f"_ab{_label_float(old_access_block)}"
        f"_rb{_label_float(rank_blend)}"
    )
    if variant_id in seen:
        return
    seen.add(variant_id)
    variants.append(
        {
            "variant_id": variant_id,
            "variant_group": variant_group,
            "description": (
                "Tail-only Aozora attestation lower, old/literary raise, "
                "low-cross-source missing-evidence raise, optional marked/proper/domain "
                "block on lowering, optional top taper, and optional rank-blend damping."
            ),
            "gate_lower": gate_lower,
            "gate_upper": gate_upper,
            "attestation_lower": attestation_lower,
            "old_raise": old_raise,
            "missing_raise": missing_raise,
            "old_discount": old_discount,
            "lower_dirty_block": lower_dirty_block,
            "raise_taper_start": raise_taper_start,
            "raise_taper_strength": raise_taper_strength,
            "old_access_block": old_access_block,
            "rank_blend": rank_blend,
        }
    )


def _apply_tail_variant(
    *,
    current_scores: np.ndarray,
    target_positions: np.ndarray,
    aozora: Mapping[str, Any],
    component_signals: Mapping[str, np.ndarray],
    variant: Mapping[str, Any],
) -> np.ndarray:
    if str(variant.get("variant_id")) == "current":
        return np.asarray(current_scores, dtype=np.float32)
    return np.asarray(
        _tail_variant_terms(
            current_scores=current_scores,
            target_positions=target_positions,
            aozora=aozora,
            component_signals=component_signals,
            variant=variant,
        )["final_scores"],
        dtype=np.float32,
    )


def _tail_variant_terms(
    *,
    current_scores: np.ndarray,
    target_positions: np.ndarray,
    aozora: Mapping[str, Any],
    component_signals: Mapping[str, np.ndarray],
    variant: Mapping[str, Any],
) -> dict[str, np.ndarray]:
    features = _mapping(aozora.get("features"))
    confidence = np.asarray(features.get("context_confidence"), dtype=np.float32)
    token_count = np.asarray(aozora.get("token_count"), dtype=np.float32)
    work_count = np.asarray(aozora.get("work_count"), dtype=np.float32)
    old_risk = np.maximum(
        np.asarray(features.get("old_literary_risk_context"), dtype=np.float32),
        0.65 * np.asarray(features.get("hard_work_exposure"), dtype=np.float32),
    )
    old_risk = np.clip(old_risk, 0.0, 1.0)
    accessible_context = np.maximum(
        np.asarray(features.get("accessible_work_exposure"), dtype=np.float32),
        np.asarray(features.get("modern_child_accessible_context"), dtype=np.float32),
    )
    dirty_risk = np.maximum.reduce(
        [
            np.asarray(component_signals["jmdict_marked_usage_risk"], dtype=np.float32),
            np.asarray(component_signals["jmdict_register_domain_risk"], dtype=np.float32),
            np.asarray(component_signals["jmdict_field_marked_risk"], dtype=np.float32),
            np.asarray(component_signals["jmdict_dialect_risk"], dtype=np.float32),
            np.asarray(component_signals["named_entity_risk"], dtype=np.float32),
            np.asarray(component_signals["jmnedict_name_risk"], dtype=np.float32),
            np.asarray(component_signals["problem_class_proper_risk"], dtype=np.float32),
            np.asarray(component_signals["wtype_proper_risk"], dtype=np.float32),
        ]
    )
    clean_lower_gate = np.clip(
        1.0 - float(variant.get("lower_dirty_block") or 0.0) * dirty_risk, 0.0, 1.0
    )
    token_strength = np.clip(np.log1p(token_count) / math.log1p(120.0), 0.0, 1.0)
    work_strength = np.clip(np.log1p(work_count) / math.log1p(18.0), 0.0, 1.0)
    attestation = np.sqrt(np.clip(confidence * np.maximum(token_strength, work_strength), 0.0, 1.0))
    source_coverage = np.asarray(component_signals["source_coverage_count"], dtype=np.float32)
    known_elsewhere = np.maximum.reduce(
        [
            np.asarray(component_signals["frequency_rank_known"], dtype=np.float32),
            np.asarray(component_signals["tubelex_frequency_known"], dtype=np.float32),
            np.asarray(component_signals["pedagogical_source_known"], dtype=np.float32),
            np.asarray(component_signals["jlpt_vocab_known"], dtype=np.float32),
        ]
    )
    low_cross_source = 1.0 - _smoothstep_array(0.46, 0.66, source_coverage)
    no_evidence = np.clip(
        (1.0 - attestation) * (1.0 - known_elsewhere) * low_cross_source, 0.0, 1.0
    )
    tail_gate = _smoothstep_array(
        float(variant["gate_lower"]),
        float(variant["gate_upper"]),
        np.asarray(current_scores, dtype=np.float32),
    )
    lower_shift = (
        float(variant["attestation_lower"])
        * attestation
        * np.clip(1.0 - float(variant["old_discount"]) * old_risk, 0.0, 1.0)
        * clean_lower_gate
    )
    raise_headroom = np.clip(
        1.0
        - float(variant.get("raise_taper_strength") or 0.0)
        * _smoothstep_array(
            float(variant.get("raise_taper_start") or 1.01),
            0.995,
            np.asarray(current_scores, dtype=np.float32),
        ),
        0.0,
        1.0,
    )
    old_access_gate = np.clip(
        1.0
        - float(variant.get("old_access_block") or 0.0)
        * _smoothstep_array(0.18, 0.50, accessible_context),
        0.0,
        1.0,
    )
    raise_shift = (
        float(variant["old_raise"]) * attestation * old_risk * raise_headroom * old_access_gate
    )
    missing_shift = float(variant["missing_raise"]) * no_evidence * raise_headroom
    lower_delta = -tail_gate * lower_shift
    old_raise_delta = tail_gate * raise_shift
    missing_delta = tail_gate * missing_shift
    direct_delta = lower_delta + old_raise_delta + missing_delta
    raw = np.asarray(current_scores, dtype=np.float32) + direct_delta
    normalized = np.asarray(
        _target_curve_normalize(raw, target_positions=target_positions),
        dtype=np.float32,
    )
    rank_blend = float(variant.get("rank_blend") or 1.0)
    final = np.asarray(
        np.clip(current_scores + rank_blend * (normalized - current_scores), 0.0, 1.0),
        dtype=np.float32,
    )
    return {
        "attestation": attestation,
        "known_elsewhere": known_elsewhere,
        "low_cross_source": low_cross_source,
        "no_evidence": no_evidence,
        "tail_gate": tail_gate,
        "old_risk": old_risk,
        "accessible_context": accessible_context,
        "dirty_risk": dirty_risk,
        "clean_lower_gate": clean_lower_gate,
        "raise_headroom": raise_headroom,
        "old_access_gate": old_access_gate,
        "lower_shift": lower_shift,
        "old_raise_shift": raise_shift,
        "missing_shift": missing_shift,
        "lower_delta": lower_delta,
        "old_raise_delta": old_raise_delta,
        "missing_delta": missing_delta,
        "direct_delta": direct_delta,
        "raw_scores": raw,
        "normalized_scores": normalized,
        "normalization_delta": final - raw,
        "final_scores": final,
        "final_delta": final - np.asarray(current_scores, dtype=np.float32),
    }


def _variant_result(
    *,
    variant: Mapping[str, Any],
    scores: np.ndarray,
    current_scores: np.ndarray,
    labels: Mapping[str, Any],
) -> dict[str, Any]:
    indices = np.asarray(labels["indices"], dtype=np.int64)
    expected = np.asarray(labels["expected"], dtype=np.float32)
    observed = np.asarray(scores[indices], dtype=np.float32)
    current = np.asarray(labels["current"], dtype=np.float32)
    all_metrics = _metrics_for(expected=expected, observed=observed, labels=labels)
    current_metrics = _metrics_for(expected=expected, observed=current, labels=labels)
    dataset_summaries = {}
    datasets = np.asarray(labels["datasets"], dtype=str)
    for dataset in sorted(set(str(value) for value in datasets)):
        mask = datasets == dataset
        dataset_summaries[dataset] = _delta_summary(
            expected=expected[mask],
            observed=observed[mask],
            current=current[mask],
        )
    tail60 = _subset_delta(expected=expected, observed=observed, current=current, min_expected=0.60)
    tail80 = _subset_delta(expected=expected, observed=observed, current=current, min_expected=0.80)
    beginner = _subset_delta(
        expected=expected, observed=observed, current=current, max_expected=0.40
    )
    error_delta = np.abs(observed - expected) - np.abs(current - expected)
    improved = int((error_delta < -0.01).sum())
    regressed = int((error_delta > 0.01).sum())
    selection_score = _selection_score(
        all_summary=_summary_metrics(all_metrics),
        current_summary=_summary_metrics(current_metrics),
        tail60=tail60,
        tail80=tail80,
        beginner=beginner,
        improved=improved,
        regressed=regressed,
    )
    return {
        **dict(variant),
        "selection_score": _rounded(selection_score),
        "all_summary": _summary_metrics(all_metrics),
        "all_delta": _delta_summary(expected=expected, observed=observed, current=current),
        "dataset_delta": dataset_summaries,
        "tail60": tail60,
        "tail80": tail80,
        "beginner": beginner,
        "regression_profile_0p01": _regression_profile(
            expected=expected,
            observed=observed,
            current=current,
        ),
        "label_improved_count_0p01": improved,
        "label_regressed_count_0p01": regressed,
        "largest_label_improvements": _largest_label_changes(
            labels, observed, current, expected, limit=12, sign=-1
        ),
        "largest_label_regressions": _largest_label_changes(
            labels, observed, current, expected, limit=12, sign=1
        ),
    }


def _metrics_for(
    *, expected: np.ndarray, observed: np.ndarray, labels: Mapping[str, Any]
) -> dict[str, Any]:
    return _difficulty_metrics(
        expected_values=expected,
        observed_values=observed,
        expected_bands=list(labels["expected_bands"])[: len(expected)],
        labels=list(labels["labels"])[: len(expected)],
    )


def _subset_delta(
    *,
    expected: np.ndarray,
    observed: np.ndarray,
    current: np.ndarray,
    min_expected: float | None = None,
    max_expected: float | None = None,
) -> dict[str, Any]:
    mask = np.ones(len(expected), dtype=bool)
    if min_expected is not None:
        mask &= expected >= float(min_expected)
    if max_expected is not None:
        mask &= expected <= float(max_expected)
    return _delta_summary(expected=expected[mask], observed=observed[mask], current=current[mask])


def _delta_summary(
    *, expected: np.ndarray, observed: np.ndarray, current: np.ndarray
) -> dict[str, Any]:
    if len(expected) == 0:
        return {"count": 0, "mae": None, "current_mae": None, "mae_delta_vs_current": None}
    error = np.abs(observed - expected)
    current_error = np.abs(current - expected)
    return {
        "count": int(len(expected)),
        "mae": _rounded(float(error.mean())),
        "current_mae": _rounded(float(current_error.mean())),
        "mae_delta_vs_current": _rounded(float(error.mean() - current_error.mean())),
        "improved_count_0p01": int(((error - current_error) < -0.01).sum()),
        "regressed_count_0p01": int(((error - current_error) > 0.01).sum()),
    }


def _selection_score(
    *,
    all_summary: Mapping[str, Any],
    current_summary: Mapping[str, Any],
    tail60: Mapping[str, Any],
    tail80: Mapping[str, Any],
    beginner: Mapping[str, Any],
    improved: int,
    regressed: int,
) -> float:
    pairwise = float(_optional_float(all_summary.get("pairwise_accuracy")) or 0.0)
    current_pairwise = float(_optional_float(current_summary.get("pairwise_accuracy")) or 0.0)
    all_mae_delta = float(_optional_float(all_summary.get("mae")) or 0.0) - float(
        _optional_float(current_summary.get("mae")) or 0.0
    )
    tail60_delta = float(_optional_float(tail60.get("mae_delta_vs_current")) or 0.0)
    tail80_delta = float(_optional_float(tail80.get("mae_delta_vs_current")) or 0.0)
    beginner_delta = float(_optional_float(beginner.get("mae_delta_vs_current")) or 0.0)
    label_balance = (improved - regressed) / max(1.0, float(improved + regressed))
    return (
        0.50
        + 0.70 * (pairwise - current_pairwise)
        - 1.25 * all_mae_delta
        - 1.50 * tail60_delta
        - 1.00 * tail80_delta
        - 1.25 * max(0.0, beginner_delta)
        + 0.03 * label_balance
    )


def _regression_profile(
    *,
    expected: np.ndarray,
    observed: np.ndarray,
    current: np.ndarray,
) -> dict[str, Any]:
    delta = np.abs(observed - expected) - np.abs(current - expected)
    mask = delta > 0.01
    if not mask.any():
        return {
            "count": 0,
            "below_0p60": 0,
            "from_0p60": 0,
            "from_0p75": 0,
            "from_0p80": 0,
            "from_0p90": 0,
            "max_error_delta": None,
            "mean_error_delta": None,
        }
    values = delta[mask]
    expected_regressions = expected[mask]
    return {
        "count": int(mask.sum()),
        "below_0p60": int((expected_regressions < 0.60).sum()),
        "from_0p60": int((expected_regressions >= 0.60).sum()),
        "from_0p75": int((expected_regressions >= 0.75).sum()),
        "from_0p80": int((expected_regressions >= 0.80).sum()),
        "from_0p90": int((expected_regressions >= 0.90).sum()),
        "max_error_delta": _rounded(float(values.max())),
        "mean_error_delta": _rounded(float(values.mean())),
    }


def _largest_label_changes(
    labels: Mapping[str, Any],
    observed: np.ndarray,
    current: np.ndarray,
    expected: np.ndarray,
    *,
    limit: int,
    sign: int,
) -> list[dict[str, Any]]:
    rows = list(labels["rows"])
    delta = np.abs(observed - expected) - np.abs(current - expected)
    order = np.argsort(delta if sign < 0 else -delta, kind="stable")
    output = []
    for index in order:
        value = float(delta[index])
        if sign < 0 and value >= -0.001:
            continue
        if sign > 0 and value <= 0.001:
            continue
        row = rows[int(index)]
        output.append(
            {
                "dataset": row["dataset"],
                "label": row["label"],
                "expected": _rounded(float(expected[index])),
                "current": _rounded(float(current[index])),
                "observed": _rounded(float(observed[index])),
                "error_delta": _rounded(value),
            }
        )
        if len(output) >= limit:
            break
    return output


def _variant_samples(
    *,
    variant_id: str,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
    per_band: int,
) -> dict[str, Any]:
    return {
        "variant_id": variant_id,
        "band_samples": _band_samples_for_scores(
            scores=scores,
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            per_band=per_band,
        ),
        "largest_down_moves": _move_samples(
            scores=scores,
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            direction="down",
            limit=35,
        ),
        "largest_up_moves": _move_samples(
            scores=scores,
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            direction="up",
            limit=35,
        ),
    }


def _band_samples_for_scores(
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
    per_band: int,
) -> list[dict[str, Any]]:
    output = []
    for start, end in SAMPLE_BANDS:
        if end >= 1.0:
            mask = (scores >= start) & (scores <= end)
        else:
            mask = (scores >= start) & (scores < end)
        indices = np.where(mask)[0]
        ordered = indices[np.argsort(scores[indices], kind="stable")]
        sample_indices = _quantile_indices(ordered, per_band)
        output.append(
            {
                "band": f"{start:.2f}-{min(end, 1.0):.2f}",
                "count": int(len(indices)),
                "samples": [
                    _sample_row(
                        index,
                        scores=scores,
                        current_scores=current_scores,
                        view=view,
                        aozora=aozora,
                    )
                    for index in sample_indices
                ],
            }
        )
    return output


def _move_samples(
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
    direction: str,
    limit: int,
) -> list[dict[str, Any]]:
    delta = scores - current_scores
    tail_mask = (current_scores >= 0.50) | (scores >= 0.50)
    if direction == "down":
        order = np.argsort(delta, kind="stable")
        selected = [int(index) for index in order if tail_mask[index] and delta[index] < -0.001]
    else:
        order = np.argsort(-delta, kind="stable")
        selected = [int(index) for index in order if tail_mask[index] and delta[index] > 0.001]
    return [
        _sample_row(index, scores=scores, current_scores=current_scores, view=view, aozora=aozora)
        for index in selected[:limit]
    ]


def _sample_row(
    index: int,
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
) -> dict[str, Any]:
    features = _mapping(aozora.get("features"))
    return {
        "lemma": str(view.lemmas[index]),
        "reading": str(view.readings[index]),
        "score": _rounded(float(scores[index])),
        "current": _rounded(float(current_scores[index])),
        "delta": _rounded(float(scores[index] - current_scores[index])),
        "match_status": str(np.asarray(aozora.get("match_status"))[index]),
        "token_count": int(float(np.asarray(aozora.get("token_count"))[index])),
        "work_count": int(float(np.asarray(aozora.get("work_count"))[index])),
        "author_count": int(float(np.asarray(aozora.get("author_count"))[index])),
        "confidence": _rounded(float(np.asarray(features.get("context_confidence"))[index])),
        "old_risk": _rounded(float(np.asarray(features.get("old_literary_risk_context"))[index])),
        "hard": _rounded(float(np.asarray(features.get("hard_work_exposure"))[index])),
        "access": _rounded(float(np.asarray(features.get("accessible_work_exposure"))[index])),
        "modern_child": _rounded(
            float(np.asarray(features.get("modern_child_accessible_context"))[index])
        ),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    method = _mapping(report.get("method"))
    baseline = _mapping(report.get("baseline"))
    lines = [
        "# en-ja Aozora Tail Bakeoff",
        "",
        "## Summary",
        "",
        f"- Candidate: `{_escape(method.get('candidate_id'))}`",
        f"- Candidate family: `{_escape(method.get('candidate_family'))}`",
        f"- Target curve: `{_escape(method.get('target_curve_override'))}`",
        f"- Variants tested: `{_escape(_mapping(report.get('inputs')).get('variant_count'))}`",
        f"- Component count: `{_escape(_mapping(report.get('inputs')).get('component_count'))}`",
        f"- Label count: `{_escape(_mapping(report.get('inputs')).get('label_count'))}`",
        "",
        "This is a diagnostic sidecar only. It does not change scorer behavior.",
        "",
        "## Baseline",
        "",
        _variant_metric_table([baseline]),
        "",
        "## Top Variants",
        "",
        _variant_metric_table(report.get("top_variants") or []),
        "",
        "## Spotlight Sample Variants",
        "",
        _variant_metric_table(report.get("spotlight_variants") or []),
        "",
        "## Aggressive Spotlight Variants",
        "",
        _variant_metric_table(report.get("aggressive_spotlight_variants") or []),
        "",
        _regression_profile_table(report.get("aggressive_spotlight_variants") or []),
        "",
        "## Largest Label Changes",
        "",
    ]
    for row in (report.get("top_variants") or [])[:3]:
        variant = _mapping(row)
        lines.extend(
            [
                f"### `{_escape(variant.get('variant_id'))}`",
                "",
                "Improvements:",
                "",
                _label_change_table(variant.get("largest_label_improvements") or []),
                "",
                "Regressions:",
                "",
                _label_change_table(variant.get("largest_label_regressions") or []),
                "",
            ]
        )
    lines.extend(["## Qualitative Samples", ""])
    for variant_id, samples in _mapping(report.get("variant_samples")).items():
        lines.extend(
            [
                f"### `{_escape(variant_id)}`",
                "",
                "Largest down moves:",
                "",
                _sample_table(_mapping(samples).get("largest_down_moves") or []),
                "",
                "Largest up moves:",
                "",
                _sample_table(_mapping(samples).get("largest_up_moves") or []),
                "",
            ]
        )
        for band in _mapping(samples).get("band_samples") or []:
            band_row = _mapping(band)
            lines.extend(
                [
                    f"Band `{_escape(band_row.get('band'))}` count `{_escape(band_row.get('count'))}`:",
                    "",
                    _sample_table(band_row.get("samples") or []),
                    "",
                ]
            )
    lines.extend(
        [
            "## Caveats",
            "",
            "- Aozora attestation is book/literary attestation, not a direct learner-frequency source.",
            "- All variants preserve the current target curve by re-normalizing after the tail shift.",
            "- Missing Aozora context only raises rows when other broad source-coverage signals are also weak.",
            "",
        ]
    )
    return "\n".join(lines)


def _regression_profile_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Variant | Reg>0.01 | <0.60 | >=0.60 | >=0.75 | >=0.80 | >=0.90 | Max dErr | Mean dErr |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        profile = _mapping(row.get("regression_profile_0p01"))
        cells = [
            str(row.get("variant_id") or ""),
            str(profile.get("count") or 0),
            str(profile.get("below_0p60") or 0),
            str(profile.get("from_0p60") or 0),
            str(profile.get("from_0p75") or 0),
            str(profile.get("from_0p80") or 0),
            str(profile.get("from_0p90") or 0),
            _fmt(profile.get("max_error_delta")),
            _fmt(profile.get("mean_error_delta")),
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _variant_metric_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Variant | Select | MAE | Pairwise | Tail60 dMAE | Tail80 dMAE | Begin dMAE | Improve | Regress | Params |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        summary = _mapping(row.get("all_summary"))
        tail60 = _mapping(row.get("tail60"))
        tail80 = _mapping(row.get("tail80"))
        beginner = _mapping(row.get("beginner"))
        params = ", ".join(
            f"{key}={_fmt(row.get(key))}"
            for key in (
                "gate_lower",
                "gate_upper",
                "attestation_lower",
                "old_raise",
                "missing_raise",
                "old_discount",
                "lower_dirty_block",
                "raise_taper_start",
                "raise_taper_strength",
                "old_access_block",
                "rank_blend",
            )
            if key in row
        )
        cells = [
            str(row.get("variant_id") or ""),
            _fmt(row.get("selection_score")),
            _fmt(summary.get("mae")),
            _fmt(summary.get("pairwise_accuracy")),
            _fmt(tail60.get("mae_delta_vs_current")),
            _fmt(tail80.get("mae_delta_vs_current")),
            _fmt(beginner.get("mae_delta_vs_current")),
            str(row.get("label_improved_count_0p01") or 0),
            str(row.get("label_regressed_count_0p01") or 0),
            params,
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _label_change_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Dataset | Label | Expected | Current | Variant | dError |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape(cell)
                for cell in (
                    row.get("dataset"),
                    row.get("label"),
                    _fmt(row.get("expected")),
                    _fmt(row.get("current")),
                    _fmt(row.get("observed")),
                    _fmt(row.get("error_delta")),
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _sample_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Word | Score | Current | Delta | Aozora | Tok | Works | Authors | Conf | Old | Hard | Access | ModChild |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows[:40]:
        label = (
            f"{row.get('lemma')}/{row.get('reading')}"
            if row.get("reading")
            else str(row.get("lemma") or "")
        )
        cells = [
            label,
            _fmt(row.get("score")),
            _fmt(row.get("current")),
            _fmt(row.get("delta")),
            str(row.get("match_status") or ""),
            str(row.get("token_count") or 0),
            str(row.get("work_count") or 0),
            str(row.get("author_count") or 0),
            _fmt(row.get("confidence")),
            _fmt(row.get("old_risk")),
            _fmt(row.get("hard")),
            _fmt(row.get("access")),
            _fmt(row.get("modern_child")),
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _sample_variant_ids(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    ids = {str(row.get("variant_id")) for row in rows[:2]}
    best_tail60 = min(
        rows,
        key=lambda row: (
            _optional_float(_mapping(row.get("tail60")).get("mae_delta_vs_current")) or 999.0
        ),
        default={},
    )
    best_tail80 = min(
        rows,
        key=lambda row: (
            _optional_float(_mapping(row.get("tail80")).get("mae_delta_vs_current")) or 999.0
        ),
        default={},
    )
    for row in (best_tail60, best_tail80):
        if row:
            ids.add(str(row.get("variant_id")))
    best_dirty_blocked = next(
        (row for row in rows if float(_optional_float(row.get("lower_dirty_block")) or 0.0) > 0.0),
        {},
    )
    if best_dirty_blocked:
        ids.add(str(best_dirty_blocked.get("variant_id")))
    return {value for value in ids if value}


def _aggressive_spotlight_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    candidates = [
        dict(row)
        for row in rows
        if int(row.get("label_improved_count_0p01") or 0)
        + int(row.get("label_regressed_count_0p01") or 0)
        >= 20
    ]
    candidates.sort(
        key=lambda row: (
            _optional_float(_mapping(row.get("tail60")).get("mae_delta_vs_current")) or 999.0,
            _optional_float(_mapping(row.get("tail80")).get("mae_delta_vs_current")) or 999.0,
            -(
                int(row.get("label_improved_count_0p01") or 0)
                - int(row.get("label_regressed_count_0p01") or 0)
            ),
        )
    )
    selected: list[dict[str, Any]] = []
    seen_groups: set[tuple[Any, ...]] = set()
    for row in candidates:
        group = (
            row.get("variant_group"),
            row.get("gate_lower"),
            row.get("gate_upper"),
            row.get("rank_blend"),
            row.get("raise_taper_strength"),
            row.get("lower_dirty_block"),
        )
        if group in seen_groups:
            continue
        seen_groups.add(group)
        selected.append(row)
        if len(selected) >= limit:
            break
    return selected


def _variant_by_id(variant_id: str, variants: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    for variant in variants:
        if str(variant.get("variant_id")) == variant_id:
            return variant
    raise KeyError(variant_id)


def _quantile_indices(indices: np.ndarray, count: int) -> list[int]:
    if len(indices) == 0:
        return []
    offsets = np.linspace(0, len(indices) - 1, num=min(count, len(indices)), dtype=int)
    return [int(indices[offset]) for offset in offsets]


def _smoothstep_array(lower: float, upper: float, values: np.ndarray) -> np.ndarray:
    if upper <= lower:
        return (values >= upper).astype(np.float32)
    x = np.clip((values - lower) / (upper - lower), 0.0, 1.0)
    return np.asarray(x * x * (3.0 - 2.0 * x), dtype=np.float32)


def _label_float(value: float) -> str:
    return str(int(round(float(value) * 100))).zfill(2)


def _fmt(value: Any) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.3f}"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(value: Path) -> Path:
    if value.is_absolute():
        return value
    return (PROJECT_ROOT / value).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
