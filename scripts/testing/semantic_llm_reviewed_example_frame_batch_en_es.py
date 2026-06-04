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
TEST_INPUTS_ROOT = DOCS_ROOT / "test_inputs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXPERIMENT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_llm_example_frame_batches"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402
from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    build_runtime_context_views,
)
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_QUEUE_JSON,
    _load_json,
)
from semantic_reverse_aux_text_pilot_en_es import build_queue_subset_dataset  # noqa: E402
from semantic_routing_sentence_veto_helpers import _normalize_string_list  # noqa: E402
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_RUN_ID = "reviewed-example-frames-v10-20260425a"
DEFAULT_INTAKE_OUT = EXPERIMENT_ROOT / f"en-es-{DEFAULT_RUN_ID}_intake_batch.json"
DEFAULT_NORMALIZED_OUT = EXPERIMENT_ROOT / f"en-es-{DEFAULT_RUN_ID}_normalized_evidence.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_reviewed_example_frame_batch_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_reviewed_example_frame_batch_latest.md"
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a no-spend, schema-shaped example-frame batch from reviewed en-es "
            "sentence-veto cases."
        )
    )
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--all-dataset-families",
        action="store_true",
        help="Include every family in the dataset instead of the prompt queue slice.",
    )
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--intake-batch-out", type=Path, default=DEFAULT_INTAKE_OUT)
    parser.add_argument("--normalized-batch-out", type=Path, default=DEFAULT_NORMALIZED_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_reviewed_example_frame_bundle(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    all_dataset_families: bool = False,
    run_id: str = DEFAULT_RUN_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
    if all_dataset_families:
        subset_dataset = _all_family_dataset(dataset_payload)
        scope = "all_dataset_families"
    else:
        subset_dataset, _family_roles = build_queue_subset_dataset(dataset_payload, queue_payload)
        scope = "prompt_queue"
    intake_batch = _build_intake_batch(
        subset_dataset=subset_dataset,
        run_id=run_id,
        generated_at=generated_at,
        evaluation_scope=scope,
    )
    normalized_batch = normalize_llm_intake_batch(intake_batch)
    report = _build_report(
        intake_batch=intake_batch,
        normalized_batch=normalized_batch,
        dataset_payload=dataset_payload,
        evaluation_scope=scope,
        generated_at=generated_at,
    )
    return {
        "intake_batch": intake_batch,
        "normalized_batch": normalized_batch,
        "report": report,
    }


def _all_family_dataset(dataset_payload: Mapping[str, object]) -> dict[str, object]:
    payload = dict(dataset_payload)
    payload["families"] = [
        dict(family)
        for family in dataset_payload.get("families", ())
        if isinstance(family, Mapping)
    ]
    return payload


def _build_intake_batch(
    *,
    subset_dataset: Mapping[str, object],
    run_id: str,
    generated_at: str,
    evaluation_scope: str,
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    family_rows: list[dict[str, object]] = []
    for family in subset_dataset.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_items = _build_family_items(family)
        items.extend(family_items)
        family_rows.append(_family_summary_row(family, family_items))
    batch_id = f"en-es:reviewed-example-frames:{run_id}"
    return {
        "schema_version": 1,
        "batch_id": batch_id,
        "pair": str(subset_dataset.get("pair") or "").strip() or "en-es",
        "source_type": "llm",
        "source_id": "reviewed_sentence_veto_example_frames",
        "source_family": "silver_llm_generation",
        "roles": ["cue_generation", "discrimination", "phrase_containment"],
        "generated_at": generated_at,
        "ingested_at": generated_at,
        "review_state": "accepted",
        "model_id": "reviewed-sentence-veto-fixture",
        "prompt_version": "reviewed-example-frames-v1",
        "temperature": 0.0,
        "provenance": {
            "dataset_id": str(subset_dataset.get("dataset_id") or "").strip(),
            "evaluation_scope": evaluation_scope,
            "source_note": "schema-shaped no-spend fixture generated from reviewed cases",
            "family_rows": family_rows,
        },
        "items": items,
    }


def _build_family_items(family: Mapping[str, object]) -> list[dict[str, object]]:
    active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
    active_id = _sense_id(active)
    items: list[dict[str, object]] = []
    for index, example in enumerate(_examples_for_winner(family, winner_id=active_id), start=1):
        items.append(
            _item(
                family=family,
                active_sense=active,
                relation_type="anchor_cue",
                candidate_sense=active,
                evidence_text=example,
                row_suffix=f"active-{index}",
                roles=["cue_generation", "discrimination"],
                metadata={"example_bucket": "active"},
            )
        )
    for shadow in family.get("shadows", ()):
        if not isinstance(shadow, Mapping):
            continue
        for index, example in enumerate(
            _examples_for_winner(family, winner_id=_sense_id(shadow)),
            start=1,
        ):
            items.append(
                _item(
                    family=family,
                    active_sense=active,
                    relation_type="shadow_candidate",
                    candidate_sense=shadow,
                    evidence_text=example,
                    row_suffix=f"shadow-{_slug(_sense_id(shadow))}-{index}",
                    roles=["discrimination"],
                    metadata={"example_bucket": "shadow"},
                )
            )
    for index, example in enumerate(_phrase_examples_for_family(family), start=1):
        items.append(
            _item(
                family=family,
                active_sense=active,
                relation_type="phrase_control_example",
                candidate_sense={},
                evidence_text=example,
                row_suffix=f"phrase-{index}",
                roles=["discrimination", "phrase_containment"],
                metadata={"example_bucket": "phrase_control", "gold_decision": "abstain"},
            )
        )
    return items


def _item(
    *,
    family: Mapping[str, object],
    active_sense: Mapping[str, object],
    relation_type: str,
    candidate_sense: Mapping[str, object],
    evidence_text: str,
    row_suffix: str,
    roles: Sequence[str],
    metadata: Mapping[str, object],
) -> dict[str, object]:
    family_id = str(family.get("family_id") or "").strip()
    trigger = str(family.get("trigger") or "").strip()
    candidate_id = _sense_id(candidate_sense)
    candidate_target = (
        str(candidate_sense.get("target_lemma") or "").strip() if candidate_id else "phrase_control"
    )
    row_metadata = {
        "family_id": family_id,
        "active_sense_id": _sense_id(active_sense),
        **dict(metadata),
    }
    if candidate_id:
        row_metadata["candidate_sense_id"] = candidate_id
    item = {
        "row_id": f"{_slug(family_id)}:{row_suffix}",
        "relation_type": relation_type,
        "trigger": trigger,
        "active_target": str(active_sense.get("target_lemma") or "").strip(),
        "candidate_target": candidate_target,
        "active_sense_hint": _sense_hint(active_sense, note="fixed_shadow_active"),
        "candidate_pos": str(candidate_sense.get("canonical_pos") or "").strip()
        if candidate_id
        else "phrase_control",
        "evidence_text": evidence_text,
        "example_count": 1,
        "review_state": "accepted",
        "promotion_state": "kept",
        "runtime_publishable": False,
        "roles": list(roles),
        "metadata": row_metadata,
    }
    if candidate_id:
        item["candidate_sense_hint"] = _sense_hint(
            candidate_sense,
            note="fixed_shadow_candidate",
        )
    return item


def _sense_hint(sense: Mapping[str, object], *, note: str) -> dict[str, object]:
    return {
        "provider": "sentence_veto_dataset",
        "locator_kind": "sense_id",
        "target_key": _sense_id(sense),
        "canonical_pos": str(sense.get("canonical_pos") or "").strip(),
        "note": note,
    }


def _examples_for_winner(family: Mapping[str, object], *, winner_id: str) -> list[str]:
    examples: list[str] = []
    for case in family.get("cases", ()):
        if not isinstance(case, Mapping):
            continue
        if str(case.get("gold_winner") or "").strip() != winner_id:
            continue
        if "phrase_control" in _normalize_string_list(case.get("slice_tags")):
            continue
        _append_example(examples, family=family, case=case)
    return examples[:2]


def _phrase_examples_for_family(family: Mapping[str, object]) -> list[str]:
    examples: list[str] = []
    for case in family.get("cases", ()):
        if not isinstance(case, Mapping):
            continue
        if (
            "phrase_control" not in _normalize_string_list(case.get("slice_tags"))
            and str(case.get("gold_winner") or "").strip() != "none"
        ):
            continue
        _append_example(examples, family=family, case=case)
    return examples[:2]


def _append_example(
    examples: list[str],
    *,
    family: Mapping[str, object],
    case: Mapping[str, object],
) -> None:
    context_views = build_runtime_context_views(
        str(case.get("sentence") or "").strip(),
        source_phrase=str(case.get("source_phrase") or family.get("trigger") or "").strip(),
    )
    text = str(context_views.get("masked_sentence") or "").strip()
    if text and text not in examples:
        examples.append(text)


def _family_summary_row(
    family: Mapping[str, object],
    items: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    counts = {"active": 0, "shadow": 0, "phrase_control": 0}
    for item in items:
        bucket = str((item.get("metadata") or {}).get("example_bucket") or "")
        if bucket in counts:
            counts[bucket] += 1
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "active_example_count": counts["active"],
        "shadow_example_count": counts["shadow"],
        "phrase_control_example_count": counts["phrase_control"],
        "row_count": len(items),
    }


def _build_report(
    *,
    intake_batch: Mapping[str, object],
    normalized_batch: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    evaluation_scope: str,
    generated_at: str,
) -> dict[str, object]:
    provenance = intake_batch.get("provenance") if isinstance(intake_batch, Mapping) else {}
    family_rows = list(
        (provenance.get("family_rows") if isinstance(provenance, Mapping) else None) or []
    )
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ok",
        "pair": str(normalized_batch.get("pair") or "").strip() or "en-es",
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "evaluation_scope": evaluation_scope,
        "batch_id": str(normalized_batch.get("batch_id") or "").strip(),
        "source_id": str(normalized_batch.get("source_id") or "").strip(),
        "row_count": int(normalized_batch.get("row_count") or 0),
        "family_count": len(family_rows),
        "family_rows": family_rows,
        "recommendation": (
            "Use this no-spend reviewed fixture to test the active/shadow/phrase-control "
            "source contract and prototype-admission plumbing. It is not runtime-publishable "
            "and must not be treated as paid-generation evidence."
        ),
    }


def render_reviewed_example_frame_batch_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Reviewed Example-Frame Batch",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Scope: `{report.get('evaluation_scope', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Rows: `{report.get('row_count', 0)}`",
        f"- Families: `{report.get('family_count', 0)}`",
        "",
        "## Family Rows",
        "",
        "| Family | Active | Shadow | Phrase Control | Rows |",
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
                    str(row.get("active_example_count", 0)),
                    str(row.get("shadow_example_count", 0)),
                    str(row.get("phrase_control_example_count", 0)),
                    str(row.get("row_count", 0)),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


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
    bundle = build_reviewed_example_frame_bundle(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        all_dataset_families=bool(args.all_dataset_families),
        run_id=str(args.run_id or "").strip() or DEFAULT_RUN_ID,
    )
    _write_json(args.intake_batch_out, bundle["intake_batch"])
    _write_json(args.normalized_batch_out, bundle["normalized_batch"])
    _write_json(args.json_out, bundle["report"])
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_reviewed_example_frame_batch_markdown(bundle["report"]),
        encoding="utf-8",
    )
    print(f"Wrote intake batch to {args.intake_batch_out}")
    print(f"Wrote normalized batch to {args.normalized_batch_out}")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
