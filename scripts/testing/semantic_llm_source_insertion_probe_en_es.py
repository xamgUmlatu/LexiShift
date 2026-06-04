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
from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    build_runtime_context_views,
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
from semantic_llm_prompt_failure_diagnostic_en_es import (  # noqa: E402
    _build_reverse_plus_llm_dataset,
    _drop_shadow_reverse_aux_views,
)
from semantic_reverse_aux_text_pilot_en_es import (  # noqa: E402
    augment_queue_dataset_with_reverse_aux_views,
    build_queue_subset_dataset,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_source_insertion_probe_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_source_insertion_probe_latest.md"
)
MIXED_LLM_ACTIVE_SHADOW_REVERSE_VIEW = "llm_active_shadow_reverse_aux"
REVERSE_AUX_VIEW = "reverse_aux_plus_all_evidence"
LLM_ADD_VIEW = "llm_cue_plus_all_evidence"
REVIEWED_EXAMPLE_FRAME_VIEW = "reviewed_example_frame_text"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a no-spend en-es source/insertion probe after the LLM prompt cue "
            "tranches failed the downstream gate."
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


def build_source_insertion_probe_report(
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
    reverse_shadow_only_dataset = _drop_active_reverse_aux_views(reverse_augmented_dataset)
    llm_active_shadow_reverse_dataset = _build_llm_active_shadow_reverse_dataset(
        subset_dataset=subset_dataset,
        llm_augmented_dataset=llm_augmented_dataset,
        reverse_augmented_dataset=reverse_augmented_dataset,
    )
    reviewed_frame_dataset, reviewed_frame_coverage_rows = _build_reviewed_frame_dataset(
        subset_dataset
    )
    reverse_plus_llm_dataset = _build_reverse_plus_llm_dataset(
        reverse_augmented_dataset=reverse_augmented_dataset,
        llm_augmented_dataset=llm_augmented_dataset,
    )

    config_inputs = (
        _config(
            "hard_current_default",
            "Hard current default runtime row",
            subset_dataset,
            "all_evidence_text",
            "family_all",
            "baseline",
        ),
        _config(
            "hard_reverse_aux_active_only",
            "Hard reverse aux active-only",
            reverse_active_only_dataset,
            REVERSE_AUX_VIEW,
            "family_all",
            "source_ablation",
        ),
        _config(
            "hard_reverse_aux_shadow_only",
            "Hard reverse aux shadow-only",
            reverse_shadow_only_dataset,
            REVERSE_AUX_VIEW,
            "family_all",
            "source_ablation",
        ),
        _config(
            "hard_reverse_aux_symmetric",
            "Hard reverse aux symmetric",
            reverse_augmented_dataset,
            REVERSE_AUX_VIEW,
            "family_all",
            "source_control",
        ),
        _config(
            "hard_llm_active_base_shadow",
            "Hard LLM active cue with base shadows",
            llm_augmented_dataset,
            LLM_ADD_VIEW,
            "family_all",
            "llm_insertion_probe",
        ),
        _config(
            "hard_llm_active_reverse_shadow",
            "Hard LLM active cue with reverse shadows",
            llm_active_shadow_reverse_dataset,
            MIXED_LLM_ACTIVE_SHADOW_REVERSE_VIEW,
            "family_all",
            "mixed_insertion_probe",
        ),
        _config(
            "hard_reviewed_example_frames",
            "Hard reviewed example frames",
            reviewed_frame_dataset,
            REVIEWED_EXAMPLE_FRAME_VIEW,
            "family_all",
            "reviewed_source_oracle",
        ),
        _config(
            "active_guard_reviewed_example_frames",
            "Active-guard reviewed example frames",
            reviewed_frame_dataset,
            REVIEWED_EXAMPLE_FRAME_VIEW,
            "active_only",
            "reviewed_source_oracle",
        ),
        _config(
            "hard_reverse_aux_plus_llm_cue",
            "Hard reverse aux plus LLM cue",
            reverse_plus_llm_dataset,
            "reverse_aux_plus_llm_cue",
            "family_all",
            "combined_source_probe",
            baseline_config_id="hard_reverse_aux_symmetric",
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
    case_matrix_rows = _build_case_matrix_rows(config_rows)
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
        "reviewed_frame_coverage_rows": reviewed_frame_coverage_rows,
        "configurations": config_rows,
        "case_matrix": case_matrix_rows,
    }
    report["summary_findings"] = _build_summary_findings(report)
    report["recommendation"] = _build_recommendation(report)
    return report


def _config(
    config_id: str,
    label: str,
    payload: Mapping[str, object],
    evidence_view: str,
    phrase_guard_pos_scope: str,
    category: str,
    *,
    baseline_config_id: str = "hard_current_default",
) -> tuple[str, str, Mapping[str, object], str, str, str, str]:
    return (
        config_id,
        label,
        payload,
        evidence_view,
        phrase_guard_pos_scope,
        baseline_config_id,
        category,
    )


def _drop_active_reverse_aux_views(dataset_payload: Mapping[str, object]) -> dict[str, object]:
    payload = deepcopy(dict(dataset_payload))
    for family in payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        active = family.get("active")
        evidence_views = active.get("evidence_views") if isinstance(active, Mapping) else {}
        if not isinstance(evidence_views, dict):
            continue
        for view in ("reverse_aux_text", "reverse_aux_plus_sense_label", REVERSE_AUX_VIEW):
            evidence_views.pop(view, None)
    return payload


def _build_reviewed_frame_dataset(
    dataset_payload: Mapping[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    payload = deepcopy(dict(dataset_payload))
    coverage_rows: list[dict[str, object]] = []
    for family in payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        trigger = str(family.get("trigger") or "").strip()
        active = family.get("active")
        if not isinstance(active, Mapping):
            continue
        active_examples = _reviewed_examples_for_sense(
            family,
            sense_id=str(active.get("sense_id") or "").strip(),
        )
        active_views = active.get("evidence_views")
        if isinstance(active_views, dict):
            active_views[REVIEWED_EXAMPLE_FRAME_VIEW] = _join_unique_text_parts(active_examples)

        shadow_example_counts: list[int] = []
        for shadow in family.get("shadows", ()):
            if not isinstance(shadow, Mapping):
                continue
            shadow_examples = _reviewed_examples_for_sense(
                family,
                sense_id=str(shadow.get("sense_id") or "").strip(),
            )
            shadow_views = shadow.get("evidence_views")
            if isinstance(shadow_views, dict):
                shadow_views[REVIEWED_EXAMPLE_FRAME_VIEW] = _join_unique_text_parts(shadow_examples)
            shadow_example_counts.append(len(shadow_examples))

        coverage_rows.append(
            {
                "family_id": family_id,
                "trigger": trigger,
                "active_target": str(active.get("target_lemma") or "").strip(),
                "active_example_count": len(active_examples),
                "shadow_example_counts": shadow_example_counts,
                "sample_active_examples": active_examples[:2],
            }
        )
    return payload, coverage_rows


def _reviewed_examples_for_sense(
    family: Mapping[str, object],
    *,
    sense_id: str,
) -> list[str]:
    examples: list[str] = []
    trigger = str(family.get("trigger") or "").strip()
    for case in family.get("cases", ()):
        if not isinstance(case, Mapping):
            continue
        if str(case.get("gold_winner") or "").strip() != sense_id:
            continue
        if "phrase_control" in _normalize_string_list(case.get("slice_tags")):
            continue
        context_views = build_runtime_context_views(
            str(case.get("sentence") or "").strip(),
            source_phrase=str(case.get("source_phrase") or trigger).strip(),
        )
        example = str(context_views.get("masked_sentence") or "").strip()
        if example and example not in examples:
            examples.append(example)
    return examples[:2]


def _build_llm_active_shadow_reverse_dataset(
    *,
    subset_dataset: Mapping[str, object],
    llm_augmented_dataset: Mapping[str, object],
    reverse_augmented_dataset: Mapping[str, object],
) -> dict[str, object]:
    payload = deepcopy(dict(subset_dataset))
    llm_lookup = _family_lookup(llm_augmented_dataset)
    reverse_lookup = _family_lookup(reverse_augmented_dataset)
    for family in payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        llm_family = llm_lookup.get(family_id, {})
        reverse_family = reverse_lookup.get(family_id, {})
        _set_mixed_active_view(family, llm_family)
        _set_mixed_shadow_views(family, reverse_family)
    return payload


def _set_mixed_active_view(
    family: Mapping[str, object],
    llm_family: Mapping[str, object],
) -> None:
    active = family.get("active")
    llm_active = llm_family.get("active") if isinstance(llm_family, Mapping) else {}
    active_views = active.get("evidence_views") if isinstance(active, Mapping) else {}
    llm_views = llm_active.get("evidence_views") if isinstance(llm_active, Mapping) else {}
    if isinstance(active_views, dict) and isinstance(llm_views, Mapping):
        active_views[MIXED_LLM_ACTIVE_SHADOW_REVERSE_VIEW] = str(
            llm_views.get(LLM_ADD_VIEW) or ""
        ).strip()


def _set_mixed_shadow_views(
    family: Mapping[str, object],
    reverse_family: Mapping[str, object],
) -> None:
    reverse_shadows = {
        str(shadow.get("sense_id") or "").strip(): shadow
        for shadow in reverse_family.get("shadows", ())
        if isinstance(shadow, Mapping) and str(shadow.get("sense_id") or "").strip()
    }
    for shadow in family.get("shadows", ()):
        if not isinstance(shadow, Mapping):
            continue
        shadow_id = str(shadow.get("sense_id") or "").strip()
        reverse_shadow = reverse_shadows.get(shadow_id, {})
        shadow_views = shadow.get("evidence_views")
        reverse_views = (
            reverse_shadow.get("evidence_views") if isinstance(reverse_shadow, Mapping) else {}
        )
        if isinstance(shadow_views, dict) and isinstance(reverse_views, Mapping):
            shadow_views[MIXED_LLM_ACTIVE_SHADOW_REVERSE_VIEW] = str(
                reverse_views.get(REVERSE_AUX_VIEW) or ""
            ).strip()


def _family_lookup(dataset_payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(family.get("family_id") or "").strip(): family
        for family in dataset_payload.get("families", ())
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
    }


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


def _build_case_matrix_rows(config_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    focus_ids: set[str] = set()
    for row in config_rows:
        focus_ids.update(_case_id_set(row.get("false_abstain_case_ids")))
        focus_ids.update(_case_id_set(row.get("harmful_replace_case_ids")))
        focus_ids.update(_case_id_set(row.get("fixed_false_abstain_case_ids")))
        focus_ids.update(_case_id_set(row.get("introduced_false_abstain_case_ids")))
        focus_ids.update(_case_id_set(row.get("introduced_harmful_replace_case_ids")))

    row_lookups = {
        str(config.get("config_id") or "").strip(): _row_lookup(config)
        for config in config_rows
        if str(config.get("config_id") or "").strip()
    }
    baseline_rows = row_lookups.get("hard_current_default", {})
    case_rows: list[dict[str, object]] = []
    for case_id in sorted(focus_ids):
        baseline = baseline_rows.get(case_id)
        if baseline is None:
            continue
        config_predictions = {}
        for config_id, lookup in row_lookups.items():
            row = lookup.get(case_id)
            if row is not None:
                config_predictions[config_id] = _case_prediction(row)
        case_rows.append(
            {
                "case_id": case_id,
                "family_id": str(baseline.get("family_id") or "").strip(),
                "gold_decision": str(baseline.get("gold_decision") or "").strip(),
                "slice_tags": list(baseline.get("slice_tags") or []),
                "configs": config_predictions,
            }
        )
    return case_rows


def _row_lookup(config: Mapping[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(row.get("case_id") or "").strip(): dict(row)
        for row in config.get("row_results", ())
        if isinstance(row, Mapping) and str(row.get("case_id") or "").strip()
    }


def _case_prediction(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "predicted_decision": str(row.get("predicted_decision") or "").strip(),
        "predicted_winner_type": str(row.get("predicted_winner_type") or "").strip(),
        "active_score": _round_float(row.get("active_score")),
        "strongest_shadow_score": _round_float(row.get("strongest_shadow_score")),
        "margin": _round_float(row.get("margin")),
        "phrase_preemption_hit": bool(row.get("phrase_preemption_hit")),
        "active_rescue_applied": bool(row.get("active_rescue_applied")),
    }


def _build_summary_findings(report: Mapping[str, object]) -> dict[str, object]:
    configs = {
        str(row.get("config_id") or "").strip(): row
        for row in report.get("configurations", ())
        if isinstance(row, Mapping)
    }
    reverse = _summary_metrics(configs.get("hard_reverse_aux_symmetric"))
    active_only = _summary_metrics(configs.get("hard_reverse_aux_active_only"))
    shadow_only = _summary_metrics(configs.get("hard_reverse_aux_shadow_only"))
    llm_base = _summary_metrics(configs.get("hard_llm_active_base_shadow"))
    llm_shadow = _summary_metrics(configs.get("hard_llm_active_reverse_shadow"))
    reviewed_frames = _summary_metrics(configs.get("hard_reviewed_example_frames"))
    active_guard_reviewed = _summary_metrics(configs.get("active_guard_reviewed_example_frames"))
    combined = _summary_metrics(configs.get("hard_reverse_aux_plus_llm_cue"))
    return {
        "reverse_aux_symmetric_result": reverse,
        "reverse_aux_active_only_result": active_only,
        "reverse_aux_shadow_only_result": shadow_only,
        "llm_active_base_shadow_result": llm_base,
        "llm_active_reverse_shadow_result": llm_shadow,
        "reviewed_example_frame_result": reviewed_frames,
        "active_guard_reviewed_example_frame_result": active_guard_reviewed,
        "reverse_aux_plus_llm_result": combined,
        "symmetric_reverse_beats_single_sided_reverse": _beats(reverse, active_only)
        and _beats(reverse, shadow_only),
        "shadow_calibration_salvages_llm_active_cues": _beats(llm_shadow, llm_base)
        and _beats(llm_shadow, reverse),
        "active_guard_reviewed_frames_beat_reverse_aux": _beats(active_guard_reviewed, reverse),
        "llm_adds_incremental_value_over_reverse_aux": combined != reverse,
    }


def _beats(candidate: Mapping[str, object], baseline: Mapping[str, object]) -> bool:
    return int(candidate.get("harmful_replace_count") or 0) <= int(
        baseline.get("harmful_replace_count") or 0
    ) and int(candidate.get("false_abstain_count") or 0) < int(
        baseline.get("false_abstain_count") or 0
    )


def _build_recommendation(report: Mapping[str, object]) -> str:
    findings = (
        report.get("summary_findings")
        if isinstance(report.get("summary_findings"), Mapping)
        else {}
    )
    reverse = findings.get("reverse_aux_symmetric_result")
    active_only = findings.get("reverse_aux_active_only_result")
    shadow_only = findings.get("reverse_aux_shadow_only_result")
    llm_shadow = findings.get("llm_active_reverse_shadow_result")
    reviewed_active_guard = findings.get("active_guard_reviewed_example_frame_result")
    return (
        "Keep the next step source/insertion-shaped. Full reverse-aux evidence is "
        f"{_format_metric_summary(reverse)}, while active-only reverse is "
        f"{_format_metric_summary(active_only)} and shadow-only reverse is "
        f"{_format_metric_summary(shadow_only)}. The mixed LLM-active plus reverse-shadow "
        f"probe is {_format_metric_summary(llm_shadow)}, so shadow calibration alone does "
        "not salvage active-only LLM cue insertion. The internal reviewed example-frame "
        f"oracle with the active-sense phrase guard is {_format_metric_summary(reviewed_active_guard)}, "
        "which shows the next viable path is competition-symmetric example/frame evidence plus "
        "phrase-leak containment. It is not runtime-publishable evidence; use it as an upper-bound "
        "target for external source ingestion or future paid generation."
    )


def render_source_insertion_probe_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Semantic LLM Source/Insertion Probe",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Runtime dataset: `{report.get('dataset_id', '')}`",
        f"- LLM batch: `{_llm_batch_id(report)}`",
        f"- Scorer: `{report.get('scorer_id', '')}`",
        "",
        "## Insertion Matrix",
        "",
        "| Config | Category | Phrase Guard | Harmful | False Abstain | Replace Recall | Decision Acc. | Fixed False Abstains | Introduced Harmful |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
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
                    f"`{row.get('phrase_guard_pos_scope', '')}`",
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
            "## Focus Case Matrix",
            "",
            "| Case | Gold | Baseline | Reverse active | Reverse shadow | Reverse full | LLM active + reverse shadow | Reviewed active guard |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report.get("case_matrix", ()):
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
                    _format_case_config(configs.get("hard_reverse_aux_active_only")),
                    _format_case_config(configs.get("hard_reverse_aux_shadow_only")),
                    _format_case_config(configs.get("hard_reverse_aux_symmetric")),
                    _format_case_config(configs.get("hard_llm_active_reverse_shadow")),
                    _format_case_config(configs.get("active_guard_reviewed_example_frames")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _llm_batch_id(report: Mapping[str, object]) -> str:
    batch = report.get("llm_batch")
    return str(batch.get("batch_id") or "").strip() if isinstance(batch, Mapping) else ""


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


def _format_metric_summary(value: object) -> str:
    if not isinstance(value, Mapping):
        return "unavailable"
    return (
        f"`{_pct(value.get('decision_accuracy'))}` accuracy / "
        f"`{_pct(value.get('replace_recall'))}` recall / "
        f"`{value.get('harmful_replace_count', 0)}` harmful / "
        f"`{value.get('false_abstain_count', 0)}` false abstains"
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


def _normalize_string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _join_unique_text_parts(parts: Sequence[str]) -> str:
    values: list[str] = []
    for part in parts:
        text = str(part or "").strip()
        if text and text not in values:
            values.append(text)
    return " | ".join(values)


def _join_case_ids(value: object) -> str:
    items = sorted(_case_id_set(value))
    return ", ".join(f"`{item}`" for item in items) if items else "none"


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

    report = build_source_insertion_probe_report(
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
    args.markdown_out.write_text(render_source_insertion_probe_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
