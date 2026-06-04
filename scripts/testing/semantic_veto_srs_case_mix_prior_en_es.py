#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (str(CORE_ROOT), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_full_family_representative_sample_en_es import (  # noqa: E402
    DEFAULT_WORDNET_DIR,
)
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _format_percent,
    _load_json,
    _mapping_rows,
    _repo_path,
    _resolve_repo_path,
    _safe_float,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_SRS_BRIDGE_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.json"
DEFAULT_SCORE_SURFACE_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_repaired_full_score_surface_en_es_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_srs_case_mix_prior_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_srs_case_mix_prior_en_es_latest.md"

CASE_TYPES = ("positive_active", "shadow_negative", "phrase_no_winner")
SOURCE_BAND_ORDER = (
    "zipf_5_plus_very_common",
    "zipf_4_to_5_common",
    "zipf_3_to_4_mid",
    "zipf_below_3_rare",
    "missing",
)


@dataclass(frozen=True)
class PriorScenario:
    scenario_id: str
    description: str
    no_winner_base: float
    no_winner_span: float
    shadow_base: float
    shadow_span: float
    no_winner_cap: float
    shadow_cap: float


PRIOR_SCENARIOS = (
    PriorScenario(
        scenario_id="low_no_winner_product_prior",
        description="Assumes no-winner contexts are uncommon in real SRS browsing exposure.",
        no_winner_base=0.02,
        no_winner_span=0.08,
        shadow_base=0.05,
        shadow_span=0.20,
        no_winner_cap=0.12,
        shadow_cap=0.35,
    ),
    PriorScenario(
        scenario_id="base_product_prior",
        description="Default static prior: no-winner is meaningful but not test-suite-balanced.",
        no_winner_base=0.05,
        no_winner_span=0.15,
        shadow_base=0.08,
        shadow_span=0.30,
        no_winner_cap=0.25,
        shadow_cap=0.45,
    ),
    PriorScenario(
        scenario_id="high_no_winner_product_prior",
        description="Stress prior for UI/title/code/name-heavy browsing exposure.",
        no_winner_base=0.10,
        no_winner_span=0.25,
        shadow_base=0.08,
        shadow_span=0.30,
        no_winner_cap=0.40,
        shadow_cap=0.45,
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate active/shadow/no-winner case-type priors for the full en-es SRS "
            "source-target distribution using programmatic static features, then "
            "reweight approved repaired-full veto performance by those priors."
        )
    )
    parser.add_argument("--srs-bridge-json", type=Path, default=DEFAULT_SRS_BRIDGE_JSON)
    parser.add_argument("--score-surface-json", type=Path, default=DEFAULT_SCORE_SURFACE_JSON)
    parser.add_argument("--wordnet-dir", type=Path, default=DEFAULT_WORDNET_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    wordnet_dir = _resolve_repo_path(args.wordnet_dir)
    wordnet_index = WordNetIndex.load(wordnet_dir)
    report = build_srs_case_mix_prior_report(
        srs_bridge_payload=_load_json(args.srs_bridge_json),
        score_surface_payload=_load_json(args.score_surface_json),
        wordnet_index=wordnet_index,
        srs_bridge_path=args.srs_bridge_json,
        score_surface_path=args.score_surface_json,
        wordnet_dir=wordnet_dir,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_srs_case_mix_prior_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_srs_case_mix_prior_report(
    *,
    srs_bridge_payload: Mapping[str, object],
    score_surface_payload: Mapping[str, object],
    wordnet_index: WordNetIndex | None = None,
    srs_bridge_path: Path | None = None,
    score_surface_path: Path | None = None,
    wordnet_dir: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    source_target_rows = _dedupe_source_target_pairs(
        _mapping_rows(srs_bridge_payload.get("full_source_target_pairs"))
    )
    fanout_by_source = _fanout_by_source(source_target_rows)
    pair_rows = [
        _pair_prior_features(
            row=row, fanout_by_source=fanout_by_source, wordnet_index=wordnet_index
        )
        for row in source_target_rows
    ]
    performance_rows = _performance_rows(score_surface_payload)
    scenario_rows = [
        _scenario_report(
            scenario=scenario,
            pair_rows=pair_rows,
            performance_rows=performance_rows,
        )
        for scenario in PRIOR_SCENARIOS
    ]
    issues = []
    if not source_target_rows:
        issues.append("srs_bridge_has_no_full_source_target_pairs")
    if not performance_rows:
        issues.append("score_surface_has_no_case_type_performance_rows")
    if wordnet_index is None or not wordnet_index.entries_by_word:
        issues.append("wordnet_profile_unavailable")
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "pair": str(srs_bridge_payload.get("pair") or score_surface_payload.get("pair") or "en-es"),
        "status": status,
        "decision": (
            "srs_case_mix_prior_established"
            if status == "ok"
            else "srs_case_mix_prior_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "srs_bridge_path": _repo_path(srs_bridge_path),
            "srs_bridge_decision": str(srs_bridge_payload.get("decision") or ""),
            "score_surface_path": _repo_path(score_surface_path),
            "score_surface_decision": str(score_surface_payload.get("decision") or ""),
            "wordnet_dir": _repo_path(wordnet_dir),
            "wordnet_source_file_count": int(
                getattr(wordnet_index, "source_file_count", 0) if wordnet_index else 0
            ),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_generation": "none",
            "purpose": (
                "Estimate real-SRS active/shadow/no-winner proportions by source band "
                "from programmatic static features, then multiply those proportions by "
                "approved repaired-full conditional veto performance."
            ),
            "case_type_boundary": (
                "These are priors, not observed sentence labels. Static metadata can "
                "estimate shadow/no-winner risk, but true case type still requires "
                "runtime or corpus context."
            ),
            "programmatic_features": [
                "source_zipf_band_en",
                "target_zipf_band_es",
                "source_zipf_frequency_en",
                "target_zipf_frequency_es",
                "source_translation_fanout",
                "wordnet_sense_count",
                "wordnet_pos_count",
                "source_form_risk",
            ],
            "weighted_success_formula": (
                "p_active * positive_allow_rate + p_shadow * shadow_abstain_rate + "
                "p_no_winner * phrase_no_winner_abstain_rate"
            ),
        },
        "summary": {
            "issues": issues,
            "source_target_pair_count": len(source_target_rows),
            "unique_source_count": len(fanout_by_source),
            "wordnet_profile_known_pair_count": sum(
                1 for row in pair_rows if row.get("wordnet_sense_count")
            ),
            "scenario_count": len(scenario_rows),
            "base_scenario": _base_summary(scenario_rows),
        },
        "e2e_checks": {
            "full_srs_pairs_available": bool(source_target_rows),
            "performance_rows_available": bool(performance_rows),
            "case_type_priors_sum_to_one": all(
                _priors_sum_to_one(row)
                for scenario in scenario_rows
                for row in _mapping_rows(scenario.get("band_prior_rows"))
            ),
            "weighted_success_rows_available": all(
                bool(_mapping_rows(scenario.get("weighted_success_rows")))
                for scenario in scenario_rows
            ),
            "wordnet_loaded": bool(wordnet_index and wordnet_index.entries_by_word),
        },
        "prior_scenarios": [scenario.__dict__ for scenario in PRIOR_SCENARIOS],
        "scenario_rows": scenario_rows,
        "pair_feature_samples": pair_rows[:50],
        "limitations": [
            "case_type_proportions_are_static_priors_not_observed_browser_labels",
            "no_winner_rate_cannot_be_known_without_contexts",
            "source_target_pairs_are_current_rulegen_outputs_not_every_possible_runtime_trigger",
            "wordnet_polysemy_can_overstate_or_understate practical translation ambiguity",
            "weighted_success_uses_repaired_full_conditional_performance_not final locked eval",
        ],
        "next_steps": [
            "Use this report to choose plausible product-mix priors before spending LLM budget.",
            "Add real or corpus-like SRS-trigger contexts to replace static priors with observed case-type rates.",
            "Track no-winner sensitivity separately because it dominates sentence-transformer product success.",
        ],
    }


def render_srs_case_mix_prior_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    base = _as_mapping(summary.get("base_scenario"))
    lines = [
        "# en-es Semantic Veto SRS Case-Mix Prior",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Source-target pairs: `{summary.get('source_target_pair_count', 0)}`",
        f"- Unique sources: `{summary.get('unique_source_count', 0)}`",
        f"- WordNet-profile known pairs: `{summary.get('wordnet_profile_known_pair_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("purpose") or ""),
        "",
        "The report does not claim to know true browser sentence labels. It estimates "
        "case-type priors from static SRS source-target metadata, then applies those "
        "priors to the approved repaired-full conditional veto rates.",
        "",
        "## Base Prior By Source Band",
        "",
        _band_prior_table(base.get("band_prior_rows")),
        "",
        "## Base Weighted Success",
        "",
        _weighted_success_table(base.get("weighted_success_rows")),
        "",
        "## Scenario Comparison",
        "",
        _scenario_comparison_table(report.get("scenario_rows")),
        "",
        "## Sensitivity Read",
        "",
        _sensitivity_read(report.get("scenario_rows")),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _scenario_report(
    *,
    scenario: PriorScenario,
    pair_rows: Sequence[Mapping[str, object]],
    performance_rows: Mapping[tuple[str, str, str], float],
) -> dict[str, object]:
    pair_priors = [_pair_with_priors(row=row, scenario=scenario) for row in pair_rows]
    band_prior_rows = _band_prior_rows(pair_priors)
    weighted_success_rows = _weighted_success_rows(
        band_prior_rows=band_prior_rows,
        performance_rows=performance_rows,
    )
    return {
        "scenario_id": scenario.scenario_id,
        "description": scenario.description,
        "band_prior_rows": band_prior_rows,
        "weighted_success_rows": weighted_success_rows,
        "overall_weighted_success_by_scorer": _overall_weighted_success(weighted_success_rows),
    }


def _pair_prior_features(
    *,
    row: Mapping[str, object],
    fanout_by_source: Mapping[str, int],
    wordnet_index: WordNetIndex | None,
) -> dict[str, object]:
    source = str(row.get("source") or "").strip()
    source_key = source.lower()
    wordnet = _wordnet_profile(source_key, wordnet_index)
    fanout = int(fanout_by_source.get(source_key, 1))
    sense_count = int(wordnet.get("wordnet_sense_count") or 0)
    pos_count = int(wordnet.get("wordnet_pos_count") or 0)
    return {
        "source": source,
        "target": str(row.get("target") or ""),
        "source_zipf_band_en": str(row.get("source_zipf_band_en") or "missing"),
        "target_zipf_band_es": str(row.get("target_zipf_band_es") or "missing"),
        "source_zipf_frequency_en": _optional_float(row.get("source_zipf_frequency_en")),
        "target_zipf_frequency_es": _optional_float(row.get("target_zipf_frequency_es")),
        "source_translation_fanout": fanout,
        "wordnet_sense_count": sense_count,
        "wordnet_pos_count": pos_count,
        "shadow_risk": _shadow_risk(sense_count=sense_count, pos_count=pos_count, fanout=fanout),
        "no_winner_surface_risk": _no_winner_surface_risk(
            source=source,
            source_band=str(row.get("source_zipf_band_en") or "missing"),
        ),
    }


def _pair_with_priors(*, row: Mapping[str, object], scenario: PriorScenario) -> dict[str, object]:
    shadow_risk = _safe_float(row.get("shadow_risk"))
    no_winner_risk = _safe_float(row.get("no_winner_surface_risk"))
    p_no_winner = min(
        scenario.no_winner_cap,
        scenario.no_winner_base + scenario.no_winner_span * no_winner_risk,
    )
    p_shadow = min(
        scenario.shadow_cap,
        scenario.shadow_base + scenario.shadow_span * shadow_risk,
    )
    if p_no_winner + p_shadow > 0.85:
        scale = 0.85 / (p_no_winner + p_shadow)
        p_no_winner *= scale
        p_shadow *= scale
    p_active = max(0.0, 1.0 - p_shadow - p_no_winner)
    return {
        **dict(row),
        "p_positive_active": round(p_active, 4),
        "p_shadow_negative": round(p_shadow, 4),
        "p_phrase_no_winner": round(p_no_winner, 4),
    }


def _band_prior_rows(pair_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in pair_rows:
        grouped[str(row.get("source_zipf_band_en") or "missing")].append(row)
    total_pairs = len(pair_rows)
    output = []
    for band in SOURCE_BAND_ORDER:
        rows = grouped.get(band, [])
        if not rows:
            continue
        count = len(rows)
        output.append(
            {
                "source_zipf_band_en": band,
                "source_target_pair_count": count,
                "srs_pair_share": _rate(count, total_pairs),
                "p_positive_active": _mean(rows, "p_positive_active"),
                "p_shadow_negative": _mean(rows, "p_shadow_negative"),
                "p_phrase_no_winner": _mean(rows, "p_phrase_no_winner"),
                "mean_shadow_risk": _mean(rows, "shadow_risk"),
                "mean_no_winner_surface_risk": _mean(rows, "no_winner_surface_risk"),
                "mean_wordnet_sense_count": _mean(rows, "wordnet_sense_count"),
                "mean_wordnet_pos_count": _mean(rows, "wordnet_pos_count"),
                "mean_translation_fanout": _mean(rows, "source_translation_fanout"),
            }
        )
    return output


def _weighted_success_rows(
    *,
    band_prior_rows: Sequence[Mapping[str, object]],
    performance_rows: Mapping[tuple[str, str, str], float],
) -> list[dict[str, object]]:
    scorer_ids = sorted({key[0] for key in performance_rows})
    output = []
    for scorer_id in scorer_ids:
        for prior in band_prior_rows:
            band = str(prior.get("source_zipf_band_en") or "missing")
            positive = _performance_rate(performance_rows, scorer_id, band, "positive_active")
            shadow = _performance_rate(performance_rows, scorer_id, band, "shadow_negative")
            no_winner = _performance_rate(performance_rows, scorer_id, band, "phrase_no_winner")
            weighted = (
                _safe_float(prior.get("p_positive_active")) * positive
                + _safe_float(prior.get("p_shadow_negative")) * shadow
                + _safe_float(prior.get("p_phrase_no_winner")) * no_winner
            )
            output.append(
                {
                    "scorer_id": scorer_id,
                    "source_zipf_band_en": band,
                    "srs_pair_share": prior.get("srs_pair_share"),
                    "estimated_weighted_success": round(weighted, 4),
                    "p_positive_active": prior.get("p_positive_active"),
                    "p_shadow_negative": prior.get("p_shadow_negative"),
                    "p_phrase_no_winner": prior.get("p_phrase_no_winner"),
                    "positive_allow_rate": round(positive, 4),
                    "shadow_abstain_rate": round(shadow, 4),
                    "no_winner_abstain_rate": round(no_winner, 4),
                }
            )
    return output


def _overall_weighted_success(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("scorer_id") or "")].append(row)
    output = []
    for scorer_id, scorer_rows in sorted(grouped.items()):
        total_weight = sum(_safe_float(row.get("srs_pair_share")) for row in scorer_rows)
        weighted = sum(
            _safe_float(row.get("srs_pair_share"))
            * _safe_float(row.get("estimated_weighted_success"))
            for row in scorer_rows
        )
        output.append(
            {
                "scorer_id": scorer_id,
                "estimated_overall_srs_weighted_success": round(weighted / total_weight, 4)
                if total_weight
                else None,
            }
        )
    return output


def _performance_rows(
    score_surface_payload: Mapping[str, object],
) -> dict[tuple[str, str, str], float]:
    rows: dict[tuple[str, str, str], float] = {}
    for row in _mapping_rows(
        _as_mapping(score_surface_payload.get("breakdowns")).get("scorer_x_source_band_x_case_type")
    ):
        scorer_id = str(row.get("scorer_id") or "")
        band = str(row.get("source_zipf_band_en") or "missing")
        case_type = str(row.get("manual_case_type") or "")
        if case_type == "positive_active":
            rate = row.get("positive_allow_rate")
        elif case_type == "shadow_negative":
            rate = row.get("shadow_negative_abstain_rate")
        elif case_type == "phrase_no_winner":
            rate = row.get("phrase_no_winner_abstain_rate")
        else:
            continue
        if rate is not None:
            rows[(scorer_id, band, case_type)] = _safe_float(rate)
    return rows


def _performance_rate(
    rows: Mapping[tuple[str, str, str], float],
    scorer_id: str,
    band: str,
    case_type: str,
) -> float:
    if (scorer_id, band, case_type) in rows:
        return rows[(scorer_id, band, case_type)]
    band_rates = [value for (s, _b, c), value in rows.items() if s == scorer_id and c == case_type]
    if not band_rates:
        return 0.0
    return sum(band_rates) / len(band_rates)


def _base_summary(scenario_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    for row in scenario_rows:
        if row.get("scenario_id") == "base_product_prior":
            return dict(row)
    return dict(scenario_rows[0]) if scenario_rows else {}


def _shadow_risk(*, sense_count: int, pos_count: int, fanout: int) -> float:
    sense_risk = min(1.0, max(0, sense_count - 1) / 14.0) if sense_count else 0.35
    pos_risk = min(1.0, max(0, pos_count - 1) / 3.0) if pos_count else 0.25
    fanout_risk = min(1.0, max(0, fanout - 1) / 4.0)
    return round(0.50 * sense_risk + 0.25 * pos_risk + 0.25 * fanout_risk, 4)


def _no_winner_surface_risk(*, source: str, source_band: str) -> float:
    token = str(source or "").strip()
    band_risk = {
        "zipf_5_plus_very_common": 1.0,
        "zipf_4_to_5_common": 0.65,
        "zipf_3_to_4_mid": 0.35,
        "zipf_below_3_rare": 0.15,
        "missing": 0.45,
    }.get(source_band, 0.45)
    short_risk = 0.7 if len(token) <= 3 else 0.4 if len(token) <= 5 else 0.1
    artifact_risk = 0.0
    if not re.fullmatch(r"[A-Za-z]+", token):
        artifact_risk = 0.8
    elif len(token) >= 14:
        artifact_risk = 0.35
    elif re.search(r"(site|work|man|woman|journalist|language)$", token.lower()):
        artifact_risk = 0.25
    return round(0.60 * band_risk + 0.25 * short_risk + 0.15 * artifact_risk, 4)


def _wordnet_profile(source: str, wordnet_index: WordNetIndex | None) -> dict[str, int]:
    if wordnet_index is None:
        return {}
    entry = wordnet_index.entries_by_word.get(str(source or "").strip().lower())
    if not isinstance(entry, Mapping):
        return {}
    sense_count = 0
    pos_count = 0
    for section in entry.values():
        if not isinstance(section, Mapping):
            continue
        senses = _sequence(section.get("sense"))
        count = sum(1 for item in senses if isinstance(item, Mapping))
        if count:
            sense_count += count
            pos_count += 1
    return {
        "wordnet_sense_count": sense_count,
        "wordnet_pos_count": pos_count,
    }


def _fanout_by_source(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    targets: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        source = str(row.get("source") or "").strip().lower()
        target = str(row.get("target") or "").strip().lower()
        if source and target:
            targets[source].add(target)
    return {source: len(values) for source, values in targets.items()}


def _dedupe_source_target_pairs(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    deduped: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        source = str(row.get("source") or "").strip()
        target = str(row.get("target") or "").strip()
        if not source or not target:
            continue
        deduped[(source.lower(), target.lower())] = dict(row)
    return [deduped[key] for key in sorted(deduped)]


def _band_prior_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No rows._"
    headers = [
        "source band",
        "pairs",
        "SRS share",
        "active prior",
        "shadow prior",
        "no-winner prior",
        "shadow risk",
        "no-winner risk",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape_md(value)
                for value in [
                    str(row.get("source_zipf_band_en") or ""),
                    str(row.get("source_target_pair_count") or 0),
                    _format_percent(row.get("srs_pair_share")),
                    _format_percent(row.get("p_positive_active")),
                    _format_percent(row.get("p_shadow_negative")),
                    _format_percent(row.get("p_phrase_no_winner")),
                    _format_percent(row.get("mean_shadow_risk")),
                    _format_percent(row.get("mean_no_winner_surface_risk")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _weighted_success_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No rows._"
    headers = [
        "scorer",
        "source band",
        "estimated success",
        "active rate",
        "shadow rate",
        "no-winner rate",
        "SRS share",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape_md(value)
                for value in [
                    str(row.get("scorer_id") or ""),
                    str(row.get("source_zipf_band_en") or ""),
                    _format_percent(row.get("estimated_weighted_success")),
                    _format_percent(row.get("positive_allow_rate")),
                    _format_percent(row.get("shadow_abstain_rate")),
                    _format_percent(row.get("no_winner_abstain_rate")),
                    _format_percent(row.get("srs_pair_share")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _scenario_comparison_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No rows._"
    lines = [
        "| scenario | scorer | estimated overall SRS-weighted success |",
        "| --- | --- | ---: |",
    ]
    for scenario in rows:
        for scorer in _mapping_rows(scenario.get("overall_weighted_success_by_scorer")):
            lines.append(
                f"| `{_escape_md(str(scenario.get('scenario_id') or ''))}` | "
                f"`{_escape_md(str(scorer.get('scorer_id') or ''))}` | "
                f"{_format_percent(scorer.get('estimated_overall_srs_weighted_success'))} |"
            )
    return "\n".join(lines)


def _sensitivity_read(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No scenario rows._"
    by_scenario = {
        str(row.get("scenario_id") or ""): {
            str(item.get("scorer_id") or ""): item.get("estimated_overall_srs_weighted_success")
            for item in _mapping_rows(row.get("overall_weighted_success_by_scorer"))
        }
        for row in rows
    }
    st_values = [
        _safe_float(by_scenario.get(scenario.scenario_id, {}).get("sentence_transformer_cosine"))
        for scenario in PRIOR_SCENARIOS
    ]
    if not st_values:
        return "_No sentence-transformer scenario values._"
    return (
        "For sentence-transformer, estimated SRS-weighted success ranges from "
        f"`{_format_percent(min(st_values))}` to `{_format_percent(max(st_values))}` "
        "across the no-winner prior scenarios. A wide range means no-winner exposure "
        "must be measured with real contexts before promotion claims."
    )


def _priors_sum_to_one(row: Mapping[str, object]) -> bool:
    total = (
        _safe_float(row.get("p_positive_active"))
        + _safe_float(row.get("p_shadow_negative"))
        + _safe_float(row.get("p_phrase_no_winner"))
    )
    return abs(total - 1.0) < 0.002


def _mean(rows: Sequence[Mapping[str, object]], key: str) -> float:
    values = [_safe_float(row.get(key)) for row in rows]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sequence(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
