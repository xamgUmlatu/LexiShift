#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
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

from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402

DEFAULT_DATASET = (
    DOCS_ROOT / "test_inputs" / "semantic_routing_cases" / "en_es_sentence_veto_v10.json"
)
DEFAULT_ALIGNMENT_AUDIT = (
    TEST_OUTPUTS_ROOT / "semantic_source_row_alignment_audit_en_es_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_source_frame_gap_plan_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_source_frame_gap_plan_en_es_latest.md"

SOURCE_ID = "llm_aligned_sentence_frame_rows"
PROMPT_VERSION = "aligned-sentence-frame-v2"
DEFAULT_MODEL_ID = "gpt-5.4-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_STANDARD_CANDIDATES_PER_SLOT = 3
DEFAULT_HARD_CANDIDATES_PER_SLOT = 5
SLUG_RE = re.compile(r"[^a-z0-9]+")
DIVERSITY_FRAMES = (
    {
        "frame_id": "specific_role_action",
        "directive": (
            "Use a specific role or person doing a concrete action; avoid generic event "
            "attendance, generic approval, and repeated subject-verb openings."
        ),
    },
    {
        "frame_id": "place_time_observation",
        "directive": (
            "Use a clear place or time anchor plus an observation; make the words around "
            "the trigger carry the intended sense."
        ),
    },
    {
        "frame_id": "problem_resolution",
        "directive": (
            "Use a problem, repair, correction, warning, or resolution frame; avoid "
            "copying ordinary textbook-style examples."
        ),
    },
    {
        "frame_id": "instruction_or_plan",
        "directive": (
            "Use an instruction, plan, request, or future action frame; keep the trigger "
            "grammatical in that sentence."
        ),
    },
    {
        "frame_id": "contrastive_detail",
        "directive": (
            "Use a concrete nearby detail that would distinguish this sense from the "
            "active or competing senses without naming the Spanish target."
        ),
    },
)


def main() -> int:
    args = _parse_args()
    report = build_source_frame_gap_plan(
        dataset_payload=load_sentence_veto_dataset(args.dataset),
        alignment_audit_payload=_load_json(args.alignment_audit),
        dataset_path=args.dataset,
        alignment_audit_path=args.alignment_audit,
        standard_candidates_per_slot=args.standard_candidates_per_slot,
        hard_candidates_per_slot=args.hard_candidates_per_slot,
        model_id=args.model_id,
        temperature=args.temperature,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_source_frame_gap_plan_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_source_frame_gap_plan(
    *,
    dataset_payload: Mapping[str, object],
    alignment_audit_payload: Mapping[str, object],
    dataset_path: Path | None = None,
    alignment_audit_path: Path | None = None,
    standard_candidates_per_slot: int = DEFAULT_STANDARD_CANDIDATES_PER_SLOT,
    hard_candidates_per_slot: int = DEFAULT_HARD_CANDIDATES_PER_SLOT,
    model_id: str = DEFAULT_MODEL_ID,
    temperature: float = DEFAULT_TEMPERATURE,
) -> dict[str, object]:
    if standard_candidates_per_slot <= 0:
        raise ValueError("standard_candidates_per_slot must be > 0")
    if hard_candidates_per_slot <= 0:
        raise ValueError("hard_candidates_per_slot must be > 0")
    ready_counts = _selector_ready_counts(alignment_audit_payload)
    slot_rows = _build_slot_rows(dataset_payload=dataset_payload, ready_counts=ready_counts)
    missing_slots = [row for row in slot_rows if not row["selector_ready"]]
    request_rows = _build_request_rows(
        dataset_payload=dataset_payload,
        missing_slots=missing_slots,
        standard_candidates_per_slot=standard_candidates_per_slot,
        hard_candidates_per_slot=hard_candidates_per_slot,
        model_id=str(model_id or "").strip() or DEFAULT_MODEL_ID,
        temperature=float(temperature),
    )
    summary = _build_summary(slot_rows, request_rows)
    return {
        "schema_version": 1,
        "status": "ready" if request_rows else "no_frame_gaps",
        "generated_at": _utc_now(),
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "dataset_path": str(dataset_path or ""),
        "alignment_audit_path": str(alignment_audit_path or ""),
        "source_id": SOURCE_ID,
        "prompt_version": PROMPT_VERSION,
        "selected_model_id": str(model_id or "").strip() or DEFAULT_MODEL_ID,
        "selected_temperature": float(temperature),
        "leakage_policy": "prompts_use_sense_labels_and_glosses_only; do_not_include_sentence_veto_case_sentences",
        "summary": summary,
        "slot_rows": slot_rows,
        "request_rows": request_rows,
        "recommendation": _recommendation(summary),
    }


def render_source_frame_gap_plan_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es Source Frame Gap Plan",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_path', '')}`",
        f"- Alignment audit: `{report.get('alignment_audit_path', '')}`",
        f"- Candidate source id: `{report.get('source_id', '')}`",
        f"- Prompt version: `{report.get('prompt_version', '')}`",
        f"- Selected model: `{report.get('selected_model_id', '')}`",
        f"- Temperature: `{report.get('selected_temperature', '')}`",
        f"- Leakage policy: `{report.get('leakage_policy', '')}`",
        f"- Sense slots: `{summary.get('slot_count', 0)}`",
        f"- Missing selector-ready slots: `{summary.get('missing_slot_count', 0)}`",
        f"- Planned candidate requests: `{summary.get('request_count', 0)}`",
        f"- Candidate diversity frames: `{summary.get('diversity_frame_count', 0)}`",
        f"- Estimated prompt tokens: `{summary.get('estimated_prompt_tokens', 0)}`",
        "",
        "## Recommendation",
        "",
        str(report.get("recommendation") or ""),
        "",
        "## Gap Summary",
        "",
        "| Target | Slots | Missing Slots | Candidate Requests |",
        "| --- | ---: | ---: | ---: |",
    ]
    target_counts = summary.get("target_counts")
    if isinstance(target_counts, Mapping):
        for target in ("active_example", "shadow_example"):
            row = (
                target_counts.get(target) if isinstance(target_counts.get(target), Mapping) else {}
            )
            lines.append(
                "| "
                + " | ".join(
                    (
                        target,
                        str(int(row.get("slot_count") or 0)),
                        str(int(row.get("missing_slot_count") or 0)),
                        str(int(row.get("request_count") or 0)),
                    )
                )
                + " |"
            )

    lines.extend(["", "## Missing Slots By Family", ""])
    lines.append("| Family | Missing Active | Missing Shadows | Candidate Requests |")
    lines.append("| --- | ---: | ---: | ---: |")
    for row in _mapping_rows(summary.get("family_gap_rows")):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row.get("family_id") or ""),
                    str(int(row.get("missing_active_slot_count") or 0)),
                    str(int(row.get("missing_shadow_slot_count") or 0)),
                    str(int(row.get("request_count") or 0)),
                )
            )
            + " |"
        )

    lines.extend(["", "## Request Rows", ""])
    lines.append(
        "| Request | Target | Family | Candidate Sense | Attempt | Diversity Frame | Prompt Tokens Est. |"
    )
    lines.append("| --- | --- | --- | --- | ---: | --- | ---: |")
    for row in _mapping_rows(report.get("request_rows"))[:80]:
        lines.append(
            "| "
            + " | ".join(
                (
                    _escape_md(str(row.get("request_id") or "")),
                    _escape_md(str(row.get("generation_target") or "")),
                    _escape_md(str(row.get("family_id") or "")),
                    _escape_md(str(row.get("candidate_sense_id") or "")),
                    str(int(row.get("candidate_index") or 0)),
                    _escape_md(str(row.get("diversity_frame_id") or "")),
                    str(int(row.get("prompt_token_estimate") or 0)),
                )
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _selector_ready_counts(
    alignment_audit_payload: Mapping[str, object],
) -> dict[str, int]:
    rows = alignment_audit_payload.get("audited_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        rows = alignment_audit_payload.get("sample_rows")
    counts: dict[str, int] = defaultdict(int)
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return {}
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("selector_ready"):
            continue
        candidate_sense_id = str(row.get("candidate_sense_id") or "").strip()
        if candidate_sense_id:
            counts[candidate_sense_id] += 1
    return dict(counts)


def _build_slot_rows(
    *,
    dataset_payload: Mapping[str, object],
    ready_counts: Mapping[str, int],
) -> list[dict[str, object]]:
    slot_rows: list[dict[str, object]] = []
    for family in _families(dataset_payload):
        family_id = str(family.get("family_id") or "").strip()
        trigger = str(family.get("trigger") or "").strip()
        active = _active_sense(family)
        active_id = _sense_id(active)
        if active_id:
            slot_rows.append(
                _slot_row(
                    family=family,
                    candidate_sense=active,
                    generation_target="active_example",
                    relation_type="anchor_cue",
                    selector_ready_count=int(ready_counts.get(active_id) or 0),
                    trigger=trigger,
                    family_id=family_id,
                )
            )
        for shadow in _shadow_senses(family):
            shadow_id = _sense_id(shadow)
            if not shadow_id:
                continue
            slot_rows.append(
                _slot_row(
                    family=family,
                    candidate_sense=shadow,
                    generation_target="shadow_example",
                    relation_type="shadow_candidate",
                    selector_ready_count=int(ready_counts.get(shadow_id) or 0),
                    trigger=trigger,
                    family_id=family_id,
                )
            )
    return slot_rows


def _slot_row(
    *,
    family: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    generation_target: str,
    relation_type: str,
    selector_ready_count: int,
    trigger: str,
    family_id: str,
) -> dict[str, object]:
    active = _active_sense(family)
    shadow_positions = [
        str(shadow.get("canonical_pos") or "").strip() for shadow in _shadow_senses(family)
    ]
    candidate_pos = str(candidate_sense.get("canonical_pos") or "").strip()
    active_pos = str(active.get("canonical_pos") or "").strip()
    return {
        "slot_id": f"{family_id}:{generation_target}:{_sense_id(candidate_sense)}",
        "family_id": family_id,
        "trigger": trigger,
        "generation_target": generation_target,
        "relation_type": relation_type,
        "active_sense_id": _sense_id(active),
        "candidate_sense_id": _sense_id(candidate_sense),
        "active_target": str(active.get("target_lemma") or "").strip(),
        "candidate_target": str(candidate_sense.get("target_lemma") or "").strip(),
        "candidate_pos": candidate_pos,
        "selector_ready_count": selector_ready_count,
        "selector_ready": selector_ready_count > 0,
        "difficulty": _slot_difficulty(
            generation_target=generation_target,
            active_pos=active_pos,
            candidate_pos=candidate_pos,
            shadow_positions=shadow_positions,
        ),
        "sense_label": _sense_text(candidate_sense, "sense_label"),
        "gloss_text": _sense_text(candidate_sense, "gloss_text"),
    }


def _build_request_rows(
    *,
    dataset_payload: Mapping[str, object],
    missing_slots: Sequence[Mapping[str, object]],
    standard_candidates_per_slot: int,
    hard_candidates_per_slot: int,
    model_id: str,
    temperature: float,
) -> list[dict[str, object]]:
    family_lookup = {
        str(family.get("family_id") or "").strip(): family for family in _families(dataset_payload)
    }
    request_rows: list[dict[str, object]] = []
    for slot in missing_slots:
        family = family_lookup.get(str(slot.get("family_id") or ""))
        if not isinstance(family, Mapping):
            continue
        candidate_sense = _sense_by_id(family, str(slot.get("candidate_sense_id") or ""))
        if not candidate_sense:
            continue
        candidate_count = (
            hard_candidates_per_slot
            if str(slot.get("difficulty") or "") == "same_pos_hard_semantic"
            else standard_candidates_per_slot
        )
        for candidate_index in range(1, candidate_count + 1):
            diversity_frame = _diversity_frame(candidate_index)
            prompt = _frame_user_prompt(
                family=family,
                candidate_sense=candidate_sense,
                generation_target=str(slot.get("generation_target") or ""),
                candidate_index=candidate_index,
                candidate_count=candidate_count,
                diversity_frame=diversity_frame,
            )
            request_rows.append(
                {
                    "request_id": _request_id(
                        slot=slot,
                        candidate_index=candidate_index,
                        candidate_count=candidate_count,
                    ),
                    "slot_id": str(slot.get("slot_id") or ""),
                    "family_id": str(slot.get("family_id") or ""),
                    "trigger": str(slot.get("trigger") or ""),
                    "prompt_slot": str(slot.get("generation_target") or ""),
                    "generation_target": str(slot.get("generation_target") or ""),
                    "relation_type": str(slot.get("relation_type") or ""),
                    "roles": _roles_for_generation_target(str(slot.get("generation_target") or "")),
                    "active_sense_id": str(slot.get("active_sense_id") or ""),
                    "candidate_sense_id": str(slot.get("candidate_sense_id") or ""),
                    "active_target": str(slot.get("active_target") or ""),
                    "candidate_target": str(slot.get("candidate_target") or ""),
                    "candidate_pos": str(slot.get("candidate_pos") or ""),
                    "difficulty": str(slot.get("difficulty") or ""),
                    "candidate_index": candidate_index,
                    "candidate_count": candidate_count,
                    "diversity_frame_id": str(diversity_frame["frame_id"]),
                    "diversity_directive": str(diversity_frame["directive"]),
                    "model_id": model_id,
                    "temperature": temperature,
                    "source_id": SOURCE_ID,
                    "prompt_version": PROMPT_VERSION,
                    "expected_row_id": _expected_row_id(
                        slot=slot,
                        candidate_index=candidate_index,
                        candidate_count=candidate_count,
                    ),
                    "system_prompt": _frame_system_prompt(),
                    "user_prompt": prompt,
                    "prompt_token_estimate": _token_estimate(prompt),
                    "expected_row_preview": _expected_row_preview(
                        slot=slot,
                        candidate_index=candidate_index,
                        candidate_count=candidate_count,
                        diversity_frame=diversity_frame,
                    ),
                    "output_contract": {
                        "json_shape": {"items": [{"evidence_text": "string"}]},
                        "minimum_words_before_trigger": 2,
                        "minimum_words_after_trigger": 2,
                        "must_include_trigger": True,
                        "must_not_copy_sentence_veto_cases": True,
                        "must_follow_diversity_frame": True,
                    },
                }
            )
    return request_rows


def _expected_row_preview(
    *,
    slot: Mapping[str, object],
    candidate_index: int,
    candidate_count: int,
    diversity_frame: Mapping[str, str],
) -> dict[str, object]:
    generation_target = str(slot.get("generation_target") or "")
    return {
        "row_id": _expected_row_id(
            slot=slot,
            candidate_index=candidate_index,
            candidate_count=candidate_count,
        ),
        "relation_type": str(slot.get("relation_type") or ""),
        "roles": _roles_for_generation_target(generation_target),
        "trigger": str(slot.get("trigger") or ""),
        "active_target": str(slot.get("active_target") or ""),
        "candidate_target": str(slot.get("candidate_target") or ""),
        "candidate_pos": str(slot.get("candidate_pos") or ""),
        "evidence_text": "<model-written original trigger-bearing sentence frame>",
        "prompt_slot": generation_target,
        "input_ref": _request_id(
            slot=slot,
            candidate_index=candidate_index,
            candidate_count=candidate_count,
        ),
        "review_state": "unreviewed",
        "promotion_state": "proposed",
        "runtime_publishable": False,
        "metadata": {
            "family_id": str(slot.get("family_id") or ""),
            "active_sense_id": str(slot.get("active_sense_id") or ""),
            "candidate_sense_id": str(slot.get("candidate_sense_id") or ""),
            "generation_target": generation_target,
            "source_gap": "selector_ready_sentence_frame",
            "candidate_index": int(candidate_index),
            "candidate_count": int(candidate_count),
            "candidate_strategy": str(slot.get("difficulty") or ""),
            "diversity_frame_id": str(diversity_frame["frame_id"]),
            "requires_trigger_bearing_frame": True,
            "minimum_words_before_trigger": 2,
            "minimum_words_after_trigger": 2,
        },
    }


def _build_summary(
    slot_rows: Sequence[Mapping[str, object]],
    request_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    target_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"slot_count": 0, "missing_slot_count": 0, "request_count": 0}
    )
    for slot in slot_rows:
        target = str(slot.get("generation_target") or "").strip()
        target_counts[target]["slot_count"] += 1
        if not slot.get("selector_ready"):
            target_counts[target]["missing_slot_count"] += 1
    for request in request_rows:
        target = str(request.get("generation_target") or "").strip()
        target_counts[target]["request_count"] += 1

    family_missing = Counter(
        str(slot.get("family_id") or "") for slot in slot_rows if not slot.get("selector_ready")
    )
    family_request_counts = Counter(str(row.get("family_id") or "") for row in request_rows)
    family_gap_rows = []
    for family_id in sorted(family_missing):
        family_slots = [
            slot
            for slot in slot_rows
            if str(slot.get("family_id") or "") == family_id and not slot.get("selector_ready")
        ]
        family_gap_rows.append(
            {
                "family_id": family_id,
                "missing_active_slot_count": sum(
                    1 for slot in family_slots if slot.get("generation_target") == "active_example"
                ),
                "missing_shadow_slot_count": sum(
                    1 for slot in family_slots if slot.get("generation_target") == "shadow_example"
                ),
                "missing_slot_count": family_missing[family_id],
                "request_count": family_request_counts[family_id],
            }
        )
    family_gap_rows.sort(key=lambda row: (-int(row["request_count"]), str(row["family_id"])))
    return {
        "slot_count": len(slot_rows),
        "selector_ready_slot_count": sum(1 for slot in slot_rows if slot.get("selector_ready")),
        "missing_slot_count": sum(1 for slot in slot_rows if not slot.get("selector_ready")),
        "request_count": len(request_rows),
        "diversity_frame_count": len(
            {str(row.get("diversity_frame_id") or "") for row in request_rows}
        ),
        "estimated_prompt_tokens": sum(
            int(row.get("prompt_token_estimate") or 0) for row in request_rows
        ),
        "target_counts": dict(target_counts),
        "family_gap_rows": family_gap_rows,
    }


def _recommendation(summary: Mapping[str, object]) -> str:
    request_count = int(summary.get("request_count") or 0)
    missing_slot_count = int(summary.get("missing_slot_count") or 0)
    if request_count == 0:
        return "No source-frame generation requests are needed for the audited selector surface."
    return (
        f"Plan {request_count} no-spend candidate requests covering {missing_slot_count} "
        "missing active/shadow selector slots. Execute these only through the existing "
        "leakage audit and source-admission cycle, then rerun the context-conditioned "
        "matrix before any runtime claim."
    )


def _frame_system_prompt() -> str:
    return (
        "You generate one LexiShift source-evidence sentence frame. Return compact JSON only. "
        "The sentence must contain the English trigger with useful words before and after it. "
        "Do not use Spanish. Do not copy any benchmark sentence."
    )


def _diversity_frame(candidate_index: int) -> Mapping[str, str]:
    return DIVERSITY_FRAMES[(max(1, int(candidate_index)) - 1) % len(DIVERSITY_FRAMES)]


def _roles_for_generation_target(generation_target: str) -> list[str]:
    if generation_target == "active_example":
        return ["cue_generation", "discrimination"]
    return ["discrimination"]


def _frame_user_prompt(
    *,
    family: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    generation_target: str,
    candidate_index: int,
    candidate_count: int,
    diversity_frame: Mapping[str, str],
) -> str:
    trigger = str(family.get("trigger") or "").strip()
    active = _active_sense(family)
    shadows = _shadow_senses(family)
    shadow_lines = "\n".join(
        f"- {_sense_id(shadow)}: {_sense_text(shadow, 'sense_label')} | {_sense_text(shadow, 'gloss_text')} | POS: {str(shadow.get('canonical_pos') or '').strip()}"
        for shadow in shadows
    )
    target_label = "active sense" if generation_target == "active_example" else "competing sense"
    target_instruction = (
        "Make the active sense more plausible than every competing sense."
        if generation_target == "active_example"
        else "Make this competing sense more plausible than the active sense."
    )
    lines = [
        "Return a JSON object with exactly one key `items`.",
        "`items` must be an array with exactly one object.",
        "That object may contain only `evidence_text` and optional numeric `confidence`.",
        "",
        f"English trigger: `{trigger}`",
        f"Target: {target_label}",
        f"Target sense id: {_sense_id(candidate_sense)}",
        f"Target sense: {_sense_text(candidate_sense, 'sense_label')} | {_sense_text(candidate_sense, 'gloss_text')}",
        f"Active sense: {_sense_text(active, 'sense_label')} | {_sense_text(active, 'gloss_text')}",
        "",
        "Competing senses:",
        shadow_lines or "- none",
        "",
        "Task:",
        "- write one original English sentence-frame evidence row",
        f"- include the exact trigger text `{trigger}` naturally",
        "- include at least two useful words before the trigger and at least two useful words after it when grammatical",
        f"- {target_instruction}",
        "- make the surrounding words useful for sense selection, not merely generic filler",
    ]
    if candidate_count > 1:
        lines.extend(
            [
                "",
                f"Candidate attempt: {candidate_index} of {candidate_count}.",
                f"Diversity frame: `{diversity_frame['frame_id']}`.",
                f"- {diversity_frame['directive']}",
                "- do not reuse the same opening subject, main verb, or local phrase skeleton as another attempt for this sense",
                "- prefer a different setting and supporting detail from the other planned attempts",
            ]
        )
    lines.extend(
        [
            "",
            "Rules:",
            "- write 8 to 18 English words",
            "- do not use Spanish or translation-target words",
            "- do not quote or lightly rewrite any sentence from the evaluation dataset",
            "- do not mention this prompt, senses, or labels",
            "- return JSON only",
        ]
    )
    return "\n".join(lines)


def _slot_difficulty(
    *,
    generation_target: str,
    active_pos: str,
    candidate_pos: str,
    shadow_positions: Sequence[str],
) -> str:
    normalized_active_pos = str(active_pos or "").strip().lower()
    normalized_candidate_pos = str(candidate_pos or "").strip().lower()
    if generation_target == "active_example":
        same_pos = any(
            str(shadow_pos or "").strip().lower() == normalized_active_pos
            for shadow_pos in shadow_positions
        )
    else:
        same_pos = bool(normalized_active_pos and normalized_candidate_pos == normalized_active_pos)
    return "same_pos_hard_semantic" if same_pos else "standard_semantic"


def _request_id(
    *,
    slot: Mapping[str, object],
    candidate_index: int,
    candidate_count: int,
) -> str:
    parts = [
        "en-es",
        "source-frame-gap",
        str(slot.get("generation_target") or "slot"),
        slug(slot.get("family_id")),
        slug(slot.get("candidate_sense_id")),
    ]
    if candidate_count > 1:
        parts.append(f"candidate-{candidate_index:02d}")
    return ":".join(parts)


def _expected_row_id(
    *,
    slot: Mapping[str, object],
    candidate_index: int,
    candidate_count: int,
) -> str:
    parts = [
        slug(slot.get("family_id")),
        "aligned-frame",
        slug(slot.get("generation_target")),
        slug(slot.get("candidate_sense_id")),
    ]
    if candidate_count > 1:
        parts.append(f"candidate-{candidate_index:02d}")
    return ":".join(parts)


def _families(dataset_payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    families = dataset_payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
        return []
    return [family for family in families if isinstance(family, Mapping)]


def _active_sense(family: Mapping[str, object]) -> Mapping[str, object]:
    active = family.get("active")
    return active if isinstance(active, Mapping) else {}


def _shadow_senses(family: Mapping[str, object]) -> list[Mapping[str, object]]:
    shadows = family.get("shadows")
    if not isinstance(shadows, Sequence) or isinstance(shadows, (str, bytes)):
        return []
    return [shadow for shadow in shadows if isinstance(shadow, Mapping)]


def _sense_by_id(family: Mapping[str, object], sense_id: str) -> Mapping[str, object]:
    active = _active_sense(family)
    if _sense_id(active) == sense_id:
        return active
    for shadow in _shadow_senses(family):
        if _sense_id(shadow) == sense_id:
            return shadow
    return {}


def _sense_id(sense: Mapping[str, object]) -> str:
    return str(sense.get("sense_id") or "").strip()


def _sense_text(sense: Mapping[str, object], key: str) -> str:
    views = sense.get("evidence_views")
    if isinstance(views, Mapping):
        return str(views.get(key) or "").strip()
    return ""


def _token_estimate(prompt: str) -> int:
    return max(1, (len(prompt) + 3) // 4)


def slug(value: object) -> str:
    text = str(value or "").strip().lower()
    return SLUG_RE.sub("-", text).strip("-") or "row"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan no-spend active/shadow sentence-frame source rows for selector gaps."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--alignment-audit", type=Path, default=DEFAULT_ALIGNMENT_AUDIT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument(
        "--standard-candidates-per-slot",
        type=int,
        default=DEFAULT_STANDARD_CANDIDATES_PER_SLOT,
    )
    parser.add_argument(
        "--hard-candidates-per-slot",
        type=int,
        default=DEFAULT_HARD_CANDIDATES_PER_SLOT,
    )
    args = parser.parse_args()
    args.dataset = _resolve_path(args.dataset)
    args.alignment_audit = _resolve_path(args.alignment_audit)
    args.json_out = _resolve_path(args.json_out)
    args.markdown_out = _resolve_path(args.markdown_out)
    return args


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
