#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import html
import itertools
import json
from pathlib import Path
import sys
from typing import Iterable, Mapping, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.helper.lp_capabilities import resolve_pair_capability  # noqa: E402
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
            f"w_pos={self.score_weight_pos_match:.3f}"
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
) -> tuple[Optional[Path], Optional[Path]]:
    jmdict_path, freedict_path, _ = resolve_pair_resources(
        paths,
        pair=pair,
        jmdict_path=jmdict_override,
        freedict_de_en_path=freedict_override,
        set_source_db=None,
    )
    capability = resolve_pair_capability(pair)
    if capability.requires_jmdict_for_rulegen:
        if jmdict_path is None or not jmdict_path.exists():
            raise FileNotFoundError(f"JMDict path not found for pair {pair}: {jmdict_path}")
    if capability.requires_freedict_de_en_for_rulegen:
        if freedict_path is None or not freedict_path.exists():
            raise FileNotFoundError(f"FreeDict path not found for pair {pair}: {freedict_path}")
    return jmdict_path, freedict_path


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


def _escape_html(value: object) -> str:
    return html.escape(str(value), quote=True)


def _format_percent(value: float) -> str:
    return f"{float(value) * 100.0:.1f}%"


def _format_optional_float(value: object, *, digits: int = 3) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _render_html_report(
    *,
    report_payload: Mapping[str, object],
    pair_runs: Mapping[str, Sequence[SweepRun]],
    cases_by_pair: Mapping[str, Sequence[RulegenBenchmarkCase]],
    top_n: int,
) -> str:
    generated_at = _escape_html(report_payload.get("generated_at", ""))
    profile_id = _escape_html(report_payload.get("profile_id", ""))
    data_root = _escape_html(report_payload.get("data_root", ""))
    dataset_path = _escape_html(report_payload.get("dataset_path", ""))
    sweep_payload = report_payload.get("sweep")
    configuration_count = "-"
    if isinstance(sweep_payload, Mapping):
        configuration_count = _escape_html(sweep_payload.get("configuration_count", "-"))

    pair_sections: list[str] = []
    for pair, runs in sorted(pair_runs.items()):
        if not runs:
            continue
        pair_html = _escape_html(pair)
        pair_cases = tuple(cases_by_pair.get(pair, ()))
        pair_case_by_id = {case.case_id: case for case in pair_cases}
        pair_case_by_target = {case.target: case for case in pair_cases}
        best_run = runs[0]
        best_summary = best_run.summary

        top_rows: list[str] = []
        for rank, run in enumerate(runs[:max(1, int(top_n))], start=1):
            summary = run.summary
            top_rows.append(
                "<tr>"
                f"<td>{rank}</td>"
                f"<td>{summary.objective_score:.3f}</td>"
                f"<td>{_format_percent(summary.top1_accuracy)}</td>"
                f"<td>{_format_percent(summary.top3_recall)}</td>"
                f"<td>{_format_percent(summary.forbidden_top1_rate)}</td>"
                f"<td>{_format_percent(summary.forbidden_any_rate)}</td>"
                f"<td>{summary.avg_rules_per_target:.2f}</td>"
                f"<td><code>{_escape_html(run.config.label())}</code></td>"
                "</tr>"
            )

        case_rows: list[str] = []
        for case_result in best_run.case_results:
            target_raw = str(case_result.get("target", "") or "").strip()
            target_html = _escape_html(target_raw)
            case_id_raw = str(case_result.get("case_id", "") or "").strip()
            case_id_html = _escape_html(case_id_raw)
            case_def = pair_case_by_id.get(case_id_raw) or pair_case_by_target.get(target_raw)
            known_green: set[str] = set()
            known_black: set[str] = set()
            if case_def is not None:
                known_green.update(case_def.expected_any)
                known_green.update(case_def.expected_top1_any)
                known_black.update(case_def.forbidden_top1)
                known_black.update(case_def.forbidden_any)

            all_sources_raw = case_result.get("all_sources")
            all_sources: list[str] = []
            if isinstance(all_sources_raw, Sequence) and not isinstance(all_sources_raw, (str, bytes)):
                all_sources = _dedupe_preserve_order(
                    str(item or "").strip()
                    for item in all_sources_raw
                )

            source_chips: list[str] = []
            for source in all_sources:
                source_html = _escape_html(source)
                if source in known_black:
                    base_label = "black"
                    chip_class = "chip-black"
                elif source in known_green:
                    base_label = "green"
                    chip_class = "chip-green"
                else:
                    base_label = "neutral"
                    chip_class = "chip-neutral"
                source_chips.append(
                    "<button type=\"button\" class=\"source-chip "
                    f"{chip_class}\" "
                    f"data-pair=\"{pair_html}\" "
                    f"data-case-id=\"{case_id_html}\" "
                    f"data-target=\"{target_html}\" "
                    f"data-phrase=\"{source_html}\" "
                    f"data-base-label=\"{base_label}\" "
                    f"data-current-label=\"{base_label}\" "
                    "title=\"Right-click to label\">"
                    f"{source_html}</button>"
                )
            all_sources_html = "".join(source_chips) if source_chips else "<span class=\"text-muted\">-</span>"
            label_hint = _escape_html(f"G:{len(known_green)} / B:{len(known_black)}")

            top1_source = _escape_html(case_result.get("top1_source", "-") or "-")
            top1_conf = _format_optional_float(case_result.get("top1_confidence"), digits=4)
            top3_sources_raw = case_result.get("top3_sources")
            if isinstance(top3_sources_raw, Sequence) and not isinstance(top3_sources_raw, (str, bytes)):
                top3_sources = ", ".join(_escape_html(item) for item in top3_sources_raw) or "-"
            else:
                top3_sources = "-"

            top1_correct = bool(case_result.get("top1_correct", False))
            top3_contains = bool(case_result.get("top3_contains_expected", False))
            top1_forbidden = bool(case_result.get("top1_forbidden", False))
            forbidden_any = bool(case_result.get("forbidden_any_present", False))
            variant_count = int(case_result.get("variant_rule_count", 0) or 0)
            rule_count = int(case_result.get("rule_count", 0) or 0)
            if top1_correct and not top1_forbidden and not forbidden_any:
                status_class = "status-ok"
                status_text = "PASS"
            elif top3_contains and not top1_forbidden:
                status_class = "status-warn"
                status_text = "REVIEW"
            else:
                status_class = "status-bad"
                status_text = "FAIL"
            case_rows.append(
                "<tr>"
                f"<td><span class=\"status-pill {status_class}\">{status_text}</span></td>"
                f"<td><code>{case_id_html}</code></td>"
                f"<td>{target_html}</td>"
                f"<td>{top1_source}</td>"
                f"<td>{top1_conf}</td>"
                f"<td>{top3_sources}</td>"
                f"<td class=\"source-cell\">{all_sources_html}</td>"
                f"<td><span class=\"label-hint\">{label_hint}</span></td>"
                f"<td>{'yes' if top1_correct else 'no'}</td>"
                f"<td>{'yes' if top3_contains else 'no'}</td>"
                f"<td>{'yes' if top1_forbidden else 'no'}</td>"
                f"<td>{'yes' if forbidden_any else 'no'}</td>"
                f"<td>{rule_count}</td>"
                f"<td>{variant_count}</td>"
                "</tr>"
            )

        pair_sections.append(
            f"<section class=\"pair-section\" data-pair=\"{pair_html}\">"
            f"<div class=\"pair-head\"><h2>{pair_html}</h2>"
            f"<p>best objective <strong>{best_summary.objective_score:.3f}</strong> "
            f"| top1 {_format_percent(best_summary.top1_accuracy)} "
            f"| top3 {_format_percent(best_summary.top3_recall)}</p></div>"
            "<div class=\"metric-grid\">"
            f"<article class=\"metric-card\"><h3>Top1</h3><p>{_format_percent(best_summary.top1_accuracy)}</p></article>"
            f"<article class=\"metric-card\"><h3>Top3</h3><p>{_format_percent(best_summary.top3_recall)}</p></article>"
            f"<article class=\"metric-card\"><h3>Forbidden Top1</h3><p>{_format_percent(best_summary.forbidden_top1_rate)}</p></article>"
            f"<article class=\"metric-card\"><h3>Forbidden Any</h3><p>{_format_percent(best_summary.forbidden_any_rate)}</p></article>"
            f"<article class=\"metric-card\"><h3>Avg Rules</h3><p>{best_summary.avg_rules_per_target:.2f}</p></article>"
            f"<article class=\"metric-card\"><h3>Variant Top1</h3><p>{_format_percent(best_summary.variant_top1_rate)}</p></article>"
            "</div>"
            "<details open>"
            "<summary>Leaderboard</summary>"
            "<div class=\"table-wrap\"><table><thead><tr>"
            "<th>Rank</th><th>Objective</th><th>Top1</th><th>Top3</th><th>Forbidden Top1</th>"
            "<th>Forbidden Any</th><th>Avg Rules</th><th>Config</th>"
            "</tr></thead><tbody>"
            + "".join(top_rows)
            + "</tbody></table></div>"
            "</details>"
            "<details>"
            "<summary>Best Run Case Diagnostics + Labeling</summary>"
            "<div class=\"table-wrap\"><table><thead><tr>"
            "<th>Status</th><th>Case</th><th>Target</th><th>Top1 Source</th><th>Top1 Conf</th><th>Top3 Sources</th>"
            "<th>All Sources (right-click chips)</th><th>Known Labels</th>"
            "<th>Top1 Correct</th><th>Top3 Hit</th><th>Top1 Forbidden</th><th>Forbidden Any</th>"
            "<th>Rules</th><th>Variants</th>"
            "</tr></thead><tbody>"
            + "".join(case_rows)
            + "</tbody></table></div>"
            "</details>"
            "</section>"
        )

    label_script = """
<script>
const DATASET_PATH = __DATASET_PATH__;
const REPORT_GENERATED_AT = __REPORT_GENERATED_AT__;
const STORAGE_KEY = 'lexishift_rulegen_label_workbench_v1';
const WORKFLOW_STORAGE_KEY = 'lexishift_rulegen_lp_workflow_v1';

const chips = Array.from(document.querySelectorAll('.source-chip'));
const pairSections = Array.from(document.querySelectorAll('.pair-section[data-pair]'));
const pairOrder = pairSections
  .map((section) => section.dataset.pair || '')
  .filter((pair, index, arr) => pair && arr.indexOf(pair) === index);

const menu = document.getElementById('label-menu');
const labelCountEl = document.getElementById('label-count');
const downloadBtn = document.getElementById('download-labels');
const copyBtn = document.getElementById('copy-labels');
const clearBtn = document.getElementById('clear-labels');

const pairStateEl = document.getElementById('pair-workflow-state');
const pairNavListEl = document.getElementById('pair-nav-list');
const prevPairBtn = document.getElementById('prev-pair');
const nextPairBtn = document.getElementById('next-pair');
const markDoneBtn = document.getElementById('mark-pair-done');
const skipPairBtn = document.getElementById('skip-pair');
const resetPairStatusBtn = document.getElementById('reset-pair-status');
const showAllPairsToggle = document.getElementById('show-all-pairs');

let activeChip = null;

function emptyState() {
  return { cases: {} };
}

function normalizeLabel(value) {
  if (value === 'green' || value === 'black' || value === 'neutral') {
    return value;
  }
  return 'neutral';
}

function caseKey(pair, caseId, target) {
  return [pair || '', caseId || '', target || ''].join('|||');
}

function loadState() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyState();
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || !parsed.cases || typeof parsed.cases !== 'object') {
      return emptyState();
    }
    return parsed;
  } catch (error) {
    return emptyState();
  }
}

function emptyWorkflowState() {
  return {
    current_pair: pairOrder[0] || '',
    statuses: {},
    show_all_pairs: false,
  };
}

function normalizePairStatus(value) {
  if (value === 'done' || value === 'skipped') return value;
  return 'todo';
}

function loadWorkflowState() {
  try {
    const raw = window.localStorage.getItem(WORKFLOW_STORAGE_KEY);
    if (!raw) return emptyWorkflowState();
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return emptyWorkflowState();
    const statuses = parsed.statuses && typeof parsed.statuses === 'object' ? parsed.statuses : {};
    return {
      current_pair: typeof parsed.current_pair === 'string' ? parsed.current_pair : (pairOrder[0] || ''),
      statuses,
      show_all_pairs: Boolean(parsed.show_all_pairs),
    };
  } catch (error) {
    return emptyWorkflowState();
  }
}

let state = loadState();
let workflowState = loadWorkflowState();
if (!pairOrder.includes(workflowState.current_pair)) {
  workflowState.current_pair = pairOrder[0] || '';
}

function saveState() {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function saveWorkflowState() {
  window.localStorage.setItem(WORKFLOW_STORAGE_KEY, JSON.stringify(workflowState));
}

function ensureCaseBucket(pair, caseId, target) {
  const key = caseKey(pair, caseId, target);
  if (!state.cases[key]) {
    state.cases[key] = {
      pair: pair || '',
      case_id: caseId || '',
      target: target || '',
      decisions: {},
    };
  }
  return state.cases[key];
}

function getDecision(pair, caseId, target, phrase) {
  const key = caseKey(pair, caseId, target);
  const bucket = state.cases[key];
  if (!bucket || !bucket.decisions || typeof bucket.decisions !== 'object') return null;
  if (!(phrase in bucket.decisions)) return null;
  return normalizeLabel(bucket.decisions[phrase]);
}

function getPairStatus(pair) {
  if (!pair || !workflowState.statuses || typeof workflowState.statuses !== 'object') {
    return 'todo';
  }
  return normalizePairStatus(workflowState.statuses[pair]);
}

function setPairStatus(pair, status) {
  if (!pair) return;
  const normalized = normalizePairStatus(status);
  if (!workflowState.statuses || typeof workflowState.statuses !== 'object') {
    workflowState.statuses = {};
  }
  if (normalized === 'todo') {
    delete workflowState.statuses[pair];
  } else {
    workflowState.statuses[pair] = normalized;
  }
  saveWorkflowState();
}

function setCurrentPair(pair, options = {}) {
  if (!pairOrder.includes(pair)) return;
  workflowState.current_pair = pair;
  saveWorkflowState();
  applyPairVisibility(options);
  renderPairWorkflow();
}

function applyChipClasses(chip, label, isManual) {
  chip.classList.remove('chip-green', 'chip-black', 'chip-neutral', 'chip-manual');
  if (label === 'green') chip.classList.add('chip-green');
  else if (label === 'black') chip.classList.add('chip-black');
  else chip.classList.add('chip-neutral');
  if (isManual) chip.classList.add('chip-manual');
  chip.dataset.currentLabel = label;
  chip.title = `Right-click to label (${label})`;
}

function applyChipLabel(chip) {
  const pair = chip.dataset.pair || '';
  const caseId = chip.dataset.caseId || '';
  const target = chip.dataset.target || '';
  const phrase = chip.dataset.phrase || '';
  const baseLabel = normalizeLabel(chip.dataset.baseLabel || 'neutral');
  const decision = getDecision(pair, caseId, target, phrase);
  const resolved = decision || baseLabel;
  applyChipClasses(chip, resolved, Boolean(decision && decision !== baseLabel));
}

function refreshDecisionCount() {
  const buckets = Object.values(state.cases || {});
  let decisionCount = 0;
  let caseCount = 0;
  for (const bucket of buckets) {
    if (!bucket || !bucket.decisions || typeof bucket.decisions !== 'object') continue;
    const size = Object.keys(bucket.decisions).length;
    if (size > 0) caseCount += 1;
    decisionCount += size;
  }
  if (labelCountEl) {
    labelCountEl.textContent = `${decisionCount} decisions across ${caseCount} cases`;
  }
}

function applyPairVisibility(options = {}) {
  const showAll = Boolean(workflowState.show_all_pairs);
  pairSections.forEach((section) => {
    const pair = section.dataset.pair || '';
    section.hidden = !showAll && pair !== workflowState.current_pair;
  });
  const shouldScroll = options.scroll !== false;
  if (!showAll && shouldScroll) {
    const active = pairSections.find((section) => (section.dataset.pair || '') === workflowState.current_pair);
    if (active) {
      active.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}

function renderPairWorkflow() {
  if (!pairOrder.length) {
    if (pairStateEl) pairStateEl.textContent = 'No LP sections in this report';
    return;
  }

  if (!pairOrder.includes(workflowState.current_pair)) {
    workflowState.current_pair = pairOrder[0];
    saveWorkflowState();
  }

  const currentIndex = pairOrder.indexOf(workflowState.current_pair);
  const doneCount = pairOrder.filter((pair) => getPairStatus(pair) === 'done').length;
  const skippedCount = pairOrder.filter((pair) => getPairStatus(pair) === 'skipped').length;
  const todoCount = pairOrder.length - doneCount - skippedCount;

  if (pairStateEl) {
    pairStateEl.textContent = `LP ${currentIndex + 1}/${pairOrder.length}: ${workflowState.current_pair} | todo ${todoCount} done ${doneCount} skipped ${skippedCount}`;
  }

  if (pairNavListEl) {
    pairNavListEl.innerHTML = '';
    pairOrder.forEach((pair) => {
      const status = getPairStatus(pair);
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `pair-chip status-${status}${pair === workflowState.current_pair ? ' active' : ''}`;
      button.textContent = `${pair} (${status})`;
      button.addEventListener('click', () => {
        setCurrentPair(pair);
      });
      pairNavListEl.appendChild(button);
    });
  }

  if (prevPairBtn) prevPairBtn.disabled = currentIndex <= 0;
  if (nextPairBtn) nextPairBtn.disabled = currentIndex >= (pairOrder.length - 1);
  if (markDoneBtn) markDoneBtn.disabled = !workflowState.current_pair;
  if (skipPairBtn) skipPairBtn.disabled = !workflowState.current_pair;
  if (resetPairStatusBtn) resetPairStatusBtn.disabled = !workflowState.current_pair;
}

function moveRelativePair(offset) {
  if (!pairOrder.length) return;
  const index = pairOrder.indexOf(workflowState.current_pair);
  if (index < 0) return;
  const targetIndex = index + offset;
  if (targetIndex < 0 || targetIndex >= pairOrder.length) return;
  setCurrentPair(pairOrder[targetIndex]);
}

function findNextTodoIndex(afterIndex) {
  for (let i = afterIndex + 1; i < pairOrder.length; i += 1) {
    if (getPairStatus(pairOrder[i]) === 'todo') return i;
  }
  for (let i = 0; i < pairOrder.length; i += 1) {
    if (getPairStatus(pairOrder[i]) === 'todo') return i;
  }
  return -1;
}

function markCurrentPairAndAdvance(status) {
  if (!workflowState.current_pair) return;
  const currentIndex = pairOrder.indexOf(workflowState.current_pair);
  setPairStatus(workflowState.current_pair, status);
  const nextTodo = findNextTodoIndex(currentIndex);
  if (nextTodo >= 0) {
    setCurrentPair(pairOrder[nextTodo]);
    return;
  }
  if (currentIndex >= 0 && currentIndex < pairOrder.length - 1) {
    setCurrentPair(pairOrder[currentIndex + 1]);
    return;
  }
  renderPairWorkflow();
  applyPairVisibility({ scroll: false });
}

function setLabelForChip(chip, label) {
  const pair = chip.dataset.pair || '';
  const caseId = chip.dataset.caseId || '';
  const target = chip.dataset.target || '';
  const phrase = chip.dataset.phrase || '';
  const baseLabel = normalizeLabel(chip.dataset.baseLabel || 'neutral');
  const normalizedLabel = normalizeLabel(label);
  const key = caseKey(pair, caseId, target);
  const bucket = ensureCaseBucket(pair, caseId, target);
  if (normalizedLabel === baseLabel) {
    delete bucket.decisions[phrase];
  } else {
    bucket.decisions[phrase] = normalizedLabel;
  }
  if (Object.keys(bucket.decisions).length === 0) {
    delete state.cases[key];
  }
  applyChipLabel(chip);
  saveState();
  refreshDecisionCount();
}

function hideMenu() {
  if (!menu) return;
  menu.hidden = true;
  activeChip = null;
}

function openMenuForChip(event) {
  if (!menu) return;
  event.preventDefault();
  activeChip = event.currentTarget;
  menu.hidden = false;
  const x = Math.min(event.pageX, window.scrollX + window.innerWidth - 190);
  const y = Math.min(event.pageY, window.scrollY + window.innerHeight - 160);
  menu.style.left = `${x}px`;
  menu.style.top = `${y}px`;
}

function sortedDecisionCases() {
  const entries = Object.values(state.cases || {}).filter((entry) => {
    return entry && entry.decisions && Object.keys(entry.decisions).length > 0;
  });
  entries.sort((a, b) => {
    const left = `${a.pair || ''}::${a.case_id || ''}::${a.target || ''}`;
    const right = `${b.pair || ''}::${b.case_id || ''}::${b.target || ''}`;
    return left.localeCompare(right);
  });
  return entries.map((entry) => {
    const ordered = {};
    Object.keys(entry.decisions || {}).sort().forEach((phrase) => {
      ordered[phrase] = normalizeLabel(entry.decisions[phrase]);
    });
    return {
      pair: entry.pair || '',
      case_id: entry.case_id || '',
      target: entry.target || '',
      decisions: ordered,
    };
  });
}

function exportPayloadText() {
  const payload = {
    labels_version: 1,
    generated_at: new Date().toISOString(),
    source_report_generated_at: REPORT_GENERATED_AT,
    dataset_path: DATASET_PATH,
    cases: sortedDecisionCases(),
  };
  return JSON.stringify(payload, null, 2);
}

function downloadDecisions() {
  const payloadText = exportPayloadText();
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `rulegen_label_overrides_${timestamp}.json`;
  const blob = new Blob([payloadText], { type: 'application/json' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => window.URL.revokeObjectURL(url), 1500);
}

async function copyDecisions() {
  if (!copyBtn) return;
  const original = copyBtn.textContent;
  try {
    await navigator.clipboard.writeText(exportPayloadText());
    copyBtn.textContent = 'Copied';
  } catch (error) {
    copyBtn.textContent = 'Copy failed';
  }
  window.setTimeout(() => {
    copyBtn.textContent = original;
  }, 1500);
}

function clearDecisions() {
  if (!window.confirm('Clear all local label decisions for this report?')) return;
  state = emptyState();
  saveState();
  chips.forEach((chip) => applyChipLabel(chip));
  refreshDecisionCount();
}

if (menu) {
  menu.querySelectorAll('button[data-action]').forEach((button) => {
    button.addEventListener('click', () => {
      if (activeChip) {
        setLabelForChip(activeChip, button.dataset.action || 'neutral');
      }
      hideMenu();
    });
  });
}

chips.forEach((chip) => {
  chip.addEventListener('contextmenu', openMenuForChip);
  applyChipLabel(chip);
});

document.addEventListener('click', (event) => {
  if (!menu || menu.hidden) return;
  if (!menu.contains(event.target)) hideMenu();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') hideMenu();
});

if (showAllPairsToggle) {
  showAllPairsToggle.checked = Boolean(workflowState.show_all_pairs);
  showAllPairsToggle.addEventListener('change', () => {
    workflowState.show_all_pairs = Boolean(showAllPairsToggle.checked);
    saveWorkflowState();
    applyPairVisibility({ scroll: false });
    renderPairWorkflow();
  });
}

if (prevPairBtn) prevPairBtn.addEventListener('click', () => moveRelativePair(-1));
if (nextPairBtn) nextPairBtn.addEventListener('click', () => moveRelativePair(1));
if (markDoneBtn) markDoneBtn.addEventListener('click', () => markCurrentPairAndAdvance('done'));
if (skipPairBtn) skipPairBtn.addEventListener('click', () => markCurrentPairAndAdvance('skipped'));
if (resetPairStatusBtn) {
  resetPairStatusBtn.addEventListener('click', () => {
    if (!workflowState.current_pair) return;
    setPairStatus(workflowState.current_pair, 'todo');
    renderPairWorkflow();
    applyPairVisibility({ scroll: false });
  });
}

window.addEventListener('scroll', hideMenu, true);
if (downloadBtn) downloadBtn.addEventListener('click', downloadDecisions);
if (copyBtn) copyBtn.addEventListener('click', copyDecisions);
if (clearBtn) clearBtn.addEventListener('click', clearDecisions);

refreshDecisionCount();
renderPairWorkflow();
applyPairVisibility({ scroll: false });
</script>
""".replace("__DATASET_PATH__", json.dumps(str(report_payload.get("dataset_path", "")))).replace(
        "__REPORT_GENERATED_AT__", json.dumps(str(report_payload.get("generated_at", "")))
    )

    return "".join(
        [
            "<!doctype html>",
            "<html lang=\"en\">",
            "<head>",
            "<meta charset=\"utf-8\">",
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            "<title>LexiShift Rulegen Benchmark</title>",
            "<style>",
            ":root{",
            "--bg:#f7f4ef;--panel:#ffffff;--text:#162022;--muted:#5d6a6d;",
            "--line:#d8dfdc;--accent:#0f766e;--accent-soft:#d1fae5;",
            "--warn:#b45309;--warn-soft:#fef3c7;--bad:#b91c1c;--bad-soft:#fee2e2;",
            "--ok:#166534;--ok-soft:#dcfce7;--radius:16px;--shadow:0 10px 25px rgba(15,23,42,0.08);",
            "}",
            "*{box-sizing:border-box}",
            "body{margin:0;font-family:'IBM Plex Sans','Avenir Next',sans-serif;color:var(--text);",
            "background:radial-gradient(circle at 15% 0%, #fff9ec 0%, var(--bg) 55%),",
            "linear-gradient(180deg,#f6f7f4 0%,#f3f1ec 100%);}",
            "main{max-width:1320px;margin:0 auto;padding:32px 20px 60px}",
            "header{background:linear-gradient(135deg,#fcfffe 0%,#ecfdf5 100%);border:1px solid var(--line);",
            "border-radius:calc(var(--radius) + 6px);box-shadow:var(--shadow);padding:26px 26px 20px;position:relative;overflow:hidden}",
            "header::after{content:'';position:absolute;right:-24px;top:-24px;width:180px;height:180px;border-radius:50%;",
            "background:radial-gradient(circle,rgba(15,118,110,0.14) 0%,rgba(15,118,110,0) 70%)}",
            "h1{margin:0;font-family:'Fraunces','Iowan Old Style',serif;font-size:clamp(1.6rem,2.8vw,2.3rem);letter-spacing:0.01em}",
            ".meta{margin-top:10px;color:var(--muted);font-size:0.94rem;display:flex;gap:14px;flex-wrap:wrap}",
            ".meta code{background:#eef2f3;border:1px solid #d9e0e2;padding:2px 6px;border-radius:8px}",
            ".label-workbench{margin-top:14px;padding:12px;border:1px solid #c8d7d3;background:#f8fffd;border-radius:12px}",
            ".label-workbench p{margin:0 0 10px;color:#33484c;font-size:0.92rem}",
            ".label-actions{display:flex;flex-wrap:wrap;gap:10px;align-items:center}",
            ".pair-workflow{margin-top:12px;padding:12px;border:1px dashed #b8ccc9;border-radius:12px;background:#f5fbfa}",
            ".pair-workflow-head{display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:space-between}",
            ".pair-workflow-state{font-size:0.9rem;color:#2c4044;font-weight:700}",
            ".pair-workflow-buttons{display:flex;flex-wrap:wrap;gap:8px;align-items:center}",
            ".pair-nav{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}",
            ".pair-chip{border:1px solid #bfd0ce;background:#fff;border-radius:999px;padding:4px 11px;font-size:0.78rem;font-weight:700;color:#1e3236;cursor:pointer}",
            ".pair-chip:hover{background:#eef8f6}",
            ".pair-chip.active{box-shadow:0 0 0 2px rgba(15,23,42,0.18) inset}",
            ".pair-chip.status-done{background:#e8fff2;border-color:#9ad8b6;color:#12502d}",
            ".pair-chip.status-skipped{background:#f5f7fa;border-color:#ccd7df;color:#34434f}",
            ".pair-chip.status-todo{background:#fffdf6;border-color:#e7dbb2;color:#5f4a0a}",
            ".show-all-wrap{display:inline-flex;align-items:center;gap:6px;color:#2f4649;font-size:0.83rem;font-weight:700}",
            ".btn{background:#0f766e;color:#fff;border:1px solid #0f766e;border-radius:10px;padding:7px 11px;font-weight:700;cursor:pointer}",
            ".btn.btn-secondary{background:#fff;color:#0f766e}",
            ".btn:hover{filter:brightness(0.96)}",
            "#label-count{font-weight:700;color:#30484b;font-size:0.88rem}",
            ".pair-section{margin-top:22px;background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);padding:20px}",
            ".pair-head h2{margin:0;font-family:'Fraunces','Iowan Old Style',serif;font-size:1.45rem}",
            ".pair-head p{margin:8px 0 0;color:var(--muted)}",
            ".metric-grid{margin-top:16px;display:grid;grid-template-columns:repeat(6,minmax(140px,1fr));gap:10px}",
            ".metric-card{background:#f8faf9;border:1px solid var(--line);border-radius:12px;padding:10px 12px}",
            ".metric-card h3{margin:0;color:var(--muted);font-size:0.76rem;font-weight:700;letter-spacing:0.04em;text-transform:uppercase}",
            ".metric-card p{margin:8px 0 0;font-size:1.25rem;font-weight:700;color:#0f172a}",
            "details{margin-top:14px;border:1px solid var(--line);border-radius:12px;background:#fcfdfd;overflow:hidden}",
            "summary{cursor:pointer;padding:12px 14px;font-weight:700;background:#f4f8f7}",
            ".table-wrap{overflow:auto}",
            "table{width:100%;border-collapse:collapse;font-size:0.9rem}",
            "th,td{padding:10px 10px;text-align:left;border-bottom:1px solid #ebeff0;vertical-align:top}",
            "th{font-size:0.78rem;text-transform:uppercase;letter-spacing:0.04em;color:#415255;background:#f8fbfa;position:sticky;top:0;z-index:1}",
            "code{font-family:'Source Code Pro','Menlo',monospace;font-size:0.84rem}",
            ".status-pill{display:inline-block;padding:2px 8px;border-radius:999px;font-weight:700;font-size:0.72rem;letter-spacing:0.04em}",
            ".status-ok{background:var(--ok-soft);color:var(--ok)}",
            ".status-warn{background:var(--warn-soft);color:var(--warn)}",
            ".status-bad{background:var(--bad-soft);color:var(--bad)}",
            ".source-cell{min-width:380px;max-width:560px}",
            ".source-chip{border:1px solid #cad4d6;background:#fff;border-radius:999px;padding:3px 10px;margin:2px 4px 2px 0;font-size:0.78rem;cursor:context-menu;line-height:1.4}",
            ".source-chip.chip-green{background:#e8fff2;border-color:#a7f3d0;color:#14532d}",
            ".source-chip.chip-black{background:#ffe8e8;border-color:#fecaca;color:#7f1d1d}",
            ".source-chip.chip-neutral{background:#f8fafb;border-color:#d3dde0;color:#1f2f33}",
            ".source-chip.chip-manual{box-shadow:0 0 0 2px rgba(15,23,42,0.18) inset}",
            ".label-hint{font-weight:700;color:#4a5f63;font-size:0.78rem}",
            ".text-muted{color:#7a8a8d;font-style:italic}",
            ".label-menu{position:absolute;z-index:5000;background:#fff;border:1px solid #bfd0ce;border-radius:10px;box-shadow:0 14px 30px rgba(15,23,42,0.2);padding:6px;width:170px}",
            ".label-menu[hidden]{display:none}",
            ".label-menu button{display:block;width:100%;text-align:left;background:#fff;border:0;border-radius:8px;padding:7px 9px;cursor:pointer;font-weight:600;color:#203235}",
            ".label-menu button:hover{background:#eef8f5}",
            "@media (max-width:1020px){.metric-grid{grid-template-columns:repeat(3,minmax(140px,1fr));}.source-cell{min-width:320px}}",
            "@media (max-width:640px){main{padding:20px 12px 36px}.metric-grid{grid-template-columns:repeat(2,minmax(120px,1fr));}.source-cell{min-width:250px}",
            "th,td{padding:8px 8px;font-size:0.82rem}}",
            "</style>",
            "</head>",
            "<body>",
            "<main>",
            "<header>",
            "<h1>Rulegen Benchmark Dashboard</h1>",
            "<div class=\"meta\">",
            f"<span>generated <code>{generated_at}</code></span>",
            f"<span>pairs <code>{len(pair_runs)}</code></span>",
            f"<span>configs per pair <code>{configuration_count}</code></span>",
            f"<span>profile <code>{profile_id}</code></span>",
            f"<span>data root <code>{data_root}</code></span>",
            "</div>",
            "<section class=\"label-workbench\">",
            "<p>Right-click any source chip to mark greenlist or blacklist. Export the decisions JSON to update benchmark cases.</p>",
            "<div class=\"label-actions\">",
            "<button id=\"download-labels\" class=\"btn\" type=\"button\">Download labels JSON</button>",
            "<button id=\"copy-labels\" class=\"btn btn-secondary\" type=\"button\">Copy labels JSON</button>",
            "<button id=\"clear-labels\" class=\"btn btn-secondary\" type=\"button\">Clear local labels</button>",
            "<span id=\"label-count\">0 decisions across 0 cases</span>",
            f"<span>dataset <code>{dataset_path}</code></span>",
            "</div>",
            "<div class=\"pair-workflow\">",
            "<div class=\"pair-workflow-head\">",
            "<span id=\"pair-workflow-state\" class=\"pair-workflow-state\">LP workflow</span>",
            "<div class=\"pair-workflow-buttons\">",
            "<button id=\"prev-pair\" class=\"btn btn-secondary\" type=\"button\">Prev LP</button>",
            "<button id=\"next-pair\" class=\"btn btn-secondary\" type=\"button\">Next LP</button>",
            "<button id=\"mark-pair-done\" class=\"btn\" type=\"button\">Mark Done + Next</button>",
            "<button id=\"skip-pair\" class=\"btn btn-secondary\" type=\"button\">Skip LP</button>",
            "<button id=\"reset-pair-status\" class=\"btn btn-secondary\" type=\"button\">Reset LP</button>",
            "<label class=\"show-all-wrap\"><input id=\"show-all-pairs\" type=\"checkbox\">Show all LPs</label>",
            "</div>",
            "</div>",
            "<div id=\"pair-nav-list\" class=\"pair-nav\"></div>",
            "</div>",
            "</section>",
            "</header>",
            "".join(pair_sections),
            "</main>",
            "<div id=\"label-menu\" class=\"label-menu\" hidden>",
            "<button type=\"button\" data-action=\"green\">Greenlist</button>",
            "<button type=\"button\" data-action=\"black\">Blacklist</button>",
            "<button type=\"button\" data-action=\"neutral\">Clear label</button>",
            "</div>",
            label_script,
            "</body>",
            "</html>",
        ]
    )


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
    parser.add_argument("--profile-id", default="default", help="SRS profile id for word_package hints.")
    parser.add_argument(
        "--data-root",
        type=Path,
        help="Override LexiShift data root (default: platform data dir or LEXISHIFT_DATA_DIR).",
    )
    parser.add_argument("--jmdict", type=Path, help="Optional JMdict override path.")
    parser.add_argument(
        "--freedict-en-de",
        type=Path,
        help="Optional FreeDict override for en-de pair (deu-eng.tei / sqlite).",
    )
    parser.add_argument(
        "--freedict-en-es",
        type=Path,
        help="Optional FreeDict override for en-es pair (spa-eng.tei / sqlite).",
    )
    parser.add_argument(
        "--freedict-es-en",
        type=Path,
        help="Optional FreeDict override for es-en pair (eng-spa.tei / sqlite).",
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
        {item.strip().lower() for item in _parse_csv_strings(args.pairs)}
        if args.pairs
        else None
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

    freedict_overrides: dict[str, Optional[Path]] = {
        "en-de": args.freedict_en_de,
        "en-es": args.freedict_en_es,
        "es-en": args.freedict_es_en,
    }

    pair_runs: dict[str, list[SweepRun]] = {}
    pair_resources: dict[str, dict[str, Optional[str]]] = {}
    for pair, cases in sorted(cases_by_pair.items()):
        capability = resolve_pair_capability(pair)
        if capability.rulegen_mode is None:
            continue
        jmdict_path, freedict_path = _resolve_pair_resources_for_benchmark(
            paths=paths,
            pair=pair,
            jmdict_override=args.jmdict,
            freedict_override=freedict_overrides.get(pair),
        )
        pair_resources[pair] = {
            "jmdict_path": str(jmdict_path) if jmdict_path else None,
            "freedict_path": str(freedict_path) if freedict_path else None,
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
                    jmdict_path=jmdict_path,
                    freedict_de_en_path=freedict_path,
                    word_packages_by_target=word_packages,
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
            key: value
            for key, value in dataset_payload.items()
            if key != "cases"
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
        report_payload["pairs"][pair] = {
            "case_count": len(cases_by_pair.get(pair, ())),
            "run_count": len(runs),
            "best_run": runs[0].to_dict(include_case_results=True) if runs else None,
            "runs": [
                run.to_dict(include_case_results=args.include_case_results)
                for run in runs
            ],
        }

    top_runs = max(1, int(args.top_runs))
    markdown_report = _render_markdown_report(pair_runs=pair_runs, top_n=top_runs)
    html_report = _render_html_report(
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
