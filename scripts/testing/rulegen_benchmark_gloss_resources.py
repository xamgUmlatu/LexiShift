from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.resources.dict_loaders import (
    TranslationGlossRecord,
    load_translation_gloss_base_forms,
    load_translation_gloss_records_ordered,
    load_translation_headwords,
)
from lexishift_core.rulegen.generation import RuleCandidate
from lexishift_core.rulegen.pairs.en_es import build_en_es_compiled_resources
from lexishift_core.rulegen.pairs.en_es_support import (
    collect_sanitized_gloss_records,
    normalize_reverse_token_with_pos,
)
from lexishift_core.rulegen.utils import (
    BasicStringNormalizer,
    LeadingEnglishInfinitiveNormalizer,
    PairedInflectionVariantExpander,
    sanitize_dictionary_gloss,
)


def translation_target_lang_for_pair(pair: str) -> Optional[str]:
    normalized = str(pair or "").strip().lower()
    return {
        "en-de": "en",
        "en-es": "en",
        "es-en": "es",
    }.get(normalized)


def reverse_translation_target_lang_for_pair(pair: str) -> Optional[str]:
    normalized = str(pair or "").strip().lower()
    return {
        "en-es": "es",
        "es-en": "en",
    }.get(normalized)


def load_translation_gloss_records(
    path: Optional[Path],
    *,
    target_lang: Optional[str],
    headwords: Optional[Sequence[str]] = None,
) -> Optional[dict[str, list[TranslationGlossRecord]]]:
    if path is None or target_lang is None:
        return None
    if not path.exists():
        return None
    return load_translation_gloss_records_ordered(
        path,
        target_lang=target_lang,
        headwords=headwords,
    )


def build_reverse_preload_headwords(
    *,
    pair: str,
    forward_records_by_target: Optional[Mapping[str, Sequence[TranslationGlossRecord]]],
) -> Optional[tuple[str, ...]]:
    normalized_pair = str(pair or "").strip().lower()
    if normalized_pair != "en-es" or not forward_records_by_target:
        return None
    normalizers = (BasicStringNormalizer(), LeadingEnglishInfinitiveNormalizer())
    expander = PairedInflectionVariantExpander(target_surface_resolver=None)
    headwords: set[str] = set()
    for raw_records in forward_records_by_target.values():
        for record in collect_sanitized_gloss_records(raw_records):
            raw_translation = str(record.translation or "").strip()
            if not raw_translation:
                continue
            sanitized = sanitize_dictionary_gloss(raw_translation).lower()
            if sanitized:
                headwords.add(sanitized)
            normalized_reverse = normalize_reverse_token_with_pos(
                raw_translation,
                pos_raw=record.pos_raw,
            )
            if normalized_reverse:
                headwords.add(normalized_reverse)
            candidate = RuleCandidate(
                source_phrase=raw_translation,
                replacement="",
                language_pair="en-es",
                source_dict="benchmark-preload",
                metadata={},
            )
            normalized_candidate = candidate
            for normalizer in normalizers:
                normalized_candidate = normalizer.normalize(normalized_candidate)
            normalized_phrase = str(normalized_candidate.source_phrase or "").strip().lower()
            if normalized_phrase:
                headwords.add(normalized_phrase)
                if all(ord(ch) < 128 for ch in normalized_phrase):
                    for expanded in expander.expand(normalized_candidate):
                        expanded_phrase = str(expanded.source_phrase or "").strip().lower()
                        if expanded_phrase:
                            headwords.add(expanded_phrase)
    return tuple(sorted(headwords))


def expand_reverse_preload_headwords(
    *,
    pair: str,
    reverse_translation_dict_path: Optional[Path],
    reverse_headwords: Optional[Sequence[str]],
    load_reverse_headword_norm_index,
) -> Optional[tuple[str, ...]]:
    normalized_pair = str(pair or "").strip().lower()
    if normalized_pair != "en-es" or reverse_headwords is None:
        return tuple(reverse_headwords) if reverse_headwords is not None else None
    if reverse_translation_dict_path is None or not reverse_translation_dict_path.exists():
        return tuple(reverse_headwords)
    wanted = {
        str(headword or "").strip().lower()
        for headword in reverse_headwords
        if str(headword or "").strip()
    }
    if not wanted:
        return ()
    expanded = set(wanted)
    normalized_index = load_reverse_headword_norm_index(reverse_translation_dict_path)
    for desired_headword in wanted:
        expanded.update(normalized_index.get(desired_headword, ()))
    return tuple(sorted(expanded))


def collect_en_es_reverse_headword_forms(raw_headword: str) -> tuple[str, ...]:
    normalizers = (BasicStringNormalizer(), LeadingEnglishInfinitiveNormalizer())
    normalized_forms: list[str] = []
    seen: set[str] = set()

    def add(text: object) -> None:
        normalized = str(text or "").strip().lower()
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        normalized_forms.append(normalized)

    add(raw_headword)
    add(sanitize_dictionary_gloss(raw_headword))
    add(normalize_reverse_token_with_pos(raw_headword))
    candidate = RuleCandidate(
        source_phrase=raw_headword,
        replacement="",
        language_pair="en-es",
        source_dict="benchmark-preload",
        metadata={},
    )
    normalized_candidate = candidate
    for normalizer in normalizers:
        normalized_candidate = normalizer.normalize(normalized_candidate)
    add(normalized_candidate.source_phrase)
    return tuple(normalized_forms)


def build_en_es_reverse_headword_norm_index(
    reverse_translation_dict_path: Path,
) -> dict[str, tuple[str, ...]]:
    raw_headwords_by_normalized: dict[str, list[str]] = {}
    for raw_headword in load_translation_headwords(reverse_translation_dict_path):
        raw_text = str(raw_headword or "").strip()
        if not raw_text:
            continue
        raw_lower = raw_text.lower()
        for normalized in collect_en_es_reverse_headword_forms(raw_text):
            bucket = raw_headwords_by_normalized.setdefault(normalized, [])
            if raw_lower not in bucket:
                bucket.append(raw_lower)
    return {
        normalized: tuple(raw_headwords)
        for normalized, raw_headwords in sorted(raw_headwords_by_normalized.items())
    }


def path_looks_kaikki(path: Optional[Path]) -> bool:
    if path is None:
        return False
    name = path.name.strip().lower()
    return "wiktionary" in name or "kaikki" in name


def build_pair_compiled_rulegen_context(
    *,
    pair: str,
    targets: Sequence[str],
    translation_dict_path: Optional[Path],
    reverse_translation_dict_path: Optional[Path],
    gloss_records_by_target: Optional[Mapping[str, Sequence[TranslationGlossRecord]]],
    reverse_gloss_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]],
    word_packages_by_target: Mapping[str, Mapping[str, object]],
    gloss_base_forms: Optional[Sequence[str]] = None,
) -> Optional[object]:
    normalized_pair = str(pair or "").strip().lower()
    if normalized_pair != "en-es":
        return None
    if gloss_records_by_target is None:
        return None
    source_dict = (
        "wiktionary_es_en" if path_looks_kaikki(translation_dict_path) else "freedict_es_en"
    )
    dictionary_pos_source_profile = (
        "wiktionary" if path_looks_kaikki(translation_dict_path) else "freedict"
    )
    return build_en_es_compiled_resources(
        targets=targets,
        records_by_target=gloss_records_by_target,
        reverse_records_by_source=reverse_gloss_records_by_source,
        word_packages_by_target=word_packages_by_target,
        language_pair=normalized_pair,
        source_dict=source_dict,
        dictionary_pos_source_profile=dictionary_pos_source_profile,
        gloss_base_forms_override=gloss_base_forms,
    )


def load_gloss_base_forms_for_pair(
    *,
    pair: str,
    translation_dict_path: Optional[Path],
) -> Optional[tuple[str, ...]]:
    target_lang = translation_target_lang_for_pair(pair)
    if translation_dict_path is None or target_lang is None:
        return None
    return tuple(
        sorted(
            load_translation_gloss_base_forms(
                translation_dict_path,
                target_lang=target_lang,
            )
        )
    )


def preload_pair_gloss_records(
    *,
    pair: str,
    translation_dict_path: Optional[Path],
    reverse_translation_dict_path: Optional[Path],
    targets: Sequence[str] = (),
    expand_reverse_headwords,
) -> tuple[
    Optional[dict[str, list[TranslationGlossRecord]]],
    Optional[dict[str, list[TranslationGlossRecord]]],
]:
    forward_records = load_translation_gloss_records(
        translation_dict_path,
        target_lang=translation_target_lang_for_pair(pair),
        headwords=targets,
    )
    reverse_headwords = build_reverse_preload_headwords(
        pair=pair,
        forward_records_by_target=forward_records,
    )
    reverse_headwords = expand_reverse_headwords(
        pair=pair,
        reverse_translation_dict_path=reverse_translation_dict_path,
        reverse_headwords=reverse_headwords,
    )
    return (
        forward_records,
        load_translation_gloss_records(
            reverse_translation_dict_path,
            target_lang=reverse_translation_target_lang_for_pair(pair),
            headwords=reverse_headwords,
        ),
    )
