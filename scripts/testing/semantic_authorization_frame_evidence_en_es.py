#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
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


DEFAULT_RUN_ID = "authorization-frame-non-v10-wave6-wiktextract-supported-v1-latest"
DEFAULT_DATASET_JSON = (
    DEFAULT_DRAFT_ROOT / "en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json"
)
DEFAULT_NORMALIZED_OUT = EXPERIMENT_ROOT / (f"en-es-{DEFAULT_RUN_ID}_normalized_evidence.json")
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_authorization_frame_evidence_non_v10_wave6_wiktextract_supported_latest.json"
)
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_authorization_frame_evidence_non_v10_wave6_wiktextract_supported_latest.md"
)
SOURCE_TYPE = "internal"
SOURCE_ID = "authorization_frame_evidence"
SOURCE_FAMILY = "internal_rulegen_artifact"
PROMPT_VERSION = "authorization-frame-evidence-v1"
AUTHORIZATION_CLASS_ID = "permission_authorization"
AUTHORIZATION_RE = re.compile(
    r"\b("
    r"approval|approved|authori[sz]ation|authori[sz]ed|consent|grant|granted|"
    r"licen[cs]e|permit|permission"
    r")\b",
    re.IGNORECASE,
)
AUTHORIZATION_TEMPLATES = (
    "official permission granted",
    "approved permission request",
    "request for permission was approved",
    "authorization granted",
    "consent granted by an authority",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build deterministic semantic-class evidence rows for source-backed "
            "permission/authorization senses. This is a no-spend adapter and does not "
            "change runtime policy."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--normalized-batch-out", type=Path, default=DEFAULT_NORMALIZED_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_authorization_frame_evidence_bundle(
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
        run_id=run_id,
        generated_at=generated_at,
    )
    return {
        "intake_batch": intake_batch,
        "normalized_batch": normalized_batch,
        "report": report,
    }


def render_authorization_frame_evidence_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Authorization-Frame Evidence Batch",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_id', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Source: `{report.get('source_id', '')}` / `{report.get('source_family', '')}`",
        f"- Matching senses: `{summary.get('matching_sense_count', 0)}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Active / shadow rows: `{summary.get('active_row_count', 0)}` / `{summary.get('shadow_row_count', 0)}`",
        "",
        "## Family Rows",
        "",
        "| Family | Matching Senses | Rows |",
        "| --- | ---: | ---: |",
    ]
    for row in report.get("family_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('family_id', '')}`",
                    str(row.get("matching_sense_count", 0)),
                    str(row.get("row_count", 0)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Source Trigger Audit",
            "",
            "| Family | Sense | Relation | Matched | Target In Source | Source Text |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report.get("family_rows", ()):
        if not isinstance(row, Mapping):
            continue
        family_id = str(row.get("family_id") or "").strip()
        for sense_row in row.get("sense_rows", ()):
            if not isinstance(sense_row, Mapping):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{family_id}`",
                        f"`{sense_row.get('sense_id', '')}`",
                        f"`{sense_row.get('relation_type', '')}`",
                        f"`{str(bool(sense_row.get('matched'))).lower()}`",
                        f"`{str(bool(sense_row.get('target_lemma_in_source_match_text'))).lower()}`",
                        _markdown_cell(_snippet(sense_row.get("source_match_text"))),
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
        "batch_id": f"en-es:authorization-frame-evidence:{run_id}",
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
            "semantic_class_id": AUTHORIZATION_CLASS_ID,
            "source_note": (
                "Deterministic English frame rows emitted only when a selected sense's "
                "source-backed English gloss or translation-sense text is "
                "permission/authorization-like. Spanish target lemmas are excluded from "
                "evidence_text."
            ),
            "templates": list(AUTHORIZATION_TEMPLATES),
            "family_rows": family_rows,
        },
        "items": items,
    }


def _family_items(
    family: Mapping[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    active = _as_mapping(family.get("active"))
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
        match_text = _authorization_match_text(sense)
        matched = bool(AUTHORIZATION_RE.search(match_text))
        sense_rows.append(
            _sense_row(
                sense,
                relation_type=relation_type,
                matched=matched,
                source_match_text=match_text,
            )
        )
        if not matched:
            continue
        for index, evidence_text in enumerate(AUTHORIZATION_TEMPLATES, start=1):
            items.append(
                _item(
                    family=family,
                    active_sense=active,
                    candidate_sense=sense,
                    relation_type=relation_type,
                    evidence_text=evidence_text,
                    index=index,
                    match_text=match_text,
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
    index: int,
    match_text: str,
) -> dict[str, object]:
    family_id = str(family.get("family_id") or "").strip()
    candidate_id = _sense_id(candidate_sense)
    example_bucket = _bucket_for_relation(relation_type)
    metadata = _as_mapping(candidate_sense.get("metadata"))
    return {
        "row_id": (
            f"{_slug(family_id)}:{example_bucket}-{_slug(candidate_id)}-authorization-frame-{index}"
        ),
        "relation_type": relation_type,
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(active_sense.get("target_lemma") or "").strip(),
        "candidate_target": str(candidate_sense.get("target_lemma") or "").strip(),
        "active_sense_hint": _sense_hint(active_sense, note="fixed_shadow_active"),
        "candidate_sense_hint": _sense_hint(
            candidate_sense,
            note="authorization_semantic_class_candidate",
            metadata={
                "semantic_class_id": AUTHORIZATION_CLASS_ID,
                "source_view": "source_backed_gloss_or_translation_sense",
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
            "semantic_class_id": AUTHORIZATION_CLASS_ID,
            "source_view": "authorization_frame_template",
            "source_match_text": match_text,
            "template_index": int(index),
            "template_count": len(AUTHORIZATION_TEMPLATES),
        },
    }


def _authorization_match_text(sense: Mapping[str, object]) -> str:
    evidence_views = _as_mapping(sense.get("evidence_views"))
    metadata = _as_mapping(sense.get("metadata"))
    parts = [
        evidence_views.get("sense_label"),
        evidence_views.get("gloss_text"),
        evidence_views.get("sense_gloss_bundle"),
        metadata.get("translation_sense_text"),
    ]
    for match in metadata.get("wiktextract_translation_support_matches") or ():
        if isinstance(match, Mapping):
            parts.append(match.get("translation_sense"))
    return " | ".join(str(part or "").strip() for part in parts if str(part or "").strip())


def _sense_row(
    sense: Mapping[str, object],
    *,
    relation_type: str,
    matched: bool,
    source_match_text: str,
) -> dict[str, object]:
    target_lemma = str(sense.get("target_lemma") or "").strip()
    metadata = _as_mapping(sense.get("metadata"))
    return {
        "sense_id": _sense_id(sense),
        "relation_type": relation_type,
        "matched": bool(matched),
        "canonical_pos": str(sense.get("canonical_pos") or "").strip(),
        "target_lemma": target_lemma,
        "support_sources": _text_list(metadata.get("support_sources")),
        "source_match_text": source_match_text,
        "target_lemma_in_source_match_text": bool(
            target_lemma and target_lemma.lower() in source_match_text.lower()
        ),
    }


def _family_summary_row(
    family: Mapping[str, object],
    items: Sequence[Mapping[str, object]],
    sense_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "selected_sense_count": len(sense_rows),
        "matching_sense_count": sum(1 for row in sense_rows if row.get("matched")),
        "row_count": len(items),
        "active_row_count": sum(1 for item in items if item.get("relation_type") == "anchor_cue"),
        "shadow_row_count": sum(
            1 for item in items if item.get("relation_type") == "shadow_candidate"
        ),
        "sense_rows": [dict(row) for row in sense_rows],
    }


def _build_report(
    *,
    dataset_payload: Mapping[str, object],
    family_rows: Sequence[Mapping[str, object]],
    normalized_batch: Mapping[str, object] | None,
    run_id: str,
    generated_at: str,
) -> dict[str, object]:
    rows = list(normalized_batch.get("rows", ())) if isinstance(normalized_batch, Mapping) else []
    target_family_count = sum(1 for row in family_rows if row.get("row_count"))
    row_count = len(rows)
    return {
        "schema_version": 1,
        "status": "ok" if row_count else "review",
        "decision": "authorization_frame_rows_ready" if row_count else "no_rows",
        "generated_at": generated_at,
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "run_id": run_id,
        "batch_id": str(normalized_batch.get("batch_id") or "").strip()
        if isinstance(normalized_batch, Mapping)
        else "",
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "prompt_version": PROMPT_VERSION,
        "summary": {
            "family_count": len(family_rows),
            "target_family_count": target_family_count,
            "selected_sense_count": sum(
                int(row.get("selected_sense_count") or 0) for row in family_rows
            ),
            "matching_sense_count": sum(
                int(row.get("matching_sense_count") or 0) for row in family_rows
            ),
            "row_count": row_count,
            "active_row_count": sum(1 for row in rows if row.get("relation_type") == "anchor_cue"),
            "shadow_row_count": sum(
                1 for row in rows if row.get("relation_type") == "shadow_candidate"
            ),
        },
        "family_rows": [dict(row) for row in family_rows if int(row.get("row_count") or 0) > 0],
        "limitations": [
            "deterministic_semantic_class_frame_not_runtime_policy",
            "authorization_class_templates_require_heldout_validation",
            "does_not_use_heldout_sentence_text",
        ],
    }


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item or "").strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _snippet(value: object, *, limit: int = 120) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def main() -> int:
    args = _parse_args()
    dataset = load_sentence_veto_dataset(args.dataset)
    bundle = build_authorization_frame_evidence_bundle(
        dataset_payload=dataset,
        run_id=str(args.run_id or "").strip() or DEFAULT_RUN_ID,
    )
    normalized = bundle["normalized_batch"]
    if isinstance(normalized, Mapping):
        _write_json(args.normalized_batch_out, normalized)
        print(f"Wrote normalized batch to {args.normalized_batch_out}")
    else:
        print("No normalized batch rows produced.")
    _write_json(args.json_out, bundle["report"])
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_authorization_frame_evidence_markdown(bundle["report"]),
        encoding="utf-8",
    )
    print(f"Wrote JSON report to {args.json_out}")
    print(f"Wrote Markdown report to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
