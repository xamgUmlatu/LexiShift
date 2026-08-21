from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
from typing import Mapping, Sequence

from lexishift_core.lexicon.word_package import normalize_reading
from lexishift_core.srs.admission_features import clamp01, safe_optional_float

LEARNER_DIFFICULTY_MODEL_VERSION = "learner_difficulty_v1"
CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV = "LEXISHIFT_EN_JA_LEARNER_DIFFICULTY_CSV"
CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV = "LEXISHIFT_EN_ES_LEARNER_DIFFICULTY_CSV"
CORRECTED_EN_DE_LEARNER_DIFFICULTY_CSV_ENV = "LEXISHIFT_EN_DE_LEARNER_DIFFICULTY_CSV"
_PACKAGED_RESOURCE_ROOT = Path(__file__).resolve().parents[1] / "resources" / "srs" / "en_ja"
PACKAGED_EN_JA_LEARNER_DIFFICULTY_CSV = _PACKAGED_RESOURCE_ROOT / "learner_difficulty_corrected.csv"
PACKAGED_EN_JA_LEARNER_DIFFICULTY_MANUAL_CORRECTIONS_JSON = (
    _PACKAGED_RESOURCE_ROOT / "learner_difficulty_manual_corrections.json"
)
_PACKAGED_SRS_RESOURCE_ROOT = Path(__file__).resolve().parents[1] / "resources" / "srs"
CORRECTED_LEARNER_DIFFICULTY_CSV_ENV_BY_PAIR = {
    "en-ja": CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV,
    "en-es": CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV,
    "en-de": CORRECTED_EN_DE_LEARNER_DIFFICULTY_CSV_ENV,
}
PACKAGED_LEARNER_DIFFICULTY_CSV_BY_PAIR = {
    "en-ja": PACKAGED_EN_JA_LEARNER_DIFFICULTY_CSV,
    "en-es": _PACKAGED_SRS_RESOURCE_ROOT / "en_es" / "learner_difficulty_corrected.csv",
    "en-de": _PACKAGED_SRS_RESOURCE_ROOT / "en_de" / "learner_difficulty_corrected.csv",
}

_EN_JA_EXACT_LEARNER_DIFFICULTY: Mapping[str, tuple[float, str]] = {
    "する": (0.005, "beginner_core_verb"),
    "いる": (0.005, "beginner_core_verb"),
    "ある": (0.12, "beginner_core_verb"),
    "なる": (0.005, "beginner_core_verb"),
    "見る": (0.20, "beginner_core_verb"),
    "行く": (0.22, "beginner_core_verb"),
    "食べる": (0.28, "beginner_core_verb"),
    "飲む": (0.32, "beginner_core_verb"),
    "こと": (0.12, "beginner_core_nominalizer"),
    "ため": (0.16, "beginner_core_grammar_noun"),
    "よう": (0.12, "beginner_core_grammar_noun"),
    "ところ": (0.01, "beginner_core_place_noun"),
    "これ": (0.005, "beginner_core_demonstrative"),
    "それ": (0.008, "beginner_core_demonstrative"),
    "この": (0.03, "beginner_core_demonstrative"),
    "その": (0.04, "beginner_core_demonstrative"),
    "ここ": (0.025, "beginner_core_location"),
    "そこ": (0.03, "beginner_core_location"),
    "どこ": (0.025, "beginner_core_location"),
    "いつ": (0.12, "beginner_core_question_word"),
    "私": (0.04, "beginner_core_pronoun"),
    "あなた": (0.12, "beginner_core_pronoun"),
    "彼": (0.18, "beginner_core_pronoun"),
    "彼女": (0.20, "beginner_core_pronoun"),
    "我々": (0.45, "formal_pronoun"),
    "あの": (0.08, "beginner_core_deictic"),
    "あれ": (0.13, "beginner_core_deictic"),
    "あっ": (0.30, "common_interjection"),
    "いただく": (0.13, "beginner_polite_verb"),
    "なお": (0.415, "written_adverb"),
    "大きい": (0.28, "beginner_core_adjective"),
    "小さい": (0.28, "beginner_core_adjective"),
    "赤い": (0.32, "beginner_core_color"),
    "青い": (0.32, "beginner_core_color"),
    "水": (0.25, "beginner_core_nature"),
    "火": (0.35, "beginner_core_nature"),
    "山": (0.35, "beginner_core_nature"),
    "川": (0.35, "beginner_core_nature"),
    "犬": (0.20, "beginner_core_animal"),
    "猫": (0.20, "beginner_core_animal"),
    "鳥": (0.30, "beginner_core_animal"),
    "魚": (0.30, "beginner_core_animal"),
    "パン": (0.30, "beginner_core_food"),
    "レタス": (0.30, "beginner_core_food"),
}

_EN_JA_EXACT_READING_LEARNER_DIFFICULTY: Mapping[tuple[str, str], tuple[float, str]] = {
    ("月", "がつ"): (0.18, "common_calendar_reading"),
    ("月", "げつ"): (0.28, "common_calendar_reading"),
    ("月", "つき"): (0.20, "common_noun_reading"),
    ("週", "しゅう"): (0.22, "common_calendar_reading"),
    ("秒", "びょう"): (0.24, "common_measure_reading"),
    ("度", "ど"): (0.30, "common_measure_reading"),
    ("度", "たび"): (0.36, "common_wago_reading"),
    ("袋", "ふくろ"): (0.26, "common_noun_reading"),
    ("版", "はん"): (0.36, "common_publication_reading"),
    ("種", "しゅ"): (0.45, "common_bound_sino_reading"),
}


@dataclass(frozen=True)
class LearnerDifficultyEstimate:
    value: float
    proxy: str
    sources: Sequence[str]
    frequency_proxy: float

    def to_dict(self) -> dict[str, object]:
        return {
            "version": LEARNER_DIFFICULTY_MODEL_VERSION,
            "value": round(float(self.value), 6),
            "proxy": self.proxy,
            "sources": list(self.sources),
            "frequency_proxy": round(float(self.frequency_proxy), 6),
        }


@dataclass(frozen=True)
class CorrectedLearnerDifficultyRow:
    lemma: str
    reading: str
    score: float
    rank: int | None
    band: str | None
    candidate_state: str | None
    correction_types: tuple[str, ...]
    display_form: str | None
    admission_override: str | None
    topic_stretch_allowed: str | None
    manual_correction_active: str | None


@dataclass(frozen=True)
class CorrectedLearnerDifficultyMatch:
    row: CorrectedLearnerDifficultyRow
    match_mode: str


@dataclass(frozen=True)
class _CorrectedDifficultyIndex:
    by_pair: Mapping[tuple[str, str], CorrectedLearnerDifficultyRow]
    by_display_pair: Mapping[tuple[str, str], CorrectedLearnerDifficultyRow]
    by_unique_lemma: Mapping[str, CorrectedLearnerDifficultyRow]
    by_unique_display_form: Mapping[str, CorrectedLearnerDifficultyRow]


def estimate_learner_difficulty(
    *,
    language_pair: object,
    lemma: object,
    reading: object = None,
    reading_candidates: Sequence[object] | None = None,
    frequency_proxy: object,
    candidate_state: object = None,
    presentation_mode: object = None,
    problem_class: object = None,
) -> LearnerDifficultyEstimate:
    del candidate_state, presentation_mode, problem_class
    base = clamp01(safe_optional_float(frequency_proxy)) or 0.0
    pair = str(language_pair or "").strip().lower()
    surface = str(lemma or "").strip()
    corrected = lookup_corrected_learner_difficulty(
        language_pair=pair,
        lemma=surface,
        reading=reading,
        reading_candidates=reading_candidates,
    )
    if corrected is not None:
        pair_source = pair.replace("-", "_")
        return LearnerDifficultyEstimate(
            value=clamp01(corrected.row.score) or 0.0,
            proxy=(
                f"{LEARNER_DIFFICULTY_MODEL_VERSION}:"
                f"{pair_source}_corrected_ranking:{corrected.match_mode}"
            ),
            sources=(
                "frequency_proxy",
                f"{pair_source}_corrected_learner_difficulty_csv",
                corrected.match_mode,
            ),
            frequency_proxy=base,
        )
    if pair == "en-ja":
        for candidate_reading in _normalized_reading_candidates(
            pair,
            reading,
            *(reading_candidates or ()),
        ):
            exact_reading = _EN_JA_EXACT_READING_LEARNER_DIFFICULTY.get(
                (surface, candidate_reading)
            )
            if exact_reading is not None:
                value, source = exact_reading
                return LearnerDifficultyEstimate(
                    value=clamp01(value) or 0.0,
                    proxy=f"{LEARNER_DIFFICULTY_MODEL_VERSION}:en_ja_reading_exact_overlay",
                    sources=("frequency_proxy", source),
                    frequency_proxy=base,
                )
        exact = _EN_JA_EXACT_LEARNER_DIFFICULTY.get(surface)
        if exact is not None:
            value, source = exact
            return LearnerDifficultyEstimate(
                value=clamp01(value) or 0.0,
                proxy=f"{LEARNER_DIFFICULTY_MODEL_VERSION}:en_ja_exact_overlay",
                sources=("frequency_proxy", source),
                frequency_proxy=base,
            )
    return LearnerDifficultyEstimate(
        value=base,
        proxy="1_minus_base_weight",
        sources=("frequency_proxy",),
        frequency_proxy=base,
    )


def lookup_corrected_en_ja_learner_difficulty(
    *,
    lemma: object,
    reading: object = None,
    reading_candidates: Sequence[object] | None = None,
    csv_path: object = None,
) -> CorrectedLearnerDifficultyMatch | None:
    return lookup_corrected_learner_difficulty(
        language_pair="en-ja",
        lemma=lemma,
        reading=reading,
        reading_candidates=reading_candidates,
        csv_path=csv_path,
    )


def lookup_corrected_learner_difficulty(
    *,
    language_pair: object,
    lemma: object,
    reading: object = None,
    reading_candidates: Sequence[object] | None = None,
    csv_path: object = None,
) -> CorrectedLearnerDifficultyMatch | None:
    pair = _normalize_pair(language_pair)
    path = _resolve_corrected_csv_path(pair, csv_path)
    if path is None:
        return None
    surface = str(lemma or "").strip()
    if not surface:
        return None
    index = _load_corrected_index(pair, str(path))
    for candidate_reading in _normalized_reading_candidates(
        pair,
        reading,
        *(reading_candidates or ()),
    ):
        row = index.by_pair.get((surface, candidate_reading))
        if row is not None:
            return CorrectedLearnerDifficultyMatch(row=row, match_mode="exact_pair")
        row = index.by_display_pair.get((surface, candidate_reading))
        if row is not None:
            return CorrectedLearnerDifficultyMatch(row=row, match_mode="exact_display_pair")
    row = index.by_unique_lemma.get(surface)
    if row is not None:
        return CorrectedLearnerDifficultyMatch(row=row, match_mode="unique_lemma")
    row = index.by_unique_display_form.get(surface)
    if row is not None:
        return CorrectedLearnerDifficultyMatch(row=row, match_mode="unique_display_form")
    return None


def clear_corrected_learner_difficulty_cache() -> None:
    _load_corrected_index.cache_clear()


def resolve_corrected_en_ja_learner_difficulty_csv_path(
    csv_path: object = None,
) -> Path | None:
    return _resolve_corrected_csv_path("en-ja", csv_path)


def resolve_corrected_learner_difficulty_csv_path(
    *,
    language_pair: object,
    csv_path: object = None,
) -> Path | None:
    return _resolve_corrected_csv_path(_normalize_pair(language_pair), csv_path)


def resolve_packaged_en_ja_learner_difficulty_manual_corrections_path() -> Path | None:
    path = PACKAGED_EN_JA_LEARNER_DIFFICULTY_MANUAL_CORRECTIONS_JSON
    if path.exists() and path.is_file():
        return path
    return None


def _resolve_corrected_en_ja_csv_path(csv_path: object = None) -> Path | None:
    return _resolve_corrected_csv_path("en-ja", csv_path)


def _resolve_corrected_csv_path(pair: str, csv_path: object = None) -> Path | None:
    raw_path = str(csv_path or "").strip()
    if not raw_path:
        env_name = CORRECTED_LEARNER_DIFFICULTY_CSV_ENV_BY_PAIR.get(pair, "")
        raw_path = os.environ.get(env_name, "").strip() if env_name else ""
    if not raw_path:
        path = PACKAGED_LEARNER_DIFFICULTY_CSV_BY_PAIR.get(pair)
        if path is None:
            return None
    else:
        path = Path(raw_path).expanduser()
    if not path.exists() or not path.is_file():
        return None
    return path


@lru_cache(maxsize=4)
def _load_corrected_index(pair: str, path_text: str) -> _CorrectedDifficultyIndex:
    by_pair: dict[tuple[str, str], CorrectedLearnerDifficultyRow] = {}
    by_display_pair: dict[tuple[str, str], CorrectedLearnerDifficultyRow] = {}
    by_lemma_rows: dict[str, list[CorrectedLearnerDifficultyRow]] = {}
    by_display_form_rows: dict[str, list[CorrectedLearnerDifficultyRow]] = {}
    path = Path(path_text)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            row = _parse_corrected_row(raw_row, pair=pair)
            if row is None:
                continue
            if row.reading:
                by_pair.setdefault((row.lemma, row.reading), row)
                if row.display_form:
                    by_display_pair.setdefault((row.display_form, row.reading), row)
            by_lemma_rows.setdefault(row.lemma, []).append(row)
            if row.display_form:
                by_display_form_rows.setdefault(row.display_form, []).append(row)
    by_unique_lemma = {lemma: rows[0] for lemma, rows in by_lemma_rows.items() if len(rows) == 1}
    by_unique_display_form = {
        display_form: rows[0]
        for display_form, rows in by_display_form_rows.items()
        if len(rows) == 1
    }
    return _CorrectedDifficultyIndex(
        by_pair=by_pair,
        by_display_pair=by_display_pair,
        by_unique_lemma=by_unique_lemma,
        by_unique_display_form=by_unique_display_form,
    )


def _parse_corrected_row(
    row: Mapping[str, object],
    *,
    pair: str,
) -> CorrectedLearnerDifficultyRow | None:
    lemma = str(row.get("lemma") or "").strip()
    reading = _normalize_corrected_reading(row.get("reading"), pair=pair)
    score = clamp01(safe_optional_float(row.get("score")))
    if not lemma or score is None:
        return None
    return CorrectedLearnerDifficultyRow(
        lemma=lemma,
        reading=reading,
        score=score,
        rank=_int_or_none(row.get("rank")),
        band=str(row.get("band") or "").strip() or None,
        candidate_state=str(row.get("candidate_state") or "").strip() or None,
        correction_types=tuple(
            part.strip()
            for part in str(row.get("correction_types") or "").split(",")
            if part.strip()
        ),
        display_form=str(row.get("display_form") or "").strip() or None,
        admission_override=str(row.get("admission_override") or "").strip() or None,
        topic_stretch_allowed=str(row.get("topic_stretch_allowed") or "").strip() or None,
        manual_correction_active=str(row.get("manual_correction_active") or "").strip() or None,
    )


def _normalized_reading_candidates(pair: str, *values: object) -> tuple[str, ...]:
    candidates: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        normalized = _normalize_corrected_reading(value, pair=pair)
        if not normalized or normalized in seen:
            continue
        candidates.append(normalized)
        seen.add(normalized)
    return tuple(candidates)


def _normalize_corrected_reading(value: object, *, pair: str) -> str:
    if pair == "en-ja":
        return normalize_reading(value, language_tag="ja")
    return str(value or "").strip().lower()


def _normalize_pair(value: object) -> str:
    return str(value or "").strip().lower()


def _int_or_none(value: object) -> int | None:
    parsed = safe_optional_float(value)
    if parsed is None:
        return None
    return int(parsed)
