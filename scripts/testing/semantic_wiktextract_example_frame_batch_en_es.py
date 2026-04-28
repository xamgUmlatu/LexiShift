#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
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

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402
from semantic_example_frame_source_adapter_support import (  # noqa: E402
    WORD_RE as _WORD_RE,
    all_family_dataset as _all_family_dataset,
    bucket_for_relation as _bucket_for_relation,
    content_tokens as _content_tokens,
    family_key_dataset as _family_key_dataset,
    sense_hint as _sense_hint,
    sense_id as _sense_id,
    sense_target_tokens as _sense_target_tokens,
    slug as _slug,
    stem as _stem,
    utc_now as _utc_now,
    write_json as _write_json,
)
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_QUEUE_JSON,
    _load_json,
)
from semantic_reverse_aux_text_pilot_en_es import build_queue_subset_dataset  # noqa: E402
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_RUN_ID = "wiktextract-example-frames-v10-20260425a"
DEFAULT_INTAKE_OUT = EXPERIMENT_ROOT / f"en-es-{DEFAULT_RUN_ID}_intake_batch.json"
DEFAULT_NORMALIZED_OUT = EXPERIMENT_ROOT / f"en-es-{DEFAULT_RUN_ID}_normalized_evidence.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_wiktextract_example_frame_batch_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_wiktextract_example_frame_batch_en_es_latest.md"
)
SOURCE_TYPE = "external"
SOURCE_ID = "wiktextract_example_frames"
SOURCE_FAMILY = "external_example_corpus"
PROMPT_VERSION = "wiktextract-example-frames-v1"
DEFAULT_SCOPE = "family_keys"
SUPPORTED_SCOPES = frozenset({"prompt_queue", "all_dataset_families", "family_keys"})
DEFAULT_MIN_LINK_SCORE = 0.12
DEFAULT_MAX_EXAMPLES_PER_SENSE = 2
DEFAULT_EARLY_STOP_AFTER_TRIGGER_MISS = 25000


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build schema-normalized example-frame evidence from local raw Wiktextract "
            "English examples. This recovers example rows that the current SQLite "
            "translation conversion may not expose."
        )
    )
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--raw-wiktextract-jsonl-gz", type=Path, default=None)
    parser.add_argument("--scope", choices=sorted(SUPPORTED_SCOPES), default=DEFAULT_SCOPE)
    parser.add_argument(
        "--family-key",
        action="append",
        default=[],
        help=(
            "Family key to extract when --scope family_keys is active. Can be repeated. "
            "Defaults to the current plant residual family."
        ),
    )
    parser.add_argument("--min-link-score", type=float, default=DEFAULT_MIN_LINK_SCORE)
    parser.add_argument(
        "--max-examples-per-sense", type=int, default=DEFAULT_MAX_EXAMPLES_PER_SENSE
    )
    parser.add_argument(
        "--early-stop-after-trigger-miss",
        type=int,
        default=DEFAULT_EARLY_STOP_AFTER_TRIGGER_MISS,
        help=(
            "For single-trigger residual extraction, stop after this many subsequent "
            "non-target records once at least one matching record has been seen. Use 0 "
            "for a complete gzip scan."
        ),
    )
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--intake-batch-out", type=Path, default=DEFAULT_INTAKE_OUT)
    parser.add_argument("--normalized-batch-out", type=Path, default=DEFAULT_NORMALIZED_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_wiktextract_example_frame_bundle(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    records_by_trigger: Mapping[str, Sequence[Mapping[str, object]]],
    data_root: Path,
    raw_wiktextract_path: Path,
    family_keys: Sequence[str] = (),
    scope: str = DEFAULT_SCOPE,
    min_link_score: float = DEFAULT_MIN_LINK_SCORE,
    max_examples_per_sense: int = DEFAULT_MAX_EXAMPLES_PER_SENSE,
    run_id: str = DEFAULT_RUN_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    source_scope = _normalize_scope(scope)
    subset_dataset, family_roles = _build_source_dataset(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        family_keys=family_keys,
        scope=source_scope,
    )
    intake_batch = _build_intake_batch(
        subset_dataset=subset_dataset,
        family_roles=family_roles,
        records_by_trigger=records_by_trigger,
        run_id=run_id,
        source_scope=source_scope,
        min_link_score=max(0.0, float(min_link_score)),
        max_examples_per_sense=max(1, int(max_examples_per_sense)),
        generated_at=generated_at,
    )
    normalized_batch = normalize_llm_intake_batch(intake_batch) if intake_batch["items"] else None
    family_rows = list(
        intake_batch.get("provenance", {}).get("family_rows", ())
        if isinstance(intake_batch.get("provenance"), Mapping)
        else ()
    )
    report = _build_report(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        family_rows=family_rows,
        normalized_batch=normalized_batch,
        data_root=data_root,
        raw_wiktextract_path=raw_wiktextract_path,
        generated_at=generated_at,
        run_id=run_id,
        source_scope=source_scope,
        min_link_score=float(min_link_score),
    )
    return {
        "intake_batch": intake_batch,
        "normalized_batch": normalized_batch,
        "report": report,
    }


def load_wiktextract_records_by_trigger(
    raw_wiktextract_path: Path,
    *,
    triggers: Sequence[str],
    early_stop_after_trigger_miss: int = DEFAULT_EARLY_STOP_AFTER_TRIGGER_MISS,
) -> dict[str, list[Mapping[str, object]]]:
    trigger_set = {
        str(trigger or "").strip().lower() for trigger in triggers if str(trigger).strip()
    }
    records_by_trigger: dict[str, list[Mapping[str, object]]] = {
        trigger: [] for trigger in trigger_set
    }
    if not raw_wiktextract_path.exists() or not trigger_set:
        return records_by_trigger
    seen_target_record = False
    post_hit_miss_count = 0
    early_stop_limit = max(0, int(early_stop_after_trigger_miss))
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
            trigger = str(record.get("word") or "").strip().lower()
            if trigger in trigger_set:
                records_by_trigger.setdefault(trigger, []).append(record)
                seen_target_record = True
                post_hit_miss_count = 0
            elif seen_target_record and len(trigger_set) == 1 and early_stop_limit:
                post_hit_miss_count += 1
                if post_hit_miss_count >= early_stop_limit:
                    break
    return records_by_trigger


def _build_intake_batch(
    *,
    subset_dataset: Mapping[str, object],
    family_roles: Mapping[str, str],
    records_by_trigger: Mapping[str, Sequence[Mapping[str, object]]],
    run_id: str,
    source_scope: str,
    min_link_score: float,
    max_examples_per_sense: int,
    generated_at: str,
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    family_rows: list[dict[str, object]] = []
    for family in subset_dataset.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        role = str(family_roles.get(str(family.get("family_id") or "").strip()) or "target")
        family_items, link_rows = _build_family_items(
            family,
            role=role,
            records=records_by_trigger.get(str(family.get("trigger") or "").strip().lower(), ()),
            min_link_score=min_link_score,
            max_examples_per_sense=max_examples_per_sense,
        )
        items.extend(family_items)
        family_rows.append(
            _family_summary_row(family, role=role, items=family_items, link_rows=link_rows)
        )
    return {
        "schema_version": 1,
        "batch_id": f"en-es:wiktextract-example-frames:{run_id}",
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
            "source_scope": source_scope,
            "source_note": "local raw Wiktextract English examples linked to dataset senses",
            "min_link_score": min_link_score,
            "max_examples_per_sense": max_examples_per_sense,
            "family_rows": family_rows,
        },
        "items": items,
    }


def _build_family_items(
    family: Mapping[str, object],
    *,
    role: str,
    records: Sequence[Mapping[str, object]],
    min_link_score: float,
    max_examples_per_sense: int,
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
    link_rows: list[dict[str, object]] = []
    for relation_type, sense in senses:
        match = _best_sense_match(
            records,
            trigger=str(family.get("trigger") or "").strip(),
            target_sense=sense,
            min_link_score=min_link_score,
        )
        link_rows.append(_link_row(sense, relation_type=relation_type, match=match))
        if match is None:
            continue
        examples = _sense_examples(match["sense"], trigger=str(family.get("trigger") or "").strip())
        for index, example in enumerate(examples[:max_examples_per_sense], start=1):
            items.append(
                _item(
                    family=family,
                    role=role,
                    active_sense=active,
                    candidate_sense=sense,
                    relation_type=relation_type,
                    evidence_text=example["text"],
                    row_suffix=(
                        f"{_bucket_for_relation(relation_type)}-{_slug(_sense_id(sense))}-"
                        f"wiktextract-example-{index}"
                    ),
                    roles=["cue_generation", "discrimination"]
                    if relation_type == "anchor_cue"
                    else ["discrimination"],
                    example_bucket=_bucket_for_relation(relation_type),
                    match=match,
                    example=example,
                )
            )
    return items, link_rows


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
    match: Mapping[str, object],
    example: Mapping[str, object],
) -> dict[str, object]:
    family_id = str(family.get("family_id") or "").strip()
    return {
        "row_id": f"{_slug(family_id)}:{row_suffix}",
        "relation_type": relation_type,
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(active_sense.get("target_lemma") or "").strip(),
        "candidate_target": str(candidate_sense.get("target_lemma") or "").strip(),
        "active_sense_hint": _sense_hint(active_sense, note="fixed_shadow_active"),
        "candidate_sense_hint": _sense_hint(candidate_sense, note="wiktextract_linked_candidate"),
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
            "candidate_sense_id": _sense_id(candidate_sense),
            "example_bucket": example_bucket,
            "source_view": "raw_wiktextract_example",
            "wiktextract_record_pos": str(match.get("record_pos") or ""),
            "wiktextract_sense_index": int(match.get("sense_index") or 0),
            "wiktextract_link_score": float(match.get("score") or 0.0),
            "wiktextract_link_overlap": list(match.get("overlap_tokens") or ()),
            "wiktextract_example_type": str(example.get("type") or ""),
        },
    }


def _best_sense_match(
    records: Sequence[Mapping[str, object]],
    *,
    trigger: str,
    target_sense: Mapping[str, object],
    min_link_score: float,
) -> dict[str, object] | None:
    target_tokens = _sense_target_tokens(target_sense, trigger=trigger)
    target_pos = str(target_sense.get("canonical_pos") or "").strip().lower()
    matches: list[dict[str, object]] = []
    for record in records:
        record_pos = str(record.get("pos") or "").strip().lower()
        if target_pos and record_pos and record_pos != target_pos:
            continue
        senses = record.get("senses")
        if not isinstance(senses, Sequence) or isinstance(senses, (str, bytes)):
            continue
        for index, sense in enumerate(senses):
            if not isinstance(sense, Mapping):
                continue
            if not _sense_examples(sense, trigger=trigger):
                continue
            candidate_tokens = _content_tokens(_sense_gloss_text(sense), trigger=trigger)
            overlap = tuple(sorted(target_tokens & candidate_tokens))
            score = len(overlap) / max(len(target_tokens), 1)
            if score < min_link_score:
                continue
            matches.append(
                {
                    "record_pos": record_pos,
                    "sense": sense,
                    "sense_index": index,
                    "score": round(score, 4),
                    "overlap_tokens": overlap,
                }
            )
    if not matches:
        return None
    return sorted(
        matches, key=lambda item: (item["score"], len(item["overlap_tokens"])), reverse=True
    )[0]


def _sense_examples(sense: Mapping[str, object], *, trigger: str) -> list[dict[str, object]]:
    examples = sense.get("examples")
    if not isinstance(examples, Sequence) or isinstance(examples, (str, bytes)):
        return []
    trigger_stem = _stem(str(trigger or "").strip().lower())
    rows: list[dict[str, object]] = []
    for item in examples:
        if not isinstance(item, Mapping):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        if str(item.get("type") or "example").strip() not in {"", "example"}:
            continue
        tokens = {_stem(token) for token in _WORD_RE.findall(text.lower())}
        if trigger_stem and trigger_stem not in tokens:
            continue
        rows.append({"text": text, "type": str(item.get("type") or "example").strip() or "example"})
    return rows


def _sense_gloss_text(sense: Mapping[str, object]) -> str:
    parts = []
    for key in ("glosses", "raw_glosses"):
        value = sense.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            parts.extend(str(item) for item in value)
    return " | ".join(parts)


def _family_summary_row(
    family: Mapping[str, object],
    *,
    role: str,
    items: Sequence[Mapping[str, object]],
    link_rows: Sequence[Mapping[str, object]],
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
        "role": role,
        "active_example_count": active_count,
        "shadow_example_count": shadow_count,
        "phrase_control_example_count": 0,
        "row_count": len(items),
        "link_rows": list(link_rows),
    }


def _link_row(
    sense: Mapping[str, object],
    *,
    relation_type: str,
    match: Mapping[str, object] | None,
) -> dict[str, object]:
    return {
        "sense_id": _sense_id(sense),
        "target_lemma": str(sense.get("target_lemma") or "").strip(),
        "canonical_pos": str(sense.get("canonical_pos") or "").strip(),
        "relation_type": relation_type,
        "linked": match is not None,
        "best_link_score": float(match.get("score") or 0.0) if isinstance(match, Mapping) else 0.0,
        "best_overlap": list(match.get("overlap_tokens") or ())
        if isinstance(match, Mapping)
        else [],
        "sense_index": int(match.get("sense_index") or 0) if isinstance(match, Mapping) else None,
    }


def _build_report(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    family_rows: Sequence[Mapping[str, object]],
    normalized_batch: Mapping[str, object] | None,
    data_root: Path,
    raw_wiktextract_path: Path,
    generated_at: str,
    run_id: str,
    source_scope: str,
    min_link_score: float,
) -> dict[str, object]:
    summary = {
        "queue_family_count": len(
            [f for f in queue_payload.get("families", ()) if isinstance(f, Mapping)]
        ),
        "source_family_count": len(family_rows),
        "target_family_count": len(family_rows),
        "row_count": int(normalized_batch.get("row_count") or 0)
        if isinstance(normalized_batch, Mapping)
        else 0,
        "families_with_active_examples": sum(
            1 for row in family_rows if int(row.get("active_example_count") or 0) > 0
        ),
        "families_with_shadow_examples": sum(
            1 for row in family_rows if int(row.get("shadow_example_count") or 0) > 0
        ),
        "families_with_phrase_control_examples": 0,
        "min_link_score": float(min_link_score),
    }
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ok",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "run_id": run_id,
        "source_scope": source_scope,
        "batch_id": str(normalized_batch.get("batch_id") or "").strip()
        if isinstance(normalized_batch, Mapping)
        else "",
        "source_type": SOURCE_TYPE,
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "resource_status": {
            "data_root": str(data_root),
            "raw_wiktextract_path": str(raw_wiktextract_path),
            "raw_wiktextract_exists": raw_wiktextract_path.exists(),
        },
        "summary": summary,
        "family_rows": list(family_rows),
        "recommendation": (
            "Use this adapter for residual source-example coverage, then rerun the "
            "source-admission cycle against the composite source batch."
        ),
    }


def render_wiktextract_example_frame_batch_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es Wiktextract Example-Frame Batch",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Source: `{report.get('source_id', '')}` / `{report.get('source_family', '')}`",
        f"- Scope: `{report.get('source_scope', '')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        "",
        "| Family | Active | Shadow | Phrase | Rows |",
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


def _build_source_dataset(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    family_keys: Sequence[str],
    scope: str,
) -> tuple[dict[str, object], dict[str, str]]:
    if scope == "prompt_queue":
        return build_queue_subset_dataset(dataset_payload, queue_payload)
    if scope == "all_dataset_families":
        return _all_family_dataset(dataset_payload)
    return _family_key_dataset(
        dataset_payload,
        family_keys=family_keys,
        default_family_keys=["en-es:sentence-veto:plant:planta"],
    )


def _normalize_scope(value: str) -> str:
    text = str(value or "").strip() or DEFAULT_SCOPE
    if text not in SUPPORTED_SCOPES:
        raise ValueError(f"unsupported source scope: {text}")
    return text


def main() -> int:
    args = _parse_args()
    queue_payload = _load_json(args.queue_json)
    dataset_payload = load_sentence_veto_dataset(args.dataset)
    data_root = Path(args.data_root)
    raw_path = (
        Path(args.raw_wiktextract_jsonl_gz)
        if args.raw_wiktextract_jsonl_gz is not None
        else data_root / "language_packs" / "raw-wiktextract-data.jsonl.gz"
    )
    subset_dataset, _roles = _build_source_dataset(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        family_keys=args.family_key,
        scope=str(args.scope or "").strip() or DEFAULT_SCOPE,
    )
    triggers = [
        str(family.get("trigger") or "").strip()
        for family in subset_dataset.get("families", ())
        if isinstance(family, Mapping)
    ]
    records_by_trigger = load_wiktextract_records_by_trigger(
        raw_path,
        triggers=triggers,
        early_stop_after_trigger_miss=int(args.early_stop_after_trigger_miss),
    )
    bundle = build_wiktextract_example_frame_bundle(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        records_by_trigger=records_by_trigger,
        data_root=data_root,
        raw_wiktextract_path=raw_path,
        family_keys=args.family_key,
        scope=str(args.scope or "").strip() or DEFAULT_SCOPE,
        min_link_score=float(args.min_link_score),
        max_examples_per_sense=int(args.max_examples_per_sense),
        run_id=str(args.run_id or "").strip() or DEFAULT_RUN_ID,
    )
    if isinstance(bundle.get("intake_batch"), Mapping):
        _write_json(args.intake_batch_out, bundle["intake_batch"])
    if isinstance(bundle.get("normalized_batch"), Mapping):
        _write_json(args.normalized_batch_out, bundle["normalized_batch"])
    _write_json(args.json_out, bundle["report"])
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_wiktextract_example_frame_batch_markdown(bundle["report"]),
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
