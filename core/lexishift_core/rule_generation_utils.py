from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Callable, Iterable, Optional

from lexishift_core.core import Tokenizer
from lexishift_core.inflect import InflectionGenerator, InflectionSpec, expand_phrase
from lexishift_core.rule_generation import RuleCandidate

_PUNCT_STRIP = ".,;:!?\"“”'’()[]{}<>"


@dataclass(frozen=True)
class BasicStringNormalizer:
    lower_case: bool = True
    strip_punctuation: bool = True
    collapse_whitespace: bool = True

    def normalize(self, candidate: RuleCandidate) -> RuleCandidate:
        text = candidate.source_phrase.strip()
        if self.strip_punctuation:
            text = text.strip(_PUNCT_STRIP)
        if self.collapse_whitespace:
            text = re.sub(r"\s+", " ", text)
        if self.lower_case:
            text = text.lower()
        return replace(candidate, source_phrase=text)


@dataclass(frozen=True)
class NonEmptyFilter:
    min_length: int = 1

    def accept(self, candidate: RuleCandidate) -> bool:
        text = candidate.source_phrase.strip()
        if len(text) < self.min_length:
            return False
        return bool(re.search(r"\w", text))


@dataclass(frozen=True)
class InflectionVariantExpander:
    spec: InflectionSpec = InflectionSpec()
    generator: InflectionGenerator = InflectionGenerator()
    tokenizer: Tokenizer = Tokenizer()
    should_expand: Optional[Callable[[RuleCandidate], bool]] = None
    metadata_key: str = "variant"
    metadata_value: str = "inflected"

    def expand(self, candidate: RuleCandidate) -> Iterable[RuleCandidate]:
        if self.should_expand and not self.should_expand(candidate):
            return [candidate]
        expanded = expand_phrase(
            candidate.source_phrase,
            generator=self.generator,
            spec=self.spec,
            tokenizer=self.tokenizer,
        )
        results = []
        for phrase in expanded:
            if phrase == candidate.source_phrase:
                results.append(candidate)
                continue
            metadata = dict(candidate.metadata)
            metadata[self.metadata_key] = self.metadata_value
            results.append(replace(candidate, source_phrase=phrase, metadata=metadata))
        return results or [candidate]
