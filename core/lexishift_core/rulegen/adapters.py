from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from lexishift_core.replacement.core import VocabRule
from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.rulegen.generation import RuleScoringConfig
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig
from lexishift_core.rulegen.pairs.en_de import EnDeRulegenConfig, generate_en_de_results
from lexishift_core.rulegen.pairs.en_es import (
    EnEsKaikkiPolicyConfig,
    EnEsRulegenConfig,
    generate_en_es_results,
)
from lexishift_core.rulegen.pairs.es_en import EsEnRulegenConfig, generate_es_en_results
from lexishift_core.rulegen.pairs.en_ja import EnJaRulegenConfig, generate_en_ja_results
from lexishift_core.scoring.weighting import GlossDecay


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
    freedict_de_en_path: Optional[Path] = None
    freedict_reverse_path: Optional[Path] = None
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None
    kaikki_policy_live_demotion: bool = False
    kaikki_policy_risk_families: Optional[Sequence[str]] = None


RulegenAdapter = Callable[[RulegenAdapterRequest], Sequence[VocabRule]]


def _is_kaikki_dictionary(path: Path | None) -> bool:
    if path is None:
        return False
    name = path.name.strip().lower()
    return "wiktionary" in name or "kaikki" in name


def _run_en_ja_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
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
    )
    results = generate_en_ja_results(request.targets, config=config)
    return [result.rule for result in results]


def _run_en_de_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    if request.freedict_de_en_path is None:
        raise ValueError("Missing FreeDict DE->EN path for en-de rule generation.")
    config = EnDeRulegenConfig(
        freedict_de_en_path=request.freedict_de_en_path,
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
    )
    results = generate_en_de_results(request.targets, config=config)
    return [result.rule for result in results]


def _run_en_es_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    if request.freedict_de_en_path is None:
        raise ValueError("Missing FreeDict ES->EN path for en-es rule generation.")
    source_dict_id = "freedict_es_en"
    dictionary_pos_source_profile = "freedict"
    reverse_source_dict_id = "freedict_en_es"
    default_kaikki_policy = EnEsKaikkiPolicyConfig()
    if _is_kaikki_dictionary(request.freedict_de_en_path):
        source_dict_id = "wiktionary_es_en"
        dictionary_pos_source_profile = "wiktionary"
    if _is_kaikki_dictionary(request.freedict_reverse_path):
        reverse_source_dict_id = "wiktionary_en_es"
    config = EnEsRulegenConfig(
        freedict_es_en_path=request.freedict_de_en_path,
        reverse_freedict_en_es_path=request.freedict_reverse_path,
        language_pair=request.language_pair,
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
            risk_families=tuple(
                request.kaikki_policy_risk_families or default_kaikki_policy.risk_families
            ),
        ),
    )
    results = generate_en_es_results(request.targets, config=config)
    return [result.rule for result in results]


def _run_es_en_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    if request.freedict_de_en_path is None:
        raise ValueError("Missing FreeDict EN->ES path for es-en rule generation.")
    config = EsEnRulegenConfig(
        freedict_en_es_path=request.freedict_de_en_path,
        reverse_freedict_es_en_path=request.freedict_reverse_path,
        language_pair=request.language_pair,
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
