#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
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
_SLUG_RE = re.compile(r"[^a-z0-9]+")


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
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be > 0")
    required_family_keys = _required_family_keys(required_family_payload)
    queue_lookup = _queue_family_lookup(required_family_payload)
    contract_report = build_example_frame_contract_report(
        base_evidence_batch_payload,
        required_family_keys=required_family_keys,
        generated_at=generated_at,
    )
    dataset_lookup = _dataset_family_lookup(dataset_payload)
    request_rows = _build_request_rows(
        contract_report=contract_report,
        dataset_lookup=dataset_lookup,
        queue_lookup=queue_lookup,
        required_family_keys=required_family_keys,
        model_id=str(model_id or "").strip() or DEFAULT_MODEL_ID,
        temperature=float(temperature),
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
    model_id: str,
    temperature: float,
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
        if "active_examples" in missing:
            active = _active_sense(family)
            request_rows.append(
                _request_row(
                    family=family,
                    queue_family=queue_family,
                    candidate_sense=active,
                    generation_target="active_example",
                    relation_type="anchor_cue",
                    model_id=model_id,
                    temperature=temperature,
                )
            )
        if "shadow_examples" in missing:
            for shadow in _shadow_senses(family):
                request_rows.append(
                    _request_row(
                        family=family,
                        queue_family=queue_family,
                        candidate_sense=shadow,
                        generation_target="shadow_example",
                        relation_type="shadow_candidate",
                        model_id=model_id,
                        temperature=temperature,
                    )
                )
        if "phrase_control_examples" in missing:
            request_rows.append(
                _request_row(
                    family=family,
                    queue_family=queue_family,
                    candidate_sense={},
                    generation_target="phrase_control_example",
                    relation_type="phrase_control_example",
                    model_id=model_id,
                    temperature=temperature,
                )
            )
    return request_rows


def _request_row(
    *,
    family: Mapping[str, object],
    queue_family: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    generation_target: str,
    relation_type: str,
    model_id: str,
    temperature: float,
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
    request_id = _request_id(
        family_id=family_id,
        request_kind=request_kind,
        candidate_id=candidate_id,
    )
    roles = _roles_for_generation_target(generation_target)
    queue_metadata = _queue_metadata(queue_family)
    expected_row = {
        "row_id": _expected_row_id(
            family_id=family_id,
            request_kind=request_kind,
            candidate_id=candidate_id,
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
        "input_ref": request_id,
        "review_state": "unreviewed",
        "promotion_state": "proposed",
        "runtime_publishable": False,
        "metadata": {
            "family_id": family_id,
            "active_sense_id": _sense_id(active),
            "candidate_sense_id": candidate_id,
            "generation_target": generation_target,
            "source_gap": generation_target,
            **queue_metadata,
        },
    }
    if generation_target == "phrase_control_example":
        expected_row["metadata"]["gold_decision"] = "abstain"

    return {
        "request_id": request_id,
        "prompt_slot": generation_target,
        "family_id": family_id,
        "trigger": trigger,
        "active_target": active_target,
        "candidate_target": candidate_target,
        "candidate_pos": str(expected_row["candidate_pos"]),
        "relation_type": relation_type,
        "roles": roles,
        "queue_metadata": queue_metadata,
        "model_id": model_id,
        "temperature": temperature,
        "system_prompt": _system_prompt(generation_target),
        "user_prompt": _user_prompt(
            family=family,
            queue_family=queue_family,
            candidate_sense=candidate_sense,
            generation_target=generation_target,
        ),
        "expected_row_preview": expected_row,
    }


def _system_prompt(generation_target: str) -> str:
    if generation_target == "phrase_control_example":
        return (
            "You generate one LexiShift phrase-control example. Return compact JSON only. "
            "The example must use the English trigger in a phrase, idiom, lexicalized frame, "
            "or unrelated sense that should make LexiShift abstain. Do not use Spanish. "
            "Do not copy any benchmark sentence."
        )
    return (
        "You generate one LexiShift semantic example frame. Return compact JSON only. "
        "The example must help discriminate one English trigger sense from its competitor. "
        "Write an original English sentence or compact frame that could overlap real user text. "
        "Do not use Spanish. Do not copy any benchmark sentence."
    )


def _user_prompt(
    *,
    family: Mapping[str, object],
    queue_family: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    generation_target: str,
) -> str:
    trigger = str(family.get("trigger") or "").strip()
    active = _active_sense(family)
    shadows = _shadow_senses(family)
    selected_shadow_label = _selected_shadow_label(
        shadows=shadows,
        candidate_sense=candidate_sense,
    )
    active_label = _sense_text(active, "sense_label")
    active_gloss = _sense_text(active, "gloss_text")
    shadow_lines = "\n".join(
        (
            f"- competing sense {index}: {_sense_text(shadow, 'sense_label')} | "
            f"{_sense_text(shadow, 'gloss_text')} | POS: "
            f"{str(shadow.get('canonical_pos') or '').strip() or 'unknown'}"
        )
        for index, shadow in enumerate(shadows, start=1)
    )
    queue_lines = _queue_prompt_lines(queue_family)
    base = [
        "Return a JSON object with exactly one key `items`.",
        "`items` must be an array with exactly one object.",
        "That object may contain only `evidence_text` and optional numeric `confidence`.",
        "",
        f"English trigger: `{trigger}`",
        f"Active sense: {active_label} | {active_gloss} | POS: {str(active.get('canonical_pos') or '').strip() or 'unknown'}",
        "",
        "Competing senses:",
        shadow_lines or "- none",
        "",
        "Queue context:",
        *queue_lines,
        "",
    ]
    if generation_target == "active_example":
        base.extend(
            [
                "Task: write one original English example for the active sense.",
                "The example must make the active sense more plausible than the competing senses.",
            ]
        )
    elif generation_target == "shadow_example":
        base.extend(
            [
                f"Task: write one original English example for {selected_shadow_label}.",
                f"Competing sense details: {_sense_text(candidate_sense, 'sense_label')} | {_sense_text(candidate_sense, 'gloss_text')}",
                "The example must make the competing sense more plausible than the active sense.",
            ]
        )
    else:
        base.extend(
            [
                "Task: write one original phrase-control example that should abstain.",
                "It must contain the trigger text, but it must not express the active sense or any listed competing sense cleanly.",
                "Prefer idioms, lexicalized particles, verb frames, or phrase-level uses when natural.",
            ]
        )
    base.extend(
        [
            "",
            "Rules:",
            "- write 5 to 18 English words",
            "- include the trigger text naturally",
            "- do not mention translation targets or non-English words",
            "- do not explain the answer",
            "- do not use bullets or multiple examples",
            "- return JSON only",
        ]
    )
    return "\n".join(base)


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
    families: set[str] = set()
    estimated_input_tokens = 0
    for row in request_rows:
        target = str(row.get("prompt_slot") or "").strip()
        by_target[target] = by_target.get(target, 0) + 1
        family_id = str(row.get("family_id") or "").strip()
        if family_id:
            families.add(family_id)
        estimated_input_tokens += int(row.get("estimated_input_tokens") or 0)
    return {
        "request_count": len(request_rows),
        "family_count": len(families),
        "requests_by_generation_target": by_target,
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
        "",
        "## Summary",
        "",
        f"- Requests: `{summary.get('request_count', 0)}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Estimated input tokens: `{summary.get('estimated_input_tokens', 0)}`",
        f"- Expected output tokens: `{summary.get('expected_output_tokens', 0)}`",
        f"- Max output tokens: `{summary.get('max_output_tokens', 0)}`",
        f"- Requests by target: `{json.dumps(summary.get('requests_by_generation_target', {}), sort_keys=True)}`",
        "",
        "## Request Rows",
        "",
        "| Request | Target | Family | Candidate | Input Tokens |",
        "| --- | --- | --- | --- | ---: |",
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
                    str(row.get("estimated_input_tokens", 0)),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _build_recommendation(summary: Mapping[str, object]) -> str:
    if int(summary.get("request_count") or 0) <= 0:
        return "The base evidence batch already satisfies the required-family source contract."
    return (
        "Execute only these missing-row requests, then merge accepted rows with the base "
        "reverse-aux batch and rerun the required-family contract plus prototype-admission probe."
    )


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


def _sense_text(sense: Mapping[str, object], key: str) -> str:
    views = sense.get("evidence_views")
    if isinstance(views, Mapping):
        text = str(views.get(key) or "").strip()
        if text:
            return text
    return ""


def _sense_id(sense: Mapping[str, object]) -> str:
    return str(sense.get("sense_id") or "").strip()


def _selected_shadow_label(
    *,
    shadows: Sequence[Mapping[str, object]],
    candidate_sense: Mapping[str, object],
) -> str:
    candidate_id = _sense_id(candidate_sense)
    for index, shadow in enumerate(shadows, start=1):
        if _sense_id(shadow) == candidate_id:
            return f"competing sense {index}"
    return "the requested competing sense"


def _queue_prompt_lines(queue_family: Mapping[str, object]) -> list[str]:
    lines = [
        f"- role: {str(queue_family.get('role') or '').strip() or 'unspecified'}",
        f"- archetype: {str(queue_family.get('archetype') or '').strip() or 'unspecified'}",
        f"- likely bucket: {str(queue_family.get('likely_bucket') or '').strip() or 'unspecified'}",
    ]
    notes = queue_family.get("notes")
    if isinstance(notes, Sequence) and not isinstance(notes, (str, bytes)):
        note_texts = [str(note).strip() for note in notes if str(note).strip()]
        if note_texts:
            lines.append("- notes: " + " | ".join(note_texts))
    return lines


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
    return _slug(generation_target)


def _request_id(*, family_id: str, request_kind: str, candidate_id: str) -> str:
    parts = ["en-es", "example-frame-missing", request_kind, _slug(family_id)]
    if request_kind == "shadow" and candidate_id:
        parts.append(_slug(candidate_id))
    return ":".join(parts)


def _expected_row_id(
    *,
    family_id: str,
    request_kind: str,
    candidate_id: str,
) -> str:
    parts = [_slug(family_id), "llm"]
    if request_kind == "phrase-control":
        parts.extend(["phrase-control", "missing", "v1"])
    elif request_kind == "shadow":
        parts.extend(["shadow", _slug(candidate_id), "missing", "v1"])
    else:
        parts.extend(["active", "missing", "v1"])
    return ":".join(parts)


def _slug(value: object) -> str:
    text = str(value or "").strip().lower()
    return _SLUG_RE.sub("-", text).strip("-") or "row"


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
