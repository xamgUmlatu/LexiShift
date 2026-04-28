from __future__ import annotations

from typing import Mapping, Sequence


NOUN_LIKE_POS_TAGS = frozenset({"noun", "proper_noun"})
VERB_LIKE_POS_TAGS = frozenset({"verb"})
ADJECTIVE_LIKE_POS_TAGS = frozenset({"adjective", "adverb"})
NON_VERB_ACTIVE_POS_TAGS = NOUN_LIKE_POS_TAGS | ADJECTIVE_LIKE_POS_TAGS
NOUN_FRAME_PRECEDING_TOKENS = frozenset(
    {
        "a",
        "an",
        "her",
        "his",
        "my",
        "our",
        "that",
        "the",
        "their",
        "these",
        "this",
        "those",
        "your",
    }
)
VERB_FRAME_TRIGGER_TOKENS = frozenset(
    {
        "can",
        "cannot",
        "can't",
        "could",
        "may",
        "might",
        "must",
        "please",
        "shall",
        "should",
        "to",
        "will",
        "would",
    }
)
VERB_FRAME_FOLLOWING_PREPOSITION_TOKENS = frozenset(
    {
        "after",
        "at",
        "before",
        "beside",
        "by",
        "during",
        "for",
        "from",
        "in",
        "into",
        "near",
        "off",
        "on",
        "out",
        "over",
        "past",
        "through",
        "to",
        "toward",
        "up",
        "with",
        "within",
        "without",
    }
)
VERB_FRAME_IDIOM_PRECEDING_TOKENS = frozenset({"held", "hold", "holds"})
NOUN_FRAME_FOLLOWING_AUXILIARY_TOKENS = frozenset(
    {
        "are",
        "be",
        "became",
        "become",
        "becomes",
        "been",
        "being",
        "is",
        "remain",
        "remained",
        "remains",
        "was",
        "were",
    }
)
NOUN_FRAME_FOLLOWING_IRREGULAR_PREDICATE_TOKENS = frozenset(
    {
        "began",
        "broke",
        "came",
        "drew",
        "fell",
        "grew",
        "lay",
        "left",
        "ran",
        "rose",
        "sang",
        "sat",
        "stood",
        "swam",
        "took",
        "was",
        "went",
        "won",
        "wrote",
    }
)
NOUN_FRAME_PREPOSITIONAL_COMPLEMENT_TOKENS = frozenset({"of"})


def surface_pos_signal(
    *,
    active_sense: Mapping[str, object],
    shadow_examples: Sequence[tuple[Mapping[str, object], str]],
    preceding_token: str,
    following_token: str,
) -> str:
    active_pos = str(active_sense.get("canonical_pos") or "").strip().lower()
    shadow_pos_tags = {
        str(shadow.get("canonical_pos") or "").strip().lower()
        for shadow, _example in shadow_examples
        if str(shadow.get("canonical_pos") or "").strip()
    }
    if active_pos not in NON_VERB_ACTIVE_POS_TAGS:
        return ""
    has_verb_shadow = bool(shadow_pos_tags.intersection(VERB_LIKE_POS_TAGS))
    preceding = str(preceding_token or "").strip().lower()
    following = str(following_token or "").strip().lower()
    if active_pos in NON_VERB_ACTIVE_POS_TAGS and _looks_like_clear_verb_frame(
        preceding=preceding,
        following=following,
        active_pos=active_pos,
    ):
        return "shadow_verb_frame"
    if active_pos in ADJECTIVE_LIKE_POS_TAGS and _looks_like_active_modifier_frame(
        preceding=preceding,
        following=following,
    ):
        return "active_modifier_frame"
    if active_pos not in NOUN_LIKE_POS_TAGS or not has_verb_shadow:
        return ""
    if preceding in NOUN_FRAME_PRECEDING_TOKENS:
        return "active_noun_frame"
    if following in NOUN_FRAME_PREPOSITIONAL_COMPLEMENT_TOKENS:
        return "active_noun_frame"
    if preceding in NOUN_FRAME_PREPOSITIONAL_COMPLEMENT_TOKENS:
        return "active_noun_frame"
    if preceding and _looks_like_noun_subject_predicate(following):
        return "active_noun_frame"
    if preceding and preceding not in NOUN_FRAME_PRECEDING_TOKENS:
        return "shadow_verb_frame"
    if not preceding and following in NOUN_FRAME_PRECEDING_TOKENS:
        return "shadow_verb_frame"
    return ""


def active_noun_rescue_shadow_context_is_verb_like(
    *,
    strongest_shadow_sense: Mapping[str, object],
    shadow_examples: Sequence[tuple[Mapping[str, object], str]],
) -> bool:
    strongest_pos = str(strongest_shadow_sense.get("canonical_pos") or "").strip().lower()
    if strongest_pos:
        return strongest_pos == "verb"
    shadow_pos_tags = {
        str(shadow.get("canonical_pos") or "").strip().lower()
        for shadow, _example in shadow_examples
        if str(shadow.get("canonical_pos") or "").strip()
    }
    return bool(shadow_pos_tags) and shadow_pos_tags == {"verb"}


def _looks_like_noun_subject_predicate(token: str) -> bool:
    normalized = str(token or "").strip().lower()
    if normalized in NOUN_FRAME_FOLLOWING_AUXILIARY_TOKENS:
        return True
    if normalized in NOUN_FRAME_FOLLOWING_IRREGULAR_PREDICATE_TOKENS:
        return True
    return len(normalized) > 3 and normalized.endswith("ed")


def _looks_like_clear_verb_frame(*, preceding: str, following: str, active_pos: str) -> bool:
    if preceding in VERB_FRAME_TRIGGER_TOKENS and following:
        return True
    if (
        active_pos in ADJECTIVE_LIKE_POS_TAGS
        and preceding in VERB_FRAME_IDIOM_PRECEDING_TOKENS
        and following == "to"
    ):
        return True
    if active_pos not in NOUN_LIKE_POS_TAGS:
        return False
    if (
        preceding
        and preceding not in NOUN_FRAME_PRECEDING_TOKENS
        and preceding not in NOUN_FRAME_PREPOSITIONAL_COMPLEMENT_TOKENS
        and following in VERB_FRAME_FOLLOWING_PREPOSITION_TOKENS
        and following not in NOUN_FRAME_PREPOSITIONAL_COMPLEMENT_TOKENS
    ):
        return True
    return False


def _looks_like_active_modifier_frame(*, preceding: str, following: str) -> bool:
    if preceding not in NOUN_FRAME_PRECEDING_TOKENS:
        return False
    if not following:
        return False
    if following in NOUN_FRAME_PRECEDING_TOKENS:
        return False
    if following in VERB_FRAME_FOLLOWING_PREPOSITION_TOKENS:
        return False
    if _looks_like_noun_subject_predicate(following):
        return False
    return True
