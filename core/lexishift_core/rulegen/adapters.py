from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Mapping, Optional, Sequence

from lexishift_core.replacement.core import VocabRule
from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.generation import RuleScoringConfig
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig
from lexishift_core.scoring.weighting import GlossDecay

if TYPE_CHECKING:
    from lexishift_core.rulegen.pairs.en_de import EnDeRulegenConfig
    from lexishift_core.rulegen.pairs.en_es import (
        EnEsCompiledResources,
        EnEsKaikkiPolicyConfig,
        EnEsRulegenConfig,
    )
    from lexishift_core.rulegen.pairs.es_en import EsEnRulegenConfig
    from lexishift_core.rulegen.pairs.en_ja import EnJaRulegenConfig


@dataclass(frozen=True)
class RulegenAdapterRequest:
    pair: str
    targets: Sequence[str]
    language_pair: str
    confidence_threshold: float = 0.0
    max_definitions_per_target: Optional[int] = 3
    max_rules_per_target: Optional[int] = None
    semantic_demotion_scale: float = 1.0
    include_variants: bool = True
    allow_multiword_glosses: bool = False
    scoring: RuleScoringConfig = field(default_factory=RuleScoringConfig)
    reverse_check: ReverseCheckScoringConfig = field(default_factory=ReverseCheckScoringConfig)
    gloss_decay: GlossDecay = field(default_factory=GlossDecay)
    jmdict_path: Optional[Path] = None
    translation_dict_path: Optional[Path] = None
    freedict_de_en_path: Optional[Path] = None
    freedict_reverse_path: Optional[Path] = None
    gloss_records_by_target: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    gloss_records_by_reading: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    gloss_records_by_alias: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    reverse_gloss_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    compiled_pair_context: Optional[object] = None
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None
    kaikki_policy_live_demotion: bool = False
    kaikki_policy_risk_families: Optional[Sequence[str]] = None
    kaikki_policy_risk_family_demotions: Optional[Sequence[tuple[str, float]]] = None
    kaikki_policy_late_sense_penalty: float = 0.0


RulegenAdapter = Callable[[RulegenAdapterRequest], Sequence[VocabRule]]


def _load_en_ja_pair_exports():
    from lexishift_core.rulegen.pairs.en_ja import EnJaRulegenConfig, generate_en_ja_results

    return EnJaRulegenConfig, generate_en_ja_results


def _load_en_de_pair_exports():
    from lexishift_core.rulegen.pairs.en_de import EnDeRulegenConfig, generate_en_de_results

    return EnDeRulegenConfig, generate_en_de_results


def _load_en_es_pair_exports():
    from lexishift_core.rulegen.pairs.en_es import (
        EnEsCompiledResources,
        EnEsKaikkiPolicyConfig,
        EnEsRulegenConfig,
        generate_en_es_results,
    )

    return EnEsCompiledResources, EnEsKaikkiPolicyConfig, EnEsRulegenConfig, generate_en_es_results


def _load_es_en_pair_exports():
    from lexishift_core.rulegen.pairs.es_en import EsEnRulegenConfig, generate_es_en_results

    return EsEnRulegenConfig, generate_es_en_results


def generate_en_ja_results(*args, **kwargs):
    _, generate = _load_en_ja_pair_exports()
    return generate(*args, **kwargs)


def generate_en_de_results(*args, **kwargs):
    _, generate = _load_en_de_pair_exports()
    return generate(*args, **kwargs)


def generate_en_es_results(*args, **kwargs):
    _, _, _, generate = _load_en_es_pair_exports()
    return generate(*args, **kwargs)


def generate_es_en_results(*args, **kwargs):
    _, generate = _load_es_en_pair_exports()
    return generate(*args, **kwargs)


def _is_kaikki_dictionary(path: Path | None) -> bool:
    if path is None:
        return False
    name = path.name.strip().lower()
    return "wiktionary" in name or "kaikki" in name


def _run_en_ja_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    dictionary_path = request.translation_dict_path or request.jmdict_path
    if dictionary_path is None:
        raise ValueError("Missing translation dictionary path for en-ja rule generation.")
    source_dict_id = "jmdict"
    dictionary_pos_source_profile = ""
    if _is_kaikki_dictionary(dictionary_path):
        source_dict_id = "wiktionary_ja_en"
        dictionary_pos_source_profile = "wiktionary"
    EnJaRulegenConfig, _ = _load_en_ja_pair_exports()
    config = EnJaRulegenConfig(
        jmdict_path=dictionary_path,
        language_pair=request.language_pair,
        confidence_threshold=request.confidence_threshold,
        max_definitions_per_target=request.max_definitions_per_target,
        max_rules_per_target=request.max_rules_per_target,
        semantic_demotion_scale=request.semantic_demotion_scale,
        include_variants=request.include_variants,
        allow_multiword_glosses=request.allow_multiword_glosses,
        scoring=request.scoring,
        gloss_decay=request.gloss_decay,
        gloss_records_by_target=request.gloss_records_by_target,
        gloss_records_by_reading=request.gloss_records_by_reading,
        gloss_records_by_alias=request.gloss_records_by_alias,
        word_packages_by_target=request.word_packages_by_target,
        source_dict_id=source_dict_id,
        dictionary_pos_source_profile=dictionary_pos_source_profile,
    )
    results = generate_en_ja_results(request.targets, config=config)
    return [result.rule for result in results]


def _run_en_de_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    translation_dict_path = request.translation_dict_path or request.freedict_de_en_path
    if translation_dict_path is None:
        raise ValueError("Missing FreeDict DE->EN path for en-de rule generation.")
    EnDeRulegenConfig, _ = _load_en_de_pair_exports()
    config = EnDeRulegenConfig(
        freedict_de_en_path=translation_dict_path,
        language_pair=request.language_pair,
        gloss_records_by_target=request.gloss_records_by_target,
        confidence_threshold=request.confidence_threshold,
        max_definitions_per_target=request.max_definitions_per_target,
        max_rules_per_target=request.max_rules_per_target,
        semantic_demotion_scale=request.semantic_demotion_scale,
        include_variants=request.include_variants,
        allow_multiword_glosses=request.allow_multiword_glosses,
        scoring=request.scoring,
        gloss_decay=request.gloss_decay,
        word_packages_by_target=request.word_packages_by_target,
    )
    results = generate_en_de_results(request.targets, config=config)
    return [result.rule for result in results]


def build_en_es_rulegen_config(request: RulegenAdapterRequest) -> EnEsRulegenConfig:
    translation_dict_path = request.translation_dict_path or request.freedict_de_en_path
    if translation_dict_path is None:
        raise ValueError("Missing FreeDict ES->EN path for en-es rule generation.")
    source_dict_id = "freedict_es_en"
    dictionary_pos_source_profile = "freedict"
    reverse_source_dict_id = "freedict_en_es"
    EnEsCompiledResources, EnEsKaikkiPolicyConfig, EnEsRulegenConfig, _ = _load_en_es_pair_exports()
    default_kaikki_policy = EnEsKaikkiPolicyConfig()
    if _is_kaikki_dictionary(translation_dict_path):
        source_dict_id = "wiktionary_es_en"
        dictionary_pos_source_profile = "wiktionary"
    if _is_kaikki_dictionary(request.freedict_reverse_path):
        reverse_source_dict_id = "wiktionary_en_es"
    compiled_resources = (
        request.compiled_pair_context
        if isinstance(request.compiled_pair_context, EnEsCompiledResources)
        else None
    )
    return EnEsRulegenConfig(
        freedict_es_en_path=translation_dict_path,
        reverse_freedict_en_es_path=request.freedict_reverse_path,
        language_pair=request.language_pair,
        gloss_records_by_target=request.gloss_records_by_target,
        reverse_gloss_records_by_source=request.reverse_gloss_records_by_source,
        source_dict_id=source_dict_id,
        reverse_source_dict_id=reverse_source_dict_id,
        confidence_threshold=request.confidence_threshold,
        max_definitions_per_target=request.max_definitions_per_target,
        max_rules_per_target=request.max_rules_per_target,
        semantic_demotion_scale=request.semantic_demotion_scale,
        include_variants=request.include_variants,
        allow_multiword_glosses=request.allow_multiword_glosses,
        scoring=request.scoring,
        reverse_check=request.reverse_check,
        gloss_decay=request.gloss_decay,
        word_packages_by_target=request.word_packages_by_target,
        dictionary_pos_source_profile=dictionary_pos_source_profile,
        kaikki_policy=EnEsKaikkiPolicyConfig(
            enable_shadow_metadata=True,
            enable_live_demotion=bool(request.kaikki_policy_live_demotion),
            late_sense_clean_earlier_competition_penalty=max(
                0.0,
                float(request.kaikki_policy_late_sense_penalty),
            ),
            risk_families=tuple(
                request.kaikki_policy_risk_families or default_kaikki_policy.risk_families
            ),
            risk_family_demotions=tuple(request.kaikki_policy_risk_family_demotions or ()),
        ),
        compiled_resources=compiled_resources,
    )


def _run_en_es_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    config = build_en_es_rulegen_config(request)
    results = generate_en_es_results(request.targets, config=config)
    return [result.rule for result in results]


def _run_es_en_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    translation_dict_path = request.translation_dict_path or request.freedict_de_en_path
    if translation_dict_path is None:
        raise ValueError("Missing FreeDict EN->ES path for es-en rule generation.")
    EsEnRulegenConfig, _ = _load_es_en_pair_exports()
    config = EsEnRulegenConfig(
        freedict_en_es_path=translation_dict_path,
        reverse_freedict_es_en_path=request.freedict_reverse_path,
        language_pair=request.language_pair,
        gloss_records_by_target=request.gloss_records_by_target,
        reverse_gloss_records_by_source=request.reverse_gloss_records_by_source,
        confidence_threshold=request.confidence_threshold,
        max_definitions_per_target=request.max_definitions_per_target,
        max_rules_per_target=request.max_rules_per_target,
        semantic_demotion_scale=request.semantic_demotion_scale,
        allow_multiword_glosses=request.allow_multiword_glosses,
        scoring=request.scoring,
        reverse_check=request.reverse_check,
        gloss_decay=request.gloss_decay,
        word_packages_by_target=request.word_packages_by_target,
    )
    results = generate_es_en_results(request.targets, config=config)
    return [result.rule for result in results]


_RULEGEN_ADAPTERS: dict[str, RulegenAdapter] = {
    "en_ja": _run_en_ja_adapter,
    "en_de": _run_en_de_adapter,
    "en_es": _run_en_es_adapter,
    "es_en": _run_es_en_adapter,
}


def run_rules_with_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    capability = resolve_pair_capability(request.pair)
    mode = capability.rulegen_mode
    if mode is None:
        return []
    adapter = _RULEGEN_ADAPTERS.get(mode)
    if adapter is None:
        raise ValueError(
            f"No rulegen adapter registered for mode '{mode}' (pair '{capability.pair}')."
        )
    return adapter(request)
