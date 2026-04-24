from __future__ import annotations

from hashlib import sha1
import json
import re
from typing import Mapping, Sequence


SEMANTIC_EVIDENCE_SCHEMA_VERSION = 1
SEMANTIC_EVIDENCE_NORMALIZATION_VERSION = "semantic_evidence_v1"
LLM_SOURCE_TYPE = "llm"
LLM_SOURCE_FAMILY = "silver_llm_generation"
SUPPORTED_SOURCE_TYPES = frozenset(
    {
        "llm",
        "external",
        "internal",
    }
)
SUPPORTED_SOURCE_FAMILIES = frozenset(
    {
        "silver_llm_generation",
        "internal_reviewed_dataset",
        "internal_rulegen_artifact",
        "installed_translation_pack",
        "installed_translation_pack_plus_internal_derivations",
        "installed_frequency_pack",
        "derived_embedding_probe",
        "external_structured_dictionary_dump",
        "external_sense_graph",
        "external_parallel_corpus_derivation",
        "external_example_corpus",
    }
)
SUPPORTED_RELATION_TYPES = frozenset(
    {
        "shadow_candidate",
        "bridge_candidate",
        "anchor_cue",
        "phrase_control_example",
    }
)
SUPPORTED_REVIEW_STATES = frozenset(
    {
        "unreviewed",
        "accepted",
        "rejected",
        "edited",
    }
)
SUPPORTED_PROMOTION_STATES = frozenset(
    {
        "proposed",
        "kept",
        "dropped",
        "published",
    }
)
SUPPORTED_ROLES = frozenset(
    {
        "seed",
        "candidate_generation",
        "discrimination",
        "sense_linking",
        "cue_generation",
        "phrase_containment",
    }
)

_PAIR_RE = re.compile(r"^[a-z]{2,3}-[a-z]{2,3}$")
_SENSE_HINT_TEXT_FIELDS = (
    "provider",
    "locator_kind",
    "target_key",
    "sense_label",
    "canonical_pos",
    "note",
)
_SENSE_HINT_INT_FIELDS = ("entry_ord", "sense_ord", "gloss_ord")
_SENSE_HINT_TEXT_FIELDS_SET = frozenset(_SENSE_HINT_TEXT_FIELDS)
_SENSE_HINT_INT_FIELDS_SET = frozenset(_SENSE_HINT_INT_FIELDS)


def normalize_llm_intake_batch(batch: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(batch, Mapping):
        raise ValueError("batch must be an object")
    _require_schema_version(batch)
    batch_id = _require_text(batch, "batch_id")
    pair = _require_pair(batch, "pair")
    source_type = _require_enum_text(batch, "source_type", SUPPORTED_SOURCE_TYPES)
    source_id = _require_text(batch, "source_id")
    source_family = _require_enum_text(batch, "source_family", SUPPORTED_SOURCE_FAMILIES)
    roles = _normalize_roles(batch.get("roles"))
    generated_at = _require_text(batch, "generated_at")
    ingested_at = _require_text(batch, "ingested_at")
    review_state = _normalize_review_state(batch.get("review_state"))
    model_id = _require_text(batch, "model_id")
    prompt_version = _require_text(batch, "prompt_version")
    temperature = _optional_float(batch.get("temperature"), field_name="temperature")
    cost_metadata = _normalize_json_object(batch.get("cost_metadata"))
    upstream_provenance = _normalize_json_object(batch.get("provenance"))
    items = batch.get("items")
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise ValueError("items must be a non-string array of row objects")
    if not items:
        raise ValueError("items must contain at least one row")

    batch_context = {
        "batch_id": batch_id,
        "pair": pair,
        "source_type": source_type,
        "source_id": source_id,
        "source_family": source_family,
        "roles": tuple(roles),
        "generated_at": generated_at,
        "ingested_at": ingested_at,
        "review_state": review_state,
        "model_id": model_id,
        "prompt_version": prompt_version,
        "temperature": temperature,
    }
    rows = [normalize_llm_intake_row(row, batch_context=batch_context) for row in items]

    provenance: dict[str, object] = {
        "source_type": source_type,
        "source_id": source_id,
        "source_family": source_family,
        "batch_id": batch_id,
        "model_id": model_id,
        "prompt_version": prompt_version,
        "generated_at": generated_at,
        "ingested_at": ingested_at,
        "normalization_version": SEMANTIC_EVIDENCE_NORMALIZATION_VERSION,
    }
    if temperature is not None:
        provenance["temperature"] = temperature
    if cost_metadata:
        provenance["cost_metadata"] = cost_metadata
    if upstream_provenance:
        provenance["upstream"] = upstream_provenance

    normalized: dict[str, object] = {
        "schema_version": SEMANTIC_EVIDENCE_SCHEMA_VERSION,
        "normalization_version": SEMANTIC_EVIDENCE_NORMALIZATION_VERSION,
        "batch_id": batch_id,
        "pair": pair,
        "source_type": source_type,
        "source_id": source_id,
        "source_family": source_family,
        "roles": roles,
        "generated_at": generated_at,
        "ingested_at": ingested_at,
        "review_state": review_state,
        "model_id": model_id,
        "prompt_version": prompt_version,
        "row_count": len(rows),
        "rows": rows,
        "provenance": provenance,
    }
    if temperature is not None:
        normalized["temperature"] = temperature
    if cost_metadata:
        normalized["cost_metadata"] = cost_metadata
    return normalized


def normalize_llm_intake_row(
    row: Mapping[str, object],
    *,
    batch_context: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(row, Mapping):
        raise ValueError("row must be an object")
    batch_id = str(batch_context["batch_id"])
    batch_pair = str(batch_context["pair"])
    source_type = str(batch_context["source_type"])
    source_id = str(batch_context["source_id"])
    source_family = str(batch_context["source_family"])
    batch_roles = tuple(str(role) for role in batch_context["roles"])
    batch_review_state = str(batch_context["review_state"])
    model_id = str(batch_context["model_id"])
    prompt_version = str(batch_context["prompt_version"])
    generated_at = str(batch_context["generated_at"])
    ingested_at = str(batch_context["ingested_at"])
    temperature = batch_context.get("temperature")

    row_id = _require_text(row, "row_id")
    row_pair = _optional_pair(row.get("pair"), field_name=f"row {row_id} pair") or batch_pair
    if row_pair != batch_pair:
        raise ValueError(f"row {row_id} pair {row_pair!r} does not match batch pair {batch_pair!r}")
    roles = _normalize_roles(row.get("roles"), default=batch_roles)
    relation_type = _require_enum_text(row, "relation_type", SUPPORTED_RELATION_TYPES)
    trigger = _require_text(row, "trigger", collapse=True)
    active_target = _require_text(row, "active_target", collapse=True)
    candidate_target = _require_text(row, "candidate_target", collapse=True)
    evidence_text = _require_text(row, "evidence_text", collapse=True)
    candidate_pos = _normalize_key_text(row.get("candidate_pos"))
    active_sense_hint = _normalize_sense_hint(row.get("active_sense_hint"))
    candidate_sense_hint = _normalize_sense_hint(row.get("candidate_sense_hint"))
    example_count = _optional_nonnegative_int(row.get("example_count"), field_name="example_count")
    confidence = _optional_probability(row.get("confidence"), field_name="confidence")
    review_state = _normalize_review_state(
        row.get("review_state"),
        default=batch_review_state,
    )
    promotion_state = _normalize_promotion_state(row.get("promotion_state"))
    prompt_slot = _optional_text(row.get("prompt_slot"))
    input_ref = _optional_text(row.get("input_ref"))
    raw_response_ref = _optional_text(row.get("raw_response_ref"))
    requested_runtime_publishable = _optional_bool(
        row.get("runtime_publishable"),
        field_name="runtime_publishable",
    )
    metadata = _normalize_json_object(row.get("metadata"))

    normalized_trigger = _normalize_key_text(trigger)
    normalized_active_target = _normalize_key_text(active_target)
    normalized_candidate_target = _normalize_key_text(candidate_target)
    linkage_status = _resolve_linkage_status(
        active_sense_hint=active_sense_hint,
        candidate_sense_hint=candidate_sense_hint,
    )

    evidence_id = _hash_identifier(
        {
            "batch_id": batch_id,
            "row_id": row_id,
            "pair": row_pair,
            "source_id": source_id,
            "relation_type": relation_type,
            "trigger": normalized_trigger,
            "active_target": normalized_active_target,
            "candidate_target": normalized_candidate_target,
        },
        prefix="evidence",
    )
    dedupe_key = _hash_identifier(
        {
            "pair": row_pair,
            "relation_type": relation_type,
            "trigger": normalized_trigger,
            "active_target": normalized_active_target,
            "candidate_target": normalized_candidate_target,
            "candidate_pos": _normalize_key_text(candidate_pos),
        },
        prefix="dedupe",
    )

    provenance: dict[str, object] = {
        "source_type": source_type,
        "source_id": source_id,
        "source_family": source_family,
        "batch_id": batch_id,
        "row_id": row_id,
        "model_id": model_id,
        "prompt_version": prompt_version,
        "generated_at": generated_at,
        "ingested_at": ingested_at,
        "normalization_version": SEMANTIC_EVIDENCE_NORMALIZATION_VERSION,
    }
    if temperature is not None:
        provenance["temperature"] = float(temperature)
    if prompt_slot:
        provenance["prompt_slot"] = prompt_slot
    if input_ref:
        provenance["input_ref"] = input_ref
    if raw_response_ref:
        provenance["raw_response_ref"] = raw_response_ref
    if requested_runtime_publishable is not None:
        provenance["requested_runtime_publishable"] = requested_runtime_publishable

    normalized: dict[str, object] = {
        "evidence_id": evidence_id,
        "dedupe_key": dedupe_key,
        "batch_id": batch_id,
        "row_id": row_id,
        "pair": row_pair,
        "source_type": source_type,
        "source_id": source_id,
        "source_family": source_family,
        "roles": roles,
        "relation_type": relation_type,
        "trigger": trigger,
        "normalized_trigger": normalized_trigger,
        "active_target": active_target,
        "normalized_active_target": normalized_active_target,
        "candidate_target": candidate_target,
        "normalized_candidate_target": normalized_candidate_target,
        "is_multiword": _is_multiword(trigger, active_target, candidate_target),
        "evidence_text": evidence_text,
        "review_state": review_state,
        "promotion_state": promotion_state,
        "linkage_status": linkage_status,
        "runtime_publishable": False,
        "provenance": provenance,
    }
    if active_sense_hint is not None:
        normalized["active_sense_hint"] = active_sense_hint
    if candidate_sense_hint is not None:
        normalized["candidate_sense_hint"] = candidate_sense_hint
    if candidate_pos:
        normalized["candidate_pos"] = candidate_pos
    if example_count is not None:
        normalized["example_count"] = example_count
    if confidence is not None:
        normalized["confidence"] = confidence
    if metadata:
        normalized["metadata"] = metadata
    return normalized


def _require_text(
    data: Mapping[str, object],
    key: str,
    *,
    collapse: bool = False,
) -> str:
    raw = data.get(key)
    text = _optional_text(raw, collapse=collapse)
    if not text:
        raise ValueError(f"{key} must be a non-empty string")
    return text


def _require_schema_version(data: Mapping[str, object]) -> None:
    raw = data.get("schema_version")
    if isinstance(raw, bool):
        raise ValueError("schema_version must be integer 1")
    if isinstance(raw, int):
        value = int(raw)
    elif isinstance(raw, str):
        text = raw.strip()
        if not text:
            raise ValueError("schema_version must be integer 1")
        try:
            value = int(text)
        except ValueError as exc:
            raise ValueError("schema_version must be integer 1") from exc
    else:
        raise ValueError("schema_version must be integer 1")
    if value != SEMANTIC_EVIDENCE_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SEMANTIC_EVIDENCE_SCHEMA_VERSION}")


def _optional_text(value: object, *, collapse: bool = False) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if collapse:
        return _collapse_whitespace(text)
    return text


def _require_pair(data: Mapping[str, object], key: str) -> str:
    value = _optional_pair(data.get(key), field_name=key)
    if not value:
        raise ValueError(f"{key} must be a non-empty language pair")
    return value


def _optional_pair(value: object, *, field_name: str) -> str:
    text = _optional_text(value)
    if not text:
        return ""
    if not _PAIR_RE.fullmatch(text):
        raise ValueError(f"{field_name} must match the pair format xx-yy")
    return text


def _require_enum_text(
    data: Mapping[str, object],
    key: str,
    allowed: set[str] | frozenset[str],
) -> str:
    text = _require_text(data, key)
    if text not in allowed:
        raise ValueError(f"{key} must be one of {sorted(allowed)!r}")
    return text


def _normalize_roles(
    value: object,
    *,
    default: Sequence[str] | None = None,
) -> list[str]:
    source = value if value is not None else default
    if not isinstance(source, Sequence) or isinstance(source, (str, bytes)):
        raise ValueError("roles must be a non-empty array of strings")
    normalized: list[str] = []
    for item in source:
        role = _optional_text(item)
        if not role:
            continue
        if role not in SUPPORTED_ROLES:
            raise ValueError(f"unsupported role {role!r}")
        if role not in normalized:
            normalized.append(role)
    if not normalized:
        raise ValueError("roles must contain at least one supported role")
    return normalized


def _normalize_review_state(value: object, *, default: str | None = None) -> str:
    text = _optional_text(value) or str(default or "").strip()
    if text not in SUPPORTED_REVIEW_STATES:
        raise ValueError(f"review_state must be one of {sorted(SUPPORTED_REVIEW_STATES)!r}")
    return text


def _normalize_promotion_state(value: object) -> str:
    text = _optional_text(value) or "proposed"
    if text not in SUPPORTED_PROMOTION_STATES:
        raise ValueError(f"promotion_state must be one of {sorted(SUPPORTED_PROMOTION_STATES)!r}")
    return text


def _optional_nonnegative_int(value: object, *, field_name: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if isinstance(value, int):
        resolved = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            resolved = int(text)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an integer") from exc
    else:
        raise ValueError(f"{field_name} must be an integer")
    if resolved < 0:
        raise ValueError(f"{field_name} must be >= 0")
    return resolved


def _optional_float(value: object, *, field_name: str) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be numeric") from exc
    raise ValueError(f"{field_name} must be numeric")


def _optional_probability(value: object, *, field_name: str) -> float | None:
    resolved = _optional_float(value, field_name=field_name)
    if resolved is None:
        return None
    if resolved < 0.0 or resolved > 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return resolved


def _optional_bool(value: object, *, field_name: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _normalize_sense_hint(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("sense hints must be objects")
    normalized: dict[str, object] = {}
    for field in _SENSE_HINT_TEXT_FIELDS:
        if field == "canonical_pos":
            text = _normalize_key_text(value.get(field))
        else:
            text = _optional_text(value.get(field), collapse=True)
        if text:
            normalized[field] = text
    for field in _SENSE_HINT_INT_FIELDS:
        number = _optional_nonnegative_int(value.get(field), field_name=field)
        if number is not None:
            normalized[field] = number
    metadata = _normalize_json_object(value.get("metadata"))
    extra_keys = {
        str(key): _normalize_json_value(item)
        for key, item in value.items()
        if str(key) not in _SENSE_HINT_TEXT_FIELDS_SET
        and str(key) not in _SENSE_HINT_INT_FIELDS_SET
        and str(key) != "metadata"
        and str(key).strip()
    }
    if extra_keys:
        if metadata is None:
            metadata = {}
        metadata.update(extra_keys)
    if metadata:
        normalized["metadata"] = metadata
    return normalized or None


def _normalize_json_object(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, object] = {}
    for key, item in value.items():
        text = str(key).strip()
        if not text:
            continue
        normalized[text] = _normalize_json_value(item)
    return normalized or None


def _normalize_json_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_json_value(item) for key, item in value.items() if str(key).strip()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_normalize_json_value(item) for item in value]
    return str(value)


def _collapse_whitespace(value: str) -> str:
    return " ".join(str(value or "").split())


def _normalize_key_text(value: object) -> str:
    return _collapse_whitespace(str(value or "").strip().lower())


def _hash_identifier(payload: Mapping[str, object], *, prefix: str) -> str:
    digest = sha1(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8"
        )
    ).hexdigest()
    return f"{prefix}:{digest}"


def _resolve_linkage_status(
    *,
    active_sense_hint: Mapping[str, object] | None,
    candidate_sense_hint: Mapping[str, object] | None,
) -> str:
    if active_sense_hint or candidate_sense_hint:
        return "partially_linked"
    return "unlinked"


def _is_multiword(*values: str) -> bool:
    for value in values:
        if len(_collapse_whitespace(value).split()) > 1:
            return True
    return False
