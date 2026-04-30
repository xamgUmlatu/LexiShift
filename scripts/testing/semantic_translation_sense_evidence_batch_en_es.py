#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXPERIMENT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
DEFAULT_DRAFT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_non_v10_wave_drafts"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402
from semantic_example_frame_source_adapter_support import (  # noqa: E402
    bucket_for_relation as _bucket_for_relation,
    sense_hint as _sense_hint,
    sense_id as _sense_id,
    slug as _slug,
    utc_now as _utc_now,
    write_json as _write_json,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_RUN_ID = "translation-sense-non-v10-wave6-wiktextract-supported-v1-latest"
DEFAULT_DATASET_JSON = (
    DEFAULT_DRAFT_ROOT / "en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json"
)
DEFAULT_NORMALIZED_OUT = EXPERIMENT_ROOT / (f"en-es-{DEFAULT_RUN_ID}_normalized_evidence.json")
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_translation_sense_evidence_non_v10_wave6_wiktextract_supported_latest.json"
)
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_translation_sense_evidence_non_v10_wave6_wiktextract_supported_latest.md"
)
SOURCE_TYPE = "external"
SOURCE_ID = "translation_sense_evidence"
SOURCE_FAMILY = "external_structured_dictionary_dump"
PROMPT_VERSION = "translation-sense-evidence-v1"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build normalized en-es semantic evidence rows from already-supported "
            "translation-table English sense text. This is a no-spend source adapter: "
            "it does not change runtime policy and does not generate examples."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--normalized-batch-out", type=Path, default=DEFAULT_NORMALIZED_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_translation_sense_evidence_bundle(
    *,
    dataset_payload: Mapping[str, object],
    run_id: str = DEFAULT_RUN_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    intake_batch = _build_intake_batch(
        dataset_payload=dataset_payload,
        run_id=run_id,
        generated_at=generated_at,
    )
    normalized_batch = (
        normalize_llm_intake_batch(intake_batch) if intake_batch.get("items") else None
    )
    family_rows = list(
        intake_batch.get("provenance", {}).get("family_rows", ())
        if isinstance(intake_batch.get("provenance"), Mapping)
        else ()
    )
    report = _build_report(
        dataset_payload=dataset_payload,
        family_rows=family_rows,
        normalized_batch=normalized_batch,
        generated_at=generated_at,
        run_id=run_id,
    )
    return {
        "intake_batch": intake_batch,
        "normalized_batch": normalized_batch,
        "report": report,
    }


def render_translation_sense_evidence_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Translation-Sense Evidence Batch",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_id', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Source: `{report.get('source_id', '')}` / `{report.get('source_family', '')}`",
        f"- Selected senses: `{summary.get('selected_sense_count', 0)}`",
        f"- Source-supported senses: `{summary.get('source_supported_sense_count', 0)}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Active / shadow rows: `{summary.get('active_row_count', 0)}` / `{summary.get('shadow_row_count', 0)}`",
        "",
        "## Family Rows",
        "",
        "| Family | Active | Shadow | Skipped | Rows |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in report.get("family_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('family_id', '')}`",
                    str(row.get("active_row_count", 0)),
                    str(row.get("shadow_row_count", 0)),
                    str(row.get("skipped_sense_count", 0)),
                    str(row.get("row_count", 0)),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    return "\n".join(lines) + "\n"


def _build_intake_batch(
    *,
    dataset_payload: Mapping[str, object],
    run_id: str,
    generated_at: str,
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    family_rows: list[dict[str, object]] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_items, sense_rows = _family_items(family)
        items.extend(family_items)
        family_rows.append(_family_summary_row(family, family_items, sense_rows))
    return {
        "schema_version": 1,
        "batch_id": f"en-es:translation-sense-evidence:{run_id}",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "source_type": SOURCE_TYPE,
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "roles": ["cue_generation", "discrimination"],
        "generated_at": generated_at,
        "ingested_at": generated_at,
        "review_state": "unreviewed",
        "model_id": "not_applicable",
        "prompt_version": PROMPT_VERSION,
        "provenance": {
            "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
            "source_note": (
                "English sense text from supported translation-table rows; "
                "Spanish target lemmas are excluded from evidence_text."
            ),
            "family_rows": family_rows,
        },
        "items": items,
    }


def _family_items(
    family: Mapping[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
    senses = [
        ("anchor_cue", active),
        *[
            ("shadow_candidate", shadow)
            for shadow in family.get("shadows", ())
            if isinstance(shadow, Mapping)
        ],
    ]
    items: list[dict[str, object]] = []
    sense_rows: list[dict[str, object]] = []
    for relation_type, sense in senses:
        evidence_text = _source_evidence_text(family, sense)
        supported = bool(_support_matches(sense)) and bool(evidence_text)
        sense_rows.append(_sense_row(sense, relation_type=relation_type, supported=supported))
        if not supported:
            continue
        items.append(
            _item(
                family=family,
                active_sense=active,
                candidate_sense=sense,
                relation_type=relation_type,
                evidence_text=evidence_text,
            )
        )
    return items, sense_rows


def _item(
    *,
    family: Mapping[str, object],
    active_sense: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    relation_type: str,
    evidence_text: str,
) -> dict[str, object]:
    family_id = str(family.get("family_id") or "").strip()
    candidate_id = _sense_id(candidate_sense)
    example_bucket = _bucket_for_relation(relation_type)
    metadata = _as_mapping(candidate_sense.get("metadata"))
    return {
        "row_id": (
            f"{_slug(family_id)}:{example_bucket}-{_slug(candidate_id)}-translation-sense-1"
        ),
        "relation_type": relation_type,
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(active_sense.get("target_lemma") or "").strip(),
        "candidate_target": str(candidate_sense.get("target_lemma") or "").strip(),
        "active_sense_hint": _sense_hint(active_sense, note="fixed_shadow_active"),
        "candidate_sense_hint": _sense_hint(
            candidate_sense,
            note="translation_sense_linked_candidate",
            metadata={
                "source_view": "translation_sense_text",
                "support_sources": _text_list(metadata.get("support_sources")),
            },
        ),
        "candidate_pos": str(candidate_sense.get("canonical_pos") or "").strip(),
        "evidence_text": evidence_text,
        "example_count": 1,
        "review_state": "unreviewed",
        "promotion_state": "proposed",
        "runtime_publishable": False,
        "roles": ["cue_generation", "discrimination"]
        if relation_type == "anchor_cue"
        else ["discrimination"],
        "metadata": {
            "family_id": family_id,
            "queue_role": "target",
            "active_sense_id": _sense_id(active_sense),
            "candidate_sense_id": candidate_id,
            "example_bucket": example_bucket,
            "source_view": "translation_sense_text",
            "translation_sense_text": str(metadata.get("translation_sense_text") or "").strip(),
            "translation_support_sources": _text_list(metadata.get("support_sources")),
            "wiktextract_translation_support": bool(
                metadata.get("wiktextract_translation_support")
            ),
            "wiktextract_translation_support_match_count": len(_support_matches(candidate_sense)),
            "wiktextract_translation_support_matches": _support_matches(candidate_sense),
        },
    }


def _source_evidence_text(
    family: Mapping[str, object],
    sense: Mapping[str, object],
) -> str:
    metadata = _as_mapping(sense.get("metadata"))
    source_text = str(metadata.get("translation_sense_text") or "").strip()
    if not source_text:
        evidence_views = _as_mapping(sense.get("evidence_views"))
        source_text = str(evidence_views.get("gloss_text") or "").strip()
    if not source_text:
        return ""
    trigger = str(family.get("trigger") or "").strip()
    canonical_pos = str(sense.get("canonical_pos") or "").strip()
    parts = [trigger, canonical_pos, "sense:", source_text]
    return " ".join(part for part in parts if part).strip()


def _support_matches(sense: Mapping[str, object]) -> list[dict[str, object]]:
    metadata = _as_mapping(sense.get("metadata"))
    raw_matches = metadata.get("wiktextract_translation_support_matches")
    if not isinstance(raw_matches, Sequence) or isinstance(raw_matches, (str, bytes)):
        return []
    rows = []
    for match in raw_matches:
        if not isinstance(match, Mapping):
            continue
        rows.append(
            {
                "record_word": str(match.get("record_word") or "").strip(),
                "record_pos": str(match.get("record_pos") or "").strip(),
                "translation_word": str(match.get("translation_word") or "").strip(),
                "translation_sense": str(match.get("translation_sense") or "").strip(),
                "translation_tags": _text_list(match.get("translation_tags")),
                "sense_overlap": _text_list(match.get("sense_overlap")),
            }
        )
    return rows


def _sense_row(
    sense: Mapping[str, object],
    *,
    relation_type: str,
    supported: bool,
) -> dict[str, object]:
    metadata = _as_mapping(sense.get("metadata"))
    return {
        "sense_id": _sense_id(sense),
        "target_lemma": str(sense.get("target_lemma") or "").strip(),
        "canonical_pos": str(sense.get("canonical_pos") or "").strip(),
        "relation_type": relation_type,
        "translation_sense_text": str(metadata.get("translation_sense_text") or "").strip(),
        "source_supported": supported,
        "support_match_count": len(_support_matches(sense)),
    }


def _family_summary_row(
    family: Mapping[str, object],
    items: Sequence[Mapping[str, object]],
    sense_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "active_row_count": sum(
            1 for item in items if str(item.get("relation_type") or "") == "anchor_cue"
        ),
        "shadow_row_count": sum(
            1 for item in items if str(item.get("relation_type") or "") == "shadow_candidate"
        ),
        "skipped_sense_count": sum(1 for row in sense_rows if not row.get("source_supported")),
        "row_count": len(items),
        "senses": list(sense_rows),
    }


def _build_report(
    *,
    dataset_payload: Mapping[str, object],
    family_rows: Sequence[Mapping[str, object]],
    normalized_batch: Mapping[str, object] | None,
    generated_at: str,
    run_id: str,
) -> dict[str, object]:
    selected_senses = [
        sense
        for row in family_rows
        for sense in row.get("senses", ())
        if isinstance(sense, Mapping)
    ]
    row_count = (
        int(normalized_batch.get("row_count") or 0) if isinstance(normalized_batch, Mapping) else 0
    )
    normalized_rows = (
        [row for row in normalized_batch.get("rows", ()) if isinstance(row, Mapping)]
        if isinstance(normalized_batch, Mapping)
        else []
    )
    skipped = sum(1 for sense in selected_senses if not sense.get("source_supported"))
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ok" if row_count and skipped == 0 else "review",
        "decision": "candidate_batch_ready" if row_count and skipped == 0 else "source_gaps_remain",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "run_id": run_id,
        "batch_id": str(normalized_batch.get("batch_id") or "").strip()
        if isinstance(normalized_batch, Mapping)
        else "",
        "source_type": SOURCE_TYPE,
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "summary": {
            "family_count": len(family_rows),
            "source_family_count": len(family_rows),
            "target_family_count": len(family_rows),
            "selected_sense_count": len(selected_senses),
            "source_supported_sense_count": len(selected_senses) - skipped,
            "skipped_sense_count": skipped,
            "row_count": row_count,
            "active_row_count": sum(
                1 for row in normalized_rows if str(row.get("relation_type") or "") == "anchor_cue"
            ),
            "shadow_row_count": sum(
                1
                for row in normalized_rows
                if str(row.get("relation_type") or "") == "shadow_candidate"
            ),
        },
        "family_rows": list(family_rows),
        "limitations": [
            "translation_sense_text_is_dictionary_gloss_not_sentence_example",
            "runtime_publishable=false_until_admission_and_heldout_validation",
            "does_not_cover_unselected_no_winner_senses",
            "does_not_add_phrase_containment_examples",
            "spanish_target_lemmas_are_excluded_from_evidence_text",
        ],
    }


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item or "").strip()]
    text = str(value or "").strip()
    return [text] if text else []


def main() -> int:
    args = _parse_args()
    dataset_payload = load_sentence_veto_dataset(args.dataset)
    bundle = build_translation_sense_evidence_bundle(
        dataset_payload=dataset_payload,
        run_id=str(args.run_id or "").strip() or DEFAULT_RUN_ID,
    )
    if isinstance(bundle.get("normalized_batch"), Mapping):
        _write_json(args.normalized_batch_out, bundle["normalized_batch"])
    _write_json(args.json_out, bundle["report"])
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_translation_sense_evidence_markdown(bundle["report"]),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if isinstance(bundle.get("normalized_batch"), Mapping):
        print(f"Wrote normalized batch to {args.normalized_batch_out}")
    return 0 if bundle["report"]["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
