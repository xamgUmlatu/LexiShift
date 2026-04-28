#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: F405

from semantic_decision_rule_matrix_common import *  # noqa: F403


def _build_matrix_context_views(
    sentence: str,
    *,
    source_phrase: str,
    mask_token: str,
    window_tokens: int,
) -> dict[str, str]:
    views = dict(
        build_runtime_context_views(
            sentence,
            source_phrase=source_phrase,
            mask_token=mask_token,
            window_tokens=window_tokens,
        )
    )
    tokens = _tokenize_experiment_text(sentence)
    phrase_tokens = _tokenize_experiment_text(source_phrase)
    span = _find_token_span(tokens, phrase_tokens)
    if span is None:
        span = _find_mask_span(_tokenize_experiment_text(views.get("masked_sentence", "")))
    if span is None:
        window = _tokenize_experiment_text(views.get("masked_window") or sentence)
        masked_window = window
        before: list[str] = []
        after: list[str] = []
    else:
        start, end = span
        left = tokens[max(0, start - max(0, int(window_tokens))) : start]
        right = tokens[end : min(len(tokens), end + max(0, int(window_tokens)))]
        masked_window = [*left, mask_token, *right]
        before = left
        after = right

    views.update(
        {
            "ordered_ngram_context": _ordered_ngram_text(masked_window),
            "skipgram_context": _skipgram_text(masked_window),
            "before_after_slot_context": _before_after_slot_text(before, after),
            "surface_frame_context": _surface_frame_text(before, after, mask_token=mask_token),
            "pos_frame_context": _pos_frame_text(masked_window, mask_token=mask_token),
            "dependency_role_context": _dependency_role_text(
                before,
                after,
                mask_token=mask_token,
            ),
            "negation_modal_context": _negation_modal_text(masked_window),
            "shuffled_context_tokens": _deterministic_shuffle_text(
                masked_window, seed=source_phrase
            ),
            "reversed_context_tokens": " ".join(reversed(masked_window)),
            "lexical_only_without_frame": " ".join(sorted(set(masked_window))),
            "frame_only_without_lexical_content": _frame_only_text(
                masked_window, mask_token=mask_token
            ),
        }
    )
    return views


def _selector_context_text(
    context_views: Mapping[str, object],
    *,
    config: Mapping[str, object],
) -> str:
    selector_view = str(
        config.get("evidence_selector_context_view")
        or config.get("context_view")
        or "masked_sentence"
    ).strip()
    return str(
        context_views.get(selector_view) or context_views.get("masked_sentence") or ""
    ).strip()


def _tokenize_experiment_text(value: object) -> list[str]:
    return [match.group(0).casefold() for match in _EXPERIMENT_TOKEN_RE.finditer(str(value or ""))]


def _find_token_span(tokens: Sequence[str], phrase_tokens: Sequence[str]) -> tuple[int, int] | None:
    if not tokens or not phrase_tokens:
        return None
    phrase = [token.casefold() for token in phrase_tokens]
    width = len(phrase)
    for index in range(0, len(tokens) - width + 1):
        if [token.casefold() for token in tokens[index : index + width]] == phrase:
            return index, index + width
    return None


def _find_mask_span(tokens: Sequence[str]) -> tuple[int, int] | None:
    for index, token in enumerate(tokens):
        if token == DEFAULT_SENTENCE_VETO_MASK_TOKEN:
            return index, index + 1
    return None


def _ordered_ngram_text(tokens: Sequence[str]) -> str:
    materialized = [token for token in tokens if token]
    parts: list[str] = []
    for size in (2, 3):
        for index in range(0, max(0, len(materialized) - size + 1)):
            parts.append(f"ng{size}=" + "_".join(materialized[index : index + size]))
    return " | ".join(parts) or " ".join(materialized)


def _skipgram_text(tokens: Sequence[str]) -> str:
    materialized = [token for token in tokens if token]
    parts: list[str] = []
    max_gap = 2
    for index, left in enumerate(materialized):
        for right_index in range(index + 1, min(len(materialized), index + max_gap + 2)):
            parts.append(f"skip={left}>{materialized[right_index]}")
    return " | ".join(parts) or " ".join(materialized)


def _before_after_slot_text(before: Sequence[str], after: Sequence[str]) -> str:
    left = list(before)[-3:]
    right = list(after)[:3]
    parts = [f"left{len(left) - index}={token}" for index, token in enumerate(left)]
    parts.extend(f"right{index + 1}={token}" for index, token in enumerate(right))
    if left:
        parts.append("left_phrase=" + "_".join(left))
    if right:
        parts.append("right_phrase=" + "_".join(right))
    if left and right:
        parts.append(f"bridge={left[-1]}___{right[0]}")
    return " | ".join(parts)


def _surface_frame_text(before: Sequence[str], after: Sequence[str], *, mask_token: str) -> str:
    left = list(before)[-2:]
    right = list(after)[:3]
    prev_token = left[-1] if left else "BOS"
    next_token = right[0] if right else "EOS"
    parts = [
        f"frame={prev_token}_{mask_token}_{next_token}",
        f"prev={prev_token}",
        f"next={next_token}",
    ]
    if next_token in _PREPOSITIONS:
        object_token = right[1] if len(right) > 1 else "EOS"
        parts.append(f"prep_frame={mask_token}_{next_token}_{object_token}")
    if prev_token in _DETERMINERS:
        parts.append(f"det_frame={prev_token}_{mask_token}_{next_token}")
    if left and right:
        parts.append("ordered_window=" + "_".join([*left, mask_token, *right]))
    return " | ".join(parts)


def _pos_frame_text(tokens: Sequence[str], *, mask_token: str) -> str:
    tags = [_coarse_token_class(token, mask_token=mask_token) for token in tokens if token]
    return " ".join(tags)


def _frame_only_text(tokens: Sequence[str], *, mask_token: str) -> str:
    return " ".join(_coarse_token_class(token, mask_token=mask_token) for token in tokens if token)


def _dependency_role_text(
    before: Sequence[str],
    after: Sequence[str],
    *,
    mask_token: str,
) -> str:
    left = list(before)[-4:]
    right = list(after)[:4]
    prev_token = left[-1] if left else "BOS"
    prev2_token = left[-2] if len(left) > 1 else "BOS"
    next_token = right[0] if right else "EOS"
    next2_token = right[1] if len(right) > 1 else "EOS"
    prev_class = _coarse_token_class(prev_token, mask_token=mask_token)
    next_class = _coarse_token_class(next_token, mask_token=mask_token)
    parts = [
        f"dep_frame={prev_class}_TRIGGER_{next_class}",
        f"dep_prev={prev_token}",
        f"dep_next={next_token}",
    ]
    if next_token in _PREPOSITIONS:
        parts.extend(
            (
                "role=head_with_prepositional_complement",
                f"dep_prep_after={next_token}",
                f"dep_prep_object={next2_token}",
            )
        )
        if next_token in _PARTICLES:
            parts.append(f"role=phrasal_verb_particle_{next_token}")
    if prev_token in _PREPOSITIONS:
        parts.extend(
            (
                "role=prepositional_object",
                f"dep_prep_before={prev_token}",
                f"dep_prep_governor={prev2_token}",
            )
        )
    if prev_token in _DETERMINERS or prev2_token in _DETERMINERS:
        parts.append("role=noun_phrase_head")
    if next_token in _BE_VERBS or next_token in _MODALS or _looks_like_verb(next_token):
        parts.append("role=subject_or_topic")
    if prev_token in _AUXILIARY_VERBS or prev_token in _MODALS or prev_token == "to":
        parts.append("role=verb_head_after_auxiliary")
    if (
        next_token in _DETERMINERS
        or next_token in _PRONOUNS
        or _coarse_token_class(next_token, mask_token=mask_token) == "WORD"
    ) and prev_token not in _DETERMINERS:
        parts.append("role=verb_or_predicate_with_object")
    if right:
        parts.append("right_dependency_chain=" + ">".join(right[:3]))
    if left:
        parts.append("left_dependency_chain=" + ">".join(left[-3:]))
    return " | ".join(dict.fromkeys(parts))


def _coarse_token_class(token: str, *, mask_token: str) -> str:
    normalized = str(token or "").casefold()
    if normalized == str(mask_token).casefold():
        return "TRIGGER"
    if normalized in _DETERMINERS:
        return "DET"
    if normalized in _PREPOSITIONS:
        return "PREP"
    if normalized in _MODALS:
        return "MODAL"
    if normalized in _NEGATIONS:
        return "NEG"
    if normalized.isdigit():
        return "NUM"
    if normalized.endswith("ing"):
        return "ING"
    if normalized.endswith("ed"):
        return "PAST"
    if normalized.endswith("ly"):
        return "ADV"
    return "WORD"


def _looks_like_verb(token: str) -> bool:
    normalized = str(token or "").casefold()
    return normalized in _AUXILIARY_VERBS or normalized.endswith(("ed", "ing", "s"))


def _negation_modal_text(tokens: Sequence[str]) -> str:
    materialized = [token for token in tokens if token]
    signals = [f"neg={token}" for token in materialized if token in _NEGATIONS] + [
        f"modal={token}" for token in materialized if token in _MODALS
    ]
    return " | ".join(signals) or "no_negation_or_modal"


def _deterministic_shuffle_text(tokens: Sequence[str], *, seed: str) -> str:
    return " ".join(
        sorted(
            [token for token in tokens if token],
            key=lambda token: _text_sha256(f"{seed}|{token}")[:12],
        )
    )


__all__ = [name for name in globals() if not name.startswith("__")]
