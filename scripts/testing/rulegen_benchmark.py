#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import itertools
import json
import multiprocessing
from pathlib import Path
import sys
from time import perf_counter
from typing import Mapping, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_freedict_reverse_path,
    resolve_pair_capability,
)
from lexishift_core.helper.pair_resources import resolve_pair_resources  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.lexicon.word_package import (  # noqa: E402
    build_word_package,
    normalize_word_package,
)
from lexishift_core.resources.dict_loaders import (  # noqa: E402
    TranslationGlossRecord,
    load_translation_gloss_base_forms,
    load_translation_gloss_records_ordered,
    load_translation_headwords,
)
from lexishift_core.resources.path_cache import load_or_compute_path_json_value  # noqa: E402
from lexishift_core.replacement.core import VocabRule  # noqa: E402
from lexishift_core.rulegen.adapters import (  # noqa: E402
    RulegenAdapterRequest,
    build_en_es_rulegen_config,
    run_rules_with_adapter,
)
from lexishift_core.rulegen.benchmarking import (  # noqa: E402
    RulegenBenchmarkCase,
    RulegenBenchmarkObjectiveWeights,
    RulegenBenchmarkCaseResult,
    RulegenBenchmarkSummary,
    _extract_rule_confidence,
    _is_variant_rule,
    evaluate_benchmark_case,
    normalize_benchmark_phrase,
    summarize_benchmark_results,
)
from lexishift_core.rulegen.generation import (  # noqa: E402
    PosMatchScoringConfig,
    RuleCandidate,
    RuleScoreWeights,
    RuleScoringConfig,
)
from lexishift_core.rulegen.pairs.en_es import (  # noqa: E402
    EnEsCompiledResources,
    EnEsCompiledSelectedRowTable,
    build_en_es_compiled_selected_row_table,
    build_en_es_compiled_resources,
)
from lexishift_core.rulegen.pairs.en_es_support import (  # noqa: E402
    collect_sanitized_gloss_records,
    normalize_reverse_token_with_pos,
)
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig  # noqa: E402
from lexishift_core.rulegen.utils import (  # noqa: E402
    BasicStringNormalizer,
    LeadingEnglishInfinitiveNormalizer,
    PairedInflectionVariantExpander,
    sanitize_dictionary_gloss,
)
from lexishift_core.srs import SrsStore, load_srs_store  # noqa: E402

from rulegen_benchmark_presets import (  # noqa: E402
    BenchmarkPreset,
    format_benchmark_presets_listing,
    load_benchmark_presets,
)


DEFAULT_PRESET_PATH = PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_presets.json"


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
    cases: Sequence[RulegenBenchmarkCase]
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


_WORKER_CONTEXT: Optional[PairBenchmarkContext] = None
_WORKER_OBJECTIVE_WEIGHTS: Optional[RulegenBenchmarkObjectiveWeights] = None
_WORKER_MATERIALIZE_CASE_RESULTS = True


def _build_pair_report_payload(
    *,
    case_count: int,
    runs: Sequence[SweepRun],
    resources: Mapping[str, object],
    word_package_snapshot: Mapping[str, object],
    include_case_results: bool,
) -> dict[str, object]:
    return {
        "case_count": int(case_count),
        "run_count": len(runs),
        "resources": dict(resources),
        "word_package_snapshot": dict(word_package_snapshot),
        "best_run": runs[0].to_dict(include_case_results=True) if runs else None,
        "runs": [run.to_dict(include_case_results=include_case_results) for run in runs],
    }


def _load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return dict(payload)


def _resolve_path_from_report_payload(value: object, *, project_root: Path) -> Path:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Expected non-empty path in benchmark report payload.")
    path = Path(text)
    if not path.is_absolute():
        path = (project_root / path).resolve()
    return path


def _summary_from_payload(payload: Mapping[str, object]) -> RulegenBenchmarkSummary:
    return RulegenBenchmarkSummary(
        pair=str(payload.get("pair") or "").strip(),
        case_count=int(payload.get("case_count") or 0),
        top1_correct_count=int(payload.get("top1_correct_count") or 0),
        top3_contains_expected_count=int(payload.get("top3_contains_expected_count") or 0),
        forbidden_top1_count=int(payload.get("forbidden_top1_count") or 0),
        forbidden_any_count=int(payload.get("forbidden_any_count") or 0),
        avg_rules_per_target=float(payload.get("avg_rules_per_target") or 0.0),
        avg_top1_confidence=(
            float(payload["avg_top1_confidence"])
            if payload.get("avg_top1_confidence") is not None
            else None
        ),
        variant_rule_count=int(payload.get("variant_rule_count") or 0),
        total_rule_count=int(payload.get("total_rule_count") or 0),
        variant_top1_count=int(payload.get("variant_top1_count") or 0),
        top1_accuracy=float(payload.get("top1_accuracy") or 0.0),
        top3_recall=float(payload.get("top3_recall") or 0.0),
        forbidden_top1_rate=float(payload.get("forbidden_top1_rate") or 0.0),
        forbidden_any_rate=float(payload.get("forbidden_any_rate") or 0.0),
        variant_rule_rate=float(payload.get("variant_rule_rate") or 0.0),
        variant_top1_rate=float(payload.get("variant_top1_rate") or 0.0),
        objective_score=float(payload.get("objective_score") or 0.0),
    )


def _config_from_payload(payload: Mapping[str, object]) -> SweepConfig:
    families = payload.get("kaikki_policy_risk_families") or ()
    if isinstance(families, Sequence) and not isinstance(families, (str, bytes)):
        normalized_families = tuple(
            str(item or "").strip() for item in families if str(item or "").strip()
        )
    else:
        normalized_families = ()
    return SweepConfig(
        max_definitions_per_target=(
            int(payload["max_definitions_per_target"])
            if payload.get("max_definitions_per_target") is not None
            else None
        ),
        max_rules_per_target=(
            int(payload["max_rules_per_target"])
            if payload.get("max_rules_per_target") is not None
            else None
        ),
        confidence_threshold=float(payload.get("confidence_threshold") or 0.0),
        semantic_demotion_scale=float(payload.get("semantic_demotion_scale") or 0.0),
        include_variants=bool(payload.get("include_variants", False)),
        pos_scoring_enabled=bool(payload.get("pos_scoring_enabled", False)),
        pos_exact_match_bonus=float(payload.get("pos_exact_match_bonus") or 0.0),
        pos_compatible_match_bonus=float(payload.get("pos_compatible_match_bonus") or 0.0),
        score_weight_dict_priority=float(payload.get("score_weight_dict_priority") or 0.0),
        score_weight_frequency_weight=float(payload.get("score_weight_frequency_weight") or 0.0),
        score_weight_pos_match=float(payload.get("score_weight_pos_match") or 0.0),
        score_weight_variant_penalty=float(payload.get("score_weight_variant_penalty") or 0.0),
        score_weight_phrase_penalty=float(payload.get("score_weight_phrase_penalty") or 0.0),
        score_weight_embedding=float(payload.get("score_weight_embedding") or 0.0),
        reverse_check_enabled=bool(payload.get("reverse_check_enabled", False)),
        reverse_check_match_bonus=float(payload.get("reverse_check_match_bonus") or 0.0),
        reverse_check_near_bonus=float(payload.get("reverse_check_near_bonus") or 0.0),
        reverse_check_near_rank_max=int(payload.get("reverse_check_near_rank_max") or 0),
        reverse_check_far_hit_penalty=float(payload.get("reverse_check_far_hit_penalty") or 0.0),
        reverse_check_miss_penalty=float(payload.get("reverse_check_miss_penalty") or 0.0),
        reverse_check_exact_hit_ambiguity_threshold=int(
            payload.get("reverse_check_exact_hit_ambiguity_threshold") or 0
        ),
        reverse_check_exact_hit_ambiguity_penalty=float(
            payload.get("reverse_check_exact_hit_ambiguity_penalty") or 0.0
        ),
        kaikki_policy_live_demotion=bool(payload.get("kaikki_policy_live_demotion", False)),
        kaikki_policy_risk_families=normalized_families,
        reverse_check_exact_hit_specificity_bonus=float(
            payload.get("reverse_check_exact_hit_specificity_bonus") or 0.0
        ),
        kaikki_policy_late_sense_penalty=float(
            payload.get("kaikki_policy_late_sense_penalty") or 0.0
        ),
    )


def _run_from_payload(
    payload: Mapping[str, object],
    *,
    case_results_override: Optional[Sequence[Mapping[str, object]]] = None,
) -> SweepRun:
    raw_config = payload.get("config")
    if not isinstance(raw_config, Mapping):
        raise ValueError("Benchmark run payload is missing `config` object.")
    raw_summary = payload.get("summary")
    if not isinstance(raw_summary, Mapping):
        raise ValueError("Benchmark run payload is missing `summary` object.")
    raw_case_results = payload.get("case_results")
    case_results: tuple[dict[str, object], ...] = ()
    if case_results_override is not None:
        case_results = tuple(dict(item) for item in case_results_override)
    elif isinstance(raw_case_results, Sequence) and not isinstance(raw_case_results, (str, bytes)):
        case_results = tuple(dict(item) for item in raw_case_results if isinstance(item, Mapping))
    return SweepRun(
        pair=str(payload.get("pair") or "").strip(),
        run_index=int(payload.get("run_index") or 0),
        config=_config_from_payload(raw_config),
        summary=_summary_from_payload(raw_summary),
        case_results=case_results,
    )


def _load_pair_runs_from_report_payload(
    report_payload: Mapping[str, object],
) -> dict[str, list[SweepRun]]:
    raw_pairs = report_payload.get("pairs")
    if not isinstance(raw_pairs, Mapping):
        raise ValueError("Benchmark report payload is missing `pairs` object.")
    pair_runs: dict[str, list[SweepRun]] = {}
    for raw_pair, raw_pair_payload in raw_pairs.items():
        pair = str(raw_pair or "").strip()
        if not pair or not isinstance(raw_pair_payload, Mapping):
            continue
        best_run_payload = raw_pair_payload.get("best_run")
        best_case_results: Optional[tuple[dict[str, object], ...]] = None
        best_run_index: Optional[int] = None
        if isinstance(best_run_payload, Mapping):
            best_run_index = int(best_run_payload.get("run_index") or 0)
            raw_case_results = best_run_payload.get("case_results")
            if isinstance(raw_case_results, Sequence) and not isinstance(
                raw_case_results, (str, bytes)
            ):
                best_case_results = tuple(
                    dict(item) for item in raw_case_results if isinstance(item, Mapping)
                )
        runs: list[SweepRun] = []
        raw_runs = raw_pair_payload.get("runs")
        if isinstance(raw_runs, Sequence) and not isinstance(raw_runs, (str, bytes)):
            for raw_run in raw_runs:
                if not isinstance(raw_run, Mapping):
                    continue
                run_index = int(raw_run.get("run_index") or 0)
                case_results_override = (
                    best_case_results
                    if best_case_results is not None and best_run_index == run_index
                    else None
                )
                runs.append(
                    _run_from_payload(
                        raw_run,
                        case_results_override=case_results_override,
                    )
                )
        if not runs and isinstance(best_run_payload, Mapping):
            runs.append(
                _run_from_payload(
                    best_run_payload,
                    case_results_override=best_case_results,
                )
            )
        runs.sort(key=_run_sort_key)
        pair_runs[pair] = runs
    return pair_runs


def _load_html_report_renderer():
    module_name = "rulegen_benchmark_html"
    if __package__:
        module_name = f"{__package__}.rulegen_benchmark_html"
    module = __import__(module_name, fromlist=["render_html_report"])
    return module.render_html_report


def _parse_csv_strings(text: str) -> list[str]:
    return [item.strip() for item in str(text or "").split(",") if item.strip()]


def _parse_csv_floats(text: str, *, name: str) -> list[float]:
    values = _parse_csv_strings(text)
    if not values:
        raise ValueError(f"{name}: expected at least one value.")
    parsed: list[float] = []
    for item in values:
        parsed.append(float(item))
    return parsed


def _parse_csv_ints(text: str, *, name: str, min_value: Optional[int] = None) -> list[int]:
    values = _parse_csv_strings(text)
    if not values:
        raise ValueError(f"{name}: expected at least one value.")
    parsed: list[int] = []
    for item in values:
        value = int(item)
        if min_value is not None:
            value = max(int(min_value), value)
        parsed.append(value)
    return parsed


def _parse_csv_optional_ints(
    text: str,
    *,
    name: str,
    zero_as_none: bool,
) -> list[Optional[int]]:
    values = _parse_csv_strings(text)
    if not values:
        raise ValueError(f"{name}: expected at least one value.")
    parsed: list[Optional[int]] = []
    for item in values:
        normalized = item.lower()
        if normalized in {"none", "null", "off"}:
            parsed.append(None)
            continue
        value = int(item)
        if zero_as_none and value <= 0:
            parsed.append(None)
        else:
            parsed.append(max(1, value))
    return parsed


def _parse_csv_bools(text: str, *, name: str) -> list[bool]:
    values = _parse_csv_strings(text)
    if not values:
        raise ValueError(f"{name}: expected at least one value.")
    parsed: list[bool] = []
    for item in values:
        normalized = item.lower()
        if normalized in {"1", "true", "on", "yes"}:
            parsed.append(True)
            continue
        if normalized in {"0", "false", "off", "no"}:
            parsed.append(False)
            continue
        raise ValueError(f"{name}: unsupported boolean token '{item}'.")
    return parsed


def _parse_family_set_specs(text: str, *, name: str) -> list[tuple[str, ...]]:
    raw_specs = [item.strip() for item in str(text or "").split(";") if item.strip()]
    if not raw_specs:
        raise ValueError(f"{name}: expected at least one family set.")
    parsed: list[tuple[str, ...]] = []
    for spec in raw_specs:
        lowered = spec.lower()
        if lowered in {"none", "off", "null"}:
            parsed.append(())
            continue
        families = [item.strip() for item in spec.replace(",", "+").split("+") if item.strip()]
        if not families:
            raise ValueError(f"{name}: invalid family set '{spec}'.")
        parsed.append(tuple(dict.fromkeys(families)))
    return parsed


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


def _load_dataset_cases(
    path: Path,
    *,
    pair_filter: Optional[set[str]],
) -> tuple[dict[str, object], dict[str, list[RulegenBenchmarkCase]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Dataset payload must be an object: {path}")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, Sequence):
        raise ValueError(f"Dataset is missing `cases` list: {path}")

    by_pair: dict[str, list[RulegenBenchmarkCase]] = {}
    for index, raw_case in enumerate(raw_cases):
        if not isinstance(raw_case, Mapping):
            continue
        case = RulegenBenchmarkCase.from_mapping(raw_case, index=index)
        if not case.pair or not case.target:
            continue
        if pair_filter and case.pair not in pair_filter:
            continue
        by_pair.setdefault(case.pair, []).append(case)
    return dict(payload), by_pair


def _load_store(paths, *, profile_id: str) -> SrsStore:
    store_path = paths.srs_store_path_for(profile_id)
    if not store_path.exists():
        return SrsStore()
    return load_srs_store(store_path)


def _build_store_word_packages(
    *,
    store: SrsStore,
    pair: str,
    targets: set[str],
) -> dict[str, Mapping[str, object]]:
    package_map: dict[str, Mapping[str, object]] = {}
    for item in store.items:
        if item.language_pair != pair:
            continue
        lemma = str(item.lemma or "").strip()
        if lemma not in targets:
            continue
        if not isinstance(item.word_package, Mapping):
            continue
        package_map[lemma] = item.word_package
    return package_map


def _build_word_package_snapshot(
    *,
    targets: Sequence[str],
    word_packages_by_target: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    snapshot: dict[str, object] = {}
    normalized_targets = sorted(
        {str(target or "").strip() for target in targets if str(target or "").strip()}
    )
    for target in normalized_targets:
        normalized_package = normalize_word_package(word_packages_by_target.get(target))
        snapshot[target] = dict(normalized_package) if normalized_package is not None else None
    return snapshot


def _load_frozen_word_package_snapshots(path: Path) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_pairs = payload
    if isinstance(payload, Mapping) and isinstance(payload.get("pairs"), Mapping):
        raw_pairs = payload.get("pairs")
        if isinstance(raw_pairs, Mapping):
            sample_value = next(iter(raw_pairs.values()), None)
            if isinstance(sample_value, Mapping) and "word_package_snapshot" in sample_value:
                raw_pairs = {
                    pair: value.get("word_package_snapshot")
                    for pair, value in raw_pairs.items()
                    if isinstance(value, Mapping)
                }
    if not isinstance(raw_pairs, Mapping):
        raise ValueError(f"Frozen word-package snapshot payload must be an object: {path}")
    frozen: dict[str, dict[str, object]] = {}
    for raw_pair, raw_snapshot in raw_pairs.items():
        pair = str(raw_pair or "").strip()
        if not pair:
            continue
        if not isinstance(raw_snapshot, Mapping):
            continue
        pair_snapshot: dict[str, object] = {}
        for raw_target, raw_package in raw_snapshot.items():
            target = str(raw_target or "").strip()
            if not target:
                continue
            if raw_package is None:
                pair_snapshot[target] = None
                continue
            if not isinstance(raw_package, Mapping):
                raise ValueError(
                    f"Frozen word-package snapshot for pair `{pair}` target `{target}` "
                    f"must be an object or null: {path}"
                )
            normalized_package = normalize_word_package(raw_package)
            pair_snapshot[target] = (
                dict(normalized_package) if normalized_package is not None else None
            )
        frozen[pair] = pair_snapshot
    return frozen


def _apply_case_word_package_overrides(
    *,
    package_map: dict[str, Mapping[str, object]],
    pair: str,
    cases: Sequence[RulegenBenchmarkCase],
) -> None:
    for case in cases:
        if case.target in package_map:
            continue
        if not case.target_reading:
            continue
        package = build_word_package(
            language_pair=pair,
            surface=case.target,
            reading=case.target_reading,
            source_provider="rulegen_benchmark",
        )
        if package is None:
            continue
        package_map[case.target] = package


def _resolve_pair_resources_for_benchmark(
    *,
    paths,
    pair: str,
    jmdict_override: Optional[Path],
    freedict_override: Optional[Path],
    freedict_reverse_override: Optional[Path],
) -> tuple[Optional[Path], Optional[Path], Optional[Path]]:
    jmdict_path, freedict_path, _ = resolve_pair_resources(
        paths,
        pair=pair,
        jmdict_path=jmdict_override,
        freedict_de_en_path=freedict_override,
        set_source_db=None,
    )
    reverse_freedict_path = freedict_reverse_override
    if reverse_freedict_path is None:
        reverse_freedict_path = default_freedict_reverse_path(
            pair,
            language_packs_dir=paths.language_packs_dir,
        )
    capability = resolve_pair_capability(pair)
    if capability.requires_jmdict_for_rulegen:
        if jmdict_path is None or not jmdict_path.exists():
            raise FileNotFoundError(f"JMDict path not found for pair {pair}: {jmdict_path}")
    if capability.requires_freedict_de_en_for_rulegen:
        if freedict_path is None or not freedict_path.exists():
            raise FileNotFoundError(
                f"Translation dictionary path not found for pair {pair}: {freedict_path}"
            )
    if pair in {"en-es", "es-en"} and reverse_freedict_path is not None:
        if not reverse_freedict_path.exists():
            raise FileNotFoundError(
                f"Reverse translation dictionary path not found for pair {pair}: "
                f"{reverse_freedict_path}"
            )
    return jmdict_path, freedict_path, reverse_freedict_path


def _translation_target_lang_for_pair(pair: str) -> Optional[str]:
    normalized = str(pair or "").strip().lower()
    return {
        "en-de": "en",
        "en-es": "en",
        "es-en": "es",
    }.get(normalized)


def _reverse_translation_target_lang_for_pair(pair: str) -> Optional[str]:
    normalized = str(pair or "").strip().lower()
    return {
        "en-es": "es",
        "es-en": "en",
    }.get(normalized)


def _load_translation_gloss_records(
    path: Optional[Path],
    *,
    target_lang: Optional[str],
    headwords: Optional[Sequence[str]] = None,
) -> Optional[dict[str, list[TranslationGlossRecord]]]:
    if path is None or target_lang is None:
        return None
    if not path.exists():
        return None
    return load_translation_gloss_records_ordered(
        path,
        target_lang=target_lang,
        headwords=headwords,
    )


def _preload_pair_gloss_records(
    *,
    pair: str,
    translation_dict_path: Optional[Path],
    reverse_translation_dict_path: Optional[Path],
    targets: Sequence[str] = (),
) -> tuple[
    Optional[dict[str, list[TranslationGlossRecord]]],
    Optional[dict[str, list[TranslationGlossRecord]]],
]:
    forward_records = _load_translation_gloss_records(
        translation_dict_path,
        target_lang=_translation_target_lang_for_pair(pair),
        headwords=targets,
    )
    reverse_headwords = _build_reverse_preload_headwords(
        pair=pair,
        forward_records_by_target=forward_records,
    )
    reverse_headwords = _expand_reverse_preload_headwords(
        pair=pair,
        reverse_translation_dict_path=reverse_translation_dict_path,
        reverse_headwords=reverse_headwords,
    )
    return (
        forward_records,
        _load_translation_gloss_records(
            reverse_translation_dict_path,
            target_lang=_reverse_translation_target_lang_for_pair(pair),
            headwords=reverse_headwords,
        ),
    )


def _build_reverse_preload_headwords(
    *,
    pair: str,
    forward_records_by_target: Optional[Mapping[str, Sequence[TranslationGlossRecord]]],
) -> Optional[tuple[str, ...]]:
    normalized_pair = str(pair or "").strip().lower()
    if normalized_pair != "en-es" or not forward_records_by_target:
        return None
    normalizers = (BasicStringNormalizer(), LeadingEnglishInfinitiveNormalizer())
    expander = PairedInflectionVariantExpander(target_surface_resolver=None)
    headwords: set[str] = set()
    for raw_records in forward_records_by_target.values():
        for record in collect_sanitized_gloss_records(raw_records):
            raw_translation = str(record.translation or "").strip()
            if not raw_translation:
                continue
            sanitized = sanitize_dictionary_gloss(raw_translation).lower()
            if sanitized:
                headwords.add(sanitized)
            normalized_reverse = normalize_reverse_token_with_pos(
                raw_translation,
                pos_raw=record.pos_raw,
            )
            if normalized_reverse:
                headwords.add(normalized_reverse)
            candidate = RuleCandidate(
                source_phrase=raw_translation,
                replacement="",
                language_pair="en-es",
                source_dict="benchmark-preload",
                metadata={},
            )
            normalized_candidate = candidate
            for normalizer in normalizers:
                normalized_candidate = normalizer.normalize(normalized_candidate)
            normalized_phrase = str(normalized_candidate.source_phrase or "").strip().lower()
            if normalized_phrase:
                headwords.add(normalized_phrase)
                if all(ord(ch) < 128 for ch in normalized_phrase):
                    for expanded in expander.expand(normalized_candidate):
                        expanded_phrase = str(expanded.source_phrase or "").strip().lower()
                        if expanded_phrase:
                            headwords.add(expanded_phrase)
    return tuple(sorted(headwords))


def _expand_reverse_preload_headwords(
    *,
    pair: str,
    reverse_translation_dict_path: Optional[Path],
    reverse_headwords: Optional[Sequence[str]],
) -> Optional[tuple[str, ...]]:
    normalized_pair = str(pair or "").strip().lower()
    if normalized_pair != "en-es" or reverse_headwords is None:
        return tuple(reverse_headwords) if reverse_headwords is not None else None
    if reverse_translation_dict_path is None or not reverse_translation_dict_path.exists():
        return tuple(reverse_headwords)
    wanted = {
        str(headword or "").strip().lower()
        for headword in reverse_headwords
        if str(headword or "").strip()
    }
    if not wanted:
        return ()
    expanded = set(wanted)
    normalized_index = _load_en_es_reverse_headword_norm_index(reverse_translation_dict_path)
    for desired_headword in wanted:
        expanded.update(normalized_index.get(desired_headword, ()))
    return tuple(sorted(expanded))


def _collect_en_es_reverse_headword_forms(raw_headword: str) -> tuple[str, ...]:
    normalizers = (BasicStringNormalizer(), LeadingEnglishInfinitiveNormalizer())
    normalized_forms: list[str] = []
    seen: set[str] = set()

    def add(text: object) -> None:
        normalized = str(text or "").strip().lower()
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        normalized_forms.append(normalized)

    add(raw_headword)
    add(sanitize_dictionary_gloss(raw_headword))
    add(normalize_reverse_token_with_pos(raw_headword))
    candidate = RuleCandidate(
        source_phrase=raw_headword,
        replacement="",
        language_pair="en-es",
        source_dict="benchmark-preload",
        metadata={},
    )
    normalized_candidate = candidate
    for normalizer in normalizers:
        normalized_candidate = normalizer.normalize(normalized_candidate)
    add(normalized_candidate.source_phrase)
    return tuple(normalized_forms)


def _load_en_es_reverse_headword_norm_index(
    reverse_translation_dict_path: Path,
) -> dict[str, tuple[str, ...]]:
    return load_or_compute_path_json_value(
        reverse_translation_dict_path,
        namespace="translation_pack_metadata",
        key={
            "kind": "reverse_headword_norm_index",
            "pair": "en-es",
        },
        compute=lambda: _build_en_es_reverse_headword_norm_index(reverse_translation_dict_path),
        serialize=lambda mapping: {
            str(normalized or "").strip().lower(): [
                str(raw_headword or "").strip().lower()
                for raw_headword in raw_headwords
                if str(raw_headword or "").strip()
            ]
            for normalized, raw_headwords in mapping.items()
            if str(normalized or "").strip()
        },
        deserialize=lambda payload: {
            str(normalized or "").strip().lower(): tuple(
                str(raw_headword or "").strip().lower()
                for raw_headword in raw_headwords
                if str(raw_headword or "").strip()
            )
            for normalized, raw_headwords in payload.items()
            if str(normalized or "").strip()
        },
    )


def _build_en_es_reverse_headword_norm_index(
    reverse_translation_dict_path: Path,
) -> dict[str, tuple[str, ...]]:
    raw_headwords_by_normalized: dict[str, list[str]] = {}
    for raw_headword in load_translation_headwords(reverse_translation_dict_path):
        raw_text = str(raw_headword or "").strip()
        if not raw_text:
            continue
        raw_lower = raw_text.lower()
        for normalized in _collect_en_es_reverse_headword_forms(raw_text):
            bucket = raw_headwords_by_normalized.setdefault(normalized, [])
            if raw_lower not in bucket:
                bucket.append(raw_lower)
    return {
        normalized: tuple(raw_headwords)
        for normalized, raw_headwords in sorted(raw_headwords_by_normalized.items())
    }


def _path_looks_kaikki(path: Optional[Path]) -> bool:
    if path is None:
        return False
    name = path.name.strip().lower()
    return "wiktionary" in name or "kaikki" in name


def _build_pair_compiled_rulegen_context(
    *,
    pair: str,
    targets: Sequence[str],
    translation_dict_path: Optional[Path],
    reverse_translation_dict_path: Optional[Path],
    gloss_records_by_target: Optional[Mapping[str, Sequence[TranslationGlossRecord]]],
    reverse_gloss_records_by_source: Optional[Mapping[str, Sequence[TranslationGlossRecord]]],
    word_packages_by_target: Mapping[str, Mapping[str, object]],
    gloss_base_forms: Optional[Sequence[str]] = None,
) -> Optional[object]:
    normalized_pair = str(pair or "").strip().lower()
    if normalized_pair != "en-es":
        return None
    if gloss_records_by_target is None:
        return None
    source_dict = (
        "wiktionary_es_en" if _path_looks_kaikki(translation_dict_path) else "freedict_es_en"
    )
    dictionary_pos_source_profile = (
        "wiktionary" if _path_looks_kaikki(translation_dict_path) else "freedict"
    )
    return build_en_es_compiled_resources(
        targets=targets,
        records_by_target=gloss_records_by_target,
        reverse_records_by_source=reverse_gloss_records_by_source,
        word_packages_by_target=word_packages_by_target,
        language_pair=normalized_pair,
        source_dict=source_dict,
        dictionary_pos_source_profile=dictionary_pos_source_profile,
        gloss_base_forms_override=gloss_base_forms,
    )


def _build_pair_benchmark_context(
    *,
    paths,
    store: SrsStore,
    pair: str,
    cases: Sequence[RulegenBenchmarkCase],
    jmdict_override: Optional[Path],
    translation_dict_override: Optional[Path],
    reverse_translation_dict_override: Optional[Path],
    frozen_word_package_snapshots: Mapping[str, Mapping[str, object]],
    timing: Optional[BenchmarkTimingCollector] = None,
) -> PairBenchmarkContext:
    started = perf_counter()
    jmdict_path, translation_dict_path, reverse_translation_dict_path = (
        _resolve_pair_resources_for_benchmark(
            paths=paths,
            pair=pair,
            jmdict_override=jmdict_override,
            freedict_override=translation_dict_override,
            freedict_reverse_override=reverse_translation_dict_override,
        )
    )
    if timing is not None:
        timing.add("resolve_resources", perf_counter() - started, pair=pair)

    started = perf_counter()
    resources = _build_pair_resources_payload(
        jmdict_path=jmdict_path,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
    )
    if timing is not None:
        timing.add("build_resource_payload", perf_counter() - started, pair=pair)

    target_set = {case.target for case in cases}
    targets = tuple(sorted(target_set))
    started = perf_counter()
    frozen_snapshot = frozen_word_package_snapshots.get(pair)
    if isinstance(frozen_snapshot, Mapping):
        word_package_snapshot = {target: frozen_snapshot.get(target) for target in targets}
        word_packages = {
            target: package
            for target, package in word_package_snapshot.items()
            if isinstance(package, Mapping)
        }
    else:
        word_packages = _build_store_word_packages(store=store, pair=pair, targets=target_set)
        _apply_case_word_package_overrides(package_map=word_packages, pair=pair, cases=cases)
        word_package_snapshot = _build_word_package_snapshot(
            targets=targets,
            word_packages_by_target=word_packages,
        )
    if timing is not None:
        timing.add("build_word_packages", perf_counter() - started, pair=pair)

    started = perf_counter()
    gloss_records_by_target, reverse_gloss_records_by_source = _preload_pair_gloss_records(
        pair=pair,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
        targets=targets,
    )
    gloss_base_forms = (
        tuple(
            sorted(
                load_translation_gloss_base_forms(
                    translation_dict_path,
                    target_lang=_translation_target_lang_for_pair(pair) or "",
                )
            )
        )
        if translation_dict_path is not None and _translation_target_lang_for_pair(pair) is not None
        else None
    )
    if timing is not None:
        timing.add("preload_translation_gloss_records", perf_counter() - started, pair=pair)

    started = perf_counter()
    compiled_pair_context = _build_pair_compiled_rulegen_context(
        pair=pair,
        targets=targets,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
        gloss_records_by_target=gloss_records_by_target,
        reverse_gloss_records_by_source=reverse_gloss_records_by_source,
        word_packages_by_target=word_packages,
        gloss_base_forms=gloss_base_forms,
    )
    if timing is not None:
        timing.add("compile_pair_context", perf_counter() - started, pair=pair)

    compiled_case_refs = _build_compiled_case_refs(
        cases=cases,
        compiled_pair_context=compiled_pair_context,
    )
    compiled_case_table = _build_compiled_case_table(
        cases=cases,
        compiled_case_refs=compiled_case_refs,
    )

    return PairBenchmarkContext(
        pair=pair,
        cases=tuple(cases),
        targets=targets,
        jmdict_path=jmdict_path,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
        resources=resources,
        word_package_snapshot=word_package_snapshot,
        word_packages_by_target=word_packages,
        gloss_records_by_target=gloss_records_by_target,
        reverse_gloss_records_by_source=reverse_gloss_records_by_source,
        compiled_pair_context=compiled_pair_context,
        compiled_case_refs=compiled_case_refs,
        compiled_case_table=compiled_case_table,
    )


def _build_compiled_case_refs(
    *,
    cases: Sequence[RulegenBenchmarkCase],
    compiled_pair_context: Optional[object],
) -> tuple[CompiledBenchmarkCaseRef, ...]:
    target_ids_by_target = getattr(compiled_pair_context, "target_ids_by_target", {})
    if not isinstance(target_ids_by_target, Mapping):
        target_ids_by_target = {}
    candidate_table = getattr(compiled_pair_context, "candidate_table", None)
    candidate_row_ids_by_target_id = getattr(
        candidate_table,
        "candidate_row_ids_by_target_id",
        {},
    )
    if not isinstance(candidate_row_ids_by_target_id, Mapping):
        candidate_row_ids_by_target_id = {}
    refs: list[CompiledBenchmarkCaseRef] = []
    for index, case in enumerate(cases):
        target_id = (
            int(target_ids_by_target[case.target]) if case.target in target_ids_by_target else None
        )
        candidate_row_ids = (
            tuple(
                int(row_id)
                for row_id in candidate_row_ids_by_target_id.get(target_id, ())
                if isinstance(row_id, int)
            )
            if target_id is not None
            else ()
        )
        refs.append(
            CompiledBenchmarkCaseRef(
                case_row_id=index,
                case_id=str(case.case_id),
                target=str(case.target),
                target_id=target_id,
                candidate_row_ids=candidate_row_ids,
            )
        )
    return tuple(refs)


def _build_compiled_case_table(
    *,
    cases: Sequence[RulegenBenchmarkCase],
    compiled_case_refs: Sequence[CompiledBenchmarkCaseRef],
) -> CompiledBenchmarkCaseTable:
    refs_by_case_id = {
        str(ref.case_id): ref for ref in compiled_case_refs if str(ref.case_id).strip()
    }
    phrase_table = _build_compiled_phrase_table(cases)
    phrase_ids_by_phrase = phrase_table.phrase_ids_by_phrase

    case_row_ids: list[int] = []
    case_ids: list[str] = []
    targets: list[str] = []
    target_ids: list[int] = []
    candidate_row_id_rows: list[tuple[int, ...]] = []
    expected_any_phrase_id_rows: list[tuple[int, ...]] = []
    expected_top1_phrase_id_rows: list[tuple[int, ...]] = []
    forbidden_top1_phrase_id_rows: list[tuple[int, ...]] = []
    forbidden_any_phrase_id_rows: list[tuple[int, ...]] = []

    for index, case in enumerate(cases):
        ref = refs_by_case_id.get(str(case.case_id))
        expected_any = _normalize_case_phrase_list(case.expected_any)
        expected_top1 = (
            _normalize_case_phrase_list(case.expected_top1_any)
            if case.expected_top1_any
            else expected_any
        )
        forbidden_top1 = _normalize_case_phrase_list(case.forbidden_top1)
        forbidden_any = _normalize_case_phrase_list(case.forbidden_any)
        case_row_ids.append(int(ref.case_row_id) if ref is not None else index)
        case_ids.append(str(case.case_id))
        targets.append(str(case.target))
        target_ids.append(
            int(ref.target_id) if ref is not None and ref.target_id is not None else -1
        )
        candidate_row_id_rows.append(
            tuple(int(row_id) for row_id in (ref.candidate_row_ids if ref is not None else ()))
        )
        expected_any_phrase_id_rows.append(
            _encode_phrase_id_row(expected_any, phrase_ids_by_phrase)
        )
        expected_top1_phrase_id_rows.append(
            _encode_phrase_id_row(expected_top1, phrase_ids_by_phrase)
        )
        forbidden_top1_phrase_id_rows.append(
            _encode_phrase_id_row(forbidden_top1, phrase_ids_by_phrase)
        )
        forbidden_any_phrase_id_rows.append(
            _encode_phrase_id_row(forbidden_any, phrase_ids_by_phrase)
        )

    return CompiledBenchmarkCaseTable(
        case_row_ids=tuple(case_row_ids),
        case_ids=tuple(case_ids),
        targets=tuple(targets),
        target_ids=tuple(target_ids),
        candidate_row_id_rows=tuple(candidate_row_id_rows),
        expected_any_phrase_id_rows=tuple(expected_any_phrase_id_rows),
        expected_top1_phrase_id_rows=tuple(expected_top1_phrase_id_rows),
        forbidden_top1_phrase_id_rows=tuple(forbidden_top1_phrase_id_rows),
        forbidden_any_phrase_id_rows=tuple(forbidden_any_phrase_id_rows),
        phrase_table=phrase_table,
    )


def _build_compiled_phrase_table(
    cases: Sequence[RulegenBenchmarkCase],
) -> CompiledBenchmarkPhraseTable:
    ordered_phrases: list[str] = []
    phrase_ids_by_phrase: dict[str, int] = {}
    for case in cases:
        expected_any = _normalize_case_phrase_list(case.expected_any)
        expected_top1 = (
            _normalize_case_phrase_list(case.expected_top1_any)
            if case.expected_top1_any
            else expected_any
        )
        for phrase in itertools.chain(
            expected_any,
            expected_top1,
            _normalize_case_phrase_list(case.forbidden_top1),
            _normalize_case_phrase_list(case.forbidden_any),
        ):
            if phrase not in phrase_ids_by_phrase:
                phrase_ids_by_phrase[phrase] = len(ordered_phrases)
                ordered_phrases.append(phrase)
    return CompiledBenchmarkPhraseTable(
        normalized_phrases=tuple(ordered_phrases),
        phrase_ids_by_phrase=dict(phrase_ids_by_phrase),
    )


def _normalize_case_phrase_list(values: Sequence[object]) -> tuple[str, ...]:
    normalized = [normalize_benchmark_phrase(value) for value in values]
    return tuple(dict.fromkeys(item for item in normalized if item))


def _encode_phrase_id_row(
    phrases: Sequence[str],
    phrase_ids_by_phrase: Mapping[str, int],
) -> tuple[int, ...]:
    return tuple(
        int(phrase_ids_by_phrase[phrase]) for phrase in phrases if phrase in phrase_ids_by_phrase
    )


def _resolve_rule_candidate_row_id(
    rule: VocabRule,
    *,
    candidate_row_id_by_candidate_id: Mapping[int, int],
) -> int:
    metadata = getattr(rule, "metadata", None)
    if metadata is None:
        return -1
    rulegen = getattr(metadata, "rulegen", None)
    if not isinstance(rulegen, Mapping):
        return -1
    candidate_id = rulegen.get("compiled_candidate_id")
    if isinstance(candidate_id, bool):
        return -1
    if isinstance(candidate_id, int):
        return int(candidate_row_id_by_candidate_id.get(int(candidate_id), -1))
    if isinstance(candidate_id, str):
        text = candidate_id.strip()
        if not text:
            return -1
        try:
            parsed = int(text)
        except ValueError:
            return -1
        return int(candidate_row_id_by_candidate_id.get(parsed, -1))
    return -1


def _build_compiled_rule_table(
    *,
    rules_by_target: Mapping[str, Sequence[VocabRule]],
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_pair_context: Optional[object] = None,
) -> CompiledBenchmarkRuleTable:
    phrase_ids_by_phrase = compiled_case_table.phrase_table.phrase_ids_by_phrase
    candidate_table = getattr(compiled_pair_context, "candidate_table", None)
    candidate_row_id_by_candidate_id = getattr(
        candidate_table,
        "candidate_row_id_by_candidate_id",
        {},
    )
    if not isinstance(candidate_row_id_by_candidate_id, Mapping):
        candidate_row_id_by_candidate_id = {}
    ordered_targets = tuple(
        sorted(str(target) for target in rules_by_target if str(target).strip())
    )
    all_source_rows: list[tuple[str, ...]] = []
    source_phrase_id_rows: list[tuple[int, ...]] = []
    candidate_row_id_rows: list[tuple[int, ...]] = []
    top1_confidences: list[Optional[float]] = []
    variant_rule_counts: list[int] = []
    top1_variant_flags: list[bool] = []
    row_id_by_target: dict[str, int] = {}

    for row_id, target in enumerate(ordered_targets):
        rules = tuple(rules_by_target.get(target, ()))
        normalized_sources = tuple(
            source
            for source in (normalize_benchmark_phrase(rule.source_phrase) for rule in rules)
            if source
        )
        source_phrase_ids = tuple(
            int(phrase_ids_by_phrase.get(source, -1)) for source in normalized_sources
        )
        candidate_row_ids = tuple(
            _resolve_rule_candidate_row_id(
                rule,
                candidate_row_id_by_candidate_id=candidate_row_id_by_candidate_id,
            )
            for rule in rules
        )
        all_source_rows.append(normalized_sources)
        source_phrase_id_rows.append(source_phrase_ids)
        candidate_row_id_rows.append(candidate_row_ids)
        top1_confidences.append(_extract_rule_confidence(rules[0]) if rules else None)
        variant_rule_counts.append(sum(1 for rule in rules if _is_variant_rule(rule)))
        top1_variant_flags.append(bool(rules and _is_variant_rule(rules[0])))
        row_id_by_target[target] = row_id

    return CompiledBenchmarkRuleTable(
        targets=ordered_targets,
        all_source_rows=tuple(all_source_rows),
        source_phrase_id_rows=tuple(source_phrase_id_rows),
        candidate_row_id_rows=tuple(candidate_row_id_rows),
        top1_confidences=tuple(top1_confidences),
        variant_rule_counts=tuple(variant_rule_counts),
        top1_variant_flags=tuple(top1_variant_flags),
        row_id_by_target=dict(row_id_by_target),
    )


def _build_compiled_rule_table_from_rules(
    *,
    rules: Sequence[VocabRule],
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_pair_context: Optional[object] = None,
) -> CompiledBenchmarkRuleTable:
    phrase_ids_by_phrase = compiled_case_table.phrase_table.phrase_ids_by_phrase
    candidate_table = getattr(compiled_pair_context, "candidate_table", None)
    candidate_row_id_by_candidate_id = getattr(
        candidate_table,
        "candidate_row_id_by_candidate_id",
        {},
    )
    if not isinstance(candidate_row_id_by_candidate_id, Mapping):
        candidate_row_id_by_candidate_id = {}

    target_rows: dict[str, dict[str, object]] = {}
    for rule in rules:
        target = str(rule.replacement or "").strip()
        if not target:
            continue
        row = target_rows.setdefault(
            target,
            {
                "all_sources": [],
                "source_phrase_ids": [],
                "candidate_row_ids": [],
                "top1_confidence": None,
                "variant_rule_count": 0,
                "top1_variant_flag": False,
            },
        )
        normalized_source = normalize_benchmark_phrase(rule.source_phrase)
        if normalized_source:
            cast_sources = row["all_sources"]
            cast_phrase_ids = row["source_phrase_ids"]
            assert isinstance(cast_sources, list)
            assert isinstance(cast_phrase_ids, list)
            cast_sources.append(normalized_source)
            cast_phrase_ids.append(int(phrase_ids_by_phrase.get(normalized_source, -1)))
        cast_candidate_row_ids = row["candidate_row_ids"]
        assert isinstance(cast_candidate_row_ids, list)
        cast_candidate_row_ids.append(
            _resolve_rule_candidate_row_id(
                rule,
                candidate_row_id_by_candidate_id=candidate_row_id_by_candidate_id,
            )
        )
        is_variant = _is_variant_rule(rule)
        row["variant_rule_count"] = int(row["variant_rule_count"]) + (1 if is_variant else 0)
        if row["top1_confidence"] is None:
            row["top1_confidence"] = _extract_rule_confidence(rule)
            row["top1_variant_flag"] = bool(is_variant)

    ordered_targets = tuple(sorted(target_rows))
    all_source_rows: list[tuple[str, ...]] = []
    source_phrase_id_rows: list[tuple[int, ...]] = []
    candidate_row_id_rows: list[tuple[int, ...]] = []
    top1_confidences: list[Optional[float]] = []
    variant_rule_counts: list[int] = []
    top1_variant_flags: list[bool] = []
    row_id_by_target: dict[str, int] = {}

    for row_id, target in enumerate(ordered_targets):
        row = target_rows[target]
        row_id_by_target[target] = row_id
        all_sources = row["all_sources"]
        source_phrase_ids = row["source_phrase_ids"]
        candidate_row_ids = row["candidate_row_ids"]
        assert isinstance(all_sources, list)
        assert isinstance(source_phrase_ids, list)
        assert isinstance(candidate_row_ids, list)
        all_source_rows.append(tuple(str(source) for source in all_sources))
        source_phrase_id_rows.append(tuple(int(value) for value in source_phrase_ids))
        candidate_row_id_rows.append(tuple(int(value) for value in candidate_row_ids))
        top1_confidences.append(
            float(row["top1_confidence"]) if row["top1_confidence"] is not None else None
        )
        variant_rule_counts.append(int(row["variant_rule_count"]))
        top1_variant_flags.append(bool(row["top1_variant_flag"]))

    return CompiledBenchmarkRuleTable(
        targets=ordered_targets,
        all_source_rows=tuple(all_source_rows),
        source_phrase_id_rows=tuple(source_phrase_id_rows),
        candidate_row_id_rows=tuple(candidate_row_id_rows),
        top1_confidences=tuple(top1_confidences),
        variant_rule_counts=tuple(variant_rule_counts),
        top1_variant_flags=tuple(top1_variant_flags),
        row_id_by_target=dict(row_id_by_target),
    )


def _build_compiled_rule_table_from_en_es_selected_rows(
    *,
    selected_row_table: EnEsCompiledSelectedRowTable,
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_pair_context: Optional[object] = None,
) -> CompiledBenchmarkRuleTable:
    phrase_ids_by_phrase = compiled_case_table.phrase_table.phrase_ids_by_phrase
    all_source_rows: list[tuple[str, ...]] = []
    source_phrase_id_rows: list[tuple[int, ...]] = []
    candidate_row_id_rows: list[tuple[int, ...]] = []
    top1_confidences: list[Optional[float]] = []
    variant_rule_counts: list[int] = []
    top1_variant_flags: list[bool] = []
    row_id_by_target: dict[str, int] = {}

    for row_id, target in enumerate(selected_row_table.targets):
        selected_row_ids = tuple(
            int(candidate_row_id)
            for candidate_row_id in selected_row_table.candidate_row_id_rows[row_id]
        )
        normalized_sources = tuple(
            str(source or "").strip()
            for source in selected_row_table.normalized_source_phrase_rows[row_id]
            if str(source or "").strip()
        )
        source_phrase_ids = tuple(
            int(phrase_ids_by_phrase.get(normalized_source, -1))
            for normalized_source in normalized_sources
        )
        all_source_rows.append(tuple(normalized_sources))
        source_phrase_id_rows.append(tuple(source_phrase_ids))
        candidate_row_id_rows.append(selected_row_ids)
        top1_confidences.append(selected_row_table.top1_confidences[row_id])
        variant_rule_counts.append(int(selected_row_table.variant_rule_counts[row_id]))
        top1_variant_flags.append(bool(selected_row_table.top1_variant_flags[row_id]))
        row_id_by_target[str(target)] = row_id

    return CompiledBenchmarkRuleTable(
        targets=tuple(str(target) for target in selected_row_table.targets),
        all_source_rows=tuple(all_source_rows),
        source_phrase_id_rows=tuple(source_phrase_id_rows),
        candidate_row_id_rows=tuple(candidate_row_id_rows),
        top1_confidences=tuple(top1_confidences),
        variant_rule_counts=tuple(variant_rule_counts),
        top1_variant_flags=tuple(top1_variant_flags),
        row_id_by_target=dict(row_id_by_target),
    )


def _evaluate_benchmark_case_compiled(
    *,
    case: RulegenBenchmarkCase,
    case_row_id: int,
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_rule_table: CompiledBenchmarkRuleTable,
) -> RulegenBenchmarkCaseResult:
    result, _ = _evaluate_benchmark_case_compiled_row(
        case=case,
        case_row_id=case_row_id,
        compiled_case_table=compiled_case_table,
        compiled_rule_table=compiled_rule_table,
    )
    return result


def _evaluate_benchmark_case_compiled_payload_row(
    *,
    case: RulegenBenchmarkCase,
    case_row_id: int,
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_rule_table: CompiledBenchmarkRuleTable,
    include_payload: bool = True,
) -> tuple[
    Optional[dict[str, object]], tuple[int, Optional[float], bool, bool, bool, bool, int, bool]
]:
    rule_row_id = compiled_rule_table.row_id_by_target.get(str(case.target), -1)
    if rule_row_id >= 0:
        all_sources = compiled_rule_table.all_source_rows[rule_row_id]
        source_phrase_ids = compiled_rule_table.source_phrase_id_rows[rule_row_id]
        top1_confidence = compiled_rule_table.top1_confidences[rule_row_id]
        variant_rule_count = compiled_rule_table.variant_rule_counts[rule_row_id]
        top1_is_variant = compiled_rule_table.top1_variant_flags[rule_row_id]
    else:
        all_sources = ()
        source_phrase_ids = ()
        top1_confidence = None
        variant_rule_count = 0
        top1_is_variant = False

    top1_source = all_sources[0] if all_sources else None
    top3_phrase_ids = tuple(source_phrase_ids[:3])
    top1_phrase_id = source_phrase_ids[0] if source_phrase_ids else -1
    expected_any_ids = frozenset(compiled_case_table.expected_any_phrase_id_rows[case_row_id])
    expected_top1_ids = frozenset(compiled_case_table.expected_top1_phrase_id_rows[case_row_id])
    forbidden_top1_ids = frozenset(compiled_case_table.forbidden_top1_phrase_id_rows[case_row_id])
    forbidden_any_ids = frozenset(compiled_case_table.forbidden_any_phrase_id_rows[case_row_id])
    top1_correct = bool(top1_source and expected_top1_ids and top1_phrase_id in expected_top1_ids)
    top3_contains_expected = bool(
        expected_any_ids and any(phrase_id in expected_any_ids for phrase_id in top3_phrase_ids)
    )
    top1_forbidden = bool(
        top1_source and forbidden_top1_ids and top1_phrase_id in forbidden_top1_ids
    )
    forbidden_any_present = bool(
        any(phrase_id >= 0 and phrase_id in forbidden_any_ids for phrase_id in source_phrase_ids)
    )

    payload: Optional[dict[str, object]]
    if include_payload:
        top3_sources = tuple(all_sources[:3])
        expected_matches = tuple(
            source
            for source, phrase_id in zip(all_sources, source_phrase_ids)
            if phrase_id >= 0 and phrase_id in expected_any_ids
        )
        forbidden_matches = tuple(
            source
            for source, phrase_id in zip(all_sources, source_phrase_ids)
            if phrase_id >= 0 and phrase_id in forbidden_any_ids
        )
        payload = {
            "case_id": case.case_id,
            "pair": case.pair,
            "target": case.target,
            "rule_count": len(all_sources),
            "top1_source": top1_source,
            "top3_sources": list(top3_sources),
            "all_sources": list(all_sources),
            "top1_confidence": top1_confidence,
            "top1_correct": bool(top1_correct),
            "top3_contains_expected": bool(top3_contains_expected),
            "top1_forbidden": bool(top1_forbidden),
            "forbidden_any_present": bool(forbidden_any_present),
            "variant_rule_count": int(variant_rule_count),
            "top1_is_variant": bool(top1_is_variant),
            "expected_matches": list(expected_matches),
            "forbidden_matches": list(forbidden_matches),
        }
    else:
        payload = None

    return (
        payload,
        (
            len(all_sources),
            top1_confidence,
            top1_correct,
            top3_contains_expected,
            top1_forbidden,
            forbidden_any_present,
            variant_rule_count,
            top1_is_variant,
        ),
    )


def _evaluate_benchmark_case_compiled_row(
    *,
    case: RulegenBenchmarkCase,
    case_row_id: int,
    compiled_case_table: CompiledBenchmarkCaseTable,
    compiled_rule_table: CompiledBenchmarkRuleTable,
) -> tuple[
    RulegenBenchmarkCaseResult, tuple[int, Optional[float], bool, bool, bool, bool, int, bool]
]:
    payload, case_row = _evaluate_benchmark_case_compiled_payload_row(
        case=case,
        case_row_id=case_row_id,
        compiled_case_table=compiled_case_table,
        compiled_rule_table=compiled_rule_table,
    )
    assert payload is not None

    result = RulegenBenchmarkCaseResult(
        case_id=str(payload["case_id"]),
        pair=str(payload["pair"]),
        target=str(payload["target"]),
        rule_count=int(payload["rule_count"]),
        top1_source=payload["top1_source"]
        if payload["top1_source"] is None
        else str(payload["top1_source"]),
        top3_sources=tuple(str(source) for source in payload["top3_sources"]),
        all_sources=tuple(str(source) for source in payload["all_sources"]),
        top1_confidence=(
            float(payload["top1_confidence"]) if payload["top1_confidence"] is not None else None
        ),
        top1_correct=bool(payload["top1_correct"]),
        top3_contains_expected=bool(payload["top3_contains_expected"]),
        top1_forbidden=bool(payload["top1_forbidden"]),
        forbidden_any_present=bool(payload["forbidden_any_present"]),
        variant_rule_count=int(payload["variant_rule_count"]),
        top1_is_variant=bool(payload["top1_is_variant"]),
        expected_matches=tuple(str(source) for source in payload["expected_matches"]),
        forbidden_matches=tuple(str(source) for source in payload["forbidden_matches"]),
    )
    return (result, case_row)


def _build_compiled_case_result_table(
    *,
    case_rows: Sequence[tuple[int, Optional[float], bool, bool, bool, bool, int, bool]],
) -> CompiledBenchmarkCaseResultTable:
    rule_counts: list[int] = []
    top1_confidences: list[Optional[float]] = []
    top1_correct_flags: list[bool] = []
    top3_contains_expected_flags: list[bool] = []
    top1_forbidden_flags: list[bool] = []
    forbidden_any_present_flags: list[bool] = []
    variant_rule_counts: list[int] = []
    top1_variant_flags: list[bool] = []
    for (
        rule_count,
        top1_confidence,
        top1_correct,
        top3_contains_expected,
        top1_forbidden,
        forbidden_any_present,
        variant_rule_count,
        top1_is_variant,
    ) in case_rows:
        rule_counts.append(int(rule_count))
        top1_confidences.append(float(top1_confidence) if top1_confidence is not None else None)
        top1_correct_flags.append(bool(top1_correct))
        top3_contains_expected_flags.append(bool(top3_contains_expected))
        top1_forbidden_flags.append(bool(top1_forbidden))
        forbidden_any_present_flags.append(bool(forbidden_any_present))
        variant_rule_counts.append(int(variant_rule_count))
        top1_variant_flags.append(bool(top1_is_variant))
    return CompiledBenchmarkCaseResultTable(
        case_row_ids=tuple(range(len(case_rows))),
        rule_counts=tuple(rule_counts),
        top1_confidences=tuple(top1_confidences),
        top1_correct_flags=tuple(top1_correct_flags),
        top3_contains_expected_flags=tuple(top3_contains_expected_flags),
        top1_forbidden_flags=tuple(top1_forbidden_flags),
        forbidden_any_present_flags=tuple(forbidden_any_present_flags),
        variant_rule_counts=tuple(variant_rule_counts),
        top1_variant_flags=tuple(top1_variant_flags),
    )


def _evaluate_case_results_with_table(
    *,
    context: PairBenchmarkContext,
    rules_by_target: Optional[Mapping[str, Sequence[VocabRule]]] = None,
    rules: Optional[Sequence[VocabRule]] = None,
    compiled_rule_table: Optional[CompiledBenchmarkRuleTable] = None,
) -> tuple[tuple[RulegenBenchmarkCaseResult, ...], Optional[CompiledBenchmarkCaseResultTable]]:
    compiled_case_table = context.compiled_case_table
    if compiled_case_table is None:
        resolved_rules_by_target = (
            rules_by_target if rules_by_target is not None else _group_rules_by_target(rules or ())
        )
        return (
            tuple(
                evaluate_benchmark_case(case, tuple(resolved_rules_by_target.get(case.target, ())))
                for case in context.cases
            ),
            None,
        )
    if compiled_rule_table is None and rules is not None:
        compiled_rule_table = _build_compiled_rule_table_from_rules(
            rules=rules,
            compiled_case_table=compiled_case_table,
            compiled_pair_context=context.compiled_pair_context,
        )
    elif compiled_rule_table is None:
        compiled_rule_table = _build_compiled_rule_table(
            rules_by_target=rules_by_target or {},
            compiled_case_table=compiled_case_table,
            compiled_pair_context=context.compiled_pair_context,
        )
    case_results: list[RulegenBenchmarkCaseResult] = []
    case_rows: list[tuple[int, Optional[float], bool, bool, bool, bool, int, bool]] = []
    for index, case in enumerate(context.cases):
        case_result, case_row = _evaluate_benchmark_case_compiled_row(
            case=case,
            case_row_id=index,
            compiled_case_table=compiled_case_table,
            compiled_rule_table=compiled_rule_table,
        )
        case_results.append(case_result)
        case_rows.append(case_row)
    return (
        tuple(case_results),
        _build_compiled_case_result_table(case_rows=case_rows),
    )


def _evaluate_case_payloads_with_table(
    *,
    context: PairBenchmarkContext,
    rules_by_target: Optional[Mapping[str, Sequence[VocabRule]]] = None,
    rules: Optional[Sequence[VocabRule]] = None,
    compiled_rule_table: Optional[CompiledBenchmarkRuleTable] = None,
    include_payloads: bool = True,
) -> tuple[tuple[dict[str, object], ...], Optional[CompiledBenchmarkCaseResultTable]]:
    compiled_case_table = context.compiled_case_table
    if compiled_case_table is None:
        case_results, case_result_table = _evaluate_case_results_with_table(
            context=context,
            rules_by_target=rules_by_target,
            rules=rules,
            compiled_rule_table=compiled_rule_table,
        )
        return (
            tuple(result.to_dict() for result in case_results) if include_payloads else (),
            case_result_table,
        )
    if compiled_rule_table is None and rules is not None:
        compiled_rule_table = _build_compiled_rule_table_from_rules(
            rules=rules,
            compiled_case_table=compiled_case_table,
            compiled_pair_context=context.compiled_pair_context,
        )
    elif compiled_rule_table is None:
        compiled_rule_table = _build_compiled_rule_table(
            rules_by_target=rules_by_target or {},
            compiled_case_table=compiled_case_table,
            compiled_pair_context=context.compiled_pair_context,
        )
    case_payloads: list[dict[str, object]] = []
    case_rows: list[tuple[int, Optional[float], bool, bool, bool, bool, int, bool]] = []
    for index, case in enumerate(context.cases):
        case_payload, case_row = _evaluate_benchmark_case_compiled_payload_row(
            case=case,
            case_row_id=index,
            compiled_case_table=compiled_case_table,
            compiled_rule_table=compiled_rule_table,
            include_payload=include_payloads,
        )
        if case_payload is not None:
            case_payloads.append(case_payload)
        case_rows.append(case_row)
    return (
        tuple(case_payloads),
        _build_compiled_case_result_table(case_rows=case_rows),
    )


def _evaluate_case_results(
    *,
    context: PairBenchmarkContext,
    rules_by_target: Mapping[str, Sequence[VocabRule]],
) -> tuple[RulegenBenchmarkCaseResult, ...]:
    case_results, _ = _evaluate_case_results_with_table(
        context=context,
        rules_by_target=rules_by_target,
    )
    return case_results


def _summarize_compiled_case_results(
    *,
    pair: str,
    case_result_table: CompiledBenchmarkCaseResultTable,
    objective_weights: Optional[RulegenBenchmarkObjectiveWeights] = None,
) -> RulegenBenchmarkSummary:
    weights = objective_weights or RulegenBenchmarkObjectiveWeights()
    case_count = len(case_result_table.case_row_ids)
    top1_correct_count = sum(1 for flag in case_result_table.top1_correct_flags if flag)
    top3_contains_expected_count = sum(
        1 for flag in case_result_table.top3_contains_expected_flags if flag
    )
    forbidden_top1_count = sum(1 for flag in case_result_table.top1_forbidden_flags if flag)
    forbidden_any_count = sum(1 for flag in case_result_table.forbidden_any_present_flags if flag)
    variant_top1_count = sum(1 for flag in case_result_table.top1_variant_flags if flag)

    total_rule_count = sum(case_result_table.rule_counts)
    variant_rule_count = sum(case_result_table.variant_rule_counts)
    avg_rules_per_target = (total_rule_count / case_count) if case_count else 0.0
    top1_confidences = [
        confidence for confidence in case_result_table.top1_confidences if confidence is not None
    ]
    avg_top1_confidence = (
        float(sum(top1_confidences) / len(top1_confidences)) if top1_confidences else None
    )

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


def _compute_file_sha256_uncached(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            if not chunk:
                break
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _compute_file_sha256(path: Optional[Path]) -> Optional[str]:
    if path is None or not path.exists() or not path.is_file():
        return None
    return load_or_compute_path_json_value(
        path,
        namespace="benchmark_resource_checksums",
        key={"kind": "sha256"},
        compute=lambda: _compute_file_sha256_uncached(path),
        serialize=lambda value: str(value or ""),
        deserialize=lambda payload: str(payload or ""),
    )


def _build_pair_resources_payload(
    *,
    jmdict_path: Optional[Path],
    translation_dict_path: Optional[Path],
    reverse_translation_dict_path: Optional[Path],
) -> dict[str, object]:
    jmdict_path_text = str(jmdict_path) if jmdict_path else None
    translation_dict_path_text = str(translation_dict_path) if translation_dict_path else None
    reverse_translation_dict_path_text = (
        str(reverse_translation_dict_path) if reverse_translation_dict_path else None
    )
    checksums = {
        "jmdict_sha256": _compute_file_sha256(jmdict_path),
        "translation_dict_sha256": _compute_file_sha256(translation_dict_path),
        "reverse_translation_dict_sha256": _compute_file_sha256(reverse_translation_dict_path),
    }
    return {
        "jmdict_path": jmdict_path_text,
        "translation_dict_path": translation_dict_path_text,
        "reverse_translation_dict_path": reverse_translation_dict_path_text,
        "freedict_path": translation_dict_path_text,
        "freedict_reverse_path": reverse_translation_dict_path_text,
        "checksums": checksums,
    }


def _group_rules_by_target(rules: Sequence[VocabRule]) -> dict[str, list[VocabRule]]:
    by_target: dict[str, list[VocabRule]] = {}
    for rule in rules:
        target = str(rule.replacement or "").strip()
        if not target:
            continue
        by_target.setdefault(target, []).append(rule)
    return by_target


def _build_sweep_configs(args: argparse.Namespace) -> list[SweepConfig]:
    max_definitions_values = _parse_csv_optional_ints(
        args.max_definitions_values,
        name="max-definitions-values",
        zero_as_none=True,
    )
    max_rules_values = _parse_csv_optional_ints(
        args.max_rules_values,
        name="max-rules-values",
        zero_as_none=True,
    )
    confidence_values = _parse_csv_floats(
        args.confidence_threshold_values,
        name="confidence-threshold-values",
    )
    semantic_demotion_scale_values = _parse_csv_floats(
        args.semantic_demotion_scale_values,
        name="semantic-demotion-scale-values",
    )
    include_variants_values = _parse_csv_bools(
        args.include_variants_values,
        name="include-variants-values",
    )
    pos_scoring_values = _parse_csv_bools(
        args.pos_scoring_values,
        name="pos-scoring-values",
    )
    pos_exact_values = _parse_csv_floats(args.pos_exact_values, name="pos-exact-values")
    pos_compatible_values = _parse_csv_floats(
        args.pos_compatible_values,
        name="pos-compatible-values",
    )
    score_weight_dict_values = _parse_csv_floats(
        args.score_weight_dict_values,
        name="score-weight-dict-values",
    )
    score_weight_frequency_values = _parse_csv_floats(
        args.score_weight_frequency_values,
        name="score-weight-frequency-values",
    )
    score_weight_pos_values = _parse_csv_floats(
        args.score_weight_pos_values,
        name="score-weight-pos-values",
    )
    score_weight_variant_values = _parse_csv_floats(
        args.score_weight_variant_values,
        name="score-weight-variant-values",
    )
    score_weight_phrase_values = _parse_csv_floats(
        args.score_weight_phrase_values,
        name="score-weight-phrase-values",
    )
    score_weight_embedding_values = _parse_csv_floats(
        args.score_weight_embedding_values,
        name="score-weight-embedding-values",
    )
    reverse_check_enabled_values = _parse_csv_bools(
        args.reverse_check_enabled_values,
        name="reverse-check-enabled-values",
    )
    reverse_check_match_bonus_values = _parse_csv_floats(
        args.reverse_check_match_bonus_values,
        name="reverse-check-match-bonus-values",
    )
    reverse_check_near_bonus_values = _parse_csv_floats(
        args.reverse_check_near_bonus_values,
        name="reverse-check-near-bonus-values",
    )
    reverse_check_near_rank_max_values = _parse_csv_ints(
        args.reverse_check_near_rank_max_values,
        name="reverse-check-near-rank-max-values",
        min_value=0,
    )
    reverse_check_far_hit_penalty_values = _parse_csv_floats(
        args.reverse_check_far_hit_penalty_values,
        name="reverse-check-far-hit-penalty-values",
    )
    reverse_check_miss_penalty_values = _parse_csv_floats(
        args.reverse_check_miss_penalty_values,
        name="reverse-check-miss-penalty-values",
    )
    reverse_check_exact_hit_ambiguity_threshold_values = _parse_csv_ints(
        args.reverse_check_exact_hit_ambiguity_threshold_values,
        name="reverse-check-exact-hit-ambiguity-threshold-values",
        min_value=0,
    )
    reverse_check_exact_hit_ambiguity_penalty_values = _parse_csv_floats(
        args.reverse_check_exact_hit_ambiguity_penalty_values,
        name="reverse-check-exact-hit-ambiguity-penalty-values",
    )
    reverse_check_exact_hit_specificity_bonus_values = _parse_csv_floats(
        args.reverse_check_exact_hit_specificity_bonus_values,
        name="reverse-check-exact-hit-specificity-bonus-values",
    )
    kaikki_policy_live_demotion_values = _parse_csv_bools(
        args.kaikki_policy_live_demotion_values,
        name="kaikki-policy-live-demotion-values",
    )
    kaikki_policy_risk_family_sets = _parse_family_set_specs(
        args.kaikki_policy_risk_family_sets,
        name="kaikki-policy-risk-family-sets",
    )
    kaikki_policy_late_sense_penalty_values = _parse_csv_floats(
        args.kaikki_policy_late_sense_penalty_values,
        name="kaikki-policy-late-sense-penalty-values",
    )

    configs: list[SweepConfig] = []
    for combo in itertools.product(
        max_definitions_values,
        max_rules_values,
        confidence_values,
        semantic_demotion_scale_values,
        include_variants_values,
        pos_scoring_values,
        pos_exact_values,
        pos_compatible_values,
        score_weight_dict_values,
        score_weight_frequency_values,
        score_weight_pos_values,
        score_weight_variant_values,
        score_weight_phrase_values,
        score_weight_embedding_values,
        reverse_check_enabled_values,
        reverse_check_match_bonus_values,
        reverse_check_near_bonus_values,
        reverse_check_near_rank_max_values,
        reverse_check_far_hit_penalty_values,
        reverse_check_miss_penalty_values,
        reverse_check_exact_hit_ambiguity_threshold_values,
        reverse_check_exact_hit_ambiguity_penalty_values,
        kaikki_policy_live_demotion_values,
        kaikki_policy_risk_family_sets,
        reverse_check_exact_hit_specificity_bonus_values,
        kaikki_policy_late_sense_penalty_values,
    ):
        configs.append(
            SweepConfig(
                max_definitions_per_target=combo[0],
                max_rules_per_target=combo[1],
                confidence_threshold=float(combo[2]),
                semantic_demotion_scale=float(combo[3]),
                include_variants=bool(combo[4]),
                pos_scoring_enabled=bool(combo[5]),
                pos_exact_match_bonus=float(combo[6]),
                pos_compatible_match_bonus=float(combo[7]),
                score_weight_dict_priority=float(combo[8]),
                score_weight_frequency_weight=float(combo[9]),
                score_weight_pos_match=float(combo[10]),
                score_weight_variant_penalty=float(combo[11]),
                score_weight_phrase_penalty=float(combo[12]),
                score_weight_embedding=float(combo[13]),
                reverse_check_enabled=bool(combo[14]),
                reverse_check_match_bonus=float(combo[15]),
                reverse_check_near_bonus=float(combo[16]),
                reverse_check_near_rank_max=max(0, int(combo[17])),
                reverse_check_far_hit_penalty=float(combo[18]),
                reverse_check_miss_penalty=float(combo[19]),
                reverse_check_exact_hit_ambiguity_threshold=max(0, int(combo[20])),
                reverse_check_exact_hit_ambiguity_penalty=float(combo[21]),
                kaikki_policy_live_demotion=bool(combo[22]),
                kaikki_policy_risk_families=tuple(combo[23]),
                reverse_check_exact_hit_specificity_bonus=float(combo[24]),
                kaikki_policy_late_sense_penalty=float(combo[25]),
            )
        )
    return configs


def _run_sort_key(run: SweepRun) -> tuple[float, float, float, float, float, float]:
    summary = run.summary
    return (
        -float(summary.objective_score),
        -float(summary.top1_accuracy),
        -float(summary.top3_recall),
        float(summary.forbidden_top1_rate),
        float(summary.forbidden_any_rate),
        float(summary.avg_rules_per_target),
    )


def _build_rulegen_adapter_request(
    *,
    context: PairBenchmarkContext,
    config: SweepConfig,
) -> RulegenAdapterRequest:
    return RulegenAdapterRequest(
        pair=context.pair,
        targets=context.targets,
        language_pair=context.pair,
        confidence_threshold=config.confidence_threshold,
        max_definitions_per_target=config.max_definitions_per_target,
        max_rules_per_target=config.max_rules_per_target,
        semantic_demotion_scale=config.semantic_demotion_scale,
        include_variants=config.include_variants,
        scoring=config.scoring(),
        reverse_check=config.reverse_check(),
        jmdict_path=context.jmdict_path,
        freedict_de_en_path=context.translation_dict_path,
        freedict_reverse_path=context.reverse_translation_dict_path,
        gloss_records_by_target=context.gloss_records_by_target,
        reverse_gloss_records_by_source=context.reverse_gloss_records_by_source,
        compiled_pair_context=context.compiled_pair_context,
        word_packages_by_target=context.word_packages_by_target,
        kaikki_policy_live_demotion=config.kaikki_policy_live_demotion,
        kaikki_policy_risk_families=config.kaikki_policy_risk_families,
        kaikki_policy_late_sense_penalty=config.kaikki_policy_late_sense_penalty,
    )


def _can_evaluate_sweep_run_from_en_es_compiled_rows(
    *,
    context: PairBenchmarkContext,
    config: SweepConfig,
) -> bool:
    if context.pair != "en-es":
        return False
    if context.compiled_case_table is None or context.translation_dict_path is None:
        return False
    compiled_pair_context = context.compiled_pair_context
    if not isinstance(compiled_pair_context, EnEsCompiledResources):
        return False
    return compiled_pair_context.candidate_table is not None


def _evaluate_sweep_run(
    *,
    context: PairBenchmarkContext,
    config: SweepConfig,
    run_index: int,
    objective_weights: RulegenBenchmarkObjectiveWeights,
    timing: Optional[BenchmarkTimingCollector] = None,
    materialize_case_results: bool = True,
) -> SweepRunEvaluation:
    phase_timings: dict[str, float] = {}
    case_results: tuple[RulegenBenchmarkCaseResult, ...] = ()
    rules: Sequence[VocabRule] = ()
    compiled_rule_table: Optional[CompiledBenchmarkRuleTable] = None
    request = _build_rulegen_adapter_request(context=context, config=config)

    started = perf_counter()
    if _can_evaluate_sweep_run_from_en_es_compiled_rows(context=context, config=config):
        compiled_case_table = context.compiled_case_table
        assert compiled_case_table is not None
        en_es_config = build_en_es_rulegen_config(request)
        selected_row_table = build_en_es_compiled_selected_row_table(
            context.targets,
            config=en_es_config,
        )
        compiled_rule_table = _build_compiled_rule_table_from_en_es_selected_rows(
            selected_row_table=selected_row_table,
            compiled_case_table=compiled_case_table,
            compiled_pair_context=context.compiled_pair_context,
        )
    else:
        rules = run_rules_with_adapter(request)
    phase_timings["run_config"] = perf_counter() - started

    started = perf_counter()
    if context.compiled_case_table is not None:
        phase_timings["group_rules"] = 0.0
        case_result_payloads, compiled_case_result_table = _evaluate_case_payloads_with_table(
            context=context,
            rules=rules,
            compiled_rule_table=compiled_rule_table,
            include_payloads=materialize_case_results,
        )
    else:
        grouped_started = perf_counter()
        rules_by_target = _group_rules_by_target(rules)
        phase_timings["group_rules"] = perf_counter() - grouped_started
        case_results, compiled_case_result_table = _evaluate_case_results_with_table(
            context=context,
            rules_by_target=rules_by_target,
        )
        case_result_payloads = (
            tuple(result.to_dict() for result in case_results) if materialize_case_results else ()
        )
    phase_timings["evaluate_cases"] = perf_counter() - started

    started = perf_counter()
    if compiled_case_result_table is not None:
        summary = _summarize_compiled_case_results(
            pair=context.pair,
            case_result_table=compiled_case_result_table,
            objective_weights=objective_weights,
        )
    else:
        summary = summarize_benchmark_results(
            pair=context.pair,
            case_results=case_results,
            objective_weights=objective_weights,
        )
    phase_timings["summarize_run"] = perf_counter() - started

    run = SweepRun(
        pair=context.pair,
        run_index=run_index,
        config=config,
        summary=summary,
        case_results=case_result_payloads,
    )
    if timing is not None:
        for phase, duration in phase_timings.items():
            timing.add(phase, duration, pair=context.pair)
    return SweepRunEvaluation(run=run, phase_timings=phase_timings)


def _init_sweep_worker(
    context: PairBenchmarkContext,
    objective_weights: RulegenBenchmarkObjectiveWeights,
    materialize_case_results: bool,
) -> None:
    global _WORKER_CONTEXT, _WORKER_OBJECTIVE_WEIGHTS, _WORKER_MATERIALIZE_CASE_RESULTS
    _WORKER_CONTEXT = context
    _WORKER_OBJECTIVE_WEIGHTS = objective_weights
    _WORKER_MATERIALIZE_CASE_RESULTS = bool(materialize_case_results)


def _evaluate_sweep_run_from_worker_state(
    run_index: int,
    config: SweepConfig,
) -> SweepRunEvaluation:
    if _WORKER_CONTEXT is None or _WORKER_OBJECTIVE_WEIGHTS is None:
        raise RuntimeError("Sweep worker context not initialized.")
    return _evaluate_sweep_run(
        context=_WORKER_CONTEXT,
        config=config,
        run_index=run_index,
        objective_weights=_WORKER_OBJECTIVE_WEIGHTS,
        materialize_case_results=bool(_WORKER_MATERIALIZE_CASE_RESULTS),
    )


def _resolve_job_count(requested_jobs: int, *, config_count: int) -> int:
    jobs = max(1, int(requested_jobs))
    if config_count <= 0:
        return 1
    return min(jobs, config_count)


def _run_pair_sweep(
    *,
    context: PairBenchmarkContext,
    sweep_configs: Sequence[SweepConfig],
    objective_weights: RulegenBenchmarkObjectiveWeights,
    jobs: int,
    timing: Optional[BenchmarkTimingCollector] = None,
    materialize_case_results: bool = True,
) -> list[SweepRun]:
    evaluations: list[SweepRunEvaluation] = []
    max_workers = _resolve_job_count(jobs, config_count=len(sweep_configs))
    materialize_case_results_during_sweep = materialize_case_results or len(sweep_configs) <= 1
    if max_workers <= 1 or len(sweep_configs) <= 1:
        for run_index, config in enumerate(sweep_configs, start=1):
            evaluations.append(
                _evaluate_sweep_run(
                    context=context,
                    config=config,
                    run_index=run_index,
                    objective_weights=objective_weights,
                    timing=timing,
                    materialize_case_results=materialize_case_results_during_sweep,
                )
            )
    else:
        with ProcessPoolExecutor(
            max_workers=max_workers,
            mp_context=multiprocessing.get_context("spawn"),
            initializer=_init_sweep_worker,
            initargs=(context, objective_weights, materialize_case_results_during_sweep),
        ) as executor:
            future_by_run_index = {
                executor.submit(_evaluate_sweep_run_from_worker_state, run_index, config): run_index
                for run_index, config in enumerate(sweep_configs, start=1)
            }
            for future in as_completed(future_by_run_index):
                evaluations.append(future.result())
        evaluations.sort(key=lambda evaluation: evaluation.run.run_index)
        if timing is not None:
            for evaluation in evaluations:
                for phase, duration in evaluation.phase_timings.items():
                    timing.add(phase, duration, pair=context.pair)
    pair_run_list = [evaluation.run for evaluation in evaluations]
    started = perf_counter()
    pair_run_list.sort(key=_run_sort_key)
    if timing is not None:
        timing.add("sort_pair_runs", perf_counter() - started, pair=context.pair)
    if (
        not materialize_case_results
        and len(sweep_configs) > 1
        and pair_run_list
        and not pair_run_list[0].case_results
    ):
        started = perf_counter()
        pair_run_list[0] = _evaluate_sweep_run(
            context=context,
            config=pair_run_list[0].config,
            run_index=pair_run_list[0].run_index,
            objective_weights=objective_weights,
            materialize_case_results=True,
        ).run
        if timing is not None:
            timing.add(
                "rehydrate_best_run_case_results",
                perf_counter() - started,
                pair=context.pair,
            )
    return pair_run_list


def _render_markdown_report(
    *,
    pair_runs: Mapping[str, Sequence[SweepRun]],
    top_n: int,
) -> str:
    lines: list[str] = [
        "# Rulegen Benchmark Sweep",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    for pair, runs in sorted(pair_runs.items()):
        lines.append(f"## {pair}")
        lines.append("")
        if not runs:
            lines.append("No runs.")
            lines.append("")
            continue
        lines.append(
            "| Rank | Objective | Top1 | Top3 | ForbidTop1 | ForbidAny | AvgRules | Config |"
        )
        lines.append("|---:|---:|---:|---:|---:|---:|---:|---|")
        for rank, run in enumerate(runs[:top_n], start=1):
            summary = run.summary
            lines.append(
                "| "
                f"{rank} | "
                f"{summary.objective_score:.3f} | "
                f"{summary.top1_accuracy:.2%} | "
                f"{summary.top3_recall:.2%} | "
                f"{summary.forbidden_top1_rate:.2%} | "
                f"{summary.forbidden_any_rate:.2%} | "
                f"{summary.avg_rules_per_target:.2f} | "
                f"`{run.config.label()}` |"
            )
        lines.append("")
    return "\n".join(lines)


def _write_benchmark_outputs(
    *,
    report_payload: Mapping[str, object],
    markdown_report: Optional[str],
    html_report: Optional[str],
    json_output: Optional[Path],
    markdown_output: Optional[Path],
    html_output: Optional[Path],
    timing_payload: Mapping[str, object],
    timing_json_output: Optional[Path],
) -> None:
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(report_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if markdown_output is not None and markdown_report is not None:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(markdown_report, encoding="utf-8")
    if html_output is not None and html_report is not None:
        html_output.parent.mkdir(parents=True, exist_ok=True)
        html_output.write_text(html_report, encoding="utf-8")
    if timing_json_output is not None:
        timing_json_output.parent.mkdir(parents=True, exist_ok=True)
        timing_json_output.write_text(
            json.dumps(timing_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _render_report_artifacts(
    *,
    report_payload: dict[str, object],
    pair_runs: Mapping[str, Sequence[SweepRun]],
    cases_by_pair: Mapping[str, Sequence[RulegenBenchmarkCase]],
    top_n: int,
    timing: BenchmarkTimingCollector,
    wall_clock_started: float,
) -> tuple[str, str, dict[str, object]]:
    started = perf_counter()
    markdown_report = _render_markdown_report(pair_runs=pair_runs, top_n=top_n)
    timing.add("render_markdown", perf_counter() - started)

    report_payload["timing"] = timing.to_dict(
        wall_clock_seconds=perf_counter() - wall_clock_started
    )
    started = perf_counter()
    html_report = _load_html_report_renderer()(
        report_payload=report_payload,
        pair_runs=pair_runs,
        cases_by_pair=cases_by_pair,
        top_n=top_n,
    )
    timing.add("render_html", perf_counter() - started)
    timing_payload = timing.to_dict(wall_clock_seconds=perf_counter() - wall_clock_started)
    report_payload["timing"] = timing_payload
    return markdown_report, html_report, timing_payload


def _load_render_inputs_from_report_payload(
    report_payload: Mapping[str, object],
) -> tuple[dict[str, list[SweepRun]], dict[str, list[RulegenBenchmarkCase]]]:
    pair_runs = _load_pair_runs_from_report_payload(report_payload)
    dataset_path = _resolve_path_from_report_payload(
        report_payload.get("dataset_path"),
        project_root=PROJECT_ROOT,
    )
    pair_filter = set(pair_runs) or None
    _, cases_by_pair = _load_dataset_cases(dataset_path, pair_filter=pair_filter)
    return pair_runs, cases_by_pair


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep rulegen parameters over labeled benchmark cases and rank settings by objective score."
        )
    )
    parser.add_argument(
        "--preset-file",
        type=Path,
        default=DEFAULT_PRESET_PATH,
        help="Path to benchmark preset registry JSON.",
    )
    parser.add_argument(
        "--preset",
        help="Optional named benchmark preset from the preset registry.",
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List available benchmark presets and exit.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases.json",
        help="Path to benchmark dataset JSON.",
    )
    parser.add_argument(
        "--pairs",
        help="Optional comma-separated pair filter (default: all pairs present in dataset).",
    )
    parser.add_argument(
        "--profile-id", default="default", help="SRS profile id for word_package hints."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        help="Override LexiShift data root (default: platform data dir or LEXISHIFT_DATA_DIR).",
    )
    parser.add_argument(
        "--word-package-snapshot-json",
        type=Path,
        help=(
            "Optional frozen per-pair word_package snapshot JSON. When provided for a pair, "
            "the benchmark uses it instead of the live SRS store for that pair."
        ),
    )
    parser.add_argument("--jmdict", type=Path, help="Optional JMdict override path.")
    parser.add_argument(
        "--translation-dict-en-de",
        "--freedict-en-de",
        dest="translation_dict_en_de",
        type=Path,
        help="Optional translation-dictionary override for en-de pair (deu-eng.tei / sqlite).",
    )
    parser.add_argument(
        "--translation-dict-en-es",
        "--freedict-en-es",
        dest="translation_dict_en_es",
        type=Path,
        help=(
            "Optional translation-dictionary override for en-es pair "
            "(wiktionary-es-en.sqlite / spa-eng.tei / sqlite)."
        ),
    )
    parser.add_argument(
        "--translation-dict-es-en",
        "--freedict-es-en",
        dest="translation_dict_es_en",
        type=Path,
        help="Optional translation-dictionary override for es-en pair (eng-spa.tei / sqlite).",
    )
    parser.add_argument("--max-definitions-values", default="3")
    parser.add_argument("--max-rules-values", default="none")
    parser.add_argument("--confidence-threshold-values", default="0.0")
    parser.add_argument("--semantic-demotion-scale-values", default="1.0")
    parser.add_argument("--include-variants-values", default="true,false")
    parser.add_argument("--pos-scoring-values", default="true,false")
    parser.add_argument("--pos-exact-values", default="1.0")
    parser.add_argument("--pos-compatible-values", default="0.5")
    parser.add_argument("--score-weight-dict-values", default="0.6")
    parser.add_argument("--score-weight-frequency-values", default="0.2")
    parser.add_argument("--score-weight-pos-values", default="0.1")
    parser.add_argument("--score-weight-variant-values", default="0.1")
    parser.add_argument("--score-weight-phrase-values", default="0.1")
    parser.add_argument("--score-weight-embedding-values", default="0.2")
    parser.add_argument("--reverse-check-enabled-values", default="false,true")
    parser.add_argument("--reverse-check-match-bonus-values", default="0.2")
    parser.add_argument("--reverse-check-near-bonus-values", default="0.1")
    parser.add_argument("--reverse-check-near-rank-max-values", default="2")
    parser.add_argument("--reverse-check-far-hit-penalty-values", default="0.0")
    parser.add_argument("--reverse-check-miss-penalty-values", default="0.2")
    parser.add_argument("--reverse-check-exact-hit-ambiguity-threshold-values", default="0")
    parser.add_argument("--reverse-check-exact-hit-ambiguity-penalty-values", default="0.0")
    parser.add_argument(
        "--reverse-check-exact-hit-specificity-bonus-values",
        default="0.0,0.1,0.2",
    )
    parser.add_argument("--kaikki-policy-live-demotion-values", default="false,true")
    parser.add_argument(
        "--kaikki-policy-risk-family-sets",
        default=(
            "math_geometry+government_law+hunting_fishing_tools+"
            "register_region+abbreviation_ellipsis_formof"
        ),
    )
    parser.add_argument(
        "--kaikki-policy-late-sense-penalty-values",
        default="0.0,0.1,0.2",
    )
    parser.add_argument("--objective-top1-weight", type=float, default=100.0)
    parser.add_argument("--objective-top3-weight", type=float, default=60.0)
    parser.add_argument("--objective-forbidden-top1-weight", type=float, default=120.0)
    parser.add_argument("--objective-forbidden-any-weight", type=float, default=80.0)
    parser.add_argument("--objective-avg-rules-weight", type=float, default=6.0)
    parser.add_argument("--objective-variant-top1-weight", type=float, default=10.0)
    parser.add_argument(
        "--max-configurations",
        type=int,
        default=500,
        help="Safety cap for number of sweep combinations per pair.",
    )
    parser.add_argument("--top-runs", type=int, default=10, help="Top-N runs per pair in markdown.")
    parser.add_argument(
        "--include-case-results",
        action="store_true",
        help="Include per-case rule outputs for every run in JSON output.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_latest.json",
        help="Path to write JSON report.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_latest.md",
        help="Path to write markdown leaderboard.",
    )
    parser.add_argument(
        "--html-output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_latest.html",
        help="Path to write styled HTML dashboard.",
    )
    parser.add_argument(
        "--timing-json-output",
        type=Path,
        help="Optional path to write benchmark timing breakdown JSON.",
    )
    parser.add_argument(
        "--compute-only",
        action="store_true",
        help="Write JSON compute output only and skip markdown/HTML materialization.",
    )
    parser.add_argument(
        "--render-from-json",
        type=Path,
        help="Load an existing benchmark JSON report and render markdown/HTML without rerunning the sweep.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Number of worker processes to use for config execution (default: 1).",
    )
    return parser


def _resolve_cli_with_preset(
    *,
    argv: Sequence[str],
) -> tuple[argparse.Namespace, Optional[BenchmarkPreset]]:
    parser = _build_parser()
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--preset-file", type=Path, default=DEFAULT_PRESET_PATH)
    pre_parser.add_argument("--preset")
    pre_parser.add_argument("--list-presets", action="store_true")
    pre_args, remaining_argv = pre_parser.parse_known_args(list(argv))
    preset_file = Path(pre_args.preset_file)
    presets = load_benchmark_presets(preset_file)
    if pre_args.list_presets:
        print(format_benchmark_presets_listing(presets))
        raise SystemExit(0)
    selected_preset: Optional[BenchmarkPreset] = None
    effective_argv = list(remaining_argv)
    preset_name = str(pre_args.preset or "").strip()
    if preset_name:
        selected_preset = presets.get(preset_name)
        if selected_preset is None:
            available = ", ".join(sorted(presets))
            raise ValueError(
                f"Unknown preset `{preset_name}` in {preset_file}. Available: {available}"
            )
        effective_argv = list(selected_preset.args) + effective_argv
    args = parser.parse_args(effective_argv)
    args.preset_file = preset_file
    args.preset = selected_preset.name if selected_preset is not None else None
    args.list_presets = False
    return args, selected_preset


def main(argv: Optional[Sequence[str]] = None) -> None:
    wall_clock_started = perf_counter()
    timing = BenchmarkTimingCollector()
    args, selected_preset = _resolve_cli_with_preset(
        argv=tuple(argv) if argv is not None else tuple(sys.argv[1:])
    )
    if args.compute_only and args.render_from_json is not None:
        raise ValueError("--compute-only and --render-from-json cannot be combined.")

    if args.render_from_json is not None:
        started = perf_counter()
        report_payload = _load_json_object(args.render_from_json)
        timing.add("load_report_json", perf_counter() - started)
        started = perf_counter()
        pair_runs, cases_by_pair = _load_render_inputs_from_report_payload(report_payload)
        timing.add("load_render_inputs", perf_counter() - started)
        markdown_report, html_report, timing_payload = _render_report_artifacts(
            report_payload=report_payload,
            pair_runs=pair_runs,
            cases_by_pair=cases_by_pair,
            top_n=max(1, int(args.top_runs)),
            timing=timing,
            wall_clock_started=wall_clock_started,
        )
        _write_benchmark_outputs(
            report_payload=report_payload,
            markdown_report=markdown_report,
            html_report=html_report,
            json_output=None,
            markdown_output=args.markdown_output,
            html_output=args.html_output,
            timing_payload=timing_payload,
            timing_json_output=args.timing_json_output,
        )
        print(f"source_json: {args.render_from_json}")
        print(f"markdown_output: {args.markdown_output}")
        print(f"html_output: {args.html_output}")
        if args.timing_json_output is not None:
            print(f"timing_json_output: {args.timing_json_output}")
        return

    pair_filter = (
        {item.strip().lower() for item in _parse_csv_strings(args.pairs)} if args.pairs else None
    )
    started = perf_counter()
    dataset_payload, cases_by_pair = _load_dataset_cases(args.dataset, pair_filter=pair_filter)
    timing.add("load_dataset", perf_counter() - started)
    if not cases_by_pair:
        raise ValueError("No benchmark cases found after applying filters.")

    started = perf_counter()
    sweep_configs = _build_sweep_configs(args)
    timing.add("build_sweep_configs", perf_counter() - started)
    if len(sweep_configs) > max(1, int(args.max_configurations)):
        raise ValueError(
            f"Sweep combinations={len(sweep_configs)} exceed --max-configurations={args.max_configurations}."
        )

    objective_weights = RulegenBenchmarkObjectiveWeights(
        top1_accuracy=float(args.objective_top1_weight),
        top3_recall=float(args.objective_top3_weight),
        forbidden_top1_rate=float(args.objective_forbidden_top1_weight),
        forbidden_any_rate=float(args.objective_forbidden_any_weight),
        avg_rules_per_target=float(args.objective_avg_rules_weight),
        variant_top1_rate=float(args.objective_variant_top1_weight),
    )

    started = perf_counter()
    paths = build_helper_paths(args.data_root)
    store = _load_store(paths, profile_id=args.profile_id)
    timing.add("load_store", perf_counter() - started)
    frozen_word_package_snapshots = (
        _load_frozen_word_package_snapshots(args.word_package_snapshot_json)
        if args.word_package_snapshot_json is not None
        else {}
    )

    translation_dict_overrides: dict[str, Optional[Path]] = {
        "en-de": args.translation_dict_en_de,
        "en-es": args.translation_dict_en_es,
        "es-en": args.translation_dict_es_en,
    }
    reverse_translation_dict_overrides: dict[str, Optional[Path]] = {
        "en-es": args.translation_dict_es_en,
        "es-en": args.translation_dict_en_es,
    }

    pair_runs: dict[str, list[SweepRun]] = {}
    pair_resources: dict[str, dict[str, object]] = {}
    pair_word_package_snapshots: dict[str, dict[str, object]] = {}
    for pair, cases in sorted(cases_by_pair.items()):
        capability = resolve_pair_capability(pair)
        if capability.rulegen_mode is None:
            continue
        context = _build_pair_benchmark_context(
            paths=paths,
            store=store,
            pair=pair,
            cases=cases,
            jmdict_override=args.jmdict,
            translation_dict_override=translation_dict_overrides.get(pair),
            reverse_translation_dict_override=reverse_translation_dict_overrides.get(pair),
            frozen_word_package_snapshots=frozen_word_package_snapshots,
            timing=timing,
        )
        pair_resources[pair] = dict(context.resources)
        pair_word_package_snapshots[pair] = dict(context.word_package_snapshot)

        pair_run_list = _run_pair_sweep(
            context=context,
            sweep_configs=sweep_configs,
            objective_weights=objective_weights,
            jobs=args.jobs,
            timing=timing,
            materialize_case_results=args.include_case_results,
        )
        pair_runs[pair] = pair_run_list

    timing_payload = timing.to_dict(wall_clock_seconds=perf_counter() - wall_clock_started)
    report_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(args.dataset),
        "dataset_metadata": {
            key: value for key, value in dataset_payload.items() if key != "cases"
        },
        "profile_id": str(args.profile_id),
        "data_root": str(paths.data_root),
        "sweep": {
            "pair_filter": sorted(pair_filter) if pair_filter else None,
            "configuration_count": len(sweep_configs),
            "jobs": max(1, int(args.jobs)),
            "word_package_snapshot_json": (
                str(args.word_package_snapshot_json)
                if args.word_package_snapshot_json is not None
                else None
            ),
            "preset": (
                {
                    "name": selected_preset.name,
                    "description": selected_preset.description,
                    "preset_file": str(args.preset_file),
                    "args": list(selected_preset.args),
                }
                if selected_preset is not None
                else None
            ),
            "objective_weights": {
                "top1_accuracy": objective_weights.top1_accuracy,
                "top3_recall": objective_weights.top3_recall,
                "forbidden_top1_rate": objective_weights.forbidden_top1_rate,
                "forbidden_any_rate": objective_weights.forbidden_any_rate,
                "avg_rules_per_target": objective_weights.avg_rules_per_target,
                "variant_top1_rate": objective_weights.variant_top1_rate,
            },
        },
        "resources": pair_resources,
        "timing": timing_payload,
        "pairs": {},
    }

    for pair, runs in sorted(pair_runs.items()):
        report_payload["pairs"][pair] = _build_pair_report_payload(
            case_count=len(cases_by_pair.get(pair, ())),
            runs=runs,
            resources=pair_resources.get(pair, {}),
            word_package_snapshot=pair_word_package_snapshots.get(pair, {}),
            include_case_results=args.include_case_results,
        )

    timing_payload = timing.to_dict(wall_clock_seconds=perf_counter() - wall_clock_started)
    report_payload["timing"] = timing_payload
    markdown_report: Optional[str] = None
    html_report: Optional[str] = None
    if not args.compute_only:
        markdown_report, html_report, timing_payload = _render_report_artifacts(
            report_payload=report_payload,
            pair_runs=pair_runs,
            cases_by_pair=cases_by_pair,
            top_n=max(1, int(args.top_runs)),
            timing=timing,
            wall_clock_started=wall_clock_started,
        )
    _write_benchmark_outputs(
        report_payload=report_payload,
        markdown_report=markdown_report,
        html_report=html_report,
        json_output=args.json_output,
        markdown_output=(None if args.compute_only else args.markdown_output),
        html_output=(None if args.compute_only else args.html_output),
        timing_payload=timing_payload,
        timing_json_output=args.timing_json_output,
    )

    print(f"pairs: {len(pair_runs)}")
    print(f"configs_per_pair: {len(sweep_configs)}")
    print(f"json_output: {args.json_output}")
    if args.compute_only:
        print("materialization: skipped (--compute-only)")
    else:
        print(f"markdown_output: {args.markdown_output}")
        print(f"html_output: {args.html_output}")
    if args.timing_json_output is not None:
        print(f"timing_json_output: {args.timing_json_output}")
    for pair, runs in sorted(pair_runs.items()):
        if not runs:
            continue
        best = runs[0]
        summary = best.summary
        print(
            f"[{pair}] best objective={summary.objective_score:.3f} "
            f"top1={summary.top1_accuracy:.2%} "
            f"top3={summary.top3_recall:.2%} "
            f"forbid_top1={summary.forbidden_top1_rate:.2%} "
            f"config={best.config.label()}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
