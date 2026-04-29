#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import gzip
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence
import unicodedata

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
DEFAULT_DRAFT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_non_v10_wave_drafts"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from semantic_example_frame_source_adapter_support import content_tokens, utc_now, write_json  # noqa: E402


DEFAULT_DATASET_JSON = (
    DEFAULT_DRAFT_ROOT
    / "en_es_source_non_v10_wave6_anypos_unsupported_upper_bound_selected_v1_dataset.json"
)
DEFAULT_DATASET_OUT = (
    DEFAULT_DRAFT_ROOT / "en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_wiktextract_translation_support_wave6_anypos_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_wiktextract_translation_support_wave6_anypos_latest.md"
)
SOURCE_ID = "wiktextract_en_es_translation_table"
SPANISH_CODES = frozenset({"es", "spa"})
POS_MAP = {
    "adj": "adjective",
    "adjective": "adjective",
    "adv": "adverb",
    "adverb": "adverb",
    "noun": "noun",
    "n": "noun",
    "verb": "verb",
    "v": "verb",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Overlay local raw Wiktextract en-es translation-table support onto a non-v10 "
            "semantic source dataset. This converts forward-only upper-bound rows into "
            "source-supported rows when the raw entry explicitly lists the selected Spanish target."
        )
    )
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--raw-wiktextract-jsonl-gz", type=Path, default=None)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_wiktextract_translation_support_bundle(
    *,
    dataset_payload: Mapping[str, object],
    records_by_trigger: Mapping[str, Sequence[Mapping[str, object]]],
    raw_wiktextract_path: Path,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = utc_now()
    supported_dataset = copy.deepcopy(dict(dataset_payload))
    family_rows: list[dict[str, object]] = []
    for family in supported_dataset.get("families", ()):
        if not isinstance(family, dict):
            continue
        family_rows.append(_apply_family_support(family, records_by_trigger=records_by_trigger))
    _mark_dataset_overlay(supported_dataset, generated_at=generated_at)
    report = _build_report(
        dataset_payload=dataset_payload,
        supported_dataset=supported_dataset,
        family_rows=family_rows,
        raw_wiktextract_path=raw_wiktextract_path,
        generated_at=generated_at,
    )
    return {"report": report, "supported_dataset": supported_dataset}


def load_translation_records_by_trigger(
    raw_wiktextract_path: Path, *, triggers: Sequence[str]
) -> dict[str, list[Mapping[str, object]]]:
    trigger_set = {_norm(trigger) for trigger in triggers if _norm(trigger)}
    records_by_trigger = {trigger: [] for trigger in trigger_set}
    if not raw_wiktextract_path.exists() or not trigger_set:
        return records_by_trigger
    with gzip.open(raw_wiktextract_path, "rt", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, Mapping):
                continue
            if str(record.get("lang_code") or "").strip().lower() != "en":
                continue
            trigger = _norm(record.get("word"))
            if trigger in trigger_set:
                records_by_trigger.setdefault(trigger, []).append(record)
    return records_by_trigger


def render_wiktextract_translation_support_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Wiktextract Translation Support Overlay",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_id', '')}`",
        f"- Selected senses: `{summary.get('selected_sense_count', 0)}`",
        f"- Already supported senses: `{summary.get('already_supported_sense_count', 0)}`",
        f"- Wiktextract-supported senses: `{summary.get('wiktextract_supported_sense_count', 0)}`",
        f"- Newly supported senses: `{summary.get('newly_supported_sense_count', 0)}`",
        f"- Fully supported families after overlay: `{summary.get('fully_supported_family_count', 0)}` / `{summary.get('family_count', 0)}`",
        f"- Unsupported senses after overlay: `{summary.get('unsupported_sense_count', 0)}`",
        "",
        "## Family Support",
        "",
        "| Trigger | Support | Wiktextract hits | Unsupported |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in report.get("family_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"| `{row.get('trigger', '')}` | "
            f"`{row.get('supported_sense_count', 0)} / {row.get('selected_sense_count', 0)}` | "
            f"`{row.get('wiktextract_supported_sense_count', 0)}` | "
            f"`{row.get('unsupported_sense_count', 0)}` |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    return "\n".join(lines) + "\n"


def _apply_family_support(
    family: dict[str, object],
    *,
    records_by_trigger: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, object]:
    trigger = str(family.get("trigger") or "").strip()
    records = records_by_trigger.get(_norm(trigger), ())
    rows: list[dict[str, object]] = []
    for sense in _selected_sense_dicts(family):
        matches = _translation_support_matches(trigger=trigger, sense=sense, records=records)
        if matches:
            _mark_sense_supported(sense, matches=matches)
        rows.append(_sense_row(sense, matches=matches))
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": trigger,
        "selected_sense_count": len(rows),
        "supported_sense_count": sum(1 for row in rows if row["has_translation_support"]),
        "wiktextract_supported_sense_count": sum(
            1 for row in rows if row["wiktextract_translation_support"]
        ),
        "unsupported_sense_count": sum(1 for row in rows if not row["has_translation_support"]),
        "senses": rows,
    }


def _translation_support_matches(
    *,
    trigger: str,
    sense: Mapping[str, object],
    records: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    target = _norm(sense.get("target_lemma"))
    canonical_pos = _canonical_pos(sense.get("canonical_pos"))
    sense_tokens = content_tokens(_sense_text(sense), trigger=trigger)
    matches: list[dict[str, object]] = []
    for record in records:
        record_pos = _canonical_pos(record.get("pos"))
        if canonical_pos and record_pos and canonical_pos != record_pos:
            continue
        for translation in record.get("translations") or ():
            if not isinstance(translation, Mapping) or not _is_spanish_translation(translation):
                continue
            if _norm(translation.get("word")) != target:
                continue
            translation_sense = str(translation.get("sense") or "").strip()
            overlap = sorted(sense_tokens & content_tokens(translation_sense, trigger=trigger))
            matches.append(
                {
                    "record_word": str(record.get("word") or "").strip(),
                    "record_pos": str(record.get("pos") or "").strip(),
                    "translation_word": str(translation.get("word") or "").strip(),
                    "translation_sense": translation_sense,
                    "translation_tags": list(translation.get("tags") or ()),
                    "sense_overlap": overlap,
                }
            )
    return matches


def _mark_sense_supported(
    sense: dict[str, object], *, matches: Sequence[Mapping[str, object]]
) -> None:
    metadata = sense.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        sense["metadata"] = metadata
    metadata["wiktextract_translation_support"] = True
    support_sources = list(metadata.get("support_sources") or ())
    if SOURCE_ID not in support_sources:
        support_sources.append(SOURCE_ID)
    metadata["support_sources"] = support_sources
    metadata["wiktextract_translation_support_matches"] = list(matches)


def _mark_dataset_overlay(dataset: dict[str, object], *, generated_at: str) -> None:
    overlays = list(dataset.get("source_support_overlays") or ())
    overlays.append(
        {
            "source_id": SOURCE_ID,
            "generated_at": generated_at,
            "support_kind": "raw_wiktextract_translation_table",
        }
    )
    dataset["source_support_overlays"] = overlays
    dataset["translation_support_mode"] = "forward_only_plus_wiktextract_translation_support"


def _build_report(
    *,
    dataset_payload: Mapping[str, object],
    supported_dataset: Mapping[str, object],
    family_rows: Sequence[Mapping[str, object]],
    raw_wiktextract_path: Path,
    generated_at: str,
) -> dict[str, object]:
    senses = [
        sense
        for family in family_rows
        for sense in family.get("senses", ())
        if isinstance(sense, Mapping)
    ]
    selected = len(senses)
    wiktextract_supported = sum(
        1 for sense in senses if sense.get("wiktextract_translation_support")
    )
    already_supported = sum(1 for sense in senses if sense.get("preexisting_translation_support"))
    unsupported = sum(1 for sense in senses if not sense.get("has_translation_support"))
    return {
        "schema_version": 1,
        "status": "ok" if selected and unsupported == 0 else "review",
        "decision": "wiktextract_support_complete"
        if selected and unsupported == 0
        else "support_gaps_remain",
        "generated_at": generated_at,
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "supported_dataset_id": str(supported_dataset.get("dataset_id") or "").strip(),
        "source_id": SOURCE_ID,
        "resource_status": {
            "raw_wiktextract_path": str(raw_wiktextract_path),
            "raw_wiktextract_exists": raw_wiktextract_path.exists(),
        },
        "summary": {
            "family_count": len(family_rows),
            "fully_supported_family_count": sum(
                1 for row in family_rows if int(row.get("unsupported_sense_count") or 0) == 0
            ),
            "selected_sense_count": selected,
            "already_supported_sense_count": already_supported,
            "wiktextract_supported_sense_count": wiktextract_supported,
            "newly_supported_sense_count": sum(
                1
                for sense in senses
                if sense.get("wiktextract_translation_support")
                and not sense.get("preexisting_translation_support")
            ),
            "unsupported_sense_count": unsupported,
        },
        "family_rows": list(family_rows),
        "limitations": [
            "translation_table_support_requires_admission_and_heldout_validation_before_promotion",
            "raw_wiktextract_sense_labels_are_source_evidence_not reviewed gold",
            "phrase_containment_rows_are_out_of_scope_for_this_overlay",
        ],
    }


def _selected_sense_dicts(family: Mapping[str, object]) -> list[dict[str, object]]:
    rows = []
    active = family.get("active")
    if isinstance(active, dict):
        rows.append(active)
    for shadow in family.get("shadows", ()):
        if isinstance(shadow, dict):
            rows.append(shadow)
    return rows


def _sense_row(
    sense: Mapping[str, object], *, matches: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    metadata = _as_mapping(sense.get("metadata"))
    preexisting = bool(metadata.get("reverse_support")) or bool(metadata.get("freedict_support"))
    wiktextract_support = bool(metadata.get("wiktextract_translation_support"))
    return {
        "sense_id": str(sense.get("sense_id") or "").strip(),
        "target_lemma": str(sense.get("target_lemma") or "").strip(),
        "canonical_pos": str(sense.get("canonical_pos") or "").strip(),
        "preexisting_translation_support": preexisting,
        "wiktextract_translation_support": wiktextract_support,
        "has_translation_support": preexisting or wiktextract_support,
        "matches": list(matches),
    }


def _sense_text(sense: Mapping[str, object]) -> str:
    metadata = _as_mapping(sense.get("metadata"))
    evidence = _as_mapping(sense.get("evidence_views"))
    return " | ".join(
        str(item or "").strip()
        for item in (
            metadata.get("translation_sense_text"),
            evidence.get("all_evidence_text"),
            evidence.get("gloss_text"),
        )
        if str(item or "").strip()
    )


def _is_spanish_translation(translation: Mapping[str, object]) -> bool:
    code = str(translation.get("code") or translation.get("lang_code") or "").strip().lower()
    lang = str(translation.get("lang") or "").strip().lower()
    return code in SPANISH_CODES or lang == "spanish"


def _canonical_pos(value: object) -> str:
    return POS_MAP.get(str(value or "").strip().lower(), str(value or "").strip().lower())


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def main() -> int:
    args = _parse_args()
    dataset_payload = _load_json(args.dataset_json)
    raw_path = (
        args.raw_wiktextract_jsonl_gz
        if args.raw_wiktextract_jsonl_gz is not None
        else args.data_root / "language_packs" / "raw-wiktextract-data.jsonl.gz"
    )
    triggers = [
        str(family.get("trigger") or "").strip()
        for family in dataset_payload.get("families", ())
        if isinstance(family, Mapping)
    ]
    records_by_trigger = load_translation_records_by_trigger(raw_path, triggers=triggers)
    bundle = build_wiktextract_translation_support_bundle(
        dataset_payload=dataset_payload,
        records_by_trigger=records_by_trigger,
        raw_wiktextract_path=raw_path,
    )
    report = {
        **bundle["report"],
        "artifacts": {"dataset_json": str(args.dataset_json), "dataset_out": str(args.dataset_out)},
    }
    write_json(args.dataset_out, bundle["supported_dataset"])
    write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_wiktextract_translation_support_markdown(report))
    print(f"Wrote supported dataset to {args.dataset_out}")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
