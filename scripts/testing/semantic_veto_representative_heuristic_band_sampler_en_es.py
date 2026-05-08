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

from semantic_veto_difficulty_stratification_en_es import (  # noqa: E402
    DEFAULT_SOURCE_FREQUENCY_DB,
    FrequencyLookup,
    _escape_md,
    _load_json,
    _repo_path,
    _resolve_repo_path,
)
from semantic_veto_heuristic_group_pilot_en_es import (  # noqa: E402
    DEFAULT_DIFFICULTY_REPORT,
    DEFAULT_WORDNET_DIR,
    _candidate_pool,
    _measured_triggers,
)
from semantic_veto_product_quality_en_es import _as_mapping  # noqa: E402
from semantic_veto_veto_only_probe_en_es import _mapping_rows  # noqa: E402
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_representative_heuristic_band_sampler_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_representative_heuristic_band_sampler_en_es_latest.md"
)
DEFAULT_SAMPLE_PER_CELL = 8
DEFAULT_SEED = "semantic_veto_representative_heuristic_band_sampler_en_es_v1"
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
RANK_BANDS = (
    (1, 500, "1-500"),
    (501, 1000, "501-1000"),
    (1001, 2000, "1001-2000"),
    (2001, 5000, "2001-5000"),
    (5001, 10000, "5001-10000"),
    (10001, 999999999, ">10000"),
)
POLYSEMY_BANDS = (
    (1, 3, "low_1_to_3"),
    (4, 9, "medium_4_to_9"),
    (10, 999999999, "high_10_plus"),
)
POS_SHAPES = ("single_sense", "same_pos_polysemy", "cross_pos_polysemy")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze a representative seeded sample from each source-rank, WordNet "
            "polysemy, and POS-shape cell for en-es semantic-veto difficulty research."
        )
    )
    parser.add_argument("--source-frequency-db", type=Path, default=DEFAULT_SOURCE_FREQUENCY_DB)
    parser.add_argument("--wordnet-dir", type=Path, default=DEFAULT_WORDNET_DIR)
    parser.add_argument("--difficulty-json", type=Path, default=DEFAULT_DIFFICULTY_REPORT)
    parser.add_argument("--sample-per-cell", type=int, default=DEFAULT_SAMPLE_PER_CELL)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--include-measured-triggers", action="store_true")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def build_representative_heuristic_band_sampler_report(
    *,
    source_frequency: FrequencyLookup,
    wordnet_index: WordNetIndex,
    difficulty_payload: Mapping[str, object] | None = None,
    source_frequency_path: Path | None = None,
    wordnet_dir: Path | None = None,
    difficulty_path: Path | None = None,
    sample_per_cell: int = DEFAULT_SAMPLE_PER_CELL,
    seed: str = DEFAULT_SEED,
    exclude_measured_triggers: bool = True,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    difficulty_payload = difficulty_payload or {}
    measured_triggers = (
        _measured_triggers(difficulty_payload) if exclude_measured_triggers else set()
    )
    candidate_rows = _representative_candidate_rows(
        source_frequency=source_frequency,
        wordnet_index=wordnet_index,
        measured_triggers=measured_triggers,
    )
    cells = _cell_rows(
        candidate_rows=candidate_rows,
        sample_per_cell=max(1, int(sample_per_cell)),
        seed=seed,
    )
    sampled_rows = [row for cell in cells for row in _mapping_rows(cell.get("sampled_rows"))]
    checks = _checks(cells=cells, sampled_rows=sampled_rows)
    issues = [key for key, value in checks.items() if not value]
    return {
        "schema_version": 1,
        "pair": "en-es",
        "status": "review" if issues else "ok",
        "decision": (
            "representative_heuristic_band_sample_frozen"
            if not issues
            else "representative_heuristic_band_sample_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "source_frequency_path": _repo_path(source_frequency_path),
            "source_frequency_status": source_frequency.status,
            "source_frequency_record_count": len(source_frequency.records_by_key),
            "wordnet_dir": _repo_path(wordnet_dir),
            "wordnet_source_file_count": int(wordnet_index.source_file_count),
            "difficulty_report_path": _repo_path(difficulty_path),
            "difficulty_report_status": str(difficulty_payload.get("status") or ""),
        },
        "methodology": {
            "goal": (
                "Estimate heuristic-band mean veto difficulty by sampling representative "
                "source triggers within predeclared cells, instead of choosing the most "
                "interesting or hardest-looking words."
            ),
            "sampling_unit": "english_source_trigger",
            "cell_dimensions": ["source_rank_band", "polysemy_band", "pos_shape"],
            "sampling_method": "frozen_seed_hash_order_within_each_cell",
            "seed": seed,
            "sample_per_cell": max(1, int(sample_per_cell)),
            "outcome_fields_forbidden_in_selection": sorted(FORBIDDEN_SELECTION_FIELDS),
            "measured_trigger_policy": (
                "excluded_from_default_universe"
                if exclude_measured_triggers
                else "included_by_request"
            ),
            "mean_estimation_note": (
                "Per-cell means should use the sampled rows. Overall means over the "
                "candidate universe should use each row's cell_sampling_weight or cell "
                "universe counts; equal-cell averages answer a different question."
            ),
        },
        "summary": _summary(
            candidate_rows=candidate_rows,
            cells=cells,
            sampled_rows=sampled_rows,
            measured_trigger_count=len(measured_triggers),
        ),
        "e2e_checks": checks,
        "cells": cells,
        "sampled_rows": sampled_rows,
        "limitations": [
            "english_source_trigger_sample_only_no_spanish_target_family_yet",
            "sample_is_representative_within_cells_not_a_natural_browser_token_distribution",
            "wordnet_polysemy_and_pos_shape_are_proxy_features_not_human_sense_labels",
            "measured_triggers_are_excluded_by_default_to_avoid_reusing_biased_prior_outcomes",
            "case_authoring_or_llm_generation_must_not_replace_this_frozen_sample_ad_hoc",
        ],
        "next_steps": [
            "Run target/shadow family construction over the frozen sampled rows without reselecting triggers.",
            "For source-ready sampled words, generate or author a fixed small context packet per word.",
            "Estimate mean veto difficulty and confidence intervals by cell, then fit factor effects across rank, polysemy, and POS shape.",
            "Only after representative means are measured, run separate targeted oversampling for high-uncertainty or high-value cells.",
        ],
    }


def render_representative_heuristic_band_sampler_markdown(
    report: Mapping[str, object],
) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Representative Heuristic-Band Sampler",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate universe: `{summary.get('candidate_universe_count', 0)}`",
        f"- Non-empty cells: `{summary.get('nonempty_cell_count', 0)}` / `{summary.get('cell_count', 0)}`",
        f"- Empty cells: `{summary.get('empty_cell_count', 0)}`",
        f"- Sampled triggers: `{summary.get('sampled_trigger_count', 0)}`",
        f"- Underfilled non-empty cells: `{summary.get('nonempty_underfilled_cell_count', 0)}`",
        f"- Underfilled cells including empty cells: `{summary.get('underfilled_cell_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("goal") or ""),
        "",
        "Cells are sampled by frozen hash order inside each cell. This avoids the old "
        "hard-case bias where each band could be represented by its most difficult-looking words.",
        "",
        "## Cell Summary",
        "",
        _cell_table(report.get("cells")),
        "",
        "## Sample Rows",
        "",
        _sample_table(report.get("sampled_rows")),
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


def _representative_candidate_rows(
    *,
    source_frequency: FrequencyLookup,
    wordnet_index: WordNetIndex,
    measured_triggers: set[str],
) -> list[dict[str, object]]:
    rows = []
    for row in _candidate_pool(
        source_frequency=source_frequency,
        wordnet_index=wordnet_index,
        measured_triggers=measured_triggers,
    ):
        rank = float(row.get("source_rank") or 0.0)
        senses = int(row.get("wordnet_sense_count") or 0)
        pos_count = int(row.get("wordnet_pos_count") or 0)
        rank_band = _rank_band(rank)
        polysemy_band = _polysemy_band(senses)
        pos_shape = _pos_shape(sense_count=senses, pos_count=pos_count)
        if not rank_band or not polysemy_band or not pos_shape:
            continue
        rows.append(
            {
                "trigger": str(row.get("trigger") or ""),
                "source_rank": rank,
                "source_frequency": row.get("source_frequency"),
                "source_rank_band": rank_band,
                "wordnet_sense_count": senses,
                "polysemy_band": polysemy_band,
                "wordnet_pos_count": pos_count,
                "pos_shape": pos_shape,
                "wordnet_pos_counts": dict(_as_mapping(row.get("wordnet_pos_counts"))),
                "sample_synsets": list(row.get("sample_synsets") or [])[:3],
            }
        )
    return rows


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
                str(row.get("source_rank_band") or ""),
                str(row.get("polysemy_band") or ""),
                str(row.get("pos_shape") or ""),
            )
        ].append(row)
    cells = []
    for rank_band in [band[2] for band in RANK_BANDS]:
        for polysemy_band in [band[2] for band in POLYSEMY_BANDS]:
            for pos_shape in POS_SHAPES:
                key = (rank_band, polysemy_band, pos_shape)
                eligible = sorted(
                    grouped.get(key, []),
                    key=lambda row: _sample_sort_key(seed=seed, row=row, cell_key=key),
                )
                sampled = [dict(row) for row in eligible[:sample_per_cell]]
                sample_count = len(sampled)
                eligible_count = len(eligible)
                sampling_weight = (eligible_count / sample_count) if sample_count else None
                cell_id = (
                    f"source_rank_band={rank_band}::"
                    f"polysemy_band={polysemy_band}::pos_shape={pos_shape}"
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
                            "selection_score": _stable_hex(
                                f"{seed}:{cell_id}:{sample.get('trigger')}"
                            )[:16],
                        }
                    )
                cells.append(
                    {
                        "cell_id": cell_id,
                        "source_rank_band": rank_band,
                        "polysemy_band": polysemy_band,
                        "pos_shape": pos_shape,
                        "eligible_count": eligible_count,
                        "sample_count": sample_count,
                        "underfilled": eligible_count < sample_per_cell,
                        "cell_sampling_weight": _round4(sampling_weight)
                        if sampling_weight is not None
                        else None,
                        "sampled_triggers": [str(row.get("trigger") or "") for row in sampled],
                        "sampled_rows": sampled,
                    }
                )
    return cells


def _summary(
    *,
    candidate_rows: Sequence[Mapping[str, object]],
    cells: Sequence[Mapping[str, object]],
    sampled_rows: Sequence[Mapping[str, object]],
    measured_trigger_count: int,
) -> dict[str, object]:
    rank_counts = Counter(str(row.get("source_rank_band") or "") for row in candidate_rows)
    polysemy_counts = Counter(str(row.get("polysemy_band") or "") for row in candidate_rows)
    pos_counts = Counter(str(row.get("pos_shape") or "") for row in candidate_rows)
    return {
        "candidate_universe_count": len(candidate_rows),
        "measured_trigger_exclusion_count": measured_trigger_count,
        "cell_count": len(cells),
        "nonempty_cell_count": sum(1 for cell in cells if int(cell.get("eligible_count") or 0) > 0),
        "empty_cell_count": sum(1 for cell in cells if int(cell.get("eligible_count") or 0) == 0),
        "underfilled_cell_count": sum(1 for cell in cells if bool(cell.get("underfilled"))),
        "nonempty_underfilled_cell_count": sum(
            1
            for cell in cells
            if bool(cell.get("underfilled")) and int(cell.get("eligible_count") or 0) > 0
        ),
        "sampled_trigger_count": len(sampled_rows),
        "rank_band_universe_counts": dict(sorted(rank_counts.items())),
        "polysemy_band_universe_counts": dict(sorted(polysemy_counts.items())),
        "pos_shape_universe_counts": dict(sorted(pos_counts.items())),
    }


def _checks(
    *,
    cells: Sequence[Mapping[str, object]],
    sampled_rows: Sequence[Mapping[str, object]],
) -> dict[str, bool]:
    sample_keys = [key for row in sampled_rows for key in row if key in FORBIDDEN_SELECTION_FIELDS]
    return {
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
        "empty_cells_are_preserved": any(
            int(cell.get("eligible_count") or 0) == 0 for cell in cells
        ),
    }


def _rank_band(rank: float) -> str:
    for low, high, label in RANK_BANDS:
        if low <= rank <= high:
            return label
    return ""


def _polysemy_band(sense_count: int) -> str:
    for low, high, label in POLYSEMY_BANDS:
        if low <= sense_count <= high:
            return label
    return ""


def _pos_shape(*, sense_count: int, pos_count: int) -> str:
    if pos_count >= 2:
        return "cross_pos_polysemy"
    if sense_count >= 2:
        return "same_pos_polysemy"
    if sense_count == 1 and pos_count == 1:
        return "single_sense"
    return ""


def _sample_sort_key(
    *,
    seed: str,
    row: Mapping[str, object],
    cell_key: tuple[str, str, str],
) -> tuple[str, str]:
    cell_id = (
        f"source_rank_band={cell_key[0]}::polysemy_band={cell_key[1]}::pos_shape={cell_key[2]}"
    )
    trigger = str(row.get("trigger") or "")
    return (_stable_hex(f"{seed}:{cell_id}:{trigger}"), trigger)


def _stable_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _cell_table(value: object) -> str:
    rows = [row for row in _mapping_rows(value) if int(row.get("eligible_count") or 0) > 0]
    if not rows:
        return "_No non-empty cells._"
    lines = [
        "| Cell | Eligible | Sampled | Weight | Triggers |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        triggers = ", ".join(f"`{_escape_md(item)}`" for item in row.get("sampled_triggers", []))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('cell_id') or ''))}`",
                    str(int(row.get("eligible_count") or 0)),
                    str(int(row.get("sample_count") or 0)),
                    str(row.get("cell_sampling_weight") or ""),
                    triggers,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _sample_table(value: object, *, limit: int = 80) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No sampled rows._"
    lines = [
        "| Trigger | Rank | Freq | Senses | POS | Rank band | Polysemy | POS shape | Weight |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: |",
    ]
    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    str(row.get("source_rank") or ""),
                    str(row.get("source_frequency") or ""),
                    str(row.get("wordnet_sense_count") or ""),
                    str(row.get("wordnet_pos_count") or ""),
                    f"`{_escape_md(str(row.get('source_rank_band') or ''))}`",
                    f"`{_escape_md(str(row.get('polysemy_band') or ''))}`",
                    f"`{_escape_md(str(row.get('pos_shape') or ''))}`",
                    str(row.get("cell_sampling_weight") or ""),
                ]
            )
            + " |"
        )
    if len(rows) > limit:
        lines.append("| ... | ... | ... | ... | ... | ... | ... | ... | ... |")
    return "\n".join(lines)


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def write_report(report: Mapping[str, object], *, json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_representative_heuristic_band_sampler_markdown(report), encoding="utf-8"
    )


def main() -> int:
    args = _parse_args()
    source_frequency_path = _resolve_repo_path(args.source_frequency_db)
    wordnet_dir = _resolve_repo_path(args.wordnet_dir)
    difficulty_path = _resolve_repo_path(args.difficulty_json)
    report = build_representative_heuristic_band_sampler_report(
        source_frequency=FrequencyLookup.from_sqlite(
            path=source_frequency_path,
            language="en",
        ),
        wordnet_index=WordNetIndex.load(wordnet_dir),
        difficulty_payload=_load_json(difficulty_path) if difficulty_path.exists() else {},
        source_frequency_path=source_frequency_path,
        wordnet_dir=wordnet_dir,
        difficulty_path=difficulty_path,
        sample_per_cell=max(1, int(args.sample_per_cell)),
        seed=str(args.seed),
        exclude_measured_triggers=not bool(args.include_measured_triggers),
    )
    json_out = _resolve_repo_path(args.json_out)
    markdown_out = _resolve_repo_path(args.markdown_out)
    write_report(report, json_out=json_out, markdown_out=markdown_out)
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
