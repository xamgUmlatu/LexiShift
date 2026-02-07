from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


POS_BUCKET_NOUN = "noun"
POS_BUCKET_ADJECTIVE = "adjective"
POS_BUCKET_VERB = "verb"
POS_BUCKET_ADVERB = "adverb"
POS_BUCKET_OTHER = "other"


# Admission coefficients are intentionally explicit and centralized so they can
# be tuned from a single place and surfaced in diagnostics.
DEFAULT_POS_WEIGHT_NOUN = 1.00
DEFAULT_POS_WEIGHT_ADJECTIVE = 0.85
DEFAULT_POS_WEIGHT_VERB = 0.70
DEFAULT_POS_WEIGHT_ADVERB = 0.55
DEFAULT_POS_WEIGHT_OTHER = 0.40


@dataclass(frozen=True)
class AdmissionPosWeights:
    noun: float = DEFAULT_POS_WEIGHT_NOUN
    adjective: float = DEFAULT_POS_WEIGHT_ADJECTIVE
    verb: float = DEFAULT_POS_WEIGHT_VERB
    adverb: float = DEFAULT_POS_WEIGHT_ADVERB
    other: float = DEFAULT_POS_WEIGHT_OTHER

    def for_bucket(self, bucket: str) -> float:
        normalized_bucket = str(bucket or POS_BUCKET_OTHER).strip().lower()
        if normalized_bucket == POS_BUCKET_NOUN:
            return float(self.noun)
        if normalized_bucket == POS_BUCKET_ADJECTIVE:
            return float(self.adjective)
        if normalized_bucket == POS_BUCKET_VERB:
            return float(self.verb)
        if normalized_bucket == POS_BUCKET_ADVERB:
            return float(self.adverb)
        return float(self.other)

    def to_dict(self) -> dict[str, float]:
        return {
            POS_BUCKET_NOUN: float(self.noun),
            POS_BUCKET_ADJECTIVE: float(self.adjective),
            POS_BUCKET_VERB: float(self.verb),
            POS_BUCKET_ADVERB: float(self.adverb),
            POS_BUCKET_OTHER: float(self.other),
        }


def resolve_default_pos_weights(*, language_pair: str) -> AdmissionPosWeights:
    # Keep default behavior predictable across pairs. Language-specific
    # overrides can branch here once profile-aware policy is introduced.
    _ = language_pair
    return AdmissionPosWeights()


def classify_pos_bucket(*, language_pair: str, raw_pos: Optional[str]) -> str:
    normalized = str(raw_pos or "").strip()
    if not normalized:
        return POS_BUCKET_OTHER

    target_language = _target_language_from_pair(language_pair)
    if target_language == "ja":
        return _classify_ja_pos_bucket(normalized)
    return _classify_generic_pos_bucket(normalized)


def compute_admission_weight(
    *,
    language_pair: str,
    raw_pos: Optional[str],
    base_weight: float,
    pos_weights: Optional[AdmissionPosWeights] = None,
) -> tuple[str, float, float]:
    resolved_weights = pos_weights or resolve_default_pos_weights(language_pair=language_pair)
    bucket = classify_pos_bucket(language_pair=language_pair, raw_pos=raw_pos)
    pos_weight = resolved_weights.for_bucket(bucket)
    admission_weight = max(0.0, float(base_weight)) * max(0.0, float(pos_weight))
    return bucket, pos_weight, admission_weight


def _target_language_from_pair(pair: str) -> str:
    normalized_pair = str(pair or "").strip()
    source, separator, target = normalized_pair.partition("-")
    _ = source
    if not separator:
        return ""
    return target.strip().lower()


def _classify_ja_pos_bucket(raw_pos: str) -> str:
    head = raw_pos.split("-", 1)[0].strip()
    if head == "名詞":
        return POS_BUCKET_NOUN
    if head in {"形容詞", "形状詞"}:
        return POS_BUCKET_ADJECTIVE
    if head == "動詞":
        return POS_BUCKET_VERB
    if head == "副詞":
        return POS_BUCKET_ADVERB
    return POS_BUCKET_OTHER


def _classify_generic_pos_bucket(raw_pos: str) -> str:
    lowered = raw_pos.lower()
    if "noun" in lowered:
        return POS_BUCKET_NOUN
    if "adj" in lowered:
        return POS_BUCKET_ADJECTIVE
    if "verb" in lowered:
        return POS_BUCKET_VERB
    if "adv" in lowered:
        return POS_BUCKET_ADVERB
    return POS_BUCKET_OTHER
