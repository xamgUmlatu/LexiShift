#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_llm_example_frame_contract_en_es import (  # noqa: E402
    build_example_frame_contract_report,
)
from semantic_llm_example_frame_generation_plan_candidates import (  # noqa: E402
    DEFAULT_HARD_SEMANTIC_CANDIDATES_PER_ROW,
    DEFAULT_PHRASE_CANDIDATES_PER_ROW,
    DEFAULT_SEMANTIC_CANDIDATES_PER_ROW,
    candidate_count_for_slot,
    candidate_strategy,
    expected_row_id,
    request_id,
    slug,
)
from semantic_llm_example_frame_generation_prompts import (  # noqa: E402
    system_prompt,
    user_prompt,
)
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_QUEUE_JSON,
    _load_json,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_BASE_BATCH_JSON = (
    TEST_OUTPUTS_ROOT
    / "experiments"
    / "semantic_example_frame_batches"
    / "en-es-reverse-aux-example-frames-v10-20260425a_normalized_evidence.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_generation_plan_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_generation_plan_latest.md"
DEFAULT_MODEL_ID = "gpt-5.4-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_CHARS_PER_TOKEN = 4.0
DEFAULT_EXPECTED_OUTPUT_TOKENS = 50
DEFAULT_MAX_OUTPUT_TOKENS = 180
PROMPT_VERSION = "example-frame-missing-rows-v1"
SOURCE_ID = "llm_example_frame_missing_rows"
DEFAULT_GENERATION_TARGETS = ("active_example", "shadow_example")
SUPPORTED_GENERATION_TARGETS = frozenset((*DEFAULT_GENERATION_TARGETS, "phrase_control_example"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a no-spend LLM generation plan for only the example-frame rows still "
            "missing from a required-family source contract read."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--required-family-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--base-evidence-batch-json", type=Path, default=DEFAULT_BASE_BATCH_JSON)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--chars-per-token", type=float, default=DEFAULT_CHARS_PER_TOKEN)
    parser.add_argument(
        "--expected-output-tokens", type=int, default=DEFAULT_EXPECTED_OUTPUT_TOKENS
    )
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument(
        "--generation-targets",
        default=",".join(DEFAULT_GENERATION_TARGETS),
        help=(
            "Comma-separated missing-row targets to plan: active_example, "
            "shadow_example, phrase_control_example. Phrase rows are excluded by default "
            "and must be requested explicitly."
        ),
    )
    parser.add_argument(
        "--semantic-candidates-per-row",
        type=int,
        default=DEFAULT_SEMANTIC_CANDIDATES_PER_ROW,
        help="Candidate attempts to plan for ordinary active/shadow missing rows.",
    )
    parser.add_argument(
        "--hard-semantic-candidates-per-row",
        type=int,
        default=DEFAULT_HARD_SEMANTIC_CANDIDATES_PER_ROW,
        help=(
            "Candidate attempts to plan for same-POS active/shadow families, where "
            "surface ambiguity is harder."
        ),
    )
    parser.add_argument(
        "--phrase-candidates-per-row",
        type=int,
        default=DEFAULT_PHRASE_CANDIDATES_PER_ROW,
        help="Candidate attempts to plan for explicitly requested phrase-containment rows.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_example_frame_generation_plan(
    *,
    dataset_payload: Mapping[str, object],
    required_family_payload: Mapping[str, object],
    base_evidence_batch_payload: Mapping[str, object],
    model_id: str = DEFAULT_MODEL_ID,
    temperature: float = DEFAULT_TEMPERATURE,
    chars_per_token: float = DEFAULT_CHARS_PER_TOKEN,
    expected_output_tokens: int = DEFAULT_EXPECTED_OUTPUT_TOKENS,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    generation_targets: Sequence[str] = DEFAULT_GENERATION_TARGETS,
    semantic_candidates_per_row: int = DEFAULT_SEMANTIC_CANDIDATES_PER_ROW,
    hard_semantic_candidates_per_row: int = DEFAULT_HARD_SEMANTIC_CANDIDATES_PER_ROW,
    phrase_candidates_per_row: int = DEFAULT_PHRASE_CANDIDATES_PER_ROW,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be > 0")
    if semantic_candidates_per_row <= 0:
        raise ValueError("semantic_candidates_per_row must be > 0")
    if hard_semantic_candidates_per_row <= 0:
        raise ValueError("hard_semantic_candidates_per_row must be > 0")
    if phrase_candidates_per_row <= 0:
        raise ValueError("phrase_candidates_per_row must be > 0")
    required_family_keys = _required_family_keys(required_family_payload)
    queue_lookup = _queue_family_lookup(required_family_payload)
    contract_report = build_example_frame_contract_report(
        base_evidence_batch_payload,
        required_family_keys=required_family_keys,
        generated_at=generated_at,
    )
    dataset_lookup = _dataset_family_lookup(dataset_payload)
    target_filter = _normalize_generation_targets(generation_targets)
    request_rows = _build_request_rows(
        contract_report=contract_report,
        dataset_lookup=dataset_lookup,
        queue_lookup=queue_lookup,
        required_family_keys=required_family_keys,
        generation_targets=target_filter,
        model_id=str(model_id or "").strip() or DEFAULT_MODEL_ID,
        temperature=float(temperature),
        semantic_candidates_per_row=int(semantic_candidates_per_row),
        hard_semantic_candidates_per_row=int(hard_semantic_candidates_per_row),
        phrase_candidates_per_row=int(phrase_candidates_per_row),
    )
    _attach_token_estimates(
        request_rows,
        chars_per_token=chars_per_token,
        expected_output_tokens=expected_output_tokens,
        max_output_tokens=max_output_tokens,
    )
    summary = _build_summary(
        request_rows,
        expected_output_tokens=expected_output_tokens,
        max_output_tokens=max_output_tokens,
    )
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ready" if request_rows else "no_missing_rows",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "required_family_source": str(required_family_payload.get("queue_id") or "").strip()
        or str(required_family_payload.get("inventory_id") or "").strip()
        or str(required_family_payload.get("dataset_id") or "").strip(),
        "base_batch_id": str(base_evidence_batch_payload.get("batch_id") or "").strip(),
        "source_id": SOURCE_ID,
        "prompt_version": PROMPT_VERSION,
        "selected_model_id": str(model_id or "").strip() or DEFAULT_MODEL_ID,
        "selected_temperature": float(temperature),
        "decision_contract": "binary_replace_or_abstain",
        "review_leakage_policy": "do_not_include_sentence_veto_case_sentences_in_prompts",
        "generation_targets": target_filter,
        "candidate_defaults": {
            "semantic_candidates_per_row": int(semantic_candidates_per_row),
            "hard_semantic_candidates_per_row": int(hard_semantic_candidates_per_row),
            "phrase_candidates_per_row": int(phrase_candidates_per_row),
            "hard_semantic_condition": "active_and_candidate_sense_share_canonical_pos",
        },
        "input_token_heuristic": f"ceil(characters / {chars_per_token})",
        "contract_summary": contract_report.get("summary", {}),
        "summary": summary,
        "request_rows": request_rows,
        "recommendation": _build_recommendation(summary),
    }


def _build_request_rows(
    *,
    contract_report: Mapping[str, object],
    dataset_lookup: Mapping[str, Mapping[str, object]],
    queue_lookup: Mapping[str, Mapping[str, object]],
    required_family_keys: Sequence[str],
    generation_targets: Sequence[str],
    model_id: str,
    temperature: float,
    semantic_candidates_per_row: int,
    hard_semantic_candidates_per_row: int,
    phrase_candidates_per_row: int,
) -> list[dict[str, object]]:
    contract_rows = {
        str(row.get("family_key") or "").strip(): row
        for row in contract_report.get("family_rows", ())
        if isinstance(row, Mapping) and str(row.get("family_key") or "").strip()
    }
    request_rows: list[dict[str, object]] = []
    for family_key in required_family_keys:
        family = dataset_lookup.get(family_key)
        if not isinstance(family, Mapping):
            raise ValueError(f"Required family {family_key!r} is missing from dataset payload.")
        queue_family = queue_lookup.get(family_key, {})
        contract_row = contract_rows.get(family_key, {})
        missing = {
            str(item).strip()
            for item in contract_row.get("missing_requirements", ())
            if str(item).strip()
        }
        if "active_examples" in missing and "active_example" in generation_targets:
            active = _active_sense(family)
            request_rows.extend(
                _request_rows_for_candidate_slot(
                    family=family,
                    queue_family=queue_family,
                    candidate_sense=active,
                    generation_target="active_example",
                    relation_type="anchor_cue",
                    model_id=model_id,
                    temperature=temperature,
                    semantic_candidates_per_row=semantic_candidates_per_row,
                    hard_semantic_candidates_per_row=hard_semantic_candidates_per_row,
                    phrase_candidates_per_row=phrase_candidates_per_row,
                )
            )
        if "shadow_examples" in missing and "shadow_example" in generation_targets:
            for shadow in _shadow_senses(family):
                request_rows.extend(
                    _request_rows_for_candidate_slot(
                        family=family,
                        queue_family=queue_family,
                        candidate_sense=shadow,
                        generation_target="shadow_example",
                        relation_type="shadow_candidate",
                        model_id=model_id,
                        temperature=temperature,
                        semantic_candidates_per_row=semantic_candidates_per_row,
                        hard_semantic_candidates_per_row=hard_semantic_candidates_per_row,
                        phrase_candidates_per_row=phrase_candidates_per_row,
                    )
                )
        if "phrase_control_examples" in missing and "phrase_control_example" in generation_targets:
            request_rows.extend(
                _request_rows_for_candidate_slot(
                    family=family,
                    queue_family=queue_family,
                    candidate_sense={},
                    generation_target="phrase_control_example",
                    relation_type="phrase_control_example",
                    model_id=model_id,
                    temperature=temperature,
                    semantic_candidates_per_row=semantic_candidates_per_row,
                    hard_semantic_candidates_per_row=hard_semantic_candidates_per_row,
                    phrase_candidates_per_row=phrase_candidates_per_row,
                )
            )
    return request_rows


def _request_rows_for_candidate_slot(
    *,
    family: Mapping[str, object],
    queue_family: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    generation_target: str,
    relation_type: str,
    model_id: str,
    temperature: float,
    semantic_candidates_per_row: int,
    hard_semantic_candidates_per_row: int,
    phrase_candidates_per_row: int,
) -> list[dict[str, object]]:
    active = _active_sense(family)
    shadows = _shadow_senses(family)
    candidate_count = candidate_count_for_slot(
        generation_target=generation_target,
        active_pos=_canonical_pos(active),
        candidate_pos=_canonical_pos(candidate_sense),
        shadow_positions=[_canonical_pos(shadow) for shadow in shadows],
        semantic_candidates_per_row=semantic_candidates_per_row,
        hard_semantic_candidates_per_row=hard_semantic_candidates_per_row,
        phrase_candidates_per_row=phrase_candidates_per_row,
    )
    return [
        _request_row(
            family=family,
            queue_family=queue_family,
            candidate_sense=candidate_sense,
            generation_target=generation_target,
            relation_type=relation_type,
            model_id=model_id,
            temperature=temperature,
            candidate_index=index,
            candidate_count=candidate_count,
        )
        for index in range(1, candidate_count + 1)
    ]


def _request_row(
    *,
    family: Mapping[str, object],
    queue_family: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    generation_target: str,
    relation_type: str,
    model_id: str,
    temperature: float,
    candidate_index: int,
    candidate_count: int,
) -> dict[str, object]:
    family_id = str(family.get("family_id") or "").strip()
    trigger = str(family.get("trigger") or "").strip()
    active = _active_sense(family)
    active_target = str(active.get("target_lemma") or "").strip()
    candidate_id = _sense_id(candidate_sense)
    candidate_target = (
        str(candidate_sense.get("target_lemma") or "").strip() if candidate_id else "phrase_control"
    )
    request_kind = _request_kind(generation_target)
    request_id_value = request_id(
        family_id=family_id,
        request_kind=request_kind,
        candidate_id=candidate_id,
        candidate_index=candidate_index,
        candidate_count=candidate_count,
    )
    roles = _roles_for_generation_target(generation_target)
    queue_metadata = _queue_metadata(queue_family)
    candidate_strategy_value = candidate_strategy(
        generation_target=generation_target,
        active_pos=_canonical_pos(active),
        candidate_pos=_canonical_pos(candidate_sense),
        shadow_positions=[_canonical_pos(shadow) for shadow in _shadow_senses(family)],
    )
    expected_row = {
        "row_id": expected_row_id(
            family_id=family_id,
            request_kind=request_kind,
            candidate_id=candidate_id,
            candidate_index=candidate_index,
            candidate_count=candidate_count,
        ),
        "relation_type": relation_type,
        "roles": roles,
        "trigger": trigger,
        "active_target": active_target,
        "candidate_target": candidate_target,
        "candidate_pos": str(candidate_sense.get("canonical_pos") or "").strip()
        if candidate_id
        else "phrase_control",
        "evidence_text": "<model-written original example frame>",
        "prompt_slot": generation_target,
        "input_ref": request_id_value,
        "review_state": "unreviewed",
        "promotion_state": "proposed",
        "runtime_publishable": False,
        "metadata": {
            "family_id": family_id,
            "active_sense_id": _sense_id(active),
            "candidate_sense_id": candidate_id,
            "generation_target": generation_target,
            "source_gap": generation_target,
            "candidate_index": candidate_index,
            "candidate_count": candidate_count,
            "candidate_strategy": candidate_strategy_value,
            **queue_metadata,
        },
    }
    if generation_target == "phrase_control_example":
        expected_row["metadata"]["gold_decision"] = "abstain"

    return {
        "request_id": request_id_value,
        "prompt_slot": generation_target,
        "family_id": family_id,
        "trigger": trigger,
        "active_target": active_target,
        "candidate_target": candidate_target,
        "candidate_pos": str(expected_row["candidate_pos"]),
        "relation_type": relation_type,
        "roles": roles,
        "queue_metadata": queue_metadata,
        "candidate_index": candidate_index,
        "candidate_count": candidate_count,
        "candidate_strategy": candidate_strategy_value,
        "model_id": model_id,
        "temperature": temperature,
        "system_prompt": system_prompt(generation_target),
        "user_prompt": user_prompt(
            family=family,
            queue_family=queue_family,
            candidate_sense=candidate_sense,
            generation_target=generation_target,
            candidate_index=candidate_index,
            candidate_count=candidate_count,
        ),
        "expected_row_preview": expected_row,
    }


def _attach_token_estimates(
    request_rows: Sequence[dict[str, object]],
    *,
    chars_per_token: float,
    expected_output_tokens: int,
    max_output_tokens: int,
) -> None:
    for row in request_rows:
        request_text = "\n".join(
            [
                str(row.get("system_prompt") or "").strip(),
                str(row.get("user_prompt") or "").strip(),
            ]
        ).strip()
        row["estimated_input_tokens"] = math.ceil(len(request_text) / chars_per_token)
        row["expected_output_tokens"] = int(expected_output_tokens)
        row["max_output_tokens"] = int(max_output_tokens)


def _build_summary(
    request_rows: Sequence[Mapping[str, object]],
    *,
    expected_output_tokens: int,
    max_output_tokens: int,
) -> dict[str, object]:
    by_target: dict[str, int] = {}
    by_strategy: dict[str, int] = {}
    families: set[str] = set()
    candidate_slots: set[tuple[str, str, str]] = set()
    estimated_input_tokens = 0
    semantic_candidate_count = 0
    phrase_candidate_count = 0
    for row in request_rows:
        target = str(row.get("prompt_slot") or "").strip()
        by_target[target] = by_target.get(target, 0) + 1
        strategy = str(row.get("candidate_strategy") or "").strip()
        if strategy:
            by_strategy[strategy] = by_strategy.get(strategy, 0) + 1
        family_id = str(row.get("family_id") or "").strip()
        if family_id:
            families.add(family_id)
            candidate_slots.add(
                (
                    family_id,
                    target,
                    str(row.get("candidate_target") or "").strip(),
                )
            )
        if target in {"active_example", "shadow_example"}:
            semantic_candidate_count += 1
        elif target == "phrase_control_example":
            phrase_candidate_count += 1
        estimated_input_tokens += int(row.get("estimated_input_tokens") or 0)
    return {
        "request_count": len(request_rows),
        "family_count": len(families),
        "candidate_slot_count": len(candidate_slots),
        "planned_raw_candidate_count": len(request_rows),
        "planned_semantic_candidate_count": semantic_candidate_count,
        "planned_phrase_candidate_count": phrase_candidate_count,
        "requests_by_generation_target": by_target,
        "requests_by_candidate_strategy": by_strategy,
        "estimated_input_tokens": estimated_input_tokens,
        "expected_output_tokens": expected_output_tokens * len(request_rows),
        "max_output_tokens": max_output_tokens * len(request_rows),
    }


def render_example_frame_generation_plan_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es LLM Example-Frame Generation Plan",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_id', '')}`",
        f"- Required families: `{report.get('required_family_source', '')}`",
        f"- Base batch: `{report.get('base_batch_id', '')}`",
        f"- Prompt version: `{report.get('prompt_version', '')}`",
        f"- Selected model: `{report.get('selected_model_id', '')}`",
        f"- Decision contract: `{report.get('decision_contract', '')}`",
        f"- Review leakage policy: `{report.get('review_leakage_policy', '')}`",
        f"- Generation targets: `{', '.join(_as_texts(report.get('generation_targets')) or [])}`",
        f"- Candidate defaults: `{json.dumps(report.get('candidate_defaults', {}), sort_keys=True)}`",
        "",
        "## Summary",
        "",
        f"- Requests: `{summary.get('request_count', 0)}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Candidate slots: `{summary.get('candidate_slot_count', 0)}`",
        f"- Planned raw candidates: `{summary.get('planned_raw_candidate_count', 0)}`",
        f"- Planned semantic candidates: `{summary.get('planned_semantic_candidate_count', 0)}`",
        f"- Planned phrase candidates: `{summary.get('planned_phrase_candidate_count', 0)}`",
        f"- Estimated input tokens: `{summary.get('estimated_input_tokens', 0)}`",
        f"- Expected output tokens: `{summary.get('expected_output_tokens', 0)}`",
        f"- Max output tokens: `{summary.get('max_output_tokens', 0)}`",
        f"- Requests by target: `{json.dumps(summary.get('requests_by_generation_target', {}), sort_keys=True)}`",
        f"- Requests by strategy: `{json.dumps(summary.get('requests_by_candidate_strategy', {}), sort_keys=True)}`",
        "",
        "## Request Rows",
        "",
        "| Request | Target | Family | Candidate | Attempt | Strategy | Input Tokens |",
        "| --- | --- | --- | --- | ---: | --- | ---: |",
    ]
    for row in report.get("request_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('request_id', '')}`",
                    f"`{row.get('prompt_slot', '')}`",
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('candidate_target', '')}`",
                    str(row.get("candidate_index", 1)),
                    f"`{row.get('candidate_strategy', '')}`",
                    str(row.get("estimated_input_tokens", 0)),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _build_recommendation(summary: Mapping[str, object]) -> str:
    if int(summary.get("request_count") or 0) <= 0:
        return (
            "The base evidence batch already satisfies the selected missing-row target plan "
            "for the required families."
        )
    return (
        "Execute only these selected candidate requests, preserve raw generated count separately "
        "from structurally accepted, leakage-kept, and admitted counts, then merge admitted rows "
        "with the base evidence batch and rerun the split contract plus prototype-admission "
        "ablation matrix."
    )


def _normalize_generation_targets(values: Sequence[str]) -> list[str]:
    normalized = []
    unsupported = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        if text not in SUPPORTED_GENERATION_TARGETS:
            unsupported.append(text)
            continue
        if text not in normalized:
            normalized.append(text)
    if unsupported:
        raise ValueError(
            "Unsupported generation_targets values: "
            f"{unsupported!r}; expected one of {sorted(SUPPORTED_GENERATION_TARGETS)!r}."
        )
    if not normalized:
        raise ValueError(
            "generation_targets must include at least one of "
            f"{sorted(SUPPORTED_GENERATION_TARGETS)!r}."
        )
    return normalized


def _as_texts(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _required_family_keys(payload: Mapping[str, object]) -> list[str]:
    families = payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
        raise ValueError("required-family payload must contain a `families` array.")
    keys: list[str] = []
    for family in families:
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        if family_id and family_id not in keys:
            keys.append(family_id)
    if not keys:
        raise ValueError("required-family payload did not contain any family ids.")
    return keys


def _queue_family_lookup(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    families = payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
        raise ValueError("required-family payload must contain a `families` array.")
    return {
        str(family.get("family_id") or "").strip(): family
        for family in families
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
    }


def _dataset_family_lookup(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    families = payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
        raise ValueError("dataset payload must contain a `families` array.")
    return {
        str(family.get("family_id") or "").strip(): family
        for family in families
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
    }


def _active_sense(family: Mapping[str, object]) -> Mapping[str, object]:
    active = family.get("active")
    if not isinstance(active, Mapping):
        raise ValueError(f"Family {family.get('family_id', '')!r} is missing `active`.")
    return active


def _shadow_senses(family: Mapping[str, object]) -> list[Mapping[str, object]]:
    shadows = family.get("shadows")
    if not isinstance(shadows, Sequence) or isinstance(shadows, (str, bytes)):
        return []
    return [shadow for shadow in shadows if isinstance(shadow, Mapping)]


def _sense_id(sense: Mapping[str, object]) -> str:
    return str(sense.get("sense_id") or "").strip()


def _canonical_pos(sense: Mapping[str, object]) -> str:
    return str(sense.get("canonical_pos") or "").strip().lower()


def _queue_metadata(queue_family: Mapping[str, object]) -> dict[str, object]:
    metadata: dict[str, object] = {}
    for source_key, target_key in (
        ("role", "queue_role"),
        ("archetype", "queue_archetype"),
        ("likely_bucket", "queue_likely_bucket"),
        ("primary_prompt_slot", "queue_primary_prompt_slot"),
    ):
        text = str(queue_family.get(source_key) or "").strip()
        if text:
            metadata[target_key] = text
    priority = queue_family.get("priority_rank")
    if isinstance(priority, int) and not isinstance(priority, bool):
        metadata["queue_priority_rank"] = priority
    notes = queue_family.get("notes")
    if isinstance(notes, Sequence) and not isinstance(notes, (str, bytes)):
        note_texts = [str(note).strip() for note in notes if str(note).strip()]
        if note_texts:
            metadata["queue_notes"] = note_texts
    return metadata


def _roles_for_generation_target(generation_target: str) -> list[str]:
    if generation_target == "phrase_control_example":
        return ["discrimination", "phrase_containment"]
    if generation_target == "active_example":
        return ["cue_generation", "discrimination"]
    return ["discrimination"]


def _request_kind(generation_target: str) -> str:
    if generation_target == "active_example":
        return "active"
    if generation_target == "shadow_example":
        return "shadow"
    if generation_target == "phrase_control_example":
        return "phrase-control"
    return slug(generation_target)


def main() -> int:
    args = _parse_args()
    report = build_example_frame_generation_plan(
        dataset_payload=load_sentence_veto_dataset(args.dataset),
        required_family_payload=_load_json(args.required_family_json),
        base_evidence_batch_payload=_load_json(args.base_evidence_batch_json),
        model_id=str(args.model_id or "").strip() or DEFAULT_MODEL_ID,
        temperature=float(args.temperature),
        chars_per_token=float(args.chars_per_token),
        expected_output_tokens=int(args.expected_output_tokens),
        max_output_tokens=int(args.max_output_tokens),
        generation_targets=_as_texts(str(args.generation_targets or "").split(",")),
        semantic_candidates_per_row=int(args.semantic_candidates_per_row),
        hard_semantic_candidates_per_row=int(args.hard_semantic_candidates_per_row),
        phrase_candidates_per_row=int(args.phrase_candidates_per_row),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_example_frame_generation_plan_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
