#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.helper.translation_packs import TranslationPackRef  # noqa: E402
from lexishift_core.resources.dict_loaders import (  # noqa: E402
    TranslationGlossRecord,
    load_translation_gloss_records_ordered,
)
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_LLM_BATCH_JSON,
    DEFAULT_MIN_ACTIVE_SCORE,
    DEFAULT_MIN_MARGIN,
    DEFAULT_QUEUE_JSON,
    DEFAULT_SCORER_ID,
    _build_pack_record,
    _load_json,
    _run_sentence_veto_config,
    augment_queue_dataset_with_llm_cue_views,
    load_normalized_llm_batch,
)
from semantic_reverse_aux_text_pilot_en_es import (  # noqa: E402
    augment_queue_dataset_with_reverse_aux_views,
    build_queue_subset_dataset,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_failure_diagnostic_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_failure_diagnostic_latest.md"
)

KEY_CONFIG_IDS = (
    "hard_current_default",
    "hard_reverse_aux_plus_all_evidence",
    "hard_reverse_aux_active_only",
    "hard_llm_cue_text",
    "hard_llm_cue_plus_all_evidence",
    "hard_reverse_aux_plus_llm_cue",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnose why the accepted en-es LLM cue tranche fails the downstream "
            "fixed-shadow acceptance gate, without making API calls."
        )
    )
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--llm-batch-json", type=Path, default=DEFAULT_LLM_BATCH_JSON)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--reverse-translation-dict", type=Path, default=None)
    parser.add_argument("--scorer-id", default=DEFAULT_SCORER_ID)
    parser.add_argument("--min-active-score", type=float, default=DEFAULT_MIN_ACTIVE_SCORE)
    parser.add_argument("--min-margin", type=float, default=DEFAULT_MIN_MARGIN)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_failure_diagnostic_report(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    llm_batch_payload: Mapping[str, object],
    reverse_records_by_trigger: Mapping[str, Sequence[TranslationGlossRecord]],
    data_root: Path,
    reverse_pack: TranslationPackRef | None,
    scorer_id: str = DEFAULT_SCORER_ID,
    min_active_score: float = DEFAULT_MIN_ACTIVE_SCORE,
    min_margin: float = DEFAULT_MIN_MARGIN,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )

    subset_dataset, family_roles = build_queue_subset_dataset(dataset_payload, queue_payload)
    llm_augmented_dataset, llm_coverage_rows, llm_batch_summary = (
        augment_queue_dataset_with_llm_cue_views(
            subset_dataset,
            family_roles=family_roles,
            llm_batch_payload=llm_batch_payload,
        )
    )
    reverse_augmented_dataset, reverse_aux_coverage_rows = (
        augment_queue_dataset_with_reverse_aux_views(
            subset_dataset,
            family_roles=family_roles,
            reverse_records_by_trigger=reverse_records_by_trigger,
        )
    )
    reverse_active_only_dataset = _drop_shadow_reverse_aux_views(reverse_augmented_dataset)
    reverse_plus_llm_dataset = _build_reverse_plus_llm_dataset(
        reverse_augmented_dataset=reverse_augmented_dataset,
        llm_augmented_dataset=llm_augmented_dataset,
    )

    config_inputs = (
        (
            "hard_current_default",
            "Hard current default runtime row",
            subset_dataset,
            "all_evidence_text",
            "family_all",
            "hard_current_default",
            "baseline",
        ),
        (
            "hard_reverse_aux_plus_all_evidence",
            "Hard reverse aux plus all evidence",
            reverse_augmented_dataset,
            "reverse_aux_plus_all_evidence",
            "family_all",
            "hard_current_default",
            "source_control",
        ),
        (
            "hard_reverse_aux_active_only",
            "Hard reverse aux active-only",
            reverse_active_only_dataset,
            "reverse_aux_plus_all_evidence",
            "family_all",
            "hard_current_default",
            "source_ablation",
        ),
        (
            "hard_llm_cue_text",
            "Hard LLM cue text only",
            llm_augmented_dataset,
            "llm_cue_text",
            "family_all",
            "hard_current_default",
            "llm_diagnostic",
        ),
        (
            "hard_llm_cue_plus_all_evidence",
            "Hard LLM cue plus all evidence",
            llm_augmented_dataset,
            "llm_cue_plus_all_evidence",
            "family_all",
            "hard_current_default",
            "llm_safe_additive",
        ),
        (
            "hard_reverse_aux_plus_llm_cue",
            "Hard reverse aux plus LLM cue",
            reverse_plus_llm_dataset,
            "reverse_aux_plus_llm_cue",
            "family_all",
            "hard_reverse_aux_plus_all_evidence",
            "combined_source_probe",
        ),
    )

    config_rows = [
        _run_sentence_veto_config(
            dataset_payload=payload,
            config_id=config_id,
            label=label,
            evidence_view=evidence_view,
            phrase_guard_pos_scope=phrase_guard_pos_scope,
            baseline_config_id=baseline_config_id,
            category=category,
            scorer_id=scorer_id,
            min_active_score=min_active_score,
            min_margin=min_margin,
        )
        for (
            config_id,
            label,
            payload,
            evidence_view,
            phrase_guard_pos_scope,
            baseline_config_id,
            category,
        ) in config_inputs
    ]
    _attach_config_deltas(config_rows)

    config_lookup = {
        str(row.get("config_id") or ""): row
        for row in config_rows
        if str(row.get("config_id") or "")
    }
    rescue_sweep_rows = _build_llm_rescue_sweep_rows(
        primary_config=config_lookup["hard_current_default"],
        backup_configs=[
            config_lookup["hard_llm_cue_text"],
            config_lookup["hard_llm_cue_plus_all_evidence"],
        ],
    )
    case_diagnostic_rows = _build_case_diagnostic_rows(config_lookup)
    for row in config_rows:
        row.pop("row_results", None)

    report: dict[str, object] = {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ok",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "scorer_id": str(scorer_id or "").strip() or DEFAULT_SCORER_ID,
        "min_active_score": float(min_active_score),
        "min_margin": float(min_margin),
        "resource_status": {
            "data_root": str(data_root),
            "reverse_pack": _build_pack_record(reverse_pack),
            "missing_resources": []
            if reverse_pack is not None and reverse_pack.path.exists()
            else ["reverse_translation_pack"],
        },
        "llm_batch": llm_batch_summary,
        "coverage_rows": llm_coverage_rows,
        "reverse_aux_coverage_rows": reverse_aux_coverage_rows,
        "configurations": config_rows,
        "llm_rescue_sweep": rescue_sweep_rows,
        "case_diagnostics": case_diagnostic_rows,
    }
    report["summary_findings"] = _build_summary_findings(report)
    report["recommendation"] = _build_recommendation(report)
    return report


def _drop_shadow_reverse_aux_views(dataset_payload: Mapping[str, object]) -> dict[str, object]:
    payload = deepcopy(dict(dataset_payload))
    for family in payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        for shadow in family.get("shadows", ()):
            if not isinstance(shadow, Mapping):
                continue
            evidence_views = shadow.get("evidence_views")
            if not isinstance(evidence_views, dict):
                continue
            for view in (
                "reverse_aux_text",
                "reverse_aux_plus_sense_label",
                "reverse_aux_plus_all_evidence",
            ):
                evidence_views.pop(view, None)
    return payload


def _build_reverse_plus_llm_dataset(
    *,
    reverse_augmented_dataset: Mapping[str, object],
    llm_augmented_dataset: Mapping[str, object],
) -> dict[str, object]:
    payload = deepcopy(dict(reverse_augmented_dataset))
    llm_lookup = {
        str(family.get("family_id") or "").strip(): family
        for family in llm_augmented_dataset.get("families", ())
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
    }
    for family in payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        llm_family = llm_lookup.get(family_id)
        if not isinstance(llm_family, Mapping):
            continue
        llm_active = llm_family.get("active")
        active = family.get("active")
        if isinstance(active, Mapping):
            active_views = active.get("evidence_views")
            llm_active_views = (
                llm_active.get("evidence_views") if isinstance(llm_active, Mapping) else {}
            )
            if isinstance(active_views, dict) and isinstance(llm_active_views, Mapping):
                active_views["reverse_aux_plus_llm_cue"] = _join_unique_text_parts(
                    (
                        str(active_views.get("reverse_aux_plus_all_evidence") or "").strip(),
                        str(llm_active_views.get("llm_cue_text") or "").strip(),
                    )
                )
        for shadow in family.get("shadows", ()):
            if not isinstance(shadow, Mapping):
                continue
            shadow_views = shadow.get("evidence_views")
            if isinstance(shadow_views, dict):
                shadow_views["reverse_aux_plus_llm_cue"] = str(
                    shadow_views.get("reverse_aux_plus_all_evidence") or ""
                ).strip()
    return payload


def _attach_config_deltas(config_rows: Sequence[dict[str, object]]) -> None:
    lookup = {
        str(row.get("config_id") or "").strip(): row
        for row in config_rows
        if str(row.get("config_id") or "").strip()
    }
    for row in config_rows:
        baseline_id = str(row.get("baseline_config_id") or "").strip()
        baseline = lookup.get(baseline_id)
        baseline_false = _case_id_set(
            baseline.get("false_abstain_case_ids") if isinstance(baseline, Mapping) else ()
        )
        baseline_harmful = _case_id_set(
            baseline.get("harmful_replace_case_ids") if isinstance(baseline, Mapping) else ()
        )
        false_ids = _case_id_set(row.get("false_abstain_case_ids"))
        harmful_ids = _case_id_set(row.get("harmful_replace_case_ids"))
        row["fixed_false_abstain_case_ids"] = sorted(baseline_false - false_ids)
        row["introduced_false_abstain_case_ids"] = sorted(false_ids - baseline_false)
        row["fixed_harmful_replace_case_ids"] = sorted(baseline_harmful - harmful_ids)
        row["introduced_harmful_replace_case_ids"] = sorted(harmful_ids - baseline_harmful)


def _build_llm_rescue_sweep_rows(
    *,
    primary_config: Mapping[str, object],
    backup_configs: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    primary_rows = _row_lookup(primary_config)
    floors = (-0.10, -0.05, -0.02, 0.0)
    sweep_rows: list[dict[str, object]] = []
    for backup_config in backup_configs:
        backup_rows = _row_lookup(backup_config)
        backup_id = str(backup_config.get("config_id") or "").strip()
        for floor in floors:
            combined_rows: list[dict[str, object]] = []
            rescue_case_ids: list[str] = []
            for case_id, primary in primary_rows.items():
                backup = backup_rows.get(case_id)
                if backup is None:
                    continue
                predicted_decision = str(primary.get("predicted_decision") or "").strip()
                predicted_winner_type = str(primary.get("predicted_winner_type") or "").strip()
                rescue_applied = False
                if (
                    predicted_decision != "replace"
                    and not bool(primary.get("phrase_preemption_hit"))
                    and float(primary.get("margin") or 0.0) >= floor
                    and str(backup.get("predicted_decision") or "").strip() == "replace"
                    and str(backup.get("predicted_winner_type") or "").strip() == "active"
                ):
                    predicted_decision = "replace"
                    predicted_winner_type = "active"
                    rescue_applied = True
                    rescue_case_ids.append(case_id)
                combined_rows.append(
                    {
                        "case_id": case_id,
                        "gold_decision": str(primary.get("gold_decision") or "").strip(),
                        "predicted_decision": predicted_decision,
                        "predicted_winner_type": predicted_winner_type,
                        "rescue_applied": rescue_applied,
                    }
                )
            summary = _summarize_prediction_rows(combined_rows)
            sweep_rows.append(
                {
                    "backup_config_id": backup_id,
                    "primary_margin_floor": floor,
                    "rescue_case_ids": rescue_case_ids,
                    "summary": summary,
                }
            )
    return sweep_rows


def _build_case_diagnostic_rows(
    config_lookup: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    focus_ids = set()
    for config_id in KEY_CONFIG_IDS:
        config = config_lookup.get(config_id)
        if not isinstance(config, Mapping):
            continue
        focus_ids.update(_case_id_set(config.get("false_abstain_case_ids")))
        focus_ids.update(_case_id_set(config.get("harmful_replace_case_ids")))
        focus_ids.update(_case_id_set(config.get("fixed_false_abstain_case_ids")))
        focus_ids.update(_case_id_set(config.get("introduced_false_abstain_case_ids")))
        focus_ids.update(_case_id_set(config.get("introduced_harmful_replace_case_ids")))

    row_lookups = {
        config_id: _row_lookup(config)
        for config_id, config in config_lookup.items()
        if config_id in KEY_CONFIG_IDS
    }
    baseline_rows = row_lookups.get("hard_current_default", {})
    diagnostic_rows: list[dict[str, object]] = []
    for case_id in sorted(focus_ids):
        baseline = baseline_rows.get(case_id)
        if baseline is None:
            continue
        configs: dict[str, object] = {}
        for config_id in KEY_CONFIG_IDS:
            row = row_lookups.get(config_id, {}).get(case_id)
            if row is None:
                continue
            configs[config_id] = {
                "predicted_decision": str(row.get("predicted_decision") or "").strip(),
                "predicted_winner_type": str(row.get("predicted_winner_type") or "").strip(),
                "active_score": _round_float(row.get("active_score")),
                "strongest_shadow_score": _round_float(row.get("strongest_shadow_score")),
                "margin": _round_float(row.get("margin")),
                "phrase_preemption_hit": bool(row.get("phrase_preemption_hit")),
                "active_rescue_applied": bool(row.get("active_rescue_applied")),
            }
        diagnostic_rows.append(
            {
                "case_id": case_id,
                "family_id": str(baseline.get("family_id") or "").strip(),
                "sentence": str(baseline.get("sentence") or "").strip(),
                "gold_decision": str(baseline.get("gold_decision") or "").strip(),
                "gold_winner_type": str(baseline.get("gold_winner_type") or "").strip(),
                "slice_tags": list(baseline.get("slice_tags") or []),
                "configs": configs,
            }
        )
    return diagnostic_rows


def _build_summary_findings(report: Mapping[str, object]) -> dict[str, object]:
    configs = {
        str(row.get("config_id") or "").strip(): row
        for row in report.get("configurations", ())
        if isinstance(row, Mapping)
    }
    baseline = configs.get("hard_current_default", {})
    reverse = configs.get("hard_reverse_aux_plus_all_evidence", {})
    reverse_active_only = configs.get("hard_reverse_aux_active_only", {})
    llm_all = configs.get("hard_llm_cue_plus_all_evidence", {})
    combined = configs.get("hard_reverse_aux_plus_llm_cue", {})
    best_rescue = _best_rescue_row(report.get("llm_rescue_sweep", ()))
    return {
        "reverse_aux_is_current_control": _summary_metrics(reverse),
        "llm_safe_additive_result": _summary_metrics(llm_all),
        "reverse_aux_active_only_result": _summary_metrics(reverse_active_only),
        "reverse_aux_plus_llm_result": _summary_metrics(combined),
        "baseline_result": _summary_metrics(baseline),
        "llm_safe_additive_fixed_false_abstains": list(
            llm_all.get("fixed_false_abstain_case_ids") or []
        ),
        "llm_safe_additive_introduced_false_abstains": list(
            llm_all.get("introduced_false_abstain_case_ids") or []
        ),
        "llm_safe_additive_introduced_harmful": list(
            llm_all.get("introduced_harmful_replace_case_ids") or []
        ),
        "reverse_aux_shadow_side_is_material": _summary_metrics(reverse)
        != _summary_metrics(reverse_active_only),
        "llm_adds_incremental_value_over_reverse_aux": _summary_metrics(combined)
        != _summary_metrics(reverse),
        "best_llm_rescue_probe": best_rescue,
    }


def _build_recommendation(report: Mapping[str, object]) -> str:
    findings = (
        report.get("summary_findings")
        if isinstance(report.get("summary_findings"), Mapping)
        else {}
    )
    reverse_metrics = findings.get("reverse_aux_is_current_control")
    llm_metrics = findings.get("llm_safe_additive_result")
    combined_metrics = findings.get("reverse_aux_plus_llm_result")
    best_rescue = findings.get("best_llm_rescue_probe")
    return (
        "Stop prompt-only iteration. The accepted LLM overlap cues are valid text, "
        f"but the safe additive lane is {_format_metric_summary(llm_metrics)}, while "
        f"reverse auxiliary evidence is {_format_metric_summary(reverse_metrics)}. "
        f"Adding LLM cues on top of reverse auxiliary evidence is {_format_metric_summary(combined_metrics)}, "
        "so the cue text adds no incremental value once the source-derived active/shadow evidence is present. "
        f"The best rescue-only LLM probe is {_format_rescue_summary(best_rescue)}, which still does not beat "
        "the reverse-aux control. The next path should be source/insertion work: build or ingest "
        "competition-symmetric evidence for active and shadow senses, then rerun this diagnostic before any "
        "paid generation."
    )


def render_failure_diagnostic_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Semantic LLM Prompt Failure Diagnostic",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Runtime dataset: `{report.get('dataset_id', '')}`",
        f"- LLM batch: `{(report.get('llm_batch') or {}).get('batch_id', '') if isinstance(report.get('llm_batch'), Mapping) else ''}`",
        f"- Scorer: `{report.get('scorer_id', '')}`",
        "",
        "## Configuration Summary",
        "",
        "| Config | Category | Harmful | False Abstain | Replace Recall | Decision Acc. | Fixed False Abstains | Introduced Harmful |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in report.get("configurations", ()):
        if not isinstance(row, Mapping):
            continue
        summary = row.get("summary") if isinstance(row.get("summary"), Mapping) else {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('label', row.get('config_id', ''))}`",
                    f"`{row.get('category', '')}`",
                    str(summary.get("harmful_replace_count", 0)),
                    str(summary.get("false_abstain_count", 0)),
                    _pct(summary.get("replace_recall")),
                    _pct(summary.get("decision_accuracy")),
                    _join_case_ids(row.get("fixed_false_abstain_case_ids")),
                    _join_case_ids(row.get("introduced_harmful_replace_case_ids")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## LLM Rescue Probe",
            "",
            "| Backup Config | Primary Margin Floor | Harmful | False Abstain | Replace Recall | Rescue Cases |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in report.get("llm_rescue_sweep", ()):
        if not isinstance(row, Mapping):
            continue
        summary = row.get("summary") if isinstance(row.get("summary"), Mapping) else {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('backup_config_id', '')}`",
                    str(row.get("primary_margin_floor", "")),
                    str(summary.get("harmful_replace_count", 0)),
                    str(summary.get("false_abstain_count", 0)),
                    _pct(summary.get("replace_recall")),
                    _join_case_ids(row.get("rescue_case_ids")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Case Diagnostics",
            "",
            "| Case | Gold | Baseline | Reverse Aux | LLM + All | Reverse + LLM |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report.get("case_diagnostics", ()):
        if not isinstance(row, Mapping):
            continue
        configs = row.get("configs") if isinstance(row.get("configs"), Mapping) else {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('case_id', '')}`",
                    f"`{row.get('gold_decision', '')}`",
                    _format_case_config(configs.get("hard_current_default")),
                    _format_case_config(configs.get("hard_reverse_aux_plus_all_evidence")),
                    _format_case_config(configs.get("hard_llm_cue_plus_all_evidence")),
                    _format_case_config(configs.get("hard_reverse_aux_plus_llm_cue")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            f"- {report.get('recommendation', '')}",
        ]
    )
    return "\n".join(lines) + "\n"


def _row_lookup(config: Mapping[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(row.get("case_id") or "").strip(): dict(row)
        for row in config.get("row_results", ())
        if isinstance(row, Mapping) and str(row.get("case_id") or "").strip()
    }


def _summarize_prediction_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    gold_replace_count = 0
    true_replace_count = 0
    true_abstain_count = 0
    harmful_ids: list[str] = []
    false_ids: list[str] = []
    for row in rows:
        gold = str(row.get("gold_decision") or "").strip()
        predicted = str(row.get("predicted_decision") or "").strip()
        if gold == "replace":
            gold_replace_count += 1
        if predicted == "replace" and gold == "replace":
            true_replace_count += 1
        if predicted != "replace" and gold != "replace":
            true_abstain_count += 1
        if predicted == "replace" and gold != "replace":
            harmful_ids.append(str(row.get("case_id") or "").strip())
        if predicted != "replace" and gold == "replace":
            false_ids.append(str(row.get("case_id") or "").strip())
    case_count = len(rows)
    return {
        "cases_total": case_count,
        "decision_accuracy": (true_replace_count + true_abstain_count) / case_count
        if case_count
        else 0.0,
        "replace_recall": true_replace_count / gold_replace_count if gold_replace_count else 0.0,
        "harmful_replace_count": len(harmful_ids),
        "false_abstain_count": len(false_ids),
        "harmful_replace_case_ids": harmful_ids,
        "false_abstain_case_ids": false_ids,
    }


def _summary_metrics(config: object) -> dict[str, object]:
    if not isinstance(config, Mapping):
        return {}
    summary = config.get("summary") if isinstance(config.get("summary"), Mapping) else {}
    return {
        "decision_accuracy": _round_float(summary.get("decision_accuracy")),
        "replace_recall": _round_float(summary.get("replace_recall")),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
    }


def _best_rescue_row(rows: object) -> dict[str, object]:
    candidates = (
        [dict(row) for row in rows if isinstance(row, Mapping)]
        if isinstance(rows, Sequence)
        else []
    )
    if not candidates:
        return {}
    return min(
        candidates,
        key=lambda row: (
            int((row.get("summary") or {}).get("harmful_replace_count") or 0)
            if isinstance(row.get("summary"), Mapping)
            else 0,
            int((row.get("summary") or {}).get("false_abstain_count") or 0)
            if isinstance(row.get("summary"), Mapping)
            else 0,
            -float((row.get("summary") or {}).get("decision_accuracy") or 0.0)
            if isinstance(row.get("summary"), Mapping)
            else 0.0,
        ),
    )


def _format_metric_summary(value: object) -> str:
    if not isinstance(value, Mapping):
        return "unavailable"
    return (
        f"`{_pct(value.get('decision_accuracy'))}` accuracy / "
        f"`{_pct(value.get('replace_recall'))}` recall / "
        f"`{value.get('harmful_replace_count', 0)}` harmful / "
        f"`{value.get('false_abstain_count', 0)}` false abstains"
    )


def _format_rescue_summary(value: object) -> str:
    if not isinstance(value, Mapping):
        return "unavailable"
    summary = value.get("summary") if isinstance(value.get("summary"), Mapping) else {}
    return (
        f"`{value.get('backup_config_id', '')}` at margin floor `{value.get('primary_margin_floor', '')}`: "
        f"{_pct(summary.get('decision_accuracy'))} accuracy / "
        f"{_pct(summary.get('replace_recall'))} recall / "
        f"{summary.get('harmful_replace_count', 0)} harmful / "
        f"{summary.get('false_abstain_count', 0)} false abstains"
    )


def _format_case_config(value: object) -> str:
    if not isinstance(value, Mapping):
        return "`n/a`"
    return (
        f"`{value.get('predicted_decision', '')}` "
        f"m={value.get('margin', '')} "
        f"a={value.get('active_score', '')} "
        f"s={value.get('strongest_shadow_score', '')}"
    )


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _round_float(value: object) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _case_id_set(value: object) -> set[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return {str(item).strip() for item in value if str(item).strip()}
    text = str(value or "").strip()
    return {text} if text else set()


def _join_case_ids(value: object) -> str:
    items = sorted(_case_id_set(value))
    if not items:
        return "none"
    return ", ".join(f"`{item}`" for item in items)


def _join_unique_text_parts(parts: Sequence[str]) -> str:
    values: list[str] = []
    for part in parts:
        text = str(part or "").strip()
        if text and text not in values:
            values.append(text)
    return " | ".join(values)


def main() -> int:
    args = _parse_args()
    queue_payload = _load_json(args.queue_json)
    dataset_payload = load_sentence_veto_dataset(args.dataset)
    llm_batch_payload = load_normalized_llm_batch(args.llm_batch_json)

    helper_paths = build_helper_paths(Path(args.data_root))
    _forward_pack, reverse_pack = resolve_pair_translation_packs(
        helper_paths,
        pair="en-es",
        reverse_translation_dict_path=args.reverse_translation_dict,
    )
    reverse_records_by_trigger: dict[str, Sequence[TranslationGlossRecord]] = {}
    if reverse_pack is not None and reverse_pack.path.exists():
        triggers = sorted(
            {
                str(item.get("trigger") or "").strip()
                for item in queue_payload.get("families", ())
                if isinstance(item, Mapping) and str(item.get("trigger") or "").strip()
            }
        )
        reverse_records_by_trigger = load_translation_gloss_records_ordered(
            reverse_pack.path,
            target_lang="es",
            headwords=triggers,
        )

    report = build_failure_diagnostic_report(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        llm_batch_payload=llm_batch_payload,
        reverse_records_by_trigger=reverse_records_by_trigger,
        data_root=Path(args.data_root),
        reverse_pack=reverse_pack,
        scorer_id=str(args.scorer_id or "").strip() or DEFAULT_SCORER_ID,
        min_active_score=float(args.min_active_score),
        min_margin=float(args.min_margin),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_failure_diagnostic_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
