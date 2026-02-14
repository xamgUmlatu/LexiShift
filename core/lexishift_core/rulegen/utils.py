from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Callable, Iterable, Mapping, Optional, Sequence

from lexishift_core.replacement.core import Tokenizer
from lexishift_core.replacement.inflect import (
    FORM_PLURAL,
    InflectionGenerator,
    InflectionSpec,
    expand_phrase,
)
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
        morphology = candidate.metadata.get("morphology")
        if isinstance(morphology, Mapping):
            # Paired morphology expansion explicitly requested this variant.
            return True
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


@dataclass(frozen=True)
class PairedInflectionVariantExpander:
    forms: Sequence[str] = (FORM_PLURAL,)
    generator: InflectionGenerator = InflectionGenerator()
    tokenizer: Tokenizer = Tokenizer()
    should_expand: Optional[Callable[[RuleCandidate], bool]] = None
    target_surface_resolver: Optional[Callable[[RuleCandidate, str], Optional[str]]] = None
    variant_metadata_key: str = "variant"
    variant_metadata_value: str = "inflected"
    morphology_metadata_key: str = "morphology"

    def expand(self, candidate: RuleCandidate) -> Iterable[RuleCandidate]:
        if self.should_expand and not self.should_expand(candidate):
            return [candidate]
        tokens = self.tokenizer.tokenize(candidate.source_phrase)
        word_indices = [index for index, token in enumerate(tokens) if token.kind == "word"]
        if not word_indices:
            return [candidate]

        target_index = word_indices[-1]
        base_word = tokens[target_index].text
        if not base_word:
            return [candidate]

        results: list[RuleCandidate] = [candidate]
        seen_phrases = {candidate.source_phrase}
        for form in self.forms:
            generated_words = self.generator.generate(base_word, (form,))
            for inflected_word in generated_words:
                if not inflected_word or inflected_word == base_word:
                    continue
                updated_tokens = list(tokens)
                updated_tokens[target_index] = replace(updated_tokens[target_index], text=inflected_word)
                source_phrase = "".join(token.text for token in updated_tokens)
                if source_phrase in seen_phrases:
                    continue
                seen_phrases.add(source_phrase)
                target_surface = None
                if self.target_surface_resolver:
                    target_surface = self.target_surface_resolver(candidate, str(form))
                    if not target_surface:
                        continue
                metadata = dict(candidate.metadata)
                metadata[self.variant_metadata_key] = self.variant_metadata_value
                morphology = _normalize_morphology(metadata.get(self.morphology_metadata_key))
                morphology["source_form"] = str(form)
                morphology["source_phrase_base"] = candidate.source_phrase
                if target_surface:
                    morphology["target_surface"] = str(target_surface).strip()
                    morphology["target_lemma"] = candidate.replacement
                metadata[self.morphology_metadata_key] = morphology
                results.append(
                    replace(
                        candidate,
                        source_phrase=source_phrase,
                        metadata=metadata,
                    )
                )
        return results


def _normalize_morphology(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, object] = {}
    for key, raw in dict(value).items():
        name = str(key or "").strip()
        if not name:
            continue
        normalized[name] = raw
    return normalized
