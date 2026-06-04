#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
GUI_SRC_ROOT = PROJECT_ROOT / "apps" / "gui" / "src"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXAMPLE_FRAME_BATCH_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
WAVE_DRAFT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_non_v10_wave_drafts"
for candidate in (str(CORE_ROOT), str(GUI_SRC_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from semantic_non_v10_wave_builder_en_es import (  # noqa: E402
    DEFAULT_CANDIDATE_JSON,
    DEFAULT_MAX_SENSE_COUNT,
    FAMILY_POS_STRATEGIES,
    build_non_v10_wave_draft_report,
)
from semantic_source_admission_cycle_en_es import (  # noqa: E402
    _empty_base_batch,
    build_source_admission_cycle_bundle,
    write_source_admission_cycle_bundle,
)
from semantic_wordnet_example_frame_batch_en_es import (  # noqa: E402
    build_wordnet_example_frame_bundle,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_PREFIX = "semantic_non_v10_source_portfolio_wave5_anypos_latest"
DEFAULT_SWEEP_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_non_v10_wave_admission_sweep_wave64_anypos_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / f"{DEFAULT_PREFIX}.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / f"{DEFAULT_PREFIX}.md"
DEFAULT_SELECTED_DATASET_OUT = (
    WAVE_DRAFT_ROOT
    / "en_es_source_non_v10_wave5_anypos_source_portfolio_materialized_v1_dataset.json"
)
DEFAULT_SELECTED_QUEUE_OUT = (
    WAVE_DRAFT_ROOT
    / "semantic_source_non_v10_wave5_anypos_source_portfolio_materialized_queue_en_es_v1.json"
)
DEFAULT_CANDIDATE_BATCH_OUT = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-wordnet-source-portfolio-non-v10-wave5-anypos-v1-latest_normalized_evidence.json"
)
DEFAULT_CYCLE_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_source_admission_cycle_non_v10_wave5_source_portfolio_latest.json"
)
DEFAULT_CYCLE_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_source_admission_cycle_non_v10_wave5_source_portfolio_latest.md"
)
DEFAULT_FILTERED_BATCH_OUT = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-wordnet-source-portfolio-non-v10-wave5-anypos-v1-latest_cycle_filtered_normalized_evidence.json"
)
DEFAULT_SENSE_BATCH_OUT = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-wordnet-source-portfolio-non-v10-wave5-anypos-v1-latest_cycle_sense_admitted_normalized_evidence.json"
)
DEFAULT_MERGED_BATCH_OUT = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-wordnet-source-portfolio-non-v10-wave5-anypos-v1-latest_cycle_merged_normalized_evidence.json"
)
DEFAULT_CANDIDATE_ADMITTED_BATCH_OUT = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-wordnet-source-portfolio-non-v10-wave5-anypos-v1-latest_admitted_delta_normalized_evidence.json"
)
DEFAULT_BATCH_ID = "en-es:wordnet-source-portfolio:non-v10-wave5-anypos-v1"
DEFAULT_SOURCE_ID = "wordnet_source_portfolio_non_v10_wave5_anypos_v1"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize the supported-source non-v10 semantic portfolio found by the "
            "admission sweep. The script replays only the variants needed by the selected "
            "portfolio, combines admitted rows family-by-family, and runs the normal "
            "source-admission cycle on the combined batch."
        )
    )
    parser.add_argument("--sweep-json", type=Path, default=DEFAULT_SWEEP_JSON)
    parser.add_argument("--candidate-json", type=Path, default=DEFAULT_CANDIDATE_JSON)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--wiktionary-en-es-sqlite", type=Path, default=None)
    parser.add_argument("--wiktionary-es-en-sqlite", type=Path, default=None)
    parser.add_argument("--freedict-es-en-sqlite", type=Path, default=None)
    parser.add_argument("--wordnet-dir", type=Path, default=None)
    parser.add_argument("--max-sense-count", type=int, default=DEFAULT_MAX_SENSE_COUNT)
    parser.add_argument(
        "--family-pos-strategy",
        choices=FAMILY_POS_STRATEGIES,
        default="any_cross_pos",
    )
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--selected-dataset-out", type=Path, default=DEFAULT_SELECTED_DATASET_OUT)
    parser.add_argument("--selected-queue-out", type=Path, default=DEFAULT_SELECTED_QUEUE_OUT)
    parser.add_argument("--candidate-batch-out", type=Path, default=DEFAULT_CANDIDATE_BATCH_OUT)
    parser.add_argument("--cycle-json-out", type=Path, default=DEFAULT_CYCLE_JSON_OUT)
    parser.add_argument("--cycle-markdown-out", type=Path, default=DEFAULT_CYCLE_MARKDOWN_OUT)
    parser.add_argument("--filtered-batch-out", type=Path, default=DEFAULT_FILTERED_BATCH_OUT)
    parser.add_argument("--sense-batch-out", type=Path, default=DEFAULT_SENSE_BATCH_OUT)
    parser.add_argument("--merged-batch-out", type=Path, default=DEFAULT_MERGED_BATCH_OUT)
    parser.add_argument(
        "--candidate-admitted-batch-out",
        type=Path,
        default=DEFAULT_CANDIDATE_ADMITTED_BATCH_OUT,
    )
    return parser.parse_args()


def build_source_portfolio_materialization_bundle(
    *,
    sweep_report: Mapping[str, object],
    candidate_payload: Mapping[str, object],
    wiktionary_en_es_sqlite: Path,
    wiktionary_es_en_sqlite: Path | None,
    freedict_es_en_sqlite: Path | None,
    wordnet_dir: Path,
    max_sense_count: int = DEFAULT_MAX_SENSE_COUNT,
    family_pos_strategy: str = "any_cross_pos",
    batch_id: str = DEFAULT_BATCH_ID,
    source_id: str = DEFAULT_SOURCE_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    sweep_selected_dataset = _as_mapping(sweep_report.get("admission_selected_dataset"))
    sweep_selected_queue = _as_mapping(sweep_report.get("admission_selected_queue"))
    selected_keys = [
        str(item or "").strip()
        for item in _as_mapping(sweep_report.get("semantic_portfolio")).get(
            "admission_selected_family_keys", ()
        )
        if str(item or "").strip()
    ]
    best_variant_id = str(
        _as_mapping(sweep_report.get("summary")).get("best_variant_id") or ""
    ).strip()
    variant_specs = _variant_specs_by_id(sweep_report.get("variant_rows", ()))
    chosen_variant_by_family = _choose_supporting_variants(
        selected_keys=selected_keys,
        support_by_family=_as_mapping(
            _as_mapping(sweep_report.get("semantic_portfolio")).get(
                "supporting_variant_ids_by_family_key"
            )
        ),
        best_variant_id=best_variant_id,
    )
    required_variant_ids = sorted(set(chosen_variant_by_family.values()))
    variant_batches = _replay_variant_batches(
        variant_ids=required_variant_ids,
        variant_specs=variant_specs,
        candidate_payload=candidate_payload,
        wiktionary_en_es_sqlite=wiktionary_en_es_sqlite,
        wiktionary_es_en_sqlite=wiktionary_es_en_sqlite,
        freedict_es_en_sqlite=freedict_es_en_sqlite,
        wordnet_dir=wordnet_dir,
        max_sense_count=max_sense_count,
        family_pos_strategy=family_pos_strategy,
        generated_at=generated_at,
    )
    selected_dataset, selected_queue = _materialized_selected_payloads(
        selected_keys=selected_keys,
        chosen_variant_by_family=chosen_variant_by_family,
        variant_batches=variant_batches,
        sweep_selected_dataset=sweep_selected_dataset,
        sweep_selected_queue=sweep_selected_queue,
        generated_at=generated_at,
    )
    portfolio_batch, family_rows = _materialized_candidate_batch(
        selected_keys=selected_keys,
        chosen_variant_by_family=chosen_variant_by_family,
        variant_batches=variant_batches,
        selected_dataset=selected_dataset,
        batch_id=batch_id,
        source_id=source_id,
        generated_at=generated_at,
    )
    cycle_bundle = build_source_admission_cycle_bundle(
        dataset_payload=selected_dataset,
        queue_payload=selected_queue,
        required_family_payload=selected_dataset,
        base_batch_payload=_empty_base_batch(generated_at=generated_at),
        candidate_batch_payload=portfolio_batch,
        batch_id=f"{batch_id}:cycle",
        source_id=source_id,
        run_ablation=False,
        generated_at=generated_at,
    )
    report = _materialization_report(
        generated_at=generated_at,
        sweep_report=sweep_report,
        selected_keys=selected_keys,
        chosen_variant_by_family=chosen_variant_by_family,
        family_rows=family_rows,
        portfolio_batch=portfolio_batch,
        cycle_report=_as_mapping(cycle_bundle.get("report")),
    )
    return {
        "report": report,
        "selected_dataset": selected_dataset,
        "selected_queue": selected_queue,
        "candidate_batch": portfolio_batch,
        "cycle_bundle": cycle_bundle,
    }


def write_source_portfolio_materialization_bundle(
    *,
    bundle: Mapping[str, object],
    json_out: Path,
    markdown_out: Path,
    selected_dataset_out: Path,
    selected_queue_out: Path,
    candidate_batch_out: Path,
    cycle_json_out: Path,
    cycle_markdown_out: Path,
    filtered_batch_out: Path,
    sense_batch_out: Path,
    merged_batch_out: Path,
    candidate_admitted_batch_out: Path,
) -> None:
    _write_json(selected_dataset_out, _as_mapping(bundle.get("selected_dataset")))
    _write_json(selected_queue_out, _as_mapping(bundle.get("selected_queue")))
    _write_json(candidate_batch_out, _as_mapping(bundle.get("candidate_batch")))
    cycle_bundle = _as_mapping(bundle.get("cycle_bundle"))
    write_source_admission_cycle_bundle(
        bundle=cycle_bundle,
        json_out=cycle_json_out,
        markdown_out=cycle_markdown_out,
        filtered_batch_out=filtered_batch_out,
        sense_batch_out=sense_batch_out,
        merged_batch_out=merged_batch_out,
        candidate_admitted_batch_out=candidate_admitted_batch_out,
    )
    report = dict(_as_mapping(bundle.get("report")))
    report["artifacts"] = {
        **_as_mapping(report.get("artifacts")),
        "selected_dataset_json": str(selected_dataset_out),
        "selected_queue_json": str(selected_queue_out),
        "candidate_batch_json": str(candidate_batch_out),
        "cycle_json": str(cycle_json_out),
        "cycle_markdown": str(cycle_markdown_out),
        "cycle_sense_batch_json": str(sense_batch_out),
        "cycle_candidate_admitted_batch_json": str(candidate_admitted_batch_out),
    }
    _write_json(json_out, report)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(
        render_source_portfolio_materialization_markdown(report), encoding="utf-8"
    )


def render_source_portfolio_materialization_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Non-v10 Source Portfolio Materialization",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Selected families: `{summary.get('selected_family_count', 0)}`",
        f"- Materialized families: `{summary.get('materialized_family_count', 0)}`",
        f"- Candidate rows: `{summary.get('candidate_row_count', 0)}`",
        f"- Final admitted rows: `{summary.get('final_admitted_row_count', 0)}`",
        f"- Semantic contract: `{summary.get('semantic_contract_complete_family_count', 0)}` / `{summary.get('selected_family_count', 0)}`",
        f"- Phrase contract: `{summary.get('phrase_contract_complete_family_count', 0)}` / `{summary.get('selected_family_count', 0)}`",
        f"- Supporting variants used: `{summary.get('supporting_variant_count', 0)}`",
        "",
        "## Family Selection",
        "",
        _family_table(report.get("families", ())),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    lines.extend(["", "## Artifacts", ""])
    for label, path in _as_mapping(report.get("artifacts")).items():
        lines.append(f"- {label}: `{path}`")
    return "\n".join(lines) + "\n"


def _choose_supporting_variants(
    *,
    selected_keys: Sequence[str],
    support_by_family: Mapping[str, object],
    best_variant_id: str,
) -> dict[str, str]:
    choices: dict[str, str] = {}
    for family_key in selected_keys:
        options = [str(item or "").strip() for item in support_by_family.get(family_key, ())]
        options = [item for item in options if item]
        if not options:
            raise ValueError(f"No supporting variant recorded for selected family: {family_key}")
        choices[family_key] = best_variant_id if best_variant_id in options else options[0]
    return choices


def _variant_specs_by_id(rows: object) -> dict[str, dict[str, object]]:
    specs: dict[str, dict[str, object]] = {}
    for row in _as_sequence(rows):
        if not isinstance(row, Mapping):
            continue
        variant_id = str(row.get("variant_id") or "").strip()
        if not variant_id:
            continue
        specs[variant_id] = {
            "min_link_score": float(row.get("min_link_score") or 0.0),
            "extraction_min_link_score": float(row.get("extraction_min_link_score") or 0.0),
            "evidence_mode": str(row.get("evidence_mode") or "").strip(),
            "max_rows_per_sense": int(row.get("max_rows_per_sense") or 1),
        }
    return specs


def _replay_variant_batches(
    *,
    variant_ids: Sequence[str],
    variant_specs: Mapping[str, Mapping[str, object]],
    candidate_payload: Mapping[str, object],
    wiktionary_en_es_sqlite: Path,
    wiktionary_es_en_sqlite: Path | None,
    freedict_es_en_sqlite: Path | None,
    wordnet_dir: Path,
    max_sense_count: int,
    family_pos_strategy: str,
    generated_at: str,
) -> dict[str, Mapping[str, object]]:
    wordnet_index = WordNetIndex.load(wordnet_dir)
    batches: dict[str, Mapping[str, object]] = {}
    wave_reports: dict[float, Mapping[str, object]] = {}
    for variant_id in variant_ids:
        spec = variant_specs.get(variant_id)
        if spec is None:
            raise ValueError(f"Variant row missing from sweep report: {variant_id}")
        min_link_score = float(spec.get("min_link_score") or 0.0)
        wave_report = wave_reports.get(min_link_score)
        if wave_report is None:
            wave_report = build_non_v10_wave_draft_report(
                candidate_payload=candidate_payload,
                wiktionary_en_es_sqlite=wiktionary_en_es_sqlite,
                wiktionary_es_en_sqlite=wiktionary_es_en_sqlite,
                freedict_es_en_sqlite=freedict_es_en_sqlite,
                wordnet_index=wordnet_index,
                wave_id=f"source_non_v10_portfolio_min{_score_slug(min_link_score)}",
                wave_size=int(_as_mapping(spec).get("selected_family_count") or 64),
                max_sense_count=max_sense_count,
                min_wordnet_link_score=min_link_score,
                require_translation_support=True,
                family_pos_strategy=family_pos_strategy,
                generated_at=generated_at,
            )
            wave_reports[min_link_score] = wave_report
        dataset_payload = _as_mapping(wave_report.get("draft_dataset"))
        queue_payload = _as_mapping(wave_report.get("draft_queue"))
        wordnet_bundle = build_wordnet_example_frame_bundle(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            wordnet_dir=wordnet_dir,
            run_id=f"non-v10-source-portfolio-{variant_id}",
            scope="all_dataset_families",
            min_link_score=float(spec.get("extraction_min_link_score") or 0.0),
            max_rows_per_sense=int(spec.get("max_rows_per_sense") or 1),
            evidence_mode=str(spec.get("evidence_mode") or ""),
            generated_at=generated_at,
        )
        normalized_batch = _as_mapping(wordnet_bundle.get("normalized_batch"))
        admission_bundle = build_source_admission_cycle_bundle(
            dataset_payload=dataset_payload,
            queue_payload=queue_payload,
            required_family_payload=dataset_payload,
            base_batch_payload=_empty_base_batch(generated_at=generated_at),
            candidate_batch_payload=normalized_batch,
            batch_id=f"en-es:{variant_id}:source-portfolio-replay",
            source_id=f"non_v10_source_portfolio_{variant_id}",
            run_ablation=False,
            generated_at=generated_at,
        )
        batches[variant_id] = {
            "dataset_payload": dataset_payload,
            "queue_payload": queue_payload,
            "candidate_admitted_batch": _as_mapping(
                admission_bundle.get("candidate_admitted_batch")
            ),
        }
    return batches


def _materialized_selected_payloads(
    *,
    selected_keys: Sequence[str],
    chosen_variant_by_family: Mapping[str, str],
    variant_batches: Mapping[str, Mapping[str, object]],
    sweep_selected_dataset: Mapping[str, object],
    sweep_selected_queue: Mapping[str, object],
    generated_at: str,
) -> tuple[dict[str, object], dict[str, object]]:
    family_payloads: list[dict[str, object]] = []
    for family_key in selected_keys:
        variant_id = chosen_variant_by_family.get(family_key, "")
        dataset_payload = _as_mapping(variant_batches.get(variant_id, {}).get("dataset_payload"))
        family_by_key = {
            str(row.get("family_id") or "").strip(): dict(row)
            for row in _as_sequence(dataset_payload.get("families"))
            if isinstance(row, Mapping)
        }
        family = family_by_key.get(family_key)
        if family is None:
            raise ValueError(f"Selected family missing from replayed variant dataset: {family_key}")
        family_payloads.append(family)
    dataset = dict(sweep_selected_dataset)
    dataset.update(
        {
            "generated_at": generated_at,
            "review_state": "draft_source_portfolio_materialized_needs_case_review",
            "source_sweep_selection_strategy": "portfolio_materialized",
            "semantic_complete_family_count": len(family_payloads),
            "families": family_payloads,
        }
    )
    queue_families = []
    for index, family in enumerate(family_payloads, start=1):
        queue_families.append(
            {
                "family_id": str(family.get("family_id") or "").strip(),
                "trigger": str(family.get("trigger") or "").strip(),
                "role": "target",
                "archetype": "automatic_non_v10_source_portfolio_materialized",
                "likely_bucket": "source_coverage_probe",
                "priority_rank": index,
                "review_state": "draft_source_portfolio_materialized_needs_case_review",
            }
        )
    queue = dict(sweep_selected_queue)
    queue.update(
        {
            "generated_at": generated_at,
            "source_sweep_selection_strategy": "portfolio_materialized",
            "families": queue_families,
        }
    )
    return dataset, queue


def _materialized_candidate_batch(
    *,
    selected_keys: Sequence[str],
    chosen_variant_by_family: Mapping[str, str],
    variant_batches: Mapping[str, Mapping[str, object]],
    selected_dataset: Mapping[str, object],
    batch_id: str,
    source_id: str,
    generated_at: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    family_rows: list[dict[str, object]] = []
    trigger_by_family = {
        str(row.get("family_id") or "").strip(): str(row.get("trigger") or "").strip()
        for row in _as_sequence(selected_dataset.get("families"))
        if isinstance(row, Mapping)
    }
    for family_key in selected_keys:
        variant_id = chosen_variant_by_family.get(family_key, "")
        batch_rows = [
            _annotate_portfolio_row(row, variant_id=variant_id, generated_at=generated_at)
            for row in _as_sequence(
                _as_mapping(
                    variant_batches.get(variant_id, {}).get("candidate_admitted_batch")
                ).get("rows")
            )
            if isinstance(row, Mapping)
            and str(_as_mapping(row.get("metadata")).get("family_id") or "").strip() == family_key
        ]
        rows.extend(batch_rows)
        family_rows.append(
            {
                "family_id": family_key,
                "trigger": trigger_by_family.get(family_key, ""),
                "supporting_variant_id": variant_id,
                "row_count": len(batch_rows),
            }
        )
    return (
        {
            "schema_version": 1,
            "normalization_version": "semantic_evidence_v1",
            "batch_id": batch_id,
            "pair": "en-es",
            "source_type": "external",
            "source_id": source_id,
            "source_family": "external_sense_graph",
            "roles": ["cue_generation", "discrimination"],
            "generated_at": generated_at,
            "ingested_at": generated_at,
            "review_state": "draft_source_portfolio_materialized_needs_case_review",
            "model_id": "not_applicable",
            "prompt_version": "wordnet-source-portfolio-v1",
            "row_count": len(rows),
            "rows": rows,
            "provenance": {
                "source_type": "external",
                "source_id": source_id,
                "source_family": "external_sense_graph",
                "selected_family_count": len(selected_keys),
                "supporting_variant_ids": sorted(set(chosen_variant_by_family.values())),
            },
        },
        family_rows,
    )


def _annotate_portfolio_row(
    row: Mapping[str, object], *, variant_id: str, generated_at: str
) -> dict[str, object]:
    payload = dict(row)
    metadata = dict(_as_mapping(payload.get("metadata")))
    metadata["source_portfolio_variant_id"] = variant_id
    payload["metadata"] = metadata
    provenance = dict(_as_mapping(payload.get("provenance")))
    provenance["source_portfolio_materialization"] = {
        "supporting_variant_id": variant_id,
        "generated_at": generated_at,
    }
    payload["provenance"] = provenance
    return payload


def _materialization_report(
    *,
    generated_at: str,
    sweep_report: Mapping[str, object],
    selected_keys: Sequence[str],
    chosen_variant_by_family: Mapping[str, str],
    family_rows: Sequence[Mapping[str, object]],
    portfolio_batch: Mapping[str, object],
    cycle_report: Mapping[str, object],
) -> dict[str, object]:
    cycle_summary = _as_mapping(cycle_report.get("summary"))
    materialized_families = sum(1 for row in family_rows if int(row.get("row_count") or 0) > 0)
    semantic_complete = int(cycle_summary.get("semantic_contract_complete_family_count") or 0)
    status = (
        "ok"
        if materialized_families == len(selected_keys)
        and semantic_complete == len(selected_keys)
        and str(cycle_report.get("status") or "") == "ok"
        else "review"
    )
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "source_portfolio_materialized"
            if status == "ok"
            else "source_portfolio_materialization_needs_review"
        ),
        "generated_at": generated_at,
        "pair": "en-es",
        "source_sweep_json": str(
            _as_mapping(sweep_report.get("artifacts")).get("selected_dataset_json") or ""
        ),
        "summary": {
            "selected_family_count": len(selected_keys),
            "materialized_family_count": materialized_families,
            "candidate_row_count": int(portfolio_batch.get("row_count") or 0),
            "final_admitted_row_count": int(cycle_summary.get("final_admitted_row_count") or 0),
            "semantic_contract_complete_family_count": semantic_complete,
            "phrase_contract_complete_family_count": int(
                cycle_summary.get("phrase_contract_complete_family_count") or 0
            ),
            "supporting_variant_count": len(set(chosen_variant_by_family.values())),
            "sense_rejected_row_count": int(cycle_summary.get("sense_rejected_row_count") or 0),
            "leakage_rejected_row_count": int(cycle_summary.get("leakage_rejected_row_count") or 0),
        },
        "families": [dict(row) for row in family_rows],
        "limitations": [
            "draft_wave_is_unreviewed_and_not_a_promotion_candidate",
            "materialized_rows_are_external_wordnet_evidence_only",
            "phrase_containment_rows_are_not_generated_by_this_lane",
            "independent_active_shadow_and_phrase_heldout_cases_are_still_required",
        ],
        "next_steps": [
            "add independent active/shadow held-out cases for the selected 16 families",
            "add independent phrase/no-winner held-out cases for the same selected families",
            "run held-out validation against this exact materialized source batch",
            "only then compare scoring or runtime-policy promotion claims",
        ],
        "artifacts": {},
    }


def _family_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No family rows were materialized."
    lines = ["| Family | Trigger | Supporting Variant | Rows |", "| --- | --- | --- | ---: |"]
    for row in materialized:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('trigger', '')}`",
                    f"`{row.get('supporting_variant_id', '')}`",
                    str(int(row.get("row_count") or 0)),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _score_slug(value: float) -> str:
    text = f"{float(value):.4f}".rstrip("0").rstrip(".")
    return text.replace(".", "p")


def main() -> int:
    args = _parse_args()
    data_root = args.data_root
    language_pack_root = data_root / "language_packs"
    wiktionary_en_es = (
        args.wiktionary_en_es_sqlite or language_pack_root / "wiktionary-en-es.sqlite"
    )
    wiktionary_es_en = (
        args.wiktionary_es_en_sqlite or language_pack_root / "wiktionary-es-en.sqlite"
    )
    freedict_es_en = (
        args.freedict_es_en_sqlite or language_pack_root / "freedict-es-en" / "main.sqlite"
    )
    wordnet_dir = args.wordnet_dir or language_pack_root / "english-wordnet-2025-json"
    bundle = build_source_portfolio_materialization_bundle(
        sweep_report=_load_json(args.sweep_json),
        candidate_payload=_load_json(args.candidate_json),
        wiktionary_en_es_sqlite=wiktionary_en_es,
        wiktionary_es_en_sqlite=wiktionary_es_en,
        freedict_es_en_sqlite=freedict_es_en,
        wordnet_dir=wordnet_dir,
        max_sense_count=args.max_sense_count,
        family_pos_strategy=args.family_pos_strategy,
        batch_id=args.batch_id,
        source_id=args.source_id,
    )
    write_source_portfolio_materialization_bundle(
        bundle=bundle,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
        selected_dataset_out=args.selected_dataset_out,
        selected_queue_out=args.selected_queue_out,
        candidate_batch_out=args.candidate_batch_out,
        cycle_json_out=args.cycle_json_out,
        cycle_markdown_out=args.cycle_markdown_out,
        filtered_batch_out=args.filtered_batch_out,
        sense_batch_out=args.sense_batch_out,
        merged_batch_out=args.merged_batch_out,
        candidate_admitted_batch_out=args.candidate_admitted_batch_out,
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
