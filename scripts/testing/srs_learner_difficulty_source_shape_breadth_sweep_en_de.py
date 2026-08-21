#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_metrics,
    _summary_metrics,
)


PAIR = "en-de"
PRIMARY_STATE = "normal_vocab"
DEFAULT_ROWS_JSONL = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_de_rows_latest.jsonl"
)
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_de.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_de.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_shape_breadth_sweep_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_shape_breadth_sweep_en_de_latest.md"
)
SOURCE_GROUPS = (
    "openlingo_known",
    "odenet_only",
    "goethe_only",
    "any_learner_source",
    "wiktionary_guard_signal",
    "source_conflict",
    "no_learner_source",
)


@dataclass(frozen=True)
class BaseProfile:
    profile_id: str
    rank_weight: float
    rank_gamma: float
    pmw_gamma: float
    warp_gamma: float
    raw_frequency: bool
    description: str


@dataclass(frozen=True)
class SourceShape:
    shape_id: str
    family: str
    mode: str
    params: Mapping[str, object]
    description: str


@dataclass(frozen=True)
class BreadthCandidate:
    candidate_id: str
    base_profile: BaseProfile
    source_shape: SourceShape


@dataclass(frozen=True)
class SourceEvidence:
    source_id: str
    target: float
    strength: float
    trust: float


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a sidecar en-de source-use breadth sweep. The sweep freezes base "
            "frequency curves to a small set and varies learner/Wiktionary source-use "
            "shapes deliberately, so it can test source hypotheses without expanding the "
            "older full formula sweep."
        )
    )
    parser.add_argument("--rows-jsonl", type=Path, default=DEFAULT_ROWS_JSONL)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=0,
        help="Optional deterministic cap for smoke runs. Zero evaluates all candidates.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        signal_rows=_load_jsonl(Path(args.rows_jsonl).expanduser()),
        calibration_payload=_load_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_json(Path(args.holdout_json).expanduser()),
        max_candidates=max(0, int(args.max_candidates)),
    )
    json_out = Path(args.json_out).expanduser().resolve(strict=False)
    markdown_out = Path(args.markdown_out).expanduser().resolve(strict=False)
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
    signal_rows: Sequence[Mapping[str, object]],
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    max_candidates: int = 0,
    generated_at: str | None = None,
) -> dict[str, object]:
    rows = [dict(row) for row in signal_rows if str(row.get("lemma") or "").strip()]
    if not rows:
        raise ValueError("signal_rows must contain rows")
    rows_by_lemma = {str(row.get("lemma") or "").strip().lower(): row for row in rows}
    calibration_labels = [
        _as_mapping(row) for row in _as_sequence(calibration_payload.get("labels"))
    ]
    holdout_labels = [_as_mapping(row) for row in _as_sequence(holdout_payload.get("labels"))]
    candidates = list(generate_candidates())
    if max_candidates:
        candidates = candidates[:max_candidates]

    records = [
        _candidate_record(
            candidate=candidate,
            rows=rows,
            rows_by_lemma=rows_by_lemma,
            calibration_labels=calibration_labels,
            holdout_labels=holdout_labels,
        )
        for candidate in candidates
    ]
    raw_frequency_record = next(
        (record for record in records if record.get("candidate_id") == "raw_frequency_blend__none"),
        {},
    )
    legacy_current_record = next(
        (
            record
            for record in records
            if record.get("candidate_id") == "current_best_curve__legacy_openlingo50_floor25"
        ),
        {},
    )
    calibration_top = sorted(records, key=_calibration_sort_key, reverse=True)[:30]
    holdout_guarded_top = sorted(records, key=_holdout_guarded_sort_key, reverse=True)[:30]
    stable_top = sorted(records, key=_stable_sort_key, reverse=True)[:30]
    selected = _unique_records(
        calibration_top[:5]
        + holdout_guarded_top[:5]
        + stable_top[:5]
        + [legacy_current_record, raw_frequency_record],
        key="candidate_id",
    )
    selected_details = [
        _with_change_samples(
            record,
            rows=rows,
            candidate=_candidate_by_id(candidates, str(record.get("candidate_id"))),
            sample_limit=14,
        )
        for record in selected
        if record
    ]
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_de_learner_difficulty_source_shape_breadth_sweep_ready",
        "generated_at": generated_at or _utc_now(),
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "method": {
            "purpose": (
                "Breadth-test source-use shapes after adding en-de learner-source and "
                "Wiktionary metadata signals. This intentionally limits base curves so "
                "source arbitration structure is visible."
            ),
            "candidate_count": len(candidates),
            "base_profile_count": len(generate_base_profiles()),
            "source_shape_count": len(generate_source_shapes()),
            "primary_score_policy": (
                "Primary metrics exclude labels whose expected_candidate_state is not "
                "`normal_vocab`; restricted rows remain product-cleanup evidence, not "
                "numeric formula targets."
            ),
            "shape_families": sorted({shape.family for shape in generate_source_shapes()}),
            "source_groups": list(SOURCE_GROUPS),
        },
        "inputs": {
            "signal_row_count": len(rows),
            "calibration_id": calibration_payload.get("calibration_id"),
            "holdout_id": holdout_payload.get("holdout_id"),
            "calibration_count": len(calibration_labels),
            "holdout_count": len(holdout_labels),
        },
        "summary": {
            "raw_frequency_baseline": _compact_record(raw_frequency_record),
            "legacy_current_formula_analog": _compact_record(legacy_current_record),
            "best_calibration_candidate": _compact_record(
                calibration_top[0] if calibration_top else {}
            ),
            "best_holdout_guarded_candidate": _compact_record(
                holdout_guarded_top[0] if holdout_guarded_top else {}
            ),
            "best_stable_candidate": _compact_record(stable_top[0] if stable_top else {}),
        },
        "leaderboards": {
            "calibration_top": calibration_top,
            "holdout_guarded_top": holdout_guarded_top,
            "stable_top": stable_top,
            "best_by_source_family": _best_by_source_family(records),
        },
        "selected_candidate_details": selected_details,
        "limitations": [
            "This is a breadth test, not exhaustive scalar optimization.",
            "Wiktionary metadata is mechanical; marked/form evidence can be useful but is not a direct difficulty label.",
            "Source-list levels are treated as learner-source evidence, not official CEFR truth.",
        ],
    }


def generate_candidates() -> tuple[BreadthCandidate, ...]:
    candidates: list[BreadthCandidate] = []
    for base in generate_base_profiles():
        for shape in generate_source_shapes():
            candidates.append(
                BreadthCandidate(
                    candidate_id=f"{base.profile_id}__{shape.shape_id}",
                    base_profile=base,
                    source_shape=shape,
                )
            )
    return tuple(candidates)


def generate_base_profiles() -> tuple[BaseProfile, ...]:
    return (
        BaseProfile(
            profile_id="raw_frequency_blend",
            rank_weight=0.55,
            rank_gamma=1.0,
            pmw_gamma=1.0,
            warp_gamma=1.0,
            raw_frequency=True,
            description="Raw signal-palette frequency_blend baseline.",
        ),
        BaseProfile(
            profile_id="current_best_curve",
            rank_weight=0.90,
            rank_gamma=2.20,
            pmw_gamma=1.40,
            warp_gamma=1.12,
            raw_frequency=False,
            description="Curve used by the current formula-sweep winner before source shifts.",
        ),
        BaseProfile(
            profile_id="mid_rank_curve",
            rank_weight=0.75,
            rank_gamma=1.75,
            pmw_gamma=1.40,
            warp_gamma=1.12,
            raw_frequency=False,
            description="Neighbor curve with less aggressive rank dominance.",
        ),
        BaseProfile(
            profile_id="balanced_curve",
            rank_weight=0.60,
            rank_gamma=1.35,
            pmw_gamma=1.00,
            warp_gamma=1.00,
            raw_frequency=False,
            description="Softer curve that keeps PMW evidence more visible.",
        ),
    )


def generate_source_shapes() -> tuple[SourceShape, ...]:
    shapes = [
        SourceShape(
            "none",
            "baseline",
            "none",
            {},
            "No learner-source or Wiktionary adjustment.",
        ),
        SourceShape(
            "legacy_openlingo50_floor25",
            "legacy_openlingo",
            "weighted_pull",
            {
                "openlingo_down_weight": 0.50,
                "openlingo_up_weight": 0.25,
                "down_cap": 0.24,
                "up_cap": 0.10,
            },
            "Replicates the current full-sweep winner's source treatment: exact OpenLingo pull plus floor.",
        ),
        SourceShape(
            "openlingo_upper_light",
            "openlingo_upper_bound",
            "upper_bound",
            {
                "source_ids": ("openlingo",),
                "margin": 0.06,
                "uncertainty": 0.16,
                "cap_weight": 0.45,
                "cap": 0.18,
            },
            "Treat exact OpenLingo as an upper-bound source without pulling low-frequency words upward.",
        ),
        SourceShape(
            "openlingo_upper_medium",
            "openlingo_upper_bound",
            "upper_bound",
            {
                "source_ids": ("openlingo",),
                "margin": 0.10,
                "uncertainty": 0.14,
                "cap_weight": 0.70,
                "cap": 0.24,
            },
            "Stronger exact-source upper bound with moderate uncertainty allowance.",
        ),
        SourceShape(
            "openlingo_cap_soft",
            "openlingo_cap",
            "pull_then_bound",
            {
                "source_ids": ("openlingo",),
                "openlingo_down_weight": 0.35,
                "openlingo_up_weight": 0.05,
                "down_cap": 0.18,
                "up_cap": 0.03,
                "margin": 0.10,
                "uncertainty": 0.12,
                "cap_weight": 0.45,
                "cap": 0.16,
            },
            "Exact source softly pulls toward its level, then prevents large overshoots.",
        ),
        SourceShape(
            "openlingo_cap_strong",
            "openlingo_cap",
            "pull_then_bound",
            {
                "source_ids": ("openlingo",),
                "openlingo_down_weight": 0.55,
                "openlingo_up_weight": 0.10,
                "down_cap": 0.24,
                "up_cap": 0.05,
                "margin": 0.08,
                "uncertainty": 0.10,
                "cap_weight": 0.80,
                "cap": 0.24,
            },
            "Stronger exact-source cap and pull; tests whether source levels should dominate frequency for known learner words.",
        ),
        SourceShape(
            "weighted_exact_basis_light",
            "weighted_sources",
            "weighted_pull",
            {
                "openlingo_down_weight": 0.40,
                "openlingo_up_weight": 0.10,
                "odenet_down_weight": 0.18,
                "odenet_up_weight": 0.04,
                "down_cap": 0.22,
                "up_cap": 0.07,
            },
            "Exact OpenLingo plus weak OdeNet support.",
        ),
        SourceShape(
            "weighted_exact_basis_goethe",
            "weighted_sources",
            "weighted_pull",
            {
                "openlingo_down_weight": 0.45,
                "openlingo_up_weight": 0.12,
                "odenet_down_weight": 0.20,
                "odenet_up_weight": 0.05,
                "goethe_down_weight": 0.10,
                "goethe_up_weight": 0.02,
                "down_cap": 0.24,
                "up_cap": 0.08,
            },
            "All learner sources, with Goethe stems intentionally weak.",
        ),
        SourceShape(
            "odenet_corroborated",
            "odenet_basis",
            "conditional_pull",
            {
                "openlingo_down_weight": 0.40,
                "openlingo_up_weight": 0.10,
                "odenet_down_weight": 0.32,
                "odenet_up_weight": 0.02,
                "odenet_requires_openlingo_or_tail": True,
                "tail_start": 0.42,
                "tail_end": 0.78,
                "down_cap": 0.22,
                "up_cap": 0.06,
            },
            "Use OdeNet more when corroborated by OpenLingo or when rescuing suspiciously late rows.",
        ),
        SourceShape(
            "odenet_only_rescue",
            "odenet_basis",
            "conditional_pull",
            {
                "odenet_down_weight": 0.36,
                "odenet_up_weight": 0.00,
                "odenet_only": True,
                "tail_start": 0.35,
                "tail_end": 0.78,
                "down_cap": 0.16,
                "up_cap": 0.00,
            },
            "OdeNet can only pull down OdeNet-only words, and only when the base puts them late.",
        ),
        SourceShape(
            "goethe_weak_corroborated",
            "goethe_stem",
            "conditional_pull",
            {
                "goethe_down_weight": 0.22,
                "goethe_up_weight": 0.00,
                "goethe_requires_exact_or_basis": True,
                "openlingo_down_weight": 0.35,
                "openlingo_up_weight": 0.08,
                "odenet_down_weight": 0.14,
                "odenet_up_weight": 0.00,
                "down_cap": 0.20,
                "up_cap": 0.04,
            },
            "Goethe stems are useful only when exact/basis evidence agrees.",
        ),
        SourceShape(
            "goethe_tail_rescue_only",
            "goethe_stem",
            "conditional_pull",
            {
                "goethe_down_weight": 0.24,
                "goethe_up_weight": 0.00,
                "goethe_only": True,
                "tail_start": 0.50,
                "tail_end": 0.85,
                "down_cap": 0.12,
                "up_cap": 0.00,
            },
            "Goethe-only evidence can rescue very late words but cannot affect early/mid words.",
        ),
        SourceShape(
            "exact_vs_family_conflict_damped",
            "source_conflict",
            "conflict_damped_pull",
            {
                "openlingo_down_weight": 0.48,
                "openlingo_up_weight": 0.12,
                "odenet_down_weight": 0.22,
                "odenet_up_weight": 0.03,
                "goethe_down_weight": 0.14,
                "goethe_up_weight": 0.00,
                "family_conflict_damping": 0.80,
                "exact_conflict_damping": 0.25,
                "down_cap": 0.24,
                "up_cap": 0.07,
            },
            "Trust exact source more than family/stem source when Wiktionary says the lemma is marked/form-like.",
        ),
        SourceShape(
            "conflict_guard_light",
            "source_conflict",
            "conflict_guard",
            {
                "openlingo_down_weight": 0.42,
                "openlingo_up_weight": 0.08,
                "odenet_down_weight": 0.18,
                "goethe_down_weight": 0.08,
                "family_conflict_damping": 0.70,
                "exact_conflict_damping": 0.20,
                "guard_weight": 0.05,
                "down_cap": 0.22,
                "up_cap": 0.05,
                "guard_cap": 0.08,
            },
            "Damp learner pulls under source conflict and add a small rare/form guard.",
        ),
        SourceShape(
            "conflict_guard_medium",
            "source_conflict",
            "conflict_guard",
            {
                "openlingo_down_weight": 0.48,
                "openlingo_up_weight": 0.08,
                "odenet_down_weight": 0.20,
                "goethe_down_weight": 0.10,
                "family_conflict_damping": 0.90,
                "exact_conflict_damping": 0.35,
                "guard_weight": 0.08,
                "down_cap": 0.22,
                "up_cap": 0.05,
                "guard_cap": 0.12,
            },
            "Stronger conflict handling for rows with learner evidence plus Wiktionary rare/form evidence.",
        ),
        SourceShape(
            "wiki_guard_light",
            "wiktionary_guard",
            "wiki_guard",
            {
                "guard_weight": 0.05,
                "guard_cap": 0.08,
                "tail_start": 0.28,
                "tail_end": 0.85,
            },
            "Raise rows with Wiktionary rare/form/marked signals, tail-gated.",
        ),
        SourceShape(
            "wiki_guard_medium",
            "wiktionary_guard",
            "wiki_guard",
            {
                "guard_weight": 0.09,
                "guard_cap": 0.14,
                "tail_start": 0.25,
                "tail_end": 0.82,
            },
            "Medium Wiktionary guard for marked, rare, sensitive, form/alt-of, and high-sense-count rows.",
        ),
        SourceShape(
            "wiki_blocks_family",
            "wiktionary_blocks_pedagogy",
            "wiki_blocks_family",
            {
                "openlingo_down_weight": 0.42,
                "openlingo_up_weight": 0.08,
                "odenet_down_weight": 0.24,
                "goethe_down_weight": 0.16,
                "family_block_strength": 0.95,
                "exact_block_strength": 0.30,
                "guard_weight": 0.04,
                "down_cap": 0.22,
                "up_cap": 0.05,
                "guard_cap": 0.08,
            },
            "Wiktionary rare/form evidence mostly blocks family/stem pull while preserving exact-source evidence.",
        ),
        SourceShape(
            "wiki_blocks_all_but_exact_cap",
            "wiktionary_blocks_pedagogy",
            "wiki_blocks_family",
            {
                "openlingo_down_weight": 0.46,
                "openlingo_up_weight": 0.06,
                "odenet_down_weight": 0.24,
                "goethe_down_weight": 0.16,
                "family_block_strength": 1.00,
                "exact_block_strength": 0.55,
                "guard_weight": 0.06,
                "down_cap": 0.20,
                "up_cap": 0.04,
                "guard_cap": 0.10,
            },
            "More conservative: conflict can damp even exact-source pulls, but exact still survives better than family evidence.",
        ),
        SourceShape(
            "absence_tail_light",
            "absence_tail",
            "absence_tail",
            {
                "guard_weight": 0.05,
                "guard_cap": 0.08,
                "tail_start": 0.50,
                "tail_end": 0.92,
            },
            "Raise rows with no learner source and weak dictionary support only in the tail.",
        ),
        SourceShape(
            "source_mix_plus_absence_tail",
            "composed",
            "composed",
            {
                "openlingo_down_weight": 0.42,
                "openlingo_up_weight": 0.10,
                "odenet_down_weight": 0.16,
                "goethe_down_weight": 0.06,
                "down_cap": 0.22,
                "up_cap": 0.06,
                "absence_guard_weight": 0.04,
                "wiki_guard_weight": 0.04,
                "guard_cap": 0.08,
            },
            "Mixed source pull plus cautious tail-only absence and Wiktionary guards.",
        ),
        SourceShape(
            "topic_tail_tiebreak",
            "topic_documented",
            "topic_tail",
            {
                "topic_weight": 0.03,
                "cap": 0.05,
                "tail_start": 0.35,
                "tail_end": 0.82,
            },
            "Weakly lower topic-documented tail rows as a usefulness tiebreaker.",
        ),
    ]
    return tuple(shapes)


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _as_mapping(report.get("inputs"))
    summary = _as_mapping(report.get("summary"))
    method = _as_mapping(report.get("method"))
    lines = [
        "# en-de Learner Difficulty Source-Shape Breadth Sweep",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Inputs",
        "",
        f"- Signal rows: `{inputs.get('signal_row_count')}`",
        f"- Calibration labels: `{inputs.get('calibration_count')}`",
        f"- Holdout labels: `{inputs.get('holdout_count')}`",
        f"- Base profiles: `{method.get('base_profile_count')}`",
        f"- Source shapes: `{method.get('source_shape_count')}`",
        f"- Candidates swept: `{method.get('candidate_count')}`",
        "",
        "## Summary",
        "",
    ]
    for key, label in (
        ("raw_frequency_baseline", "raw frequency baseline"),
        ("legacy_current_formula_analog", "legacy current formula analog"),
        ("best_calibration_candidate", "best calibration"),
        ("best_holdout_guarded_candidate", "best holdout-guarded"),
        ("best_stable_candidate", "best stable"),
    ):
        record = _as_mapping(summary.get(key))
        lines.append(
            f"- {label}: `{record.get('candidate_id')}` "
            f"(family={record.get('source_family')}, "
            f"cal={_fmt(record.get('calibration_balanced'))}, "
            f"holdout={_fmt(record.get('holdout_balanced'))}, "
            f"cal MAE={_fmt(record.get('calibration_mae'))}, "
            f"holdout MAE={_fmt(record.get('holdout_mae'))})"
        )
    lines.extend(["", "## Best By Source Family", ""])
    lines.extend(
        [
            "| Family | Candidate | Cal Balanced | Holdout Balanced | Cal MAE | Holdout MAE |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for raw in _as_sequence(_as_mapping(report.get("leaderboards")).get("best_by_source_family")):
        row = _as_mapping(raw)
        lines.append(
            f"| `{row.get('source_family')}` | `{row.get('candidate_id')}` | "
            f"{_fmt(_score_at(row, 'calibration_primary', 'balanced_score'))} | "
            f"{_fmt(_score_at(row, 'holdout_primary', 'balanced_score'))} | "
            f"{_fmt(_metric_at(row, 'calibration_primary', 'mae'))} | "
            f"{_fmt(_metric_at(row, 'holdout_primary', 'mae'))} |"
        )
    lines.extend(["", "## Leaderboards", ""])
    for leaderboard_key, title in (
        ("calibration_top", "Calibration Top"),
        ("holdout_guarded_top", "Holdout-Guarded Top"),
        ("stable_top", "Stable Top"),
    ):
        lines.extend(
            [
                f"### {title}",
                "",
                "| Candidate | Family | Cal Balanced | Holdout Balanced | Cal MAE | Holdout MAE | Cal Pairwise | Holdout Pairwise |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for raw in _as_sequence(_as_mapping(report.get("leaderboards")).get(leaderboard_key))[:15]:
            row = _as_mapping(raw)
            lines.append(
                f"| `{row.get('candidate_id')}` | `{row.get('source_family')}` | "
                f"{_fmt(_score_at(row, 'calibration_primary', 'balanced_score'))} | "
                f"{_fmt(_score_at(row, 'holdout_primary', 'balanced_score'))} | "
                f"{_fmt(_metric_at(row, 'calibration_primary', 'mae'))} | "
                f"{_fmt(_metric_at(row, 'holdout_primary', 'mae'))} | "
                f"{_fmt(_metric_at(row, 'calibration_primary', 'pairwise_accuracy'))} | "
                f"{_fmt(_metric_at(row, 'holdout_primary', 'pairwise_accuracy'))} |"
            )
        lines.append("")
    lines.extend(["## Selected Candidate Details", ""])
    for raw in _as_sequence(report.get("selected_candidate_details")):
        detail = _as_mapping(raw)
        lines.extend(
            [
                f"### `{detail.get('candidate_id')}`",
                "",
                str(detail.get("description") or ""),
                "",
                "| Split | Rows | Balanced | MAE | Bucket | Pairwise | High Tail |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for split_key, label in (
            ("calibration_primary", "calibration"),
            ("holdout_primary", "holdout"),
        ):
            item = _compact_eval(detail.get(split_key))
            lines.append(
                f"| {label} | {item.get('count', '')} | {_fmt(item.get('balanced_score'))} | "
                f"{_fmt(item.get('mae'))} | {_fmt(item.get('bucket_accuracy'))} | "
                f"{_fmt(item.get('pairwise_accuracy'))} | {_fmt(item.get('high_tail_score'))} |"
            )
        lines.extend(
            ["", "Source-group shifts versus the same base curve with no source shape:", ""]
        )
        lines.extend(
            [
                "| Group | Rows | Changed | Mean Delta | Mean Abs Delta | Up | Down |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for group in SOURCE_GROUPS:
            group_row = _as_mapping(
                _as_mapping(detail.get("source_group_shift_summary")).get(group)
            )
            lines.append(
                f"| `{group}` | {group_row.get('row_count', 0)} | "
                f"{group_row.get('changed_count', 0)} | {_fmt_signed(group_row.get('mean_delta'))} | "
                f"{_fmt(group_row.get('mean_abs_delta'))} | {group_row.get('up_count', 0)} | "
                f"{group_row.get('down_count', 0)} |"
            )
        lines.extend(["", "Largest shifts from no-source base:", ""])
        for row in _as_sequence(detail.get("largest_base_shifts"))[:8]:
            item = _as_mapping(row)
            lines.append(
                f"- `{item.get('lemma')}`: {_fmt(item.get('base_score'))} -> "
                f"{_fmt(item.get('candidate_score'))} ({_fmt_signed(item.get('delta'))}); "
                f"{_escape(', '.join(str(t) for t in _as_sequence(item.get('translations'))))}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _candidate_record(
    *,
    candidate: BreadthCandidate,
    rows: Sequence[Mapping[str, object]],
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    calibration_labels: Sequence[Mapping[str, object]],
    holdout_labels: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "candidate_id": candidate.candidate_id,
        "base_profile_id": candidate.base_profile.profile_id,
        "source_shape_id": candidate.source_shape.shape_id,
        "source_family": candidate.source_shape.family,
        "description": candidate.source_shape.description,
        "profile": _profile_payload(candidate),
        "calibration_primary": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=True,
        ),
        "holdout_primary": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=True,
        ),
        "calibration_all_numeric": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=False,
        ),
        "holdout_all_numeric": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            candidate=candidate,
            primary_only=False,
        ),
        "labeled_subgroups": {
            group: {
                "calibration": _compact_eval(
                    _evaluate_labels(
                        labels=_labels_for_source_group(
                            labels=calibration_labels,
                            rows_by_lemma=rows_by_lemma,
                            group=group,
                        ),
                        rows_by_lemma=rows_by_lemma,
                        candidate=candidate,
                        primary_only=True,
                    )
                ),
                "holdout": _compact_eval(
                    _evaluate_labels(
                        labels=_labels_for_source_group(
                            labels=holdout_labels,
                            rows_by_lemma=rows_by_lemma,
                            group=group,
                        ),
                        rows_by_lemma=rows_by_lemma,
                        candidate=candidate,
                        primary_only=True,
                    )
                ),
            }
            for group in SOURCE_GROUPS
        },
    }


def _evaluate_labels(
    *,
    labels: Sequence[Mapping[str, object]],
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    candidate: BreadthCandidate,
    primary_only: bool,
) -> dict[str, object]:
    selected = [
        label
        for label in labels
        if _safe_float(label.get("expected_learner_difficulty")) is not None
        and (not primary_only or str(label.get("expected_candidate_state") or "") == PRIMARY_STATE)
    ]
    expected_values = []
    observed_values = []
    expected_bands = []
    label_names = []
    expected_states = []
    observed_states = []
    row_pairs = []
    missing = []
    for label in selected:
        lemma = str(label.get("lemma") or "").strip()
        row = rows_by_lemma.get(lemma.lower())
        observed = _score_row(candidate, row) if row is not None else None
        if observed is None:
            missing.append(lemma)
            observed = float("nan")
        expected = _safe_float(label.get("expected_learner_difficulty"))
        expected_values.append(expected if expected is not None else float("nan"))
        observed_values.append(observed)
        expected_bands.append(str(label.get("expected_difficulty_band") or ""))
        label_names.append(lemma)
        expected_states.append(str(label.get("expected_candidate_state") or ""))
        observed_states.append(PRIMARY_STATE if row is not None else "")
        row_pairs.append((label, row, observed))
    metrics = _difficulty_metrics(
        expected_values=np.asarray(expected_values, dtype=np.float32),
        observed_values=np.asarray(observed_values, dtype=np.float32),
        expected_bands=expected_bands,
        labels=label_names,
        expected_candidate_states=np.asarray(expected_states, dtype="<U64"),
        observed_candidate_states=np.asarray(observed_states, dtype="<U64"),
    )
    return {
        "label_count": len(selected),
        "missing_count": len(missing),
        "missing": missing[:20],
        "scores": metrics["scores"],
        "metrics": _summary_metrics(metrics),
        "largest_errors": _largest_errors(row_pairs, limit=20),
    }


def _score_row(candidate: BreadthCandidate, row: Mapping[str, object] | None) -> float | None:
    if row is None:
        return None
    base = _base_unwarped(candidate.base_profile, row)
    score = _apply_source_shape(candidate.source_shape, row, base)
    if candidate.base_profile.warp_gamma != 1.0:
        score = score ** max(0.01, candidate.base_profile.warp_gamma)
    return _round_float(_clamp01(score))


def _base_only_score(candidate: BreadthCandidate, row: Mapping[str, object]) -> float:
    base = _base_unwarped(candidate.base_profile, row)
    if candidate.base_profile.warp_gamma != 1.0:
        base = base ** max(0.01, candidate.base_profile.warp_gamma)
    return _clamp01(base)


def _base_unwarped(profile: BaseProfile, row: Mapping[str, object]) -> float:
    if profile.raw_frequency:
        return _clamp01(_safe_float(row.get("frequency_blend")) or 0.0)
    rank_base = _clamp01(_safe_float(row.get("rank_base")) or 0.0)
    pmw_base = _clamp01(_safe_float(row.get("pmw_base")) or 0.0)
    rank_curve = rank_base ** max(0.01, profile.rank_gamma)
    pmw_curve = pmw_base ** max(0.01, profile.pmw_gamma)
    return _clamp01((profile.rank_weight * rank_curve) + ((1.0 - profile.rank_weight) * pmw_curve))


def _apply_source_shape(shape: SourceShape, row: Mapping[str, object], base: float) -> float:
    if shape.mode == "none":
        return _clamp01(base)
    if shape.mode == "weighted_pull":
        return _clamp01(base + _weighted_pull_delta(row, base, shape.params))
    if shape.mode == "upper_bound":
        return _clamp01(_apply_upper_bound(row, base, shape.params))
    if shape.mode == "pull_then_bound":
        score = _clamp01(base + _weighted_pull_delta(row, base, shape.params))
        return _clamp01(_apply_upper_bound(row, score, shape.params))
    if shape.mode == "conditional_pull":
        return _clamp01(base + _weighted_pull_delta(row, base, shape.params, conditional=True))
    if shape.mode == "conflict_damped_pull":
        return _clamp01(
            base
            + _weighted_pull_delta(
                row,
                base,
                shape.params,
                exact_damping=_safe_float(shape.params.get("exact_conflict_damping")) or 0.0,
                family_damping=_safe_float(shape.params.get("family_conflict_damping")) or 0.0,
            )
        )
    if shape.mode == "conflict_guard":
        score = _clamp01(
            base
            + _weighted_pull_delta(
                row,
                base,
                shape.params,
                exact_damping=_safe_float(shape.params.get("exact_conflict_damping")) or 0.0,
                family_damping=_safe_float(shape.params.get("family_conflict_damping")) or 0.0,
            )
        )
        return _clamp01(score + _wiki_guard_delta(row, base, shape.params))
    if shape.mode == "wiki_guard":
        return _clamp01(base + _wiki_guard_delta(row, base, shape.params))
    if shape.mode == "wiki_blocks_family":
        score = _clamp01(
            base
            + _weighted_pull_delta(
                row,
                base,
                shape.params,
                exact_damping=_safe_float(shape.params.get("exact_block_strength")) or 0.0,
                family_damping=_safe_float(shape.params.get("family_block_strength")) or 0.0,
            )
        )
        return _clamp01(score + _wiki_guard_delta(row, base, shape.params))
    if shape.mode == "absence_tail":
        return _clamp01(base + _absence_tail_delta(row, base, shape.params))
    if shape.mode == "topic_tail":
        return _clamp01(base - _topic_tail_delta(row, base, shape.params))
    if shape.mode == "composed":
        score = _clamp01(base + _weighted_pull_delta(row, base, shape.params))
        score = _clamp01(
            score + _absence_tail_delta(row, base, shape.params, key_prefix="absence_")
        )
        score = _clamp01(score + _wiki_guard_delta(row, base, shape.params, key_prefix="wiki_"))
        return score
    raise ValueError(f"Unknown source shape mode: {shape.mode}")


def _weighted_pull_delta(
    row: Mapping[str, object],
    base: float,
    params: Mapping[str, object],
    *,
    conditional: bool = False,
    exact_damping: float = 0.0,
    family_damping: float = 0.0,
) -> float:
    evidences = _source_evidences(row)
    risk = _wiktionary_conflict_risk(row)
    down_total = 0.0
    up_total = 0.0
    down_cap = _safe_float(params.get("down_cap"))
    up_cap = _safe_float(params.get("up_cap"))
    for evidence in evidences:
        if conditional and not _conditional_source_allowed(evidence, row, base, params):
            continue
        prefix = evidence.source_id
        down_weight = _safe_float(params.get(f"{prefix}_down_weight")) or 0.0
        up_weight = _safe_float(params.get(f"{prefix}_up_weight")) or 0.0
        if down_weight <= 0.0 and up_weight <= 0.0:
            continue
        damping = exact_damping if evidence.source_id == "openlingo" else family_damping
        effective_strength = _clamp01(evidence.strength * evidence.trust * (1.0 - damping * risk))
        down_total += down_weight * effective_strength * max(0.0, base - evidence.target)
        up_total += up_weight * effective_strength * max(0.0, evidence.target - base)
    if down_cap is not None:
        down_total = min(down_total, down_cap)
    if up_cap is not None:
        up_total = min(up_total, up_cap)
    return up_total - down_total


def _conditional_source_allowed(
    evidence: SourceEvidence,
    row: Mapping[str, object],
    base: float,
    params: Mapping[str, object],
) -> bool:
    openlingo_known = _flag(row, "openlingo_learner_source_known")
    odenet_known = _flag(row, "odenet_basis_learner_source_known")
    goethe_known = _flag(row, "goethe_stem_learner_source_known")
    tail_gate = _ramp(
        base,
        _safe_float(params.get("tail_start")) or 0.0,
        _safe_float(params.get("tail_end")) or 1.0,
    )
    if params.get("odenet_only") and evidence.source_id != "odenet":
        return False
    if params.get("goethe_only") and evidence.source_id != "goethe":
        return False
    if evidence.source_id == "odenet" and params.get("odenet_requires_openlingo_or_tail"):
        return openlingo_known or tail_gate > 0.0
    if evidence.source_id == "goethe" and params.get("goethe_requires_exact_or_basis"):
        return openlingo_known or odenet_known
    if params.get("odenet_only") and evidence.source_id == "odenet":
        return odenet_known and not openlingo_known and not goethe_known and tail_gate > 0.0
    if params.get("goethe_only") and evidence.source_id == "goethe":
        return goethe_known and not openlingo_known and not odenet_known and tail_gate > 0.0
    return True


def _apply_upper_bound(
    row: Mapping[str, object], score: float, params: Mapping[str, object]
) -> float:
    source_ids = {str(item) for item in _as_sequence(params.get("source_ids"))}
    evidences = [
        evidence
        for evidence in _source_evidences(row)
        if not source_ids or evidence.source_id in source_ids
    ]
    target, strength = _weighted_source_target(evidences)
    if strength <= 0.0:
        return score
    margin = _safe_float(params.get("margin")) or 0.0
    uncertainty = _safe_float(params.get("uncertainty")) or 0.0
    cap_weight = _safe_float(params.get("cap_weight")) or 0.0
    cap = _safe_float(params.get("cap"))
    upper_bound = _clamp01(target + margin + ((1.0 - strength) * uncertainty))
    excess = max(0.0, score - upper_bound)
    reduction = cap_weight * excess
    if cap is not None:
        reduction = min(reduction, cap)
    return _clamp01(score - reduction)


def _wiki_guard_delta(
    row: Mapping[str, object],
    base: float,
    params: Mapping[str, object],
    *,
    key_prefix: str = "",
) -> float:
    weight = _safe_float(params.get(f"{key_prefix}guard_weight")) or 0.0
    cap = _safe_float(params.get(f"{key_prefix}guard_cap"))
    tail_start = _safe_float(params.get("tail_start")) or 0.30
    tail_end = _safe_float(params.get("tail_end")) or 0.85
    delta = weight * _wiktionary_conflict_risk(row) * _ramp(base, tail_start, tail_end)
    if cap is not None:
        delta = min(delta, cap)
    return delta


def _absence_tail_delta(
    row: Mapping[str, object],
    base: float,
    params: Mapping[str, object],
    *,
    key_prefix: str = "",
) -> float:
    weight = _safe_float(params.get(f"{key_prefix}guard_weight")) or 0.0
    cap = _safe_float(params.get(f"{key_prefix}guard_cap"))
    no_learner = 1.0 - (_safe_float(row.get("learner_source_known")) or 0.0)
    no_reverse = 1.0 if int(_safe_float(row.get("reverse_support_count")) or 0) <= 0 else 0.0
    no_wiktionary = 1.0 - (_safe_float(row.get("wiktionary_metadata_known")) or 0.0)
    signal_gap = _clamp01((0.55 * no_learner) + (0.30 * no_reverse) + (0.15 * no_wiktionary))
    tail_start = _safe_float(params.get("tail_start")) or 0.50
    tail_end = _safe_float(params.get("tail_end")) or 0.92
    delta = weight * signal_gap * _ramp(base, tail_start, tail_end)
    if cap is not None:
        delta = min(delta, cap)
    return delta


def _topic_tail_delta(
    row: Mapping[str, object], base: float, params: Mapping[str, object]
) -> float:
    topic = _safe_float(row.get("topic_documented")) or 0.0
    weight = _safe_float(params.get("topic_weight")) or 0.0
    cap = _safe_float(params.get("cap"))
    delta = (
        weight
        * topic
        * _ramp(
            base,
            _safe_float(params.get("tail_start")) or 0.35,
            _safe_float(params.get("tail_end")) or 0.82,
        )
    )
    if cap is not None:
        delta = min(delta, cap)
    return delta


def _source_evidences(row: Mapping[str, object]) -> tuple[SourceEvidence, ...]:
    return tuple(
        evidence
        for evidence in (
            _source_evidence(
                "openlingo",
                row,
                known_key="openlingo_learner_source_known",
                score_key="openlingo_learner_core_score",
                confidence_key="openlingo_learner_source_confidence",
                trust=1.0,
            ),
            _source_evidence(
                "odenet",
                row,
                known_key="odenet_basis_learner_source_known",
                score_key="odenet_basis_learner_core_score",
                confidence_key="odenet_basis_learner_source_confidence",
                trust=0.72,
            ),
            _source_evidence(
                "goethe",
                row,
                known_key="goethe_stem_learner_source_known",
                score_key="goethe_stem_learner_core_score",
                confidence_key="goethe_stem_learner_source_confidence",
                trust=0.45,
            ),
        )
        if evidence is not None
    )


def _source_evidence(
    source_id: str,
    row: Mapping[str, object],
    *,
    known_key: str,
    score_key: str,
    confidence_key: str,
    trust: float,
) -> SourceEvidence | None:
    if (_safe_float(row.get(known_key)) or 0.0) <= 0.0:
        return None
    target = _safe_float(row.get(score_key))
    confidence = _safe_float(row.get(confidence_key)) or 0.0
    if target is None or confidence <= 0.0:
        return None
    return SourceEvidence(
        source_id=source_id,
        target=_clamp01(target),
        strength=_clamp01(confidence),
        trust=_clamp01(trust),
    )


def _weighted_source_target(evidences: Sequence[SourceEvidence]) -> tuple[float, float]:
    weights = [evidence.strength * evidence.trust for evidence in evidences]
    total = sum(weights)
    if total <= 0.0:
        return 0.0, 0.0
    target = (
        sum(evidence.target * weight for evidence, weight in zip(evidences, weights, strict=False))
        / total
    )
    strength = _clamp01(total / max(1.0, len(weights)))
    return _clamp01(target), strength


def _wiktionary_conflict_risk(row: Mapping[str, object]) -> float:
    marked = _safe_float(row.get("wiktionary_marked_usage_flag")) or 0.0
    rare = _safe_float(row.get("wiktionary_rare_dated_flag")) or 0.0
    sensitive = _safe_float(row.get("wiktionary_sensitive_flag")) or 0.0
    form = _safe_float(row.get("wiktionary_form_variant_score")) or 0.0
    ambiguity = _safe_float(row.get("wiktionary_sense_count_score")) or 0.0
    return _clamp01(max(rare, sensitive, form, 0.70 * marked, 0.45 * ambiguity))


def _source_group_shift_summary(
    *,
    rows: Sequence[Mapping[str, object]],
    candidate: BreadthCandidate,
) -> dict[str, object]:
    return _source_shift_diagnostics(
        rows=rows,
        candidate=candidate,
        sample_limit=0,
    )["source_group_shift_summary"]


def _source_shift_diagnostics(
    *,
    rows: Sequence[Mapping[str, object]],
    candidate: BreadthCandidate,
    sample_limit: int,
) -> dict[str, object]:
    states: dict[str, dict[str, float]] = {
        group: {
            "row_count": 0.0,
            "changed_count": 0.0,
            "sum_delta": 0.0,
            "sum_abs_delta": 0.0,
            "up_count": 0.0,
            "down_count": 0.0,
        }
        for group in SOURCE_GROUPS
    }
    scored = []
    for row in rows:
        base = _base_only_score(candidate, row)
        score = _score_row(candidate, row)
        if score is None:
            continue
        delta = score - base
        groups = [group for group in SOURCE_GROUPS if _row_in_source_group(row, group)]
        for group in groups:
            state = states[group]
            state["row_count"] += 1.0
            state["sum_delta"] += delta
            state["sum_abs_delta"] += abs(delta)
            if abs(delta) >= 0.01:
                state["changed_count"] += 1.0
                if delta > 0.0:
                    state["up_count"] += 1.0
                elif delta < 0.0:
                    state["down_count"] += 1.0
        if sample_limit:
            scored.append(
                {
                    "lemma": row.get("lemma"),
                    "base_score": _round_float(base),
                    "candidate_score": _round_float(score),
                    "delta": _round_float(delta),
                    "pos_bucket": row.get("pos_bucket"),
                    "translations": list(_as_sequence(row.get("translations")))[:3],
                    "source_groups": groups,
                }
            )
    result: dict[str, object] = {}
    for group, state in states.items():
        row_count = int(state["row_count"])
        result[group] = {
            "row_count": row_count,
            "changed_count": int(state["changed_count"]),
            "mean_delta": _round_float(state["sum_delta"] / row_count) if row_count else None,
            "mean_abs_delta": _round_float(state["sum_abs_delta"] / row_count)
            if row_count
            else None,
            "up_count": int(state["up_count"]),
            "down_count": int(state["down_count"]),
        }
    return {
        "source_group_shift_summary": result,
        "largest_base_shifts": sorted(
            scored,
            key=lambda row: abs(float(row.get("delta") or 0.0)),
            reverse=True,
        )[:sample_limit],
    }


def _labels_for_source_group(
    *,
    labels: Sequence[Mapping[str, object]],
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    group: str,
) -> list[Mapping[str, object]]:
    selected = []
    for label in labels:
        row = rows_by_lemma.get(str(label.get("lemma") or "").strip().lower())
        if row and _row_in_source_group(row, group):
            selected.append(label)
    return selected


def _row_in_source_group(row: Mapping[str, object], group: str) -> bool:
    openlingo = _flag(row, "openlingo_learner_source_known")
    odenet = _flag(row, "odenet_basis_learner_source_known")
    goethe = _flag(row, "goethe_stem_learner_source_known")
    learner = _flag(row, "learner_source_known")
    wiki_guard = _wiktionary_conflict_risk(row) >= 0.35
    if group == "openlingo_known":
        return openlingo
    if group == "odenet_only":
        return odenet and not openlingo and not goethe
    if group == "goethe_only":
        return goethe and not openlingo and not odenet
    if group == "any_learner_source":
        return learner
    if group == "wiktionary_guard_signal":
        return wiki_guard
    if group == "source_conflict":
        return learner and wiki_guard
    if group == "no_learner_source":
        return not learner
    raise ValueError(f"Unknown source group: {group}")


def _with_change_samples(
    record: Mapping[str, object],
    *,
    rows: Sequence[Mapping[str, object]],
    candidate: BreadthCandidate | None,
    sample_limit: int,
) -> dict[str, object]:
    if candidate is None:
        return dict(record)
    result = dict(record)
    diagnostics = _source_shift_diagnostics(
        rows=rows,
        candidate=candidate,
        sample_limit=sample_limit,
    )
    result["source_group_shift_summary"] = diagnostics["source_group_shift_summary"]
    result["largest_base_shifts"] = diagnostics["largest_base_shifts"]
    return result


def _largest_errors(
    row_pairs: Sequence[tuple[Mapping[str, object], Mapping[str, object] | None, float]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    rows = []
    for label, row, observed in row_pairs:
        expected = _safe_float(label.get("expected_learner_difficulty"))
        if expected is None or not np.isfinite(observed):
            continue
        rows.append(
            {
                "lemma": label.get("lemma"),
                "expected": _round_float(expected),
                "observed": _round_float(observed),
                "abs_error": _round_float(abs(observed - expected)),
                "expected_band": label.get("expected_difficulty_band"),
                "observed_band": _difficulty_band(observed),
                "source_frequency_blend": _round_float(
                    _safe_float(_as_mapping(row).get("frequency_blend"))
                ),
                "review_flags": list(_as_sequence(label.get("review_flags"))),
            }
        )
    return sorted(rows, key=lambda item: float(item.get("abs_error") or 0.0), reverse=True)[:limit]


def _compact_record(record: Mapping[str, object]) -> dict[str, object]:
    return {
        "candidate_id": record.get("candidate_id"),
        "base_profile_id": record.get("base_profile_id"),
        "source_shape_id": record.get("source_shape_id"),
        "source_family": record.get("source_family"),
        "calibration_balanced": _score_at(record, "calibration_primary", "balanced_score"),
        "holdout_balanced": _score_at(record, "holdout_primary", "balanced_score"),
        "calibration_mae": _metric_at(record, "calibration_primary", "mae"),
        "holdout_mae": _metric_at(record, "holdout_primary", "mae"),
        "calibration_pairwise": _metric_at(record, "calibration_primary", "pairwise_accuracy"),
        "holdout_pairwise": _metric_at(record, "holdout_primary", "pairwise_accuracy"),
        "profile": record.get("profile"),
    }


def _compact_eval(item: object) -> dict[str, object]:
    row = _as_mapping(item)
    scores = _as_mapping(row.get("scores"))
    metrics = _as_mapping(row.get("metrics"))
    return {
        "count": row.get("label_count"),
        "balanced_score": scores.get("balanced_score"),
        "mae": metrics.get("mae"),
        "bucket_accuracy": metrics.get("bucket_accuracy"),
        "pairwise_accuracy": metrics.get("pairwise_accuracy"),
        "high_tail_score": scores.get("high_tail_score"),
    }


def _best_by_source_family(records: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    by_family: dict[str, Mapping[str, object]] = {}
    for record in records:
        family = str(record.get("source_family") or "")
        if not family:
            continue
        if family not in by_family or _stable_sort_key(record) > _stable_sort_key(
            by_family[family]
        ):
            by_family[family] = record
    return sorted(
        [dict(record) for record in by_family.values()],
        key=_stable_sort_key,
        reverse=True,
    )


def _calibration_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    return (
        _score_at(row, "calibration_primary", "balanced_score") or -1.0,
        _score_at(row, "holdout_primary", "balanced_score") or -1.0,
        _metric_at(row, "calibration_primary", "pairwise_accuracy") or -1.0,
        -(_metric_at(row, "calibration_primary", "mae") or 999.0),
    )


def _holdout_guarded_sort_key(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    return (
        min(
            _score_at(row, "calibration_primary", "balanced_score") or -1.0,
            _score_at(row, "holdout_primary", "balanced_score") or -1.0,
        ),
        _score_at(row, "calibration_primary", "balanced_score") or -1.0,
        _metric_at(row, "holdout_primary", "pairwise_accuracy") or -1.0,
        -(_metric_at(row, "holdout_primary", "mae") or 999.0),
    )


def _stable_sort_key(row: Mapping[str, object]) -> tuple[float, float, float]:
    cal = _score_at(row, "calibration_primary", "balanced_score") or -1.0
    holdout = _score_at(row, "holdout_primary", "balanced_score") or -1.0
    gap = abs(cal - holdout)
    mean_score = (cal + holdout) / 2.0
    return (mean_score - gap * 0.35, min(cal, holdout), -gap)


def _candidate_by_id(
    candidates: Sequence[BreadthCandidate],
    candidate_id: str,
) -> BreadthCandidate | None:
    for candidate in candidates:
        if candidate.candidate_id == candidate_id:
            return candidate
    return None


def _unique_records(
    records: Sequence[Mapping[str, object]],
    *,
    key: str,
) -> list[Mapping[str, object]]:
    result = []
    seen = set()
    for record in records:
        value = str(record.get(key) or "")
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(record)
    return result


def _profile_payload(candidate: BreadthCandidate) -> dict[str, object]:
    return {
        "base_profile": {
            "profile_id": candidate.base_profile.profile_id,
            "rank_weight": candidate.base_profile.rank_weight,
            "rank_gamma": candidate.base_profile.rank_gamma,
            "pmw_gamma": candidate.base_profile.pmw_gamma,
            "warp_gamma": candidate.base_profile.warp_gamma,
            "raw_frequency": candidate.base_profile.raw_frequency,
            "description": candidate.base_profile.description,
        },
        "source_shape": {
            "shape_id": candidate.source_shape.shape_id,
            "family": candidate.source_shape.family,
            "mode": candidate.source_shape.mode,
            "params": dict(candidate.source_shape.params),
            "description": candidate.source_shape.description,
        },
    }


def _score_at(row: Mapping[str, object], eval_key: str, score_key: str) -> float | None:
    return _safe_float(_as_mapping(_as_mapping(row.get(eval_key)).get("scores")).get(score_key))


def _metric_at(row: Mapping[str, object], eval_key: str, metric_key: str) -> float | None:
    return _safe_float(_as_mapping(_as_mapping(row.get(eval_key)).get("metrics")).get(metric_key))


def _difficulty_band(value: float) -> str:
    if value < 0.20:
        return "beginner"
    if value < 0.40:
        return "core"
    if value < 0.60:
        return "intermediate"
    if value < 0.80:
        return "advanced"
    if value < 0.94:
        return "tail"
    return "recondite"


def _ramp(value: object, low: float, high: float) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    if numeric <= low:
        return 0.0
    if numeric >= high:
        return 1.0
    return (numeric - low) / (high - low)


def _flag(row: Mapping[str, object], key: str) -> bool:
    return (_safe_float(row.get(key)) or 0.0) > 0.0


def _clamp01(value: object) -> float:
    return min(1.0, max(0.0, _safe_float(value) or 0.0))


def _round_float(value: object, digits: int = 6) -> float | None:
    numeric = _safe_float(value)
    return round(numeric, digits) if numeric is not None and np.isfinite(numeric) else None


def _safe_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[Mapping[str, object]]:
    rows: list[Mapping[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            if isinstance(row, Mapping):
                rows.append(row)
    return rows


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:.3f}"


def _fmt_signed(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:+.3f}"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


if __name__ == "__main__":
    raise SystemExit(main())
