from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from lexishift_core.replacement.core import VocabRule
from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.translation_packs import (
    FORWARD_PACK_DIRECTION,
    REVERSE_PACK_DIRECTION,
    TranslationPackRef,
    build_translation_pack_ref,
)
from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.generation import RuleGenerationResult, RuleScoringConfig
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig
from lexishift_core.rulegen.pairs.de_en import DeEnRulegenConfig, generate_de_en_results
from lexishift_core.rulegen.pairs.en_de import (
    EnDeKaikkiPolicyConfig,
    EnDeRulegenConfig,
    generate_en_de_results,
)

try:
    from lexishift_core.rulegen.pairs.en_de import EnDeCompiledResources
except ImportError:  # pragma: no cover - branch-local capability seam
    EnDeCompiledResources = None
from lexishift_core.rulegen.pairs.en_es import (
    EnEsCompiledResources,
    EnEsKaikkiPolicyConfig,
    EnEsRulegenConfig,
    generate_en_es_results,
)
from lexishift_core.rulegen.pairs.es_en import EsEnRulegenConfig, generate_es_en_results
from lexishift_core.rulegen.pairs.en_ja import EnJaRulegenConfig, generate_en_ja_results
from lexishift_core.rulegen.semantic_publication import annotate_results_with_semantic_admission
from lexishift_core.scoring.weighting import GlossDecay


@dataclass(frozen=True)
class RulegenAdapterRequest:
    pair: str
    targets: Sequence[str]
    language_pair: str
    confidence_threshold: float = 0.0
    max_definitions_per_target: Optional[int] = 3
    max_rules_per_target: Optional[int] = None
    interleave_definition_groups: bool = False
    sense_representative_selection: bool = False
    sense_representative_penalty: float = 0.60
    sense_defaultness_competition_penalty: float = 0.0
    semantic_demotion_scale: float = 1.0
    include_variants: bool = True
    allow_multiword_glosses: bool = False
    scoring: RuleScoringConfig = field(default_factory=RuleScoringConfig)
    reverse_check: ReverseCheckScoringConfig = field(default_factory=ReverseCheckScoringConfig)
    gloss_decay: GlossDecay = field(default_factory=GlossDecay)
    jmdict_path: Optional[Path] = None
    translation_pack: Optional[TranslationPackRef] = None
    translation_dict_path: Optional[Path] = None
    reverse_translation_pack: Optional[TranslationPackRef] = None
    reverse_translation_dict_path: Optional[Path] = None
    source_frequency_db_path: Optional[Path] = None
    gloss_records_by_target: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    reverse_gloss_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    compiled_pair_context: Optional[object] = None
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None
    kaikki_policy_live_demotion: bool = False
    kaikki_policy_register_demotion: bool = False
    kaikki_policy_risk_families: Optional[Sequence[str]] = None
    kaikki_policy_late_sense_penalty: float = 0.0
    enable_exact_gloss_demotions: bool = False
    enable_source_frequency_prior: bool = False
    cleaner_later_competition_penalty: float = 0.0


RulegenAdapter = Callable[[RulegenAdapterRequest], Sequence[VocabRule]]
RulegenResultAdapter = Callable[[RulegenAdapterRequest], Sequence[RuleGenerationResult]]


def _resolved_translation_dict_path(request: RulegenAdapterRequest) -> Path | None:
    if request.translation_pack is not None:
        return request.translation_pack.path
    return request.translation_dict_path


def _resolved_reverse_translation_dict_path(request: RulegenAdapterRequest) -> Path | None:
    if request.reverse_translation_pack is not None:
        return request.reverse_translation_pack.path
    return request.reverse_translation_dict_path


def _resolved_translation_pack(request: RulegenAdapterRequest) -> TranslationPackRef | None:
    if request.translation_pack is not None:
        return request.translation_pack
    return build_translation_pack_ref(
        request.pair,
        _resolved_translation_dict_path(request),
        direction=FORWARD_PACK_DIRECTION,
    )


def _resolved_reverse_translation_pack(request: RulegenAdapterRequest) -> TranslationPackRef | None:
    if request.reverse_translation_pack is not None:
        return request.reverse_translation_pack
    return build_translation_pack_ref(
        request.pair,
        _resolved_reverse_translation_dict_path(request),
        direction=REVERSE_PACK_DIRECTION,
    )


def _run_en_ja_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    return [result.rule for result in _run_en_ja_results_adapter(request)]


def _run_en_ja_results_adapter(request: RulegenAdapterRequest) -> Sequence[RuleGenerationResult]:
    if request.jmdict_path is None:
        raise ValueError("Missing JMDict path for en-ja rule generation.")
    config = EnJaRulegenConfig(
        jmdict_path=request.jmdict_path,
        language_pair=request.language_pair,
        confidence_threshold=request.confidence_threshold,
        max_definitions_per_target=request.max_definitions_per_target,
        max_rules_per_target=request.max_rules_per_target,
        semantic_demotion_scale=request.semantic_demotion_scale,
        include_variants=request.include_variants,
        allow_multiword_glosses=request.allow_multiword_glosses,
        scoring=request.scoring,
        gloss_decay=request.gloss_decay,
        word_packages_by_target=request.word_packages_by_target,
        enable_exact_gloss_demotions=request.enable_exact_gloss_demotions,
    )
    return tuple(
        annotate_results_with_semantic_admission(
            generate_en_ja_results(request.targets, config=config)
        )
    )


def build_en_de_rulegen_config(request: RulegenAdapterRequest) -> EnDeRulegenConfig:
    translation_pack = _resolved_translation_pack(request)
    if translation_pack is None:
        raise ValueError("Missing translation dictionary path for en-de rule generation.")
    translation_dict_path = translation_pack.path
    reverse_translation_pack = _resolved_reverse_translation_pack(request)
    reverse_translation_dict_path = (
        reverse_translation_pack.path if reverse_translation_pack is not None else None
    )
    reverse_source_dict_id = (
        reverse_translation_pack.pack_id if reverse_translation_pack is not None else None
    )
    default_kaikki_policy = EnDeKaikkiPolicyConfig()
    compiled_resources = (
        request.compiled_pair_context
        if EnDeCompiledResources is not None
        and isinstance(request.compiled_pair_context, EnDeCompiledResources)
        else None
    )
    config_kwargs = {
        "translation_dict_path": translation_dict_path,
        "reverse_translation_dict_path": reverse_translation_dict_path,
        "language_pair": request.language_pair,
        "source_dict_id": translation_pack.pack_id,
        "reverse_source_dict_id": reverse_source_dict_id,
        "dictionary_pos_source_profile": translation_pack.pos_source_profile,
        "gloss_records_by_target": request.gloss_records_by_target,
        "reverse_gloss_records_by_source": request.reverse_gloss_records_by_source,
        "confidence_threshold": request.confidence_threshold,
        "max_definitions_per_target": request.max_definitions_per_target,
        "max_rules_per_target": request.max_rules_per_target,
        "interleave_definition_groups": request.interleave_definition_groups,
        "sense_representative_selection": request.sense_representative_selection,
        "sense_representative_penalty": request.sense_representative_penalty,
        "sense_defaultness_competition_penalty": request.sense_defaultness_competition_penalty,
        "semantic_demotion_scale": request.semantic_demotion_scale,
        "include_variants": request.include_variants,
        "allow_multiword_glosses": request.allow_multiword_glosses,
        "scoring": request.scoring,
        "reverse_check": request.reverse_check,
        "gloss_decay": request.gloss_decay,
        "word_packages_by_target": request.word_packages_by_target,
        "enable_exact_gloss_demotions": request.enable_exact_gloss_demotions,
        "enable_source_frequency_prior": request.enable_source_frequency_prior,
        "source_frequency_db_path": request.source_frequency_db_path,
        "cleaner_later_competition_penalty": request.cleaner_later_competition_penalty,
        "compiled_resources": compiled_resources,
        "kaikki_policy": EnDeKaikkiPolicyConfig(
            enable_shadow_metadata=True,
            enable_live_demotion=bool(request.kaikki_policy_live_demotion),
            enable_register_demotion=bool(request.kaikki_policy_register_demotion),
            late_sense_clean_earlier_competition_penalty=max(
                0.0,
                float(request.kaikki_policy_late_sense_penalty),
            ),
            risk_families=tuple(
                request.kaikki_policy_risk_families or default_kaikki_policy.risk_families
            ),
        ),
    }
    supported_fields = EnDeRulegenConfig.__dataclass_fields__
    return EnDeRulegenConfig(
        **{key: value for key, value in config_kwargs.items() if key in supported_fields}
    )


def _run_en_de_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    return [result.rule for result in _run_en_de_results_adapter(request)]


def _run_en_de_results_adapter(request: RulegenAdapterRequest) -> Sequence[RuleGenerationResult]:
    config = build_en_de_rulegen_config(request)
    return tuple(
        annotate_results_with_semantic_admission(
            generate_en_de_results(request.targets, config=config)
        )
    )


def _run_de_en_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    return [result.rule for result in _run_de_en_results_adapter(request)]


def _run_de_en_results_adapter(request: RulegenAdapterRequest) -> Sequence[RuleGenerationResult]:
    translation_dict_path = _resolved_translation_dict_path(request)
    if translation_dict_path is None:
        raise ValueError("Missing translation dictionary path for de-en rule generation.")
    config = DeEnRulegenConfig(
        translation_dict_path=translation_dict_path,
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
        enable_exact_gloss_demotions=request.enable_exact_gloss_demotions,
    )
    return tuple(
        annotate_results_with_semantic_admission(
            generate_de_en_results(request.targets, config=config)
        )
    )


def build_en_es_rulegen_config(request: RulegenAdapterRequest) -> EnEsRulegenConfig:
    translation_pack = _resolved_translation_pack(request)
    reverse_translation_pack = _resolved_reverse_translation_pack(request)
    if translation_pack is None:
        raise ValueError("Missing translation dictionary path for en-es rule generation.")
    translation_dict_path = translation_pack.path
    reverse_translation_dict_path = (
        reverse_translation_pack.path if reverse_translation_pack is not None else None
    )
    source_dict_id = translation_pack.pack_id
    dictionary_pos_source_profile = translation_pack.pos_source_profile
    reverse_source_dict_id = (
        reverse_translation_pack.pack_id
        if reverse_translation_pack is not None
        else "freedict_en_es"
    )
    default_kaikki_policy = EnEsKaikkiPolicyConfig()
    compiled_resources = (
        request.compiled_pair_context
        if isinstance(request.compiled_pair_context, EnEsCompiledResources)
        else None
    )
    return EnEsRulegenConfig(
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
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
        enable_exact_gloss_demotions=request.enable_exact_gloss_demotions,
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
        ),
        compiled_resources=compiled_resources,
    )


def _run_en_es_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    return [result.rule for result in _run_en_es_results_adapter(request)]


def _run_en_es_results_adapter(request: RulegenAdapterRequest) -> Sequence[RuleGenerationResult]:
    config = build_en_es_rulegen_config(request)
    return tuple(
        annotate_results_with_semantic_admission(
            generate_en_es_results(request.targets, config=config)
        )
    )


def _run_es_en_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    return [result.rule for result in _run_es_en_results_adapter(request)]


def _run_es_en_results_adapter(request: RulegenAdapterRequest) -> Sequence[RuleGenerationResult]:
    translation_dict_path = _resolved_translation_dict_path(request)
    reverse_translation_dict_path = _resolved_reverse_translation_dict_path(request)
    if translation_dict_path is None:
        raise ValueError("Missing translation dictionary path for es-en rule generation.")
    config = EsEnRulegenConfig(
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
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
        enable_exact_gloss_demotions=request.enable_exact_gloss_demotions,
    )
    return tuple(
        annotate_results_with_semantic_admission(
            generate_es_en_results(request.targets, config=config)
        )
    )


_RULEGEN_ADAPTERS: dict[str, RulegenAdapter] = {
    "de_en": _run_de_en_adapter,
    "en_ja": _run_en_ja_adapter,
    "en_de": _run_en_de_adapter,
    "en_es": _run_en_es_adapter,
    "es_en": _run_es_en_adapter,
}

_RULEGEN_RESULT_ADAPTERS: dict[str, RulegenResultAdapter] = {
    "de_en": _run_de_en_results_adapter,
    "en_ja": _run_en_ja_results_adapter,
    "en_de": _run_en_de_results_adapter,
    "en_es": _run_en_es_results_adapter,
    "es_en": _run_es_en_results_adapter,
}


def run_results_with_adapter(request: RulegenAdapterRequest) -> Sequence[RuleGenerationResult]:
    capability = resolve_pair_capability(request.pair)
    mode = capability.rulegen_mode
    if mode is None:
        return []
    adapter = _RULEGEN_RESULT_ADAPTERS.get(mode)
    if adapter is None:
        raise ValueError(
            f"No rulegen results adapter registered for mode '{mode}' (pair '{capability.pair}')."
        )
    return adapter(request)


def run_rules_with_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    return [result.rule for result in run_results_with_adapter(request)]
