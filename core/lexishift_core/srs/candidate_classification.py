from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Mapping, Sequence

CANDIDATE_STATE_NORMAL_VOCAB = "normal_vocab"
CANDIDATE_STATE_DEPRIORITIZED_VOCAB = "deprioritized_vocab"
CANDIDATE_STATE_PATTERN_ITEM = "pattern_item"
CANDIDATE_STATE_GRAMMAR_ITEM = "grammar_item"
CANDIDATE_STATE_TOPIC_ONLY = "topic_only"
CANDIDATE_STATE_SUPPRESSED_DEFAULT = "suppressed_default"

PRESENTATION_MODE_VOCAB = "vocab"
PRESENTATION_MODE_PATTERN = "pattern"
PRESENTATION_MODE_GRAMMAR = "grammar"
PRESENTATION_MODE_TOPIC_SCOPED = "topic_scoped"
PRESENTATION_MODE_SUPPRESS = "suppress"

PROBLEM_CLASS_NORMAL_VOCAB = "normal_vocab"
PROBLEM_CLASS_NUMERAL_OR_COUNTER = "numeral_or_counter"
PROBLEM_CLASS_PARTICLE_OR_AUXILIARY = "particle_or_auxiliary"
PROBLEM_CLASS_PREFIX_OR_SUFFIX = "prefix_or_suffix"
PROBLEM_CLASS_PROPER_NOUN = "proper_noun"
PROBLEM_CLASS_SYMBOL_OR_PUNCTUATION = "symbol_or_punctuation"
PROBLEM_CLASS_ACRONYM_OR_CODE = "acronym_or_code"

CLASSIFICATION_CONFIDENCE_HIGH = "high"
CLASSIFICATION_CONFIDENCE_REVIEW = "review"

CANDIDATE_CLASSIFICATION_VERSION = "candidate_classification_v5"

_CANDIDATE_STATES = frozenset(
    {
        CANDIDATE_STATE_NORMAL_VOCAB,
        CANDIDATE_STATE_DEPRIORITIZED_VOCAB,
        CANDIDATE_STATE_PATTERN_ITEM,
        CANDIDATE_STATE_GRAMMAR_ITEM,
        CANDIDATE_STATE_TOPIC_ONLY,
        CANDIDATE_STATE_SUPPRESSED_DEFAULT,
    }
)

_NON_ACRONYM_OVERRIDE_STATES = frozenset(
    {
        CANDIDATE_STATE_PATTERN_ITEM,
        CANDIDATE_STATE_GRAMMAR_ITEM,
    }
)

_JA_NUMERAL_CHARS = frozenset("〇零一二三四五六七八九十百千万億兆壱弐参")
_ASCII_DIGITS = frozenset("0123456789")
_FULLWIDTH_DIGITS = frozenset("０１２３４５６７８９")
_SYMBOL_LIKE_POS_HEADS = frozenset({"補助記号", "記号", "空白"})
_JA_CORE_PROPER_NOUN_VOCAB = frozenset(
    {
        "日本",
        "中国",
        "アメリカ",
        "フランス",
        "ドイツ",
        "韓国",
        "イギリス",
        "米国",
    }
)
_JA_EXACT_FUNCTION_ITEMS = frozenset({"で", "が", "より", "そして", "及び"})
_DE_EXACT_GRAMMAR_ITEMS = frozenset(
    {
        "am",
        "ans",
        "aufs",
        "beim",
        "durchs",
        "fürs",
        "im",
        "ins",
        "ums",
        "unterm",
        "vom",
        "vors",
        "zum",
        "zur",
    }
)
_DE_BOUND_STANDALONE_FRAGMENTS = frozenset({"dar"})
_DE_ABBREVIATION_POS_HEADS = frozenset({"ABK", "ABBR", "ABBREV"})
_DE_GRAMMAR_POS_HEADS = frozenset(
    {
        "ART",
        "APPO",
        "APPR",
        "APPRART",
        "APZR",
        "KON",
        "KOKOM",
        "KOUI",
        "KOUS",
        "PTK",
        "PTKA",
        "PTKANT",
        "PTKNEG",
        "PTKVZ",
        "PTKZU",
        "PAV",
        "PDS",
        "PDAT",
        "PIAT",
        "PIDAT",
        "PIS",
        "PPER",
        "PPOSAT",
        "PPOSS",
        "PRELAT",
        "PRELS",
        "PRF",
        "PRO",
        "PWAT",
        "PWAV",
        "PWS",
    }
)


@dataclass(frozen=True)
class CandidateClassification:
    version: str = CANDIDATE_CLASSIFICATION_VERSION
    candidate_state: str = CANDIDATE_STATE_NORMAL_VOCAB
    presentation_mode: str = PRESENTATION_MODE_VOCAB
    problem_class: str = PROBLEM_CLASS_NORMAL_VOCAB
    confidence: str = CLASSIFICATION_CONFIDENCE_REVIEW
    reasons: Sequence[str] = field(default_factory=tuple)
    admission_suitability: float = 1.0

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_classification_version": self.version,
            "candidate_state": self.candidate_state,
            "presentation_mode": self.presentation_mode,
            "problem_class": self.problem_class,
            "classification_confidence": self.confidence,
            "classification_reasons": list(self.reasons),
            "admission_suitability": round(_clamp_01(self.admission_suitability), 6),
        }


def classify_srs_candidate(
    *,
    language_pair: str,
    lemma: object,
    raw_pos: object | None = None,
    learner_signals: object | None = None,
    apply_learner_signal_recommendations: bool = True,
) -> CandidateClassification:
    target_language = _target_language_from_pair(language_pair)
    if target_language == "de":
        return _classify_de_candidate(lemma=lemma, raw_pos=raw_pos)
    if target_language != "ja":
        return _normal_vocab("no_lp_specific_classifier")
    classification = _classify_ja_candidate(lemma=lemma, raw_pos=raw_pos)
    if not apply_learner_signal_recommendations:
        return classification
    return _apply_ja_learner_signal_recommendation(
        classification,
        learner_signals=learner_signals,
    )


def _classify_ja_candidate(
    *,
    lemma: object,
    raw_pos: object | None,
) -> CandidateClassification:
    text = str(lemma or "").strip()
    raw_pos_text = str(raw_pos or "").strip()
    pos_head = raw_pos_text.split("-", 1)[0].strip()

    if _is_symbol_like_lemma(text) or pos_head in _SYMBOL_LIKE_POS_HEADS:
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_SUPPRESSED_DEFAULT,
            presentation_mode=PRESENTATION_MODE_SUPPRESS,
            problem_class=PROBLEM_CLASS_SYMBOL_OR_PUNCTUATION,
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=("symbol_or_punctuation",),
            admission_suitability=0.0,
        )
    if text in _JA_EXACT_FUNCTION_ITEMS:
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_GRAMMAR_ITEM,
            presentation_mode=PRESENTATION_MODE_GRAMMAR,
            problem_class=PROBLEM_CLASS_PARTICLE_OR_AUXILIARY,
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=("ja_exact_function_item",),
            admission_suitability=0.02,
        )
    if _is_obvious_ja_number_expression(text):
        if not _is_simple_ja_number_expression(text):
            return CandidateClassification(
                candidate_state=CANDIDATE_STATE_SUPPRESSED_DEFAULT,
                presentation_mode=PRESENTATION_MODE_SUPPRESS,
                problem_class=PROBLEM_CLASS_NUMERAL_OR_COUNTER,
                confidence=CLASSIFICATION_CONFIDENCE_HIGH,
                reasons=("ja_compositional_number_expression",),
                admission_suitability=0.0,
            )
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_PATTERN_ITEM,
            presentation_mode=PRESENTATION_MODE_PATTERN,
            problem_class=PROBLEM_CLASS_NUMERAL_OR_COUNTER,
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=("ja_numeral_or_number_expression",),
            admission_suitability=0.02,
        )
    if "数詞" in raw_pos_text or "助数詞" in raw_pos_text:
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_PATTERN_ITEM,
            presentation_mode=PRESENTATION_MODE_PATTERN,
            problem_class=PROBLEM_CLASS_NUMERAL_OR_COUNTER,
            confidence=CLASSIFICATION_CONFIDENCE_REVIEW,
            reasons=("ja_pos_numeral_or_counter_possible",),
            admission_suitability=0.35,
        )
    if pos_head in {"助詞", "助動詞"}:
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_GRAMMAR_ITEM,
            presentation_mode=PRESENTATION_MODE_GRAMMAR,
            problem_class=PROBLEM_CLASS_PARTICLE_OR_AUXILIARY,
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=(f"ja_pos_head:{pos_head}",),
            admission_suitability=0.02,
        )
    if pos_head in {"接頭辞", "接尾辞"}:
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_GRAMMAR_ITEM,
            presentation_mode=PRESENTATION_MODE_GRAMMAR,
            problem_class=PROBLEM_CLASS_PREFIX_OR_SUFFIX,
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=(f"ja_pos_head:{pos_head}",),
            admission_suitability=0.02,
        )
    if "固有名詞" in raw_pos_text:
        if text in _JA_CORE_PROPER_NOUN_VOCAB:
            return CandidateClassification(
                candidate_state=CANDIDATE_STATE_NORMAL_VOCAB,
                presentation_mode=PRESENTATION_MODE_VOCAB,
                problem_class=PROBLEM_CLASS_PROPER_NOUN,
                confidence=CLASSIFICATION_CONFIDENCE_REVIEW,
                reasons=("ja_core_proper_noun_vocab",),
                admission_suitability=0.85,
            )
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_DEPRIORITIZED_VOCAB,
            presentation_mode=PRESENTATION_MODE_VOCAB,
            problem_class=PROBLEM_CLASS_PROPER_NOUN,
            confidence=CLASSIFICATION_CONFIDENCE_REVIEW,
            reasons=("ja_proper_noun_deprioritized",),
            admission_suitability=0.25,
        )
    return _normal_vocab("no_obvious_non_vocab_signal")


def _classify_de_candidate(
    *,
    lemma: object,
    raw_pos: object | None,
) -> CandidateClassification:
    text = str(lemma or "").strip()
    raw_pos_text = str(raw_pos or "").strip()
    analyses = _de_pos_analyses(raw_pos_text)
    pos_heads = {analysis[0] for analysis in analyses if analysis}

    if _is_symbol_like_lemma(text):
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_SUPPRESSED_DEFAULT,
            presentation_mode=PRESENTATION_MODE_SUPPRESS,
            problem_class=PROBLEM_CLASS_SYMBOL_OR_PUNCTUATION,
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=("symbol_or_punctuation",),
            admission_suitability=0.0,
        )
    if text.casefold() in _DE_EXACT_GRAMMAR_ITEMS:
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_GRAMMAR_ITEM,
            presentation_mode=PRESENTATION_MODE_GRAMMAR,
            problem_class=PROBLEM_CLASS_PARTICLE_OR_AUXILIARY,
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=("de_exact_grammar_item",),
            admission_suitability=0.08,
        )
    if text.casefold() in _DE_BOUND_STANDALONE_FRAGMENTS:
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_GRAMMAR_ITEM,
            presentation_mode=PRESENTATION_MODE_GRAMMAR,
            problem_class=PROBLEM_CLASS_PREFIX_OR_SUFFIX,
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=("de_bound_standalone_fragment",),
            admission_suitability=0.03,
        )
    if pos_heads & _DE_ABBREVIATION_POS_HEADS:
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_DEPRIORITIZED_VOCAB,
            presentation_mode=PRESENTATION_MODE_VOCAB,
            problem_class=PROBLEM_CLASS_ACRONYM_OR_CODE,
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=("de_pos_abbreviation_or_code",),
            admission_suitability=0.2,
        )
    if pos_heads and pos_heads <= _DE_GRAMMAR_POS_HEADS:
        return CandidateClassification(
            candidate_state=CANDIDATE_STATE_GRAMMAR_ITEM,
            presentation_mode=PRESENTATION_MODE_GRAMMAR,
            problem_class=PROBLEM_CLASS_PARTICLE_OR_AUXILIARY,
            confidence=CLASSIFICATION_CONFIDENCE_HIGH,
            reasons=("de_function_pos_only",),
            admission_suitability=0.08,
        )
    return _normal_vocab("no_obvious_non_vocab_signal")


def _normal_vocab(reason: str) -> CandidateClassification:
    return CandidateClassification(
        candidate_state=CANDIDATE_STATE_NORMAL_VOCAB,
        presentation_mode=PRESENTATION_MODE_VOCAB,
        problem_class=PROBLEM_CLASS_NORMAL_VOCAB,
        confidence=CLASSIFICATION_CONFIDENCE_REVIEW,
        reasons=(reason,),
        admission_suitability=1.0,
    )


def _apply_ja_learner_signal_recommendation(
    classification: CandidateClassification,
    *,
    learner_signals: object | None,
) -> CandidateClassification:
    if classification.candidate_state in _NON_ACRONYM_OVERRIDE_STATES:
        return classification
    if not isinstance(learner_signals, Mapping):
        return classification
    acronym = learner_signals.get("ja_acronym")
    if not isinstance(acronym, Mapping):
        return classification
    recommended_state = str(acronym.get("recommended_candidate_state") or "").strip()
    if recommended_state not in _CANDIDATE_STATES:
        return classification
    acronym_class = str(acronym.get("recommended_acronym_class") or "").strip()
    return CandidateClassification(
        candidate_state=recommended_state,
        presentation_mode=_presentation_mode_for_state(recommended_state),
        problem_class=_problem_class_for_acronym_recommendation(
            acronym_class=acronym_class,
            fallback=classification.problem_class,
        ),
        confidence=_confidence_for_acronym_recommendation(recommended_state),
        reasons=(
            *classification.reasons,
            f"ja_acronym:{acronym_class or 'unknown'}",
            f"ja_acronym_recommended_state:{recommended_state}",
        ),
        admission_suitability=_recommended_admission_suitability(
            acronym,
            fallback=classification.admission_suitability,
        ),
    )


def _presentation_mode_for_state(candidate_state: str) -> str:
    if candidate_state == CANDIDATE_STATE_SUPPRESSED_DEFAULT:
        return PRESENTATION_MODE_SUPPRESS
    if candidate_state == CANDIDATE_STATE_TOPIC_ONLY:
        return PRESENTATION_MODE_TOPIC_SCOPED
    if candidate_state == CANDIDATE_STATE_PATTERN_ITEM:
        return PRESENTATION_MODE_PATTERN
    if candidate_state == CANDIDATE_STATE_GRAMMAR_ITEM:
        return PRESENTATION_MODE_GRAMMAR
    return PRESENTATION_MODE_VOCAB


def _problem_class_for_acronym_recommendation(
    *,
    acronym_class: str,
    fallback: str,
) -> str:
    if acronym_class == "proper_name_acronym":
        return PROBLEM_CLASS_PROPER_NOUN
    if acronym_class and acronym_class != "not_acronym":
        return PROBLEM_CLASS_ACRONYM_OR_CODE
    return fallback


def _confidence_for_acronym_recommendation(candidate_state: str) -> str:
    if candidate_state == CANDIDATE_STATE_SUPPRESSED_DEFAULT:
        return CLASSIFICATION_CONFIDENCE_HIGH
    return CLASSIFICATION_CONFIDENCE_REVIEW


def _recommended_admission_suitability(
    acronym: Mapping[object, object],
    *,
    fallback: float,
) -> float:
    raw = acronym.get("recommended_admission_suitability")
    try:
        return _clamp_01(float(raw))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return _clamp_01(fallback)


def _is_obvious_ja_number_expression(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if text.startswith("第") and len(text) > 1:
        text = text[1:]
    allowed = _JA_NUMERAL_CHARS | _ASCII_DIGITS | _FULLWIDTH_DIGITS
    return all(char in allowed for char in text)


def _is_simple_ja_number_expression(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if text.startswith("第"):
        return False
    return len(text) == 1 and all(char in _JA_NUMERAL_CHARS for char in text)


def _is_symbol_like_lemma(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return True
    return all(not char.isalnum() for char in text)


def _de_pos_analyses(raw_pos: str) -> tuple[tuple[str, ...], ...]:
    analyses: list[tuple[str, ...]] = []
    for raw_analysis in str(raw_pos or "").split("|"):
        tokens = tuple(
            token for token in re.split(r"[:+_\-\s]+", raw_analysis.strip().upper()) if token
        )
        if tokens:
            analyses.append(tokens)
    return tuple(analyses)


def _target_language_from_pair(pair: str) -> str:
    normalized = str(pair or "").strip().lower()
    _source, separator, target = normalized.partition("-")
    if not separator:
        return ""
    return target.strip()


def _clamp_01(value: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 1.0
    if parsed != parsed:
        return 1.0
    return max(0.0, min(1.0, parsed))
