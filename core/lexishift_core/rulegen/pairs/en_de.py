from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Callable, Iterable, Mapping, Optional, Sequence

from lexishift_core.frequency.providers import (
    SqliteFrequencyProvider,
    SqliteFrequencyProviderConfig,
)
from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig
from lexishift_core.replacement.inflect import FORM_PLURAL, InflectionSpec
from lexishift_core.resources.dict_loaders import (
    FreedictGlossRecord,
    load_translation_gloss_records_ordered,
)
from lexishift_core.rulegen.generation import (
    CandidateNormalizer,
    CandidateFilter,
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationPipeline,
    RuleGenerationResult,
    RuleScorer,
    RuleScoringConfig,
    SimpleSignalProvider,
    build_optional_pos_match_provider,
)
from lexishift_core.rulegen.kaikki_views import build_kaikki_record_views
from lexishift_core.rulegen.pairs.en_ja import DEFAULT_STOPWORDS
from lexishift_core.rulegen.pairs.en_es_support import (
    apply_semantic_demotion as _apply_semantic_demotion,
    build_definition_bucket_key as _build_definition_bucket_key,
    build_gloss_provenance as _build_gloss_provenance,
    build_kaikki_policy_shadow_by_index as _build_kaikki_policy_shadow_by_index,
    build_target_provenance_by_index as _build_target_provenance_by_index,
    resolve_kaikki_policy_live_demotion as _resolve_kaikki_policy_live_demotion,
    resolve_kaikki_provenance_competition_demotion as _resolve_kaikki_provenance_competition_demotion,
)
from lexishift_core.rulegen.pairs.pos_utils import (
    build_candidate_pos_metadata,
    extract_target_pos_component,
    normalize_pos_component,
    resolve_target_word_package,
)
from lexishift_core.rulegen.ranking import (
    CandidateRankingContext,
    DictionaryEntryOrderRankingMechanism,
)
from lexishift_core.rulegen.semantic_demotion import (
    resolve_generic_gloss_demotion,
    resolve_pair_generic_gloss_demotions,
)
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    InflectionArtifactFilter,
    InflectionVariantExpander,
    LeadingEnglishInfinitiveNormalizer,
    LengthFilter,
    NonEmptyFilter,
    PossessiveFilter,
    PunctuationFilter,
    SingleWordFilter,
    StopwordFilter,
    sanitize_dictionary_gloss,
)
from lexishift_core.scoring.weighting import GlossDecay

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


def _should_expand_english(candidate: RuleCandidate) -> bool:
    return all(ord(ch) < 128 for ch in candidate.source_phrase)


@dataclass(frozen=True)
class EnDeRulegenConfig:
    freedict_de_en_path: Path
    gloss_mapping: Optional[Mapping[str, Sequence[str]]] = None
    gloss_records_by_target: Optional[Mapping[str, Sequence[FreedictGlossRecord]]] = None
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None
    language_pair: str = "en-de"
    source_dict_id: str = "freedict_de_en"
    dictionary_pos_source_profile: str = "freedict"
    dict_priority: float = 0.8
    confidence_threshold: float = 0.0
    max_definitions_per_target: Optional[int] = 3
    max_rules_per_target: Optional[int] = None
    interleave_definition_groups: bool = False
    sense_representative_selection: bool = False
    semantic_demotion_scale: float = 1.0
    scoring: RuleScoringConfig = field(default_factory=RuleScoringConfig)
    include_variants: bool = True
    variant_penalty: float = 0.2
    allow_multiword_glosses: bool = False
    gloss_decay: GlossDecay = GlossDecay()
    enable_punctuation_filter: bool = True
    enable_possessive_filter: bool = True
    enable_inflection_filter: bool = True
    enable_stopword_filter: bool = True
    enable_length_filter: bool = True
    min_source_length: int = 2
    max_source_length: Optional[int] = None
    stopwords: Optional[set[str]] = None
    inflection_suffixes: Sequence[str] = ("s", "es")
    inflection_forms: Sequence[str] = (FORM_PLURAL,)
    allow_hyphen: bool = True
    generic_gloss_demotions: Mapping[str, float] = field(
        default_factory=lambda: resolve_pair_generic_gloss_demotions("en-de")
    )
    enable_exact_gloss_demotions: bool = False
    enable_source_frequency_prior: bool = False
    source_frequency_db_path: Optional[Path] = None
    cleaner_later_competition_penalty: float = 0.0
    kaikki_policy: "EnDeKaikkiPolicyConfig" = field(
        default_factory=lambda: EnDeKaikkiPolicyConfig()
    )


@dataclass(frozen=True)
class EnDeKaikkiPolicyConfig:
    enable_shadow_metadata: bool = True
    enable_live_demotion: bool = False
    late_sense_clean_earlier_competition_penalty: float = 0.0
    risk_families: tuple[str, ...] = (
        "math_geometry",
        "government_law",
        "hunting_fishing_tools",
        "register_region",
        "abbreviation_ellipsis_formof",
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


@dataclass(frozen=True)
class EnDeSourceFrequencyRankingMechanism:
    fallback: DictionaryEntryOrderRankingMechanism = field(
        default_factory=DictionaryEntryOrderRankingMechanism
    )
    prior_weight: float = 0.0

    def score(self, candidate: CandidateRankingContext) -> float:
        base_score = self.fallback.score(candidate)
        if self.prior_weight <= 0.0:
            return base_score
        prior = _extract_source_frequency_prior(candidate.metadata)
        return base_score + (prior * self.prior_weight)

    def bucket_key(self, candidate: CandidateRankingContext) -> str:
        return self.fallback.bucket_key(candidate)


def build_en_de_pipeline(
    config: EnDeRulegenConfig,
    *,
    source_frequency_provider: Optional[Callable[[str], float]] = None,
) -> RuleGenerationPipeline:
    records_by_target = _resolve_gloss_records(config)
    mapping = _records_to_gloss_mapping(records_by_target)
    source = FreedictCandidateSource(
        records_by_target=records_by_target,
        source_dict=config.source_dict_id,
        source_type="translation",
        dictionary_pos_source_profile=config.dictionary_pos_source_profile,
        word_packages_by_target=config.word_packages_by_target,
        generic_gloss_demotions=(
            config.generic_gloss_demotions if config.enable_exact_gloss_demotions else {}
        ),
        source_frequency_provider=source_frequency_provider,
        cleaner_later_competition_penalty=config.cleaner_later_competition_penalty,
        sense_representative_selection=config.sense_representative_selection,
        kaikki_policy=config.kaikki_policy,
    )
    normalizers: list[CandidateNormalizer] = [
        BasicStringNormalizer(),
        LeadingEnglishInfinitiveNormalizer(),
    ]
    expanders = []
    if config.include_variants:
        expanders.append(
            InflectionVariantExpander(
                should_expand=_should_expand_english,
                spec=InflectionSpec(forms=frozenset(config.inflection_forms)),
            )
        )

    def variant_penalty_provider(candidate: RuleCandidate) -> float:
        return config.variant_penalty if candidate.metadata.get("variant") else 0.0

    def gloss_decay_weight(candidate: RuleCandidate) -> float:
        gloss_index = candidate.metadata.get("gloss_index")
        return config.gloss_decay.multiplier(gloss_index if isinstance(gloss_index, int) else None)

    frequency_provider = gloss_decay_weight
    if source_frequency_provider is not None:

        def frequency_provider(candidate: RuleCandidate) -> float:
            return _extract_source_frequency_prior(candidate.metadata) * gloss_decay_weight(
                candidate
            )

    signal_provider = SimpleSignalProvider(
        dict_priorities={"freedict_de_en": config.dict_priority},
        frequency_provider=frequency_provider,
        pos_match_provider=build_optional_pos_match_provider(config.scoring.pos_match),
        variant_penalty_provider=variant_penalty_provider,
    )
    ranking_mechanism = (
        EnDeSourceFrequencyRankingMechanism(
            prior_weight=float(config.scoring.weights.frequency_weight),
        )
        if source_frequency_provider is not None
        else DictionaryEntryOrderRankingMechanism()
    )
    return RuleGenerationPipeline(
        sources=[source],
        normalizers=normalizers,
        expanders=expanders,
        filters=_build_filters(config, mapping),
        scorer=RuleScorer(weights=config.scoring.weights),
        signal_provider=signal_provider,
        ranking_mechanism=ranking_mechanism,
    )


def generate_en_de_results(
    targets: Iterable[str],
    *,
    config: EnDeRulegenConfig,
) -> list[RuleGenerationResult]:
    source_frequency_store: Optional[SqliteFrequencyProvider] = None
    source_frequency_provider: Optional[Callable[[str], float]] = None
    if config.enable_source_frequency_prior and config.source_frequency_db_path is not None:
        source_frequency_store = SqliteFrequencyProvider(
            SqliteFrequencyProviderConfig(
                sqlite=SqliteFrequencyConfig(path=config.source_frequency_db_path)
            )
        )

        def source_frequency_provider(source_phrase: str) -> float:
            return source_frequency_store.weight_phrase(str(source_phrase), reducer="avg")

    try:
        pipeline = build_en_de_pipeline(
            config,
            source_frequency_provider=source_frequency_provider,
        )
        rule_config = RuleGenerationConfig(
            language_pair=config.language_pair,
            confidence_threshold=config.confidence_threshold,
            max_definitions_per_target=config.max_definitions_per_target,
            max_rules_per_target=config.max_rules_per_target,
            interleave_definition_groups=config.interleave_definition_groups,
            semantic_demotion_scale=config.semantic_demotion_scale,
            tags=("translation", "freedict_de_en"),
        )
        return pipeline.generate_results(targets, config=rule_config)
    finally:
        if source_frequency_store is not None:
            source_frequency_store.close()


def generate_en_de_rules(
    targets: Iterable[str],
    *,
    config: EnDeRulegenConfig,
):
    return [result.rule for result in generate_en_de_results(targets, config=config)]


class FreedictCandidateSource:
    def __init__(
        self,
        *,
        records_by_target: Mapping[str, Sequence[FreedictGlossRecord]],
        source_dict: str,
        source_type: str,
        dictionary_pos_source_profile: str = "freedict",
        word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
        generic_gloss_demotions: Optional[Mapping[str, float]] = None,
        source_frequency_provider: Optional[Callable[[str], float]] = None,
        cleaner_later_competition_penalty: float = 0.0,
        sense_representative_selection: bool = False,
        kaikki_policy: Optional[EnDeKaikkiPolicyConfig] = None,
    ) -> None:
        self._records_by_target = records_by_target
        self._source_dict = source_dict
        self._source_type = source_type
        self._dictionary_pos_source_profile = (
            str(dictionary_pos_source_profile or "").strip() or "freedict"
        )
        self._word_packages_by_target = word_packages_by_target or {}
        self._generic_gloss_demotions = dict(generic_gloss_demotions or {})
        self._source_frequency_provider = source_frequency_provider
        self._cleaner_later_competition_penalty = _normalize_competition_penalty(
            cleaner_later_competition_penalty
        )
        self._sense_representative_selection = bool(sense_representative_selection)
        self._kaikki_policy = kaikki_policy or EnDeKaikkiPolicyConfig()

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        for target in targets:
            target_word_package = resolve_target_word_package(
                target=target,
                language_pair=language_pair,
                fallback_provider="frequency",
                package_hint=self._word_packages_by_target.get(target),
            )
            target_pos = extract_target_pos_component(
                target_word_package=target_word_package,
                language_pair=language_pair,
            )
            entries = _collect_sanitized_gloss_records(self._records_by_target.get(target, ()))
            total = len(entries)
            dictionary_pos_rows = [
                normalize_pos_component(
                    entry.pos_raw,
                    language_pair=language_pair,
                    source_provider=self._source_dict,
                    source_kind="dictionary",
                    source_profile=self._dictionary_pos_source_profile,
                )
                for entry in entries
            ]
            canonical_inventory = [
                _canonical_for_competition(dictionary_pos) for dictionary_pos in dictionary_pos_rows
            ]
            dictionary_record_views_by_index = []
            for entry in entries:
                raw_record = entry.metadata if isinstance(entry.metadata, Mapping) else {}
                dictionary_record_views = build_kaikki_record_views(raw_record)
                dictionary_record_views_by_index.append(
                    {"kaikki": dictionary_record_views} if dictionary_record_views else {}
                )
            target_provenance_by_index = tuple(
                _build_target_provenance_by_index(
                    target=target,
                    entries=entries,
                    canonical_inventory=canonical_inventory,
                )
            )
            shadow_by_index = (
                _build_kaikki_policy_shadow_by_index(
                    dictionary_record_views_by_index=dictionary_record_views_by_index,
                    canonical_inventory=canonical_inventory,
                    risk_families=self._kaikki_policy.risk_families,
                )
                if self._kaikki_policy.enable_shadow_metadata
                else [{} for _ in entries]
            )
            source_frequency_priors = [
                (
                    max(0.0, float(self._source_frequency_provider(entry.translation)))
                    if self._source_frequency_provider is not None
                    else 0.0
                )
                for entry in entries
            ]
            representative_by_index = (
                _resolve_sense_representative_indexes(
                    entries=entries,
                    source_frequency_priors=source_frequency_priors,
                )
                if self._sense_representative_selection
                and self._source_frequency_provider is not None
                else {}
            )
            for index, entry in enumerate(entries):
                dictionary_pos = dictionary_pos_rows[index]
                dictionary_record_views = (
                    dictionary_record_views_by_index[index]
                    if index < len(dictionary_record_views_by_index)
                    else {}
                )
                target_provenance = (
                    target_provenance_by_index[index]
                    if index < len(target_provenance_by_index)
                    else None
                )
                metadata: dict[str, object] = {
                    "gloss_index": index,
                    "gloss_total": total,
                    "definition_bucket_key": _build_definition_bucket_key(
                        entry,
                        fallback_index=index,
                    ),
                }
                if entry.metadata:
                    metadata["dictionary_record"] = dict(entry.metadata)
                if dictionary_record_views:
                    metadata["dictionary_record_views"] = dict(dictionary_record_views)
                kaikki_family_names = _extract_kaikki_family_names(dictionary_record_views)
                if kaikki_family_names:
                    metadata["kaikki_family_names"] = kaikki_family_names
                gloss_provenance = _build_gloss_provenance(entry)
                if gloss_provenance:
                    metadata["gloss_provenance"] = gloss_provenance
                if target_provenance:
                    metadata["target_provenance"] = target_provenance
                demotion = resolve_generic_gloss_demotion(
                    entry.translation,
                    demotions=self._generic_gloss_demotions,
                )
                if demotion > 0.0:
                    _apply_semantic_demotion(
                        metadata,
                        demotion=demotion,
                        reason="generic_gloss",
                    )
                marked_demotion, marked_reasons = _resolve_en_de_marked_sense_demotion(
                    entry.metadata if isinstance(entry.metadata, Mapping) else {}
                )
                if marked_demotion > 0.0:
                    _apply_semantic_demotion(
                        metadata,
                        demotion=marked_demotion,
                        reason=";".join(marked_reasons) if marked_reasons else "marked_sense",
                    )
                if self._source_frequency_provider is not None:
                    metadata["source_frequency_prior"] = source_frequency_priors[index]
                representative_index = representative_by_index.get(index)
                if representative_index is not None:
                    representative_entry = entries[representative_index]
                    representative_prior = (
                        float(source_frequency_priors[representative_index])
                        if representative_index < len(source_frequency_priors)
                        else 0.0
                    )
                    metadata["sense_representative_selection_present"] = True
                    metadata["sense_representative_index"] = representative_index
                    metadata["sense_representative_phrase"] = str(representative_entry.translation)
                    metadata["sense_representative_prior"] = representative_prior
                    _apply_semantic_demotion(
                        metadata,
                        demotion=0.60,
                        reason="sense_representative_selection",
                    )
                if (
                    self._cleaner_later_competition_penalty > 0.0
                    and self._source_frequency_provider is not None
                ):
                    cleaner_later_index = _resolve_cleaner_later_competition(
                        current_index=index,
                        source_frequency_priors=source_frequency_priors,
                        canonical_inventory=canonical_inventory,
                    )
                    if cleaner_later_index is not None:
                        metadata["cleaner_later_competition_present"] = True
                        metadata["cleaner_later_competitor_index"] = cleaner_later_index
                        metadata["cleaner_later_competitor_phrase"] = str(
                            entries[cleaner_later_index].translation
                        )
                        metadata["cleaner_later_competitor_prior"] = float(
                            source_frequency_priors[cleaner_later_index]
                        )
                        metadata["cleaner_later_competition_penalty"] = (
                            self._cleaner_later_competition_penalty
                        )
                        _apply_semantic_demotion(
                            metadata,
                            demotion=self._cleaner_later_competition_penalty,
                            reason="cleaner_later_competition",
                        )
                shadow = shadow_by_index[index] if index < len(shadow_by_index) else {}
                if shadow:
                    _apply_kaikki_policy_overlay(
                        metadata=metadata,
                        shadow=shadow,
                        kaikki_policy=self._kaikki_policy,
                    )
                if target_word_package is not None:
                    metadata["word_package"] = target_word_package
                metadata.update(
                    build_candidate_pos_metadata(
                        source_pos=dictionary_pos,
                        target_pos=target_pos,
                        dictionary_pos=dictionary_pos,
                    )
                )
                yield RuleCandidate(
                    source_phrase=str(entry.translation),
                    replacement=str(target),
                    language_pair=language_pair,
                    source_dict=self._source_dict,
                    source_type=self._source_type,
                    metadata=metadata,
                )


def _build_filters(
    config: EnDeRulegenConfig,
    mapping: Mapping[str, Sequence[str]],
) -> list[CandidateFilter]:
    filters: list[CandidateFilter] = [NonEmptyFilter()]
    if not config.allow_multiword_glosses:
        filters.append(SingleWordFilter(allow_hyphen=config.allow_hyphen))
    if config.enable_length_filter:
        filters.append(
            LengthFilter(min_length=config.min_source_length, max_length=config.max_source_length)
        )
    if config.enable_punctuation_filter:
        filters.append(PunctuationFilter())
    if config.enable_possessive_filter:
        filters.append(PossessiveFilter())
    if config.enable_stopword_filter:
        stopwords = config.stopwords or DEFAULT_STOPWORDS
        filters.append(StopwordFilter(stopwords=stopwords))
    if config.enable_inflection_filter:
        base_forms = _build_gloss_base_forms(mapping)
        filters.append(
            InflectionArtifactFilter(
                suffixes=config.inflection_suffixes,
                base_forms=base_forms,
            )
        )
    return filters


def _build_gloss_base_forms(mapping: Mapping[str, Sequence[str]]) -> set[str]:
    base_forms: set[str] = set()
    for glosses in mapping.values():
        for gloss in glosses:
            sanitized = sanitize_dictionary_gloss(gloss).lower()
            if sanitized:
                base_forms.add(sanitized)
    return base_forms


def _resolve_gloss_records(config: EnDeRulegenConfig) -> dict[str, list[FreedictGlossRecord]]:
    if config.gloss_records_by_target is not None:
        return _coerce_gloss_records(config.gloss_records_by_target)
    if config.gloss_mapping is not None:
        return _coerce_gloss_records(config.gloss_mapping)
    return load_translation_gloss_records_ordered(
        config.freedict_de_en_path,
        target_lang="en",
    )


def _coerce_gloss_records(
    mapping: Mapping[str, Sequence[object]],
) -> dict[str, list[FreedictGlossRecord]]:
    records_by_target: dict[str, list[FreedictGlossRecord]] = {}
    for target, entries in mapping.items():
        bucket: list[FreedictGlossRecord] = []
        for entry in entries:
            if isinstance(entry, FreedictGlossRecord):
                bucket.append(entry)
                continue
            bucket.append(FreedictGlossRecord(translation=str(entry), pos_raw=""))
        records_by_target[str(target)] = bucket
    return records_by_target


def _records_to_gloss_mapping(
    records_by_target: Mapping[str, Sequence[FreedictGlossRecord]],
) -> dict[str, list[str]]:
    return {
        target: [entry.translation for entry in entries]
        for target, entries in records_by_target.items()
    }


def _collect_sanitized_gloss_records(
    records: Iterable[FreedictGlossRecord],
) -> list[FreedictGlossRecord]:
    cleaned: list[FreedictGlossRecord] = []
    seen: dict[str, int] = {}
    for record in records:
        normalized_pos = str(record.pos_raw or "").strip()
        variants = _expand_en_de_gloss_variants(record.translation, pos_raw=normalized_pos)
        for sanitized, variant_metadata in variants:
            existing_index = seen.get(sanitized)
            metadata = dict(record.metadata or {})
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
