from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional, Sequence

from .core import Tokenizer, VocabPool, VocabRule
from .inflect import InflectionGenerator, InflectionSpec, expand_phrase


@dataclass(frozen=True)
class BuildOptions:
    inflection_spec: Optional[InflectionSpec] = None
    inflection_overrides: Optional[Mapping[str, InflectionSpec]] = None
    inflection_generator: Optional[InflectionGenerator] = None
    tokenizer: Optional[Tokenizer] = None
    include_generated_tag: bool = True
    generated_tag: str = "generated"


def expand_vocab_rules(
    rules: Iterable[VocabRule],
    *,
    options: Optional[BuildOptions] = None,
) -> Sequence[VocabRule]:
    options = options or BuildOptions()
    tokenizer = options.tokenizer or Tokenizer()
    generator = options.inflection_generator or InflectionGenerator()
    base_spec = options.inflection_spec
    overrides = options.inflection_overrides or {}

    expanded: list[VocabRule] = []
    seen_sources: set[str] = set()
    for rule in rules:
        spec = overrides.get(rule.source_phrase) or base_spec
        if spec is None:
            _append_rule(rule, expanded, seen_sources)
            continue

        phrases = expand_phrase(
            rule.source_phrase,
            generator=generator,
            spec=spec,
            tokenizer=tokenizer,
        )
        for phrase in phrases:
            new_tags = rule.tags
            if options.include_generated_tag and phrase != rule.source_phrase:
                new_tags = tuple(rule.tags) + (options.generated_tag,)
            expanded_rule = VocabRule(
                source_phrase=phrase,
                replacement=rule.replacement,
                priority=rule.priority,
                case_policy=rule.case_policy,
                enabled=rule.enabled,
                tags=new_tags,
                metadata=rule.metadata,
            )
            _append_rule(expanded_rule, expanded, seen_sources)
    return tuple(expanded)


def build_vocab_pool(
    rules: Iterable[VocabRule],
    *,
    options: Optional[BuildOptions] = None,
    tokenizer: Optional[Tokenizer] = None,
    normalizer=None,
) -> VocabPool:
    expanded = expand_vocab_rules(rules, options=options)
    return VocabPool(expanded, tokenizer=tokenizer, normalizer=normalizer)


def _append_rule(rule: VocabRule, expanded: list[VocabRule], seen_sources: set[str]) -> None:
    if rule.source_phrase in seen_sources:
        return
    expanded.append(rule)
    seen_sources.add(rule.source_phrase)
