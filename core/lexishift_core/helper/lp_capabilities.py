from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from lexishift_core.helper.installed_packs import resolve_installed_pack_artifact


@dataclass(frozen=True)
class SemanticPublicationCapability:
    locator_modes: tuple[str, ...] = ()
    missing_locator_reason_code: str = "pair_lacks_sense_locator"
    competition_publication_mode: str = "not_published"
    competition_selection_policy_version: str = ""
    missing_competition_reason_code: str = "missing_shadow_selection"


@dataclass(frozen=True)
class PairCapability:
    pair: str
    rulegen_mode: Optional[str] = None
    default_frequency_db: Optional[str] = None
    srs_selectable: bool = False
    requires_jmdict_for_seed: bool = False
    requires_jmdict_for_rulegen: bool = False
    requires_translation_dictionary_for_rulegen: bool = False
    semantic_publication: SemanticPublicationCapability = field(
        default_factory=SemanticPublicationCapability
    )


_PAIR_CAPABILITIES: dict[str, PairCapability] = {
    "en-ja": PairCapability(
        pair="en-ja",
        rulegen_mode="en_ja",
        default_frequency_db="freq-ja-bccwj.sqlite",
        srs_selectable=True,
        requires_jmdict_for_seed=True,
        requires_jmdict_for_rulegen=True,
        semantic_publication=SemanticPublicationCapability(
            locator_modes=("jmdict_entry",),
            missing_locator_reason_code="missing_jmdict_entry_locator",
        ),
    ),
    "ja-ja": PairCapability(
        pair="ja-ja",
        default_frequency_db="freq-ja-bccwj.sqlite",
        srs_selectable=True,
    ),
    "en-en": PairCapability(
        pair="en-en",
        default_frequency_db="freq-en-coca.sqlite",
        srs_selectable=True,
    ),
    "de-en": PairCapability(
        pair="de-en",
        rulegen_mode="de_en",
        default_frequency_db="freq-en-coca.sqlite",
        srs_selectable=True,
        requires_translation_dictionary_for_rulegen=True,
        semantic_publication=SemanticPublicationCapability(
            locator_modes=("translation_gloss",),
            missing_locator_reason_code="missing_translation_gloss_locator",
        ),
    ),
    "en-de": PairCapability(
        pair="en-de",
        rulegen_mode="en_de",
        default_frequency_db="freq-de-default.sqlite",
        srs_selectable=True,
        requires_translation_dictionary_for_rulegen=True,
        semantic_publication=SemanticPublicationCapability(
            locator_modes=("sense_provenance", "translation_gloss"),
            missing_locator_reason_code="missing_source_sense_locator",
        ),
    ),
    "en-es": PairCapability(
        pair="en-es",
        rulegen_mode="en_es",
        default_frequency_db="freq-es-cde.sqlite",
        srs_selectable=True,
        requires_translation_dictionary_for_rulegen=True,
        semantic_publication=SemanticPublicationCapability(
            locator_modes=("sense_provenance", "translation_gloss"),
            missing_locator_reason_code="missing_source_sense_locator",
            competition_publication_mode="emitted_rule_siblings",
            competition_selection_policy_version="en_es_emitted_rule_siblings_v1",
        ),
    ),
    "es-en": PairCapability(
        pair="es-en",
        rulegen_mode="es_en",
        default_frequency_db="freq-en-coca.sqlite",
        srs_selectable=True,
        requires_translation_dictionary_for_rulegen=True,
        semantic_publication=SemanticPublicationCapability(
            locator_modes=("translation_gloss",),
            missing_locator_reason_code="missing_translation_gloss_locator",
        ),
    ),
    "es-es": PairCapability(
        pair="es-es",
        default_frequency_db="freq-es-cde.sqlite",
        srs_selectable=True,
    ),
    "de-de": PairCapability(pair="de-de", srs_selectable=True),
    "en-zh": PairCapability(pair="en-zh"),
}


def normalize_pair_key(pair: str, *, default: str = "en-ja") -> str:
    normalized = str(pair or "").strip().lower()
    return normalized or default


def _target_language(pair: str) -> str:
    normalized = normalize_pair_key(pair)
    parts = normalized.split("-", 1)
    if len(parts) == 2 and parts[1].strip():
        return parts[1].strip().lower()
    return ""


def resolve_pair_capability(pair: str) -> PairCapability:
    normalized = normalize_pair_key(pair)
    return _PAIR_CAPABILITIES.get(normalized, PairCapability(pair=normalized))


def known_pairs() -> tuple[str, ...]:
    return tuple(_PAIR_CAPABILITIES.keys())


def selectable_srs_pairs() -> tuple[str, ...]:
    return tuple(cap.pair for cap in _PAIR_CAPABILITIES.values() if cap.srs_selectable)


def supported_rulegen_pairs() -> tuple[str, ...]:
    return tuple(cap.pair for cap in _PAIR_CAPABILITIES.values() if cap.rulegen_mode is not None)


def supports_rulegen(pair: str) -> bool:
    capability = resolve_pair_capability(pair)
    return capability.rulegen_mode is not None


def default_frequency_db_path(
    pair: str,
    *,
    frequency_packs_dir: Path,
) -> Optional[Path]:
    capability = resolve_pair_capability(pair)
    if capability.default_frequency_db:
        pack_id = Path(capability.default_frequency_db).stem
        resolved_pack_artifact = resolve_installed_pack_artifact(frequency_packs_dir, pack_id)
        if resolved_pack_artifact is not None:
            return resolved_pack_artifact
        return frequency_packs_dir / capability.default_frequency_db
    target_lang = _target_language(capability.pair)
    if not target_lang:
        return None
    # Fallback convention for LPs that have not yet declared a concrete corpus filename.
    fallback_filename = f"freq-{target_lang}-default.sqlite"
    resolved_pack_artifact = resolve_installed_pack_artifact(
        frequency_packs_dir,
        Path(fallback_filename).stem,
    )
    if resolved_pack_artifact is not None:
        return resolved_pack_artifact
    return frequency_packs_dir / fallback_filename


def default_jmdict_path(
    pair: str,
    *,
    language_packs_dir: Path,
) -> Optional[Path]:
    capability = resolve_pair_capability(pair)
    if not (capability.requires_jmdict_for_seed or capability.requires_jmdict_for_rulegen):
        return None
    return language_packs_dir / "JMdict_e"


def default_translation_dictionary_path(
    pair: str,
    *,
    language_packs_dir: Path,
) -> Optional[Path]:
    capability = resolve_pair_capability(pair)
    if not capability.requires_translation_dictionary_for_rulegen:
        return None
    for pack_id in _default_translation_pack_ids_for_pair(capability.pair):
        resolved_pack_artifact = resolve_installed_pack_artifact(language_packs_dir, pack_id)
        if resolved_pack_artifact is not None:
            return resolved_pack_artifact
    filenames = _default_translation_dictionary_filenames_for_pair(capability.pair)
    return _resolve_translation_fallback_path(
        language_packs_dir=language_packs_dir,
        filenames=filenames,
        pack_ids=_default_translation_pack_ids_for_pair(capability.pair),
    )


def default_reverse_translation_dictionary_path(
    pair: str,
    *,
    language_packs_dir: Path,
) -> Optional[Path]:
    capability = resolve_pair_capability(pair)
    if not capability.requires_translation_dictionary_for_rulegen:
        return None
    for pack_id in _default_reverse_translation_pack_ids_for_pair(capability.pair):
        resolved_pack_artifact = resolve_installed_pack_artifact(language_packs_dir, pack_id)
        if resolved_pack_artifact is not None:
            return resolved_pack_artifact
    filenames = _default_reverse_translation_filenames_for_pair(capability.pair)
    return _resolve_translation_fallback_path(
        language_packs_dir=language_packs_dir,
        filenames=filenames,
        pack_ids=_default_reverse_translation_pack_ids_for_pair(capability.pair),
    )


def _reverse_pair_key(pair: str) -> str:
    normalized = normalize_pair_key(pair)
    left, sep, right = normalized.partition("-")
    if not sep or not left or not right:
        return ""
    return f"{right}-{left}"


def _default_translation_dictionary_filenames_for_pair(pair: str) -> tuple[str, ...]:
    if pair == "de-en":
        return ("freedict-en-de.sqlite", "eng-deu.sqlite", "eng-deu.tei")
    if pair == "en-de":
        return ("freedict-de-en.sqlite", "deu-eng.sqlite", "deu-eng.tei")
    if pair == "en-es":
        return (
            "wiktionary-es-en.sqlite",
            "freedict-es-en.sqlite",
            "spa-eng.sqlite",
            "spa-eng.tei",
        )
    if pair == "es-en":
        return ("freedict-en-es.sqlite", "eng-spa.sqlite", "eng-spa.tei")
    return ("freedict-de-en.sqlite", "deu-eng.sqlite", "deu-eng.tei")


def _default_translation_pack_ids_for_pair(pair: str) -> tuple[str, ...]:
    if pair == "de-en":
        return ("freedict-en-de",)
    if pair == "en-de":
        return ("freedict-de-en",)
    if pair == "en-es":
        return ("wiktionary-es-en", "freedict-es-en")
    if pair == "es-en":
        return ("freedict-en-es",)
    return ("freedict-de-en",)


def _default_reverse_translation_filenames_for_pair(pair: str) -> tuple[str, ...]:
    if pair == "en-es":
        return (
            "wiktionary-en-es.sqlite",
            "freedict-en-es.sqlite",
            "eng-spa.sqlite",
            "eng-spa.tei",
        )
    if pair == "es-en":
        return (
            "wiktionary-es-en.sqlite",
            "freedict-es-en.sqlite",
            "spa-eng.sqlite",
            "spa-eng.tei",
        )
    reverse_pair = _reverse_pair_key(pair)
    if not reverse_pair:
        return ()
    return _default_translation_dictionary_filenames_for_pair(reverse_pair)


def _default_reverse_translation_pack_ids_for_pair(pair: str) -> tuple[str, ...]:
    if pair == "de-en":
        return ("freedict-de-en",)
    if pair == "en-de":
        return ("freedict-en-de",)
    if pair == "en-es":
        return ("wiktionary-en-es", "freedict-en-es")
    if pair == "es-en":
        return ("wiktionary-es-en", "freedict-es-en")
    return ("freedict-en-de",)


def _resolve_translation_fallback_path(
    *,
    language_packs_dir: Path,
    filenames: tuple[str, ...],
    pack_ids: tuple[str, ...],
) -> Optional[Path]:
    if not filenames:
        return None
    for filename in filenames:
        direct_candidate = language_packs_dir / filename
        if direct_candidate.exists():
            return direct_candidate
    for pack_id in pack_ids:
        pack_root = language_packs_dir / pack_id
        if not pack_root.exists() or not pack_root.is_dir():
            continue
        for filename in filenames:
            discovered = sorted(pack_root.rglob(filename))
            if discovered:
                return discovered[0]
    return language_packs_dir / filenames[0]


def pair_requirements(pair: str) -> dict[str, object]:
    capability = resolve_pair_capability(pair)
    fallback_frequency = capability.default_frequency_db
    if not fallback_frequency:
        target_lang = _target_language(capability.pair)
        fallback_frequency = f"freq-{target_lang}-default.sqlite" if target_lang else None
    return {
        "pair": capability.pair,
        "rulegen_mode": capability.rulegen_mode,
        "supports_rulegen": supports_rulegen(capability.pair),
        "srs_selectable": capability.srs_selectable,
        "default_frequency_db": fallback_frequency,
        "requires_jmdict_for_seed": capability.requires_jmdict_for_seed,
        "requires_jmdict_for_rulegen": capability.requires_jmdict_for_rulegen,
        "requires_translation_dictionary_for_rulegen": (
            capability.requires_translation_dictionary_for_rulegen
        ),
    }
