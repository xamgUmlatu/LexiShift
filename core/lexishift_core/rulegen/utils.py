from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Callable, Iterable, Optional, Sequence

from lexishift_core.core import Tokenizer
from lexishift_core.inflect import InflectionGenerator, InflectionSpec, expand_phrase
from lexishift_core.rulegen.generation import RuleCandidate

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
class SingleWordFilter:
    allow_hyphen: bool = True

    def accept(self, candidate: RuleCandidate) -> bool:
        phrase = candidate.source_phrase.strip()
        if not phrase:
            return False
        if any(ch.isspace() for ch in phrase):
            return False
        if not self.allow_hyphen and "-" in phrase:
            return False
        return True


@dataclass(frozen=True)
class LengthFilter:
    min_length: int = 2
    max_length: Optional[int] = None

    def accept(self, candidate: RuleCandidate) -> bool:
        text = candidate.source_phrase.strip()
        if len(text) < self.min_length:
            return False
        if self.max_length is not None and len(text) > self.max_length:
            return False
        return True


@dataclass(frozen=True)
class PunctuationFilter:
    allowed_pattern: str = r"^[a-z0-9-]+$"
    _compiled: re.Pattern = re.compile(r"^[a-z0-9-]+$")

    def __post_init__(self) -> None:
        object.__setattr__(self, "_compiled", re.compile(self.allowed_pattern))

    def accept(self, candidate: RuleCandidate) -> bool:
        phrase = candidate.source_phrase.strip()
        return bool(self._compiled.match(phrase))


@dataclass(frozen=True)
class PossessiveFilter:
    suffixes: Sequence[str] = ("'s", "’s")

    def accept(self, candidate: RuleCandidate) -> bool:
        phrase = candidate.source_phrase.strip()
        return not any(phrase.endswith(suffix) for suffix in self.suffixes)


@dataclass(frozen=True)
class StopwordFilter:
    stopwords: set[str]

    def accept(self, candidate: RuleCandidate) -> bool:
        phrase = candidate.source_phrase.strip()
        return phrase not in self.stopwords


@dataclass(frozen=True)
class InflectionArtifactFilter:
    suffixes: Sequence[str] = ("s", "es", "ed", "ing")
    base_forms: Optional[set[str]] = None
    min_base_length: int = 2

    def accept(self, candidate: RuleCandidate) -> bool:
        phrase = candidate.source_phrase.strip()
        if not self.base_forms:
            return True
        for suffix in self.suffixes:
            if not phrase.endswith(suffix):
                continue
            base = phrase[: -len(suffix)]
            if len(base) < self.min_base_length:
                continue
            if base in self.base_forms:
                return False
        return True


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
