from __future__ import annotations

from pathlib import Path
from typing import Optional

from lexishift_core.lexicon.word_package import resolve_language_tag_from_pair
from lexishift_core.helper.frequency_packs import FrequencyPackRef, build_frequency_pack_ref
from lexishift_core.helper.lp_capabilities import (
    default_frequency_db_path,
    default_jmdict_path,
    default_reverse_translation_dictionary_path,
    default_translation_dictionary_path,
    resolve_pair_capability,
)
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.translation_packs import (
    FORWARD_PACK_DIRECTION,
    REVERSE_PACK_DIRECTION,
    TranslationPackRef,
    build_translation_pack_ref,
)


def target_language_from_pair(pair: str) -> str:
    return resolve_language_tag_from_pair(pair)


def resolve_stopwords_path(paths: HelperPaths, *, pair: str) -> Optional[Path]:
    target_lang = target_language_from_pair(pair)
    if not target_lang:
        return None
    candidates = (
        paths.srs_dir / f"stopwords-{target_lang}.json",
        paths.srs_dir / "stopwords" / f"stopwords-{target_lang}.json",
        paths.data_root / "stopwords" / f"stopwords-{target_lang}.json",
        paths.language_packs_dir / f"stopwords-{target_lang}.json",
    )
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def resolve_pair_resources(
    paths: HelperPaths,
    *,
    pair: str,
    jmdict_path: Optional[Path],
    translation_dict_path: Optional[Path] = None,
    freedict_de_en_path: Optional[Path],
    set_source_db: Optional[Path],
) -> tuple[Optional[Path], Optional[Path], Optional[Path]]:
    capability = resolve_pair_capability(pair)
    resolved_jmdict = (
        Path(jmdict_path)
        if jmdict_path is not None
        else default_jmdict_path(capability.pair, language_packs_dir=paths.language_packs_dir)
    )
    resolved_translation_dict = (
        Path(translation_dict_path)
        if translation_dict_path is not None
        else Path(freedict_de_en_path)
        if freedict_de_en_path is not None
        else default_translation_dictionary_path(
            capability.pair,
            language_packs_dir=paths.language_packs_dir,
        )
    )
    resolved_frequency_db = (
        Path(set_source_db)
        if set_source_db is not None
        else default_frequency_db_path(
            capability.pair, frequency_packs_dir=paths.frequency_packs_dir
        )
    )
    return resolved_jmdict, resolved_translation_dict, resolved_frequency_db


def resolve_pair_translation_packs(
    paths: HelperPaths,
    *,
    pair: str,
    translation_dict_path: Optional[Path] = None,
    freedict_de_en_path: Optional[Path] = None,
    reverse_translation_dict_path: Optional[Path] = None,
    freedict_reverse_path: Optional[Path] = None,
) -> tuple[Optional[TranslationPackRef], Optional[TranslationPackRef]]:
    capability = resolve_pair_capability(pair)
    resolved_translation_dict = (
        Path(translation_dict_path)
        if translation_dict_path is not None
        else Path(freedict_de_en_path)
        if freedict_de_en_path is not None
        else default_translation_dictionary_path(
            capability.pair,
            language_packs_dir=paths.language_packs_dir,
        )
    )
    resolved_reverse_translation_dict = (
        Path(reverse_translation_dict_path)
        if reverse_translation_dict_path is not None
        else Path(freedict_reverse_path)
        if freedict_reverse_path is not None
        else default_reverse_translation_dictionary_path(
            capability.pair,
            language_packs_dir=paths.language_packs_dir,
        )
    )
    return (
        build_translation_pack_ref(
            capability.pair,
            resolved_translation_dict,
            direction=FORWARD_PACK_DIRECTION,
        ),
        build_translation_pack_ref(
            capability.pair,
            resolved_reverse_translation_dict,
            direction=REVERSE_PACK_DIRECTION,
        ),
    )


def resolve_pair_frequency_pack(
    paths: HelperPaths,
    *,
    pair: str,
    set_source_db: Optional[Path] = None,
) -> Optional[FrequencyPackRef]:
    capability = resolve_pair_capability(pair)
    resolved_frequency_db = (
        Path(set_source_db)
        if set_source_db is not None
        else default_frequency_db_path(
            capability.pair,
            frequency_packs_dir=paths.frequency_packs_dir,
        )
    )
    return build_frequency_pack_ref(capability.pair, resolved_frequency_db)
