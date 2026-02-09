from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Sequence

from lexishift_core.core import VocabRule
from lexishift_core.lp_capabilities import resolve_pair_capability
from lexishift_core.rule_generation_en_de import EnDeRulegenConfig, generate_en_de_results
from lexishift_core.rule_generation_ja_en import JaEnRulegenConfig, generate_ja_en_results
from lexishift_core.weighting import GlossDecay


@dataclass(frozen=True)
class RulegenAdapterRequest:
    pair: str
    targets: Sequence[str]
    language_pair: str
    confidence_threshold: float = 0.0
    include_variants: bool = True
    allow_multiword_glosses: bool = False
    gloss_decay: GlossDecay = field(default_factory=GlossDecay)
    jmdict_path: Optional[Path] = None
    freedict_de_en_path: Optional[Path] = None


RulegenAdapter = Callable[[RulegenAdapterRequest], Sequence[VocabRule]]


def _run_ja_en_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    if request.jmdict_path is None:
        raise ValueError("Missing JMDict path for en-ja rule generation.")
    config = JaEnRulegenConfig(
        jmdict_path=request.jmdict_path,
        language_pair=request.language_pair,
        confidence_threshold=request.confidence_threshold,
        include_variants=request.include_variants,
        allow_multiword_glosses=request.allow_multiword_glosses,
        gloss_decay=request.gloss_decay,
    )
    results = generate_ja_en_results(request.targets, config=config)
    return [result.rule for result in results]


def _run_en_de_adapter(request: RulegenAdapterRequest) -> Sequence[VocabRule]:
    if request.freedict_de_en_path is None:
        raise ValueError("Missing FreeDict DE->EN path for en-de rule generation.")
    config = EnDeRulegenConfig(
        freedict_de_en_path=request.freedict_de_en_path,
        language_pair=request.language_pair,
        confidence_threshold=request.confidence_threshold,
        include_variants=request.include_variants,
        allow_multiword_glosses=request.allow_multiword_glosses,
        gloss_decay=request.gloss_decay,
    )
    results = generate_en_de_results(request.targets, config=config)
    return [result.rule for result in results]


_RULEGEN_ADAPTERS: dict[str, RulegenAdapter] = {
    "ja_en": _run_ja_en_adapter,
    "en_de": _run_en_de_adapter,
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
