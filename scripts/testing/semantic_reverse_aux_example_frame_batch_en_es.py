#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXPERIMENT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
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
from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_QUEUE_JSON,
    _load_json,
)
from semantic_reverse_aux_text_pilot_en_es import (  # noqa: E402
    _build_pack_record,
    build_queue_subset_dataset,
    extract_reverse_aux_text,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_RUN_ID = "reverse-aux-example-frames-v10-20260425a"
DEFAULT_INTAKE_OUT = EXPERIMENT_ROOT / f"en-es-{DEFAULT_RUN_ID}_intake_batch.json"
DEFAULT_NORMALIZED_OUT = EXPERIMENT_ROOT / f"en-es-{DEFAULT_RUN_ID}_normalized_evidence.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_reverse_aux_example_frame_batch_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_reverse_aux_example_frame_batch_en_es_latest.md"
)
SOURCE_TYPE = "external"
SOURCE_ID = "reverse_aux_example_frames"
SOURCE_FAMILY = "installed_translation_pack"
PROMPT_VERSION = "reverse-aux-example-frames-v1"
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a schema-normalized example-frame candidate batch from installed en-es "
            "reverse auxiliary sense text. This is an external-source coverage probe, not "
            "LLM or reviewed oracle evidence."
        )
    )
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--reverse-translation-dict", type=Path, default=None)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--intake-batch-out", type=Path, default=DEFAULT_INTAKE_OUT)
    parser.add_argument("--normalized-batch-out", type=Path, default=DEFAULT_NORMALIZED_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_reverse_aux_example_frame_bundle(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    reverse_records_by_trigger: Mapping[str, Sequence[TranslationGlossRecord]],
    data_root: Path,
    reverse_pack: TranslationPackRef | None,
    run_id: str = DEFAULT_RUN_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
    subset_dataset, family_roles = build_queue_subset_dataset(dataset_payload, queue_payload)
    missing_resources = []
    if reverse_pack is None or not reverse_pack.path.exists():
        missing_resources.append("reverse_translation_pack")

    intake_batch: dict[str, object] | None = None
    normalized_batch: dict[str, object] | None = None
    family_rows: list[dict[str, object]] = []
    if not missing_resources:
        intake_batch = _build_intake_batch(
            subset_dataset=subset_dataset,
            family_roles=family_roles,
            reverse_records_by_trigger=reverse_records_by_trigger,
            run_id=run_id,
            generated_at=generated_at,
        )
        family_rows = list(
            intake_batch.get("provenance", {}).get("family_rows", ())
            if isinstance(intake_batch.get("provenance"), Mapping)
            else ()
        )
        if intake_batch["items"]:
            normalized_batch = normalize_llm_intake_batch(intake_batch)

    report = _build_report(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        family_rows=family_rows,
        normalized_batch=normalized_batch,
        data_root=data_root,
        reverse_pack=reverse_pack,
        missing_resources=missing_resources,
        generated_at=generated_at,
        run_id=run_id,
    )
    return {
        "intake_batch": intake_batch,
        "normalized_batch": normalized_batch,
        "report": report,
    }


def _build_intake_batch(
    *,
    subset_dataset: Mapping[str, object],
    family_roles: Mapping[str, str],
    reverse_records_by_trigger: Mapping[str, Sequence[TranslationGlossRecord]],
    run_id: str,
    generated_at: str,
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    family_rows: list[dict[str, object]] = []
    for family in subset_dataset.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_items = _build_family_items(
            family,
            role=str(family_roles.get(str(family.get("family_id") or "").strip()) or "target"),
            reverse_records_by_trigger=reverse_records_by_trigger,
        )
        items.extend(family_items)
        family_rows.append(_family_summary_row(family, family_items))
    return {
        "schema_version": 1,
        "batch_id": f"en-es:reverse-aux-example-frames:{run_id}",
        "pair": str(subset_dataset.get("pair") or "").strip() or "en-es",
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
            "dataset_id": str(subset_dataset.get("dataset_id") or "").strip(),
            "source_note": "installed reverse-pack auxiliary sense text, no LLM or reviewed examples",
            "family_rows": family_rows,
        },
        "items": items,
    }


def _build_family_items(
    family: Mapping[str, object],
    *,
    role: str,
    reverse_records_by_trigger: Mapping[str, Sequence[TranslationGlossRecord]],
) -> list[dict[str, object]]:
    trigger = str(family.get("trigger") or "").strip()
    active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
    items: list[dict[str, object]] = []
    active_aux_text = extract_reverse_aux_text(
        trigger=trigger,
        target_lemma=str(active.get("target_lemma") or "").strip(),
        reverse_records_by_trigger=reverse_records_by_trigger,
    )
    if active_aux_text:
        items.append(
            _item(
                family=family,
                role=role,
                active_sense=active,
                candidate_sense=active,
                relation_type="anchor_cue",
                evidence_text=active_aux_text,
                row_suffix="active-reverse-aux",
                roles=["cue_generation", "discrimination"],
                example_bucket="active",
            )
        )

    for shadow in family.get("shadows", ()):
        if not isinstance(shadow, Mapping):
            continue
        shadow_aux_text = extract_reverse_aux_text(
            trigger=trigger,
            target_lemma=str(shadow.get("target_lemma") or "").strip(),
            reverse_records_by_trigger=reverse_records_by_trigger,
        )
        if not shadow_aux_text:
            continue
        items.append(
            _item(
                family=family,
                role=role,
                active_sense=active,
                candidate_sense=shadow,
                relation_type="shadow_candidate",
                evidence_text=shadow_aux_text,
                row_suffix=f"shadow-{_slug(_sense_id(shadow))}-reverse-aux",
                roles=["discrimination"],
                example_bucket="shadow",
            )
        )
    return items


def _item(
    *,
    family: Mapping[str, object],
    role: str,
    active_sense: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    relation_type: str,
    evidence_text: str,
    row_suffix: str,
    roles: Sequence[str],
    example_bucket: str,
) -> dict[str, object]:
    family_id = str(family.get("family_id") or "").strip()
    trigger = str(family.get("trigger") or "").strip()
    candidate_id = _sense_id(candidate_sense)
    return {
        "row_id": f"{_slug(family_id)}:{row_suffix}",
        "relation_type": relation_type,
        "trigger": trigger,
        "active_target": str(active_sense.get("target_lemma") or "").strip(),
        "candidate_target": str(candidate_sense.get("target_lemma") or "").strip(),
        "active_sense_hint": _sense_hint(active_sense, note="fixed_shadow_active"),
        "candidate_sense_hint": _sense_hint(candidate_sense, note="reverse_aux_candidate"),
        "candidate_pos": str(candidate_sense.get("canonical_pos") or "").strip(),
        "evidence_text": evidence_text,
        "example_count": 1,
        "review_state": "unreviewed",
        "promotion_state": "proposed",
        "runtime_publishable": False,
        "roles": list(roles),
        "metadata": {
            "family_id": family_id,
            "queue_role": role,
            "active_sense_id": _sense_id(active_sense),
            "candidate_sense_id": candidate_id,
            "example_bucket": example_bucket,
            "source_view": "reverse_aux_text",
        },
    }


def _family_summary_row(
    family: Mapping[str, object],
    items: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    active_count = sum(1 for item in items if str(item.get("relation_type") or "") == "anchor_cue")
    shadow_count = sum(
        1 for item in items if str(item.get("relation_type") or "") == "shadow_candidate"
    )
    active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(active.get("target_lemma") or "").strip(),
        "active_aux_count": active_count,
        "shadow_aux_count": shadow_count,
        "phrase_control_example_count": 0,
        "row_count": len(items),
    }


def _build_report(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    family_rows: Sequence[Mapping[str, object]],
    normalized_batch: Mapping[str, object] | None,
    data_root: Path,
    reverse_pack: TranslationPackRef | None,
    missing_resources: Sequence[str],
    generated_at: str,
    run_id: str,
) -> dict[str, object]:
    queue_families = [
        family for family in queue_payload.get("families", ()) if isinstance(family, Mapping)
    ]
    queue_roles = {
        str(family.get("family_id") or "").strip(): str(family.get("role") or "").strip()
        for family in queue_families
        if str(family.get("family_id") or "").strip()
    }
    target_rows = [
        row
        for row in family_rows
        if str(queue_roles.get(str(row.get("family_id") or "").strip()) or "target") == "target"
    ]
    summary = {
        "queue_family_count": len(queue_families),
        "target_family_count": sum(1 for role in queue_roles.values() if role == "target"),
        "row_count": int(normalized_batch.get("row_count") or 0)
        if isinstance(normalized_batch, Mapping)
        else 0,
        "families_with_active_aux": sum(
            1 for row in family_rows if int(row.get("active_aux_count") or 0) > 0
        ),
        "families_with_shadow_aux": sum(
            1 for row in family_rows if int(row.get("shadow_aux_count") or 0) > 0
        ),
        "target_families_with_active_aux": sum(
            1 for row in target_rows if int(row.get("active_aux_count") or 0) > 0
        ),
        "target_families_with_shadow_aux": sum(
            1 for row in target_rows if int(row.get("shadow_aux_count") or 0) > 0
        ),
        "families_with_phrase_control_examples": 0,
    }
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "missing_resources" if missing_resources else "ok",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "run_id": run_id,
        "batch_id": str(normalized_batch.get("batch_id") or "").strip()
        if isinstance(normalized_batch, Mapping)
        else "",
        "source_type": SOURCE_TYPE,
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "resource_status": {
            "data_root": str(data_root),
            "reverse_pack": _build_pack_record(reverse_pack),
            "missing_resources": list(missing_resources),
        },
        "summary": summary,
        "family_rows": list(family_rows),
        "recommendation": _build_recommendation(summary, missing_resources=missing_resources),
    }


def render_reverse_aux_example_frame_batch_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es Reverse Aux Example-Frame Batch",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Source: `{report.get('source_id', '')}` / `{report.get('source_family', '')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        "",
        "## Coverage",
        "",
        f"- Queue families: `{summary.get('queue_family_count', 0)}`",
        f"- Target families: `{summary.get('target_family_count', 0)}`",
        f"- Target families with active reverse aux: `{summary.get('target_families_with_active_aux', 0)}`",
        f"- Target families with shadow reverse aux: `{summary.get('target_families_with_shadow_aux', 0)}`",
        f"- Families with phrase-control examples: `{summary.get('families_with_phrase_control_examples', 0)}`",
        "",
        "| Family | Active Aux | Shadow Aux | Phrase Control | Rows |",
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
                    str(row.get("active_aux_count", 0)),
                    str(row.get("shadow_aux_count", 0)),
                    str(row.get("phrase_control_example_count", 0)),
                    str(row.get("row_count", 0)),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _build_recommendation(
    summary: Mapping[str, object],
    *,
    missing_resources: Sequence[str],
) -> str:
    if missing_resources:
        return (
            "Resolve the installed en-es reverse translation pack before building "
            "reverse-aux example-frame evidence."
        )
    return (
        "This is a real non-LLM source batch, but it is not contract-complete: reverse aux "
        f"covers active text for `{summary.get('target_families_with_active_aux', 0)}` target "
        f"families and shadow text for `{summary.get('target_families_with_shadow_aux', 0)}`, "
        "with no phrase-control examples. Use the required-family contract gate to route "
        "the remaining rows to source ingestion or a narrow LLM example-frame generator."
    )


def _sense_hint(sense: Mapping[str, object], *, note: str) -> dict[str, object]:
    return {
        "provider": "sentence_veto_dataset",
        "locator_kind": "sense_id",
        "target_key": _sense_id(sense),
        "canonical_pos": str(sense.get("canonical_pos") or "").strip(),
        "note": note,
    }


def _sense_id(sense: Mapping[str, object]) -> str:
    return str(sense.get("sense_id") or "").strip()


def _slug(value: object) -> str:
    text = str(value or "").strip().lower()
    return _SLUG_RE.sub("-", text).strip("-") or "row"


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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

    bundle = build_reverse_aux_example_frame_bundle(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        reverse_records_by_trigger=reverse_records_by_trigger,
        data_root=Path(args.data_root),
        reverse_pack=reverse_pack,
        run_id=str(args.run_id or "").strip() or DEFAULT_RUN_ID,
    )
    if isinstance(bundle.get("intake_batch"), Mapping):
        _write_json(args.intake_batch_out, bundle["intake_batch"])
    if isinstance(bundle.get("normalized_batch"), Mapping):
        _write_json(args.normalized_batch_out, bundle["normalized_batch"])
    _write_json(args.json_out, bundle["report"])
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_reverse_aux_example_frame_batch_markdown(bundle["report"]),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if isinstance(bundle.get("intake_batch"), Mapping):
        print(f"Wrote intake batch to {args.intake_batch_out}")
    if isinstance(bundle.get("normalized_batch"), Mapping):
        print(f"Wrote normalized batch to {args.normalized_batch_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
