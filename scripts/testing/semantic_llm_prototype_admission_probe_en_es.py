#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
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
    RuntimeSimilarityBackend,
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


DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_prototype_admission_probe_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_prototype_admission_probe_latest.md"
PROTOTYPE_CONFIGS: tuple[tuple[str, str, str, bool, bool], ...] = (
    (
        "prototype_reviewed_examples_family_guard",
        "Prototype reviewed examples, family phrase guard",
        "family_all",
        False,
        False,
    ),
    (
        "prototype_reviewed_examples_active_guard",
        "Prototype reviewed examples, active phrase guard",
        "active_only",
        False,
        False,
    ),
    (
        "prototype_reviewed_examples_phrase_containment_guard",
        "Prototype reviewed examples, phrase-control containment guard",
        "active_only",
        False,
        True,
    ),
    (
        "prototype_reviewed_examples_phrase_prototype_guard",
        "Prototype reviewed examples, phrase-control prototype guard",
        "active_only",
        True,
        False,
    ),
)


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
    parser.add_argument("--min-active-score", type=float, default=DEFAULT_MIN_ACTIVE_SCORE)
    parser.add_argument("--min-margin", type=float, default=DEFAULT_MIN_MARGIN)
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
    min_active_score: float = DEFAULT_MIN_ACTIVE_SCORE,
    min_margin: float = DEFAULT_MIN_MARGIN,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
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
    texts = _collect_prototype_texts(subset_dataset, evidence_lookup=evidence_lookup)
    backend = RuntimeSimilarityBackend(scorer_id=scorer_id)
    backend.fit(texts)
    coverage_rows = _build_coverage_rows(subset_dataset, evidence_lookup=evidence_lookup)
    config_rows = [
        _run_prototype_config(
            dataset_payload=subset_dataset,
            config_id=config_id,
            label=label,
            phrase_guard_pos_scope=phrase_guard_pos_scope,
            scorer=backend,
            min_active_score=min_active_score,
            min_margin=min_margin,
            use_phrase_prototypes=use_phrase_prototypes,
            use_phrase_containment_gate=use_phrase_containment_gate,
            evidence_lookup=evidence_lookup,
            prototype_source_label=prototype_source_label,
        )
        for (
            config_id,
            label,
            phrase_guard_pos_scope,
            use_phrase_prototypes,
            use_phrase_containment_gate,
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
        "min_active_score": float(min_active_score),
        "min_margin": float(min_margin),
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
    report["summary_findings"] = _build_summary_findings(config_rows)
    report["case_matrix"] = _build_case_matrix(config_rows)
    report["recommendation"] = _build_recommendation(report)
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
) -> list[str]:
    texts: list[str] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        for case in family.get("cases", ()):
            if not isinstance(case, Mapping):
                continue
            context_text = case_context_text(case, trigger=str(family.get("trigger") or ""))
            if context_text:
                texts.append(context_text)
        texts.extend(active_examples_for_family(family, evidence_lookup))
        texts.extend(phrase_examples_for_family(family, evidence_lookup))
        for shadow in family.get("shadows", ()):
            if isinstance(shadow, Mapping):
                texts.extend(
                    shadow_examples_for_sense(
                        family,
                        sense_id=sense_id(shadow),
                        lookup=evidence_lookup,
                    )
                )
    return _unique_texts(texts)


def _build_coverage_rows(
    dataset_payload: Mapping[str, object],
    *,
    evidence_lookup: Mapping[str, Mapping[str, object]] | None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
        shadows = [shadow for shadow in family.get("shadows", ()) if isinstance(shadow, Mapping)]
        active_examples = active_examples_for_family(family, evidence_lookup)
        shadow_counts = [
            len(
                shadow_examples_for_sense(
                    family,
                    sense_id=sense_id(shadow),
                    lookup=evidence_lookup,
                )
            )
            for shadow in shadows
        ]
        phrase_count = len(phrase_examples_for_family(family, evidence_lookup))
        rows.append(
            {
                "family_id": str(family.get("family_id") or "").strip(),
                "trigger": str(family.get("trigger") or "").strip(),
                "case_count": len(
                    [case for case in family.get("cases", ()) if isinstance(case, Mapping)]
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
    use_phrase_prototypes: bool,
    use_phrase_containment_gate: bool,
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
        active_examples = active_examples_for_family(family, evidence_lookup)
        shadow_examples = shadow_example_pairs_for_family(family, shadows, evidence_lookup)
        phrase_examples = (
            phrase_examples_for_family(family, evidence_lookup)
            if use_phrase_prototypes or use_phrase_containment_gate
            else []
        )
        for case in family.get("cases", ()):
            if not isinstance(case, Mapping):
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
                use_phrase_prototypes=use_phrase_prototypes,
                use_phrase_containment_gate=use_phrase_containment_gate,
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
        "phrase_control_evidence_mode": _phrase_control_evidence_mode(
            use_phrase_prototypes=use_phrase_prototypes,
            use_phrase_containment_gate=use_phrase_containment_gate,
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
    use_phrase_prototypes: bool,
    use_phrase_containment_gate: bool,
) -> dict[str, object]:
    trigger = str(family.get("trigger") or "").strip()
    context_text = case_context_text(case, trigger=trigger)
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
        and phrase_control_score >= max(active_score, strongest_shadow_score)
    ):
        predicted_decision = "abstain"
        predicted_winner = "phrase_control"
        predicted_winner_type = "none"
    if phrase_containment_match.hit:
        predicted_decision = "abstain"
        predicted_winner = "phrase_control"
        predicted_winner_type = "none"
    phrase_signals = extract_runtime_phrase_control_signals(
        str(case.get("sentence") or "").strip(),
        source_phrase=str(case.get("source_phrase") or trigger).strip(),
        family_pos_tags=family_pos_tags,
    )
    if phrase_signals.phrase_preemption_hit:
        predicted_decision = "abstain"

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
        "matched_phrase_pattern": phrase_signals.matched_phrase_pattern,
        "phrase_reason_code": phrase_signals.phrase_reason_code,
        "active_rescue_applied": False,
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
) -> str:
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


def _build_summary_findings(config_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    lookup = {
        str(row.get("config_id") or "").strip(): row
        for row in config_rows
        if str(row.get("config_id") or "").strip()
    }
    family_guard = _summary_metrics(lookup.get("prototype_reviewed_examples_family_guard"))
    active_guard = _summary_metrics(lookup.get("prototype_reviewed_examples_active_guard"))
    phrase_containment_guard = _summary_metrics(
        lookup.get("prototype_reviewed_examples_phrase_containment_guard")
    )
    phrase_prototype_guard = _summary_metrics(
        lookup.get("prototype_reviewed_examples_phrase_prototype_guard")
    )
    return {
        "family_guard_result": family_guard,
        "active_guard_result": active_guard,
        "phrase_containment_guard_result": phrase_containment_guard,
        "phrase_prototype_guard_result": phrase_prototype_guard,
        "active_guard_reduces_phrase_leak_without_false_abstain": int(
            active_guard.get("harmful_replace_count") or 0
        )
        < int(family_guard.get("harmful_replace_count") or 0)
        and int(active_guard.get("false_abstain_count") or 0)
        <= int(family_guard.get("false_abstain_count") or 0),
        "phrase_prototype_guard_clears_active_guard_residue": int(
            phrase_prototype_guard.get("harmful_replace_count") or 0
        )
        < int(active_guard.get("harmful_replace_count") or 0)
        and int(phrase_prototype_guard.get("false_abstain_count") or 0)
        <= int(active_guard.get("false_abstain_count") or 0),
        "phrase_containment_avoids_phrase_prototype_overreach": int(
            phrase_containment_guard.get("harmful_replace_count") or 0
        )
        <= int(phrase_prototype_guard.get("harmful_replace_count") or 0)
        and int(phrase_containment_guard.get("false_abstain_count") or 0)
        <= int(phrase_prototype_guard.get("false_abstain_count") or 0),
    }


def _build_case_matrix(config_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    config_lookups = {
        str(config.get("config_id") or "").strip(): {
            str(row.get("case_id") or "").strip(): row
            for row in config.get("row_results", ())
            if isinstance(row, Mapping) and str(row.get("case_id") or "").strip()
        }
        for config in config_rows
        if str(config.get("config_id") or "").strip()
    }
    focus_case_ids: set[str] = set()
    for config in config_rows:
        focus_case_ids.update(_case_id_set(config.get("harmful_replace_case_ids")))
        focus_case_ids.update(_case_id_set(config.get("false_abstain_case_ids")))
    rows: list[dict[str, object]] = []
    for case_id in sorted(focus_case_ids):
        configs = {}
        gold_decision = ""
        family_id = ""
        for config_id, lookup in config_lookups.items():
            row = lookup.get(case_id)
            if row is None:
                continue
            gold_decision = gold_decision or str(row.get("gold_decision") or "").strip()
            family_id = family_id or str(row.get("family_id") or "").strip()
            configs[config_id] = _case_prediction(row)
        rows.append(
            {
                "case_id": case_id,
                "family_id": family_id,
                "gold_decision": gold_decision,
                "configs": configs,
            }
        )
    return rows


def _build_recommendation(report: Mapping[str, object]) -> str:
    findings = report.get("summary_findings")
    best_guard = (
        findings.get("phrase_containment_guard_result")
        if isinstance(findings, Mapping)
        and isinstance(findings.get("phrase_containment_guard_result"), Mapping)
        else {}
    )
    scope = str(report.get("evaluation_scope") or "").strip()
    if (
        int(best_guard.get("harmful_replace_count") or 0) == 0
        and int(best_guard.get("false_abstain_count") or 0) == 0
    ):
        verdict = "clears this evaluation slice"
    else:
        verdict = "still leaves residual cases on this evaluation slice"
    source_note = _source_note(report)
    return (
        "Keep the user-facing UX binary, but move the internal experiment from a single "
        "evidence string toward prototype admission: context competes against active and "
        "shadow example frames, while phrase-control evidence can only abstain through local "
        "containment-pattern matches. "
        f"The phrase-control containment guard {verdict} ({_format_metric_summary(best_guard)}) "
        f"on `{scope}`; keep broad phrase-control prototype scoring as an overreach control only. "
        f"{source_note}"
    )


def _config_label(label: str, prototype_source_label: str) -> str:
    source_label = str(prototype_source_label or "").strip() or "reviewed examples"
    return str(label).replace("reviewed examples", source_label)


def _prototype_source_label(evidence_source_id: str) -> str:
    source_id = str(evidence_source_id or "").strip()
    if not source_id or source_id == "reviewed_sentence_veto_example_frames":
        return "reviewed examples"
    return source_id


def _source_shape(evidence_source_id: str) -> str:
    source_id = str(evidence_source_id or "").strip()
    if source_id:
        return f"{source_id}_as_per_sense_prototypes"
    return "reviewed_sentence_veto_examples_as_per_sense_prototypes"


def _source_note(report: Mapping[str, object]) -> str:
    source_id = str(report.get("evidence_source_id") or "").strip()
    if (
        str(report.get("evidence_source") or "").strip() == "reviewed_dataset"
        or source_id == "reviewed_sentence_veto_example_frames"
    ):
        return (
            "The reviewed examples are internal oracle data, not runtime-publishable evidence; "
            "use this as the acceptance target for external or generated example-frame sources."
        )
    batch_id = str(report.get("evidence_batch_id") or "").strip()
    source_id = source_id or "evidence_batch"
    return (
        f"The `{source_id}` batch `{batch_id}` is source evidence, but it should clear the "
        "required-family contract gate before any promotion or runtime publication claim."
    )


def _summary_metrics(config: object) -> dict[str, object]:
    if not isinstance(config, Mapping):
        return {}
    summary = config.get("summary") if isinstance(config.get("summary"), Mapping) else {}
    return {
        "decision_accuracy": _round_float(summary.get("decision_accuracy")),
        "replace_recall": _round_float(summary.get("replace_recall")),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
    }


def _case_prediction(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "predicted_decision": str(row.get("predicted_decision") or "").strip(),
        "predicted_winner_type": str(row.get("predicted_winner_type") or "").strip(),
        "active_score": _round_float(row.get("active_score")),
        "strongest_shadow_score": _round_float(row.get("strongest_shadow_score")),
        "phrase_control_score": _round_float(row.get("phrase_control_score")),
        "margin": _round_float(row.get("margin")),
        "phrase_preemption_hit": bool(row.get("phrase_preemption_hit")),
        "phrase_containment_hit": bool(row.get("phrase_containment_hit")),
    }


def _format_metric_summary(value: Mapping[str, object]) -> str:
    return (
        f"`{_pct(value.get('decision_accuracy'))}` accuracy / "
        f"`{_pct(value.get('replace_recall'))}` recall / "
        f"`{value.get('harmful_replace_count', 0)}` harmful / "
        f"`{value.get('false_abstain_count', 0)}` false abstains"
    )


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _round_float(value: object) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _case_id_set(value: object) -> set[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return {str(item).strip() for item in value if str(item).strip()}
    text = str(value or "").strip()
    return {text} if text else set()


def _unique_texts(values: Sequence[str]) -> list[str]:
    texts: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in texts:
            texts.append(text)
    return texts


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
        min_active_score=float(args.min_active_score),
        min_margin=float(args.min_margin),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_prototype_admission_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
