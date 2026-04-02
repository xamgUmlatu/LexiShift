#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.adapters import RulegenAdapterRequest
from lexishift_core.rulegen.benchmarking import RulegenBenchmarkSummary
from lexishift_core.rulegen.generation import (
    PosMatchScoringConfig,
    RuleScoreWeights,
    RuleScoringConfig,
)
from lexishift_core.rulegen.pairs.en_es import (
    EnEsCompiledBenchmarkEvaluationTables,
    EnEsCompiledSelectedRowTable,
)
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig


def _format_kaikki_policy_family_label(families: Sequence[str]) -> str:
    if not families:
        return "none"
    abbreviations = {
        "math_geometry": "mg",
        "government_law": "gl",
        "hunting_fishing_tools": "hft",
        "register_region": "rr",
        "abbreviation_ellipsis_formof": "aef",
    }
    tokens = [
        abbreviations.get(str(family).strip(), str(family).strip())
        for family in families
        if str(family).strip()
    ]
    return "+".join(tokens) if tokens else "none"


def _format_exact_hit_ambiguity_label(config: SweepConfig) -> str:
    threshold = max(0, int(config.reverse_check_exact_hit_ambiguity_threshold))
    penalty = max(0.0, float(config.reverse_check_exact_hit_ambiguity_penalty))
    if threshold <= 0 or penalty <= 0.0:
        return "off"
    return f"{threshold}:{penalty:.2f}"


def _format_exact_hit_specificity_label(config: SweepConfig) -> str:
    bonus = max(0.0, float(config.reverse_check_exact_hit_specificity_bonus))
    if bonus <= 0.0:
        return "off"
    return f"{bonus:.2f}"


def _format_kaikki_provenance_label(config: SweepConfig) -> str:
    penalty = max(0.0, float(config.kaikki_policy_late_sense_penalty))
    if penalty <= 0.0:
        return "off"
    return f"{penalty:.2f}"


@dataclass(frozen=True)
class SweepConfig:
    max_definitions_per_target: Optional[int]
    max_rules_per_target: Optional[int]
    confidence_threshold: float
    semantic_demotion_scale: float
    include_variants: bool
    pos_scoring_enabled: bool
    pos_exact_match_bonus: float
    pos_compatible_match_bonus: float
    score_weight_dict_priority: float
    score_weight_frequency_weight: float
    score_weight_pos_match: float
    score_weight_variant_penalty: float
    score_weight_phrase_penalty: float
    score_weight_embedding: float
    reverse_check_enabled: bool
    reverse_check_match_bonus: float
    reverse_check_near_bonus: float
    reverse_check_near_rank_max: int
    reverse_check_far_hit_penalty: float
    reverse_check_miss_penalty: float
    reverse_check_exact_hit_ambiguity_threshold: int
    reverse_check_exact_hit_ambiguity_penalty: float
    kaikki_policy_live_demotion: bool
    kaikki_policy_risk_families: tuple[str, ...]
    reverse_check_exact_hit_specificity_bonus: float = 0.0
    kaikki_policy_late_sense_penalty: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "max_definitions_per_target": self.max_definitions_per_target,
            "max_rules_per_target": self.max_rules_per_target,
            "confidence_threshold": self.confidence_threshold,
            "semantic_demotion_scale": self.semantic_demotion_scale,
            "include_variants": self.include_variants,
            "pos_scoring_enabled": self.pos_scoring_enabled,
            "pos_exact_match_bonus": self.pos_exact_match_bonus,
            "pos_compatible_match_bonus": self.pos_compatible_match_bonus,
            "score_weight_dict_priority": self.score_weight_dict_priority,
            "score_weight_frequency_weight": self.score_weight_frequency_weight,
            "score_weight_pos_match": self.score_weight_pos_match,
            "score_weight_variant_penalty": self.score_weight_variant_penalty,
            "score_weight_phrase_penalty": self.score_weight_phrase_penalty,
            "score_weight_embedding": self.score_weight_embedding,
            "reverse_check_enabled": self.reverse_check_enabled,
            "reverse_check_match_bonus": self.reverse_check_match_bonus,
            "reverse_check_near_bonus": self.reverse_check_near_bonus,
            "reverse_check_near_rank_max": self.reverse_check_near_rank_max,
            "reverse_check_far_hit_penalty": self.reverse_check_far_hit_penalty,
            "reverse_check_miss_penalty": self.reverse_check_miss_penalty,
            "reverse_check_exact_hit_ambiguity_threshold": (
                self.reverse_check_exact_hit_ambiguity_threshold
            ),
            "reverse_check_exact_hit_ambiguity_penalty": (
                self.reverse_check_exact_hit_ambiguity_penalty
            ),
            "kaikki_policy_live_demotion": self.kaikki_policy_live_demotion,
            "kaikki_policy_risk_families": list(self.kaikki_policy_risk_families),
            "reverse_check_exact_hit_specificity_bonus": (
                self.reverse_check_exact_hit_specificity_bonus
            ),
            "kaikki_policy_late_sense_penalty": self.kaikki_policy_late_sense_penalty,
        }

    def label(self) -> str:
        def _cap_text(value: Optional[int]) -> str:
            return "none" if value is None else str(value)

        return (
            f"md={_cap_text(self.max_definitions_per_target)} "
            f"mr={_cap_text(self.max_rules_per_target)} "
            f"thr={self.confidence_threshold:.3f} "
            f"sd={self.semantic_demotion_scale:.2f} "
            f"var={'on' if self.include_variants else 'off'} "
            f"pos={'on' if self.pos_scoring_enabled else 'off'} "
            f"rev={'on' if self.reverse_check_enabled else 'off'} "
            f"xamb={_format_exact_hit_ambiguity_label(self)} "
            f"xspec={_format_exact_hit_specificity_label(self)} "
            f"w_pos={self.score_weight_pos_match:.3f} "
            f"kdem={'on' if self.kaikki_policy_live_demotion else 'off'} "
            f"kfam={_format_kaikki_policy_family_label(self.kaikki_policy_risk_families)} "
            f"kprov={_format_kaikki_provenance_label(self)}"
        )

    def scoring(self) -> RuleScoringConfig:
        return RuleScoringConfig(
            weights=RuleScoreWeights(
                dict_priority=self.score_weight_dict_priority,
                frequency_weight=self.score_weight_frequency_weight,
                pos_match=self.score_weight_pos_match,
                variant_penalty=self.score_weight_variant_penalty,
                phrase_penalty=self.score_weight_phrase_penalty,
                embedding_weight=self.score_weight_embedding,
            ),
            pos_match=PosMatchScoringConfig(
                enabled=self.pos_scoring_enabled,
                exact_match_bonus=self.pos_exact_match_bonus,
                compatible_match_bonus=self.pos_compatible_match_bonus,
            ),
        )

    def reverse_check(self) -> ReverseCheckScoringConfig:
        return ReverseCheckScoringConfig(
            enabled=bool(self.reverse_check_enabled),
            match_bonus=float(self.reverse_check_match_bonus),
            near_bonus=float(self.reverse_check_near_bonus),
            near_rank_max=max(0, int(self.reverse_check_near_rank_max)),
            far_hit_penalty=float(self.reverse_check_far_hit_penalty),
            miss_penalty=float(self.reverse_check_miss_penalty),
            exact_hit_ambiguity_threshold=max(
                0,
                int(self.reverse_check_exact_hit_ambiguity_threshold),
            ),
            exact_hit_ambiguity_penalty=float(self.reverse_check_exact_hit_ambiguity_penalty),
            exact_hit_specificity_bonus=float(self.reverse_check_exact_hit_specificity_bonus),
        )


@dataclass(frozen=True)
class SweepRun:
    pair: str
    run_index: int
    config: SweepConfig
    summary: RulegenBenchmarkSummary
    case_results: Sequence[dict[str, object]]

    def to_dict(self, *, include_case_results: bool) -> dict[str, object]:
        payload = {
            "pair": self.pair,
            "run_index": self.run_index,
            "config": self.config.to_dict(),
            "config_label": self.config.label(),
            "summary": self.summary.to_dict(),
        }
        if include_case_results:
            payload["case_results"] = list(self.case_results)
        return payload


@dataclass(frozen=True)
class CompiledBenchmarkCaseRef:
    case_row_id: int
    case_id: str
    target: str
    target_id: Optional[int] = None
    candidate_row_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class CompiledBenchmarkPhraseTable:
    normalized_phrases: tuple[str, ...] = ()
    phrase_ids_by_phrase: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class CompiledBenchmarkCaseTable:
    case_row_ids: tuple[int, ...] = ()
    case_ids: tuple[str, ...] = ()
    targets: tuple[str, ...] = ()
    target_ids: tuple[int, ...] = ()
    candidate_row_id_rows: tuple[tuple[int, ...], ...] = ()
    expected_any_phrase_id_rows: tuple[tuple[int, ...], ...] = ()
    expected_top1_phrase_id_rows: tuple[tuple[int, ...], ...] = ()
    forbidden_top1_phrase_id_rows: tuple[tuple[int, ...], ...] = ()
    forbidden_any_phrase_id_rows: tuple[tuple[int, ...], ...] = ()
    phrase_table: CompiledBenchmarkPhraseTable = field(default_factory=CompiledBenchmarkPhraseTable)


@dataclass(frozen=True)
class CompiledBenchmarkRuleTable:
    targets: tuple[str, ...] = ()
    all_source_rows: tuple[tuple[str, ...], ...] = ()
    source_phrase_id_rows: tuple[tuple[int, ...], ...] = ()
    candidate_row_id_rows: tuple[tuple[int, ...], ...] = ()
    top1_confidences: tuple[Optional[float], ...] = ()
    variant_rule_counts: tuple[int, ...] = ()
    top1_variant_flags: tuple[bool, ...] = ()
    row_id_by_target: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class CompiledBenchmarkCaseResultTable:
    case_row_ids: tuple[int, ...] = ()
    rule_counts: tuple[int, ...] = ()
    top1_confidences: tuple[Optional[float], ...] = ()
    top1_correct_flags: tuple[bool, ...] = ()
    top3_contains_expected_flags: tuple[bool, ...] = ()
    top1_forbidden_flags: tuple[bool, ...] = ()
    forbidden_any_present_flags: tuple[bool, ...] = ()
    variant_rule_counts: tuple[int, ...] = ()
    top1_variant_flags: tuple[bool, ...] = ()


@dataclass(frozen=True)
class PairBenchmarkContext:
    pair: str
    cases: Sequence[object]
    targets: tuple[str, ...]
    jmdict_path: Optional[Path]
    translation_dict_path: Optional[Path]
    reverse_translation_dict_path: Optional[Path]
    resources: Mapping[str, object]
    word_package_snapshot: Mapping[str, object]
    word_packages_by_target: Mapping[str, Mapping[str, object]]
    gloss_records_by_target: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    reverse_gloss_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]] = None
    compiled_pair_context: Optional[object] = None
    compiled_case_refs: Sequence[CompiledBenchmarkCaseRef] = field(default_factory=tuple)
    compiled_case_table: Optional[CompiledBenchmarkCaseTable] = None


@dataclass(frozen=True)
class SweepRunEvaluation:
    run: SweepRun
    phase_timings: Mapping[str, float]


@dataclass(frozen=True)
class PreparedSweepRunInputs:
    request: RulegenAdapterRequest
    compiled_pair_config: Optional[object] = None
    en_es_tables: Optional[EnEsCompiledBenchmarkEvaluationTables] = None
    en_es_selected_row_table: Optional[EnEsCompiledSelectedRowTable] = None


@dataclass
class _TimingStat:
    total_seconds: float = 0.0
    count: int = 0

    def add(self, duration_seconds: float) -> None:
        self.total_seconds += max(0.0, float(duration_seconds))
        self.count += 1

    def to_dict(self) -> dict[str, object]:
        avg_seconds = self.total_seconds / self.count if self.count else 0.0
        return {
            "total_seconds": float(self.total_seconds),
            "count": int(self.count),
            "avg_seconds": float(avg_seconds),
        }


@dataclass
class BenchmarkTimingCollector:
    phases: dict[str, _TimingStat] = field(default_factory=dict)
    pairs: dict[str, dict[str, _TimingStat]] = field(default_factory=dict)

    def add(self, phase: str, duration_seconds: float, *, pair: Optional[str] = None) -> None:
        phase_name = str(phase or "").strip()
        if not phase_name:
            return
        self.phases.setdefault(phase_name, _TimingStat()).add(duration_seconds)
        pair_name = str(pair or "").strip()
        if not pair_name:
            return
        self.pairs.setdefault(pair_name, {}).setdefault(phase_name, _TimingStat()).add(
            duration_seconds
        )

    def to_dict(self, *, wall_clock_seconds: Optional[float] = None) -> dict[str, object]:
        total_recorded_seconds = sum(stat.total_seconds for stat in self.phases.values())
        payload: dict[str, object] = {
            "total_recorded_seconds": float(total_recorded_seconds),
            "phases": {phase: stat.to_dict() for phase, stat in sorted(self.phases.items())},
            "pairs": {
                pair: {phase: stat.to_dict() for phase, stat in sorted(pair_stats.items())}
                for pair, pair_stats in sorted(self.pairs.items())
            },
        }
        if wall_clock_seconds is not None:
            payload["wall_clock_seconds"] = float(max(0.0, wall_clock_seconds))
        return payload
