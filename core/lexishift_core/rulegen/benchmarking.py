from __future__ import annotations

from collections.abc import Iterable as IterableCollection
from dataclasses import dataclass, field
from statistics import mean
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.replacement.core import VocabRule


def normalize_benchmark_phrase(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return " ".join(text.split())


def _normalize_phrase_list(values: Iterable[object]) -> tuple[str, ...]:
    normalized = [normalize_benchmark_phrase(value) for value in values]
    return tuple(item for item in normalized if item)


def _coerce_phrase_values(value: object) -> Iterable[object]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    if isinstance(value, IterableCollection):
        return value
    return ()


@dataclass(frozen=True)
class RulegenBenchmarkCase:
    case_id: str
    pair: str
    target: str
    expected_any: Sequence[str] = field(default_factory=tuple)
    expected_top1_any: Sequence[str] = field(default_factory=tuple)
    forbidden_top1: Sequence[str] = field(default_factory=tuple)
    forbidden_any: Sequence[str] = field(default_factory=tuple)
    target_reading: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object],
        *,
        default_pair: str = "",
        index: int = 0,
    ) -> "RulegenBenchmarkCase":
        pair = str(payload.get("pair") or default_pair).strip().lower()
        target = str(payload.get("target") or "").strip()
        case_id = str(payload.get("case_id") or payload.get("id") or "").strip()
        if not case_id:
            case_id = f"{pair}:{target}:{index}"
        return cls(
            case_id=case_id,
            pair=pair,
            target=target,
            expected_any=_normalize_phrase_list(
                _coerce_phrase_values(payload.get("expected_any", ()) or ())
            ),
            expected_top1_any=_normalize_phrase_list(
                _coerce_phrase_values(payload.get("expected_top1_any", ()) or ())
            ),
            forbidden_top1=_normalize_phrase_list(
                _coerce_phrase_values(payload.get("forbidden_top1", ()) or ())
            ),
            forbidden_any=_normalize_phrase_list(
                _coerce_phrase_values(payload.get("forbidden_any", ()) or ())
            ),
            target_reading=str(payload.get("target_reading") or "").strip() or None,
            notes=str(payload.get("notes") or "").strip() or None,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "pair": self.pair,
            "target": self.target,
            "expected_any": list(self.expected_any),
            "expected_top1_any": list(self.expected_top1_any),
            "forbidden_top1": list(self.forbidden_top1),
            "forbidden_any": list(self.forbidden_any),
            "target_reading": self.target_reading,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class RulegenBenchmarkCaseResult:
    case_id: str
    pair: str
    target: str
    rule_count: int
    top1_source: Optional[str]
    top3_sources: Sequence[str]
    all_sources: Sequence[str]
    top1_confidence: Optional[float]
    top1_correct: bool
    top3_contains_expected: bool
    top1_forbidden: bool
    forbidden_any_present: bool
    variant_rule_count: int
    top1_is_variant: bool
    expected_matches: Sequence[str] = field(default_factory=tuple)
    forbidden_matches: Sequence[str] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "pair": self.pair,
            "target": self.target,
            "rule_count": int(self.rule_count),
            "top1_source": self.top1_source,
            "top3_sources": list(self.top3_sources),
            "all_sources": list(self.all_sources),
            "top1_confidence": self.top1_confidence,
            "top1_correct": bool(self.top1_correct),
            "top3_contains_expected": bool(self.top3_contains_expected),
            "top1_forbidden": bool(self.top1_forbidden),
            "forbidden_any_present": bool(self.forbidden_any_present),
            "variant_rule_count": int(self.variant_rule_count),
            "top1_is_variant": bool(self.top1_is_variant),
            "expected_matches": list(self.expected_matches),
            "forbidden_matches": list(self.forbidden_matches),
        }


@dataclass(frozen=True)
class RulegenBenchmarkObjectiveWeights:
    top1_accuracy: float = 100.0
    top3_recall: float = 60.0
    forbidden_top1_rate: float = 120.0
    forbidden_any_rate: float = 80.0
    avg_rules_per_target: float = 6.0
    variant_top1_rate: float = 10.0


@dataclass(frozen=True)
class RulegenBenchmarkSummary:
    pair: str
    case_count: int
    top1_correct_count: int
    top3_contains_expected_count: int
    forbidden_top1_count: int
    forbidden_any_count: int
    avg_rules_per_target: float
    avg_top1_confidence: Optional[float]
    variant_rule_count: int
    total_rule_count: int
    variant_top1_count: int
    top1_accuracy: float
    top3_recall: float
    forbidden_top1_rate: float
    forbidden_any_rate: float
    variant_rule_rate: float
    variant_top1_rate: float
    objective_score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "pair": self.pair,
            "case_count": int(self.case_count),
            "top1_correct_count": int(self.top1_correct_count),
            "top3_contains_expected_count": int(self.top3_contains_expected_count),
            "forbidden_top1_count": int(self.forbidden_top1_count),
            "forbidden_any_count": int(self.forbidden_any_count),
            "avg_rules_per_target": float(self.avg_rules_per_target),
            "avg_top1_confidence": self.avg_top1_confidence,
            "variant_rule_count": int(self.variant_rule_count),
            "total_rule_count": int(self.total_rule_count),
            "variant_top1_count": int(self.variant_top1_count),
            "top1_accuracy": float(self.top1_accuracy),
            "top3_recall": float(self.top3_recall),
            "forbidden_top1_rate": float(self.forbidden_top1_rate),
            "forbidden_any_rate": float(self.forbidden_any_rate),
            "variant_rule_rate": float(self.variant_rule_rate),
            "variant_top1_rate": float(self.variant_top1_rate),
            "objective_score": float(self.objective_score),
        }


def evaluate_benchmark_case(
    case: RulegenBenchmarkCase,
    rules: Sequence[VocabRule],
) -> RulegenBenchmarkCaseResult:
    sources = [normalize_benchmark_phrase(rule.source_phrase) for rule in rules]
    sources = [source for source in sources if source]
    top3_sources = tuple(sources[:3])
    top1_source = sources[0] if sources else None
    top1_confidence = _extract_rule_confidence(rules[0]) if rules else None
    variant_rule_count = sum(1 for rule in rules if _is_variant_rule(rule))
    top1_is_variant = bool(rules and _is_variant_rule(rules[0]))

    expected_any = {normalize_benchmark_phrase(item) for item in case.expected_any}
    expected_any.discard("")
    expected_top1 = (
        {normalize_benchmark_phrase(item) for item in case.expected_top1_any}
        if case.expected_top1_any
        else set(expected_any)
    )
    expected_top1.discard("")
    forbidden_top1 = {normalize_benchmark_phrase(item) for item in case.forbidden_top1}
    forbidden_top1.discard("")
    forbidden_any = {normalize_benchmark_phrase(item) for item in case.forbidden_any}
    forbidden_any.discard("")

    expected_matches = tuple(source for source in sources if source in expected_any)
    forbidden_matches = tuple(source for source in sources if source in forbidden_any)

    top1_correct = bool(top1_source and expected_top1 and top1_source in expected_top1)
    top3_contains_expected = bool(
        expected_any and any(source in expected_any for source in top3_sources)
    )
    top1_forbidden = bool(top1_source and forbidden_top1 and top1_source in forbidden_top1)
    forbidden_any_present = bool(forbidden_matches)

    return RulegenBenchmarkCaseResult(
        case_id=case.case_id,
        pair=case.pair,
        target=case.target,
        rule_count=len(rules),
        top1_source=top1_source,
        top3_sources=top3_sources,
        all_sources=tuple(sources),
        top1_confidence=top1_confidence,
        top1_correct=top1_correct,
        top3_contains_expected=top3_contains_expected,
        top1_forbidden=top1_forbidden,
        forbidden_any_present=forbidden_any_present,
        variant_rule_count=variant_rule_count,
        top1_is_variant=top1_is_variant,
        expected_matches=expected_matches,
        forbidden_matches=forbidden_matches,
    )


def summarize_benchmark_results(
    *,
    pair: str,
    case_results: Sequence[RulegenBenchmarkCaseResult],
    objective_weights: Optional[RulegenBenchmarkObjectiveWeights] = None,
) -> RulegenBenchmarkSummary:
    weights = objective_weights or RulegenBenchmarkObjectiveWeights()
    case_count = len(case_results)
    top1_correct_count = sum(1 for result in case_results if result.top1_correct)
    top3_contains_expected_count = sum(
        1 for result in case_results if result.top3_contains_expected
    )
    forbidden_top1_count = sum(1 for result in case_results if result.top1_forbidden)
    forbidden_any_count = sum(1 for result in case_results if result.forbidden_any_present)
    variant_top1_count = sum(1 for result in case_results if result.top1_is_variant)

    total_rule_count = sum(result.rule_count for result in case_results)
    variant_rule_count = sum(result.variant_rule_count for result in case_results)
    avg_rules_per_target = (total_rule_count / case_count) if case_count else 0.0
    top1_confidences = [
        result.top1_confidence for result in case_results if result.top1_confidence is not None
    ]
    avg_top1_confidence = float(mean(top1_confidences)) if top1_confidences else None

    top1_accuracy = (top1_correct_count / case_count) if case_count else 0.0
    top3_recall = (top3_contains_expected_count / case_count) if case_count else 0.0
    forbidden_top1_rate = (forbidden_top1_count / case_count) if case_count else 0.0
    forbidden_any_rate = (forbidden_any_count / case_count) if case_count else 0.0
    variant_rule_rate = (variant_rule_count / total_rule_count) if total_rule_count else 0.0
    variant_top1_rate = (variant_top1_count / case_count) if case_count else 0.0

    objective_score = (
        (top1_accuracy * weights.top1_accuracy)
        + (top3_recall * weights.top3_recall)
        - (forbidden_top1_rate * weights.forbidden_top1_rate)
        - (forbidden_any_rate * weights.forbidden_any_rate)
        - (avg_rules_per_target * weights.avg_rules_per_target)
        - (variant_top1_rate * weights.variant_top1_rate)
    )

    return RulegenBenchmarkSummary(
        pair=pair,
        case_count=case_count,
        top1_correct_count=top1_correct_count,
        top3_contains_expected_count=top3_contains_expected_count,
        forbidden_top1_count=forbidden_top1_count,
        forbidden_any_count=forbidden_any_count,
        avg_rules_per_target=avg_rules_per_target,
        avg_top1_confidence=avg_top1_confidence,
        variant_rule_count=variant_rule_count,
        total_rule_count=total_rule_count,
        variant_top1_count=variant_top1_count,
        top1_accuracy=top1_accuracy,
        top3_recall=top3_recall,
        forbidden_top1_rate=forbidden_top1_rate,
        forbidden_any_rate=forbidden_any_rate,
        variant_rule_rate=variant_rule_rate,
        variant_top1_rate=variant_top1_rate,
        objective_score=objective_score,
    )


def _extract_rule_confidence(rule: VocabRule) -> Optional[float]:
    metadata = getattr(rule, "metadata", None)
    if metadata is None:
        return None
    confidence = getattr(metadata, "confidence", None)
    if confidence is None:
        return None
    return float(confidence)


def _is_variant_rule(rule: VocabRule) -> bool:
    metadata = getattr(rule, "metadata", None)
    if metadata is None:
        return False
    morphology = getattr(metadata, "morphology", None)
    if not isinstance(morphology, Mapping):
        return False
    source_form = normalize_benchmark_phrase(morphology.get("source_form"))
    if source_form:
        return True
    target_surface = normalize_benchmark_phrase(morphology.get("target_surface"))
    target_lemma = normalize_benchmark_phrase(morphology.get("target_lemma"))
    return bool(target_surface and target_lemma and target_surface != target_lemma)
