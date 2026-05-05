#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_INPUTS_ROOT = DOCS_ROOT / "test_inputs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    RuntimeSimilarityBackend,
    extract_runtime_phrase_control_signals,
)
from semantic_example_frame_evidence_support import (  # noqa: E402
    active_examples_for_family,
    build_example_frame_lookup,
    case_context_text,
    phrase_examples_for_family,
    sense_id,
    shadow_example_pairs_for_family,
)
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_SCORER_ID,
    _load_json,
)
from semantic_routing_sentence_veto_support import (  # noqa: E402
    _resolve_sentence_veto_phrase_guard_pos_tags,
)
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _repo_path,
    _safe_float,
    _utility_weights,
    score_product_outcome_counts,
)
from semantic_veto_llm_pilot_scoring_rendering import (  # noqa: E402
    render_semantic_veto_llm_pilot_scoring_markdown,
)
from semantic_veto_llm_pilot_scoring_policy import (  # noqa: E402
    limitations as _limitations,
    next_steps as _next_steps,
)
from semantic_veto_veto_only_probe_en_es import _veto_hit  # noqa: E402


DEFAULT_PLAN = TEST_INPUTS_ROOT / "semantic_veto_llm_pilot_plan_en_es.json"
DEFAULT_ADMISSION = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_admission_en_es_latest.json"
DEFAULT_POLICY = TEST_INPUTS_ROOT / "semantic_veto_product_quality_policy_en_es.json"
DEFAULT_SOURCE_CONTRACT = (
    TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_contract_expanded_latest.json"
)
DEFAULT_MATRIX = TEST_OUTPUTS_ROOT / "semantic_decision_rule_matrix_en_es_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_scoring_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_scoring_en_es_latest.md"
DEFAULT_CONFIG_ID = "control_st_masked_all_margin_phrase_override"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Score admitted en-es semantic-veto LLM pilot rows against independent "
            "source evidence and the frozen allow-by-default veto candidate."
        )
    )
    parser.add_argument("--plan-json", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--admission-json", type=Path, default=DEFAULT_ADMISSION)
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--source-contract-json", type=Path, default=DEFAULT_SOURCE_CONTRACT)
    parser.add_argument("--matrix-json", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--base-config-id", default=DEFAULT_CONFIG_ID)
    parser.add_argument("--scorer-id", default="")
    parser.add_argument("--context-view", default="")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_semantic_veto_llm_pilot_scoring_report(
        plan_payload=_load_json(args.plan_json),
        admission_payload=_load_json(args.admission_json),
        policy_payload=_load_json(args.policy_json),
        dataset_payload=_load_json(args.dataset_json),
        source_contract_payload=_load_json(args.source_contract_json),
        matrix_payload=_load_json(args.matrix_json) if args.matrix_json.exists() else {},
        plan_path=args.plan_json,
        admission_path=args.admission_json,
        policy_path=args.policy_json,
        dataset_path=args.dataset_json,
        source_contract_path=args.source_contract_json,
        matrix_path=args.matrix_json if args.matrix_json.exists() else None,
        base_config_id=args.base_config_id,
        scorer_id_override=args.scorer_id,
        context_view_override=args.context_view,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_semantic_veto_llm_pilot_scoring_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_semantic_veto_llm_pilot_scoring_report(
    *,
    plan_payload: Mapping[str, object],
    admission_payload: Mapping[str, object],
    policy_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    source_contract_payload: Mapping[str, object],
    matrix_payload: Mapping[str, object] | None = None,
    plan_path: Path | None = None,
    admission_path: Path | None = None,
    policy_path: Path | None = None,
    dataset_path: Path | None = None,
    source_contract_path: Path | None = None,
    matrix_path: Path | None = None,
    base_config_id: str = DEFAULT_CONFIG_ID,
    scorer_id_override: str = "",
    context_view_override: str = "",
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    candidate = dict(
        _as_mapping(plan_payload.get("candidate"))
        or _as_mapping(admission_payload.get("candidate"))
    )
    base_config = _base_config(
        matrix_payload or {}, str(base_config_id or candidate.get("base_config_id") or "")
    )
    scorer_id = str(scorer_id_override or base_config.get("scorer_id") or DEFAULT_SCORER_ID).strip()
    context_view = str(
        context_view_override or base_config.get("context_view") or "masked_sentence"
    ).strip()
    shadow_lead_min = float(candidate.get("shadow_lead_min") or 0.0)
    shadow_score_min = float(candidate.get("shadow_score_min") or 0.0)
    phrase_mode = str(candidate.get("phrase_mode") or "shadow_or_phrase_score").strip()
    source_batch_payload = _source_batch_from_contract(
        source_contract_payload, source_contract_path
    )
    evidence_lookup = build_example_frame_lookup(source_batch_payload)
    dataset_family_index = _dataset_family_index(dataset_payload)
    admitted_rows = _mapping_rows(admission_payload.get("admitted_rows"))
    coverage_rows, case_rows, unscored_rows = _bind_pilot_rows(
        admitted_rows=admitted_rows,
        dataset_family_index=dataset_family_index,
        evidence_lookup=evidence_lookup,
        context_view=context_view,
    )
    texts = _collect_fit_texts(
        cases=case_rows,
        coverage_rows=coverage_rows,
        context_view=context_view,
    )
    scorer = RuntimeSimilarityBackend(scorer_id=scorer_id)
    scorer.fit(texts)
    scored_cases = [
        _score_case(
            case=row,
            scorer=scorer,
            phrase_mode=phrase_mode,
            shadow_lead_min=shadow_lead_min,
            shadow_score_min=shadow_score_min,
            context_view=context_view,
        )
        for row in case_rows
    ]
    weights = _utility_weights(policy_payload)
    acceptance = _as_mapping(policy_payload.get("acceptance"))
    overall_metrics = _score_product_cases(scored_cases, weights=weights, acceptance=acceptance)
    leakage = _leakage_checks(
        admitted_rows=admitted_rows,
        source_rows=_mapping_rows(source_batch_payload.get("rows")),
        scored_cases=scored_cases,
    )
    source_summary = _source_summary(source_contract_payload, source_batch_payload)
    source_summary["coverage_family_count"] = sum(1 for row in coverage_rows if row["scoreable"])
    source_summary["pilot_family_count"] = len(coverage_rows)
    source_summary["coverage_row_count"] = sum(
        int(row["pilot_row_count"]) for row in coverage_rows if row["scoreable"]
    )
    source_summary["pilot_row_count"] = len(admitted_rows)
    status = "ok" if not unscored_rows and not leakage["blocking_issue_count"] else "review"
    decision = _decision(status=status, metrics=overall_metrics, unscored_rows=unscored_rows)
    return {
        "schema_version": 1,
        "status": status,
        "decision": decision,
        "generated_at": generated_at,
        "pair": str(plan_payload.get("pair") or admission_payload.get("pair") or "en-es"),
        "inputs": {
            "plan_path": _repo_path(plan_path),
            "admission_path": _repo_path(admission_path),
            "policy_path": _repo_path(policy_path),
            "dataset_path": _repo_path(dataset_path),
            "source_contract_path": _repo_path(source_contract_path),
            "source_batch_path": str(source_contract_payload.get("batch_path") or ""),
            "matrix_path": _repo_path(matrix_path),
        },
        "candidate": {
            **candidate,
            "base_config_id": str(base_config_id or candidate.get("base_config_id") or ""),
            "scorer_id": scorer_id,
            "context_view": context_view,
            "scoring_shape": "independent_source_prototype_scores",
            "final_decision": "binary_replace_or_abstain",
        },
        "strict_flow": {
            "evaluation_rows_used_as_evidence": False,
            "source_evidence_promotion": str(candidate.get("source_evidence_promotion") or ""),
            "runtime_policy_change": str(candidate.get("runtime_policy_change") or ""),
            "locked_eval_threshold_tuning_allowed": bool(
                _as_mapping(plan_payload.get("split_policy")).get(
                    "threshold_tuning_allowed_on_locked_eval"
                )
            ),
            "thresholds_frozen_from_plan": True,
        },
        "source_evidence": source_summary,
        "leakage_checks": leakage,
        "summary": {
            "admitted_row_count": len(admitted_rows),
            "scored_case_count": len(scored_cases),
            "unscored_case_count": len(unscored_rows),
            "family_count": len(coverage_rows),
            "scoreable_family_count": source_summary["coverage_family_count"],
            "overall": overall_metrics,
            "target_status": str(
                _as_mapping(overall_metrics.get("target_checks")).get("target_status") or ""
            ),
        },
        "split_breakdowns": _breakdowns(
            scored_cases, "split", weights=weights, acceptance=acceptance
        ),
        "gold_type_breakdowns": _breakdowns(
            scored_cases, "gold_type", weights=weights, acceptance=acceptance
        ),
        "family_breakdowns": _breakdowns(
            scored_cases, "family_id", weights=weights, acceptance=acceptance
        ),
        "coverage_rows": coverage_rows,
        "unscored_rows": unscored_rows,
        "failure_rows": _failure_rows(scored_cases),
        "case_results": scored_cases,
        "limitations": _limitations(),
        "next_steps": _next_steps(
            status=status, metrics=overall_metrics, unscored_rows=unscored_rows
        ),
    }


def _bind_pilot_rows(
    *,
    admitted_rows: Sequence[Mapping[str, object]],
    dataset_family_index: Mapping[tuple[str, str], Mapping[str, object]],
    evidence_lookup: Mapping[str, Mapping[str, object]],
    context_view: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    grouped_rows: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    case_rows: list[dict[str, object]] = []
    unscored_rows: list[dict[str, object]] = []
    family_cache: dict[str, dict[str, object]] = {}
    for row in admitted_rows:
        trigger = str(row.get("trigger") or "").strip()
        target = str(row.get("candidate_replacement") or "").strip()
        family = dataset_family_index.get((trigger, target))
        if not isinstance(family, Mapping):
            unscored_rows.append(_unscored(row, "missing_dataset_family"))
            continue
        family_id = str(family.get("family_id") or "").strip()
        grouped_rows[family_id].append(row)
        coverage = family_cache.get(family_id)
        if coverage is None:
            coverage = _family_source_coverage(
                family=family,
                evidence_lookup=evidence_lookup,
                context_view=context_view,
            )
            family_cache[family_id] = coverage
        if not coverage["scoreable"]:
            unscored_rows.append(_unscored(row, ",".join(coverage["missing_requirements"])))
            continue
        case_rows.append(_case_from_pilot_row(row, family=family, coverage=coverage))
    coverage_rows = []
    for family_id, coverage in sorted(family_cache.items()):
        pilot_rows = grouped_rows.get(family_id, [])
        coverage_rows.append(
            {
                **coverage,
                "pilot_row_count": len(pilot_rows),
                "split_counts": dict(
                    sorted(Counter(str(row.get("split") or "") for row in pilot_rows).items())
                ),
                "gold_type_counts": dict(
                    sorted(Counter(str(row.get("gold_type") or "") for row in pilot_rows).items())
                ),
            }
        )
    return coverage_rows, case_rows, unscored_rows


def _family_source_coverage(
    *,
    family: Mapping[str, object],
    evidence_lookup: Mapping[str, Mapping[str, object]],
    context_view: str,
) -> dict[str, object]:
    active = _as_mapping(family.get("active"))
    shadows = [shadow for shadow in _mapping_rows(family.get("shadows"))]
    active_examples = active_examples_for_family(family, evidence_lookup, context_view=context_view)
    shadow_pairs = shadow_example_pairs_for_family(
        family,
        shadows,
        evidence_lookup,
        context_view=context_view,
    )
    phrase_examples = phrase_examples_for_family(family, evidence_lookup, context_view=context_view)
    shadow_counts = Counter(sense_id(shadow) for shadow, _example in shadow_pairs)
    missing = []
    if not active_examples:
        missing.append("active_examples")
    if not shadow_pairs:
        missing.append("shadow_examples")
    if not phrase_examples:
        missing.append("phrase_control_examples")
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(active.get("target_lemma") or "").strip(),
        "shadow_targets": [str(shadow.get("target_lemma") or "").strip() for shadow in shadows],
        "active_example_count": len(active_examples),
        "shadow_example_count": len(shadow_pairs),
        "shadow_example_counts_by_sense": dict(sorted(shadow_counts.items())),
        "phrase_control_example_count": len(phrase_examples),
        "scoreable": not missing,
        "missing_requirements": missing,
        "active_examples": active_examples,
        "shadow_examples": [
            {
                "sense_id": sense_id(shadow),
                "target_lemma": str(shadow.get("target_lemma") or "").strip(),
                "text": example,
            }
            for shadow, example in shadow_pairs
        ],
        "phrase_examples": phrase_examples,
    }


def _case_from_pilot_row(
    row: Mapping[str, object],
    *,
    family: Mapping[str, object],
    coverage: Mapping[str, object],
) -> dict[str, object]:
    active = _as_mapping(family.get("active"))
    shadows = _mapping_rows(family.get("shadows"))
    gold_type = str(row.get("gold_type") or "").strip()
    gold_decision = (
        "replace" if str(row.get("gold_decision") or "").strip() == "allow" else "abstain"
    )
    if gold_type == "positive_active":
        gold_winner = sense_id(active)
        gold_winner_type = "active"
    elif gold_type == "shadow_negative" and shadows:
        gold_winner = sense_id(shadows[0])
        gold_winner_type = "shadow"
    else:
        gold_winner = "none"
        gold_winner_type = "none"
    return {
        "case_id": str(row.get("row_id") or "").strip(),
        "family_id": str(family.get("family_id") or "").strip(),
        "pilot_family_id": str(row.get("family_id") or "").strip(),
        "trigger": str(row.get("trigger") or family.get("trigger") or "").strip(),
        "candidate_replacement": str(row.get("candidate_replacement") or "").strip(),
        "sentence": str(row.get("sentence") or "").strip(),
        "source_phrase": str(row.get("trigger") or family.get("trigger") or "").strip(),
        "split": str(row.get("split") or "").strip(),
        "gold_type": gold_type,
        "gold_decision": gold_decision,
        "gold_winner": gold_winner,
        "gold_winner_type": gold_winner_type,
        "active_sense": active,
        "shadow_senses": shadows,
        "active_examples": list(_as_sequence(coverage.get("active_examples"))),
        "shadow_examples": _mapping_rows(coverage.get("shadow_examples")),
        "phrase_examples": list(_as_sequence(coverage.get("phrase_examples"))),
        "difficulty_tags": [
            str(tag).strip() for tag in _as_sequence(row.get("difficulty_tags")) if str(tag).strip()
        ],
    }


def _score_case(
    *,
    case: Mapping[str, object],
    scorer: RuntimeSimilarityBackend,
    phrase_mode: str,
    shadow_lead_min: float,
    shadow_score_min: float,
    context_view: str,
) -> dict[str, object]:
    context_text = case_context_text(
        case,
        trigger=str(case.get("trigger") or ""),
        context_view=context_view,
    )
    active_score, active_example = _best_score(
        scorer=scorer,
        context_text=context_text,
        examples=[str(value) for value in _as_sequence(case.get("active_examples"))],
    )
    strongest_shadow_score = 0.0
    strongest_shadow_id = ""
    strongest_shadow_target = ""
    strongest_shadow_example = ""
    for shadow in _mapping_rows(case.get("shadow_examples")):
        score = scorer.similarity(context_text, str(shadow.get("text") or ""))
        shadow_id = str(shadow.get("sense_id") or "").strip()
        if score > strongest_shadow_score or (
            score == strongest_shadow_score and shadow_id and shadow_id < strongest_shadow_id
        ):
            strongest_shadow_score = score
            strongest_shadow_id = shadow_id
            strongest_shadow_target = str(shadow.get("target_lemma") or "").strip()
            strongest_shadow_example = str(shadow.get("text") or "").strip()
    phrase_control_score, phrase_example = _best_score(
        scorer=scorer,
        context_text=context_text,
        examples=[str(value) for value in _as_sequence(case.get("phrase_examples"))],
    )
    family_pos_tags = _resolve_sentence_veto_phrase_guard_pos_tags(
        active_sense=_as_mapping(case.get("active_sense")),
        shadow_senses=_mapping_rows(case.get("shadow_senses")),
        phrase_guard_pos_scope="family_all",
    )
    phrase_signals = extract_runtime_phrase_control_signals(
        str(case.get("sentence") or "").strip(),
        source_phrase=str(case.get("source_phrase") or case.get("trigger") or "").strip(),
        family_pos_tags=family_pos_tags,
    )
    veto_case = {
        "active_score": active_score,
        "strongest_shadow_score": strongest_shadow_score,
        "phrase_control_score": phrase_control_score,
        "phrase_preemption_hit": bool(phrase_signals.phrase_preemption_hit),
    }
    veto_hit, veto_reason = _veto_hit(
        case=veto_case,
        phrase_mode=phrase_mode,
        shadow_lead_min=shadow_lead_min,
        shadow_score_min=shadow_score_min,
    )
    predicted_decision = "abstain" if veto_hit else "replace"
    if veto_reason in {"phrase_preemption", "phrase_score_lead"}:
        predicted_winner = "phrase_control"
        predicted_winner_type = "none"
    elif veto_hit:
        predicted_winner = strongest_shadow_id
        predicted_winner_type = "shadow"
    else:
        predicted_winner = sense_id(_as_mapping(case.get("active_sense")))
        predicted_winner_type = "active"
    product_outcome = _product_outcome(
        gold=str(case.get("gold_decision") or ""),
        predicted=predicted_decision,
    )
    return {
        "case_id": str(case.get("case_id") or "").strip(),
        "family_id": str(case.get("family_id") or "").strip(),
        "pilot_family_id": str(case.get("pilot_family_id") or "").strip(),
        "trigger": str(case.get("trigger") or "").strip(),
        "candidate_replacement": str(case.get("candidate_replacement") or "").strip(),
        "sentence": str(case.get("sentence") or "").strip(),
        "split": str(case.get("split") or "").strip(),
        "gold_type": str(case.get("gold_type") or "").strip(),
        "gold_decision": str(case.get("gold_decision") or "").strip(),
        "gold_winner": str(case.get("gold_winner") or "").strip(),
        "gold_winner_type": str(case.get("gold_winner_type") or "").strip(),
        "predicted_decision": predicted_decision,
        "predicted_winner": predicted_winner,
        "predicted_winner_type": predicted_winner_type,
        "product_outcome": product_outcome,
        "veto_reason": veto_reason,
        "active_score": _round4(active_score),
        "strongest_shadow_score": _round4(strongest_shadow_score),
        "phrase_control_score": _round4(phrase_control_score),
        "shadow_lead": _round4(strongest_shadow_score - active_score),
        "phrase_lead_to_best": _round4(
            phrase_control_score - max(active_score, strongest_shadow_score)
        ),
        "margin": _round4(active_score - strongest_shadow_score),
        "strongest_shadow_id": strongest_shadow_id,
        "strongest_shadow_target": strongest_shadow_target,
        "context_text": context_text,
        "active_evidence_text": active_example,
        "strongest_shadow_evidence_text": strongest_shadow_example,
        "phrase_control_evidence_text": phrase_example,
        "phrase_preemption_hit": bool(phrase_signals.phrase_preemption_hit),
        "matched_phrase_pattern": str(phrase_signals.matched_phrase_pattern or ""),
        "phrase_reason_code": str(phrase_signals.phrase_reason_code or ""),
        "difficulty_tags": list(_as_sequence(case.get("difficulty_tags"))),
    }


def _source_batch_from_contract(
    source_contract_payload: Mapping[str, object],
    source_contract_path: Path | None,
) -> dict[str, object]:
    batch_path_text = str(source_contract_payload.get("batch_path") or "").strip()
    if not batch_path_text:
        raise ValueError("Source contract must include batch_path.")
    batch_path = Path(batch_path_text)
    if not batch_path.is_absolute():
        batch_path = PROJECT_ROOT / batch_path
    return _load_json(batch_path)


def _base_config(matrix_payload: Mapping[str, object], config_id: str) -> dict[str, object]:
    wanted = str(config_id or "").strip()
    for row in _mapping_rows(matrix_payload.get("config_rows")):
        if str(row.get("config_id") or "").strip() == wanted:
            return dict(row)
    return {"config_id": wanted, "scorer_id": DEFAULT_SCORER_ID, "context_view": "masked_sentence"}


def _dataset_family_index(
    dataset_payload: Mapping[str, object],
) -> dict[tuple[str, str], Mapping[str, object]]:
    rows: dict[tuple[str, str], Mapping[str, object]] = {}
    for family in _mapping_rows(dataset_payload.get("families")):
        active = _as_mapping(family.get("active"))
        key = (
            str(family.get("trigger") or "").strip(),
            str(active.get("target_lemma") or "").strip(),
        )
        if key[0] and key[1]:
            rows[key] = family
    return rows


def _collect_fit_texts(
    *,
    cases: Sequence[Mapping[str, object]],
    coverage_rows: Sequence[Mapping[str, object]],
    context_view: str,
) -> list[str]:
    texts: list[str] = []
    for case in cases:
        text = case_context_text(
            case, trigger=str(case.get("trigger") or ""), context_view=context_view
        )
        if text:
            texts.append(text)
    for row in coverage_rows:
        texts.extend(str(value) for value in _as_sequence(row.get("active_examples")))
        texts.extend(str(value) for value in _as_sequence(row.get("phrase_examples")))
        texts.extend(
            str(value.get("text") or "") for value in _mapping_rows(row.get("shadow_examples"))
        )
    return _unique_texts(texts)


def _best_score(
    *,
    scorer: RuntimeSimilarityBackend,
    context_text: str,
    examples: Sequence[str],
) -> tuple[float, str]:
    best_score = 0.0
    best_example = ""
    for example in examples:
        text = str(example or "").strip()
        if not text:
            continue
        score = scorer.similarity(context_text, text)
        if score > best_score:
            best_score = score
            best_example = text
    return best_score, best_example


def _score_product_cases(
    cases: Sequence[Mapping[str, object]],
    *,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    return score_product_outcome_counts(
        outcome_counts=Counter(str(row.get("product_outcome") or "") for row in cases),
        weights=weights,
        acceptance=acceptance,
    )


def _breakdowns(
    cases: Sequence[Mapping[str, object]],
    key: str,
    *,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in cases:
        grouped[str(row.get(key) or "").strip()].append(row)
    output = []
    for scope_id, rows in sorted(grouped.items()):
        metrics = _score_product_cases(rows, weights=weights, acceptance=acceptance)
        metrics["scope_id"] = scope_id
        output.append(metrics)
    return output


def _leakage_checks(
    *,
    admitted_rows: Sequence[Mapping[str, object]],
    source_rows: Sequence[Mapping[str, object]],
    scored_cases: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    admitted_ids = {str(row.get("row_id") or "").strip() for row in admitted_rows}
    source_ids = {str(row.get("row_id") or "").strip() for row in source_rows}
    source_texts = {_norm(str(row.get("evidence_text") or "")) for row in source_rows}
    context_overlaps = [
        str(row.get("case_id") or "")
        for row in scored_cases
        if _norm(str(row.get("context_text") or "")) in source_texts
    ]
    row_id_overlap = sorted(admitted_ids & source_ids)
    return {
        "evaluation_rows_used_as_evidence": False,
        "row_id_overlap_count": len(row_id_overlap),
        "row_id_overlaps": row_id_overlap[:12],
        "context_text_exact_overlap_count": len(context_overlaps),
        "context_text_exact_overlap_case_ids": context_overlaps[:12],
        "gold_reason_used_for_scoring": False,
        "negative_sense_label_used_for_scoring": False,
        "no_winner_reason_used_for_scoring": False,
        "blocking_issue_count": len(row_id_overlap) + len(context_overlaps),
    }


def _source_summary(
    source_contract_payload: Mapping[str, object],
    source_batch_payload: Mapping[str, object],
) -> dict[str, object]:
    summary = _as_mapping(source_contract_payload.get("summary"))
    contract_complete = bool(summary.get("contract_complete"))
    return {
        "contract_status": str(source_contract_payload.get("status") or ""),
        "contract_complete": contract_complete,
        "semantic_contract_complete": bool(
            summary.get("semantic_contract_complete", contract_complete)
        ),
        "phrase_containment_contract_complete": bool(
            summary.get("phrase_containment_contract_complete", contract_complete)
        ),
        "contract_family_count": int(summary.get("families_total") or 0),
        "contract_complete_family_count": int(summary.get("contract_complete_family_count") or 0),
        "batch_id": str(source_batch_payload.get("batch_id") or ""),
        "source_id": str(source_batch_payload.get("source_id") or ""),
        "source_family": str(source_batch_payload.get("source_family") or ""),
        "model_id": str(source_batch_payload.get("model_id") or ""),
        "row_count": len(_mapping_rows(source_batch_payload.get("rows"))),
    }


def _failure_rows(cases: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "case_id": str(row.get("case_id") or ""),
            "split": str(row.get("split") or ""),
            "gold_type": str(row.get("gold_type") or ""),
            "trigger": str(row.get("trigger") or ""),
            "product_outcome": str(row.get("product_outcome") or ""),
            "veto_reason": str(row.get("veto_reason") or ""),
            "active_score": row.get("active_score"),
            "strongest_shadow_score": row.get("strongest_shadow_score"),
            "phrase_control_score": row.get("phrase_control_score"),
            "sentence": str(row.get("sentence") or ""),
        }
        for row in cases
        if str(row.get("product_outcome") or "") in {"positive_abstain", "negative_allow"}
    ]


def _decision(
    *,
    status: str,
    metrics: Mapping[str, object],
    unscored_rows: Sequence[Mapping[str, object]],
) -> str:
    if unscored_rows:
        return "pilot_scoring_blocked_by_source_coverage"
    target_status = str(_as_mapping(metrics.get("target_checks")).get("target_status") or "")
    if status != "ok":
        return "pilot_scoring_needs_review"
    if target_status == "pass":
        return "frozen_candidate_product_target_passed_on_llm_pilot"
    return "frozen_candidate_product_target_missed_on_llm_pilot"


def _product_outcome(*, gold: str, predicted: str) -> str:
    product_class = "positive" if str(gold or "").strip() == "replace" else "negative"
    user_outcome = "allow" if str(predicted or "").strip() == "replace" else "abstain"
    return f"{product_class}_{user_outcome}"


def _unscored(row: Mapping[str, object], reason: str) -> dict[str, object]:
    return {
        "row_id": str(row.get("row_id") or "").strip(),
        "family_id": str(row.get("family_id") or "").strip(),
        "trigger": str(row.get("trigger") or "").strip(),
        "candidate_replacement": str(row.get("candidate_replacement") or "").strip(),
        "reason": reason,
    }


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _unique_texts(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            output.append(text)
    return output


def _norm(value: str) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _round4(value: object) -> float:
    return round(_safe_float(value), 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
