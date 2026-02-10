from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.replacement.core import Tokenizer

FORM_PLURAL = "plural"
FORM_POSSESSIVE = "possessive"
FORM_PAST = "past"
FORM_GERUND = "gerund"
FORM_THIRD_PERSON = "third_person"

DEFAULT_FORMS = frozenset(
    {
        FORM_PLURAL,
        FORM_POSSESSIVE,
        FORM_PAST,
        FORM_GERUND,
        FORM_THIRD_PERSON,
    }
)


@dataclass(frozen=True)
class InflectionSpec:
    forms: frozenset[str] = DEFAULT_FORMS
    apply_to: str = "last_word"  # last_word, all_words
    include_original: bool = True


@dataclass(frozen=True)
class InflectionOverrides:
    plurals: Mapping[str, str] = field(default_factory=dict)
    past: Mapping[str, str] = field(default_factory=dict)
    gerunds: Mapping[str, str] = field(default_factory=dict)
    third_person: Mapping[str, str] = field(default_factory=dict)
    blocked: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class InflectionGenerator:
    overrides: Optional[InflectionOverrides] = None
    strict: bool = True

    def generate(self, word: str, forms: Iterable[str]) -> frozenset[str]:
        results = set()
        overrides = self.overrides or InflectionOverrides()
        requested = set(forms)
        if FORM_PLURAL in requested:
            results.update(self._pluralize(word, overrides))
        if FORM_POSSESSIVE in requested:
            results.update(self._possessive(word))
        if FORM_PAST in requested:
            results.update(self._past_tense(word, overrides))
        if FORM_GERUND in requested:
            results.update(self._gerund(word, overrides))
        if FORM_THIRD_PERSON in requested:
            results.update(self._third_person(word, overrides))
        results.difference_update(overrides.blocked)
        return frozenset(results)

    def _pluralize(self, word: str, overrides: InflectionOverrides) -> Sequence[str]:
        irregular = overrides.plurals.get(word) or _IRREGULAR_PLURALS.get(word)
        if irregular:
            return [irregular]
        if word.endswith(("s", "x", "z", "ch", "sh")):
            return [word + "es"]
        if _ends_with_consonant_y(word):
            return [word[:-1] + "ies"]
        return [word + "s"]

    def _possessive(self, word: str) -> Sequence[str]:
        if word.endswith("s"):
            return [word + "'"]
        return [word + "'s"]

    def _past_tense(self, word: str, overrides: InflectionOverrides) -> Sequence[str]:
        irregular = overrides.past.get(word) or _IRREGULAR_PAST.get(word)
        if irregular:
            return [irregular]
        if self.strict and _needs_consonant_doubling(word):
            return []
        if word.endswith("e"):
            return [word + "d"]
        if _ends_with_consonant_y(word):
            return [word[:-1] + "ied"]
        return [word + "ed"]

    def _gerund(self, word: str, overrides: InflectionOverrides) -> Sequence[str]:
        irregular = overrides.gerunds.get(word) or _IRREGULAR_GERUND.get(word)
        if irregular:
            return [irregular]
        if self.strict and _needs_consonant_doubling(word):
            return []
        if word.endswith("ie"):
            return [word[:-2] + "ying"]
        if word.endswith("e") and not word.endswith(("ee", "ye", "oe")):
            return [word[:-1] + "ing"]
        return [word + "ing"]

    def _third_person(self, word: str, overrides: InflectionOverrides) -> Sequence[str]:
        irregular = overrides.third_person.get(word) or _IRREGULAR_THIRD_PERSON.get(word)
        if irregular:
            return [irregular]
        if word.endswith(("s", "x", "z", "ch", "sh")):
            return [word + "es"]
        if _ends_with_consonant_y(word):
            return [word[:-1] + "ies"]
        return [word + "s"]


def expand_phrase(
    phrase: str,
    *,
    generator: Optional[InflectionGenerator] = None,
    spec: Optional[InflectionSpec] = None,
    tokenizer: Optional[Tokenizer] = None,
) -> frozenset[str]:
    generator = generator or InflectionGenerator()
    spec = spec or InflectionSpec()
    tokenizer = tokenizer or Tokenizer()
    tokens = tokenizer.tokenize(phrase)
    word_indices = [idx for idx, token in enumerate(tokens) if token.kind == "word"]
    if not word_indices:
        return frozenset({phrase}) if spec.include_original else frozenset()

    targets = word_indices[-1:] if spec.apply_to == "last_word" else word_indices
    expansions = set()
    if spec.include_original:
        expansions.add(phrase)
    for target_index in targets:
        base_word = tokens[target_index].text
        for form in generator.generate(base_word, spec.forms):
            tokens[target_index] = tokens[target_index].__class__(text=form, kind="word")
            expansions.add("".join(token.text for token in tokens))
        tokens[target_index] = tokens[target_index].__class__(text=base_word, kind="word")
    return frozenset(expansions)


def _ends_with_consonant_y(word: str) -> bool:
    return len(word) > 1 and word.endswith("y") and _is_consonant(word[-2])


def _is_consonant(ch: str) -> bool:
    return ch.lower() not in {"a", "e", "i", "o", "u"}


def _needs_consonant_doubling(word: str) -> bool:
    if len(word) < 3:
        return False
    last = word[-1].lower()
    if last in {"w", "x", "y"}:
        return False
    if not _is_consonant(last):
        return False
    if _is_consonant(word[-2]):
        return False
    if not _is_consonant(word[-3]):
        return False
    return True


_IRREGULAR_PLURALS = {
    "child": "children",
    "foot": "feet",
    "goose": "geese",
    "man": "men",
    "mouse": "mice",
    "person": "people",
    "tooth": "teeth",
    "woman": "women",
}

_IRREGULAR_PAST = {
    "be": "was",
    "begin": "began",
    "come": "came",
    "do": "did",
    "drink": "drank",
    "eat": "ate",
    "feel": "felt",
    "get": "got",
    "give": "gave",
    "go": "went",
    "have": "had",
    "keep": "kept",
    "know": "knew",
    "leave": "left",
    "make": "made",
    "run": "ran",
    "say": "said",
    "see": "saw",
    "take": "took",
    "think": "thought",
    "write": "wrote",
}

_IRREGULAR_GERUND = {
    "be": "being",
    "lie": "lying",
    "tie": "tying",
}

_IRREGULAR_THIRD_PERSON = {
    "be": "is",
    "do": "does",
    "go": "goes",
    "have": "has",
}
