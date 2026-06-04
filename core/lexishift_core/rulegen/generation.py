from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping, Optional, Protocol, Sequence

from lexishift_core.lexicon.word_package import (
    normalize_word_package,
    resolve_language_tag_from_pair,
)
from lexishift_core.pos.normalization import (
    CANONICAL_POS_OTHER,
    CANONICAL_POS_TAGS,
)
from lexishift_core.replacement.core import RuleMetadata, VocabRule
from lexishift_core.rulegen.generation_selection import (
    _limit_results_per_target_with_ranking,
    _limit_rule_count_per_target_with_ranking,
    limit_rule_generation_results as _limit_rule_generation_results,
    resolve_reverse_hygiene_anchor_allowed_from_values as _resolve_reverse_hygiene_anchor_allowed_from_values,
)
from lexishift_core.rulegen.ranking import (
    CandidateRankingMechanism,
    DictionaryEntryOrderRankingMechanism,
)


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


@dataclass(frozen=True)
class PosMatchScoringConfig:
    enabled: bool = True
    exact_match_bonus: float = 1.0
    compatible_match_bonus: float = 0.5
    compatibility_classes: Optional[Mapping[str, str]] = None


@dataclass(frozen=True)
class RuleScoringConfig:
    weights: RuleScoreWeights = field(default_factory=RuleScoreWeights)
    pos_match: PosMatchScoringConfig = field(default_factory=PosMatchScoringConfig)


class RuleScorer:
    def __init__(self, weights: Optional[RuleScoreWeights] = None) -> None:
        self._weights = weights or RuleScoreWeights()

    def score(self, signals: RuleConfidenceSignals) -> float:
        return score_rule_confidence_signals(signals, weights=self._weights)


def score_rule_confidence_signals(
    signals: RuleConfidenceSignals,
    *,
    weights: Optional[RuleScoreWeights] = None,
) -> float:
    resolved_weights = weights or RuleScoreWeights()
    score = (
        (signals.dict_priority * resolved_weights.dict_priority)
        + (signals.frequency_weight * resolved_weights.frequency_weight)
        + (signals.pos_match * resolved_weights.pos_match)
        - (signals.variant_penalty * resolved_weights.variant_penalty)
        - (signals.phrase_penalty * resolved_weights.phrase_penalty)
    )
    if signals.embedding_score is not None:
        score += (signals.embedding_score - 0.5) * resolved_weights.embedding_weight
    return _clamp(score)


class CandidateSource(Protocol):
    def generate(
        self, targets: Iterable[str], *, language_pair: str
    ) -> Iterable[RuleCandidate]: ...


class CandidateNormalizer(Protocol):
    def normalize(self, candidate: RuleCandidate) -> RuleCandidate: ...


class VariantExpander(Protocol):
    def expand(self, candidate: RuleCandidate) -> Iterable[RuleCandidate]: ...


class CandidateFilter(Protocol):
    def accept(self, candidate: RuleCandidate) -> bool: ...


class SignalProvider(Protocol):
    def signals(self, candidate: RuleCandidate) -> RuleConfidenceSignals: ...


@dataclass(frozen=True)
class RuleGenerationConfig:
    language_pair: str
    confidence_threshold: float = 0.0
    max_definitions_per_target: Optional[int] = None
    max_rules_per_target: Optional[int] = None
    interleave_definition_groups: bool = False
    semantic_demotion_scale: float = 1.0
    base_priority: int = 0
    case_policy: str = "match"
    tags: Sequence[str] = field(default_factory=tuple)
    dedupe: bool = True


@dataclass(frozen=True)
class RuleGenerationResult:
    candidate: RuleCandidate
    confidence: float
    rule: VocabRule


DEFAULT_POS_EXACT_MATCH_BONUS = 1.0
DEFAULT_POS_COMPATIBLE_MATCH_BONUS = 0.5

DEFAULT_POS_COMPATIBILITY_CLASSES: Mapping[str, str] = {
    "noun": "nominal",
    "pronoun": "nominal",
    "determiner": "nominal",
    "numeral": "nominal",
    "adjective": "modifier",
    "adverb": "modifier",
    "verb": "verbal",
    "adposition": "connector",
    "conjunction": "connector",
    "interjection": "expressive",
    "punctuation": "punctuation",
}


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
        ranking_mechanism: Optional[CandidateRankingMechanism] = None,
    ) -> None:
        self._sources = list(sources)
        self._normalizers = list(normalizers or [])
        self._expanders = list(expanders or [])
        self._filters = list(filters or [])
        self._scorer = scorer or RuleScorer()
        self._signal_provider = signal_provider
        self._ranking_mechanism = ranking_mechanism or DictionaryEntryOrderRankingMechanism()

    def generate_results(
        self,
        targets: Iterable[str],
        *,
        config: RuleGenerationConfig,
    ) -> list[RuleGenerationResult]:
        semantic_demotion_scale = _normalize_semantic_demotion_scale(config.semantic_demotion_scale)
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
            signals = (
                self._signal_provider.signals(candidate)
                if self._signal_provider
                else RuleConfidenceSignals()
            )
            confidence = self._scorer.score(signals)
            if confidence < config.confidence_threshold:
                continue
            rule = self._to_rule(candidate, confidence, config)
            results.append(
                RuleGenerationResult(candidate=candidate, confidence=confidence, rule=rule)
            )
        limited_results = results
        max_definitions = config.max_definitions_per_target
        if max_definitions is not None:
            max_definitions = int(max_definitions)
            if max_definitions > 0:
                limited_results = _limit_results_per_target_with_ranking(
                    limited_results,
                    ranking_mechanism=self._ranking_mechanism,
                    max_definitions_per_target=max_definitions,
                    interleave_definition_groups=bool(config.interleave_definition_groups),
                    semantic_demotion_scale=semantic_demotion_scale,
                )
        max_rules = config.max_rules_per_target
        if max_rules is not None:
            max_rules = int(max_rules)
            if max_rules > 0:
                limited_results = _limit_rule_count_per_target_with_ranking(
                    limited_results,
                    ranking_mechanism=self._ranking_mechanism,
                    max_rules_per_target=max_rules,
                    semantic_demotion_scale=semantic_demotion_scale,
                )
        return limited_results

    def generate_rules(
        self,
        targets: Iterable[str],
        *,
        config: RuleGenerationConfig,
    ) -> list[VocabRule]:
        return [result.rule for result in self.generate_results(targets, config=config)]

    def _iter_candidates(
        self, targets: Iterable[str], language_pair: str
    ) -> Iterable[RuleCandidate]:
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

    def _to_rule(
        self, candidate: RuleCandidate, confidence: float, config: RuleGenerationConfig
    ) -> VocabRule:
        return materialize_vocab_rule(candidate, confidence=confidence, config=config)


def materialize_vocab_rule(
    candidate: RuleCandidate,
    *,
    confidence: float,
    config: RuleGenerationConfig,
) -> VocabRule:
    word_package = normalize_word_package(
        candidate.metadata.get("word_package"),
        fallback_surface=candidate.replacement,
        fallback_language_tag=resolve_language_tag_from_pair(candidate.language_pair),
        fallback_provider=candidate.source_dict or "rulegen",
    )
    script_forms = _normalize_script_forms(candidate.metadata.get("script_forms"))
    morphology = _normalize_morphology(candidate.metadata.get("morphology"))
    pos = _normalize_pos_metadata(candidate.metadata.get("pos"))
    if pos is None:
        pos = _build_pos_metadata_from_flat(candidate.metadata)
    if script_forms is None and word_package is not None:
        script_forms = _normalize_script_forms(word_package.get("script_forms"))
    rulegen = _normalize_rulegen_metadata(candidate.metadata)
    metadata = RuleMetadata(
        source=candidate.source_dict,
        source_type=candidate.source_type,
        language_pair=candidate.language_pair,
        confidence=confidence,
        script_forms=script_forms,
        word_package=word_package,
        morphology=morphology,
        pos=pos,
        rulegen=rulegen,
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


def materialize_rule_generation_result(
    candidate: RuleCandidate,
    *,
    confidence: float,
    config: RuleGenerationConfig,
) -> RuleGenerationResult:
    return RuleGenerationResult(
        candidate=candidate,
        confidence=confidence,
        rule=materialize_vocab_rule(candidate, confidence=confidence, config=config),
    )


def limit_rule_generation_results(
    results: Sequence[RuleGenerationResult],
    *,
    ranking_mechanism: CandidateRankingMechanism,
    max_definitions_per_target: Optional[int] = None,
    interleave_definition_groups: bool = False,
    max_rules_per_target: Optional[int] = None,
    semantic_demotion_scale: float = 1.0,
) -> list[RuleGenerationResult]:
    return _limit_rule_generation_results(
        results,
        ranking_mechanism=ranking_mechanism,
        max_definitions_per_target=max_definitions_per_target,
        interleave_definition_groups=interleave_definition_groups,
        max_rules_per_target=max_rules_per_target,
        semantic_demotion_scale=semantic_demotion_scale,
    )


def resolve_reverse_hygiene_anchor_allowed_from_values(
    *,
    hit: object,
    rank: Optional[int],
    total: Optional[int],
) -> bool:
    return _resolve_reverse_hygiene_anchor_allowed_from_values(
        hit=hit,
        rank=rank,
        total=total,
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
        variant_penalty = (
            self.variant_penalty_provider(candidate) if self.variant_penalty_provider else 0.0
        )
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


def build_pos_match_provider(
    *,
    exact_match_bonus: float = DEFAULT_POS_EXACT_MATCH_BONUS,
    compatible_match_bonus: float = DEFAULT_POS_COMPATIBLE_MATCH_BONUS,
    compatibility_classes: Optional[Mapping[str, str]] = None,
) -> Callable[[RuleCandidate], float]:
    def _provider(candidate: RuleCandidate) -> float:
        return score_candidate_pos_match(
            candidate,
            exact_match_bonus=exact_match_bonus,
            compatible_match_bonus=compatible_match_bonus,
            compatibility_classes=compatibility_classes,
        )

    return _provider


def build_optional_pos_match_provider(
    config: Optional[PosMatchScoringConfig],
) -> Optional[Callable[[RuleCandidate], float]]:
    resolved = config or PosMatchScoringConfig()
    if not bool(resolved.enabled):
        return None
    return build_pos_match_provider(
        exact_match_bonus=resolved.exact_match_bonus,
        compatible_match_bonus=resolved.compatible_match_bonus,
        compatibility_classes=resolved.compatibility_classes,
    )


def score_candidate_pos_match(
    candidate: RuleCandidate,
    *,
    exact_match_bonus: float = DEFAULT_POS_EXACT_MATCH_BONUS,
    compatible_match_bonus: float = DEFAULT_POS_COMPATIBLE_MATCH_BONUS,
    compatibility_classes: Optional[Mapping[str, str]] = None,
) -> float:
    metadata = candidate.metadata if isinstance(candidate.metadata, Mapping) else {}
    source = extract_candidate_pos_canonical(
        metadata,
        nested_key="source",
        flat_key="source_pos_canonical",
    )
    target = extract_candidate_pos_canonical(
        metadata,
        nested_key="target",
        flat_key="target_pos_canonical",
    )
    if source and target:
        return score_canonical_pos_pair(
            source,
            target,
            exact_match_bonus=exact_match_bonus,
            compatible_match_bonus=compatible_match_bonus,
            compatibility_classes=compatibility_classes,
        )
    dictionary = extract_candidate_pos_canonical(
        metadata,
        nested_key="dictionary",
        flat_key="dictionary_pos_canonical",
    )
    if not dictionary:
        dictionary = extract_candidate_pos_canonical(
            metadata,
            nested_key="dictionary",
            flat_key="dict_entry_pos_canonical",
        )
    if dictionary and target:
        return score_canonical_pos_pair(
            dictionary,
            target,
            exact_match_bonus=exact_match_bonus,
            compatible_match_bonus=compatible_match_bonus,
            compatibility_classes=compatibility_classes,
        )
    return 0.0


def score_canonical_pos_pair(
    left: str,
    right: str,
    *,
    exact_match_bonus: float = DEFAULT_POS_EXACT_MATCH_BONUS,
    compatible_match_bonus: float = DEFAULT_POS_COMPATIBLE_MATCH_BONUS,
    compatibility_classes: Optional[Mapping[str, str]] = None,
) -> float:
    return _score_canonical_pos_pair(
        left,
        right,
        exact_match_bonus=exact_match_bonus,
        compatible_match_bonus=compatible_match_bonus,
        compatibility_classes=compatibility_classes,
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


def _normalize_morphology(value: object) -> Optional[dict[str, object]]:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, object] = {}
    for key, raw in dict(value).items():
        name = str(key or "").strip()
        if not name:
            continue
        normalized[name] = raw
    return normalized or None


def _normalize_pos_metadata(value: object) -> Optional[dict[str, object]]:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, object] = {}
    for key in ("source", "target", "dictionary"):
        component = _normalize_pos_component(value.get(key))
        if component:
            normalized[key] = component
    return normalized or None


def _normalize_rulegen_metadata(value: object) -> Optional[dict[str, object]]:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, object] = {}
    for key in (
        "compiled_target_id",
        "compiled_candidate_id",
        "compiled_definition_bucket_id",
        "compiled_source_dict_id",
        "compiled_source_type_id",
    ):
        raw = value.get(key)
        if isinstance(raw, bool):
            continue
        if isinstance(raw, int):
            normalized[key] = int(raw)
            continue
        if isinstance(raw, str):
            text = raw.strip()
            if not text:
                continue
            try:
                normalized[key] = int(text)
            except ValueError:
                continue
    raw_family_marker_ids = value.get("compiled_family_marker_ids")
    if isinstance(raw_family_marker_ids, Sequence) and not isinstance(
        raw_family_marker_ids, (str, bytes)
    ):
        family_marker_ids: list[int] = []
        for item in raw_family_marker_ids:
            if isinstance(item, bool):
                continue
            if isinstance(item, int):
                family_marker_ids.append(int(item))
                continue
            if isinstance(item, str):
                text = item.strip()
                if not text:
                    continue
                try:
                    family_marker_ids.append(int(text))
                except ValueError:
                    continue
        if family_marker_ids:
            normalized["compiled_family_marker_ids"] = tuple(family_marker_ids)
    return normalized or None


def _normalize_pos_component(value: object) -> Optional[dict[str, object]]:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, object] = {}
    raw = str(value.get("raw") or "").strip()
    if raw:
        normalized["raw"] = raw
    canonical = _normalize_canonical_pos(value.get("canonical"))
    if canonical:
        normalized["canonical"] = canonical
    if "mapped" in value:
        normalized["mapped"] = bool(value.get("mapped"))
    source_profile = str(value.get("source_profile") or "").strip()
    if source_profile:
        normalized["source_profile"] = source_profile
    matched_rule = str(value.get("matched_rule") or "").strip()
    if matched_rule:
        normalized["matched_rule"] = matched_rule
    return normalized or None


def _build_pos_metadata_from_flat(metadata: Mapping[str, object]) -> Optional[dict[str, object]]:
    normalized: dict[str, object] = {}
    source = _build_flat_pos_component(metadata, prefix="source_pos")
    if source:
        normalized["source"] = source
    target = _build_flat_pos_component(metadata, prefix="target_pos")
    if target:
        normalized["target"] = target
    dictionary = _build_flat_pos_component(metadata, prefix="dictionary_pos")
    if not dictionary:
        dictionary = _build_flat_pos_component(metadata, prefix="dict_entry_pos")
    if dictionary:
        normalized["dictionary"] = dictionary
    return normalized or None


def _build_flat_pos_component(
    metadata: Mapping[str, object],
    *,
    prefix: str,
) -> Optional[dict[str, object]]:
    component: dict[str, object] = {}
    raw = str(metadata.get(f"{prefix}_raw") or "").strip()
    if raw:
        component["raw"] = raw
    canonical = _normalize_canonical_pos(metadata.get(f"{prefix}_canonical"))
    if canonical:
        component["canonical"] = canonical
    mapped_key = f"{prefix}_mapped"
    if mapped_key in metadata:
        component["mapped"] = bool(metadata.get(mapped_key))
    source_profile = str(metadata.get(f"{prefix}_source_profile") or "").strip()
    if source_profile:
        component["source_profile"] = source_profile
    matched_rule = str(metadata.get(f"{prefix}_matched_rule") or "").strip()
    if matched_rule:
        component["matched_rule"] = matched_rule
    return component or None


def extract_candidate_pos_canonical(
    metadata: Mapping[str, object],
    *,
    nested_key: str,
    flat_key: str,
) -> str:
    pos = metadata.get("pos")
    if isinstance(pos, Mapping):
        component = pos.get(nested_key)
        if isinstance(component, Mapping):
            canonical = _normalize_canonical_pos(component.get("canonical"))
            if canonical:
                return canonical
    return _normalize_canonical_pos(metadata.get(flat_key))


def _extract_candidate_pos_canonical(
    metadata: Mapping[str, object],
    *,
    nested_key: str,
    flat_key: str,
) -> str:
    return extract_candidate_pos_canonical(
        metadata,
        nested_key=nested_key,
        flat_key=flat_key,
    )


def _score_canonical_pos_pair(
    left: str,
    right: str,
    *,
    exact_match_bonus: float,
    compatible_match_bonus: float,
    compatibility_classes: Optional[Mapping[str, str]],
) -> float:
    if left == right:
        return _clamp(exact_match_bonus)
    classes = compatibility_classes or DEFAULT_POS_COMPATIBILITY_CLASSES
    left_class = str(classes.get(left, "")).strip()
    right_class = str(classes.get(right, "")).strip()
    if left_class and left_class == right_class:
        return _clamp(compatible_match_bonus)
    return 0.0


def _normalize_canonical_pos(value: object) -> str:
    canonical = str(value or "").strip().lower()
    if canonical not in CANONICAL_POS_TAGS:
        return ""
    if canonical == CANONICAL_POS_OTHER:
        return ""
    return canonical


def _normalize_semantic_demotion_scale(value: object) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, float(value))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 1.0
        try:
            return max(0.0, float(text))
        except ValueError:
            return 1.0
    return 1.0


def _clamp(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))
