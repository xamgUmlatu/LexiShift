#!/usr/bin/env python3
from __future__ import annotations

from typing import Mapping, Sequence


def system_prompt(generation_target: str) -> str:
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


def user_prompt(
    *,
    family: Mapping[str, object],
    queue_family: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    generation_target: str,
    candidate_index: int,
    candidate_count: int,
) -> str:
    trigger = str(family.get("trigger") or "").strip()
    active = _active_sense(family)
    shadows = _shadow_senses(family)
    selected_shadow_label = _selected_shadow_label(
        shadows=shadows,
        candidate_sense=candidate_sense,
    )
    shadow_lines = "\n".join(
        (
            f"- competing sense {index}: {_sense_text(shadow, 'sense_label')} | "
            f"{_sense_text(shadow, 'gloss_text')} | POS: "
            f"{str(shadow.get('canonical_pos') or '').strip() or 'unknown'}"
        )
        for index, shadow in enumerate(shadows, start=1)
    )
    base = [
        "Return a JSON object with exactly one key `items`.",
        "`items` must be an array with exactly one object.",
        "That object may contain only `evidence_text` and optional numeric `confidence`.",
        "",
        f"English trigger: `{trigger}`",
        (
            f"Active sense: {_sense_text(active, 'sense_label')} | "
            f"{_sense_text(active, 'gloss_text')} | POS: "
            f"{str(active.get('canonical_pos') or '').strip() or 'unknown'}"
        ),
        "",
        "Competing senses:",
        shadow_lines or "- none",
        "",
        "Queue context:",
        *_queue_prompt_lines(queue_family),
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
                (
                    "Competing sense details: "
                    f"{_sense_text(candidate_sense, 'sense_label')} | "
                    f"{_sense_text(candidate_sense, 'gloss_text')}"
                ),
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
    if generation_target in {"active_example", "shadow_example"} and candidate_count > 1:
        base.extend(
            [
                "",
                f"Candidate attempt: {candidate_index} of {candidate_count}.",
                "Use a distinct context, subject, and surrounding vocabulary from the other planned attempts.",
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


def _active_sense(family: Mapping[str, object]) -> Mapping[str, object]:
    active = family.get("active")
    if isinstance(active, Mapping):
        return active
    return {}


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
