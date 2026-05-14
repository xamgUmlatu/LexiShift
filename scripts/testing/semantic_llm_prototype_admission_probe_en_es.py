#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from types import SimpleNamespace
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
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    RuntimeSimilarityBackend,
    SENTENCE_VETO_CONTEXT_VIEWS,
    decide_runtime_veto_outcome,
    extract_runtime_phrase_control_signals,
)
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_MIN_ACTIVE_SCORE,
    DEFAULT_MIN_MARGIN,
    DEFAULT_QUEUE_JSON,
    DEFAULT_SCORER_ID,
    _load_json,
)
from semantic_example_frame_evidence_support import (  # noqa: E402
    active_examples_for_family,
    build_example_frame_lookup,
    case_context_text,
    phrase_examples_for_family,
    sense_id,
    shadow_example_pairs_for_family,
    shadow_examples_for_sense,
)
from semantic_llm_prototype_admission_rendering import (  # noqa: E402
    render_prototype_admission_markdown,
)
from semantic_llm_prototype_admission_summary import (  # noqa: E402
    build_prototype_case_matrix,
    build_prototype_recommendation,
    build_prototype_summary_findings,
)
from semantic_llm_prototype_admission_config import (  # noqa: E402
    ACTIVE_MODIFIER_RESCUE_MARGIN_FLOOR,
    DEFAULT_PHRASE_PROTOTYPE_MARGIN,
    PROTOTYPE_CONFIGS,
    phrase_preemption_should_apply,
)
from semantic_llm_prototype_admission_probe_support import (  # noqa: E402
    _config_label,
    _prototype_source_label,
    _round_float,
    _source_shape,
    _unique_texts,
    _utc_now,
    _write_json,
)
from semantic_reverse_aux_text_pilot_en_es import build_queue_subset_dataset  # noqa: E402
from semantic_routing_sentence_veto_helpers import (  # noqa: E402
    _accumulate_sentence_veto_summary,
    _finalize_sentence_veto_summary,
    _new_sentence_veto_summary,
    _normalize_slice_dimensions,
    _normalize_string_list,
)
from semantic_routing_sentence_veto_support import (  # noqa: E402
    _resolve_sentence_veto_phrase_guard_pos_tags,
    load_sentence_veto_dataset,
)
from semantic_phrase_containment_support import (  # noqa: E402
    PhraseContainmentMatch,
    add_phrase_containment_summary,
    match_phrase_containment_examples,
)
from semantic_llm_surface_pos_support import (  # noqa: E402
    active_noun_rescue_shadow_context_is_verb_like,
    surface_pos_signal as build_surface_pos_signal,
)


DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_prototype_admission_probe_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_prototype_admission_probe_latest.md"
DEFAULT_PROTOTYPE_CONTEXT_VIEW = "masked_sentence"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a no-spend prototype admission probe using reviewed sentence examples as "
            "per-sense exemplars. The probe keeps the final user-visible decision binary."
        )
    )
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--evidence-batch-json",
        type=Path,
        default=None,
        help="Optional raw intake or normalized evidence batch to use as prototype evidence.",
    )
    parser.add_argument(
        "--all-dataset-families",
        action="store_true",
        help="Evaluate every family in the sentence-veto dataset instead of the prompt queue slice.",
    )
    parser.add_argument("--scorer-id", default=DEFAULT_SCORER_ID)
    parser.add_argument(
        "--context-view",
        default=DEFAULT_PROTOTYPE_CONTEXT_VIEW,
        choices=SENTENCE_VETO_CONTEXT_VIEWS,
    )
    parser.add_argument("--min-active-score", type=float, default=DEFAULT_MIN_ACTIVE_SCORE)
    parser.add_argument("--min-margin", type=float, default=DEFAULT_MIN_MARGIN)
    parser.add_argument(
        "--phrase-prototype-margin",
        type=float,
        default=DEFAULT_PHRASE_PROTOTYPE_MARGIN,
        help=(
            "Extra dominance margin required before semantic phrase-control prototypes "
            "can veto an active/shadow replacement."
        ),
    )
    parser.add_argument(
        "--window-tokens",
        type=int,
        default=DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    )
    parser.add_argument("--mask-token", default=DEFAULT_SENTENCE_VETO_MASK_TOKEN)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_prototype_admission_report(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    evidence_batch_payload: Mapping[str, object] | None = None,
    all_dataset_families: bool = False,
    scorer_id: str = DEFAULT_SCORER_ID,
    context_view: str = DEFAULT_PROTOTYPE_CONTEXT_VIEW,
    min_active_score: float = DEFAULT_MIN_ACTIVE_SCORE,
    min_margin: float = DEFAULT_MIN_MARGIN,
    phrase_prototype_margin: float = DEFAULT_PHRASE_PROTOTYPE_MARGIN,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    if all_dataset_families:
        subset_dataset = _all_family_dataset(dataset_payload)
        effective_queue = _all_family_queue_payload(dataset_payload, generated_at=generated_at)
        scope = "all_dataset_families"
    else:
        subset_dataset, _family_roles = build_queue_subset_dataset(dataset_payload, queue_payload)
        effective_queue = queue_payload
        scope = "prompt_queue"

    evidence_lookup = (
        build_example_frame_lookup(evidence_batch_payload)
        if isinstance(evidence_batch_payload, Mapping)
        else None
    )
    evidence_source_id = (
        str(evidence_batch_payload.get("source_id") or "").strip()
        if isinstance(evidence_batch_payload, Mapping)
        else ""
    )
    prototype_source_label = _prototype_source_label(evidence_source_id)
    resolved_context_view = str(context_view or "").strip() or DEFAULT_PROTOTYPE_CONTEXT_VIEW
    if resolved_context_view not in SENTENCE_VETO_CONTEXT_VIEWS:
        raise ValueError(
            f"Unsupported prototype context view: {resolved_context_view!r}; "
            f"expected one of {SENTENCE_VETO_CONTEXT_VIEWS!r}"
        )
    context_options = {
        "context_view": resolved_context_view,
        "window_tokens": window_tokens,
        "mask_token": mask_token,
    }
    texts = _collect_prototype_texts(
        subset_dataset,
        evidence_lookup=evidence_lookup,
        context_options=context_options,
    )
    backend = RuntimeSimilarityBackend(scorer_id=scorer_id)
    backend.fit(texts)
    coverage_rows = _build_coverage_rows(
        subset_dataset,
        evidence_lookup=evidence_lookup,
        context_options=context_options,
    )
    config_rows = [
        _run_prototype_config(
            dataset_payload=subset_dataset,
            config_id=config_id,
            label=label,
            phrase_guard_pos_scope=phrase_guard_pos_scope,
            scorer=backend,
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_prototype_margin=phrase_prototype_margin,
            context_options=context_options,
            use_phrase_prototypes=use_phrase_prototypes,
            use_phrase_containment_gate=use_phrase_containment_gate,
            use_surface_pos_rescue=use_surface_pos_rescue,
            evidence_lookup=evidence_lookup,
            prototype_source_label=prototype_source_label,
        )
        for (
            config_id,
            label,
            phrase_guard_pos_scope,
            use_phrase_prototypes,
            use_phrase_containment_gate,
            use_surface_pos_rescue,
        ) in PROTOTYPE_CONFIGS
    ]

    report: dict[str, object] = {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ok",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "queue_id": str(effective_queue.get("queue_id") or "").strip(),
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "evaluation_scope": scope,
        "scorer_id": str(scorer_id or "").strip() or DEFAULT_SCORER_ID,
        "context_view": resolved_context_view,
        "min_active_score": float(min_active_score),
        "min_margin": float(min_margin),
        "phrase_prototype_margin": float(phrase_prototype_margin),
        "window_tokens": int(window_tokens),
        "mask_token": str(mask_token or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
        "decision_contract": "binary_replace_or_abstain",
        "source_shape": _source_shape(evidence_source_id),
        "evidence_source": "evidence_batch" if evidence_lookup is not None else "reviewed_dataset",
        "evidence_source_id": evidence_source_id,
        "evidence_batch_id": str(evidence_batch_payload.get("batch_id") or "").strip()
        if isinstance(evidence_batch_payload, Mapping)
        else "",
        "runtime_publishable": False,
        "coverage_rows": coverage_rows,
        "configurations": config_rows,
    }
    report["summary_findings"] = build_prototype_summary_findings(config_rows)
    report["case_matrix"] = build_prototype_case_matrix(config_rows)
    report["recommendation"] = build_prototype_recommendation(report)
    return report


def _all_family_dataset(dataset_payload: Mapping[str, object]) -> dict[str, object]:
    payload = dict(dataset_payload)
    payload["families"] = [
        dict(family)
        for family in dataset_payload.get("families", ())
        if isinstance(family, Mapping)
    ]
    return payload


def _all_family_queue_payload(
    dataset_payload: Mapping[str, object],
    *,
    generated_at: str,
) -> dict[str, object]:
    dataset_id = str(dataset_payload.get("dataset_id") or "").strip() or "sentence_veto_dataset"
    return {
        "schema_version": 1,
        "queue_id": f"{dataset_id}_all_family_prototype_probe",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "generated_at": generated_at,
        "dataset_id": dataset_id,
        "families": [
            {
                "family_id": str(family.get("family_id") or "").strip(),
                "trigger": str(family.get("trigger") or "").strip(),
                "role": "target",
                "likely_bucket": "prototype_admission_probe",
            }
            for family in dataset_payload.get("families", ())
            if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
        ],
    }


def _collect_prototype_texts(
    dataset_payload: Mapping[str, object],
    *,
    evidence_lookup: Mapping[str, Mapping[str, object]] | None,
    context_options: Mapping[str, object],
) -> list[str]:
    texts: list[str] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        for case in family.get("cases", ()):
            if not isinstance(case, Mapping) or "not_quality_evaluation" in case.get(
                "slice_tags", ()
            ):
                continue
            context_text = case_context_text(
                case,
                trigger=str(family.get("trigger") or ""),
                **context_options,
            )
            if context_text:
                texts.append(context_text)
        texts.extend(
            active_examples_for_family(
                family,
                evidence_lookup,
                **context_options,
            )
        )
        texts.extend(
            phrase_examples_for_family(
                family,
                evidence_lookup,
                **context_options,
            )
        )
        for shadow in family.get("shadows", ()):
            if isinstance(shadow, Mapping):
                texts.extend(
                    shadow_examples_for_sense(
                        family,
                        sense_id=sense_id(shadow),
                        lookup=evidence_lookup,
                        **context_options,
                    )
                )
    return _unique_texts(texts)


def _build_coverage_rows(
    dataset_payload: Mapping[str, object],
    *,
    evidence_lookup: Mapping[str, Mapping[str, object]] | None,
    context_options: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
        shadows = [shadow for shadow in family.get("shadows", ()) if isinstance(shadow, Mapping)]
        active_examples = active_examples_for_family(
            family,
            evidence_lookup,
            **context_options,
        )
        shadow_counts = [
            len(
                shadow_examples_for_sense(
                    family,
                    sense_id=sense_id(shadow),
                    lookup=evidence_lookup,
                    **context_options,
                )
            )
            for shadow in shadows
        ]
        phrase_count = len(
            phrase_examples_for_family(
                family,
                evidence_lookup,
                **context_options,
            )
        )
        rows.append(
            {
                "family_id": str(family.get("family_id") or "").strip(),
                "trigger": str(family.get("trigger") or "").strip(),
                "case_count": sum(
                    1
                    for case in family.get("cases", ())
                    if isinstance(case, Mapping)
                    and "not_quality_evaluation" not in case.get("slice_tags", ())
                ),
                "active_target": str(active.get("target_lemma") or "").strip(),
                "active_example_count": len(active_examples),
                "shadow_example_counts": shadow_counts,
                "phrase_control_example_count": phrase_count,
            }
        )
    return rows


def _run_prototype_config(
    *,
    dataset_payload: Mapping[str, object],
    config_id: str,
    label: str,
    phrase_guard_pos_scope: str,
    scorer: RuntimeSimilarityBackend,
    min_active_score: float,
    min_margin: float,
    phrase_prototype_margin: float,
    context_options: Mapping[str, object],
    use_phrase_prototypes: bool,
    use_phrase_containment_gate: bool,
    use_surface_pos_rescue: bool,
    evidence_lookup: Mapping[str, Mapping[str, object]] | None,
    prototype_source_label: str,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    summary = _new_sentence_veto_summary()
    harmful_ids: list[str] = []
    false_ids: list[str] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
        shadows = [shadow for shadow in family.get("shadows", ()) if isinstance(shadow, Mapping)]
        family_pos_tags = _resolve_sentence_veto_phrase_guard_pos_tags(
            active_sense=active,
            shadow_senses=shadows,
            phrase_guard_pos_scope=phrase_guard_pos_scope,
        )
        active_examples = active_examples_for_family(
            family,
            evidence_lookup,
            **context_options,
        )
        shadow_examples = shadow_example_pairs_for_family(
            family,
            shadows,
            evidence_lookup,
            **context_options,
        )
        phrase_examples = (
            phrase_examples_for_family(
                family,
                evidence_lookup,
                **context_options,
            )
            if use_phrase_prototypes or use_phrase_containment_gate
            else []
        )
        for case in family.get("cases", ()):
            if not isinstance(case, Mapping) or "not_quality_evaluation" in case.get(
                "slice_tags", ()
            ):
                continue
            row = _score_case(
                family=family,
                case=case,
                active_sense=active,
                active_examples=active_examples,
                shadow_examples=shadow_examples,
                phrase_examples=phrase_examples,
                family_pos_tags=family_pos_tags,
                scorer=scorer,
                min_active_score=min_active_score,
                min_margin=min_margin,
                phrase_prototype_margin=phrase_prototype_margin,
                context_options=context_options,
                use_phrase_prototypes=use_phrase_prototypes,
                use_phrase_containment_gate=use_phrase_containment_gate,
                use_surface_pos_rescue=use_surface_pos_rescue,
            )
            rows.append(row)
            summary_result = SimpleNamespace(**row)
            _accumulate_sentence_veto_summary(summary, result=summary_result)
            if row["predicted_decision"] == "replace" and row["gold_decision"] != "replace":
                harmful_ids.append(str(row["case_id"]))
            if row["predicted_decision"] != "replace" and row["gold_decision"] == "replace":
                false_ids.append(str(row["case_id"]))
    _finalize_sentence_veto_summary(summary)
    add_phrase_containment_summary(summary, rows)
    return {
        "config_id": config_id,
        "label": _config_label(label, prototype_source_label),
        "category": "prototype_admission_probe",
        "phrase_guard_pos_scope": phrase_guard_pos_scope,
        "use_phrase_prototypes": bool(use_phrase_prototypes),
        "use_phrase_containment_gate": bool(use_phrase_containment_gate),
        "use_surface_pos_rescue": bool(use_surface_pos_rescue),
        "phrase_prototype_margin": float(phrase_prototype_margin),
        "phrase_control_evidence_mode": _phrase_control_evidence_mode(
            use_phrase_prototypes=use_phrase_prototypes,
            use_phrase_containment_gate=use_phrase_containment_gate,
            use_surface_pos_rescue=use_surface_pos_rescue,
        ),
        "summary": summary,
        "harmful_replace_case_ids": harmful_ids,
        "false_abstain_case_ids": false_ids,
        "row_results": rows,
    }


def _score_case(
    *,
    family: Mapping[str, object],
    case: Mapping[str, object],
    active_sense: Mapping[str, object],
    active_examples: Sequence[str],
    shadow_examples: Sequence[tuple[Mapping[str, object], str]],
    phrase_examples: Sequence[str],
    family_pos_tags: Sequence[str],
    scorer: RuntimeSimilarityBackend,
    min_active_score: float,
    min_margin: float,
    phrase_prototype_margin: float,
    context_options: Mapping[str, object],
    use_phrase_prototypes: bool,
    use_phrase_containment_gate: bool,
    use_surface_pos_rescue: bool,
) -> dict[str, object]:
    trigger = str(family.get("trigger") or "").strip()
    context_text = case_context_text(
        case,
        trigger=trigger,
        **context_options,
    )
    active_score, active_example = _best_example_score(
        scorer=scorer,
        context_text=context_text,
        examples=active_examples,
    )
    shadow_sense: Mapping[str, object] = {}
    strongest_shadow_score = 0.0
    strongest_shadow_example = ""
    for candidate_shadow, candidate_example in shadow_examples:
        shadow_score = scorer.similarity(context_text, candidate_example)
        shadow_id = sense_id(candidate_shadow)
        current_shadow_id = sense_id(shadow_sense)
        if shadow_score > strongest_shadow_score or (
            shadow_score == strongest_shadow_score
            and shadow_id
            and current_shadow_id
            and shadow_id < current_shadow_id
        ):
            shadow_sense = candidate_shadow
            strongest_shadow_score = shadow_score
            strongest_shadow_example = candidate_example
    phrase_containment_match = (
        match_phrase_containment_examples(
            sentence=str(case.get("sentence") or "").strip(),
            source_phrase=str(case.get("source_phrase") or trigger).strip(),
            trigger=trigger,
            phrase_examples=phrase_examples,
        )
        if use_phrase_containment_gate
        else PhraseContainmentMatch(hit=False)
    )
    phrase_control_score = 0.0
    phrase_control_example = ""
    if use_phrase_prototypes:
        phrase_control_score, phrase_control_example = _best_example_score(
            scorer=scorer,
            context_text=context_text,
            examples=phrase_examples,
        )
    elif phrase_containment_match.hit:
        phrase_control_score = 1.0
        phrase_control_example = phrase_containment_match.example_text

    active_sense_id = sense_id(active_sense)
    strongest_shadow_id = sense_id(shadow_sense)
    predicted_winner = active_sense_id
    predicted_winner_type = "active"
    if strongest_shadow_id and strongest_shadow_score > active_score:
        predicted_winner = strongest_shadow_id
        predicted_winner_type = "shadow"
    margin = float(active_score) - float(strongest_shadow_score)
    predicted_decision = decide_runtime_veto_outcome(
        active_score=active_score,
        strongest_shadow_score=strongest_shadow_score,
        min_active_score=min_active_score,
        min_margin=min_margin,
    )
    if not active_examples:
        predicted_decision = "abstain"
    if (
        use_phrase_prototypes
        and phrase_examples
        and phrase_control_score
        >= max(active_score, strongest_shadow_score) + float(phrase_prototype_margin)
    ):
        predicted_decision = "abstain"
        predicted_winner = "phrase_control"
        predicted_winner_type = "none"
    phrase_signals = extract_runtime_phrase_control_signals(
        str(case.get("sentence") or "").strip(),
        source_phrase=str(case.get("source_phrase") or trigger).strip(),
        family_pos_tags=family_pos_tags,
    )
    if phrase_containment_match.hit:
        predicted_decision = "abstain"
        predicted_winner = "phrase_control"
        predicted_winner_type = "none"
    phrase_preemption_applied = phrase_preemption_should_apply(
        phrase_preemption_hit=phrase_signals.phrase_preemption_hit,
        decision_before_phrase_preemption=predicted_decision,
        active_score=active_score,
        strongest_shadow_score=strongest_shadow_score,
        phrase_control_score=phrase_control_score,
        phrase_prototype_margin=phrase_prototype_margin,
    )
    phrase_preemption_blocked_reason = (
        "strong_active_margin_dominates_phrase_control"
        if phrase_signals.phrase_preemption_hit and not phrase_preemption_applied
        else ""
    )
    if phrase_preemption_applied:
        predicted_decision = "abstain"
    surface_pos_signal = (
        build_surface_pos_signal(
            active_sense=active_sense,
            shadow_examples=shadow_examples,
            preceding_token=phrase_signals.preceding_token,
            following_token=phrase_signals.following_token,
        )
        if use_surface_pos_rescue
        and not phrase_containment_match.hit
        and not phrase_signals.phrase_preemption_hit
        else ""
    )
    active_rescue_applied = False
    surface_pos_preemption_applied = False
    surface_pos_rescue_blocked_reason = ""
    surface_pos_noun_shadow_verb_like = False
    if surface_pos_signal == "active_noun_frame" and active_examples:
        surface_pos_noun_shadow_verb_like = active_noun_rescue_shadow_context_is_verb_like(
            strongest_shadow_sense=shadow_sense,
            shadow_examples=shadow_examples,
        )
    if surface_pos_signal in {"active_noun_frame", "active_modifier_frame"} and (
        predicted_decision != "replace"
    ):
        if not active_examples:
            surface_pos_rescue_blocked_reason = "missing_active_examples"
        elif surface_pos_signal == "active_noun_frame" and not surface_pos_noun_shadow_verb_like:
            surface_pos_rescue_blocked_reason = "strongest_shadow_not_verb_like"
        elif (
            surface_pos_signal == "active_modifier_frame"
            and float(margin) < ACTIVE_MODIFIER_RESCUE_MARGIN_FLOOR
        ):
            surface_pos_rescue_blocked_reason = "active_modifier_margin_below_floor"
        else:
            predicted_decision = "replace"
            predicted_winner = active_sense_id
            predicted_winner_type = "active"
            active_rescue_applied = True
    elif surface_pos_signal == "non_active_nominal_frame" and predicted_decision == "replace":
        predicted_decision = "abstain"
        predicted_winner = "surface_pos_non_active_nominal_frame"
        predicted_winner_type = "none"
        surface_pos_preemption_applied = True
    elif surface_pos_signal == "shadow_verb_frame" and predicted_decision == "replace":
        predicted_decision = "abstain"
        if strongest_shadow_id:
            predicted_winner = strongest_shadow_id
            predicted_winner_type = "shadow"
        surface_pos_preemption_applied = True

    gold_winner = str(case.get("gold_winner") or "").strip()
    gold_decision = str(case.get("gold_decision") or "").strip().lower()
    gold_winner_type = _classify_gold_winner_type(gold_winner, active_sense_id=active_sense_id)
    if gold_decision not in {"replace", "abstain"}:
        gold_decision = "replace" if gold_winner_type == "active" else "abstain"
    return {
        "case_id": str(case.get("case_id") or "").strip(),
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": trigger,
        "sentence": str(case.get("sentence") or "").strip(),
        "source_phrase": str(case.get("source_phrase") or trigger).strip(),
        "gold_decision": gold_decision,
        "gold_winner": gold_winner,
        "gold_winner_type": gold_winner_type,
        "predicted_decision": predicted_decision,
        "predicted_winner": predicted_winner,
        "predicted_winner_type": predicted_winner_type,
        "active_score": _round_float(active_score),
        "strongest_shadow_score": _round_float(strongest_shadow_score),
        "phrase_control_score": _round_float(phrase_control_score),
        "phrase_prototype_margin": _round_float(phrase_prototype_margin),
        "phrase_prototype_margin_to_best": _round_float(
            phrase_control_score - max(active_score, strongest_shadow_score)
        ),
        "margin": _round_float(margin),
        "strongest_shadow_id": strongest_shadow_id,
        "context_text": context_text,
        "active_evidence_text": active_example,
        "strongest_shadow_evidence_text": strongest_shadow_example,
        "phrase_control_evidence_text": phrase_control_example,
        "phrase_containment_hit": bool(phrase_containment_match.hit),
        "phrase_containment_pattern": phrase_containment_match.pattern_text,
        "phrase_containment_reason_code": phrase_containment_match.reason_code,
        "phrase_preemption_hit": bool(phrase_signals.phrase_preemption_hit),
        "phrase_preemption_applied": phrase_preemption_applied,
        "phrase_preemption_blocked_reason": phrase_preemption_blocked_reason,
        "matched_phrase_pattern": phrase_signals.matched_phrase_pattern,
        "phrase_reason_code": phrase_signals.phrase_reason_code,
        "active_rescue_applied": active_rescue_applied,
        "active_rescue_reason_code": (
            f"surface_pos_{surface_pos_signal}_rescue" if active_rescue_applied else ""
        ),
        "surface_pos_rescue_blocked_reason": surface_pos_rescue_blocked_reason,
        "surface_pos_noun_shadow_verb_like": surface_pos_noun_shadow_verb_like,
        "surface_pos_signal": surface_pos_signal,
        "surface_pos_preemption_applied": surface_pos_preemption_applied,
        "slice_tags": _normalize_string_list(case.get("slice_tags")),
        "slice_dimensions": _normalize_slice_dimensions(case.get("slice_dimensions")),
        "notes": str(case.get("notes") or "").strip(),
    }


def _best_example_score(
    *,
    scorer: RuntimeSimilarityBackend,
    context_text: str,
    examples: Sequence[str],
) -> tuple[float, str]:
    best_score = 0.0
    best_example = ""
    for example in examples:
        score = scorer.similarity(context_text, example)
        if score > best_score:
            best_score = score
            best_example = example
    return best_score, best_example


def _phrase_control_evidence_mode(
    *,
    use_phrase_prototypes: bool,
    use_phrase_containment_gate: bool,
    use_surface_pos_rescue: bool,
) -> str:
    if use_surface_pos_rescue:
        if use_phrase_prototypes:
            return "semantic_prototype_competition_plus_surface_pos"
        return "local_containment_patterns_plus_surface_pos"
    if use_phrase_prototypes:
        return "semantic_prototype_competition"
    if use_phrase_containment_gate:
        return "local_containment_patterns"
    return "runtime_phrase_guard_only"


def _classify_gold_winner_type(gold_winner: str, *, active_sense_id: str) -> str:
    normalized = str(gold_winner or "").strip()
    if not normalized or normalized in {"none", "abstain"}:
        return "none"
    if normalized == active_sense_id:
        return "active"
    return "shadow"


def main() -> int:
    args = _parse_args()
    queue_payload = _load_json(args.queue_json)
    dataset_payload = load_sentence_veto_dataset(args.dataset)
    evidence_batch_payload = (
        _load_json(args.evidence_batch_json) if args.evidence_batch_json else None
    )
    report = build_prototype_admission_report(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        evidence_batch_payload=evidence_batch_payload,
        all_dataset_families=bool(args.all_dataset_families),
        scorer_id=str(args.scorer_id or "").strip() or DEFAULT_SCORER_ID,
        context_view=str(args.context_view or "").strip() or DEFAULT_PROTOTYPE_CONTEXT_VIEW,
        min_active_score=float(args.min_active_score),
        min_margin=float(args.min_margin),
        phrase_prototype_margin=float(args.phrase_prototype_margin),
        window_tokens=max(0, int(args.window_tokens)),
        mask_token=str(args.mask_token or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    )
    _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_prototype_admission_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
