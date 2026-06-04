#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
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
for candidate in (str(CORE_ROOT), str(GUI_SRC_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from semantic_non_v10_wave_builder_en_es import (  # noqa: E402
    DEFAULT_CANDIDATE_JSON,
    FAMILY_POS_STRATEGIES,
    DEFAULT_MAX_SENSE_COUNT,
    DEFAULT_WAVE_SIZE,
    build_non_v10_wave_draft_report,
)
from semantic_source_admission_cycle_en_es import (  # noqa: E402
    _empty_base_batch,
    build_source_admission_cycle_bundle,
)
from semantic_wordnet_example_frame_batch_en_es import (  # noqa: E402
    build_wordnet_example_frame_bundle,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_non_v10_wave_admission_sweep_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_non_v10_wave_admission_sweep_latest.md"
DEFAULT_SELECTED_DRAFT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_non_v10_wave_drafts"
DEFAULT_SELECTED_DATASET_OUT = (
    DEFAULT_SELECTED_DRAFT_ROOT / "en_es_source_non_v10_wave2_admission_selected_v1_dataset.json"
)
DEFAULT_SELECTED_QUEUE_OUT = (
    DEFAULT_SELECTED_DRAFT_ROOT
    / "semantic_source_non_v10_wave2_admission_selected_queue_en_es_v1.json"
)
DEFAULT_SELECTED_DATASET_ID = "en_es_source_non_v10_wave2_admission_selected_v1"
DEFAULT_SELECTED_QUEUE_ID = "semantic_source_non_v10_wave2_admission_selected_queue_en_es_v1"
DEFAULT_MIN_LINK_SCORE_GRID = (0.12, 0.16, 0.2)
DEFAULT_EVIDENCE_CONFIGS = (
    "definition_preferred:1",
    "definition_and_example:2",
    "definition_and_example:2:0",
    "example_preferred:1",
)


@dataclass(frozen=True)
class EvidenceConfig:
    mode: str
    max_rows_per_sense: int
    extraction_min_link_score: float | None = None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a no-spend admission sweep for automatic non-v10 en-es source waves. "
            "Each variant rebuilds a draft wave, extracts local WordNet evidence, and "
            "runs the source-admission cycle without ablation."
        )
    )
    parser.add_argument("--candidate-json", type=Path, default=DEFAULT_CANDIDATE_JSON)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--wiktionary-en-es-sqlite", type=Path, default=None)
    parser.add_argument("--wiktionary-es-en-sqlite", type=Path, default=None)
    parser.add_argument("--freedict-es-en-sqlite", type=Path, default=None)
    parser.add_argument("--wordnet-dir", type=Path, default=None)
    parser.add_argument("--wave-size", type=int, default=DEFAULT_WAVE_SIZE)
    parser.add_argument(
        "--selection-size",
        type=int,
        default=None,
        help=(
            "Number of semantic-complete families required for an admission-selected wave. "
            "Defaults to --wave-size; set lower than --wave-size to over-generate a pool."
        ),
    )
    parser.add_argument("--max-sense-count", type=int, default=DEFAULT_MAX_SENSE_COUNT)
    parser.add_argument(
        "--family-pos-strategy",
        choices=FAMILY_POS_STRATEGIES,
        default="noun_verb",
    )
    parser.add_argument(
        "--min-link-score-grid",
        default=",".join(_format_float(value) for value in DEFAULT_MIN_LINK_SCORE_GRID),
        help="Comma-separated WordNet link-score thresholds used for wave construction.",
    )
    parser.add_argument(
        "--evidence-config",
        action="append",
        default=[],
        help=(
            "Evidence variant as mode:max_rows_per_sense[:extraction_min_link_score]. "
            "The optional extraction score lets the sweep build a conservative family pool "
            "while extracting a broader WordNet candidate slate for admission."
        ),
    )
    parser.add_argument(
        "--allow-unsupported-translations",
        action="store_true",
        help="Allow forward-only translations without reverse Wiktionary or FreeDict support.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--selected-dataset-out", type=Path, default=DEFAULT_SELECTED_DATASET_OUT)
    parser.add_argument("--selected-queue-out", type=Path, default=DEFAULT_SELECTED_QUEUE_OUT)
    parser.add_argument("--selected-dataset-id", default=DEFAULT_SELECTED_DATASET_ID)
    parser.add_argument("--selected-queue-id", default=DEFAULT_SELECTED_QUEUE_ID)
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="Exit non-zero when the best variant still lacks full semantic completion.",
    )
    return parser.parse_args()


def build_non_v10_wave_admission_sweep_report(
    *,
    candidate_payload: Mapping[str, object],
    wiktionary_en_es_sqlite: Path,
    wiktionary_es_en_sqlite: Path | None,
    freedict_es_en_sqlite: Path | None,
    wordnet_dir: Path,
    wave_size: int = DEFAULT_WAVE_SIZE,
    selection_size: int | None = None,
    max_sense_count: int = DEFAULT_MAX_SENSE_COUNT,
    min_link_score_grid: Sequence[float] = DEFAULT_MIN_LINK_SCORE_GRID,
    evidence_configs: Sequence[EvidenceConfig] = (),
    require_translation_support: bool = True,
    selected_dataset_id: str = DEFAULT_SELECTED_DATASET_ID,
    selected_queue_id: str = DEFAULT_SELECTED_QUEUE_ID,
    family_pos_strategy: str = "noun_verb",
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    configs = tuple(evidence_configs) or tuple(
        _parse_evidence_config(item) for item in DEFAULT_EVIDENCE_CONFIGS
    )
    link_scores = tuple(_normalize_link_scores(min_link_score_grid))
    target_selection_size = int(selection_size if selection_size is not None else wave_size)
    if not configs:
        raise ValueError("At least one evidence config is required.")
    if not link_scores:
        raise ValueError("At least one min-link-score value is required.")

    wordnet_index = WordNetIndex.load(wordnet_dir)
    variant_rows: list[dict[str, object]] = []
    for min_link_score in link_scores:
        wave_report = build_non_v10_wave_draft_report(
            candidate_payload=candidate_payload,
            wiktionary_en_es_sqlite=wiktionary_en_es_sqlite,
            wiktionary_es_en_sqlite=wiktionary_es_en_sqlite,
            freedict_es_en_sqlite=freedict_es_en_sqlite,
            wordnet_index=wordnet_index,
            wave_id=f"source_non_v10_sweep_min{_score_slug(min_link_score)}",
            wave_size=wave_size,
            max_sense_count=max_sense_count,
            min_wordnet_link_score=min_link_score,
            require_translation_support=require_translation_support,
            family_pos_strategy=family_pos_strategy,
            generated_at=generated_at,
        )
        for config in configs:
            variant_rows.append(
                _run_variant(
                    wave_report=wave_report,
                    wordnet_dir=wordnet_dir,
                    min_link_score=min_link_score,
                    config=config,
                    generated_at=generated_at,
                )
            )

    best = _best_variant(variant_rows)
    portfolio = _semantic_portfolio(variant_rows)
    best_selected_keys = list(best.get("semantic_complete_family_keys") or ())[
        : max(0, target_selection_size)
    ]
    best_selected_triggers = list(best.get("semantic_complete_triggers") or ())[
        : max(0, target_selection_size)
    ]
    portfolio_selected_keys = list(portfolio.get("semantic_complete_family_keys") or ())[
        : max(0, target_selection_size)
    ]
    portfolio_selected_triggers = list(portfolio.get("semantic_complete_triggers") or ())[
        : max(0, target_selection_size)
    ]
    use_portfolio_selection = (
        len(best_selected_keys) < target_selection_size
        and len(portfolio_selected_keys) >= target_selection_size
    )
    selected_wave_keys = portfolio_selected_keys if use_portfolio_selection else best_selected_keys
    selection_strategy = "portfolio" if use_portfolio_selection else "single_variant"
    payloads_by_key = {
        str(row.get("family_id") or "").strip(): dict(row)
        for variant in variant_rows
        for row in variant.get("_selected_family_payloads") or ()
        if isinstance(row, Mapping) and str(row.get("family_id") or "").strip()
    }
    selected_family_payloads = [
        payloads_by_key[key] for key in selected_wave_keys if key in payloads_by_key
    ]
    best["admission_selected_family_keys"] = best_selected_keys
    best["admission_selected_triggers"] = best_selected_triggers
    best.pop("_selected_family_payloads", None)
    for row in variant_rows:
        row["is_best"] = row.get("variant_id") == best.get("variant_id")
        row.pop("_selected_family_payloads", None)
    best_complete = int(best.get("semantic_contract_complete_family_count") or 0)
    portfolio_complete = int(portfolio.get("semantic_complete_family_count") or 0)
    status = "ok" if len(selected_wave_keys) >= target_selection_size else "review"
    translation_support_mode = (
        "reverse_or_freedict_required"
        if require_translation_support
        else "forward_only_upper_bound"
    )
    best["translation_support_mode"] = translation_support_mode
    limitations = [
        "draft_waves_are_unreviewed_and_not_promotion_candidates",
        "phrase_control_rows_are_not_generated_by_the_wordnet_adapter",
        "heldout_validation_is_not_included_in_this_screening_sweep",
        "admission_selected_wave_is_a_control_selection_not_a_reviewed_dataset",
    ]
    if use_portfolio_selection:
        limitations.append("portfolio_selection_combines_admitted_families_across_source_variants")
    if not require_translation_support:
        limitations.append("forward_only_translations_are_upper_bound_not_promotion_evidence")
    next_steps = [
        "use the best semantic variant as the source-coverage control",
        "materialize the admission-selected wave as a draft dataset",
        "build phrase-containment rows through a separate containment-only lane",
        "add independent held-out cases before any promotion claim",
    ]
    if not require_translation_support:
        next_steps.insert(
            1,
            "convert upper-bound families into supported rows through reverse or reviewed source evidence",
        )
    return {
        "schema_version": 1,
        "status": status,
        "decision": _sweep_decision(
            status=status,
            best_complete=best_complete,
            portfolio_complete=portfolio_complete,
            selection_size=target_selection_size,
            selection_strategy=selection_strategy,
        ),
        "generated_at": generated_at,
        "pair": "en-es",
        "summary": {
            "variant_count": len(variant_rows),
            "requested_pool_size": int(wave_size),
            "selection_size": target_selection_size,
            "best_variant_id": str(best.get("variant_id") or ""),
            "best_semantic_contract_complete_family_count": int(
                best.get("semantic_contract_complete_family_count") or 0
            ),
            "best_final_admitted_row_count": int(best.get("final_admitted_row_count") or 0),
            "best_phrase_contract_complete_family_count": int(
                best.get("phrase_contract_complete_family_count") or 0
            ),
            "best_admission_selected_family_count": len(best_selected_keys),
            "admission_selected_family_count": len(selected_wave_keys),
            "selection_strategy": selection_strategy,
            "portfolio_semantic_complete_family_count": portfolio_complete,
            "portfolio_admission_selected_family_count": len(portfolio_selected_keys),
            "family_pos_strategy": str(family_pos_strategy or "").strip() or "noun_verb",
            "translation_support_mode": translation_support_mode,
        },
        "best_variant": best,
        "semantic_portfolio": {
            **portfolio,
            "admission_selected_family_keys": portfolio_selected_keys,
            "admission_selected_triggers": portfolio_selected_triggers,
        },
        "variant_rows": variant_rows,
        "admission_selected_dataset": _admission_selected_dataset(
            selected_family_payloads,
            best_variant=best,
            selection_size=target_selection_size,
            selection_strategy=selection_strategy,
            dataset_id=selected_dataset_id,
            generated_at=generated_at,
        ),
        "admission_selected_queue": _admission_selected_queue(
            selected_family_payloads,
            best_variant=best,
            dataset_id=selected_dataset_id,
            queue_id=selected_queue_id,
            selection_strategy=selection_strategy,
            generated_at=generated_at,
        ),
        "limitations": limitations,
        "next_steps": next_steps,
    }


def render_non_v10_wave_admission_sweep_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    best = _as_mapping(report.get("best_variant"))
    lines = [
        "# en-es Non-v10 Source Wave Admission Sweep",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Variants: `{summary.get('variant_count', 0)}`",
        f"- Best variant: `{summary.get('best_variant_id', '')}`",
        f"- Pool size: `{summary.get('requested_pool_size', 0)}`",
        f"- Selection size: `{summary.get('selection_size', 0)}`",
        f"- Translation support mode: `{summary.get('translation_support_mode', '')}`",
        f"- Best semantic contract: `{summary.get('best_semantic_contract_complete_family_count', 0)}` / `{summary.get('requested_pool_size', 0)}`",
        f"- Admission-selected families: `{summary.get('admission_selected_family_count', 0)}` / `{summary.get('selection_size', 0)}`",
        f"- Best admitted rows: `{summary.get('best_final_admitted_row_count', 0)}`",
        f"- Best phrase contract: `{summary.get('best_phrase_contract_complete_family_count', 0)}` / `{summary.get('requested_pool_size', 0)}`",
        f"- Selection strategy: `{summary.get('selection_strategy', '')}`",
        f"- Portfolio semantic families: `{summary.get('portfolio_semantic_complete_family_count', 0)}`",
        "",
        "## Best Variant",
        "",
        _best_variant_summary(best),
        "",
        "## Variant Grid",
        "",
        _variant_table(report.get("variant_rows", ())),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _run_variant(
    *,
    wave_report: Mapping[str, object],
    wordnet_dir: Path,
    min_link_score: float,
    config: EvidenceConfig,
    generated_at: str,
) -> dict[str, object]:
    dataset_payload = _as_mapping(wave_report.get("draft_dataset"))
    queue_payload = _as_mapping(wave_report.get("draft_queue"))
    extraction_min_link_score = (
        float(config.extraction_min_link_score)
        if config.extraction_min_link_score is not None
        else float(min_link_score)
    )
    extract_suffix = (
        ""
        if round(extraction_min_link_score, 4) == round(float(min_link_score), 4)
        else f"-extract{_score_slug(extraction_min_link_score)}"
    )
    variant_id = (
        f"min{_score_slug(min_link_score)}{extract_suffix}"
        f"-{config.mode}-rows{config.max_rows_per_sense}"
    )
    wordnet_bundle = build_wordnet_example_frame_bundle(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        wordnet_dir=wordnet_dir,
        run_id=f"non-v10-wave-admission-sweep-{variant_id}",
        scope="all_dataset_families",
        min_link_score=extraction_min_link_score,
        max_rows_per_sense=config.max_rows_per_sense,
        evidence_mode=config.mode,
        generated_at=generated_at,
    )
    wordnet_report = _as_mapping(wordnet_bundle.get("report"))
    normalized_batch = wordnet_bundle.get("normalized_batch")
    selected_families = [
        str(row.get("trigger") or "").strip()
        for row in _as_sequence(wave_report.get("selected_families"))
        if isinstance(row, Mapping)
    ]
    selected_family_rows = [
        row for row in _as_sequence(dataset_payload.get("families")) if isinstance(row, Mapping)
    ]
    selected_family_keys = [str(row.get("family_id") or "").strip() for row in selected_family_rows]
    trigger_by_family_key = {
        str(row.get("family_id") or "").strip(): str(row.get("trigger") or "").strip()
        for row in selected_family_rows
    }
    row = {
        "variant_id": variant_id,
        "min_link_score": float(min_link_score),
        "extraction_min_link_score": extraction_min_link_score,
        "evidence_mode": config.mode,
        "max_rows_per_sense": int(config.max_rows_per_sense),
        "selected_family_count": int(
            _as_mapping(wave_report.get("summary")).get("selected_family_count") or 0
        ),
        "selected_triggers": selected_families,
        "selected_family_keys": selected_family_keys,
        "_selected_family_payloads": [dict(item) for item in selected_family_rows],
        "wordnet_row_count": int(_as_mapping(wordnet_report.get("summary")).get("row_count") or 0),
        "target_families_with_active_wordnet": int(
            _as_mapping(wordnet_report.get("summary")).get("target_families_with_active_wordnet")
            or 0
        ),
        "target_families_with_shadow_wordnet": int(
            _as_mapping(wordnet_report.get("summary")).get("target_families_with_shadow_wordnet")
            or 0
        ),
    }
    if not isinstance(normalized_batch, Mapping) or not normalized_batch.get("rows"):
        return {
            **row,
            "status": "review",
            "decision": "no_normalized_wordnet_rows",
            "leakage_rejected_row_count": 0,
            "sense_rejected_row_count": 0,
            "final_admitted_row_count": 0,
            "semantic_contract_complete_family_count": 0,
            "phrase_contract_complete_family_count": 0,
            "semantic_gap_family_keys": [],
            "semantic_complete_family_keys": [],
            "semantic_complete_triggers": [],
            "phrase_containment_gap_family_keys": [],
        }
    admission_bundle = build_source_admission_cycle_bundle(
        dataset_payload=dataset_payload,
        queue_payload=queue_payload,
        required_family_payload=dataset_payload,
        base_batch_payload=_empty_base_batch(generated_at=generated_at),
        candidate_batch_payload=normalized_batch,
        batch_id=f"en-es:{variant_id}:source-admission-sweep",
        source_id=f"non_v10_wave_sweep_{variant_id}",
        run_ablation=False,
        generated_at=generated_at,
    )
    admission_report = _as_mapping(admission_bundle.get("report"))
    summary = _as_mapping(admission_report.get("summary"))
    residuals = _as_mapping(admission_report.get("residuals"))
    semantic_gap_keys = [str(item) for item in residuals.get("semantic_gap_family_keys") or ()]
    semantic_gap_key_set = set(semantic_gap_keys)
    semantic_complete_keys = [
        key for key in selected_family_keys if key and key not in semantic_gap_key_set
    ]
    return {
        **row,
        "status": str(admission_report.get("status") or "review"),
        "decision": str(admission_report.get("decision") or ""),
        "leakage_rejected_row_count": int(summary.get("leakage_rejected_row_count") or 0),
        "sense_rejected_row_count": int(summary.get("sense_rejected_row_count") or 0),
        "final_admitted_row_count": int(summary.get("final_admitted_row_count") or 0),
        "semantic_contract_complete_family_count": int(
            summary.get("semantic_contract_complete_family_count") or 0
        ),
        "phrase_contract_complete_family_count": int(
            summary.get("phrase_contract_complete_family_count") or 0
        ),
        "semantic_gap_family_keys": semantic_gap_keys,
        "semantic_complete_family_keys": semantic_complete_keys,
        "semantic_complete_triggers": [
            trigger_by_family_key.get(key, "") for key in semantic_complete_keys
        ],
        "phrase_containment_gap_family_keys": list(
            residuals.get("phrase_containment_gap_family_keys") or ()
        ),
    }


def _best_variant(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    best = max(
        rows,
        key=lambda row: (
            int(row.get("semantic_contract_complete_family_count") or 0),
            int(row.get("final_admitted_row_count") or 0),
            -int(row.get("sense_rejected_row_count") or 0),
            int(row.get("wordnet_row_count") or 0),
            int(row.get("selected_family_count") or 0),
        ),
    )
    return dict(best)


def _semantic_portfolio(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    complete_keys: list[str] = []
    complete_triggers: list[str] = []
    variant_ids_by_family_key: dict[str, list[str]] = {}
    triggers_by_key: dict[str, str] = {}
    for row in rows:
        variant_id = str(row.get("variant_id") or "").strip()
        selected_keys = [str(key or "").strip() for key in row.get("selected_family_keys") or ()]
        selected_triggers = [
            str(trigger or "").strip() for trigger in row.get("selected_triggers") or ()
        ]
        for key, trigger in zip(selected_keys, selected_triggers, strict=False):
            if key and trigger and key not in triggers_by_key:
                triggers_by_key[key] = trigger
        for key in row.get("semantic_complete_family_keys") or ():
            family_key = str(key or "").strip()
            if not family_key:
                continue
            if family_key not in variant_ids_by_family_key:
                complete_keys.append(family_key)
                complete_triggers.append(triggers_by_key.get(family_key, ""))
            if variant_id:
                variant_ids_by_family_key.setdefault(family_key, []).append(variant_id)
    return {
        "semantic_complete_family_count": len(complete_keys),
        "semantic_complete_family_keys": complete_keys,
        "semantic_complete_triggers": complete_triggers,
        "supporting_variant_ids_by_family_key": variant_ids_by_family_key,
    }


def _sweep_decision(
    *,
    status: str,
    best_complete: int,
    portfolio_complete: int,
    selection_size: int,
    selection_strategy: str,
) -> str:
    if status == "ok" and best_complete >= selection_size:
        return "semantic_complete_variant_found"
    if status == "ok" and selection_strategy == "portfolio":
        return "semantic_complete_source_portfolio_found"
    if portfolio_complete > best_complete:
        return "semantic_portfolio_improves_but_gaps_remain"
    return "semantic_gaps_remain"


def _admission_selected_dataset(
    families: Sequence[Mapping[str, object]],
    *,
    best_variant: Mapping[str, object],
    selection_size: int,
    selection_strategy: str,
    dataset_id: str,
    generated_at: str,
) -> dict[str, object]:
    variant_id = str(best_variant.get("variant_id") or "").strip()
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": str(dataset_id or "").strip() or DEFAULT_SELECTED_DATASET_ID,
        "generated_at": generated_at,
        "description": (
            "Admission-selected draft non-v10 source wave selected from the automatic "
            "pool sweep. Families still require independent active/shadow and phrase "
            "held-out cases before quality claims."
        ),
        "review_state": "draft_admission_selected_needs_case_review",
        "source_sweep_variant_id": variant_id,
        "source_sweep_selection_strategy": selection_strategy,
        "selection_size": int(selection_size),
        "semantic_complete_family_count": len(families),
        "translation_support_mode": str(best_variant.get("translation_support_mode") or ""),
        "families": [dict(family) for family in families],
    }


def _admission_selected_queue(
    families: Sequence[Mapping[str, object]],
    *,
    best_variant: Mapping[str, object],
    dataset_id: str,
    queue_id: str,
    selection_strategy: str,
    generated_at: str,
) -> dict[str, object]:
    queue_families = []
    for index, family in enumerate(families, start=1):
        queue_families.append(
            {
                "family_id": str(family.get("family_id") or "").strip(),
                "trigger": str(family.get("trigger") or "").strip(),
                "role": "target",
                "archetype": "automatic_non_v10_admission_selected_draft",
                "likely_bucket": "source_coverage_probe",
                "priority_rank": index,
                "review_state": "draft_admission_selected_needs_case_review",
            }
        )
    return {
        "schema_version": 1,
        "queue_id": str(queue_id or "").strip() or DEFAULT_SELECTED_QUEUE_ID,
        "pair": "en-es",
        "generated_at": generated_at,
        "source_sweep_variant_id": str(best_variant.get("variant_id") or "").strip(),
        "source_sweep_selection_strategy": selection_strategy,
        "dataset_id": str(dataset_id or "").strip() or DEFAULT_SELECTED_DATASET_ID,
        "translation_support_mode": str(best_variant.get("translation_support_mode") or ""),
        "families": queue_families,
    }


def _best_variant_summary(row: Mapping[str, object]) -> str:
    if not row:
        return "No variant rows were produced."
    semantic_gaps = ", ".join(str(item) for item in row.get("semantic_gap_family_keys") or ())
    admission_selected = ", ".join(
        str(item) for item in row.get("admission_selected_triggers") or ()
    )
    return "\n".join(
        [
            f"- Variant: `{row.get('variant_id', '')}`",
            f"- Selected triggers: `{', '.join(str(item) for item in row.get('selected_triggers') or ())}`",
            f"- Admission-selected triggers: `{admission_selected}`",
            f"- WordNet rows: `{row.get('wordnet_row_count', 0)}`",
            f"- Final admitted rows: `{row.get('final_admitted_row_count', 0)}`",
            f"- Semantic contract: `{row.get('semantic_contract_complete_family_count', 0)}`",
            f"- Phrase contract: `{row.get('phrase_contract_complete_family_count', 0)}`",
            f"- Semantic gaps: `{semantic_gaps}`",
        ]
    )


def _variant_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No variants were produced."
    lines = [
        (
            "| Variant | Best | Selected | Extract Min | WordNet Rows | Admitted | "
            "Sense Rejects | Semantic | Phrase |"
        ),
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in materialized:
        lines.append(
            f"| `{row.get('variant_id', '')}` | `{bool(row.get('is_best'))}` | "
            f"`{row.get('selected_family_count', 0)}` | "
            f"`{_format_float(float(row.get('extraction_min_link_score') or 0.0))}` | "
            f"`{row.get('wordnet_row_count', 0)}` | "
            f"`{row.get('final_admitted_row_count', 0)}` | "
            f"`{row.get('sense_rejected_row_count', 0)}` | "
            f"`{row.get('semantic_contract_complete_family_count', 0)}` | "
            f"`{row.get('phrase_contract_complete_family_count', 0)}` |"
        )
    return "\n".join(lines)


def _parse_evidence_config(value: str) -> EvidenceConfig:
    parts = [part.strip() for part in str(value or "").split(":")]
    mode = parts[0] if parts else ""
    normalized_mode = mode.strip()
    if normalized_mode not in {
        "definition_preferred",
        "definition_and_example",
        "example_preferred",
    }:
        raise ValueError(f"Unsupported evidence mode: {normalized_mode}")
    try:
        rows = int(parts[1] if len(parts) >= 2 and parts[1] else "1")
    except ValueError as exc:
        raise ValueError(f"Invalid evidence config row count: {value}") from exc
    if len(parts) > 3:
        raise ValueError(f"Invalid evidence config: {value}")
    extraction_min_link_score = None
    if len(parts) == 3 and parts[2]:
        try:
            extraction_min_link_score = max(0.0, float(parts[2]))
        except ValueError as exc:
            raise ValueError(f"Invalid evidence config extraction score: {value}") from exc
    return EvidenceConfig(
        mode=normalized_mode,
        max_rows_per_sense=max(1, rows),
        extraction_min_link_score=extraction_min_link_score,
    )


def _normalize_link_scores(values: Sequence[float]) -> list[float]:
    return sorted({round(float(value), 4) for value in values})


def _parse_float_grid(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _score_slug(value: float) -> str:
    return _format_float(value).replace(".", "p")


def _format_float(value: float) -> str:
    return f"{float(value):g}"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    args = _parse_args()
    wiktionary_en_es = args.wiktionary_en_es_sqlite or (
        args.data_root / "language_packs" / "wiktionary-en-es.sqlite"
    )
    wiktionary_es_en = args.wiktionary_es_en_sqlite or (
        args.data_root / "language_packs" / "wiktionary-es-en.sqlite"
    )
    freedict_es_en = args.freedict_es_en_sqlite or (
        args.data_root / "language_packs" / "freedict-es-en" / "main.sqlite"
    )
    wordnet_dir = args.wordnet_dir or (
        args.data_root / "language_packs" / "english-wordnet-2025-json"
    )
    report = build_non_v10_wave_admission_sweep_report(
        candidate_payload=_load_json(args.candidate_json),
        wiktionary_en_es_sqlite=wiktionary_en_es,
        wiktionary_es_en_sqlite=wiktionary_es_en if wiktionary_es_en.exists() else None,
        freedict_es_en_sqlite=freedict_es_en if freedict_es_en.exists() else None,
        wordnet_dir=wordnet_dir,
        wave_size=args.wave_size,
        selection_size=args.selection_size,
        max_sense_count=args.max_sense_count,
        min_link_score_grid=_parse_float_grid(args.min_link_score_grid),
        evidence_configs=tuple(
            _parse_evidence_config(item)
            for item in (args.evidence_config or DEFAULT_EVIDENCE_CONFIGS)
        ),
        require_translation_support=not args.allow_unsupported_translations,
        selected_dataset_id=args.selected_dataset_id,
        selected_queue_id=args.selected_queue_id,
        family_pos_strategy=args.family_pos_strategy,
    )
    report["artifacts"] = {
        "candidate_json": str(args.candidate_json),
        "wiktionary_en_es_sqlite": str(wiktionary_en_es),
        "wiktionary_es_en_sqlite": str(wiktionary_es_en) if wiktionary_es_en.exists() else "",
        "freedict_es_en_sqlite": str(freedict_es_en) if freedict_es_en.exists() else "",
        "wordnet_dir": str(wordnet_dir) if wordnet_dir.exists() else "",
    }
    _write_json(args.json_out, report)
    selected_dataset = _as_mapping(report.get("admission_selected_dataset"))
    selected_queue = _as_mapping(report.get("admission_selected_queue"))
    if report.get("status") == "ok" and selected_dataset.get("families"):
        _write_json(args.selected_dataset_out, selected_dataset)
        _write_json(args.selected_queue_out, selected_queue)
        report["artifacts"] = {
            **_as_mapping(report.get("artifacts")),
            "selected_dataset_json": str(args.selected_dataset_out),
            "selected_queue_json": str(args.selected_queue_out),
        }
        _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_non_v10_wave_admission_sweep_markdown(report), encoding="utf-8"
    )
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
