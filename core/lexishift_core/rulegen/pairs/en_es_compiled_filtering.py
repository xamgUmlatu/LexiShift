from __future__ import annotations

from dataclasses import dataclass, field, replace
import re
from typing import TYPE_CHECKING, Mapping, Optional, Sequence

from lexishift_core.rulegen.pairs.en_es_compiled_inventory import (
    EnEsCompiledCandidateTable,
    EnEsCompiledResources,
)
from lexishift_core.rulegen.pairs.en_ja import DEFAULT_STOPWORDS

if TYPE_CHECKING:
    from lexishift_core.rulegen.pairs.en_es import EnEsRulegenConfig


_EN_ES_SINGLE_WORD_RE = re.compile(r"^[a-z0-9-]+$")
_EN_ES_MULTIWORD_RE = re.compile(r"^[a-z0-9-]+(?: [a-z0-9-]+){0,3}$")
_FUNCTION_WORD_CANONICALS = frozenset(
    {
        "determiner",
        "pronoun",
        "adposition",
        "conjunction",
    }
)
_DEFAULT_STOPWORDS_FROZEN = frozenset(DEFAULT_STOPWORDS)
_COMPILED_FILTER_TABLE_CACHE: dict[
    tuple[int, tuple[object, ...]],
    "EnEsCompiledCandidateFilterTable",
] = {}


@dataclass(frozen=True)
class EnEsCompiledCandidateFilterTable:
    candidate_ids: tuple[int, ...] = ()
    target_ids: tuple[int, ...] = ()
    normalized_source_phrases: tuple[str, ...] = ()
    definition_group_ids: tuple[int, ...] = ()
    non_empty_flags: tuple[bool, ...] = ()
    gloss_shape_flags: tuple[bool, ...] = ()
    length_flags: tuple[bool, ...] = ()
    possessive_flags: tuple[bool, ...] = ()
    shadowed_interjection_flags: tuple[bool, ...] = ()
    stopword_flags: tuple[bool, ...] = ()
    inflection_artifact_flags: tuple[bool, ...] = ()
    accepted_flags: tuple[bool, ...] = ()
    selected_row_signature: tuple[object, ...] = ()
    accepted_candidate_row_ids_by_target_id: Mapping[int, tuple[int, ...]] = field(
        default_factory=dict
    )
    accepted_candidate_row_id_groups_by_target_id: Mapping[int, tuple[tuple[int, ...], ...]] = (
        field(default_factory=dict)
    )


def build_en_es_compiled_candidate_filter_table(
    *,
    compiled_resources: EnEsCompiledResources,
    config: EnEsRulegenConfig,
) -> EnEsCompiledCandidateFilterTable:
    candidate_table = compiled_resources.candidate_table
    return _build_compiled_candidate_filter_table_for_table(
        compiled_resources=compiled_resources,
        candidate_table=candidate_table,
        candidate_table_cache_token=("base", int(compiled_resources.cache_token)),
        config=config,
    )


def _build_compiled_candidate_filter_table_for_table(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table: Optional[EnEsCompiledCandidateTable],
    candidate_table_cache_token: object,
    config: EnEsRulegenConfig,
) -> EnEsCompiledCandidateFilterTable:
    if candidate_table is None:
        return EnEsCompiledCandidateFilterTable()
    cache_key = _build_compiled_filter_table_cache_key(
        compiled_resources=compiled_resources,
        candidate_table_cache_token=candidate_table_cache_token,
        config=config,
    )
    cached = _COMPILED_FILTER_TABLE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    stopwords = set(config.stopwords or DEFAULT_STOPWORDS)
    gloss_base_forms = set(compiled_resources.gloss_base_forms)
    normalized_source_phrases: list[str] = []
    definition_group_ids: list[int] = []
    non_empty_flags: list[bool] = []
    gloss_shape_flags: list[bool] = []
    length_flags: list[bool] = []
    possessive_flags: list[bool] = []
    shadowed_interjection_flags: list[bool] = []
    stopword_flags: list[bool] = []
    inflection_artifact_flags: list[bool] = []
    accepted_flags: list[bool] = []
    accepted_candidate_row_ids_by_target_id: dict[int, list[int]] = {}
    accepted_candidate_row_id_groups_by_target_id: dict[int, dict[str, list[int]]] = {}
    accepted_candidate_row_group_order_by_target_id: dict[int, list[str]] = {}
    definition_group_id_by_key: dict[tuple[str, object], int] = {}
    for row_id, candidate_id in enumerate(candidate_table.candidate_ids):
        normalized_phrase = candidate_table.normalized_source_phrases[row_id]
        normalized_source_phrases.append(normalized_phrase)
        definition_bucket_id = int(candidate_table.definition_bucket_ids[row_id])
        definition_group_key: tuple[str, object]
        if definition_bucket_id >= 0:
            definition_group_key = ("definition_bucket_id", definition_bucket_id)
        else:
            definition_group_key = (
                "source_phrase",
                str(normalized_phrase or "").strip().lower(),
            )
        definition_group_ids.append(
            int(
                definition_group_id_by_key.setdefault(
                    definition_group_key,
                    len(definition_group_id_by_key),
                )
            )
        )
        allows_function_word_phrase = (
            candidate_table.dictionary_pos_canonicals[row_id] in _FUNCTION_WORD_CANONICALS
        )
        non_empty_ok = _compiled_non_empty_accepts(normalized_phrase)
        gloss_shape_ok = _compiled_gloss_shape_accepts(
            normalized_phrase,
            allow_hyphen=config.allow_hyphen,
            allow_multiword_glosses=config.allow_multiword_glosses,
            allows_function_word_phrase=allows_function_word_phrase,
        )
        length_ok = (
            _compiled_length_accepts(
                normalized_phrase,
                min_length=config.min_source_length,
                max_length=config.max_source_length,
            )
            if config.enable_length_filter
            else True
        )
        possessive_ok = (
            _compiled_possessive_accepts(normalized_phrase)
            if config.enable_possessive_filter
            else True
        )
        shadow_ok = not candidate_table.interjection_shadowed_flags[row_id]
        stopword_ok = (
            _compiled_stopword_accepts(
                normalized_phrase,
                stopwords=stopwords,
                allows_function_word_phrase=allows_function_word_phrase,
            )
            if config.enable_stopword_filter
            else True
        )
        inflection_ok = (
            _compiled_inflection_artifact_accepts(
                normalized_phrase,
                base_forms=gloss_base_forms,
                suffixes=config.inflection_suffixes,
            )
            if config.enable_inflection_filter
            else True
        )
        accepted = (
            non_empty_ok
            and gloss_shape_ok
            and length_ok
            and possessive_ok
            and shadow_ok
            and stopword_ok
            and inflection_ok
        )
        non_empty_flags.append(non_empty_ok)
        gloss_shape_flags.append(gloss_shape_ok)
        length_flags.append(length_ok)
        possessive_flags.append(possessive_ok)
        shadowed_interjection_flags.append(shadow_ok)
        stopword_flags.append(stopword_ok)
        inflection_artifact_flags.append(inflection_ok)
        accepted_flags.append(accepted)
        if accepted:
            target_id = int(candidate_table.target_ids[row_id])
            accepted_candidate_row_ids_by_target_id.setdefault(target_id, []).append(row_id)
            group_key = str(normalized_phrase or "").strip().lower()
            groups_by_key = accepted_candidate_row_id_groups_by_target_id.setdefault(
                target_id,
                {},
            )
            if group_key not in groups_by_key:
                accepted_candidate_row_group_order_by_target_id.setdefault(target_id, []).append(
                    group_key
                )
                groups_by_key[group_key] = []
            groups_by_key[group_key].append(row_id)
    filter_table = EnEsCompiledCandidateFilterTable(
        candidate_ids=tuple(int(candidate_id) for candidate_id in candidate_table.candidate_ids),
        target_ids=tuple(int(target_id) for target_id in candidate_table.target_ids),
        normalized_source_phrases=tuple(normalized_source_phrases),
        definition_group_ids=tuple(definition_group_ids),
        non_empty_flags=tuple(non_empty_flags),
        gloss_shape_flags=tuple(gloss_shape_flags),
        length_flags=tuple(length_flags),
        possessive_flags=tuple(possessive_flags),
        shadowed_interjection_flags=tuple(shadowed_interjection_flags),
        stopword_flags=tuple(stopword_flags),
        inflection_artifact_flags=tuple(inflection_artifact_flags),
        accepted_flags=tuple(accepted_flags),
        accepted_candidate_row_ids_by_target_id={
            key: tuple(value)
            for key, value in sorted(accepted_candidate_row_ids_by_target_id.items())
        },
        accepted_candidate_row_id_groups_by_target_id={
            key: tuple(
                tuple(groups_by_key[group_key])
                for group_key in accepted_candidate_row_group_order_by_target_id.get(key, [])
            )
            for key, groups_by_key in sorted(accepted_candidate_row_id_groups_by_target_id.items())
        },
    )
    filter_table = replace(
        filter_table,
        selected_row_signature=_build_compiled_filter_selected_row_signature(
            filter_table=filter_table
        ),
    )
    _COMPILED_FILTER_TABLE_CACHE[cache_key] = filter_table
    return filter_table


def _build_compiled_filter_table_cache_key(
    *,
    compiled_resources: EnEsCompiledResources,
    candidate_table_cache_token: object | None = None,
    config: EnEsRulegenConfig,
) -> tuple[int, tuple[object, ...]]:
    return (
        int(compiled_resources.cache_token),
        (
            (
                candidate_table_cache_token
                if candidate_table_cache_token is not None
                else ("base", int(compiled_resources.cache_token))
            ),
            bool(config.allow_hyphen),
            bool(config.allow_multiword_glosses),
            bool(config.enable_length_filter),
            int(config.min_source_length),
            (None if config.max_source_length is None else int(config.max_source_length)),
            bool(config.enable_possessive_filter),
            bool(config.enable_stopword_filter),
            (
                frozenset(str(stopword).strip().lower() for stopword in config.stopwords)
                if config.stopwords is not None
                else _DEFAULT_STOPWORDS_FROZEN
            ),
            bool(config.enable_inflection_filter),
            tuple(str(suffix) for suffix in config.inflection_suffixes),
        ),
    )


def _build_compiled_filter_selected_row_signature(
    *,
    filter_table: EnEsCompiledCandidateFilterTable,
) -> tuple[object, ...]:
    return (
        tuple(
            (
                int(target_id),
                tuple(tuple(int(row_id) for row_id in row_group) for row_group in groups),
            )
            for target_id, groups in sorted(
                filter_table.accepted_candidate_row_id_groups_by_target_id.items()
            )
        ),
        tuple(int(group_id) for group_id in filter_table.definition_group_ids),
        tuple(str(source_phrase) for source_phrase in filter_table.normalized_source_phrases),
    )


def _compiled_non_empty_accepts(source_phrase: str) -> bool:
    text = str(source_phrase or "").strip()
    if len(text) < 1:
        return False
    return bool(re.search(r"\w", text))


def _compiled_gloss_shape_accepts(
    source_phrase: str,
    *,
    allow_hyphen: bool,
    allow_multiword_glosses: bool,
    allows_function_word_phrase: bool,
) -> bool:
    phrase = str(source_phrase or "").strip().lower()
    if not phrase:
        return False
    if not allow_hyphen and "-" in phrase:
        return False
    if allow_multiword_glosses or allows_function_word_phrase:
        return bool(_EN_ES_MULTIWORD_RE.fullmatch(phrase))
    return bool(_EN_ES_SINGLE_WORD_RE.fullmatch(phrase))


def _compiled_length_accepts(
    source_phrase: str,
    *,
    min_length: int,
    max_length: Optional[int],
) -> bool:
    text = str(source_phrase or "").strip()
    if len(text) < int(min_length):
        return False
    if max_length is not None and len(text) > int(max_length):
        return False
    return True


def _compiled_possessive_accepts(source_phrase: str) -> bool:
    phrase = str(source_phrase or "").strip()
    return not any(phrase.endswith(suffix) for suffix in ("'s", "’s"))


def _compiled_stopword_accepts(
    source_phrase: str,
    *,
    stopwords: set[str],
    allows_function_word_phrase: bool,
) -> bool:
    phrase = str(source_phrase or "").strip().lower()
    if phrase not in stopwords:
        return True
    return allows_function_word_phrase


def _compiled_inflection_artifact_accepts(
    source_phrase: str,
    *,
    base_forms: set[str],
    suffixes: Sequence[str],
    min_base_length: int = 2,
) -> bool:
    phrase = str(source_phrase or "").strip()
    if not base_forms:
        return True
    for suffix in suffixes:
        normalized_suffix = str(suffix or "")
        if not normalized_suffix or not phrase.endswith(normalized_suffix):
            continue
        base = phrase[: -len(normalized_suffix)]
        if len(base) < int(min_base_length):
            continue
        if base in base_forms:
            return False
    return True
