from __future__ import annotations

from typing import Mapping, Sequence


NOUN_LIKE_POS_TAGS = frozenset({"noun", "proper_noun"})
VERB_LIKE_POS_TAGS = frozenset({"verb"})
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
    if active_pos not in NOUN_LIKE_POS_TAGS or not shadow_pos_tags.intersection(VERB_LIKE_POS_TAGS):
        return ""
    preceding = str(preceding_token or "").strip().lower()
    following = str(following_token or "").strip().lower()
    if preceding in NOUN_FRAME_PRECEDING_TOKENS:
        return "active_noun_frame"
    if preceding and preceding not in NOUN_FRAME_PRECEDING_TOKENS:
        return "shadow_verb_frame"
    if not preceding and following in NOUN_FRAME_PRECEDING_TOKENS:
        return "shadow_verb_frame"
    return ""
