from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping, Sequence


_PHRASE_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ']+")
_PHRASE_MARKER_STOP_TOKENS = frozenset(
    {
        "a",
        "an",
        "are",
        "be",
        "been",
        "being",
        "her",
        "his",
        "is",
        "its",
        "my",
        "our",
        "that",
        "the",
        "their",
        "these",
        "this",
        "those",
        "was",
        "were",
        "will",
        "your",
    }
)


@dataclass(frozen=True)
class PhraseContainmentMatch:
    hit: bool
    example_text: str = ""
    pattern_text: str = ""
    reason_code: str = ""


@dataclass(frozen=True)
class _PhraseContainmentPattern:
    example_text: str
    pattern_text: str
    preceding_token: str
    following_token: str


def match_phrase_containment_examples(
    *,
    sentence: str,
    source_phrase: str,
    trigger: str,
    phrase_examples: Sequence[str],
) -> PhraseContainmentMatch:
    sentence_tokens = _phrase_tokens(sentence)
    phrase_tokens = _phrase_tokens(source_phrase or trigger)
    span = _find_phrase_span(sentence_tokens, phrase_tokens)
    if span is None:
        return PhraseContainmentMatch(hit=False)
    start_index, end_index = span
    preceding = sentence_tokens[start_index - 1] if start_index > 0 else ""
    following = sentence_tokens[end_index] if end_index < len(sentence_tokens) else ""
    for pattern in _phrase_containment_patterns(
        trigger=trigger,
        source_phrase=source_phrase,
        phrase_examples=phrase_examples,
    ):
        if pattern.preceding_token and pattern.following_token:
            if _marker_tokens_match(preceding, pattern.preceding_token) and _marker_tokens_match(
                following, pattern.following_token
            ):
                return PhraseContainmentMatch(
                    hit=True,
                    example_text=pattern.example_text,
                    pattern_text=pattern.pattern_text,
                    reason_code="example_phrase_trigram_containment",
                )
            continue
        if pattern.preceding_token and _marker_tokens_match(preceding, pattern.preceding_token):
            return PhraseContainmentMatch(
                hit=True,
                example_text=pattern.example_text,
                pattern_text=pattern.pattern_text,
                reason_code="example_phrase_left_containment",
            )
        if pattern.following_token and _marker_tokens_match(following, pattern.following_token):
            return PhraseContainmentMatch(
                hit=True,
                example_text=pattern.example_text,
                pattern_text=pattern.pattern_text,
                reason_code="example_phrase_right_containment",
            )
    return PhraseContainmentMatch(hit=False)


def add_phrase_containment_summary(
    summary: dict[str, object],
    rows: Sequence[Mapping[str, object]],
) -> None:
    containment_hits = [row for row in rows if bool(row.get("phrase_containment_hit"))]
    correct_abstains = [
        row
        for row in containment_hits
        if str(row.get("gold_decision") or "").strip() == "abstain"
        and str(row.get("predicted_decision") or "").strip() == "abstain"
    ]
    harmful_blocks = [
        row
        for row in containment_hits
        if str(row.get("gold_decision") or "").strip() == "replace"
        and str(row.get("predicted_decision") or "").strip() == "abstain"
    ]
    cases_total = int(summary.get("cases_total") or 0)
    summary["phrase_containment_hit_count"] = len(containment_hits)
    summary["phrase_containment_correct_abstain_count"] = len(correct_abstains)
    summary["phrase_containment_harmful_block_count"] = len(harmful_blocks)
    summary["phrase_containment_hit_rate"] = (
        len(containment_hits) / cases_total if cases_total else 0.0
    )


def _phrase_containment_patterns(
    *,
    trigger: str,
    source_phrase: str,
    phrase_examples: Sequence[str],
) -> list[_PhraseContainmentPattern]:
    trigger_tokens = _phrase_tokens(source_phrase or trigger)
    patterns: list[_PhraseContainmentPattern] = []
    for example in phrase_examples:
        example_text = str(example or "").strip()
        example_tokens = _phrase_tokens(example_text)
        for start_index, end_index in _find_all_phrase_spans(example_tokens, trigger_tokens):
            raw_preceding = example_tokens[start_index - 1] if start_index > 0 else ""
            raw_following = example_tokens[end_index] if end_index < len(example_tokens) else ""
            preceding = raw_preceding if raw_preceding not in _PHRASE_MARKER_STOP_TOKENS else ""
            following = raw_following if raw_following not in _PHRASE_MARKER_STOP_TOKENS else ""
            if not preceding and not following:
                continue
            pattern = _PhraseContainmentPattern(
                example_text=example_text,
                pattern_text=_format_phrase_pattern(
                    preceding=preceding,
                    source_phrase=" ".join(trigger_tokens),
                    following=following,
                ),
                preceding_token=preceding,
                following_token=following,
            )
            if pattern not in patterns:
                patterns.append(pattern)
    return patterns


def _format_phrase_pattern(*, preceding: str, source_phrase: str, following: str) -> str:
    pieces = [piece for piece in (preceding, source_phrase, following) if piece]
    return " ".join(pieces)


def _marker_tokens_match(left: str, right: str) -> bool:
    if left == right:
        return True
    return _singular_marker(left) == _singular_marker(right)


def _singular_marker(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if len(normalized) > 4 and normalized.endswith("ies"):
        return f"{normalized[:-3]}y"
    if len(normalized) > 3 and normalized.endswith("s") and not normalized.endswith("ss"):
        return normalized[:-1]
    return normalized


def _find_phrase_span(
    sentence_tokens: Sequence[str],
    phrase_tokens: Sequence[str],
) -> tuple[int, int] | None:
    spans = _find_all_phrase_spans(sentence_tokens, phrase_tokens)
    return spans[0] if spans else None


def _find_all_phrase_spans(
    sentence_tokens: Sequence[str],
    phrase_tokens: Sequence[str],
) -> list[tuple[int, int]]:
    normalized_phrase_tokens = [token for token in phrase_tokens if token]
    if not normalized_phrase_tokens:
        return []
    phrase_length = len(normalized_phrase_tokens)
    spans: list[tuple[int, int]] = []
    for index in range(0, len(sentence_tokens) - phrase_length + 1):
        if list(sentence_tokens[index : index + phrase_length]) == normalized_phrase_tokens:
            spans.append((index, index + phrase_length))
    return spans


def _phrase_tokens(text: str) -> list[str]:
    return [match.lower() for match in _PHRASE_TOKEN_RE.findall(str(text or ""))]
