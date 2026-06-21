from __future__ import annotations

import hashlib
import json
from typing import Mapping

from lexishift_core.lexicon.word_package import (
    normalize_reading,
    resolve_language_tag_from_pair,
)

CANDIDATE_IDENTITY_VERSION = "candidate_identity_v1"


def build_candidate_identity(
    *,
    language_pair: object,
    surface: object,
    reading: object = None,
    pos: object = None,
    source_provider: object = None,
    row_index: object = None,
    row_rank: object = None,
) -> dict[str, object]:
    pair = _clean_text(language_pair).lower()
    normalized_surface = _clean_text(surface)
    language_tag = resolve_language_tag_from_pair(pair)
    normalized_reading = normalize_reading(reading, language_tag=language_tag)
    normalized_pos = _clean_text(pos)
    provider = _clean_text(source_provider)
    payload: dict[str, object] = {
        "version": CANDIDATE_IDENTITY_VERSION,
        "language_pair": pair,
        "surface": normalized_surface,
    }
    if normalized_reading:
        payload["reading"] = normalized_reading
    if normalized_pos:
        payload["pos"] = normalized_pos
    if provider:
        payload["source_provider"] = provider
    normalized_row_index = _optional_int(row_index)
    if normalized_row_index is not None:
        payload["row_index"] = normalized_row_index
    normalized_row_rank = _optional_float(row_rank)
    if normalized_row_rank is not None:
        payload["row_rank"] = normalized_row_rank
    payload["key"] = _identity_key(payload)
    return payload


def candidate_identity_from_seed(seed: object) -> dict[str, object]:
    metadata = _mapping_or_empty(getattr(seed, "metadata", None))
    existing = metadata.get("candidate_identity")
    if isinstance(existing, Mapping):
        normalized = dict(existing)
        if _clean_text(normalized.get("key")):
            return normalized
    word_package = _mapping_or_empty(getattr(seed, "word_package", None))
    source = _mapping_or_empty(word_package.get("source"))
    source_provider = (
        source.get("provider") or metadata.get("source") or getattr(seed, "source_type", None)
    )
    return build_candidate_identity(
        language_pair=getattr(seed, "language_pair", None) or metadata.get("language_pair"),
        surface=word_package.get("surface") or getattr(seed, "lemma", None),
        reading=(
            word_package.get("reading")
            or word_package.get("lform_raw")
            or source.get("lform_raw")
            or metadata.get("lform_raw")
        ),
        pos=(
            word_package.get("pos_raw")
            or word_package.get("pos")
            or getattr(seed, "pos_raw", None)
            or getattr(seed, "pos", None)
            or metadata.get("pos_raw")
            or metadata.get("pos")
        ),
        source_provider=source_provider,
        row_index=word_package.get("row_index") or source.get("row_index"),
        row_rank=word_package.get("row_rank")
        or word_package.get("core_rank")
        or source.get("row_rank"),
    )


def candidate_identity_key_from_seed(seed: object) -> str:
    explicit = _clean_text(getattr(seed, "identity_key", None))
    if explicit:
        return explicit
    metadata = _mapping_or_empty(getattr(seed, "metadata", None))
    metadata_key = _clean_text(metadata.get("candidate_identity_key"))
    if metadata_key:
        return metadata_key
    return _clean_text(candidate_identity_from_seed(seed).get("key"))


def _identity_key(payload: Mapping[str, object]) -> str:
    fingerprint_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"key"} and value not in (None, "")
    }
    encoded = json.dumps(
        fingerprint_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    pair = _clean_text(fingerprint_payload.get("language_pair"))
    surface = _clean_text(fingerprint_payload.get("surface"))
    if pair and surface:
        return f"{pair}:{surface}:{digest}"
    return digest


def _mapping_or_empty(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _optional_int(value: object) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: object) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
