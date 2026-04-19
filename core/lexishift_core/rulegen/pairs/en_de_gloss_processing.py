from __future__ import annotations

import re
from typing import TYPE_CHECKING, Mapping, Optional, Sequence

from lexishift_core.resources.dict_loaders import FreedictGlossRecord
from lexishift_core.rulegen.pairs.en_es_support import (
    apply_semantic_demotion as _apply_semantic_demotion,
    resolve_kaikki_policy_live_demotion as _resolve_kaikki_policy_live_demotion,
    resolve_kaikki_provenance_competition_demotion as _resolve_kaikki_provenance_competition_demotion,
)
from lexishift_core.rulegen.utils import sanitize_dictionary_gloss

if TYPE_CHECKING:
    from lexishift_core.rulegen.pairs.en_de import EnDeKaikkiPolicyConfig


_EN_DE_COMPETITION_MIN_CLEAN_PRIOR = 0.25
_EN_DE_COMPETITION_MIN_PRIOR_GAP = 0.10
_EN_DE_SENSE_REPRESENTATIVE_MIN_PRIOR_GAP = 0.05
_EN_DE_MAX_SPLIT_PARTS = 8
_EN_DE_ARTICLE_PREFIXES = ("a ", "an ", "the ")
_EN_DE_INLINE_ANNOTATION_RE = re.compile(r"\s*(?:\([^)]*\)|\[[^\]]*\]|\{[^}]*\})")
_EN_DE_SIMPLE_SLASH_VARIANT_RE = re.compile(r"^[A-Za-z]{1,8}(?:/[A-Za-z]{1,8})+$")
_EN_DE_EXPLANATORY_GLOSS_RE = re.compile(
    r"^(?:"
    r"used to\b|"
    r"separable verb prefix\b|"
    r"noun prefix\b|"
    r"the first letter of\b|"
    r"written in the latin script\b|"
    r"an intensifier\b"
    r")",
    re.IGNORECASE,
)
_EN_DE_HEAD_QUALIFIER_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"^(?P<head>[A-Za-z][A-Za-z'/-]*)\s+as\s+(?:a|an|the)\b.+$",
            re.IGNORECASE,
        ),
        "trim_head_as_qualifier",
    ),
    (
        re.compile(r"^(?P<head>[A-Za-z][A-Za-z'/-]*)\s+with\b.+$", re.IGNORECASE),
        "trim_head_with_qualifier",
    ),
    (
        re.compile(
            r"^(?P<head>[A-Za-z][A-Za-z'/-]*)\s+of\s+(?:a|an|the)\b.+$",
            re.IGNORECASE,
        ),
        "trim_head_of_qualifier",
    ),
)
_EN_DE_COLON_LABEL_RE = re.compile(
    r"^(?:"
    r"more negative also|"
    r"official name|"
    r"capital|"
    r"in full|"
    r"abbreviation of|"
    r"of a work of art|"
    r"in good condition|"
    r"specific uses include|"
    r"usually translated as"
    r")\b",
    re.IGNORECASE,
)
_EN_DE_MARKED_SENSE_TAG_DEMOTIONS: Mapping[str, float] = {
    "obsolete": 0.8,
    "archaic": 0.7,
    "dated": 0.55,
    "historical": 0.55,
    "in-compounds": 0.45,
}
_EN_DE_REGISTER_MARKERS = ("informal", "colloquial", "slang")
_EN_DE_REGION_MARKERS = (
    "regional",
    "austria",
    "austrian",
    "switzerland",
    "swiss",
    "germany",
    "northern-germany",
    "southern-germany",
    "northern german",
    "southern german",
)


def _extract_source_frequency_prior(metadata: Mapping[str, object]) -> float:
    raw = metadata.get("source_frequency_prior")
    if isinstance(raw, bool):
        return 1.0 if raw else 0.0
    if isinstance(raw, (int, float)):
        return max(0.0, min(1.0, float(raw)))
    return 0.0


def _extract_semantic_demotion(metadata: Mapping[str, object]) -> float:
    raw = metadata.get("semantic_demotion")
    if isinstance(raw, bool):
        return 1.0 if raw else 0.0
    if isinstance(raw, (int, float)):
        return max(0.0, min(1.0, float(raw)))
    return 0.0


def _extract_kaikki_family_names(dictionary_record_views: Mapping[str, object]) -> tuple[str, ...]:
    if not isinstance(dictionary_record_views, Mapping):
        return ()
    kaikki_views = dictionary_record_views.get("kaikki")
    if not isinstance(kaikki_views, Mapping):
        return ()
    combined = kaikki_views.get("combined_families")
    if isinstance(combined, Sequence) and not isinstance(combined, (str, bytes)):
        return tuple(dict.fromkeys(str(value).strip() for value in combined if str(value).strip()))
    family_fields = kaikki_views.get("family_fields")
    if isinstance(family_fields, Mapping):
        return tuple(sorted(str(key).strip() for key in family_fields if str(key).strip()))
    return ()


def _normalize_competition_penalty(value: object) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    return 0.0


def _canonical_for_competition(dictionary_pos: Optional[Mapping[str, object]]) -> str:
    if not isinstance(dictionary_pos, Mapping):
        return ""
    return str(dictionary_pos.get("canonical") or "").strip().lower()


def _resolve_cleaner_later_competition(
    *,
    current_index: int,
    source_frequency_priors: Sequence[float],
    canonical_inventory: Sequence[str],
) -> Optional[int]:
    if current_index < 0 or current_index >= len(source_frequency_priors):
        return None
    current_prior = float(source_frequency_priors[current_index])
    current_canonical = (
        canonical_inventory[current_index] if current_index < len(canonical_inventory) else ""
    )
    later_indexes = list(range(current_index + 1, len(source_frequency_priors)))
    if current_canonical:
        same_canonical = [
            candidate_index
            for candidate_index in later_indexes
            if candidate_index < len(canonical_inventory)
            and canonical_inventory[candidate_index] == current_canonical
        ]
        if same_canonical:
            later_indexes = same_canonical
    cleaner_indexes = [
        candidate_index
        for candidate_index in later_indexes
        if float(source_frequency_priors[candidate_index]) >= _EN_DE_COMPETITION_MIN_CLEAN_PRIOR
        and (float(source_frequency_priors[candidate_index]) - current_prior)
        >= _EN_DE_COMPETITION_MIN_PRIOR_GAP
    ]
    if not cleaner_indexes:
        return None
    return max(
        cleaner_indexes,
        key=lambda candidate_index: (
            float(source_frequency_priors[candidate_index]),
            -int(candidate_index),
        ),
    )


def _sense_key_for_entry(
    metadata: Mapping[str, object],
    *,
    fallback_index: int,
) -> tuple[str, object, object]:
    entry_ord = metadata.get("entry_ord")
    sense_ord = metadata.get("sense_ord")
    if entry_ord is not None or sense_ord is not None:
        return ("sense", entry_ord, sense_ord)
    return ("gloss", fallback_index, None)


def _is_headword_like_candidate(entry: FreedictGlossRecord) -> bool:
    operations = entry.metadata.get("gloss_fragment_operations")
    if isinstance(operations, Sequence) and not isinstance(operations, (str, bytes)):
        return any(str(item).strip().startswith("trim_head_") for item in operations)
    return False


def _sense_representative_score(
    entry: FreedictGlossRecord,
    *,
    source_frequency_prior: float,
    existing_demotion: float,
) -> tuple[float, float, float, float]:
    text = str(entry.translation or "").strip()
    direct_gloss_bonus = 1.0 if not _is_headword_like_candidate(entry) else 0.0
    word_length = len(text)
    length_bonus = 0.0
    if 4 <= word_length <= 8:
        length_bonus = 0.05
    elif word_length >= 12:
        length_bonus = -0.05
    return (
        direct_gloss_bonus,
        float(source_frequency_prior),
        -float(existing_demotion),
        length_bonus,
    )


def _resolve_sense_representative_indexes(
    *,
    entries: Sequence[FreedictGlossRecord],
    source_frequency_priors: Sequence[float],
) -> dict[int, int]:
    grouped_indexes: dict[tuple[str, object, object], list[int]] = {}
    for index, entry in enumerate(entries):
        metadata = entry.metadata if isinstance(entry.metadata, Mapping) else {}
        grouped_indexes.setdefault(
            _sense_key_for_entry(metadata, fallback_index=index),
            [],
        ).append(index)
    representative_by_index: dict[int, int] = {}
    for indexes in grouped_indexes.values():
        if len(indexes) <= 1:
            continue
        best_index = max(
            indexes,
            key=lambda index: (
                _sense_representative_score(
                    entries[index],
                    source_frequency_prior=(
                        float(source_frequency_priors[index])
                        if index < len(source_frequency_priors)
                        else 0.0
                    ),
                    existing_demotion=_extract_semantic_demotion(
                        entries[index].metadata
                        if isinstance(entries[index].metadata, Mapping)
                        else {}
                    ),
                ),
                -int(index),
            ),
        )
        best_prior = (
            float(source_frequency_priors[best_index])
            if best_index < len(source_frequency_priors)
            else 0.0
        )
        for index in indexes:
            if index == best_index:
                continue
            current_prior = (
                float(source_frequency_priors[index])
                if index < len(source_frequency_priors)
                else 0.0
            )
            if (best_prior - current_prior) < _EN_DE_SENSE_REPRESENTATIVE_MIN_PRIOR_GAP:
                continue
            representative_by_index[index] = best_index
    return representative_by_index


def _expand_en_de_gloss_variants(
    translation: object,
    *,
    pos_raw: str,
) -> list[tuple[str, dict[str, object]]]:
    input_text = str(translation or "").strip()
    sanitized = sanitize_dictionary_gloss(translation)
    if not sanitized:
        return []
    fragments = _split_en_de_gloss_fragments(sanitized, pos_raw=pos_raw)
    variants: list[tuple[str, dict[str, object]]] = []
    seen: set[str] = set()
    fragment_count = len(fragments)
    for index, fragment in enumerate(fragments):
        raw_source_text = str(fragment.get("raw_text") or "").strip()
        fragment_text = str(fragment.get("text") or "").strip()
        normalization_input = fragment_text or raw_source_text
        normalized_text, normalization_operations = _normalize_en_de_gloss_fragment(
            normalization_input
        )
        raw_operations = fragment.get("operations", ())
        if isinstance(raw_operations, Sequence) and not isinstance(raw_operations, (str, bytes)):
            operations = [str(item).strip() for item in raw_operations if str(item).strip()]
        else:
            operations = []
        operations.extend(normalization_operations)
        if not normalized_text:
            continue
        slash_variants = _expand_en_de_simple_slash_variants(normalized_text)
        for emitted_text, slash_operations in slash_variants:
            if not emitted_text or emitted_text in seen:
                continue
            emitted_operations = tuple(dict.fromkeys([*operations, *slash_operations]))
            metadata: dict[str, object] = {
                "gloss_fragment_index": index,
                "gloss_fragment_count": fragment_count,
                "gloss_fragment_strategy": str(fragment.get("strategy") or "identity"),
                "gloss_input_text": input_text,
                "gloss_raw_text": sanitized,
                "gloss_fragment_emitted_text": emitted_text,
            }
            separator = str(fragment.get("separator") or "").strip()
            if separator:
                metadata["gloss_fragment_separator"] = separator
            if raw_source_text:
                metadata["gloss_fragment_source_text"] = raw_source_text
            if emitted_operations:
                metadata["gloss_fragment_operations"] = emitted_operations
            if "strip_inline_annotation" in emitted_operations:
                metadata["gloss_fragment_parenthetical_stripped"] = True
            variants.append((emitted_text, metadata))
            seen.add(emitted_text)
    if variants:
        return variants
    normalized_text, normalization_operations = _normalize_en_de_gloss_fragment(sanitized)
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


def _split_en_de_gloss_fragments(text: str, *, pos_raw: str) -> list[dict[str, object]]:
    del pos_raw
    semicolon_parts = _split_top_level_fragments(text, separator=";")
    if 1 < len(semicolon_parts) <= _EN_DE_MAX_SPLIT_PARTS:
        fragments: list[dict[str, object]] = []
        for part in semicolon_parts:
            fragments.extend(_split_en_de_comma_fragments(part))
        return fragments or [
            {"raw_text": text, "text": text, "strategy": "identity", "separator": ""}
        ]
    return _split_en_de_comma_fragments(text)


def _split_en_de_comma_fragments(text: str) -> list[dict[str, object]]:
    comma_parts = _split_top_level_fragments(text, separator=",")
    if not (1 < len(comma_parts) <= _EN_DE_MAX_SPLIT_PARTS):
        return _split_en_de_colon_fragments(text)
    fragments: list[dict[str, object]] = []
    for part in comma_parts:
        raw_fragment_text = re.sub(r"\s+", " ", str(part or "")).strip()
        if not raw_fragment_text:
            continue
        colon_fragments = _split_en_de_colon_fragments(raw_fragment_text)
        for fragment in colon_fragments:
            fragment = dict(fragment)
            if str(fragment.get("strategy") or "").strip() == "identity":
                fragment["strategy"] = "top_level_comma"
                fragment["separator"] = ","
            else:
                fragment["strategy"] = f"top_level_comma+{fragment['strategy']}"
                fragment["separator"] = ","
            fragments.append(fragment)
    return fragments or _split_en_de_colon_fragments(text)


def _split_en_de_colon_fragments(text: str) -> list[dict[str, object]]:
    colon_parts = _split_top_level_colon_label_fragments(text)
    if colon_parts is None:
        return [{"raw_text": text, "text": text, "strategy": "identity", "separator": ""}]
    prefix, suffix = colon_parts
    if not _should_promote_en_de_colon_suffix(prefix=prefix, suffix=suffix):
        return [{"raw_text": text, "text": text, "strategy": "identity", "separator": ""}]
    return [
        {
            "raw_text": suffix,
            "text": suffix,
            "strategy": "top_level_colon",
            "separator": ":",
            "operations": ("extract_colon_suffix",),
        }
    ]


def _normalize_en_de_gloss_fragment(text: str) -> tuple[str, tuple[str, ...]]:
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
    dearticled = _strip_leading_english_article(stripped)
    if dearticled != stripped:
        operations.append("strip_leading_article")
    deorphaned = _strip_orphaned_gloss_delimiters(dearticled)
    if deorphaned != dearticled:
        operations.append("strip_orphaned_delimiter")
    trimmed_head, trim_operation = _trim_en_de_head_qualifier(deorphaned)
    if trim_operation:
        operations.append(trim_operation)
    if _should_drop_en_de_explanatory_gloss(trimmed_head):
        operations.append("drop_explanatory_gloss")
        return "", tuple(dict.fromkeys(operations))
    normalized = sanitize_dictionary_gloss(trimmed_head)
    if normalized:
        if normalized != trimmed_head:
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
        current = _EN_DE_INLINE_ANNOTATION_RE.sub("", current)
        current = re.sub(r"\s+", " ", current).strip()
    return current


def _strip_leading_english_article(text: str) -> str:
    current = str(text or "").strip()
    lowered = current.lower()
    for prefix in _EN_DE_ARTICLE_PREFIXES:
        if lowered.startswith(prefix) and len(current) > len(prefix):
            return current[len(prefix) :].strip()
    return current


def _strip_orphaned_gloss_delimiters(text: str) -> str:
    current = str(text or "").strip()
    previous = None
    while current and current != previous:
        previous = current
        if current.startswith("(") and current.count("(") > current.count(")"):
            current = current[1:].strip()
        if current.startswith("[") and current.count("[") > current.count("]"):
            current = current[1:].strip()
        if current.startswith("{") and current.count("{") > current.count("}"):
            current = current[1:].strip()
        if current.endswith(")") and current.count(")") > current.count("("):
            current = current[:-1].rstrip()
        if current.endswith("]") and current.count("]") > current.count("["):
            current = current[:-1].rstrip()
        if current.endswith("}") and current.count("}") > current.count("{"):
            current = current[:-1].rstrip()
        current = re.sub(r"\s+", " ", current).strip()
    return current


def _trim_en_de_head_qualifier(text: str) -> tuple[str, str]:
    current = str(text or "").strip()
    if not current:
        return "", ""
    word_count = len(current.split())
    for pattern, operation in _EN_DE_HEAD_QUALIFIER_PATTERNS:
        match = pattern.match(current)
        if match is None:
            continue
        if word_count > 6:
            continue
        head = sanitize_dictionary_gloss(match.group("head"))
        if head:
            return head, operation
    return current, ""


def _should_drop_en_de_explanatory_gloss(text: str) -> bool:
    current = str(text or "").strip()
    if not current:
        return True
    return bool(_EN_DE_EXPLANATORY_GLOSS_RE.match(current))


def _expand_en_de_simple_slash_variants(text: str) -> list[tuple[str, tuple[str, ...]]]:
    current = str(text or "").strip()
    if not current:
        return []
    if not _EN_DE_SIMPLE_SLASH_VARIANT_RE.fullmatch(current):
        return [(current, ())]
    variants: list[tuple[str, tuple[str, ...]]] = []
    seen: set[str] = set()
    for fragment in current.split("/"):
        normalized = sanitize_dictionary_gloss(fragment)
        if not normalized or normalized in seen:
            continue
        variants.append((normalized, ("split_simple_slash",)))
        seen.add(normalized)
    return variants or [(current, ())]


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


def _split_top_level_colon_label_fragments(text: str) -> Optional[tuple[str, str]]:
    current = str(text or "").strip()
    if ": " not in current:
        return None
    buffer: list[str] = []
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    for index, char in enumerate(current):
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
        if (
            char == ":"
            and paren_depth == 0
            and bracket_depth == 0
            and brace_depth == 0
            and index + 1 < len(current)
            and current[index + 1] == " "
        ):
            prefix = "".join(buffer).strip()
            suffix = current[index + 1 :].strip()
            if prefix and suffix:
                return prefix, suffix
            return None
        buffer.append(char)
    return None


def _should_promote_en_de_colon_suffix(*, prefix: str, suffix: str) -> bool:
    prefix_text = str(prefix or "").strip()
    suffix_text = str(suffix or "").strip()
    if not prefix_text or not suffix_text:
        return False
    if _EN_DE_COLON_LABEL_RE.match(prefix_text):
        return True
    prefix_words = len(prefix_text.split())
    suffix_words = len(suffix_text.split())
    return prefix_words >= 3 and suffix_words <= 6 and prefix_text.endswith("condition")


def _normalize_en_de_tag_values(values: object) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return ()
    normalized: list[str] = []
    for value in values:
        text = str(value or "").strip().lower().replace(" ", "-")
        if text and text not in normalized:
            normalized.append(text)
    return tuple(normalized)


def _collect_lowered_metadata_markers(value: object) -> tuple[str, ...]:
    markers: list[str] = []
    _visit_marker_values(value, markers)
    return tuple(markers)


def _visit_marker_values(value: object, markers: list[str]) -> None:
    if isinstance(value, str):
        text = " ".join(value.strip().lower().split())
        if text:
            markers.append(text)
        return
    if isinstance(value, Mapping):
        for item in value.values():
            _visit_marker_values(item, markers)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _visit_marker_values(item, markers)


def _resolve_en_de_marked_sense_demotion(
    metadata: Mapping[str, object],
) -> tuple[float, tuple[str, ...]]:
    tags: list[str] = []
    for key in ("sense_tags", "translation_tags", "entry_tags"):
        tags.extend(_normalize_en_de_tag_values(metadata.get(key)))
    reasons = [f"marked_sense:{tag}" for tag in tags if tag in _EN_DE_MARKED_SENSE_TAG_DEMOTIONS]
    if not reasons:
        return 0.0, ()
    demotion = max(
        _EN_DE_MARKED_SENSE_TAG_DEMOTIONS[tag.removeprefix("marked_sense:")] for tag in reasons
    )
    return demotion, tuple(dict.fromkeys(reasons))


def _resolve_en_de_kaikki_register_demotion(
    metadata: Mapping[str, object],
) -> tuple[float, tuple[str, ...]]:
    marker_payload = {
        "entry_tags": metadata.get("entry_tags"),
        "entry_categories": metadata.get("entry_categories"),
        "sense_tags": metadata.get("sense_tags"),
        "sense_topics": metadata.get("sense_topics"),
        "sense_categories": metadata.get("sense_categories"),
        "translation_tags": metadata.get("translation_tags"),
    }
    markers = _collect_lowered_metadata_markers(marker_payload)
    if not markers:
        return 0.0, ()
    register_hit = any(
        any(token in marker for token in _EN_DE_REGISTER_MARKERS) for marker in markers
    )
    region_hit = any(any(token in marker for token in _EN_DE_REGION_MARKERS) for marker in markers)
    reasons: list[str] = []
    if register_hit:
        reasons.append("kaikki_register")
    if region_hit:
        reasons.append("kaikki_region")
    if register_hit and region_hit:
        return 0.55, tuple(reasons)
    if register_hit:
        return 0.40, tuple(reasons)
    if region_hit:
        return 0.20, tuple(reasons)
    return 0.0, ()


def _apply_kaikki_policy_overlay(
    *,
    metadata: dict[str, object],
    shadow: Mapping[str, object],
    kaikki_policy: EnDeKaikkiPolicyConfig,
) -> None:
    shadow_metadata = dict(shadow)
    if kaikki_policy.enable_live_demotion:
        demotion, reasons = _resolve_kaikki_policy_live_demotion(shadow_metadata)
        if demotion > 0.0:
            _apply_semantic_demotion(
                metadata,
                demotion=demotion,
                reason=";".join(reasons) if reasons else "kaikki_policy",
            )
            shadow_metadata["live_demotion_applied"] = True
            shadow_metadata["live_demotion_value"] = demotion
            if reasons:
                shadow_metadata["live_demotion_reasons"] = reasons
    provenance_demotion, provenance_reasons = _resolve_kaikki_provenance_competition_demotion(
        target_provenance=(
            metadata.get("target_provenance")
            if isinstance(metadata.get("target_provenance"), Mapping)
            else None
        ),
        gloss_provenance=(
            metadata.get("gloss_provenance")
            if isinstance(metadata.get("gloss_provenance"), Mapping)
            else None
        ),
        shadow=shadow_metadata,
        late_sense_clean_earlier_competition_penalty=(
            kaikki_policy.late_sense_clean_earlier_competition_penalty
        ),
    )
    if provenance_demotion > 0.0:
        _apply_semantic_demotion(
            metadata,
            demotion=provenance_demotion,
            reason=(";".join(provenance_reasons) if provenance_reasons else "kaikki_provenance"),
        )
        shadow_metadata["provenance_demotion_applied"] = True
        shadow_metadata["provenance_demotion_value"] = provenance_demotion
        if provenance_reasons:
            shadow_metadata["provenance_demotion_reasons"] = provenance_reasons
    if shadow_metadata:
        metadata["kaikki_policy_shadow"] = shadow_metadata
