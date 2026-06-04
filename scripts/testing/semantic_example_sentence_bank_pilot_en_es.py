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
for candidate in (str(CORE_ROOT),):
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


DEFAULT_QUEUE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing"
    / "semantic_prompt_bakeoff_queue_en_es.json"
)
DEFAULT_INVENTORY_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing"
    / "semantic_family_inventory_en_es_v10.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_example_sentence_bank_pilot_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_example_sentence_bank_pilot_en_es_latest.md"
)

SOURCE_ID = "example_sentence_bank"
SOURCE_FAMILY = "external_example_corpus"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the frozen en-es semantic prompt queue against installed packs and "
            "report whether example-backed cue rows are actually available before prompt spend."
        )
    )
    parser.add_argument(
        "--queue-json",
        type=Path,
        default=DEFAULT_QUEUE_JSON,
        help="Frozen prompt bakeoff queue JSON.",
    )
    parser.add_argument(
        "--inventory-json",
        type=Path,
        default=DEFAULT_INVENTORY_JSON,
        help="Frozen semantic family inventory JSON.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(resolve_data_root()),
        help="LexiShift data root (default: helper resolve_data_root()).",
    )
    parser.add_argument(
        "--translation-dict",
        type=Path,
        default=None,
        help="Optional explicit forward translation pack path for en-es.",
    )
    parser.add_argument(
        "--reverse-translation-dict",
        type=Path,
        default=None,
        help="Optional explicit reverse translation pack path for en-es.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=2,
        help="Maximum number of example or aux-text samples to retain per family.",
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
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


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


def _metadata(record: TranslationGlossRecord) -> Mapping[str, object]:
    return record.metadata if isinstance(record.metadata, Mapping) else {}


def _has_examples(record: TranslationGlossRecord) -> bool:
    metadata = _metadata(record)
    for key in ("sense_examples", "examples"):
        value = metadata.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and value:
            return True
        if isinstance(value, str) and value.strip():
            return True
    return False


def _extract_example_samples(
    records: Sequence[TranslationGlossRecord],
    *,
    sample_limit: int,
) -> list[str]:
    samples: list[str] = []
    for record in records:
        metadata = _metadata(record)
        for key in ("sense_examples", "examples"):
            value = metadata.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                for item in value:
                    text = _coerce_example_text(item)
                    if text and text not in samples:
                        samples.append(text)
                    if len(samples) >= sample_limit:
                        return samples
            else:
                text = _coerce_example_text(value)
                if text and text not in samples:
                    samples.append(text)
                if len(samples) >= sample_limit:
                    return samples
    return samples


def _coerce_example_text(value: object) -> str:
    if isinstance(value, Mapping):
        for key in ("text", "translation", "english", "roman"):
            text = str(value.get(key) or "").strip()
            if text:
                return text
        return ""
    return str(value or "").strip()


def _extract_aux_text_samples(
    records: Sequence[TranslationGlossRecord],
    *,
    sample_limit: int,
) -> list[str]:
    samples: list[str] = []
    for record in records:
        metadata = _metadata(record)
        for key in ("translation_sense_text", "translation_english_text", "translation_note_text"):
            text = str(metadata.get(key) or "").strip()
            if text and text not in samples:
                samples.append(text)
            if len(samples) >= sample_limit:
                return samples
    return samples


def build_example_sentence_bank_pilot_report(
    *,
    queue_payload: Mapping[str, object],
    inventory_payload: Mapping[str, object],
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    reverse_records_by_trigger: Mapping[str, Sequence[TranslationGlossRecord]],
    data_root: Path,
    forward_pack: TranslationPackRef | None,
    reverse_pack: TranslationPackRef | None,
    sample_limit: int = 2,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
    inventory_families = inventory_payload.get("families")
    if not isinstance(inventory_families, Sequence) or isinstance(inventory_families, (str, bytes)):
        raise ValueError("Inventory payload is missing a `families` array.")
    inventory_by_family_id = {
        str(item.get("family_id") or "").strip(): item
        for item in inventory_families
        if isinstance(item, Mapping) and str(item.get("family_id") or "").strip()
    }
    queue_families = queue_payload.get("families")
    if not isinstance(queue_families, Sequence) or isinstance(queue_families, (str, bytes)):
        raise ValueError("Queue payload is missing a `families` array.")

    missing_resources: list[str] = []
    if forward_pack is None or not forward_pack.path.exists():
        missing_resources.append("forward_translation_pack")
    if reverse_pack is None or not reverse_pack.path.exists():
        missing_resources.append("reverse_translation_pack")

    report: dict[str, object] = {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "missing_resources" if missing_resources else "ok",
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "inventory_id": str(inventory_payload.get("inventory_id") or "").strip(),
        "dataset_id": str(queue_payload.get("dataset_id") or "").strip(),
        "resource_status": {
            "data_root": str(data_root),
            "forward_pack": _build_pack_record(forward_pack),
            "reverse_pack": _build_pack_record(reverse_pack),
            "missing_resources": missing_resources,
        },
    }
    if missing_resources:
        report["families"] = []
        report["summary"] = {}
        report["recommendation"] = (
            "Resolve the installed en-es forward and reverse packs before trying to "
            "assess example-backed cue availability."
        )
        return report

    family_reports: list[dict[str, object]] = []
    target_family_count = 0
    negative_control_family_count = 0
    target_any_example_ready_count = 0
    target_trigger_matched_example_ready_count = 0
    target_aux_only_count = 0
    target_no_signal_count = 0
    target_reverse_aux_count = 0

    for queue_family in queue_families:
        if not isinstance(queue_family, Mapping):
            continue
        family_id = str(queue_family.get("family_id") or "").strip()
        if not family_id:
            continue
        inventory_family = inventory_by_family_id.get(family_id)
        if not isinstance(inventory_family, Mapping):
            raise ValueError(f"Queue family {family_id!r} is missing from the inventory payload.")
        role = str(queue_family.get("role") or "").strip() or "target"
        trigger = str(queue_family.get("trigger") or "").strip()
        active_target = str(inventory_family.get("active_target") or "").strip()
        normalized_trigger = normalize_shadow_text(trigger)
        normalized_active_target = normalize_shadow_text(active_target)

        all_forward_records = tuple(forward_records_by_target.get(active_target, ()))
        matched_forward_records = tuple(
            record
            for record in all_forward_records
            if normalize_shadow_text(record.translation) == normalized_trigger
        )
        forward_example_records = tuple(
            record for record in all_forward_records if _has_examples(record)
        )
        matched_forward_example_records = tuple(
            record for record in matched_forward_records if _has_examples(record)
        )

        all_reverse_records = tuple(reverse_records_by_trigger.get(trigger, ()))
        matched_reverse_active_records = tuple(
            record
            for record in all_reverse_records
            if normalize_shadow_text(record.translation) == normalized_active_target
        )
        matched_reverse_example_records = tuple(
            record for record in matched_reverse_active_records if _has_examples(record)
        )
        matched_reverse_aux_records = tuple(
            record
            for record in matched_reverse_active_records
            if _extract_aux_text_samples((record,), sample_limit=1)
        )

        any_example_ready = bool(forward_example_records or matched_reverse_example_records)
        trigger_matched_example_ready = bool(
            matched_forward_example_records or matched_reverse_example_records
        )
        reverse_aux_ready = bool(matched_reverse_aux_records)

        if role == "negative_control":
            family_status = "guardrail_only"
            recommended_action = "keep_as_negative_control"
            negative_control_family_count += 1
        elif any_example_ready:
            family_status = "example_ready"
            recommended_action = "candidate_for_example_bank_cue_review"
            target_family_count += 1
            target_any_example_ready_count += 1
            if trigger_matched_example_ready:
                target_trigger_matched_example_ready_count += 1
            if reverse_aux_ready:
                target_reverse_aux_count += 1
        elif reverse_aux_ready:
            family_status = "no_examples_but_aux_text_available"
            recommended_action = "candidate_for_reverse_aux_text_control"
            target_family_count += 1
            target_aux_only_count += 1
            target_reverse_aux_count += 1
        else:
            family_status = "no_example_like_signal"
            recommended_action = "source_ingestion_required"
            target_family_count += 1
            target_no_signal_count += 1

        family_reports.append(
            {
                "family_id": family_id,
                "trigger": trigger,
                "active_target": active_target,
                "role": role,
                "likely_bucket": str(queue_family.get("likely_bucket") or "").strip(),
                "primary_prompt_slot": str(queue_family.get("primary_prompt_slot") or "").strip(),
                "split_id": str(
                    (
                        (inventory_family.get("metadata") or {})
                        if isinstance(inventory_family, Mapping)
                        else {}
                    ).get("split_id")
                    or ""
                ).strip(),
                "forward_record_count": len(all_forward_records),
                "forward_matching_trigger_record_count": len(matched_forward_records),
                "forward_example_record_count": len(forward_example_records),
                "forward_matching_trigger_example_record_count": len(
                    matched_forward_example_records
                ),
                "reverse_record_count": len(all_reverse_records),
                "reverse_matching_active_record_count": len(matched_reverse_active_records),
                "reverse_matching_active_example_record_count": len(
                    matched_reverse_example_records
                ),
                "reverse_matching_active_aux_record_count": len(matched_reverse_aux_records),
                "any_example_ready": any_example_ready,
                "trigger_matched_example_ready": trigger_matched_example_ready,
                "reverse_aux_ready": reverse_aux_ready,
                "sample_forward_examples": _extract_example_samples(
                    matched_forward_example_records or forward_example_records,
                    sample_limit=sample_limit,
                ),
                "sample_reverse_aux_texts": _extract_aux_text_samples(
                    matched_reverse_aux_records,
                    sample_limit=sample_limit,
                ),
                "status": family_status,
                "recommended_action": recommended_action,
            }
        )

    example_source_ready = target_any_example_ready_count > 0
    summary = {
        "family_count": len(family_reports),
        "target_family_count": target_family_count,
        "negative_control_family_count": negative_control_family_count,
        "target_families_with_any_examples": target_any_example_ready_count,
        "target_families_with_trigger_matched_examples": target_trigger_matched_example_ready_count,
        "target_families_with_reverse_aux_text": target_reverse_aux_count,
        "target_families_aux_only": target_aux_only_count,
        "target_families_without_example_like_signal": target_no_signal_count,
        "example_source_ready_on_current_packs": example_source_ready,
    }
    report["families"] = family_reports
    report["summary"] = summary
    report["recommendation"] = (
        "Current installed packs can support a real example-backed cue review on the frozen queue."
        if example_source_ready
        else (
            "Current installed packs do not expose queued-family example rows for "
            f"`{SOURCE_ID}`; if we want that control before prompt spend, we need dedicated "
            "source ingestion. The only immediately available non-LLM cue-like signal on this "
            "slice is reverse-side auxiliary sense text."
        )
    )
    return report


def render_example_sentence_bank_pilot_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Example Sentence Bank Pilot",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Source: `{report.get('source_id', '')}` / `{report.get('source_family', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Inventory: `{report.get('inventory_id', '')}`",
        f"- Runtime dataset: `{report.get('dataset_id', '')}`",
    ]
    resource_status = report.get("resource_status")
    if isinstance(resource_status, Mapping):
        lines.extend(
            [
                "",
                "## Resources",
                f"- Data root: `{resource_status.get('data_root', '')}`",
            ]
        )
        for label in ("forward_pack", "reverse_pack"):
            pack = resource_status.get(label)
            if isinstance(pack, Mapping):
                lines.append(
                    f"- `{label}`: `{pack.get('path', '')}` (`exists={pack.get('exists', False)}`, provider=`{pack.get('provider', '')}`)"
                )
            else:
                lines.append(f"- `{label}`: missing")
    summary = report.get("summary")
    if isinstance(summary, Mapping):
        lines.extend(
            [
                "",
                "## Summary",
                f"- Target families: `{summary.get('target_family_count', 0)}`",
                f"- Negative-control families: `{summary.get('negative_control_family_count', 0)}`",
                f"- Target families with any example-bearing rows: `{summary.get('target_families_with_any_examples', 0)}`",
                (
                    "- Target families with trigger-matched example-bearing rows: "
                    f"`{summary.get('target_families_with_trigger_matched_examples', 0)}`"
                ),
                (
                    "- Target families with reverse-side auxiliary sense text but no examples: "
                    f"`{summary.get('target_families_aux_only', 0)}`"
                ),
                (
                    "- Target families with any reverse-side auxiliary sense text: "
                    f"`{summary.get('target_families_with_reverse_aux_text', 0)}`"
                ),
                (
                    "- Example source ready on current packs: "
                    f"`{bool(summary.get('example_source_ready_on_current_packs'))}`"
                ),
            ]
        )
    families = report.get("families")
    if isinstance(families, Sequence) and not isinstance(families, (str, bytes)) and families:
        lines.extend(
            [
                "",
                "## Family Coverage",
                "| Family | Role | Any Examples | Trigger-Matched Examples | Reverse Aux Text | Pilot Read |",
                "| --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        for family in families:
            if not isinstance(family, Mapping):
                continue
            family_label = (
                f"{family.get('trigger', '')} -> {family.get('active_target', '')}"
                if family.get("active_target")
                else str(family.get("trigger") or "")
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{family_label}`",
                        f"`{family.get('role', '')}`",
                        str(int(bool(family.get("any_example_ready")))),
                        str(int(bool(family.get("trigger_matched_example_ready")))),
                        str(int(bool(family.get("reverse_aux_ready")))),
                        f"`{family.get('status', '')}`",
                    ]
                )
                + " |"
            )
        lines.extend(["", "## Sample Aux Text"])
        for family in families:
            if not isinstance(family, Mapping):
                continue
            samples = family.get("sample_reverse_aux_texts")
            if (
                not isinstance(samples, Sequence)
                or isinstance(samples, (str, bytes))
                or not samples
            ):
                continue
            family_label = (
                f"{family.get('trigger', '')} -> {family.get('active_target', '')}"
                if family.get("active_target")
                else str(family.get("trigger") or "")
            )
            lines.append(f"- `{family_label}`:")
            for sample in samples:
                text = str(sample or "").strip()
                if text:
                    lines.append(f"  - `{text}`")
    recommendation = str(report.get("recommendation") or "").strip()
    if recommendation:
        lines.extend(["", "## Recommendation", f"- {recommendation}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    queue_payload = _load_json(args.queue_json)
    inventory_payload = _load_json(args.inventory_json)
    helper_paths = build_helper_paths(Path(args.data_root))
    forward_pack, reverse_pack = resolve_pair_translation_packs(
        helper_paths,
        pair="en-es",
        translation_dict_path=args.translation_dict,
        reverse_translation_dict_path=args.reverse_translation_dict,
    )

    forward_records_by_target: dict[str, Sequence[TranslationGlossRecord]] = {}
    reverse_records_by_trigger: dict[str, Sequence[TranslationGlossRecord]] = {}
    if forward_pack is not None and forward_pack.path.exists():
        inventory_families = inventory_payload.get("families")
        if isinstance(inventory_families, Sequence) and not isinstance(
            inventory_families, (str, bytes)
        ):
            active_targets = sorted(
                {
                    str(item.get("active_target") or "").strip()
                    for item in inventory_families
                    if isinstance(item, Mapping) and str(item.get("active_target") or "").strip()
                }
            )
            forward_records_by_target = load_translation_gloss_records_ordered(
                forward_pack.path,
                target_lang="en",
                headwords=active_targets,
            )
    if reverse_pack is not None and reverse_pack.path.exists():
        queue_families = queue_payload.get("families")
        if isinstance(queue_families, Sequence) and not isinstance(queue_families, (str, bytes)):
            triggers = sorted(
                {
                    str(item.get("trigger") or "").strip()
                    for item in queue_families
                    if isinstance(item, Mapping) and str(item.get("trigger") or "").strip()
                }
            )
            reverse_records_by_trigger = load_translation_gloss_records_ordered(
                reverse_pack.path,
                target_lang="es",
                headwords=triggers,
            )

    report = build_example_sentence_bank_pilot_report(
        queue_payload=queue_payload,
        inventory_payload=inventory_payload,
        forward_records_by_target=forward_records_by_target,
        reverse_records_by_trigger=reverse_records_by_trigger,
        data_root=Path(args.data_root),
        forward_pack=forward_pack,
        reverse_pack=reverse_pack,
        sample_limit=max(1, int(args.sample_limit)),
    )
    markdown = render_example_sentence_bank_pilot_markdown(report)

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
