#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXAMPLE_FRAME_BATCH_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
for candidate in (str(SCRIPT_ROOT), str(PROJECT_ROOT / "core")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
)
from semantic_llm_prompt_downstream_en_es import DEFAULT_DATASET_PATH  # noqa: E402
from semantic_llm_prototype_admission_probe_en_es import (  # noqa: E402
    DEFAULT_PHRASE_PROTOTYPE_MARGIN,
)
from semantic_llm_prototype_ablation_matrix_en_es import (  # noqa: E402
    build_prototype_ablation_matrix_report,
)
from semantic_phrase_prototype_policy_replay import (  # noqa: E402
    replay_phrase_prototype_policy_summary,
)
from semantic_source_margin_policy_sweep_rendering import (  # noqa: E402
    render_margin_policy_sweep_markdown,
)
from semantic_source_margin_policy_support import (  # noqa: E402
    limitations_for_margin_recommendation,
)
from semantic_source_margin_policy_sweep_io import (  # noqa: E402
    _load_json,
    _repo_relative,
    _resolve_repo_path,
    _utc_now,
    _write_json,
)
from semantic_source_heldout_validation_en_es import (  # noqa: E402
    DEFAULT_CONTEXT_VIEW,
    DEFAULT_DECISION_SHAPE,
    DEFAULT_PROMOTION_CANDIDATE_EVIDENCE,
    DEFAULT_SCORER,
    DEFAULT_SOURCE_MODE,
    build_heldout_sentence_dataset,
    build_source_heldout_validation_report,
)


DEFAULT_HELDOUT_SUITES = (
    (
        "active_shadow_v2",
        DOCS_ROOT / "test_inputs" / "semantic_routing_cases" / "en_es_source_heldout_cases_v2.json",
    ),
    (
        "phrase_v1",
        DOCS_ROOT
        / "test_inputs"
        / "semantic_routing_cases"
        / "en_es_source_phrase_heldout_cases_v1.json",
    ),
    (
        "phrase_v2",
        DOCS_ROOT
        / "test_inputs"
        / "semantic_routing_cases"
        / "en_es_source_phrase_heldout_cases_v2.json",
    ),
    (
        "phrase_challenge_v1",
        DOCS_ROOT
        / "test_inputs"
        / "semantic_routing_cases"
        / "en_es_source_phrase_challenge_cases_v1.json",
    ),
    (
        "phrase_stress_v1",
        DOCS_ROOT
        / "test_inputs"
        / "semantic_routing_cases"
        / "en_es_source_phrase_stress_cases_v1.json",
    ),
)
DEFAULT_MARGIN_GRID = (0.0, 0.001, 0.005, 0.01, 0.02, 0.05)
DEFAULT_PHRASE_PROTOTYPE_MARGIN_GRID = (DEFAULT_PHRASE_PROTOTYPE_MARGIN,)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_source_margin_policy_sweep_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_source_margin_policy_sweep_latest.md"


@dataclass(frozen=True)
class HeldoutSuiteSpec:
    suite_id: str
    path: Path
    payload: Mapping[str, object]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep candidate active-vs-shadow margins across the current en-es source "
            "held-out suites and the full v10 source ablation lane."
        )
    )
    parser.add_argument("--base-dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--evidence-batch-json",
        type=Path,
        default=DEFAULT_PROMOTION_CANDIDATE_EVIDENCE,
    )
    parser.add_argument(
        "--heldout-suite",
        action="append",
        default=[],
        help="Optional held-out suite in the form suite_id=path. Defaults to current suites.",
    )
    parser.add_argument(
        "--margin-grid",
        default=",".join(_format_margin(value) for value in DEFAULT_MARGIN_GRID),
        help="Comma-separated min-margin values.",
    )
    parser.add_argument(
        "--phrase-prototype-margin-grid",
        default=",".join(_format_margin(value) for value in DEFAULT_PHRASE_PROTOTYPE_MARGIN_GRID),
        help=(
            "Comma-separated dominance margins required before semantic phrase-control "
            "prototypes can veto active/shadow scoring."
        ),
    )
    parser.add_argument("--scorer-id", default=DEFAULT_SCORER)
    parser.add_argument("--context-view", default=DEFAULT_CONTEXT_VIEW)
    parser.add_argument("--min-active-score", type=float, default=0.0)
    parser.add_argument("--decision-shape", default=DEFAULT_DECISION_SHAPE)
    parser.add_argument(
        "--window-tokens",
        type=int,
        default=DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    )
    parser.add_argument("--mask-token", default=DEFAULT_SENTENCE_VETO_MASK_TOKEN)
    parser.add_argument(
        "--skip-full-v10-ablation",
        action="store_true",
        help="Only sweep the held-out suites, not the full sentence-veto v10 dataset.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="Exit non-zero when no margin passes every included suite.",
    )
    return parser.parse_args()


def build_margin_policy_sweep_report(
    *,
    base_dataset_payload: Mapping[str, object],
    evidence_batch_payload: Mapping[str, object],
    heldout_suites: Sequence[HeldoutSuiteSpec],
    margins: Sequence[float] = DEFAULT_MARGIN_GRID,
    phrase_prototype_margins: Sequence[float] = DEFAULT_PHRASE_PROTOTYPE_MARGIN_GRID,
    scorer_id: str = DEFAULT_SCORER,
    context_view: str = DEFAULT_CONTEXT_VIEW,
    min_active_score: float = 0.0,
    decision_shape: str = DEFAULT_DECISION_SHAPE,
    include_full_v10_ablation: bool = True,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    normalized_margins = _normalize_margins(margins)
    normalized_phrase_prototype_margins = _normalize_margins(phrase_prototype_margins)
    if not heldout_suites:
        raise ValueError("At least one held-out suite is required.")
    if not normalized_margins or not normalized_phrase_prototype_margins:
        raise ValueError("At least one active and phrase margin is required.")

    rows: list[dict[str, object]] = []
    if decision_shape in {
        "active_shadow_phrase_semantic_prototypes",
        "active_shadow_phrase_semantic_surface_pos",
    }:
        for suite in heldout_suites:
            rows.extend(
                _heldout_phrase_prototype_policy_rows(
                    base_dataset_payload=base_dataset_payload,
                    suite=suite,
                    evidence_batch_payload=evidence_batch_payload,
                    margins=normalized_margins,
                    phrase_prototype_margins=normalized_phrase_prototype_margins,
                    scorer_id=scorer_id,
                    context_view=context_view,
                    min_active_score=min_active_score,
                    window_tokens=window_tokens,
                    mask_token=mask_token,
                    generated_at=generated_at,
                    decision_shape=decision_shape,
                )
            )
    else:
        for suite in heldout_suites:
            for margin in normalized_margins:
                for phrase_prototype_margin in normalized_phrase_prototype_margins:
                    report = build_source_heldout_validation_report(
                        base_dataset_payload=base_dataset_payload,
                        heldout_case_payload=suite.payload,
                        evidence_batch_payload=evidence_batch_payload,
                        scorer_id=scorer_id,
                        context_view=context_view,
                        min_active_score=min_active_score,
                        min_margin=margin,
                        phrase_prototype_margin=phrase_prototype_margin,
                        decision_shape=decision_shape,
                        window_tokens=window_tokens,
                        mask_token=mask_token,
                        generated_at=generated_at,
                    )
                    rows.append(
                        _heldout_policy_row(
                            suite=suite,
                            report=report,
                            margin=margin,
                            phrase_prototype_margin=phrase_prototype_margin,
                        )
                    )

    if include_full_v10_ablation:
        rows.extend(
            _full_v10_policy_rows(
                dataset_payload=base_dataset_payload,
                evidence_batch_payload=evidence_batch_payload,
                margins=normalized_margins,
                phrase_prototype_margins=normalized_phrase_prototype_margins,
                scorer_id=scorer_id,
                context_view=context_view,
                min_active_score=min_active_score,
                decision_shape=decision_shape,
                window_tokens=window_tokens,
                mask_token=mask_token,
                generated_at=generated_at,
            )
        )

    recommendation = _build_margin_recommendation(
        rows,
        margins=normalized_margins,
        phrase_prototype_margins=normalized_phrase_prototype_margins,
    )
    status = "ok" if recommendation["recommended_policy"] is not None else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "margin_candidate_found" if status == "ok" else "margin_review",
        "generated_at": generated_at,
        "pair": str(base_dataset_payload.get("pair") or "").strip() or "en-es",
        "base_dataset_id": str(base_dataset_payload.get("dataset_id") or "").strip(),
        "evidence_source_id": str(evidence_batch_payload.get("source_id") or "").strip(),
        "evidence_batch_id": str(evidence_batch_payload.get("batch_id") or "").strip(),
        "configured_lane": {
            "source_mode": DEFAULT_SOURCE_MODE,
            "scorer_id": str(scorer_id or "").strip(),
            "context_view": str(context_view or "").strip(),
            "min_active_score": float(min_active_score),
            "decision_shape": str(decision_shape or "").strip(),
        },
        "grid": {
            "margins": normalized_margins,
            "phrase_prototype_margins": normalized_phrase_prototype_margins,
            "heldout_suites": [
                {
                    "suite_id": suite.suite_id,
                    "path": _repo_relative(suite.path),
                    "dataset_id": str(suite.payload.get("dataset_id") or "").strip(),
                    "case_scope": str(suite.payload.get("case_scope") or "").strip(),
                }
                for suite in heldout_suites
            ],
            "include_full_v10_ablation": bool(include_full_v10_ablation),
        },
        "summary": {
            "suite_count": len({str(row.get("suite_id") or "") for row in rows}),
            "row_count": len(rows),
            "passing_policy_count": len(recommendation["passing_policies"]),
            "recommended_min_margin": recommendation["recommended_min_margin"],
            "recommended_phrase_prototype_margin": recommendation[
                "recommended_phrase_prototype_margin"
            ],
            "recommended_policy": recommendation["recommended_policy"],
        },
        "recommendation": recommendation,
        "rows": rows,
        "limitations": limitations_for_margin_recommendation(recommendation),
    }


def _heldout_policy_row(
    *,
    suite: HeldoutSuiteSpec,
    report: Mapping[str, object],
    margin: float,
    phrase_prototype_margin: float,
) -> dict[str, object]:
    summary = _as_mapping(report.get("summary"))
    configured_row = _as_mapping(report.get("configured_row"))
    return {
        "suite_id": suite.suite_id,
        "suite_type": "heldout",
        "dataset_id": str(report.get("heldout_dataset_id") or "").strip(),
        "case_scope": str(report.get("heldout_case_scope") or "").strip(),
        "min_margin": float(margin),
        "phrase_prototype_margin": float(phrase_prototype_margin),
        "status": str(summary.get("status") or report.get("status") or "").strip(),
        "decision": str(summary.get("decision") or report.get("decision") or "").strip(),
        "passes": _row_passes(summary),
        "case_count": int(summary.get("case_count") or 0),
        "gold_replace_cases": int(summary.get("gold_replace_cases") or 0),
        "gold_abstain_cases": int(summary.get("gold_abstain_cases") or 0),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
        "replace_recall": _round_float(summary.get("replace_recall")),
        "decision_accuracy": _round_float(summary.get("decision_accuracy")),
        "harmful_replace_case_ids": list(summary.get("harmful_replace_case_ids") or ()),
        "false_abstain_case_ids": list(summary.get("false_abstain_case_ids") or ()),
        "phrase_preemption_hit_count": int(configured_row.get("phrase_preemption_hit_count") or 0),
        "active_rescue_applied_count": int(configured_row.get("active_rescue_applied_count") or 0),
    }


def _heldout_phrase_prototype_policy_rows(
    *,
    base_dataset_payload: Mapping[str, object],
    suite: HeldoutSuiteSpec,
    evidence_batch_payload: Mapping[str, object],
    margins: Sequence[float],
    phrase_prototype_margins: Sequence[float],
    scorer_id: str,
    context_view: str,
    min_active_score: float,
    window_tokens: int,
    mask_token: str,
    generated_at: str,
    decision_shape: str = "active_shadow_phrase_semantic_prototypes",
) -> list[dict[str, object]]:
    heldout_dataset = build_heldout_sentence_dataset(
        base_dataset_payload=base_dataset_payload,
        heldout_case_payload=suite.payload,
    )
    base_row = _base_phrase_prototype_matrix_row(
        dataset_payload=heldout_dataset,
        evidence_batch_payload=evidence_batch_payload,
        scorer_id=scorer_id,
        context_view=context_view,
        min_active_score=min_active_score,
        window_tokens=window_tokens,
        mask_token=mask_token,
        generated_at=generated_at,
        decision_shape=decision_shape,
    )
    if not isinstance(base_row, Mapping):
        return []
    rows: list[dict[str, object]] = []
    for margin in margins:
        for phrase_prototype_margin in phrase_prototype_margins:
            summary = replay_phrase_prototype_policy_summary(
                base_row.get("row_results", ()),
                min_active_score=min_active_score,
                min_margin=margin,
                phrase_prototype_margin=phrase_prototype_margin,
                use_surface_pos=decision_shape == "active_shadow_phrase_semantic_surface_pos",
            )
            rows.append(
                _phrase_prototype_policy_row(
                    suite_id=suite.suite_id,
                    suite_type="heldout",
                    dataset_id=str(heldout_dataset.get("dataset_id") or "").strip(),
                    case_scope=str(suite.payload.get("case_scope") or "").strip(),
                    margin=margin,
                    phrase_prototype_margin=phrase_prototype_margin,
                    summary=summary,
                    base_row=base_row,
                )
            )
    return rows


def _full_v10_policy_rows(
    *,
    dataset_payload: Mapping[str, object],
    evidence_batch_payload: Mapping[str, object],
    margins: Sequence[float],
    phrase_prototype_margins: Sequence[float],
    scorer_id: str,
    context_view: str,
    min_active_score: float,
    decision_shape: str,
    window_tokens: int,
    mask_token: str,
    generated_at: str,
) -> list[dict[str, object]]:
    if decision_shape in {
        "active_shadow_phrase_semantic_prototypes",
        "active_shadow_phrase_semantic_surface_pos",
    }:
        base_row = _base_phrase_prototype_matrix_row(
            dataset_payload=dataset_payload,
            evidence_batch_payload=evidence_batch_payload,
            scorer_id=scorer_id,
            context_view=context_view,
            min_active_score=min_active_score,
            window_tokens=window_tokens,
            mask_token=mask_token,
            generated_at=generated_at,
            decision_shape=decision_shape,
        )
        if not isinstance(base_row, Mapping):
            return []
        rows: list[dict[str, object]] = []
        for margin in margins:
            for phrase_prototype_margin in phrase_prototype_margins:
                summary = replay_phrase_prototype_policy_summary(
                    base_row.get("row_results", ()),
                    min_active_score=min_active_score,
                    min_margin=margin,
                    phrase_prototype_margin=phrase_prototype_margin,
                    use_surface_pos=decision_shape == "active_shadow_phrase_semantic_surface_pos",
                )
                rows.append(
                    _phrase_prototype_policy_row(
                        suite_id="full_v10_ablation",
                        suite_type="full_dataset_ablation",
                        dataset_id=str(dataset_payload.get("dataset_id") or "").strip(),
                        case_scope="full_sentence_veto_v10",
                        margin=margin,
                        phrase_prototype_margin=phrase_prototype_margin,
                        summary=summary,
                        base_row=base_row,
                    )
                )
        return rows

    matrix_report = build_prototype_ablation_matrix_report(
        queue_payload=_all_family_queue_payload(dataset_payload, generated_at=generated_at),
        dataset_payload=dataset_payload,
        source_modes=(DEFAULT_SOURCE_MODE,),
        scopes=("all_dataset_families",),
        scorers=(scorer_id,),
        context_views=(context_view,),
        min_active_scores=(float(min_active_score),),
        min_margins=margins,
        phrase_prototype_margins=phrase_prototype_margins,
        source_payload_overrides={DEFAULT_SOURCE_MODE: evidence_batch_payload},
        window_tokens=window_tokens,
        mask_token=mask_token,
        generated_at=generated_at,
    )
    rows: list[dict[str, object]] = []
    for matrix_row in matrix_report.get("rows", ()):
        if not isinstance(matrix_row, Mapping):
            continue
        if str(matrix_row.get("decision_shape") or "") != decision_shape:
            continue
        rows.append(
            {
                "suite_id": "full_v10_ablation",
                "suite_type": "full_dataset_ablation",
                "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
                "case_scope": "full_sentence_veto_v10",
                "min_margin": float(matrix_row.get("min_margin") or 0.0),
                "phrase_prototype_margin": float(matrix_row.get("phrase_prototype_margin") or 0.0),
                "status": "ok" if _row_passes(matrix_row) else "review",
                "decision": "heldout_pass" if _row_passes(matrix_row) else "heldout_review",
                "passes": _row_passes(matrix_row),
                "case_count": int(matrix_row.get("cases_total") or 0),
                "gold_replace_cases": int(matrix_row.get("gold_replace_cases") or 0),
                "gold_abstain_cases": int(matrix_row.get("gold_abstain_cases") or 0),
                "harmful_replace_count": int(matrix_row.get("harmful_replace_count") or 0),
                "false_abstain_count": int(matrix_row.get("false_abstain_count") or 0),
                "replace_recall": _round_float(matrix_row.get("replace_recall")),
                "decision_accuracy": _round_float(matrix_row.get("decision_accuracy")),
                "harmful_replace_case_ids": list(matrix_row.get("harmful_replace_case_ids") or ()),
                "false_abstain_case_ids": list(matrix_row.get("false_abstain_case_ids") or ()),
                "phrase_preemption_hit_count": int(
                    matrix_row.get("phrase_preemption_hit_count") or 0
                ),
                "active_rescue_applied_count": int(
                    matrix_row.get("active_rescue_applied_count") or 0
                ),
            }
        )
    return rows


def _base_phrase_prototype_matrix_row(
    *,
    dataset_payload: Mapping[str, object],
    evidence_batch_payload: Mapping[str, object],
    scorer_id: str,
    context_view: str,
    min_active_score: float,
    window_tokens: int,
    mask_token: str,
    generated_at: str,
    decision_shape: str = "active_shadow_phrase_semantic_prototypes",
) -> Mapping[str, object] | None:
    matrix_report = build_prototype_ablation_matrix_report(
        queue_payload=_all_family_queue_payload(dataset_payload, generated_at=generated_at),
        dataset_payload=dataset_payload,
        source_modes=(DEFAULT_SOURCE_MODE,),
        scopes=("all_dataset_families",),
        scorers=(scorer_id,),
        context_views=(context_view,),
        min_active_scores=(float(min_active_score),),
        min_margins=(0.0,),
        phrase_prototype_margins=(0.0,),
        source_payload_overrides={DEFAULT_SOURCE_MODE: evidence_batch_payload},
        window_tokens=window_tokens,
        mask_token=mask_token,
        include_row_results=True,
        generated_at=generated_at,
    )
    for matrix_row in matrix_report.get("rows", ()):
        if not isinstance(matrix_row, Mapping):
            continue
        if str(matrix_row.get("decision_shape") or "") == decision_shape:
            return matrix_row
    return None


def _phrase_prototype_policy_row(
    *,
    suite_id: str,
    suite_type: str,
    dataset_id: str,
    case_scope: str,
    margin: float,
    phrase_prototype_margin: float,
    summary: Mapping[str, object],
    base_row: Mapping[str, object],
) -> dict[str, object]:
    return {
        "suite_id": suite_id,
        "suite_type": suite_type,
        "dataset_id": dataset_id,
        "case_scope": case_scope,
        "min_margin": float(margin),
        "phrase_prototype_margin": float(phrase_prototype_margin),
        "status": "ok" if _row_passes(summary) else "review",
        "decision": "heldout_pass" if _row_passes(summary) else "heldout_review",
        "passes": _row_passes(summary),
        "case_count": int(summary.get("case_count") or 0),
        "gold_replace_cases": int(summary.get("gold_replace_cases") or 0),
        "gold_abstain_cases": int(summary.get("gold_abstain_cases") or 0),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
        "replace_recall": _round_float(summary.get("replace_recall")),
        "decision_accuracy": _round_float(summary.get("decision_accuracy")),
        "harmful_replace_case_ids": list(summary.get("harmful_replace_case_ids") or ()),
        "false_abstain_case_ids": list(summary.get("false_abstain_case_ids") or ()),
        "phrase_preemption_hit_count": int(base_row.get("phrase_preemption_hit_count") or 0),
        "active_rescue_applied_count": int(summary.get("active_rescue_applied_count") or 0),
    }


def _build_margin_recommendation(
    rows: Sequence[Mapping[str, object]],
    *,
    margins: Sequence[float],
    phrase_prototype_margins: Sequence[float],
) -> dict[str, object]:
    suite_ids = sorted({str(row.get("suite_id") or "") for row in rows if row.get("suite_id")})
    passing_policies: list[dict[str, float]] = []
    blockers_by_policy: dict[str, list[dict[str, object]]] = {}
    for margin in margins:
        for phrase_prototype_margin in phrase_prototype_margins:
            policy_rows = [
                row
                for row in rows
                if abs(float(row.get("min_margin") or 0.0) - margin) <= 1e-9
                and abs(float(row.get("phrase_prototype_margin") or 0.0) - phrase_prototype_margin)
                <= 1e-9
            ]
            present_suite_ids = {str(row.get("suite_id") or "") for row in policy_rows}
            blockers = [row for row in policy_rows if not row.get("passes")]
            missing_suite_ids = [
                suite_id for suite_id in suite_ids if suite_id not in present_suite_ids
            ]
            policy_key = _format_policy_key(margin, phrase_prototype_margin)
            if not blockers and not missing_suite_ids and suite_ids:
                passing_policies.append(
                    {
                        "min_margin": float(margin),
                        "phrase_prototype_margin": float(phrase_prototype_margin),
                    }
                )
                continue
            blockers_by_policy[policy_key] = [
                {
                    "suite_id": str(row.get("suite_id") or "").strip(),
                    "harmful_replace_count": int(row.get("harmful_replace_count") or 0),
                    "false_abstain_count": int(row.get("false_abstain_count") or 0),
                    "harmful_replace_case_ids": list(row.get("harmful_replace_case_ids") or ()),
                    "false_abstain_case_ids": list(row.get("false_abstain_case_ids") or ()),
                }
                for row in blockers
            ] + [
                {
                    "suite_id": suite_id,
                    "harmful_replace_count": 0,
                    "false_abstain_count": 0,
                    "harmful_replace_case_ids": [],
                    "false_abstain_case_ids": [],
                    "reason": "suite_result_missing",
                }
                for suite_id in missing_suite_ids
            ]
    recommended_policy = min(
        passing_policies,
        key=lambda policy: (
            float(policy.get("min_margin") or 0.0),
            float(policy.get("phrase_prototype_margin") or 0.0),
        ),
        default=None,
    )
    recommended_min_margin = (
        float(recommended_policy["min_margin"]) if recommended_policy is not None else None
    )
    recommended_phrase_margin = (
        float(recommended_policy["phrase_prototype_margin"])
        if recommended_policy is not None
        else None
    )
    return {
        "decision": "candidate_margin" if recommended_policy is not None else "review",
        "recommended_min_margin": recommended_min_margin,
        "recommended_phrase_prototype_margin": recommended_phrase_margin,
        "recommended_policy": recommended_policy,
        "passing_margins": sorted({policy["min_margin"] for policy in passing_policies}),
        "passing_policies": passing_policies,
        "reason": (
            "smallest_passing_policy" if recommended_policy is not None else "no_policy_passed"
        ),
        "next_step": (
            "stress the candidate margin on non-v10 and broader phrase held-out suites"
            if recommended_policy is not None
            else (
                "diagnose phrase challenge misses and test phrase-source or pattern policy "
                "before promoting any margin"
            )
        ),
        "blockers_by_margin": blockers_by_policy,
        "blockers_by_policy": blockers_by_policy,
    }


def _row_passes(row: Mapping[str, object]) -> bool:
    return (
        int(row.get("harmful_replace_count") or 0) <= 0
        and int(row.get("false_abstain_count") or 0) <= 0
    )


def _all_family_queue_payload(
    dataset_payload: Mapping[str, object],
    *,
    generated_at: str,
) -> dict[str, object]:
    dataset_id = str(dataset_payload.get("dataset_id") or "").strip() or "sentence_veto_dataset"
    return {
        "schema_version": 1,
        "queue_id": f"{dataset_id}_margin_policy_sweep",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "generated_at": generated_at,
        "dataset_id": dataset_id,
        "families": [
            {
                "family_id": str(family.get("family_id") or "").strip(),
                "trigger": str(family.get("trigger") or "").strip(),
                "role": "target",
                "likely_bucket": "margin_policy_sweep",
            }
            for family in dataset_payload.get("families", ())
            if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
        ],
    }


def _parse_heldout_suite_specs(values: Sequence[str]) -> list[tuple[str, Path]]:
    if not values:
        return [(suite_id, path) for suite_id, path in DEFAULT_HELDOUT_SUITES]
    specs: list[tuple[str, Path]] = []
    for raw_value in values:
        if "=" not in raw_value:
            raise ValueError(f"Held-out suite must use suite_id=path: {raw_value!r}")
        suite_id, raw_path = raw_value.split("=", 1)
        normalized_suite_id = suite_id.strip()
        if not normalized_suite_id:
            raise ValueError(f"Held-out suite is missing a suite id: {raw_value!r}")
        specs.append((normalized_suite_id, _resolve_repo_path(raw_path)))
    return specs


def _load_heldout_suites(values: Sequence[str]) -> list[HeldoutSuiteSpec]:
    return [
        HeldoutSuiteSpec(
            suite_id=suite_id,
            path=path,
            payload=_load_json(path),
        )
        for suite_id, path in _parse_heldout_suite_specs(values)
    ]


def _normalize_margins(values: Sequence[float]) -> list[float]:
    seen: set[float] = set()
    margins: list[float] = []
    for value in values:
        margin = float(value)
        if margin < 0:
            raise ValueError("Margins must be non-negative.")
        if margin not in seen:
            margins.append(margin)
            seen.add(margin)
    return sorted(margins)


def _parse_float_grid(value: str) -> list[float]:
    return [float(item) for item in _normalize_string_list(value)]


def _normalize_string_list(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _format_policy_key(min_margin: float, phrase_prototype_margin: float) -> str:
    return f"m={_format_margin(min_margin)};phrase={_format_margin(phrase_prototype_margin)}"


def _format_margin(value: object) -> str:
    return f"{float(value):.3f}".rstrip("0").rstrip(".") if value is not None else "none"


def _round_float(value: object) -> float:
    return round(float(value or 0.0), 4)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def main() -> int:
    args = _parse_args()
    report = build_margin_policy_sweep_report(
        base_dataset_payload=_load_json(args.base_dataset),
        evidence_batch_payload=_load_json(args.evidence_batch_json),
        heldout_suites=_load_heldout_suites(args.heldout_suite),
        margins=_parse_float_grid(args.margin_grid),
        phrase_prototype_margins=_parse_float_grid(args.phrase_prototype_margin_grid),
        scorer_id=args.scorer_id,
        context_view=args.context_view,
        min_active_score=float(args.min_active_score),
        decision_shape=args.decision_shape,
        include_full_v10_ablation=not args.skip_full_v10_ablation,
        window_tokens=int(args.window_tokens),
        mask_token=args.mask_token,
    )
    _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_margin_policy_sweep_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
