#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from semantic_routing_generalization_bound_helpers import (  # noqa: E402
    build_surface_bound as _build_surface_bound,
    extend_with_split_surfaces as _extend_with_split_surfaces,
    summarize_sentence_veto_ladder_rows as _summarize_sentence_veto_ladder_rows,
    summarize_sentence_veto_rows as _summarize_sentence_veto_rows,
    summarize_veto_proxy_rows as _summarize_veto_proxy_rows,
)
from semantic_routing_generalization_bound_reporting import (  # noqa: E402
    render_generalization_bound_markdown,
)
from semantic_routing_generalization_bound_splits import (  # noqa: E402
    build_split_lookup,
    find_row,
    load_generalization_split_manifest,
    resolve_overlap_family_split_id,
    resolve_sentence_veto_split_id,
    select_best_source_only_row,
)
from semantic_routing_sentence_veto_support import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_DATASET,
    build_sentence_veto_ladder_report,
    build_sentence_veto_rescue_overlay_case_rows,
    build_sentence_veto_ladder_case_rows,
    build_sentence_veto_report,
)
from semantic_shadow_seed_compare_en_es import (  # noqa: E402
    DEFAULT_BENCHMARK_JSON,
    DEFAULT_DATASET_PATH,
)
from semantic_shadow_veto_proxy_compare_en_es import (  # noqa: E402
    build_veto_proxy_compare_report,
)

DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_routing_generalization_bound_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_routing_generalization_bound_en_es_latest.md"
)
DEFAULT_SPLIT_MANIFEST = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_routing_generalization_splits_en_es.json"
)
DEFAULT_BOOTSTRAP_ITERATIONS = 2000
DEFAULT_RANDOM_SEED = 1729
DEFAULT_CONFIDENCE_LEVEL = 0.95

FIXED_SHADOW_CONTROL_CONFIG = {
    "label": "Fixed-shadow runtime control",
    "scorer_id": "tfidf_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.05,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
}

FIXED_SHADOW_REFERENCE_CONFIG = {
    "label": "Sentence-transformer phrase-guard candidate",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
}

FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG = {
    "label": "Sentence-transformer active-sense phrase-guard experiment",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "phrase_guard_pos_scope": "active_only",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
    "experimental": True,
}

FIXED_SHADOW_LADDER_CONFIG = {
    "label": "Sentence-transformer zero-noise soft ladder",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
    "soft_min_active_score": 0.55,
    "soft_min_margin": -0.03,
    "apply_over_current_abstains_only": True,
}

FIXED_SHADOW_RESCUE_OVERLAY_CONFIG = {
    "label": "Sentence-transformer widened-rescue candidate (simulated)",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
    "backup_evidence_view": "sense_label",
    "primary_margin_floor": -0.05,
    "backup_margin_floor": 0.02,
    "simulated": True,
}

FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG = {
    "label": "Sentence-transformer active-sense phrase-guard overlay (simulated)",
    "scorer_id": "sentence_transformer_cosine",
    "context_view": "masked_sentence",
    "evidence_view": "all_evidence_text",
    "min_active_score": 0.0,
    "min_margin": 0.0,
    "phrase_control_mode": "noun_family_frame_guard",
    "phrase_guard_pos_scope": "active_only",
    "active_rescue_mode": "sense_label_near_tie_active_rescue",
    "backup_evidence_view": "sense_label",
    "primary_margin_floor": -0.05,
    "backup_margin_floor": 0.02,
    "simulated": True,
    "experimental": True,
}

FIXED_SHADOW_METRIC_DIRECTIONS = {
    "decision_accuracy": "higher",
    "replace_precision": "higher",
    "replace_recall": "higher",
    "harmful_replace_rate": "lower",
    "false_abstain_rate": "lower",
    "winner_accuracy": "higher",
    "shadow_winner_accuracy": "higher",
}

FIXED_SHADOW_LADDER_METRIC_DIRECTIONS = {
    "hard_replace_recall": "higher",
    "hard_harmful_replace_rate": "lower",
    "replace_or_soft_recall": "higher",
    "soft_noise_rate": "lower",
    "surfaced_precision": "higher",
    "remaining_missed_replace_rate": "lower",
}

VETO_PROXY_METRIC_DIRECTIONS = {
    "overall_accuracy": "higher",
    "abstain_recall": "higher",
    "harmful_allow_rate": "lower",
    "allow_precision": "higher",
    "overblocking_rate": "lower",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate cluster-aware confidence bounds for the current en-es semantic-veto "
            "controls. The report combines a fixed-shadow runtime scorer control with the "
            "current lower-bound blocker-generation lanes."
        )
    )
    parser.add_argument(
        "--sentence-dataset",
        type=Path,
        default=DEFAULT_SENTENCE_VETO_DATASET,
        help="Sentence-level fixed-shadow veto dataset JSON.",
    )
    parser.add_argument(
        "--benchmark-dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Reviewed rulegen benchmark dataset JSON.",
    )
    parser.add_argument(
        "--benchmark-json",
        type=Path,
        default=DEFAULT_BENCHMARK_JSON,
        help="Rulegen benchmark report JSON containing best_run case_results.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(resolve_data_root()),
        help="LexiShift data root (default: helper resolve_data_root()).",
    )
    parser.add_argument(
        "--translation-dict",
        type=Path,
        default=None,
        help="Optional explicit forward translation pack path for en-es.",
    )
    parser.add_argument(
        "--reverse-translation-dict",
        type=Path,
        default=None,
        help="Optional explicit reverse translation pack path for en-es.",
    )
    parser.add_argument(
        "--forward-seed-max-words",
        type=int,
        default=1,
        help="Maximum word count for forward-gloss-derived trigger seeds.",
    )
    parser.add_argument(
        "--family-splits-manifest",
        type=Path,
        default=DEFAULT_SPLIT_MANIFEST,
        help="Explicit tune vs held-out family split manifest.",
    )
    parser.add_argument(
        "--bootstrap-iterations",
        type=int,
        default=DEFAULT_BOOTSTRAP_ITERATIONS,
        help="Cluster-bootstrap resample count.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Random seed for cluster-bootstrap sampling.",
    )
    parser.add_argument(
        "--confidence-level",
        type=float,
        default=DEFAULT_CONFIDENCE_LEVEL,
        help="Bootstrap confidence level between 0 and 1.",
    )
    parser.add_argument(
        "--include-sentence-transformer-reference",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to also compute the current sentence-transformer candidate row.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_MARKDOWN_OUT,
        help="Output Markdown artifact path.",
    )
    return parser.parse_args()


def resolve_fixed_shadow_ladder_config(*, sentence_dataset: Path) -> dict[str, object]:
    ladder_report = build_sentence_veto_ladder_report(
        dataset_path=sentence_dataset,
        scorer_id=str(FIXED_SHADOW_LADDER_CONFIG["scorer_id"]),
        context_view=str(FIXED_SHADOW_LADDER_CONFIG["context_view"]),
        evidence_view=str(FIXED_SHADOW_LADDER_CONFIG["evidence_view"]),
        min_active_score=float(FIXED_SHADOW_LADDER_CONFIG["min_active_score"]),
        min_margin=float(FIXED_SHADOW_LADDER_CONFIG["min_margin"]),
        phrase_control_mode=str(FIXED_SHADOW_LADDER_CONFIG["phrase_control_mode"]),
        active_rescue_mode=str(FIXED_SHADOW_LADDER_CONFIG["active_rescue_mode"]),
    )
    budget_rows = (
        ladder_report.get("best_rows_by_soft_false_positive_budget")
        if isinstance(ladder_report.get("best_rows_by_soft_false_positive_budget"), list)
        else []
    )
    selected_row: Mapping[str, object] | None = None
    for entry in budget_rows:
        if not isinstance(entry, Mapping):
            continue
        if int(entry.get("soft_false_positive_budget") or 0) != 0:
            continue
        row = entry.get("row")
        if isinstance(row, Mapping):
            selected_row = row
            break
    if selected_row is None:
        best_row = ladder_report.get("best_row")
        if isinstance(best_row, Mapping):
            selected_row = best_row
    if selected_row is None:
        raise ValueError("Unable to resolve the current fixed-shadow ladder row.")
    return {
        **FIXED_SHADOW_LADDER_CONFIG,
        "soft_min_active_score": float(selected_row.get("soft_min_active_score") or 0.0),
        "soft_min_margin": float(selected_row.get("soft_min_margin") or 0.0),
        "resolved_config_id": str(selected_row.get("config_id") or "").strip(),
    }


def build_generalization_bound_report(
    *,
    sentence_dataset: Path,
    benchmark_dataset: Path,
    benchmark_json: Path,
    family_splits_manifest: Path,
    data_root: Path,
    translation_dict: Path | None,
    reverse_translation_dict: Path | None,
    forward_seed_max_words: int,
    bootstrap_iterations: int,
    random_seed: int,
    confidence_level: float,
    include_sentence_transformer_reference: bool,
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    split_manifest = load_generalization_split_manifest(family_splits_manifest)
    fixed_shadow_split_ids, fixed_shadow_split_lookup = build_split_lookup(
        dict(split_manifest.get("fixed_shadow_sentence_veto") or {})
    )
    reviewed_family_split_ids, reviewed_family_split_lookup = build_split_lookup(
        dict(split_manifest.get("reviewed_overlap_semantic_families") or {})
    )

    fixed_shadow_surfaces: list[dict[str, object]] = []
    reference_surface: dict[str, object] | None = None
    active_only_reference_surface: dict[str, object] | None = None
    ladder_surface: dict[str, object] | None = None
    rescue_overlay_surface: dict[str, object] | None = None
    active_only_rescue_overlay_surface: dict[str, object] | None = None
    resolved_ladder_config = resolve_fixed_shadow_ladder_config(sentence_dataset=sentence_dataset)
    fixed_shadow_control_report = build_sentence_veto_report(
        dataset_path=sentence_dataset,
        scorer_id=str(FIXED_SHADOW_CONTROL_CONFIG["scorer_id"]),
        context_view=str(FIXED_SHADOW_CONTROL_CONFIG["context_view"]),
        evidence_view=str(FIXED_SHADOW_CONTROL_CONFIG["evidence_view"]),
        min_active_score=float(FIXED_SHADOW_CONTROL_CONFIG["min_active_score"]),
        min_margin=float(FIXED_SHADOW_CONTROL_CONFIG["min_margin"]),
        phrase_control_mode=str(FIXED_SHADOW_CONTROL_CONFIG["phrase_control_mode"]),
        active_rescue_mode=str(FIXED_SHADOW_CONTROL_CONFIG["active_rescue_mode"]),
    )
    fixed_shadow_control_rows = tuple(
        row
        for row in fixed_shadow_control_report.get("row_results", ())
        if isinstance(row, Mapping)
    )
    fixed_shadow_surfaces.append(
        _build_surface_bound(
            label=str(FIXED_SHADOW_CONTROL_CONFIG["label"]),
            rows=fixed_shadow_control_rows,
            cluster_key_name="family_id",
            summarize_rows=_summarize_sentence_veto_rows,
            metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed,
            confidence_level=confidence_level,
            config=FIXED_SHADOW_CONTROL_CONFIG,
        )
    )
    _extend_with_split_surfaces(
        fixed_shadow_surfaces,
        label=str(FIXED_SHADOW_CONTROL_CONFIG["label"]),
        rows=fixed_shadow_control_rows,
        cluster_key_name="family_id",
        summarize_rows=_summarize_sentence_veto_rows,
        metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
        bootstrap_iterations=bootstrap_iterations,
        random_seed=random_seed,
        confidence_level=confidence_level,
        config=FIXED_SHADOW_CONTROL_CONFIG,
        split_ids=fixed_shadow_split_ids,
        split_lookup=fixed_shadow_split_lookup,
        resolve_split_id=resolve_sentence_veto_split_id,
    )
    if include_sentence_transformer_reference:
        reference_report = build_sentence_veto_report(
            dataset_path=sentence_dataset,
            scorer_id=str(FIXED_SHADOW_REFERENCE_CONFIG["scorer_id"]),
            context_view=str(FIXED_SHADOW_REFERENCE_CONFIG["context_view"]),
            evidence_view=str(FIXED_SHADOW_REFERENCE_CONFIG["evidence_view"]),
            min_active_score=float(FIXED_SHADOW_REFERENCE_CONFIG["min_active_score"]),
            min_margin=float(FIXED_SHADOW_REFERENCE_CONFIG["min_margin"]),
            phrase_control_mode=str(FIXED_SHADOW_REFERENCE_CONFIG["phrase_control_mode"]),
            active_rescue_mode=str(FIXED_SHADOW_REFERENCE_CONFIG["active_rescue_mode"]),
        )
        reference_rows = tuple(
            row for row in reference_report.get("row_results", ()) if isinstance(row, Mapping)
        )
        fixed_shadow_surfaces.append(
            _build_surface_bound(
                label=str(FIXED_SHADOW_REFERENCE_CONFIG["label"]),
                rows=reference_rows,
                cluster_key_name="family_id",
                summarize_rows=_summarize_sentence_veto_rows,
                metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
                bootstrap_iterations=bootstrap_iterations,
                random_seed=random_seed + 1,
                confidence_level=confidence_level,
                config=FIXED_SHADOW_REFERENCE_CONFIG,
            )
        )
        reference_surface = fixed_shadow_surfaces[-1]
        _extend_with_split_surfaces(
            fixed_shadow_surfaces,
            label=str(FIXED_SHADOW_REFERENCE_CONFIG["label"]),
            rows=reference_rows,
            cluster_key_name="family_id",
            summarize_rows=_summarize_sentence_veto_rows,
            metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed + 1,
            confidence_level=confidence_level,
            config=FIXED_SHADOW_REFERENCE_CONFIG,
            split_ids=fixed_shadow_split_ids,
            split_lookup=fixed_shadow_split_lookup,
            resolve_split_id=resolve_sentence_veto_split_id,
        )
        active_only_reference_report = build_sentence_veto_report(
            dataset_path=sentence_dataset,
            scorer_id=str(FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["scorer_id"]),
            context_view=str(FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["context_view"]),
            evidence_view=str(FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["evidence_view"]),
            min_active_score=float(FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["min_active_score"]),
            min_margin=float(FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["min_margin"]),
            phrase_control_mode=str(
                FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["phrase_control_mode"]
            ),
            phrase_guard_pos_scope=str(
                FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["phrase_guard_pos_scope"]
            ),
            active_rescue_mode=str(FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["active_rescue_mode"]),
        )
        active_only_reference_rows = tuple(
            row
            for row in active_only_reference_report.get("row_results", ())
            if isinstance(row, Mapping)
        )
        fixed_shadow_surfaces.append(
            _build_surface_bound(
                label=str(FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["label"]),
                rows=active_only_reference_rows,
                cluster_key_name="family_id",
                summarize_rows=_summarize_sentence_veto_rows,
                metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
                bootstrap_iterations=bootstrap_iterations,
                random_seed=random_seed + 4,
                confidence_level=confidence_level,
                config=FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG,
            )
        )
        active_only_reference_surface = fixed_shadow_surfaces[-1]
        _extend_with_split_surfaces(
            fixed_shadow_surfaces,
            label=str(FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["label"]),
            rows=active_only_reference_rows,
            cluster_key_name="family_id",
            summarize_rows=_summarize_sentence_veto_rows,
            metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed + 4,
            confidence_level=confidence_level,
            config=FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG,
            split_ids=fixed_shadow_split_ids,
            split_lookup=fixed_shadow_split_lookup,
            resolve_split_id=resolve_sentence_veto_split_id,
        )
        ladder_rows = tuple(
            row
            for row in build_sentence_veto_ladder_case_rows(
                reference_report,
                soft_min_active_score=float(resolved_ladder_config["soft_min_active_score"]),
                soft_min_margin=float(resolved_ladder_config["soft_min_margin"]),
            )
            if isinstance(row, Mapping)
        )
        fixed_shadow_surfaces.append(
            _build_surface_bound(
                label=str(resolved_ladder_config["label"]),
                rows=ladder_rows,
                cluster_key_name="family_id",
                summarize_rows=_summarize_sentence_veto_ladder_rows,
                metric_directions=FIXED_SHADOW_LADDER_METRIC_DIRECTIONS,
                bootstrap_iterations=bootstrap_iterations,
                random_seed=random_seed + 2,
                confidence_level=confidence_level,
                config=resolved_ladder_config,
            )
        )
        ladder_surface = fixed_shadow_surfaces[-1]
        _extend_with_split_surfaces(
            fixed_shadow_surfaces,
            label=str(resolved_ladder_config["label"]),
            rows=ladder_rows,
            cluster_key_name="family_id",
            summarize_rows=_summarize_sentence_veto_ladder_rows,
            metric_directions=FIXED_SHADOW_LADDER_METRIC_DIRECTIONS,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed + 2,
            confidence_level=confidence_level,
            config=resolved_ladder_config,
            split_ids=fixed_shadow_split_ids,
            split_lookup=fixed_shadow_split_lookup,
            resolve_split_id=resolve_sentence_veto_split_id,
        )
        rescue_overlay_backup_report = build_sentence_veto_report(
            dataset_path=sentence_dataset,
            scorer_id=str(FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["scorer_id"]),
            context_view=str(FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["context_view"]),
            evidence_view=str(FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["backup_evidence_view"]),
            min_active_score=float(FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["min_active_score"]),
            min_margin=float(FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["min_margin"]),
            phrase_control_mode=str(FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["phrase_control_mode"]),
            active_rescue_mode="off",
        )
        rescue_overlay_rows = tuple(
            row
            for row in build_sentence_veto_rescue_overlay_case_rows(
                primary_report=reference_report,
                backup_report=rescue_overlay_backup_report,
                primary_margin_floor=float(
                    FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["primary_margin_floor"]
                ),
                backup_margin_floor=float(
                    FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["backup_margin_floor"]
                ),
            )
            if isinstance(row, Mapping)
        )
        fixed_shadow_surfaces.append(
            _build_surface_bound(
                label=str(FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["label"]),
                rows=rescue_overlay_rows,
                cluster_key_name="family_id",
                summarize_rows=_summarize_sentence_veto_rows,
                metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
                bootstrap_iterations=bootstrap_iterations,
                random_seed=random_seed + 3,
                confidence_level=confidence_level,
                config=FIXED_SHADOW_RESCUE_OVERLAY_CONFIG,
            )
        )
        rescue_overlay_surface = fixed_shadow_surfaces[-1]
        _extend_with_split_surfaces(
            fixed_shadow_surfaces,
            label=str(FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["label"]),
            rows=rescue_overlay_rows,
            cluster_key_name="family_id",
            summarize_rows=_summarize_sentence_veto_rows,
            metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed + 3,
            confidence_level=confidence_level,
            config=FIXED_SHADOW_RESCUE_OVERLAY_CONFIG,
            split_ids=fixed_shadow_split_ids,
            split_lookup=fixed_shadow_split_lookup,
            resolve_split_id=resolve_sentence_veto_split_id,
        )
        active_only_rescue_overlay_backup_report = build_sentence_veto_report(
            dataset_path=sentence_dataset,
            scorer_id=str(FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["scorer_id"]),
            context_view=str(FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["context_view"]),
            evidence_view=str(
                FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["backup_evidence_view"]
            ),
            min_active_score=float(
                FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["min_active_score"]
            ),
            min_margin=float(FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["min_margin"]),
            phrase_control_mode=str(
                FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["phrase_control_mode"]
            ),
            phrase_guard_pos_scope=str(
                FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["phrase_guard_pos_scope"]
            ),
            active_rescue_mode="off",
        )
        active_only_rescue_overlay_primary_report = build_sentence_veto_report(
            dataset_path=sentence_dataset,
            scorer_id=str(FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["scorer_id"]),
            context_view=str(FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["context_view"]),
            evidence_view=str(FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["evidence_view"]),
            min_active_score=float(
                FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["min_active_score"]
            ),
            min_margin=float(FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["min_margin"]),
            phrase_control_mode=str(
                FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["phrase_control_mode"]
            ),
            phrase_guard_pos_scope=str(
                FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["phrase_guard_pos_scope"]
            ),
            active_rescue_mode="off",
        )
        active_only_rescue_overlay_rows = tuple(
            row
            for row in build_sentence_veto_rescue_overlay_case_rows(
                primary_report=active_only_rescue_overlay_primary_report,
                backup_report=active_only_rescue_overlay_backup_report,
                primary_margin_floor=float(
                    FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["primary_margin_floor"]
                ),
                backup_margin_floor=float(
                    FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["backup_margin_floor"]
                ),
            )
            if isinstance(row, Mapping)
        )
        fixed_shadow_surfaces.append(
            _build_surface_bound(
                label=str(FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["label"]),
                rows=active_only_rescue_overlay_rows,
                cluster_key_name="family_id",
                summarize_rows=_summarize_sentence_veto_rows,
                metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
                bootstrap_iterations=bootstrap_iterations,
                random_seed=random_seed + 5,
                confidence_level=confidence_level,
                config=FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG,
            )
        )
        active_only_rescue_overlay_surface = fixed_shadow_surfaces[-1]
        _extend_with_split_surfaces(
            fixed_shadow_surfaces,
            label=str(FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["label"]),
            rows=active_only_rescue_overlay_rows,
            cluster_key_name="family_id",
            summarize_rows=_summarize_sentence_veto_rows,
            metric_directions=FIXED_SHADOW_METRIC_DIRECTIONS,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed + 5,
            confidence_level=confidence_level,
            config=FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG,
            split_ids=fixed_shadow_split_ids,
            split_lookup=fixed_shadow_split_lookup,
            resolve_split_id=resolve_sentence_veto_split_id,
        )

    veto_proxy_report = build_veto_proxy_compare_report(
        benchmark_dataset=benchmark_dataset,
        benchmark_json=benchmark_json,
        data_root=data_root,
        translation_dict=translation_dict,
        reverse_translation_dict=reverse_translation_dict,
        forward_seed_max_words=forward_seed_max_words,
        include_row_results=True,
    )
    veto_proxy_rows = [row for row in veto_proxy_report.get("rows", ()) if isinstance(row, Mapping)]
    veto_proxy_surfaces: list[dict[str, object]] = []
    for row in veto_proxy_rows:
        source_id = str(row.get("source_id") or "").strip()
        label = str(row.get("label") or source_id)
        row_results = tuple(
            result for result in row.get("row_results", ()) if isinstance(result, Mapping)
        )
        if not row_results:
            continue
        veto_proxy_surfaces.append(
            _build_surface_bound(
                label=label,
                rows=row_results,
                cluster_key_name="trigger",
                summarize_rows=_summarize_veto_proxy_rows,
                metric_directions=VETO_PROXY_METRIC_DIRECTIONS,
                bootstrap_iterations=bootstrap_iterations,
                random_seed=random_seed + len(veto_proxy_surfaces) + 10,
                confidence_level=confidence_level,
                config={
                    "source_id": source_id,
                    "seed_mode": row.get("seed_mode"),
                    "policy": row.get("policy"),
                    "support_score_min": row.get("support_score_min"),
                    "support_score_max_promoted": row.get("support_score_max_promoted"),
                },
            )
        )
        _extend_with_split_surfaces(
            veto_proxy_surfaces,
            label=label,
            rows=row_results,
            cluster_key_name="trigger",
            summarize_rows=_summarize_veto_proxy_rows,
            metric_directions=VETO_PROXY_METRIC_DIRECTIONS,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed + len(veto_proxy_surfaces) + 10,
            confidence_level=confidence_level,
            config={
                "source_id": source_id,
                "seed_mode": row.get("seed_mode"),
                "policy": row.get("policy"),
                "support_score_min": row.get("support_score_min"),
                "support_score_max_promoted": row.get("support_score_max_promoted"),
            },
            split_ids=reviewed_family_split_ids,
            split_lookup=reviewed_family_split_lookup,
            resolve_split_id=resolve_overlap_family_split_id,
        )

    source_only_row = select_best_source_only_row(veto_proxy_rows)
    reviewed_auto_row = find_row(veto_proxy_rows, "reviewed_auto_shadows")
    curated_row = find_row(veto_proxy_rows, "curated_shadows")
    fixed_shadow_control_surface = fixed_shadow_surfaces[0] if fixed_shadow_surfaces else {}

    def _metric_view(surface: Mapping[str, object], metric_name: str) -> Mapping[str, object]:
        metric_views = surface.get("metric_views")
        if isinstance(metric_views, Mapping):
            metric_view = metric_views.get(metric_name)
            if isinstance(metric_view, Mapping):
                return metric_view
        return {}

    source_only_surface = None
    source_only_source_id = ""
    if isinstance(source_only_row, Mapping):
        source_only_source_id = str(source_only_row.get("source_id") or "").strip()
        source_only_surface = next(
            (
                surface
                for surface in veto_proxy_surfaces
                if isinstance(surface.get("config"), Mapping)
                and str(surface["config"].get("source_id") or "").strip() == source_only_source_id
            ),
            None,
        )

    confidence_corridor = {
        "source_only_source_id": source_only_source_id,
        "source_only_abstain_recall_conservative_floor": (
            _metric_view(source_only_surface or {}, "abstain_recall").get("conservative_floor")
            if isinstance(source_only_surface, Mapping)
            else None
        ),
        "source_only_harmful_allow_conservative_ceiling": (
            _metric_view(source_only_surface or {}, "harmful_allow_rate").get(
                "conservative_ceiling"
            )
            if isinstance(source_only_surface, Mapping)
            else None
        ),
        "fixed_shadow_replace_recall_conservative_floor": _metric_view(
            fixed_shadow_control_surface, "replace_recall"
        ).get("conservative_floor"),
        "fixed_shadow_harmful_replace_conservative_ceiling": _metric_view(
            fixed_shadow_control_surface, "harmful_replace_rate"
        ).get("conservative_ceiling"),
        "fixed_shadow_reference_label": (
            str(reference_surface.get("label") or "")
            if isinstance(reference_surface, Mapping)
            else ""
        ),
        "fixed_shadow_reference_replace_recall_conservative_floor": (
            _metric_view(reference_surface or {}, "replace_recall").get("conservative_floor")
            if isinstance(reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_reference_harmful_replace_conservative_ceiling": (
            _metric_view(reference_surface or {}, "harmful_replace_rate").get(
                "conservative_ceiling"
            )
            if isinstance(reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_reference_false_abstain_conservative_ceiling": (
            _metric_view(reference_surface or {}, "false_abstain_rate").get("conservative_ceiling")
            if isinstance(reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_reference_label": (
            str(active_only_reference_surface.get("label") or "")
            if isinstance(active_only_reference_surface, Mapping)
            else ""
        ),
        "fixed_shadow_active_only_reference_replace_recall_conservative_floor": (
            _metric_view(active_only_reference_surface or {}, "replace_recall").get(
                "conservative_floor"
            )
            if isinstance(active_only_reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_reference_harmful_replace_conservative_ceiling": (
            _metric_view(active_only_reference_surface or {}, "harmful_replace_rate").get(
                "conservative_ceiling"
            )
            if isinstance(active_only_reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_reference_false_abstain_conservative_ceiling": (
            _metric_view(active_only_reference_surface or {}, "false_abstain_rate").get(
                "conservative_ceiling"
            )
            if isinstance(active_only_reference_surface, Mapping)
            else None
        ),
        "fixed_shadow_ladder_label": (
            str(ladder_surface.get("label") or "") if isinstance(ladder_surface, Mapping) else ""
        ),
        "fixed_shadow_ladder_replace_or_soft_recall_conservative_floor": (
            _metric_view(ladder_surface or {}, "replace_or_soft_recall").get("conservative_floor")
            if isinstance(ladder_surface, Mapping)
            else None
        ),
        "fixed_shadow_ladder_soft_noise_conservative_ceiling": (
            _metric_view(ladder_surface or {}, "soft_noise_rate").get("conservative_ceiling")
            if isinstance(ladder_surface, Mapping)
            else None
        ),
        "fixed_shadow_rescue_overlay_label": (
            str(rescue_overlay_surface.get("label") or "")
            if isinstance(rescue_overlay_surface, Mapping)
            else ""
        ),
        "fixed_shadow_rescue_overlay_replace_recall_conservative_floor": (
            _metric_view(rescue_overlay_surface or {}, "replace_recall").get("conservative_floor")
            if isinstance(rescue_overlay_surface, Mapping)
            else None
        ),
        "fixed_shadow_rescue_overlay_harmful_replace_conservative_ceiling": (
            _metric_view(rescue_overlay_surface or {}, "harmful_replace_rate").get(
                "conservative_ceiling"
            )
            if isinstance(rescue_overlay_surface, Mapping)
            else None
        ),
        "fixed_shadow_rescue_overlay_false_abstain_conservative_ceiling": (
            _metric_view(rescue_overlay_surface or {}, "false_abstain_rate").get(
                "conservative_ceiling"
            )
            if isinstance(rescue_overlay_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_rescue_overlay_label": (
            str(active_only_rescue_overlay_surface.get("label") or "")
            if isinstance(active_only_rescue_overlay_surface, Mapping)
            else ""
        ),
        "fixed_shadow_active_only_rescue_overlay_replace_recall_conservative_floor": (
            _metric_view(active_only_rescue_overlay_surface or {}, "replace_recall").get(
                "conservative_floor"
            )
            if isinstance(active_only_rescue_overlay_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_rescue_overlay_harmful_replace_conservative_ceiling": (
            _metric_view(active_only_rescue_overlay_surface or {}, "harmful_replace_rate").get(
                "conservative_ceiling"
            )
            if isinstance(active_only_rescue_overlay_surface, Mapping)
            else None
        ),
        "fixed_shadow_active_only_rescue_overlay_false_abstain_conservative_ceiling": (
            _metric_view(active_only_rescue_overlay_surface or {}, "false_abstain_rate").get(
                "conservative_ceiling"
            )
            if isinstance(active_only_rescue_overlay_surface, Mapping)
            else None
        ),
        "reviewed_auto_abstain_recall_conservative_floor": None,
        "reviewed_auto_harmful_allow_conservative_ceiling": None,
        "curated_abstain_recall_conservative_floor": None,
        "curated_harmful_allow_conservative_ceiling": None,
    }
    if isinstance(reviewed_auto_row, Mapping):
        reviewed_auto_surface = next(
            (
                surface
                for surface in veto_proxy_surfaces
                if isinstance(surface.get("config"), Mapping)
                and str(surface["config"].get("source_id") or "").strip()
                == str(reviewed_auto_row.get("source_id") or "").strip()
            ),
            None,
        )
        if isinstance(reviewed_auto_surface, Mapping):
            confidence_corridor["reviewed_auto_abstain_recall_conservative_floor"] = _metric_view(
                reviewed_auto_surface, "abstain_recall"
            ).get("conservative_floor")
            confidence_corridor["reviewed_auto_harmful_allow_conservative_ceiling"] = _metric_view(
                reviewed_auto_surface, "harmful_allow_rate"
            ).get("conservative_ceiling")
    if isinstance(curated_row, Mapping):
        curated_surface = next(
            (
                surface
                for surface in veto_proxy_surfaces
                if isinstance(surface.get("config"), Mapping)
                and str(surface["config"].get("source_id") or "").strip()
                == str(curated_row.get("source_id") or "").strip()
            ),
            None,
        )
        if isinstance(curated_surface, Mapping):
            confidence_corridor["curated_abstain_recall_conservative_floor"] = _metric_view(
                curated_surface, "abstain_recall"
            ).get("conservative_floor")
            confidence_corridor["curated_harmful_allow_conservative_ceiling"] = _metric_view(
                curated_surface, "harmful_allow_rate"
            ).get("conservative_ceiling")

    return {
        "schema_version": 1,
        "status": "ok",
        "pair": "en-es",
        "generated_at": generated_at,
        "methodology": {
            "bootstrap_kind": "cluster_bootstrap_plus_leave_one_cluster_out",
            "bootstrap_iterations": int(bootstrap_iterations),
            "random_seed": int(random_seed),
            "confidence_level": float(confidence_level),
            "fixed_shadow_cluster_key": "family_id",
            "veto_proxy_cluster_key": "trigger",
            "caveats": [
                "Fixed-shadow runtime scorer bounds and veto-proxy blocker bounds are different evaluation surfaces.",
                "The conservative floors and ceilings are intended as current en-es corridor reads, not as fully calibrated production guarantees.",
                "Leave-one-cluster-out stress is included because family sensitivity matters more than optimistic per-row confidence.",
            ],
        },
        "inputs": {
            "sentence_dataset": str(sentence_dataset),
            "benchmark_dataset": str(benchmark_dataset),
            "benchmark_json": str(benchmark_json),
            "family_splits_manifest": str(family_splits_manifest),
            "data_root": str(data_root),
            "forward_seed_max_words": int(forward_seed_max_words),
            "translation_dict": str(translation_dict) if translation_dict else "",
            "reverse_translation_dict": (
                str(reverse_translation_dict) if reverse_translation_dict else ""
            ),
        },
        "fixed_shadow_bounds": fixed_shadow_surfaces,
        "veto_proxy_bounds": veto_proxy_surfaces,
        "confidence_corridor": confidence_corridor,
    }


def main() -> int:
    args = _parse_args()
    report = build_generalization_bound_report(
        sentence_dataset=args.sentence_dataset,
        benchmark_dataset=args.benchmark_dataset,
        benchmark_json=args.benchmark_json,
        family_splits_manifest=args.family_splits_manifest,
        data_root=args.data_root,
        translation_dict=args.translation_dict,
        reverse_translation_dict=args.reverse_translation_dict,
        forward_seed_max_words=max(1, int(args.forward_seed_max_words)),
        bootstrap_iterations=max(1, int(args.bootstrap_iterations)),
        random_seed=int(args.random_seed),
        confidence_level=min(max(float(args.confidence_level), 0.50), 0.999),
        include_sentence_transformer_reference=bool(args.include_sentence_transformer_reference),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_generalization_bound_markdown(
            report,
            fixed_shadow_metric_order=tuple(
                list(FIXED_SHADOW_METRIC_DIRECTIONS.keys())
                + [
                    metric_name
                    for metric_name in FIXED_SHADOW_LADDER_METRIC_DIRECTIONS.keys()
                    if metric_name not in FIXED_SHADOW_METRIC_DIRECTIONS
                ]
            ),
            veto_proxy_metric_order=tuple(VETO_PROXY_METRIC_DIRECTIONS.keys()),
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
