from __future__ import annotations

from collections import defaultdict
import re
from typing import Mapping, Sequence

from semantic_veto_evidence_gap_generation_score_contribution_core import (
    _as_mapping,
    _mapping_rows,
)


HIGH_EVAL_OVERLAP_THRESHOLD = 0.45
MEDIUM_EVAL_OVERLAP_THRESHOLD = 0.30
HIGH_SHADOW_CONFUSABILITY_THRESHOLD = 0.25
MEDIUM_SHADOW_CONFUSABILITY_THRESHOLD = 0.15
LOW_DIVERSITY_THRESHOLD = 0.60
POS_ANCHORED_THRESHOLD = 0.65

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "because",
        "before",
        "by",
        "can",
        "could",
        "for",
        "from",
        "had",
        "has",
        "have",
        "he",
        "her",
        "his",
        "in",
        "into",
        "is",
        "it",
        "its",
        "my",
        "of",
        "on",
        "or",
        "our",
        "she",
        "that",
        "the",
        "their",
        "they",
        "this",
        "to",
        "was",
        "we",
        "were",
        "will",
        "with",
        "you",
        "your",
    }
)
DETERMINERS = frozenset(
    {
        "a",
        "an",
        "the",
        "this",
        "that",
        "these",
        "those",
        "my",
        "your",
        "his",
        "her",
        "its",
        "our",
        "their",
        "each",
        "every",
        "no",
        "one",
    }
)
MODALS = frozenset({"can", "could", "will", "would", "should", "may", "might", "must", "shall"})
BE_VERBS = frozenset({"am", "are", "be", "been", "being", "is", "was", "were"})
PREPOSITIONS = frozenset(
    {
        "about",
        "above",
        "across",
        "after",
        "among",
        "around",
        "at",
        "before",
        "behind",
        "below",
        "between",
        "by",
        "for",
        "from",
        "in",
        "inside",
        "into",
        "near",
        "of",
        "on",
        "over",
        "through",
        "to",
        "under",
        "with",
    }
)
FINITE_VERB_HINTS = frozenset(
    {
        "approved",
        "appeared",
        "began",
        "changed",
        "continued",
        "eroded",
        "grew",
        "helped",
        "looked",
        "made",
        "remained",
        "returned",
        "said",
        "was",
        "were",
    }
)
MONTHS = frozenset(
    {
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    }
)


def audit_generated_active_items(
    *,
    admitted_items: Sequence[Mapping[str, object]],
    families: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    audits = []
    for index, item in enumerate(admitted_items, start=1):
        family = _as_mapping(families.get(str(item.get("family_id") or "")))
        active = _as_mapping(family.get("active"))
        expected_pos = str(active.get("canonical_pos") or "").lower()
        source_phrase = str(item.get("source_phrase") or family.get("trigger") or "")
        target_lemma = str(item.get("target_lemma") or active.get("target_lemma") or "")
        sentence = str(item.get("sentence") or "")
        note = str(item.get("evidence_note") or "")
        observed = _infer_source_syntax(
            sentence=sentence,
            source_phrase=source_phrase,
            expected_pos=expected_pos,
        )
        pos_strength = _pos_anchor_strength(expected_pos=expected_pos, observed_syntax=observed)
        eval_overlap = _max_eval_overlap(sentence=sentence, family=family)
        shadow_confusability = _max_shadow_confusability(sentence=sentence, family=family)
        flags = _mechanical_flags(
            sentence=sentence,
            note=note,
            source_phrase=source_phrase,
            target_lemma=target_lemma,
            expected_pos=expected_pos,
            observed_syntax=observed,
            pos_strength=pos_strength,
            eval_overlap=eval_overlap,
            shadow_confusability=shadow_confusability,
        )
        audits.append(
            {
                "audit_id": f"generated_active_item:{index:03d}",
                "item_id": str(item.get("item_id") or ""),
                "family_id": str(item.get("family_id") or ""),
                "source_phrase": source_phrase,
                "target_lemma": target_lemma,
                "expected_pos": expected_pos,
                "model_source_pos_frame": str(item.get("source_pos_frame") or ""),
                "model_topic_frame": str(item.get("topic_frame") or ""),
                "model_diversity_note": str(item.get("diversity_note") or ""),
                "observed_source_syntax": observed,
                "pos_anchor_strength": pos_strength,
                "sentence": sentence,
                "evidence_note": note,
                "definition_like_sentence": _is_definition_like_sentence(sentence, source_phrase),
                "target_lemma_in_evidence_note": _contains_phrase(note, target_lemma),
                "eval_overlap": eval_overlap,
                "shadow_confusability": shadow_confusability,
                "peer_similarity_max": 0.0,
                "flags": flags,
                "quality_score": 0.0,
            }
        )
    _annotate_peer_similarity(audits)
    for audit in audits:
        flags = list(audit["flags"])
        if float(audit["peer_similarity_max"]) >= LOW_DIVERSITY_THRESHOLD:
            flags.append("low_family_diversity")
        audit["flags"] = sorted(set(flags))
        audit["quality_score"] = _quality_score(audit)
    return audits


def has_critical_flag(audit: Mapping[str, object]) -> bool:
    return any(str(flag).startswith("critical_") for flag in audit.get("flags", ()))


def scrub_evidence_note(note: str, *, source_phrase: str, target_lemma: str) -> str:
    scrubbed = note
    for value in (target_lemma, "active sense", "matching", "shows", "uses"):
        if value:
            scrubbed = re.sub(re.escape(value), "", scrubbed, flags=re.IGNORECASE)
    scrubbed = re.sub(r"\s+", " ", scrubbed)
    scrubbed = scrubbed.replace(" ,", ",").replace(" .", ".")
    return scrubbed.strip(" ;,.")


def _mechanical_flags(
    *,
    sentence: str,
    note: str,
    source_phrase: str,
    target_lemma: str,
    expected_pos: str,
    observed_syntax: str,
    pos_strength: float,
    eval_overlap: Mapping[str, object],
    shadow_confusability: Mapping[str, object],
) -> list[str]:
    flags = []
    if not _contains_runtime_trigger(sentence, source_phrase):
        flags.append("critical_source_phrase_missing_or_not_standalone")
    if _contains_phrase(sentence, target_lemma):
        flags.append("critical_target_lemma_in_sentence")
    if _contains_phrase(note, target_lemma):
        flags.append("target_lemma_in_evidence_note")
    if _has_label_leakage(sentence):
        flags.append("critical_label_leakage_in_sentence")
    if _is_definition_like_sentence(sentence, source_phrase):
        flags.append("definition_like_sentence")
    if expected_pos and observed_syntax == "unknown":
        flags.append("pos_unknown")
    if pos_strength < POS_ANCHORED_THRESHOLD:
        flags.append("pos_weak")
    if eval_overlap.get("risk") == "high":
        flags.append("high_eval_overlap")
    elif eval_overlap.get("risk") == "medium":
        flags.append("medium_eval_overlap")
    if shadow_confusability.get("risk") == "high":
        flags.append("high_shadow_confusability")
    elif shadow_confusability.get("risk") == "medium":
        flags.append("medium_shadow_confusability")
    return sorted(set(flags))


def _quality_score(audit: Mapping[str, object]) -> float:
    score = 1.0
    flags = set(str(flag) for flag in audit.get("flags", ()))
    if any(flag.startswith("critical_") for flag in flags):
        score -= 1.0
    if "high_eval_overlap" in flags:
        score -= 0.25
    elif "medium_eval_overlap" in flags:
        score -= 0.10
    if "pos_weak" in flags:
        score -= 0.20
    elif "pos_unknown" in flags:
        score -= 0.10
    if "definition_like_sentence" in flags:
        score -= 0.15
    if "target_lemma_in_evidence_note" in flags:
        score -= 0.10
    if "high_shadow_confusability" in flags:
        score -= 0.25
    elif "medium_shadow_confusability" in flags:
        score -= 0.10
    if "low_family_diversity" in flags:
        score -= 0.10
    return round(max(0.0, min(1.0, score)), 4)


def _infer_source_syntax(*, sentence: str, source_phrase: str, expected_pos: str = "") -> str:
    source_tokens = _word_tokens(source_phrase)
    if len(source_tokens) != 1:
        return "phrase"
    source = source_tokens[0]
    tokens = _word_tokens(sentence)
    try:
        index = tokens.index(source)
    except ValueError:
        return "missing"
    prev_token = tokens[index - 1] if index > 0 else ""
    prev_prev = tokens[index - 2] if index > 1 else ""
    next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
    if source in MONTHS:
        return "month_name"
    if expected_pos == "preposition" and source in PREPOSITIONS:
        return "preposition"
    if source.endswith("ly"):
        return "adverb"
    if prev_token == "to":
        return "verb_infinitive"
    if prev_token in MODALS:
        return "verb_after_modal"
    if prev_token == "not" and prev_prev in MODALS:
        return "verb_after_modal"
    if prev_prev in {"try", "tries", "tried", "trying"} and prev_token == "to":
        return "verb_infinitive"
    if expected_pos == "verb" and next_token == "to":
        return "verb_before_infinitive"
    if expected_pos == "adjective":
        if prev_token in BE_VERBS:
            return "predicative"
        if next_token and not _looks_finite_verb(next_token):
            return "adjective_attributive"
    if prev_token in BE_VERBS:
        return "predicative"
    if prev_token in DETERMINERS:
        return "noun_determined"
    if next_token and _looks_finite_verb(next_token):
        return "noun_subject"
    if next_token and next_token not in BE_VERBS and next_token not in MODALS:
        if next_token in {"citizen", "art", "history", "passport", "language", "building", "lot"}:
            return "adjective_attributive"
    if expected_pos == "noun" and observed_noun_context(
        prev_token=prev_token, next_token=next_token
    ):
        return "noun_context"
    return "unknown"


def _pos_anchor_strength(*, expected_pos: str, observed_syntax: str) -> float:
    if not expected_pos:
        return 0.5
    expected = expected_pos.lower()
    if observed_syntax in {"missing", "phrase"}:
        return 0.0 if observed_syntax == "missing" else 0.5
    if expected == "verb":
        return 0.95 if observed_syntax.startswith("verb") else 0.25
    if expected == "noun":
        if observed_syntax in {"noun_context", "noun_determined", "noun_subject", "month_name"}:
            return 0.95
        if observed_syntax in {"unknown", "predicative"}:
            return 0.55
        return 0.25
    if expected == "adjective":
        if observed_syntax in {"adjective_attributive", "predicative"}:
            return 0.90
        if observed_syntax == "unknown":
            return 0.55
        return 0.35
    if expected == "adverb":
        if observed_syntax == "adverb":
            return 0.95
        if observed_syntax in {"unknown", "predicative"}:
            return 0.55
        return 0.30
    if expected == "preposition":
        return 0.95 if observed_syntax == "preposition" else 0.35
    return 0.5


def observed_noun_context(*, prev_token: str, next_token: str) -> bool:
    return bool(
        prev_token
        and prev_token not in MODALS
        and next_token
        and (next_token in PREPOSITIONS or _looks_finite_verb(next_token))
    )


def _looks_finite_verb(token: str) -> bool:
    return token in FINITE_VERB_HINTS or token.endswith("ed")


def _max_eval_overlap(*, sentence: str, family: Mapping[str, object]) -> dict[str, object]:
    best_score = 0.0
    best_case_id = ""
    best_sentence = ""
    best_gold = ""
    sentence_tokens = _content_tokens(sentence)
    for case in _mapping_rows(family.get("cases")):
        case_sentence = str(case.get("sentence") or "")
        score = _jaccard(sentence_tokens, _content_tokens(case_sentence))
        if score > best_score:
            best_score = score
            best_case_id = str(case.get("case_id") or "")
            best_sentence = case_sentence
            best_gold = str(case.get("gold_decision") or "")
    return {
        "max_jaccard": round(best_score, 4),
        "risk": _overlap_risk(best_score),
        "case_id": best_case_id,
        "gold_decision": best_gold,
        "sentence": best_sentence,
    }


def _max_shadow_confusability(*, sentence: str, family: Mapping[str, object]) -> dict[str, object]:
    best_score = 0.0
    best_shadow_id = ""
    sentence_tokens = _content_tokens(sentence)
    for shadow in _mapping_rows(family.get("shadows")):
        evidence = _all_evidence_text(shadow)
        score = _jaccard(sentence_tokens, _content_tokens(evidence))
        if score > best_score:
            best_score = score
            best_shadow_id = str(shadow.get("sense_id") or shadow.get("target_lemma") or "")
    return {
        "max_jaccard": round(best_score, 4),
        "risk": _shadow_confusability_risk(best_score),
        "shadow_id": best_shadow_id,
    }


def _annotate_peer_similarity(audits: list[dict[str, object]]) -> None:
    by_family: dict[str, list[dict[str, object]]] = defaultdict(list)
    for audit in audits:
        by_family[str(audit.get("family_id") or "")].append(audit)
    for family_audits in by_family.values():
        for audit in family_audits:
            tokens = _content_tokens(str(audit.get("sentence") or ""))
            best = 0.0
            for peer in family_audits:
                if peer is audit:
                    continue
                best = max(best, _jaccard(tokens, _content_tokens(str(peer.get("sentence") or ""))))
            audit["peer_similarity_max"] = round(best, 4)


def _is_definition_like_sentence(sentence: str, source_phrase: str) -> bool:
    lower = sentence.lower()
    source = source_phrase.lower()
    if any(marker in lower for marker in (" means ", " refers to ", " is defined as ")):
        return True
    if f"{source} is a " in lower or f"{source} is an " in lower:
        return True
    if "twelfth month" in lower or "calendar month" in lower:
        return True
    return False


def _contains_runtime_trigger(sentence: str, source_phrase: str) -> bool:
    if not source_phrase:
        return False
    pattern = rf"(?<![A-Za-z0-9_]){re.escape(source_phrase)}(?![A-Za-z0-9_])"
    return bool(re.search(pattern, sentence, flags=re.IGNORECASE))


def _contains_phrase(text: str, phrase: str) -> bool:
    if not text or not phrase:
        return False
    return bool(re.search(rf"(?<![A-Za-z0-9_]){re.escape(phrase)}(?![A-Za-z0-9_])", text, re.I))


def _has_label_leakage(sentence: str) -> bool:
    return bool(re.search(r"\b(active|shadow|abstain|replace|no-winner)\b", sentence, re.I))


def _overlap_risk(score: float) -> str:
    if score >= HIGH_EVAL_OVERLAP_THRESHOLD:
        return "high"
    if score >= MEDIUM_EVAL_OVERLAP_THRESHOLD:
        return "medium"
    return "low"


def _shadow_confusability_risk(score: float) -> str:
    if score >= HIGH_SHADOW_CONFUSABILITY_THRESHOLD:
        return "high"
    if score >= MEDIUM_SHADOW_CONFUSABILITY_THRESHOLD:
        return "medium"
    return "low"


def _all_evidence_text(sense: Mapping[str, object]) -> str:
    evidence_views = _as_mapping(sense.get("evidence_views"))
    return " | ".join(str(value) for value in evidence_views.values() if str(value).strip())


def _word_tokens(value: str) -> list[str]:
    return re.findall(r"[a-z]+", value.lower())


def _content_tokens(value: str) -> set[str]:
    return {token for token in _word_tokens(value) if token not in STOPWORDS}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
