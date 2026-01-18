from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable, List, Mapping, Optional, Sequence


@dataclass(frozen=True)
class Token:
    text: str
    kind: str  # "word", "space", "punct"


class Tokenizer:
    _token_re = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*|\s+|[^\w\s]+")
    _word_re = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*\Z")

    def tokenize(self, text: str) -> List[Token]:
        tokens: List[Token] = []
        for match in self._token_re.finditer(text):
            chunk = match.group(0)
            if self._word_re.match(chunk):
                kind = "word"
            elif chunk.isspace():
                kind = "space"
            else:
                kind = "punct"
            tokens.append(Token(text=chunk, kind=kind))
        return tokens


class Normalizer:
    def normalize_word(self, word: str) -> str:
        return word.lower()


class SynonymNormalizer(Normalizer):
    def __init__(self, synonyms: Mapping[str, str], *, fallback: Optional[Normalizer] = None) -> None:
        self._fallback = fallback or Normalizer()
        self._synonyms = {
            self._fallback.normalize_word(key): self._fallback.normalize_word(value)
            for key, value in synonyms.items()
        }

    def normalize_word(self, word: str) -> str:
        base = self._fallback.normalize_word(word)
        return self._synonyms.get(base, base)


@dataclass(frozen=True)
class RuleMetadata:
    label: Optional[str] = None
    description: Optional[str] = None
    examples: Sequence[str] = field(default_factory=tuple)
    notes: Optional[str] = None
    source: Optional[str] = None


@dataclass(frozen=True)
class VocabRule:
    source_phrase: str
    replacement: str
    priority: int = 0
    case_policy: str = "match"  # match, as-is, lower, upper, title
    enabled: bool = True
    tags: Sequence[str] = field(default_factory=tuple)
    metadata: Optional[RuleMetadata] = None
    created_at: Optional[str] = None

    def tokens(self, tokenizer: Tokenizer, normalizer: Normalizer) -> List[str]:
        words = [t.text for t in tokenizer.tokenize(self.source_phrase) if t.kind == "word"]
        return [normalizer.normalize_word(word) for word in words]


@dataclass(frozen=True)
class MeaningRule:
    source_phrases: Sequence[str]
    replacement: str
    priority: int = 0
    case_policy: str = "match"
    enabled: bool = True
    tags: Sequence[str] = field(default_factory=tuple)
    metadata: Optional[RuleMetadata] = None

    def to_vocab_rules(self) -> List[VocabRule]:
        return [
            VocabRule(
                source_phrase=phrase,
                replacement=self.replacement,
                priority=self.priority,
                case_policy=self.case_policy,
                enabled=self.enabled,
                tags=self.tags,
                metadata=self.metadata,
            )
            for phrase in self.source_phrases
        ]


class PhraseTrieNode:
    __slots__ = ("children", "best_rule")

    def __init__(self) -> None:
        self.children: dict[str, PhraseTrieNode] = {}
        self.best_rule: Optional[VocabRule] = None


class PhraseTrie:
    def __init__(self) -> None:
        self.root = PhraseTrieNode()

    def add(self, tokens: Sequence[str], rule: VocabRule) -> None:
        node = self.root
        for token in tokens:
            node = node.children.setdefault(token, PhraseTrieNode())
        if node.best_rule is None or rule.priority > node.best_rule.priority:
            node.best_rule = rule


class VocabPool:
    def __init__(
        self,
        rules: Optional[Iterable[VocabRule]] = None,
        *,
        tokenizer: Optional[Tokenizer] = None,
        normalizer: Optional[Normalizer] = None,
    ) -> None:
        self._rules: List[VocabRule] = list(rules) if rules else []
        self._tokenizer = tokenizer or Tokenizer()
        self._normalizer = normalizer or Normalizer()
        self._trie: Optional[PhraseTrie] = None
        self._dirty = True

    @classmethod
    def from_mapping(
        cls,
        mapping: dict[str, str],
        *,
        tokenizer: Optional[Tokenizer] = None,
        normalizer: Optional[Normalizer] = None,
    ) -> "VocabPool":
        rules = [VocabRule(source, replacement) for source, replacement in mapping.items()]
        return cls(rules, tokenizer=tokenizer, normalizer=normalizer)

    def add_rule(self, rule: VocabRule) -> None:
        self._rules.append(rule)
        self._dirty = True

    def add_meaning_rule(self, rule: MeaningRule) -> None:
        self._rules.extend(rule.to_vocab_rules())
        self._dirty = True

    def compile(self) -> None:
        trie = PhraseTrie()
        for rule in self._rules:
            if not rule.enabled:
                continue
            tokens = rule.tokens(self._tokenizer, self._normalizer)
            if not tokens:
                continue
            trie.add(tokens, rule)
        self._trie = trie
        self._dirty = False

    def clone(
        self,
        *,
        tokenizer: Optional[Tokenizer] = None,
        normalizer: Optional[Normalizer] = None,
    ) -> "VocabPool":
        return VocabPool(
            self._rules,
            tokenizer=tokenizer or self._tokenizer,
            normalizer=normalizer or self._normalizer,
        )

    @property
    def rules(self) -> Sequence[VocabRule]:
        return tuple(self._rules)

    @property
    def trie(self) -> PhraseTrie:
        if self._dirty or self._trie is None:
            self.compile()
        return self._trie

    @property
    def normalizer(self) -> Normalizer:
        return self._normalizer

    @property
    def tokenizer(self) -> Tokenizer:
        return self._tokenizer


@dataclass(frozen=True)
class Match:
    start_word_index: int
    end_word_index: int
    rule: VocabRule


@dataclass(frozen=True)
class ReplacementResult:
    text: str
    matches: List[Match]


class Replacer:
    def __init__(self, vocab_pool: VocabPool) -> None:
        self._pool = vocab_pool

    def replace_text(self, text: str, *, with_stats: bool = False) -> str | ReplacementResult:
        tokens = self._pool.tokenizer.tokenize(text)
        word_positions = [idx for idx, token in enumerate(tokens) if token.kind == "word"]
        word_texts = [tokens[idx].text for idx in word_positions]
        gap_ok = self._compute_word_gaps_ok(tokens, word_positions)

        matches: List[Match] = []
        word_index = 0
        while word_index < len(word_texts):
            match = self._find_longest_match(word_texts, gap_ok, word_index)
            if match:
                matches.append(match)
                word_index = match.end_word_index + 1
            else:
                word_index += 1

        replaced_text = self._apply_matches(tokens, word_positions, word_texts, matches)
        if with_stats:
            return ReplacementResult(text=replaced_text, matches=matches)
        return replaced_text

    def _compute_word_gaps_ok(self, tokens: Sequence[Token], word_positions: Sequence[int]) -> List[bool]:
        gap_ok: List[bool] = []
        for idx in range(len(word_positions) - 1):
            start = word_positions[idx] + 1
            end = word_positions[idx + 1]
            ok = True
            for token in tokens[start:end]:
                if token.kind != "space":
                    ok = False
                    break
            gap_ok.append(ok)
        return gap_ok

    def _find_longest_match(
        self,
        words: Sequence[str],
        gap_ok: Sequence[bool],
        start_index: int,
    ) -> Optional[Match]:
        node = self._pool.trie.root
        best_rule: Optional[VocabRule] = None
        best_end: Optional[int] = None
        best_priority = -1

        for idx in range(start_index, len(words)):
            if idx > start_index and not gap_ok[idx - 1]:
                break
            normalized = self._pool.normalizer.normalize_word(words[idx])
            node = node.children.get(normalized)
            if node is None:
                break
            if node.best_rule and node.best_rule.priority >= best_priority:
                if node.best_rule.priority > best_priority or best_end is None or idx > best_end:
                    best_rule = node.best_rule
                    best_end = idx
                    best_priority = node.best_rule.priority

        if best_rule is None or best_end is None:
            return None
        return Match(start_word_index=start_index, end_word_index=best_end, rule=best_rule)

    def _apply_matches(
        self,
        tokens: Sequence[Token],
        word_positions: Sequence[int],
        word_texts: Sequence[str],
        matches: Sequence[Match],
    ) -> str:
        output_parts: List[str] = []
        token_cursor = 0
        for match in matches:
            start_token_idx = word_positions[match.start_word_index]
            end_token_idx = word_positions[match.end_word_index]

            output_parts.extend(token.text for token in tokens[token_cursor:start_token_idx])

            source_words = word_texts[match.start_word_index : match.end_word_index + 1]
            replacement_text = _apply_case(match.rule.replacement, source_words, match.rule.case_policy)
            output_parts.append(replacement_text)

            token_cursor = end_token_idx + 1

        output_parts.extend(token.text for token in tokens[token_cursor:])
        return "".join(output_parts)


def _apply_case(replacement: str, source_words: Sequence[str], policy: str) -> str:
    if policy == "as-is":
        return replacement
    if policy == "lower":
        return replacement.lower()
    if policy == "upper":
        return replacement.upper()
    if policy == "title":
        return replacement.title()
    if policy == "match":
        source_text = " ".join(source_words)
        if source_text.isupper():
            return replacement.upper()
        if source_words and source_words[0][:1].isupper():
            return replacement.title()
    return replacement
