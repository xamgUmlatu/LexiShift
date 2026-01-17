from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Optional

from lexishift_core.core import MeaningRule, Replacer, SynonymNormalizer, VocabPool


class ReplacementMode(Enum):
    EXACT = "exact"
    MEANING = "meaning"


@dataclass(frozen=True)
class ReplacementPipeline:
    exact: Replacer
    meaning: Optional[Replacer] = None

    def replace_text(self, text: str, *, mode: ReplacementMode = ReplacementMode.EXACT, with_stats: bool = False):
        if mode is ReplacementMode.MEANING and self.meaning is not None:
            return self.meaning.replace_text(text, with_stats=with_stats)
        return self.exact.replace_text(text, with_stats=with_stats)


def build_meaning_pool(
    base_pool: VocabPool,
    *,
    meaning_rules: Optional[Iterable[MeaningRule]] = None,
    synonyms: Optional[Mapping[str, str]] = None,
) -> VocabPool:
    normalizer = base_pool.normalizer
    if synonyms:
        normalizer = SynonymNormalizer(synonyms, fallback=normalizer)
    meaning_pool = VocabPool(base_pool.rules, tokenizer=base_pool.tokenizer, normalizer=normalizer)
    if meaning_rules:
        for rule in meaning_rules:
            meaning_pool.add_meaning_rule(rule)
    return meaning_pool


def compile_pipeline(
    base_pool: VocabPool,
    *,
    meaning_rules: Optional[Iterable[MeaningRule]] = None,
    synonyms: Optional[Mapping[str, str]] = None,
) -> ReplacementPipeline:
    exact = Replacer(base_pool)
    meaning: Optional[Replacer] = None
    if meaning_rules or synonyms:
        meaning_pool = build_meaning_pool(base_pool, meaning_rules=meaning_rules, synonyms=synonyms)
        meaning = Replacer(meaning_pool)
    return ReplacementPipeline(exact=exact, meaning=meaning)
