#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

from semantic_veto_difficulty_stratification_common import (
    COUNT_BIN_ORDER,
    RANK_BIN_ORDER,
    SOURCE_ZIPF_BIN_ORDER,
    _optional_float as _optional_float,
    _utc_now,
)
from semantic_veto_difficulty_stratification_frequency import (
    FrequencyLookup as FrequencyLookup,
    _frequency_public,
    _source_zipf_status,
)
from semantic_veto_difficulty_stratification_rendering import (
    render_difficulty_stratification_markdown as render_difficulty_stratification_markdown,
)
from semantic_veto_difficulty_stratification_rows import (
    _build_family_index,
    _llm_case_rows,
    _policy_case_rows,
    _rank_bin as _rank_bin,
)
from semantic_veto_difficulty_stratification_summary import (
    _breakdowns,
    _decision,
    _failure_rows,
    _key_findings,
    _limitations,
    _metadata_diagnostics,
    _metrics,
    _next_steps,
    _trigger_risk_summary,
)
from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md as _escape_md,
    _load_json,
    _repo_path as _repo_path,
    _resolve_repo_path as _resolve_repo_path,
    _utility_weights,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
SEMANTIC_CASES_ROOT = TEST_INPUTS_ROOT / "semantic_routing_cases"

DEFAULT_POLICY = TEST_INPUTS_ROOT / "semantic_veto_product_quality_policy_en_es.json"
DEFAULT_LLM_PLAN = TEST_INPUTS_ROOT / "semantic_veto_llm_pilot_plan_en_es.json"
DEFAULT_V10_DATASET = SEMANTIC_CASES_ROOT / "en_es_sentence_veto_v10.json"
DEFAULT_WAVE7_DATASET = (
    TEST_OUTPUTS_ROOT
    / "experiments"
    / "semantic_non_v10_wave_drafts"
    / "en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json"
)
DEFAULT_LLM_SCORING = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_scoring_en_es_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_difficulty_stratification_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_difficulty_stratification_en_es_latest.md"
DEFAULT_FREQUENCY_PACK_DIR = (
    Path.home() / "Library" / "Application Support" / "LexiShift" / "LexiShift" / "frequency_packs"
)
DEFAULT_SOURCE_FREQUENCY_DB = DEFAULT_FREQUENCY_PACK_DIR / "freq-en-coca.sqlite"
DEFAULT_TARGET_FREQUENCY_DB = DEFAULT_FREQUENCY_PACK_DIR / "freq-es-cde.sqlite"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stratify current en-es semantic-veto evaluation rows by source-trigger "
            "rank, target-rank proxy, ambiguity metadata, and score-surface risk."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--llm-scoring-json", type=Path, default=DEFAULT_LLM_SCORING)
    parser.add_argument("--llm-plan-json", type=Path, default=DEFAULT_LLM_PLAN)
    parser.add_argument("--v10-dataset-json", type=Path, default=DEFAULT_V10_DATASET)
    parser.add_argument("--wave7-dataset-json", type=Path, default=DEFAULT_WAVE7_DATASET)
    parser.add_argument("--source-frequency-db", type=Path, default=DEFAULT_SOURCE_FREQUENCY_DB)
    parser.add_argument("--target-frequency-db", type=Path, default=DEFAULT_TARGET_FREQUENCY_DB)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    source_frequency = FrequencyLookup.from_sqlite(
        path=args.source_frequency_db,
        language="en",
    )
    target_frequency = FrequencyLookup.from_sqlite(
        path=args.target_frequency_db,
        language="es",
    )
    report = build_difficulty_stratification_report(
        policy_payload=_load_json(args.policy_json),
        llm_scoring_payload=_load_json(args.llm_scoring_json),
        llm_plan_payload=_load_optional_json(args.llm_plan_json),
        v10_dataset_payload=_load_optional_json(args.v10_dataset_json),
        wave7_dataset_payload=_load_optional_json(args.wave7_dataset_json),
        source_frequency=source_frequency,
        target_frequency=target_frequency,
        policy_path=args.policy_json,
        llm_scoring_path=args.llm_scoring_json,
        llm_plan_path=args.llm_plan_json,
        v10_dataset_path=args.v10_dataset_json,
        wave7_dataset_path=args.wave7_dataset_json,
        top_n=max(1, int(args.top_n)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(
        render_difficulty_stratification_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_difficulty_stratification_report(
    *,
    policy_payload: Mapping[str, object],
    llm_scoring_payload: Mapping[str, object] | None = None,
    llm_plan_payload: Mapping[str, object] | None = None,
    v10_dataset_payload: Mapping[str, object] | None = None,
    wave7_dataset_payload: Mapping[str, object] | None = None,
    source_frequency: FrequencyLookup | None = None,
    target_frequency: FrequencyLookup | None = None,
    source_zipf_by_trigger: Mapping[str, float] | None = None,
    policy_path: Path | None = None,
    llm_scoring_path: Path | None = None,
    llm_plan_path: Path | None = None,
    v10_dataset_path: Path | None = None,
    wave7_dataset_path: Path | None = None,
    top_n: int = 12,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    source_frequency = source_frequency or FrequencyLookup.from_records(
        language="en",
        rows={},
    )
    target_frequency = target_frequency or FrequencyLookup.from_records(
        language="es",
        rows={},
    )
    source_zipf_status = _source_zipf_status(source_zipf_by_trigger)
    weights = _utility_weights(policy_payload)
    acceptance = _as_mapping(policy_payload.get("acceptance"))
    family_index = _build_family_index(
        llm_plan_payload=llm_plan_payload or {},
        llm_scoring_payload=llm_scoring_payload or {},
        v10_dataset_payload=v10_dataset_payload or {},
        wave7_dataset_payload=wave7_dataset_payload or {},
    )
    policy_rows, policy_sources = _policy_case_rows(
        policy_payload=policy_payload,
        family_index=family_index,
        source_frequency=source_frequency,
        target_frequency=target_frequency,
        source_zipf_by_trigger=source_zipf_by_trigger,
        source_zipf_status=source_zipf_status,
    )
    llm_rows = _llm_case_rows(
        llm_scoring_payload=llm_scoring_payload or {},
        family_index=family_index,
        source_frequency=source_frequency,
        target_frequency=target_frequency,
        source_zipf_by_trigger=source_zipf_by_trigger,
        source_zipf_status=source_zipf_status,
    )
    all_rows = [*policy_rows, *llm_rows]
    overall = _metrics(all_rows, weights=weights, acceptance=acceptance)
    lane_breakdowns = _breakdowns(
        all_rows,
        key="lane_id",
        weights=weights,
        acceptance=acceptance,
    )
    source_rank_breakdowns = _breakdowns(
        all_rows,
        key="source_trigger_rank_bin_en",
        weights=weights,
        acceptance=acceptance,
        order=RANK_BIN_ORDER,
    )
    source_zipf_breakdowns = _breakdowns(
        all_rows,
        key="source_zipf_band_en",
        weights=weights,
        acceptance=acceptance,
        order=SOURCE_ZIPF_BIN_ORDER,
    )
    target_rank_breakdowns = _breakdowns(
        all_rows,
        key="target_lemma_rank_bin_es",
        weights=weights,
        acceptance=acceptance,
        order=RANK_BIN_ORDER,
    )
    ambiguity_breakdowns = _breakdowns(
        all_rows,
        key="declared_ambiguity_class",
        weights=weights,
        acceptance=acceptance,
    )
    wordnet_sense_breakdowns = _breakdowns(
        all_rows,
        key="wordnet_sense_count_bin",
        weights=weights,
        acceptance=acceptance,
        order=COUNT_BIN_ORDER,
    )
    translation_candidate_breakdowns = _breakdowns(
        all_rows,
        key="translation_candidate_count_bin",
        weights=weights,
        acceptance=acceptance,
        order=COUNT_BIN_ORDER,
    )
    shadow_margin_breakdowns = _breakdowns(
        all_rows,
        key="shadow_lead_bin",
        weights=weights,
        acceptance=acceptance,
    )
    phrase_margin_breakdowns = _breakdowns(
        all_rows,
        key="phrase_lead_bin",
        weights=weights,
        acceptance=acceptance,
    )
    diagnostics = _metadata_diagnostics(all_rows)
    decision = _decision(
        row_count=len(all_rows),
        source_frequency=source_frequency,
        target_frequency=target_frequency,
    )
    return {
        "schema_version": 1,
        "status": decision["status"],
        "decision": decision["decision"],
        "generated_at": generated_at,
        "pair": str(policy_payload.get("pair") or "en-es"),
        "policy": {
            "path": _repo_path(policy_path),
            "policy_id": str(policy_payload.get("policy_id") or ""),
            "acceptance": dict(acceptance),
            "utility_weights": weights,
        },
        "inputs": {
            "policy_path": _repo_path(policy_path),
            "llm_scoring_path": _repo_path(llm_scoring_path),
            "llm_plan_path": _repo_path(llm_plan_path),
            "v10_dataset_path": _repo_path(v10_dataset_path),
            "wave7_dataset_path": _repo_path(wave7_dataset_path),
            "policy_report_sources": policy_sources,
            "source_frequency": _frequency_public(source_frequency),
            "target_frequency": _frequency_public(target_frequency),
            "source_zipf_status": source_zipf_status,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
            "rank_interpretation": (
                "English source-trigger rank is a veto-risk proxy; Spanish target rank is "
                "a learner-difficulty proxy. Missing metadata is retained as a measured gap."
            ),
            "llm_lane_role": "current generated-evaluation pilot, not representative browsing proof",
        },
        "e2e_checks": {
            "policy_case_rows_read": len(policy_rows),
            "llm_case_rows_read": len(llm_rows),
            "total_case_rows": len(all_rows),
            "unique_families": len({row["family_id"] for row in all_rows if row["family_id"]}),
            "unique_triggers": len({row["trigger"] for row in all_rows if row["trigger"]}),
            "source_rank_known_rows": diagnostics["source_rank_known_rows"],
            "target_rank_known_rows": diagnostics["target_rank_known_rows"],
            "source_frequency_status": source_frequency.status,
            "target_frequency_status": target_frequency.status,
            "source_zipf_status": source_zipf_status,
            "source_zipf_known_rows": diagnostics["source_zipf_known_rows"],
        },
        "summary": {
            "overall": overall,
            "lane_count": len(lane_breakdowns),
            "case_count": len(all_rows),
            "metadata_diagnostics": diagnostics,
            "top_n": max(1, int(top_n)),
            "key_findings": _key_findings(
                rows=all_rows,
                overall=overall,
                diagnostics=diagnostics,
            ),
        },
        "lane_breakdowns": lane_breakdowns,
        "source_trigger_rank_breakdowns_en": source_rank_breakdowns,
        "source_zipf_breakdowns_en": source_zipf_breakdowns,
        "target_lemma_rank_breakdowns_es": target_rank_breakdowns,
        "declared_ambiguity_breakdowns": ambiguity_breakdowns,
        "wordnet_sense_count_breakdowns": wordnet_sense_breakdowns,
        "translation_candidate_count_breakdowns": translation_candidate_breakdowns,
        "shadow_lead_breakdowns": shadow_margin_breakdowns,
        "phrase_lead_breakdowns": phrase_margin_breakdowns,
        "trigger_risk_summary": _trigger_risk_summary(all_rows, top_n=top_n),
        "failure_rows": _failure_rows(all_rows, top_n=top_n),
        "case_traces": all_rows,
        "limitations": _limitations(
            source_frequency=source_frequency,
            target_frequency=target_frequency,
            diagnostics=diagnostics,
        ),
        "next_steps": _next_steps(diagnostics),
    }


def _load_optional_json(path: Path) -> dict[str, object]:
    if not Path(path).exists():
        return {}
    return _load_json(path)


if __name__ == "__main__":
    raise SystemExit(main())
