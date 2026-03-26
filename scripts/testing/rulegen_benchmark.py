#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import itertools
import json
from pathlib import Path
import sys
from typing import Mapping, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_freedict_reverse_path,
    resolve_pair_capability,
)
from lexishift_core.helper.pair_resources import resolve_pair_resources  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.lexicon.word_package import build_word_package  # noqa: E402
from lexishift_core.replacement.core import VocabRule  # noqa: E402
from lexishift_core.rulegen.adapters import (  # noqa: E402
    RulegenAdapterRequest,
    run_rules_with_adapter,
)
from lexishift_core.rulegen.benchmarking import (  # noqa: E402
    RulegenBenchmarkCase,
    RulegenBenchmarkObjectiveWeights,
    RulegenBenchmarkSummary,
    evaluate_benchmark_case,
    summarize_benchmark_results,
)
from lexishift_core.rulegen.generation import (  # noqa: E402
    PosMatchScoringConfig,
    RuleScoreWeights,
    RuleScoringConfig,
)
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig  # noqa: E402
from lexishift_core.srs import SrsStore, load_srs_store  # noqa: E402


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
            f"w_pos={self.score_weight_pos_match:.3f} "
            f"kdem={'on' if self.kaikki_policy_live_demotion else 'off'} "
            f"kfam={_format_kaikki_policy_family_label(self.kaikki_policy_risk_families)}"
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


def _build_pair_report_payload(
    *,
    case_count: int,
    runs: Sequence[SweepRun],
    resources: Mapping[str, Optional[str]],
    include_case_results: bool,
) -> dict[str, object]:
    return {
        "case_count": int(case_count),
        "run_count": len(runs),
        "resources": dict(resources),
        "best_run": runs[0].to_dict(include_case_results=True) if runs else None,
        "runs": [run.to_dict(include_case_results=include_case_results) for run in runs],
    }


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
    kaikki_policy_live_demotion_values = _parse_csv_bools(
        args.kaikki_policy_live_demotion_values,
        name="kaikki-policy-live-demotion-values",
    )
    kaikki_policy_risk_family_sets = _parse_family_set_specs(
        args.kaikki_policy_risk_family_sets,
        name="kaikki-policy-risk-family-sets",
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep rulegen parameters over labeled benchmark cases and rank settings by objective score."
        )
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
    parser.add_argument("--kaikki-policy-live-demotion-values", default="false,true")
    parser.add_argument(
        "--kaikki-policy-risk-family-sets",
        default=(
            "math_geometry+government_law+hunting_fishing_tools+"
            "register_region+abbreviation_ellipsis_formof"
        ),
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
    args = parser.parse_args()

    pair_filter = (
        {item.strip().lower() for item in _parse_csv_strings(args.pairs)} if args.pairs else None
    )
    dataset_payload, cases_by_pair = _load_dataset_cases(args.dataset, pair_filter=pair_filter)
    if not cases_by_pair:
        raise ValueError("No benchmark cases found after applying filters.")

    sweep_configs = _build_sweep_configs(args)
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

    paths = build_helper_paths(args.data_root)
    store = _load_store(paths, profile_id=args.profile_id)

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
    pair_resources: dict[str, dict[str, Optional[str]]] = {}
    for pair, cases in sorted(cases_by_pair.items()):
        capability = resolve_pair_capability(pair)
        if capability.rulegen_mode is None:
            continue
        jmdict_path, freedict_path, reverse_freedict_path = _resolve_pair_resources_for_benchmark(
            paths=paths,
            pair=pair,
            jmdict_override=args.jmdict,
            freedict_override=translation_dict_overrides.get(pair),
            freedict_reverse_override=reverse_translation_dict_overrides.get(pair),
        )
        pair_resources[pair] = {
            "jmdict_path": str(jmdict_path) if jmdict_path else None,
            "translation_dict_path": str(freedict_path) if freedict_path else None,
            "reverse_translation_dict_path": (
                str(reverse_freedict_path) if reverse_freedict_path else None
            ),
            "freedict_path": str(freedict_path) if freedict_path else None,
            "freedict_reverse_path": str(reverse_freedict_path) if reverse_freedict_path else None,
        }

        target_set = {case.target for case in cases}
        targets = sorted(target_set)
        word_packages = _build_store_word_packages(store=store, pair=pair, targets=target_set)
        _apply_case_word_package_overrides(package_map=word_packages, pair=pair, cases=cases)

        pair_run_list: list[SweepRun] = []
        for index, config in enumerate(sweep_configs, start=1):
            rules = run_rules_with_adapter(
                RulegenAdapterRequest(
                    pair=pair,
                    targets=tuple(targets),
                    language_pair=pair,
                    confidence_threshold=config.confidence_threshold,
                    max_definitions_per_target=config.max_definitions_per_target,
                    max_rules_per_target=config.max_rules_per_target,
                    semantic_demotion_scale=config.semantic_demotion_scale,
                    include_variants=config.include_variants,
                    scoring=config.scoring(),
                    reverse_check=config.reverse_check(),
                    jmdict_path=jmdict_path,
                    freedict_de_en_path=freedict_path,
                    freedict_reverse_path=reverse_freedict_path,
                    word_packages_by_target=word_packages,
                    kaikki_policy_live_demotion=config.kaikki_policy_live_demotion,
                    kaikki_policy_risk_families=config.kaikki_policy_risk_families,
                )
            )
            rules_by_target = _group_rules_by_target(rules)
            case_results = [
                evaluate_benchmark_case(case, tuple(rules_by_target.get(case.target, ())))
                for case in cases
            ]
            summary = summarize_benchmark_results(
                pair=pair,
                case_results=case_results,
                objective_weights=objective_weights,
            )
            pair_run_list.append(
                SweepRun(
                    pair=pair,
                    run_index=index,
                    config=config,
                    summary=summary,
                    case_results=tuple(result.to_dict() for result in case_results),
                )
            )
        pair_run_list.sort(key=_run_sort_key)
        pair_runs[pair] = pair_run_list

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
        "pairs": {},
    }

    for pair, runs in sorted(pair_runs.items()):
        report_payload["pairs"][pair] = _build_pair_report_payload(
            case_count=len(cases_by_pair.get(pair, ())),
            runs=runs,
            resources=pair_resources.get(pair, {}),
            include_case_results=args.include_case_results,
        )

    top_runs = max(1, int(args.top_runs))
    markdown_report = _render_markdown_report(pair_runs=pair_runs, top_n=top_runs)
    html_report = _load_html_report_renderer()(
        report_payload=report_payload,
        pair_runs=pair_runs,
        cases_by_pair=cases_by_pair,
        top_n=top_runs,
    )

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(markdown_report, encoding="utf-8")
    args.html_output.parent.mkdir(parents=True, exist_ok=True)
    args.html_output.write_text(html_report, encoding="utf-8")

    print(f"pairs: {len(pair_runs)}")
    print(f"configs_per_pair: {len(sweep_configs)}")
    print(f"json_output: {args.json_output}")
    print(f"markdown_output: {args.markdown_output}")
    print(f"html_output: {args.html_output}")
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
