#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
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
from semantic_llm_prompt_reporting import render_prompt_downstream_markdown  # noqa: E402
from semantic_reverse_aux_text_pilot_en_es import (  # noqa: E402
    augment_queue_dataset_with_reverse_aux_views,
    build_queue_subset_dataset,
)
from semantic_routing_sentence_veto_support import (  # noqa: E402
    build_sentence_veto_report,
    load_sentence_veto_dataset,
)


DEFAULT_QUEUE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing"
    / "semantic_prompt_bakeoff_queue_en_es.json"
)
DEFAULT_DATASET_PATH = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing_cases"
    / "en_es_sentence_veto_v10.json"
)
DEFAULT_LLM_BATCH_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "experiments"
    / "semantic_llm_prompt_batches"
    / "en-es-target-prompt-target-v2-20260424a_normalized_evidence.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_downstream_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_downstream_latest.md"
)

DEFAULT_SCORER_ID = "sentence_transformer_cosine"
DEFAULT_CONTEXT_VIEW = "masked_sentence"
DEFAULT_MIN_ACTIVE_SCORE = 0.0
DEFAULT_MIN_MARGIN = 0.0
DEFAULT_PHRASE_CONTROL_MODE = "noun_family_frame_guard"
DEFAULT_ACTIVE_RESCUE_MODE = "sense_label_near_tie_active_rescue"

CONFIG_SPECS: tuple[dict[str, object], ...] = (
    {
        "config_id": "hard_current_default",
        "label": "Hard current default runtime row",
        "dataset_variant": "base",
        "evidence_view": "all_evidence_text",
        "phrase_guard_pos_scope": "family_all",
        "baseline_config_id": "hard_current_default",
        "category": "hard_reference",
    },
    {
        "config_id": "hard_reverse_aux_plus_all_evidence",
        "label": "Hard reverse aux plus all evidence",
        "dataset_variant": "reverse_aux",
        "evidence_view": "reverse_aux_plus_all_evidence",
        "phrase_guard_pos_scope": "family_all",
        "baseline_config_id": "hard_current_default",
        "category": "hard_control",
    },
    {
        "config_id": "hard_llm_cue_text",
        "label": "Hard LLM cue text only",
        "dataset_variant": "llm",
        "evidence_view": "llm_cue_text",
        "phrase_guard_pos_scope": "family_all",
        "baseline_config_id": "hard_current_default",
        "category": "llm_diagnostic",
    },
    {
        "config_id": "hard_llm_cue_plus_sense_label",
        "label": "Hard LLM cue plus sense label",
        "dataset_variant": "llm",
        "evidence_view": "llm_cue_plus_sense_label",
        "phrase_guard_pos_scope": "family_all",
        "baseline_config_id": "hard_current_default",
        "category": "llm_diagnostic",
    },
    {
        "config_id": "hard_llm_cue_plus_gloss",
        "label": "Hard LLM cue plus gloss",
        "dataset_variant": "llm",
        "evidence_view": "llm_cue_plus_gloss",
        "phrase_guard_pos_scope": "family_all",
        "baseline_config_id": "hard_current_default",
        "category": "llm_diagnostic",
    },
    {
        "config_id": "hard_llm_cue_plus_all_evidence",
        "label": "Hard LLM cue plus all evidence",
        "dataset_variant": "llm",
        "evidence_view": "llm_cue_plus_all_evidence",
        "phrase_guard_pos_scope": "family_all",
        "baseline_config_id": "hard_current_default",
        "category": "hard_llm_candidate",
    },
    {
        "config_id": "active_only_current_default",
        "label": "Active-sense overlay reference",
        "dataset_variant": "base",
        "evidence_view": "all_evidence_text",
        "phrase_guard_pos_scope": "active_only",
        "baseline_config_id": "active_only_current_default",
        "category": "overlay_reference",
    },
    {
        "config_id": "active_only_reverse_aux_plus_all_evidence",
        "label": "Active-sense overlay reverse aux plus all evidence",
        "dataset_variant": "reverse_aux",
        "evidence_view": "reverse_aux_plus_all_evidence",
        "phrase_guard_pos_scope": "active_only",
        "baseline_config_id": "active_only_current_default",
        "category": "overlay_control",
    },
    {
        "config_id": "active_only_llm_cue_plus_all_evidence",
        "label": "Active-sense overlay LLM cue plus all evidence",
        "dataset_variant": "llm",
        "evidence_view": "llm_cue_plus_all_evidence",
        "phrase_guard_pos_scope": "active_only",
        "baseline_config_id": "active_only_current_default",
        "category": "overlay_llm_candidate",
    },
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the downstream fixed-shadow comparison for the frozen en-es prompt "
            "bakeoff queue using the accepted gpt-5.4 cue batch."
        )
    )
    parser.add_argument(
        "--queue-json",
        type=Path,
        default=DEFAULT_QUEUE_JSON,
        help="Frozen prompt bakeoff queue JSON.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Sentence-veto dataset JSON.",
    )
    parser.add_argument(
        "--llm-batch-json",
        type=Path,
        default=DEFAULT_LLM_BATCH_JSON,
        help="Normalized target-model LLM batch JSON.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(resolve_data_root()),
        help="LexiShift data root (default: helper resolve_data_root()).",
    )
    parser.add_argument(
        "--reverse-translation-dict",
        type=Path,
        default=None,
        help="Optional explicit reverse translation pack path for en-es.",
    )
    parser.add_argument(
        "--scorer-id",
        default=DEFAULT_SCORER_ID,
        help="Sentence-veto scorer to use for the downstream bakeoff.",
    )
    parser.add_argument(
        "--min-active-score",
        type=float,
        default=DEFAULT_MIN_ACTIVE_SCORE,
        help="Min active score for sentence-veto evaluation.",
    )
    parser.add_argument(
        "--min-margin",
        type=float,
        default=DEFAULT_MIN_MARGIN,
        help="Min margin for sentence-veto evaluation.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_MARKDOWN_OUT,
        help="Output Markdown artifact path.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _build_pack_record(pack: TranslationPackRef | None) -> dict[str, object] | None:
    if pack is None:
        return None
    return {
        "path": str(pack.path),
        "exists": pack.path.exists(),
        "provider": pack.provider,
        "pack_id": pack.pack_id,
        "direction": pack.direction,
    }


def _join_unique_text_parts(parts: Sequence[str]) -> str:
    deduped: list[str] = []
    for part in parts:
        text = str(part or "").strip()
        if text and text not in deduped:
            deduped.append(text)
    return " | ".join(deduped)


def _normalize_string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _build_focus_case_row(row: Mapping[str, object] | None) -> dict[str, object]:
    if not isinstance(row, Mapping):
        return {}
    return {
        "case_id": str(row.get("case_id") or "").strip(),
        "family_id": str(row.get("family_id") or "").strip(),
        "gold_decision": str(row.get("gold_decision") or "").strip(),
        "predicted_decision": str(row.get("predicted_decision") or "").strip(),
        "predicted_winner": str(row.get("predicted_winner") or "").strip(),
        "margin": row.get("margin"),
        "phrase_preemption_hit": bool(row.get("phrase_preemption_hit")),
        "active_rescue_applied": bool(row.get("active_rescue_applied")),
    }


def load_normalized_llm_batch(path: Path) -> dict[str, object]:
    payload = _load_json(path)
    rows = payload.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError(f"{path} must contain a normalized evidence batch with `rows`.")
    payload["rows"] = [dict(row) for row in rows if isinstance(row, Mapping)]
    return payload


def augment_queue_dataset_with_llm_cue_views(
    dataset_payload: Mapping[str, object],
    *,
    family_roles: Mapping[str, str],
    llm_batch_payload: Mapping[str, object],
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object]]:
    augmented_payload = deepcopy(dict(dataset_payload))
    families = augmented_payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
        raise ValueError("Queue subset dataset is missing a `families` array.")

    family_ids = set(family_roles.keys())
    llm_rows = [
        dict(row)
        for row in llm_batch_payload.get("rows", ())
        if isinstance(row, Mapping)
        and str(row.get("relation_type") or "").strip() == "anchor_cue"
    ]
    cues_by_active_sense: dict[str, list[str]] = {}
    family_row_bundles: dict[str, list[dict[str, object]]] = {}
    unmatched_row_ids: list[str] = []
    review_states: set[str] = set()
    runtime_publishable_count = 0

    for row in llm_rows:
        metadata = row.get("metadata") if isinstance(row.get("metadata"), Mapping) else {}
        family_id = str(metadata.get("family_id") or "").strip()
        row_id = str(row.get("row_id") or "").strip()
        if family_id not in family_ids:
            if row_id:
                unmatched_row_ids.append(row_id)
            continue
        active_hint = (
            row.get("active_sense_hint") if isinstance(row.get("active_sense_hint"), Mapping) else {}
        )
        active_sense_id = str(
            active_hint.get("target_key") or metadata.get("active_sense_id") or ""
        ).strip()
        evidence_text = str(row.get("evidence_text") or "").strip()
        if active_sense_id and evidence_text:
            cues_by_active_sense.setdefault(active_sense_id, [])
            if evidence_text not in cues_by_active_sense[active_sense_id]:
                cues_by_active_sense[active_sense_id].append(evidence_text)
        family_row_bundles.setdefault(family_id, []).append(row)
        review_state = str(row.get("review_state") or "").strip()
        if review_state:
            review_states.add(review_state)
        if bool(row.get("runtime_publishable")):
            runtime_publishable_count += 1

    coverage_rows: list[dict[str, object]] = []
    for family in families:
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        role = str(family_roles.get(family_id) or "target")
        trigger = str(family.get("trigger") or "").strip()
        active = family.get("active")
        if not isinstance(active, dict):
            continue
        active_sense_id = str(active.get("sense_id") or "").strip()
        cue_text = _join_unique_text_parts(cues_by_active_sense.get(active_sense_id, ()))
        evidence_views = active.get("evidence_views")
        if not isinstance(evidence_views, dict):
            evidence_views = {}
            active["evidence_views"] = evidence_views
        if cue_text:
            evidence_views["llm_cue_text"] = cue_text
            evidence_views["llm_cue_plus_sense_label"] = _join_unique_text_parts(
                (str(evidence_views.get("sense_label") or "").strip(), cue_text)
            )
            evidence_views["llm_cue_plus_gloss"] = _join_unique_text_parts(
                (str(evidence_views.get("gloss_text") or "").strip(), cue_text)
            )
            evidence_views["llm_cue_plus_all_evidence"] = _join_unique_text_parts(
                (str(evidence_views.get("all_evidence_text") or "").strip(), cue_text)
            )
        family_rows = family_row_bundles.get(family_id, [])
        coverage_rows.append(
            {
                "family_id": family_id,
                "role": role,
                "trigger": trigger,
                "active_target": str(active.get("target_lemma") or "").strip(),
                "llm_cue_ready": bool(cue_text),
                "llm_cue_row_count": len(family_rows),
                "sample_llm_cue_texts": [str(row.get("evidence_text") or "").strip() for row in family_rows if str(row.get("evidence_text") or "").strip()][:2],
                "prompt_slots": list(
                    dict.fromkeys(
                        str(((row.get("provenance") or {}) if isinstance(row.get("provenance"), Mapping) else {}).get("prompt_slot") or "").strip()
                        for row in family_rows
                        if str(((row.get("provenance") or {}) if isinstance(row.get("provenance"), Mapping) else {}).get("prompt_slot") or "").strip()
                    )
                ),
                "review_states": list(
                    dict.fromkeys(
                        str(row.get("review_state") or "").strip()
                        for row in family_rows
                        if str(row.get("review_state") or "").strip()
                    )
                ),
                "runtime_publishable_count": sum(
                    1 for row in family_rows if bool(row.get("runtime_publishable"))
                ),
            }
        )

    llm_summary = {
        "batch_id": str(llm_batch_payload.get("batch_id") or "").strip(),
        "source_id": str(llm_batch_payload.get("source_id") or "").strip(),
        "prompt_version": str(llm_batch_payload.get("prompt_version") or "").strip(),
        "model_id": str(llm_batch_payload.get("model_id") or "").strip(),
        "generated_at": str(llm_batch_payload.get("generated_at") or "").strip(),
        "review_state": str(llm_batch_payload.get("review_state") or "").strip(),
        "row_count": len(llm_rows),
        "runtime_publishable_count": int(runtime_publishable_count),
        "distinct_review_states": sorted(review_states),
        "unmatched_row_ids": unmatched_row_ids,
    }
    return augmented_payload, coverage_rows, llm_summary


def _run_sentence_veto_config(
    *,
    dataset_payload: Mapping[str, object],
    config_id: str,
    label: str,
    evidence_view: str,
    phrase_guard_pos_scope: str,
    baseline_config_id: str,
    category: str,
    scorer_id: str,
    min_active_score: float,
    min_margin: float,
) -> dict[str, object]:
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(dataset_payload, handle, ensure_ascii=False, indent=2)
        handle.flush()
        dataset_path = Path(handle.name)
    try:
        config_report = build_sentence_veto_report(
            dataset_path=dataset_path,
            scorer_id=scorer_id,
            context_view=DEFAULT_CONTEXT_VIEW,
            evidence_view=evidence_view,
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_control_mode=DEFAULT_PHRASE_CONTROL_MODE,
            phrase_guard_pos_scope=phrase_guard_pos_scope,
            active_rescue_mode=DEFAULT_ACTIVE_RESCUE_MODE,
        )
    finally:
        dataset_path.unlink(missing_ok=True)

    summary = dict(config_report.get("summary") or {})
    return {
        "config_id": config_id,
        "label": label,
        "baseline_config_id": baseline_config_id,
        "category": category,
        "evidence_view": evidence_view,
        "phrase_guard_pos_scope": phrase_guard_pos_scope,
        "summary": summary,
        "harmful_replace_case_ids": [
            str(row.get("case_id") or "")
            for row in config_report.get("sample_harmful_replace_rows", ())
            if isinstance(row, Mapping)
        ],
        "false_abstain_case_ids": [
            str(row.get("case_id") or "")
            for row in config_report.get("sample_false_abstain_rows", ())
            if isinstance(row, Mapping)
        ],
        "row_results": [
            dict(row)
            for row in config_report.get("row_results", ())
            if isinstance(row, Mapping)
        ],
    }


def build_prompt_downstream_report(
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
    llm_augmented_dataset, llm_coverage_rows, llm_batch_summary = augment_queue_dataset_with_llm_cue_views(
        subset_dataset,
        family_roles=family_roles,
        llm_batch_payload=llm_batch_payload,
    )
    reverse_augmented_dataset, reverse_aux_coverage_rows = augment_queue_dataset_with_reverse_aux_views(
        subset_dataset,
        family_roles=family_roles,
        reverse_records_by_trigger=reverse_records_by_trigger,
    )

    missing_resources: list[str] = []
    if reverse_pack is None or not reverse_pack.path.exists():
        missing_resources.append("reverse_translation_pack")

    config_rows: list[dict[str, object]] = []
    for spec in CONFIG_SPECS:
        dataset_variant = str(spec.get("dataset_variant") or "").strip()
        if dataset_variant == "reverse_aux" and missing_resources:
            continue
        variant_payload = subset_dataset
        if dataset_variant == "llm":
            variant_payload = llm_augmented_dataset
        elif dataset_variant == "reverse_aux":
            variant_payload = reverse_augmented_dataset
        config_rows.append(
            _run_sentence_veto_config(
                dataset_payload=variant_payload,
                config_id=str(spec["config_id"]),
                label=str(spec["label"]),
                evidence_view=str(spec["evidence_view"]),
                phrase_guard_pos_scope=str(spec["phrase_guard_pos_scope"]),
                baseline_config_id=str(spec["baseline_config_id"]),
                category=str(spec["category"]),
                scorer_id=scorer_id,
                min_active_score=min_active_score,
                min_margin=min_margin,
            )
        )

    config_lookup = {
        str(row.get("config_id") or "").strip(): row
        for row in config_rows
        if isinstance(row, Mapping) and str(row.get("config_id") or "").strip()
    }

    target_replace_case_ids = sorted(
        {
            str(case.get("case_id") or "").strip()
            for family in subset_dataset.get("families", ())
            if isinstance(family, Mapping)
            and str(family_roles.get(str(family.get("family_id") or "").strip()) or "") == "target"
            for case in family.get("cases", ())
            if isinstance(case, Mapping) and str(case.get("gold_decision") or "").strip() == "replace"
        }
    )
    negative_control_phrase_case_ids = sorted(
        {
            str(case.get("case_id") or "").strip()
            for family in subset_dataset.get("families", ())
            if isinstance(family, Mapping)
            and str(family_roles.get(str(family.get("family_id") or "").strip()) or "")
            == "negative_control"
            for case in family.get("cases", ())
            if isinstance(case, Mapping)
            and "phrase_control" in _normalize_string_list(case.get("slice_tags"))
        }
    )
    hard_baseline_row = config_lookup.get("hard_current_default")
    hard_baseline_harmful = set(
        _normalize_string_list(
            hard_baseline_row.get("harmful_replace_case_ids") if isinstance(hard_baseline_row, Mapping) else []
        )
    )
    hard_baseline_false_abstain = set(
        _normalize_string_list(
            hard_baseline_row.get("false_abstain_case_ids") if isinstance(hard_baseline_row, Mapping) else []
        )
    )
    focus_case_ids = list(
        dict.fromkeys(
            [
                *target_replace_case_ids,
                *negative_control_phrase_case_ids,
                *sorted(hard_baseline_harmful),
                *sorted(hard_baseline_false_abstain),
            ]
        )
    )

    for config_row in config_rows:
        baseline_id = str(config_row.get("baseline_config_id") or "").strip()
        baseline_row = config_lookup.get(baseline_id)
        baseline_harmful = set(
            _normalize_string_list(
                baseline_row.get("harmful_replace_case_ids") if isinstance(baseline_row, Mapping) else []
            )
        )
        baseline_false_abstain = set(
            _normalize_string_list(
                baseline_row.get("false_abstain_case_ids") if isinstance(baseline_row, Mapping) else []
            )
        )
        harmful_ids = set(_normalize_string_list(config_row.get("harmful_replace_case_ids")))
        false_abstain_ids = set(_normalize_string_list(config_row.get("false_abstain_case_ids")))
        config_row["fixed_false_abstain_case_ids"] = sorted(
            baseline_false_abstain - false_abstain_ids
        )
        config_row["introduced_false_abstain_case_ids"] = sorted(
            false_abstain_ids - baseline_false_abstain
        )
        config_row["fixed_harmful_replace_case_ids"] = sorted(baseline_harmful - harmful_ids)
        config_row["introduced_harmful_replace_case_ids"] = sorted(harmful_ids - baseline_harmful)
        config_row["fixed_target_case_ids"] = sorted(
            set(config_row["fixed_false_abstain_case_ids"]) & set(target_replace_case_ids)
        )
        config_row["introduced_target_false_abstain_case_ids"] = sorted(
            set(config_row["introduced_false_abstain_case_ids"]) & set(target_replace_case_ids)
        )
        row_lookup = {
            str(row.get("case_id") or "").strip(): row
            for row in config_row.get("row_results", ())
            if isinstance(row, Mapping) and str(row.get("case_id") or "").strip()
        }
        config_row["focus_cases"] = [
            _build_focus_case_row(row_lookup.get(case_id))
            for case_id in focus_case_ids
            if row_lookup.get(case_id) is not None
        ]
        config_row.pop("row_results", None)

    target_coverage_rows = [
        row for row in llm_coverage_rows if str(row.get("role") or "").strip() == "target"
    ]
    negative_control_coverage_rows = [
        row for row in llm_coverage_rows if str(row.get("role") or "").strip() == "negative_control"
    ]

    summary = {
        "queue_family_count": len(llm_coverage_rows),
        "target_family_count": len(target_coverage_rows),
        "negative_control_family_count": len(negative_control_coverage_rows),
        "target_families_with_llm_cues": sum(
            1 for row in target_coverage_rows if bool(row.get("llm_cue_ready"))
        ),
        "negative_controls_with_llm_cues": sum(
            1 for row in negative_control_coverage_rows if bool(row.get("llm_cue_ready"))
        ),
        "llm_runtime_publishable_count": int(llm_batch_summary.get("runtime_publishable_count") or 0),
        "hard_baseline_harmful_replace_count": int(
            ((hard_baseline_row or {}).get("summary") or {}).get("harmful_replace_count") or 0
        ),
        "hard_baseline_false_abstain_count": int(
            ((hard_baseline_row or {}).get("summary") or {}).get("false_abstain_count") or 0
        ),
    }

    report = {
        "schema_version": 1,
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "generated_at": generated_at,
        "status": "partial_missing_resources" if missing_resources else "ok",
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "scorer_id": str(scorer_id or "").strip() or DEFAULT_SCORER_ID,
        "min_active_score": float(min_active_score),
        "min_margin": float(min_margin),
        "resource_status": {
            "data_root": str(data_root),
            "reverse_pack": _build_pack_record(reverse_pack),
            "missing_resources": missing_resources,
        },
        "llm_batch": llm_batch_summary,
        "summary": summary,
        "focus_case_ids": focus_case_ids,
        "target_replace_case_ids": target_replace_case_ids,
        "negative_control_phrase_case_ids": negative_control_phrase_case_ids,
        "coverage_rows": llm_coverage_rows,
        "reverse_aux_coverage_rows": reverse_aux_coverage_rows,
        "configurations": config_rows,
    }
    report["recommendation"] = _build_recommendation(report)
    return report


def _build_recommendation(report: Mapping[str, object]) -> str:
    config_rows = {
        str(row.get("config_id") or "").strip(): row
        for row in report.get("configurations", ())
        if isinstance(row, Mapping) and str(row.get("config_id") or "").strip()
    }
    hard_baseline = config_rows.get("hard_current_default") or {}
    hard_control = config_rows.get("hard_reverse_aux_plus_all_evidence") or {}
    hard_llm = config_rows.get("hard_llm_cue_plus_all_evidence") or {}
    overlay_baseline = config_rows.get("active_only_current_default") or {}
    overlay_control = config_rows.get("active_only_reverse_aux_plus_all_evidence") or {}
    overlay_llm = config_rows.get("active_only_llm_cue_plus_all_evidence") or {}
    diagnostic_llm = config_rows.get("hard_llm_cue_plus_gloss") or {}

    hard_base_summary = hard_baseline.get("summary") if isinstance(hard_baseline.get("summary"), Mapping) else {}
    hard_control_summary = hard_control.get("summary") if isinstance(hard_control.get("summary"), Mapping) else {}
    hard_llm_summary = hard_llm.get("summary") if isinstance(hard_llm.get("summary"), Mapping) else {}
    overlay_base_summary = overlay_baseline.get("summary") if isinstance(overlay_baseline.get("summary"), Mapping) else {}
    overlay_control_summary = overlay_control.get("summary") if isinstance(overlay_control.get("summary"), Mapping) else {}
    overlay_llm_summary = overlay_llm.get("summary") if isinstance(overlay_llm.get("summary"), Mapping) else {}
    diagnostic_summary = diagnostic_llm.get("summary") if isinstance(diagnostic_llm.get("summary"), Mapping) else {}

    hard_llm_false = int(hard_llm_summary.get("false_abstain_count") or 0)
    hard_base_false = int(hard_base_summary.get("false_abstain_count") or 0)
    hard_control_false = int(hard_control_summary.get("false_abstain_count") or 0)
    hard_llm_harmful = int(hard_llm_summary.get("harmful_replace_count") or 0)
    hard_base_harmful = int(hard_base_summary.get("harmful_replace_count") or 0)
    overlay_llm_false = int(overlay_llm_summary.get("false_abstain_count") or 0)
    overlay_base_false = int(overlay_base_summary.get("false_abstain_count") or 0)
    overlay_control_false = int(overlay_control_summary.get("false_abstain_count") or 0)
    diagnostic_harmful = int(diagnostic_summary.get("harmful_replace_count") or 0)
    diagnostic_false = int(diagnostic_summary.get("false_abstain_count") or 0)

    hard_fixed = ", ".join(f"`{case_id}`" for case_id in _normalize_string_list(hard_llm.get("fixed_target_case_ids"))) or "none"
    hard_introduced = ", ".join(
        f"`{case_id}`" for case_id in _normalize_string_list(hard_llm.get("introduced_target_false_abstain_case_ids"))
    ) or "none"

    if (
        hard_llm_harmful <= hard_base_harmful
        and hard_llm_false < hard_base_false
        and overlay_llm_false < overlay_base_false
    ):
        return (
            "`Hard LLM cue plus all evidence` looks promotion-worthy on the frozen queue slice: "
            "it lowers false abstains without widening harmful replace on either the hard or "
            "active-sense overlay references."
        )

    if config_rows.get("hard_reverse_aux_plus_all_evidence"):
        return (
            "`Hard LLM cue plus all evidence` is not yet promotion-ready on the frozen queue slice. "
            f"On the hard reference it stays at `{hard_llm_harmful}` harmful and `{hard_llm_false}` false abstains "
            f"against the baseline `{hard_base_harmful}` / `{hard_base_false}`, fixing {hard_fixed} but introducing "
            f"{hard_introduced}. The active-sense overlay lane is also flat at `{overlay_llm_false}` false abstains "
            f"versus the overlay baseline `{overlay_base_false}` and still behind the reverse-aux control "
            f"(`{hard_control_false}` hard false abstains, `{overlay_control_false}` overlay false abstains). "
            "`Hard LLM cue plus gloss` shows some signal, but it widens harmful replace to "
            f"`{diagnostic_harmful}` while only reducing false abstains to `{diagnostic_false}`."
        )

    return (
        "`Hard LLM cue plus all evidence` does not yet clear the downstream acceptance bar. "
        "The safe additive lane remains flat against the current references, and the stronger "
        "diagnostic lane only improves recall by widening harmful replace."
    )


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

    report = build_prompt_downstream_report(
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
    markdown = render_prompt_downstream_markdown(report)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(markdown, encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
