from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch
from lexishift_core.rulegen.semantic_routing_runtime_scoring import (
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    build_runtime_context_views,
)
from semantic_routing_sentence_veto_helpers import _normalize_string_list


ACTIVE_RELATION_TYPES = frozenset({"anchor_cue"})
SHADOW_RELATION_TYPES = frozenset({"shadow_candidate", "bridge_candidate"})
PHRASE_RELATION_TYPES = frozenset({"phrase_control_example"})


def normalize_evidence_batch_payload(batch_payload: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(batch_payload, Mapping):
        raise ValueError("Batch payload must be a JSON object.")
    if isinstance(batch_payload.get("rows"), Sequence) and not isinstance(
        batch_payload.get("rows"), (str, bytes)
    ):
        return dict(batch_payload)
    if isinstance(batch_payload.get("items"), Sequence) and not isinstance(
        batch_payload.get("items"), (str, bytes)
    ):
        return normalize_llm_intake_batch(batch_payload)
    raise ValueError("Batch must contain either normalized `rows` or raw intake `items`.")


def build_example_frame_lookup(
    batch_payload: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    normalized_batch = normalize_evidence_batch_payload(batch_payload)
    lookup: dict[str, dict[str, object]] = {}
    for row in normalized_batch.get("rows", ()):
        if not isinstance(row, Mapping):
            continue
        family_key = row_family_key(row)
        if not family_key:
            continue
        family_entry = lookup.setdefault(
            family_key,
            {
                "active_examples": [],
                "shadow_examples_by_sense": {},
                "phrase_examples": [],
            },
        )
        relation_type = str(row.get("relation_type") or "").strip()
        evidence_text = str(row.get("evidence_text") or "").strip()
        if not evidence_text:
            continue
        if relation_type in ACTIVE_RELATION_TYPES:
            _append_unique(family_entry["active_examples"], evidence_text)
        elif relation_type in SHADOW_RELATION_TYPES:
            sense_id = row_sense_id(row, "candidate_sense_hint")
            if sense_id:
                shadow_lookup = family_entry["shadow_examples_by_sense"]
                if isinstance(shadow_lookup, dict):
                    _append_unique(shadow_lookup.setdefault(sense_id, []), evidence_text)
        elif relation_type in PHRASE_RELATION_TYPES:
            _append_unique(family_entry["phrase_examples"], evidence_text)
    return lookup


def row_family_key(row: Mapping[str, object]) -> str:
    family_id = row_metadata_text(row, "family_id")
    if family_id:
        return family_id
    active_sense = row.get("active_sense_hint")
    if isinstance(active_sense, Mapping):
        target_key = str(active_sense.get("target_key") or "").strip()
        if target_key:
            return target_key
    trigger = str(row.get("normalized_trigger") or row.get("trigger") or "").strip()
    active = str(row.get("normalized_active_target") or row.get("active_target") or "").strip()
    return f"{trigger}:{active}" if trigger or active else "unknown"


def row_sense_id(row: Mapping[str, object], hint_key: str) -> str:
    metadata_key = "active_sense_id" if hint_key == "active_sense_hint" else "candidate_sense_id"
    metadata_value = row_metadata_text(row, metadata_key)
    if metadata_value:
        return metadata_value
    hint = row.get(hint_key)
    if isinstance(hint, Mapping):
        return str(hint.get("target_key") or "").strip()
    return ""


def row_metadata_text(row: Mapping[str, object], key: str) -> str:
    metadata = row.get("metadata")
    if not isinstance(metadata, Mapping):
        return ""
    return str(metadata.get(key) or "").strip()


def row_roles(row: Mapping[str, object]) -> set[str]:
    roles = row.get("roles")
    if isinstance(roles, Sequence) and not isinstance(roles, (str, bytes)):
        return {str(role).strip() for role in roles if str(role).strip()}
    return set()


def active_examples_for_family(
    family: Mapping[str, object],
    lookup: Mapping[str, Mapping[str, object]] | None,
    *,
    context_view: str = "masked_sentence",
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> list[str]:
    if lookup is None:
        active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
        return reviewed_examples_for_sense(
            family,
            sense_id=sense_id(active),
            context_view=context_view,
            window_tokens=window_tokens,
            mask_token=mask_token,
        )
    return _lookup_text_list(family, lookup, "active_examples")


def phrase_examples_for_family(
    family: Mapping[str, object],
    lookup: Mapping[str, Mapping[str, object]] | None,
    *,
    context_view: str = "masked_sentence",
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> list[str]:
    if lookup is None:
        return reviewed_phrase_examples_for_family(
            family,
            context_view=context_view,
            window_tokens=window_tokens,
            mask_token=mask_token,
        )
    return _lookup_text_list(family, lookup, "phrase_examples")


def shadow_examples_for_sense(
    family: Mapping[str, object],
    *,
    sense_id: str,
    lookup: Mapping[str, Mapping[str, object]] | None,
    context_view: str = "masked_sentence",
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> list[str]:
    if lookup is None:
        return reviewed_examples_for_sense(
            family,
            sense_id=sense_id,
            context_view=context_view,
            window_tokens=window_tokens,
            mask_token=mask_token,
        )
    family_entry = lookup.get(_dataset_family_key(family))
    if not isinstance(family_entry, Mapping):
        return []
    shadow_lookup = family_entry.get("shadow_examples_by_sense")
    if not isinstance(shadow_lookup, Mapping):
        return []
    values = shadow_lookup.get(str(sense_id or "").strip())
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        return [str(value).strip() for value in values if str(value).strip()]
    return []


def shadow_example_pairs_for_family(
    family: Mapping[str, object],
    shadows: Sequence[Mapping[str, object]],
    lookup: Mapping[str, Mapping[str, object]] | None,
    *,
    context_view: str = "masked_sentence",
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> list[tuple[Mapping[str, object], str]]:
    pairs: list[tuple[Mapping[str, object], str]] = []
    for shadow in shadows:
        examples = shadow_examples_for_sense(
            family,
            sense_id=sense_id(shadow),
            lookup=lookup,
            context_view=context_view,
            window_tokens=window_tokens,
            mask_token=mask_token,
        )
        pairs.extend((shadow, example) for example in examples)
    return pairs


def reviewed_examples_for_sense(
    family: Mapping[str, object],
    *,
    sense_id: str,
    context_view: str = "masked_sentence",
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> list[str]:
    examples: list[str] = []
    trigger = str(family.get("trigger") or "").strip()
    for case in family.get("cases", ()):
        if not isinstance(case, Mapping):
            continue
        if str(case.get("gold_winner") or "").strip() != sense_id:
            continue
        if "phrase_control" in _normalize_string_list(case.get("slice_tags")):
            continue
        example = case_context_text(
            case,
            trigger=trigger,
            context_view=context_view,
            window_tokens=window_tokens,
            mask_token=mask_token,
        )
        if example and example not in examples:
            examples.append(example)
    return examples[:2]


def reviewed_phrase_examples_for_family(
    family: Mapping[str, object],
    *,
    context_view: str = "masked_sentence",
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> list[str]:
    examples: list[str] = []
    trigger = str(family.get("trigger") or "").strip()
    for case in family.get("cases", ()):
        if not isinstance(case, Mapping):
            continue
        if (
            "phrase_control" not in _normalize_string_list(case.get("slice_tags"))
            and str(case.get("gold_winner") or "").strip() != "none"
        ):
            continue
        example = case_context_text(
            case,
            trigger=trigger,
            context_view=context_view,
            window_tokens=window_tokens,
            mask_token=mask_token,
        )
        if example and example not in examples:
            examples.append(example)
    return examples[:2]


def case_context_text(
    case: Mapping[str, object],
    *,
    trigger: str,
    context_view: str = "masked_sentence",
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> str:
    context_views = build_runtime_context_views(
        str(case.get("sentence") or "").strip(),
        source_phrase=str(case.get("source_phrase") or trigger).strip(),
        mask_token=mask_token,
        window_tokens=window_tokens,
    )
    resolved_context_view = str(context_view or "").strip() or "masked_sentence"
    return str(
        context_views.get(resolved_context_view) or context_views.get("masked_sentence") or ""
    ).strip()


def sense_id(sense: Mapping[str, object]) -> str:
    return str(sense.get("sense_id") or "").strip()


def _lookup_text_list(
    family: Mapping[str, object],
    lookup: Mapping[str, Mapping[str, object]],
    key: str,
) -> list[str]:
    family_entry = lookup.get(_dataset_family_key(family))
    if not isinstance(family_entry, Mapping):
        return []
    values = family_entry.get(key)
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        return [str(value).strip() for value in values if str(value).strip()]
    return []


def _dataset_family_key(family: Mapping[str, object]) -> str:
    return str(family.get("family_id") or "").strip()


def _append_unique(values: object, text: str) -> None:
    if not isinstance(values, list):
        return
    if text and text not in values:
        values.append(text)
