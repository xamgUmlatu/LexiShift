#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_reverse_translation_dictionary_path,
    resolve_pair_capability,
)
from lexishift_core.helper.pair_resources import (  # noqa: E402
    resolve_pair_resources,
    resolve_stopwords_path,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.rulegen.adapters import RulegenAdapterRequest, run_rules_with_adapter  # noqa: E402
from lexishift_core.rulegen.tuning import resolve_rulegen_tuning  # noqa: E402
from lexishift_core.srs.admission_policy import resolve_default_pos_weights  # noqa: E402
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from semantic_veto_srs_zipf_bridge_rendering import (  # noqa: E402
    render_srs_zipf_bridge_markdown as render_srs_zipf_bridge_markdown,
)
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _load_json,
    _mapping_rows,
    _repo_path,
    _safe_float,
)


TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_SRS_JOURNEY_JSON = (
    TEST_OUTPUTS_ROOT / "srs_journey" / "srs_journey_en_es_installed_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.md"
DEFAULT_PAIR = "en-es"
DEFAULT_FULL_SRS_TOP_N = 50000

ZIPF_BANDS = (
    "zipf_5_plus_very_common",
    "zipf_4_to_5_common",
    "zipf_3_to_4_mid",
    "zipf_below_3_rare",
    "missing",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bridge SRS en-es target distribution to semantic-veto Zipf cost planning. "
            "This report is diagnostic-only and does not change SRS or runtime policy."
        )
    )
    parser.add_argument("--srs-journey-json", type=Path, default=DEFAULT_SRS_JOURNEY_JSON)
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument(
        "--frequency-db",
        type=Path,
        default=None,
        help=(
            "Optional candidate frequency SQLite for the full SRS-admissible universe. "
            "Use this to evaluate an expansion candidate without installing it or "
            "overwriting the current default pack."
        ),
    )
    parser.add_argument("--full-srs-top-n", type=int, default=DEFAULT_FULL_SRS_TOP_N)
    parser.add_argument(
        "--include-full-rulegen",
        action="store_true",
        help=(
            "Generate rule source-target pairs for the full SRS-admissible target universe. "
            "This can take a couple of minutes on installed en-es resources."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    full_srs_rows, full_srs_inputs = build_full_srs_admissible_rows(
        pair=str(args.pair),
        top_n=max(1, int(args.full_srs_top_n)),
        frequency_db=args.frequency_db,
    )
    full_rulegen_pairs: list[dict[str, object]] = []
    full_rulegen_inputs: dict[str, object] = {
        "status": "skipped",
        "reason": "include_full_rulegen_not_requested",
    }
    if bool(args.include_full_rulegen):
        full_rulegen_pairs, full_rulegen_inputs = build_full_rulegen_source_target_pairs(
            pair=str(args.pair),
            full_srs_rows=full_srs_rows,
        )
    report = build_srs_zipf_bridge_report(
        srs_journey_payload=_load_json(args.srs_journey_json),
        srs_journey_path=args.srs_journey_json,
        full_srs_rows=full_srs_rows,
        full_srs_inputs=full_srs_inputs,
        full_source_target_pairs=full_rulegen_pairs,
        full_rulegen_inputs=full_rulegen_inputs,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_srs_zipf_bridge_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_srs_zipf_bridge_report(
    *,
    srs_journey_payload: Mapping[str, object],
    srs_journey_path: Path | None = None,
    full_srs_rows: Sequence[Mapping[str, object]] | None = None,
    full_srs_inputs: Mapping[str, object] | None = None,
    full_source_target_pairs: Sequence[Mapping[str, object]] | None = None,
    full_rulegen_inputs: Mapping[str, object] | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    scenario = _as_mapping(srs_journey_payload.get("scenario"))
    full_srs_rows = _dedupe_rows_by_key(full_srs_rows or [], key_name="lemma")
    full_srs_inputs = _as_mapping(full_srs_inputs)
    full_source_target_pairs = _dedupe_source_target_pairs(full_source_target_pairs or [])
    full_rulegen_inputs = _as_mapping(full_rulegen_inputs)
    candidate_rows = _dedupe_rows_by_key(
        _mapping_rows(scenario.get("candidate_universe")),
        key_name="lemma",
    )
    selected_rows = [row for row in candidate_rows if bool(row.get("selected"))]
    phases = _mapping_rows(srs_journey_payload.get("phases"))
    latest_phase = _as_mapping(phases[-1]) if phases else {}
    latest_items = _dedupe_rows_by_key(_mapping_rows(latest_phase.get("items")), key_name="lemma")
    latest_admitted_rows = latest_items
    latest_due_rows = [row for row in latest_items if bool(row.get("in_due"))]
    latest_published_rows = [row for row in latest_items if bool(row.get("in_published"))]
    union_published_target_rows = [
        {"lemma": lemma}
        for lemma in sorted(
            {
                str(target or "").strip()
                for phase in phases
                for target in _as_mapping(phase.get("sets")).get("published", [])
                if str(target or "").strip()
            }
        )
    ]

    source_target_pairs = _source_target_pairs(phases)
    source_trigger_rows = [
        {"source": source}
        for source in sorted(
            {
                str(row.get("source") or "").strip()
                for row in source_target_pairs
                if str(row.get("source") or "").strip()
            }
        )
    ]
    source_preview_rows = _source_preview_rows(phases)
    source_mapping_status = _source_mapping_status(
        source_target_pairs=source_target_pairs,
        source_trigger_rows=source_trigger_rows,
        source_preview_rows=source_preview_rows,
    )
    full_source_trigger_rows = [
        {"source": source}
        for source in sorted(
            {
                str(row.get("source") or "").strip()
                for row in full_source_target_pairs
                if str(row.get("source") or "").strip()
            }
        )
    ]
    full_source_mapping_status = (
        "full_source_target_pairs_available"
        if full_source_target_pairs
        else str(full_rulegen_inputs.get("status") or "not_requested")
    )

    target_scopes = [
        _target_scope(
            "full_srs_admissible_universe",
            full_srs_rows,
            weight_key="admission_weight",
        ),
        _target_scope("journey_srs_candidate_slice", candidate_rows, weight_key="admission_weight"),
        _target_scope("srs_selected_initial_active", selected_rows, weight_key="admission_weight"),
        _target_scope("latest_admitted_srs_items", latest_admitted_rows, weight_key="confidence"),
        _target_scope("latest_due_srs_items", latest_due_rows, weight_key="confidence"),
        _target_scope(
            "latest_published_srs_targets", latest_published_rows, weight_key="confidence"
        ),
        _target_scope("journey_union_published_targets", union_published_target_rows),
    ]
    source_scope = _source_scope(
        "journey_union_rule_source_triggers",
        source_trigger_rows if source_trigger_rows else source_preview_rows,
        preview_only=not source_trigger_rows and bool(source_preview_rows),
    )
    full_source_scope = _source_scope(
        "full_srs_rule_source_triggers",
        full_source_trigger_rows,
        preview_only=False,
    )
    journey_matrix_rows = _source_target_matrix(source_target_pairs)
    full_matrix_rows = _source_target_matrix(full_source_target_pairs)
    annotated_journey_pairs = _annotated_source_target_pairs(source_target_pairs)
    annotated_full_pairs = _annotated_source_target_pairs(full_source_target_pairs)

    issues = []
    if not full_srs_rows:
        issues.append("full_srs_admissible_universe_missing")
    if not candidate_rows:
        issues.append("journey_srs_candidate_slice_missing")
    if not source_target_pairs:
        issues.append("source_target_rule_pairs_missing")

    full_common_count = _sum_band_counts(
        target_scopes[0],
        bands={"zipf_5_plus_very_common", "zipf_4_to_5_common"},
    )
    journey_common_count = _sum_band_counts(
        target_scopes[1],
        bands={"zipf_5_plus_very_common", "zipf_4_to_5_common"},
    )
    full_srs_frequency_limitation = (
        "full_srs_universe_uses_candidate_frequency_db_override"
        if str(full_srs_inputs.get("frequency_db_source") or "") == "override"
        else "full_srs_universe_is_limited_by_current_installed_frequency_pack"
    )
    return {
        "schema_version": 1,
        "pair": str(scenario.get("pair") or full_srs_inputs.get("pair") or DEFAULT_PAIR),
        "status": "review" if issues else "ok",
        "decision": (
            "srs_zipf_bridge_established" if not issues else "srs_zipf_bridge_needs_mapping"
        ),
        "generated_at": generated_at,
        "inputs": {
            "srs_journey_path": _repo_path(srs_journey_path),
            "srs_journey_scenario": str(scenario.get("name") or scenario.get("id") or ""),
            "srs_resource_mode": str(scenario.get("resource_mode") or ""),
            "full_srs": dict(full_srs_inputs),
            "full_rulegen": dict(full_rulegen_inputs),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_generation": "none",
            "target_language": "es",
            "source_language": "en",
            "target_denominator": (
                "Full installed SRS-admissible target lemmas from the SRS seed/admission "
                "path, plus journey-slice selected/admitted/due/published target lemmas."
            ),
            "source_denominator": (
                "Full generated rule source-target pairs when requested, plus published "
                "journey rule source triggers and source-target pairs."
            ),
            "zipf_thresholds": {
                "zipf_5_plus_very_common": ">= 5.0",
                "zipf_4_to_5_common": ">= 4.0 and < 5.0",
                "zipf_3_to_4_mid": ">= 3.0 and < 4.0",
                "zipf_below_3_rare": "> 0.0 and < 3.0",
            },
        },
        "summary": {
            "issues": issues,
            "full_srs_admissible_seed_row_count": int(
                full_srs_inputs.get("seed_row_count") or len(full_srs_rows)
            ),
            "full_srs_admissible_target_count": len(full_srs_rows),
            "journey_srs_candidate_target_count": len(candidate_rows),
            "srs_candidate_target_count": len(candidate_rows),
            "srs_selected_initial_active_count": len(selected_rows),
            "latest_admitted_target_count": len(latest_admitted_rows),
            "latest_due_target_count": len(latest_due_rows),
            "latest_published_target_count": len(latest_published_rows),
            "journey_union_published_target_count": len(union_published_target_rows),
            "journey_union_rule_source_trigger_count": len(source_trigger_rows),
            "journey_union_source_target_pair_count": len(source_target_pairs),
            "full_rule_source_trigger_count": len(full_source_trigger_rows),
            "full_source_target_pair_count": len(full_source_target_pairs),
            "source_mapping_status": source_mapping_status,
            "full_source_mapping_status": full_source_mapping_status,
            "full_target_very_common_or_common_count": full_common_count,
            "full_target_very_common_or_common_share": _ratio(
                full_common_count,
                len(full_srs_rows),
            ),
            "journey_candidate_target_very_common_or_common_count": journey_common_count,
            "journey_candidate_target_very_common_or_common_share": _ratio(
                journey_common_count,
                len(candidate_rows),
            ),
            "candidate_target_very_common_or_common_count": journey_common_count,
            "candidate_target_very_common_or_common_share": _ratio(
                journey_common_count, len(candidate_rows)
            ),
        },
        "target_zipf_scopes_es": target_scopes,
        "source_zipf_scope_en": source_scope,
        "full_source_zipf_scope_en": full_source_scope,
        "journey_source_target_pairs": annotated_journey_pairs,
        "full_source_target_pairs": annotated_full_pairs,
        "source_target_family_zipf_matrix": journey_matrix_rows,
        "full_source_target_family_zipf_matrix": full_matrix_rows,
        "limitations": [
            "srs_target_frequency_is_not_the_same_as_source_trigger_veto_difficulty",
            "zipf_frequency_is_not_cefr_or_user_known_word_level",
            "journey_candidate_universe_is_current_top_n_slice_not_full_srs_universe",
            full_srs_frequency_limitation,
            "source_target_matrix_depends_on_journey_artifact_preserving_rule_pairs",
            "full_source_target_matrix_requires_explicit_full_rulegen_run",
            "report_is_cost_planning_evidence_not_runtime_policy",
        ],
        "next_steps": [
            "Use target-side rows to estimate which SRS words users actually experience.",
            "Use source-trigger rows to estimate which published replacement families need semantic-veto evidence.",
            "Weight future LLM generation by SRS admission exposure and source-trigger veto difficulty, not by source frequency alone.",
            "Keep target-side learner difficulty and source-side veto ambiguity as separate axes.",
        ],
    }


def build_full_srs_admissible_rows(
    *,
    pair: str,
    top_n: int,
    frequency_db: Path | None = None,
) -> tuple[list[Mapping[str, object]], dict[str, object]]:
    normalized_pair = str(pair or DEFAULT_PAIR).strip().lower() or DEFAULT_PAIR
    paths = build_helper_paths()
    capability = resolve_pair_capability(normalized_pair)
    jmdict_path, translation_dict_path, resolved_frequency_db = resolve_pair_resources(
        paths,
        pair=normalized_pair,
        jmdict_path=None,
        translation_dict_path=None,
        set_source_db=None,
    )
    selected_frequency_db = (
        Path(frequency_db).expanduser() if frequency_db else resolved_frequency_db
    )
    stopwords_path = resolve_stopwords_path(paths, pair=normalized_pair)
    inputs: dict[str, object] = {
        "status": "ok",
        "pair": capability.pair,
        "top_n": int(top_n),
        "frequency_db": _repo_path(selected_frequency_db),
        "frequency_db_exists": bool(selected_frequency_db and selected_frequency_db.exists()),
        "frequency_db_source": "override" if frequency_db else "installed_default",
        "default_frequency_db": _repo_path(resolved_frequency_db),
        "jmdict_path": _repo_path(jmdict_path),
        "requires_jmdict_for_seed": bool(capability.requires_jmdict_for_seed),
        "stopwords_path": _repo_path(stopwords_path),
        "stopwords_exists": bool(stopwords_path and stopwords_path.exists()),
        "translation_dict_path": _repo_path(translation_dict_path),
    }
    if selected_frequency_db is None or not selected_frequency_db.exists():
        inputs["status"] = "review"
        inputs["reason"] = "frequency_db_missing"
        inputs["seed_row_count"] = 0
        inputs["unique_target_count"] = 0
        return [], inputs
    if capability.requires_jmdict_for_seed and (jmdict_path is None or not jmdict_path.exists()):
        inputs["status"] = "review"
        inputs["reason"] = "jmdict_required_but_missing"
        inputs["seed_row_count"] = 0
        inputs["unique_target_count"] = 0
        return [], inputs

    seeds = build_seed_candidates(
        frequency_db=selected_frequency_db,
        config=SeedSelectionConfig(
            language_pair=capability.pair,
            top_n=max(1, int(top_n)),
            jmdict_path=jmdict_path,
            require_jmdict=bool(capability.requires_jmdict_for_seed),
            stopwords_path=stopwords_path,
            admission_pos_weights=resolve_default_pos_weights(language_pair=capability.pair),
        ),
    )
    rows: list[Mapping[str, object]] = []
    for seed_rank, seed in enumerate(seeds, start=1):
        rows.append(
            {
                "lemma": seed.lemma,
                "seed_rank": seed_rank,
                "core_rank": seed.core_rank,
                "pmw": seed.pmw,
                "pos": seed.pos,
                "pos_raw": seed.pos_raw,
                "pos_bucket": seed.pos_bucket,
                "pos_weight": seed.pos_weight,
                "base_weight": seed.base_weight,
                "admission_weight": seed.admission_weight,
                "word_package": seed.word_package or {},
            }
        )
    unique_rows = _dedupe_rows_by_key(rows, key_name="lemma")
    inputs["seed_row_count"] = len(rows)
    inputs["unique_target_count"] = len(unique_rows)
    return unique_rows, inputs


def build_full_rulegen_source_target_pairs(
    *,
    pair: str,
    full_srs_rows: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    normalized_pair = str(pair or DEFAULT_PAIR).strip().lower() or DEFAULT_PAIR
    paths = build_helper_paths()
    capability = resolve_pair_capability(normalized_pair)
    jmdict_path, translation_dict_path, _frequency_db = resolve_pair_resources(
        paths,
        pair=normalized_pair,
        jmdict_path=None,
        translation_dict_path=None,
        set_source_db=None,
    )
    reverse_translation_dict_path = default_reverse_translation_dictionary_path(
        capability.pair,
        language_packs_dir=paths.language_packs_dir,
    )
    targets = [
        str(row.get("lemma") or "").strip()
        for row in full_srs_rows
        if str(row.get("lemma") or "").strip()
    ]
    targets = sorted(dict.fromkeys(targets))
    inputs: dict[str, object] = {
        "status": "ok",
        "pair": capability.pair,
        "target_count": len(targets),
        "translation_dict_path": _repo_path(translation_dict_path),
        "translation_dict_exists": bool(translation_dict_path and translation_dict_path.exists()),
        "reverse_translation_dict_path": _repo_path(reverse_translation_dict_path),
        "reverse_translation_dict_exists": bool(
            reverse_translation_dict_path and reverse_translation_dict_path.exists()
        ),
        "jmdict_path": _repo_path(jmdict_path),
    }
    if not targets:
        inputs["status"] = "review"
        inputs["reason"] = "full_srs_targets_missing"
        inputs["rule_count"] = 0
        inputs["source_target_pair_count"] = 0
        return [], inputs
    if translation_dict_path is None or not translation_dict_path.exists():
        inputs["status"] = "review"
        inputs["reason"] = "translation_dict_missing"
        inputs["rule_count"] = 0
        inputs["source_target_pair_count"] = 0
        return [], inputs

    tuning = resolve_rulegen_tuning(capability.pair)
    word_packages_by_target = {
        str(row.get("lemma") or "").strip(): dict(_as_mapping(row.get("word_package")))
        for row in full_srs_rows
        if str(row.get("lemma") or "").strip() and _as_mapping(row.get("word_package"))
    }
    start = perf_counter()
    rules = run_rules_with_adapter(
        RulegenAdapterRequest(
            pair=capability.pair,
            targets=targets,
            language_pair=capability.pair,
            confidence_threshold=tuning.confidence_threshold,
            max_definitions_per_target=tuning.max_definitions_per_target,
            max_rules_per_target=tuning.max_rules_per_target,
            semantic_demotion_scale=tuning.semantic_demotion_scale,
            include_variants=tuning.include_variants,
            allow_multiword_glosses=tuning.allow_multiword_glosses,
            scoring=tuning.scoring,
            reverse_check=tuning.reverse_check,
            enable_exact_gloss_demotions=tuning.enable_exact_gloss_demotions,
            jmdict_path=jmdict_path,
            translation_dict_path=translation_dict_path,
            reverse_translation_dict_path=reverse_translation_dict_path,
            word_packages_by_target=word_packages_by_target or None,
        )
    )
    elapsed_seconds = perf_counter() - start
    pairs = _dedupe_source_target_pairs(
        {"source": rule.source_phrase, "target": rule.replacement} for rule in rules
    )
    inputs["rule_count"] = len(rules)
    inputs["source_target_pair_count"] = len(pairs)
    inputs["elapsed_seconds"] = round(elapsed_seconds, 3)
    return pairs, inputs


def _target_scope(
    scope_id: str,
    rows: Sequence[Mapping[str, object]],
    *,
    weight_key: str | None = None,
) -> dict[str, object]:
    terms = [
        str(row.get("lemma") or "").strip() for row in rows if str(row.get("lemma") or "").strip()
    ]
    weights_by_term: dict[str, float] = defaultdict(float)
    if weight_key:
        for row in rows:
            term = str(row.get("lemma") or "").strip()
            if term:
                weights_by_term[term] += _safe_float(row.get(weight_key))
    return _scope_from_terms(
        scope_id=scope_id,
        terms=terms,
        language="es",
        term_label="target",
        weights_by_term=weights_by_term,
    )


def _source_scope(
    scope_id: str,
    rows: Sequence[Mapping[str, object]],
    *,
    preview_only: bool,
) -> dict[str, object]:
    terms = [
        str(row.get("source") or "").strip() for row in rows if str(row.get("source") or "").strip()
    ]
    scope = _scope_from_terms(
        scope_id=scope_id,
        terms=terms,
        language="en",
        term_label="source",
    )
    scope["preview_only"] = preview_only
    return scope


def _scope_from_terms(
    *,
    scope_id: str,
    terms: Sequence[str],
    language: str,
    term_label: str,
    weights_by_term: Mapping[str, float] | None = None,
) -> dict[str, object]:
    unique_terms = sorted({term for term in terms if term})
    weights_by_term = weights_by_term or {}
    total_weight = sum(float(value) for value in weights_by_term.values() if value)
    by_band: dict[str, list[str]] = defaultdict(list)
    weight_by_band: Counter[str] = Counter()
    for term in unique_terms:
        band = _zipf_band(_zipf_frequency(term, language))
        by_band[band].append(term)
        weight_by_band[band] += float(weights_by_term.get(term) or 0.0)
    breakdowns = []
    for band in ZIPF_BANDS:
        band_terms = sorted(by_band.get(band, []))
        count = len(band_terms)
        breakdowns.append(
            {
                "scope_id": scope_id,
                "zipf_band": band,
                f"{term_label}_count": count,
                "share": _ratio(count, len(unique_terms)),
                "weight_sum": round(float(weight_by_band.get(band) or 0.0), 6),
                "weight_share": _ratio(float(weight_by_band.get(band) or 0.0), total_weight)
                if total_weight
                else None,
                "sample_terms": band_terms[:12],
            }
        )
    return {
        "scope_id": scope_id,
        "language": language,
        "term_label": term_label,
        "term_count": len(unique_terms),
        "weight_sum": round(total_weight, 6) if total_weight else None,
        "breakdowns": breakdowns,
    }


def _source_target_matrix(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    pairs = sorted(
        {
            (
                str(row.get("source") or "").strip(),
                str(row.get("target") or "").strip(),
            )
            for row in rows
            if str(row.get("source") or "").strip() and str(row.get("target") or "").strip()
        }
    )
    grouped: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for source, target in pairs:
        source_band = _zipf_band(_zipf_frequency(source, "en"))
        target_band = _zipf_band(_zipf_frequency(target, "es"))
        grouped[(source_band, target_band)].append((source, target))
    output = []
    total = len(pairs)
    for source_band in ZIPF_BANDS:
        for target_band in ZIPF_BANDS:
            bucket = grouped.get((source_band, target_band), [])
            if not bucket:
                continue
            output.append(
                {
                    "source_zipf_band_en": source_band,
                    "target_zipf_band_es": target_band,
                    "family_count": len(bucket),
                    "share": _ratio(len(bucket), total),
                    "sample_families": [
                        {"source": source, "target": target} for source, target in bucket[:12]
                    ],
                }
            )
    return output


def _annotated_source_target_pairs(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    output = []
    for row in _dedupe_source_target_pairs(rows):
        source = str(row.get("source") or "").strip()
        target = str(row.get("target") or "").strip()
        source_zipf = _zipf_frequency(source, "en")
        target_zipf = _zipf_frequency(target, "es")
        output.append(
            {
                "source": source,
                "target": target,
                "source_zipf_frequency_en": source_zipf,
                "source_zipf_band_en": _zipf_band(source_zipf),
                "target_zipf_frequency_es": target_zipf,
                "target_zipf_band_es": _zipf_band(target_zipf),
            }
        )
    return output


def _source_target_pairs(phases: Sequence[Mapping[str, object]]) -> list[dict[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for phase in phases:
        runtime = _as_mapping(phase.get("runtime"))
        for row in _mapping_rows(runtime.get("ruleset_source_target_pairs")):
            source = str(row.get("source") or row.get("source_phrase") or "").strip()
            target = str(row.get("target") or row.get("replacement") or "").strip()
            if source and target:
                pairs.add((source, target))
    return [{"source": source, "target": target} for source, target in sorted(pairs)]


def _dedupe_source_target_pairs(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    pairs: set[tuple[str, str]] = set()
    for row in rows:
        source = str(row.get("source") or row.get("source_phrase") or "").strip()
        target = str(row.get("target") or row.get("replacement") or "").strip()
        if source and target:
            pairs.add((source, target))
    return [{"source": source, "target": target} for source, target in sorted(pairs)]


def _source_preview_rows(phases: Sequence[Mapping[str, object]]) -> list[dict[str, str]]:
    sources: set[str] = set()
    for phase in phases:
        runtime = _as_mapping(phase.get("runtime"))
        raw_sources = runtime.get("ruleset_sources") or runtime.get("ruleset_sources_preview") or []
        for source in raw_sources if isinstance(raw_sources, Sequence) else []:
            text = str(source or "").strip()
            if text:
                sources.add(text)
    return [{"source": source} for source in sorted(sources)]


def _source_mapping_status(
    *,
    source_target_pairs: Sequence[Mapping[str, object]],
    source_trigger_rows: Sequence[Mapping[str, object]],
    source_preview_rows: Sequence[Mapping[str, object]],
) -> str:
    if source_target_pairs:
        return "source_target_pairs_available"
    if source_trigger_rows:
        return "source_triggers_available_without_targets"
    if source_preview_rows:
        return "preview_only_sources_without_targets"
    return "missing"


def _sum_band_counts(scope: Mapping[str, object], *, bands: set[str]) -> int:
    total = 0
    for row in _mapping_rows(scope.get("breakdowns")):
        if str(row.get("zipf_band") or "") in bands:
            total += int(row.get("target_count") or row.get("source_count") or 0)
    return total


def _zipf_frequency(term: str, language: str) -> float | None:
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        return None
    value = _safe_float(zipf_frequency(term, language))
    return value if value > 0 else None


def _zipf_band(value: float | None) -> str:
    if value is None or value <= 0:
        return "missing"
    if value >= 5.0:
        return "zipf_5_plus_very_common"
    if value >= 4.0:
        return "zipf_4_to_5_common"
    if value >= 3.0:
        return "zipf_3_to_4_mid"
    return "zipf_below_3_rare"


def _dedupe_rows_by_key(
    rows: Sequence[Mapping[str, object]],
    *,
    key_name: str,
) -> list[Mapping[str, object]]:
    by_key: dict[str, Mapping[str, object]] = {}
    for row in rows:
        key = str(row.get(key_name) or "").strip()
        if key and key not in by_key:
            by_key[key] = row
    return [by_key[key] for key in sorted(by_key)]


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return round(float(numerator) / float(denominator), 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
