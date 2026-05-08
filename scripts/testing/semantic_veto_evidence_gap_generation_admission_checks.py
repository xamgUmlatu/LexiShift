from __future__ import annotations

import re


LABEL_LEAKAGE_TERMS = (
    "active evidence expansion",
    "shadow or competitor evidence",
    "no winner context",
    "positive active",
    "shadow negative",
    "phrase no winner",
    "competitor sense",
    "target lemma",
    "allow",
)


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


NO_WINNER_CONTEXT_ANCHORS = {
    "proper_name_or_title": ("called", "named", "title", "song", "album", "book"),
    "code_or_identifier": ("code", "identifier", "project", "label", "file", "sku"),
    "quoted_or_mentioned_word": ("word", "term", "spelled", "phrase", "quoted"),
    "unrelated_named_entity": ("company", "brand", "restaurant", "team", "product"),
    "source_language_meta_use": ("english", "translation", "vocabulary", "dictionary"),
    "ui_label": ("menu", "label", "button", "tab", "toolbar"),
}
WEAK_NO_WINNER_CONTAINER_TERMS = (
    "dashboard",
    "file named",
    "listed",
    "internal project code",
    "placeholder",
    "example sentence",
)


def _contains_runtime_trigger(sentence: str, term: str) -> bool:
    term = term.strip()
    if not term:
        return False
    pattern = r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])"
    return re.search(pattern, sentence, flags=re.IGNORECASE) is not None


def _contains_loose_lemma(text: str, lemma: str) -> bool:
    normalized_text = _normalize_text(text)
    normalized_lemma = _normalize_text(lemma)
    if not normalized_text or not normalized_lemma:
        return False
    return normalized_lemma in normalized_text


def _contains_negative_judgment(text: str) -> bool:
    normalized_text = _normalize_text(text)
    return any(
        phrase in normalized_text
        for phrase in (
            "does not fit",
            "is less natural",
            "is wrong",
            "not fit",
            "too general",
            "wrong",
        )
    )


def _has_label_leakage(sentence: str, *, source_phrase: str = "") -> bool:
    normalized_sentence = _normalize_text(sentence)
    normalized_source = _normalize_text(source_phrase)
    for term in LABEL_LEAKAGE_TERMS:
        if _normalize_text(term) == normalized_source:
            continue
        if " " in term:
            if term in normalized_sentence:
                return True
        elif _contains_runtime_trigger(sentence, term):
            return True
    return False


def _has_weak_no_winner_container(sentence: str) -> bool:
    normalized_sentence = _normalize_text(sentence)
    return any(term in normalized_sentence for term in WEAK_NO_WINNER_CONTAINER_TERMS)


def _has_no_winner_context_anchor(*, sentence: str, context_class: str) -> bool:
    normalized_sentence = _normalize_text(sentence)
    anchors = NO_WINNER_CONTEXT_ANCHORS.get(context_class, ())
    if any(anchor in normalized_sentence for anchor in anchors):
        return True
    if context_class in {"literal_fragment", "quoted_user_text", "name_or_title", "page_title"}:
        return '"' in sentence or "'" in sentence
    return False


def _normalize_no_winner_context_class(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", "_").split())
