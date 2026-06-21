#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _load_json,
    _mapping,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_tail_partition_search_en_ja import (  # noqa: E402
    DEFAULT_BASE_CANDIDATE,
    DEFAULT_BASE_FAMILY_JSON,
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_TAIL_CANDIDATE,
    DEFAULT_TAIL_TREE_JSON,
    _family_candidate_raw,
    _tail_candidates,
    _tree_candidate_raw,
)


DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_q15_review_pack_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_q15_review_pack_en_ja_latest.md"
)
REVIEW_CANDIDATES = ("base_reference", "raw_replace_q20", "soft_blend_q15_s75")
TARGET_WINDOWS = (
    (0.00, 0.00, 0.10),
    (0.25, 0.20, 0.30),
    (0.50, 0.45, 0.55),
    (0.75, 0.70, 0.80),
    (1.00, 0.90, 1.00),
)
UPPER_BANDS = tuple(
    (round(start, 2), round(start + 0.05, 2)) for start in np.arange(0.65, 1.0, 0.05)
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a focused product-review pack for the current en-ja q15 "
            "learner-difficulty research candidate."
        )
    )
    parser.add_argument("--base-family-json", type=Path, default=DEFAULT_BASE_FAMILY_JSON)
    parser.add_argument("--tail-tree-json", type=Path, default=DEFAULT_TAIL_TREE_JSON)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--base-candidate", default=DEFAULT_BASE_CANDIDATE)
    parser.add_argument("--tail-candidate", default=DEFAULT_TAIL_CANDIDATE)
    parser.add_argument("--sample-count", type=int, default=12)
    parser.add_argument("--band-sample-count", type=int, default=10)
    parser.add_argument("--divergence-limit", type=int, default=24)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        base_family_json=_resolve_path(args.base_family_json),
        tail_tree_json=_resolve_path(args.tail_tree_json),
        component_matrix_path=_resolve_path(args.component_matrix),
        base_candidate_id=str(args.base_candidate),
        tail_candidate_id=str(args.tail_candidate),
        sample_count=max(1, int(args.sample_count)),
        band_sample_count=max(1, int(args.band_sample_count)),
        divergence_limit=max(1, int(args.divergence_limit)),
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
    base_family_json: Path,
    tail_tree_json: Path,
    component_matrix_path: Path,
    base_candidate_id: str,
    tail_candidate_id: str,
    sample_count: int,
    band_sample_count: int,
    divergence_limit: int,
) -> dict[str, object]:
    component = np.load(component_matrix_path)
    base_raw = _family_candidate_raw(
        _load_json(base_family_json),
        component=component,
        candidate_id=base_candidate_id,
    )
    tail_raw = _tree_candidate_raw(
        _load_json(tail_tree_json),
        component=component,
        candidate_id=tail_candidate_id,
    )
    candidates = _tail_candidates(
        base_raw=base_raw,
        tail_raw=tail_raw,
        target_positions=np.asarray(component["target_curve_positions"], dtype=np.float32),
        tail_quantiles=(0.15, 0.20),
        soft_strengths=(0.75, 1.0),
    )
    values_by_id = {
        candidate.candidate_id: np.asarray(candidate.normalized, dtype=np.float32)
        for candidate in candidates
        if candidate.candidate_id in REVIEW_CANDIDATES
    }
    if set(REVIEW_CANDIDATES) - set(values_by_id):
        missing = ", ".join(sorted(set(REVIEW_CANDIDATES) - set(values_by_id)))
        raise ValueError(f"missing review candidates: {missing}")
    q15 = values_by_id["soft_blend_q15_s75"]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "base_family_json": base_family_json,
                "tail_tree_json": tail_tree_json,
                "component_matrix": component_matrix_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "difficulty_normalization": (
                    SCRIPT_DIR / "srs_learner_difficulty_normalization.py"
                ),
                "difficulty_piecewise_search": (
                    SCRIPT_DIR / "srs_learner_difficulty_piecewise_search_en_ja.py"
                ),
                "difficulty_tail_partition_search": (
                    SCRIPT_DIR / "srs_learner_difficulty_tail_partition_search_en_ja.py"
                ),
                "difficulty_q15_review_pack": Path(__file__),
            },
            version_constants={"target_curve": TARGET_CURVE_ID},
            argv=sys.argv,
        ),
        "purpose": (
            "Focused qualitative review pack for q15; samples are difficulty-target "
            "proxies and not installed runtime selector output."
        ),
        "inputs": {
            "base_family_json": _repo_or_home_path(base_family_json),
            "tail_tree_json": _repo_or_home_path(tail_tree_json),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "base_candidate_id": base_candidate_id,
            "tail_candidate_id": tail_candidate_id,
            "review_candidate_ids": list(REVIEW_CANDIDATES),
            "normalization_population_count": int(len(q15)),
        },
        "target_window_samples": _target_window_samples(
            q15,
            component=component,
            values_by_id=values_by_id,
            sample_count=sample_count,
        ),
        "upper_band_samples": _upper_band_samples(
            q15,
            component=component,
            values_by_id=values_by_id,
            sample_count=band_sample_count,
        ),
        "divergence": {
            "q20_promotes_over_q15": _divergence_rows(
                q15,
                values_by_id["raw_replace_q20"],
                component=component,
                values_by_id=values_by_id,
                direction="other_higher",
                minimum_q15=0.65,
                limit=divergence_limit,
            ),
            "q15_promotes_over_base": _divergence_rows(
                q15,
                values_by_id["base_reference"],
                component=component,
                values_by_id=values_by_id,
                direction="q15_higher",
                minimum_q15=0.65,
                limit=divergence_limit,
            ),
            "base_promotes_over_q15": _divergence_rows(
                q15,
                values_by_id["base_reference"],
                component=component,
                values_by_id=values_by_id,
                direction="other_higher",
                minimum_q15=0.65,
                limit=divergence_limit,
            ),
        },
    }


def _target_window_samples(
    q15_values: object,
    *,
    component: object,
    values_by_id: Mapping[str, object],
    sample_count: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    values = np.asarray(q15_values, dtype=np.float32)
    for target, start, end in TARGET_WINDOWS:
        indices = _window_indices(values, start=start, end=end)
        sampled = _evenly_spaced_indices(indices, sample_count=sample_count)
        rows.append(
            {
                "target": _rounded(target),
                "window": f"{start:.2f}-{end:.2f}",
                "row_count": int(len(indices)),
                "samples": [
                    _row_snapshot(index, values_by_id=values_by_id, component=component)
                    for index in sampled
                ],
            }
        )
    return rows


def _upper_band_samples(
    q15_values: object,
    *,
    component: object,
    values_by_id: Mapping[str, object],
    sample_count: int,
) -> list[dict[str, object]]:
    values = np.asarray(q15_values, dtype=np.float32)
    bands: list[dict[str, object]] = []
    for start, end in UPPER_BANDS:
        indices = _window_indices(values, start=start, end=end)
        sampled = _evenly_spaced_indices(indices, sample_count=sample_count)
        bands.append(
            {
                "band": f"{start:.2f}-{end:.2f}",
                "row_count": int(len(indices)),
                "samples": [
                    _row_snapshot(index, values_by_id=values_by_id, component=component)
                    for index in sampled
                ],
            }
        )
    return bands


def _divergence_rows(
    q15_values: object,
    other_values: object,
    *,
    component: object,
    values_by_id: Mapping[str, object],
    direction: str,
    minimum_q15: float,
    limit: int,
) -> list[dict[str, object]]:
    q15 = np.asarray(q15_values, dtype=np.float32)
    other = np.asarray(other_values, dtype=np.float32)
    if direction == "q15_higher":
        delta = q15 - other
    elif direction == "other_higher":
        delta = other - q15
    else:
        raise ValueError(f"unknown divergence direction: {direction}")
    eligible = np.where((q15 >= minimum_q15) & np.isfinite(delta) & (delta >= 0.03))[0]
    ordered = eligible[np.argsort(delta[eligible], kind="stable")[::-1]]
    return [
        _row_snapshot(int(index), values_by_id=values_by_id, component=component)
        | {"selected_delta": _rounded(float(delta[int(index)]))}
        for index in ordered[:limit]
    ]


def _window_indices(values: object, *, start: float, end: float) -> object:
    parsed = np.asarray(values, dtype=np.float32)
    if end >= 1.0:
        indices = np.where((parsed >= start) & (parsed <= end))[0]
    else:
        indices = np.where((parsed >= start) & (parsed < end))[0]
    order = np.argsort(parsed[indices], kind="stable")
    return indices[order]


def _evenly_spaced_indices(indices: object, *, sample_count: int) -> list[int]:
    parsed = np.asarray(indices, dtype=np.int64)
    if len(parsed) <= sample_count:
        return [int(index) for index in parsed]
    offsets = np.linspace(0, len(parsed) - 1, num=sample_count, dtype=np.int64)
    return [int(parsed[offset]) for offset in offsets]


def _row_snapshot(
    index: int,
    *,
    values_by_id: Mapping[str, object],
    component: object,
) -> dict[str, object]:
    q15 = float(np.asarray(values_by_id["soft_blend_q15_s75"], dtype=np.float32)[index])
    base = float(np.asarray(values_by_id["base_reference"], dtype=np.float32)[index])
    q20 = float(np.asarray(values_by_id["raw_replace_q20"], dtype=np.float32)[index])
    return {
        "lemma": str(component["lemmas"][index]),
        "reading": str(component["readings"][index]),
        "candidate_state": str(component["candidate_states"][index]),
        "problem_class": str(component["problem_classes"][index]),
        "core_rank": _rounded(float(component["core_ranks"][index])),
        "base": _rounded(base),
        "q15": _rounded(q15),
        "q20": _rounded(q20),
        "q15_minus_base": _rounded(q15 - base),
        "q20_minus_q15": _rounded(q20 - q15),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja q15 Learner-Difficulty Review Pack",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Normalization population: `{_escape(inputs.get('normalization_population_count'))}`",
        "- Candidate under review: `soft_blend_q15_s75`",
        "- Comparison candidates: `base_reference`, `raw_replace_q20`",
        "",
        "These are difficulty-target proxy samples for qualitative review. They are not installed runtime selector output.",
        "",
        "## Difficulty-Target Proxy Samples",
        "",
    ]
    for window in _rows(report.get("target_window_samples")):
        lines.append(
            f"### Target `{_escape(window.get('target'))}` "
            f"window `{_escape(window.get('window'))}` "
            f"rows `{_escape(window.get('row_count'))}`"
        )
        lines.extend(_sample_table(_rows(window.get("samples"))))
        lines.append("")
    lines.extend(["## q15 Upper-Band Samples", ""])
    for band in _rows(report.get("upper_band_samples")):
        lines.append(
            f"### Band `{_escape(band.get('band'))}` rows `{_escape(band.get('row_count'))}`"
        )
        lines.extend(_sample_table(_rows(band.get("samples"))))
        lines.append("")
    lines.extend(["## Divergence Examples", ""])
    divergence = _mapping(report.get("divergence"))
    for key, title in (
        ("q20_promotes_over_q15", "q20 promotes over q15"),
        ("q15_promotes_over_base", "q15 promotes over base"),
        ("base_promotes_over_q15", "base promotes over q15"),
    ):
        lines.append(f"### {title}")
        lines.extend(_sample_table(_rows(divergence.get(key)), include_selected_delta=True))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _sample_table(
    rows: Sequence[Mapping[str, object]],
    *,
    include_selected_delta: bool = False,
) -> list[str]:
    headers = [
        "Lemma",
        "Reading",
        "q15",
        "Base",
        "q20",
        "q15-Base",
        "q20-q15",
        "Class",
        "Rank",
    ]
    if include_selected_delta:
        headers.append("Selected Delta")
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = [
            _escape(row.get("lemma")),
            _escape(row.get("reading")),
            _escape(row.get("q15")),
            _escape(row.get("base")),
            _escape(row.get("q20")),
            _escape(row.get("q15_minus_base")),
            _escape(row.get("q20_minus_q15")),
            _escape(row.get("problem_class")),
            _escape(row.get("core_rank")),
        ]
        if include_selected_delta:
            values.append(_escape(row.get("selected_delta")))
        lines.append("| " + " | ".join(f"`{value}`" for value in values) + " |")
    return lines


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
