from __future__ import annotations

import re
from typing import Iterable, Mapping, Sequence

from lexishift_core.resources.dict_loaders import FreedictGlossRecord
from lexishift_core.rulegen.utils import sanitize_dictionary_gloss

_GRAMMATICAL_POS_HINTS = ("det", "pron", "prep", "conj", "adp", "adposition", "preposition")
_VERB_POS_HINTS = ("verb", "auxiliary", "v")
_EN_ES_MAX_SPLIT_PARTS = 8
_EN_ES_MAX_ALIAS_WORDS = 4
_EN_ES_ARTICLE_PREFIXES = ("a ", "an ", "the ")
_EN_ES_INLINE_ANNOTATION_RE = re.compile(r"\s*(?:\([^)]*\)|\[[^\]]*\]|\{[^}]*\})")


def collect_sanitized_gloss_records(
    records: Iterable[FreedictGlossRecord],
) -> list[FreedictGlossRecord]:
    cleaned: list[FreedictGlossRecord] = []
    seen: dict[str, int] = {}
    for record in records:
        normalized_pos = str(record.pos_raw or "").strip()
        variants = _expand_en_es_gloss_variants(record.translation, pos_raw=normalized_pos)
        for sanitized, variant_metadata in variants:
            if not sanitized:
                continue
            existing_index = seen.get(sanitized)
            metadata = dict(record.metadata)
            if variant_metadata:
                metadata.update(variant_metadata)
            if existing_index is None:
                cleaned.append(
                    FreedictGlossRecord(
                        translation=sanitized,
                        pos_raw=normalized_pos,
                        metadata=metadata,
                    )
                )
                seen[sanitized] = len(cleaned) - 1
                continue
            if not cleaned[existing_index].pos_raw and normalized_pos:
                cleaned[existing_index] = FreedictGlossRecord(
                    translation=sanitized,
                    pos_raw=normalized_pos,
                    metadata=cleaned[existing_index].metadata,
                )
    return cleaned


def normalize_reverse_token(value: object) -> str:
    return normalize_reverse_token_with_pos(value)


def normalize_reverse_token_with_pos(
    value: object,
    *,
    pos_raw: object = "",
) -> str:
    normalized = sanitize_dictionary_gloss(value).lower()
    if not normalized:
        return ""
    if _raw_pos_looks_verbal(pos_raw) and normalized.startswith("to "):
        stripped = normalized[3:].strip()
        if stripped:
            return stripped
    return normalized


def build_reverse_lookup(
    records_by_source: Mapping[str, Sequence[FreedictGlossRecord]],
) -> dict[str, tuple[str, ...]]:
    lookup: dict[str, tuple[str, ...]] = {}
    for raw_source, raw_records in records_by_source.items():
        source_pos_raw = next(
            (
                str(record.pos_raw or "").strip()
                for record in raw_records
                if str(record.pos_raw or "").strip()
            ),
            "",
        )
        source_norm = normalize_reverse_token_with_pos(raw_source, pos_raw=source_pos_raw)
        if not source_norm:
            continue
        ordered: list[str] = []
        seen: set[str] = set()
        for record in raw_records:
            target_norm = normalize_reverse_token(record.translation)
            if not target_norm or target_norm in seen:
                continue
            seen.add(target_norm)
            ordered.append(target_norm)
        lookup[source_norm] = tuple(ordered)
    return lookup


def _expand_en_es_gloss_variants(
    translation: object,
    *,
    pos_raw: str,
) -> list[tuple[str, dict[str, object]]]:
    input_text = str(translation or "").strip()
    sanitized = sanitize_dictionary_gloss(translation)
    if not sanitized:
        return []
    fragments = _split_en_es_gloss_fragments(sanitized, pos_raw=pos_raw)
    variants: list[tuple[str, dict[str, object]]] = []
    seen: set[str] = set()
    fragment_count = len(fragments)
    for index, fragment in enumerate(fragments):
        raw_source_text = str(fragment.get("raw_text") or "").strip()
        fragment_text = str(fragment.get("text") or "").strip()
        normalization_input = fragment_text or raw_source_text
        normalized_text, normalization_operations = _normalize_en_es_gloss_fragment(
            normalization_input
        )
        if not normalized_text or normalized_text in seen:
            continue
        raw_operations = fragment.get("operations", ())
        if isinstance(raw_operations, Sequence) and not isinstance(raw_operations, (str, bytes)):
            operations = [str(item).strip() for item in raw_operations if str(item).strip()]
        else:
            operations = []
        operations.extend(normalization_operations)
        metadata: dict[str, object] = {
            "gloss_fragment_index": index,
            "gloss_fragment_count": fragment_count,
            "gloss_fragment_strategy": str(fragment.get("strategy") or "identity"),
            "gloss_input_text": input_text,
            "gloss_raw_text": sanitized,
            "gloss_fragment_emitted_text": normalized_text,
        }
        separator = str(fragment.get("separator") or "").strip()
        if separator:
            metadata["gloss_fragment_separator"] = separator
        if raw_source_text:
            metadata["gloss_fragment_source_text"] = raw_source_text
        if operations:
            metadata["gloss_fragment_operations"] = tuple(dict.fromkeys(operations))
        if "strip_inline_annotation" in operations:
            metadata["gloss_fragment_parenthetical_stripped"] = True
        variants.append((normalized_text, metadata))
        seen.add(normalized_text)
    if variants:
        return variants
    normalized_text, normalization_operations = _normalize_en_es_gloss_fragment(sanitized)
    if not normalized_text:
        return []
    fallback_metadata: dict[str, object] = {
        "gloss_fragment_index": 0,
        "gloss_fragment_count": 1,
        "gloss_fragment_strategy": "identity",
        "gloss_input_text": input_text,
        "gloss_raw_text": sanitized,
        "gloss_fragment_emitted_text": normalized_text,
    }
    if normalization_operations:
        fallback_metadata["gloss_fragment_operations"] = normalization_operations
    if "strip_inline_annotation" in normalization_operations:
        fallback_metadata["gloss_fragment_parenthetical_stripped"] = True
    return [(normalized_text, fallback_metadata)]


def _split_en_es_gloss_fragments(text: str, *, pos_raw: str) -> list[dict[str, object]]:
    semicolon_parts = _split_top_level_fragments(text, separator=";")
    if _should_split_semicolon_fragments(semicolon_parts):
        fragments: list[dict[str, object]] = []
        for part in semicolon_parts:
            fragments.extend(_split_en_es_comma_fragments(part, pos_raw=pos_raw))
        return fragments or [
            {"raw_text": text, "text": text, "strategy": "identity", "separator": ""}
        ]
    return _split_en_es_comma_fragments(text, pos_raw=pos_raw)


def _split_en_es_comma_fragments(text: str, *, pos_raw: str) -> list[dict[str, object]]:
    comma_parts = _split_top_level_fragments(text, separator=",")
    if not _should_split_comma_fragments(comma_parts, pos_raw=pos_raw):
        return [{"raw_text": text, "text": text, "strategy": "identity", "separator": ""}]
    verb_list = _looks_like_verb_comma_gloss(comma_parts, pos_raw=pos_raw)
    prefix_infinitive = bool(comma_parts and comma_parts[0].strip().lower().startswith("to "))
    fragments: list[dict[str, object]] = []
    for part in comma_parts:
        raw_fragment_text = re.sub(r"\s+", " ", str(part or "")).strip()
        if not raw_fragment_text:
            continue
        if not _normalize_en_es_gloss_fragment(raw_fragment_text)[0]:
            continue
        fragment_text = raw_fragment_text
        operations: list[str] = []
        if verb_list and prefix_infinitive and not fragment_text.lower().startswith("to "):
            fragment_text = f"to {fragment_text}"
            operations.append("prepend_to_prefix")
        fragments.append(
            {
                "raw_text": raw_fragment_text,
                "text": fragment_text,
                "strategy": "top_level_comma",
                "separator": ",",
                "operations": tuple(operations),
            }
        )
    return fragments or [{"raw_text": text, "text": text, "strategy": "identity", "separator": ""}]


def _allows_en_es_comma_split(pos_raw: str) -> bool:
    lowered = str(pos_raw or "").strip().lower()
    return any(marker in lowered for marker in _GRAMMATICAL_POS_HINTS)


def _normalize_en_es_gloss_fragment(text: str) -> tuple[str, tuple[str, ...]]:
    raw_text = str(text or "").strip()
    if not raw_text:
        return "", ()
    operations: list[str] = []
    collapsed = re.sub(r"\s+", " ", raw_text).strip()
    if collapsed != raw_text:
        operations.append("sanitize_gloss")
    stripped = _strip_inline_gloss_annotations(collapsed)
    if stripped != collapsed:
        operations.append("strip_inline_annotation")
    normalized = sanitize_dictionary_gloss(stripped)
    if normalized:
        if normalized != stripped:
            operations.append("resanitize_gloss")
        return normalized, tuple(dict.fromkeys(operations))
    sanitized = sanitize_dictionary_gloss(collapsed)
    if sanitized:
        return sanitized, tuple(dict.fromkeys(operations))
    return "", tuple(dict.fromkeys(operations))


def _strip_inline_gloss_annotations(text: str) -> str:
    current = str(text or "").strip()
    previous = None
    while current and current != previous:
        previous = current
        current = _EN_ES_INLINE_ANNOTATION_RE.sub("", current)
        current = re.sub(r"\s+", " ", current).strip()
    return current


def _split_top_level_fragments(text: str, *, separator: str) -> list[str]:
    if not text or separator not in text:
        return [text]
    parts: list[str] = []
    buffer: list[str] = []
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    for char in text:
        if char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth > 0:
            paren_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]" and bracket_depth > 0:
            bracket_depth -= 1
        elif char == "{":
            brace_depth += 1
        elif char == "}" and brace_depth > 0:
            brace_depth -= 1
        if char == separator and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            part = "".join(buffer).strip()
            if part:
                parts.append(part)
            buffer = []
            continue
        buffer.append(char)
    tail = "".join(buffer).strip()
    if tail:
        parts.append(tail)
    return parts or [text]


def _should_split_semicolon_fragments(parts: Sequence[str]) -> bool:
    if len(parts) <= 1 or len(parts) > _EN_ES_MAX_SPLIT_PARTS:
        return False
    return all(sanitize_dictionary_gloss(part) for part in parts)


def _should_split_comma_fragments(parts: Sequence[str], *, pos_raw: str) -> bool:
    if len(parts) <= 1 or len(parts) > _EN_ES_MAX_SPLIT_PARTS:
        return False
    normalized_parts = [_normalize_en_es_gloss_fragment(part)[0] for part in parts]
    if not all(normalized_parts):
        return False
    if _allows_en_es_comma_split(pos_raw):
        return True
    if _looks_like_verb_comma_gloss(parts, pos_raw=pos_raw):
        return True
    return _looks_like_alias_gloss_list(normalized_parts)


def _looks_like_verb_comma_gloss(parts: Sequence[str], *, pos_raw: str) -> bool:
    lowered = str(pos_raw or "").strip().lower()
    if not any(marker in lowered for marker in _VERB_POS_HINTS):
        return False
    normalized_parts = [_normalize_en_es_gloss_fragment(part)[0] for part in parts]
    if not all(normalized_parts):
        return False
    if not normalized_parts[0].lower().startswith("to "):
        return False
    return all(_word_count(fragment) <= _EN_ES_MAX_ALIAS_WORDS for fragment in normalized_parts)


def _looks_like_alias_gloss_list(parts: Sequence[str]) -> bool:
    if len(parts) > 4:
        return False
    for fragment in parts:
        lowered = fragment.strip().lower()
        if not lowered:
            return False
        if lowered.startswith(_EN_ES_ARTICLE_PREFIXES):
            return False
        if _word_count(fragment) > _EN_ES_MAX_ALIAS_WORDS:
            return False
    return True


def _word_count(text: str) -> int:
    return len([token for token in str(text or "").strip().split(" ") if token])


def _raw_pos_looks_verbal(value: object) -> bool:
    lowered = str(value or "").strip().lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in _VERB_POS_HINTS)
