from __future__ import annotations

from typing import Mapping, Sequence


def eligible_rows(
    translations: Sequence[Mapping[str, object]],
    *,
    canonical_pos: str | None = None,
    require_wordnet_link: bool,
    require_translation_support: bool,
) -> list[Mapping[str, object]]:
    normalized_pos = str(canonical_pos or "").strip()
    rows = [
        row
        for row in translations
        if not normalized_pos or row.get("canonical_pos") == normalized_pos
    ]
    if require_wordnet_link:
        rows = [row for row in rows if bool(row.get("wordnet_linked"))]
    if require_translation_support:
        rows = [
            row
            for row in rows
            if bool(row.get("reverse_support")) or bool(row.get("freedict_support"))
        ]
    return rows


def selected_active_shadow_pair(
    translations: Sequence[Mapping[str, object]],
    *,
    family_pos_strategy: str,
    require_wordnet_link: bool,
    require_translation_support: bool,
) -> tuple[Mapping[str, object], Mapping[str, object]] | None:
    eligible = eligible_rows(
        translations,
        require_wordnet_link=require_wordnet_link,
        require_translation_support=require_translation_support,
    )
    pairs = [
        (active, shadow)
        for active in eligible
        for shadow in eligible
        if active is not shadow
        and normalized_translation(active) != normalized_translation(shadow)
        and str(active.get("canonical_pos") or "") != str(shadow.get("canonical_pos") or "")
    ]
    if str(family_pos_strategy or "").strip() == "noun_verb":
        pairs = [
            pair
            for pair in pairs
            if pair[0].get("canonical_pos") == "noun" and pair[1].get("canonical_pos") == "verb"
        ]
    if not pairs:
        return None
    return sorted(pairs, key=pos_pair_priority)[0]


def pos_pair_priority(
    pair: tuple[Mapping[str, object], Mapping[str, object]],
) -> tuple[int, tuple[int, int, int, int, int, str], tuple[int, int, int, int, int, str]]:
    active, shadow = pair
    pos_pair = (str(active.get("canonical_pos") or ""), str(shadow.get("canonical_pos") or ""))
    priority = {
        ("noun", "verb"): 0,
        ("adjective", "noun"): 1,
        ("noun", "adjective"): 2,
        ("adjective", "verb"): 3,
        ("verb", "noun"): 4,
        ("adverb", "adjective"): 5,
        ("adjective", "adverb"): 6,
    }.get(pos_pair, 20)
    return (priority, translation_sort_key(active), translation_sort_key(shadow))


def alternate_same_pos(
    active_row: Mapping[str, object], rows: Sequence[Mapping[str, object]]
) -> Mapping[str, object] | None:
    active_translation = normalized_translation(active_row)
    active_gloss = gloss_key(active_row)
    for row in rows[1:]:
        if normalized_translation(row) == active_translation:
            continue
        if gloss_key(row) == active_gloss:
            continue
        return row
    return None


def active_visible_target_aliases(
    active_row: Mapping[str, object], translations: Sequence[Mapping[str, object]]
) -> list[Mapping[str, object]]:
    active_translation = normalized_translation(active_row)
    active_pos = str(active_row.get("canonical_pos") or "").strip()
    active_gloss = gloss_key(active_row)
    aliases = []
    for row in translations:
        if row is active_row:
            continue
        if normalized_translation(row) != active_translation:
            continue
        if (
            str(row.get("canonical_pos") or "").strip() == active_pos
            and gloss_key(row) == active_gloss
        ):
            continue
        aliases.append(row)
    return aliases


def reason_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        reason = str(row.get("reason") or "").strip()
        if reason:
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def missing_shape_reason(
    translations: Sequence[Mapping[str, object]],
    *,
    require_wordnet_link: bool,
    require_translation_support: bool,
    family_pos_strategy: str,
) -> str:
    if str(family_pos_strategy or "").strip() == "noun_verb":
        has_noun = any(row.get("canonical_pos") == "noun" for row in translations)
        has_verb = any(row.get("canonical_pos") == "verb" for row in translations)
        if not has_noun or not has_verb:
            return "missing_noun_or_verb_translation"
    elif len({str(row.get("canonical_pos") or "") for row in translations}) < 2:
        return "missing_cross_pos_translation"
    if (
        selected_active_shadow_pair(
            translations,
            family_pos_strategy=family_pos_strategy,
            require_wordnet_link=False,
            require_translation_support=False,
        )
        is None
    ):
        return (
            "missing_distinct_noun_or_verb_translation"
            if str(family_pos_strategy or "").strip() == "noun_verb"
            else "missing_distinct_cross_pos_translation"
        )
    if require_wordnet_link:
        eligible_wordnet = selected_active_shadow_pair(
            translations,
            family_pos_strategy=family_pos_strategy,
            require_wordnet_link=True,
            require_translation_support=False,
        )
        if eligible_wordnet is None:
            return (
                "missing_wordnet_linked_noun_or_verb_translation"
                if str(family_pos_strategy or "").strip() == "noun_verb"
                else "missing_wordnet_linked_cross_pos_translation"
            )
    if require_translation_support:
        eligible_supported = selected_active_shadow_pair(
            translations,
            family_pos_strategy=family_pos_strategy,
            require_wordnet_link=require_wordnet_link,
            require_translation_support=True,
        )
        if eligible_supported is None:
            return (
                "missing_reverse_or_freedict_supported_noun_or_verb_translation"
                if str(family_pos_strategy or "").strip() == "noun_verb"
                else "missing_reverse_or_freedict_supported_cross_pos_translation"
            )
    return "translation_family_selection_failed"


def translation_sort_key(row: Mapping[str, object]) -> tuple[int, int, int, int, int, str]:
    return (
        0 if row.get("wordnet_linked") else 1,
        0 if row.get("reverse_support") else 1,
        0 if row.get("freedict_support") else 1,
        int(row.get("rank") or 9999),
        -int(round(float(row.get("best_wordnet_link_score") or 0.0) * 10000)),
        str(row.get("translation") or ""),
    )


def normalized_translation(row: Mapping[str, object]) -> str:
    return str(row.get("translation") or "").strip().lower()


def gloss_key(row: Mapping[str, object]) -> str:
    text = str(row.get("sense_text") or "").strip().lower()
    if text:
        return text
    return " | ".join(str(item).lower() for item in row.get("raw_glosses") or ())


def evidence_views(
    *,
    trigger: str,
    target: str,
    row: Mapping[str, object],
    visible_alias_rows: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    pos = str(row.get("canonical_pos") or "").strip()
    sense_text = str(row.get("sense_text") or "").strip()
    raw_glosses = [str(item) for item in row.get("raw_glosses") or () if str(item or "").strip()]
    gloss_text = sense_text or " | ".join(raw_glosses)
    label = f"{trigger} {pos} sense"
    if gloss_text:
        label = f"{trigger} {pos} sense: {gloss_text}"
    alias_glosses = [
        _visible_alias_evidence_text(trigger=trigger, row=alias)
        for alias in visible_alias_rows
        if _visible_alias_evidence_text(trigger=trigger, row=alias)
    ]
    return {
        "sense_label": label,
        "gloss_text": gloss_text,
        "sense_gloss_bundle": f"{label} | {gloss_text}".strip(" |"),
        "all_evidence_text": " | ".join(
            item for item in (target, label, gloss_text, *raw_glosses[:2], *alias_glosses) if item
        ),
    }


def temporary_sense_for_link(row: Mapping[str, object], *, trigger: str) -> dict[str, object]:
    return {
        "target_lemma": str(row.get("translation") or "").strip(),
        "canonical_pos": str(row.get("canonical_pos") or "").strip(),
        "evidence_views": evidence_views(
            trigger=trigger,
            target=str(row.get("translation") or "").strip(),
            row=row,
        ),
    }


def source_summary(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "translation": str(row.get("translation") or "").strip(),
        "canonical_pos": str(row.get("canonical_pos") or "").strip(),
        "rank": int(row.get("rank") or 0),
        "sense_text": str(row.get("sense_text") or "").strip(),
        "support_sources": list(row.get("support_sources") or ()),
        "wordnet_linked": bool(row.get("wordnet_linked")),
        "best_wordnet_link_score": float(row.get("best_wordnet_link_score") or 0.0),
        "best_wordnet_overlap": list(row.get("best_wordnet_overlap") or ()),
    }


def _visible_alias_evidence_text(*, trigger: str, row: Mapping[str, object]) -> str:
    pos = str(row.get("canonical_pos") or "").strip()
    sense_text = str(row.get("sense_text") or "").strip()
    raw_glosses = [str(item) for item in row.get("raw_glosses") or () if str(item or "").strip()]
    gloss_text = sense_text or " | ".join(raw_glosses)
    if not gloss_text:
        return ""
    return f"{trigger} {pos} same-visible-target sense: {gloss_text}"
