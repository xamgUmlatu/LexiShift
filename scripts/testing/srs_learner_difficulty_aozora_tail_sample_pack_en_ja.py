#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    DEFAULT_AOZORA_SQLITE,
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_SOURCE_ARBITRATION_JSON,
    DEFAULT_VALIDATION_JSON,
    _aozora_feature_arrays,
    _component_signal_arrays,
    _current_scores,
    _load_json,
    _resolve_path,
    _sample_row,
    _selected_candidate_metadata,
    _tail_variant_terms,
    _variant_specs,
    ComponentView,
    _view_with_target_curve_override,
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


PAIR = "en-ja"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_tail_sample_pack_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_aozora_tail_sample_pack_en_ja_latest.md"
)
DEFAULT_VARIANTS = (
    "current",
    # Cautious top refined variant: no >0.01 regressions in the reviewed labels.
    "aoztail_refine_gl68_gu94_al02_or12_mr04_od100_db00_ts92_tt100_ab00_rb50",
    # Same refined family with dirty-risk blocking on attestation lowering.
    "aoztail_refine_gl68_gu94_al02_or12_mr04_od100_db75_ts92_tt100_ab00_rb50",
    # Aggressive variant with strongest tail-label gains.
    "aoztail_base_gl55_gu82_al02_or12_mr04_od100_db00_ts101_tt00_ab00_rb100",
    # Aggressive dirty-risk blocked contrast.
    "aoztail_base_gl55_gu82_al02_or12_mr04_od100_db75_ts101_tt00_ab00_rb100",
)
VARIANT_ALIASES = {
    "current": "current",
    "aoztail_refine_gl68_gu94_al02_or12_mr04_od100_db00_ts92_tt100_ab00_rb50": "cautious",
    "aoztail_refine_gl68_gu94_al02_or12_mr04_od100_db75_ts92_tt100_ab00_rb50": "cautious_guarded",
    "aoztail_base_gl55_gu82_al02_or12_mr04_od100_db00_ts101_tt00_ab00_rb100": "aggressive",
    "aoztail_base_gl55_gu82_al02_or12_mr04_od100_db75_ts101_tt00_ab00_rb100": "aggressive_guarded",
}
REVIEW_BANDS = (
    (0.60, 0.70),
    (0.70, 0.80),
    (0.80, 0.90),
    (0.90, 1.01),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate qualitative en-ja Aozora-tail sample packs for selected "
            "current/cautious/aggressive difficulty variants."
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
        "--variant-id",
        action="append",
        default=[],
        help="Variant id to include. Defaults to current, cautious, guarded, and aggressive variants.",
    )
    parser.add_argument("--sample-per-band", type=int, default=18)
    parser.add_argument("--move-limit", type=int, default=35)
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
        variant_ids=tuple(args.variant_id) or DEFAULT_VARIANTS,
        sample_per_band=max(1, int(args.sample_per_band)),
        move_limit=max(1, int(args.move_limit)),
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
    variant_ids: Sequence[str],
    sample_per_band: int,
    move_limit: int,
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
    aozora = _aozora_feature_arrays(view=view, aozora_sqlite=aozora_sqlite)
    component_signals = _component_signal_arrays(view)
    variant_scores, variant_terms = _selected_variant_scores(
        variant_ids=variant_ids,
        current_scores=current_scores,
        target_positions=np.asarray(view.target_positions, dtype=np.float32),
        aozora=aozora,
        component_signals=component_signals,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "model_behavior_changed": False,
        "method": {
            "purpose": (
                "Qualitative side-by-side review samples for current, cautious, "
                "guarded, and aggressive Aozora-tail variants, including direct "
                "term and normalization decomposition."
            ),
            "candidate_id": selected["candidate_id"],
            "candidate_family": selected["candidate_family"],
            "target_curve_override": selected["target_curve_override"],
        },
        "inputs": {
            "source_arbitration_json": _repo_or_home_path(source_arbitration_json),
            "component_matrix": _repo_or_home_path(component_matrix),
            "calibration_json": _repo_or_home_path(calibration_json),
            "holdout_json": _repo_or_home_path(holdout_json),
            "validation_json": _repo_or_home_path(validation_json),
            "aozora_sqlite": _repo_or_home_path(aozora_sqlite),
            "component_count": int(len(current_scores)),
            "variant_ids": list(variant_scores.keys()),
        },
        "band_samples": _band_samples(
            variant_scores=variant_scores,
            variant_terms=variant_terms,
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            per_band=sample_per_band,
        ),
        "move_comparisons": _move_comparisons(
            variant_scores=variant_scores,
            variant_terms=variant_terms,
            current_scores=current_scores,
            view=view,
            aozora=aozora,
            limit=move_limit,
        ),
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
                "aozora_tail_bakeoff": (
                    SCRIPT_DIR / "srs_learner_difficulty_aozora_tail_bakeoff_en_ja.py"
                ),
                "aozora_tail_sample_pack": Path(__file__),
            },
            argv=sys.argv,
        ),
    }


def _selected_variant_scores(
    *,
    variant_ids: Sequence[str],
    current_scores: np.ndarray,
    target_positions: np.ndarray,
    aozora: Mapping[str, Any],
    component_signals: Mapping[str, np.ndarray],
) -> tuple[dict[str, np.ndarray], dict[str, Mapping[str, np.ndarray]]]:
    variants = {str(variant["variant_id"]): variant for variant in _variant_specs()}
    scores = {}
    terms_by_variant: dict[str, Mapping[str, np.ndarray]] = {}
    for variant_id in variant_ids:
        if variant_id == "current":
            scores[variant_id] = np.asarray(current_scores, dtype=np.float32)
            terms_by_variant[variant_id] = {}
            continue
        variant = variants.get(str(variant_id))
        if variant is None:
            raise SystemExit(f"Unknown variant id: {variant_id}")
        terms = _tail_variant_terms(
            current_scores=current_scores,
            target_positions=target_positions,
            aozora=aozora,
            component_signals=component_signals,
            variant=variant,
        )
        scores[str(variant_id)] = np.asarray(terms["final_scores"], dtype=np.float32)
        terms_by_variant[str(variant_id)] = terms
    return scores, terms_by_variant


def _band_samples(
    *,
    variant_scores: Mapping[str, np.ndarray],
    variant_terms: Mapping[str, Mapping[str, np.ndarray]],
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
    per_band: int,
) -> list[dict[str, Any]]:
    output = []
    for start, end in REVIEW_BANDS:
        variants = []
        for variant_id, scores in variant_scores.items():
            if end >= 1.0:
                mask = (scores >= start) & (scores <= end)
            else:
                mask = (scores >= start) & (scores < end)
            indices = np.where(mask)[0]
            ordered = indices[np.argsort(scores[indices], kind="stable")]
            sample_indices = _quantile_indices(ordered, per_band)
            variants.append(
                {
                    "variant_id": variant_id,
                    "count": int(len(indices)),
                    "samples": [
                        _sample_row_with_terms(
                            int(index),
                            scores=scores,
                            current_scores=current_scores,
                            view=view,
                            aozora=aozora,
                            terms=variant_terms.get(variant_id) or {},
                        )
                        for index in sample_indices
                    ],
                }
            )
        output.append(
            {
                "band": f"{start:.2f}-{min(end, 1.0):.2f}",
                "variants": variants,
            }
        )
    return output


def _move_comparisons(
    *,
    variant_scores: Mapping[str, np.ndarray],
    variant_terms: Mapping[str, Mapping[str, np.ndarray]],
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
    limit: int,
) -> list[dict[str, Any]]:
    output = []
    for variant_id, scores in variant_scores.items():
        if variant_id == "current":
            continue
        delta = scores - current_scores
        tail_mask = (scores >= 0.50) | (current_scores >= 0.50)
        down_indices = [
            int(index)
            for index in np.argsort(delta, kind="stable")
            if tail_mask[index] and delta[index] < -0.001
        ][:limit]
        up_indices = [
            int(index)
            for index in np.argsort(-delta, kind="stable")
            if tail_mask[index] and delta[index] > 0.001
        ][:limit]
        output.append(
            {
                "variant_id": variant_id,
                "largest_down": [
                    _comparison_row(
                        index,
                        primary_variant_id=variant_id,
                        variant_scores=variant_scores,
                        variant_terms=variant_terms,
                        current_scores=current_scores,
                        view=view,
                        aozora=aozora,
                    )
                    for index in down_indices
                ],
                "largest_up": [
                    _comparison_row(
                        index,
                        primary_variant_id=variant_id,
                        variant_scores=variant_scores,
                        variant_terms=variant_terms,
                        current_scores=current_scores,
                        view=view,
                        aozora=aozora,
                    )
                    for index in up_indices
                ],
            }
        )
    return output


def _comparison_row(
    index: int,
    *,
    primary_variant_id: str,
    variant_scores: Mapping[str, np.ndarray],
    variant_terms: Mapping[str, Mapping[str, np.ndarray]],
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
) -> dict[str, Any]:
    base = _sample_row(
        index,
        scores=current_scores,
        current_scores=current_scores,
        view=view,
        aozora=aozora,
    )
    return {
        **base,
        **_terms_for_index(variant_terms.get(primary_variant_id) or {}, index),
        "scores": {
            variant_id: _rounded(float(scores[index]))
            for variant_id, scores in variant_scores.items()
        },
    }


def _sample_row_with_terms(
    index: int,
    *,
    scores: np.ndarray,
    current_scores: np.ndarray,
    view: ComponentView,
    aozora: Mapping[str, Any],
    terms: Mapping[str, np.ndarray],
) -> dict[str, Any]:
    return {
        **_sample_row(
            index,
            scores=scores,
            current_scores=current_scores,
            view=view,
            aozora=aozora,
        ),
        **_terms_for_index(terms, index),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    method = _mapping(report.get("method"))
    lines = [
        "# en-ja Aozora Tail Qualitative Sample Pack",
        "",
        "## Summary",
        "",
        f"- Candidate: `{_escape(method.get('candidate_id'))}`",
        f"- Candidate family: `{_escape(method.get('candidate_family'))}`",
        f"- Target curve: `{_escape(method.get('target_curve_override'))}`",
        f"- Variants: `{_escape(', '.join(_variant_label(variant_id) for variant_id in _mapping(report.get('inputs')).get('variant_ids') or []))}`",
        "",
        "This is a qualitative review artifact only. It does not change scorer behavior.",
        "",
        "## Band Samples",
        "",
    ]
    for band in report.get("band_samples") or []:
        band_row = _mapping(band)
        lines.extend([f"### {band_row.get('band')}", ""])
        for variant in band_row.get("variants") or []:
            variant_row = _mapping(variant)
            lines.extend(
                [
                    f"#### `{_escape(_variant_label(variant_row.get('variant_id')))}` count `{_escape(variant_row.get('count'))}`",
                    "",
                    f"Variant id: `{_escape(variant_row.get('variant_id'))}`",
                    "",
                    _sample_table(variant_row.get("samples") or []),
                    "",
                ]
            )
    lines.extend(["## Largest Move Comparisons", ""])
    for comparison in report.get("move_comparisons") or []:
        row = _mapping(comparison)
        lines.extend(
            [
                f"### `{_escape(_variant_label(row.get('variant_id')))}`",
                "",
                f"Variant id: `{_escape(row.get('variant_id'))}`",
                "",
                "Largest down moves:",
                "",
                _comparison_table(row.get("largest_down") or []),
                "",
                "Largest up moves:",
                "",
                _comparison_table(row.get("largest_up") or []),
                "",
            ]
        )
    lines.extend(
        [
            "## Caveats",
            "",
            "- Samples are quantile picks within each variant's score band, not hand-picked examples.",
            "- Aozora context is book/literary evidence, so high attestation still needs qualitative judgment.",
            "- The comparison tables use the same row and show how each selected variant scores it.",
            "",
        ]
    )
    return "\n".join(lines)


def _sample_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Word | Score | Current | Delta | Direct | Norm | Lower | OldRaise | Missing | Gate | Attest | NoEv | Aozora | Tok | Works | Conf | Old | Hard | Access | ModChild |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_escape(cell) for cell in _sample_cells(row)) + " |")
    return "\n".join(lines)


def _comparison_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    variant_ids = list(_mapping(rows[0].get("scores")).keys())
    headers = [
        "Word",
        *(_variant_label(variant_id) for variant_id in variant_ids),
        "FinalD",
        "Direct",
        "Norm",
        "Lower",
        "OldRaise",
        "Missing",
        "Aozora",
        "Tok",
        "Works",
        "Conf",
        "Old",
        "Hard",
        "Access",
        "ModChild",
    ]
    lines = [
        "| " + " | ".join(_escape(header) for header in headers) + " |",
        "| " + " | ".join(["---", *["---:" for _ in headers[1:]]]) + " |",
    ]
    for row in rows:
        scores = _mapping(row.get("scores"))
        cells = [
            _label(row),
            *(_fmt(scores.get(variant_id)) for variant_id in variant_ids),
            _fmt(row.get("final_delta")),
            _fmt(row.get("direct_delta")),
            _fmt(row.get("normalization_delta")),
            _fmt(row.get("lower_delta")),
            _fmt(row.get("old_raise_delta")),
            _fmt(row.get("missing_delta")),
            str(row.get("match_status") or ""),
            str(row.get("token_count") or 0),
            str(row.get("work_count") or 0),
            _fmt(row.get("confidence")),
            _fmt(row.get("old_risk")),
            _fmt(row.get("hard")),
            _fmt(row.get("access")),
            _fmt(row.get("modern_child")),
        ]
        lines.append("| " + " | ".join(_escape(cell) for cell in cells) + " |")
    return "\n".join(lines)


def _sample_cells(row: Mapping[str, Any]) -> list[str]:
    return [
        _label(row),
        _fmt(row.get("score")),
        _fmt(row.get("current")),
        _fmt(row.get("delta")),
        _fmt(row.get("direct_delta")),
        _fmt(row.get("normalization_delta")),
        _fmt(row.get("lower_delta")),
        _fmt(row.get("old_raise_delta")),
        _fmt(row.get("missing_delta")),
        _fmt(row.get("tail_gate")),
        _fmt(row.get("attestation")),
        _fmt(row.get("no_evidence")),
        str(row.get("match_status") or ""),
        str(row.get("token_count") or 0),
        str(row.get("work_count") or 0),
        _fmt(row.get("confidence")),
        _fmt(row.get("old_risk")),
        _fmt(row.get("hard")),
        _fmt(row.get("access")),
        _fmt(row.get("modern_child")),
    ]


def _label(row: Mapping[str, Any]) -> str:
    return (
        f"{row.get('lemma')}/{row.get('reading')}"
        if row.get("reading")
        else str(row.get("lemma") or "")
    )


def _terms_for_index(terms: Mapping[str, np.ndarray], index: int) -> dict[str, Any]:
    if not terms:
        return {}
    fields = (
        "attestation",
        "no_evidence",
        "tail_gate",
        "lower_delta",
        "old_raise_delta",
        "missing_delta",
        "direct_delta",
        "normalization_delta",
        "final_delta",
    )
    return {
        field: _rounded(float(np.asarray(terms[field], dtype=np.float32)[index]))
        for field in fields
        if field in terms
    }


def _variant_label(variant_id: Any) -> str:
    return VARIANT_ALIASES.get(str(variant_id), str(variant_id))


def _quantile_indices(indices: np.ndarray, count: int) -> list[int]:
    if len(indices) == 0:
        return []
    offsets = np.linspace(0, len(indices) - 1, num=min(count, len(indices)), dtype=int)
    return [int(indices[offset]) for offset in offsets]


def _fmt(value: Any) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.3f}"


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


if __name__ == "__main__":
    raise SystemExit(main())
