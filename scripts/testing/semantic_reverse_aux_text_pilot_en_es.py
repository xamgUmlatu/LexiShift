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
from lexishift_core.rulegen.semantic_shadow_inventory_targets import normalize_shadow_text  # noqa: E402
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
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_reverse_aux_text_pilot_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_reverse_aux_text_pilot_en_es_latest.md"
)

DEFAULT_CONFIGS = (
    ("current_default", "Current default runtime row", "all_evidence_text"),
    ("reverse_aux_text_primary", "Reverse aux text only", "reverse_aux_text"),
    (
        "reverse_aux_plus_sense_label",
        "Reverse aux text plus sense label",
        "reverse_aux_plus_sense_label",
    ),
    (
        "reverse_aux_plus_all_evidence",
        "Reverse aux text plus all evidence",
        "reverse_aux_plus_all_evidence",
    ),
)

DEFAULT_SCORER_ID = "sentence_transformer_cosine"
DEFAULT_CONTEXT_VIEW = "masked_sentence"
DEFAULT_MIN_ACTIVE_SCORE = 0.0
DEFAULT_MIN_MARGIN = 0.0
DEFAULT_PHRASE_CONTROL_MODE = "noun_family_frame_guard"
DEFAULT_ACTIVE_RESCUE_MODE = "sense_label_near_tie_active_rescue"
_AUX_METADATA_KEYS = (
    "translation_sense_text",
    "translation_english_text",
    "translation_note_text",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a frozen-queue testing-only pilot that compares reverse auxiliary "
            "sense text against the current sentence-veto evidence row."
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
        help="Sentence-veto scorer to use for the pilot.",
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


def build_queue_subset_dataset(
    dataset_payload: Mapping[str, object],
    queue_payload: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, str]]:
    families = dataset_payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
        raise ValueError("Sentence-veto dataset is missing a `families` array.")
    queue_families = queue_payload.get("families")
    if not isinstance(queue_families, Sequence) or isinstance(queue_families, (str, bytes)):
        raise ValueError("Queue payload is missing a `families` array.")
    allowed_family_ids = {
        str(item.get("family_id") or "").strip()
        for item in queue_families
        if isinstance(item, Mapping) and str(item.get("family_id") or "").strip()
    }
    family_roles = {
        str(item.get("family_id") or "").strip(): str(item.get("role") or "").strip() or "target"
        for item in queue_families
        if isinstance(item, Mapping) and str(item.get("family_id") or "").strip()
    }
    subset_payload = deepcopy(dict(dataset_payload))
    subset_payload["families"] = [
        deepcopy(dict(family))
        for family in families
        if isinstance(family, Mapping)
        and str(family.get("family_id") or "").strip() in allowed_family_ids
    ]
    return subset_payload, family_roles


def extract_reverse_aux_text(
    *,
    trigger: str,
    target_lemma: str,
    reverse_records_by_trigger: Mapping[str, Sequence[TranslationGlossRecord]],
) -> str:
    normalized_trigger = str(trigger or "").strip()
    normalized_target = normalize_shadow_text(target_lemma)
    values: list[str] = []
    for record in reverse_records_by_trigger.get(normalized_trigger, ()):
        if normalize_shadow_text(record.translation) != normalized_target:
            continue
        metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
        for key in _AUX_METADATA_KEYS:
            text = str(metadata.get(key) or "").strip()
            if text and text not in values:
                values.append(text)
    return " | ".join(values)


def augment_queue_dataset_with_reverse_aux_views(
    dataset_payload: Mapping[str, object],
    *,
    family_roles: Mapping[str, str],
    reverse_records_by_trigger: Mapping[str, Sequence[TranslationGlossRecord]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    augmented_payload = deepcopy(dict(dataset_payload))
    family_rows: list[dict[str, object]] = []
    families = augmented_payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
        raise ValueError("Queue subset dataset is missing a `families` array.")
    for family in families:
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        role = str(family_roles.get(family_id) or "target")
        trigger = str(family.get("trigger") or "").strip()
        active = family.get("active")
        shadows = family.get("shadows")
        if not isinstance(active, dict) or not isinstance(shadows, list):
            continue

        active_aux_text = _apply_reverse_aux_views(
            active,
            trigger=trigger,
            reverse_records_by_trigger=reverse_records_by_trigger,
        )
        shadow_aux_count = 0
        shadow_aux_text_samples: list[str] = []
        for shadow in shadows:
            if not isinstance(shadow, dict):
                continue
            shadow_aux_text = _apply_reverse_aux_views(
                shadow,
                trigger=trigger,
                reverse_records_by_trigger=reverse_records_by_trigger,
            )
            if shadow_aux_text:
                shadow_aux_count += 1
                if shadow_aux_text not in shadow_aux_text_samples:
                    shadow_aux_text_samples.append(shadow_aux_text)

        family_rows.append(
            {
                "family_id": family_id,
                "role": role,
                "trigger": trigger,
                "active_target": str(active.get("target_lemma") or "").strip(),
                "active_aux_ready": bool(active_aux_text),
                "shadow_aux_count": int(shadow_aux_count),
                "shadow_count": len([item for item in shadows if isinstance(item, Mapping)]),
                "sample_active_aux_text": active_aux_text,
                "sample_shadow_aux_texts": shadow_aux_text_samples[:2],
            }
        )
    return augmented_payload, family_rows


def _apply_reverse_aux_views(
    sense_record: dict[str, object],
    *,
    trigger: str,
    reverse_records_by_trigger: Mapping[str, Sequence[TranslationGlossRecord]],
) -> str:
    target_lemma = str(sense_record.get("target_lemma") or "").strip()
    aux_text = extract_reverse_aux_text(
        trigger=trigger,
        target_lemma=target_lemma,
        reverse_records_by_trigger=reverse_records_by_trigger,
    )
    evidence_views = sense_record.get("evidence_views")
    if not isinstance(evidence_views, dict):
        evidence_views = {}
        sense_record["evidence_views"] = evidence_views
    if not aux_text:
        return ""
    evidence_views["reverse_aux_text"] = aux_text
    sense_label = str(evidence_views.get("sense_label") or "").strip()
    all_evidence_text = str(evidence_views.get("all_evidence_text") or "").strip()
    evidence_views["reverse_aux_plus_sense_label"] = _join_unique_text_parts(
        (sense_label, aux_text)
    )
    evidence_views["reverse_aux_plus_all_evidence"] = _join_unique_text_parts(
        (all_evidence_text, aux_text)
    )
    return aux_text


def _join_unique_text_parts(parts: Sequence[str]) -> str:
    deduped: list[str] = []
    for part in parts:
        text = str(part or "").strip()
        if text and text not in deduped:
            deduped.append(text)
    return " | ".join(deduped)


def select_reverse_aux_candidate_config(
    config_rows: Sequence[Mapping[str, object]],
) -> dict[str, object] | None:
    candidates = [
        row
        for row in config_rows
        if isinstance(row, Mapping) and str(row.get("config_id") or "").strip() != "current_default"
    ]
    if not candidates:
        return None
    return dict(
        min(
            candidates,
            key=lambda row: (
                int(
                    (
                        (row.get("summary") or {})
                        if isinstance(row.get("summary"), Mapping)
                        else {}
                    ).get("harmful_replace_count")
                    or 0
                ),
                int(
                    (
                        (row.get("summary") or {})
                        if isinstance(row.get("summary"), Mapping)
                        else {}
                    ).get("false_abstain_count")
                    or 0
                ),
                -float(
                    (
                        (row.get("summary") or {})
                        if isinstance(row.get("summary"), Mapping)
                        else {}
                    ).get("decision_accuracy")
                    or 0.0
                ),
                -float(
                    (
                        (row.get("summary") or {})
                        if isinstance(row.get("summary"), Mapping)
                        else {}
                    ).get("replace_recall")
                    or 0.0
                ),
            ),
        )
    )


def build_reverse_aux_text_pilot_report(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    reverse_records_by_trigger: Mapping[str, Sequence[TranslationGlossRecord]],
    data_root: Path,
    reverse_pack: TranslationPackRef | None,
    scorer_id: str = DEFAULT_SCORER_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
    subset_dataset, family_roles = build_queue_subset_dataset(dataset_payload, queue_payload)
    augmented_dataset, coverage_rows = augment_queue_dataset_with_reverse_aux_views(
        subset_dataset,
        family_roles=family_roles,
        reverse_records_by_trigger=reverse_records_by_trigger,
    )

    missing_resources: list[str] = []
    if reverse_pack is None or not reverse_pack.path.exists():
        missing_resources.append("reverse_translation_pack")

    report: dict[str, object] = {
        "schema_version": 1,
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "generated_at": generated_at,
        "status": "missing_resources" if missing_resources else "ok",
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "resource_status": {
            "data_root": str(data_root),
            "reverse_pack": _build_pack_record(reverse_pack),
            "missing_resources": missing_resources,
        },
        "coverage_rows": coverage_rows,
    }
    if missing_resources:
        report["summary"] = {}
        report["configurations"] = []
        report["recommendation"] = (
            "Resolve the installed en-es reverse pack before attempting the reverse-aux-text control."
        )
        return report

    with tempfile.NamedTemporaryFile(
        "w+", suffix=".json", delete=False, encoding="utf-8"
    ) as handle:
        json.dump(augmented_dataset, handle, ensure_ascii=False, indent=2)
        handle.flush()
        augmented_dataset_path = Path(handle.name)
    try:
        config_rows: list[dict[str, object]] = []
        for config_id, label, evidence_view in DEFAULT_CONFIGS:
            config_report = build_sentence_veto_report(
                dataset_path=augmented_dataset_path,
                scorer_id=str(scorer_id or "").strip() or DEFAULT_SCORER_ID,
                context_view=DEFAULT_CONTEXT_VIEW,
                evidence_view=evidence_view,
                min_active_score=DEFAULT_MIN_ACTIVE_SCORE,
                min_margin=DEFAULT_MIN_MARGIN,
                phrase_control_mode=DEFAULT_PHRASE_CONTROL_MODE,
                active_rescue_mode=DEFAULT_ACTIVE_RESCUE_MODE,
            )
            summary = dict(config_report.get("summary") or {})
            config_rows.append(
                {
                    "config_id": config_id,
                    "label": label,
                    "evidence_view": evidence_view,
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
            )
    finally:
        augmented_dataset_path.unlink(missing_ok=True)

    baseline_row = next(
        (
            row
            for row in config_rows
            if str(row.get("config_id") or "").strip() == "current_default"
        ),
        None,
    )
    if baseline_row is None:
        raise ValueError("Reverse aux pilot requires the `current_default` configuration row.")

    baseline_harmful = set(_normalize_string_list(baseline_row.get("harmful_replace_case_ids")))
    baseline_false_abstain = set(_normalize_string_list(baseline_row.get("false_abstain_case_ids")))
    focus_case_ids = list(
        dict.fromkeys(
            [
                *baseline_harmful,
                *baseline_false_abstain,
                *(
                    str(row.get("case_id") or "")
                    for family in subset_dataset.get("families", ())
                    if isinstance(family, Mapping)
                    and str(family_roles.get(str(family.get("family_id") or "").strip()) or "")
                    == "negative_control"
                    for row in family.get("cases", ())
                    if isinstance(row, Mapping)
                    and "phrase_control" in _normalize_string_list(row.get("slice_tags"))
                ),
            ]
        )
    )

    for config_row in config_rows:
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

    selected_candidate = select_reverse_aux_candidate_config(config_rows)
    selected_summary = (
        selected_candidate.get("summary") if isinstance(selected_candidate, Mapping) else {}
    )
    baseline_summary = baseline_row.get("summary") if isinstance(baseline_row, Mapping) else {}

    target_coverage_rows = [
        row for row in coverage_rows if str(row.get("role") or "").strip() == "target"
    ]
    summary = {
        "queue_family_count": len(coverage_rows),
        "target_family_count": len(target_coverage_rows),
        "target_families_with_active_aux_text": sum(
            1 for row in target_coverage_rows if bool(row.get("active_aux_ready"))
        ),
        "target_families_with_any_shadow_aux_text": sum(
            1 for row in target_coverage_rows if int(row.get("shadow_aux_count") or 0) > 0
        ),
        "baseline_harmful_replace_count": int(baseline_summary.get("harmful_replace_count") or 0),
        "baseline_false_abstain_count": int(baseline_summary.get("false_abstain_count") or 0),
        "selected_candidate_config_id": str(selected_candidate.get("config_id") or "").strip()
        if isinstance(selected_candidate, Mapping)
        else "",
        "selected_candidate_harmful_replace_count": int(
            selected_summary.get("harmful_replace_count") or 0
        )
        if isinstance(selected_summary, Mapping)
        else 0,
        "selected_candidate_false_abstain_count": int(
            selected_summary.get("false_abstain_count") or 0
        )
        if isinstance(selected_summary, Mapping)
        else 0,
    }
    report["summary"] = summary
    report["focus_case_ids"] = focus_case_ids
    report["configurations"] = config_rows
    report["selected_candidate_config_id"] = (
        str(selected_candidate.get("config_id") or "").strip()
        if isinstance(selected_candidate, Mapping)
        else ""
    )
    report["selected_candidate_label"] = (
        str(selected_candidate.get("label") or "").strip()
        if isinstance(selected_candidate, Mapping)
        else ""
    )
    report["recommendation"] = _build_recommendation(
        baseline_row=baseline_row,
        selected_candidate=selected_candidate,
    )
    return report


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


def _build_recommendation(
    *,
    baseline_row: Mapping[str, object],
    selected_candidate: Mapping[str, object] | None,
) -> str:
    if not isinstance(selected_candidate, Mapping):
        return "No reverse-aux-text candidate row was available to compare against the baseline."
    baseline_summary = (
        baseline_row.get("summary") if isinstance(baseline_row.get("summary"), Mapping) else {}
    )
    candidate_summary = (
        selected_candidate.get("summary")
        if isinstance(selected_candidate.get("summary"), Mapping)
        else {}
    )
    baseline_harmful = int(baseline_summary.get("harmful_replace_count") or 0)
    candidate_harmful = int(candidate_summary.get("harmful_replace_count") or 0)
    baseline_false_abstain = int(baseline_summary.get("false_abstain_count") or 0)
    candidate_false_abstain = int(candidate_summary.get("false_abstain_count") or 0)
    if candidate_harmful <= baseline_harmful and candidate_false_abstain < baseline_false_abstain:
        return (
            f"`{selected_candidate.get('label', selected_candidate.get('config_id', ''))}` "
            "is a credible last non-LLM control for the frozen prompt queue: it improves the "
            "queue-slice point read without widening the current harmful-replace count."
        )
    return (
        f"`{selected_candidate.get('label', selected_candidate.get('config_id', ''))}` does not "
        "clear the current safety bar cleanly enough to act as the last non-LLM control before "
        "prompt spend."
    )


def render_reverse_aux_text_pilot_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    configs = (
        report.get("configurations")
        if isinstance(report.get("configurations"), Sequence)
        and not isinstance(report.get("configurations"), (str, bytes))
        else []
    )
    coverage_rows = (
        report.get("coverage_rows")
        if isinstance(report.get("coverage_rows"), Sequence)
        and not isinstance(report.get("coverage_rows"), (str, bytes))
        else []
    )
    lines = [
        "# en-es Reverse Aux Text Pilot",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Runtime dataset: `{report.get('dataset_id', '')}`",
        f"- Selected candidate: `{report.get('selected_candidate_label', '') or 'n/a'}`",
        "",
        "## Coverage",
        "",
        f"- Target families: `{summary.get('target_family_count', 0)}`",
        f"- Target families with active reverse aux text: `{summary.get('target_families_with_active_aux_text', 0)}`",
        f"- Target families with any shadow reverse aux text: `{summary.get('target_families_with_any_shadow_aux_text', 0)}`",
        "",
        "| Family | Role | Active Aux | Shadow Aux Count | Active Aux Sample |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in coverage_rows:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('trigger', '')} -> {row.get('active_target', '')}`",
                    f"`{row.get('role', '')}`",
                    str(int(bool(row.get("active_aux_ready")))),
                    str(int(row.get("shadow_aux_count") or 0)),
                    f"`{str(row.get('sample_active_aux_text') or '').strip() or 'n/a'}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Configuration Summary",
            "",
            "| Config | Evidence View | Harmful | False Abstain | Replace Recall | Decision Acc. | Fixed False Abstains | Introduced False Abstains |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in configs:
        if not isinstance(row, Mapping):
            continue
        summary_row = row.get("summary") if isinstance(row.get("summary"), Mapping) else {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('label', row.get('config_id', ''))}`",
                    f"`{row.get('evidence_view', '')}`",
                    str(int(summary_row.get("harmful_replace_count") or 0)),
                    str(int(summary_row.get("false_abstain_count") or 0)),
                    _render_rate(summary_row.get("replace_recall")),
                    _render_rate(summary_row.get("decision_accuracy")),
                    ", ".join(
                        f"`{case_id}`"
                        for case_id in _normalize_string_list(
                            row.get("fixed_false_abstain_case_ids")
                        )
                    )
                    or "none",
                    ", ".join(
                        f"`{case_id}`"
                        for case_id in _normalize_string_list(
                            row.get("introduced_false_abstain_case_ids")
                        )
                    )
                    or "none",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Focus Case Outcomes",
            "",
            "| Config | Case | Gold | Predicted | Margin | Phrase | Rescue |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in configs:
        if not isinstance(row, Mapping):
            continue
        for case in row.get("focus_cases", ()):
            if not isinstance(case, Mapping):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row.get("config_id") or ""),
                        str(case.get("case_id") or ""),
                        str(case.get("gold_decision") or ""),
                        str(case.get("predicted_decision") or ""),
                        _render_metric(case.get("margin")),
                        "yes" if bool(case.get("phrase_preemption_hit")) else "no",
                        "yes" if bool(case.get("active_rescue_applied")) else "no",
                    ]
                )
                + " |"
            )
    recommendation = str(report.get("recommendation") or "").strip()
    if recommendation:
        lines.extend(["", "## Recommendation", "", f"- {recommendation}"])
    return "\n".join(lines) + "\n"


def _normalize_string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _render_rate(value: object) -> str:
    try:
        return f"{float(value) * 100.0:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _render_metric(value: object) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "n/a"


def main() -> int:
    args = _parse_args()
    queue_payload = _load_json(args.queue_json)
    dataset_payload = load_sentence_veto_dataset(args.dataset)
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

    report = build_reverse_aux_text_pilot_report(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        reverse_records_by_trigger=reverse_records_by_trigger,
        data_root=Path(args.data_root),
        reverse_pack=reverse_pack,
        scorer_id=str(args.scorer_id or "").strip() or DEFAULT_SCORER_ID,
    )
    markdown = render_reverse_aux_text_pilot_markdown(report)

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
