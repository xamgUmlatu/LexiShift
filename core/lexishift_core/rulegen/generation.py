from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping, Optional, Protocol, Sequence

from lexishift_core.replacement.core import RuleMetadata, VocabRule


@dataclass(frozen=True)
class RuleCandidate:
    source_phrase: str
    replacement: str
    language_pair: str
    source_dict: str
    source_type: str = "synonym"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RuleConfidenceSignals:
    dict_priority: float = 0.0
    frequency_weight: float = 0.0
    pos_match: float = 0.0
    variant_penalty: float = 0.0
    phrase_penalty: float = 0.0
    embedding_score: Optional[float] = None


@dataclass(frozen=True)
class RuleScoreWeights:
    dict_priority: float = 0.6
    frequency_weight: float = 0.2
    pos_match: float = 0.1
    variant_penalty: float = 0.1
    phrase_penalty: float = 0.1
    embedding_weight: float = 0.2


class RuleScorer:
    def __init__(self, weights: Optional[RuleScoreWeights] = None) -> None:
        self._weights = weights or RuleScoreWeights()

    def score(self, signals: RuleConfidenceSignals) -> float:
        weights = self._weights
        score = (
            (signals.dict_priority * weights.dict_priority)
            + (signals.frequency_weight * weights.frequency_weight)
            + (signals.pos_match * weights.pos_match)
            - (signals.variant_penalty * weights.variant_penalty)
            - (signals.phrase_penalty * weights.phrase_penalty)
        )
        if signals.embedding_score is not None:
            score += (signals.embedding_score - 0.5) * weights.embedding_weight
        return _clamp(score)


class CandidateSource(Protocol):
    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        ...


class CandidateNormalizer(Protocol):
    def normalize(self, candidate: RuleCandidate) -> RuleCandidate:
        ...


class VariantExpander(Protocol):
    def expand(self, candidate: RuleCandidate) -> Iterable[RuleCandidate]:
        ...


class CandidateFilter(Protocol):
    def accept(self, candidate: RuleCandidate) -> bool:
        ...


class SignalProvider(Protocol):
    def signals(self, candidate: RuleCandidate) -> RuleConfidenceSignals:
        ...


@dataclass(frozen=True)
class RuleGenerationConfig:
    language_pair: str
    confidence_threshold: float = 0.0
    base_priority: int = 0
    case_policy: str = "match"
    tags: Sequence[str] = field(default_factory=tuple)
    dedupe: bool = True


@dataclass(frozen=True)
class RuleGenerationResult:
    candidate: RuleCandidate
    confidence: float
    rule: VocabRule


class RuleGenerationPipeline:
    def __init__(
        self,
        *,
        sources: Sequence[CandidateSource],
        normalizers: Sequence[CandidateNormalizer] | None = None,
        expanders: Sequence[VariantExpander] | None = None,
        filters: Sequence[CandidateFilter] | None = None,
        scorer: Optional[RuleScorer] = None,
        signal_provider: Optional[SignalProvider] = None,
    ) -> None:
        self._sources = list(sources)
        self._normalizers = list(normalizers or [])
        self._expanders = list(expanders or [])
        self._filters = list(filters or [])
        self._scorer = scorer or RuleScorer()
        self._signal_provider = signal_provider

    def generate_results(
        self,
        targets: Iterable[str],
        *,
        config: RuleGenerationConfig,
    ) -> list[RuleGenerationResult]:
        seen: set[tuple[str, str, str]] = set()
        results: list[RuleGenerationResult] = []
        for candidate in self._iter_candidates(targets, config.language_pair):
            if config.dedupe:
                key = (
                    candidate.source_phrase.lower(),
                    candidate.replacement.lower(),
                    candidate.language_pair,
                )
                if key in seen:
                    continue
                seen.add(key)
            if not self._accept(candidate):
                continue
            signals = self._signal_provider.signals(candidate) if self._signal_provider else RuleConfidenceSignals()
            confidence = self._scorer.score(signals)
            if confidence < config.confidence_threshold:
                continue
            rule = self._to_rule(candidate, confidence, config)
            results.append(RuleGenerationResult(candidate=candidate, confidence=confidence, rule=rule))
        return results

    def generate_rules(
        self,
        targets: Iterable[str],
        *,
        config: RuleGenerationConfig,
    ) -> list[VocabRule]:
        return [result.rule for result in self.generate_results(targets, config=config)]

    def _iter_candidates(self, targets: Iterable[str], language_pair: str) -> Iterable[RuleCandidate]:
        for source in self._sources:
            for candidate in source.generate(targets, language_pair=language_pair):
                normalized = self._normalize(candidate)
                for expanded in self._expand_variants(normalized):
                    yield expanded

    def _normalize(self, candidate: RuleCandidate) -> RuleCandidate:
        normalized = candidate
        for normalizer in self._normalizers:
            normalized = normalizer.normalize(normalized)
        return normalized

    def _expand_variants(self, candidate: RuleCandidate) -> Iterable[RuleCandidate]:
        expanded: list[RuleCandidate] = [candidate]
        for expander in self._expanders:
            next_batch: list[RuleCandidate] = []
            for item in expanded:
                next_batch.extend(list(expander.expand(item)))
            expanded = next_batch or expanded
        return expanded

    def _accept(self, candidate: RuleCandidate) -> bool:
        return all(filt.accept(candidate) for filt in self._filters)

    def _to_rule(self, candidate: RuleCandidate, confidence: float, config: RuleGenerationConfig) -> VocabRule:
        script_forms = _normalize_script_forms(candidate.metadata.get("script_forms"))
        metadata = RuleMetadata(
            source=candidate.source_dict,
            source_type=candidate.source_type,
            language_pair=candidate.language_pair,
            confidence=confidence,
            script_forms=script_forms,
        )
        tags = list(config.tags)
        if candidate.source_type and candidate.source_type not in tags:
            tags.append(candidate.source_type)
        return VocabRule(
            source_phrase=candidate.source_phrase,
            replacement=candidate.replacement,
            priority=config.base_priority,
            case_policy=config.case_policy,
            enabled=True,
            tags=tuple(tags),
            metadata=metadata,
        )


@dataclass(frozen=True)
class SimpleSignalProvider:
    dict_priorities: Mapping[str, float] = field(default_factory=dict)
    frequency_provider: Optional[Callable[[RuleCandidate], float]] = None
    pos_match_provider: Optional[Callable[[RuleCandidate], float]] = None
    variant_penalty_provider: Optional[Callable[[RuleCandidate], float]] = None
    embedding_provider: Optional[Callable[[RuleCandidate], Optional[float]]] = None

    def signals(self, candidate: RuleCandidate) -> RuleConfidenceSignals:
        dict_priority = self.dict_priorities.get(candidate.source_dict, 0.0)
        frequency_weight = self.frequency_provider(candidate) if self.frequency_provider else 0.0
        pos_match = self.pos_match_provider(candidate) if self.pos_match_provider else 0.0
        variant_penalty = self.variant_penalty_provider(candidate) if self.variant_penalty_provider else 0.0
        phrase_penalty = 1.0 if " " in candidate.source_phrase.strip() else 0.0
        embedding_score = self.embedding_provider(candidate) if self.embedding_provider else None
        return RuleConfidenceSignals(
            dict_priority=dict_priority,
            frequency_weight=frequency_weight,
            pos_match=pos_match,
            variant_penalty=variant_penalty,
            phrase_penalty=phrase_penalty,
            embedding_score=embedding_score,
        )


@dataclass(frozen=True)
class MappingCandidateSource:
    mapping: Mapping[str, Sequence[str]]
    source_dict: str
    source_type: str = "synonym"

    def generate(self, targets: Iterable[str], *, language_pair: str) -> Iterable[RuleCandidate]:
        for target in targets:
            for source in self.mapping.get(target, []):
                yield RuleCandidate(
                    source_phrase=str(source),
                    replacement=str(target),
                    language_pair=language_pair,
                    source_dict=self.source_dict,
                    source_type=self.source_type,
                )


def _normalize_script_forms(value: object) -> Optional[dict[str, str]]:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, str] = {}
    for key, raw in dict(value).items():
        script = str(key or "").strip().lower()
        text = str(raw or "").strip()
        if not script or not text:
            continue
        normalized[script] = text
    return normalized or None


def _clamp(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))
