#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_aozora_tail_bakeoff_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_SOURCE_ARBITRATION_JSON,
    DEFAULT_VALIDATION_JSON,
    ComponentView,
    _current_scores,
    _label_context,
    _load_json,
    _selected_candidate_metadata,
    _variant_result,
    _view_with_target_curve_override,
)
from srs_learner_difficulty_early_exact_support_gate_bakeoff_en_ja import (  # noqa: E402
    _apply_variant,
    _early_gate_evidence,
    _movement_summary,
    _variant_specs,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_source_arbitration_en_ja import family_parts  # noqa: E402


PAIR = "en-ja"
NORMAL_ADMISSION_CLASS = "normal_vocab"
DEFAULT_VARIANT_ID = "exgate_orth_ec06_fl044_fh058_mr022_xcr0_ts04_te06_sp05"
DEFAULT_CSV_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_final_ranking_en_ja_latest.csv"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_review_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_review_en_ja_latest.md"
)
DEFAULT_MANUAL_CORRECTIONS_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_manual_corrections_en_ja.json"
)
FIRST_REVIEW_COUNT = 100
MANUAL_WATCHLIST: dict[tuple[str, str], str] = {
    ("吐く", "つく"): (
        "manual_override_candidate: JLPT lists exact pair, but product "
        "presentation likely wants this written form later."
    ),
    ("時々", "じじ"): ("manual_override_candidate: rare reading of common surface 時々/ときどき."),
    ("何人", "なにびと"): (
        "manual_override_candidate: rare/literary reading of common-looking surface."
    ),
    ("或いは", "あるいは"): "watch_only: acceptable unless final review finds it too early.",
    ("猶", "なお"): (
        "watch_only: should be handled by orthographic overlay; verify final placement."
    ),
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export the deterministic full en-ja learner-difficulty ranking for "
            "the selected acceptance sidecar variant, plus a first-100 review pack."
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
    parser.add_argument(
        "--manual-corrections-json",
        type=Path,
        default=DEFAULT_MANUAL_CORRECTIONS_JSON,
        help=(
            "Optional manual correction layer. Active corrections adjust effective "
            "scores and annotate display/admission/topic-stretch metadata."
        ),
    )
    parser.add_argument(
        "--disable-manual-corrections",
        action="store_true",
        help="Export raw model scores without applying the manual correction layer.",
    )
    parser.add_argument("--variant-id", default=DEFAULT_VARIANT_ID)
    parser.add_argument("--first-review-count", type=int, default=FIRST_REVIEW_COUNT)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    csv_out = _resolve_path(args.csv_out)
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    report, rows = build_report(
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
        manual_corrections_json=(
            None if args.disable_manual_corrections else _resolve_path(args.manual_corrections_json)
        ),
        variant_id=str(args.variant_id or DEFAULT_VARIANT_ID),
        first_review_count=max(1, int(args.first_review_count)),
        csv_out=csv_out,
    )
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(csv_out, rows)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote CSV ranking to {csv_out}")
    print(f"Wrote JSON review artifact to {json_out}")
    print(f"Wrote Markdown review artifact to {markdown_out}")
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
    manual_corrections_json: Path | None,
    variant_id: str,
    first_review_count: int,
    csv_out: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
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
    evidence = _early_gate_evidence(view=view, parts=family_parts(view))
    variant = _variant_by_id(variant_id)
    model_scores = _apply_variant(
        current_scores=current_scores,
        evidence=evidence,
        variant=variant,
    )
    corrections = _load_corrections(manual_corrections_json)
    scores, correction_applications = _apply_corrections(
        scores=model_scores,
        view=view,
        corrections=corrections,
    )
    labels = _label_context(
        view=view,
        current_scores=current_scores,
        calibration_json=calibration_json,
        holdout_json=holdout_json,
        validation_json=validation_json,
    )
    raw_variant_metrics = _variant_result(
        variant=variant,
        scores=model_scores,
        current_scores=current_scores,
        labels=labels,
    )
    raw_variant_metrics.update(
        _movement_summary(scores=model_scores, current_scores=current_scores)
    )
    variant_metrics = _variant_result(
        variant={
            **variant,
            "variant_id": f"{variant_id}+manual_corrections",
            "description": ("Selected sidecar variant after active manual score corrections."),
        },
        scores=scores,
        current_scores=current_scores,
        labels=labels,
    )
    variant_metrics.update(_movement_summary(scores=scores, current_scores=current_scores))
    order = _ranking_order(scores=scores, view=view)
    rows = [
        _ranking_row(
            rank=rank,
            index=index,
            scores=scores,
            model_scores=model_scores,
            current_scores=current_scores,
            view=view,
            evidence=evidence,
            corrections=corrections,
        )
        for rank, index in enumerate(order, start=1)
    ]
    first_rows = rows[:first_review_count]
    watchlist_rows = _watchlist_rows(rows)
    report = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "model_behavior_changed": False,
        "method": {
            "purpose": (
                "Deterministic full-ranking export for final acceptance review. "
                "The full ranking is sorted by final score, then core rank, then "
                "surface and reading."
            ),
            "base_candidate_id": selected["candidate_id"],
            "base_candidate_family": selected["candidate_family"],
            "target_curve_override": selected["target_curve_override"],
            "variant_id": variant_id,
            "manual_corrections_applied": manual_corrections_json is not None,
            "first_review_count": first_review_count,
        },
        "outputs": {
            "full_ranking_csv": _repo_or_home_path(csv_out),
        },
        "inputs": {
            "source_arbitration_json": _repo_or_home_path(source_arbitration_json),
            "component_matrix": _repo_or_home_path(component_matrix),
            "calibration_json": _repo_or_home_path(calibration_json),
            "holdout_json": _repo_or_home_path(holdout_json),
            "validation_json": _repo_or_home_path(validation_json),
            "manual_corrections_json": (
                _repo_or_home_path(manual_corrections_json)
                if manual_corrections_json is not None
                else None
            ),
            "component_count": int(len(current_scores)),
        },
        "raw_variant_metrics": raw_variant_metrics,
        "variant_metrics": variant_metrics,
        "correction_summary": _correction_summary(correction_applications),
        "band_counts": _band_counts(scores=scores),
        "first_rows": first_rows,
        "first_row_review_flags": _flag_summary(first_rows),
        "manual_watchlist_rows": watchlist_rows,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "source_arbitration_json": source_arbitration_json,
                "component_matrix": component_matrix,
                "calibration_json": calibration_json,
                "holdout_json": holdout_json,
                "validation_json": validation_json,
                **(
                    {"manual_corrections_json": manual_corrections_json}
                    if manual_corrections_json is not None
                    else {}
                ),
            },
            code_paths={
                **_srs_difficulty_code_paths(),
                "source_arbitration": (
                    SCRIPT_DIR / "srs_learner_difficulty_source_arbitration_en_ja.py"
                ),
                "aozora_tail_bakeoff": (
                    SCRIPT_DIR / "srs_learner_difficulty_aozora_tail_bakeoff_en_ja.py"
                ),
                "early_exact_support_gate_bakeoff": (
                    SCRIPT_DIR / "srs_learner_difficulty_early_exact_support_gate_bakeoff_en_ja.py"
                ),
                "final_ranking_export": Path(__file__),
            },
            argv=sys.argv,
        ),
    }
    return report, rows


def _variant_by_id(variant_id: str) -> dict[str, Any]:
    for variant in _variant_specs():
        if str(variant.get("variant_id")) == variant_id:
            return variant
    raise ValueError(f"Unknown variant id: {variant_id}")


def _load_corrections(path: Path | None) -> dict[tuple[str, str], dict[str, Any]]:
    if path is None:
        return {}
    payload = _load_json(path)
    rows = payload.get("corrections") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list):
        raise ValueError(f"Manual corrections JSON has no corrections list: {path}")
    corrections: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        surface = str(row.get("surface") or row.get("lemma") or "").strip()
        reading = str(row.get("reading") or "").strip()
        if not surface or not reading:
            raise ValueError(f"Manual correction row needs surface and reading: {row!r}")
        key = (surface, reading)
        if key in corrections:
            raise ValueError(f"Duplicate manual correction row for {surface}/{reading}")
        corrections[key] = dict(row)
    return corrections


def _apply_corrections(
    *,
    scores: np.ndarray,
    view: ComponentView,
    corrections: Mapping[tuple[str, str], Mapping[str, Any]],
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    corrected = np.asarray(scores, dtype=np.float32).copy()
    applications: list[dict[str, Any]] = []
    if not corrections:
        return corrected, applications
    index_by_key = {
        (str(lemma), str(reading)): index
        for index, (lemma, reading) in enumerate(zip(view.lemmas, view.readings, strict=False))
    }
    for key, correction in sorted(corrections.items()):
        index = index_by_key.get(key)
        if index is None:
            applications.append(
                {
                    "lemma": key[0],
                    "reading": key[1],
                    "status": str(correction.get("status") or ""),
                    "applied": False,
                    "reason": "missing_from_component_matrix",
                }
            )
            continue
        before = float(corrected[index])
        after = before
        if _is_active_correction(correction):
            override = _optional_float(correction.get("score_override"))
            floor = _optional_float(correction.get("min_score"))
            if override is not None:
                after = override
            elif floor is not None:
                after = max(before, floor)
            corrected[index] = np.float32(min(1.0, max(0.0, after)))
        applications.append(
            {
                "lemma": key[0],
                "reading": key[1],
                "status": str(correction.get("status") or ""),
                "applied": bool(_is_active_correction(correction) and abs(after - before) > 1e-9),
                "model_score": _rounded(before),
                "effective_score": _rounded(float(corrected[index])),
                "delta": _rounded(float(corrected[index] - before)),
                "correction_types": ",".join(_correction_types(correction)),
                "display_form": str(correction.get("display_form") or ""),
                "admission_override": str(correction.get("admission_override") or ""),
                "topic_stretch_allowed": _topic_stretch_allowed(correction),
                "rationale": str(correction.get("rationale") or ""),
            }
        )
    return corrected, applications


def _is_active_correction(correction: Mapping[str, Any]) -> bool:
    if not correction:
        return False
    status = str(correction.get("status") or "active").strip().lower()
    return status in {"active", "accepted"}


def _correction_types(correction: Mapping[str, Any]) -> list[str]:
    raw = correction.get("correction_types")
    if raw is None:
        raw = correction.get("correction_type")
    if raw is None:
        return []
    if isinstance(raw, str):
        values = raw.split(",")
    elif isinstance(raw, Sequence):
        values = [str(value) for value in raw]
    else:
        values = [str(raw)]
    return [value.strip() for value in values if value and value.strip()]


def _topic_stretch_allowed(correction: Mapping[str, Any]) -> bool | str:
    if not correction:
        return ""
    correction_types = set(_correction_types(correction))
    admission = str(correction.get("admission_override") or "").strip()
    if "exclude_standalone_srs" in correction_types:
        return False
    if "restricted_admission" in correction_types:
        return False
    if admission and admission != NORMAL_ADMISSION_CLASS:
        return False
    return True


def _correction_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    applied = 0
    moved = 0
    max_delta = 0.0
    for row in rows:
        status = str(row.get("status") or "")
        status_counts[status] = status_counts.get(status, 0) + 1
        if bool(row.get("applied")):
            applied += 1
        delta = _optional_float(row.get("delta")) or 0.0
        if abs(delta) > 0.0005:
            moved += 1
            max_delta = max(max_delta, abs(delta))
    return {
        "correction_rows": len(rows),
        "status_counts": status_counts,
        "applied_count": applied,
        "moved_count": moved,
        "max_abs_score_delta": _rounded(max_delta),
        "rows": [dict(row) for row in rows],
    }


def _ranking_order(*, scores: np.ndarray, view: ComponentView) -> list[int]:
    def sort_key(index: int) -> tuple[float, float, str, str, int]:
        core_rank = float(view.core_ranks[index])
        if not np.isfinite(core_rank):
            core_rank = 999999999.0
        return (
            float(scores[index]),
            core_rank,
            str(view.lemmas[index]),
            str(view.readings[index]),
            index,
        )

    return sorted(range(len(scores)), key=sort_key)


def _ranking_row(
    *,
    rank: int,
    index: int,
    scores: np.ndarray,
    model_scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    evidence: Mapping[str, np.ndarray],
    corrections: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    lemma = str(view.lemmas[index])
    reading = str(view.readings[index])
    key = (lemma, reading)
    correction = corrections.get(key, {})
    display_form = str(correction.get("display_form") or "")
    admission_override = str(correction.get("admission_override") or "")
    correction_status = str(correction.get("status") or "")
    correction_types = _correction_types(correction)
    topic_stretch_allowed = _topic_stretch_allowed(correction)
    has_active_correction = _is_active_correction(correction)
    return {
        "rank": rank,
        "lemma": lemma,
        "reading": reading,
        "score": _rounded(float(scores[index])),
        "model_score": _rounded(float(model_scores[index])),
        "correction_delta": _rounded(float(scores[index] - model_scores[index])),
        "band": _score_band(float(scores[index])),
        "current": _rounded(float(current_scores[index])),
        "delta": _rounded(float(scores[index] - current_scores[index])),
        "core_rank": (
            _rounded(float(view.core_ranks[index]))
            if np.isfinite(float(view.core_ranks[index]))
            else None
        ),
        "candidate_state": str(view.candidate_states[index]),
        "correction_types": ",".join(correction_types),
        "display_form": display_form,
        "admission_override": admission_override,
        "topic_stretch_allowed": topic_stretch_allowed,
        "correction_status": correction_status,
        "correction_rationale": str(correction.get("rationale") or ""),
        "manual_correction_active": "yes" if has_active_correction else "",
        "manual_review": "yes" if key in MANUAL_WATCHLIST else "",
        "manual_note": MANUAL_WATCHLIST.get(key, ""),
        "review_flags": ",".join(_review_flags(index, scores=scores, evidence=evidence, key=key)),
        "exact_commonness": _rounded(float(evidence["exact_commonness"][index])),
        "jlpt_exact_known": _rounded(float(evidence["jlpt_exact_known"][index])),
        "jlpt_raw_exact_known": _rounded(float(evidence["jlpt_raw_exact_known"][index])),
        "jlpt_normalized_only_known": _rounded(
            float(evidence["jlpt_normalized_only_known"][index])
        ),
        "lesson_known": _rounded(float(evidence["lesson_known"][index])),
        "kana_preferred": _rounded(float(evidence["kana_preferred"][index])),
        "rare_wago_obscure_written": _rounded(float(evidence["rare_wago_obscure_written"][index])),
        "kanji_surface": _rounded(float(evidence["kanji_surface"][index])),
        "same_surface_risk": _rounded(float(evidence["same_surface_risk"][index])),
        "hard_form": _rounded(float(evidence["hard_form"][index])),
        "soft_form": _rounded(float(evidence["soft_form"][index])),
        "reading_inheritance": _rounded(float(evidence["reading_inheritance"][index])),
        "tail_guard": _rounded(float(evidence["tail_guard"][index])),
        "suspicion_full": _rounded(float(evidence["suspicion_full"][index])),
    }


def _review_flags(
    index: int,
    *,
    scores: np.ndarray,
    evidence: Mapping[str, np.ndarray],
    key: tuple[str, str],
) -> list[str]:
    flags = []
    score = float(scores[index])
    if key in MANUAL_WATCHLIST:
        flags.append("manual_watchlist")
    if (
        score <= 0.30
        and float(evidence["kana_preferred"][index]) >= 0.5
        and float(evidence["kanji_surface"][index]) >= 0.5
    ):
        flags.append("early_kana_preferred_kanji")
    if score <= 0.30 and float(evidence["same_surface_risk"][index]) >= 0.5:
        flags.append("early_same_surface_risk")
    if score <= 0.30 and float(evidence["jlpt_normalized_only_known"][index]) >= 0.5:
        flags.append("normalized_only_jlpt")
    if (
        score <= 0.30
        and float(evidence["exact_commonness"][index]) < 0.05
        and not any(
            float(evidence[key_name][index]) >= 0.5
            for key_name in ("jlpt_exact_known", "lesson_known")
        )
    ):
        flags.append("low_exact_support")
    return flags


def _band_counts(*, scores: np.ndarray) -> list[dict[str, Any]]:
    rows = []
    for start, end in _bands():
        mask = _band_mask(scores, start, end)
        rows.append(
            {
                "band": _band_label(start, end),
                "count": int(mask.sum()),
                "cumulative_count": int((scores < end if end < 1.0 else scores <= end).sum()),
            }
        )
    return rows


def _watchlist_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (str(row.get("lemma") or ""), str(row.get("reading") or "")): dict(row) for row in rows
    }
    return [
        {
            **by_key.get(key, {"lemma": key[0], "reading": key[1], "missing": True}),
            "watchlist_note": note,
        }
        for key, note in MANUAL_WATCHLIST.items()
    ]


def _flag_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        for flag in str(row.get("review_flags") or "").split(","):
            if flag:
                counts[flag] = counts.get(flag, 0) + 1
    return [{"flag": flag, "count": count} for flag, count in sorted(counts.items())]


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = [
        "rank",
        "lemma",
        "reading",
        "score",
        "model_score",
        "correction_delta",
        "band",
        "current",
        "delta",
        "core_rank",
        "candidate_state",
        "correction_types",
        "display_form",
        "admission_override",
        "topic_stretch_allowed",
        "correction_status",
        "correction_rationale",
        "manual_correction_active",
        "manual_review",
        "manual_note",
        "review_flags",
        "exact_commonness",
        "jlpt_exact_known",
        "jlpt_raw_exact_known",
        "jlpt_normalized_only_known",
        "lesson_known",
        "kana_preferred",
        "rare_wago_obscure_written",
        "kanji_surface",
        "same_surface_risk",
        "hard_form",
        "soft_form",
        "reading_inheritance",
        "tail_guard",
        "suspicion_full",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(report: Mapping[str, Any]) -> str:
    method = _mapping(report.get("method"))
    metrics = _mapping(report.get("variant_metrics"))
    all_summary = _mapping(metrics.get("all_summary"))
    first_review_count = method.get("first_review_count") or FIRST_REVIEW_COUNT
    lines = [
        "# en-ja Learner Difficulty Final Ranking Review",
        "",
        "## Summary",
        "",
        f"- Variant: `{_escape(method.get('variant_id'))}`",
        f"- Base candidate: `{_escape(method.get('base_candidate_id'))}`",
        f"- Full ranking CSV: `{_escape(_mapping(report.get('outputs')).get('full_ranking_csv'))}`",
        f"- Component count: `{_escape(_mapping(report.get('inputs')).get('component_count'))}`",
        f"- Manual corrections applied: `{_escape(method.get('manual_corrections_applied'))}`",
        f"- Selection score: `{_escape(metrics.get('selection_score'))}`",
        f"- MAE: `{_escape(all_summary.get('mae'))}`",
        f"- Pairwise accuracy: `{_escape(all_summary.get('pairwise_accuracy'))}`",
        f"- Improved/regressed labels >=0.01: `{_escape(metrics.get('label_improved_count_0p01'))}` / `{_escape(metrics.get('label_regressed_count_0p01'))}`",
        "",
        "The full ranking is sorted by final score, then core rank, then surface and reading.",
        "",
        "## Band Counts",
        "",
        _band_count_table(report.get("band_counts") or []),
        "",
        "## Manual Correction Summary",
        "",
        _correction_table(_mapping(report.get("correction_summary")).get("rows") or []),
        "",
        f"## First {first_review_count} Review Rows",
        "",
        _ranking_table(report.get("first_rows") or []),
        "",
        "## Manual Watchlist Rows",
        "",
        _ranking_table(report.get("manual_watchlist_rows") or []),
        "",
        f"## First {first_review_count} Flag Summary",
        "",
        _flag_summary_table(report.get("first_row_review_flags") or []),
        "",
    ]
    return "\n".join(lines)


def _band_count_table(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "| Band | Count | Cumulative |",
        "| --- | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape(cell)
                for cell in (
                    str(row.get("band") or ""),
                    str(row.get("count") or 0),
                    str(row.get("cumulative_count") or 0),
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _ranking_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Rank | Word | Score | Model | Correction | Current | Core rank | Flags |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        word = f"{row.get('lemma')}/{row.get('reading')}"
        flags = str(row.get("review_flags") or row.get("watchlist_note") or "")
        if row.get("correction_types"):
            flags = ",".join(value for value in (flags, str(row.get("correction_types"))) if value)
        if row.get("admission_override"):
            flags = ",".join(
                value for value in (flags, str(row.get("admission_override"))) if value
            )
        if row.get("display_form"):
            flags = ",".join(
                value for value in (flags, f"display={row.get('display_form')}") if value
            )
        lines.append(
            "| "
            + " | ".join(
                _escape(cell)
                for cell in (
                    str(row.get("rank") or ""),
                    word,
                    _fmt(row.get("score")),
                    _fmt(row.get("model_score")),
                    _fmt(row.get("correction_delta")),
                    _fmt(row.get("current")),
                    _fmt(row.get("core_rank")),
                    flags,
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _correction_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No manual correction layer loaded._"
    lines = [
        "| Row | Status | Types | Applied | Model | Effective | Delta | Display | Admission | Topic stretch |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        word = f"{row.get('lemma')}/{row.get('reading')}"
        lines.append(
            "| "
            + " | ".join(
                _escape(cell)
                for cell in (
                    word,
                    str(row.get("status") or ""),
                    str(row.get("correction_types") or ""),
                    str(row.get("applied") or False),
                    _fmt(row.get("model_score")),
                    _fmt(row.get("effective_score")),
                    _fmt(row.get("delta")),
                    str(row.get("display_form") or ""),
                    str(row.get("admission_override") or ""),
                    _text(row.get("topic_stretch_allowed")),
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _flag_summary_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No flags._"
    lines = ["| Flag | Count |", "| --- | ---: |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape(cell) for cell in (str(row.get("flag") or ""), str(row.get("count") or 0))
            )
            + " |"
        )
    return "\n".join(lines)


def _bands() -> list[tuple[float, float]]:
    return [(index / 20.0, (index + 1) / 20.0) for index in range(20)]


def _band_mask(scores: np.ndarray, start: float, end: float) -> np.ndarray:
    if end >= 1.0:
        return (scores >= start) & (scores <= end)
    return (scores >= start) & (scores < end)


def _band_label(start: float, end: float) -> str:
    return f"{start:.2f}-{end:.2f}"


def _score_band(score: float) -> str:
    bounded = min(max(score, 0.0), 1.0)
    index = min(19, int(bounded * 20.0))
    return _band_label(index / 20.0, (index + 1) / 20.0)


def _fmt(value: Any) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.3f}"


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _resolve_path(value: Path) -> Path:
    if value.is_absolute():
        return value
    return (PROJECT_ROOT / value).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
