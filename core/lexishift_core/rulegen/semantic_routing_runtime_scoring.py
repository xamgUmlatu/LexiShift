from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping, Sequence

import numpy as np

from lexishift_core.rulegen.semantic_shadow_embedding_bridge import (
    DEFAULT_EMBEDDING_BRIDGE_MODEL,
)

DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS = 4
DEFAULT_SENTENCE_VETO_MASK_TOKEN = "___"
DEFAULT_SENTENCE_VETO_CONTEXT_VIEW = "raw_sentence"
DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW = "all_evidence_text"
DEFAULT_SENTENCE_VETO_MIN_ACTIVE_SCORE = 0.35
DEFAULT_SENTENCE_VETO_MIN_MARGIN = 0.05
DEFAULT_SENTENCE_VETO_PHRASE_CONTROL_MODE = "off"

SENTENCE_VETO_CONTEXT_VIEWS = (
    "raw_sentence",
    "masked_sentence",
    "raw_window",
    "masked_window",
)
SENTENCE_VETO_EVIDENCE_VIEWS = (
    "sense_label",
    "gloss_text",
    "sense_gloss_bundle",
    "qualifier_text",
    "all_evidence_text",
)
SENTENCE_VETO_SCORERS = (
    "token_jaccard",
    "tfidf_cosine",
    "sentence_transformer_cosine",
)
SENTENCE_VETO_PHRASE_CONTROL_MODES = (
    "off",
    "noun_family_frame_guard",
)

_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ']+")
_NOUN_LIKE_POS_TAGS = frozenset({"noun", "proper_noun"})
_PHRASE_CONTROL_MODAL_TOKENS = frozenset(
    {
        "can",
        "cannot",
        "can't",
        "could",
        "may",
        "might",
        "must",
        "shall",
        "should",
        "will",
        "would",
    }
)
_PHRASE_CONTROL_DETERMINER_TOKENS = frozenset(
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
_PHRASE_CONTROL_PARTICLE_TOKENS = frozenset(
    {
        "away",
        "back",
        "down",
        "in",
        "into",
        "off",
        "on",
        "out",
        "over",
        "past",
        "through",
        "up",
    }
)
_PHRASE_CONTROL_PREPOSITION_TOKENS = _PHRASE_CONTROL_PARTICLE_TOKENS | frozenset(
    {
        "at",
        "before",
        "beside",
        "by",
        "during",
        "for",
        "from",
        "near",
        "through",
        "to",
        "toward",
        "with",
        "within",
        "without",
    }
)
_PHRASE_CONTROL_SUBJECT_TRIGGER_PARTICLE_TOKENS = frozenset(
    {
        "away",
        "back",
        "down",
        "off",
        "out",
        "over",
        "past",
        "through",
        "up",
    }
)
_PHRASE_CONTROL_PROGRESSIVE_OBJECT_VERBS = frozenset(
    {"get", "gets", "got", "keep", "keeps", "kept", "set", "sets", "start", "starts", "started"}
)
_PHRASE_CONTROL_PROGRESSIVE_OBJECT_TRIGGERS = {
    "ball": frozenset({"rolling"}),
}
_PHRASE_CONTROL_NOUN_OF_PHRASE_TRIGGERS = {
    "rest": "alternate_noun_of_phrase_frame",
}


@dataclass(frozen=True)
class RuntimeVetoCaseScore:
    case_id: str
    family_id: str
    gold_decision: str
    gold_winner: str
    gold_winner_type: str
    predicted_decision: str
    predicted_winner: str
    predicted_winner_type: str
    active_score: float
    strongest_shadow_score: float
    margin: float
    strongest_shadow_id: str
    context_text: str
    active_evidence_text: str
    strongest_shadow_evidence_text: str
    phrase_preemption_hit: bool
    matched_phrase_pattern: str
    phrase_reason_code: str


@dataclass(frozen=True)
class RuntimePhraseControlSignals:
    phrase_preemption_hit: bool
    matched_phrase_pattern: str
    phrase_reason_code: str
    signal_codes: tuple[str, ...]
    preceding_token: str
    following_token: str
    family_pos_tags: tuple[str, ...]


def build_runtime_context_views(
    sentence: str,
    *,
    source_phrase: str,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
) -> dict[str, str]:
    normalized_sentence = str(sentence or "").strip()
    normalized_source_phrase = str(source_phrase or "").strip()
    if not normalized_sentence:
        return {
            "raw_sentence": "",
            "masked_sentence": "",
            "raw_window": "",
            "masked_window": "",
        }
    if not normalized_source_phrase:
        return {
            "raw_sentence": normalized_sentence,
            "masked_sentence": normalized_sentence,
            "raw_window": normalized_sentence,
            "masked_window": normalized_sentence,
        }

    tokens = normalized_sentence.split()
    phrase_tokens = normalized_source_phrase.split()
    match = _find_phrase_token_span(tokens, phrase_tokens)
    if match is None:
        return {
            "raw_sentence": normalized_sentence,
            "masked_sentence": normalized_sentence,
            "raw_window": normalized_sentence,
            "masked_window": normalized_sentence,
        }
    start_index, end_index = match
    masked_tokens = list(tokens[:start_index]) + [mask_token] + list(tokens[end_index:])
    raw_window_start = max(0, start_index - max(0, int(window_tokens)))
    raw_window_end = min(len(tokens), end_index + max(0, int(window_tokens)))
    raw_window_tokens = tokens[raw_window_start:raw_window_end]
    masked_window_tokens = (
        raw_window_tokens[: start_index - raw_window_start]
        + [mask_token]
        + raw_window_tokens[end_index - raw_window_start :]
    )
    return {
        "raw_sentence": normalized_sentence,
        "masked_sentence": " ".join(masked_tokens),
        "raw_window": " ".join(raw_window_tokens),
        "masked_window": " ".join(masked_window_tokens),
    }


def resolve_runtime_evidence_text(
    sense_record: Mapping[str, object],
    *,
    evidence_view: str = DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW,
) -> str:
    evidence_views = sense_record.get("evidence_views")
    if not isinstance(evidence_views, Mapping):
        evidence_views = {}
    requested = str(evidence_view or "").strip() or DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW
    text = str(evidence_views.get(requested) or "").strip()
    if text:
        return text
    for fallback_view in (
        "all_evidence_text",
        "sense_gloss_bundle",
        "gloss_text",
        "sense_label",
        "qualifier_text",
    ):
        fallback_text = str(evidence_views.get(fallback_view) or "").strip()
        if fallback_text:
            return fallback_text
    return str(sense_record.get("sense_label") or sense_record.get("target_lemma") or "").strip()


def decide_runtime_veto_outcome(
    *,
    active_score: float,
    strongest_shadow_score: float,
    min_active_score: float = DEFAULT_SENTENCE_VETO_MIN_ACTIVE_SCORE,
    min_margin: float = DEFAULT_SENTENCE_VETO_MIN_MARGIN,
) -> str:
    if float(active_score) < float(min_active_score):
        return "abstain"
    if float(active_score) - float(strongest_shadow_score) < float(min_margin):
        return "abstain"
    return "replace"


def extract_runtime_phrase_control_signals(
    sentence: str,
    *,
    source_phrase: str,
    family_pos_tags: Sequence[str] = (),
) -> RuntimePhraseControlSignals:
    normalized_sentence = str(sentence or "").strip()
    normalized_source_phrase = str(source_phrase or "").strip()
    normalized_family_pos_tags = tuple(
        sorted(
            {
                str(value or "").strip().lower()
                for value in family_pos_tags
                if str(value or "").strip()
            }
        )
    )
    if not normalized_sentence or not normalized_source_phrase:
        return RuntimePhraseControlSignals(
            phrase_preemption_hit=False,
            matched_phrase_pattern="",
            phrase_reason_code="",
            signal_codes=(),
            preceding_token="",
            following_token="",
            family_pos_tags=normalized_family_pos_tags,
        )
    tokens = normalized_sentence.split()
    phrase_tokens = normalized_source_phrase.split()
    match = _find_phrase_token_span(tokens, phrase_tokens)
    if match is None:
        return RuntimePhraseControlSignals(
            phrase_preemption_hit=False,
            matched_phrase_pattern="",
            phrase_reason_code="",
            signal_codes=(),
            preceding_token="",
            following_token="",
            family_pos_tags=normalized_family_pos_tags,
        )

    start_index, end_index = match
    preceding_token = _normalize_surface_token(tokens[start_index - 1]) if start_index > 0 else ""
    pre_preceding_token = (
        _normalize_surface_token(tokens[start_index - 2]) if start_index > 1 else ""
    )
    following_token = _normalize_surface_token(tokens[end_index]) if end_index < len(tokens) else ""

    if not normalized_family_pos_tags or any(
        tag not in _NOUN_LIKE_POS_TAGS for tag in normalized_family_pos_tags
    ):
        return RuntimePhraseControlSignals(
            phrase_preemption_hit=False,
            matched_phrase_pattern="",
            phrase_reason_code="",
            signal_codes=(),
            preceding_token=preceding_token,
            following_token=following_token,
            family_pos_tags=normalized_family_pos_tags,
        )

    signal_codes: list[str] = []
    matched_phrase_pattern = ""
    phrase_reason_code = ""

    def register_signal(*, reason_code: str, pattern: str) -> None:
        nonlocal matched_phrase_pattern, phrase_reason_code
        if reason_code not in signal_codes:
            signal_codes.append(reason_code)
        if not phrase_reason_code:
            phrase_reason_code = reason_code
        if not matched_phrase_pattern:
            matched_phrase_pattern = pattern

    strong_signal_rows: list[tuple[str, str]] = []
    if preceding_token in _PHRASE_CONTROL_MODAL_TOKENS:
        strong_signal_rows.append(
            ("modal_trigger_frame", f"{preceding_token} {normalized_source_phrase}")
        )
    if preceding_token == "to":
        strong_signal_rows.append(("infinitive_trigger_frame", f"to {normalized_source_phrase}"))
    if preceding_token == "please":
        strong_signal_rows.append(
            ("polite_imperative_trigger_frame", f"please {normalized_source_phrase}")
        )
    if start_index == 0 and following_token in _PHRASE_CONTROL_DETERMINER_TOKENS:
        strong_signal_rows.append(
            ("sentence_initial_object_frame", f"{normalized_source_phrase} {following_token}")
        )
    if (
        start_index > 0
        and preceding_token
        and preceding_token not in _PHRASE_CONTROL_DETERMINER_TOKENS
        and following_token in _PHRASE_CONTROL_DETERMINER_TOKENS
    ):
        strong_signal_rows.append(
            (
                "subject_trigger_object_frame",
                f"{preceding_token} {normalized_source_phrase} {following_token}",
            )
        )
    if (
        start_index > 0
        and preceding_token
        and preceding_token not in _PHRASE_CONTROL_DETERMINER_TOKENS
        and preceding_token not in _PHRASE_CONTROL_PREPOSITION_TOKENS
        and following_token in _PHRASE_CONTROL_SUBJECT_TRIGGER_PARTICLE_TOKENS
    ):
        strong_signal_rows.append(
            (
                "subject_trigger_particle_frame",
                f"{preceding_token} {normalized_source_phrase} {following_token}",
            )
        )
    progressive_followers = _PHRASE_CONTROL_PROGRESSIVE_OBJECT_TRIGGERS.get(
        normalized_source_phrase
    )
    if (
        progressive_followers
        and preceding_token in _PHRASE_CONTROL_DETERMINER_TOKENS
        and pre_preceding_token in _PHRASE_CONTROL_PROGRESSIVE_OBJECT_VERBS
        and following_token in progressive_followers
    ):
        strong_signal_rows.append(
            (
                "idiom_progressive_object_frame",
                (
                    f"{pre_preceding_token} {preceding_token} "
                    f"{normalized_source_phrase} {following_token}"
                ),
            )
        )
    noun_of_phrase_reason = _PHRASE_CONTROL_NOUN_OF_PHRASE_TRIGGERS.get(normalized_source_phrase)
    if (
        noun_of_phrase_reason
        and preceding_token in _PHRASE_CONTROL_DETERMINER_TOKENS
        and following_token == "of"
    ):
        strong_signal_rows.append(
            (
                noun_of_phrase_reason,
                f"{preceding_token} {normalized_source_phrase} {following_token}",
            )
        )
    if following_token in _PHRASE_CONTROL_PARTICLE_TOKENS and strong_signal_rows:
        register_signal(
            reason_code="trigger_particle_frame",
            pattern=f"{normalized_source_phrase} {following_token}",
        )
    for reason_code, pattern in strong_signal_rows:
        register_signal(reason_code=reason_code, pattern=pattern)

    return RuntimePhraseControlSignals(
        phrase_preemption_hit=bool(signal_codes),
        matched_phrase_pattern=matched_phrase_pattern,
        phrase_reason_code=phrase_reason_code,
        signal_codes=tuple(signal_codes),
        preceding_token=preceding_token,
        following_token=following_token,
        family_pos_tags=normalized_family_pos_tags,
    )


class RuntimeSimilarityBackend:
    def __init__(
        self,
        *,
        scorer_id: str,
        model_name: str = DEFAULT_EMBEDDING_BRIDGE_MODEL,
    ) -> None:
        normalized_scorer_id = str(scorer_id or "").strip() or "token_jaccard"
        if normalized_scorer_id not in SENTENCE_VETO_SCORERS:
            raise ValueError(
                f"Unsupported sentence-veto scorer: {normalized_scorer_id!r}; "
                f"expected one of {SENTENCE_VETO_SCORERS!r}"
            )
        self.scorer_id = normalized_scorer_id
        self.model_name = str(model_name or "").strip() or DEFAULT_EMBEDDING_BRIDGE_MODEL
        self._token_sets: dict[str, frozenset[str]] = {}
        self._tfidf_vocabulary: dict[tuple[str, ...], int] = {}
        self._tfidf_idf: np.ndarray | None = None
        self._row_lookup: dict[str, int] = {}
        self._normalized_matrix: np.ndarray | None = None
        self._embedding_model = None

    def fit(self, texts: Sequence[str]) -> None:
        normalized_texts = []
        seen: set[str] = set()
        for raw_text in texts:
            text = str(raw_text or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            normalized_texts.append(text)
        if not normalized_texts:
            return
        if self.scorer_id == "token_jaccard":
            self._token_sets = {
                text: frozenset(_normalize_text_tokens(text)) for text in normalized_texts
            }
            return
        if self.scorer_id == "tfidf_cosine":
            self._tfidf_vocabulary, self._tfidf_idf = _build_runtime_tfidf_components(
                normalized_texts
            )
            dense_rows = [
                _build_runtime_tfidf_row(
                    _build_runtime_tfidf_terms(text),
                    vocabulary=self._tfidf_vocabulary,
                    idf=self._tfidf_idf,
                )
                for text in normalized_texts
            ]
            dense_matrix = (
                np.vstack(dense_rows)
                if dense_rows
                else np.zeros((0, len(self._tfidf_vocabulary)), dtype=np.float64)
            )
            self._row_lookup = {text: index for index, text in enumerate(normalized_texts)}
            self._normalized_matrix = _normalize_embedding_rows(dense_matrix)
            return
        if self.scorer_id == "sentence_transformer_cosine":
            try:
                from sentence_transformers import SentenceTransformer
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "sentence_transformers is required for sentence_transformer_cosine."
                ) from exc

            self._embedding_model = SentenceTransformer(self.model_name)
            encoded = self._embedding_model.encode(
                normalized_texts,
                normalize_embeddings=True,
            )
            dense_matrix = np.asarray(encoded, dtype=np.float64)
            self._row_lookup = {text: index for index, text in enumerate(normalized_texts)}
            self._normalized_matrix = _normalize_embedding_rows(dense_matrix)
            return

    def similarity(self, left_text: str, right_text: str) -> float:
        left = str(left_text or "").strip()
        right = str(right_text or "").strip()
        if not left or not right:
            return 0.0
        if self.scorer_id == "token_jaccard":
            left_tokens = self._token_sets.get(left)
            if left_tokens is None:
                left_tokens = frozenset(_normalize_text_tokens(left))
                self._token_sets[left] = left_tokens
            right_tokens = self._token_sets.get(right)
            if right_tokens is None:
                right_tokens = frozenset(_normalize_text_tokens(right))
                self._token_sets[right] = right_tokens
            union = left_tokens | right_tokens
            if not union:
                return 0.0
            return len(left_tokens & right_tokens) / len(union)
        if self.scorer_id == "tfidf_cosine":
            return self._vector_similarity(left, right)
        if self.scorer_id == "sentence_transformer_cosine":
            return self._vector_similarity(left, right)
        return 0.0

    def _vector_similarity(self, left_text: str, right_text: str) -> float:
        left_index = self._resolve_row_index(left_text)
        right_index = self._resolve_row_index(right_text)
        if left_index is None or right_index is None or self._normalized_matrix is None:
            return 0.0
        cosine = float(self._normalized_matrix[left_index] @ self._normalized_matrix[right_index])
        if self.scorer_id == "sentence_transformer_cosine":
            return max(0.0, min(1.0, (cosine + 1.0) / 2.0))
        return max(0.0, min(1.0, cosine))

    def _resolve_row_index(self, text: str) -> int | None:
        index = self._row_lookup.get(text)
        if index is not None:
            return index
        if self.scorer_id == "tfidf_cosine" and self._tfidf_idf is not None:
            dense_row = _normalize_embedding_rows(
                _build_runtime_tfidf_row(
                    _build_runtime_tfidf_terms(text),
                    vocabulary=self._tfidf_vocabulary,
                    idf=self._tfidf_idf,
                )
            )
        elif self.scorer_id == "sentence_transformer_cosine" and self._embedding_model is not None:
            encoded = self._embedding_model.encode([text], normalize_embeddings=True)
            dense_row = _normalize_embedding_rows(np.asarray(encoded, dtype=np.float64))
        else:
            return None
        if self._normalized_matrix is None:
            self._normalized_matrix = dense_row
            resolved_index = 0
        else:
            resolved_index = int(self._normalized_matrix.shape[0])
            self._normalized_matrix = np.vstack([self._normalized_matrix, dense_row])
        self._row_lookup[text] = resolved_index
        return resolved_index


def evaluate_runtime_veto_case(
    *,
    family_id: str,
    case: Mapping[str, object],
    active_sense: Mapping[str, object],
    shadow_senses: Sequence[Mapping[str, object]],
    scorer: RuntimeSimilarityBackend,
    context_view: str = DEFAULT_SENTENCE_VETO_CONTEXT_VIEW,
    evidence_view: str = DEFAULT_SENTENCE_VETO_EVIDENCE_VIEW,
    min_active_score: float = DEFAULT_SENTENCE_VETO_MIN_ACTIVE_SCORE,
    min_margin: float = DEFAULT_SENTENCE_VETO_MIN_MARGIN,
    phrase_control_mode: str = DEFAULT_SENTENCE_VETO_PHRASE_CONTROL_MODE,
    family_pos_tags: Sequence[str] = (),
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
) -> RuntimeVetoCaseScore:
    sentence = str(case.get("sentence") or "").strip()
    source_phrase = str(case.get("source_phrase") or case.get("trigger") or "").strip()
    context_views = build_runtime_context_views(
        sentence,
        source_phrase=source_phrase,
        mask_token=mask_token,
        window_tokens=window_tokens,
    )
    resolved_context_view = str(context_view or "").strip() or DEFAULT_SENTENCE_VETO_CONTEXT_VIEW
    if resolved_context_view not in SENTENCE_VETO_CONTEXT_VIEWS:
        raise ValueError(
            f"Unsupported context view: {resolved_context_view!r}; "
            f"expected one of {SENTENCE_VETO_CONTEXT_VIEWS!r}"
        )
    context_text = str(context_views.get(resolved_context_view) or "").strip()
    active_evidence_text = resolve_runtime_evidence_text(
        active_sense,
        evidence_view=evidence_view,
    )
    active_score = scorer.similarity(context_text, active_evidence_text)

    strongest_shadow_id = ""
    strongest_shadow_score = 0.0
    strongest_shadow_evidence_text = ""
    for shadow_sense in shadow_senses:
        shadow_id = str(shadow_sense.get("sense_id") or "").strip()
        shadow_evidence_text = resolve_runtime_evidence_text(
            shadow_sense,
            evidence_view=evidence_view,
        )
        shadow_score = scorer.similarity(context_text, shadow_evidence_text)
        if shadow_score > strongest_shadow_score or (
            shadow_score == strongest_shadow_score
            and shadow_id
            and strongest_shadow_id
            and shadow_id < strongest_shadow_id
        ):
            strongest_shadow_id = shadow_id
            strongest_shadow_score = shadow_score
            strongest_shadow_evidence_text = shadow_evidence_text

    active_sense_id = str(active_sense.get("sense_id") or "").strip()
    predicted_winner = active_sense_id
    predicted_winner_type = "active"
    if strongest_shadow_id and strongest_shadow_score > active_score:
        predicted_winner = strongest_shadow_id
        predicted_winner_type = "shadow"
    margin = float(active_score) - float(strongest_shadow_score)
    predicted_decision = decide_runtime_veto_outcome(
        active_score=active_score,
        strongest_shadow_score=strongest_shadow_score,
        min_active_score=min_active_score,
        min_margin=min_margin,
    )
    resolved_phrase_control_mode = (
        str(phrase_control_mode or "").strip() or DEFAULT_SENTENCE_VETO_PHRASE_CONTROL_MODE
    )
    if resolved_phrase_control_mode not in SENTENCE_VETO_PHRASE_CONTROL_MODES:
        raise ValueError(
            f"Unsupported phrase control mode: {resolved_phrase_control_mode!r}; "
            f"expected one of {SENTENCE_VETO_PHRASE_CONTROL_MODES!r}"
        )
    phrase_control_signals = extract_runtime_phrase_control_signals(
        sentence,
        source_phrase=source_phrase,
        family_pos_tags=family_pos_tags,
    )
    if (
        resolved_phrase_control_mode == "noun_family_frame_guard"
        and phrase_control_signals.phrase_preemption_hit
    ):
        predicted_decision = "abstain"
    gold_winner = str(case.get("gold_winner") or "").strip()
    gold_winner_type = _classify_gold_winner_type(gold_winner, active_sense_id=active_sense_id)
    gold_decision = str(case.get("gold_decision") or "").strip().lower()
    if gold_decision not in {"replace", "abstain"}:
        gold_decision = "replace" if gold_winner_type == "active" else "abstain"

    return RuntimeVetoCaseScore(
        case_id=str(case.get("case_id") or "").strip(),
        family_id=str(family_id or "").strip(),
        gold_decision=gold_decision,
        gold_winner=gold_winner,
        gold_winner_type=gold_winner_type,
        predicted_decision=predicted_decision,
        predicted_winner=predicted_winner,
        predicted_winner_type=predicted_winner_type,
        active_score=float(active_score),
        strongest_shadow_score=float(strongest_shadow_score),
        margin=float(margin),
        strongest_shadow_id=strongest_shadow_id,
        context_text=context_text,
        active_evidence_text=active_evidence_text,
        strongest_shadow_evidence_text=strongest_shadow_evidence_text,
        phrase_preemption_hit=phrase_control_signals.phrase_preemption_hit,
        matched_phrase_pattern=phrase_control_signals.matched_phrase_pattern,
        phrase_reason_code=phrase_control_signals.phrase_reason_code,
    )


def _classify_gold_winner_type(gold_winner: str, *, active_sense_id: str) -> str:
    normalized_gold_winner = str(gold_winner or "").strip()
    if not normalized_gold_winner or normalized_gold_winner in {"none", "abstain"}:
        return "none"
    if normalized_gold_winner == active_sense_id:
        return "active"
    return "shadow"


def _find_phrase_token_span(
    sentence_tokens: Sequence[str],
    phrase_tokens: Sequence[str],
) -> tuple[int, int] | None:
    normalized_sentence_tokens = [_normalize_surface_token(token) for token in sentence_tokens]
    normalized_phrase_tokens = [
        token for token in (_normalize_surface_token(token) for token in phrase_tokens) if token
    ]
    if not normalized_phrase_tokens:
        return None
    phrase_length = len(normalized_phrase_tokens)
    for index in range(0, len(normalized_sentence_tokens) - phrase_length + 1):
        if normalized_sentence_tokens[index : index + phrase_length] == normalized_phrase_tokens:
            return (index, index + phrase_length)
    return None


def _normalize_surface_token(token: str) -> str:
    matches = _TOKEN_RE.findall(str(token or "").lower())
    return matches[0] if matches else ""


def _normalize_text_tokens(text: str) -> list[str]:
    return [match.lower() for match in _TOKEN_RE.findall(str(text or ""))]


def _build_runtime_tfidf_terms(text: str) -> list[tuple[str, ...]]:
    tokens = _normalize_text_tokens(text)
    terms: list[tuple[str, ...]] = []
    for ngram_size in (1, 2):
        if len(tokens) < ngram_size:
            continue
        for index in range(0, len(tokens) - ngram_size + 1):
            terms.append(tuple(tokens[index : index + ngram_size]))
    return terms


def _build_runtime_tfidf_components(
    texts: Sequence[str],
) -> tuple[dict[tuple[str, ...], int], np.ndarray]:
    documents = [_build_runtime_tfidf_terms(text) for text in texts]
    document_frequency: dict[tuple[str, ...], int] = {}
    for document in documents:
        for term in set(document):
            document_frequency[term] = document_frequency.get(term, 0) + 1
    vocabulary = {
        term: index
        for index, term in enumerate(sorted(document_frequency, key=lambda value: value))
    }
    idf = np.zeros((len(vocabulary),), dtype=np.float64)
    document_count = max(1, len(documents))
    for term, index in vocabulary.items():
        idf[index] = (
            np.log((1.0 + float(document_count)) / (1.0 + float(document_frequency[term]))) + 1.0
        )
    return vocabulary, idf


def _build_runtime_tfidf_row(
    terms: Sequence[tuple[str, ...]],
    *,
    vocabulary: Mapping[tuple[str, ...], int],
    idf: np.ndarray,
) -> np.ndarray:
    row = np.zeros((1, len(vocabulary)), dtype=np.float64)
    if not vocabulary or not terms:
        return row
    counts: dict[int, int] = {}
    for term in terms:
        index = vocabulary.get(term)
        if index is None:
            continue
        counts[index] = counts.get(index, 0) + 1
    for index, count in counts.items():
        row[0, index] = float(count) * float(idf[index])
    return row


def _normalize_embedding_rows(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2:
        raise ValueError("Expected a 2D matrix for runtime-veto scoring normalization.")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms
