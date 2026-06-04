#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_heuristic_group_pilot_en_es import (  # noqa: E402
    DEFAULT_WORDNET_DIR,
    _wordnet_profile,
)
from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _format_percent,
    _load_json,
    _mapping_rows,
    _repo_path,
    _resolve_repo_path,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_BRIDGE_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.json"
DEFAULT_DIFFICULTY_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_difficulty_stratification_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_representative_sample_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_representative_sample_en_es_latest.md"
)
DEFAULT_SAMPLE_PER_CELL = 2
DEFAULT_SEED = "semantic_veto_full_family_representative_sample_en_es_v1"
SOURCE_ZIPF_BANDS = (
    "zipf_5_plus_very_common",
    "zipf_4_to_5_common",
    "zipf_3_to_4_mid",
    "zipf_below_3_rare",
    "missing",
)
POLYSEMY_BANDS = ("low_1_to_3", "medium_4_to_9", "high_10_plus", "missing")
POS_SHAPES = ("single_sense", "same_pos_polysemy", "cross_pos_polysemy", "missing")
FORBIDDEN_SELECTION_FIELDS = frozenset(
    {
        "gold_decision",
        "gold_winner",
        "gold_winner_type",
        "product_outcome",
        "error_type",
        "predicted_decision",
        "predicted_winner_type",
        "observed_failure_count",
        "negative_allow_count",
        "positive_abstain_count",
    }
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze a representative manual-evaluation sample from the full generated "
            "en-es semantic-veto source-target family denominator."
        )
    )
    parser.add_argument("--srs-zipf-bridge-json", type=Path, default=DEFAULT_BRIDGE_JSON)
    parser.add_argument("--difficulty-json", type=Path, default=DEFAULT_DIFFICULTY_JSON)
    parser.add_argument("--wordnet-dir", type=Path, default=DEFAULT_WORDNET_DIR)
    parser.add_argument("--sample-per-cell", type=int, default=DEFAULT_SAMPLE_PER_CELL)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--include-measured-triggers", action="store_true")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bridge_path = _resolve_repo_path(args.srs_zipf_bridge_json)
    difficulty_path = _resolve_repo_path(args.difficulty_json)
    wordnet_dir = _resolve_repo_path(args.wordnet_dir)
    report = build_full_family_representative_sample_report(
        bridge_payload=_load_json(bridge_path),
        difficulty_payload=_load_json(difficulty_path) if difficulty_path.exists() else {},
        wordnet_index=WordNetIndex.load(wordnet_dir),
        bridge_path=bridge_path,
        difficulty_path=difficulty_path,
        wordnet_dir=wordnet_dir,
        sample_per_cell=max(1, int(args.sample_per_cell)),
        seed=str(args.seed),
        exclude_measured_triggers=not bool(args.include_measured_triggers),
    )
    json_out = _resolve_repo_path(args.json_out)
    markdown_out = _resolve_repo_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_full_family_representative_sample_markdown(report))
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


def build_full_family_representative_sample_report(
    *,
    bridge_payload: Mapping[str, object],
    difficulty_payload: Mapping[str, object] | None = None,
    wordnet_index: WordNetIndex | None = None,
    wordnet_profiles_by_source: Mapping[str, Mapping[str, object]] | None = None,
    bridge_path: Path | None = None,
    difficulty_path: Path | None = None,
    wordnet_dir: Path | None = None,
    sample_per_cell: int = DEFAULT_SAMPLE_PER_CELL,
    seed: str = DEFAULT_SEED,
    exclude_measured_triggers: bool = True,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    difficulty_payload = difficulty_payload or {}
    full_pairs = _dedupe_full_pairs(_mapping_rows(bridge_payload.get("full_source_target_pairs")))
    measured_triggers = _measured_triggers(difficulty_payload)
    eligible_pairs = [
        row
        for row in full_pairs
        if not exclude_measured_triggers
        or str(row.get("source") or "").strip().lower() not in measured_triggers
    ]
    candidate_rows = [
        _candidate_row(
            row=row,
            wordnet_index=wordnet_index,
            wordnet_profiles_by_source=wordnet_profiles_by_source,
        )
        for row in eligible_pairs
    ]
    cells = _cell_rows(
        candidate_rows=candidate_rows,
        sample_per_cell=max(1, int(sample_per_cell)),
        seed=seed,
    )
    sampled_rows = [row for cell in cells for row in _mapping_rows(cell.get("sampled_rows"))]
    authoring_queue = [_authoring_row(row) for row in sampled_rows]
    checks = _checks(
        full_pairs=full_pairs,
        cells=cells,
        sampled_rows=sampled_rows,
        authoring_queue=authoring_queue,
        exclude_measured_triggers=exclude_measured_triggers,
        measured_triggers=measured_triggers,
    )
    issues = [key for key, value in checks.items() if not value]
    return {
        "schema_version": 1,
        "pair": str(bridge_payload.get("pair") or difficulty_payload.get("pair") or "en-es"),
        "status": "review" if issues else "ok",
        "decision": (
            "full_family_representative_sample_frozen"
            if not issues
            else "full_family_representative_sample_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "srs_zipf_bridge_path": _repo_path(bridge_path),
            "srs_zipf_bridge_decision": str(bridge_payload.get("decision") or ""),
            "difficulty_path": _repo_path(difficulty_path),
            "difficulty_decision": str(difficulty_payload.get("decision") or ""),
            "wordnet_dir": _repo_path(wordnet_dir),
            "wordnet_source_file_count": int(wordnet_index.source_file_count)
            if wordnet_index is not None
            else None,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_generation": "none",
            "sampling_unit": "generated_english_source_plus_spanish_target_family",
            "full_denominator": "full_source_target_pairs from the SRS Zipf bridge",
            "cell_dimensions": [
                "source_zipf_band_en",
                "source_wordnet_polysemy_band",
                "source_wordnet_pos_shape",
            ],
            "sampling_method": "frozen_seed_hash_order_within_each_nonempty_cell",
            "seed": seed,
            "sample_per_cell": max(1, int(sample_per_cell)),
            "measured_trigger_policy": "excluded"
            if exclude_measured_triggers
            else "included_by_request",
            "manual_packet_contract": {
                "active_positive_rows_per_family": 2,
                "shadow_negative_rows_per_polysemic_family": 2,
                "shadow_negative_rows_per_single_sense_family": 0,
                "phrase_no_winner_rows_per_family": 1,
            },
            "outcome_fields_forbidden_in_selection": sorted(FORBIDDEN_SELECTION_FIELDS),
            "mean_estimation_note": (
                "Cell-level means use sampled rows directly. Full-universe means should "
                "weight each sampled family by its cell_sampling_weight."
            ),
        },
        "summary": _summary(
            full_pairs=full_pairs,
            eligible_pairs=eligible_pairs,
            candidate_rows=candidate_rows,
            cells=cells,
            sampled_rows=sampled_rows,
            authoring_queue=authoring_queue,
            measured_trigger_count=len(measured_triggers),
        ),
        "e2e_checks": checks,
        "cells": cells,
        "sampled_rows": sampled_rows,
        "manual_authoring_queue": authoring_queue,
        "limitations": [
            "manual_sentences_are_not_authored_by_this_report",
            "wordnet_polysemy_is_a_proxy_for_shadow_availability",
            "source_zipf_bands_are_reporting_cells_not_proven_difficulty_boundaries",
            "sample_is_representative_within_declared_cells_not_a_browser_token_distribution",
            "missing_wordnet_profiles_are_preserved_as_missing_cells",
        ],
        "next_steps": [
            "Author fixed manual sentence packets for the frozen queue without reselecting families.",
            "Keep rows that lack honest shadow negatives as not_applicable rather than inventing fake shadows.",
            "Score the authored packet with the current veto algorithm.",
            "Estimate positive allow and negative abstain by source Zipf, polysemy, and POS-shape cell.",
            "Rerun formula-shape and formula-weight sweeps only after this representative packet is scored.",
        ],
    }


def render_full_family_representative_sample_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Full-Family Representative Sample",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Full source-target families: `{summary.get('full_source_target_pair_count', 0)}`",
        f"- Eligible families: `{summary.get('eligible_source_target_pair_count', 0)}`",
        f"- Non-empty cells: `{summary.get('nonempty_cell_count', 0)}` / `{summary.get('cell_count', 0)}`",
        f"- Sampled families: `{summary.get('sampled_family_count', 0)}`",
        f"- Planned manual cases: `{summary.get('planned_total_manual_cases', 0)}`",
        "",
        "## Methodology",
        "",
        "The sample is drawn from the full generated source-target family denominator, "
        "not from the 200-row SRS journey slice. Sampling is random by stable hash "
        "inside predeclared cells, so mid and rare source bands are represented even "
        "though they are smaller than common bands.",
        "",
        "## Universe Versus Sample",
        "",
        _band_count_table(
            title="Source Zipf",
            universe=_as_mapping(summary.get("universe_by_source_zipf_band")),
            sample=_as_mapping(summary.get("sample_by_source_zipf_band")),
        ),
        "",
        _band_count_table(
            title="Target Zipf",
            universe=_as_mapping(summary.get("universe_by_target_zipf_band")),
            sample=_as_mapping(summary.get("sample_by_target_zipf_band")),
        ),
        "",
        "## Cell Summary",
        "",
        _cell_table(report.get("cells")),
        "",
        "## Manual Authoring Queue",
        "",
        _queue_table(report.get("manual_authoring_queue")),
        "",
        "## Guardrails",
        "",
        "| Check | Value |",
        "| --- | --- |",
    ]
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(key)}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _candidate_row(
    *,
    row: Mapping[str, object],
    wordnet_index: WordNetIndex | None,
    wordnet_profiles_by_source: Mapping[str, Mapping[str, object]] | None,
) -> dict[str, object]:
    source = str(row.get("source") or "").strip().lower()
    target = str(row.get("target") or "").strip()
    profile = _profile_for_source(
        source=source,
        wordnet_index=wordnet_index,
        wordnet_profiles_by_source=wordnet_profiles_by_source,
    )
    sense_count = int(profile.get("wordnet_sense_count") or 0)
    pos_count = int(profile.get("wordnet_pos_count") or 0)
    return {
        "family_id": f"{source}->{target}",
        "source": source,
        "target": target,
        "source_zipf_frequency_en": row.get("source_zipf_frequency_en"),
        "source_zipf_band_en": _source_zipf_band(row.get("source_zipf_band_en")),
        "target_zipf_frequency_es": row.get("target_zipf_frequency_es"),
        "target_zipf_band_es": _target_zipf_band(row.get("target_zipf_band_es")),
        "wordnet_sense_count": sense_count,
        "wordnet_pos_count": pos_count,
        "wordnet_polysemy_band": _polysemy_band(sense_count),
        "wordnet_pos_shape": _pos_shape(sense_count=sense_count, pos_count=pos_count),
        "wordnet_pos_counts": dict(_as_mapping(profile.get("wordnet_pos_counts"))),
        "wordnet_sample_synsets": list(profile.get("wordnet_sample_synsets") or [])[:3],
    }


def _profile_for_source(
    *,
    source: str,
    wordnet_index: WordNetIndex | None,
    wordnet_profiles_by_source: Mapping[str, Mapping[str, object]] | None,
) -> Mapping[str, object]:
    if wordnet_profiles_by_source is not None:
        return _as_mapping(wordnet_profiles_by_source.get(source))
    if wordnet_index is None:
        return {}
    return _wordnet_profile(trigger=source, wordnet_index=wordnet_index)


def _cell_rows(
    *,
    candidate_rows: Sequence[Mapping[str, object]],
    sample_per_cell: int,
    seed: str,
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[
            (
                str(row.get("source_zipf_band_en") or "missing"),
                str(row.get("wordnet_polysemy_band") or "missing"),
                str(row.get("wordnet_pos_shape") or "missing"),
            )
        ].append(row)
    cells = []
    for source_band in SOURCE_ZIPF_BANDS:
        for polysemy_band in POLYSEMY_BANDS:
            for pos_shape in POS_SHAPES:
                key = (source_band, polysemy_band, pos_shape)
                eligible = sorted(
                    grouped.get(key, []),
                    key=lambda row: _sample_sort_key(seed=seed, row=row, cell_key=key),
                )
                sampled = [dict(row) for row in eligible[:sample_per_cell]]
                sample_count = len(sampled)
                eligible_count = len(eligible)
                sampling_weight = (eligible_count / sample_count) if sample_count else None
                cell_id = (
                    f"source_zipf={source_band}::polysemy={polysemy_band}::pos_shape={pos_shape}"
                )
                for sample_rank, sample in enumerate(sampled, start=1):
                    sample.update(
                        {
                            "cell_id": cell_id,
                            "sample_rank_in_cell": sample_rank,
                            "cell_eligible_count": eligible_count,
                            "cell_sample_count": sample_count,
                            "cell_sampling_weight": _round4(sampling_weight)
                            if sampling_weight is not None
                            else None,
                            "selection_hash": _stable_hex(
                                f"{seed}:{cell_id}:{sample.get('family_id')}"
                            )[:16],
                        }
                    )
                cells.append(
                    {
                        "cell_id": cell_id,
                        "source_zipf_band_en": source_band,
                        "wordnet_polysemy_band": polysemy_band,
                        "wordnet_pos_shape": pos_shape,
                        "eligible_count": eligible_count,
                        "sample_count": sample_count,
                        "underfilled": eligible_count < sample_per_cell,
                        "cell_sampling_weight": _round4(sampling_weight)
                        if sampling_weight is not None
                        else None,
                        "sampled_families": [
                            f"{row.get('source')}->{row.get('target')}" for row in sampled
                        ],
                        "sampled_rows": sampled,
                    }
                )
    return cells


def _authoring_row(row: Mapping[str, object]) -> dict[str, object]:
    sense_count = int(row.get("wordnet_sense_count") or 0)
    shadow_rows = 2 if sense_count >= 2 else 0
    return {
        **dict(row),
        "manual_packet": {
            "active_positive_rows": 2,
            "shadow_negative_rows": shadow_rows,
            "phrase_no_winner_rows": 1,
            "total_rows": 3 + shadow_rows,
            "shadow_contract": "candidate_polysemic" if shadow_rows else "not_applicable",
            "authoring_instruction": (
                "Write honest browser-like contexts. If no real alternate sense exists, "
                "keep shadow_negative not_applicable instead of forcing a fake case."
            ),
        },
    }


def _summary(
    *,
    full_pairs: Sequence[Mapping[str, object]],
    eligible_pairs: Sequence[Mapping[str, object]],
    candidate_rows: Sequence[Mapping[str, object]],
    cells: Sequence[Mapping[str, object]],
    sampled_rows: Sequence[Mapping[str, object]],
    authoring_queue: Sequence[Mapping[str, object]],
    measured_trigger_count: int,
) -> dict[str, object]:
    manual_totals = Counter()
    for row in authoring_queue:
        packet = _as_mapping(row.get("manual_packet"))
        manual_totals["active_positive"] += int(packet.get("active_positive_rows") or 0)
        manual_totals["shadow_negative"] += int(packet.get("shadow_negative_rows") or 0)
        manual_totals["phrase_no_winner"] += int(packet.get("phrase_no_winner_rows") or 0)
        manual_totals["total"] += int(packet.get("total_rows") or 0)
    return {
        "full_source_target_pair_count": len(full_pairs),
        "eligible_source_target_pair_count": len(eligible_pairs),
        "measured_trigger_exclusion_count": measured_trigger_count,
        "cell_count": len(cells),
        "nonempty_cell_count": sum(1 for cell in cells if int(cell.get("eligible_count") or 0)),
        "empty_cell_count": sum(1 for cell in cells if not int(cell.get("eligible_count") or 0)),
        "underfilled_cell_count": sum(1 for cell in cells if bool(cell.get("underfilled"))),
        "nonempty_underfilled_cell_count": sum(
            1
            for cell in cells
            if bool(cell.get("underfilled")) and int(cell.get("eligible_count") or 0)
        ),
        "sampled_family_count": len(sampled_rows),
        "planned_active_positive_cases": manual_totals["active_positive"],
        "planned_shadow_negative_cases": manual_totals["shadow_negative"],
        "planned_phrase_no_winner_cases": manual_totals["phrase_no_winner"],
        "planned_total_manual_cases": manual_totals["total"],
        "universe_by_source_zipf_band": _counter_dict(
            (row.get("source_zipf_band_en") for row in candidate_rows),
            order=SOURCE_ZIPF_BANDS,
        ),
        "sample_by_source_zipf_band": _counter_dict(
            (row.get("source_zipf_band_en") for row in sampled_rows),
            order=SOURCE_ZIPF_BANDS,
        ),
        "universe_by_target_zipf_band": _counter_dict(
            (row.get("target_zipf_band_es") for row in candidate_rows),
            order=SOURCE_ZIPF_BANDS,
        ),
        "sample_by_target_zipf_band": _counter_dict(
            (row.get("target_zipf_band_es") for row in sampled_rows),
            order=SOURCE_ZIPF_BANDS,
        ),
        "universe_by_polysemy_band": _counter_dict(
            (row.get("wordnet_polysemy_band") for row in candidate_rows),
            order=POLYSEMY_BANDS,
        ),
        "sample_by_polysemy_band": _counter_dict(
            (row.get("wordnet_polysemy_band") for row in sampled_rows),
            order=POLYSEMY_BANDS,
        ),
    }


def _checks(
    *,
    full_pairs: Sequence[Mapping[str, object]],
    cells: Sequence[Mapping[str, object]],
    sampled_rows: Sequence[Mapping[str, object]],
    authoring_queue: Sequence[Mapping[str, object]],
    exclude_measured_triggers: bool,
    measured_triggers: set[str],
) -> dict[str, bool]:
    sampled_sources = {str(row.get("source") or "").strip().lower() for row in sampled_rows}
    sample_keys = [key for row in sampled_rows for key in row if key in FORBIDDEN_SELECTION_FIELDS]
    sampled_bands = {str(row.get("source_zipf_band_en") or "") for row in sampled_rows}
    return {
        "full_source_target_pairs_available": bool(full_pairs),
        "outcome_fields_absent_from_sample_rows": not sample_keys,
        "all_sampled_rows_have_cell_ids": all(row.get("cell_id") for row in sampled_rows),
        "all_nonempty_cells_have_samples": all(
            int(cell.get("sample_count") or 0) > 0
            for cell in cells
            if int(cell.get("eligible_count") or 0) > 0
        ),
        "sample_counts_do_not_exceed_eligible_counts": all(
            int(cell.get("sample_count") or 0) <= int(cell.get("eligible_count") or 0)
            for cell in cells
        ),
        "mid_source_band_represented": "zipf_3_to_4_mid" in sampled_bands,
        "rare_source_band_represented": "zipf_below_3_rare" in sampled_bands,
        "measured_triggers_excluded_when_requested": (
            not exclude_measured_triggers or sampled_sources.isdisjoint(measured_triggers)
        ),
        "all_authoring_rows_have_manual_packet": all(
            _as_mapping(row.get("manual_packet")) for row in authoring_queue
        ),
    }


def _dedupe_full_pairs(rows: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    by_key: dict[tuple[str, str], Mapping[str, object]] = {}
    for row in rows:
        source = str(row.get("source") or "").strip().lower()
        target = str(row.get("target") or "").strip()
        if source and target and (source, target) not in by_key:
            by_key[(source, target)] = row
    return [by_key[key] for key in sorted(by_key)]


def _measured_triggers(payload: Mapping[str, object]) -> set[str]:
    return {
        str(row.get("trigger") or "").strip().lower()
        for row in _mapping_rows(payload.get("case_traces"))
        if str(row.get("trigger") or "").strip()
    }


def _source_zipf_band(value: object) -> str:
    raw = str(value or "").strip()
    return raw if raw in SOURCE_ZIPF_BANDS else "missing"


def _target_zipf_band(value: object) -> str:
    raw = str(value or "").strip()
    return raw if raw in SOURCE_ZIPF_BANDS else "missing"


def _polysemy_band(sense_count: int) -> str:
    if sense_count <= 0:
        return "missing"
    if sense_count <= 3:
        return "low_1_to_3"
    if sense_count <= 9:
        return "medium_4_to_9"
    return "high_10_plus"


def _pos_shape(*, sense_count: int, pos_count: int) -> str:
    if sense_count <= 0 or pos_count <= 0:
        return "missing"
    if pos_count >= 2:
        return "cross_pos_polysemy"
    if sense_count >= 2:
        return "same_pos_polysemy"
    return "single_sense"


def _sample_sort_key(
    *,
    seed: str,
    row: Mapping[str, object],
    cell_key: tuple[str, str, str],
) -> tuple[str, str]:
    cell_id = f"source_zipf={cell_key[0]}::polysemy={cell_key[1]}::pos_shape={cell_key[2]}"
    family_id = str(row.get("family_id") or "")
    return (_stable_hex(f"{seed}:{cell_id}:{family_id}"), family_id)


def _stable_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _counter_dict(values: Sequence[object], *, order: Sequence[str]) -> dict[str, int]:
    counter = Counter(str(value or "missing") for value in values)
    return {key: int(counter.get(key, 0)) for key in order if counter.get(key, 0)}


def _band_count_table(
    *,
    title: str,
    universe: Mapping[str, object],
    sample: Mapping[str, object],
) -> str:
    universe_total = sum(int(value or 0) for value in universe.values())
    sample_total = sum(int(value or 0) for value in sample.values())
    lines = [
        f"### {title}",
        "",
        "| Band | Universe | Universe Share | Sample | Sample Share |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for band in SOURCE_ZIPF_BANDS:
        universe_count = int(universe.get(band) or 0)
        sample_count = int(sample.get(band) or 0)
        if universe_count == 0 and sample_count == 0:
            continue
        lines.append(
            f"| `{_escape_md(band)}` | {universe_count} | "
            f"{_format_percent(_ratio(universe_count, universe_total))} | "
            f"{sample_count} | {_format_percent(_ratio(sample_count, sample_total))} |"
        )
    return "\n".join(lines)


def _cell_table(value: object) -> str:
    rows = [row for row in _mapping_rows(value) if int(row.get("eligible_count") or 0)]
    if not rows:
        return "_No non-empty cells._"
    lines = [
        "| Cell | Eligible | Sampled | Weight | Families |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        families = ", ".join(
            f"`{_escape_md(str(item))}`" for item in list(row.get("sampled_families") or [])[:6]
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('cell_id') or ''))}`",
                    str(int(row.get("eligible_count") or 0)),
                    str(int(row.get("sample_count") or 0)),
                    str(row.get("cell_sampling_weight") or ""),
                    families,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _queue_table(value: object, *, limit: int = 100) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No manual authoring rows._"
    lines = [
        "| Family | Source Band | Target Band | Senses | POS Shape | Manual Rows | Weight |",
        "| --- | --- | --- | ---: | --- | ---: | ---: |",
    ]
    for row in rows[:limit]:
        packet = _as_mapping(row.get("manual_packet"))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('source') or ''))}` -> `{_escape_md(str(row.get('target') or ''))}`",
                    f"`{_escape_md(str(row.get('source_zipf_band_en') or ''))}`",
                    f"`{_escape_md(str(row.get('target_zipf_band_es') or ''))}`",
                    str(int(row.get("wordnet_sense_count") or 0)),
                    f"`{_escape_md(str(row.get('wordnet_pos_shape') or ''))}`",
                    str(int(packet.get("total_rows") or 0)),
                    str(row.get("cell_sampling_weight") or ""),
                ]
            )
            + " |"
        )
    if len(rows) > limit:
        lines.append("| ... | ... | ... | ... | ... | ... | ... |")
    return "\n".join(lines)


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return round(float(numerator) / float(denominator), 4)


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
